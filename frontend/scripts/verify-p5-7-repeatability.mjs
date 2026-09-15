import { createHash } from "node:crypto";
import { readFileSync } from "node:fs";
import { resolve } from "node:path";

const repositoryRoot = resolve(import.meta.dirname, "..", "..");
const contractRoot = resolve(repositoryRoot, "contracts", "phase-5", "p5-7");
const corpus = JSON.parse(
  readFileSync(resolve(contractRoot, "generated-contract-cases.json"), "utf8"),
);
const workloads = JSON.parse(
  readFileSync(resolve(contractRoot, "generated-workloads.json"), "utf8"),
);
const canonicalBytes = Buffer.from(`${JSON.stringify(corpus, null, 2)}\n`, "utf8");
const digest = createHash("sha256").update(canonicalBytes).digest("hex").toUpperCase();
const refs = corpus.cases.map(({ ref }) => ref);
const failures = [];
if (corpus.generated_only !== true) failures.push("generated_boundary");
if (corpus.exact_case_count !== 2048 || corpus.cases.length !== 2048) failures.push("case_count");
if (new Set(refs).size !== 2048) failures.push("case_identity");
if (workloads.corpus_sha256 !== digest) failures.push("corpus_digest");
if (workloads.replays.length !== 2 || workloads.replays.some(({ sha256 }) => sha256 !== digest))
  failures.push("replay_drift");
const result = {
  status: failures.length ? "fail" : "pass",
  exact_case_count: 2048,
  replay_count: 2,
  corpus_sha256: digest,
  failures,
};
process.stdout.write(`${JSON.stringify(result)}\n`);
if (failures.length) process.exit(1);
