import type { GisTimeWindow } from "@hcam/gis-contracts";

export function validateTimeWindow(window: GisTimeWindow): boolean {
  const from = Date.parse(window.from);
  const to = Date.parse(window.to);
  const server = Date.parse(window.serverNow);
  return (
    Number.isFinite(from) &&
    Number.isFinite(to) &&
    Number.isFinite(server) &&
    from < to &&
    to <= server &&
    to - from <= 86_400_000
  );
}
export function clampTimeWindow(window: GisTimeWindow): GisTimeWindow {
  const server = Date.parse(window.serverNow);
  const to = Math.min(Date.parse(window.to), server);
  const from = Math.max(Date.parse(window.from), to - 86_400_000);
  return {
    from: new Date(from).toISOString(),
    to: new Date(to).toISOString(),
    serverNow: new Date(server).toISOString(),
  };
}
