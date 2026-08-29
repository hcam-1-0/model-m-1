from __future__ import annotations


ADAPTER_BACKEND_DASHBOARD_HTML = r"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <meta name="referrer" content="no-referrer">
  <title>Adapter Backend Dashboard</title>
  <style>
    :root { color-scheme: dark; font-family: Arial, Helvetica, sans-serif; }
    body { margin: 0; background: #101317; color: #edf1f5; }
    header { padding: 18px 24px; background: #1b2229; border-bottom: 1px solid #3a434d; }
    h1 { margin: 0; font-size: 1.45rem; }
    header p { margin: 7px 0 0; color: #b8c3cd; font-size: .92rem; }
    main { max-width: 1000px; margin: 0 auto; padding: 20px 24px 40px; }
    section { margin: 0 0 18px; padding: 16px; border: 1px solid #3a434d; background: #171d23; }
    h2 { margin: 0 0 14px; font-size: 1.1rem; }
    .grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(180px, 1fr)); gap: 10px; }
    .item { padding: 10px; border: 1px solid #34404a; background: #11161b; }
    .label { display: block; color: #9fadb9; font-size: .78rem; text-transform: uppercase; }
    .value { display: block; margin-top: 5px; overflow-wrap: anywhere; font-weight: 700; }
    table { width: 100%; border-collapse: collapse; font-size: .92rem; }
    th, td { padding: 10px 8px; border-bottom: 1px solid #34404a; text-align: left; vertical-align: top; }
    th { color: #b8c3cd; font-size: .78rem; text-transform: uppercase; }
    .ok { color: #96d9a8; }
    .warn { color: #ffd28a; }
    .error { color: #ffaca5; }
    .empty { color: #b8c3cd; }
    a { color: #9dccff; }
    button { padding: 8px 12px; border: 1px solid #526b80; background: #243846; color: #edf1f5; cursor: pointer; font: inherit; }
    .videos { display: grid; grid-template-columns: repeat(auto-fit, minmax(320px, 1fr)); gap: 14px; }
    .video-card { border: 1px solid #34404a; background: #11161b; }
    .video-title { padding: 10px; font-weight: 700; }
    video { display: block; width: 100%; aspect-ratio: 16 / 9; background: #050709; object-fit: contain; }
    .video-controls { display: flex; justify-content: space-between; gap: 10px; align-items: center; padding: 10px; color: #b8c3cd; font-size: .85rem; }
  </style>
</head>
<body>
  <header>
    <h1>Adapter Backend Dashboard</h1>
    <p>Basic operational view with approved live footage. It does not start recording, start workers, or save video.</p>
  </header>
  <main>
    <p><a href="/camera-monitoring-dashboard">Open monitoring center</a> &middot; <button id="refresh" type="button">Refresh status</button></p>
    <section aria-labelledby="live-title">
      <h2 id="live-title">Live footage</h2>
      <p id="video-note" class="empty">Loading approved live cameras…</p>
      <div id="live-videos" class="videos"></div>
    </section>
    <section aria-labelledby="adapter-title">
      <h2 id="adapter-title">Adapter status</h2>
      <div id="adapter-status" class="grid"><p class="empty">Loading adapter status…</p></div>
    </section>
    <section aria-labelledby="camera-title">
      <h2 id="camera-title">Approved live cameras</h2>
      <p id="camera-note" class="empty">Loading live camera list…</p>
      <table>
        <thead><tr><th>Camera</th><th>Department</th><th>State</th></tr></thead>
        <tbody id="camera-list"></tbody>
      </table>
    </section>
  </main>
  <script>
    "use strict";
    const statusNode = document.getElementById("adapter-status");
    const cameraNote = document.getElementById("camera-note");
    const cameraList = document.getElementById("camera-list");
    const videoNote = document.getElementById("video-note");
    const videoList = document.getElementById("live-videos");
    const connections = new Map();

    function text(value) {
      return value === null || value === undefined || value === "" ? "—" : String(value);
    }

    function addStatus(label, value, className = "") {
      const box = document.createElement("div");
      box.className = "item";
      const labelNode = document.createElement("span");
      labelNode.className = "label";
      labelNode.textContent = label;
      const valueNode = document.createElement("span");
      valueNode.className = `value ${className}`;
      valueNode.textContent = text(value);
      box.append(labelNode, valueNode);
      statusNode.append(box);
    }

    function waitForIceGathering(peer) {
      if (peer.iceGatheringState === "complete") return Promise.resolve();
      return new Promise((resolve) => {
        const finished = () => {
          peer.removeEventListener("icegatheringstatechange", changed);
          resolve();
        };
        const changed = () => { if (peer.iceGatheringState === "complete") finished(); };
        peer.addEventListener("icegatheringstatechange", changed);
        window.setTimeout(finished, 5000);
      });
    }

    function closeCamera(cameraId) {
      const connection = connections.get(cameraId);
      if (!connection) return;
      connections.delete(cameraId);
      connection.peer.close();
      if (connection.playbackSessionId) {
        fetch(`/cam-adapter/live/whep/${encodeURIComponent(connection.playbackSessionId)}`, {
          method: "DELETE", credentials: "same-origin", keepalive: true
        }).catch(() => undefined);
      }
    }

    async function connectCamera(camera, video, button, state) {
      closeCamera(camera.camera_id);
      button.disabled = true;
      state.textContent = "Connecting to live feed…";
      state.className = "";
      try {
        const peer = new RTCPeerConnection();
        peer.addTransceiver("video", { direction: "recvonly" });
        peer.ontrack = (event) => {
          video.srcObject = event.streams[0];
          video.play().catch(() => undefined);
          state.textContent = "Live";
          state.className = "ok";
        };
        peer.onconnectionstatechange = () => {
          if (["failed", "disconnected", "closed"].includes(peer.connectionState)) {
            state.textContent = "Connection ended";
            state.className = "warn";
          }
        };
        await peer.setLocalDescription(await peer.createOffer());
        await waitForIceGathering(peer);
        const response = await fetch(`/cam-adapter/live/whep/${encodeURIComponent(camera.camera_id)}`, {
          method: "POST",
          credentials: "same-origin",
          headers: { "Content-Type": "application/sdp", "Accept": "application/sdp" },
          body: peer.localDescription.sdp
        });
        if (!response.ok) throw new Error("Live camera is unavailable");
        await peer.setRemoteDescription({ type: "answer", sdp: await response.text() });
        connections.set(camera.camera_id, {
          peer,
          playbackSessionId: response.headers.get("X-HCAM-Playback-Session")
        });
        state.textContent = "Waiting for video…";
      } catch (_error) {
        state.textContent = "Live video is unavailable. Use Connect to retry.";
        state.className = "warn";
      } finally {
        button.disabled = false;
      }
    }

    function addLiveCamera(camera) {
      const card = document.createElement("article");
      card.className = "video-card";
      const title = document.createElement("div");
      title.className = "video-title";
      title.textContent = camera.location_label || camera.camera_id;
      const video = document.createElement("video");
      video.autoplay = true;
      video.muted = true;
      video.playsInline = true;
      video.controls = true;
      const controls = document.createElement("div");
      controls.className = "video-controls";
      const state = document.createElement("span");
      state.textContent = "Ready";
      const button = document.createElement("button");
      button.type = "button";
      button.textContent = "Connect";
      button.addEventListener("click", () => connectCamera(camera, video, button, state));
      controls.append(state, button);
      card.append(title, video, controls);
      videoList.append(card);
      return () => connectCamera(camera, video, button, state);
    }

    function renderLiveCameras(data) {
      for (const cameraId of Array.from(connections.keys())) closeCamera(cameraId);
      videoList.replaceChildren();
      if (!data.live_cameras_available) {
        videoNote.textContent = data.live_cameras_message || "Live footage is unavailable.";
        videoNote.className = "warn";
        return;
      }
      if (!data.live_cameras.length) {
        videoNote.textContent = "No approved live cameras are available.";
        videoNote.className = "empty";
        return;
      }
      videoNote.textContent = "The first approved live camera connects automatically. Use Connect for another camera.";
      videoNote.className = "ok";
      const starters = data.live_cameras.map(addLiveCamera);
      starters[0]();
    }

    function render(data) {
      statusNode.replaceChildren();
      const adapter = data.adapter;
      addStatus("Configuration", adapter.config_loaded ? "Loaded" : "Not loaded", adapter.config_loaded ? "ok" : "warn");
      addStatus("Live viewer", adapter.live_viewer_enabled ? "Enabled" : "Disabled", adapter.live_viewer_enabled ? "ok" : "warn");
      addStatus("Recorder", adapter.running ? "Running" : "Stopped", adapter.running ? "warn" : "ok");
      addStatus("Recording streams", adapter.streams_enabled);
      addStatus("Active workers", adapter.active_workers.length);
      addStatus("Camera limit", adapter.live_viewer_camera_limit);
      if (adapter.configuration_error) addStatus("Configuration note", adapter.configuration_error, "error");

      renderLiveCameras(data);

      cameraList.replaceChildren();
      if (!data.live_cameras_available) {
        cameraNote.textContent = data.live_cameras_message || "The live camera list is unavailable. Adapter status remains available.";
        cameraNote.className = "warn";
        return;
      }
      if (!data.live_cameras.length) {
        cameraNote.textContent = "No approved live cameras are available.";
        cameraNote.className = "empty";
        return;
      }
      cameraNote.textContent = `${data.live_cameras.length} approved live camera${data.live_cameras.length === 1 ? "" : "s"}.`;
      cameraNote.className = "ok";
      for (const camera of data.live_cameras) {
        const row = document.createElement("tr");
        const cameraCell = document.createElement("td");
        cameraCell.textContent = camera.location_label || camera.camera_id;
        const departmentCell = document.createElement("td");
        departmentCell.textContent = camera.department || "—";
        const stateCell = document.createElement("td");
        stateCell.textContent = "Approved for live viewer";
        stateCell.className = "ok";
        row.append(cameraCell, departmentCell, stateCell);
        cameraList.append(row);
      }
    }

    async function loadDashboard() {
      statusNode.replaceChildren();
      statusNode.textContent = "Loading adapter status…";
      try {
        const response = await fetch("/cam-adapter/dashboard/data", { credentials: "same-origin", cache: "no-store" });
        if (!response.ok) throw new Error("Dashboard session is unavailable.");
        render(await response.json());
      } catch (_error) {
        statusNode.textContent = "The dashboard backend is not available. Refresh after H-CAM starts.";
        cameraNote.textContent = "Live camera list was not requested because the dashboard backend is unavailable.";
        cameraNote.className = "error";
      }
    }

    document.getElementById("refresh").addEventListener("click", loadDashboard);
    window.addEventListener("pagehide", () => {
      for (const cameraId of Array.from(connections.keys())) closeCamera(cameraId);
    });
    loadDashboard();
  </script>
</body>
</html>"""
