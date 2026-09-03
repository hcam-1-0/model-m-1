# P3.6 Inventory R1 Authorization Proposal R0

Status: owner review pending. This is a planning package under
`D-P3.6-PLAN-AUTH`; it is not an inventory authorization and no action in the
collector specification has been run.

Machine-readable records:

- [authorization proposal](../../contracts/phase-3/p3-6-inventory-r1-authorization-proposal.json);
- [collector specification](../../contracts/phase-3/p3-6-inventory-r1-collector-spec.json);
- [trust policy snapshot](../../contracts/phase-3/p3-6-inventory-r1-trust-policy.json);
- [research sources](../../contracts/phase-3/p3-6-inventory-r1-research-sources.json); and
- [historical R0](../../contracts/phase-3/p3-6-inventory-lab-laptop-01-r0.json).

## Purpose

The accepted `D-P3.6-U3A-001` through `D-P3.6-U3A-004` choices require a new,
fresh inventory in the exact shared Phase -1 shape. They do not authorize that
collection. This package turns the policy choices into one inspectable action
proposal for `LAB-LAPTOP-01` while preserving historical R0 unchanged.

The proposed R1 is deliberately narrower than R0. It collects only facts
needed to form the required operating-system, CPU, memory, and limited runtime
metadata fields. It does not repeat fixed-storage, drive-letter, display,
driver, or raw device observations. Unobserved facts remain explicit
`unknown` values.

## Exact Shared Contract

The future record must validate against:

| Property | Binding |
| --- | --- |
| Repository | `hcam-2-0/hcam-protos` |
| Revision | `d71cdc9c51d01d746d5195bcb2ac639e0fdf11c8` |
| Schema | `schemas/platform/v1alpha1/node-capability-inventory.schema.json` |
| Schema version | `hcam.platform.node-capability-inventory/v1alpha1` |
| SHA-256 | `C9947BE12888C0A05B29DA0266E2359B107024AF07E536AE10BAC55457C5C7D3` |

The schema requires timestamps, provenance, normalized capability states,
bounded findings, and the exact seven-category redaction declaration. The
shared documentation also requires consumers to fail closed outside the
freshness interval and states that inventory is never execution authority.

## Proposed Collection

One future owner acceptance would authorize one attempt within 24 hours of
acceptance. A failed attempt would consume the authorization; retrying would
require another explicit owner decision.

The exact action set is:

1. Read the UTC transaction start time in process memory.
2. Read only `Version`, `BuildNumber`, `OSArchitecture`,
   `TotalVisibleMemorySize`, and `FreePhysicalMemory` from the local
   `Win32_OperatingSystem` CIM instance.
3. Read only `Architecture`, `NumberOfCores`, and
   `NumberOfLogicalProcessors` from local `Win32_Processor` CIM instances.
4. Start the default Python interpreter in isolated, no-site mode and ask only
   for its version family, if available.
5. Start Python in isolated, no-site mode; add only its calculated distribution
   metadata roots in process memory; and ask `importlib.metadata` only for the
   installed `onnxruntime` distribution version. The proposal forbids importing
   or loading `onnxruntime` and never persists a calculated path.
6. Run only `ffmpeg -version`, parse the first line, and discard all raw
   output. No media, input, device, protocol, codec listing, or build
   configuration is opened.
7. Generate an opaque `inv_` snapshot identifier from random bytes, without
   using a host or hardware value.
8. Read one UTC completion time and set `valid_until` to exactly 86,400 seconds
   later.
9. Normalize in memory, validate against the pinned schema, hash canonical
   JSON, and atomically write only the authorized outputs.

Each source or version action is bounded to 10 seconds; the whole transaction
is bounded to 60 seconds. Each version process is limited to 16 KiB of stdout
and 16 KiB of stderr. Actions run sequentially. No `ComputerName`,
`CimSession`, remote target, proxy, localhost service, or other network route is
permitted.

The property allowlists prevent intentional access to non-selected CIM fields.
If a CIM provider supplies key metadata as part of its internal instance shape,
the collector may not inspect, project, log, hash, or persist it; it is
discarded with the short-lived source object.

Microsoft documents that `Get-CimInstance` without `ComputerName` or
`CimSession` uses local Windows WMI, and that its `Property` parameter limits
the returned subset. The selected operating-system and processor fields are
read-only properties. Python documents `importlib.metadata.version()` as the
installed distribution-version API. FFmpeg documents `-version` as a version
display action. Exact source URLs and the facts used are recorded in the source
ledger.

## Projection Rules

Required OS, CPU, or memory collection or normalization failure aborts R1
creation. Optional Python, ONNX Runtime metadata, or FFmpeg failure does not;
the result remains `unknown` and receives a bounded finding.

The projection records:

- local read-only, observed provenance and collector version
  `hcam-p36-r1-spec-1.0.0`;
- `cpu_laptop` as the node class;
- Windows family, normalized architecture, and sanitized version/build family;
- summed physical-core and logical-processor counts;
- current total and available memory converted from reported kilobytes to MiB;
- `unknown` instruction sets;
- `unknown` accelerators with no items;
- only successfully parsed Python, ONNX Runtime distribution, and FFmpeg
  version families, each without a compatibility claim;
- `unknown` container and scheduler capabilities; and
- only the shared bounded finding codes and exact redaction declaration.

Version metadata means only that a command or distribution record was
observable. It is not proof that an H-CAM runtime, execution provider, model,
decoder, container engine, or scheduler is functional or compatible.

## Fields Intentionally Not Collected

The proposal expressly excludes:

- hostname, domain, user, registered owner, serial, asset tag, UUID, MAC, IP,
  network, personal path, installation path, and secret reference;
- manufacturer, model, processor name, processor ID, PNP ID, PCI location, and
  raw device identifier;
- disks, volumes, free storage, drive letters, and storage paths;
- display adapter, display driver, accelerator memory, GPU driver, compute API,
  precision, and `nvidia-smi`;
- environment and `PATH` enumeration;
- Python package files, dependencies, origins, paths, or entry points;
- Docker, containerd, Kubernetes, scheduler, daemon, socket, or service
  contact;
- model/runtime import, loading, inference, conversion, compilation, benchmark,
  performance, capacity, stress, or thermal action; and
- camera, stream, media, device, protocol, dataset, private, or Government data
  access.

This minimization is why accelerators, containers, scheduler features, CPU
instruction sets, and runtime compatibility remain unknown. The record must
not infer them from R0 or from an installed CLI.

## Trust Snapshot

The package contains a separate `hcam-owned-local-generated-only-r0` policy
snapshot. It binds the logical `portable_cpu` environment to an owned local lab
with network denied and generated-only data boundaries. Its SHA-256 is:

`E76D0C56476A98AADDBC7880AD75858B5B61D45CE95802E3FB39557E226C6106`

Accepting the future authorization statement would also accept this exact
snapshot as the trust context for R1. The digest may become a future placement
input only after separate admission authority. The policy and digest do not
authorize profile resolution, placement, or execution.

## Outputs And Failure Handling

Before collection, an accepted owner statement would be recorded at:

`contracts/phase-3/p3-6-inventory-r1-authorization.json`

A successful attempt would then write:

- `contracts/phase-3/p3-6-inventory-lab-laptop-01-r1.json`; and
- `contracts/phase-3/p3-6-inventory-r1-collection-evidence.json`.

The evidence record is also required on failure, but it may contain only
bounded action outcomes and no raw command output, exception, stack trace, host
identity, path, or machine values. R1 is not written if a required source,
required value, schema validation, hash, path, or atomic-write rule fails.

Canonical output uses UTF-8 without a byte-order mark or trailing newline,
recursively sorted object keys, contract-defined array order, compact JSON
separators, ASCII escaping, and uppercase SHA-256. Writes use a same-directory
temporary file followed by replacement of the exact non-symlink target.

## Freshness And Invalidation

`observed_at` is the single UTC timestamp at successful completion.
`valid_until` is exactly 86,400 seconds later. The record must be invalidated
earlier after an authorized hardware, operating-system, driver, runtime,
collector, or trust-policy change.

This package does not implement change monitoring. Expiry or known
invalidation blocks new resolution and placement and never retimestamps the
record. Independent reservation, lease, fencing, health, cancellation, and
policy authority remains separate.

## Owner Decision

No owner decision has been inferred from `continue`. To accept this package,
the owner must use the final package digest in the exact statement below:

```text
D-P3.6-INVENTORY-R1-AUTH: I, mayank-admin, accept the owned-local generated-only trust policy and authorize one sanitized local read-only R1 collection attempt on LAB-LAPTOP-01 against package digest <PACKAGE_DIGEST_SHA256>, within 24 hours and limited to the exact actions, fields, timeouts, redaction, schema, and output paths in that package. A failed attempt requires new authorization. This does not authorize reusable collector or product implementation, profile activation or placement, models or AI runtime execution, hardware testing, accelerators, containers or Kubernetes, cameras, media, data, network access, deployment, or remote Git.
```

Acceptance must bind the exact manifest digest. Any change to a core file,
schema revision, collector action, field, timeout, trust policy, output path,
or prohibition requires a new package and a new owner statement.

## Current Effect

Current authority remains planning only. No collector exists, no action has
run, no current laptop fact has been observed, and no R1 or evidence output has
been created. `P36-G2` stays blocked. Profile activation, model/runtime action,
hardware testing, accelerators, containers, Kubernetes, camera/media/data
access, deployment, and remote Git all remain unauthorized.
