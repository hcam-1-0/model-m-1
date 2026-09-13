import { describe, expect, it, vi } from "vitest";
import {
  bearing,
  buildGeometry,
  circleToRing,
  closeRing,
  compassPoint,
  destination,
  drawReducer,
  formatArea,
  formatDistance,
  haversine,
  initialDrawState,
  measure,
  pathLength,
  polygonArea,
  queryRing,
  rectToRing,
  ringPerimeter,
  toShape,
} from "@hcam/gis-domain";
import {
  DEVELOPMENT_BASEMAP_STYLE,
  LOCAL_GUJARAT_STYLE,
  resolveOperationalStyle,
} from "../apps/gis-center/src/map-runtime";

describe("GIS map runtime", () => {
  it("uses the public development basemap only on loopback", () => {
    expect(resolveOperationalStyle("127.0.0.1", LOCAL_GUJARAT_STYLE)).toBe(
      DEVELOPMENT_BASEMAP_STYLE,
    );
    expect(resolveOperationalStyle("localhost")).toBe(DEVELOPMENT_BASEMAP_STYLE);
    expect(resolveOperationalStyle("gis.hcam.invalid", LOCAL_GUJARAT_STYLE)).toBe(
      LOCAL_GUJARAT_STYLE,
    );
  });
});

describe("Gujarat operational geometry", () => {
  it("keeps distance, bearing, destination, and labels deterministic", () => {
    const ahmedabad: [number, number] = [72.5714, 23.0225];
    const gandhinagar: [number, number] = [72.6369, 23.2156];
    const distance = haversine(ahmedabad, gandhinagar);
    const heading = bearing(ahmedabad, gandhinagar);
    const projected = destination(ahmedabad, heading, distance);

    expect(distance).toBeGreaterThan(20);
    expect(distance).toBeLessThan(24);
    expect(projected[0]).toBeCloseTo(gandhinagar[0], 5);
    expect(projected[1]).toBeCloseTo(gandhinagar[1], 5);
    expect(compassPoint(heading)).toMatch(/N/);
    expect(formatDistance(0.45)).toBe("450 m");
    expect(formatArea(0.005)).toBe("5,000 m²");
  });

  it("builds bounded rectangles, circles, paths, and polygon measurements", () => {
    const rectangle = rectToRing([72.5, 22.9], [72.7, 23.1]);
    const circle = circleToRing([72.6, 23], 2, 16);
    const path = [
      [72.5, 23],
      [72.6, 23.1],
      [72.7, 23.1],
    ];

    expect(rectangle).toHaveLength(5);
    expect(rectangle[0]).toEqual(rectangle.at(-1));
    expect(circle).toHaveLength(17);
    expect(circle[0]).toEqual(circle.at(-1));
    expect(polygonArea(rectangle)).toBeGreaterThan(400);
    expect(ringPerimeter(rectangle)).toBeGreaterThan(70);
    expect(pathLength(path)).toBeGreaterThan(20);
    expect(
      buildGeometry("rectangle", [
        [72.5, 22.9],
        [72.7, 23.1],
      ]),
    ).toEqual(rectangle);
    expect(measure("line", path)).toMatchObject({ closable: true, areaKm2: 0, vertices: 3 });
  });
});

describe("generated drawing reducer", () => {
  it("completes polygon, rectangle, circle, and route workflows", () => {
    let polygon = initialDrawState("polygon");
    polygon = drawReducer(polygon, { type: "click", at: [72.5, 23] }).state;
    polygon = drawReducer(polygon, { type: "click", at: [72.7, 23] }).state;
    polygon = drawReducer(polygon, { type: "click", at: [72.6, 23.2] }).state;
    const completedPolygon = drawReducer(polygon, { type: "finish" });
    expect(completedPolygon.result?.kind).toBe("polygon");

    let rectangle = initialDrawState("rectangle");
    rectangle = drawReducer(rectangle, { type: "click", at: [72.5, 23] }).state;
    const completedRectangle = drawReducer(rectangle, { type: "click", at: [72.7, 23.2] });
    expect(completedRectangle.result?.coords).toHaveLength(5);

    let circle = initialDrawState("circle");
    circle = drawReducer(circle, { type: "click", at: [72.5, 23] }).state;
    const completedCircle = drawReducer(circle, { type: "click", at: [72.6, 23] });
    expect(completedCircle.result?.meta?.radiusKm).toBeGreaterThan(10);

    let route = initialDrawState("line");
    route = drawReducer(route, { type: "click", at: [72.5, 23] }).state;
    route = drawReducer(route, { type: "click", at: [72.6, 23.1] }).state;
    route = drawReducer(route, { type: "undo" }).state;
    expect(route.points).toHaveLength(1);
    expect(drawReducer(route, { type: "cancel" })).toMatchObject({
      cancelled: true,
      state: { points: [] },
    });
  });

  it("creates session drawings with stable geometry semantics", () => {
    vi.spyOn(Date, "now").mockReturnValue(1_000);
    vi.spyOn(Math, "random").mockReturnValue(0.25);
    const result = {
      kind: "polygon" as const,
      coords: [
        [72.5, 23],
        [72.7, 23],
        [72.6, 23.2],
      ],
    };
    const shape = toShape(result, [], 0);
    expect(shape.name).toBe("Area 1");
    expect(shape.createdAt).toBe(1_000);
    expect(queryRing(shape)).toEqual(closeRing(result.coords));
    expect(shape.areaKm2).toBeGreaterThan(0);
    vi.restoreAllMocks();
  });
});
