import { useCallback, useEffect, useRef, useState } from "react";
import * as maplibregl from "maplibre-gl";
import mapLibreWorkerUrl from "maplibre-gl/dist/maplibre-gl-worker.mjs?worker&url";
import type {
  GeoJSONSource,
  Map as MapLibreMap,
  MapLayerMouseEvent,
  MapMouseEvent,
} from "maplibre-gl";
import type { CameraFixture } from "../operations-fixtures";
import type { HcamBaseMode, HcamMapBootstrap } from "../operations-contracts";
import { isDevelopmentBasemap, LOCAL_GUJARAT_STYLE, resolveOperationalStyle } from "../map-runtime";
import {
  buildGeometry,
  closeRing,
  drawReducer,
  initialDrawState,
  measure,
  type DrawAction,
  type DrawMode,
  type DrawProgress,
  type DrawResult,
  type DrawnShape,
} from "@hcam/gis-domain";

interface HcamOperationsMapProps {
  cameras: CameraFixture[];
  selectedCameraId: string | null;
  onCameraSelect: (camera: CameraFixture) => void;
  onViewportChange: (bounds: CameraBounds) => void;
  onMapViewportChange: (viewport: { longitude: number; latitude: number; zoom: number }) => void;
  inspectionPoint: [number, number] | null;
  onMapInspect: (coordinates: [number, number]) => void;
  viewMode: "2d" | "3d";
  baseMode: HcamBaseMode;
  mapBootstrap: HcamMapBootstrap | null;
  showCameraPositions: boolean;
  showCameraLabels: boolean;
  showCameraCoverage: boolean;
  drawMode: DrawMode | null;
  drawCommand: { action: DrawAction["type"]; seq: number } | null;
  mapViewCommand: {
    action: "reset-gujarat" | "focus-location";
    seq: number;
    coordinates?: [number, number];
    zoom?: number;
  } | null;
  drawnShapes: DrawnShape[];
  onDrawProgress: (progress: DrawProgress | null) => void;
  onDrawComplete: (result: DrawResult) => void;
  fullscreenMap: boolean;
  onPointerInfo: (pointer: { longitude: number; latitude: number; zoom: number }) => void;
  operationalAlerts: {
    id: string;
    cameraId: string;
    title: string;
    severity: "low" | "medium" | "high";
    coordinates: [number, number];
  }[];
  showAlertMarkers: boolean;
  selectedAlertId: string | null;
  selectedDistrictName: string | null;
  showDistricts: boolean;
  onAlertClick: (cameraId: string, alertId: string) => void;
  onDistrictSelect: (districtName: string) => void;
}

const CAMERA_SOURCE = "hcam-cameras";
const COVERAGE_SOURCE = "hcam-camera-coverage";
const DRAW_SOURCE = "hcam-drawings";
const DRAW_TEMP_SOURCE = "hcam-draw-temp";
const ALERT_SOURCE = "hcam-operational-alerts";
const REFERENCE_SOURCE = "hcam-gujarat-reference";
const CONTEXT_SOURCE = "hcam-local-operational-context";
const DISTRICT_SOURCE = "hcam-gujarat-districts";
const INSPECTION_SOURCE = "hcam-coordinate-inspection";
const STYLE_NOT_READY_MESSAGE = "Style is not done loading";
maplibregl.setWorkerUrl(mapLibreWorkerUrl);
// Derived from the locally packaged Gujarat district-boundary reference. This
// is intentionally tighter than the wider service package bounds so reset
// returns to the H-CAM operating area rather than an India/Gulf overview.
const GUJARAT_OPERATIONAL_BOUNDS: [[number, number], [number, number]] = [
  [68.177512, 20.119597],
  [74.476433, 24.712108],
];

interface StyleMutationRequirements {
  layers?: readonly string[];
  sources?: readonly string[];
}

function isGeoJSONSource(source: maplibregl.Source | undefined): source is GeoJSONSource {
  return Boolean(source && "setData" in source);
}

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null;
}

function featureProperty(feature: unknown, name: string): unknown {
  if (!isRecord(feature)) return undefined;
  const properties = feature.properties;
  return isRecord(properties) ? properties[name] : undefined;
}

function featurePoint(feature: unknown): [number, number] | null {
  if (!isRecord(feature)) return null;
  const geometry = feature.geometry;
  if (!isRecord(geometry) || geometry.type !== "Point") return null;
  const coordinates = geometry.coordinates;
  if (!Array.isArray(coordinates) || coordinates.length < 2) return null;
  const longitude: unknown = coordinates[0];
  const latitude: unknown = coordinates[1];
  return typeof longitude === "number" && typeof latitude === "number"
    ? [longitude, latitude]
    : null;
}

// Development-only operational context. This makes the map useful for layout
// and workflow testing without representing any external feed or real asset.
const LOCAL_OPERATIONAL_CONTEXT: GeoJSON.FeatureCollection = {
  type: "FeatureCollection",
  features: [
    {
      type: "Feature",
      properties: { kind: "asset", name: "Ops checkpoint · local" },
      geometry: { type: "Point", coordinates: [72.69, 23.01] },
    },
    {
      type: "Feature",
      properties: { kind: "asset", name: "Support unit · local" },
      geometry: { type: "Point", coordinates: [72.79, 21.22] },
    },
    {
      type: "Feature",
      properties: { kind: "asset", name: "Coordination post · local" },
      geometry: { type: "Point", coordinates: [70.73, 22.29] },
    },
  ],
};

// Gujarat district geometry is a locally packaged GeoJSON extract from the
// Government of India's Bharat Map Service. It is loaded from this H-CAM
// origin, not requested by the browser from a third-party map service.
const GUJARAT_DISTRICTS_PATH = "/gis/reference/gujarat-district-boundaries.geojson";
const GUJARAT_OPERATIONAL_CONTEXT_PATH = "/gis/reference/gujarat-operational-context.geojson";

export interface CameraBounds {
  minLon: number;
  minLat: number;
  maxLon: number;
  maxLat: number;
}

function toFeatureCollection(cameras: CameraFixture[]) {
  return {
    type: "FeatureCollection" as const,
    features: cameras.map((camera) => ({
      type: "Feature" as const,
      id: camera.id,
      geometry: { type: "Point" as const, coordinates: camera.coordinates },
      properties: { id: camera.id, name: camera.name, status: camera.status, zone: camera.zone },
    })),
  };
}

// Fixture-only sectors support interface testing. They are intentionally not
// inferred from camera type or metadata and must be replaced by approved H-CAM
// heading/FOV/range records before they can represent real coverage.
function toCoverageFeatureCollection(cameras: CameraFixture[]) {
  return {
    type: "FeatureCollection" as const,
    features: cameras.map((camera, index) => {
      const [longitude, latitude] = camera.coordinates;
      const heading = ((index * 47 + 25) * Math.PI) / 180;
      const halfAngle = (24 * Math.PI) / 180;
      const rangeKm = 0.62 + (index % 3) * 0.12;
      const endpoint = (angle: number): [number, number] => [
        longitude + (rangeKm * Math.sin(angle)) / (111.32 * Math.cos((latitude * Math.PI) / 180)),
        latitude + (rangeKm * Math.cos(angle)) / 110.57,
      ];
      const arc = [
        endpoint(heading - halfAngle),
        endpoint(heading - halfAngle / 2),
        endpoint(heading),
        endpoint(heading + halfAngle / 2),
        endpoint(heading + halfAngle),
      ];
      return {
        type: "Feature" as const,
        properties: { id: camera.id, status: camera.status },
        geometry: {
          type: "Polygon" as const,
          coordinates: [[camera.coordinates, ...arc, camera.coordinates]],
        },
      };
    }),
  };
}

export function GujaratOperationsMap({
  cameras,
  selectedCameraId,
  onCameraSelect,
  onViewportChange,
  onMapViewportChange,
  inspectionPoint,
  onMapInspect,
  viewMode,
  baseMode,
  mapBootstrap,
  showCameraPositions,
  showCameraLabels,
  showCameraCoverage,
  drawMode,
  drawCommand,
  mapViewCommand,
  drawnShapes,
  onDrawProgress,
  onDrawComplete,
  fullscreenMap,
  onPointerInfo,
  operationalAlerts,
  showAlertMarkers,
  selectedAlertId,
  selectedDistrictName,
  showDistricts,
  onAlertClick,
  onDistrictSelect,
}: HcamOperationsMapProps) {
  const mapElement = useRef<HTMLDivElement | null>(null);
  const mapRef = useRef<MapLibreMap | null>(null);
  const [mapReady, setMapReady] = useState(false);
  const [mapIssue, setMapIssue] = useState<string | null>(null);
  const [compactMap, setCompactMap] = useState(() => window.innerWidth <= 620);
  const camerasRef = useRef(cameras);
  const featureVisibilityRef = useRef({ positions: showCameraPositions, labels: showCameraLabels });
  const drawModeRef = useRef<DrawMode | null>(drawMode);
  const drawCallbacksRef = useRef({ onDrawProgress, onDrawComplete });
  const pointerCallbackRef = useRef(onPointerInfo);
  const cameraSelectCallbackRef = useRef(onCameraSelect);
  const boundsCallbackRef = useRef(onViewportChange);
  const mapViewportCallbackRef = useRef(onMapViewportChange);
  const inspectionCallbackRef = useRef(onMapInspect);
  const alertCallbackRef = useRef(onAlertClick);
  const districtCallbackRef = useRef(onDistrictSelect);
  const drawApplyRef = useRef<((action: DrawAction) => void) | null>(null);
  const lastDrawCommandRef = useRef(0);
  const lastMapViewCommandRef = useRef(0);
  const styleUrl = resolveOperationalStyle(
    window.location.hostname,
    mapBootstrap?.mapStyle.styleUrl,
  );
  useEffect(() => {
    camerasRef.current = cameras;
    featureVisibilityRef.current = { positions: showCameraPositions, labels: showCameraLabels };
    drawModeRef.current = drawMode;
    drawCallbacksRef.current = { onDrawProgress, onDrawComplete };
    pointerCallbackRef.current = onPointerInfo;
    mapViewportCallbackRef.current = onMapViewportChange;
    inspectionCallbackRef.current = onMapInspect;
    alertCallbackRef.current = onAlertClick;
    districtCallbackRef.current = onDistrictSelect;
    cameraSelectCallbackRef.current = onCameraSelect;
    boundsCallbackRef.current = onViewportChange;
  }, [
    cameras,
    drawMode,
    onAlertClick,
    onCameraSelect,
    onDistrictSelect,
    onDrawComplete,
    onDrawProgress,
    onMapInspect,
    onMapViewportChange,
    onPointerInfo,
    onViewportChange,
    showCameraLabels,
    showCameraPositions,
  ]);

  // MapLibre can briefly expose a map instance while replacing its style during
  // Fast Refresh. Calling layout/filter/source APIs in that window throws
  // "Style is not done loading" and Next renders it as a Turbopack error.
  // Every state-driven map change uses this gate so it either runs against the
  // current H-CAM style or retries once that style is ready. Other errors still
  // propagate instead of being hidden.
  const runWhenStyleReady = useCallback(
    (map: MapLibreMap, requirements: StyleMutationRequirements, mutation: () => void) => {
      const run = () => {
        if (mapRef.current !== map) return;
        if (!map.isStyleLoaded()) {
          map.once("style.load", run);
          return;
        }
        if (
          requirements.layers?.some((layerId) => !map.getLayer(layerId)) ||
          requirements.sources?.some((sourceId) => !map.getSource(sourceId))
        )
          return;
        try {
          mutation();
        } catch (error) {
          if (error instanceof Error && error.message.includes(STYLE_NOT_READY_MESSAGE)) {
            map.once("style.load", run);
            return;
          }
          throw error;
        }
      };
      run();
    },
    [],
  );

  useEffect(() => {
    if (!mapElement.current || mapRef.current) return;
    const developmentBasemap = isDevelopmentBasemap(styleUrl);
    let localFallbackApplied = false;
    const map = new maplibregl.Map({
      container: mapElement.current,
      // This path is H-CAM-owned.  It contains no provider URL and is replaced
      // by the locally served Gujarat style/archive in Phase 3.
      style: styleUrl,
      center: [72.4, 22.4],
      zoom: 6.4,
      minZoom: mapBootstrap?.mapStyle.minZoom ?? 4,
      maxZoom: mapBootstrap?.mapStyle.maxZoom ?? 18,
      attributionControl: false,
      // MapLibre passes source tile paths through Request in its worker.  A
      // browser Request requires an absolute URL, while our intentionally
      // local style uses root-relative H-CAM routes.  Resolve those routes at
      // the client boundary so /tiles, /gis/styles and /gis/reference remain
      // same-origin and never fall back to an external provider.
      transformRequest: (url: string) => ({ url: new URL(url, window.location.origin).toString() }),
    });
    map.addControl(new maplibregl.NavigationControl({ showCompass: true }), "bottom-right");
    if (developmentBasemap) {
      map.addControl(
        new maplibregl.AttributionControl({
          compact: true,
          customAttribution: "Development basemap: CARTO · OpenStreetMap",
        }),
        "bottom-left",
      );
    }
    mapRef.current = map;

    const activateLocalFallback = () => {
      if (!developmentBasemap || localFallbackApplied || map.isStyleLoaded()) return false;
      localFallbackApplied = true;
      map.setStyle(LOCAL_GUJARAT_STYLE);
      setMapIssue("Public development basemap unavailable. Local Gujarat reference is active.");
      return true;
    };
    const fallbackTimer = window.setTimeout(activateLocalFallback, 8_000);

    map.on("error", () => {
      if (activateLocalFallback()) return;
      setMapIssue(
        "A local map layer could not be rendered. Camera and district tables remain authoritative.",
      );
    });

    const initializeMap = () => {
      if (mapRef.current !== map || map.getSource(REFERENCE_SOURCE)) return;
      map.addSource(REFERENCE_SOURCE, {
        type: "geojson",
        data: new URL(GUJARAT_OPERATIONAL_CONTEXT_PATH, window.location.origin).toString(),
        attribution: "H-CAM local operational reference",
      });
      map.addLayer({
        id: "hcam-reference-corridors",
        type: "line",
        source: REFERENCE_SOURCE,
        filter: ["==", ["get", "kind"], "corridor"],
        paint: {
          "line-color": "#85a6ad",
          "line-width": ["interpolate", ["linear"], ["zoom"], 5, 0.9, 10, 2],
          "line-opacity": 0.76,
          "line-dasharray": [2, 1],
        },
      });
      map.addLayer({
        id: "hcam-reference-cities",
        type: "circle",
        source: REFERENCE_SOURCE,
        filter: ["==", ["get", "kind"], "city"],
        paint: {
          "circle-radius": ["interpolate", ["linear"], ["zoom"], 5, 2.8, 10, 5],
          "circle-color": "#c8e3df",
          "circle-stroke-color": "#071018",
          "circle-stroke-width": 1.4,
        },
      });
      map.addSource(DISTRICT_SOURCE, {
        type: "geojson",
        data: new URL(GUJARAT_DISTRICTS_PATH, window.location.origin).toString(),
      });
      map.addLayer({
        id: "hcam-district-fill",
        type: "fill",
        source: DISTRICT_SOURCE,
        paint: { "fill-color": "#e44c55", "fill-opacity": 0.018 },
      });
      map.addLayer({
        id: "hcam-district-lines",
        type: "line",
        source: DISTRICT_SOURCE,
        paint: {
          "line-color": "#ed5960",
          "line-width": 1.35,
          "line-opacity": 0.88,
          "line-dasharray": [1.15, 1.35],
        },
      });
      // District labels begin at a closer operational zoom. At the Gujarat-wide
      // overview, only the true boundary lines are shown so multi-part coastal
      // districts do not repeat their names across islands or enclaves.
      map.addLayer({
        id: "hcam-district-labels",
        type: "symbol",
        source: DISTRICT_SOURCE,
        minzoom: 8,
        layout: {
          "text-field": ["upcase", ["get", "dtname"]],
          "text-size": 8,
          "text-max-width": 12,
          "text-font": ["Open Sans Bold"],
          "text-allow-overlap": false,
        },
        paint: { "text-color": "#dc858a", "text-halo-color": "#060a0e", "text-halo-width": 1.25 },
      });
      map.addLayer({
        id: "hcam-district-selected-fill",
        type: "fill",
        source: DISTRICT_SOURCE,
        filter: ["==", ["get", "dtname"], ""],
        paint: { "fill-color": "#ff6970", "fill-opacity": 0.12 },
      });
      map.addLayer({
        id: "hcam-district-selected-outline",
        type: "line",
        source: DISTRICT_SOURCE,
        filter: ["==", ["get", "dtname"], ""],
        paint: { "line-color": "#ffd45a", "line-width": 2.6, "line-opacity": 1 },
      });
      map.addSource(CONTEXT_SOURCE, { type: "geojson", data: LOCAL_OPERATIONAL_CONTEXT });
      map.addLayer({
        id: "hcam-context-assets",
        type: "circle",
        source: CONTEXT_SOURCE,
        filter: ["==", ["get", "kind"], "asset"],
        paint: {
          "circle-radius": 5,
          "circle-color": "#0b161a",
          "circle-stroke-color": "#66cce1",
          "circle-stroke-width": 1.6,
        },
      });
      map.addLayer({
        id: "hcam-context-labels",
        type: "symbol",
        source: CONTEXT_SOURCE,
        minzoom: 6.1,
        layout: {
          "text-field": ["get", "name"],
          "text-size": 9,
          "text-offset": [0, 1.25],
          "text-anchor": "top",
          "text-font": ["Open Sans Regular"],
        },
        paint: { "text-color": "#7fb0b5", "text-halo-color": "#070b11", "text-halo-width": 1.2 },
      });
      map.addSource(INSPECTION_SOURCE, {
        type: "geojson",
        data: { type: "FeatureCollection", features: [] },
      });
      map.addLayer({
        id: "hcam-coordinate-inspection-ring",
        type: "circle",
        source: INSPECTION_SOURCE,
        paint: {
          "circle-radius": 10,
          "circle-color": "rgba(0,0,0,0)",
          "circle-stroke-color": "#e6c153",
          "circle-stroke-width": 1.8,
        },
      });
      map.addLayer({
        id: "hcam-coordinate-inspection-dot",
        type: "circle",
        source: INSPECTION_SOURCE,
        paint: {
          "circle-radius": 3.5,
          "circle-color": "#f5d25f",
          "circle-stroke-color": "#071018",
          "circle-stroke-width": 1.2,
        },
      });
      map.addSource(CAMERA_SOURCE, {
        type: "geojson",
        data: toFeatureCollection(camerasRef.current),
        cluster: true,
        clusterRadius: 46,
        clusterMaxZoom: 11,
      });
      map.addLayer({
        id: "hcam-camera-clusters",
        type: "circle",
        source: CAMERA_SOURCE,
        filter: ["has", "point_count"],
        paint: {
          "circle-radius": ["step", ["get", "point_count"], 15, 10, 19, 30, 24],
          "circle-color": "#163a3c",
          "circle-stroke-color": "#52caa0",
          "circle-stroke-width": 1.5,
          "circle-opacity": 0.96,
        },
      });
      map.addLayer({
        id: "hcam-camera-cluster-count",
        type: "symbol",
        source: CAMERA_SOURCE,
        filter: ["has", "point_count"],
        layout: {
          "text-field": ["get", "point_count_abbreviated"],
          "text-size": 11,
          "text-font": ["Open Sans Bold"],
        },
        paint: { "text-color": "#e7fff2" },
      });
      map.addLayer({
        id: "hcam-camera-halo",
        type: "circle",
        source: CAMERA_SOURCE,
        filter: ["!", ["has", "point_count"]],
        paint: {
          "circle-radius": 13,
          "circle-color": [
            "match",
            ["get", "status"],
            "online",
            "#38e58b",
            "degraded",
            "#f5bc4d",
            "maintenance",
            "#72a7ff",
            "#f36c6c",
          ],
          "circle-opacity": 0.18,
        },
      });
      map.addLayer({
        id: "hcam-camera-points",
        type: "circle",
        source: CAMERA_SOURCE,
        filter: ["!", ["has", "point_count"]],
        paint: {
          "circle-radius": 6,
          "circle-stroke-width": 2,
          "circle-stroke-color": "#071018",
          "circle-color": [
            "match",
            ["get", "status"],
            "online",
            "#38e58b",
            "degraded",
            "#f5bc4d",
            "maintenance",
            "#72a7ff",
            "#f36c6c",
          ],
        },
      });
      map.addLayer({
        id: "hcam-camera-labels",
        type: "symbol",
        source: CAMERA_SOURCE,
        minzoom: 7,
        filter: ["!", ["has", "point_count"]],
        layout: {
          "text-field": ["get", "name"],
          "text-size": 11,
          "text-offset": [0, 1.35],
          "text-anchor": "top",
          "text-font": ["Open Sans Regular"],
        },
        paint: { "text-color": "#d9e8e5", "text-halo-color": "#071018", "text-halo-width": 1.5 },
      });
      map.addLayer({
        id: "hcam-camera-selected-ring",
        type: "circle",
        source: CAMERA_SOURCE,
        filter: ["==", ["get", "id"], ""],
        paint: {
          "circle-radius": 16,
          "circle-color": "rgba(0,0,0,0)",
          "circle-stroke-color": "#65fff1",
          "circle-stroke-width": 2.1,
          "circle-stroke-opacity": 0.95,
        },
      });
      map.addLayer({
        id: "hcam-camera-selected-label",
        type: "symbol",
        source: CAMERA_SOURCE,
        filter: ["==", ["get", "id"], ""],
        layout: {
          "text-field": "ACTIVE CAMERA",
          "text-size": 8,
          "text-offset": [0, -2.2],
          "text-anchor": "bottom",
          "text-font": ["Open Sans Bold"],
          "text-letter-spacing": 0.08,
        },
        paint: { "text-color": "#9cfff7", "text-halo-color": "#071018", "text-halo-width": 1.4 },
      });
      map.addSource(COVERAGE_SOURCE, {
        type: "geojson",
        data: toCoverageFeatureCollection(camerasRef.current),
      });
      map.addLayer({
        id: "hcam-camera-coverage-fill",
        type: "fill",
        source: COVERAGE_SOURCE,
        paint: {
          "fill-color": [
            "match",
            ["get", "status"],
            "online",
            "#38e58b",
            "degraded",
            "#f5bc4d",
            "maintenance",
            "#72a7ff",
            "#f36c6c",
          ],
          "fill-opacity": 0.11,
        },
      });
      map.addLayer({
        id: "hcam-camera-coverage-line",
        type: "line",
        source: COVERAGE_SOURCE,
        paint: {
          "line-color": [
            "match",
            ["get", "status"],
            "online",
            "#4ff3a0",
            "degraded",
            "#f5bc4d",
            "maintenance",
            "#83b4ff",
            "#f36c6c",
          ],
          "line-width": 1.1,
          "line-opacity": 0.72,
        },
      });
      map.addSource(ALERT_SOURCE, {
        type: "geojson",
        data: { type: "FeatureCollection", features: [] },
      });
      map.addLayer({
        id: "hcam-alert-markers",
        type: "symbol",
        source: ALERT_SOURCE,
        layout: {
          "text-field": "▲",
          "text-size": ["match", ["get", "severity"], "high", 23, "medium", 21, 19],
          "text-font": ["Open Sans Bold"],
          "text-allow-overlap": true,
          "text-ignore-placement": true,
        },
        paint: {
          "text-color": [
            "match",
            ["get", "severity"],
            "high",
            "#f04d32",
            "medium",
            "#f5a83d",
            "#72a7ff",
          ],
          "text-halo-color": "#060a0e",
          "text-halo-width": 1.8,
        },
      });
      map.addLayer({
        id: "hcam-alert-labels",
        type: "symbol",
        source: ALERT_SOURCE,
        minzoom: 6.1,
        layout: {
          "text-field": ["upcase", ["get", "title"]],
          "text-size": 8.5,
          "text-offset": [0, 1.5],
          "text-anchor": "top",
          "text-font": ["Open Sans Bold"],
          "text-max-width": 13,
          "text-allow-overlap": false,
        },
        paint: {
          "text-color": [
            "match",
            ["get", "severity"],
            "high",
            "#ef624c",
            "medium",
            "#f3b45a",
            "#9bbcff",
          ],
          "text-halo-color": "#060a0e",
          "text-halo-width": 1.5,
        },
      });
      map.addLayer({
        id: "hcam-alert-selected-ring",
        type: "circle",
        source: ALERT_SOURCE,
        filter: ["==", ["get", "id"], ""],
        paint: {
          "circle-radius": 18,
          "circle-color": "rgba(0, 0, 0, 0)",
          "circle-stroke-color": "#5dfff0",
          "circle-stroke-width": 2,
          "circle-stroke-opacity": 0.9,
        },
      });
      const openAlertCamera = (event: MapLayerMouseEvent) => {
        const feature = event.features?.[0];
        const cameraId = featureProperty(feature, "cameraId");
        const alertId = featureProperty(feature, "id");
        if (typeof cameraId === "string" && typeof alertId === "string")
          alertCallbackRef.current(cameraId, alertId);
      };
      map.on("mouseenter", "hcam-alert-markers", () => {
        map.getCanvas().style.cursor = "pointer";
      });
      map.on("mouseleave", "hcam-alert-markers", () => {
        map.getCanvas().style.cursor = "";
      });
      map.on("click", "hcam-alert-markers", openAlertCamera);
      const featureVisibility = featureVisibilityRef.current;
      const compact = (mapElement.current?.clientWidth ?? window.innerWidth) <= 620;
      const cameraLayers = [
        "hcam-camera-clusters",
        "hcam-camera-cluster-count",
        "hcam-camera-halo",
        "hcam-camera-points",
        "hcam-camera-selected-ring",
        "hcam-camera-selected-label",
      ];
      const coverageLayers = ["hcam-camera-coverage-fill", "hcam-camera-coverage-line"];
      const districtLayers = [
        "hcam-district-fill",
        "hcam-district-lines",
        "hcam-district-labels",
        "hcam-district-selected-fill",
        "hcam-district-selected-outline",
      ];
      runWhenStyleReady(
        map,
        { layers: [...cameraLayers, "hcam-camera-labels", ...coverageLayers, ...districtLayers] },
        () => {
          cameraLayers.forEach((layerId) =>
            map.setLayoutProperty(
              layerId,
              "visibility",
              featureVisibility.positions ? "visible" : "none",
            ),
          );
          map.setLayoutProperty(
            "hcam-camera-labels",
            "visibility",
            featureVisibility.positions && featureVisibility.labels && !compact
              ? "visible"
              : "none",
          );
          coverageLayers.forEach((layerId) =>
            map.setLayoutProperty(layerId, "visibility", showCameraCoverage ? "visible" : "none"),
          );
          districtLayers.forEach((layerId) =>
            map.setLayoutProperty(layerId, "visibility", showDistricts ? "visible" : "none"),
          );
        },
      );
      map.on("mouseenter", "hcam-district-lines", () => {
        if (!drawModeRef.current) map.getCanvas().style.cursor = "pointer";
      });
      map.on("mouseleave", "hcam-district-lines", () => {
        if (!drawModeRef.current) map.getCanvas().style.cursor = "";
      });
      map.on("click", "hcam-district-lines", (event: MapLayerMouseEvent) => {
        if (drawModeRef.current) return;
        const districtName = featureProperty(event.features?.[0], "dtname");
        if (typeof districtName === "string") districtCallbackRef.current(districtName);
      });
      map.on("mouseenter", "hcam-camera-points", () => {
        map.getCanvas().style.cursor = "pointer";
      });
      map.on("mouseleave", "hcam-camera-points", () => {
        map.getCanvas().style.cursor = "";
      });
      map.on("click", "hcam-camera-points", (event: MapLayerMouseEvent) => {
        if (drawModeRef.current) return;
        const id = featureProperty(event.features?.[0], "id");
        if (typeof id !== "string") return;
        const camera = camerasRef.current.find((item) => item.id === id);
        if (camera) cameraSelectCallbackRef.current(camera);
      });
      map.on("click", "hcam-camera-clusters", (event: MapLayerMouseEvent) => {
        if (drawModeRef.current) return;
        const feature = event.features?.[0];
        const clusterId = featureProperty(feature, "cluster_id");
        const source = map.getSource(CAMERA_SOURCE);
        const coordinates = featurePoint(feature);
        if (typeof clusterId !== "number" || !isGeoJSONSource(source) || !coordinates) return;
        void source.getClusterExpansionZoom(clusterId).then((zoom) => {
          map.easeTo({ center: coordinates, zoom, duration: 450 });
        });
      });
      map.on("click", (event: MapMouseEvent) => {
        if (drawModeRef.current) return;
        const occupied = map.queryRenderedFeatures(event.point, {
          layers: [
            "hcam-camera-clusters",
            "hcam-camera-points",
            "hcam-alert-markers",
            "hcam-district-lines",
          ],
        });
        if (!occupied.length) inspectionCallbackRef.current([event.lngLat.lng, event.lngLat.lat]);
      });
      const reportBounds = () => {
        const currentBounds = map.getBounds();
        boundsCallbackRef.current({
          minLon: currentBounds.getWest(),
          minLat: currentBounds.getSouth(),
          maxLon: currentBounds.getEast(),
          maxLat: currentBounds.getNorth(),
        });
        const center = map.getCenter();
        mapViewportCallbackRef.current({
          longitude: center.lng,
          latitude: center.lat,
          zoom: map.getZoom(),
        });
      };
      reportBounds();
      map.on("moveend", reportBounds);
      map.on("mousemove", (event: MapMouseEvent) =>
        pointerCallbackRef.current({
          longitude: event.lngLat.lng,
          latitude: event.lngLat.lat,
          zoom: map.getZoom(),
        }),
      );
      pointerCallbackRef.current({
        longitude: map.getCenter().lng,
        latitude: map.getCenter().lat,
        zoom: map.getZoom(),
      });
      setMapIssue(null);
      setMapReady(true);
      window.clearTimeout(fallbackTimer);
    };
    if (map.isStyleLoaded()) initializeMap();
    else map.once("style.load", initializeMap);
    return () => {
      window.clearTimeout(fallbackTimer);
      map.remove();
      mapRef.current = null;
      setMapReady(false);
    };
  }, [
    mapBootstrap?.mapStyle.maxZoom,
    mapBootstrap?.mapStyle.minZoom,
    runWhenStyleReady,
    showCameraCoverage,
    showDistricts,
    styleUrl,
  ]);

  useEffect(() => {
    const map = mapRef.current;
    if (!mapReady || !map) return;
    runWhenStyleReady(map, { sources: [INSPECTION_SOURCE] }, () => {
      const source = map.getSource(INSPECTION_SOURCE);
      if (isGeoJSONSource(source))
        void source.setData({
          type: "FeatureCollection",
          features: inspectionPoint
            ? [
                {
                  type: "Feature",
                  properties: {},
                  geometry: { type: "Point", coordinates: inspectionPoint },
                },
              ]
            : [],
        });
    });
  }, [inspectionPoint, mapReady, runWhenStyleReady]);

  useEffect(() => {
    const map = mapRef.current;
    if (!map) return;
    runWhenStyleReady(map, { sources: [CAMERA_SOURCE, COVERAGE_SOURCE] }, () => {
      const cameraSource = map.getSource(CAMERA_SOURCE);
      const coverageSource = map.getSource(COVERAGE_SOURCE);
      if (isGeoJSONSource(cameraSource)) void cameraSource.setData(toFeatureCollection(cameras));
      if (isGeoJSONSource(coverageSource))
        void coverageSource.setData(toCoverageFeatureCollection(cameras));
    });
  }, [cameras, runWhenStyleReady]);

  useEffect(() => {
    const map = mapRef.current;
    if (!map) return;
    // Basemap themes and imagery are intentionally unavailable until local map
    // archives are installed.  Do not add an external fallback here.
    runWhenStyleReady(map, {}, () =>
      map.easeTo({
        pitch: viewMode === "3d" ? 54 : 0,
        bearing: viewMode === "3d" ? -18 : 0,
        duration: 520,
        essential: true,
      }),
    );
  }, [baseMode, runWhenStyleReady, viewMode]);

  useEffect(() => {
    const map = mapRef.current;
    if (!map) return;
    const cameraLayerIds = [
      "hcam-camera-clusters",
      "hcam-camera-cluster-count",
      "hcam-camera-halo",
      "hcam-camera-points",
      "hcam-camera-selected-ring",
      "hcam-camera-selected-label",
    ];
    runWhenStyleReady(map, { layers: [...cameraLayerIds, "hcam-camera-labels"] }, () => {
      cameraLayerIds.forEach((layerId) =>
        map.setLayoutProperty(layerId, "visibility", showCameraPositions ? "visible" : "none"),
      );
      map.setLayoutProperty(
        "hcam-camera-labels",
        "visibility",
        showCameraPositions && showCameraLabels && !compactMap ? "visible" : "none",
      );
    });
  }, [compactMap, runWhenStyleReady, showCameraLabels, showCameraPositions]);

  useEffect(() => {
    const map = mapRef.current;
    if (!map) return;
    const coverageLayers = ["hcam-camera-coverage-fill", "hcam-camera-coverage-line"];
    runWhenStyleReady(map, { layers: coverageLayers }, () =>
      coverageLayers.forEach((layerId) =>
        map.setLayoutProperty(layerId, "visibility", showCameraCoverage ? "visible" : "none"),
      ),
    );
  }, [runWhenStyleReady, showCameraCoverage]);

  useEffect(() => {
    const map = mapRef.current;
    if (!map) return;
    const districtLayers = [
      "hcam-district-fill",
      "hcam-district-lines",
      "hcam-district-selected-fill",
      "hcam-district-selected-outline",
    ];
    runWhenStyleReady(map, { layers: [...districtLayers, "hcam-district-labels"] }, () => {
      districtLayers.forEach((layerId) =>
        map.setLayoutProperty(layerId, "visibility", showDistricts ? "visible" : "none"),
      );
      map.setLayoutProperty(
        "hcam-district-labels",
        "visibility",
        showDistricts && !compactMap ? "visible" : "none",
      );
    });
  }, [compactMap, runWhenStyleReady, showDistricts]);

  useEffect(() => {
    const map = mapRef.current;
    if (!mapReady || !map) return;
    const filter = [
      "==",
      ["get", "dtname"],
      selectedDistrictName ?? "",
    ] as maplibregl.FilterSpecification;
    runWhenStyleReady(
      map,
      { layers: ["hcam-district-selected-fill", "hcam-district-selected-outline"] },
      () => {
        map.setFilter("hcam-district-selected-fill", filter);
        map.setFilter("hcam-district-selected-outline", filter);
      },
    );
  }, [mapReady, runWhenStyleReady, selectedDistrictName]);

  useEffect(() => {
    const map = mapRef.current;
    if (!mapReady || !map) return;
    const features = drawnShapes.map((shape) => ({
      ...shape.geojson,
      properties: { id: shape.id, color: shape.color, name: shape.name, kind: shape.kind },
    }));
    const data: GeoJSON.FeatureCollection = { type: "FeatureCollection", features };
    runWhenStyleReady(map, {}, () => {
      const source = map.getSource(DRAW_SOURCE);
      if (isGeoJSONSource(source)) {
        void source.setData(data);
        return;
      }
      map.addSource(DRAW_SOURCE, { type: "geojson", data });
      map.addLayer({
        id: "hcam-draw-fill",
        type: "fill",
        source: DRAW_SOURCE,
        filter: ["==", "$type", "Polygon"],
        paint: { "fill-color": ["get", "color"], "fill-opacity": 0.16 },
      });
      map.addLayer({
        id: "hcam-draw-line",
        type: "line",
        source: DRAW_SOURCE,
        paint: { "line-color": ["get", "color"], "line-width": 2.3, "line-opacity": 0.95 },
      });
    });
  }, [drawnShapes, mapReady, runWhenStyleReady]);

  useEffect(() => {
    const map = mapRef.current;
    if (!mapReady || !map) return;
    const data: GeoJSON.FeatureCollection = {
      type: "FeatureCollection",
      features: operationalAlerts.map((alert) => ({
        type: "Feature",
        properties: {
          id: alert.id,
          cameraId: alert.cameraId,
          title: alert.title,
          severity: alert.severity,
        },
        geometry: { type: "Point", coordinates: alert.coordinates },
      })),
    };
    const alertLayers = ["hcam-alert-markers", "hcam-alert-selected-ring"];
    runWhenStyleReady(
      map,
      { layers: [...alertLayers, "hcam-alert-labels"], sources: [ALERT_SOURCE] },
      () => {
        const source = map.getSource(ALERT_SOURCE);
        if (isGeoJSONSource(source)) void source.setData(data);
        alertLayers.forEach((layerId) =>
          map.setLayoutProperty(layerId, "visibility", showAlertMarkers ? "visible" : "none"),
        );
        map.setLayoutProperty(
          "hcam-alert-labels",
          "visibility",
          showAlertMarkers && !compactMap ? "visible" : "none",
        );
      },
    );
  }, [compactMap, mapReady, operationalAlerts, runWhenStyleReady, showAlertMarkers]);

  useEffect(() => {
    const map = mapRef.current;
    if (!mapReady || !map) return;
    runWhenStyleReady(map, { layers: ["hcam-alert-selected-ring"] }, () =>
      map.setFilter("hcam-alert-selected-ring", ["==", ["get", "id"], selectedAlertId ?? ""]),
    );
  }, [mapReady, runWhenStyleReady, selectedAlertId]);

  useEffect(() => {
    const map = mapRef.current;
    if (!mapReady || !map) return;
    let disposed = false;
    const removeTemp = () => {
      ["hcam-draw-temp-points", "hcam-draw-temp-line", "hcam-draw-temp-fill"].forEach((id) => {
        if (map.getLayer(id)) map.removeLayer(id);
      });
      if (map.getSource(DRAW_TEMP_SOURCE)) map.removeSource(DRAW_TEMP_SOURCE);
    };
    let cleanup: (() => void) | undefined;
    runWhenStyleReady(map, {}, () => {
      if (disposed) return;
      if (!drawMode) {
        removeTemp();
        drawApplyRef.current = null;
        drawCallbacksRef.current.onDrawProgress(null);
        map.getCanvas().style.cursor = "";
        return;
      }
      removeTemp();
      map.addSource(DRAW_TEMP_SOURCE, {
        type: "geojson",
        data: { type: "FeatureCollection", features: [] },
      });
      map.addLayer({
        id: "hcam-draw-temp-fill",
        type: "fill",
        source: DRAW_TEMP_SOURCE,
        filter: ["==", "$type", "Polygon"],
        paint: { "fill-color": "#00e5ff", "fill-opacity": 0.14 },
      });
      map.addLayer({
        id: "hcam-draw-temp-line",
        type: "line",
        source: DRAW_TEMP_SOURCE,
        paint: { "line-color": "#00e5ff", "line-width": 2.2, "line-dasharray": [2, 1] },
      });
      map.addLayer({
        id: "hcam-draw-temp-points",
        type: "circle",
        source: DRAW_TEMP_SOURCE,
        filter: ["==", "$type", "Point"],
        paint: {
          "circle-radius": 4,
          "circle-color": "#e7fffc",
          "circle-stroke-color": "#00bfc5",
          "circle-stroke-width": 1.5,
        },
      });
      map.getCanvas().style.cursor = "crosshair";
      let state = initialDrawState(drawMode);
      const render = (cursor?: [number, number]) => {
        const previewPoints =
          cursor && state.points.length ? [...state.points, cursor] : state.points;
        const geometryPoints = buildGeometry(drawMode, previewPoints);
        const features: GeoJSON.Feature[] = state.points.map((coordinates) => ({
          type: "Feature",
          properties: {},
          geometry: { type: "Point", coordinates },
        }));
        if (geometryPoints.length >= 2)
          features.push({
            type: "Feature",
            properties: {},
            geometry:
              drawMode === "line"
                ? { type: "LineString", coordinates: geometryPoints }
                : { type: "Polygon", coordinates: [closeRing(geometryPoints)] },
          });
        const source = map.getSource(DRAW_TEMP_SOURCE);
        if (isGeoJSONSource(source)) void source.setData({ type: "FeatureCollection", features });
        drawCallbacksRef.current.onDrawProgress(
          state.points.length ? measure(drawMode, previewPoints) : null,
        );
      };
      const apply = (action: DrawAction) => {
        const transition = drawReducer(state, action);
        state = transition.state;
        render();
        if (transition.result) drawCallbacksRef.current.onDrawComplete(transition.result);
        if (transition.cancelled) drawCallbacksRef.current.onDrawProgress(null);
      };
      const onClick = (event: maplibregl.MapMouseEvent) =>
        apply({ type: "click", at: [event.lngLat.lng, event.lngLat.lat] });
      const onDoubleClick = (event: maplibregl.MapMouseEvent) => {
        event.preventDefault();
        apply({ type: "dblclick" });
      };
      const onMove = (event: maplibregl.MapMouseEvent) =>
        render([event.lngLat.lng, event.lngLat.lat]);
      const onKeyDown = (event: KeyboardEvent) => {
        if (event.key === "Escape") apply({ type: "cancel" });
        if (event.key === "Enter") apply({ type: "finish" });
        if (event.key === "Backspace") {
          event.preventDefault();
          apply({ type: "undo" });
        }
      };
      drawApplyRef.current = apply;
      map.on("click", onClick);
      map.on("dblclick", onDoubleClick);
      map.on("mousemove", onMove);
      window.addEventListener("keydown", onKeyDown);
      render();
      cleanup = () => {
        map.off("click", onClick);
        map.off("dblclick", onDoubleClick);
        map.off("mousemove", onMove);
        window.removeEventListener("keydown", onKeyDown);
        drawApplyRef.current = null;
        map.getCanvas().style.cursor = "";
        removeTemp();
      };
    });
    return () => {
      disposed = true;
      cleanup?.();
    };
  }, [drawMode, mapReady, runWhenStyleReady]);

  useEffect(() => {
    if (!drawCommand || drawCommand.seq === lastDrawCommandRef.current) return;
    lastDrawCommandRef.current = drawCommand.seq;
    drawApplyRef.current?.({ type: drawCommand.action } as DrawAction);
  }, [drawCommand]);

  useEffect(() => {
    if (!mapViewCommand || mapViewCommand.seq === lastMapViewCommandRef.current) return;
    const map = mapRef.current;
    if (!map) return;
    runWhenStyleReady(map, {}, () => {
      lastMapViewCommandRef.current = mapViewCommand.seq;
      if (mapViewCommand.action === "focus-location" && mapViewCommand.coordinates) {
        map.flyTo({
          center: mapViewCommand.coordinates,
          zoom: mapViewCommand.zoom ?? 10,
          duration: 700,
          essential: true,
        });
        return;
      }
      // The application sidebar is outside this map element. Equal padding
      // keeps Gujarat centred within the actual map canvas; the former large
      // left-only inset pushed every reset noticeably to the right.
      map.fitBounds(GUJARAT_OPERATIONAL_BOUNDS, { padding: 72, duration: 700, essential: true });
    });
  }, [mapReady, mapViewCommand, runWhenStyleReady]);

  useEffect(() => {
    const map = mapRef.current;
    if (map) requestAnimationFrame(() => map.resize());
  }, [fullscreenMap]);

  useEffect(() => {
    const map = mapRef.current;
    const container = mapElement.current;
    if (!map || !container || typeof ResizeObserver === "undefined") return undefined;
    let frame = 0;
    const observer = new ResizeObserver(() => {
      cancelAnimationFrame(frame);
      frame = requestAnimationFrame(() => {
        setCompactMap(container.clientWidth <= 620);
        map.resize();
      });
    });
    observer.observe(container);
    return () => {
      cancelAnimationFrame(frame);
      observer.disconnect();
    };
  }, [mapReady]);

  useEffect(() => {
    const map = mapRef.current;
    if (!map) return;
    const filter = ["==", ["get", "id"], selectedCameraId ?? ""] as maplibregl.FilterSpecification;
    runWhenStyleReady(
      map,
      { layers: ["hcam-camera-halo", "hcam-camera-selected-ring", "hcam-camera-selected-label"] },
      () => {
        map.setPaintProperty("hcam-camera-halo", "circle-stroke-width", 0);
        map.setFilter("hcam-camera-selected-ring", filter);
        map.setFilter("hcam-camera-selected-label", filter);
        if (selectedCameraId) {
          const selected = cameras.find((camera) => camera.id === selectedCameraId);
          if (selected)
            map.flyTo({
              center: selected.coordinates,
              zoom: Math.max(map.getZoom(), 10),
              duration: 650,
              essential: true,
            });
        }
      },
    );
  }, [cameras, runWhenStyleReady, selectedCameraId]);

  return (
    <>
      <div
        className="hcam-map"
        ref={mapElement}
        aria-label="Interactive H-CAM camera operations map"
      />
      {mapIssue ? (
        <p className="hcam-map-issue" role="status">
          {mapIssue}
        </p>
      ) : null}
    </>
  );
}
