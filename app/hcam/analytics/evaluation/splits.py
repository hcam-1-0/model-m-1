from __future__ import annotations

import hashlib
from collections import Counter, defaultdict
from datetime import UTC, datetime
from typing import Annotated, Literal

from pydantic import Field, model_validator

from hcam.analytics.evaluation.contracts import (
    Digest,
    DigestBoundRecord,
    EvaluationContractModel,
    StableId,
    UtcDateTime,
    seal_record,
)


class SplitItemV1(EvaluationContractModel):
    item_id: StableId
    content_digest: Digest
    split: Literal["train", "validation", "test"]
    group_values: Annotated[dict[StableId, StableId], Field(min_length=1, max_length=32)]


class FinalTestAccessV1(EvaluationContractModel):
    access_id: StableId
    actor_id: StableId
    reason: Annotated[str, Field(min_length=1, max_length=500)]
    accessed_at: UtcDateTime
    tuning_use: Literal[False] = False


class SplitLeakageIssueV1(EvaluationContractModel):
    issue_code: StableId
    item_ids: Annotated[list[StableId], Field(min_length=1, max_length=1_000)]
    group_key: StableId | None = None


class SplitValidationReportV1(DigestBoundRecord):
    digest_field = "report_digest"
    contract_type: Literal["hcam.analytics.split-validation-report.v1"] = (
        "hcam.analytics.split-validation-report.v1"
    )
    report_id: StableId
    report_digest: Digest
    generated_at: UtcDateTime
    item_count: Annotated[int, Field(ge=0, le=10_000_000)]
    split_counts: Annotated[dict[StableId, int], Field(min_length=3, max_length=3)]
    required_group_keys: Annotated[list[StableId], Field(min_length=1, max_length=32)]
    final_test_frozen: bool
    final_test_accesses: Annotated[list[FinalTestAccessV1], Field(max_length=10_000)]
    exact_duplicate_count: Annotated[int, Field(ge=0, le=10_000_000)]
    cross_split_group_count: Annotated[int, Field(ge=0, le=10_000_000)]
    missing_group_key_count: Annotated[int, Field(ge=0, le=10_000_000)]
    issues: Annotated[list[SplitLeakageIssueV1], Field(max_length=10_000)]
    status: Literal["pass", "fail"]

    @model_validator(mode="after")
    def report_counts_are_consistent(self) -> SplitValidationReportV1:
        if set(self.split_counts) != {"train", "validation", "test"}:
            raise ValueError("split report requires train, validation, and test counts")
        issue_counts = Counter(issue.issue_code for issue in self.issues)
        expected = {
            "exact-duplicate-cross-split": self.exact_duplicate_count,
            "group-crosses-splits": self.cross_split_group_count,
            "required-group-key-missing": self.missing_group_key_count,
        }
        for code, count in expected.items():
            if issue_counts.get(code, 0) != count:
                raise ValueError("split issue count does not match issue records")
        has_failure = any(expected.values()) or any(
            access.tuning_use for access in self.final_test_accesses
        )
        if self.status == "pass" and has_failure:
            raise ValueError("passing split report cannot contain leakage")
        if self.status == "fail" and not has_failure:
            raise ValueError("failed split report requires leakage evidence")
        return self


def deterministic_split(group_identity: str) -> Literal["train", "validation", "test"]:
    bucket = int.from_bytes(hashlib.sha256(group_identity.encode("utf-8")).digest()[:8]) % 100
    if bucket < 70:
        return "train"
    if bucket < 85:
        return "validation"
    return "test"


def validate_splits(
    items: list[SplitItemV1],
    *,
    required_group_keys: list[str],
    final_test_frozen: bool,
    final_test_accesses: list[FinalTestAccessV1] | None = None,
    generated_at: datetime | None = None,
) -> SplitValidationReportV1:
    accesses = final_test_accesses or []
    issues: list[SplitLeakageIssueV1] = []
    digest_items: dict[str, list[SplitItemV1]] = defaultdict(list)
    grouped_splits: dict[tuple[str, str], dict[str, list[str]]] = defaultdict(
        lambda: defaultdict(list)
    )

    for item in items:
        digest_items[item.content_digest].append(item)
        missing = [key for key in required_group_keys if key not in item.group_values]
        for key in missing:
            issues.append(
                SplitLeakageIssueV1(
                    issue_code="required-group-key-missing",
                    item_ids=[item.item_id],
                    group_key=key,
                )
            )
        for key in required_group_keys:
            value = item.group_values.get(key)
            if value is not None:
                grouped_splits[(key, value)][item.split].append(item.item_id)

    for grouped in digest_items.values():
        splits = {item.split for item in grouped}
        if len(splits) > 1:
            issues.append(
                SplitLeakageIssueV1(
                    issue_code="exact-duplicate-cross-split",
                    item_ids=sorted(item.item_id for item in grouped),
                )
            )
    for (key, _value), split_items in grouped_splits.items():
        if len(split_items) > 1:
            issues.append(
                SplitLeakageIssueV1(
                    issue_code="group-crosses-splits",
                    item_ids=sorted(
                        item_id for item_ids in split_items.values() for item_id in item_ids
                    ),
                    group_key=key,
                )
            )

    counts = Counter(issue.issue_code for issue in issues)
    split_counts = Counter(item.split for item in items)
    has_failure = bool(issues) or any(access.tuning_use for access in accesses)
    document = {
        "report_id": "p31-generated-split-validation-v1",
        "generated_at": generated_at or datetime(2026, 8, 24, 12, 35, tzinfo=UTC),
        "item_count": len(items),
        "split_counts": {
            "train": split_counts["train"],
            "validation": split_counts["validation"],
            "test": split_counts["test"],
        },
        "required_group_keys": required_group_keys,
        "final_test_frozen": final_test_frozen,
        "final_test_accesses": [access.model_dump(mode="json") for access in accesses],
        "exact_duplicate_count": counts["exact-duplicate-cross-split"],
        "cross_split_group_count": counts["group-crosses-splits"],
        "missing_group_key_count": counts["required-group-key-missing"],
        "issues": [issue.model_dump(mode="json") for issue in issues],
        "status": "fail" if has_failure else "pass",
    }
    return seal_record(SplitValidationReportV1, document)
