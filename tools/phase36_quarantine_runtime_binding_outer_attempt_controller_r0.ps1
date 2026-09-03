# Phase 3.6 outer attempt-controller R0.
# Source-only implementation. This file was not parsed, imported, dot-sourced, or executed.

Set-StrictMode -Version Latest

$Script:HcamOuterContractVersion = '1.0.0'
$Script:HcamOuterSourceBuildAuthorization = 'D-P3.6-CONSOLIDATED-BUILD-AUTH'
$Script:HcamOuterRuntimeAuthorization = 'D-P3.6-CONSOLIDATED-RUNTIME-CLOSEOUT-AUTH'
$Script:HcamOuterMachineAuthorityEnabled = $false
$Script:HcamOuterAutomaticRetryEnabled = $false
$Script:HcamOuterPythonMachineFallbackEnabled = $false

$Script:HcamOuterSupportedOperations = @(
    'generated_contract_validation_v1'
)

$Script:HcamOuterStages = @(
    'authorization'
    'fixed_parent_set'
    'runtime_candidate'
    'runtime_hash'
    'runtime_trust'
    'source_preflight'
    'process'
    'result_validation'
    'source_postflight'
    'runtime_postflight'
    'evidence_seal'
)

$Script:HcamOuterRequestFields = @(
    'contract_version'
    'operation'
    'authorization'
    'parent_records'
    'stage_signals'
    'process_limits'
    'process_observation'
    'retention'
)

$Script:HcamOuterAuthorizationFields = @(
    'decision_id'
    'package_digest_sha256'
    'attempt_index'
    'max_attempts'
    'attempt_state'
    'same_package_digest'
    'retry_reason_allowlisted'
    'machine_authority'
    'automatic_retry'
)

$Script:HcamOuterParentFields = @(
    'parent_index'
    'present'
    'regular_directory'
    'nonreparse'
    'canonical_match'
    'valid'
    'reason_code'
)

$Script:HcamOuterStageSignalFields = @(
    'runtime_candidate'
    'runtime_hash'
    'runtime_trust'
    'source_preflight'
    'process'
    'result_validation'
    'source_postflight'
    'runtime_postflight'
    'evidence_seal'
)

$Script:HcamOuterProcessLimitFields = @(
    'timeout_ms'
    'max_stdout_bytes'
    'max_stderr_bytes'
    'max_result_bytes'
    'max_processes'
)

$Script:HcamOuterProcessObservationFields = @(
    'elapsed_ms'
    'stdout_bytes'
    'stderr_bytes'
    'result_bytes'
    'processes'
)

$Script:HcamOuterRetentionFields = @(
    'raw_retained_bytes'
    'sanitized_only'
)

$Script:HcamOuterResultFields = @(
    'terminal'
    'succeeded'
    'stage'
    'reason_code'
    'parent_index'
    'predicate_flags'
    'attempts_consumed'
)

$Script:HcamOuterProcessLimits = [ordered]@{
    timeout_ms = 120000
    max_stdout_bytes = 16384
    max_stderr_bytes = 0
    max_result_bytes = 32768
    max_processes = 1
}

$Script:HcamOuterStageFailureReasons = [ordered]@{
    authorization = 'authorization_invalid'
    fixed_parent_set = 'fixed_parent_set_invalid'
    runtime_candidate = 'runtime_candidate_invalid'
    runtime_hash = 'runtime_hash_invalid'
    runtime_trust = 'runtime_trust_invalid'
    source_preflight = 'source_preflight_failed'
    process = 'process_failed'
    result_validation = 'result_contract_invalid'
    source_postflight = 'source_identity_changed'
    runtime_postflight = 'runtime_identity_changed'
    evidence_seal = 'evidence_seal_failed'
}

# HCAM_OUTER_CONTRACT_PROJECTION_JSON_BEGIN
<#
{
  "authorization_fields": [
    "decision_id",
    "package_digest_sha256",
    "attempt_index",
    "max_attempts",
    "attempt_state",
    "same_package_digest",
    "retry_reason_allowlisted",
    "machine_authority",
    "automatic_retry"
  ],
  "contract_version": "1.0.0",
  "failure_reasons": [
    "authorization_invalid",
    "fixed_parent_set_invalid",
    "runtime_candidate_invalid",
    "runtime_hash_invalid",
    "runtime_trust_invalid",
    "source_preflight_failed",
    "process_failed",
    "result_contract_invalid",
    "source_identity_changed",
    "runtime_identity_changed",
    "evidence_seal_failed",
    "process_timeout",
    "process_output_bounds_failed",
    "terminal_default_deny_internal_failure"
  ],
  "parent_fields": [
    "parent_index",
    "present",
    "regular_directory",
    "nonreparse",
    "canonical_match",
    "valid",
    "reason_code"
  ],
  "parent_indexes": [
    0,
    1,
    2
  ],
  "parent_reason_codes": [
    "parent_valid",
    "parent_missing",
    "parent_not_directory",
    "parent_reparse",
    "parent_canonical_mismatch",
    "parent_predicate_inconsistent"
  ],
  "predicate_flag_fields": [
    "authorization",
    "fixed_parent_set",
    "runtime_candidate",
    "runtime_hash",
    "runtime_trust",
    "source_preflight",
    "process",
    "result_validation",
    "source_postflight",
    "runtime_postflight",
    "evidence_seal"
  ],
  "process_limits": {
    "max_processes": 1,
    "max_result_bytes": 32768,
    "max_stderr_bytes": 0,
    "max_stdout_bytes": 16384,
    "timeout_ms": 120000
  },
  "request_fields": [
    "contract_version",
    "operation",
    "authorization",
    "parent_records",
    "stage_signals",
    "process_limits",
    "process_observation",
    "retention"
  ],
  "result_fields": [
    "terminal",
    "succeeded",
    "stage",
    "reason_code",
    "parent_index",
    "predicate_flags",
    "attempts_consumed"
  ],
  "runtime_authorization": "D-P3.6-CONSOLIDATED-RUNTIME-CLOSEOUT-AUTH",
  "source_build_authorization": "D-P3.6-CONSOLIDATED-BUILD-AUTH",
  "stage_failure_reasons": {
    "authorization": "authorization_invalid",
    "evidence_seal": "evidence_seal_failed",
    "fixed_parent_set": "fixed_parent_set_invalid",
    "process": "process_failed",
    "result_validation": "result_contract_invalid",
    "runtime_candidate": "runtime_candidate_invalid",
    "runtime_hash": "runtime_hash_invalid",
    "runtime_postflight": "runtime_identity_changed",
    "runtime_trust": "runtime_trust_invalid",
    "source_postflight": "source_identity_changed",
    "source_preflight": "source_preflight_failed"
  },
  "stage_signal_fields": [
    "runtime_candidate",
    "runtime_hash",
    "runtime_trust",
    "source_preflight",
    "process",
    "result_validation",
    "source_postflight",
    "runtime_postflight",
    "evidence_seal"
  ],
  "stages": [
    "authorization",
    "fixed_parent_set",
    "runtime_candidate",
    "runtime_hash",
    "runtime_trust",
    "source_preflight",
    "process",
    "result_validation",
    "source_postflight",
    "runtime_postflight",
    "evidence_seal"
  ],
  "supported_operations": [
    "generated_contract_validation_v1"
  ]
}
#>
# HCAM_OUTER_CONTRACT_PROJECTION_JSON_END

function Test-HcamOuterExactFieldSet {
    param(
        [Parameter(Mandatory = $true)]
        [System.Collections.IDictionary]$Value,

        [Parameter(Mandatory = $true)]
        [string[]]$Expected
    )

    if ($Value.Count -ne $Expected.Count) {
        return $false
    }
    foreach ($Name in $Expected) {
        if (-not $Value.Contains($Name)) {
            return $false
        }
    }
    return $true
}

function Test-HcamOuterNonnegativeInteger {
    param([Parameter(Mandatory = $true)][object]$Value)

    if ($Value -isnot [byte] -and
        $Value -isnot [int16] -and
        $Value -isnot [int32] -and
        $Value -isnot [int64]) {
        return $false
    }
    return $Value -ge 0
}

function Get-HcamOuterExpectedParentReason {
    param(
        [Parameter(Mandatory = $true)]
        [System.Collections.IDictionary]$Record
    )

    if ($Record.present -isnot [bool] -or -not $Record.present) {
        return 'parent_missing'
    }
    if ($Record.regular_directory -isnot [bool] -or -not $Record.regular_directory) {
        return 'parent_not_directory'
    }
    if ($Record.nonreparse -isnot [bool] -or -not $Record.nonreparse) {
        return 'parent_reparse'
    }
    if ($Record.canonical_match -isnot [bool] -or -not $Record.canonical_match) {
        return 'parent_canonical_mismatch'
    }
    return 'parent_valid'
}

function Test-HcamOuterParentRecord {
    param(
        [Parameter(Mandatory = $true)]
        [System.Collections.IDictionary]$Record,

        [Parameter(Mandatory = $true)]
        [int]$ExpectedIndex
    )

    if (-not (Test-HcamOuterExactFieldSet -Value $Record -Expected $Script:HcamOuterParentFields)) {
        return $false
    }
    if ($Record.parent_index -isnot [int] -or $Record.parent_index -ne $ExpectedIndex) {
        return $false
    }
    foreach ($Name in @('present', 'regular_directory', 'nonreparse', 'canonical_match', 'valid')) {
        if ($Record[$Name] -isnot [bool]) {
            return $false
        }
    }
    $DerivedValid = (
        $Record.present -and
        $Record.regular_directory -and
        $Record.nonreparse -and
        $Record.canonical_match
    )
    if ($Record.valid -ne $DerivedValid) {
        return (-not $Record.valid -and $Record.reason_code -ceq 'parent_predicate_inconsistent')
    }
    return $Record.reason_code -ceq (Get-HcamOuterExpectedParentReason -Record $Record)
}

function Test-HcamOuterFixedParentSet {
    param(
        [Parameter(Mandatory = $true)]
        [object[]]$Records
    )

    if ($Records.Count -ne 3) {
        return [ordered]@{ valid = $false; parent_index = $null }
    }
    for ($Index = 0; $Index -lt 3; $Index += 1) {
        if ($Records[$Index] -isnot [System.Collections.IDictionary]) {
            return [ordered]@{ valid = $false; parent_index = $Index }
        }
        if (-not (Test-HcamOuterParentRecord -Record $Records[$Index] -ExpectedIndex $Index)) {
            return [ordered]@{ valid = $false; parent_index = $Index }
        }
    }
    for ($Index = 0; $Index -lt 3; $Index += 1) {
        if ($Records[$Index].valid -isnot [bool] -or $Records[$Index].valid -ne $true) {
            return [ordered]@{ valid = $false; parent_index = $Index }
        }
    }
    return [ordered]@{ valid = $true; parent_index = $null }
}

function New-HcamOuterPredicateFlags {
    param([AllowNull()][string]$FailedStage)

    $Flags = [ordered]@{}
    $FailureSeen = $false
    foreach ($Stage in $Script:HcamOuterStages) {
        if ($null -ne $FailedStage -and $Stage -ceq $FailedStage) {
            $FailureSeen = $true
        }
        $Flags[$Stage] = -not $FailureSeen
    }
    return $Flags
}

function New-HcamOuterTerminalResult {
    param(
        [Parameter(Mandatory = $true)][bool]$Succeeded,
        [Parameter(Mandatory = $true)][string]$Stage,
        [Parameter(Mandatory = $true)][string]$ReasonCode,
        [AllowNull()][object]$ParentIndex,
        [Parameter(Mandatory = $true)][int]$AttemptsConsumed
    )

    $FailedStage = if ($Succeeded) { $null } else { $Stage }
    return [ordered]@{
        terminal = $true
        succeeded = $Succeeded
        stage = $Stage
        reason_code = $ReasonCode
        parent_index = $ParentIndex
        predicate_flags = New-HcamOuterPredicateFlags -FailedStage $FailedStage
        attempts_consumed = $AttemptsConsumed
    }
}

function New-HcamOuterDefaultDenyResult {
    param([int]$AttemptsConsumed = 0)

    return New-HcamOuterTerminalResult `
        -Succeeded $false `
        -Stage 'authorization' `
        -ReasonCode 'terminal_default_deny_internal_failure' `
        -ParentIndex $null `
        -AttemptsConsumed $AttemptsConsumed
}

function Invoke-HcamOuterAttemptControllerR0 {
    param(
        [Parameter(Mandatory = $true)]
        [System.Collections.IDictionary]$Request
    )

    $Attempts = 0
    if ($Request.Contains('authorization') -and
        $Request.authorization -is [System.Collections.IDictionary] -and
        $Request.authorization.Contains('attempt_index') -and
        $Request.authorization.attempt_index -is [int] -and
        $Request.authorization.attempt_index -in @(1, 2, 3)) {
        $Attempts = $Request.authorization.attempt_index
    }
    if (-not (Test-HcamOuterExactFieldSet -Value $Request -Expected $Script:HcamOuterRequestFields)) {
        return New-HcamOuterDefaultDenyResult -AttemptsConsumed $Attempts
    }
    if ($Request.contract_version -cne $Script:HcamOuterContractVersion -or
        $Request.operation -cnotin $Script:HcamOuterSupportedOperations) {
        return New-HcamOuterDefaultDenyResult -AttemptsConsumed $Attempts
    }
    $Authorization = $Request.authorization
    if ($Authorization -isnot [System.Collections.IDictionary] -or
        -not (Test-HcamOuterExactFieldSet -Value $Authorization -Expected $Script:HcamOuterAuthorizationFields)) {
        return New-HcamOuterDefaultDenyResult -AttemptsConsumed $Attempts
    }
    if ($Authorization.decision_id -cne $Script:HcamOuterRuntimeAuthorization -or
        $Authorization.package_digest_sha256 -cnotmatch '^[0-9A-F]{64}$' -or
        $Authorization.max_attempts -ne 3 -or
        $Authorization.machine_authority -isnot [bool] -or
        -not $Authorization.machine_authority -or
        $Authorization.automatic_retry -isnot [bool] -or
        $Authorization.automatic_retry) {
        return New-HcamOuterTerminalResult `
            -Succeeded $false -Stage 'authorization' `
            -ReasonCode 'authorization_invalid' -ParentIndex $null `
            -AttemptsConsumed $Attempts
    }
    if (($Authorization.attempt_state -ceq 'first' -and $Attempts -ne 1) -or
        ($Authorization.attempt_state -ceq 'retry' -and
            ($Attempts -le 1 -or -not $Authorization.same_package_digest -or
                -not $Authorization.retry_reason_allowlisted)) -or
        $Authorization.attempt_state -cnotin @('first', 'retry')) {
        return New-HcamOuterTerminalResult `
            -Succeeded $false -Stage 'authorization' `
            -ReasonCode 'authorization_invalid' -ParentIndex $null `
            -AttemptsConsumed $Attempts
    }

    $ParentSet = Test-HcamOuterFixedParentSet -Records $Request.parent_records
    if (-not $ParentSet.valid) {
        return New-HcamOuterTerminalResult `
            -Succeeded $false -Stage 'fixed_parent_set' `
            -ReasonCode 'fixed_parent_set_invalid' `
            -ParentIndex $ParentSet.parent_index -AttemptsConsumed $Attempts
    }

    foreach ($Stage in @('runtime_candidate', 'runtime_hash', 'runtime_trust', 'source_preflight')) {
        if ($Request.stage_signals[$Stage] -isnot [bool] -or
            $Request.stage_signals[$Stage] -ne $true) {
            return New-HcamOuterTerminalResult `
                -Succeeded $false -Stage $Stage `
                -ReasonCode $Script:HcamOuterStageFailureReasons[$Stage] `
                -ParentIndex $null -AttemptsConsumed $Attempts
        }
    }

    $Process = $Request.process_observation
    if ($Request.stage_signals.process -ne $true) {
        $ProcessReason = 'process_failed'
    }
    elseif ($Process.elapsed_ms -gt $Script:HcamOuterProcessLimits.timeout_ms) {
        $ProcessReason = 'process_timeout'
    }
    elseif ($Process.stdout_bytes -gt $Script:HcamOuterProcessLimits.max_stdout_bytes -or
        $Process.stderr_bytes -gt $Script:HcamOuterProcessLimits.max_stderr_bytes -or
        $Process.result_bytes -gt $Script:HcamOuterProcessLimits.max_result_bytes -or
        $Process.processes -gt $Script:HcamOuterProcessLimits.max_processes) {
        $ProcessReason = 'process_output_bounds_failed'
    }
    else {
        $ProcessReason = $null
    }
    if ($null -ne $ProcessReason) {
        return New-HcamOuterTerminalResult `
            -Succeeded $false -Stage 'process' -ReasonCode $ProcessReason `
            -ParentIndex $null -AttemptsConsumed $Attempts
    }

    if ($Request.stage_signals.result_validation -ne $true -or
        $Request.retention.raw_retained_bytes -ne 0 -or
        $Request.retention.sanitized_only -ne $true) {
        return New-HcamOuterTerminalResult `
            -Succeeded $false -Stage 'result_validation' `
            -ReasonCode 'result_contract_invalid' -ParentIndex $null `
            -AttemptsConsumed $Attempts
    }
    foreach ($Stage in @('source_postflight', 'runtime_postflight', 'evidence_seal')) {
        if ($Request.stage_signals[$Stage] -isnot [bool] -or
            $Request.stage_signals[$Stage] -ne $true) {
            return New-HcamOuterTerminalResult `
                -Succeeded $false -Stage $Stage `
                -ReasonCode $Script:HcamOuterStageFailureReasons[$Stage] `
                -ParentIndex $null -AttemptsConsumed $Attempts
        }
    }
    return New-HcamOuterTerminalResult `
        -Succeeded $true -Stage 'evidence_seal' -ReasonCode 'policy_valid' `
        -ParentIndex $null -AttemptsConsumed $Attempts
}
