import type { GisProviderDefinition } from "@hcam/gis-contracts";

export function validateDisabledProvider(provider: GisProviderDefinition): boolean {
  if (
    !/^[a-z][a-z0-9-]{2,31}$/.test(provider.id) ||
    provider.purpose.length < 3 ||
    provider.purpose.length > 120
  )
    return false;
  try {
    const destination = new URL(provider.destination);
    return (
      destination.protocol === "https:" &&
      !destination.username &&
      !destination.password &&
      destination.pathname === "/" &&
      !destination.search &&
      !destination.hash
    );
  } catch {
    return false;
  }
}
export function providerRuntimeAllowed(): false {
  return false;
}
