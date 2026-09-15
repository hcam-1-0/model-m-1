const forbiddenKeys = new Set([
  "url",
  "uri",
  "path",
  "filePath",
  "bucket",
  "objectKey",
  "token",
  "secret",
  "secretRef",
  "credential",
  "password",
  "cameraLocator",
  "sourceLocator",
  "signedUrl",
]);
const forbiddenValue =
  /(?:rtsp|whep|webrtc|file):\/\/|BEGIN PRIVATE KEY|Bearer\s+[A-Za-z0-9._-]+/iu;
export function findProhibitedGeneratedFields(
  value: unknown,
  prefix = "$",
  found: string[] = [],
): readonly string[] {
  if (typeof value === "string") {
    if (forbiddenValue.test(value)) found.push(prefix);
    return found;
  }
  if (!value || typeof value !== "object") return found;
  if (Array.isArray(value)) {
    value.forEach((item, index) =>
      findProhibitedGeneratedFields(item, `${prefix}[${index}]`, found),
    );
    return found;
  }
  for (const [key, item] of Object.entries(value)) {
    const child = `${prefix}.${key}`;
    if (forbiddenKeys.has(key)) found.push(child);
    findProhibitedGeneratedFields(item, child, found);
  }
  return [...new Set(found)];
}
