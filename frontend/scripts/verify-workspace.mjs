import { mkdirSync, readdirSync, readFileSync, statSync, writeFileSync } from "node:fs";
import { join, relative, resolve } from "node:path";
import process from "node:process";

const root = resolve(import.meta.dirname, "..");
const expectedApps = [
  "admin-center",
  "command-center",
  "evidence-center",
  "gis-center",
  "intelligence-center",
  "investigation-center",
  "operations-center",
  "security-center",
];
const expectedPackages = [
  "admin-contracts",
  "admin-security-operations-fixtures",
  "api-client",
  "app-shell",
  "auth-session",
  "camera-live-domain",
  "capabilities",
  "command-domain",
  "contracts",
  "design-tokens",
  "event-invalidation",
  "evidence-domain",
  "gis-contracts",
  "gis-domain",
  "gis-renderers",
  "governance-domain",
  "i18n",
  "intelligence-contracts",
  "intelligence-domain",
  "intelligence-fixtures",
  "investigation-contracts",
  "investigation-domain",
  "investigation-fixtures",
  "media-adapters",
  "media-edge-contracts",
  "navigation",
  "observability",
  "operations-contracts",
  "platform-operations-domain",
  "playback-contracts",
  "quality-contracts",
  "quality-domain",
  "quality-fixtures",
  "quality-harness",
  "query-policy",
  "relationship-renderers",
  "review-workflows",
  "security-contracts",
  "test-fixtures",
  "test-support",
  "ui",
];
const failures = [];
function names(group) {
  return readdirSync(join(root, group), { withFileTypes: true })
    .filter((entry) => entry.isDirectory())
    .map((entry) => entry.name)
    .sort();
}
function files(path) {
  return readdirSync(path, { withFileTypes: true }).flatMap((entry) =>
    entry.isDirectory() && entry.name !== "node_modules" && entry.name !== "dist"
      ? files(join(path, entry.name))
      : entry.isFile()
        ? [join(path, entry.name)]
        : [],
  );
}
if (JSON.stringify(names("apps")) !== JSON.stringify(expectedApps))
  failures.push("portal_set_mismatch");
if (JSON.stringify(names("packages")) !== JSON.stringify(expectedPackages))
  failures.push("package_set_mismatch");
const manifests = new Map();
for (const group of ["apps", "packages"])
  for (const dir of names(group)) {
    const path = join(root, group, dir);
    const manifest = JSON.parse(readFileSync(join(path, "package.json"), "utf8"));
    manifests.set(manifest.name, { path, manifest });
  }
const edges = new Map(
  [...manifests].map(([name, value]) => [
    name,
    Object.keys({ ...value.manifest.dependencies, ...value.manifest.devDependencies }).filter(
      (dependency) => manifests.has(dependency),
    ),
  ]),
);
function visit(name, visiting = new Set(), visited = new Set()) {
  if (visiting.has(name)) {
    failures.push(`cycle:${name}`);
    return;
  }
  if (visited.has(name)) return;
  visiting.add(name);
  for (const dependency of edges.get(name) ?? []) visit(dependency, visiting, visited);
  visiting.delete(name);
  visited.add(name);
}
for (const name of edges.keys()) visit(name);
for (const [name, value] of manifests) {
  if (value.manifest.private !== true || value.manifest.version !== "0.1.0")
    failures.push(`manifest_policy:${name}`);
  if (name.endsWith("-center"))
    for (const dependency of edges.get(name) ?? [])
      if (dependency.endsWith("-center")) failures.push(`portal_cross_import:${name}`);
}
for (const path of files(root).filter((path) => /\.(?:ts|tsx|mjs)$/.test(path))) {
  const text = readFileSync(path, "utf8");
  if (/from\s+["']@hcam\/[^"']+\/src\//.test(text))
    failures.push(`deep_import:${relative(root, path)}`);
  if (
    text.includes("hcam-1-0/final-ui") &&
    !path.includes(`${join("scripts", "verify-workspace")}`)
  )
    failures.push(`reference_source_import:${relative(root, path)}`);
}
const lockfiles = files(root).filter((path) => path.endsWith("pnpm-lock.yaml"));
if (lockfiles.length !== 1) failures.push("lockfile_count");
for (const control of ["package.json", "pnpm-workspace.yaml", "tsconfig.base.json", ".npmrc"])
  if (!statSync(join(root, control)).isFile()) failures.push(`missing_control:${control}`);
const result = {
  status: failures.length ? "fail" : "pass",
  apps: expectedApps.length,
  packages: expectedPackages.length,
  edges: [...edges.values()].reduce((sum, value) => sum + value.length, 0),
  lockfiles: lockfiles.length,
  failures: failures.sort(),
};
mkdirSync(join(root, "test-results"), { recursive: true });
writeFileSync(
  join(root, "test-results", "workspace-verification.json"),
  `${JSON.stringify(result, null, 2)}\n`,
  "utf8",
);
process.stdout.write(`${JSON.stringify(result)}\n`);
if (failures.length) process.exit(1);
