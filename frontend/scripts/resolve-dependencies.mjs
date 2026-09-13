import { createHash } from "node:crypto";
import { mkdirSync, readFileSync, writeFileSync } from "node:fs";
import https from "node:https";
import { dirname, resolve } from "node:path";
import process from "node:process";

const REGISTRY = "https://registry.npmjs.org";
const OUTPUT = resolve(process.cwd(), "dependency-lock-candidate.json");
const MAX_RESPONSE_BYTES = 32 * 1024 * 1024;
const PREVIOUS_CANDIDATE_SHA256 =
  "B1C9123CDB7E6A22D8F90E4FA97A7F1A5233F46BBE161EE36C1D80BA57D860FA";
const requested = Object.freeze(["hls.js", "1.7.2", "runtime"]);

function fail(code) {
  throw new Error(code);
}

function packagePath(name, selector) {
  const encodedName = name.startsWith("@")
    ? `@${encodeURIComponent(name.slice(1))}`
    : encodeURIComponent(name);
  return `/${encodedName}/${encodeURIComponent(selector)}`;
}

function fetchJson(path, accept = "application/json") {
  return new Promise((resolveRequest, reject) => {
    const request = https.get(
      `${REGISTRY}${path}`,
      {
        headers: {
          Accept: accept,
          "User-Agent": "hcam-p5.3-dependency-resolver/1.0",
        },
        timeout: 20_000,
      },
      (response) => {
        if (response.statusCode !== 200) {
          response.resume();
          reject(new Error(`HCAM_REGISTRY_STATUS_${response.statusCode}`));
          return;
        }
        if (response.headers.location) {
          response.resume();
          reject(new Error("HCAM_REGISTRY_REDIRECT_REJECTED"));
          return;
        }
        const declaredLength = Number(response.headers["content-length"] ?? 0);
        if (Number.isFinite(declaredLength) && declaredLength > MAX_RESPONSE_BYTES) {
          response.resume();
          reject(new Error("HCAM_REGISTRY_RESPONSE_TOO_LARGE"));
          return;
        }
        const chunks = [];
        let bytes = 0;
        response.on("data", (chunk) => {
          bytes += chunk.length;
          if (bytes > MAX_RESPONSE_BYTES) {
            request.destroy(new Error("HCAM_REGISTRY_RESPONSE_TOO_LARGE"));
            return;
          }
          chunks.push(chunk);
        });
        response.on("end", () => {
          try {
            resolveRequest(JSON.parse(Buffer.concat(chunks).toString("utf8")));
          } catch {
            reject(new Error("HCAM_REGISTRY_JSON_INVALID"));
          }
        });
      },
    );
    request.on("timeout", () => request.destroy(new Error("HCAM_REGISTRY_TIMEOUT")));
    request.on("error", reject);
  });
}

function normalizeLicense(value) {
  if (typeof value === "string" && value.length > 0 && value.length <= 80) return value;
  if (value && typeof value.type === "string" && value.type.length <= 80) return value.type;
  fail("HCAM_DEPENDENCY_LICENSE_MISSING");
}

function assertPlainObject(value, code) {
  if (value === undefined) return {};
  if (!value || typeof value !== "object" || Array.isArray(value)) fail(code);
  return Object.fromEntries(
    Object.entries(value)
      .filter(([key, item]) => typeof key === "string" && typeof item === "string")
      .sort(([left], [right]) => left.localeCompare(right)),
  );
}

function normalizeMaintainers(value) {
  if (!Array.isArray(value)) fail("HCAM_DEPENDENCY_MAINTAINERS_MISSING");
  return value
    .map((item) => (item && typeof item.name === "string" ? item.name : ""))
    .filter((item) => item.length > 0 && item.length <= 120)
    .sort();
}

async function resolvePackage([name, selector, role]) {
  const metadata = await fetchJson(packagePath(name, selector));
  const packument = await fetchJson(`/${encodeURIComponent(name)}`, "application/json");
  if (metadata.name !== name) fail("HCAM_DEPENDENCY_NAME_MISMATCH");
  if (typeof metadata.version !== "string" || /-/.test(metadata.version)) {
    fail("HCAM_DEPENDENCY_VERSION_INVALID");
  }
  if (!metadata.dist || typeof metadata.dist.integrity !== "string") {
    fail("HCAM_DEPENDENCY_INTEGRITY_MISSING");
  }
  const tarball = new URL(metadata.dist.tarball);
  if (tarball.protocol !== "https:" || tarball.hostname !== "registry.npmjs.org") {
    fail("HCAM_DEPENDENCY_TARBALL_ORIGIN_REJECTED");
  }
  const releaseDate = packument?.time?.[metadata.version];
  if (typeof releaseDate !== "string" || !Number.isFinite(Date.parse(releaseDate))) {
    fail("HCAM_DEPENDENCY_RELEASE_DATE_MISSING");
  }
  const maintainers = normalizeMaintainers(metadata.maintainers);
  if (maintainers.length === 0) fail("HCAM_DEPENDENCY_MAINTAINERS_MISSING");
  return {
    name,
    requested: selector,
    role,
    version: metadata.version,
    integrity: metadata.dist.integrity,
    metadata_sha256: createHash("sha256")
      .update(JSON.stringify(metadata))
      .digest("hex")
      .toUpperCase(),
    license: normalizeLicense(metadata.license),
    engines: assertPlainObject(metadata.engines, "HCAM_DEPENDENCY_ENGINES_INVALID"),
    peer_dependencies: assertPlainObject(
      metadata.peerDependencies,
      "HCAM_DEPENDENCY_PEERS_INVALID",
    ),
    maintainers,
    release_date: releaseDate,
    provenance: {
      attestations_url_present: typeof metadata.dist.attestations?.url === "string",
      signature_count: Array.isArray(metadata.dist.signatures)
        ? metadata.dist.signatures.length
        : 0,
      git_head_present: typeof metadata.gitHead === "string",
    },
    package_shape: {
      unpacked_size: Number.isSafeInteger(metadata.dist.unpackedSize)
        ? metadata.dist.unpackedSize
        : null,
      file_count: Number.isSafeInteger(metadata.dist.fileCount) ? metadata.dist.fileCount : null,
    },
    deprecated: typeof metadata.deprecated === "string" ? true : false,
    tarball_origin: `${tarball.protocol}//${tarball.host}`,
  };
}

for (const key of [
  "HTTP_PROXY",
  "HTTPS_PROXY",
  "ALL_PROXY",
  "NPM_CONFIG_PROXY",
  "NPM_CONFIG_HTTPS_PROXY",
]) {
  if (process.env[key]) fail("HCAM_PROXY_ENVIRONMENT_REJECTED");
}

const previousBytes = readFileSync(OUTPUT);
const previousSha = createHash("sha256").update(previousBytes).digest("hex").toUpperCase();
if (previousSha !== PREVIOUS_CANDIDATE_SHA256) fail("HCAM_P5_2_CANDIDATE_HASH_MISMATCH");
const previous = JSON.parse(previousBytes.toString("utf8"));
if (
  previous.schema_version !== "hcam.phase5.p5_2.dependency_lock_candidate.v1" ||
  previous.package_count !== 36 ||
  !Array.isArray(previous.packages) ||
  previous.packages.length !== 36 ||
  previous.packages.some((item) => item.name === "hls.js")
) {
  fail("HCAM_P5_2_CANDIDATE_SHAPE_MISMATCH");
}

const packages = [...previous.packages, await resolvePackage(requested)];
packages.sort((left, right) => left.name.localeCompare(right.name));
const hls = packages.find((item) => item.name === "hls.js");
if (hls?.version !== "1.7.2" || hls.license !== "Apache-2.0") {
  fail("HCAM_HLS_JS_POLICY_MISMATCH");
}
const deprecatedPackage = packages.find((item) => item.deprecated);
if (deprecatedPackage) fail(`HCAM_DEPENDENCY_DEPRECATED:${deprecatedPackage.name}`);

const output = {
  schema_version: "hcam.phase5.p5_3.dependency_lock_candidate.v1",
  generated_for: "P5.3-W4",
  registry: `${REGISTRY}/`,
  node: "24.18.0",
  pnpm: "11.21.0",
  package_count: packages.length,
  transition_from: {
    schema_version: previous.schema_version,
    package_count: previous.package_count,
    sha256: previousSha,
  },
  selection_policy: "preserve_exact_P5_2_candidate_and_add_only_exact_hls_js_1_7_2",
  excluded_allowlisted_packages: previous.excluded_allowlisted_packages,
  newly_resolved_packages: ["hls.js"],
  materialized: false,
  packages,
};

mkdirSync(dirname(OUTPUT), { recursive: true });
writeFileSync(OUTPUT, `${JSON.stringify(output, null, 2)}\n`, { encoding: "utf8", flag: "w" });
process.stdout.write(
  `${JSON.stringify({ status: "pass", packages: packages.length, output: "dependency-lock-candidate.json" })}\n`,
);
