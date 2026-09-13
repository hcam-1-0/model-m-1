import { createHash } from "node:crypto";
import { existsSync, readFileSync } from "node:fs";
import { delimiter, resolve } from "node:path";
import process from "node:process";

const EXPECTED = Object.freeze({
  nodeVersion: "v24.18.0",
  pnpmVersion: "11.21.0",
  nodeSha256: "9A4EB5F1C29C6A2E93852EAD46B999E284A6A5CA8BAB4D4E241D587D025A52DE",
  pnpmPackageSha256: "D0FFE394C8507F627CCA00D09C690467EFD8138E78474330631C3B200AA2C56F",
  pnpmEntrypointSha256: "FF3224D46B47FBB24A7E9FE15FEDEDEF7E00892D07D4E376B6762D4899906BFD",
  pnpmBundleSha256: "293DCCED3C77F5A633352076FE4C9A768E60C6992ED58BC695B465F839FE9615",
});

function fail(code) {
  process.stderr.write(`${code}\n`);
  process.exit(1);
}

function sha256(path) {
  return createHash("sha256").update(readFileSync(path)).digest("hex").toUpperCase();
}

const nvmHome = process.env.NVM_HOME;
if (!nvmHome) fail("HCAM_TOOLCHAIN_NVM_HOME_MISSING");

const paths = Object.freeze({
  node: resolve(nvmHome, "v24.18.0", "node.exe"),
  pnpmPackage: resolve(nvmHome, "v26.5.0", "node_modules", "pnpm", "package.json"),
  pnpmEntrypoint: resolve(nvmHome, "v26.5.0", "node_modules", "pnpm", "bin", "pnpm.mjs"),
  pnpmBundle: resolve(nvmHome, "v26.5.0", "node_modules", "pnpm", "dist", "pnpm.mjs"),
});

if (process.version !== EXPECTED.nodeVersion) fail("HCAM_TOOLCHAIN_NODE_VERSION_MISMATCH");
if (sha256(paths.node) !== EXPECTED.nodeSha256) fail("HCAM_TOOLCHAIN_NODE_HASH_MISMATCH");
if (sha256(paths.pnpmPackage) !== EXPECTED.pnpmPackageSha256) {
  fail("HCAM_TOOLCHAIN_PNPM_PACKAGE_HASH_MISMATCH");
}
if (sha256(paths.pnpmEntrypoint) !== EXPECTED.pnpmEntrypointSha256) {
  fail("HCAM_TOOLCHAIN_PNPM_ENTRYPOINT_HASH_MISMATCH");
}
if (sha256(paths.pnpmBundle) !== EXPECTED.pnpmBundleSha256) {
  fail("HCAM_TOOLCHAIN_PNPM_BUNDLE_HASH_MISMATCH");
}

const pnpmPackage = JSON.parse(readFileSync(paths.pnpmPackage, "utf8"));
if (pnpmPackage.name !== "pnpm" || pnpmPackage.version !== EXPECTED.pnpmVersion) {
  fail("HCAM_TOOLCHAIN_PNPM_METADATA_MISMATCH");
}

const firstNodePathEntry = (process.env.PATH ?? "")
  .split(delimiter)
  .find((entry) => entry.length > 0 && existsSync(resolve(entry, "node.exe")));
if (!firstNodePathEntry || resolve(firstNodePathEntry) !== resolve(nvmHome, "v24.18.0")) {
  fail("HCAM_TOOLCHAIN_PATH_PRECEDENCE_MISMATCH");
}

process.stdout.write(
  `${JSON.stringify({ status: "pass", node: EXPECTED.nodeVersion, pnpm: EXPECTED.pnpmVersion })}\n`,
);
