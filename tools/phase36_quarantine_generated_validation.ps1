#requires -Version 7.0

[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)]
    [ValidateSet('Parse', 'Contract', 'Handler', 'Aggregate')]
    [string] $Mode,

    [Parameter(Mandatory = $true)]
    [ValidatePattern('^[A-F0-9]{64}$')]
    [string] $ExpectedHarnessSha256,

    [Parameter(Mandatory = $true)]
    [ValidatePattern('^[A-F0-9]{64}$')]
    [string] $ExpectedVectorManifestSha256
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
$PSModuleAutoLoadingPreference = 'None'

$script:ContractId = 'P36-QUARANTINE-GENERATED-VALIDATION-HARNESS-R0-1.0.0'
$script:RepositoryRoot = [System.IO.Path]::GetFullPath(
    [System.IO.Path]::Combine($PSScriptRoot, '..')
)
$script:HarnessPath = [System.IO.Path]::Combine(
    $PSScriptRoot,
    'phase36_quarantine_generated_validation.ps1'
)
$script:RunnerPath = [System.IO.Path]::Combine(
    $PSScriptRoot,
    'phase36_quarantine_transaction_runner.ps1'
)
$script:HandlerModulePath = [System.IO.Path]::Combine(
    $PSScriptRoot,
    'phase36_quarantine_machine_handlers.psm1'
)
$script:WindowsAdapterParserPath = [System.IO.Path]::Combine(
    $PSScriptRoot,
    'phase36_quarantine_windows_storage_adapter.psm1'
)
$script:VectorManifestPath = [System.IO.Path]::Combine(
    $script:RepositoryRoot,
    'contracts',
    'phase-3',
    'p3-6-quarantine-generated-powershell-validation-r0-vectors.json'
)
$script:RuntimePath = 'C:\Program Files\PowerShell\7\pwsh.exe'
$script:MaximumManifestBytes = 262144
$script:MaximumVectorBytes = 65536
$script:MaximumStdoutBytes = 65536
$script:MaximumStderrBytes = 16384
$script:MaximumResultBytes = 32768
$script:ContractTimeoutMilliseconds = 10000
$script:HandlerTimeoutSeconds = 60.0
$script:RequiredHandlerExports = @(
    'Test-P36StorageEnvelope',
    'New-P36MachineHandlerState',
    'Invoke-P36HandlerTransition',
    'Get-P36TerminalProjection'
)
$script:ActionIds = @(
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
$script:AcceptedHashes = [ordered]@{
    $script:RunnerPath = '22F2A530C5D1CFC8109F2F3A2F8D7458A3E035A12DD7CFFF00EE49CA0E2C212A'
    $script:HandlerModulePath = '41C93756BDDFDFE55B99CC6C1308FAD5EE34E2962BA99D40B9EFEDEDDDC9A721'
    $script:WindowsAdapterParserPath = '232F21819F845E35C6D576AA499B05699033E439CB9223742C21FD08FFF262A9'
}

trap {
    [ordered]@{
        contract_id = $script:ContractId
        mode = $Mode
        terminal = $true
        succeeded = $false
        reason_code = 'sanitized_validation_failure'
        raw_fixture_retained = $false
        raw_process_output_retained = $false
        raw_exception_retained = $false
        runner_storage_invocation_count = 0
        windows_adapter_import_or_execution_count = 0
        machine_action_count = 0
        network_action_count = 0
    } | ConvertTo-Json -Compress -Depth 4
    exit 1
}

function Get-P36FileSha256 {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory = $true)]
        [string] $LiteralPath
    )

    return (Get-FileHash -LiteralPath $LiteralPath -Algorithm SHA256).Hash
}

function Assert-P36ExactBindings {
    [CmdletBinding()]
    param()

    foreach ($entry in $script:AcceptedHashes.GetEnumerator()) {
        if ((Get-P36FileSha256 -LiteralPath $entry.Key) -cne $entry.Value) {
            throw 'P36_ACCEPTED_SOURCE_BINDING_MISMATCH'
        }
    }
    if ((Get-P36FileSha256 -LiteralPath $script:HarnessPath) -cne $ExpectedHarnessSha256) {
        throw 'P36_HARNESS_BINDING_MISMATCH'
    }
    if (
        (Get-P36FileSha256 -LiteralPath $script:VectorManifestPath) -cne
        $ExpectedVectorManifestSha256
    ) {
        throw 'P36_VECTOR_MANIFEST_BINDING_MISMATCH'
    }
}

function Read-P36VectorManifest {
    [CmdletBinding()]
    param()

    $length = [System.IO.FileInfo]::new($script:VectorManifestPath).Length
    if ($length -le 0 -or $length -gt $script:MaximumManifestBytes) {
        throw 'P36_VECTOR_MANIFEST_SIZE_INVALID'
    }
    $json = [System.IO.File]::ReadAllText(
        $script:VectorManifestPath,
        [System.Text.Encoding]::UTF8
    )
    $manifest = $json | ConvertFrom-Json -Depth 64
    if (
        [int] $manifest.counts.contract -ne 20 -or
        [int] $manifest.counts.handler -ne 64 -or
        [int] $manifest.counts.total -ne 84
    ) {
        throw 'P36_VECTOR_MANIFEST_COUNT_INVALID'
    }
    return $manifest
}

function ConvertTo-P36Hashtable {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory = $true)]
        [psobject] $Value
    )

    $result = [ordered]@{}
    foreach ($property in $Value.PSObject.Properties) {
        $result[$property.Name] = $property.Value
    }
    return $result
}

function Merge-P36Fixture {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory = $true)]
        [psobject] $Base,

        [Parameter(Mandatory = $true)]
        [psobject] $Mutation
    )

    $result = ConvertTo-P36Hashtable -Value $Base
    foreach ($property in $Mutation.PSObject.Properties) {
        $result[$property.Name] = $property.Value
    }
    return $result
}

function Get-P36NamedProperty {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory = $true)]
        [psobject] $Value,

        [Parameter(Mandatory = $true)]
        [string] $Name
    )

    $property = $Value.PSObject.Properties[$Name]
    if ($null -eq $property) {
        throw 'P36_GENERATED_FIXTURE_MISSING'
    }
    return $property.Value
}

function ConvertTo-P36BoundedJson {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory = $true)]
        [object] $Value,

        [int] $MaximumBytes = $script:MaximumResultBytes
    )

    $json = $Value | ConvertTo-Json -Compress -Depth 16
    if ([System.Text.Encoding]::UTF8.GetByteCount($json) -gt $MaximumBytes) {
        throw 'P36_BOUNDED_JSON_LIMIT_EXCEEDED'
    }
    return $json
}

function Invoke-P36ParserLayer {
    [CmdletBinding()]
    param()

    $targets = @(
        [ordered]@{ role = 'runner'; path = $script:RunnerPath },
        [ordered]@{ role = 'pure_handler'; path = $script:HandlerModulePath },
        [ordered]@{ role = 'windows_adapter_parser_only'; path = $script:WindowsAdapterParserPath },
        [ordered]@{ role = 'validation_harness'; path = $script:HarnessPath }
    )
    $results = @()
    foreach ($target in $targets) {
        $tokens = $null
        $errors = $null
        [void] [System.Management.Automation.Language.Parser]::ParseFile(
            $target.path,
            [ref] $tokens,
            [ref] $errors
        )
        $results += [ordered]@{
            role = $target.role
            sha256 = Get-P36FileSha256 -LiteralPath $target.path
            parse_success = @($errors).Count -eq 0
            error_count = @($errors).Count
        }
    }

    return [ordered]@{
        layer_id = 'GV-R1-L1-PARSER'
        file_count = $results.Count
        error_count = [int] (@($results | ForEach-Object { $_.error_count }) | Measure-Object -Sum).Sum
        files = $results
        source_execution_count = 0
        windows_adapter_import_or_execution_count = 0
    }
}

function Invoke-P36BoundedContractChild {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory = $true)]
        [hashtable] $Fixture
    )

    $fixtureJson = ConvertTo-P36BoundedJson -Value $Fixture -MaximumBytes $script:MaximumVectorBytes
    $startInfo = [System.Diagnostics.ProcessStartInfo]::new()
    $startInfo.FileName = $script:RuntimePath
    $startInfo.UseShellExecute = $false
    $startInfo.RedirectStandardOutput = $true
    $startInfo.RedirectStandardError = $true
    $startInfo.CreateNoWindow = $true
    [void] $startInfo.ArgumentList.Add('-NoLogo')
    [void] $startInfo.ArgumentList.Add('-NoProfile')
    [void] $startInfo.ArgumentList.Add('-NonInteractive')
    [void] $startInfo.ArgumentList.Add('-File')
    [void] $startInfo.ArgumentList.Add($script:RunnerPath)
    [void] $startInfo.ArgumentList.Add('-Mode')
    [void] $startInfo.ArgumentList.Add('Contract')
    [void] $startInfo.ArgumentList.Add('-ContractVectorJson')
    [void] $startInfo.ArgumentList.Add($fixtureJson)

    $process = [System.Diagnostics.Process]::new()
    $process.StartInfo = $startInfo
    if (-not $process.Start()) {
        throw 'P36_CONTRACT_CHILD_START_FAILED'
    }
    $stdoutTask = $process.StandardOutput.ReadToEndAsync()
    $stderrTask = $process.StandardError.ReadToEndAsync()
    if (-not $process.WaitForExit($script:ContractTimeoutMilliseconds)) {
        $process.Kill($true)
        [void] $process.WaitForExit(2000)
        throw 'P36_CONTRACT_CHILD_TIMEOUT'
    }
    $stdout = $stdoutTask.GetAwaiter().GetResult()
    $stderr = $stderrTask.GetAwaiter().GetResult()
    if ([System.Text.Encoding]::UTF8.GetByteCount($stdout) -gt $script:MaximumStdoutBytes) {
        throw 'P36_CONTRACT_STDOUT_LIMIT_EXCEEDED'
    }
    if ([System.Text.Encoding]::UTF8.GetByteCount($stderr) -gt $script:MaximumStderrBytes) {
        throw 'P36_CONTRACT_STDERR_LIMIT_EXCEEDED'
    }
    if ($process.ExitCode -ne 0 -or -not [string]::IsNullOrWhiteSpace($stderr)) {
        throw 'P36_CONTRACT_CHILD_FAILED'
    }
    return $stdout | ConvertFrom-Json -Depth 8
}

function Invoke-P36ContractLayer {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory = $true)]
        [psobject] $Manifest
    )

    $passed = 0
    $failed = 0
    foreach ($vector in $Manifest.contract_vectors) {
        $fixture = Merge-P36Fixture -Base $Manifest.contract_base_fixture -Mutation $vector.mutation
        $actual = Invoke-P36BoundedContractChild -Fixture $fixture
        $matches = (
            [string] $actual.outcome -ceq [string] $vector.expected.outcome -and
            [bool] $actual.machine_accessed -eq $false -and
            [bool] $actual.runner_execution_authorized -eq $false -and
            [bool] $actual.storage_attempt_authorized -eq $false
        )
        if ($matches) { $passed += 1 } else { $failed += 1 }
        $fixture = $null
        $actual = $null
    }
    return [ordered]@{
        layer_id = 'GV-R1-L2-CONTRACT'
        required = 20
        passed = $passed
        failed = $failed
        runner_contract_invocation_count = $passed + $failed
        runner_storage_invocation_count = 0
        machine_action_count = 0
        raw_fixture_retained = $false
        raw_process_output_retained = $false
    }
}

function Invoke-P36GeneratedActionCase {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory = $true)]
        [psobject] $Manifest,

        [Parameter(Mandatory = $true)]
        [psobject] $Vector
    )

    $targetIndex = [Array]::IndexOf($script:ActionIds, [string] $Vector.action_id)
    if ($targetIndex -lt 0) {
        throw 'P36_HANDLER_VECTOR_ACTION_INVALID'
    }
    $state = New-P36MachineHandlerState
    $decision = $null
    for ($index = 0; $index -le $targetIndex; $index++) {
        $actionId = $script:ActionIds[$index]
        $base = Get-P36NamedProperty -Value $Manifest.handler_base_transcripts -Name $actionId
        $mutation = if ($index -eq $targetIndex) { $Vector.mutation } else { [pscustomobject]@{} }
        $adapterResult = Merge-P36Fixture -Base $base -Mutation $mutation
        $monotonic = 100.0 + [double] $index
        $decision = Invoke-P36HandlerTransition `
            -State $state `
            -ActionId $actionId `
            -AdapterResult $adapterResult `
            -MonotonicSeconds $monotonic
        $adapterResult = $null
        if ($index -lt $targetIndex -and -not [bool] $decision.succeeded) {
            throw 'P36_HANDLER_PREFIX_FAILED'
        }
    }

    $expectedSucceeded = [string] $Vector.expected.outcome -ceq 'passed'
    $projection = Get-P36TerminalProjection -State $state
    $expectedTerminal = (-not $expectedSucceeded) -or ($targetIndex -eq 9)
    $matches = (
        [bool] $decision.succeeded -eq $expectedSucceeded -and
        [string] $decision.reason_code -ceq [string] $Vector.expected.reason_code -and
        [bool] $projection.terminal -eq $expectedTerminal -and
        -not [bool] $projection.automatic_retry_authorized -and
        -not [bool] $projection.execution_authorized -and
        -not [bool] $projection.profile_activation_authorized -and
        -not [bool] $projection.deployment_authorized -and
        -not [bool] $projection.remote_git_authorized
    )
    foreach ($field in @(
        'root_created_by_attempt',
        'probe_partial_created_by_attempt',
        'probe_verified_created_by_attempt',
        'cleanup_required',
        'manual_review_required'
    )) {
        $expectedProperty = $Vector.expected.PSObject.Properties[$field]
        if ($null -ne $expectedProperty) {
            $matches = $matches -and (
                [bool] $decision.$field -eq [bool] $expectedProperty.Value
            )
        }
    }
    return $matches
}

function New-P36GeneratedEnvelope {
    [CmdletBinding()]
    param()

    return [ordered]@{
        owner_statement_exact_match = $true
        authorization_window_current = $true
        attempt_unused = $true
        execution_package_binding_exact = $true
        source_bindings_exact = $true
        runtime_binding_exact = $true
        logical_node_id = 'LAB-LAPTOP-01'
        candidate_volume = 'F:'
        candidate_root = 'F:\HCAM-Quarantine'
        action_ids = @($script:ActionIds)
        output_paths = @(
            'contracts/phase-3/p3-6-quarantine-storage-r2-authorization.json',
            'contracts/phase-3/p3-6-quarantine-storage-r2-result.json',
            'contracts/phase-3/p3-6-quarantine-storage-r2-evidence.json'
        )
        probe_bytes = 4096
        per_action_timeout_seconds = 30
        total_timeout_seconds = 120
    }
}

function Invoke-P36GeneratedCrossCase {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory = $true)]
        [psobject] $Manifest,

        [Parameter(Mandatory = $true)]
        [psobject] $Vector,

        [Parameter(Mandatory = $true)]
        [string] $HandlerSourceText,

        [Parameter(Mandatory = $true)]
        [string] $HarnessSourceText
    )

    switch -CaseSensitive ([string] $Vector.scenario) {
        'invalid_envelope_action_plan' {
            $envelope = New-P36GeneratedEnvelope
            $envelope.action_ids = @($script:ActionIds[0..8]) + @('U3K-A99-UNKNOWN')
            $decision = Test-P36StorageEnvelope -Request $envelope
            return (-not [bool] $decision.succeeded -and [string] $decision.reason_code -ceq 'action_plan_invalid')
        }
        'out_of_order_transition' {
            $state = New-P36MachineHandlerState
            $base = Get-P36NamedProperty -Value $Manifest.handler_base_transcripts -Name $script:ActionIds[1]
            $decision = Invoke-P36HandlerTransition -State $state -ActionId $script:ActionIds[1] -AdapterResult (ConvertTo-P36Hashtable -Value $base) -MonotonicSeconds 100.0
            return (-not [bool] $decision.succeeded -and [string] $decision.reason_code -ceq 'action_out_of_order')
        }
        'transaction_timeout' {
            $state = New-P36MachineHandlerState
            $a01 = Get-P36NamedProperty -Value $Manifest.handler_base_transcripts -Name $script:ActionIds[0]
            $a02 = Get-P36NamedProperty -Value $Manifest.handler_base_transcripts -Name $script:ActionIds[1]
            [void] (Invoke-P36HandlerTransition -State $state -ActionId $script:ActionIds[0] -AdapterResult (ConvertTo-P36Hashtable -Value $a01) -MonotonicSeconds 100.0)
            $decision = Invoke-P36HandlerTransition -State $state -ActionId $script:ActionIds[1] -AdapterResult (ConvertTo-P36Hashtable -Value $a02) -MonotonicSeconds 221.0
            return (-not [bool] $decision.succeeded -and [string] $decision.reason_code -ceq 'transaction_timeout')
        }
        'bounded_cleanup_flags' {
            $probe = @(
                $Manifest.handler_vectors | Where-Object {
                    [string] $_.vector_id -ceq
                    'A09_V04_flush_true_failure_blocks_and_enters_bounded_cleanup'
                }
            )
            if ($probe.Count -ne 1) {
                throw 'P36_CLEANUP_VECTOR_MISSING'
            }
            return (Invoke-P36GeneratedActionCase -Manifest $Manifest -Vector $probe[0])
        }
        'sanitized_projection' {
            $state = New-P36MachineHandlerState
            $projection = Get-P36TerminalProjection -State $state
            $names = @($projection.Keys)
            return (@($names | Where-Object { $_ -match 'raw|stack|stdout|stderr|identity|descriptor|content' }).Count -eq 0)
        }
        'forbidden_surfaces_absent' {
            return (
                @(
                    $Manifest.handler_forbidden_source_tokens | Where-Object {
                        $HandlerSourceText.Contains([string] $_)
                    }
                ).Count -eq 0
            )
        }
        'adapter_not_imported' {
            return (
                $HarnessSourceText.Contains('windows_adapter_parser_only') -and
                @(
                    Get-Module | Where-Object {
                        $_.Path -ceq $script:WindowsAdapterParserPath
                    }
                ).Count -eq 0
            )
        }
        'terminal_authority_false' {
            $state = New-P36MachineHandlerState
            $base = Get-P36NamedProperty -Value $Manifest.handler_base_transcripts -Name $script:ActionIds[1]
            [void] (Invoke-P36HandlerTransition -State $state -ActionId $script:ActionIds[1] -AdapterResult (ConvertTo-P36Hashtable -Value $base) -MonotonicSeconds 100.0)
            $projection = Get-P36TerminalProjection -State $state
            return (
                [bool] $projection.terminal -and
                -not [bool] $projection.automatic_retry_authorized -and
                -not [bool] $projection.execution_authorized -and
                -not [bool] $projection.profile_activation_authorized -and
                -not [bool] $projection.deployment_authorized -and
                -not [bool] $projection.remote_git_authorized
            )
        }
        default { throw 'P36_CROSS_VECTOR_SCENARIO_INVALID' }
    }
}

function Invoke-P36HandlerLayer {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory = $true)]
        [psobject] $Manifest
    )

    Import-Module `
        -Name $script:HandlerModulePath `
        -Scope Local `
        -Function $script:RequiredHandlerExports `
        -NoClobber `
        -ErrorAction Stop
    $exported = @((Get-Module | Where-Object { $_.Path -ceq $script:HandlerModulePath }).ExportedFunctions.Keys | Sort-Object)
    if ((Compare-Object -CaseSensitive ($script:RequiredHandlerExports | Sort-Object) $exported).Count -ne 0) {
        throw 'P36_HANDLER_EXPORT_SET_INVALID'
    }

    $handlerText = [System.IO.File]::ReadAllText($script:HandlerModulePath, [System.Text.Encoding]::UTF8)
    $harnessText = [System.IO.File]::ReadAllText($script:HarnessPath, [System.Text.Encoding]::UTF8)
    $started = [System.Diagnostics.Stopwatch]::StartNew()
    $passed = 0
    $failed = 0
    foreach ($vector in $Manifest.handler_vectors) {
        if ($started.Elapsed.TotalSeconds -gt $script:HandlerTimeoutSeconds) {
            throw 'P36_HANDLER_LAYER_TIMEOUT'
        }
        $matches = if ([string] $vector.kind -ceq 'action') {
            Invoke-P36GeneratedActionCase -Manifest $Manifest -Vector $vector
        } else {
            Invoke-P36GeneratedCrossCase -Manifest $Manifest -Vector $vector -HandlerSourceText $handlerText -HarnessSourceText $harnessText
        }
        if ($matches) { $passed += 1 } else { $failed += 1 }
    }
    $handlerText = $null
    $harnessText = $null

    return [ordered]@{
        layer_id = 'GV-R1-L3-PURE-HANDLERS'
        required = 64
        passed = $passed
        failed = $failed
        pure_handler_import_count = 1
        windows_adapter_import_or_execution_count = 0
        machine_action_count = 0
        raw_fixture_retained = $false
        raw_exception_retained = $false
    }
}

Assert-P36ExactBindings
$manifest = Read-P36VectorManifest
$result = switch -CaseSensitive ($Mode) {
    'Parse' { Invoke-P36ParserLayer; break }
    'Contract' { Invoke-P36ContractLayer -Manifest $manifest; break }
    'Handler' { Invoke-P36HandlerLayer -Manifest $manifest; break }
    'Aggregate' {
        $parser = Invoke-P36ParserLayer
        $contract = Invoke-P36ContractLayer -Manifest $manifest
        $handler = Invoke-P36HandlerLayer -Manifest $manifest
        $passed = [int] $contract.passed + [int] $handler.passed
        [ordered]@{
            contract_id = $script:ContractId
            mode = 'Aggregate'
            terminal = $true
            succeeded = (
                [int] $parser.error_count -eq 0 -and
                [int] $contract.failed -eq 0 -and
                [int] $handler.failed -eq 0 -and
                $passed -eq 84
            )
            reason_code = if ($passed -eq 84) { 'ok' } else { 'generated_validation_failed' }
            parser_file_count = [int] $parser.file_count
            parser_error_count = [int] $parser.error_count
            generated_vectors_required = 84
            generated_vectors_passed = $passed
            generated_vectors_failed = [int] $contract.failed + [int] $handler.failed
            runner_contract_invocation_count = [int] $contract.runner_contract_invocation_count
            runner_storage_invocation_count = 0
            pure_handler_import_count = 1
            windows_adapter_import_or_execution_count = 0
            machine_action_count = 0
            network_action_count = 0
            raw_fixture_retained = $false
            raw_process_output_retained = $false
            raw_exception_retained = $false
            automatic_retry_authorized = $false
            storage_attempt_authorized = $false
            deployment_authorized = $false
            remote_git_authorized = $false
        }
        break
    }
    default { throw 'P36_VALIDATION_MODE_INVALID' }
}

ConvertTo-P36BoundedJson -Value $result
