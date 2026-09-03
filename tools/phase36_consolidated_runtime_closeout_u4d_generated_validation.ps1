# Phase 3.6 U4D generated-validation child harness.
# Source-only implementation. This file was not parsed, imported, dot-sourced, or executed.

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
            -Function @('ConvertFrom-Json', 'ConvertTo-Json') `
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
        $Manifest = ConvertFrom-Json `
            -InputObject $VectorJson `
            -AsHashtable `
            -Depth 100 `
            -NoEnumerate
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
            $Actual = Invoke-HcamOuterAttemptControllerR0 -Request $Vector.request
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
