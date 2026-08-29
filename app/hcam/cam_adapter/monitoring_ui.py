from __future__ import annotations


CAMERA_MONITORING_DASHBOARD_HTML = r"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <meta name="referrer" content="no-referrer">
  <title>H-CAM Monitoring Center</title>
  <style>
    :root {
      color-scheme: dark;
      font-family: Inter, "Segoe UI", Arial, sans-serif;
      --top: #30394b;
      --rail: #171d27;
      --panel: #111823;
      --panel-2: #1b2432;
      --line: #303b4d;
      --line-soft: #263142;
      --text: #e9eef7;
      --muted: #94a2b7;
      --blue: #1769df;
      --blue-2: #0e4da8;
      --green: #49c779;
      --amber: #f0b75c;
      --red: #ed7770;
    }
    * { box-sizing: border-box; }
    html, body { height: 100%; }
    body { margin: 0; overflow: hidden; background: #0b1018; color: var(--text); }
    button, input { font: inherit; }
    button { color: inherit; }
    .console {
      height: 100vh;
      display: grid;
      grid-template-columns: 54px minmax(220px, 270px) minmax(440px, 1fr) 320px;
      grid-template-rows: 42px minmax(0, 1fr);
      grid-template-areas:
        "top top top top"
        "rail resources workspace intelligence";
    }
    .topbar {
      grid-area: top;
      display: flex;
      align-items: center;
      min-width: 0;
      background: var(--top);
      border-bottom: 1px solid #465064;
    }
    .brand {
      width: 154px;
      display: flex;
      align-items: center;
      gap: 9px;
      padding: 0 14px;
      font-weight: 700;
      letter-spacing: .03em;
    }
    .brand-mark {
      width: 23px;
      height: 23px;
      display: grid;
      place-items: center;
      border-radius: 50%;
      background: linear-gradient(135deg, #17b9cc 0 34%, #3aa558 34% 66%, #1d6ae0 66%);
      color: #fff;
      font-size: 11px;
      border: 1px solid #ffffff55;
    }
    .top-link, .top-section {
      height: 42px;
      display: flex;
      align-items: center;
      padding: 0 18px;
      border-left: 1px solid #465064;
      color: #d7deea;
      text-decoration: none;
      font-size: 13px;
    }
    .top-section.active { background: #3b475c; color: #fff; }
    .top-spacer { flex: 1; }
    .top-status { display: flex; align-items: center; gap: 8px; padding: 0 16px; color: #d7deea; font-size: 12px; }
    .status-dot { width: 8px; height: 8px; border-radius: 50%; background: var(--green); }
    .rail {
      grid-area: rail;
      display: flex;
      flex-direction: column;
      background: var(--rail);
      border-right: 1px solid var(--line);
    }
    .rail-button {
      width: 54px;
      min-height: 54px;
      padding: 6px 3px;
      border: 0;
      border-bottom: 1px solid var(--line-soft);
      background: transparent;
      color: var(--muted);
      font-size: 10px;
      cursor: default;
    }
    .rail-button strong { display: block; margin-bottom: 4px; font-size: 17px; color: #c9d3e1; }
    .rail-button.active { background: #222b39; color: #fff; border-left: 3px solid var(--blue); }
    .resources {
      grid-area: resources;
      min-width: 0;
      overflow: auto;
      background: var(--panel);
      border-right: 1px solid var(--line);
    }
    .panel-heading { padding: 13px 15px; border-bottom: 1px solid var(--line); font-weight: 700; font-size: 13px; }
    .resource-tabs { display: grid; grid-template-columns: 1fr 1fr; margin: 10px 14px; border: 1px solid var(--line); }
    .resource-tab { padding: 8px; border: 0; background: transparent; color: var(--muted); font-size: 12px; }
    .resource-tab.active { background: var(--blue-2); color: #fff; }
    .search-wrap { padding: 0 14px 10px; }
    .search-wrap input { width: 100%; padding: 8px 10px; border: 1px solid var(--line); background: #0d131d; color: #fff; outline: 0; }
    .resource-group-title { padding: 8px 14px; color: #bdc8d7; font-size: 12px; font-weight: 700; }
    .camera-list { padding: 0 10px 14px; }
    .camera-button {
      width: 100%;
      display: grid;
      grid-template-columns: 22px minmax(0, 1fr);
      gap: 7px;
      align-items: center;
      padding: 9px 10px;
      border: 0;
      border-left: 3px solid transparent;
      background: transparent;
      color: #c8d2df;
      text-align: left;
      cursor: pointer;
    }
    .camera-button:hover { background: #1b2635; }
    .camera-button.active { background: #124a9d; border-left-color: #56a2ff; color: #fff; }
    .camera-icon { color: #83a9d7; font-size: 13px; }
    .camera-label { overflow: hidden; text-overflow: ellipsis; white-space: nowrap; font-size: 12px; }
    .resource-empty { padding: 14px; color: var(--muted); font-size: 12px; line-height: 1.45; }
    .extension-note { margin: 16px 14px; padding: 11px; border: 1px solid var(--line); color: var(--muted); font-size: 11px; line-height: 1.45; }
    .workspace {
      grid-area: workspace;
      min-width: 0;
      min-height: 0;
      display: grid;
      grid-template-rows: 42px 40px minmax(0, 1fr) 42px;
      background: #0c1119;
    }
    .view-tabs { display: flex; align-items: end; border-bottom: 1px solid var(--line); background: #111823; }
    .view-tab { height: 42px; padding: 0 18px; border: 0; border-bottom: 2px solid transparent; background: transparent; color: var(--muted); }
    .view-tab.active { border-bottom-color: var(--blue); color: #fff; }
    .view-tab:disabled { cursor: not-allowed; opacity: .55; }
    .viewer-toolbar { display: flex; align-items: center; justify-content: space-between; padding: 0 10px; border-bottom: 1px solid var(--line); background: #101721; }
    .toolbar-group { display: flex; align-items: center; gap: 6px; }
    .tool-button { min-width: 30px; height: 28px; padding: 0 8px; border: 1px solid transparent; background: transparent; color: #aeb9c9; cursor: pointer; }
    .tool-button.active, .tool-button:hover { border-color: #3b4b61; background: #1c2736; color: #fff; }
    .tool-button:disabled { cursor: not-allowed; opacity: .45; }
    .viewer-stage { min-height: 0; padding: 8px; background: #090d13; }
    .video-frame { height: 100%; min-height: 260px; display: grid; grid-template-rows: 30px minmax(0, 1fr); border: 1px solid #1d63c7; background: #030506; }
    .stream-header { display: flex; align-items: center; justify-content: space-between; gap: 10px; padding: 0 9px; background: #1c2430; border-bottom: 1px solid #40506a; color: #cbd5e2; font-size: 11px; }
    .stream-title { overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
    .stream-state { color: var(--amber); white-space: nowrap; }
    .stream-state.live { color: var(--green); }
    .stream-state.error { color: var(--red); }
    .video-surface { position: relative; min-height: 0; overflow: hidden; background: #020304; }
    #live-video { width: 100%; height: 100%; display: block; object-fit: contain; background: #020304; }
    .video-placeholder { position: absolute; inset: 0; display: grid; place-items: center; padding: 24px; color: #738096; text-align: center; line-height: 1.55; pointer-events: none; }
    .video-placeholder.hidden { display: none; }
    .viewer-footer { display: flex; align-items: center; justify-content: space-between; gap: 12px; padding: 0 11px; border-top: 1px solid var(--line); background: #121a25; color: var(--muted); font-size: 11px; }
    .primary-button { padding: 7px 13px; border: 1px solid #2f76d4; background: #1451a5; color: #fff; cursor: pointer; }
    .primary-button:disabled { opacity: .55; cursor: wait; }
    .intelligence {
      grid-area: intelligence;
      min-width: 0;
      overflow: auto;
      background: #131a25;
      border-left: 1px solid var(--line);
    }
    .intelligence-tools { display: flex; gap: 7px; padding: 9px 10px; border-bottom: 1px solid var(--line); }
    .secondary-button { padding: 7px 10px; border: 1px solid var(--line); background: #202a39; color: #cbd5e2; cursor: pointer; font-size: 11px; }
    .status-card, .event-card { margin: 10px; border: 1px solid var(--line); background: var(--panel-2); }
    .card-title { display: flex; align-items: center; justify-content: space-between; gap: 8px; padding: 9px 10px; border-bottom: 1px solid var(--line); color: #cdd6e3; font-size: 11px; font-weight: 700; }
    .card-body { padding: 10px; }
    .status-row { display: flex; justify-content: space-between; gap: 10px; padding: 7px 0; border-bottom: 1px solid var(--line-soft); font-size: 11px; }
    .status-row:last-child { border-bottom: 0; }
    .status-key { color: var(--muted); }
    .status-value { text-align: right; color: #d7dfeb; }
    .status-value.ok { color: var(--green); }
    .status-value.warn { color: var(--amber); }
    .event-empty { color: var(--muted); font-size: 11px; line-height: 1.55; }
    .event-badge { display: inline-block; margin-bottom: 9px; padding: 3px 7px; border: 1px solid #526076; color: #c8d2df; font-size: 10px; }
    @media (max-width: 1100px) {
      body { overflow: auto; }
      .console { height: auto; min-height: 100vh; grid-template-columns: 54px 240px minmax(420px, 1fr); grid-template-rows: 42px minmax(620px, 1fr) auto; grid-template-areas: "top top top" "rail resources workspace" "rail intelligence intelligence"; }
      .intelligence { border-left: 0; border-top: 1px solid var(--line); display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); }
      .intelligence-tools, .panel-heading { grid-column: 1 / -1; }
    }
    @media (max-width: 760px) {
      .console { display: block; }
      .topbar { min-height: 42px; flex-wrap: wrap; }
      .top-section { display: none; }
      .rail { display: none; }
      .resources, .workspace, .intelligence { border: 0; }
      .resources { max-height: 260px; }
      .workspace { min-height: 640px; }
      .intelligence { display: block; }
    }
  </style>
</head>
<body>
  <div class="console">
    <header class="topbar">
      <div class="brand"><span class="brand-mark">H</span><span>H-CAM</span></div>
      <a class="top-link" href="/adapter-backend-dashboard">Adapter Backend</a>
      <div class="top-section active">Monitoring Center</div>
      <div class="top-section">Live View</div>
      <div class="top-spacer"></div>
      <div class="top-status"><span class="status-dot"></span><span id="top-health">Checking backend</span></div>
    </header>

    <nav class="rail" aria-label="Monitoring sections">
      <button class="rail-button active" type="button"><strong>▣</strong>Monitor</button>
      <button class="rail-button" type="button" disabled><strong>◇</strong>Map</button>
    </nav>

    <aside class="resources">
      <div class="panel-heading">Resources</div>
      <div class="resource-tabs"><button class="resource-tab active" type="button">Resources</button><button class="resource-tab" type="button" disabled>Favorites</button></div>
      <div class="search-wrap"><input id="camera-search" type="search" placeholder="Search cameras" autocomplete="off"></div>
      <div class="resource-group-title">▾ Current Site <span id="camera-count">(0)</span></div>
      <div id="camera-list" class="camera-list"><div class="resource-empty">Loading approved camera resources…</div></div>
      <div class="extension-note">This monitoring center is connected directly to the same adapter backend and authenticated session as the basic dashboard.</div>
    </aside>

    <main class="workspace">
      <div class="view-tabs"><button class="view-tab active" type="button">Live View</button><button class="view-tab" type="button" disabled>Playback</button></div>
      <div class="viewer-toolbar">
        <div class="toolbar-group"><button class="tool-button active" type="button" title="Single view">1</button><button class="tool-button" type="button" disabled title="Four-view layout">4</button><button class="tool-button" type="button" disabled title="Nine-view layout">9</button></div>
        <div class="toolbar-group"><button id="refresh" class="tool-button" type="button" title="Refresh resources">↻</button><button id="fullscreen" class="tool-button" type="button" title="Full screen">⛶</button></div>
      </div>
      <div class="viewer-stage">
        <div class="video-frame">
          <div class="stream-header"><span id="stream-title" class="stream-title">Select an approved camera</span><span id="stream-state" class="stream-state">Ready</span></div>
          <div class="video-surface">
            <video id="live-video" autoplay muted playsinline controls></video>
            <div id="video-placeholder" class="video-placeholder">Select a camera from Resources to start its approved live WebRTC feed.</div>
          </div>
        </div>
      </div>
      <div class="viewer-footer"><span id="selected-details">No camera selected</span><button id="connect" class="primary-button" type="button" disabled>Connect live</button></div>
    </main>

    <aside class="intelligence">
      <div class="panel-heading">Operations</div>
      <div class="intelligence-tools"><button id="side-refresh" class="secondary-button" type="button">Refresh</button><button class="secondary-button" type="button" disabled>Clear events</button></div>
      <section class="status-card">
        <div class="card-title"><span>Adapter status</span><span id="adapter-summary">Checking</span></div>
        <div class="card-body">
          <div class="status-row"><span class="status-key">Configuration</span><span id="status-config" class="status-value">—</span></div>
          <div class="status-row"><span class="status-key">Live viewer</span><span id="status-viewer" class="status-value">—</span></div>
          <div class="status-row"><span class="status-key">Recorder</span><span id="status-recorder" class="status-value">—</span></div>
          <div class="status-row"><span class="status-key">Recording streams</span><span id="status-streams" class="status-value">—</span></div>
          <div class="status-row"><span class="status-key">Active workers</span><span id="status-workers" class="status-value">—</span></div>
        </div>
      </section>
      <section class="event-card">
        <div class="card-title"><span>Analytics events</span><span>Current Site</span></div>
        <div class="card-body">
          <span class="event-badge">ANPR / Detection</span>
          <div class="event-empty">No analytics event API is connected. Live footage remains available. Detection cards will appear here only after a real backend event source is configured.</div>
        </div>
      </section>
      <section class="event-card">
        <div class="card-title"><span>Selected camera</span><span id="selected-camera-state">Idle</span></div>
        <div class="card-body">
          <div class="status-row"><span class="status-key">Name</span><span id="selected-camera-name" class="status-value">—</span></div>
          <div class="status-row"><span class="status-key">Department</span><span id="selected-camera-department" class="status-value">—</span></div>
          <div class="status-row"><span class="status-key">Media state</span><span id="selected-media-state" class="status-value">Not connected</span></div>
        </div>
      </section>
    </aside>
  </div>

  <script>
    "use strict";
    const cameraListNode = document.getElementById("camera-list");
    const cameraCountNode = document.getElementById("camera-count");
    const searchNode = document.getElementById("camera-search");
    const video = document.getElementById("live-video");
    const placeholder = document.getElementById("video-placeholder");
    const streamTitle = document.getElementById("stream-title");
    const streamState = document.getElementById("stream-state");
    const connectButton = document.getElementById("connect");
    const selectedDetails = document.getElementById("selected-details");
    let cameras = [];
    let selectedCamera = null;
    let activeConnection = null;

    function setText(id, value, className = "status-value") {
      const node = document.getElementById(id);
      node.textContent = value;
      node.className = className;
    }

    function setMediaState(message, kind = "") {
      streamState.textContent = message;
      streamState.className = `stream-state ${kind}`.trim();
      setText("selected-media-state", message, `status-value ${kind === "live" ? "ok" : kind === "error" ? "warn" : ""}`.trim());
    }

    function waitForIceGathering(peer) {
      if (peer.iceGatheringState === "complete") return Promise.resolve();
      return new Promise((resolve) => {
        const finish = () => {
          peer.removeEventListener("icegatheringstatechange", changed);
          resolve();
        };
        const changed = () => { if (peer.iceGatheringState === "complete") finish(); };
        peer.addEventListener("icegatheringstatechange", changed);
        window.setTimeout(finish, 5000);
      });
    }

    function closeActiveConnection() {
      if (!activeConnection) return;
      const closing = activeConnection;
      activeConnection = null;
      closing.peer.close();
      video.srcObject = null;
      if (closing.playbackSessionId) {
        fetch(`/cam-adapter/live/whep/${encodeURIComponent(closing.playbackSessionId)}`, {
          method: "DELETE", credentials: "same-origin", keepalive: true
        }).catch(() => undefined);
      }
    }

    async function connectSelectedCamera() {
      if (!selectedCamera) return;
      closeActiveConnection();
      connectButton.disabled = true;
      placeholder.classList.remove("hidden");
      placeholder.textContent = "Connecting to approved live feed…";
      setMediaState("Connecting", "");
      document.getElementById("selected-camera-state").textContent = "Connecting";
      try {
        const peer = new RTCPeerConnection();
        peer.addTransceiver("video", { direction: "recvonly" });
        peer.ontrack = (event) => {
          video.srcObject = event.streams[0] || new MediaStream([event.track]);
          video.play().catch(() => undefined);
        };
        peer.onconnectionstatechange = () => {
          if (["failed", "disconnected", "closed"].includes(peer.connectionState)) {
            setMediaState("Connection ended", "error");
            document.getElementById("selected-camera-state").textContent = "Offline";
          }
        };
        video.onplaying = () => {
          placeholder.classList.add("hidden");
          setMediaState("Live", "live");
          document.getElementById("selected-camera-state").textContent = "Live";
        };
        await peer.setLocalDescription(await peer.createOffer());
        await waitForIceGathering(peer);
        const response = await fetch(`/cam-adapter/live/whep/${encodeURIComponent(selectedCamera.camera_id)}`, {
          method: "POST",
          credentials: "same-origin",
          headers: { "Content-Type": "application/sdp", "Accept": "application/sdp" },
          body: peer.localDescription.sdp
        });
        if (!response.ok) throw new Error("Live negotiation failed");
        await peer.setRemoteDescription({ type: "answer", sdp: await response.text() });
        activeConnection = {
          peer,
          playbackSessionId: response.headers.get("X-HCAM-Playback-Session")
        };
        placeholder.textContent = "Waiting for live video frames…";
        setMediaState("Waiting for video", "");
      } catch (_error) {
        placeholder.textContent = "The live feed is unavailable. Use Connect live to retry.";
        setMediaState("Unavailable", "error");
        document.getElementById("selected-camera-state").textContent = "Unavailable";
      } finally {
        connectButton.disabled = false;
      }
    }

    function selectCamera(camera, connect = true) {
      selectedCamera = camera;
      streamTitle.textContent = camera.location_label || camera.camera_id;
      selectedDetails.textContent = `${camera.location_label || camera.camera_id} · ${camera.department || "No department"}`;
      setText("selected-camera-name", camera.location_label || camera.camera_id);
      setText("selected-camera-department", camera.department || "—");
      document.getElementById("selected-camera-state").textContent = "Ready";
      connectButton.disabled = false;
      for (const button of cameraListNode.querySelectorAll(".camera-button")) {
        button.classList.toggle("active", button.dataset.cameraId === camera.camera_id);
      }
      if (connect) connectSelectedCamera();
    }

    function renderCameraList(filter = "") {
      cameraListNode.replaceChildren();
      const normalized = filter.trim().toLowerCase();
      const visible = cameras.filter((camera) => {
        const value = `${camera.camera_id} ${camera.location_label || ""} ${camera.department || ""}`.toLowerCase();
        return value.includes(normalized);
      });
      cameraCountNode.textContent = `(${visible.length}/${cameras.length})`;
      if (!visible.length) {
        const empty = document.createElement("div");
        empty.className = "resource-empty";
        empty.textContent = cameras.length ? "No cameras match this search." : "No approved live cameras are available.";
        cameraListNode.append(empty);
        return;
      }
      for (const camera of visible) {
        const button = document.createElement("button");
        button.type = "button";
        button.className = "camera-button";
        button.dataset.cameraId = camera.camera_id;
        const icon = document.createElement("span");
        icon.className = "camera-icon";
        icon.textContent = "▰";
        const label = document.createElement("span");
        label.className = "camera-label";
        label.textContent = camera.location_label || camera.camera_id;
        button.append(icon, label);
        button.addEventListener("click", () => selectCamera(camera));
        cameraListNode.append(button);
      }
    }

    function renderAdapterStatus(adapter) {
      const configured = adapter.config_loaded;
      const viewer = adapter.live_viewer_enabled;
      setText("status-config", configured ? "Loaded" : "Unavailable", `status-value ${configured ? "ok" : "warn"}`);
      setText("status-viewer", viewer ? "Enabled" : "Disabled", `status-value ${viewer ? "ok" : "warn"}`);
      setText("status-recorder", adapter.running ? "Running" : "Stopped", `status-value ${adapter.running ? "warn" : "ok"}`);
      setText("status-streams", String(adapter.streams_enabled));
      setText("status-workers", String(adapter.active_workers.length));
      document.getElementById("adapter-summary").textContent = configured && viewer ? "Ready" : "Partial";
      document.getElementById("top-health").textContent = configured ? "Backend ready" : "Backend partial";
    }

    async function loadDashboard() {
      try {
        const response = await fetch("/cam-adapter/dashboard/data", { credentials: "same-origin", cache: "no-store" });
        if (!response.ok) throw new Error("Dashboard backend unavailable");
        const data = await response.json();
        renderAdapterStatus(data.adapter);
        cameras = data.live_cameras_available ? data.live_cameras : [];
        renderCameraList(searchNode.value);
        if (!selectedCamera && cameras.length) selectCamera(cameras[0]);
        if (!data.live_cameras_available) {
          cameraListNode.replaceChildren();
          const message = document.createElement("div");
          message.className = "resource-empty";
          message.textContent = data.live_cameras_message || "Camera catalogue unavailable. Adapter status is still connected.";
          cameraListNode.append(message);
        }
      } catch (_error) {
        document.getElementById("top-health").textContent = "Backend unavailable";
        document.getElementById("adapter-summary").textContent = "Unavailable";
        cameraListNode.innerHTML = "";
        const message = document.createElement("div");
        message.className = "resource-empty";
        message.textContent = "The adapter backend is not available. Return to Adapter Backend and restart H-CAM.";
        cameraListNode.append(message);
      }
    }

    searchNode.addEventListener("input", () => renderCameraList(searchNode.value));
    connectButton.addEventListener("click", connectSelectedCamera);
    document.getElementById("refresh").addEventListener("click", loadDashboard);
    document.getElementById("side-refresh").addEventListener("click", loadDashboard);
    document.getElementById("fullscreen").addEventListener("click", () => {
      if (document.fullscreenElement) document.exitFullscreen().catch(() => undefined);
      else document.documentElement.requestFullscreen().catch(() => undefined);
    });
    window.addEventListener("pagehide", closeActiveConnection);
    loadDashboard();
  </script>
</body>
</html>"""
