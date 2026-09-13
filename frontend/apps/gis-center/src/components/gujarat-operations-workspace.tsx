import { useCallback, useEffect, useMemo, useState, type ReactNode } from "react";
import {
  Activity,
  BellRing,
  Box,
  ChevronDown,
  ChevronLeft,
  ChevronRight,
  CircleAlert,
  CircleHelp,
  Copy,
  Database,
  Filter,
  Layers3,
  ListFilter,
  LoaderCircle,
  Map as MapIcon,
  MapPinned,
  Maximize2,
  Menu,
  Minimize2,
  Moon,
  PencilRuler,
  RotateCcw,
  Route,
  Search,
  ShieldCheck,
  Satellite,
  Video,
  Wrench,
  X,
} from "lucide-react";
import type { ResourceProfile } from "@hcam/capabilities";
import type { GisRendererMode } from "@hcam/gis-contracts";
import {
  admitRenderer,
  toShape,
  type DrawMode,
  type DrawProgress,
  type DrawResult,
  type DrawnShape,
} from "@hcam/gis-domain";
import { GujaratOperationsMap, type CameraBounds } from "./gujarat-operations-map";
import { GujaratDrawingTools } from "./gujarat-drawing-tools";
import {
  HCAM_CAMERA_FIXTURES,
  type CameraFixture,
  type CameraStatus,
  type PreviewAvailability,
} from "../operations-fixtures";
import type { AlertSummary, HcamBaseMode, HcamMapBootstrap } from "../operations-contracts";
import { DEVELOPMENT_BASEMAP_STYLE, isLoopbackHostname, LOCAL_GUJARAT_STYLE } from "../map-runtime";

const STATUS_LABELS: Record<CameraStatus, string> = {
  online: "Operational",
  degraded: "Degraded",
  maintenance: "Maintenance",
  offline: "Offline",
};
const STATUS_ORDER: CameraStatus[] = ["online", "degraded", "maintenance", "offline"];
const INITIAL_BOUNDS: CameraBounds = { minLon: 68, minLat: 20, maxLon: 75, maxLat: 25 };
type CatalogueState = "loading" | "ready" | "error";
type PreviewState = "not-requested" | "authorizing" | PreviewAvailability;
type SidebarSection = "catalogue" | "status" | "layers" | "alerts" | "access" | "display";
type MapUtilityPanel = "search" | "data" | "places" | "help" | null;
type IncidentLifecycle = "new" | "acknowledged" | "investigating" | "resolved";
type AlertQueueMode = "open" | "resolved" | "all";
type AlertSeverity = OperationalAlert["severity"];
type AlertTimeWindow = "all" | "15m" | "30m";
const ALERT_SEVERITIES: AlertSeverity[] = ["high", "medium", "low"];
const OPERATIONAL_PLACES = [
  {
    id: "ahmedabad",
    label: "Ahmedabad operations",
    detail: "Central camera operations area",
    coordinates: [72.5714, 23.0225] as [number, number],
    zoom: 10.4,
  },
  {
    id: "gandhinagar",
    label: "Gandhinagar operations",
    detail: "North Gujarat coordination area",
    coordinates: [72.6369, 23.2156] as [number, number],
    zoom: 10.4,
  },
  {
    id: "vadodara",
    label: "Vadodara operations",
    detail: "East corridor operations area",
    coordinates: [73.1812, 22.3072] as [number, number],
    zoom: 10.1,
  },
  {
    id: "surat",
    label: "Surat operations",
    detail: "South Gujarat operations area",
    coordinates: [72.8311, 21.1702] as [number, number],
    zoom: 10.1,
  },
  {
    id: "rajkot",
    label: "Rajkot operations",
    detail: "Saurashtra operations area",
    coordinates: [70.8022, 22.3039] as [number, number],
    zoom: 10.1,
  },
  {
    id: "bhavnagar",
    label: "Bhavnagar operations",
    detail: "Coastal operations area",
    coordinates: [72.1407, 21.7645] as [number, number],
    zoom: 10.1,
  },
] as const;

type OperationalAlert = AlertSummary;

export function GujaratOperationsWorkspace() {
  const [activeStatuses, setActiveStatuses] = useState<CameraStatus[]>(STATUS_ORDER);
  const [query, setQuery] = useState("");
  const [bounds, setBounds] = useState<CameraBounds>(INITIAL_BOUNDS);
  const [selectedCameraId, setSelectedCameraId] = useState<string | null>(null);
  const [selectedDistrictName, setSelectedDistrictName] = useState<string | null>(null);
  const [selectedAlertId, setSelectedAlertId] = useState<string | null>(null);
  const [alertLifecycle, setAlertLifecycle] = useState<Record<string, IncidentLifecycle>>({});
  const [alertQueueMode, setAlertQueueMode] = useState<AlertQueueMode>("open");
  const [activeAlertSeverities, setActiveAlertSeverities] =
    useState<AlertSeverity[]>(ALERT_SEVERITIES);
  const [alertTimeWindow, setAlertTimeWindow] = useState<AlertTimeWindow>("all");
  const [detailRailOpen, setDetailRailOpen] = useState(false);
  const [localRole, setLocalRole] = useState<"viewer" | "operator">("viewer");
  const [fixtureClock] = useState(Date.now);
  const alerts = useMemo(() => generatedOperationalAlerts(fixtureClock), [fixtureClock]);
  const [viewMode, setViewMode] = useState<"2d" | "3d">("2d");
  const [baseMode, setBaseMode] = useState<HcamBaseMode>("dark");
  const [mapBootstrap] = useState(generatedMapBootstrap);
  const [activeSidebarSection, setActiveSidebarSection] = useState<SidebarSection>("catalogue");
  const [sidebarOpen, setSidebarOpen] = useState(
    () =>
      typeof window === "undefined" ||
      typeof window.matchMedia !== "function" ||
      !window.matchMedia("(max-width: 620px)").matches,
  );
  const [dashboardMenuOpen, setDashboardMenuOpen] = useState(false);
  const [, setFeaturePanelOpen] = useState(false);
  const [showCameraPositions, setShowCameraPositions] = useState(true);
  const [showCameraLabels, setShowCameraLabels] = useState(true);
  const [showCameraCoverage, setShowCameraCoverage] = useState(false);
  const [showOperationalOverlay, setShowOperationalOverlay] = useState(true);
  const [showDistricts, setShowDistricts] = useState(true);
  // Keep the map clear at startup. The drawing workspace is opened deliberately
  // from either tool rail, where it takes the catalogue's place instead of
  // competing with it for the same narrow operational column.
  const [drawingPanelOpen, setDrawingPanelOpen] = useState(false);

  useEffect(() => {
    if (typeof window.matchMedia !== "function") return undefined;
    const narrowViewport = window.matchMedia("(max-width: 620px)");
    const collapseForNarrowViewport = (event: MediaQueryListEvent | MediaQueryList) => {
      if (event.matches) setSidebarOpen(false);
    };
    collapseForNarrowViewport(narrowViewport);
    narrowViewport.addEventListener("change", collapseForNarrowViewport);
    return () => narrowViewport.removeEventListener("change", collapseForNarrowViewport);
  }, []);
  const [drawMode, setDrawMode] = useState<DrawMode | null>(null);
  const [drawProgress, setDrawProgress] = useState<DrawProgress | null>(null);
  const [drawnShapes, setDrawnShapes] = useState<DrawnShape[]>([]);
  const [drawCommand, setDrawCommand] = useState<{
    action: "undo" | "finish" | "cancel";
    seq: number;
  } | null>(null);
  const [mapViewCommand, setMapViewCommand] = useState<{
    action: "reset-gujarat" | "focus-location";
    seq: number;
    coordinates?: [number, number];
    zoom?: number;
  } | null>(initialMapViewCommand);
  const [clock, setClock] = useState(Date.now);
  const [mapUtilityPanel, setMapUtilityPanel] = useState<MapUtilityPanel>(null);
  const [mapControlsOpen, setMapControlsOpen] = useState(true);
  const [fullscreenMap, setFullscreenMap] = useState(false);
  const [mapPointer, setMapPointer] = useState({ longitude: 72.4, latitude: 22.4, zoom: 6.4 });
  const [mapViewport, setMapViewport] = useState({ longitude: 72.4, latitude: 22.4, zoom: 6.4 });
  const [shareStatus, setShareStatus] = useState("");
  const [inspectionPoint, setInspectionPoint] = useState<[number, number] | null>(null);
  const [resourceProfile, setResourceProfile] = useState<ResourceProfile>("enhanced");
  const [rendererMode, setRendererMode] = useState<GisRendererMode>("maplibre");

  const rendererAdmission = admitRenderer({
    requested: rendererMode,
    profile: resourceProfile,
    webgl: typeof WebGLRenderingContext !== "undefined",
    webgl2: typeof WebGL2RenderingContext !== "undefined",
    policyAllowed: true,
    healthy: true,
  });

  useEffect(() => {
    const timer = window.setInterval(() => setClock(Date.now()), 1000);
    return () => window.clearInterval(timer);
  }, []);
  useEffect(() => {
    const onKeyDown = (event: KeyboardEvent) => {
      if (
        event.target instanceof HTMLInputElement ||
        event.target instanceof HTMLTextAreaElement ||
        event.target instanceof HTMLSelectElement
      )
        return;
      if (event.key.toLowerCase() === "f") toggleFullscreenMap();
      if (event.key.toLowerCase() === "d") {
        setFullscreenMap(false);
        setDrawingPanelOpen(true);
        setFeaturePanelOpen(false);
      }
      if (event.key.toLowerCase() === "s") {
        setFullscreenMap(false);
        setMapUtilityPanel("search");
      }
      if (event.key.toLowerCase() === "h")
        setMapUtilityPanel((panel) => (panel === "help" ? null : "help"));
      if (event.key.toLowerCase() === "r") resetGujaratView();
      if (event.key === "Escape") {
        // Escape is deliberately non-destructive: it only clears temporary UI
        // context, never filters, local role, map layers, or saved drawings.
        setMapUtilityPanel(null);
        setFeaturePanelOpen(false);
        setDrawingPanelOpen(false);
        setDrawMode(null);
        setInspectionPoint(null);
        setShareStatus("");
        clearMapSelection();
        dispatchDrawCommand("cancel");
      }
    };
    window.addEventListener("keydown", onKeyDown);
    return () => window.removeEventListener("keydown", onKeyDown);
  });

  const cameras = useMemo(() => {
    const normalizedQuery = query.trim().toLowerCase();
    return HCAM_CAMERA_FIXTURES.filter(
      (camera) =>
        activeStatuses.includes(camera.status) &&
        camera.coordinates[0] >= bounds.minLon &&
        camera.coordinates[0] <= bounds.maxLon &&
        camera.coordinates[1] >= bounds.minLat &&
        camera.coordinates[1] <= bounds.maxLat &&
        (!normalizedQuery ||
          `${camera.name} ${camera.zone} ${camera.id}`.toLowerCase().includes(normalizedQuery)),
    );
  }, [activeStatuses, bounds, query]);
  const statusCounts = useMemo(
    () =>
      STATUS_ORDER.reduce<Record<CameraStatus, number>>(
        (counts, status) => {
          counts[status] = HCAM_CAMERA_FIXTURES.filter((camera) => camera.status === status).length;
          return counts;
        },
        { online: 0, degraded: 0, maintenance: 0, offline: 0 },
      ),
    [],
  );
  const [catalogueState] = useState<CatalogueState>("ready");

  const selectedCamera = useMemo(
    () => cameras.find((camera) => camera.id === selectedCameraId) ?? null,
    [cameras, selectedCameraId],
  );
  const selectedAlert = useMemo(
    () => alerts.find((alert) => alert.id === selectedAlertId) ?? null,
    [alerts, selectedAlertId],
  );
  const selectedAlertLifecycle = selectedAlert
    ? (alertLifecycle[selectedAlert.id] ?? "new")
    : "new";
  const openAlertCount = useMemo(
    () => alerts.filter((alert) => (alertLifecycle[alert.id] ?? "new") !== "resolved").length,
    [alerts, alertLifecycle],
  );
  const resolvedAlertCount = alerts.length - openAlertCount;
  const queueAlerts = useMemo(
    () =>
      alerts.filter(
        (alert) =>
          alertQueueMode === "all" ||
          (alertQueueMode === "resolved"
            ? (alertLifecycle[alert.id] ?? "new") === "resolved"
            : (alertLifecycle[alert.id] ?? "new") !== "resolved"),
      ),
    [alerts, alertLifecycle, alertQueueMode],
  );
  const visibleAlerts = useMemo(
    () =>
      queueAlerts
        .filter((alert) => activeAlertSeverities.includes(alert.severity))
        .filter((alert) => isWithinAlertWindow(alert.observedAtUtc, alertTimeWindow, clock)),
    [activeAlertSeverities, alertTimeWindow, clock, queueAlerts],
  );
  const alertSeverityCounts = useMemo(
    () =>
      Object.fromEntries(
        ALERT_SEVERITIES.map((severity) => [
          severity,
          queueAlerts.filter((alert) => alert.severity === severity).length,
        ]),
      ) as Record<AlertSeverity, number>,
    [queueAlerts],
  );
  const highestPriorityAlert = useMemo(
    () =>
      visibleAlerts
        .slice()
        .sort((left, right) => alertPriority(left.severity) - alertPriority(right.severity))[0] ??
      null,
    [visibleAlerts],
  );
  const handleCameraSelect = useCallback((camera: CameraFixture) => {
    setSelectedCameraId(camera.id);
    setDetailRailOpen(true);
  }, []);
  const handleViewportChange = useCallback((nextBounds: CameraBounds) => setBounds(nextBounds), []);
  const handleMapViewportChange = useCallback(
    (nextViewport: { longitude: number; latitude: number; zoom: number }) =>
      setMapViewport(nextViewport),
    [],
  );
  const operationalCount = statusCounts.online;
  const attentionCount = statusCounts.degraded + statusCounts.maintenance + statusCounts.offline;
  const activeStatusSummary =
    activeStatuses.length === STATUS_ORDER.length
      ? "All operational states"
      : activeStatuses.length
        ? `${activeStatuses.length} of ${STATUS_ORDER.length} states shown`
        : "No camera states shown";
  const cameraCountInAreas = useMemo(
    () =>
      Object.fromEntries(
        drawnShapes
          .filter((shape) => shape.geojson.geometry.type === "Polygon")
          .map((shape) => [
            shape.id,
            cameras.filter((camera) =>
              pointIsInRing(
                camera.coordinates,
                shape.geojson.geometry.coordinates[0] as number[][],
              ),
            ).length,
          ]),
      ),
    [cameras, drawnShapes],
  );
  const mapAlerts = useMemo(
    () =>
      visibleAlerts.flatMap((alert) => {
        const camera = cameras.find((item) => item.id === alert.cameraId);
        return camera
          ? [
              {
                id: alert.id,
                cameraId: alert.cameraId,
                title: alert.title,
                severity: alert.severity,
                coordinates: alert.coordinates ?? camera.coordinates,
              },
            ]
          : [];
      }),
    [visibleAlerts, cameras],
  );
  const nearbyCameras = useMemo(
    () =>
      !selectedCamera
        ? []
        : cameras
            .filter((camera) => camera.id !== selectedCamera.id)
            .sort(
              (left, right) =>
                distanceSquared(selectedCamera.coordinates, left.coordinates) -
                distanceSquared(selectedCamera.coordinates, right.coordinates),
            )
            .slice(0, 3),
    [cameras, selectedCamera],
  );
  const alertNearbyCameras = useMemo(() => {
    if (!selectedAlert) return [];
    const selectedCameraCoordinates = cameras.find(
      (camera) => camera.id === selectedAlert.cameraId,
    )?.coordinates;
    const origin = selectedAlert.coordinates ?? selectedCameraCoordinates;
    if (!origin) return [];
    return cameras
      .slice()
      .sort(
        (left, right) =>
          distanceSquared(origin, left.coordinates) - distanceSquared(origin, right.coordinates),
      )
      .slice(0, 3);
  }, [cameras, selectedAlert]);
  const inspectionNearbyCameras = useMemo(
    () =>
      !inspectionPoint
        ? []
        : cameras
            .slice()
            .sort(
              (left, right) =>
                distanceSquared(inspectionPoint, left.coordinates) -
                distanceSquared(inspectionPoint, right.coordinates),
            )
            .slice(0, 3),
    [cameras, inspectionPoint],
  );
  const selectedDistrictCameras = useMemo(
    () =>
      selectedDistrictName
        ? cameras.filter((camera) => belongsToDistrict(camera.zone, selectedDistrictName))
        : [],
    [cameras, selectedDistrictName],
  );
  const selectedDistrictAlerts = useMemo(
    () =>
      selectedDistrictName
        ? alerts.filter((alert) => belongsToDistrict(alert.detail, selectedDistrictName))
        : [],
    [alerts, selectedDistrictName],
  );
  const selectionContext = useMemo(() => {
    if (selectedAlert)
      return {
        kind: "Alert focus",
        label: selectedAlert.title,
        detail: `${selectedAlert.severity} priority · ${selectedAlertLifecycle}`,
      };
    if (selectedDistrictName)
      return {
        kind: "District territory",
        label: selectedDistrictName,
        detail: `${selectedDistrictCameras.length} cameras · ${selectedDistrictAlerts.length} alerts`,
      };
    if (selectedCamera)
      return {
        kind: "Camera focus",
        label: selectedCamera.name,
        detail: `${selectedCamera.zone} · ${STATUS_LABELS[selectedCamera.status]}`,
      };
    return null;
  }, [
    selectedAlert,
    selectedAlertLifecycle,
    selectedCamera,
    selectedDistrictAlerts.length,
    selectedDistrictCameras.length,
    selectedDistrictName,
  ]);
  const activeMapLayers = useMemo(
    () =>
      [
        showCameraPositions ? "Cameras" : null,
        showOperationalOverlay ? "Alerts" : null,
        showDistricts ? "Districts" : null,
        showCameraLabels ? "Labels" : null,
        showCameraCoverage ? "Sectors" : null,
      ].filter((layer): layer is string => Boolean(layer)),
    [
      showCameraCoverage,
      showCameraLabels,
      showCameraPositions,
      showDistricts,
      showOperationalOverlay,
    ],
  );
  const sidebarPanelTitle: Record<SidebarSection, { eyebrow: string; title: string }> = {
    catalogue: { eyebrow: "Camera catalogue", title: "Operational view" },
    status: { eyebrow: "Camera status", title: "Filter the map" },
    layers: { eyebrow: "Map layers", title: "Operational visibility" },
    alerts: { eyebrow: "Operational alerts", title: "Priority queue" },
    access: { eyebrow: "Preview access", title: "Operator policy" },
    display: { eyebrow: "Map display", title: "Presentation controls" },
  };

  function toggleStatus(status: CameraStatus) {
    setActiveStatuses((current) =>
      current.includes(status) ? current.filter((value) => value !== status) : [...current, status],
    );
  }

  function focusSidebarSection(section: SidebarSection) {
    setActiveSidebarSection(section);
    setSidebarOpen(true);
    setDashboardMenuOpen(false);
    setFeaturePanelOpen(false);
    setDrawingPanelOpen(false);
  }

  function selectAlert(alert: OperationalAlert) {
    setSelectedAlertId(alert.id);
    setSelectedCameraId(alert.cameraId);
    setDetailRailOpen(true);
  }

  function setAlertLifecycleState(alertId: string, lifecycle: IncidentLifecycle) {
    setAlertLifecycle((current) => ({ ...current, [alertId]: lifecycle }));
  }

  function toggleAlertSeverity(severity: AlertSeverity) {
    setActiveAlertSeverities((current) =>
      current.includes(severity)
        ? current.filter((value) => value !== severity)
        : [...current, severity],
    );
  }

  const completeDrawing = useCallback((result: DrawResult) => {
    setDrawnShapes((current) => [...current, toShape(result, current, current.length)]);
    setDrawMode(null);
    setDrawProgress(null);
  }, []);

  function dispatchDrawCommand(action: "undo" | "finish" | "cancel") {
    setDrawCommand((current) => ({ action, seq: (current?.seq ?? 0) + 1 }));
  }
  function resetGujaratView() {
    setMapViewCommand((current) => ({ action: "reset-gujarat", seq: (current?.seq ?? 0) + 1 }));
  }
  function focusOperationalPlace(place: (typeof OPERATIONAL_PLACES)[number]) {
    clearMapSelection();
    setMapViewCommand((current) => ({
      action: "focus-location",
      seq: (current?.seq ?? 0) + 1,
      coordinates: place.coordinates,
      zoom: place.zoom,
    }));
    setMapUtilityPanel(null);
  }
  async function copyCurrentMapView() {
    const url = new URL(window.location.href);
    url.search = "";
    url.searchParams.set("lon", mapViewport.longitude.toFixed(5));
    url.searchParams.set("lat", mapViewport.latitude.toFixed(5));
    url.searchParams.set("zoom", mapViewport.zoom.toFixed(2));
    window.history.replaceState(null, "", url);
    try {
      await navigator.clipboard.writeText(url.toString());
      setShareStatus("View link copied");
    } catch {
      setShareStatus("View link is in the address bar");
    }
  }
  async function copyInspectionCoordinate() {
    if (!inspectionPoint) return;
    const value = `${inspectionPoint[1].toFixed(5)}, ${inspectionPoint[0].toFixed(5)}`;
    try {
      await navigator.clipboard.writeText(value);
      setShareStatus("Coordinate copied");
    } catch {
      setShareStatus(`Coordinate: ${value}`);
    }
  }
  function clearMapSelection() {
    setSelectedAlertId(null);
    setSelectedDistrictName(null);
    setSelectedCameraId(null);
    setDetailRailOpen(false);
  }
  function restoreOperationalView() {
    setActiveStatuses(STATUS_ORDER);
    setQuery("");
    setAlertQueueMode("open");
    setActiveAlertSeverities(ALERT_SEVERITIES);
    setAlertTimeWindow("all");
    setShowCameraPositions(true);
    setShowOperationalOverlay(true);
    setShowDistricts(true);
    setShowCameraLabels(true);
    setShowCameraCoverage(false);
    setViewMode("2d");
    setBaseMode("dark");
    setMapUtilityPanel(null);
    setFeaturePanelOpen(false);
    setDrawingPanelOpen(false);
    setDrawMode(null);
    dispatchDrawCommand("cancel");
    clearMapSelection();
    resetGujaratView();
  }
  function toggleFullscreenMap() {
    if (!fullscreenMap) {
      setFeaturePanelOpen(false);
      setDashboardMenuOpen(false);
      setDrawingPanelOpen(false);
      setMapUtilityPanel(null);
      setSidebarOpen(false);
      setDrawMode(null);
      dispatchDrawCommand("cancel");
    }
    setFullscreenMap((value) => !value);
  }

  return (
    <section
      className={`hcam-operations-root hcam-shell${fullscreenMap ? " is-map-fullscreen" : ""}`}
      aria-label="Gujarat operational map"
    >
      <section
        className={`hcam-workspace${sidebarOpen ? "" : " is-sidebar-collapsed"}${detailRailOpen ? " has-detail" : ""}`}
        aria-label="H-CAM map workspace"
      >
        <aside
          className={`hcam-sidebar-shell${sidebarOpen ? "" : " is-collapsed"}`}
          aria-label="H-CAM operational navigation"
        >
          <nav className="hcam-icon-rail" aria-label="Operational panels">
            <button
              className={`hcam-rail-mark hcam-dashboard-trigger${dashboardMenuOpen ? " is-active" : ""}`}
              type="button"
              onClick={() => setDashboardMenuOpen((open) => !open)}
              aria-label={
                dashboardMenuOpen ? "Close dashboard switcher" : "Open dashboard switcher"
              }
              aria-expanded={dashboardMenuOpen}
              title="Switch dashboard"
            >
              <Menu size={18} />
            </button>
            {dashboardMenuOpen ? (
              <section className="hcam-dashboard-menu" aria-label="H-CAM dashboard switcher">
                <div className="hcam-dashboard-menu-heading">
                  <span>GIS workspaces</span>
                  <button
                    type="button"
                    onClick={() => setDashboardMenuOpen(false)}
                    aria-label="Close GIS workspace switcher"
                  >
                    <X size={14} />
                  </button>
                </div>
                <button
                  className="hcam-dashboard-entry is-active"
                  type="button"
                  onClick={() => setDashboardMenuOpen(false)}
                >
                  <MapPinned size={15} />
                  <span>
                    <strong>Gujarat operations map</strong>
                    <small>Current workspace</small>
                  </span>
                  <em>Active</em>
                </button>
                <button
                  className="hcam-dashboard-entry"
                  type="button"
                  onClick={() => {
                    window.location.assign("/gis/health");
                  }}
                >
                  <ShieldCheck size={15} />
                  <span>
                    <strong>Data and renderer health</strong>
                    <small>Source boundaries and diagnostics</small>
                  </span>
                </button>
                <button
                  className="hcam-dashboard-entry"
                  type="button"
                  onClick={() => {
                    window.location.assign("/gis/review");
                  }}
                >
                  <Activity size={15} />
                  <span>
                    <strong>Alerts and investigations</strong>
                    <small>Connected specialist view</small>
                  </span>
                </button>
              </section>
            ) : null}
            <div className="hcam-rail-footer hcam-rail-footer-top">
              <button
                className="hcam-rail-button hcam-sidebar-toggle"
                type="button"
                onClick={() => setSidebarOpen((open) => !open)}
                aria-label={
                  sidebarOpen
                    ? "Collapse camera operations panel"
                    : "Expand camera operations panel"
                }
                aria-expanded={sidebarOpen}
                title={sidebarOpen ? "Collapse panel" : "Expand panel"}
              >
                {sidebarOpen ? <ChevronLeft size={16} /> : <ChevronRight size={16} />}
              </button>
            </div>
            <div className="hcam-rail-actions">
              <RailButton
                label="Camera catalogue"
                active={activeSidebarSection === "catalogue"}
                badge={cameras.length}
                onClick={() => focusSidebarSection("catalogue")}
              >
                <Video size={17} />
              </RailButton>
              <RailButton
                label="Camera status filters"
                active={activeSidebarSection === "status"}
                onClick={() => focusSidebarSection("status")}
              >
                <ListFilter size={17} />
              </RailButton>
              <RailButton
                label="H-CAM layer controls"
                active={activeSidebarSection === "layers"}
                onClick={() => focusSidebarSection("layers")}
              >
                <Layers3 size={17} />
              </RailButton>
              <RailButton
                label="Operational alerts"
                active={activeSidebarSection === "alerts"}
                badge={alerts.length}
                onClick={() => focusSidebarSection("alerts")}
              >
                <BellRing size={17} />
              </RailButton>
              <RailButton
                label="Preview access policy"
                active={activeSidebarSection === "access"}
                onClick={() => focusSidebarSection("access")}
              >
                <ShieldCheck size={17} />
              </RailButton>
              <RailButton
                label="Map display controls"
                active={activeSidebarSection === "display"}
                onClick={() => focusSidebarSection("display")}
              >
                <MapPinned size={17} />
              </RailButton>
            </div>
          </nav>
          {drawingPanelOpen ? (
            <GujaratDrawingTools
              mode={drawMode}
              progress={drawProgress}
              shapes={drawnShapes}
              cameraCountInAreas={cameraCountInAreas}
              onSetMode={setDrawMode}
              onCommand={dispatchDrawCommand}
              onRename={(id, name) =>
                setDrawnShapes((current) =>
                  current.map((shape) => (shape.id === id ? { ...shape, name } : shape)),
                )
              }
              onDelete={(id) =>
                setDrawnShapes((current) => current.filter((shape) => shape.id !== id))
              }
              onClear={() => setDrawnShapes([])}
              onExport={() => exportDrawings(drawnShapes)}
              onClose={() => {
                setDrawingPanelOpen(false);
                setDrawMode(null);
                dispatchDrawCommand("cancel");
              }}
            />
          ) : null}
          <div
            className={`hcam-sidebar hcam-sidebar-panel panel-${activeSidebarSection}`}
            id="hcam-sidebar-panel"
            aria-label={`${sidebarPanelTitle[activeSidebarSection].eyebrow} panel`}
          >
            <div className="hcam-panel-heading">
              <div>
                <p className="hcam-eyebrow">{sidebarPanelTitle[activeSidebarSection].eyebrow}</p>
                <h1>{sidebarPanelTitle[activeSidebarSection].title}</h1>
              </div>
              <span className="hcam-count">
                {catalogueState === "loading" ? (
                  <LoaderCircle size={14} className="hcam-spin" />
                ) : activeSidebarSection === "alerts" ? (
                  alerts.length
                ) : activeSidebarSection === "layers" ? (
                  5
                ) : (
                  cameras.length
                )}
              </span>
            </div>
            {activeSidebarSection === "catalogue" ? (
              <>
                <label className="hcam-search">
                  <Search size={16} aria-hidden="true" />
                  <input
                    value={query}
                    onChange={(event) => setQuery(event.target.value)}
                    placeholder="Search cameras or zones"
                    aria-label="Search cameras or zones"
                  />
                </label>
                <div className="hcam-panel-note">
                  <Video size={14} />
                  <span>
                    Select a visible camera to inspect its authorised operational details.
                  </span>
                </div>
                <div className="hcam-camera-list">
                  {cameras.slice(0, 7).map((camera) => (
                    <button
                      type="button"
                      key={camera.id}
                      onClick={() => handleCameraSelect(camera)}
                    >
                      <span className={`hcam-status-dot status-${camera.status}`} />
                      <span>
                        <strong>{camera.name}</strong>
                        <small>
                          {camera.zone} · {camera.id}
                        </small>
                      </span>
                      <ChevronRight size={14} />
                    </button>
                  ))}
                </div>
              </>
            ) : null}

            {activeSidebarSection === "status" ? (
              <div className="hcam-layer-section">
                <div className="hcam-section-title">
                  <Filter size={14} aria-hidden="true" />
                  <span>Operational status</span>
                  <small>{activeStatuses.length}/4</small>
                </div>
                <div className="hcam-status-overview" aria-label="Camera status summary">
                  <div>
                    <span className="hcam-status-dot status-online" />
                    <strong>{operationalCount}</strong>
                    <small>operational</small>
                  </div>
                  <div>
                    <span className="hcam-status-dot status-degraded" />
                    <strong>{attentionCount}</strong>
                    <small>need review</small>
                  </div>
                </div>
                <div
                  className="hcam-status-presets"
                  role="group"
                  aria-label="Camera status filter presets"
                >
                  <button
                    className={activeStatuses.length === STATUS_ORDER.length ? "is-active" : ""}
                    type="button"
                    onClick={() => setActiveStatuses(STATUS_ORDER)}
                  >
                    All states
                  </button>
                  <button
                    className={activeStatuses.includes("online") ? "" : "is-active"}
                    type="button"
                    onClick={() => setActiveStatuses(["degraded", "maintenance", "offline"])}
                  >
                    Needs review
                  </button>
                  <button
                    className={activeStatuses.length === 0 ? "is-active" : ""}
                    type="button"
                    onClick={() => setActiveStatuses([])}
                  >
                    Clear
                  </button>
                </div>
                {STATUS_ORDER.map((status) => (
                  <label className="hcam-filter" key={status}>
                    <input
                      checked={activeStatuses.includes(status)}
                      onChange={() => toggleStatus(status)}
                      type="checkbox"
                    />
                    <span className={`hcam-status-dot status-${status}`} />
                    <span>{STATUS_LABELS[status]}</span>
                    <small>{statusCounts[status]}</small>
                  </label>
                ))}
                <p className="hcam-panel-note">
                  {activeStatusSummary}. Use <strong>All states</strong> if a restrictive filter
                  makes the map appear empty.
                </p>
              </div>
            ) : null}

            {activeSidebarSection === "layers" ? (
              <div className="hcam-layer-section">
                <div className="hcam-section-title">
                  <Layers3 size={14} aria-hidden="true" />
                  <span>Map details</span>
                </div>
                <div className="hcam-layer-palette">
                  <LayerTile
                    label="Cameras"
                    detail="Registry locations"
                    active={showCameraPositions}
                    tone="camera"
                    onClick={() => setShowCameraPositions((value) => !value)}
                  />
                  <LayerTile
                    label="Alerts"
                    detail={`${alerts.length} local events`}
                    active={showOperationalOverlay}
                    tone="alert"
                    onClick={() => setShowOperationalOverlay((value) => !value)}
                  />
                  <LayerTile
                    label="Districts"
                    detail="Gujarat boundaries"
                    active={showDistricts}
                    tone="territory"
                    onClick={() => setShowDistricts((value) => !value)}
                  />
                  <LayerTile
                    label="Labels"
                    detail="Camera names"
                    active={showCameraLabels}
                    tone="label"
                    onClick={() => setShowCameraLabels((value) => !value)}
                  />
                  <LayerTile
                    label="Coverage"
                    detail="Local test sectors"
                    active={showCameraCoverage}
                    tone="coverage"
                    onClick={() => setShowCameraCoverage((value) => !value)}
                  />
                </div>
                <MapLegend />
                <p className="hcam-panel-note">
                  District borders use the locally packaged Gujarat extract from the Government of
                  India Bharat Map Service. Coverage sectors are local planning geometry only; they
                  are not approved camera field-of-view data.
                </p>
              </div>
            ) : null}
            {activeSidebarSection === "alerts" ? (
              <div className="hcam-layer-section">
                <div className="hcam-section-title">
                  <Activity size={14} aria-hidden="true" />
                  <span>Operational alerts</span>
                  <small>
                    {openAlertCount}/{alerts.length}
                  </small>
                </div>
                {alerts.length ? (
                  <>
                    <div
                      className="hcam-alert-queue-controls"
                      role="group"
                      aria-label="Operational alert queue"
                    >
                      <button
                        className={alertQueueMode === "open" ? "is-active" : ""}
                        type="button"
                        onClick={() => setAlertQueueMode("open")}
                      >
                        Open {openAlertCount}
                      </button>
                      <button
                        className={alertQueueMode === "resolved" ? "is-active" : ""}
                        type="button"
                        onClick={() => setAlertQueueMode("resolved")}
                      >
                        Resolved {resolvedAlertCount}
                      </button>
                      <button
                        className={alertQueueMode === "all" ? "is-active" : ""}
                        type="button"
                        onClick={() => setAlertQueueMode("all")}
                      >
                        All {alerts.length}
                      </button>
                    </div>
                    <div
                      className="hcam-alert-time-controls"
                      role="group"
                      aria-label="Alert time window"
                    >
                      <span>Fixture recency</span>
                      {(
                        [
                          { id: "all", label: "All" },
                          { id: "15m", label: "15 min" },
                          { id: "30m", label: "30 min" },
                        ] as const
                      ).map((window) => (
                        <button
                          className={alertTimeWindow === window.id ? "is-active" : ""}
                          type="button"
                          key={window.id}
                          aria-pressed={alertTimeWindow === window.id}
                          onClick={() => setAlertTimeWindow(window.id)}
                        >
                          {window.label}
                        </button>
                      ))}
                    </div>
                    <div
                      className="hcam-alert-severity-controls"
                      role="group"
                      aria-label="Alert severity filters"
                    >
                      <span>Priority</span>
                      {ALERT_SEVERITIES.map((severity) => (
                        <button
                          className={`severity-${severity}${activeAlertSeverities.includes(severity) ? " is-active" : ""}`}
                          type="button"
                          key={severity}
                          aria-pressed={activeAlertSeverities.includes(severity)}
                          onClick={() => toggleAlertSeverity(severity)}
                        >
                          <i />
                          <span>{severity}</span>
                          <em>{alertSeverityCounts[severity]}</em>
                        </button>
                      ))}
                      <button
                        className="hcam-alert-severity-reset"
                        type="button"
                        onClick={() => setActiveAlertSeverities(ALERT_SEVERITIES)}
                      >
                        Reset
                      </button>
                    </div>
                    <button
                      className="hcam-alert-focus-priority"
                      type="button"
                      disabled={!highestPriorityAlert}
                      onClick={() => {
                        if (highestPriorityAlert) selectAlert(highestPriorityAlert);
                      }}
                    >
                      <CircleAlert size={13} />
                      <span>Focus highest priority</span>
                      <strong>
                        {highestPriorityAlert ? highestPriorityAlert.severity : "none"}
                      </strong>
                    </button>
                    {selectedAlert &&
                    activeAlertSeverities.includes(selectedAlert.severity) &&
                    isWithinAlertWindow(selectedAlert.observedAtUtc, alertTimeWindow, Date.now()) &&
                    (alertQueueMode === "all" ||
                      (alertQueueMode === "resolved"
                        ? selectedAlertLifecycle === "resolved"
                        : selectedAlertLifecycle !== "resolved")) ? (
                      <AlertFocusCard
                        alert={selectedAlert}
                        lifecycle={selectedAlertLifecycle}
                        localRole={localRole}
                        nearbyCameras={alertNearbyCameras}
                        onCameraSelect={handleCameraSelect}
                        onLifecycleChange={(lifecycle) =>
                          setAlertLifecycleState(selectedAlert.id, lifecycle)
                        }
                        onClear={() => setSelectedAlertId(null)}
                      />
                    ) : null}
                    {visibleAlerts.length ? (
                      <div className="hcam-alert-list">
                        {visibleAlerts.map((alert) => (
                          <button
                            className={`hcam-alert alert-${alert.severity}${selectedAlertId === alert.id ? " is-active" : ""}${(alertLifecycle[alert.id] ?? "new") === "resolved" ? " is-resolved" : ""}`}
                            type="button"
                            key={alert.id}
                            onClick={() => selectAlert(alert)}
                          >
                            <strong>{alert.title}</strong>
                            <span>
                              {alert.detail} ·{" "}
                              {(alertLifecycle[alert.id] ?? "new") === "resolved"
                                ? "Resolved · "
                                : ""}
                              {alert.observedAt}
                            </span>
                          </button>
                        ))}
                      </div>
                    ) : (
                      <p className="hcam-empty-alerts">
                        No {alertQueueMode === "resolved" ? "resolved" : "open"} alerts match the
                        selected priority and recency filters.
                      </p>
                    )}
                    <p className="hcam-panel-note">
                      Fixture recency uses generated local UTC timestamps. Production alerts must
                      provide recorded UTC event time from the H-CAM GIS API.
                    </p>
                  </>
                ) : (
                  <p className="hcam-empty-alerts">No local operational alerts.</p>
                )}
              </div>
            ) : null}
            {activeSidebarSection === "access" ? (
              <section className="hcam-access-workspace">
                <div className={`hcam-access-summary role-${localRole}`}>
                  <div>
                    <span>Current workspace access</span>
                    <strong>
                      {localRole === "operator" ? "Operator policy" : "Viewer policy"}
                    </strong>
                    <small>
                      {localRole === "operator"
                        ? "Authorised preview requests may be evaluated server-side."
                        : "Safe registry metadata only."}
                    </small>
                  </div>
                  <ShieldCheck size={18} aria-hidden="true" />
                </div>
                <label className="hcam-role">
                  <span>Local role mode</span>
                  <select
                    value={localRole}
                    onChange={(event) => setLocalRole(event.target.value as "viewer" | "operator")}
                    aria-label="Local role mode"
                  >
                    <option value="viewer">Viewer — metadata only</option>
                    <option value="operator">Operator — policy requests</option>
                  </select>
                </label>
                <dl className="hcam-access-capabilities">
                  <div>
                    <dt>Camera details</dt>
                    <dd>Allowed</dd>
                  </div>
                  <div>
                    <dt>Live preview</dt>
                    <dd>{localRole === "operator" ? "Request only" : "Not available"}</dd>
                  </div>
                  <div>
                    <dt>Scope</dt>
                    <dd>H-CAM · Gujarat</dd>
                  </div>
                </dl>
                <div className="hcam-panel-note">
                  <ShieldCheck size={14} />
                  <span>
                    {localRole === "operator"
                      ? "A preview is never opened from map data alone. H-CAM must verify camera entitlement and issue a short-lived authorisation first."
                      : "Viewer mode can inspect safe camera metadata, health, alerts, and local map layers. It cannot request a media preview."}
                  </span>
                </div>
                <p className="hcam-access-boundary">
                  No stream URL, credential, provider locator, or media token is stored in this map
                  workspace.
                </p>
              </section>
            ) : null}
            {activeSidebarSection === "display" ? (
              <>
                <div className="hcam-display-summary">
                  <MapIcon size={14} aria-hidden="true" />
                  <span>Current display</span>
                  <strong>
                    {viewMode.toUpperCase()} ·{" "}
                    {baseMode === "map" ? "Map" : baseMode === "dark" ? "Dark" : "Satellite"}
                  </strong>
                </div>
                <div className="hcam-display-config-grid">
                  <label className="hcam-profile-select">
                    <span>Resource profile</span>
                    <select
                      value={resourceProfile}
                      onChange={(event) =>
                        setResourceProfile(event.currentTarget.value as ResourceProfile)
                      }
                      aria-label="Operational map resource profile"
                    >
                      <option value="low_resource">Low resource</option>
                      <option value="enhanced">Enhanced</option>
                      <option value="control_room">Control room</option>
                      <option value="future_server">Future server</option>
                    </select>
                  </label>
                  <label className="hcam-profile-select">
                    <span>Renderer</span>
                    <select
                      value={rendererMode}
                      onChange={(event) =>
                        setRendererMode(event.currentTarget.value as GisRendererMode)
                      }
                      aria-label="Operational map renderer"
                    >
                      <option value="maplibre">MapLibre</option>
                      <option value="deck_overlaid">deck.gl overlay</option>
                      <option value="deck_interleaved">deck.gl interleaved</option>
                      <option value="list_only">List only</option>
                    </select>
                  </label>
                </div>
                <div className="hcam-display-summary hcam-renderer-admission">
                  <Activity size={14} aria-hidden="true" />
                  <span>Active renderer</span>
                  <strong>{rendererAdmission.mode.replace("_", " ")}</strong>
                </div>
                <div className="hcam-panel-actions">
                  <button
                    className={viewMode === "2d" ? "is-active" : ""}
                    type="button"
                    onClick={() => setViewMode("2d")}
                  >
                    2D map
                  </button>
                  <button
                    className={viewMode === "3d" ? "is-active" : ""}
                    type="button"
                    onClick={() => setViewMode("3d")}
                  >
                    Pitched view
                  </button>
                  <button
                    className={baseMode === "dark" ? "is-active" : ""}
                    type="button"
                    onClick={() => setBaseMode("dark")}
                  >
                    Dark mode
                  </button>
                  <button
                    className={baseMode === "map" ? "is-active" : ""}
                    type="button"
                    onClick={() => setBaseMode("map")}
                  >
                    Map mode
                  </button>
                  <button
                    className="hcam-panel-action-wide hcam-panel-action-restore"
                    type="button"
                    onClick={restoreOperationalView}
                  >
                    Restore operational view <kbd>R</kbd>
                  </button>
                </div>
                <p className="hcam-panel-note">
                  Pitched view changes perspective only; no terrain-elevation source is active.
                  Restore clears local selections and filters without changing authority or writing
                  data.
                </p>
              </>
            ) : null}
            <p className="hcam-data-boundary">
              {mapBootstrap.mapStyle.styleUrl === DEVELOPMENT_BASEMAP_STYLE
                ? "CARTO/OpenStreetMap provides the public development basemap; H-CAM overlays remain generated."
                : mapBootstrap.sources.basemap.state === "unavailable"
                  ? "Local Gujarat basemap is unavailable. Public map providers are disabled."
                  : "H-CAM local map package is active."}{" "}
              Camera catalogue data is authorised metadata only; no feeds, stream URLs, credentials,
              or external CCTV sources are loaded.
            </p>
          </div>
        </aside>

        <div className="hcam-map-frame">
          {rendererAdmission.mode === "list_only" ? (
            <div
              className="hcam-list-only-map"
              role="region"
              aria-label="Authoritative list-only operational map fallback"
            >
              <MapPinned size={36} aria-hidden="true" />
              <h2>Map renderer is not admitted</h2>
              <p>The complete generated camera catalogue remains available without WebGL.</p>
              <div>
                {cameras.map((camera) => (
                  <button type="button" key={camera.id} onClick={() => handleCameraSelect(camera)}>
                    <span className={`hcam-status-dot status-${camera.status}`} />
                    <strong>{camera.name}</strong>
                    <small>
                      {camera.zone} · {camera.status}
                    </small>
                  </button>
                ))}
              </div>
            </div>
          ) : (
            <GujaratOperationsMap
              cameras={cameras}
              selectedCameraId={selectedCamera?.id ?? null}
              onCameraSelect={handleCameraSelect}
              onViewportChange={handleViewportChange}
              onMapViewportChange={handleMapViewportChange}
              inspectionPoint={inspectionPoint}
              onMapInspect={setInspectionPoint}
              viewMode={viewMode}
              baseMode={baseMode}
              mapBootstrap={mapBootstrap}
              showCameraPositions={showCameraPositions}
              showCameraLabels={showCameraLabels}
              showCameraCoverage={showCameraCoverage}
              drawMode={drawMode}
              drawCommand={drawCommand}
              mapViewCommand={mapViewCommand}
              drawnShapes={drawnShapes}
              onDrawProgress={setDrawProgress}
              onDrawComplete={completeDrawing}
              fullscreenMap={fullscreenMap}
              onPointerInfo={setMapPointer}
              operationalAlerts={mapAlerts}
              showAlertMarkers={showOperationalOverlay}
              selectedAlertId={selectedAlertId}
              selectedDistrictName={selectedDistrictName}
              showDistricts={showDistricts}
              onAlertClick={(cameraId, alertId) => {
                const alert = alerts.find((item) => item.id === alertId);
                if (alert) selectAlert(alert);
                else {
                  setSelectedCameraId(cameraId);
                  setDetailRailOpen(true);
                }
              }}
              onDistrictSelect={setSelectedDistrictName}
            />
          )}
          <button
            className={`hcam-map-mode-toggle${mapControlsOpen ? " is-open" : ""}`}
            type="button"
            onClick={() => setMapControlsOpen((open) => !open)}
            aria-expanded={mapControlsOpen}
            aria-controls="hcam-map-display-controls"
            title={mapControlsOpen ? "Hide map display controls" : "Show map display controls"}
          >
            <MapIcon size={14} />
            <span>Map</span>
            <ChevronDown size={13} />
          </button>
          {mapControlsOpen ? (
            <div
              className="hcam-map-mode"
              id="hcam-map-display-controls"
              role="group"
              aria-label="Map display controls"
            >
              <button
                type="button"
                className={viewMode === "3d" ? "is-active" : ""}
                onClick={() => setViewMode("3d")}
                aria-pressed={viewMode === "3d"}
                aria-label="Enable pitched map view"
              >
                <Box size={13} />
                <span>3D</span>
              </button>
              <button
                type="button"
                className={viewMode === "2d" ? "is-active" : ""}
                onClick={() => setViewMode("2d")}
                aria-pressed={viewMode === "2d"}
                aria-label="Enable two-dimensional map view"
              >
                <MapPinned size={13} />
                <span>2D</span>
              </button>
              <span className="hcam-map-mode-divider" aria-hidden="true" />
              <button
                type="button"
                className={baseMode === "map" ? "is-active" : ""}
                onClick={() => setBaseMode("map")}
                aria-pressed={baseMode === "map"}
                aria-label="Use map base style"
              >
                <MapIcon size={13} />
                <span>Map</span>
              </button>
              <button
                type="button"
                className={baseMode === "dark" ? "is-active" : ""}
                onClick={() => setBaseMode("dark")}
                aria-pressed={baseMode === "dark"}
                aria-label="Use dark base style"
              >
                <Moon size={13} />
                <span>Dark</span>
              </button>
              <button
                disabled
                className="is-unavailable"
                aria-label="Local imagery is unavailable until the Gujarat map package is installed"
                title="Local imagery unavailable until the Gujarat map package is installed"
              >
                <Satellite size={13} />
                <span>Sat</span>
              </button>
              <span className="hcam-map-mode-divider" aria-hidden="true" />
              <button
                className="hcam-map-reset-button"
                type="button"
                onClick={resetGujaratView}
                aria-label="Return to Gujarat map view"
                title="Return to Gujarat map view (R)"
              >
                <RotateCcw size={13} />
                <span>Reset</span>
              </button>
              <button
                className="hcam-map-fullscreen-button"
                onClick={toggleFullscreenMap}
                aria-label={fullscreenMap ? "Exit full map view" : "Open full map view"}
                title={fullscreenMap ? "Exit full map view" : "Open full map view"}
              >
                {fullscreenMap ? <Minimize2 size={14} /> : <Maximize2 size={14} />}
              </button>
            </div>
          ) : null}
          <div className="hcam-map-utility-rail" role="toolbar" aria-label="H-CAM map utilities">
            <MapUtilityButton
              label="Drawing tools"
              active={drawingPanelOpen}
              onClick={() => {
                setDrawingPanelOpen(true);
                setFeaturePanelOpen(false);
                setSidebarOpen(false);
                setMapUtilityPanel(null);
              }}
            >
              <PencilRuler size={18} />
            </MapUtilityButton>
            <MapUtilityButton
              label="Measure a camera route"
              active={drawMode === "line"}
              onClick={() => {
                setDrawingPanelOpen(true);
                setFeaturePanelOpen(false);
                setSidebarOpen(false);
                setDrawMode("line");
                setMapUtilityPanel(null);
              }}
            >
              <Route size={18} />
            </MapUtilityButton>
            <MapUtilityButton
              label="Search and locate cameras"
              active={mapUtilityPanel === "search"}
              onClick={() => setMapUtilityPanel((panel) => (panel === "search" ? null : "search"))}
            >
              <Search size={18} />
            </MapUtilityButton>
            <MapUtilityButton
              label="Operational places"
              active={mapUtilityPanel === "places"}
              onClick={() => setMapUtilityPanel((panel) => (panel === "places" ? null : "places"))}
            >
              <MapPinned size={18} />
            </MapUtilityButton>
            <MapUtilityButton
              label="H-CAM local data workspace"
              active={mapUtilityPanel === "data"}
              onClick={() => setMapUtilityPanel((panel) => (panel === "data" ? null : "data"))}
            >
              <Database size={18} />
            </MapUtilityButton>
            <MapUtilityButton
              label="Copy safe map view"
              active={Boolean(shareStatus)}
              onClick={copyCurrentMapView}
            >
              <Copy size={17} />
            </MapUtilityButton>
            <MapUtilityButton
              label="Map controls guide"
              active={mapUtilityPanel === "help"}
              onClick={() => setMapUtilityPanel((panel) => (panel === "help" ? null : "help"))}
            >
              <CircleHelp size={17} />
            </MapUtilityButton>
          </div>
          {mapUtilityPanel === "search" ? (
            <section
              className="hcam-map-utility-panel hcam-locate-panel"
              aria-label="Search and locate cameras"
            >
              <div className="hcam-map-utility-heading">
                <span>Locate camera</span>
                <button
                  type="button"
                  onClick={() => setMapUtilityPanel(null)}
                  aria-label="Close search"
                >
                  <X size={14} />
                </button>
              </div>
              <label className="hcam-map-utility-search">
                <Search size={14} />
                <input
                  value={query}
                  onChange={(event) => setQuery(event.target.value)}
                  placeholder="Search visible cameras"
                  autoFocus
                />
              </label>
              <p>
                {cameras.length
                  ? "Select a camera to focus the map."
                  : "No visible cameras match this search."}
              </p>
              <ul>
                {cameras.slice(0, 6).map((camera) => (
                  <li key={camera.id}>
                    <button
                      type="button"
                      onClick={() => {
                        setSelectedCameraId(camera.id);
                        setMapUtilityPanel(null);
                      }}
                    >
                      <span className={`hcam-status-dot status-${camera.status}`} />
                      <span>
                        <strong>{camera.name}</strong>
                        <small>
                          {camera.zone} · {camera.id}
                        </small>
                      </span>
                    </button>
                  </li>
                ))}
              </ul>
            </section>
          ) : null}
          {mapUtilityPanel === "places" ? (
            <section
              className="hcam-map-utility-panel hcam-places-panel"
              aria-label="Operational places"
            >
              <div className="hcam-map-utility-heading">
                <span>Operational places</span>
                <button
                  type="button"
                  onClick={() => setMapUtilityPanel(null)}
                  aria-label="Close operational places"
                >
                  <X size={14} />
                </button>
              </div>
              <p>
                H-CAM local shortcuts. These only change the map view; they do not query public
                places or services.
              </p>
              <ul>
                {OPERATIONAL_PLACES.map((place) => (
                  <li key={place.id}>
                    <button type="button" onClick={() => focusOperationalPlace(place)}>
                      <MapPinned size={13} />
                      <span>
                        <strong>{place.label}</strong>
                        <small>{place.detail}</small>
                      </span>
                      <ChevronRight size={13} />
                    </button>
                  </li>
                ))}
              </ul>
              <button className="hcam-data-panel-action" type="button" onClick={resetGujaratView}>
                Return to Gujarat view
              </button>
            </section>
          ) : null}
          {mapUtilityPanel === "data" ? (
            <section
              className="hcam-map-utility-panel hcam-data-panel"
              aria-label="H-CAM local data workspace"
            >
              <div className="hcam-map-utility-heading">
                <span>H-CAM data</span>
                <button
                  type="button"
                  onClick={() => setMapUtilityPanel(null)}
                  aria-label="Close data workspace"
                >
                  <X size={14} />
                </button>
              </div>
              <p>Local, authorised workspace data only.</p>
              <dl>
                <div>
                  <dt>Camera registry</dt>
                  <dd>{cameras.length} visible</dd>
                </div>
                <div>
                  <dt>Saved drawings</dt>
                  <dd>{drawnShapes.length} session-only</dd>
                </div>
                <div>
                  <dt>Map base</dt>
                  <dd>{baseMode}</dd>
                </div>
              </dl>
              <div className="hcam-source-status-list" aria-label="Map source status">
                <span>Source readiness</span>
                <MapSourceStatus
                  label="Basemap"
                  state={mapBootstrap.sources.basemap.state}
                  message={mapBootstrap.sources.basemap.message}
                />
                <MapSourceStatus
                  label="Terrain"
                  state={mapBootstrap.sources.terrain.state}
                  message={mapBootstrap.sources.terrain.message}
                />
                <MapSourceStatus
                  label="Intelligence"
                  state={mapBootstrap.sources.intelligence.state}
                  message={mapBootstrap.sources.intelligence.message}
                />
              </div>
              <button
                className="hcam-data-panel-action"
                type="button"
                onClick={() => {
                  setDrawingPanelOpen(true);
                  setMapUtilityPanel(null);
                }}
              >
                Open drawing workspace
              </button>
            </section>
          ) : null}
          {mapUtilityPanel === "help" ? (
            <section
              className="hcam-map-utility-panel hcam-map-help-panel"
              aria-label="Map controls guide"
            >
              <div className="hcam-map-utility-heading">
                <span>Map controls</span>
                <button
                  type="button"
                  onClick={() => setMapUtilityPanel(null)}
                  aria-label="Close map controls guide"
                >
                  <X size={14} />
                </button>
              </div>
              <p>Local H-CAM GIS controls. Nothing here requests feeds or external data.</p>
              <dl>
                <div>
                  <dt>
                    <kbd>F</kbd>
                  </dt>
                  <dd>Toggle full map view</dd>
                </div>
                <div>
                  <dt>
                    <kbd>D</kbd>
                  </dt>
                  <dd>Open drawing tools</dd>
                </div>
                <div>
                  <dt>
                    <kbd>S</kbd>
                  </dt>
                  <dd>Search visible cameras</dd>
                </div>
                <div>
                  <dt>
                    <kbd>R</kbd>
                  </dt>
                  <dd>Return to Gujarat view</dd>
                </div>
                <div>
                  <dt>
                    <kbd>H</kbd>
                  </dt>
                  <dd>Toggle this controls guide</dd>
                </div>
                <div>
                  <dt>
                    <kbd>Esc</kbd>
                  </dt>
                  <dd>Close or cancel a map tool</dd>
                </div>
              </dl>
              <div className="hcam-map-help-note">
                <span>Map click</span>
                <strong>Inspect a temporary coordinate</strong>
              </div>
            </section>
          ) : null}
          {shareStatus ? (
            <div className="hcam-map-share-status" role="status">
              <Copy size={12} />
              <span>{shareStatus}</span>
              <button
                type="button"
                onClick={() => setShareStatus("")}
                aria-label="Dismiss map view link status"
              >
                <X size={12} />
              </button>
            </div>
          ) : null}
          {inspectionPoint ? (
            <section
              className="hcam-coordinate-inspector"
              aria-label="Temporary coordinate inspection"
            >
              <header>
                <span>Map coordinate</span>
                <button
                  type="button"
                  onClick={() => setInspectionPoint(null)}
                  aria-label="Clear temporary coordinate"
                >
                  <X size={12} />
                </button>
              </header>
              <strong>
                {inspectionPoint[1].toFixed(5)}, {inspectionPoint[0].toFixed(5)}
              </strong>
              <small>
                {pointerLocation(inspectionPoint[0], inspectionPoint[1])} · temporary, not saved
              </small>
              <button type="button" onClick={copyInspectionCoordinate}>
                <Copy size={12} />
                Copy coordinate
              </button>
              {inspectionNearbyCameras.length ? (
                <div className="hcam-coordinate-nearby">
                  <span>Nearest H-CAM cameras</span>
                  {inspectionNearbyCameras.map((camera) => (
                    <button
                      type="button"
                      key={camera.id}
                      onClick={() => {
                        handleCameraSelect(camera);
                        setInspectionPoint(null);
                      }}
                    >
                      <i className={`hcam-status-dot status-${camera.status}`} />
                      <strong>{camera.name}</strong>
                      <small>{camera.zone}</small>
                      <ChevronRight size={12} />
                    </button>
                  ))}
                </div>
              ) : null}
            </section>
          ) : null}
          {selectedDistrictName ? (
            <TerritoryInspector
              districtName={selectedDistrictName}
              cameraCount={selectedDistrictCameras.length}
              alertCount={selectedDistrictAlerts.length}
              onFilter={() => {
                setQuery(districtCatalogueQuery(selectedDistrictName));
                setSelectedDistrictName(null);
                focusSidebarSection("catalogue");
              }}
              onClose={() => setSelectedDistrictName(null)}
            />
          ) : null}
          {selectedCamera ? (
            <CameraConsole
              camera={selectedCamera}
              nearbyCameras={nearbyCameras}
              localRole={localRole}
              onSelect={(camera) => {
                setSelectedCameraId(camera.id);
                setDetailRailOpen(true);
              }}
              onClose={() => {
                setSelectedCameraId(null);
                setDetailRailOpen(false);
              }}
            />
          ) : null}
          {selectionContext ? (
            <section
              className="hcam-selection-context"
              aria-label={`Current map selection: ${selectionContext.label}`}
            >
              <span>{selectionContext.kind}</span>
              <strong title={selectionContext.label}>{selectionContext.label}</strong>
              <small>{selectionContext.detail}</small>
              <div>
                <button type="button" onClick={resetGujaratView}>
                  Gujarat view
                </button>
                <button
                  type="button"
                  onClick={clearMapSelection}
                  aria-label="Clear current map selection"
                >
                  <X size={13} />
                </button>
              </div>
            </section>
          ) : null}
          <div className="hcam-map-readout" aria-label="Map cursor readout">
            <span>Cursor</span>
            <strong>
              {mapPointer.longitude.toFixed(4)}, {mapPointer.latitude.toFixed(4)}
            </strong>
            <span>Location</span>
            <strong>{pointerLocation(mapPointer.longitude, mapPointer.latitude)}</strong>
            <span>Zoom</span>
            <strong>{mapPointer.zoom.toFixed(1)}</strong>
          </div>
          {mapBootstrap.sources.basemap.state === "unavailable" ? (
            <div className="hcam-map-source-state" role="status">
              <strong>Local basemap unavailable</strong>
              <span>{mapBootstrap.sources.basemap.message}</span>
              <small>H-CAM intelligence layers remain separate and can still be inspected.</small>
            </div>
          ) : null}
          <div className="hcam-map-caption" aria-label="Map visibility summary">
            <span className={`hcam-live-dot${catalogueState === "error" ? " is-error" : ""}`} />
            <span>
              {catalogueState === "loading"
                ? "Loading visible H-CAM cameras"
                : catalogueState === "error"
                  ? "Catalogue unavailable - retry by moving the map"
                  : `${cameras.length} H-CAM cameras in view`}{" "}
              · {mapBootstrap.sources.intelligence.state}
            </span>
            <div
              className="hcam-active-layer-summary"
              aria-label={`${activeMapLayers.length} active map layers`}
            >
              {activeMapLayers.length ? (
                activeMapLayers.map((layer) => <em key={layer}>{layer}</em>)
              ) : (
                <em className="is-empty">No layers</em>
              )}
            </div>
          </div>
          {!selectedCamera ? (
            <button
              className={`hcam-detail-toggle${detailRailOpen ? " is-active" : ""}`}
              type="button"
              onClick={() => setDetailRailOpen((open) => !open)}
              aria-label={detailRailOpen ? "Close camera inspector" : "Open camera inspector"}
              title={detailRailOpen ? "Close camera inspector" : "Open camera inspector"}
            >
              <Video size={15} />
            </button>
          ) : null}
        </div>

        <aside
          className={`hcam-detail-rail${detailRailOpen ? " is-open" : ""}`}
          aria-label="Selected camera details"
        >
          {selectedCamera ? (
            <CameraDetail
              key={selectedCamera.id}
              camera={selectedCamera}
              localRole={localRole}
              onClose={() => {
                setSelectedCameraId(null);
                setDetailRailOpen(false);
              }}
            />
          ) : (
            <EmptySelection state={catalogueState} />
          )}
        </aside>
      </section>
    </section>
  );
}

function generatedMapBootstrap(): HcamMapBootstrap {
  const checkedAt = new Date().toISOString();
  const developmentBasemap = isLoopbackHostname(window.location.hostname);
  return {
    contractVersion: 1,
    mapStyle: {
      version: 1,
      styleUrl: developmentBasemap ? DEVELOPMENT_BASEMAP_STYLE : LOCAL_GUJARAT_STYLE,
      sourceIds: {
        basemap: developmentBasemap ? "carto" : "hcam-gujarat-reference",
        terrain: null,
      },
      defaultBaseMode: "dark",
      attribution: developmentBasemap
        ? "CARTO and OpenStreetMap contributors; development reference only"
        : "H-CAM generated local operational reference",
      bounds: [68, 20, 75, 25],
      minZoom: 4,
      maxZoom: 18,
    },
    sources: {
      basemap: {
        state: "development-fixture",
        message: developmentBasemap
          ? "Public CARTO/OpenStreetMap development basemap is active on loopback only."
          : "Generated same-origin Gujarat reference is active.",
        checkedAt,
      },
      terrain: {
        state: "unavailable",
        message: "Terrain elevation is not configured; pitched view is perspective only.",
        checkedAt,
      },
      intelligence: {
        state: "development-fixture",
        message: "Generated camera and alert metadata is active.",
        checkedAt,
      },
    },
    allowedLayers: ["cameras", "alerts"],
    scope: { role: "viewer", agency: "H-CAM", jurisdiction: "Gujarat" },
  };
}

function initialMapViewCommand() {
  if (typeof window === "undefined") return null;
  const url = new URL(window.location.href);
  const longitude = Number(url.searchParams.get("lon"));
  const latitude = Number(url.searchParams.get("lat"));
  const zoom = Number(url.searchParams.get("zoom"));
  if (!Number.isFinite(longitude) || !Number.isFinite(latitude) || !Number.isFinite(zoom))
    return null;
  if (longitude < 68 || longitude > 75 || latitude < 20 || latitude > 25 || zoom < 5 || zoom > 16)
    return null;
  return {
    action: "focus-location" as const,
    seq: 1,
    coordinates: [longitude, latitude] as [number, number],
    zoom,
  };
}

function generatedOperationalAlerts(now = Date.now()): OperationalAlert[] {
  const at = (minutesAgo: number) => new Date(now - minutesAgo * 60_000).toISOString();
  const minutesFromLabel = (value: string) =>
    value === "Just now" ? 0 : Number.parseInt(value, 10) || 0;
  const cameraStateAlerts: OperationalAlert[] = HCAM_CAMERA_FIXTURES.filter(
    (camera) => camera.status !== "online",
  ).map((camera) => ({
    id: `alert:${camera.id}`,
    cameraId: camera.id,
    title:
      camera.status === "offline"
        ? "Camera unavailable"
        : camera.status === "maintenance"
          ? "Scheduled maintenance"
          : "Camera health degraded",
    severity:
      camera.status === "offline" ? "high" : camera.status === "degraded" ? "medium" : "low",
    detail: `${camera.name} - ${camera.zone} - generated fixture`,
    observedAt: camera.lastUpdated,
    observedAtUtc: at(minutesFromLabel(camera.lastUpdated)),
    coordinates: camera.coordinates,
  }));
  return [
    ...cameraStateAlerts,
    {
      id: "alert:HCAM-AMD-001:perimeter-review",
      cameraId: "HCAM-AMD-001",
      title: "Perimeter review required",
      severity: "medium",
      detail: "Riverfront Gate - Ahmedabad Central - generated fixture",
      observedAt: "12 min ago",
      observedAtUtc: at(12),
      coordinates: [72.569, 23.055],
    },
    {
      id: "alert:HCAM-AMD-002:coverage-check",
      cameraId: "HCAM-AMD-002",
      title: "Coverage confirmation",
      severity: "low",
      detail: "Transit Corridor North - Ahmedabad Central - generated fixture",
      observedAt: "19 min ago",
      observedAtUtc: at(19),
      coordinates: [72.64, 23.098],
    },
    {
      id: "alert:HCAM-SRT-021:access-review",
      cameraId: "HCAM-SRT-021",
      title: "Restricted access review",
      severity: "high",
      detail: "South Approach - Surat - generated fixture",
      observedAt: "8 min ago",
      observedAtUtc: at(8),
      coordinates: [72.82, 21.165],
    },
    {
      id: "alert:HCAM-RJT-041:patrol-check",
      cameraId: "HCAM-RJT-041",
      title: "Patrol check requested",
      severity: "low",
      detail: "West Sector Entry - Rajkot - generated fixture",
      observedAt: "24 min ago",
      observedAtUtc: at(24),
      coordinates: [70.755, 22.315],
    },
  ];
}

function pointIsInRing([longitude, latitude]: [number, number], ring: number[][]) {
  let inside = false;
  for (let current = 0, previous = ring.length - 1; current < ring.length; previous = current++) {
    const currentPoint = ring[current];
    const previousPoint = ring[previous];
    if (!currentPoint || !previousPoint) continue;
    const [currentLongitude = 0, currentLatitude = 0] = currentPoint;
    const [previousLongitude = 0, previousLatitude = 0] = previousPoint;
    if (
      currentLatitude > latitude !== previousLatitude > latitude &&
      longitude <
        ((previousLongitude - currentLongitude) * (latitude - currentLatitude)) /
          (previousLatitude - currentLatitude) +
          currentLongitude
    )
      inside = !inside;
  }
  return inside;
}

function distanceSquared(
  [leftLongitude, leftLatitude]: [number, number],
  [rightLongitude, rightLatitude]: [number, number],
) {
  return (leftLongitude - rightLongitude) ** 2 + (leftLatitude - rightLatitude) ** 2;
}
function alertPriority(severity: AlertSeverity) {
  return severity === "high" ? 0 : severity === "medium" ? 1 : 2;
}
function isWithinAlertWindow(observedAtUtc: string, window: AlertTimeWindow, now: number) {
  const minutes = window === "15m" ? 15 : window === "30m" ? 30 : null;
  if (minutes === null) return true;
  const observedAt = Date.parse(observedAtUtc);
  return Number.isFinite(observedAt) && observedAt >= now - minutes * 60_000;
}

function normaliseDistrictName(value: string) {
  return value
    .toLowerCase()
    .replace(/ahmadabad/g, "ahmedabad")
    .replace(/[^a-z]/g, "");
}
function belongsToDistrict(value: string, districtName: string) {
  const district = normaliseDistrictName(districtName);
  const candidate = normaliseDistrictName(value);
  return district.length > 2 && (candidate.includes(district) || district.includes(candidate));
}
function districtCatalogueQuery(districtName: string) {
  return normaliseDistrictName(districtName) === "ahmedabad" ? "Ahmedabad" : districtName;
}

function pointerLocation(longitude: number, latitude: number) {
  if (longitude >= 72.35 && longitude <= 72.8 && latitude >= 22.85 && latitude <= 23.2)
    return "Ahmedabad, Gujarat, India";
  if (longitude >= 72.8 && longitude <= 73.35 && latitude >= 22.1 && latitude <= 22.8)
    return "Vadodara, Gujarat, India";
  if (longitude >= 70.5 && longitude <= 71.8 && latitude >= 21.6 && latitude <= 23.3)
    return "Saurashtra, Gujarat, India";
  return "Gujarat, India";
}

function exportDrawings(shapes: DrawnShape[]) {
  const collection = {
    type: "FeatureCollection",
    features: shapes.map((shape) => ({
      ...shape.geojson,
      properties: {
        id: shape.id,
        name: shape.name,
        kind: shape.kind,
        areaKm2: shape.areaKm2,
        perimeterKm: shape.perimeterKm,
      },
    })),
  };
  const url = URL.createObjectURL(
    new Blob([JSON.stringify(collection, null, 2)], { type: "application/geo+json" }),
  );
  const link = document.createElement("a");
  link.href = url;
  link.download = "hcam-drawings.geojson";
  link.click();
  URL.revokeObjectURL(url);
}

function RailButton({
  label,
  active,
  badge,
  onClick,
  children,
}: {
  label: string;
  active: boolean;
  badge?: number;
  onClick: () => void;
  children: ReactNode;
}) {
  return (
    <button
      className={`hcam-rail-button${active ? " is-active" : ""}`}
      type="button"
      aria-label={label}
      aria-controls="hcam-sidebar-panel"
      aria-pressed={active}
      title={label}
      onClick={onClick}
    >
      {children}
      {badge ? <span className="hcam-rail-badge">{badge > 9 ? "9+" : badge}</span> : null}
    </button>
  );
}

function MapUtilityButton({
  label,
  active,
  onClick,
  children,
}: {
  label: string;
  active: boolean;
  onClick: () => void;
  children: ReactNode;
}) {
  return (
    <button
      className={`hcam-map-utility-button${active ? " is-active" : ""}`}
      type="button"
      title={label}
      aria-label={label}
      aria-pressed={active}
      data-tool-label={label}
      onClick={onClick}
    >
      {children}
    </button>
  );
}

function TerritoryInspector({
  districtName,
  cameraCount,
  alertCount,
  onFilter,
  onClose,
}: {
  districtName: string;
  cameraCount: number;
  alertCount: number;
  onFilter: () => void;
  onClose: () => void;
}) {
  return (
    <section
      className="hcam-territory-inspector"
      aria-label={`Selected territory: ${districtName}`}
    >
      <header>
        <span>District territory</span>
        <button type="button" onClick={onClose} aria-label="Clear selected territory">
          <X size={14} />
        </button>
      </header>
      <strong>{districtName}</strong>
      <small>Gujarat district boundary · local reference</small>
      <dl>
        <div>
          <dt>Visible cameras</dt>
          <dd>{cameraCount}</dd>
        </div>
        <div>
          <dt>Local alerts</dt>
          <dd>{alertCount}</dd>
        </div>
      </dl>
      <button type="button" onClick={onFilter}>
        Filter camera catalogue
      </button>
    </section>
  );
}

function LayerTile({
  label,
  detail,
  active,
  tone,
  onClick,
}: {
  label: string;
  detail: string;
  active: boolean;
  tone: "camera" | "alert" | "territory" | "label" | "coverage";
  onClick: () => void;
}) {
  return (
    <button
      className={`hcam-layer-tile tone-${tone}${active ? " is-active" : ""}`}
      type="button"
      aria-pressed={active}
      onClick={onClick}
    >
      <span className="hcam-layer-tile-preview" aria-hidden="true">
        <i />
        <b />
      </span>
      <strong>{label}</strong>
      <small>{detail}</small>
    </button>
  );
}

function MapLegend() {
  return (
    <section className="hcam-map-legend" aria-label="Operational map legend">
      <div>
        <span>Map legend</span>
        <small>Local operations view</small>
      </div>
      <dl>
        <div>
          <dt>
            <i className="status-online" />
            Camera
          </dt>
          <dd>Operational</dd>
        </div>
        <div>
          <dt>
            <i className="status-degraded" />
            Camera
          </dt>
          <dd>Degraded</dd>
        </div>
        <div>
          <dt>
            <i className="legend-alert-high" />
            Alert
          </dt>
          <dd>High priority</dd>
        </div>
        <div>
          <dt>
            <i className="legend-alert-medium" />
            Alert
          </dt>
          <dd>Medium priority</dd>
        </div>
        <div>
          <dt>
            <i className="legend-boundary" />
            District
          </dt>
          <dd>Local boundary</dd>
        </div>
        <div>
          <dt>
            <i className="legend-coverage" />
            Sector
          </dt>
          <dd>Planning only</dd>
        </div>
      </dl>
    </section>
  );
}

function MapSourceStatus({
  label,
  state,
  message,
}: {
  label: string;
  state: HcamMapBootstrap["sources"]["basemap"]["state"];
  message: string;
}) {
  return (
    <div className={`hcam-source-status state-${state}`} title={message}>
      <span>
        <i />
        {label}
      </span>
      <strong>{state.replace("-", " ")}</strong>
    </div>
  );
}

function AlertFocusCard({
  alert,
  lifecycle,
  localRole,
  nearbyCameras,
  onCameraSelect,
  onLifecycleChange,
  onClear,
}: {
  alert: OperationalAlert;
  lifecycle: IncidentLifecycle;
  localRole: "viewer" | "operator";
  nearbyCameras: CameraFixture[];
  onCameraSelect: (camera: CameraFixture) => void;
  onLifecycleChange: (lifecycle: IncidentLifecycle) => void;
  onClear: () => void;
}) {
  const event = eventPresentation(alert);
  const isOperator = localRole === "operator";
  return (
    <section
      className={`hcam-alert-focus severity-${alert.severity} lifecycle-${lifecycle}`}
      aria-label={`Selected alert: ${alert.title}`}
    >
      <header>
        <span>Incident focus</span>
        <button type="button" onClick={onClear} aria-label="Clear selected alert">
          <X size={13} />
        </button>
      </header>
      <div className="hcam-alert-focus-title">
        <span aria-hidden="true">{event.icon}</span>
        <div>
          <strong>{alert.title}</strong>
          <small>{event.location}</small>
        </div>
      </div>
      <dl>
        <div>
          <dt>Severity</dt>
          <dd>{alert.severity}</dd>
        </div>
        <div>
          <dt>Status</dt>
          <dd>{lifecycle}</dd>
        </div>
        <div>
          <dt>Observed</dt>
          <dd>{alert.observedAt}</dd>
        </div>
      </dl>
      <div className="hcam-alert-workflow">
        <span>Session workflow</span>
        <div>
          <button
            className={lifecycle === "acknowledged" ? "is-active" : ""}
            type="button"
            disabled={!isOperator || lifecycle === "resolved"}
            onClick={() => onLifecycleChange("acknowledged")}
          >
            Acknowledge
          </button>
          <button
            className={lifecycle === "investigating" ? "is-active" : ""}
            type="button"
            disabled={!isOperator || lifecycle === "resolved"}
            onClick={() => onLifecycleChange("investigating")}
          >
            Investigate
          </button>
          <button
            className={lifecycle === "resolved" ? "is-active" : ""}
            type="button"
            disabled={!isOperator}
            onClick={() => onLifecycleChange(lifecycle === "resolved" ? "new" : "resolved")}
          >
            {lifecycle === "resolved" ? "Reopen" : "Resolve"}
          </button>
        </div>
        <small>
          {isOperator
            ? "Local session state only — not yet written to the H-CAM incident API."
            : "Viewer role — lifecycle actions are locked."}
        </small>
      </div>
      <div className="hcam-alert-focus-nearby">
        <span>Nearest H-CAM cameras</span>
        {nearbyCameras.map((camera) => (
          <button type="button" key={camera.id} onClick={() => onCameraSelect(camera)}>
            <i className={`hcam-status-dot status-${camera.status}`} />
            <strong>{camera.name}</strong>
            <small>
              {camera.zone} · {camera.status}
            </small>
          </button>
        ))}
      </div>
    </section>
  );
}

function eventPresentation(alert: OperationalAlert) {
  const location = alert.detail.replace(/\s*·\s*local fixture/i, "");
  const title = alert.title.toLowerCase();
  if (title.includes("unavailable") || title.includes("degraded") || title.includes("maintenance"))
    return { icon: "◇", label: "Camera status", location };
  if (title.includes("coverage") || title.includes("perimeter"))
    return { icon: "◈", label: "AI review", location };
  if (title.includes("access") || title.includes("patrol"))
    return { icon: "△", label: "Operational alert", location };
  return { icon: "⚠", label: "Incident review", location };
}

function EmptySelection({ state }: { state: CatalogueState }) {
  const message =
    state === "loading"
      ? "Loading authorised camera metadata for the visible map area."
      : state === "error"
        ? "The local camera catalogue could not be reached. Move the map or retry once the service is available."
        : "Choose a visible camera marker to inspect its authorised operational metadata.";
  return (
    <div className="hcam-empty-detail">
      <span className="hcam-empty-icon">
        {state === "loading" ? (
          <LoaderCircle className="hcam-spin" size={20} />
        ) : (
          <Video size={20} />
        )}
      </span>
      <h2>
        {state === "loading"
          ? "Loading cameras"
          : state === "error"
            ? "Catalogue unavailable"
            : "Select a camera"}
      </h2>
      <p>{message}</p>
    </div>
  );
}

function CameraConsole({
  camera,
  nearbyCameras,
  localRole,
  onSelect,
  onClose,
}: {
  camera: CameraFixture;
  nearbyCameras: CameraFixture[];
  localRole: "viewer" | "operator";
  onSelect: (camera: CameraFixture) => void;
  onClose: () => void;
}) {
  const [message, setMessage] = useState(
    "No media has been requested. Start an authorised H-CAM preview policy check.",
  );
  const [checking, setChecking] = useState(false);
  function requestPreview() {
    setChecking(true);
    setMessage(
      camera.previewAvailability === "available"
        ? "Generated policy projection permits a future playback-session request. No media was requested."
        : `Generated policy projection reports ${camera.previewAvailability}. No media was requested.`,
    );
    setChecking(false);
  }
  return (
    <section className="hcam-camera-console" aria-label={`Camera console for ${camera.name}`}>
      <header>
        <span>CAM-{camera.id}</span>
        <span>{camera.lastUpdated}</span>
        <button type="button" onClick={onClose} aria-label="Close camera console">
          <X size={15} />
        </button>
      </header>
      <div className="hcam-camera-console-title">
        <span className={`hcam-status-dot status-${camera.status}`} />
        <div>
          <strong>{camera.name}</strong>
          <small>
            {camera.zone} · {camera.type} · {camera.ownership}
          </small>
        </div>
      </div>
      <div className="hcam-camera-screen">
        <Video size={27} />
        <strong>{checking ? "Authorising preview…" : "Secure camera preview"}</strong>
        <span>{message}</span>
        <small>Metadata-only until an approved H-CAM media adapter confirms playback.</small>
      </div>
      <button
        className="hcam-camera-console-action"
        type="button"
        onClick={requestPreview}
        disabled={checking || localRole !== "operator"}
      >
        {localRole === "operator"
          ? checking
            ? "Checking policy…"
            : "Request authorised preview"
          : "Viewer role — preview policy locked"}
      </button>
      {nearbyCameras.length ? (
        <div className="hcam-nearby-cameras">
          <span>Nearby cameras</span>
          <div>
            {nearbyCameras.map((nearby) => (
              <button type="button" key={nearby.id} onClick={() => onSelect(nearby)}>
                <span className="hcam-nearby-thumbnail">
                  <Video size={14} />
                  <i className={`status-${nearby.status}`} />
                </span>
                <strong>{nearby.name}</strong>
                <small>{nearby.zone}</small>
              </button>
            ))}
          </div>
        </div>
      ) : null}
    </section>
  );
}

function CameraDetail({
  camera,
  localRole,
  onClose,
}: {
  camera: CameraFixture;
  localRole: "viewer" | "operator";
  onClose: () => void;
}) {
  const [previewState, setPreviewState] = useState<PreviewState>("not-requested");
  const [previewMessage, setPreviewMessage] = useState(
    "Live preview requires an authorised H-CAM session.",
  );
  const statusIcon =
    camera.status === "maintenance" ? (
      <Wrench size={15} />
    ) : camera.status === "offline" ? (
      <CircleAlert size={15} />
    ) : (
      <Activity size={15} />
    );
  const previewLabel: Record<PreviewState, string> = {
    "not-requested": "Preview not requested",
    authorizing: "Authorizing preview",
    available: "Preview pathway available",
    degraded: "Preview pathway degraded",
    unavailable: "Preview unavailable",
    "registry-only": "Registry only camera",
  };

  function requestPreview() {
    setPreviewState("authorizing");
    setPreviewMessage("Checking the local H-CAM preview policy. No media request is being made.");
    setPreviewState(camera.previewAvailability);
    setPreviewMessage(
      camera.previewAvailability === "available"
        ? "Generated policy projection is available. No playback session or media request was created."
        : `Generated policy projection is ${camera.previewAvailability}. No playback session or media request was created.`,
    );
  }

  return (
    <div className="hcam-camera-detail">
      <div className="hcam-detail-topline">
        <span>Camera detail</span>
        <button onClick={onClose} aria-label="Close camera detail">
          <X size={17} />
        </button>
      </div>
      <div className="hcam-camera-title">
        <span className={`hcam-status-dot status-${camera.status}`} />
        <div>
          <h2>{camera.name}</h2>
          <p>{camera.id}</p>
        </div>
      </div>
      <span className={`hcam-status-badge status-${camera.status}`}>
        {statusIcon}
        {STATUS_LABELS[camera.status]}
      </span>
      <dl className="hcam-detail-list">
        <div>
          <dt>Area</dt>
          <dd>{camera.zone}</dd>
        </div>
        <div>
          <dt>Camera type</dt>
          <dd>{camera.type}</dd>
        </div>
        <div>
          <dt>Ownership</dt>
          <dd>{camera.ownership}</dd>
        </div>
        <div>
          <dt>Last status</dt>
          <dd>{camera.lastUpdated}</dd>
        </div>
      </dl>
      <div className={`hcam-preview-state preview-${previewState}`}>
        <Video size={16} />
        <div>
          <strong>
            {previewState === "authorizing" ? (
              <>
                <LoaderCircle className="hcam-spin" size={12} /> {previewLabel[previewState]}
              </>
            ) : (
              previewLabel[previewState]
            )}
          </strong>
          <span>{previewMessage}</span>
        </div>
      </div>
      <button
        className="hcam-preview-button"
        onClick={requestPreview}
        disabled={previewState === "authorizing" || localRole !== "operator"}
      >
        {localRole !== "operator"
          ? "Viewer role — preview policy locked"
          : previewState === "authorizing"
            ? "Authorizing…"
            : "Request authorised preview"}
      </button>
    </div>
  );
}
