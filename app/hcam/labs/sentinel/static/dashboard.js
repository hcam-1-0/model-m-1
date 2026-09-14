"use strict";

const state = {
  cameras: [],
  peer: null,
  resource: null,
  cleanupUrl: null,
  mediaPath: null,
  accessToken: null,
  renewalTimer: null,
  reconnectTimer: null,
  reconnectAttempts: 0,
  startAbortController: null,
  pendingPreview: null,
  selected: null,
  switching: false,
  starting: false,
  activeAdapter: null,
  autoStartAttempted: false,
  classification: "corp8-authenticated-grid",
  catalogMode: "corp8-online",
};
const byId = (id) => document.getElementById(id);

function text(value, fallback = "-") {
  return value === null || value === undefined || value === "" ? fallback : String(value);
}

async function requestJson(url, options = {}) {
  const response = await fetch(url, { cache: "no-store", ...options });
  if (!response.ok) throw new Error(`Request failed (${response.status})`);
  return response.json();
}

function renderSummary(status) {
  const counts = status.counts || {};
  const adapterId = status.resource_profile?.adapter_id || status.adapter?.adapter_id || null;
  state.classification = status.classification || "corp8-authenticated-grid";
  state.catalogMode = status.catalog_mode || "corp8-online";
  if (adapterId !== state.activeAdapter) {
    state.activeAdapter = adapterId;
    state.autoStartAttempted = false;
  }
  byId("catalogueState").textContent = text(status.source?.state, "Unavailable");
  byId("recordCount").textContent = text(counts.total, "0");
  byId("liveCount").textContent = text(counts.advertised_live, "0");
  byId("onlineCount").textContent = text(status.observed_health_counts?.online, "0");
  byId("runtimeCount").textContent = text(status.runtime_connection_limit, "0");
  const media = status.media_preparation;
  const encoder = media?.accelerator?.h264?.accelerator;
  byId("acceleratorState").textContent = state.catalogMode === "corp8-online"
    ? "External source"
    : (encoder ? encoder.toUpperCase() : "Not prepared");
  byId("classificationLabel").textContent = state.catalogMode === "corp8-online"
    ? "CORP8 AUTHENTICATED GRID"
    : "GENERATED FALLBACK";
  byId("inventoryTitle").textContent = state.catalogMode === "corp8-online"
    ? "CORP8 camera inventory"
    : "Generated camera inventory";
  byId("liveFeedLabel").textContent = state.catalogMode === "corp8-online"
    ? "CORP8 live feed"
    : "Generated fallback feed";
  for (const button of document.querySelectorAll("[data-adapter]")) {
    const active = button.dataset.adapter === adapterId;
    button.setAttribute("aria-pressed", String(active));
    button.disabled = state.switching || active;
  }
}

function cameraMedia(camera) {
  const media = camera.media || {};
  const observed = camera.observed_media || {};
  const advertisedCodec = text(media.codec, "unknown").toUpperCase();
  const observedCodec = text(observed.codec, "probe pending").toUpperCase();
  const geometry = media.width && media.height ? `${media.width}x${media.height}` : "unknown geometry";
  const observedGeometry = observed.width && observed.height ? `${observed.width}x${observed.height}` : "probe pending";
  return `advertised ${advertisedCodec} / ${geometry}; observed ${observedCodec} / ${observedGeometry}`;
}

function renderCameras() {
  const filter = byId("cameraFilter").value.trim().toLowerCase();
  const items = state.cameras.filter((camera) => JSON.stringify(camera).toLowerCase().includes(filter));
  const body = byId("cameraRows");
  body.replaceChildren();
  for (const camera of items) {
    const row = document.createElement("tr");
    const identity = document.createElement("td");
    const name = document.createElement("span");
    name.className = "camera-name";
    name.textContent = `${camera.external_camera_id} / ${text(camera.name)}`;
    const zone = document.createElement("span");
    zone.className = "camera-zone";
    zone.textContent = text(camera.location);
    identity.append(name, zone);

    const statusCell = document.createElement("td");
    const status = document.createElement("span");
    status.className = `state ${camera.lifecycle_state}`;
    status.textContent = camera.lifecycle_state;
    const observed = document.createElement("span");
    observed.className = "camera-zone";
    observed.textContent = `transport: ${text(camera.observed_health, "unknown")}`;
    statusCell.append(status, observed);

    const media = document.createElement("td");
    media.textContent = cameraMedia(camera);
    const fps = document.createElement("td");
    fps.textContent = text(camera.media?.fps, "unknown");
    const transports = document.createElement("td");
    transports.className = "transport";
    transports.textContent = camera.transports.map((item) => item.role).join(" / ");
    const action = document.createElement("td");
    const button = document.createElement("button");
    button.type = "button";
    button.dataset.cameraId = camera.external_camera_id;
    button.textContent = "Preview";
    button.disabled = !camera.preview_compatible;
    button.title = camera.preview_compatible
      ? "Open WHEP preview"
      : "WHEP preview unavailable for this camera";
    button.addEventListener("click", () => startPreview(camera));
    const selected = state.selected === camera.external_camera_id;
    row.classList.toggle("selected", selected);
    button.setAttribute("aria-pressed", String(selected));
    button.textContent = selected ? "Live" : "View live";
    action.append(button);
    row.append(identity, statusCell, media, fps, transports, action);
    body.append(row);
  }
  byId("inventoryStatus").textContent = `${items.length} of ${state.cameras.length} cameras`;
}

function renderEvents(events) {
  const list = byId("eventList");
  list.replaceChildren();
  for (const event of events) {
    const item = document.createElement("li");
    const time = document.createElement("span");
    time.className = "event-time";
    time.textContent = new Date(event.created_at).toLocaleString();
    const action = document.createElement("span");
    action.textContent = event.action;
    const outcome = document.createElement("span");
    outcome.className = "event-outcome";
    outcome.textContent = event.outcome;
    item.append(time, action, outcome);
    list.append(item);
  }
}

async function load() {
  try {
    const [status, cameras, events] = await Promise.all([
      requestJson("/api/status"),
      requestJson("/api/cameras"),
      requestJson("/api/events"),
    ]);
    state.cameras = cameras.items;
    renderSummary(status);
    renderCameras();
    renderEvents(events.items);
    await ensureLiveFeed();
  } catch (error) {
    byId("inventoryStatus").textContent = error.message;
  }
}

function setPreviewStatus(message, connectionState = "idle") {
  byId("previewStatus").textContent = message;
  byId("liveIndicator").dataset.state = connectionState;
}

function waitForIce(peer) {
  if (peer.iceGatheringState === "complete") return Promise.resolve();
  return new Promise((resolve) => {
    const timeout = window.setTimeout(resolve, 2500);
    peer.addEventListener("icegatheringstatechange", () => {
      if (peer.iceGatheringState === "complete") {
        window.clearTimeout(timeout);
        resolve();
      }
    });
  });
}

async function stopPreview({ abortStart = true } = {}) {
  if (abortStart) {
    state.pendingPreview = null;
    if (state.startAbortController) state.startAbortController.abort();
  }
  if (state.renewalTimer) window.clearTimeout(state.renewalTimer);
  if (state.reconnectTimer) window.clearTimeout(state.reconnectTimer);
  state.renewalTimer = null;
  state.reconnectTimer = null;
  const cleanupTargets = [];
  if (state.peer) state.peer.close();
  state.peer = null;
  if (state.cleanupUrl) cleanupTargets.push(state.cleanupUrl);
  else if (state.resource) cleanupTargets.push(state.resource);
  for (const cleanupTarget of cleanupTargets) {
    try {
      await fetch(cleanupTarget, {
        method: "DELETE",
        keepalive: true,
        headers: state.accessToken ? { "Authorization": `Bearer ${state.accessToken}` } : {},
      });
    } catch (_error) {
      // The peer is still closed locally when the bounded WHEP session has expired.
    }
  }
  state.resource = null;
  state.cleanupUrl = null;
  state.mediaPath = null;
  state.accessToken = null;
  state.selected = null;
  const video = byId("previewVideo");
  video.pause();
  video.srcObject = null;
  byId("previewEmpty").hidden = false;
  byId("previewTitle").textContent = "No camera selected";
  byId("previewDetails").querySelector("dd").textContent = "-";
  setPreviewStatus("Live feed stopped. No media was retained.");
  byId("stopPreview").disabled = true;
  renderCameras();
}

function schedulePreviewReconnect(camera, peer) {
  if (state.reconnectTimer) return;
  const delayMs = Math.min(2000 * (2 ** state.reconnectAttempts), 30000);
  state.reconnectAttempts += 1;
  state.reconnectTimer = window.setTimeout(() => {
    state.reconnectTimer = null;
    if (peer === state.peer && state.selected === camera.external_camera_id) {
      startPreview(camera, true);
    }
  }, delayMs);
}

function trustedWhepResource(location, whepUrl) {
  if (!location) return null;
  const base = new URL(whepUrl, window.location.href);
  const resource = new URL(location, base);
  const sessionPrefix = base.pathname.endsWith("/") ? base.pathname : `${base.pathname}/`;
  if (resource.origin !== base.origin || !resource.pathname.startsWith(sessionPrefix)) {
    throw new Error("WHEP server returned an untrusted session location");
  }
  return resource.toString();
}

async function startPreview(camera, replaceSession = false) {
  if (state.starting) {
    state.pendingPreview = { camera, replaceSession };
    if (state.startAbortController) state.startAbortController.abort();
    return;
  }
  if (!replaceSession && state.peer && state.selected === camera.external_camera_id) return;
  if (!replaceSession) state.reconnectAttempts = 0;
  state.starting = true;
  const controller = new AbortController();
  state.startAbortController = controller;
  await stopPreview({ abortStart: false });
  state.selected = camera.external_camera_id;
  byId("previewTitle").textContent = `${camera.external_camera_id} / ${text(camera.name)}`;
  setPreviewStatus("Requesting bounded live playback session", "connecting");
  byId("previewDetails").querySelector("dd").textContent = text(camera.profile_id);
  renderCameras();
  try {
    const session = await requestJson(`/api/cameras/${encodeURIComponent(camera.external_camera_id)}/playback`, {
      method: "POST",
      signal: controller.signal,
    });
    state.accessToken = session.access_token;
    state.cleanupUrl = session.cleanup_url || null;
    state.mediaPath = session.media_path || "direct-whep";
    byId("previewTransport").textContent = state.mediaPath === "hls-stream-copy-to-local-whep"
      ? "HLS to local WHEP"
      : "WHEP";
    const peer = new RTCPeerConnection();
    state.peer = peer;
    peer.addTransceiver("video", { direction: "recvonly" });
    peer.addEventListener("connectionstatechange", () => {
      if (peer !== state.peer) return;
      if (peer.connectionState === "connected") {
        state.reconnectAttempts = 0;
        setPreviewStatus(
          state.mediaPath === "hls-stream-copy-to-local-whep"
            ? "Sentinel live feed connected through HLS fallback"
            : "Sentinel WHEP live feed connected",
          "live",
        );
      } else if (["failed", "disconnected"].includes(peer.connectionState)) {
        setPreviewStatus("Sentinel live feed reconnecting", "connecting");
        byId("previewEmpty").hidden = false;
        schedulePreviewReconnect(camera, peer);
      }
    });
    peer.addEventListener("track", (event) => {
      const video = byId("previewVideo");
      video.srcObject = event.streams[0];
      video.play().catch(() => setPreviewStatus("Live feed is ready; start playback from the video controls", "connecting"));
      byId("previewEmpty").hidden = true;
    });
    await peer.setLocalDescription(await peer.createOffer());
    await waitForIce(peer);
    const response = await fetch(session.whep_url, {
      method: "POST",
      headers: {
        "Authorization": `${session.token_type} ${session.access_token}`,
        "Content-Type": "application/sdp",
      },
      body: peer.localDescription.sdp,
      signal: controller.signal,
    });
    if (!response.ok) throw new Error(`WHEP negotiation failed (${response.status})`);
    state.resource = trustedWhepResource(response.headers.get("location"), session.whep_url);
    await peer.setRemoteDescription({ type: "answer", sdp: await response.text() });
    const expiresAt = Date.parse(session.expires_at);
    if (Number.isFinite(expiresAt)) {
      const renewIn = Math.max(10000, Math.min(50000, expiresAt - Date.now() - 10000));
      state.renewalTimer = window.setTimeout(() => {
        if (peer === state.peer && state.selected === camera.external_camera_id) {
          startPreview(camera, true);
        }
      }, renewIn);
    }
    setPreviewStatus("Negotiating WHEP live feed", "connecting");
    byId("stopPreview").disabled = false;
  } catch (error) {
    if (error.name !== "AbortError") setPreviewStatus(error.message, "error");
    if (state.cleanupUrl) {
      try {
        await fetch(state.cleanupUrl, {
          method: "DELETE",
          headers: state.accessToken ? { "Authorization": `Bearer ${state.accessToken}` } : {},
        });
      } catch (_cleanupError) {
        // The server-side 60-second lease remains the final cleanup boundary.
      }
    }
    if (state.peer) state.peer.close();
    state.peer = null;
    state.resource = null;
    state.cleanupUrl = null;
    state.mediaPath = null;
    state.accessToken = null;
  } finally {
    if (state.startAbortController === controller) state.startAbortController = null;
    state.starting = false;
    renderCameras();
    const pending = state.pendingPreview;
    state.pendingPreview = null;
    if (pending) startPreview(pending.camera, pending.replaceSession);
  }
}

function autoPreviewCamera() {
  const candidates = state.cameras.filter((item) =>
    item.preview_compatible && String(item.media?.codec || "").toLowerCase() === "h264"
  );
  const fallback = candidates.length
    ? candidates
    : state.cameras.filter((item) => item.preview_compatible);
  return fallback.sort((left, right) => {
    const leftPixels = Number(left.media?.width) * Number(left.media?.height) || Number.MAX_SAFE_INTEGER;
    const rightPixels = Number(right.media?.width) * Number(right.media?.height) || Number.MAX_SAFE_INTEGER;
    if (leftPixels !== rightPixels) return leftPixels - rightPixels;
    const fpsDifference = (Number(right.media?.fps) || 0) - (Number(left.media?.fps) || 0);
    if (fpsDifference) return fpsDifference;
    return String(left.external_camera_id).localeCompare(String(right.external_camera_id), undefined, { numeric: true });
  })[0];
}

async function ensureLiveFeed() {
  if (
    state.switching ||
    state.starting ||
    state.peer ||
    state.selected ||
    state.autoStartAttempted
  ) return;
  const camera = autoPreviewCamera();
  state.autoStartAttempted = true;
  if (!camera) {
    setPreviewStatus("No compatible live feed is currently available", "error");
    return;
  }
  await startPreview(camera);
}

async function refreshCatalogue() {
  const button = byId("refreshButton");
  button.disabled = true;
  try {
    await requestJson("/api/refresh", {
      method: "POST",
      headers: {
        "X-HCAM-Lab-Confirm": state.classification,
        "X-HCAM-Reason": "Manual CORP8 camera grid catalogue refresh",
      },
    });
    await load();
  } catch (error) {
    byId("inventoryStatus").textContent = error.message;
  } finally {
    button.disabled = false;
  }
}

async function activateAdapter(adapterId) {
  if (state.switching) return;
  state.switching = true;
  for (const button of document.querySelectorAll("[data-adapter]")) button.disabled = true;
  await stopPreview();
  byId("inventoryStatus").textContent = `Activating ${adapterId}`;
  try {
    await requestJson(`/api/adapters/${encodeURIComponent(adapterId)}/activate`, {
      method: "POST",
      headers: {
        "X-HCAM-Lab-Confirm": state.classification,
        "X-HCAM-Reason": "Operator selected CORP8 resource profile",
      },
    });
    await new Promise((resolve) => window.setTimeout(resolve, 1500));
    await load();
  } catch (error) {
    byId("inventoryStatus").textContent = error.message;
  } finally {
    state.switching = false;
    await load();
  }
}

byId("cameraFilter").addEventListener("input", renderCameras);
byId("refreshButton").addEventListener("click", refreshCatalogue);
byId("stopPreview").addEventListener("click", stopPreview);
for (const button of document.querySelectorAll("[data-adapter]")) {
  button.addEventListener("click", () => activateAdapter(button.dataset.adapter));
}
window.addEventListener("beforeunload", () => stopPreview());
load();
window.setInterval(() => {
  if (!state.switching && !state.peer) load();
}, 10000);
