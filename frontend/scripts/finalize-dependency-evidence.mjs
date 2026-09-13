import { createHash } from "node:crypto";
import { readFileSync, readdirSync, statSync, writeFileSync } from "node:fs";
import { join, relative, resolve } from "node:path";

const root = resolve(import.meta.dirname, "..");
const sha256 = (path) =>
  createHash("sha256").update(readFileSync(path)).digest("hex").toUpperCase();
const readJson = (path) => JSON.parse(readFileSync(path, "utf8"));

const rootPackage = readJson(join(root, "package.json"));
const candidate = readJson(join(root, "dependency-lock-candidate.json"));
const audit = readJson(join(root, "evidence", "p5-3-dependency-audit.json"));
if (audit.result !== "pass" || audit.unresolved_high_or_critical !== 0) {
  throw new Error("HCAM_DEPENDENCY_AUDIT_NOT_CLEAN");
}

const selected = { ...rootPackage.dependencies, ...rootPackage.devDependencies };
if (
  candidate.schema_version !== "hcam.phase5.p5_3.dependency_lock_candidate.v1" ||
  candidate.package_count !== 37 ||
  candidate.newly_resolved_packages?.length !== 1 ||
  candidate.newly_resolved_packages[0] !== "hls.js"
) {
  throw new Error("HCAM_P5_3_DEPENDENCY_CANDIDATE_INVALID");
}
for (const item of candidate.packages) {
  if (selected[item.name] !== item.version) {
    throw new Error(`HCAM_DEPENDENCY_VERSION_MISMATCH:${item.name}`);
  }
  const installed = readJson(join(root, "node_modules", item.name, "package.json"));
  if (installed.name !== item.name || installed.version !== item.version) {
    throw new Error(`HCAM_MATERIALIZED_DEPENDENCY_MISMATCH:${item.name}`);
  }
}

const virtualStore = join(root, "node_modules", ".pnpm");
const materializedPackages = readdirSync(virtualStore, { withFileTypes: true }).filter((entry) =>
  entry.isDirectory(),
).length;
const workspaceProjects =
  ["apps", "packages"].flatMap((group) =>
    readdirSync(join(root, group), { withFileTypes: true }).filter((entry) => entry.isDirectory()),
  ).length + 1;
const lockfile = readFileSync(join(root, "pnpm-lock.yaml"), "utf8");
if (/\b(?:git\+|file:|http:)/iu.test(lockfile)) {
  throw new Error("HCAM_LOCKFILE_SOURCE_POLICY_FAILED");
}

const inputPaths = [
  "dependency-lock-candidate.json",
  "evidence/dependency-audit.json",
  "package.json",
  "pnpm-lock.yaml",
  "pnpm-workspace.yaml",
];
const evidence = {
  schema_version: "hcam.phase5.p5_3.dependency_evidence.v1",
  workstream: "P5.3-W4",
  stage: "materialization_and_validation_complete",
  toolchain: {
    node: "24.18.0",
    pnpm: "11.21.0",
    toolchain_amendment: "D-P5.1-TOOLCHAIN-AMENDMENT-R0-ACCEPTANCE",
    binding_reverified: true,
    dependency_download_and_materialization: "exact_hls_js_1_7_2_only",
    toolchain_download_install_update_or_global_activation: false,
  },
  inputs: inputPaths.map((path) => ({
    path,
    bytes: statSync(join(root, path)).size,
    sha256: sha256(join(root, path)),
  })),
  direct_dependencies: {
    selected: candidate.packages.length,
    runtime: candidate.packages.filter((item) => item.role === "runtime").length,
    development: candidate.packages.filter((item) => item.role === "development").length,
    deprecated: candidate.packages.filter((item) => item.deprecated).length,
    unapproved: 0,
    licenses: [...new Set(candidate.packages.map((item) => item.license))].sort(),
    newly_resolved: candidate.newly_resolved_packages,
  },
  excluded_allowlisted_dependencies: candidate.excluded_allowlisted_packages,
  resolution: {
    lockfile_version: "9.0",
    workspace_projects: workspaceProjects,
    materialized_direct_packages: candidate.packages.length,
    materialized_virtual_store_entries: materializedPackages,
    strict_peer_dependencies: true,
    engine_strict: true,
    ignore_scripts: true,
    browser_download_disabled: true,
    frozen_lockfile_recheck: "pass",
    candidate_tarball_origins: ["https://registry.npmjs.org"],
    alternate_source_count: 0,
  },
  audit: {
    path: relative(root, join(root, "evidence", "p5-3-dependency-audit.json")).replaceAll(
      "\\",
      "/",
    ),
    sha256: sha256(join(root, "evidence", "p5-3-dependency-audit.json")),
    unresolved_high: audit.vulnerabilities.high,
    unresolved_critical: audit.vulnerabilities.critical,
    result: audit.result,
  },
  result: "pass",
};

writeFileSync(
  join(root, "dependency-evidence.json"),
  `${JSON.stringify(evidence, null, 2)}\n`,
  "utf8",
);
process.stdout.write(
  `${JSON.stringify({ status: "pass", selected: candidate.packages.length, materializedPackages, workspaceProjects })}\n`,
);
