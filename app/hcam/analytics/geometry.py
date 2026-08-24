from __future__ import annotations

from typing import Annotated, Literal, TypeAlias

from pydantic import Field, field_validator, model_validator

from hcam.analytics.contracts import (
    ActorId,
    CameraId,
    ContractModel,
    Department,
    ImmutableDigest,
    NormalizedCoordinate,
    StableName,
    StreamId,
    UtcDateTime,
)


DayOfWeek = Literal[
    "monday",
    "tuesday",
    "wednesday",
    "thursday",
    "friday",
    "saturday",
    "sunday",
]


class NormalizedPoint(ContractModel):
    x: NormalizedCoordinate
    y: NormalizedCoordinate


class LineGeometryV1(ContractModel):
    kind: Literal["line"] = "line"
    start: NormalizedPoint
    end: NormalizedPoint
    crossing_direction: Literal["both", "start_to_end", "end_to_start"] = "both"

    @model_validator(mode="after")
    def endpoints_are_distinct(self) -> LineGeometryV1:
        if self.start == self.end:
            raise ValueError("line endpoints must be distinct")
        return self


def _cross(a: NormalizedPoint, b: NormalizedPoint, c: NormalizedPoint) -> float:
    return (b.x - a.x) * (c.y - a.y) - (b.y - a.y) * (c.x - a.x)


def _on_segment(a: NormalizedPoint, b: NormalizedPoint, c: NormalizedPoint) -> bool:
    epsilon = 1e-12
    return (
        min(a.x, c.x) - epsilon <= b.x <= max(a.x, c.x) + epsilon
        and min(a.y, c.y) - epsilon <= b.y <= max(a.y, c.y) + epsilon
    )


def _segments_intersect(
    a: NormalizedPoint,
    b: NormalizedPoint,
    c: NormalizedPoint,
    d: NormalizedPoint,
) -> bool:
    epsilon = 1e-12
    ab_c = _cross(a, b, c)
    ab_d = _cross(a, b, d)
    cd_a = _cross(c, d, a)
    cd_b = _cross(c, d, b)
    if (ab_c > epsilon and ab_d < -epsilon or ab_c < -epsilon and ab_d > epsilon) and (
        cd_a > epsilon and cd_b < -epsilon or cd_a < -epsilon and cd_b > epsilon
    ):
        return True
    return (
        abs(ab_c) <= epsilon
        and _on_segment(a, c, b)
        or abs(ab_d) <= epsilon
        and _on_segment(a, d, b)
        or abs(cd_a) <= epsilon
        and _on_segment(c, a, d)
        or abs(cd_b) <= epsilon
        and _on_segment(c, b, d)
    )


class ZoneGeometryV1(ContractModel):
    kind: Literal["zone"] = "zone"
    vertices: Annotated[list[NormalizedPoint], Field(min_length=3, max_length=128)]
    boundary_policy: Literal["inside_inclusive", "inside_exclusive"] = (
        "inside_inclusive"
    )

    @model_validator(mode="after")
    def polygon_is_simple_and_non_degenerate(self) -> ZoneGeometryV1:
        points = self.vertices
        coordinates = [(point.x, point.y) for point in points]
        if len(set(coordinates)) != len(points):
            raise ValueError("zone vertices must be unique and implicitly closed")

        doubled_area = sum(
            points[index].x * points[(index + 1) % len(points)].y
            - points[(index + 1) % len(points)].x * points[index].y
            for index in range(len(points))
        )
        if abs(doubled_area) <= 1e-12:
            raise ValueError("zone polygon must have non-zero area")

        edge_count = len(points)
        for left in range(edge_count):
            left_next = (left + 1) % edge_count
            for right in range(left + 1, edge_count):
                right_next = (right + 1) % edge_count
                if left == right or left_next == right or right_next == left:
                    continue
                if _segments_intersect(
                    points[left],
                    points[left_next],
                    points[right],
                    points[right_next],
                ):
                    raise ValueError("zone polygon must not self-intersect")
        return self


GeometryShapeV1: TypeAlias = LineGeometryV1 | ZoneGeometryV1


class WeeklyWindowV1(ContractModel):
    days: Annotated[list[DayOfWeek], Field(min_length=1, max_length=7)]
    start_minute: Annotated[int, Field(ge=0, le=1_439)]
    end_minute: Annotated[int, Field(ge=1, le=1_440)]

    @field_validator("days")
    @classmethod
    def days_are_unique(cls, value: list[DayOfWeek]) -> list[DayOfWeek]:
        if len(set(value)) != len(value):
            raise ValueError("weekly window days must be unique")
        return value

    @model_validator(mode="after")
    def window_does_not_wrap_midnight(self) -> WeeklyWindowV1:
        if self.end_minute <= self.start_minute:
            raise ValueError("overnight windows must be split at midnight")
        return self


class GeometryScheduleV1(ContractModel):
    mode: Literal["always", "weekly"] = "always"
    timezone: Annotated[
        str,
        Field(
            min_length=3,
            max_length=128,
            pattern=r"^(?:UTC|[A-Za-z][A-Za-z0-9._+-]*(?:/[A-Za-z0-9._+-]+)+)$",
        ),
    ] = "UTC"
    windows: Annotated[list[WeeklyWindowV1], Field(max_length=64)] = Field(
        default_factory=list
    )

    @model_validator(mode="after")
    def mode_matches_windows(self) -> GeometryScheduleV1:
        if self.mode == "always" and self.windows:
            raise ValueError("always schedule cannot contain weekly windows")
        if self.mode == "weekly" and not self.windows:
            raise ValueError("weekly schedule requires at least one window")
        intervals_by_day: dict[str, list[tuple[int, int]]] = {}
        for window in self.windows:
            for day in window.days:
                intervals = intervals_by_day.setdefault(day, [])
                if any(
                    window.start_minute < end and window.end_minute > start
                    for start, end in intervals
                ):
                    raise ValueError("weekly schedule windows must not overlap")
                intervals.append((window.start_minute, window.end_minute))
        return self


class GeometryDefinitionV1(ContractModel):
    contract_type: Literal["hcam.analytics.geometry.v1"] = (
        "hcam.analytics.geometry.v1"
    )
    geometry_id: StableName
    version: Annotated[int, Field(ge=1, le=2_147_483_647)]
    department: Department
    stream_id: StreamId
    camera_id: CameraId
    status: Literal["draft", "approved", "retired"]
    coordinate_space: Literal["normalized_top_left"] = "normalized_top_left"
    shape: Annotated[GeometryShapeV1, Field(discriminator="kind")]
    schedule: GeometryScheduleV1 = Field(default_factory=GeometryScheduleV1)
    intended_use: Annotated[str, Field(min_length=1, max_length=500)]
    policy_version: ImmutableDigest
    owner_id: ActorId
    independent_reviewer_id: ActorId | None = None
    approval_record_id: StableName | None = None
    created_at: UtcDateTime
    updated_at: UtcDateTime

    @field_validator("intended_use")
    @classmethod
    def intended_use_is_trimmed(cls, value: str) -> str:
        if value.strip() != value or not value:
            raise ValueError("intended_use must be non-blank without outer whitespace")
        return value

    @model_validator(mode="after")
    def approval_and_time_are_consistent(self) -> GeometryDefinitionV1:
        if self.updated_at < self.created_at:
            raise ValueError("updated_at cannot precede created_at")
        if self.status in {"approved", "retired"}:
            if self.approval_record_id is None:
                raise ValueError("approved or retired geometry requires approval record")
        return self
