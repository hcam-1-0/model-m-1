import { spawnSync } from "node:child_process";
import { createHash } from "node:crypto";
import { existsSync, mkdirSync, readFileSync, statSync, writeFileSync } from "node:fs";
import { join, resolve } from "node:path";
import process from "node:process";

const root = resolve(import.meta.dirname, "..");
const registry = "https://registry.npmjs.org/";
const npmExecPath = process.env.npm_execpath;
if (!npmExecPath) throw new Error("HCAM_AUDIT_PNPM_BINDING_MISSING");
const pnpm = resolve(npmExecPath);
if (!existsSync(pnpm) || !statSync(pnpm).isFile() || !/[\\/]pnpm\.mjs$/iu.test(pnpm)) {
  throw new Error("HCAM_AUDIT_PNPM_BINDING_INVALID");
}
const blockedEnvironmentKeys = new Set([
  "HTTP_PROXY",
  "HTTPS_PROXY",
  "ALL_PROXY",
  "NPM_CONFIG_PROXY",
  "NPM_CONFIG_HTTPS_PROXY",
]);
const env = Object.fromEntries(
  Object.entries(process.env).filter(([key]) => !blockedEnvironmentKeys.has(key)),
);
env.NPM_CONFIG_IGNORE_SCRIPTS = "true";
env.PLAYWRIGHT_SKIP_BROWSER_DOWNLOAD = "1";

const result = spawnSync(
  process.execPath,
  [pnpm, "audit", "--json", "--audit-level", "high", "--registry", registry],
  {
    cwd: root,
    env,
    encoding: "utf8",
    maxBuffer: 4 * 1024 * 1024,
    timeout: 60_000,
    windowsHide: true,
  },
);

if (result.error) throw result.error;
let report;
try {
  report = JSON.parse(result.stdout);
} catch {
  throw new Error("HCAM_AUDIT_OUTPUT_INVALID");
}

const rawCounts = report?.metadata?.vulnerabilities;
if (!rawCounts || typeof rawCounts !== "object") {
  throw new Error("HCAM_AUDIT_COUNTS_MISSING");
}
const counts = Object.fromEntries(
  ["info", "low", "moderate", "high", "critical", "total"].map((key) => [
    key,
    Number.isInteger(rawCounts[key]) ? rawCounts[key] : 0,
  ]),
);
const status = result.status === 0 && counts.high === 0 && counts.critical === 0 ? "pass" : "fail";
const sha256 = (path) =>
  createHash("sha256").update(readFileSync(path)).digest("hex").toUpperCase();
const evidence = {
  schema_version: "hcam.phase5.p5_3.dependency_audit.v1",
  workstream: "P5.3-W4",
  generated_on: "2026-09-08",
  generated_only: true,
  registry,
  package_manager: "pnpm@11.21.0",
  node: process.version,
  pnpm_bound_to_invoking_process: true,
  lockfile_sha256: sha256(join(root, "pnpm-lock.yaml")),
  proxy_environment_cleared_for_audit: true,
  lifecycle_scripts_enabled: false,
  browser_download_enabled: false,
  vulnerabilities: counts,
  unresolved_high_or_critical: counts.high + counts.critical,
  result: status,
};

mkdirSync(join(root, "evidence"), { recursive: true });
writeFileSync(
  join(root, "evidence", "p5-3-dependency-audit.json"),
  `${JSON.stringify(evidence, null, 2)}\n`,
  "utf8",
);
process.stdout.write(`${JSON.stringify(evidence)}\n`);
if (status !== "pass") process.exit(1);
