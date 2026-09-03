Set-StrictMode -Version Latest

$script:P36ActionIds = @(
    'U3K-A01-UTC-CLOCK-START',
    'U3K-A02-PACKAGE-RUNNER-AUTHORITY-VERIFY',
    'U3K-A03-AUTHORIZATION-RECORD',
    'U3K-A04-F-DRIVE-INFO',
    'U3K-A05-CANONICAL-PATH-AND-ABSENCE',
    'U3K-A06-PROTECTED-DACL-CONSTRUCT',
    'U3K-A07-SECURITY-AT-CREATE-ROOT',
    'U3K-A08-NORMALIZED-DACL-VERIFY',
    'U3K-A09-ATOMIC-CAPABILITY-PROBE',
    'U3K-A10-NORMALIZE-HASH-WRITE'
)

$script:P36OutputPaths = @(
    'contracts/phase-3/p3-6-quarantine-storage-r2-authorization.json',
    'contracts/phase-3/p3-6-quarantine-storage-r2-result.json',
    'contracts/phase-3/p3-6-quarantine-storage-r2-evidence.json'
)

$script:P36ReasonCodes = [System.Collections.Generic.HashSet[string]]::new(
    [System.StringComparer]::Ordinal
)
@(
    'ok',
    'clock_unavailable',
    'clock_read_count_invalid',
    'authority_binding_invalid',
    'authorization_window_invalid',
    'attempt_already_consumed',
    'action_plan_invalid',
    'target_or_limit_invalid',
    'source_or_runtime_binding_invalid',
    'authorization_record_invalid',
    'authorization_record_exists',
    'authorization_record_write_failed',
    'drive_not_ready',
    'drive_type_not_allowed',
    'filesystem_not_allowed',
    'capacity_below_minimum',
    'drive_property_unavailable',
    'candidate_path_invalid',
    'candidate_exists',
    'candidate_or_parent_reparse',
    'candidate_attribute_unavailable',
    'identity_unavailable',
    'identity_collision',
    'security_descriptor_invalid',
    'security_descriptor_construction_failed',
    'root_preexisting_or_raced',
    'root_create_failed',
    'root_creation_mechanism_invalid',
    'DACL_policy_failed',
    'probe_path_preexisting',
    'probe_write_failed',
    'probe_flush_failed',
    'probe_hash_mismatch',
    'probe_rename_policy_failed',
    'probe_cleanup_failed',
    'output_schema_invalid',
    'output_too_large',
    'output_write_failed',
    'action_timeout',
    'transaction_timeout',
    'action_out_of_order',
    'unknown_action',
    'terminal_state',
    'adapter_result_invalid',
    'sanitized_runner_failure',
    'manual_review_required'
) | ForEach-Object { [void] $script:P36ReasonCodes.Add($_) }

function Test-P36ExactStringSequence {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory = $true)]
        [object[]] $Actual,

        [Parameter(Mandatory = $true)]
        [string[]] $Expected
    )

    if ($Actual.Count -ne $Expected.Count) {
        return $false
    }

    $seen = [System.Collections.Generic.HashSet[string]]::new(
        [System.StringComparer]::Ordinal
    )
    for ($index = 0; $index -lt $Expected.Count; $index++) {
        $candidate = [string] $Actual[$index]
        if (-not $seen.Add($candidate)) {
            return $false
        }
        if ($candidate -cne $Expected[$index]) {
            return $false
        }
    }
    return $true
}

function Test-P36TrueProperties {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory = $true)]
        [hashtable] $Value,

        [Parameter(Mandatory = $true)]
        [string[]] $Names
    )

    foreach ($name in $Names) {
        if (-not $Value.ContainsKey($name) -or $Value[$name] -isnot [bool] -or -not $Value[$name]) {
            return $false
        }
    }
    return $true
}

function New-P36HandlerDecision {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory = $true)]
        [bool] $Succeeded,

        [Parameter(Mandatory = $true)]
        [string] $ReasonCode,

        [bool] $RootCreatedByAttempt = $false,
        [bool] $ProbePartialCreatedByAttempt = $false,
        [bool] $ProbeVerifiedCreatedByAttempt = $false,
        [bool] $CleanupRequired = $false,
        [bool] $ManualReviewRequired = $false
    )

    if (-not $script:P36ReasonCodes.Contains($ReasonCode)) {
        throw 'P36_UNALLOWLISTED_REASON_CODE'
    }

    [pscustomobject][ordered]@{
        succeeded                         = $Succeeded
        reason_code                      = $ReasonCode
        root_created_by_attempt           = $RootCreatedByAttempt
        probe_partial_created_by_attempt  = $ProbePartialCreatedByAttempt
        probe_verified_created_by_attempt = $ProbeVerifiedCreatedByAttempt
        cleanup_required                  = $CleanupRequired
        manual_review_required            = $ManualReviewRequired
    }
}

function Test-P36StorageEnvelope {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory = $true)]
        [hashtable] $Request
    )

    $requiredKeys = @(
        'owner_statement_exact_match',
        'authorization_window_current',
        'attempt_unused',
        'execution_package_binding_exact',
        'source_bindings_exact',
        'runtime_binding_exact',
        'logical_node_id',
        'candidate_volume',
        'candidate_root',
        'action_ids',
        'output_paths',
        'probe_bytes',
        'per_action_timeout_seconds',
        'total_timeout_seconds'
    )
    foreach ($key in $requiredKeys) {
        if (-not $Request.ContainsKey($key)) {
            return New-P36HandlerDecision -Succeeded $false -ReasonCode 'authority_binding_invalid'
        }
    }

    if (-not (Test-P36TrueProperties -Value $Request -Names @(
        'owner_statement_exact_match',
        'authorization_window_current',
        'attempt_unused',
        'execution_package_binding_exact',
        'source_bindings_exact',
        'runtime_binding_exact'
    ))) {
        return New-P36HandlerDecision -Succeeded $false -ReasonCode 'authority_binding_invalid'
    }
    if (-not (Test-P36ExactStringSequence -Actual @($Request.action_ids) -Expected $script:P36ActionIds)) {
        return New-P36HandlerDecision -Succeeded $false -ReasonCode 'action_plan_invalid'
    }
    if (-not (Test-P36ExactStringSequence -Actual @($Request.output_paths) -Expected $script:P36OutputPaths)) {
        return New-P36HandlerDecision -Succeeded $false -ReasonCode 'target_or_limit_invalid'
    }
    if (
        [string] $Request.logical_node_id -cne 'LAB-LAPTOP-01' -or
        [string] $Request.candidate_volume -cne 'F:' -or
        [string] $Request.candidate_root -cne 'F:\HCAM-Quarantine' -or
        [int] $Request.probe_bytes -ne 4096 -or
        [int] $Request.per_action_timeout_seconds -ne 30 -or
        [int] $Request.total_timeout_seconds -ne 120
    ) {
        return New-P36HandlerDecision -Succeeded $false -ReasonCode 'target_or_limit_invalid'
    }

    return New-P36HandlerDecision -Succeeded $true -ReasonCode 'ok'
}

function New-P36MachineHandlerState {
    [CmdletBinding()]
    param()

    [pscustomobject][ordered]@{
        next_action_index                 = 0
        terminal                          = $false
        succeeded                         = $false
        reason_code                       = 'ok'
        start_monotonic_seconds           = $null
        last_monotonic_seconds            = $null
        authorization_record_written      = $false
        target_access_started              = $false
        root_created_by_attempt           = $false
        probe_partial_created_by_attempt  = $false
        probe_verified_created_by_attempt = $false
        cleanup_required                  = $false
        manual_review_required            = $false
        automatic_retry_authorized         = $false
        execution_authorized               = $false
        profile_activation_authorized      = $false
        deployment_authorized              = $false
        remote_git_authorized              = $false
    }
}

function Resolve-P36A01 {
    param([hashtable] $AdapterResult)

    if (-not $AdapterResult.ContainsKey('ok') -or -not [bool] $AdapterResult.ok) {
        return New-P36HandlerDecision -Succeeded $false -ReasonCode 'clock_unavailable'
    }
    if (
        -not $AdapterResult.ContainsKey('read_count') -or
        [int] $AdapterResult.read_count -ne 1 -or
        -not $AdapterResult.ContainsKey('monotonic_seconds')
    ) {
        return New-P36HandlerDecision -Succeeded $false -ReasonCode 'clock_read_count_invalid'
    }
    return New-P36HandlerDecision -Succeeded $true -ReasonCode 'ok'
}

function Resolve-P36A02 {
    param([hashtable] $AdapterResult)

    if (-not (Test-P36TrueProperties -Value $AdapterResult -Names @(
        'ok',
        'owner_statement_exact_match',
        'authorization_window_current',
        'attempt_unused',
        'execution_package_hashes_match',
        'source_hashes_match',
        'runtime_binding_matches',
        'target_action_limits_outputs_match'
    ))) {
        if ($AdapterResult.ContainsKey('attempt_unused') -and -not [bool] $AdapterResult.attempt_unused) {
            return New-P36HandlerDecision -Succeeded $false -ReasonCode 'attempt_already_consumed'
        }
        if ($AdapterResult.ContainsKey('authorization_window_current') -and -not [bool] $AdapterResult.authorization_window_current) {
            return New-P36HandlerDecision -Succeeded $false -ReasonCode 'authorization_window_invalid'
        }
        if (
            ($AdapterResult.ContainsKey('source_hashes_match') -and -not [bool] $AdapterResult.source_hashes_match) -or
            ($AdapterResult.ContainsKey('runtime_binding_matches') -and -not [bool] $AdapterResult.runtime_binding_matches)
        ) {
            return New-P36HandlerDecision -Succeeded $false -ReasonCode 'source_or_runtime_binding_invalid'
        }
        return New-P36HandlerDecision -Succeeded $false -ReasonCode 'authority_binding_invalid'
    }
    return New-P36HandlerDecision -Succeeded $true -ReasonCode 'ok'
}

function Resolve-P36A03 {
    param([hashtable] $AdapterResult)

    if (-not (Test-P36TrueProperties -Value $AdapterResult -Names @(
        'ok',
        'schema_valid',
        'size_valid',
        'destination_absent',
        'partial_absent',
        'flushed_to_disk',
        'nonreplacement_rename'
    ))) {
        if (
            ($AdapterResult.ContainsKey('destination_absent') -and -not [bool] $AdapterResult.destination_absent) -or
            ($AdapterResult.ContainsKey('partial_absent') -and -not [bool] $AdapterResult.partial_absent)
        ) {
            return New-P36HandlerDecision -Succeeded $false -ReasonCode 'authorization_record_exists'
        }
        if (
            ($AdapterResult.ContainsKey('schema_valid') -and -not [bool] $AdapterResult.schema_valid) -or
            ($AdapterResult.ContainsKey('size_valid') -and -not [bool] $AdapterResult.size_valid)
        ) {
            return New-P36HandlerDecision -Succeeded $false -ReasonCode 'authorization_record_invalid'
        }
        return New-P36HandlerDecision -Succeeded $false -ReasonCode 'authorization_record_write_failed'
    }
    return New-P36HandlerDecision -Succeeded $true -ReasonCode 'ok'
}

function Resolve-P36A04 {
    param([hashtable] $AdapterResult)

    if (-not $AdapterResult.ContainsKey('properties_available') -or -not [bool] $AdapterResult.properties_available) {
        return New-P36HandlerDecision -Succeeded $false -ReasonCode 'drive_property_unavailable'
    }
    if (-not [bool] $AdapterResult.drive_ready) {
        return New-P36HandlerDecision -Succeeded $false -ReasonCode 'drive_not_ready'
    }
    if ([string] $AdapterResult.drive_type -cne 'Fixed') {
        return New-P36HandlerDecision -Succeeded $false -ReasonCode 'drive_type_not_allowed'
    }
    if ([string] $AdapterResult.filesystem -cnotin @('NTFS', 'ReFS')) {
        return New-P36HandlerDecision -Succeeded $false -ReasonCode 'filesystem_not_allowed'
    }
    if (
        [Int64] $AdapterResult.available_free_bytes -lt 5368709120 -or
        [double] $AdapterResult.available_free_percent -lt 15.0
    ) {
        return New-P36HandlerDecision -Succeeded $false -ReasonCode 'capacity_below_minimum'
    }
    return New-P36HandlerDecision -Succeeded $true -ReasonCode 'ok'
}

function Resolve-P36A05 {
    param([hashtable] $AdapterResult)

    if (-not $AdapterResult.ContainsKey('attributes_available') -or -not [bool] $AdapterResult.attributes_available) {
        return New-P36HandlerDecision -Succeeded $false -ReasonCode 'candidate_attribute_unavailable'
    }
    if (-not [bool] $AdapterResult.exact_canonical_path) {
        return New-P36HandlerDecision -Succeeded $false -ReasonCode 'candidate_path_invalid'
    }
    if ([bool] $AdapterResult.parent_reparse -or [bool] $AdapterResult.candidate_reparse) {
        return New-P36HandlerDecision -Succeeded $false -ReasonCode 'candidate_or_parent_reparse'
    }
    if (-not [bool] $AdapterResult.candidate_absent) {
        return New-P36HandlerDecision -Succeeded $false -ReasonCode 'candidate_exists'
    }
    return New-P36HandlerDecision -Succeeded $true -ReasonCode 'ok'
}

function Resolve-P36A06 {
    param([hashtable] $AdapterResult)

    if (-not $AdapterResult.ContainsKey('identity_available') -or -not [bool] $AdapterResult.identity_available) {
        return New-P36HandlerDecision -Succeeded $false -ReasonCode 'identity_unavailable'
    }
    if ($AdapterResult.ContainsKey('identity_collision') -and [bool] $AdapterResult.identity_collision) {
        return New-P36HandlerDecision -Succeeded $false -ReasonCode 'identity_collision'
    }
    if (-not (Test-P36TrueProperties -Value $AdapterResult -Names @(
        'ok',
        'descriptor_bounded',
        'inheritance_protected',
        'exact_three_allow_tuples',
        'identity_not_persisted',
        'account_translation_absent'
    ))) {
        return New-P36HandlerDecision -Succeeded $false -ReasonCode 'security_descriptor_invalid'
    }
    return New-P36HandlerDecision -Succeeded $true -ReasonCode 'ok'
}

function Resolve-P36A07 {
    param([hashtable] $AdapterResult)

    $created = (
        $AdapterResult.ContainsKey('native_success') -and
        [bool] $AdapterResult.native_success
    )
    if (
        $AdapterResult.ContainsKey('error_already_exists') -and
        [bool] $AdapterResult.error_already_exists
    ) {
        return New-P36HandlerDecision -Succeeded $false -ReasonCode 'root_preexisting_or_raced'
    }
    if (
        -not $AdapterResult.ContainsKey('required_API_used') -or
        -not [bool] $AdapterResult.required_API_used -or
        -not $AdapterResult.ContainsKey('security_attributes_nonnull') -or
        -not [bool] $AdapterResult.security_attributes_nonnull -or
        ($AdapterResult.ContainsKey('fallback_used') -and [bool] $AdapterResult.fallback_used)
    ) {
        return New-P36HandlerDecision -Succeeded $false -ReasonCode 'root_creation_mechanism_invalid'
    }
    if (-not $created) {
        return New-P36HandlerDecision -Succeeded $false -ReasonCode 'root_create_failed'
    }
    return New-P36HandlerDecision -Succeeded $true -ReasonCode 'ok' -RootCreatedByAttempt $true
}

function Resolve-P36A08 {
    param([hashtable] $AdapterResult, [bool] $RootCreatedByAttempt)

    $required = @(
        'ok',
        'access_rules_protected',
        'exact_rule_count_pass',
        'current_process_principal_pass',
        'current_process_Modify_Synchronize_rights_pass',
        'current_process_excessive_or_unknown_rights_absent',
        'LocalSystem_tuple_pass',
        'Administrators_tuple_pass',
        'inheritance_flags_pass',
        'propagation_flags_pass',
        'access_types_pass',
        'inherited_rule_absent',
        'deny_rule_absent',
        'unauthorized_principal_absent',
        'overall_DACL_pass'
    )
    if (-not (Test-P36TrueProperties -Value $AdapterResult -Names $required)) {
        return New-P36HandlerDecision `
            -Succeeded $false `
            -ReasonCode 'DACL_policy_failed' `
            -RootCreatedByAttempt $RootCreatedByAttempt `
            -CleanupRequired $RootCreatedByAttempt
    }
    return New-P36HandlerDecision -Succeeded $true -ReasonCode 'ok' -RootCreatedByAttempt $RootCreatedByAttempt
}

function Resolve-P36A09 {
    param([hashtable] $AdapterResult, [bool] $RootCreatedByAttempt)

    $partialCreated = $AdapterResult.ContainsKey('partial_created_by_attempt') -and [bool] $AdapterResult.partial_created_by_attempt
    $verifiedCreated = $AdapterResult.ContainsKey('verified_created_by_attempt') -and [bool] $AdapterResult.verified_created_by_attempt
    if (
        ($AdapterResult.ContainsKey('probe_paths_absent') -and -not [bool] $AdapterResult.probe_paths_absent)
    ) {
        return New-P36HandlerDecision -Succeeded $false -ReasonCode 'probe_path_preexisting' -RootCreatedByAttempt $RootCreatedByAttempt -CleanupRequired $RootCreatedByAttempt
    }
    if ($AdapterResult.ContainsKey('cleanup_complete') -and -not [bool] $AdapterResult.cleanup_complete) {
        return New-P36HandlerDecision `
            -Succeeded $false `
            -ReasonCode 'probe_cleanup_failed' `
            -RootCreatedByAttempt $RootCreatedByAttempt `
            -ProbePartialCreatedByAttempt $partialCreated `
            -ProbeVerifiedCreatedByAttempt $verifiedCreated `
            -CleanupRequired $true `
            -ManualReviewRequired $true
    }
    if (-not (Test-P36TrueProperties -Value $AdapterResult -Names @(
        'ok',
        'probe_paths_absent',
        'exact_byte_count',
        'write_through',
        'flush_to_disk',
        'first_hash_match',
        'rename_write_through_only',
        'second_hash_match',
        'cleanup_complete',
        'zero_retention'
    ))) {
        return New-P36HandlerDecision `
            -Succeeded $false `
            -ReasonCode 'probe_write_failed' `
            -RootCreatedByAttempt $RootCreatedByAttempt `
            -ProbePartialCreatedByAttempt $partialCreated `
            -ProbeVerifiedCreatedByAttempt $verifiedCreated `
            -CleanupRequired $true
    }
    return New-P36HandlerDecision -Succeeded $true -ReasonCode 'ok' -RootCreatedByAttempt $RootCreatedByAttempt
}

function Resolve-P36A10 {
    param([hashtable] $AdapterResult, [bool] $RootCreatedByAttempt)

    if (
        ($AdapterResult.ContainsKey('size_valid') -and -not [bool] $AdapterResult.size_valid)
    ) {
        return New-P36HandlerDecision -Succeeded $false -ReasonCode 'output_too_large' -RootCreatedByAttempt $RootCreatedByAttempt
    }
    if (
        ($AdapterResult.ContainsKey('schema_valid') -and -not [bool] $AdapterResult.schema_valid) -or
        ($AdapterResult.ContainsKey('canonical_JSON') -and -not [bool] $AdapterResult.canonical_JSON)
    ) {
        return New-P36HandlerDecision -Succeeded $false -ReasonCode 'output_schema_invalid' -RootCreatedByAttempt $RootCreatedByAttempt
    }
    if (-not (Test-P36TrueProperties -Value $AdapterResult -Names @(
        'ok',
        'schema_valid',
        'size_valid',
        'canonical_JSON',
        'hashes_computed',
        'flushed_to_disk',
        'nonreplacement_rename'
    ))) {
        return New-P36HandlerDecision -Succeeded $false -ReasonCode 'output_write_failed' -RootCreatedByAttempt $RootCreatedByAttempt
    }
    return New-P36HandlerDecision -Succeeded $true -ReasonCode 'ok' -RootCreatedByAttempt $RootCreatedByAttempt
}

function Invoke-P36HandlerTransition {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory = $true)]
        [pscustomobject] $State,

        [Parameter(Mandatory = $true)]
        [string] $ActionId,

        [Parameter(Mandatory = $true)]
        [hashtable] $AdapterResult,

        [Parameter(Mandatory = $true)]
        [double] $MonotonicSeconds
    )

    if ([bool] $State.terminal) {
        return New-P36HandlerDecision -Succeeded $false -ReasonCode 'terminal_state'
    }
    if ([int] $State.next_action_index -ge $script:P36ActionIds.Count) {
        $State.terminal = $true
        $State.succeeded = $false
        $State.reason_code = 'unknown_action'
        return New-P36HandlerDecision -Succeeded $false -ReasonCode 'unknown_action'
    }
    $expectedAction = $script:P36ActionIds[[int] $State.next_action_index]
    if ($ActionId -cne $expectedAction) {
        $State.terminal = $true
        $State.succeeded = $false
        $State.reason_code = 'action_out_of_order'
        return New-P36HandlerDecision -Succeeded $false -ReasonCode 'action_out_of_order'
    }

    $decision = $null
    if ($null -ne $State.start_monotonic_seconds) {
        $elapsed = $MonotonicSeconds - [double] $State.start_monotonic_seconds
        $actionElapsed = $MonotonicSeconds - [double] $State.last_monotonic_seconds
        if ($elapsed -gt 120.0) {
            $decision = New-P36HandlerDecision -Succeeded $false -ReasonCode 'transaction_timeout'
        } elseif ($actionElapsed -gt 30.0) {
            $decision = New-P36HandlerDecision -Succeeded $false -ReasonCode 'action_timeout'
        }
    }

    if ($null -eq $decision) {
        $decision = switch -CaseSensitive ($ActionId) {
            'U3K-A01-UTC-CLOCK-START' { Resolve-P36A01 -AdapterResult $AdapterResult; break }
            'U3K-A02-PACKAGE-RUNNER-AUTHORITY-VERIFY' { Resolve-P36A02 -AdapterResult $AdapterResult; break }
            'U3K-A03-AUTHORIZATION-RECORD' { Resolve-P36A03 -AdapterResult $AdapterResult; break }
            'U3K-A04-F-DRIVE-INFO' { Resolve-P36A04 -AdapterResult $AdapterResult; break }
            'U3K-A05-CANONICAL-PATH-AND-ABSENCE' { Resolve-P36A05 -AdapterResult $AdapterResult; break }
            'U3K-A06-PROTECTED-DACL-CONSTRUCT' { Resolve-P36A06 -AdapterResult $AdapterResult; break }
            'U3K-A07-SECURITY-AT-CREATE-ROOT' { Resolve-P36A07 -AdapterResult $AdapterResult; break }
            'U3K-A08-NORMALIZED-DACL-VERIFY' { Resolve-P36A08 -AdapterResult $AdapterResult -RootCreatedByAttempt ([bool] $State.root_created_by_attempt); break }
            'U3K-A09-ATOMIC-CAPABILITY-PROBE' { Resolve-P36A09 -AdapterResult $AdapterResult -RootCreatedByAttempt ([bool] $State.root_created_by_attempt); break }
            'U3K-A10-NORMALIZE-HASH-WRITE' { Resolve-P36A10 -AdapterResult $AdapterResult -RootCreatedByAttempt ([bool] $State.root_created_by_attempt); break }
            default { New-P36HandlerDecision -Succeeded $false -ReasonCode 'unknown_action'; break }
        }
    }

    if ($ActionId -ceq 'U3K-A01-UTC-CLOCK-START' -and [bool] $decision.succeeded) {
        $State.start_monotonic_seconds = [double] $AdapterResult.monotonic_seconds
    }
    if ($ActionId -ceq 'U3K-A03-AUTHORIZATION-RECORD' -and [bool] $decision.succeeded) {
        $State.authorization_record_written = $true
    }
    if ($ActionId -ceq 'U3K-A04-F-DRIVE-INFO') {
        if (-not [bool] $State.authorization_record_written) {
            $decision = New-P36HandlerDecision -Succeeded $false -ReasonCode 'action_out_of_order'
        } else {
            $State.target_access_started = $true
        }
    }

    $State.last_monotonic_seconds = $MonotonicSeconds
    $State.root_created_by_attempt = [bool] $decision.root_created_by_attempt
    $State.probe_partial_created_by_attempt = [bool] $decision.probe_partial_created_by_attempt
    $State.probe_verified_created_by_attempt = [bool] $decision.probe_verified_created_by_attempt
    $State.cleanup_required = [bool] $decision.cleanup_required
    $State.manual_review_required = [bool] $decision.manual_review_required
    $State.reason_code = [string] $decision.reason_code

    if (-not [bool] $decision.succeeded) {
        $State.terminal = $true
        $State.succeeded = $false
        return $decision
    }

    $State.next_action_index = [int] $State.next_action_index + 1
    if ([int] $State.next_action_index -eq $script:P36ActionIds.Count) {
        $State.terminal = $true
        $State.succeeded = $true
    }
    return $decision
}

function Get-P36TerminalProjection {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory = $true)]
        [pscustomobject] $State
    )

    [ordered]@{
        terminal                          = [bool] $State.terminal
        succeeded                         = [bool] $State.succeeded
        reason_code                       = [string] $State.reason_code
        authorization_record_written      = [bool] $State.authorization_record_written
        target_access_started              = [bool] $State.target_access_started
        root_created_by_attempt           = [bool] $State.root_created_by_attempt
        probe_partial_created_by_attempt  = [bool] $State.probe_partial_created_by_attempt
        probe_verified_created_by_attempt = [bool] $State.probe_verified_created_by_attempt
        cleanup_required                  = [bool] $State.cleanup_required
        manual_review_required            = [bool] $State.manual_review_required
        automatic_retry_authorized         = $false
        execution_authorized               = $false
        profile_activation_authorized      = $false
        deployment_authorized              = $false
        remote_git_authorized              = $false
    }
}

Export-ModuleMember -Function @(
    'Test-P36StorageEnvelope',
    'New-P36MachineHandlerState',
    'Invoke-P36HandlerTransition',
    'Get-P36TerminalProjection'
)
