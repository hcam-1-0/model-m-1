/**
 * H-CAM GIS public-client contract, version 1.
 *
 * This module is deliberately safe for browser use.  It describes operational
 * metadata only and must never gain stream URLs, tokens, SDP, credentials, or
 * provider locators.
 */
import type { CameraFixture, CameraStatus, PreviewAvailability } from "./operations-fixtures";

export type HcamSourceState = "loading" | "live" | "stale" | "unavailable" | "development-fixture";
export type HcamRole = "viewer" | "operator";
export type HcamBaseMode = "map" | "dark" | "satellite";

export interface HcamMapSourceStatus {
  state: HcamSourceState;
  message: string;
  checkedAt: string;
}

export interface HcamMapStyle {
  version: 1;
  styleUrl: string;
  sourceIds: { basemap: string; terrain: string | null };
  defaultBaseMode: Exclude<HcamBaseMode, "satellite">;
  attribution: string;
  bounds: [number, number, number, number];
  minZoom: number;
  maxZoom: number;
}

export interface HcamMapBootstrap {
  contractVersion: 1;
  mapStyle: HcamMapStyle;
  sources: {
    basemap: HcamMapSourceStatus;
    terrain: HcamMapSourceStatus;
    intelligence: HcamMapSourceStatus;
  };
  allowedLayers: readonly ["cameras", "alerts"];
  scope: { role: HcamRole; agency: string; jurisdiction: string };
}

export type CameraSummary = CameraFixture;

export interface CameraOperationalState {
  cameraId: string;
  status: CameraStatus;
  observedAt: string;
}

export interface IncidentSummary {
  id: string;
  title: string;
  status: "active" | "closed";
  coordinates: [number, number];
}

export interface AlertSummary {
  id: string;
  cameraId: string;
  title: string;
  severity: "low" | "medium" | "high";
  detail: string;
  observedAt: string;
  /** ISO-8601 event time. Local fixtures derive this at response generation; production must supply its recorded UTC time. */
  observedAtUtc: string;
  /** Local fixture coordinates are display-only operational context. */
  coordinates?: [number, number];
}

export interface OperationalZone {
  id: string;
  name: string;
  geometry: GeoJSON.Geometry;
}
export interface AssetSummary {
  id: string;
  name: string;
  coordinates: [number, number];
}
export interface AoiFeature {
  id: string;
  name: string;
  geometry: GeoJSON.Geometry;
}
export interface MapLayerState {
  id: string;
  enabled: boolean;
  sourceState: HcamSourceState;
}

export interface MediaPreviewAuthorization {
  cameraId: string;
  state: PreviewAvailability;
  message: string;
  playbackStarted: false;
}
