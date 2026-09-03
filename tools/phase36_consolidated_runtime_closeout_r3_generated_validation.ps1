# Phase 3.6 R3 generated-validation child harness.
# Additive successor: imports the two JSON commands as cmdlets.

param(
    [string]$ControllerPath = '',
    [string]$ControllerSha256 = '',
    [string]$VectorManifestPath = '',
    [string]$VectorManifestSha256 = ''
)

Set-StrictMode -Version Latest

$ErrorActionPreference = 'Stop'
$ProgressPreference = 'SilentlyContinue'
$WarningPreference = 'SilentlyContinue'
$VerbosePreference = 'SilentlyContinue'
$DebugPreference = 'SilentlyContinue'
$InformationPreference = 'SilentlyContinue'
$PSModuleAutoLoadingPreference = 'None'

$Script:HcamU4dContractVersion = '1.0.0'
$Script:HcamU4dRequiredCaseCount = 416
$Script:HcamU4dMachineAuthorityEnabled = $false
$Script:HcamU4dAutomaticRetryEnabled = $false
$Script:HcamU4dRawRetentionEnabled = $false
$Script:HcamU4dAllowedStages = @(
    'bootstrap'
    'source_binding'
    'vector_validation'
    'generated_validation'
    'evidence_seal'
)
$Script:HcamU4dAllowedReasons = @(
    'generated_validation_accepted'
    'harness_input_invalid'
    'module_bootstrap_failed'
    'source_identity_invalid'
    'vector_manifest_invalid'
    'controller_load_failed'
    'generated_case_mismatch'
    'terminal_default_deny_internal_failure'
)
$Script:HcamU4dProhibitedFields = @(
    'acl'
    'credentials'
    'environment'
    'exception'
    'hostname'
    'ip_address'
    'mac'
    'native_status'
    'owner'
    'password'
    'path'
    'raw'
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

# HCAM_U4D_CONTRACT_PROJECTION_JSON_BEGIN
<#
{
  "child_reason_codes": [
    "generated_validation_accepted",
    "harness_input_invalid",
    "module_bootstrap_failed",
    "source_identity_invalid",
    "vector_manifest_invalid",
    "controller_load_failed",
    "generated_case_mismatch",
    "terminal_default_deny_internal_failure"
  ],
  "contract_version": "1.0.0",
  "maximum_stderr_bytes": 0,
  "maximum_stdout_bytes": 4096,
  "operation": "classify_process_output_v1",
  "required_case_count": 416,
  "terminal_line_count": 1
}
#>
# HCAM_U4D_CONTRACT_PROJECTION_JSON_END

function Write-HcamU4dTerminalEnvelope {
    param(
        [Parameter(Mandatory = $true)][bool]$Succeeded,
        [Parameter(Mandatory = $true)][string]$Stage,
        [Parameter(Mandatory = $true)][string]$ReasonCode,
        [Parameter(Mandatory = $true)][int]$AcceptedCaseCount,
        [Parameter(Mandatory = $true)][bool]$SourceIdentityValid
    )

    if ($Stage -cnotin $Script:HcamU4dAllowedStages -or
        $ReasonCode -cnotin $Script:HcamU4dAllowedReasons -or
        $AcceptedCaseCount -lt 0 -or
        $AcceptedCaseCount -gt $Script:HcamU4dRequiredCaseCount) {
        $Succeeded = $false
        $Stage = 'bootstrap'
        $ReasonCode = 'terminal_default_deny_internal_failure'
        $AcceptedCaseCount = 0
        $SourceIdentityValid = $false
    }

    $SucceededJson = if ($Succeeded) { 'true' } else { 'false' }
    $IdentityJson = if ($SourceIdentityValid) { 'true' } else { 'false' }
    $Json = '{' +
        '"contract_version":"1.0.0",' +
        '"terminal":true,' +
        '"succeeded":' + $SucceededJson + ',' +
        '"stage":"' + $Stage + '",' +
        '"reason_code":"' + $ReasonCode + '",' +
        '"required_case_count":416,' +
        '"accepted_case_count":' + $AcceptedCaseCount.ToString(
            [System.Globalization.CultureInfo]::InvariantCulture
        ) + ',' +
        '"source_identity_valid":' + $IdentityJson + ',' +
        '"raw_retained_bytes":0' +
        '}'

    [System.Console]::Out.WriteLine($Json)
    [System.Environment]::Exit(0)
}

function Get-HcamU4dBoundedSha256 {
    param(
        [Parameter(Mandatory = $true)][string]$LiteralPath,
        [Parameter(Mandatory = $true)][long]$MaximumBytes
    )

    $Item = [System.IO.FileInfo]::new($LiteralPath)
    if (-not $Item.Exists -or
        ($Item.Attributes -band [System.IO.FileAttributes]::ReparsePoint) -ne 0 -or
        $Item.Length -lt 1 -or
        $Item.Length -gt $MaximumBytes) {
        return $null
    }

    $Stream = $null
    $Hasher = $null
    try {
        $Stream = [System.IO.File]::Open(
            $Item.FullName,
            [System.IO.FileMode]::Open,
            [System.IO.FileAccess]::Read,
            [System.IO.FileShare]::Read
        )
        $Hasher = [System.Security.Cryptography.SHA256]::Create()
        return [System.Convert]::ToHexString($Hasher.ComputeHash($Stream))
    }
    finally {
        if ($null -ne $Hasher) {
            $Hasher.Dispose()
        }
        if ($null -ne $Stream) {
            $Stream.Dispose()
        }
    }
}

function ConvertTo-HcamU4dGeneratedContractValue {
    param([AllowNull()][object]$Value)

    if ($null -eq $Value) {
        return $null
    }
    if ($Value -is [System.Collections.IDictionary]) {
        $Converted = [ordered]@{}
        foreach ($Key in $Value.Keys) {
            $Converted[[string]$Key] = ConvertTo-HcamU4dGeneratedContractValue `
                -Value $Value[$Key]
        }
        return $Converted
    }
    if ($Value -is [System.Collections.IList] -and $Value -isnot [string]) {
        $Converted = [System.Collections.Generic.List[object]]::new()
        foreach ($Item in $Value) {
            $Converted.Add((ConvertTo-HcamU4dGeneratedContractValue -Value $Item))
        }
        return ,$Converted.ToArray()
    }
    if ($Value -is [long] -and
        $Value -ge [int]::MinValue -and
        $Value -le [int]::MaxValue) {
        return [int]$Value
    }
    return $Value
}

function Test-HcamU4dNonnegativeInt32 {
    param([AllowNull()][object]$Value)

    return $Value -is [int] -and $Value -ge 0
}

function Test-HcamU4dContainsProhibitedField {
    param([AllowNull()][object]$Value)

    if ($Value -is [System.Collections.IDictionary]) {
        foreach ($Key in $Value.Keys) {
            if ($Key -isnot [string] -or
                $Key.ToLowerInvariant() -in $Script:HcamU4dProhibitedFields -or
                (Test-HcamU4dContainsProhibitedField -Value $Value[$Key])) {
                return $true
            }
        }
    }
    elseif ($Value -is [System.Collections.IList] -and $Value -isnot [string]) {
        foreach ($Item in $Value) {
            if (Test-HcamU4dContainsProhibitedField -Value $Item) {
                return $true
            }
        }
    }
    return $false
}

function Test-HcamU4dAuthorizationRequest {
    param([AllowNull()][object]$Value)

    if ($Value -isnot [System.Collections.IDictionary] -or
        -not (Test-HcamOuterExactFieldSet `
            -Value $Value -Expected $Script:HcamOuterAuthorizationFields)) {
        return $false
    }
    if ($Value.decision_id -cne $Script:HcamOuterRuntimeAuthorization -or
        $Value.package_digest_sha256 -cnotmatch '^[0-9A-F]{64}$' -or
        $Value.max_attempts -isnot [int] -or $Value.max_attempts -ne 3 -or
        $Value.attempt_index -isnot [int] -or
        $Value.attempt_index -notin @(1, 2, 3) -or
        $Value.attempt_state -cnotin @('first', 'retry')) {
        return $false
    }
    foreach ($Name in @(
        'same_package_digest',
        'retry_reason_allowlisted',
        'machine_authority',
        'automatic_retry'
    )) {
        if ($Value[$Name] -isnot [bool]) {
            return $false
        }
    }
    if (-not $Value.machine_authority -or $Value.automatic_retry -or
        ($Value.attempt_state -ceq 'first' -and $Value.attempt_index -ne 1) -or
        ($Value.attempt_state -ceq 'retry' -and
            ($Value.attempt_index -le 1 -or
                -not $Value.same_package_digest -or
                -not $Value.retry_reason_allowlisted))) {
        return $false
    }
    return $true
}

function Test-HcamU4dParentRequestRecord {
    param(
        [AllowNull()][object]$Record,
        [Parameter(Mandatory = $true)][int]$ExpectedIndex
    )

    if ($Record -isnot [System.Collections.IDictionary] -or
        -not (Test-HcamOuterExactFieldSet `
            -Value $Record -Expected $Script:HcamOuterParentFields) -or
        $Record.parent_index -isnot [int] -or
        $Record.parent_index -ne $ExpectedIndex) {
        return $false
    }
    foreach ($Name in @(
        'present',
        'regular_directory',
        'nonreparse',
        'canonical_match',
        'valid'
    )) {
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
        return -not $Record.valid -and
            $Record.reason_code -ceq 'parent_predicate_inconsistent'
    }
    return $Record.reason_code -ceq (Get-HcamOuterExpectedParentReason -Record $Record)
}

function Test-HcamU4dGeneratedControllerRequest {
    param([AllowNull()][object]$Request)

    if ($Request -isnot [System.Collections.IDictionary] -or
        -not (Test-HcamOuterExactFieldSet `
            -Value $Request -Expected $Script:HcamOuterRequestFields) -or
        (Test-HcamU4dContainsProhibitedField -Value $Request) -or
        $Request.contract_version -cne $Script:HcamOuterContractVersion -or
        $Request.operation -cnotin $Script:HcamOuterSupportedOperations -or
        -not (Test-HcamU4dAuthorizationRequest -Value $Request.authorization)) {
        return $false
    }
    if ($Request.parent_records -isnot [object[]] -or
        $Request.parent_records.Count -ne 3) {
        return $false
    }
    for ($Index = 0; $Index -lt 3; $Index += 1) {
        if (-not (Test-HcamU4dParentRequestRecord `
            -Record $Request.parent_records[$Index] -ExpectedIndex $Index)) {
            return $false
        }
    }
    if ($Request.stage_signals -isnot [System.Collections.IDictionary] -or
        -not (Test-HcamOuterExactFieldSet `
            -Value $Request.stage_signals `
            -Expected $Script:HcamOuterStageSignalFields)) {
        return $false
    }
    foreach ($Name in $Script:HcamOuterStageSignalFields) {
        if ($Request.stage_signals[$Name] -isnot [bool]) {
            return $false
        }
    }
    if ($Request.process_limits -isnot [System.Collections.IDictionary] -or
        -not (Test-HcamOuterExactFieldSet `
            -Value $Request.process_limits `
            -Expected $Script:HcamOuterProcessLimitFields)) {
        return $false
    }
    foreach ($Name in $Script:HcamOuterProcessLimitFields) {
        if ($Request.process_limits[$Name] -isnot [int] -or
            $Request.process_limits[$Name] -ne $Script:HcamOuterProcessLimits[$Name]) {
            return $false
        }
    }
    if ($Request.process_observation -isnot [System.Collections.IDictionary] -or
        -not (Test-HcamOuterExactFieldSet `
            -Value $Request.process_observation `
            -Expected $Script:HcamOuterProcessObservationFields)) {
        return $false
    }
    foreach ($Name in $Script:HcamOuterProcessObservationFields) {
        if (-not (Test-HcamU4dNonnegativeInt32 `
            -Value $Request.process_observation[$Name])) {
            return $false
        }
    }
    if ($Request.retention -isnot [System.Collections.IDictionary] -or
        -not (Test-HcamOuterExactFieldSet `
            -Value $Request.retention -Expected $Script:HcamOuterRetentionFields) -or
        -not (Test-HcamU4dNonnegativeInt32 `
            -Value $Request.retention.raw_retained_bytes) -or
        $Request.retention.sanitized_only -isnot [bool]) {
        return $false
    }
    return $true
}

try {
    if ([string]::IsNullOrWhiteSpace($ControllerPath) -or
        [string]::IsNullOrWhiteSpace($VectorManifestPath) -or
        $ControllerSha256 -cnotmatch '^[0-9A-F]{64}$' -or
        $VectorManifestSha256 -cnotmatch '^[0-9A-F]{64}$') {
        Write-HcamU4dTerminalEnvelope `
            -Succeeded $false -Stage 'bootstrap' `
            -ReasonCode 'harness_input_invalid' -AcceptedCaseCount 0 `
            -SourceIdentityValid $false
    }

    $ControllerHash = Get-HcamU4dBoundedSha256 `
        -LiteralPath $ControllerPath -MaximumBytes 131072
    $VectorHash = Get-HcamU4dBoundedSha256 `
        -LiteralPath $VectorManifestPath -MaximumBytes 4194304
    if ($ControllerHash -cne $ControllerSha256 -or
        $VectorHash -cne $VectorManifestSha256) {
        Write-HcamU4dTerminalEnvelope `
            -Succeeded $false -Stage 'source_binding' `
            -ReasonCode 'source_identity_invalid' -AcceptedCaseCount 0 `
            -SourceIdentityValid $false
    }

    $UtilityManifest = [System.IO.Path]::Combine(
        $PSHOME,
        'Modules',
        'Microsoft.PowerShell.Utility',
        'Microsoft.PowerShell.Utility.psd1'
    )
    try {
        $null = Import-Module `
            -Name $UtilityManifest `
            -Cmdlet @('ConvertFrom-Json', 'ConvertTo-Json') `
            -Scope Local `
            -NoClobber `
            -ErrorAction Stop `
            -WarningAction SilentlyContinue `
            -Verbose:$false `
            -Debug:$false
    }
    catch {
        Write-HcamU4dTerminalEnvelope `
            -Succeeded $false -Stage 'bootstrap' `
            -ReasonCode 'module_bootstrap_failed' -AcceptedCaseCount 0 `
            -SourceIdentityValid $true
    }

    try {
        $VectorJson = [System.IO.File]::ReadAllText(
            [System.IO.FileInfo]::new($VectorManifestPath).FullName,
            [System.Text.UTF8Encoding]::new($false, $true)
        )
        $ParsedManifest = ConvertFrom-Json `
            -InputObject $VectorJson `
            -AsHashtable `
            -Depth 100 `
            -NoEnumerate
        $Manifest = ConvertTo-HcamU4dGeneratedContractValue -Value $ParsedManifest
    }
    catch {
        Write-HcamU4dTerminalEnvelope `
            -Succeeded $false -Stage 'vector_validation' `
            -ReasonCode 'vector_manifest_invalid' -AcceptedCaseCount 0 `
            -SourceIdentityValid $true
    }

    if ($Manifest -isnot [System.Collections.IDictionary] -or
        $Manifest.vector_count -ne $Script:HcamU4dRequiredCaseCount -or
        $Manifest.vectors -isnot [object[]] -or
        $Manifest.vectors.Count -ne $Script:HcamU4dRequiredCaseCount) {
        Write-HcamU4dTerminalEnvelope `
            -Succeeded $false -Stage 'vector_validation' `
            -ReasonCode 'vector_manifest_invalid' -AcceptedCaseCount 0 `
            -SourceIdentityValid $true
    }

    try {
        $null = . ([System.IO.FileInfo]::new($ControllerPath).FullName)
    }
    catch {
        Write-HcamU4dTerminalEnvelope `
            -Succeeded $false -Stage 'source_binding' `
            -ReasonCode 'controller_load_failed' -AcceptedCaseCount 0 `
            -SourceIdentityValid $true
    }

    $Accepted = 0
    foreach ($Vector in $Manifest.vectors) {
        try {
            $Attempts = 0
            if ($Vector.request -is [System.Collections.IDictionary] -and
                $Vector.request.authorization -is [System.Collections.IDictionary] -and
                $Vector.request.authorization.attempt_index -is [int] -and
                $Vector.request.authorization.attempt_index -in @(1, 2, 3)) {
                $Attempts = $Vector.request.authorization.attempt_index
            }
            if (Test-HcamU4dGeneratedControllerRequest -Request $Vector.request) {
                $Actual = Invoke-HcamOuterAttemptControllerR0 -Request $Vector.request
            }
            else {
                $Actual = New-HcamOuterDefaultDenyResult -AttemptsConsumed $Attempts
            }
            $ActualJson = ConvertTo-Json -InputObject $Actual -Depth 32 -Compress
            $ExpectedJson = ConvertTo-Json `
                -InputObject $Vector.expected_result -Depth 32 -Compress
        }
        catch {
            Write-HcamU4dTerminalEnvelope `
                -Succeeded $false -Stage 'generated_validation' `
                -ReasonCode 'generated_case_mismatch' `
                -AcceptedCaseCount $Accepted -SourceIdentityValid $true
        }
        if ($ActualJson -cne $ExpectedJson) {
            Write-HcamU4dTerminalEnvelope `
                -Succeeded $false -Stage 'generated_validation' `
                -ReasonCode 'generated_case_mismatch' `
                -AcceptedCaseCount $Accepted -SourceIdentityValid $true
        }
        $Accepted += 1
    }

    $ControllerHashAfter = Get-HcamU4dBoundedSha256 `
        -LiteralPath $ControllerPath -MaximumBytes 131072
    $VectorHashAfter = Get-HcamU4dBoundedSha256 `
        -LiteralPath $VectorManifestPath -MaximumBytes 4194304
    if ($ControllerHashAfter -cne $ControllerSha256 -or
        $VectorHashAfter -cne $VectorManifestSha256) {
        Write-HcamU4dTerminalEnvelope `
            -Succeeded $false -Stage 'source_binding' `
            -ReasonCode 'source_identity_invalid' `
            -AcceptedCaseCount $Accepted -SourceIdentityValid $false
    }

    Write-HcamU4dTerminalEnvelope `
        -Succeeded $true -Stage 'evidence_seal' `
        -ReasonCode 'generated_validation_accepted' `
        -AcceptedCaseCount $Accepted -SourceIdentityValid $true
}
catch {
    Write-HcamU4dTerminalEnvelope `
        -Succeeded $false -Stage 'bootstrap' `
        -ReasonCode 'terminal_default_deny_internal_failure' `
        -AcceptedCaseCount 0 -SourceIdentityValid $false
}
