export interface CameraHandoff {
  readonly contractVersion: "1.0.0";
  readonly cameraRef: string;
  readonly streamRef: string | null;
  readonly departmentRef: string;
  readonly sourceRevision: string;
  readonly expiresAt: string;
  readonly purpose: "view_generated_camera";
}
const safeReference = /^SYN-[A-Z0-9-]{3,48}$/u;
export function validateHandoff(value: unknown, now: Date): value is CameraHandoff {
  if (!value || typeof value !== "object") return false;
  const item = value as Partial<CameraHandoff>;
  return (
    item.contractVersion === "1.0.0" &&
    typeof item.cameraRef === "string" &&
    safeReference.test(item.cameraRef) &&
    (item.streamRef === null ||
      (typeof item.streamRef === "string" && safeReference.test(item.streamRef))) &&
    typeof item.departmentRef === "string" &&
    safeReference.test(item.departmentRef) &&
    typeof item.sourceRevision === "string" &&
    safeReference.test(item.sourceRevision) &&
    item.purpose === "view_generated_camera" &&
    typeof item.expiresAt === "string" &&
    Date.parse(item.expiresAt) > now.getTime()
  );
}
export function serializeHandoff(value: CameraHandoff): string {
  if (!validateHandoff(value, new Date("2026-09-08T00:00:00.000Z")))
    throw new Error("invalid_generated_handoff");
  return encodeURIComponent(JSON.stringify(value));
}
