import {
  admitStreams,
  cameraListState,
  getResourceProfile,
  type BrowserMediaCapabilities,
  type CameraProjection,
  type ResourceProfileId,
} from "@hcam/camera-live-domain";
import {
  generatedAdmissionRequests,
  generatedCameras,
  generatedLayout,
  generatedPlaybackGrant,
} from "@hcam/test-fixtures";

export const generatedNow = new Date("2026-09-08T09:00:30.000Z");
export const cameras = generatedCameras(10);
export const initialLayout = generatedLayout(4);
export const generatedBrowserCapabilities: BrowserMediaCapabilities = {
  mse: true,
  nativeHls: false,
  webrtc: true,
  codecs: ["avc1.42E01E"],
};
export function cameraById(cameraId: string | undefined): CameraProjection | null {
  return cameras.find((camera) => camera.id === cameraId) ?? null;
}
export function cameraByStream(streamId: string | undefined): CameraProjection | null {
  return cameras.find((camera) => camera.streams.some((stream) => stream.id === streamId)) ?? null;
}
export function admissions(profile: ResourceProfileId) {
  return admitStreams(profile, generatedAdmissionRequests(), generatedBrowserCapabilities, false);
}
export const catalogueSummary = Object.freeze({
  total: cameras.length,
  online: cameras.filter((camera) => camera.state === "online").length,
  attention: cameras.filter((camera) => camera.health === "attention").length,
  unavailable: cameras.filter((camera) => camera.state === "offline").length,
  viewState: cameraListState(cameras, generatedNow),
});
export function playbackFor(streamId: string) {
  return generatedPlaybackGrant(streamId, "hls");
}
export function profileSummary(profile: ResourceProfileId) {
  return getResourceProfile(profile);
}
