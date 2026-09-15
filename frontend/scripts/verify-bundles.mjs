import { mkdirSync, readdirSync, readFileSync, writeFileSync } from "node:fs";
import { join, relative, resolve } from "node:path";
import process from "node:process";
const root = resolve(import.meta.dirname, "..");
function files(path) {
  return readdirSync(path, { withFileTypes: true }).flatMap((entry) =>
    entry.isDirectory()
      ? files(join(path, entry.name))
      : entry.isFile()
        ? [join(path, entry.name)]
        : [],
  );
}
const failures = [];
const generatedMarkerApps = new Set([
  "admin-center",
  "command-center",
  "evidence-center",
  "gis-center",
  "intelligence-center",
  "investigation-center",
  "operations-center",
  "security-center",
]);
const observedGeneratedMarkerApps = new Set();
const applicationBudgets = {
  "admin-center": {
    initialJavaScript: 320 * 1024,
    styles: 24 * 1024,
  },
  "operations-center": {
    initialJavaScript: 360 * 1024,
    deferredHlsJavaScript: 640 * 1024,
    styles: 40 * 1024,
  },
  "security-center": {
    initialJavaScript: 320 * 1024,
    styles: 24 * 1024,
  },
};
const observedBudgets = {};
let bytes = 0;
let appCount = 0;
for (const entry of readdirSync(join(root, "apps"), { withFileTypes: true })) {
  if (!entry.isDirectory()) continue;
  const dist = join(root, "apps", entry.name, "dist");
  const output = files(dist);
  appCount += 1;
  if (output.some((path) => path.endsWith(".map"))) failures.push(`source_map:${entry.name}`);
  for (const path of output) {
    bytes += readFileSync(path).byteLength;
    if (!/\.(?:js|css|html)$/.test(path)) failures.push(`unexpected_asset:${relative(root, path)}`);
    const text = readFileSync(path, "utf8");
    const containsGeneratedMarker = /HCAM-GENERATED-NON-OPERATIONAL/.test(text);
    if (containsGeneratedMarker) observedGeneratedMarkerApps.add(entry.name);
    if (
      /(?:rtsp|whep|webrtc):\/\//i.test(text) ||
      (containsGeneratedMarker && !generatedMarkerApps.has(entry.name)) ||
      /sourceMappingURL=/.test(text)
    )
      failures.push(`forbidden_content:${relative(root, path)}`);
  }
  const budget = applicationBudgets[entry.name];
  if (budget) {
    const javascript = output.filter((path) => path.endsWith(".js"));
    const initial = javascript.find((path) => !/[\\/]hls(?:[.-]|$)/iu.test(path));
    const deferredHls = javascript.find((path) => /[\\/]hls(?:[.-]|$)/iu.test(path));
    const styles = output
      .filter((path) => path.endsWith(".css"))
      .reduce((total, path) => total + statSize(path), 0);
    const actual = {
      initialJavaScript: initial ? statSize(initial) : 0,
      deferredHlsJavaScript: deferredHls ? statSize(deferredHls) : 0,
      styles,
    };
    observedBudgets[entry.name] = { limits: budget, actual };
    if (!initial) failures.push(`missing_initial_bundle:${entry.name}`);
    if ("deferredHlsJavaScript" in budget && !deferredHls)
      failures.push(`missing_deferred_hls_bundle:${entry.name}`);
    for (const [name, limit] of Object.entries(budget))
      if (actual[name] > limit) failures.push(`bundle_budget:${entry.name}:${name}`);
  }
}
for (const app of generatedMarkerApps)
  if (!observedGeneratedMarkerApps.has(app)) failures.push(`missing_generated_marker:${app}`);
const result = {
  status: failures.length ? "fail" : "pass",
  apps: appCount,
  outputBytes: bytes,
  sourceMaps: 0,
  generatedMarkerApps: [...observedGeneratedMarkerApps].sort(),
  applicationBudgets: observedBudgets,
  failures: failures.sort(),
};
mkdirSync(join(root, "test-results"), { recursive: true });
writeFileSync(
  join(root, "test-results", "bundle-verification.json"),
  `${JSON.stringify(result, null, 2)}\n`,
  "utf8",
);
process.stdout.write(`${JSON.stringify(result)}\n`);
if (failures.length) process.exit(1);

function statSize(path) {
  return readFileSync(path).byteLength;
}
