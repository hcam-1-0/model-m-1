# P3.6 U4E Runtime-Closeout R2 Failure Decisions

## Current State

The single R2 closeout attempt is consumed and failed closed at
`R2-A04-UTILITY-MANIFEST-AND-CLOSURE-BINDING` with sanitized reason
`utility_closure_declared_target_missing`.

Package authority, the owner authorization record, the exact PowerShell 7
runtime, three fixed parents, cache-only trust, and manifest classification all
passed. The manifest parsed as one literal hashtable with zero errors and an
empty `ScriptsToProcess`. Closure resolution then reached one missing declared
target and stopped. No validation process ran, no generated case ran, U3K did
not start, and `F:` was not accessed.

The retained evidence deliberately excludes the field name, path, extension,
manifest content, parser material, exception data, and identity information.
It therefore does not prove whether the resolver used the wrong base, a
non-load-bearing inventory entry was absent, or the installed module is
incomplete.

## Known Static Compatibility Transition

The full Phase 3.6 generated/static suite currently reports
`2049 passed, 1 failed`. The only failure is the historical pre-attempt
assertion in
`tests/test_phase36_consolidated_runtime_closeout_r2_authorization_proposal.py`
at pre-transition SHA-256
`FCE8DE397F91395014A6009823677F7826B34BE8A42AD3F1325D323ED0BED9D4`.
It correctly required all seven R2 outputs to be absent before authorization.
The consumed attempt created authorization, result, and evidence records; R2
acceptance and all three U3K records remain absent. A future U4F source package
must explicitly allowlist only this state transition while preserving every
immutable package and closed-gate assertion. No edit is authorized now.

## Primary-Source Finding

Microsoft's `about_Module_Manifests` documentation states that `RootModule`
paths should be relative to the module manifest and `FileList` entries should
be relative to the folder containing that manifest. It also describes
`FileList` as an informational inventory. The leading remediation hypothesis
is therefore a field-aware, manifest-directory-relative resolver with separate
load-bearing and inventory requiredness. This is a source-supported hypothesis,
not a claim about the retained missing target.

Sources:

- https://learn.microsoft.com/en-us/powershell/module/microsoft.powershell.core/about/about_module_manifests?view=powershell-7.6
- https://learn.microsoft.com/en-us/powershell/scripting/developer/module/how-to-write-a-powershell-module-manifest?view=powershell-7.5

## Decisions

### D-P3.6-U4E-001: Manifest Relative-Path Resolution

- **A. Field-aware manifest-directory resolution (recommended):** Resolve
  relative direct-file references from the exact manifest directory, then
  require canonical containment beneath both the exact module root and
  `PSHOME`. Continue rejecting absolute paths, URIs, wildcards, expressions,
  traversal, reparse points, duplicates, and overbound files.
- **B. Retain PSHome-relative resolution:** Smallest change, but conflicts with
  official relative-path semantics and may reproduce R2.
- **C. Delegate to `Test-ModuleManifest` or `Import-Module`:** Uses runtime
  semantic evaluation or module loading and materially expands the boundary.
- **D. Permit arbitrary path forms:** Breaks exact local containment.

### D-P3.6-U4E-002: Closure Requiredness And FileList

- **A. Typed load-bearing closure plus bounded inventory (recommended):**
  Strictly require all load-bearing `RootModule`, path-valued `NestedModules`,
  `RequiredAssemblies`, `TypesToProcess`, and `FormatsToProcess` targets.
  Evaluate `FileList` separately: code-like entries remain strict, while a
  missing non-load-bearing inventory entry produces only a bounded sanitized
  count and classification, never a retained path.
- **B. Require every declared entry equally:** Simpler, but can block runtime
  closure on informational inventory.
- **C. Ignore `FileList`:** Avoids inventory false positives but loses
  inventory and code-like file attestation.
- **D. Allow missing load-bearing targets:** Could accept an incomplete or
  tampered module.

### D-P3.6-U4E-003: Pre-Runtime Resolver Evidence

- **A. Generated resolver contract and machine-disabled oracle
  (recommended):** Add a typed resolver contract, PowerShell source,
  machine-disabled Python reference, and at least 512 generated manifest
  vectors covering fields, bases, separators, containment, traversal,
  requiredness, missing targets, extensions, limits, duplicates, and trust
  classifications.
- **B. Patch the R2 runner inline:** Smaller but provides weaker independent
  behavior evidence.
- **C. Run a live-manifest diagnostic first:** Could identify the local field,
  but adds a machine-observation attempt before source remediation.
- **D. Retry R2 unchanged:** The consumed authorization cannot be reused and
  the same deterministic policy is expected to fail again.

### D-P3.6-U4E-004: Historical Evidence And Remediation Shape

- **A. Additive U4F remediation with immutable R2 history (recommended):** Keep
  all consumed R2 and accepted U4D artifacts byte-exact. Add new resolver,
  contract, vectors, tests, evidence, and R3 package paths only.
- **B. Modify R2 in place:** Invalidates its digest-bound authorization and
  evidence.
- **C. Reclassify R2 as partial success:** Contradicts the all-gates closeout
  contract.
- **D. Broaden into models or deployment:** Expands scope without resolving the
  closure blocker.

### D-P3.6-U4E-005: Authorization And Runtime Reentry

- **A. One source-build authorization then one R3 runtime authorization
  (recommended):** Permit bounded source revision and generated/static
  validation first. Bind one later machine attempt to the final exact hashes.
- **B. Combine source build and runtime:** Runtime authority would exist before
  final source and evidence digests are known.
- **C. Add a live diagnostic attempt before R3:** More local evidence, but a
  third owner gate and another machine attempt.
- **D. Stop:** Preserves R2 but leaves P3.6 and Phase 3 incomplete.

Recommended selection: `A/A/A/A/A`.

Selecting options authorizes preparation only of a separate, non-effective
U4F source-build authorization proposal. It does not authorize implementation,
PowerShell parsing or execution, Python machine access, manifest or hardware
observation, another runtime attempt, machine or storage access, `F:`, U3K,
models, media/data, containers/Kubernetes, deployment, commit, push, or remote
Git.
