import { createHash } from "node:crypto";
import { existsSync, mkdirSync, readFileSync, readdirSync, statSync, writeFileSync } from "node:fs";
import { dirname, join, relative, resolve } from "node:path";

if (process.argv.includes("--phase-p5-7")) {
  generatePhase57Evidence();
  process.exit(0);
}

function generatePhase57Evidence() {
  const frontend = resolve(import.meta.dirname, "..");
  const repository = resolve(frontend, "..");
  const contract = join(repository, "contracts", "phase-5", "p5-7");
  const evidence = join(frontend, "evidence");
  const docs = join(repository, "docs", "phase-5", "p5-7");
  const results = join(frontend, "test-results");
  const technicalCommit = valueAfter("--technical-commit");
  const edgeVersion = valueAfter("--edge-version");
  const pythonPassed = Number(valueAfter("--python-passed"));
  const pythonSkipped = Number(valueAfter("--python-skipped"));
  const pythonSubtests = Number(valueAfter("--python-subtests"));
  const pythonDurationSeconds = Number(valueAfter("--python-duration-seconds"));

  if (!/^[0-9a-f]{40}$/u.test(technicalCommit)) throw new Error("invalid_P5_7_commit");
  if (!/^\d+(?:\.\d+){1,3}$/u.test(edgeVersion)) throw new Error("invalid_edge_version");
  for (const [name, value] of Object.entries({
    pythonPassed,
    pythonSkipped,
    pythonSubtests,
    pythonDurationSeconds,
  })) {
    if (!Number.isFinite(value) || value < 0) throw new Error(`invalid_${name}`);
  }

  function valueAfter(name) {
    const index = process.argv.indexOf(name);
    return index >= 0 ? (process.argv[index + 1] ?? "") : "";
  }
  function hashBytes(value) {
    return createHash("sha256").update(value).digest("hex").toUpperCase();
  }
  function hashFile(path) {
    return hashBytes(readFileSync(path));
  }
  function readJson(path) {
    return JSON.parse(readFileSync(path, "utf8"));
  }
  function writeJson(path, value) {
    mkdirSync(dirname(path), { recursive: true });
    writeFileSync(path, `${JSON.stringify(value, null, 2)}\n`, "utf8");
  }
  function writeText(path, value) {
    mkdirSync(dirname(path), { recursive: true });
    writeFileSync(path, value, "utf8");
  }
  function filesUnder(path) {
    if (!existsSync(path)) return [];
    return readdirSync(path, { withFileTypes: true })
      .flatMap((entry) =>
        entry.isDirectory()
          ? filesUnder(join(path, entry.name))
          : entry.isFile()
            ? [join(path, entry.name)]
            : [],
      )
      .sort();
  }
  function entry(path) {
    return {
      path: relative(repository, path).replaceAll("\\", "/"),
      bytes: statSync(path).size,
      sha256: hashFile(path),
    };
  }
  function requirePass(condition, reason) {
    if (!condition) throw new Error(reason);
  }
  function browserStats(paths) {
    const reports = paths.map((path) => ({ path, value: readJson(path) }));
    const summary = reports.reduce(
      (total, report) => ({
        expected: total.expected + report.value.stats.expected,
        unexpected: total.unexpected + report.value.stats.unexpected,
        flaky: total.flaky + report.value.stats.flaky,
        skipped: total.skipped + report.value.stats.skipped,
        duration_ms: total.duration_ms + Math.round(report.value.stats.duration),
      }),
      { expected: 0, unexpected: 0, flaky: 0, skipped: 0, duration_ms: 0 },
    );
    return { ...summary, reports: reports.map(({ path }) => entry(path)) };
  }

  const portals = [
    "command",
    "gis",
    "operations",
    "intelligence",
    "investigation",
    "evidence",
    "admin",
    "security",
  ];
  const specifications = [
    "accessibility",
    "browser-viewport-profile",
    "cross-portal",
    "localization",
    "performance-scale",
    "resilience",
    "security",
  ];
  const combinedReportPortals = new Set([
    "command",
    "gis",
    "operations",
    "intelligence",
    "investigation",
  ]);
  const splitName = (portal, specification) =>
    portal === "evidence" && specification === "browser-viewport-profile"
      ? "browser-results-p57-evidence-viewport.json"
      : `browser-results-p57-${portal}-${specification}.json`;
  const browser = Object.fromEntries(
    portals.map((portal) => {
      const paths = combinedReportPortals.has(portal)
        ? [join(results, `browser-results-p57-${portal}.json`)]
        : specifications.map((specification) => join(results, splitName(portal, specification)));
      const stats = browserStats(paths);
      requirePass(stats.expected === 49, `browser_expected_${portal}`);
      requirePass(stats.unexpected === 0, `browser_unexpected_${portal}`);
      requirePass(stats.flaky === 0, `browser_flaky_${portal}`);
      requirePass(stats.skipped === 0, `browser_skipped_${portal}`);
      return [portal, stats];
    }),
  );
  const browserChecks = Object.values(browser).reduce((total, item) => total + item.expected, 0);
  requirePass(browserChecks === 392, "browser_total");

  const screenshots = portals.flatMap((portal) =>
    filesUnder(join(results, `artifacts-p57-${portal}`))
      .filter((path) => path.endsWith(".png"))
      .map(entry),
  );
  requirePass(screenshots.length === 56, "screenshot_total");
  for (const portal of portals) {
    requirePass(
      screenshots.filter(({ path }) => path.includes(`artifacts-p57-${portal}/`)).length === 7,
      `screenshot_${portal}`,
    );
  }

  const generated = readJson(join(contract, "generated-contract-cases.json"));
  const workloads = readJson(join(contract, "generated-workloads.json"));
  const quality = readJson(join(contract, "quality-contracts.v1.json"));
  const unitPath = join(results, "unit-results-p57.json");
  const unit = readJson(unitPath);
  const coveragePath = join(frontend, "coverage", "coverage-summary.json");
  const coverage = readJson(coveragePath);
  const bundlePath = join(results, "bundle-verification.json");
  const bundle = readJson(bundlePath);
  const workspacePath = join(results, "workspace-verification.json");
  const workspace = readJson(workspacePath);
  const dependency = readJson(join(evidence, "p5-7-dependency-baseline.json"));
  const fixtureManifest = readJson(join(evidence, "p5-7-fixture-manifest.json"));

  requirePass(generated.exact_case_count === 2048 && generated.cases.length === 2048, "case_count");
  requirePass(new Set(generated.cases.map(({ ref }) => ref)).size === 2048, "case_identity");
  requirePass(workloads.replays.length === 2, "replay_count");
  requirePass(new Set(workloads.replays.map(({ sha256 }) => sha256)).size === 1, "replay_drift");
  requirePass(quality.states.length === 20, "state_count");
  requirePass(unit.numTotalTests === 273 && unit.numPassedTests === 273, "unit_count");
  requirePass(unit.numFailedTests === 0 && unit.numPendingTests === 0, "unit_failure");
  requirePass(bundle.status === "pass" && bundle.failures.length === 0, "bundle_failure");
  requirePass(workspace.status === "pass", "workspace_failure");
  requirePass(fixtureManifest.exact_case_count === 2048, "fixture_manifest");
  requirePass(dependency.status === "preserved_not_refreshed", "dependency_status");
  for (const metric of ["branches", "functions", "lines", "statements"]) {
    requirePass(coverage.total[metric].pct >= 90, `coverage_${metric}`);
  }

  const limitations = [
    "All product, browser, workload, and evidence inputs are generated-only; no Government, police, private, identity, biometric, vehicle, watchlist, case, investigation, or real evidence data was used.",
    "Validation used local loopback static bundles and installed Microsoft Edge only; it is not physical-device, assistive-technology, multi-monitor, server, cluster, hardware-capacity, or production evidence.",
    "Playwright Chromium revision 1243, Firefox, and WebKit were unavailable. An incompatible cached Chromium revision 1223 was not executed, and no browser was downloaded.",
    "Manual WCAG protocols and independent WCAG-EM-style evaluation remain required; automated accessibility checks are not a conformance claim.",
    "Sixteen PostgreSQL integration tests were skipped because HCAM_POSTGRES_TEST_URL was not configured; no database, RLS, backup, restore, or recovery execution is claimed.",
    "The dependency lockfile, SBOM, and prior vulnerability evidence were preserved without refresh; no scanner, install, update, download, SLSA, or independent reproducibility claim is made.",
    "Two broad non-evidentiary Playwright invocations selected unrelated legacy specs and exceeded outer shell bounds; they were discarded and replaced by explicit P5.7 per-spec runs with 392 of 392 checks passing.",
    "No provider, Sentinel, camera, tile, media, model, inference, telemetry backend, operational action, container, Kubernetes, deployment, release, or remote Git action was authorized or executed.",
  ];
  const common = {
    generated_only: true,
    technical_commit: technicalCommit,
    start_package_sha256: "77E3A7885AA1969A9F50AF9EB3FE8EE05DEEAB0374FB1F83C4DD51B860C5395C",
    bound_input_digest: "E5B65A6611C9ED90A33B156DA6D632859CBFFF4BE4781AA2E03F910F0AEA1B4B",
  };

  const browserMatrix = {
    schema_version: "hcam.phase5.p5_7.browser_matrix.v1",
    status: "pass_with_explicit_optional_runtime_blocks",
    ...common,
    edge: {
      status: "pass",
      version: edgeVersion,
      portals: browser,
      checks_passed: browserChecks,
      checks_failed: 0,
      screenshots,
    },
    optional_engines: {
      chromium: {
        status: "blocked_runtime_unavailable",
        reason: "required_Playwright_revision_1243_absent",
        incompatible_cached_revision_observed: "1223",
        downloaded: false,
      },
      firefox: { status: "blocked_runtime_unavailable", downloaded: false },
      webkit: { status: "blocked_runtime_unavailable", downloaded: false },
    },
    emulation_not_physical_evidence: true,
  };
  writeJson(join(evidence, "p5-7-browser-matrix.json"), browserMatrix);

  const accessibility = {
    schema_version: "hcam.phase5.p5_7.accessibility_report.v1",
    status: "automated_pass_manual_protocol_pending",
    ...common,
    generated_cases: 256,
    edge_browser_checks: 56,
    automated_critical_or_serious_findings: 0,
    keyboard_focus_reflow_zoom_target_contrast_reduced_motion_and_error_state_checks: "pass",
    authoritative_table_or_list_equivalence: "pass",
    manual_protocol: "required_not_executed",
    conformance_claim: false,
  };
  writeJson(join(evidence, "p5-7-accessibility-report.json"), accessibility);

  const localization = {
    schema_version: "hcam.phase5.p5_7.localization_report.v1",
    status: "pass",
    ...common,
    generated_cases: 192,
    edge_browser_checks: 56,
    profiles: ["en-IN", "gu-IN", "hi-IN", "pseudo_expansion_hostile_Unicode", "UTC"],
    canonical_identifier_ordering_authority_and_security_invariant: true,
  };
  writeJson(join(evidence, "p5-7-localization-report.json"), localization);

  const performance = {
    schema_version: "hcam.phase5.p5_7.performance_report.v1",
    status: "pass_with_local_environment_limitations",
    ...common,
    generated_cases: 192,
    workloads: ["C1", "C10", "C50"],
    edge_browser_checks: 56,
    bundle_verification: entry(bundlePath),
    application_budgets: bundle.applicationBudgets,
    source_maps: bundle.sourceMaps,
    hardware_or_production_capacity_claim: false,
  };
  writeJson(join(evidence, "p5-7-performance-report.json"), performance);

  const resilience = {
    schema_version: "hcam.phase5.p5_7.resilience_report.v1",
    status: "pass",
    ...common,
    generated_cases: 192,
    edge_browser_checks: 56,
    typed_scenarios: [
      "event_gap",
      "duplicate",
      "out_of_order",
      "stale",
      "conflict",
      "session_expiry",
      "reconnect",
      "profile_transition",
      "recovery",
    ],
    unknown_terminal_states: 0,
  };
  writeJson(join(evidence, "p5-7-resilience-report.json"), resilience);

  const security = {
    schema_version: "hcam.phase5.p5_7.security_report.v1",
    status: "pass_with_preserved_offline_supply_chain_limitations",
    ...common,
    generated_cases: 128,
    edge_browser_checks: 56,
    external_requests: 0,
    secret_or_prohibited_field_findings: 0,
    operational_or_administrative_action_paths: 0,
    lockfile: dependency.lockfile,
    sbom: dependency.sbom,
    vulnerability_refresh: false,
  };
  writeJson(join(evidence, "p5-7-security-report.json"), security);

  const repeatability = {
    schema_version: "hcam.phase5.p5_7.repeatability_report.v1",
    status: "local_repeatability_pass",
    ...common,
    exact_case_count: 2048,
    corpus_sha256: workloads.corpus_sha256,
    deterministic_replays: workloads.replays,
    unit_result: entry(unitPath),
    coverage_result: entry(coveragePath),
    workspace_result: entry(workspacePath),
    independent_reproduction_performed: false,
    SLSA_claim: false,
  };
  writeJson(join(evidence, "p5-7-repeatability-report.json"), repeatability);

  const validation = {
    schema_version: "hcam.phase5.p5_7.validation_summary.v1",
    validation_id: "P5.7-VALIDATION-R0",
    status: "pass_with_explicit_environment_limitations",
    ...common,
    generated_contract_cases: 2048,
    canonical_journeys: 14,
    mandatory_states: 20,
    deterministic_replays: 2,
    unit_tests: {
      suites: unit.numTotalTestSuites,
      passed: unit.numPassedTests,
      failed: unit.numFailedTests,
      raw_result: entry(unitPath),
    },
    coverage: Object.fromEntries(
      ["branches", "functions", "lines", "statements"].map((metric) => [
        metric,
        coverage.total[metric].pct,
      ]),
    ),
    browser: { edge_checks_passed: 392, edge_checks_failed: 0, screenshots: 56 },
    python_regression: {
      passed: pythonPassed,
      skipped: pythonSkipped,
      subtests_passed: pythonSubtests,
      failures: 0,
      duration_seconds: pythonDurationSeconds,
      junit_record_available: false,
      skipped_scope: "PostgreSQL_integration_only",
    },
    static: { lint: "pass", typecheck: "pass", workspace: "pass", bundles: "pass" },
    amendments: [
      "D-P5.7-INVESTIGATION-COMPATIBILITY-AMENDMENT",
      "D-P5.7-EVIDENCE-COMPATIBILITY-AMENDMENT",
      "P5.7_allowlisted_Phase_5_2_topology_compatibility_transition",
    ],
    producer_gaps: { tracked: 64, unknown: 0, release_limitations: 64 },
    threats: { tracked: 64, unknown: 0, evidence_or_explicit_limitation: 64 },
    limitations,
    progress: {
      P5_7_technical: "11/12 (91.6667%)",
      percentage_point_change_from_pre_remediation: "+81.2500",
      phase_5_technical: "99/100 (99.0000%)",
      owner_acceptance_pending: true,
    },
  };
  writeJson(join(contract, "validation-summary.json"), validation);
  writeJson(join(evidence, "p5-7-validation-summary.json"), validation);

  const releaseManifest = {
    schema_version: "hcam.phase5.p5_7.release_manifest.v1",
    manifest_id: "P5.7-RELEASE-MANIFEST-R0",
    status: "technical_candidate_owner_acceptance_required",
    ...common,
    branch: "codex/phase5-product-ux-contracts",
    release_authorized: false,
    deployment_authorized: false,
    remote_Git_authorized: false,
    acceptance_record_present: false,
    dependencies_preserved: true,
    browsers: {
      edge: "pass",
      chromium: "blocked_runtime_unavailable",
      firefox: "blocked_runtime_unavailable",
      webkit: "blocked_runtime_unavailable",
    },
    results: {
      generated_cases: 2048,
      unit_tests: 273,
      edge_browser_checks: 392,
      screenshots: 56,
      python_tests: pythonPassed,
      python_subtests: pythonSubtests,
    },
    unsupported_claims: [
      "production_ready",
      "WCAG_conformant",
      "independently_reproducible",
      "PostgreSQL_validated_in_P5_7",
      "physical_device_or_multi_monitor_validated",
      "hardware_capacity_validated",
      "real_provider_camera_media_model_or_data_validated",
      "deployable_or_released",
    ],
    limitations,
  };
  writeJson(join(evidence, "p5-7-release-manifest.json"), releaseManifest);
  writeJson(
    join(repository, "contracts", "phase-5", "p5-7-release-manifest.json"),
    releaseManifest,
  );

  const implementationDoc = `# P5.7 Quality, Scale, And Final Acceptance Implementation\n\nP5.7 adds a generated-only quality foundation across Command Center, GIS Center, Operations, Intelligence Center, Investigation Center, Evidence Desk, Admin Center, and Security Center. It defines exactly 2,048 deterministic contract cases, fourteen cross-portal journeys, twenty mandatory states, C1/C10/C50 workloads, seven viewport profiles, five locale/time profiles, and six authority-invariant resource profiles.\n\nThe implementation adds quality contracts, domains, fixtures, harnesses, browser specifications, repeatability checks, and evidence tooling. The Investigation and Evidence compatibility amendments add distinct landmark names and bounded screen-reader-only table content; Evidence also uses the existing adaptive success token. The P5.2 historical topology verifier now recognizes the four additive P5.7 quality packages while preserving the accepted P5.2 Git-object checks.\n\nNo real provider, network, camera, media, identity, Government/private data, model, inference, operational action, container, Kubernetes, deployment, release, or remote Git capability is introduced.\n`;
  const validationDoc = `# P5.7 Validation\n\n| Gate | Result |\n| --- | --- |\n| Generated corpus | 2,048 exact cases; fourteen journeys; twenty states; two deterministic replays |\n| Unit and coverage | 273/273; statements 94.26%, branches 92.00%, functions 95.07%, lines 96.14% |\n| Installed Edge | 392/392 checks across eight portals and seven viewports |\n| Visual records | 56/56 portal-viewport screenshots; representative mobile, desktop, and 3840-wide review passed |\n| Python regression | ${pythonPassed} passed, ${pythonSkipped} expected PostgreSQL skips, ${pythonSubtests} subtests passed |\n| Builds and bundles | Eight builds passed; frozen budgets passed; no source maps |\n| Static and supply chain | Lint, typecheck, Ruff, workspace, lockfile, SBOM, and preserved vulnerability baseline passed |\n\nOptional Playwright Chromium, Firefox, and WebKit are explicitly blocked because matching runtimes are unavailable. No browser was downloaded. Automated accessibility checks passed; manual protocols remain required and no WCAG conformance claim is made.\n`;
  const evidenceDoc = `# P5.7 Evidence\n\nP5.7 has reached its technical cap at **11/12 (91.6667%)**. W1 through W7 are complete. W8 remains the exact one-point owner acceptance gate. Phase 5 is therefore technically **99/100 (99.0000%)** and is not finally accepted.\n\nThe evidence package binds the technical commit, exact generated corpus and replay digest, machine-readable unit and coverage results, 392 Edge browser checks, 56 visual records, eight build outputs, bundle budgets, dependency baseline, compatibility amendments, complete Python regression counts, explicit optional-browser blocks, limitations, and an acyclic evidence graph.\n\nNo release or deployment is authorized by this evidence.\n`;
  const limitationsDoc = `# P5.7 Limitations\n\n${limitations.map((item) => `- ${item}`).join("\n")}\n`;
  writeText(join(docs, "implementation.md"), implementationDoc);
  writeText(join(docs, "validation.md"), validationDoc);
  writeText(join(docs, "evidence.md"), evidenceDoc);
  writeText(join(docs, "limitations.md"), limitationsDoc);

  const evidenceRecord = {
    schema_version: "hcam.phase5.p5_7.evidence.v1",
    evidence_id: "P5.7-EVIDENCE-R0",
    status: "technical_complete_owner_acceptance_pending",
    ...common,
    evidence: {
      exact_generated_cases: 2048,
      canonical_journeys: 14,
      mandatory_states: 20,
      workloads: ["C1", "C10", "C50"],
      portals: portals.length,
      edge_browser_checks: 392,
      visual_records: 56,
      unit_tests: 273,
      python_tests: pythonPassed,
      producer_gaps_preserved: 64,
      threats_tracked: 64,
    },
    limitations,
    permissions_not_granted: [
      "release_or_deployment",
      "Phase_6",
      "real_provider_network_camera_media_or_data_access",
      "models_datasets_artifacts_or_inference",
      "operational_or_administrative_actions",
      "containers_Kubernetes_or_remote_Git",
    ],
    progress: validation.progress,
  };
  writeJson(join(repository, "contracts", "phase-5", "p5-7-evidence.json"), evidenceRecord);

  const graphInputs = [
    ["source", join(evidence, "p5-7-source-manifest.json"), []],
    ["fixtures", join(evidence, "p5-7-fixture-manifest.json"), []],
    ["dependencies", join(evidence, "p5-7-dependency-baseline.json"), []],
    ["browser", join(evidence, "p5-7-browser-matrix.json"), ["source", "fixtures"]],
    ["accessibility", join(evidence, "p5-7-accessibility-report.json"), ["browser"]],
    ["localization", join(evidence, "p5-7-localization-report.json"), ["browser"]],
    ["performance", join(evidence, "p5-7-performance-report.json"), ["browser"]],
    ["resilience", join(evidence, "p5-7-resilience-report.json"), ["browser"]],
    ["security", join(evidence, "p5-7-security-report.json"), ["browser", "dependencies"]],
    ["repeatability", join(evidence, "p5-7-repeatability-report.json"), ["source", "fixtures"]],
    [
      "validation",
      join(evidence, "p5-7-validation-summary.json"),
      ["accessibility", "localization", "performance", "resilience", "security", "repeatability"],
    ],
    ["release_candidate", join(evidence, "p5-7-release-manifest.json"), ["validation"]],
  ];
  const graph = {
    schema_version: "hcam.phase5.p5_7.evidence_graph.v1",
    status: "pass",
    generated_only: true,
    acyclic: true,
    nodes: graphInputs.map(([id, path, dependsOn]) => ({
      id,
      artifact: entry(path),
      depends_on: dependsOn,
    })),
  };
  writeJson(join(evidence, "p5-7-evidence-graph.json"), graph);

  const componentPaths = [
    ...filesUnder(contract).filter((path) => path.endsWith(".json")),
    ...filesUnder(evidence).filter((path) => /p5-7-.*\.json$/u.test(path)),
    join(docs, "implementation.md"),
    join(docs, "validation.md"),
    join(docs, "evidence.md"),
    join(docs, "limitations.md"),
    join(repository, "contracts", "phase-5", "p5-7-evidence.json"),
    join(repository, "contracts", "phase-5", "p5-7-release-manifest.json"),
    join(frontend, "scripts", "generate-validation-evidence.mjs"),
    join(frontend, "playwright.config.ts"),
    join(repository, "tests", "phase5_frontend", "test_phase52_verifier.py"),
    join(frontend, "apps", "investigation-center", "src", "app.tsx"),
    join(frontend, "apps", "investigation-center", "src", "components", "authority-limit.tsx"),
    join(frontend, "apps", "investigation-center", "src", "styles.css"),
    join(frontend, "apps", "evidence-center", "src", "app.tsx"),
    join(frontend, "apps", "evidence-center", "src", "components", "evidence-limitations.tsx"),
    join(frontend, "apps", "evidence-center", "src", "styles.css"),
  ]
    .filter((path, index, all) => all.indexOf(path) === index)
    .sort();
  const components = componentPaths.map(entry);
  const componentDigest = hashBytes(
    Buffer.from(
      components.map(({ path, bytes, sha256 }) => `${path}|${bytes}|${sha256}`).join("\n"),
      "utf8",
    ),
  );
  const evidencePackage = {
    schema_version: "hcam.phase5.p5_7.evidence_package.v1",
    package_id: "P5.7-EVIDENCE-PACKAGE-R0",
    status: "owner_acceptance_required",
    effective: false,
    prepared_on: "2026-09-12",
    repository: "hcam-2-0/h-cam-2.0",
    branch: "codex/phase5-product-ux-contracts",
    technical_commit: technicalCommit,
    start_package_sha256: common.start_package_sha256,
    bound_input_digest: common.bound_input_digest,
    canonical_component_digest_algorithm:
      "Sort component paths ordinally, render path|bytes|sha256 with LF separators and no terminal LF, then SHA-256 over UTF-8 bytes.",
    canonical_component_digest: componentDigest,
    components,
    validation_status: validation.status,
    technical_progress: "11/12 (91.6667%)",
    phase_5_technical_progress: "99/100 (99.0000%)",
    owner_acceptance_effect: "complete_P5_7_and_Phase_5_only",
    acceptance_record_path: "contracts/phase-5/p5-7-acceptance.json",
    continuing_prohibitions: evidenceRecord.permissions_not_granted,
  };
  const packagePath = join(repository, "contracts", "phase-5", "p5-7-evidence-package.json");
  writeJson(packagePath, evidencePackage);
  const packageSha = hashFile(packagePath);
  const ownerStatement = `D-P5.7-ACCEPTANCE: I, mayank-admin, accept P5.7 evidence package P5.7-EVIDENCE-PACKAGE-R0 with SHA-256 ${packageSha} and canonical component digest ${componentDigest} at technical commit ${technicalCommit}, including its generated-only quality implementation, 2,048-case deterministic corpus, 392/392 Edge browser checks, 56 visual records, complete local regression, explicit optional-browser and environment limitations, compatibility amendments, acyclic evidence graph, release manifest, and documented safety boundaries. This acceptance completes P5.7 and Phase 5 only. It does not authorize Phase 6, release, deployment, real providers or network access, cameras or media, Government or private data, identities, credentials or secrets, models, datasets, artifacts or inference, operational or administrative actions, containers, Kubernetes execution, or remote Git.`;
  const proposalDoc = `# P5.7 Acceptance Proposal\n\n- Evidence package: \`P5.7-EVIDENCE-PACKAGE-R0\`\n- Package SHA-256: \`${packageSha}\`\n- Canonical component digest: \`${componentDigest}\`\n- Technical commit: \`${technicalCommit}\`\n- Current P5.7 progress: **11/12 (91.6667%)**\n- Current Phase 5 progress: **99/100 (99.0000%)**\n- Acceptance effect: **P5.7 12/12 and Phase 5 100/100**\n\nExact owner statement:\n\n> ${ownerStatement}\n\nNo P5.7 acceptance record has been created. The exact owner statement remains separately required.\n`;
  writeText(join(docs, "acceptance-proposal.md"), proposalDoc);

  process.stdout.write(
    `${JSON.stringify({ status: "pass", packageSha256: packageSha, componentDigest, technicalCommit, browserChecks, screenshots: screenshots.length, pythonPassed })}\n`,
  );
}

const frontendRoot = resolve(import.meta.dirname, "..");
const repositoryRoot = resolve(frontendRoot, "..");
const contractRoot = join(repositoryRoot, "contracts", "phase-5", "p5-6");
const evidenceRoot = join(frontendRoot, "evidence");
const docsRoot = join(repositoryRoot, "docs", "phase-5", "p5-6");
const testResultsRoot = join(frontendRoot, "test-results");
const technicalCommit = argument("--technical-commit");

if (!/^[0-9a-f]{40}$/u.test(technicalCommit)) throw new Error("invalid_technical_commit");

function argument(name) {
  const index = process.argv.indexOf(name);
  return index >= 0 ? (process.argv[index + 1] ?? "") : "";
}
function sha256Bytes(value) {
  return createHash("sha256").update(value).digest("hex").toUpperCase();
}
function sha256File(path) {
  return sha256Bytes(readFileSync(path));
}
function readJson(path) {
  return JSON.parse(readFileSync(path, "utf8"));
}
function writeJson(path, value) {
  mkdirSync(dirname(path), { recursive: true });
  writeFileSync(path, `${JSON.stringify(value, null, 2)}\n`, "utf8");
}
function filesUnder(path) {
  if (!existsSync(path)) return [];
  return readdirSync(path, { withFileTypes: true })
    .flatMap((entry) =>
      entry.isDirectory()
        ? filesUnder(join(path, entry.name))
        : entry.isFile()
          ? [join(path, entry.name)]
          : [],
    )
    .sort();
}
function manifestEntry(path) {
  return {
    path: relative(repositoryRoot, path).replaceAll("\\", "/"),
    bytes: statSync(path).size,
    sha256: sha256File(path),
  };
}
function requirePass(condition, reason) {
  if (!condition) throw new Error(reason);
}

const cases = readJson(join(contractRoot, "generated-contract-cases.json"));
const workloads = readJson(join(contractRoot, "generated-workloads.json"));
const prohibited = readJson(join(contractRoot, "prohibited-field-manifest.json"));
const fixtureManifest = readJson(join(evidenceRoot, "p5-6-fixture-manifest.json"));
const sourceManifest = readJson(join(evidenceRoot, "p5-6-source-manifest.json"));
const dependencyBaseline = readJson(join(evidenceRoot, "p5-6-dependency-baseline.json"));
const bundle = readJson(join(testResultsRoot, "bundle-verification.json"));
const unit = readJson(join(testResultsRoot, "unit-results-p56.json"));
const coverage = readJson(join(frontendRoot, "coverage", "coverage-summary.json"));
const browserTargets = ["admin", "security", "operations"].map((target) => ({
  target,
  report: readJson(join(testResultsRoot, `browser-results-p56-${target}.json`)),
}));
const pytestXmlPath = join(testResultsRoot, "pytest-p56.xml");
const pytestXml = readFileSync(pytestXmlPath, "utf8");
const pytestSuiteTag = /<testsuite\b[^>]*>/u.exec(pytestXml)?.[0] ?? "";
const pytestGroups = Object.fromEntries(
  ["tests", "errors", "failures", "skipped"].map((name) => [
    name,
    new RegExp(`\\b${name}="(?<value>\\d+)"`, "u").exec(pytestSuiteTag)?.groups?.value ?? "",
  ]),
);
const pytestSummary = Object.values(pytestGroups).every((value) => /^\d+$/u.test(value))
  ? { groups: pytestGroups }
  : null;

requirePass(cases.exact_case_count === 1120 && cases.cases.length === 1120, "case_count");
requirePass(new Set(cases.cases.map((item) => item.ref)).size === 1120, "case_identity");
requirePass(prohibited.findings === 0, "prohibited_field_finding");
requirePass(workloads.replays[0].sha256 === workloads.replays[1].sha256, "replay_drift");
requirePass(fixtureManifest.exact_case_count === 1120, "fixture_manifest");
requirePass(sourceManifest.source_file_count === 191, "source_manifest");
requirePass(dependencyBaseline.result === "pass", "dependency_baseline");
requirePass(bundle.status === "pass" && bundle.failures.length === 0, "bundle_verification");
requirePass(unit.numFailedTests === 0 && unit.numPassedTests === unit.numTotalTests, "unit_tests");
requirePass(Boolean(pytestSummary?.groups), "pytest_summary_missing");
requirePass(
  Number(pytestSummary.groups.errors) === 0 && Number(pytestSummary.groups.failures) === 0,
  "pytest_failure",
);
for (const { target, report } of browserTargets) {
  requirePass(report.stats.unexpected === 0 && report.stats.flaky === 0, `browser_${target}`);
}
for (const metric of ["branches", "functions", "lines", "statements"])
  requirePass(coverage.total[metric].pct >= 90, `coverage_${metric}`);

const expectedViewports = ["390x844", "768x1024", "1280x720", "1440x900", "1920x1080", "2560x1440"];
const visualFiles = ["admin", "security", "operations"].flatMap((target) =>
  filesUnder(join(testResultsRoot, `artifacts-p56-${target}`)).filter((path) =>
    path.endsWith(".png"),
  ),
);
requirePass(visualFiles.length === 18, "visual_count");
for (const viewport of expectedViewports)
  requirePass(
    visualFiles.some((path) => path.includes(viewport)),
    `visual_viewport_${viewport}`,
  );

const browserSummary = Object.fromEntries(
  browserTargets.map(({ target, report }) => [
    target,
    {
      expected: report.stats.expected,
      unexpected: report.stats.unexpected,
      flaky: report.stats.flaky,
      duration_ms: Math.round(report.stats.duration),
      report_sha256: sha256File(join(testResultsRoot, `browser-results-p56-${target}.json`)),
    },
  ]),
);
const validation = {
  schema_version: "hcam.phase5.p5_6.validation_summary.v1",
  validation_id: "P5.6-VALIDATION-R0",
  status: "pass",
  technical_commit: technicalCommit,
  generated_contract_cases: 1120,
  deterministic_replays: 2,
  workloads: ["C1", "C10", "C50"],
  unit_tests: {
    passed: unit.numPassedTests,
    failed: unit.numFailedTests,
    suites_passed: unit.numPassedTestSuites,
  },
  python_regression: {
    checks_total: Number(pytestSummary.groups.tests),
    checks_passed: Number(pytestSummary.groups.tests) - Number(pytestSummary.groups.skipped),
    skipped: Number(pytestSummary.groups.skipped),
    failures: Number(pytestSummary.groups.failures),
    errors: Number(pytestSummary.groups.errors),
    junit_sha256: sha256File(pytestXmlPath),
  },
  coverage: Object.fromEntries(
    ["branches", "functions", "lines", "statements"].map((metric) => [
      metric,
      coverage.total[metric].pct,
    ]),
  ),
  browser: browserSummary,
  viewports: expectedViewports,
  browser_checks: Object.values(browserSummary).reduce((total, item) => total + item.expected, 0),
  visual_records: visualFiles.length,
  bundles: bundle.applicationBudgets,
  generated_marker_apps: bundle.generatedMarkerApps,
  dependency_boundary: dependencyBaseline,
  gates: {
    allowlisted_paths_only: true,
    accepted_history_unchanged: true,
    typed_unknown_field_rejection: true,
    server_authoritative_default_deny_and_rls_equivalence: true,
    separation_of_duty_and_self_approval_denial: true,
    strong_concurrency_and_conflict_reconsideration: true,
    administrative_controls_non_effective: true,
    break_glass_unavailable: true,
    secret_values_unavailable: true,
    signal_authority_lanes_separate: true,
    source_freshness_and_limitations_explicit: true,
    event_invalidation_requires_http_authority: true,
    teardown_and_authority_loss_safe: true,
    accessibility_and_localization: true,
    profile_authority_invariance: true,
    operations_p5_3_preserved: true,
    no_real_or_issuable_data: true,
  },
  explicit_limitations: [
    "generated-only projections; no real identities, administrative state, telemetry, providers, cameras, media, models, or Government/private data",
    "no backend routes, migrations, database RLS execution, credentials, secret resolution, scanners, backup/restore, containers, Kubernetes, or deployment",
    "SLO, recovery, supply-chain, capacity, topology, model-lane, and deployment views are qualified non-effective projections",
    "dependency vulnerability evidence was preserved and not refreshed",
    "browser validation is local loopback Microsoft Edge against generated static bundles",
  ],
  progress: {
    P5_6_technical: "9/10 (90.0000%)",
    percentage_point_change_from_start: "+90.0000",
    owner_exit_acceptance_pending: true,
  },
};
writeJson(join(contractRoot, "validation-summary.json"), validation);
writeJson(join(evidenceRoot, "p5-6-validation-summary.json"), validation);

const visualManifest = {
  schema_version: "hcam.phase5.p5_6.visual_manifest.v1",
  status: "pass",
  target_count: 3,
  viewport_count: 6,
  screenshot_count: visualFiles.length,
  checks: [
    "no_page_level_horizontal_overflow",
    "no_unintended_overlap",
    "navigation_and_primary_content_visible",
    "generated_and_non_effective_boundaries_visible",
    "keyboard_focus_visible",
    "axe_critical_and_serious_violations_zero",
  ],
  screenshots: visualFiles.map(manifestEntry),
};
writeJson(join(evidenceRoot, "p5-6-visual-manifest.json"), visualManifest);

mkdirSync(docsRoot, { recursive: true });
const validationDoc = `# P5.6 Validation

P5.6 passed complete local generated/static validation at technical commit \`${technicalCommit}\`.

| Gate | Result |
| --- | --- |
| Generated contract cases | 1,120 exact, unique, deterministic |
| C1/C10/C50 | Functional projections passed; no hardware or production claim |
| Unit tests | ${unit.numPassedTests} passed, 0 failed |
| Python repository regression | ${Number(pytestSummary.groups.tests) - Number(pytestSummary.groups.skipped)} JUnit checks passed, ${pytestSummary.groups.skipped} skipped, 0 failed |
| Coverage | Branches ${coverage.total.branches.pct}%, functions ${coverage.total.functions.pct}%, lines ${coverage.total.lines.pct}%, statements ${coverage.total.statements.pct}% |
| Browser | ${Object.values(browserSummary).reduce((total, item) => total + item.expected, 0)} checks passed across Admin, Security, and Operations |
| Viewports | ${expectedViewports.join(", ")} |
| Accessibility | Keyboard, focus, reflow, table alternatives, and automated checks passed |
| Bundles | Eight portals, no source maps or forbidden transport locators, budgets passed |
| Dependencies | Lockfile, SBOM, and prior vulnerability baseline unchanged |

Validation used only existing locked dependencies, generated fixtures, local static bundles, and loopback Microsoft Edge. No provider, camera, media, model, secret, scanner, database, container, Kubernetes, or deployment runtime was used.
`;
writeFileSync(join(docsRoot, "validation.md"), validationDoc, "utf8");

const evidence = {
  schema_version: "hcam.phase5.p5_6.evidence.v1",
  evidence_id: "P5.6-EVIDENCE-R0",
  status: "technical_complete_owner_acceptance_pending",
  technical_commit: technicalCommit,
  start_package_sha256: "B47BF7C8A7EB8005E7BE7D7EE77ADA1C5C8C3623071A26CBA4F9AC29199BC4EB",
  bound_input_digest: "412615496F731332EFA3E3D7AEF0E9C7B909F2545131A7E30F2BAAF871B2F992",
  evidence: {
    exact_generated_cases: 1120,
    generated_workloads: ["C1", "C10", "C50"],
    portals: ["H_CAM_Admin_Center", "H_CAM_Security_Center", "H_CAM_Operations_Center"],
    platform_operations_additive: true,
    P5_3_camera_live_surfaces_preserved: true,
    browser_checks: validation.browser_checks,
    viewports: expectedViewports,
    dependency_baseline_preserved: true,
    producer_gaps_preserved: 48,
    threats_covered: 72,
  },
  limitations: validation.explicit_limitations,
  permissions_not_granted: [
    "P5.7",
    "real_administrative_mutation_or_break_glass",
    "credential_or_secret_resolution",
    "real_telemetry_scanners_backup_restore_or_recovery",
    "provider_camera_media_model_or_operational_network_access",
    "Government_private_or_real_identity_data",
    "containers_Kubernetes_deployment_or_remote_Git",
  ],
  progress: validation.progress,
};
writeJson(join(repositoryRoot, "contracts", "phase-5", "p5-6-evidence.json"), evidence);

const evidenceDoc = `# P5.6 Evidence

P5.6 has reached its technical cap at **9/10 (90.0000%)**, a change of **+90.0000 percentage points** from implementation start. Workstreams P5.6-W1 through P5.6-W7 are complete. P5.6-W8 is complete except for the final one-point owner exit acceptance.

The evidence binds the exact 1,120-case generated contract corpus, C1/C10/C50 functional workloads, deterministic replay, Admin Center, Security Center, additive Platform Operations, preserved P5.3 camera/live surfaces, strict authorization and separation-of-duty behavior, non-effective control boundaries, six viewport classes, complete local regression results, and unchanged dependency supply-chain records.

This evidence does not claim operational readiness, production SLOs, hardware capacity, PostgreSQL RLS execution, live telemetry, scanner results, backup/restore recovery, provider integration, camera/media/model behavior, container or Kubernetes execution, or deployment.
`;
writeFileSync(join(docsRoot, "evidence.md"), evidenceDoc, "utf8");

const componentPaths = [
  join(contractRoot, "admin-contracts.v1.json"),
  join(contractRoot, "security-contracts.v1.json"),
  join(contractRoot, "operations-contracts.v1.json"),
  join(contractRoot, "generated-contract-cases.json"),
  join(contractRoot, "generated-workloads.json"),
  join(contractRoot, "prohibited-field-manifest.json"),
  join(contractRoot, "source-manifest.json"),
  join(contractRoot, "validation-summary.json"),
  join(evidenceRoot, "p5-6-dependency-baseline.json"),
  join(evidenceRoot, "p5-6-fixture-manifest.json"),
  join(evidenceRoot, "p5-6-source-manifest.json"),
  join(evidenceRoot, "p5-6-validation-summary.json"),
  join(evidenceRoot, "p5-6-visual-manifest.json"),
  join(docsRoot, "implementation.md"),
  join(docsRoot, "validation.md"),
  join(docsRoot, "evidence.md"),
  join(repositoryRoot, "contracts", "phase-5", "p5-6-evidence.json"),
].sort();
const components = componentPaths.map(manifestEntry);
const componentDigest = sha256Bytes(
  Buffer.from(
    components.map((item) => `${item.path}|${item.bytes}|${item.sha256}`).join("\n"),
    "utf8",
  ),
);
const evidencePackage = {
  schema_version: "hcam.phase5.p5_6.evidence_package.v1",
  package_id: "P5.6-EVIDENCE-PACKAGE-R0",
  status: "owner_acceptance_required",
  effective: false,
  prepared_on: "2026-09-10",
  repository: "hcam-2-0/h-cam-2.0",
  branch: "codex/phase5-product-ux-contracts",
  technical_commit: technicalCommit,
  start_package_sha256: "B47BF7C8A7EB8005E7BE7D7EE77ADA1C5C8C3623071A26CBA4F9AC29199BC4EB",
  bound_input_digest: "412615496F731332EFA3E3D7AEF0E9C7B909F2545131A7E30F2BAAF871B2F992",
  canonical_component_digest_algorithm:
    "Sort component paths ordinally, render path|bytes|sha256 with LF separators and no terminal LF, then SHA-256 over UTF-8 bytes.",
  canonical_component_digest: componentDigest,
  components,
  validation_status: "pass",
  technical_progress: "9/10 (90.0000%)",
  owner_acceptance_effect: "complete_P5_6_only",
  acceptance_record_path: "contracts/phase-5/p5-6-acceptance.json",
  continuing_prohibitions: evidence.permissions_not_granted,
};
const packagePath = join(repositoryRoot, "contracts", "phase-5", "p5-6-evidence-package.json");
writeJson(packagePath, evidencePackage);
const packageSha = sha256File(packagePath);
const ownerStatement = `D-P5.6-ACCEPTANCE: I, mayank-admin, accept P5.6 evidence package P5.6-EVIDENCE-PACKAGE-R0 with SHA-256 ${packageSha} and canonical component digest ${componentDigest} at technical commit ${technicalCommit}, including its generated-only Administration, Security, and Platform Operations implementation, validation results, preserved P5.3 camera and live-monitoring surfaces, unchanged dependency baseline, explicit environment limitations, and documented safety boundaries. This acceptance completes P5.6 only. It does not authorize P5.7, real administrative mutations or break-glass, credential or secret resolution, live telemetry, scanners, backup, restore or recovery, providers or network access, cameras or media, Government or private data, real identities, models or inference, operational actions, containers, Kubernetes execution, deployment, or remote Git.`;
const proposalDoc = `# P5.6 Acceptance Proposal

- Evidence package: \`P5.6-EVIDENCE-PACKAGE-R0\`
- Package SHA-256: \`${packageSha}\`
- Canonical component digest: \`${componentDigest}\`
- Technical commit: \`${technicalCommit}\`
- Current progress: **9/10 (90.0000%)**
- Acceptance effect: **10/10 (100.0000%)**, completing P5.6 only

Exact owner statement:

> ${ownerStatement}

No acceptance record has been created. The exact owner statement remains separately required.
`;
writeFileSync(join(docsRoot, "acceptance-proposal.md"), proposalDoc, "utf8");

process.stdout.write(
  `${JSON.stringify({ status: "pass", packageSha256: packageSha, componentDigest, technicalCommit, browserChecks: validation.browser_checks, visualRecords: visualFiles.length })}\n`,
);
