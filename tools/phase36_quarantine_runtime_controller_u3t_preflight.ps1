# Phase 3.6 U3T H1 generated Policy projection harness R0.
# Source-only implementation. Do not parse, import, dot-source, or execute
# before separate exact owner acceptance and runtime-bound authorization.

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
$PSModuleAutoLoadingPreference = 'None'

$HcamH1AuthorizationDecision = 'D-P3.6-U3T-PREFLIGHT-R0-HARNESS-IMPLEMENTATION-AUTH'
$HcamH1AuthorizationPackage = '26B8A0A6FF1B8DA556BB68D6E1EA13B51FFF4460D5CA2F50F3E64952528E69F2'
$HcamControllerFileName = 'phase36_quarantine_runtime_controller.ps1'
$HcamControllerSha256 = '78EE382E1538E8E1E482598A812B3CF32C2C75C4B4D324F34C368849217290EB'
$HcamControllerMaximumBytes = 65536

$HcamSourceBindingFailureJson = '{"contract_version":"1.0.0","terminal":true,"succeeded":false,"reason_code":"source_binding_failed","stage_projection":{"completed_actions":12,"failed_action":"bind_sources","failed_stage":"source_binding_failed"},"action_counts":{"planned":18,"completed":12,"attempts":1,"retries":0,"processes":0},"retention_projection":{"raw_material_retained_bytes":0,"sanitized_result_only":true,"cleanup_actions":0},"gate_effect":{"machine_action_authorized":false,"python_machine_fallback":false,"retry_authorized":false,"U3T_preflight_authorized":false,"U3K_authorized":false,"deployment_authorized":false,"next_gate":"blocked"}}'
$HcamResultInvalidJson = '{"contract_version":"1.0.0","terminal":true,"succeeded":false,"reason_code":"result_contract_invalid","stage_projection":{"completed_actions":16,"failed_action":"validate_result_contract","failed_stage":"result_contract_invalid"},"action_counts":{"planned":18,"completed":16,"attempts":1,"retries":0,"processes":0},"retention_projection":{"raw_material_retained_bytes":0,"sanitized_result_only":true,"cleanup_actions":0},"gate_effect":{"machine_action_authorized":false,"python_machine_fallback":false,"retry_authorized":false,"U3T_preflight_authorized":false,"U3K_authorized":false,"deployment_authorized":false,"next_gate":"blocked"}}'
$HcamPolicyValidJson = '{"contract_version":"1.0.0","terminal":true,"succeeded":true,"reason_code":"policy_valid","stage_projection":{"completed_actions":18,"failed_action":null,"failed_stage":null},"action_counts":{"planned":18,"completed":18,"attempts":1,"retries":0,"processes":0},"retention_projection":{"raw_material_retained_bytes":0,"sanitized_result_only":true,"cleanup_actions":0},"gate_effect":{"machine_action_authorized":false,"python_machine_fallback":false,"retry_authorized":false,"U3T_preflight_authorized":false,"U3K_authorized":false,"deployment_authorized":false,"next_gate":"owner_H1_source_implementation_acceptance_required"}}'

try {
    if (
        $HcamH1AuthorizationDecision -cne
            'D-P3.6-U3T-PREFLIGHT-R0-HARNESS-IMPLEMENTATION-AUTH' -or
        $HcamH1AuthorizationPackage -cne
            '26B8A0A6FF1B8DA556BB68D6E1EA13B51FFF4460D5CA2F50F3E64952528E69F2'
    ) {
        [Console]::Out.Write($HcamSourceBindingFailureJson)
        exit 70
    }

    $HcamControllerPath = [IO.Path]::GetFullPath(
        [IO.Path]::Combine($PSScriptRoot, $HcamControllerFileName)
    )
    $HcamExpectedControllerPath = [IO.Path]::GetFullPath(
        [IO.Path]::Combine($PSScriptRoot, 'phase36_quarantine_runtime_controller.ps1')
    )
    if ($HcamControllerPath -cne $HcamExpectedControllerPath) {
        [Console]::Out.Write($HcamSourceBindingFailureJson)
        exit 70
    }

    $HcamControllerInfo = [IO.FileInfo]::new($HcamControllerPath)
    if (
        -not $HcamControllerInfo.Exists -or
        $HcamControllerInfo.Length -le 0 -or
        $HcamControllerInfo.Length -gt $HcamControllerMaximumBytes
    ) {
        [Console]::Out.Write($HcamSourceBindingFailureJson)
        exit 70
    }

    $HcamControllerStream = $null
    $HcamSha256 = $null
    try {
        $HcamControllerStream = [IO.File]::Open(
            $HcamControllerPath,
            [IO.FileMode]::Open,
            [IO.FileAccess]::Read,
            [IO.FileShare]::Read
        )
        $HcamSha256 = [Security.Cryptography.SHA256]::Create()
        $HcamControllerDigest = [Convert]::ToHexString(
            $HcamSha256.ComputeHash($HcamControllerStream)
        )
    }
    finally {
        if ($null -ne $HcamSha256) {
            $HcamSha256.Dispose()
        }
        if ($null -ne $HcamControllerStream) {
            $HcamControllerStream.Dispose()
        }
    }

    if ($HcamControllerDigest -cne $HcamControllerSha256) {
        [Console]::Out.Write($HcamSourceBindingFailureJson)
        exit 70
    }

    . $HcamControllerPath

    $HcamRequest = [ordered]@{
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
        action_plan = @(
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

    $HcamResult = Invoke-HcamRuntimeController -Request $HcamRequest
    $HcamResultValid = (
        $HcamResult -is [System.Collections.IDictionary] -and
        $HcamResult.contract_version -ceq '1.0.0' -and
        $HcamResult.terminal -eq $true -and
        $HcamResult.succeeded -eq $true -and
        $HcamResult.reason_code -ceq 'policy_valid' -and
        $HcamResult.stage_projection.completed_actions -eq 18 -and
        $null -eq $HcamResult.stage_projection.failed_action -and
        $null -eq $HcamResult.stage_projection.failed_stage -and
        $HcamResult.action_counts.planned -eq 18 -and
        $HcamResult.action_counts.completed -eq 18 -and
        $HcamResult.action_counts.attempts -eq 1 -and
        $HcamResult.action_counts.retries -eq 0 -and
        $HcamResult.action_counts.processes -eq 0 -and
        $HcamResult.retention_projection.raw_material_retained_bytes -eq 0 -and
        $HcamResult.retention_projection.sanitized_result_only -eq $true -and
        $HcamResult.retention_projection.cleanup_actions -eq 0 -and
        $HcamResult.gate_effect.machine_action_authorized -eq $false -and
        $HcamResult.gate_effect.python_machine_fallback -eq $false -and
        $HcamResult.gate_effect.retry_authorized -eq $false -and
        $HcamResult.gate_effect.U3T_preflight_authorized -eq $false -and
        $HcamResult.gate_effect.U3K_authorized -eq $false -and
        $HcamResult.gate_effect.deployment_authorized -eq $false
    )
    if (-not $HcamResultValid) {
        [Console]::Out.Write($HcamResultInvalidJson)
        exit 71
    }

    [Console]::Out.Write($HcamPolicyValidJson)
    exit 0
}
catch {
    [Console]::Out.Write($HcamSourceBindingFailureJson)
    exit 70
}
