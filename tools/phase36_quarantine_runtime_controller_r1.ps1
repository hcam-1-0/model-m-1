# Phase 3.6 runtime-controller R1 stage-projection remediation.
# Source-only implementation. No parser, import, dot-source, or execution evidence exists.

Set-StrictMode -Version Latest

$Script:HcamContractVersion = '1.0.0'
$Script:HcamAuthorizationDecision = 'D-P3.6-U3Y-CONTROLLER-R1-STAGE-PROJECTION-IMPLEMENTATION-AUTH'
$Script:HcamMachineAuthorityEnabled = $false
$Script:HcamAutomaticRetryEnabled = $false
$Script:HcamPythonMachineFallbackEnabled = $false

$Script:HcamModes = @(
    'Policy'
    'Preflight'
)

$Script:HcamRequestFields = @(
    'contract_version'
    'mode'
    'authorization_binding'
    'declared_bounds'
    'action_plan'
    'input_bindings'
)

$Script:HcamResultFields = @(
    'contract_version'
    'terminal'
    'succeeded'
    'reason_code'
    'stage_projection'
    'action_counts'
    'retention_projection'
    'gate_effect'
)

$Script:HcamStageProjectionFields = @(
    'completed_actions'
    'failed_action'
    'failed_stage'
)

$Script:HcamAuthorizationFields = @(
    'decision_id'
    'package_digest_sha256'
    'attempt_index'
    'attempt_state'
    'expires_at_utc'
    'authorization_window_state'
    'source_hashes'
    'machine_authority'
    'automatic_retry'
)

$Script:HcamSourceHashFields = @(
    'contract'
    'vectors'
    'powershell'
    'python'
)

$Script:HcamBoundFields = @(
    'per_action_timeout_ms'
    'total_timeout_ms'
    'max_stdout_bytes'
    'max_stderr_bytes'
    'max_result_bytes'
    'max_closure_files'
    'max_closure_bytes'
    'max_processes'
    'max_cleanup_actions'
)

$Script:HcamInputFields = @(
    'stage_outcomes'
    'elapsed_ms'
    'stdout_bytes'
    'stderr_bytes'
    'result_bytes'
    'closure_file_count'
    'closure_total_bytes'
    'retained_raw_bytes'
    'cleanup_count'
    'process_count'
    'source_binding_match'
    'cross_language_match'
)

$Script:HcamActionOrder = @(
    'validate_request_contract'
    'validate_authorization_binding'
    'classify_runtime_path'
    'read_runtime_metadata'
    'hash_runtime'
    'initialize_runtime_trust'
    'verify_runtime_trust'
    'close_runtime_trust'
    'reverify_runtime_identity'
    'classify_utility_manifest_path'
    'parse_utility_manifest'
    'bind_utility_manifest_closure'
    'bind_sources'
    'start_validation_process'
    'enforce_process_timeout'
    'validate_process_output_bounds'
    'validate_result_contract'
    'compare_cross_language_projection'
)

$Script:HcamActionFailureReasons = [ordered]@{
    validate_request_contract = 'request_contract_failed'
    validate_authorization_binding = 'authorization_binding_failed'
    classify_runtime_path = 'runtime_path_classification_failed'
    read_runtime_metadata = 'runtime_metadata_failed'
    hash_runtime = 'runtime_hash_failed'
    initialize_runtime_trust = 'runtime_trust_initialization_failed'
    verify_runtime_trust = 'runtime_trust_verification_failed'
    close_runtime_trust = 'runtime_trust_close_failed'
    reverify_runtime_identity = 'runtime_identity_changed'
    classify_utility_manifest_path = 'utility_manifest_path_failed'
    parse_utility_manifest = 'utility_manifest_parser_failed'
    bind_utility_manifest_closure = 'utility_manifest_closure_failed'
    bind_sources = 'source_binding_failed'
    start_validation_process = 'process_start_failed'
    enforce_process_timeout = 'process_timeout'
    validate_process_output_bounds = 'process_output_bounds_failed'
    validate_result_contract = 'result_contract_invalid'
    compare_cross_language_projection = 'cross_language_projection_diverged'
}

$Script:HcamFailureReasonCodes = @(
    'request_contract_failed'
    'authorization_binding_failed'
    'runtime_path_classification_failed'
    'runtime_metadata_failed'
    'runtime_hash_failed'
    'runtime_trust_initialization_failed'
    'runtime_trust_verification_failed'
    'runtime_trust_close_failed'
    'runtime_identity_changed'
    'utility_manifest_path_failed'
    'utility_manifest_parser_failed'
    'utility_manifest_closure_failed'
    'source_binding_failed'
    'process_start_failed'
    'process_timeout'
    'process_output_bounds_failed'
    'result_contract_invalid'
    'cross_language_projection_diverged'
)

$Script:HcamProhibitedFieldNames = @(
    'acl'
    'credentials'
    'environment'
    'exception'
    'fixture_payload'
    'hostname'
    'ip_address'
    'mac'
    'manifest_text'
    'manifest_tokens'
    'native_status'
    'parser_objects'
    'password'
    'personal_path'
    'raw_exception'
    'sddl'
    'secret'
    'serial'
    'sid'
    'stack'
    'stderr'
    'stdout'
    'user'
    'username'
)

$Script:HcamDeferredMachineOperations = [ordered]@{
    classify_runtime_path = 'future_exact_path_classification'
    read_runtime_metadata = 'future_bounded_runtime_metadata'
    hash_runtime = 'future_streaming_sha256'
    initialize_runtime_trust = 'future_cache_only_trust_initialization'
    verify_runtime_trust = 'future_cache_only_trust_verification'
    close_runtime_trust = 'future_trust_state_close'
    reverify_runtime_identity = 'future_runtime_identity_recheck'
    classify_utility_manifest_path = 'future_exact_manifest_path_classification'
    parse_utility_manifest = 'future_literal_manifest_parser'
    bind_utility_manifest_closure = 'future_bounded_manifest_closure'
    bind_sources = 'future_exact_source_hash_binding'
    start_validation_process = 'future_single_bounded_validation_process'
    enforce_process_timeout = 'future_monotonic_process_deadline'
    validate_process_output_bounds = 'future_bounded_sanitized_output'
}

# HCAM_CONTRACT_PROJECTION_JSON_BEGIN
<#
{
  "action_failure_reasons": {
    "bind_sources": "source_binding_failed",
    "bind_utility_manifest_closure": "utility_manifest_closure_failed",
    "classify_runtime_path": "runtime_path_classification_failed",
    "classify_utility_manifest_path": "utility_manifest_path_failed",
    "close_runtime_trust": "runtime_trust_close_failed",
    "compare_cross_language_projection": "cross_language_projection_diverged",
    "enforce_process_timeout": "process_timeout",
    "hash_runtime": "runtime_hash_failed",
    "initialize_runtime_trust": "runtime_trust_initialization_failed",
    "parse_utility_manifest": "utility_manifest_parser_failed",
    "read_runtime_metadata": "runtime_metadata_failed",
    "reverify_runtime_identity": "runtime_identity_changed",
    "start_validation_process": "process_start_failed",
    "validate_authorization_binding": "authorization_binding_failed",
    "validate_process_output_bounds": "process_output_bounds_failed",
    "validate_request_contract": "request_contract_failed",
    "validate_result_contract": "result_contract_invalid",
    "verify_runtime_trust": "runtime_trust_verification_failed"
  },
  "action_order": [
    "validate_request_contract",
    "validate_authorization_binding",
    "classify_runtime_path",
    "read_runtime_metadata",
    "hash_runtime",
    "initialize_runtime_trust",
    "verify_runtime_trust",
    "close_runtime_trust",
    "reverify_runtime_identity",
    "classify_utility_manifest_path",
    "parse_utility_manifest",
    "bind_utility_manifest_closure",
    "bind_sources",
    "start_validation_process",
    "enforce_process_timeout",
    "validate_process_output_bounds",
    "validate_result_contract",
    "compare_cross_language_projection"
  ],
  "authorization_fields": [
    "decision_id",
    "package_digest_sha256",
    "attempt_index",
    "attempt_state",
    "expires_at_utc",
    "authorization_window_state",
    "source_hashes",
    "machine_authority",
    "automatic_retry"
  ],
  "bound_fields": [
    "per_action_timeout_ms",
    "total_timeout_ms",
    "max_stdout_bytes",
    "max_stderr_bytes",
    "max_result_bytes",
    "max_closure_files",
    "max_closure_bytes",
    "max_processes",
    "max_cleanup_actions"
  ],
  "contract_version": "1.0.0",
  "failure_reason_codes": [
    "request_contract_failed",
    "authorization_binding_failed",
    "runtime_path_classification_failed",
    "runtime_metadata_failed",
    "runtime_hash_failed",
    "runtime_trust_initialization_failed",
    "runtime_trust_verification_failed",
    "runtime_trust_close_failed",
    "runtime_identity_changed",
    "utility_manifest_path_failed",
    "utility_manifest_parser_failed",
    "utility_manifest_closure_failed",
    "source_binding_failed",
    "process_start_failed",
    "process_timeout",
    "process_output_bounds_failed",
    "result_contract_invalid",
    "cross_language_projection_diverged"
  ],
  "input_fields": [
    "stage_outcomes",
    "elapsed_ms",
    "stdout_bytes",
    "stderr_bytes",
    "result_bytes",
    "closure_file_count",
    "closure_total_bytes",
    "retained_raw_bytes",
    "cleanup_count",
    "process_count",
    "source_binding_match",
    "cross_language_match"
  ],
  "modes": [
    "Policy",
    "Preflight"
  ],
  "prohibited_field_names": [
    "acl",
    "credentials",
    "environment",
    "exception",
    "fixture_payload",
    "hostname",
    "ip_address",
    "mac",
    "manifest_text",
    "manifest_tokens",
    "native_status",
    "parser_objects",
    "password",
    "personal_path",
    "raw_exception",
    "sddl",
    "secret",
    "serial",
    "sid",
    "stack",
    "stderr",
    "stdout",
    "user",
    "username"
  ],
  "request_fields": [
    "contract_version",
    "mode",
    "authorization_binding",
    "declared_bounds",
    "action_plan",
    "input_bindings"
  ],
  "result_fields": [
    "contract_version",
    "terminal",
    "succeeded",
    "reason_code",
    "stage_projection",
    "action_counts",
    "retention_projection",
    "gate_effect"
  ],
  "source_hash_fields": [
    "contract",
    "vectors",
    "powershell",
    "python"
  ],
  "stage_projection_fields": [
    "completed_actions",
    "failed_action",
    "failed_stage"
  ]
}
#>
# HCAM_CONTRACT_PROJECTION_JSON_END

function Test-HcamExactFieldSet {
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

function New-HcamTerminalProjection {
    param(
        [Parameter(Mandatory = $true)]
        [string]$ReasonCode,

        [Parameter(Mandatory = $true)]
        [bool]$Succeeded,

        [Parameter(Mandatory = $true)]
        [System.Collections.IDictionary]$StageProjection,

        [int]$ProcessCount = 0,

        [int]$CleanupCount = 0
    )

    return [ordered]@{
        contract_version = $Script:HcamContractVersion
        terminal = $true
        succeeded = $Succeeded
        reason_code = $ReasonCode
        stage_projection = $StageProjection
        action_counts = [ordered]@{
            planned = $Script:HcamActionOrder.Count
            completed = $StageProjection.completed_actions
            attempts = 1
            retries = 0
            processes = $ProcessCount
        }
        retention_projection = [ordered]@{
            raw_material_retained_bytes = 0
            sanitized_result_only = $true
            cleanup_actions = $CleanupCount
        }
        gate_effect = [ordered]@{
            machine_action_authorized = $false
            python_machine_fallback = $false
            retry_authorized = $false
            U3T_preflight_authorized = $false
            U3K_authorized = $false
            deployment_authorized = $false
            next_gate = if ($Succeeded) {
                'owner_source_implementation_acceptance_required'
            }
            else {
                'blocked'
            }
        }
    }
}

function New-HcamPolicyValidProjection {
    param(
        [int]$ProcessCount = 0,

        [int]$CleanupCount = 0
    )

    $StageProjection = [ordered]@{
        completed_actions = $Script:HcamActionOrder.Count
        failed_action = $null
        failed_stage = $null
    }
    return New-HcamTerminalProjection `
        -ReasonCode 'policy_valid' `
        -Succeeded $true `
        -StageProjection $StageProjection `
        -ProcessCount $ProcessCount `
        -CleanupCount $CleanupCount
}

function New-HcamActionFailureProjection {
    param(
        [Parameter(Mandatory = $true)]
        [string]$Action,

        [int]$ProcessCount = 0,

        [int]$CleanupCount = 0
    )

    if (-not $Script:HcamActionFailureReasons.Contains($Action)) {
        $Action = 'validate_result_contract'
    }
    $ReasonCode = $Script:HcamActionFailureReasons[$Action]
    $Index = [System.Array]::IndexOf($Script:HcamActionOrder, $Action)
    $StageProjection = [ordered]@{
        completed_actions = $Index
        failed_action = $Action
        failed_stage = $ReasonCode
    }
    return New-HcamTerminalProjection `
        -ReasonCode $ReasonCode `
        -Succeeded $false `
        -StageProjection $StageProjection `
        -ProcessCount $ProcessCount `
        -CleanupCount $CleanupCount
}

function Test-HcamActionPlan {
    param(
        [Parameter(Mandatory = $true)]
        [object[]]$ActionPlan
    )

    if ($ActionPlan.Count -ne $Script:HcamActionOrder.Count) {
        return $false
    }
    for ($Index = 0; $Index -lt $Script:HcamActionOrder.Count; $Index += 1) {
        if ($ActionPlan[$Index] -cne $Script:HcamActionOrder[$Index]) {
            return $false
        }
    }
    return $true
}

function Invoke-HcamRuntimeControllerR1 {
    param(
        [Parameter(Mandatory = $true)]
        [System.Collections.IDictionary]$Request
    )

    if (-not (Test-HcamExactFieldSet -Value $Request -Expected $Script:HcamRequestFields)) {
        return New-HcamActionFailureProjection -Action 'validate_request_contract'
    }
    if ($Request.contract_version -cne $Script:HcamContractVersion) {
        return New-HcamActionFailureProjection -Action 'validate_request_contract'
    }
    if ($Request.mode -cnotin $Script:HcamModes) {
        return New-HcamActionFailureProjection -Action 'validate_request_contract'
    }
    if (-not (Test-HcamActionPlan -ActionPlan $Request.action_plan)) {
        return New-HcamActionFailureProjection -Action 'validate_request_contract'
    }

    $Inputs = $Request.input_bindings
    $ProcessCount = if ($Inputs.process_count -is [int]) { $Inputs.process_count } else { 0 }
    $CleanupCount = if ($Inputs.cleanup_count -is [int]) { $Inputs.cleanup_count } else { 0 }

    if (
        $Request.mode -ceq 'Preflight' -or
        $Script:HcamMachineAuthorityEnabled -or
        $Request.authorization_binding.machine_authority -or
        $Request.authorization_binding.automatic_retry
    ) {
        return New-HcamActionFailureProjection `
            -Action 'validate_authorization_binding' `
            -ProcessCount $ProcessCount `
            -CleanupCount $CleanupCount
    }

    foreach ($Action in $Script:HcamActionOrder) {
        if ($Inputs.stage_outcomes.Contains($Action)) {
            $Outcome = $Inputs.stage_outcomes[$Action]
            if ($Outcome -cne 'pass' -and $Outcome -cne $Script:HcamActionFailureReasons[$Action]) {
                return New-HcamActionFailureProjection `
                    -Action 'validate_result_contract' `
                    -ProcessCount $ProcessCount `
                    -CleanupCount $CleanupCount
            }
            if ($Outcome -ceq $Script:HcamActionFailureReasons[$Action]) {
                return New-HcamActionFailureProjection `
                    -Action $Action `
                    -ProcessCount $ProcessCount `
                    -CleanupCount $CleanupCount
            }
        }
    }

    if (-not $Inputs.source_binding_match) {
        return New-HcamActionFailureProjection `
            -Action 'bind_sources' `
            -ProcessCount $ProcessCount `
            -CleanupCount $CleanupCount
    }
    if (-not $Inputs.cross_language_match) {
        return New-HcamActionFailureProjection `
            -Action 'compare_cross_language_projection' `
            -ProcessCount $ProcessCount `
            -CleanupCount $CleanupCount
    }

    return New-HcamPolicyValidProjection `
        -ProcessCount $ProcessCount `
        -CleanupCount $CleanupCount
}
