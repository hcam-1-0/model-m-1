const prohibited =
  /(?:password|secret_value|access_token|refresh_token|private_key|credential|connection_string)/iu;
export function isOpaqueSecretReference(value: unknown): value is string {
  return typeof value === "string" && /^SYN-SECRET-REF-[A-Z0-9-]{4,48}$/u.test(value);
}
export function sanitizeProjection(value: Record<string, unknown>): Record<string, unknown> {
  return Object.fromEntries(
    Object.entries(value)
      .filter(([key]) => !prohibited.test(key))
      .map(([key, item]) => [
        key,
        typeof item === "string" && prohibited.test(item) ? "[REDACTED]" : item,
      ]),
  );
}
export function containsProhibitedSecretField(value: unknown): boolean {
  if (!value || typeof value !== "object") return false;
  if (Array.isArray(value)) return value.some(containsProhibitedSecretField);
  return Object.entries(value).some(
    ([key, item]) => prohibited.test(key) || containsProhibitedSecretField(item),
  );
}
