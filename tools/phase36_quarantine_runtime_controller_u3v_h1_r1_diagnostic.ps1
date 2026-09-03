# Phase 3.6 U3V H1 R1 sanitized diagnostic harness.
# Source-only implementation. Do not parse, import, dot-source, or execute
# before separate exact owner acceptance and runtime-bound authorization.

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
$PSModuleAutoLoadingPreference = 'None'

$Script:HcamU3VContractVersion = '1.0.0'
$Script:HcamU3VAuthorizationDecision = 'D-P3.6-U3V-H1-R1-DIAGNOSTIC-IMPLEMENTATION-AUTH'
$Script:HcamU3VAuthorizationPackage = '745C50AEB4DB61147C541F897F5E78987F64D9C3B137559F7CA811C0A6A5FD33'
$Script:HcamU3VControllerFileName = 'phase36_quarantine_runtime_controller.ps1'
$Script:HcamU3VControllerSha256 = '78EE382E1538E8E1E482598A812B3CF32C2C75C4B4D324F34C368849217290EB'
$Script:HcamU3VControllerMaximumBytes = 65536
$Script:HcamU3VMaximumOutputBytes = 4096

# HCAM_U3V_CANONICAL_PROJECTION_BEGIN
# {"contract_version":"1.0.0","diagnostic_group_order":["top_level_shape","contract_identity","terminal_state","reason_family","stage_projection","action_counts","retention_projection","gate_effect"],"allowlisted_terminal_reason_codes":["source_binding_failed","controller_top_level_shape_invalid","controller_contract_identity_invalid","controller_terminal_state_invalid","controller_reason_family_invalid","controller_stage_projection_invalid","controller_action_counts_invalid","controller_retention_projection_invalid","controller_gate_effect_invalid","controller_projection_valid","diagnostic_internal_contract_invalid"],"allowlisted_controller_reason_families":["policy_valid","sanitized_failure","unknown_or_unavailable"],"maximum_output_bytes":4096,"raw_controller_material_retained_bytes":0,"machine_action_authorized":false,"python_machine_fallback":false,"retry_authorized":false,"U3K_authorized":false,"deployment_authorized":false}
# HCAM_U3V_CANONICAL_PROJECTION_END

$Script:HcamU3VResultFields = @(
    'contract_version'
    'terminal'
    'succeeded'
    'reason_code'
    'stage_projection'
    'action_counts'
    'retention_projection'
    'gate_effect'
)

$Script:HcamU3VStageFields = @(
    'completed_actions'
    'failed_action'
    'failed_stage'
)

$Script:HcamU3VActionCountFields = @(
    'planned'
    'completed'
    'attempts'
    'retries'
    'processes'
)

$Script:HcamU3VRetentionFields = @(
    'raw_material_retained_bytes'
    'sanitized_result_only'
    'cleanup_actions'
)

$Script:HcamU3VGateFields = @(
    'machine_action_authorized'
    'python_machine_fallback'
    'retry_authorized'
    'U3T_preflight_authorized'
    'U3K_authorized'
    'deployment_authorized'
    'next_gate'
)

$Script:HcamU3VActionOrder = @(
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

$Script:HcamU3VFailureReasonByAction = [ordered]@{
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

$Script:HcamU3VDiagnosticReasons = @(
    'source_binding_failed'
    'controller_top_level_shape_invalid'
    'controller_contract_identity_invalid'
    'controller_terminal_state_invalid'
    'controller_reason_family_invalid'
    'controller_stage_projection_invalid'
    'controller_action_counts_invalid'
    'controller_retention_projection_invalid'
    'controller_gate_effect_invalid'
    'controller_projection_valid'
    'diagnostic_internal_contract_invalid'
)

function Test-HcamU3VExactFieldSet {
    param(
        [AllowNull()]
        [object]$Value,

        [Parameter(Mandatory = $true)]
        [string[]]$Expected
    )

    if ($Value -isnot [System.Collections.IDictionary]) {
        return $false
    }
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

function Test-HcamU3VInteger {
    param(
        [AllowNull()]
        [object]$Value
    )

    return $Value -is [int]
}

function Get-HcamU3VControllerReasonFamily {
    param(
        [AllowNull()]
        [object]$Candidate
    )

    if ($Candidate -isnot [System.Collections.IDictionary]) {
        return 'unknown_or_unavailable'
    }
    if (-not $Candidate.Contains('reason_code')) {
        return 'unknown_or_unavailable'
    }
    if ($Candidate.reason_code -ceq 'policy_valid') {
        return 'policy_valid'
    }
    if ($Candidate.reason_code -cin $Script:HcamU3VFailureReasonByAction.Values) {
        return 'sanitized_failure'
    }
    return 'unknown_or_unavailable'
}

function Get-HcamU3VDiagnosticReason {
    param(
        [AllowNull()]
        [object]$Candidate
    )

    if (-not (Test-HcamU3VExactFieldSet -Value $Candidate -Expected $Script:HcamU3VResultFields)) {
        return 'controller_top_level_shape_invalid'
    }
    if ($Candidate.contract_version -cne $Script:HcamU3VContractVersion) {
        return 'controller_contract_identity_invalid'
    }
    if ($Candidate.terminal -isnot [bool] -or $Candidate.terminal -ne $true) {
        return 'controller_terminal_state_invalid'
    }
    if ($Candidate.succeeded -isnot [bool]) {
        return 'controller_terminal_state_invalid'
    }

    $Reason = $Candidate.reason_code
    $KnownFailureReasons = @($Script:HcamU3VFailureReasonByAction.Values)
    if ($Reason -cne 'policy_valid' -and $Reason -cnotin $KnownFailureReasons) {
        return 'controller_reason_family_invalid'
    }
    if ($Candidate.succeeded -ne ($Reason -ceq 'policy_valid')) {
        return 'controller_reason_family_invalid'
    }

    $Stage = $Candidate.stage_projection
    if (-not (Test-HcamU3VExactFieldSet -Value $Stage -Expected $Script:HcamU3VStageFields)) {
        return 'controller_stage_projection_invalid'
    }
    $Completed = $Stage.completed_actions
    if (
        -not (Test-HcamU3VInteger -Value $Completed) -or
        $Completed -lt 0 -or
        $Completed -gt $Script:HcamU3VActionOrder.Count
    ) {
        return 'controller_stage_projection_invalid'
    }
    if ($Reason -ceq 'policy_valid') {
        if (
            $Completed -ne $Script:HcamU3VActionOrder.Count -or
            $null -ne $Stage.failed_action -or
            $null -ne $Stage.failed_stage
        ) {
            return 'controller_stage_projection_invalid'
        }
    }
    else {
        $ExpectedAction = $null
        foreach ($Entry in $Script:HcamU3VFailureReasonByAction.GetEnumerator()) {
            if ($Entry.Value -ceq $Reason) {
                $ExpectedAction = $Entry.Key
                break
            }
        }
        $ExpectedCompleted = [System.Array]::IndexOf(
            $Script:HcamU3VActionOrder,
            $ExpectedAction
        )
        if (
            $Completed -ne $ExpectedCompleted -or
            $Stage.failed_action -cne $ExpectedAction -or
            $Stage.failed_stage -cne $Reason
        ) {
            return 'controller_stage_projection_invalid'
        }
    }

    $Counts = $Candidate.action_counts
    if (-not (Test-HcamU3VExactFieldSet -Value $Counts -Expected $Script:HcamU3VActionCountFields)) {
        return 'controller_action_counts_invalid'
    }
    foreach ($Name in $Script:HcamU3VActionCountFields) {
        if (-not (Test-HcamU3VInteger -Value $Counts[$Name])) {
            return 'controller_action_counts_invalid'
        }
    }
    if (
        $Counts.planned -ne $Script:HcamU3VActionOrder.Count -or
        $Counts.completed -ne $Completed -or
        $Counts.attempts -ne 1 -or
        $Counts.retries -ne 0 -or
        $Counts.processes -ne 0
    ) {
        return 'controller_action_counts_invalid'
    }

    $Retention = $Candidate.retention_projection
    if (-not (Test-HcamU3VExactFieldSet -Value $Retention -Expected $Script:HcamU3VRetentionFields)) {
        return 'controller_retention_projection_invalid'
    }
    if (
        -not (Test-HcamU3VInteger -Value $Retention.raw_material_retained_bytes) -or
        $Retention.raw_material_retained_bytes -ne 0 -or
        $Retention.sanitized_result_only -isnot [bool] -or
        $Retention.sanitized_result_only -ne $true -or
        -not (Test-HcamU3VInteger -Value $Retention.cleanup_actions) -or
        $Retention.cleanup_actions -ne 0
    ) {
        return 'controller_retention_projection_invalid'
    }

    $Gate = $Candidate.gate_effect
    if (-not (Test-HcamU3VExactFieldSet -Value $Gate -Expected $Script:HcamU3VGateFields)) {
        return 'controller_gate_effect_invalid'
    }
    foreach ($Name in $Script:HcamU3VGateFields[0..5]) {
        if ($Gate[$Name] -isnot [bool] -or $Gate[$Name] -ne $false) {
            return 'controller_gate_effect_invalid'
        }
    }
    $ExpectedNextGate = if ($Reason -ceq 'policy_valid') {
        'owner_source_implementation_acceptance_required'
    }
    else {
        'blocked'
    }
    if ($Gate.next_gate -cne $ExpectedNextGate) {
        return 'controller_gate_effect_invalid'
    }
    return 'controller_projection_valid'
}

function New-HcamU3VSanitizedJson {
    param(
        [Parameter(Mandatory = $true)]
        [string]$ReasonCode,

        [Parameter(Mandatory = $true)]
        [string]$ControllerReasonFamily
    )

    if ($ReasonCode -cnotin $Script:HcamU3VDiagnosticReasons) {
        $ReasonCode = 'diagnostic_internal_contract_invalid'
        $ControllerReasonFamily = 'unknown_or_unavailable'
    }
    if ($ControllerReasonFamily -cnotin @('policy_valid', 'sanitized_failure', 'unknown_or_unavailable')) {
        $ReasonCode = 'diagnostic_internal_contract_invalid'
        $ControllerReasonFamily = 'unknown_or_unavailable'
    }
    $Succeeded = $ReasonCode -ceq 'controller_projection_valid'
    $SucceededJson = if ($Succeeded) { 'true' } else { 'false' }
    $NextGate = if ($Succeeded) {
        'owner_source_implementation_acceptance_required'
    }
    else {
        'blocked'
    }
    $Json = '{"contract_version":"1.0.0","terminal":true,"succeeded":' +
        $SucceededJson + ',"reason_code":"' + $ReasonCode +
        '","diagnostic_projection":{"checked_group_count":8,"controller_reason_family":"' +
        $ControllerReasonFamily +
        '"},"retention_projection":{"raw_controller_material_retained_bytes":0,"sanitized_result_only":true},"gate_effect":{"machine_action_authorized":false,"python_machine_fallback":false,"retry_authorized":false,"U3K_authorized":false,"deployment_authorized":false,"next_gate":"' +
        $NextGate + '"}}'
    if ([Text.Encoding]::UTF8.GetByteCount($Json) -gt $Script:HcamU3VMaximumOutputBytes) {
        return '{"contract_version":"1.0.0","terminal":true,"succeeded":false,"reason_code":"diagnostic_internal_contract_invalid","diagnostic_projection":{"checked_group_count":8,"controller_reason_family":"unknown_or_unavailable"},"retention_projection":{"raw_controller_material_retained_bytes":0,"sanitized_result_only":true},"gate_effect":{"machine_action_authorized":false,"python_machine_fallback":false,"retry_authorized":false,"U3K_authorized":false,"deployment_authorized":false,"next_gate":"blocked"}}'
    }
    return $Json
}

function Get-HcamU3VGeneratedPolicyRequest {
    return [ordered]@{
        contract_version = '1.0.0'
        mode = 'Policy'
        authorization_binding = [ordered]@{
            decision_id = 'D-P3.6-U3S-DUAL-CONTROLLER-R0-IMPLEMENTATION-AUTH'
            package_digest_sha256 = '3CBE50F50171907E2ADF65B03CD5012E33B759D8BF5B8270694468DD59CBFFFC'
            attempt_index = 1
            attempt_state = 'unused'
            expires_at_utc = '2099-01-01T00:00:00Z'
            authorization_window_state = 'synthetic_policy_only'
            source_hashes = [ordered]@{
                contract = '3F2A0975F92892A96FBC67B951B226D5AB958AE067F55B697ABA43669B8FB00E'
                vectors = '31335510565E4C74908C674B88951E81B7A7983331C6DE2E91964C1F8B48C20B'
                powershell = '78EE382E1538E8E1E482598A812B3CF32C2C75C4B4D324F34C368849217290EB'
                python = 'C1470C65C6D5DA3EF93161F519BBC01507BBB805C6D433F58C65FDCAFE3FFC4F'
            }
            machine_authority = $false
            automatic_retry = $false
        }
        declared_bounds = [ordered]@{
            per_action_timeout_ms = 30000
            total_timeout_ms = 30000
            max_stdout_bytes = 16384
            max_stderr_bytes = 0
            max_result_bytes = 65536
            max_closure_files = 0
            max_closure_bytes = 0
            max_processes = 1
            max_cleanup_actions = 0
        }
        action_plan = @($Script:HcamU3VActionOrder)
        input_bindings = [ordered]@{
            stage_outcomes = [ordered]@{}
            elapsed_ms = 0
            stdout_bytes = 0
            stderr_bytes = 0
            result_bytes = 0
            closure_file_count = 0
            closure_total_bytes = 0
            retained_raw_bytes = 0
            cleanup_count = 0
            process_count = 0
            source_binding_match = $true
            cross_language_match = $true
        }
    }
}

try {
    if (
        $Script:HcamU3VAuthorizationDecision -cne
            'D-P3.6-U3V-H1-R1-DIAGNOSTIC-IMPLEMENTATION-AUTH' -or
        $Script:HcamU3VAuthorizationPackage -cne
            '745C50AEB4DB61147C541F897F5E78987F64D9C3B137559F7CA811C0A6A5FD33'
    ) {
        [Console]::Out.Write((New-HcamU3VSanitizedJson `
            -ReasonCode 'source_binding_failed' `
            -ControllerReasonFamily 'unknown_or_unavailable'))
        exit 70
    }

    $ControllerPath = [IO.Path]::GetFullPath(
        [IO.Path]::Combine($PSScriptRoot, $Script:HcamU3VControllerFileName)
    )
    $ExpectedControllerPath = [IO.Path]::GetFullPath(
        [IO.Path]::Combine($PSScriptRoot, 'phase36_quarantine_runtime_controller.ps1')
    )
    $ControllerInfo = [IO.FileInfo]::new($ControllerPath)
    if (
        $ControllerPath -cne $ExpectedControllerPath -or
        -not $ControllerInfo.Exists -or
        $ControllerInfo.Length -le 0 -or
        $ControllerInfo.Length -gt $Script:HcamU3VControllerMaximumBytes
    ) {
        [Console]::Out.Write((New-HcamU3VSanitizedJson `
            -ReasonCode 'source_binding_failed' `
            -ControllerReasonFamily 'unknown_or_unavailable'))
        exit 70
    }

    $ControllerStream = $null
    $Sha256 = $null
    try {
        $ControllerStream = [IO.File]::Open(
            $ControllerPath,
            [IO.FileMode]::Open,
            [IO.FileAccess]::Read,
            [IO.FileShare]::Read
        )
        $Sha256 = [Security.Cryptography.SHA256]::Create()
        $ControllerDigest = [Convert]::ToHexString(
            $Sha256.ComputeHash($ControllerStream)
        )
    }
    finally {
        if ($null -ne $Sha256) {
            $Sha256.Dispose()
        }
        if ($null -ne $ControllerStream) {
            $ControllerStream.Dispose()
        }
    }
    if ($ControllerDigest -cne $Script:HcamU3VControllerSha256) {
        [Console]::Out.Write((New-HcamU3VSanitizedJson `
            -ReasonCode 'source_binding_failed' `
            -ControllerReasonFamily 'unknown_or_unavailable'))
        exit 70
    }

    . $ControllerPath
    $Candidate = Invoke-HcamRuntimeController -Request (Get-HcamU3VGeneratedPolicyRequest)
    $Family = Get-HcamU3VControllerReasonFamily -Candidate $Candidate
    $DiagnosticReason = Get-HcamU3VDiagnosticReason -Candidate $Candidate
    $Candidate = $null
    [Console]::Out.Write((New-HcamU3VSanitizedJson `
        -ReasonCode $DiagnosticReason `
        -ControllerReasonFamily $Family))
    exit $(if ($DiagnosticReason -ceq 'controller_projection_valid') { 0 } else { 71 })
}
catch {
    [Console]::Out.Write((New-HcamU3VSanitizedJson `
        -ReasonCode 'diagnostic_internal_contract_invalid' `
        -ControllerReasonFamily 'unknown_or_unavailable'))
    exit 72
}
