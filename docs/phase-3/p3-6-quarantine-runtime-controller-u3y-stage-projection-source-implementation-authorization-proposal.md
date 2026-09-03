# P3.6 U3Y Controller R1 Source Implementation Authorization Proposal

## Purpose

This non-effective proposal defines a future additive controller successor for
the U3W `controller_stage_projection_invalid` failure. It does not implement or
execute that successor.

## Accepted Direction

`D-P3.6-U3X-FAILURE-ANALYSIS-DECISIONS` selected `A/A/A/A`:

- preserve the accepted controller and diagnostic as immutable history;
- retain exact null semantics for successful stage projection;
- require generated/static evidence followed by a separately authorized
  generated-only PowerShell contract validation;
- permit a later system diagnostic only after that contract evidence is
  separately accepted.

## Proposed Additive Successor

The future R1 controller must preserve wire contract version `1.0.0`. A
successful `policy_valid` result must contain:

```json
{
  "completed_actions": 18,
  "failed_action": null,
  "failed_stage": null
}
```

The successor must construct those literal nulls without routing
`failed_action` through a string-typed nullable parameter. Failure projections
continue to require the exact completed-action index and nonempty allowlisted
action and reason strings. Empty string is not equivalent to null.

## Future Implementation Surface

If separately authorized, implementation is limited to eleven additive paths:
one contract, PowerShell successor, machine-disabled Python reference, generated
vector manifest, four generated/static test modules, evidence, package, and
human evidence review. The historical controller, diagnostic, diagnostic
contract, and U3W evidence remain byte-exact.

The source evidence must include at least 256 generated vectors and at least
95% branch coverage for the machine-disabled Python reference. PowerShell is
not executed as source implementation evidence.

## Current Gate

`D-P3.6-U3Y-CONTROLLER-R1-STAGE-PROJECTION-IMPLEMENTATION-AUTH` remains
pending. This package grants no source or test implementation, PowerShell
parsing or execution, Python machine access, runtime observation, another
attempt, U3K, deployment, or remote Git.
