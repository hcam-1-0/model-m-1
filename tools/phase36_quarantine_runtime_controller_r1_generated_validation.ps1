#requires -Version 7.0

# Phase 3.6 U3Z generated-only controller R1 contract-validation harness.
# This source is inert until a separate digest-bound runtime authorization exists.

[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)]
    [ValidatePattern('^[A-F0-9]{64}$')]
    [string] $ExpectedHarnessSha256,

    [Parameter(Mandatory = $true)]
    [ValidatePattern('^[A-F0-9]{64}$')]
    [string] $ExpectedMaterializedVectorSha256
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
$PSModuleAutoLoadingPreference = 'None'

$script:ContractId = 'P36-QUARANTINE-RUNTIME-CONTROLLER-U3Z-GENERATED-CONTRACT-VALIDATION-R0'
$script:FailureStage = 'binding'
$script:AllowedFailureStages = @(
    'binding'
    'manifest'
    'controller_load'
    'validation'
    'result_serialization'
)
$script:RepositoryRoot = [System.IO.Path]::GetFullPath(
    [System.IO.Path]::Combine($PSScriptRoot, '..')
)
$script:HarnessPath = [System.IO.Path]::Combine(
    $PSScriptRoot,
    'phase36_quarantine_runtime_controller_r1_generated_validation.ps1'
)
$script:ControllerPath = [System.IO.Path]::Combine(
    $PSScriptRoot,
    'phase36_quarantine_runtime_controller_r1.ps1'
)
$script:ContractPath = [System.IO.Path]::Combine(
    $script:RepositoryRoot,
    'contracts',
    'phase-3',
    'p3-6-quarantine-runtime-controller-r1-stage-projection-contract.json'
)
$script:AcceptedVectorPath = [System.IO.Path]::Combine(
    $script:RepositoryRoot,
    'contracts',
    'phase-3',
    'p3-6-quarantine-runtime-controller-r1-stage-projection-vectors.json'
)
$script:PythonReferencePath = [System.IO.Path]::Combine(
    $PSScriptRoot,
    'phase36_quarantine_runtime_controller_r1_reference.py'
)
$script:MaterializedVectorPath = [System.IO.Path]::Combine(
    $script:RepositoryRoot,
    'contracts',
    'phase-3',
    'p3-6-quarantine-runtime-controller-u3z-generated-contract-validation-r0-vectors.json'
)
$script:MaximumHashBufferBytes = 65536
$script:MaximumManifestBytes = 8388608
$script:ExpectedCaseCount = 288
$script:ExpectedGroupCount = 9
$script:ExpectedCasesPerGroup = 32
$script:AcceptedHashes = [ordered]@{
    $script:ControllerPath = '787655BAC55DDF563E9D1DC43EC37F010C271AB381E541B0734028E3F2B90B31'
    $script:ContractPath = '637C5400122874149D9835CC6BC521E5EEC9160222F4A7AC5CA1F6CD99E1BCC4'
    $script:AcceptedVectorPath = 'D8EDF5C0255B40FB6C28BB014C09DC503D2B53665E69C5AA5AB65C744AEA81E4'
    $script:PythonReferencePath = 'B5C7328CD666E0A8988F9B616C5B2A914D690A40BF2EA289C1F1C755E42B86F0'
}

function Write-HcamGeneratedValidationFailure {
    param(
        [Parameter(Mandatory = $true)]
        [string] $Stage
    )

    $safeStage = 'binding'
    if ($script:AllowedFailureStages -ccontains $Stage) {
        $safeStage = $Stage
    }
    $json = '{"contract_id":"' + $script:ContractId +
        '","terminal":true,"succeeded":false,"reason_code":"' +
        $safeStage +
        '_failed","cases_loaded":0,"cases_executed":0,"cases_passed":0,"cases_failed":0,"raw_fixture_retained_bytes":0,"raw_process_material_retained_bytes":0,"machine_action_count":0,"network_action_count":0,"automatic_retry_count":0,"U3K_authorized":false,"deployment_authorized":false}'
    [System.Console]::Out.WriteLine($json)
    exit 1
}

trap {
    Write-HcamGeneratedValidationFailure -Stage $script:FailureStage
}

function Get-HcamGeneratedValidationFileSha256 {
    param(
        [Parameter(Mandatory = $true)]
        [string] $LiteralPath
    )

    $stream = $null
    $algorithm = $null
    try {
        $stream = [System.IO.FileStream]::new(
            $LiteralPath,
            [System.IO.FileMode]::Open,
            [System.IO.FileAccess]::Read,
            [System.IO.FileShare]::Read,
            $script:MaximumHashBufferBytes,
            [System.IO.FileOptions]::SequentialScan
        )
        $algorithm = [System.Security.Cryptography.SHA256]::Create()
        return [System.Convert]::ToHexString($algorithm.ComputeHash($stream))
    } finally {
        if ($null -ne $algorithm) {
            $algorithm.Dispose()
        }
        if ($null -ne $stream) {
            $stream.Dispose()
        }
    }
}

function Assert-HcamGeneratedValidationRegularFile {
    param(
        [Parameter(Mandatory = $true)]
        [string] $LiteralPath,

        [Parameter(Mandatory = $true)]
        [long] $MaximumBytes
    )

    $information = [System.IO.FileInfo]::new($LiteralPath)
    if (-not $information.Exists -or $information.Length -le 0 -or $information.Length -gt $MaximumBytes) {
        throw 'HCAM_FILE_SIZE_INVALID'
    }
    $attributes = [System.IO.File]::GetAttributes($LiteralPath)
    if (
        ($attributes -band [System.IO.FileAttributes]::Directory) -ne 0 -or
        ($attributes -band [System.IO.FileAttributes]::ReparsePoint) -ne 0
    ) {
        throw 'HCAM_FILE_ATTRIBUTES_INVALID'
    }
}

function Assert-HcamGeneratedValidationBindings {
    foreach ($entry in $script:AcceptedHashes.GetEnumerator()) {
        Assert-HcamGeneratedValidationRegularFile `
            -LiteralPath $entry.Key `
            -MaximumBytes $script:MaximumManifestBytes
        if ((Get-HcamGeneratedValidationFileSha256 -LiteralPath $entry.Key) -cne $entry.Value) {
            throw 'HCAM_ACCEPTED_SOURCE_BINDING_MISMATCH'
        }
    }
    Assert-HcamGeneratedValidationRegularFile `
        -LiteralPath $script:HarnessPath `
        -MaximumBytes $script:MaximumManifestBytes
    Assert-HcamGeneratedValidationRegularFile `
        -LiteralPath $script:MaterializedVectorPath `
        -MaximumBytes $script:MaximumManifestBytes
    if ((Get-HcamGeneratedValidationFileSha256 -LiteralPath $script:HarnessPath) -cne $ExpectedHarnessSha256) {
        throw 'HCAM_HARNESS_BINDING_MISMATCH'
    }
    if (
        (Get-HcamGeneratedValidationFileSha256 -LiteralPath $script:MaterializedVectorPath) -cne
        $ExpectedMaterializedVectorSha256
    ) {
        throw 'HCAM_MATERIALIZED_VECTOR_BINDING_MISMATCH'
    }
}

function ConvertFrom-HcamGeneratedValidationJsonElement {
    param(
        [Parameter(Mandatory = $true)]
        [System.Text.Json.JsonElement] $Element
    )

    switch ($Element.ValueKind) {
        ([System.Text.Json.JsonValueKind]::Object) {
            $result = [ordered]@{}
            foreach ($property in $Element.EnumerateObject()) {
                $result[$property.Name] = ConvertFrom-HcamGeneratedValidationJsonElement `
                    -Element $property.Value
            }
            return $result
        }
        ([System.Text.Json.JsonValueKind]::Array) {
            $items = [System.Collections.Generic.List[object]]::new()
            foreach ($item in $Element.EnumerateArray()) {
                $items.Add((ConvertFrom-HcamGeneratedValidationJsonElement -Element $item))
            }
            return ,$items.ToArray()
        }
        ([System.Text.Json.JsonValueKind]::String) {
            return $Element.GetString()
        }
        ([System.Text.Json.JsonValueKind]::Number) {
            $integer32 = 0
            if ($Element.TryGetInt32([ref] $integer32)) {
                return $integer32
            }
            $integer64 = [long] 0
            if ($Element.TryGetInt64([ref] $integer64)) {
                return $integer64
            }
            $decimal = [decimal] 0
            if ($Element.TryGetDecimal([ref] $decimal)) {
                return $decimal
            }
            throw 'HCAM_JSON_NUMBER_INVALID'
        }
        ([System.Text.Json.JsonValueKind]::True) {
            return $true
        }
        ([System.Text.Json.JsonValueKind]::False) {
            return $false
        }
        ([System.Text.Json.JsonValueKind]::Null) {
            return $null
        }
        default {
            throw 'HCAM_JSON_VALUE_KIND_INVALID'
        }
    }
}

function Read-HcamGeneratedValidationManifest {
    $script:FailureStage = 'manifest'
    Assert-HcamGeneratedValidationRegularFile `
        -LiteralPath $script:MaterializedVectorPath `
        -MaximumBytes $script:MaximumManifestBytes
    $json = [System.IO.File]::ReadAllText(
        $script:MaterializedVectorPath,
        [System.Text.Encoding]::UTF8
    )
    $document = $null
    try {
        $options = [System.Text.Json.JsonDocumentOptions]::new()
        $options.AllowTrailingCommas = $false
        $options.CommentHandling = [System.Text.Json.JsonCommentHandling]::Disallow
        $options.MaxDepth = 64
        $document = [System.Text.Json.JsonDocument]::Parse($json, $options)
        return ConvertFrom-HcamGeneratedValidationJsonElement -Element $document.RootElement
    } finally {
        $json = $null
        if ($null -ne $document) {
            $document.Dispose()
        }
    }
}

function Test-HcamGeneratedValidationValueEqual {
    param(
        [AllowNull()]
        [object] $Left,

        [AllowNull()]
        [object] $Right
    )

    if ($null -eq $Left -or $null -eq $Right) {
        return $null -eq $Left -and $null -eq $Right
    }
    if ($Left -is [System.Collections.IDictionary] -and $Right -is [System.Collections.IDictionary]) {
        if ($Left.Count -ne $Right.Count) {
            return $false
        }
        foreach ($key in $Left.Keys) {
            if (-not $Right.Contains($key)) {
                return $false
            }
            if (-not (Test-HcamGeneratedValidationValueEqual -Left $Left[$key] -Right $Right[$key])) {
                return $false
            }
        }
        return $true
    }
    if (
        $Left -is [System.Collections.IList] -and
        $Right -is [System.Collections.IList] -and
        $Left -isnot [string] -and
        $Right -isnot [string]
    ) {
        if ($Left.Count -ne $Right.Count) {
            return $false
        }
        for ($index = 0; $index -lt $Left.Count; $index += 1) {
            if (-not (Test-HcamGeneratedValidationValueEqual -Left $Left[$index] -Right $Right[$index])) {
                return $false
            }
        }
        return $true
    }
    if ($Left.GetType() -ne $Right.GetType()) {
        return $false
    }
    return $Left -ceq $Right
}

function Assert-HcamGeneratedValidationManifest {
    param(
        [Parameter(Mandatory = $true)]
        [System.Collections.IDictionary] $Manifest
    )

    if (
        $Manifest.contract_format -cne 'hcam.phase3.p3_6.quarantine_runtime_controller_u3z_generated_contract_validation_r0_materialized_vectors.v1' -or
        $Manifest.contract_version -cne '1.0.0' -or
        [int] $Manifest.vector_count -ne $script:ExpectedCaseCount -or
        $Manifest.cases.Count -ne $script:ExpectedCaseCount -or
        $Manifest.source_manifest.sha256 -cne $script:AcceptedHashes[$script:AcceptedVectorPath] -or
        [int] $Manifest.source_manifest.vector_count -ne $script:ExpectedCaseCount -or
        $Manifest.controller_binding.source_sha256 -cne $script:AcceptedHashes[$script:ControllerPath] -or
        $Manifest.controller_binding.function -cne 'Invoke-HcamRuntimeControllerR1' -or
        $Manifest.controller_binding.request_mode -cne 'Policy' -or
        $Manifest.group_counts.Count -ne $script:ExpectedGroupCount
    ) {
        throw 'HCAM_MATERIALIZED_MANIFEST_CONTRACT_INVALID'
    }
    foreach ($group in $Manifest.group_counts.Keys) {
        if ([int] $Manifest.group_counts[$group] -ne $script:ExpectedCasesPerGroup) {
            throw 'HCAM_MATERIALIZED_GROUP_COUNT_INVALID'
        }
    }

    $caseIds = [System.Collections.Generic.HashSet[string]]::new(
        [System.StringComparer]::Ordinal
    )
    $sourceIds = [System.Collections.Generic.HashSet[string]]::new(
        [System.StringComparer]::Ordinal
    )
    foreach ($case in $Manifest.cases) {
        if (
            -not $caseIds.Add([string] $case.case_id) -or
            -not $sourceIds.Add([string] $case.source_vector_id) -or
            $case.request.mode -cne 'Policy' -or
            $case.request.authorization_binding.machine_authority -ne $false -or
            $case.request.authorization_binding.automatic_retry -ne $false
        ) {
            throw 'HCAM_MATERIALIZED_CASE_CONTRACT_INVALID'
        }
    }
    if (
        $caseIds.Count -ne $script:ExpectedCaseCount -or
        $sourceIds.Count -ne $script:ExpectedCaseCount
    ) {
        throw 'HCAM_MATERIALIZED_PROVENANCE_INVALID'
    }
}

function Invoke-HcamGeneratedValidationCases {
    param(
        [Parameter(Mandatory = $true)]
        [System.Collections.IDictionary] $Manifest
    )

    $script:FailureStage = 'validation'
    $passed = 0
    $failed = 0
    $literalNullSuccessMatch = $true
    $failureActionReasonMatch = $true
    $crossLanguageDifferenceCount = 0

    foreach ($case in $Manifest.cases) {
        $actual = Invoke-HcamRuntimeControllerR1 -Request $case.request
        $matches = Test-HcamGeneratedValidationValueEqual `
            -Left $actual `
            -Right $case.expected_projection
        if ($matches) {
            $passed += 1
        } else {
            $failed += 1
        }

        if ($case.group -ceq 'policy_valid_exact_null_success') {
            $literalNullSuccessMatch = $literalNullSuccessMatch -and (
                $actual.succeeded -eq $true -and
                $actual.stage_projection.completed_actions -eq 18 -and
                $null -eq $actual.stage_projection.failed_action -and
                $null -eq $actual.stage_projection.failed_stage
            )
        }
        if (
            $case.group -ceq 'all_eighteen_failure_actions' -or
            $case.group -ceq 'all_eighteen_failure_reasons'
        ) {
            $failureActionReasonMatch = $failureActionReasonMatch -and (
                $actual.succeeded -eq $false -and
                -not [string]::IsNullOrEmpty([string] $actual.stage_projection.failed_action) -and
                -not [string]::IsNullOrEmpty([string] $actual.stage_projection.failed_stage) -and
                $actual.reason_code -ceq $actual.stage_projection.failed_stage
            )
        }
        if ($case.group -ceq 'cross_language_canonical_projection' -and -not $matches) {
            $crossLanguageDifferenceCount += 1
        }

        $actual = $null
        $matches = $null
    }

    return [ordered]@{
        loaded = $Manifest.cases.Count
        executed = $passed + $failed
        passed = $passed
        failed = $failed
        literal_null_success_match = $literalNullSuccessMatch
        all_failure_action_reason_match = $failureActionReasonMatch
        cross_language_projection_difference_count = $crossLanguageDifferenceCount
    }
}

$script:FailureStage = 'binding'
Assert-HcamGeneratedValidationBindings
$manifest = Read-HcamGeneratedValidationManifest
Assert-HcamGeneratedValidationManifest -Manifest $manifest

$script:FailureStage = 'controller_load'
. $script:ControllerPath

$summary = Invoke-HcamGeneratedValidationCases -Manifest $manifest
if (
    $summary.loaded -ne $script:ExpectedCaseCount -or
    $summary.executed -ne $script:ExpectedCaseCount -or
    $summary.passed -ne $script:ExpectedCaseCount -or
    $summary.failed -ne 0 -or
    -not $summary.literal_null_success_match -or
    -not $summary.all_failure_action_reason_match -or
    $summary.cross_language_projection_difference_count -ne 0
) {
    Write-HcamGeneratedValidationFailure -Stage 'validation'
}

$script:FailureStage = 'result_serialization'
$result = '{"contract_id":"' + $script:ContractId +
    '","terminal":true,"succeeded":true,"reason_code":"generated_contract_validation_passed","cases_loaded":288,"cases_executed":288,"cases_passed":288,"cases_failed":0,"literal_null_success_match":true,"all_failure_action_reason_match":true,"cross_language_projection_difference_count":0,"raw_fixture_retained_bytes":0,"raw_process_material_retained_bytes":0,"machine_action_count":0,"network_action_count":0,"automatic_retry_count":0,"U3K_authorized":false,"deployment_authorized":false}'
[System.Console]::Out.WriteLine($result)
exit 0
