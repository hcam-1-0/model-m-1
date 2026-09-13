import { createHash } from "node:crypto";
import { existsSync, readFileSync, statSync } from "node:fs";
import { dirname, resolve } from "node:path";
import process from "node:process";

const frontendRoot = resolve(import.meta.dirname, "..");
const repositoryRoot = resolve(frontendRoot, "..");
const packagePath = resolve(repositoryRoot, "contracts", "phase-5", "p5-7-evidence-package.json");

function sha256(path) {
  return createHash("sha256").update(readFileSync(path)).digest("hex").toUpperCase();
}
function readJson(path) {
  return JSON.parse(readFileSync(path, "utf8"));
}
function insideRepository(path) {
  const relative = path.slice(repositoryRoot.length);
  return (
    path.startsWith(repositoryRoot) &&
    !relative.includes("..") &&
    dirname(path).startsWith(repositoryRoot)
  );
}

const failures = [];
if (!existsSync(packagePath)) failures.push("evidence_package_missing");
if (failures.length === 0) {
  const evidencePackage = readJson(packagePath);
  const components = evidencePackage.components ?? [];
  if (evidencePackage.status !== "owner_acceptance_required" || evidencePackage.effective !== false)
    failures.push("evidence_package_state");
  if (components.length === 0) failures.push("component_set_empty");
  for (const component of components) {
    const path = resolve(repositoryRoot, component.path);
    if (!insideRepository(path) || !existsSync(path)) {
      failures.push(`component_missing:${component.path}`);
      continue;
    }
    if (statSync(path).size !== component.bytes) failures.push(`component_bytes:${component.path}`);
    if (sha256(path) !== component.sha256) failures.push(`component_hash:${component.path}`);
  }
  const canonical = components
    .slice()
    .sort((left, right) => left.path.localeCompare(right.path, "en"))
    .map(({ path, bytes, sha256: hash }) => `${path}|${bytes}|${hash}`)
    .join("\n");
  const digest = createHash("sha256")
    .update(Buffer.from(canonical, "utf8"))
    .digest("hex")
    .toUpperCase();
  if (digest !== evidencePackage.canonical_component_digest) failures.push("component_digest");
  const graph = readJson(resolve(frontendRoot, "evidence", "p5-7-evidence-graph.json"));
  const ids = new Set(graph.nodes.map(({ id }) => id));
  if (ids.size !== graph.nodes.length) failures.push("evidence_graph_duplicate");
  for (const node of graph.nodes)
    for (const dependency of node.depends_on)
      if (!ids.has(dependency)) failures.push(`evidence_graph_missing:${node.id}`);
  if (graph.acyclic !== true) failures.push("evidence_graph_cycle");
  const release = readJson(resolve(frontendRoot, "evidence", "p5-7-release-manifest.json"));
  if (release.release_authorized !== false || release.deployment_authorized !== false)
    failures.push("release_authority");
  if (release.generated_only !== true) failures.push("release_generated_boundary");
}
const result = {
  status: failures.length ? "fail" : "pass",
  package_sha256: existsSync(packagePath) ? sha256(packagePath) : null,
  failures,
};
process.stdout.write(`${JSON.stringify(result)}\n`);
if (failures.length) process.exit(1);
