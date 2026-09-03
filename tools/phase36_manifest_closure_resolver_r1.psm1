Set-StrictMode -Version Latest

$script:ContractVersion = '1.1.0'
$script:Operation = 'resolve_manifest_closure_v1'
$script:MaximumEntries = 64
$script:MaximumFileBytes = 67108864
$script:MaximumTotalBytes = 134217728
$script:MaximumReferenceCharacters = 260
$script:Fields = @(
    'RootModule',
    'NestedModules',
    'RequiredAssemblies',
    'ScriptsToProcess',
    'TypesToProcess',
    'FormatsToProcess',
    'FileList'
)
$script:FallbackFields = @('NestedModules', 'RequiredAssemblies')
$script:CodeExtensions = @('.cdxml', '.dll', '.exe', '.ps1', '.psd1', '.psm1')
$script:ReasonCodes = @(
    'manifest_closure_accepted',
    'resolver_input_invalid',
    'manifest_path_context_invalid',
    'manifest_entry_count_exceeded',
    'manifest_field_unsupported',
    'scripts_to_process_forbidden',
    'manifest_reference_forbidden',
    'manifest_reference_escape',
    'manifest_observation_invalid',
    'manifest_candidate_ambiguous',
    'load_bearing_target_missing',
    'load_bearing_target_invalid',
    'load_bearing_target_untrusted',
    'filelist_code_target_missing',
    'duplicate_canonical_target',
    'aggregate_file_bytes_exceeded'
)

function Get-HcamManifestClosureCanonicalProjection {
    [CmdletBinding()]
    param()

    [ordered]@{
        bases = @('manifest_directory', 'ps_home')
        code_extensions = @($script:CodeExtensions)
        contract_version = $script:ContractVersion
        fields = @($script:Fields)
        fallback_fields = @($script:FallbackFields)
        maximum_entries = $script:MaximumEntries
        maximum_file_bytes = $script:MaximumFileBytes
        maximum_reference_characters = $script:MaximumReferenceCharacters
        maximum_total_bytes = $script:MaximumTotalBytes
        operation = $script:Operation
        reason_codes = @($script:ReasonCodes)
    }
}

function New-HcamManifestClosureTerminal {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory)]
        [ValidateSet(
            'manifest_closure_accepted',
            'resolver_input_invalid',
            'manifest_path_context_invalid',
            'manifest_entry_count_exceeded',
            'manifest_field_unsupported',
            'scripts_to_process_forbidden',
            'manifest_reference_forbidden',
            'manifest_reference_escape',
            'manifest_observation_invalid',
            'manifest_candidate_ambiguous',
            'load_bearing_target_missing',
            'load_bearing_target_invalid',
            'load_bearing_target_untrusted',
            'filelist_code_target_missing',
            'duplicate_canonical_target',
            'aggregate_file_bytes_exceeded'
        )]
        [string]$ReasonCode,

        [Parameter(Mandatory)]
        [hashtable]$Counts,

        [string]$FieldClass = 'none',

        [string]$BaseClass = 'none'
    )

    [ordered]@{
        contract_version = $script:ContractVersion
        terminal = $true
        succeeded = $ReasonCode -eq 'manifest_closure_accepted'
        reason_code = $ReasonCode
        failing_field_class = $FieldClass
        candidate_base_class = $BaseClass
        counts = [ordered]@{
            declared_entries = [int]$Counts.declared_entries
            load_bearing_entries = [int]$Counts.load_bearing_entries
            inventory_entries = [int]$Counts.inventory_entries
            selected_targets = [int]$Counts.selected_targets
            missing_inventory_entries = [int]$Counts.missing_inventory_entries
            selected_total_bytes = [long]$Counts.selected_total_bytes
        }
        retention = [ordered]@{
            raw_path_or_reference_retained = $false
            manifest_text_or_parser_token_retained = $false
            exception_or_security_material_retained = $false
        }
    }
}

function Get-HcamCanonicalWindowsPath {
    [CmdletBinding()]
    param([Parameter(Mandatory)][string]$Path)

    [System.IO.Path]::GetFullPath($Path).TrimEnd('\').ToLowerInvariant()
}

function Test-HcamContainedPath {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory)][string]$Candidate,
        [Parameter(Mandatory)][string]$Root
    )

    $candidateCanonical = Get-HcamCanonicalWindowsPath -Path $Candidate
    $rootCanonical = Get-HcamCanonicalWindowsPath -Path $Root
    $candidateCanonical -eq $rootCanonical -or
        $candidateCanonical.StartsWith($rootCanonical + '\', [System.StringComparison]::OrdinalIgnoreCase)
}

function Test-HcamManifestReferenceForbidden {
    [CmdletBinding()]
    param([AllowNull()][object]$Value)

    if ($Value -isnot [string] -or [string]::IsNullOrWhiteSpace($Value)) { return $true }
    if ($Value.Length -gt $script:MaximumReferenceCharacters) { return $true }
    if ([System.IO.Path]::IsPathRooted($Value)) { return $true }
    if ($Value -match '^[A-Za-z][A-Za-z0-9+.-]*:' -or $Value -match '[*?\[\]$%`{}()''"]') { return $true }
    @($Value -split '[\\/]') -contains '..'
}

function Get-HcamManifestCandidates {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory)][string]$Field,
        [Parameter(Mandatory)][string]$Value,
        [Parameter(Mandatory)][string]$ManifestDirectory,
        [Parameter(Mandatory)][string]$PSHome
    )

    $result = @(
        [ordered]@{
            base = 'manifest_directory'
            candidate_path = Get-HcamCanonicalWindowsPath -Path ([System.IO.Path]::Combine($ManifestDirectory, $Value))
        }
    )
    $isBare = -not $Value.Contains('\') -and -not $Value.Contains('/')
    $extension = [System.IO.Path]::GetExtension($Value).ToLowerInvariant()
    if ($script:FallbackFields -contains $Field -and $isBare -and $script:CodeExtensions -contains $extension) {
        $result += [ordered]@{
            base = 'ps_home'
            candidate_path = Get-HcamCanonicalWindowsPath -Path ([System.IO.Path]::Combine($PSHome, $Value))
        }
    }
    @($result)
}

function Invoke-HcamManifestClosurePolicy {
    [CmdletBinding()]
    param([Parameter(Mandatory)][hashtable]$Request)

    $counts = @{
        declared_entries = 0
        load_bearing_entries = 0
        inventory_entries = 0
        selected_targets = 0
        missing_inventory_entries = 0
        selected_total_bytes = 0L
    }
    try {
        $requiredRequestFields = @(
            'contract_version', 'operation', 'manifest_directory', 'module_root',
            'ps_home', 'entries', 'observations'
        )
        if (@($Request.Keys).Count -ne $requiredRequestFields.Count -or
            @($requiredRequestFields | Where-Object { -not $Request.ContainsKey($_) }).Count -ne 0 -or
            $Request.contract_version -ne $script:ContractVersion -or
            $Request.operation -ne $script:Operation) {
            return New-HcamManifestClosureTerminal -ReasonCode resolver_input_invalid -Counts $counts
        }

        $manifestDirectory = Get-HcamCanonicalWindowsPath -Path ([string]$Request.manifest_directory)
        $moduleRoot = Get-HcamCanonicalWindowsPath -Path ([string]$Request.module_root)
        $psHome = Get-HcamCanonicalWindowsPath -Path ([string]$Request.ps_home)
        if (-not (Test-HcamContainedPath -Candidate $manifestDirectory -Root $moduleRoot) -or
            -not (Test-HcamContainedPath -Candidate $moduleRoot -Root $psHome)) {
            return New-HcamManifestClosureTerminal -ReasonCode manifest_path_context_invalid -Counts $counts
        }

        $entries = @($Request.entries)
        $counts.declared_entries = $entries.Count
        if ($entries.Count -gt $script:MaximumEntries) {
            return New-HcamManifestClosureTerminal -ReasonCode manifest_entry_count_exceeded -Counts $counts
        }
        $selected = [System.Collections.Generic.HashSet[string]]::new([System.StringComparer]::OrdinalIgnoreCase)
        for ($index = 0; $index -lt $entries.Count; $index++) {
            $entry = $entries[$index]
            $field = [string]$entry.field
            $value = $entry.value
            if ($script:Fields -notcontains $field) {
                return New-HcamManifestClosureTerminal -ReasonCode manifest_field_unsupported -Counts $counts
            }
            if ($field -eq 'ScriptsToProcess') {
                return New-HcamManifestClosureTerminal -ReasonCode scripts_to_process_forbidden -Counts $counts -FieldClass script
            }
            if (Test-HcamManifestReferenceForbidden -Value $value) {
                return New-HcamManifestClosureTerminal -ReasonCode manifest_reference_forbidden -Counts $counts -FieldClass $field
            }
            if ($field -eq 'FileList') { $counts.inventory_entries++ } else { $counts.load_bearing_entries++ }

            $candidates = @(Get-HcamManifestCandidates -Field $field -Value $value -ManifestDirectory $manifestDirectory -PSHome $psHome)
            $present = @()
            foreach ($candidate in $candidates) {
                $root = if ($candidate.base -eq 'ps_home') { $psHome } else { $moduleRoot }
                if (-not (Test-HcamContainedPath -Candidate $candidate.candidate_path -Root $root) -or
                    -not (Test-HcamContainedPath -Candidate $candidate.candidate_path -Root $psHome)) {
                    return New-HcamManifestClosureTerminal -ReasonCode manifest_reference_escape -Counts $counts -FieldClass $field -BaseClass $candidate.base
                }
                $matches = @($Request.observations | Where-Object {
                    [int]$_.entry_index -eq $index -and
                    [string]$_.base -eq [string]$candidate.base -and
                    (Get-HcamCanonicalWindowsPath -Path ([string]$_.candidate_path)) -eq [string]$candidate.candidate_path
                })
                if ($matches.Count -ne 1) {
                    return New-HcamManifestClosureTerminal -ReasonCode manifest_observation_invalid -Counts $counts -FieldClass $field -BaseClass $candidate.base
                }
                if ([bool]$matches[0].present) { $present += $matches[0] }
            }
            if ($present.Count -gt 1) {
                return New-HcamManifestClosureTerminal -ReasonCode manifest_candidate_ambiguous -Counts $counts -FieldClass $field -BaseClass multiple
            }
            if ($present.Count -eq 0) {
                $extension = [System.IO.Path]::GetExtension([string]$value).ToLowerInvariant()
                if ($field -eq 'FileList' -and $script:CodeExtensions -notcontains $extension) {
                    $counts.missing_inventory_entries++
                    continue
                }
                $reason = if ($field -eq 'FileList') { 'filelist_code_target_missing' } else { 'load_bearing_target_missing' }
                return New-HcamManifestClosureTerminal -ReasonCode $reason -Counts $counts -FieldClass $field
            }
            $item = $present[0]
            if (-not [bool]$item.regular -or -not [bool]$item.nonreparse -or [long]$item.size_bytes -gt $script:MaximumFileBytes) {
                return New-HcamManifestClosureTerminal -ReasonCode load_bearing_target_invalid -Counts $counts -FieldClass $field -BaseClass $item.base
            }
            if (-not [bool]$item.trusted) {
                return New-HcamManifestClosureTerminal -ReasonCode load_bearing_target_untrusted -Counts $counts -FieldClass $field -BaseClass $item.base
            }
            $canonical = Get-HcamCanonicalWindowsPath -Path ([string]$item.candidate_path)
            if (-not $selected.Add($canonical)) {
                return New-HcamManifestClosureTerminal -ReasonCode duplicate_canonical_target -Counts $counts -FieldClass $field -BaseClass $item.base
            }
            $counts.selected_targets++
            $counts.selected_total_bytes += [long]$item.size_bytes
            if ($counts.selected_total_bytes -gt $script:MaximumTotalBytes) {
                return New-HcamManifestClosureTerminal -ReasonCode aggregate_file_bytes_exceeded -Counts $counts -FieldClass $field -BaseClass $item.base
            }
        }
        New-HcamManifestClosureTerminal -ReasonCode manifest_closure_accepted -Counts $counts
    }
    catch {
        New-HcamManifestClosureTerminal -ReasonCode resolver_input_invalid -Counts $counts
    }
}

Export-ModuleMember -Function @(
    'Get-HcamManifestClosureCanonicalProjection',
    'Get-HcamManifestCandidates',
    'Invoke-HcamManifestClosurePolicy'
)
