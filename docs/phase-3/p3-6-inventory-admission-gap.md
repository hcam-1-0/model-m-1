# P3.6 Inventory And Admission Gap R0

Status: planning-only gap analysis and owner options under
`D-P3.6-PLAN-AUTH`. No inventory recollection, profile activation, runtime, or
deployment is authorized.

Machine-readable records:

- [gap analysis](../../contracts/phase-3/p3-6-inventory-admission-gap.json);
- [owner decision packet](../../contracts/phase-3/p3-6-inventory-admission-decision-packet.json);
- [research sources](../../contracts/phase-3/p3-6-inventory-admission-research-sources.json); and
- [historical R0 inventory](../../contracts/phase-3/p3-6-inventory-lab-laptop-01-r0.json).

## Finding

The accepted `LAB-LAPTOP-01` R0 inventory remains valid historical evidence of
the read-only collection that was authorized. It is not structurally
interchangeable with the exact Phase -1
`hcam.platform.node-capability-inventory/v1alpha1` contract. It must not be
overwritten, retimestamped, automatically extended, or treated as runnable
admission evidence.

The shared contract at `hcam-protos`
`d71cdc9c51d01d746d5195bcb2ac639e0fdf11c8` requires an opaque inventory
snapshot ID, `observed_at`, `valid_until`, structured provenance, normalized
capability states, a fixed redaction declaration, and explicit unknown values.
The portable deployment profile at `hcam-deployment`
`71095fe89d2b711e4982ddc0130fcaedda8703e7` also requires H-CAM admission,
forbids oversubscription by default, and does not grant execution authority.

## Exact Gaps

| Area | R0 state | Required R1 treatment |
| --- | --- | --- |
| Contract identity | P3.6-specific format | Use exact shared v1alpha1 schema in a new record |
| Snapshot identity | Logical node label | Create a new opaque snapshot ID, never a host identity |
| Freshness | Collection timestamp only | Bind both observation and owner-approved expiry |
| Provenance | Read-only mode recorded | Add shared collection mode, trust level, and sanitized collector version |
| Node class | Portable assessment only | Bind `cpu_laptop` explicitly |
| OS and CPU | Useful raw facts | Normalize enums and states; keep instruction sets unknown unless recollected |
| Memory | Total only | Record available memory or explicit unknown state |
| Accelerator | Display metadata only | Never infer compute API, precision, memory, or provider support |
| Runtimes | CLI/default-Python metadata | Record only exact observed families and explicit unknowns |
| Containers | Docker CLI present | Do not infer engine, Compose, or GPU passthrough |
| Scheduler | Not collected | Preserve every scheduler capability as unknown |
| Findings | Free-form risks | Use bounded shared codes; retain P3.6 risks separately |
| Redaction | Historical exclusion list | Use the exact seven-category shared policy including secret references |
| Trust zone | Missing | Bind a separate policy snapshot by opaque digest during capacity placement |

Drive letters, storage details, raw processor/display names, memory-module
layout, profile assessments, and narrative authorization evidence remain in
the immutable historical record. They do not belong in the portable shared
inventory projection.

## Freshness Policy Options

NIST SP 800-53 Rev. 5 CM-8 requires an accurate component inventory but leaves
review/update frequency to the organization. Therefore, no external standard
selects an H-CAM duration automatically.

The recommended lab policy is a maximum 24-hour validity window plus immediate
invalidation after an authorized hardware, OS, driver, runtime, collector, or
trust-policy change. This duration is a proposal, not an accepted value or a
NIST requirement. The existing R0 observation from `2026-08-28T21:10:51Z`
would already be stale under that proposal.

Alternatives are an 8-hour session window, a 7-day window, a custom positive
duration, or deferral. Shorter windows improve freshness but increase
collection friction. Longer windows reduce friction but allow older
compatibility evidence.

## Provenance And Trust

The shared inventory records provenance trust as `unknown`, `declared`,
`observed`, or `attested`. It does not contain a human trust-zone label. The
separate workload-placement contract carries only an opaque
`trust_zone_digest` sourced from a policy context.

The recommended current-lab option is:

- `local_read_only` collection with `observed` provenance;
- a separate owner-accepted policy snapshot for an owned-local,
  generated-only environment;
- an opaque digest of that policy in future capacity and placement records;
- no inference of trust from a laptop, local backend, network location, or
  inventory fact alone.

This follows the policy-decision and enforcement separation in NIST SP
800-207. No trust-zone snapshot or digest is created by this package.

## Expiry Behavior

The recommended behavior is fail closed for new work:

1. expired inventory cannot enter profile resolution or placement;
2. a derived resolution decision cannot outlive its immutable input;
3. expiry never retimestamps or extends trust automatically;
4. already admitted work remains governed by its independent reservation,
   lease, fencing, health, cancellation, and policy rules;
5. an explicit policy or lease event, not stale static inventory alone,
   decides whether active work pauses.

Immediate safe pause, a grace period, and an owner-defined alternative remain
available options. No behavior is active because no runtime exists.

## Owner Selections

The pending decision packet asks for four independent selections:

| Decision | Recommended | Topic |
| --- | --- | --- |
| `D-P3.6-U3A-001` | A | Preserve R0 and later collect canonical R1 |
| `D-P3.6-U3A-002` | A | 24-hour maximum plus change invalidation |
| `D-P3.6-U3A-003` | A | Observed local provenance plus separate generated-only trust digest |
| `D-P3.6-U3A-004` | A | Block new admission while independent leases remain authoritative |

Selecting options records policy preferences only. It does not authorize
collection. After selection, a separate exact
`D-P3.6-INVENTORY-R1-AUTH` package must enumerate collection actions, fields,
collector identity/version, sanitization, output path, schema digest, validity
policy, and continuing prohibitions.

## Continuing Boundary

This package authorizes no hardware/runtime query, projection, recollection,
installation, model loading, inference, benchmark, scheduler, container,
Kubernetes, camera/media/stream/data access, profile activation, placement,
deployment, or remote Git action. `P36-G2` remains blocked.
