export const LOCAL_GUJARAT_STYLE = "/gis/styles/operational-fallback.json";
export const DEVELOPMENT_BASEMAP_STYLE =
  "https://basemaps.cartocdn.com/gl/dark-matter-gl-style/style.json";

const LOOPBACK_HOSTS = new Set(["127.0.0.1", "localhost", "::1"]);

export function isLoopbackHostname(hostname: string): boolean {
  return LOOPBACK_HOSTS.has(hostname.toLowerCase());
}

export function resolveOperationalStyle(hostname: string, configuredStyle?: string): string {
  if (isLoopbackHostname(hostname)) return DEVELOPMENT_BASEMAP_STYLE;
  return configuredStyle ?? LOCAL_GUJARAT_STYLE;
}

export function isDevelopmentBasemap(styleUrl: string): boolean {
  return styleUrl === DEVELOPMENT_BASEMAP_STYLE;
}
