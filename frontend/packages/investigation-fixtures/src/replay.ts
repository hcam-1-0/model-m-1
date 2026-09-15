import { generatedContractCases } from "./cases";

export function canonicalGeneratedJson(value: unknown): string {
  if (Array.isArray(value)) return `[${value.map(canonicalGeneratedJson).join(",")}]`;
  if (value && typeof value === "object")
    return `{${Object.entries(value)
      .sort(([left], [right]) => left.localeCompare(right))
      .map(([key, item]) => `${JSON.stringify(key)}:${canonicalGeneratedJson(item)}`)
      .join(",")}}`;
  return JSON.stringify(value);
}
export function deterministicGeneratedDigest(value: unknown): string {
  const text = canonicalGeneratedJson(value);
  let hash = 2166136261;
  for (let index = 0; index < text.length; index += 1) {
    hash ^= text.charCodeAt(index);
    hash = Math.imul(hash, 16777619);
  }
  return `SYN-FNV1A-${(hash >>> 0).toString(16).toUpperCase().padStart(8, "0")}`;
}
export const generatedReplayManifest = Object.freeze({
  seed: "HCAM-P5.5-R0-2026-09-09",
  cases: generatedContractCases.length,
  digest: deterministicGeneratedDigest(generatedContractCases),
  runsRequired: 2,
  generated: true,
});
