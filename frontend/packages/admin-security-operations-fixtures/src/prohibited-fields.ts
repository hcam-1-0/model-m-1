export const prohibitedProjectionKeys = Object.freeze([
  "password",
  "secretValue",
  "accessToken",
  "refreshToken",
  "privateKey",
  "connectionString",
  "rawLog",
  "mediaUrl",
  "modelArtifact",
  "executableInstruction",
] as const);
const forbiddenKey =
  /^(?:password|secretValue|accessToken|refreshToken|privateKey|connectionString|rawLog|mediaUrl|modelArtifact|executableInstruction)$/iu;
const forbiddenValue = /(?:rtsp|whep|webrtc):\/\/|BEGIN PRIVATE KEY|Bearer\s+[A-Za-z0-9._-]+/iu;
export function scanGeneratedProjection(value: unknown, path = "$root"): readonly string[] {
  if (typeof value === "string")
    return forbiddenValue.test(value) ? [`${path}:forbidden_value`] : [];
  if (!value || typeof value !== "object") return [];
  if (Array.isArray(value))
    return value.flatMap((item, index) => scanGeneratedProjection(item, `${path}[${index}]`));
  return Object.entries(value).flatMap(([key, item]) => [
    ...(forbiddenKey.test(key) ? [`${path}.${key}:forbidden_key`] : []),
    ...scanGeneratedProjection(item, `${path}.${key}`),
  ]);
}
