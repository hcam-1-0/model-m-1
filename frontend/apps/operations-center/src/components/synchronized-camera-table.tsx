import { ArrowUpRight, Radio } from "lucide-react";
import { Link } from "react-router";
import type { CameraProjection } from "@hcam/camera-live-domain";
import { CameraHealthBadge } from "./camera-health-badge";

export function SynchronizedCameraTable({
  cameras,
}: {
  readonly cameras: readonly CameraProjection[];
}) {
  if (!cameras.length)
    return (
      <div className="empty-state">
        <Radio size={24} />
        <strong>No generated cameras match</strong>
        <span>Change filters to restore the authoritative table.</span>
      </div>
    );
  return (
    <div className="table-scroll" tabIndex={0} aria-label="Scrollable generated camera table">
      <table className="camera-table">
        <caption className="sr-only">
          Generated camera catalogue synchronized with the visible list
        </caption>
        <thead>
          <tr>
            <th>Camera</th>
            <th>Location</th>
            <th>State</th>
            <th>Stream</th>
            <th>Freshness</th>
            <th>
              <span className="sr-only">Open</span>
            </th>
          </tr>
        </thead>
        <tbody>
          {cameras.map((camera) => {
            const stream = camera.streams[0];
            if (!stream) return null;
            return (
              <tr key={camera.id}>
                <td>
                  <strong>{camera.label}</strong>
                  <small>{camera.id}</small>
                </td>
                <td>
                  {camera.shortLocation}
                  <small>{camera.zone}</small>
                </td>
                <td>
                  <CameraHealthBadge health={camera.health} />
                  <small>{camera.state}</small>
                </td>
                <td>
                  {stream.state}
                  <small>{stream.preferredTransport.toUpperCase()}</small>
                </td>
                <td>
                  {camera.freshness.completeness}
                  <small>{camera.freshness.observedAt.slice(11, 16)} UTC</small>
                </td>
                <td>
                  <Link
                    className="row-link"
                    to={`/operations/cameras/${camera.id}`}
                    aria-label={`Open ${camera.label}`}
                  >
                    <ArrowUpRight size={16} />
                  </Link>
                </td>
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
}
