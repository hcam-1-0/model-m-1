#requires -Version 7.0

[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)]
    [ValidateSet('Contract')]
    [string] $Mode,

    [Parameter(Mandatory = $true)]
    [ValidateLength(2, 65536)]
    [string] $ContractVectorJson
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

$script:ContractId = 'P36-QUARANTINE-TRANSACTION-RUNNER-R0-1.0.0'
$script:MaximumInputBytes = 65536
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
        [string] $ActionId
    )

    switch ($ActionId) {
        'U3K-A01-UTC-CLOCK-START' { throw 'P36_MACHINE_HANDLER_NOT_IMPLEMENTED' }
        'U3K-A02-PACKAGE-RUNNER-AUTHORITY-VERIFY' { throw 'P36_MACHINE_HANDLER_NOT_IMPLEMENTED' }
        'U3K-A03-AUTHORIZATION-RECORD' { throw 'P36_MACHINE_HANDLER_NOT_IMPLEMENTED' }
        'U3K-A04-F-DRIVE-INFO' { throw 'P36_MACHINE_HANDLER_NOT_IMPLEMENTED' }
        'U3K-A05-CANONICAL-PATH-AND-ABSENCE' { throw 'P36_MACHINE_HANDLER_NOT_IMPLEMENTED' }
        'U3K-A06-PROTECTED-DACL-CONSTRUCT' { throw 'P36_MACHINE_HANDLER_NOT_IMPLEMENTED' }
        'U3K-A07-SECURITY-AT-CREATE-ROOT' { throw 'P36_MACHINE_HANDLER_NOT_IMPLEMENTED' }
        'U3K-A08-NORMALIZED-DACL-VERIFY' { throw 'P36_MACHINE_HANDLER_NOT_IMPLEMENTED' }
        'U3K-A09-ATOMIC-CAPABILITY-PROBE' { throw 'P36_MACHINE_HANDLER_NOT_IMPLEMENTED' }
        'U3K-A10-NORMALIZE-HASH-WRITE' { throw 'P36_MACHINE_HANDLER_NOT_IMPLEMENTED' }
        default { throw 'P36_DEFAULT_DENY_UNKNOWN_ACTION' }
    }
}

if ($Mode -cne 'Contract') {
    throw 'P36_DEFAULT_DENY_MODE'
}

$inputBytes = [System.Text.Encoding]::UTF8.GetByteCount($ContractVectorJson)
if ($inputBytes -gt $script:MaximumInputBytes) {
    throw 'P36_CONTRACT_INPUT_TOO_LARGE'
}

$vector = $ContractVectorJson | ConvertFrom-Json -Depth 16
$result = Get-ContractOutcome -Vector $vector
$result | ConvertTo-Json -Compress -Depth 4
