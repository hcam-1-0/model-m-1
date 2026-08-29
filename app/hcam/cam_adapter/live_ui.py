from __future__ import annotations


LIVE_VIEWER_HTML = r"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <meta name="referrer" content="no-referrer">
  <title>H-CAM Live Viewer</title>
  <style>
    :root { color-scheme: dark; font-family: Inter, ui-sans-serif, system-ui, sans-serif; }
    body { margin: 0; min-width: 320px; background: #08111f; color: #e8eef8; }
    header { padding: 24px clamp(20px, 4vw, 56px); border-bottom: 1px solid #213048; background: #0c182b; }
    h1 { margin: 0; font-size: clamp(1.35rem, 2vw, 2rem); letter-spacing: .02em; }
    header p { margin: 8px 0 0; color: #a9b8ce; max-width: 70ch; }
    #notice { min-height: 1.4rem; margin: 16px clamp(20px, 4vw, 56px); color: #b9c8dd; }
    #notice.error { color: #ffb4ab; }
    main { padding: 0 clamp(20px, 4vw, 56px) 48px; }
    #cameras { display: grid; grid-template-columns: repeat(auto-fit, minmax(290px, 1fr)); gap: 18px; }
    .camera { overflow: hidden; border: 1px solid #2a3a55; border-radius: 14px; background: #101d31; box-shadow: 0 12px 30px #0004; }
    .camera-header { display: flex; gap: 12px; justify-content: space-between; align-items: center; padding: 14px 16px; }
    .camera-name { font-weight: 700; overflow-wrap: anywhere; }
    .camera-subtitle { color: #a9b8ce; font-size: .9rem; margin-top: 3px; }
    video { display: block; width: 100%; aspect-ratio: 16 / 9; background: #050a12; object-fit: contain; }
    button { border: 1px solid #476a94; border-radius: 8px; padding: 8px 11px; color: #eaf3ff; background: #173557; cursor: pointer; font: inherit; }
    button:hover:not(:disabled) { background: #21486f; }
    button:disabled { cursor: wait; opacity: .65; }
    .status { padding: 10px 16px 14px; min-height: 1.2rem; color: #a9b8ce; font-size: .9rem; }
    .live { color: #89e5a6; }
  </style>
</head>
<body>
  <header>
    <h1>H-CAM Live Viewer</h1>
    <p>Low-latency browser playback. This viewer does not record video, save clips, or expose upstream stream URLs.</p>
  </header>
  <div id="notice" role="status">Loading approved live cameras…</div>
  <main><section id="cameras" aria-live="polite"></section></main>
  <script>
    "use strict";
    const cameras = document.getElementById("cameras");
    const notice = document.getElementById("notice");
    const connections = new Map();

    function showNotice(message, isError = false) {
      notice.textContent = message;
      notice.className = isError ? "error" : "";
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

    async function closeCamera(cameraId) {
      const current = connections.get(cameraId);
      if (!current) return;
      connections.delete(cameraId);
      current.peer.close();
      if (current.playbackSessionId) {
        fetch(`/cam-adapter/live/whep/${encodeURIComponent(current.playbackSessionId)}`, {
          method: "DELETE", credentials: "same-origin", keepalive: true
        }).catch(() => undefined);
      }
    }

    async function startCamera(camera, video, button, status) {
      await closeCamera(camera.camera_id);
      button.disabled = true;
      status.textContent = "Connecting to live feed…";
      try {
        const peer = new RTCPeerConnection();
        peer.addTransceiver("video", { direction: "recvonly" });
        peer.ontrack = (event) => {
          video.srcObject = event.streams[0];
          video.play().catch(() => undefined);
          status.textContent = "Live";
          status.className = "status live";
        };
        peer.onconnectionstatechange = () => {
          if (["failed", "disconnected", "closed"].includes(peer.connectionState)) {
            status.textContent = "Connection ended. Select Connect to try again.";
            status.className = "status";
          }
        };
        const offer = await peer.createOffer();
        await peer.setLocalDescription(offer);
        await waitForIceGathering(peer);
        const response = await fetch(`/cam-adapter/live/whep/${encodeURIComponent(camera.camera_id)}`, {
          method: "POST",
          credentials: "same-origin",
          headers: { "Content-Type": "application/sdp", "Accept": "application/sdp" },
          body: peer.localDescription.sdp
        });
        if (!response.ok) throw new Error("The live feed could not be started.");
        const answer = await response.text();
        await peer.setRemoteDescription({ type: "answer", sdp: answer });
        connections.set(camera.camera_id, {
          peer,
          playbackSessionId: response.headers.get("X-HCAM-Playback-Session")
        });
        status.textContent = "Waiting for live video…";
      } catch (_error) {
        status.textContent = "Live feed is not available right now. Try again shortly.";
        status.className = "status";
      } finally {
        button.disabled = false;
      }
    }

    function addCamera(camera) {
      const card = document.createElement("article");
      card.className = "camera";
      const header = document.createElement("div");
      header.className = "camera-header";
      const label = document.createElement("div");
      const name = document.createElement("div");
      name.className = "camera-name";
      name.textContent = camera.location_label || camera.camera_id;
      const subtitle = document.createElement("div");
      subtitle.className = "camera-subtitle";
      subtitle.textContent = camera.department || "Approved live camera";
      label.append(name, subtitle);
      const button = document.createElement("button");
      button.type = "button";
      button.textContent = "Connect";
      header.append(label, button);
      const video = document.createElement("video");
      video.autoplay = true;
      video.muted = true;
      video.playsInline = true;
      video.controls = true;
      const status = document.createElement("div");
      status.className = "status";
      status.textContent = "Ready to connect";
      button.addEventListener("click", () => startCamera(camera, video, button, status));
      card.append(header, video, status);
      cameras.append(card);
      return () => startCamera(camera, video, button, status);
    }

    async function loadCameras() {
      try {
        const response = await fetch("/cam-adapter/live/cameras", { credentials: "same-origin" });
        if (!response.ok) throw new Error("Live viewer session is unavailable.");
        const payload = await response.json();
        if (!payload.cameras.length) {
          showNotice("No approved live cameras are currently available.");
          return;
        }
        const starters = payload.cameras.map(addCamera);
        showNotice(`${payload.cameras.length} approved live camera${payload.cameras.length === 1 ? "" : "s"} ready.`, false);
        starters[0]();
      } catch (_error) {
        showNotice("This live-viewer session has expired or the approved catalogue is unavailable. Create a new local session and reopen the viewer.", true);
      }
    }

    window.addEventListener("pagehide", () => {
      for (const cameraId of Array.from(connections.keys())) closeCamera(cameraId);
    });
    loadCameras();
  </script>
</body>
</html>"""
