#requires -Version 7.0

# Phase 3.6 additive R1 runner: preserve ISO timestamp strings during JSON parsing.

[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)]
    [ValidateSet('Contract', 'Storage')]
    [string] $Mode,

    [Parameter(Mandatory = $true, ParameterSetName = 'Contract')]
    [ValidateLength(2, 65536)]
    [string] $ContractVectorJson,

    [Parameter(Mandatory = $true, ParameterSetName = 'Storage')]
    [ValidateLength(2, 65536)]
    [string] $StorageRequestJson
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

trap {
    [ordered]@{
        contract_id                 = 'P36-QUARANTINE-TRANSACTION-RUNNER-R1-1.1.0'
        terminal                    = $true
        succeeded                   = $false
        reason_code                 = 'sanitized_runner_failure'
        raw_error_persisted         = $false
        automatic_retry_authorized  = $false
        execution_authorized        = $false
        profile_activation_authorized = $false
        deployment_authorized       = $false
        remote_git_authorized       = $false
    } | ConvertTo-Json -Compress -Depth 4
    exit 1
}

$script:ContractId = 'P36-QUARANTINE-TRANSACTION-RUNNER-R1-1.1.0'
$script:MaximumInputBytes = 65536
$script:RepositoryRoot = [System.IO.Path]::GetFullPath(
    [System.IO.Path]::Combine($PSScriptRoot, '..')
)
$script:HandlerModulePath = [System.IO.Path]::Combine(
    $PSScriptRoot,
    'phase36_quarantine_machine_handlers.psm1'
)
$script:WindowsAdapterPath = [System.IO.Path]::Combine(
    $PSScriptRoot,
    'phase36_quarantine_windows_storage_adapter.psm1'
)
$script:ExpectedCandidateVolume = 'F:'
$script:ExpectedCandidateRoot = 'F:\HCAM-Quarantine'
$script:ExpectedOutputPaths = @(
    'contracts/phase-3/p3-6-quarantine-storage-r2-authorization.json',
    'contracts/phase-3/p3-6-quarantine-storage-r2-result.json',
    'contracts/phase-3/p3-6-quarantine-storage-r2-evidence.json'
)
$script:AllowedActionIds = @(
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

function New-ContractResult {
    param(
        [Parameter(Mandatory = $true)]
        [string] $Outcome,

        [bool] $MachineAccessed = $false,
        [bool] $DefaultDeny = $false,
        [bool] $UnauthorizedPrincipalAbsent = $true
    )

    [ordered]@{
        contract_id                    = $script:ContractId
        mode                           = 'Contract'
        outcome                        = $Outcome
        machine_accessed               = $MachineAccessed
        default_deny                   = $DefaultDeny
        unauthorized_principal_absent  = $UnauthorizedPrincipalAbsent
        runner_execution_authorized    = $false
        storage_attempt_authorized     = $false
    }
}

function Test-ExactActionPlan {
    param(
        [Parameter(Mandatory = $true)]
        [object[]] $ActionIds
    )

    if ($ActionIds.Count -ne $script:AllowedActionIds.Count) {
        return $false
    }

    $seen = [System.Collections.Generic.HashSet[string]]::new(
        [System.StringComparer]::Ordinal
    )
    for ($index = 0; $index -lt $script:AllowedActionIds.Count; $index++) {
        $candidate = [string] $ActionIds[$index]
        if (-not $seen.Add($candidate)) {
            return $false
        }
        if ($candidate -cne $script:AllowedActionIds[$index]) {
            return $false
        }
    }

    return $true
}

function Test-ExactOutputPlan {
    param(
        [Parameter(Mandatory = $true)]
        [object[]] $OutputPaths
    )

    if ($OutputPaths.Count -ne $script:ExpectedOutputPaths.Count) {
        return $false
    }
    for ($index = 0; $index -lt $script:ExpectedOutputPaths.Count; $index++) {
        if ([string] $OutputPaths[$index] -cne $script:ExpectedOutputPaths[$index]) {
            return $false
        }
    }
    return $true
}

function Test-ExactCurrentProcessRights {
    param(
        [Parameter(Mandatory = $true)]
        [object[]] $Rights
    )

    $normalized = @($Rights | ForEach-Object { [string] $_ } | Sort-Object -Unique)
    return (
        $normalized.Count -eq 2 -and
        $normalized[0] -ceq 'Modify' -and
        $normalized[1] -ceq 'Synchronize'
    )
}

function Test-P36PreImportReceipt {
    param(
        [Parameter(Mandatory = $true)]
        [hashtable] $Request
    )

    foreach ($name in @(
        'owner_statement',
        'expected_owner_statement',
        'handler_module_sha256',
        'windows_adapter_sha256',
        'execution_package_digest_sha256'
    )) {
        if (-not $Request.ContainsKey($name)) {
            return $false
        }
    }
    if ([string] $Request.owner_statement -cne [string] $Request.expected_owner_statement) {
        return $false
    }
    foreach ($digestName in @(
        'handler_module_sha256',
        'windows_adapter_sha256',
        'execution_package_digest_sha256'
    )) {
        if ([string] $Request[$digestName] -cnotmatch '^[A-F0-9]{64}$') {
            return $false
        }
    }

    $handlerHash = (Get-FileHash `
        -LiteralPath $script:HandlerModulePath `
        -Algorithm SHA256).Hash
    $adapterHash = (Get-FileHash `
        -LiteralPath $script:WindowsAdapterPath `
        -Algorithm SHA256).Hash
    return (
        $handlerHash -ceq [string] $Request.handler_module_sha256 -and
        $adapterHash -ceq [string] $Request.windows_adapter_sha256
    )
}

function Get-ContractOutcome {
    param(
        [Parameter(Mandatory = $true)]
        [pscustomobject] $Vector
    )

    $authorityFields = @(
        'package_digest_match',
        'core_hashes_match',
        'owner_statement_match',
        'authorization_window_valid',
        'attempt_unused',
        'runner_binding_match',
        'runtime_binding_match'
    )
    foreach ($field in $authorityFields) {
        if (-not [bool] $Vector.$field) {
            return New-ContractResult -Outcome 'deny_before_machine_access' -DefaultDeny $true
        }
    }

    if (-not (Test-ExactActionPlan -ActionIds @($Vector.action_ids))) {
        return New-ContractResult -Outcome 'default_deny_before_machine_access' -DefaultDeny $true
    }

    if ([string] $Vector.path_policy -ceq 'prohibited') {
        return New-ContractResult -Outcome 'deny_without_access' -DefaultDeny $true
    }
    if (
        [string] $Vector.path_policy -cne 'exact' -or
        [string] $Vector.candidate_volume -cne $script:ExpectedCandidateVolume -or
        [string] $Vector.candidate_root -cne $script:ExpectedCandidateRoot -or
        [int] $Vector.probe_bytes -ne 4096 -or
        [int] $Vector.per_action_timeout_seconds -ne 30 -or
        [int] $Vector.total_timeout_seconds -ne 120
    ) {
        return New-ContractResult -Outcome 'deny_before_machine_access' -DefaultDeny $true
    }

    if (-not (Test-ExactOutputPlan -OutputPaths @($Vector.output_paths))) {
        return New-ContractResult -Outcome 'default_deny_and_no_additional_write' -DefaultDeny $true
    }
    if ([bool] $Vector.forbidden_output_present) {
        return New-ContractResult -Outcome 'output_schema_reject_and_fail_closed' -DefaultDeny $true
    }
    if (-not [bool] $Vector.candidate_absent) {
        return New-ContractResult -Outcome 'fail_without_ACL_or_content_modification'
    }

    if ([string] $Vector.acl_case -cne 'none') {
        $rightsPass = Test-ExactCurrentProcessRights -Rights @(
            $Vector.current_process_rights
        )
        $unauthorizedPrincipalAbsent = -not [bool] $Vector.unauthorized_principal

        if ([bool] $Vector.unauthorized_principal) {
            return New-ContractResult `
                -Outcome 'rule_count_and_unauthorized_principal_checks_fail' `
                -UnauthorizedPrincipalAbsent $false
        }
        if (
            [bool] $Vector.inherited_rule -or
            [bool] $Vector.deny_rule -or
            -not [bool] $Vector.inheritance_pass -or
            -not [bool] $Vector.propagation_pass -or
            -not [bool] $Vector.access_type_pass
        ) {
            return New-ContractResult -Outcome 'overall_DACL_check_fail'
        }
        if (-not $rightsPass -and [string] $Vector.acl_case -ceq 'tuple_independence') {
            return New-ContractResult `
                -Outcome 'rights_fail_and_unauthorized_principal_absence_remains_true' `
                -UnauthorizedPrincipalAbsent $unauthorizedPrincipalAbsent
        }
        if (-not $rightsPass) {
            return New-ContractResult -Outcome 'current_process_rights_check_fail'
        }
        return New-ContractResult -Outcome 'current_process_rights_check_pass'
    }

    if ([string] $Vector.probe_case -ceq 'success') {
        return New-ContractResult -Outcome 'two_hash_checks_pass_and_no_probe_content_retained'
    }
    if ([string] $Vector.probe_case -ceq 'failure') {
        return New-ContractResult -Outcome 'storage_blocked_no_retry_cleanup_scope_does_not_expand'
    }

    return New-ContractResult -Outcome 'contract_valid_no_machine_execution'
}

function Invoke-SealedMachineAction {
    param(
        [Parameter(Mandatory = $true)]
        [string] $ActionId,

        [Parameter(Mandatory = $true)]
        [hashtable] $Request,

        [Parameter(Mandatory = $true)]
        [hashtable] $Context,

        [Parameter(Mandatory = $true)]
        [pscustomobject] $State
    )

    switch -CaseSensitive ($ActionId) {
        'U3K-A01-UTC-CLOCK-START' {
            $result = Get-P36UtcStartTime
            if ([bool] $result.ok) {
                $Context.attempt_started_at = [string] $result.utc_value
            }
            return $result
        }
        'U3K-A02-PACKAGE-RUNNER-AUTHORITY-VERIFY' {
            return Test-P36ExecutionBindings `
                -Request $Request `
                -RepositoryRoot $script:RepositoryRoot `
                -RuntimePath ([System.IO.Path]::Combine($PSHOME, 'pwsh.exe')) `
                -AttemptStartedAt ([string] $Context.attempt_started_at)
        }
        'U3K-A03-AUTHORIZATION-RECORD' {
            return Write-P36AuthorizationRecord `
                -Request $Request `
                -RepositoryRoot $script:RepositoryRoot `
                -AttemptStartedAt ([string] $Context.attempt_started_at)
        }
        'U3K-A04-F-DRIVE-INFO' {
            $result = Get-P36DriveInformation
            foreach ($name in @(
                'drive_ready',
                'drive_type',
                'filesystem',
                'total_bytes',
                'available_free_bytes',
                'available_free_percent'
            )) {
                $Context.observed[$name] = $result[$name]
            }
            return $result
        }
        'U3K-A05-CANONICAL-PATH-AND-ABSENCE' {
            $result = Test-P36CandidatePath
            $Context.observed.canonical_path_policy_pass = [bool] $result.exact_canonical_path
            $Context.observed.candidate_absent_before_attempt = [bool] $result.candidate_absent
            return $result
        }
        'U3K-A06-PROTECTED-DACL-CONSTRUCT' {
            $result = New-P36ProtectedDirectorySecurity
            if ([bool] $result.ok) {
                $Context.security_descriptor_bytes = $result.security_descriptor_bytes
                $Context.current_process_SID_in_memory = $result.current_process_SID_in_memory
            }
            return $result
        }
        'U3K-A07-SECURITY-AT-CREATE-ROOT' {
            if ($null -eq $Context.security_descriptor_bytes) {
                return @{
                    ok                          = $false
                    native_success              = $false
                    error_already_exists        = $false
                    required_API_used           = $true
                    security_attributes_nonnull = $false
                    fallback_used               = $false
                    reason_code                 = 'security_descriptor_invalid'
                }
            }
            return New-P36QuarantineRoot `
                -SecurityDescriptorBytes $Context.security_descriptor_bytes
        }
        'U3K-A08-NORMALIZED-DACL-VERIFY' {
            if ($null -eq $Context.current_process_SID_in_memory) {
                return @{ ok = $false; reason_code = 'identity_unavailable' }
            }
            $result = Test-P36QuarantineDacl `
                -CurrentProcessSid $Context.current_process_SID_in_memory
            $Context.observed.bounded_DACL_policy_booleans = [ordered]@{
                access_rules_protected = [bool] $result.access_rules_protected
                exact_rule_count_pass = [bool] $result.exact_rule_count_pass
                current_process_principal_pass = [bool] $result.current_process_principal_pass
                current_process_Modify_Synchronize_rights_pass = [bool] $result.current_process_Modify_Synchronize_rights_pass
                current_process_excessive_or_unknown_rights_absent = [bool] $result.current_process_excessive_or_unknown_rights_absent
                LocalSystem_tuple_pass = [bool] $result.LocalSystem_tuple_pass
                Administrators_tuple_pass = [bool] $result.Administrators_tuple_pass
                inheritance_flags_pass = [bool] $result.inheritance_flags_pass
                propagation_flags_pass = [bool] $result.propagation_flags_pass
                access_types_pass = [bool] $result.access_types_pass
                inherited_rule_absent = [bool] $result.inherited_rule_absent
                deny_rule_absent = [bool] $result.deny_rule_absent
                unauthorized_principal_absent = [bool] $result.unauthorized_principal_absent
                overall_DACL_pass = [bool] $result.overall_DACL_pass
            }
            return $result
        }
        'U3K-A09-ATOMIC-CAPABILITY-PROBE' {
            $result = Invoke-P36AtomicCapabilityProbe
            $Context.observed.bounded_probe_policy_booleans = [ordered]@{
                probe_paths_absent = [bool] $result.probe_paths_absent
                exact_byte_count = [bool] $result.exact_byte_count
                write_through = [bool] $result.write_through
                flush_to_disk = [bool] $result.flush_to_disk
                first_hash_match = [bool] $result.first_hash_match
                rename_write_through_only = [bool] $result.rename_write_through_only
                second_hash_match = [bool] $result.second_hash_match
                cleanup_complete = [bool] $result.cleanup_complete
                zero_retention = [bool] $result.zero_retention
            }
            return $result
        }
        'U3K-A10-NORMALIZE-HASH-WRITE' {
            $projection = Get-P36TerminalProjection -State $State
            $projection.terminal = $true
            $projection.succeeded = $true
            $projection.reason_code = 'ok'
            return Write-P36AttemptOutputs `
                -RepositoryRoot $script:RepositoryRoot `
                -TerminalProjection $projection `
                -ObservedProjection $Context.observed `
                -AttemptStartedAt ([string] $Context.attempt_started_at)
        }
        default { throw 'P36_DEFAULT_DENY_UNKNOWN_ACTION' }
    }
}

if ($Mode -ceq 'Contract') {
    if ($PSCmdlet.ParameterSetName -cne 'Contract') {
        throw 'P36_DEFAULT_DENY_PARAMETER_SET'
    }
    $inputBytes = [System.Text.Encoding]::UTF8.GetByteCount($ContractVectorJson)
    if ($inputBytes -gt $script:MaximumInputBytes) {
        throw 'P36_CONTRACT_INPUT_TOO_LARGE'
    }

    $vector = $ContractVectorJson | ConvertFrom-Json -Depth 16
    $result = Get-ContractOutcome -Vector $vector
    $result | ConvertTo-Json -Compress -Depth 4
    exit 0
}

if ($Mode -cne 'Storage' -or $PSCmdlet.ParameterSetName -cne 'Storage') {
    throw 'P36_DEFAULT_DENY_MODE'
}

$storageInputBytes = [System.Text.Encoding]::UTF8.GetByteCount($StorageRequestJson)
if ($storageInputBytes -gt $script:MaximumInputBytes) {
    throw 'P36_STORAGE_INPUT_TOO_LARGE'
}
$request = $StorageRequestJson | ConvertFrom-Json -AsHashtable -Depth 24 -DateKind String

# The exact module hashes and owner receipt are checked before either module loads.
if (-not (Test-P36PreImportReceipt -Request $request)) {
    throw 'P36_PREIMPORT_RECEIPT_INVALID'
}

Import-Module -Name $script:HandlerModulePath -Force -ErrorAction Stop
$envelope = Test-P36StorageEnvelope -Request $request
if (-not [bool] $envelope.succeeded) {
    $envelope | ConvertTo-Json -Compress -Depth 4
    exit 2
}

# A02 recomputes every file and runtime binding after this exact-path import.
Import-Module -Name $script:WindowsAdapterPath -Force -ErrorAction Stop

$state = New-P36MachineHandlerState
$context = @{
    attempt_started_at             = $null
    security_descriptor_bytes      = $null
    current_process_SID_in_memory  = $null
    observed                       = @{
        drive_ready                    = $false
        drive_type                     = 'unknown'
        filesystem                     = 'unknown'
        total_bytes                    = 0
        available_free_bytes           = 0
        available_free_percent         = 0.0
        canonical_path_policy_pass     = $false
        candidate_absent_before_attempt = $false
        bounded_DACL_policy_booleans   = [ordered]@{}
        bounded_probe_policy_booleans  = [ordered]@{}
    }
}

foreach ($actionId in $script:AllowedActionIds) {
    $before = Get-P36MonotonicSeconds
    $adapterResult = Invoke-SealedMachineAction `
        -ActionId $actionId `
        -Request $request `
        -Context $context `
        -State $state
    $after = Get-P36MonotonicSeconds
    $transitionTime = if ($actionId -ceq 'U3K-A01-UTC-CLOCK-START' -and [bool] $adapterResult.ok) {
        [double] $adapterResult.monotonic_seconds
    } else {
        $after
    }
    if (($after - $before) -gt 30.0) {
        $transitionTime = $before + 30.000001
    }
    $decision = Invoke-P36HandlerTransition `
        -State $state `
        -ActionId $actionId `
        -AdapterResult $adapterResult `
        -MonotonicSeconds $transitionTime

    if (-not [bool] $decision.succeeded) {
        if ([bool] $decision.cleanup_required) {
            $cleanup = Invoke-P36BoundedCleanup `
                -RootCreatedByAttempt ([bool] $state.root_created_by_attempt) `
                -PartialCreatedByAttempt ([bool] $state.probe_partial_created_by_attempt) `
                -VerifiedCreatedByAttempt ([bool] $state.probe_verified_created_by_attempt)
            if (-not [bool] $cleanup.ok) {
                $state.manual_review_required = $true
                $state.reason_code = 'manual_review_required'
            }
        }
        if ([bool] $state.authorization_record_written) {
            $terminal = Get-P36TerminalProjection -State $state
            [void] (Write-P36AttemptOutputs `
                -RepositoryRoot $script:RepositoryRoot `
                -TerminalProjection $terminal `
                -ObservedProjection $context.observed `
                -AttemptStartedAt ([string] $context.attempt_started_at))
        }
        break
    }
}

$final = Get-P36TerminalProjection -State $state
$final | ConvertTo-Json -Compress -Depth 8
