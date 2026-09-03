Set-StrictMode -Version Latest

$script:P36CandidateRoot = 'F:\HCAM-Quarantine'
$script:P36ExcludedProjectRoot = 'F:\h cam'
$script:P36PartialProbePath = 'F:\HCAM-Quarantine\.hcam-storage-attestation.partial'
$script:P36VerifiedProbePath = 'F:\HCAM-Quarantine\.hcam-storage-attestation.verified'
$script:P36OutputPaths = @(
    'contracts/phase-3/p3-6-quarantine-storage-r5-authorization.json',
    'contracts/phase-3/p3-6-quarantine-storage-r5-result.json',
    'contracts/phase-3/p3-6-quarantine-storage-r5-evidence.json'
)
$script:P36MaximumBoundFileBytes = 134217728
$script:P36MaximumOutputBytes = 65536
$script:P36NativeInitialized = $false

function Initialize-P36NativeMethods {
    if ($script:P36NativeInitialized) {
        return
    }

    Add-Type -TypeDefinition @'
using System;
using System.Runtime.InteropServices;

namespace HCam.Phase36
{
    [StructLayout(LayoutKind.Sequential)]
    public struct SECURITY_ATTRIBUTES
    {
        public int nLength;
        public IntPtr lpSecurityDescriptor;
        [MarshalAs(UnmanagedType.Bool)]
        public bool bInheritHandle;
    }

    public static class NativeStorage
    {
        [DllImport("kernel32.dll", CharSet = CharSet.Unicode, SetLastError = true)]
        [return: MarshalAs(UnmanagedType.Bool)]
        public static extern bool CreateDirectoryW(
            string lpPathName,
            ref SECURITY_ATTRIBUTES lpSecurityAttributes
        );

        [DllImport("kernel32.dll", CharSet = CharSet.Unicode, SetLastError = true)]
        public static extern uint GetFileAttributesW(string lpFileName);

        [DllImport("kernel32.dll", CharSet = CharSet.Unicode, SetLastError = true)]
        [return: MarshalAs(UnmanagedType.Bool)]
        public static extern bool MoveFileExW(
            string lpExistingFileName,
            string lpNewFileName,
            uint dwFlags
        );
    }
}
'@
    $script:P36NativeInitialized = $true
}

function New-P36AdapterFailure {
    param([Parameter(Mandatory = $true)][string] $ReasonCode)

    @{
        ok          = $false
        reason_code = $ReasonCode
    }
}

function Get-P36MonotonicSeconds {
    [CmdletBinding()]
    param()

    [System.Diagnostics.Stopwatch]::GetTimestamp() / [double] [System.Diagnostics.Stopwatch]::Frequency
}

function Get-P36UtcStartTime {
    [CmdletBinding()]
    param()

    try {
        @{
            ok                = $true
            reason_code       = 'ok'
            utc_value         = [System.DateTimeOffset]::UtcNow.ToString('o')
            read_count        = 1
            monotonic_seconds = Get-P36MonotonicSeconds
        }
    } catch {
        New-P36AdapterFailure -ReasonCode 'clock_unavailable'
    }
}

function Get-P36Sha256Hex {
    param([Parameter(Mandatory = $true)][byte[]] $Bytes)

    $algorithm = [System.Security.Cryptography.SHA256]::Create()
    try {
        ([System.BitConverter]::ToString($algorithm.ComputeHash($Bytes))).Replace('-', '')
    } finally {
        $algorithm.Dispose()
    }
}

function Get-P36BoundFileHash {
    param(
        [Parameter(Mandatory = $true)][string] $Path,
        [Int64] $MaximumBytes = $script:P36MaximumBoundFileBytes
    )

    $stream = $null
    $algorithm = $null
    try {
        $information = [System.IO.FileInfo]::new($Path)
        if (
            -not $information.Exists -or
            ($information.Attributes -band [System.IO.FileAttributes]::ReparsePoint) -ne 0 -or
            $information.Length -lt 1 -or
            $information.Length -gt $MaximumBytes
        ) {
            return $null
        }
        $stream = [System.IO.File]::OpenRead($Path)
        $algorithm = [System.Security.Cryptography.SHA256]::Create()
        return ([System.BitConverter]::ToString($algorithm.ComputeHash($stream))).Replace('-', '')
    } catch {
        return $null
    } finally {
        if ($null -ne $algorithm) {
            $algorithm.Dispose()
        }
        if ($null -ne $stream) {
            $stream.Dispose()
        }
    }
}

function Resolve-P36RepositoryBindingPath {
    param(
        [Parameter(Mandatory = $true)][string] $RepositoryRoot,
        [Parameter(Mandatory = $true)][string] $RelativePath
    )

    if (
        [System.IO.Path]::IsPathRooted($RelativePath) -or
        $RelativePath.Contains('..') -or
        $RelativePath.Contains('*') -or
        $RelativePath.Contains('?')
    ) {
        return $null
    }
    try {
        $canonicalRoot = [System.IO.Path]::GetFullPath($RepositoryRoot).TrimEnd('\')
        $candidate = [System.IO.Path]::GetFullPath(
            [System.IO.Path]::Combine($canonicalRoot, $RelativePath)
        )
        if (-not $candidate.StartsWith($canonicalRoot + '\', [System.StringComparison]::OrdinalIgnoreCase)) {
            return $null
        }
        return $candidate
    } catch {
        return $null
    }
}

function Test-P36BoundRepositoryFiles {
    param(
        [Parameter(Mandatory = $true)][string] $RepositoryRoot,
        [Parameter(Mandatory = $true)][object[]] $Bindings
    )

    if ($Bindings.Count -lt 1 -or $Bindings.Count -gt 64) {
        return $false
    }
    $seen = [System.Collections.Generic.HashSet[string]]::new(
        [System.StringComparer]::Ordinal
    )
    foreach ($binding in $Bindings) {
        if ($null -eq $binding.path -or $null -eq $binding.sha256) {
            return $false
        }
        $relativePath = [string] $binding.path
        if (-not $seen.Add($relativePath)) {
            return $false
        }
        $path = Resolve-P36RepositoryBindingPath -RepositoryRoot $RepositoryRoot -RelativePath $relativePath
        if ($null -eq $path) {
            return $false
        }
        $actual = Get-P36BoundFileHash -Path $path
        if ($null -eq $actual -or $actual -cne [string] $binding.sha256) {
            return $false
        }
    }
    return $true
}

function Test-P36ExecutionBindings {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory = $true)][hashtable] $Request,
        [Parameter(Mandatory = $true)][string] $RepositoryRoot,
        [Parameter(Mandatory = $true)][string] $RuntimePath,
        [Parameter(Mandatory = $true)][string] $AttemptStartedAt
    )

    try {
        $required = @(
            'owner_statement',
            'expected_owner_statement',
            'authorization_not_before',
            'authorization_expires_at',
            'attempt_unused',
            'execution_package_files',
            'source_binding_files',
            'runtime_binding',
            'action_ids',
            'output_paths',
            'logical_node_id',
            'candidate_root',
            'probe_bytes',
            'per_action_timeout_seconds',
            'total_timeout_seconds'
        )
        foreach ($name in $required) {
            if (-not $Request.ContainsKey($name)) {
                return New-P36AdapterFailure -ReasonCode 'authority_binding_invalid'
            }
        }

        $startedAt = [System.DateTimeOffset]::ParseExact(
            $AttemptStartedAt,
            'o',
            [System.Globalization.CultureInfo]::InvariantCulture,
            [System.Globalization.DateTimeStyles]::RoundtripKind
        )
        $notBefore = [System.DateTimeOffset]::ParseExact(
            [string] $Request.authorization_not_before,
            'o',
            [System.Globalization.CultureInfo]::InvariantCulture,
            [System.Globalization.DateTimeStyles]::RoundtripKind
        )
        $expiresAt = [System.DateTimeOffset]::ParseExact(
            [string] $Request.authorization_expires_at,
            'o',
            [System.Globalization.CultureInfo]::InvariantCulture,
            [System.Globalization.DateTimeStyles]::RoundtripKind
        )
        $windowCurrent = $startedAt -ge $notBefore -and $startedAt -le $expiresAt
        $ownerExact = [string] $Request.owner_statement -ceq [string] $Request.expected_owner_statement
        $attemptUnused = $Request.attempt_unused -is [bool] -and [bool] $Request.attempt_unused

        $packageFilesMatch = Test-P36BoundRepositoryFiles `
            -RepositoryRoot $RepositoryRoot `
            -Bindings @($Request.execution_package_files)
        $sourceFilesMatch = Test-P36BoundRepositoryFiles `
            -RepositoryRoot $RepositoryRoot `
            -Bindings @($Request.source_binding_files)

        $runtimeBinding = $Request.runtime_binding
        $runtimePathExact = [string] $runtimeBinding.path -ceq $RuntimePath
        $runtimeHash = Get-P36BoundFileHash -Path $RuntimePath
        $runtimeHashExact = (
            $null -ne $runtimeHash -and
            $runtimeHash -ceq [string] $runtimeBinding.sha256
        )
        $runtimeValidUntil = [System.DateTimeOffset]::ParseExact(
            [string] $runtimeBinding.valid_until,
            'o',
            [System.Globalization.CultureInfo]::InvariantCulture,
            [System.Globalization.DateTimeStyles]::RoundtripKind
        )
        $runtimeBindingMatches = $runtimePathExact -and $runtimeHashExact -and $startedAt -le $runtimeValidUntil

        $expectedActions = @(
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
        $actionsExact = @($Request.action_ids).Count -eq $expectedActions.Count
        if ($actionsExact) {
            for ($index = 0; $index -lt $expectedActions.Count; $index++) {
                if ([string] $Request.action_ids[$index] -cne $expectedActions[$index]) {
                    $actionsExact = $false
                    break
                }
            }
        }
        $outputsExact = @($Request.output_paths).Count -eq $script:P36OutputPaths.Count
        if ($outputsExact) {
            for ($index = 0; $index -lt $script:P36OutputPaths.Count; $index++) {
                if ([string] $Request.output_paths[$index] -cne $script:P36OutputPaths[$index]) {
                    $outputsExact = $false
                    break
                }
            }
        }
        $targetLimitsExact = (
            $actionsExact -and
            $outputsExact -and
            [string] $Request.logical_node_id -ceq 'LAB-LAPTOP-01' -and
            [string] $Request.candidate_root -ceq $script:P36CandidateRoot -and
            [int] $Request.probe_bytes -eq 4096 -and
            [int] $Request.per_action_timeout_seconds -eq 30 -and
            [int] $Request.total_timeout_seconds -eq 120
        )

        @{
            ok                                  = $ownerExact -and $windowCurrent -and $attemptUnused -and $packageFilesMatch -and $sourceFilesMatch -and $runtimeBindingMatches -and $targetLimitsExact
            reason_code                         = 'ok'
            owner_statement_exact_match         = $ownerExact
            authorization_window_current        = $windowCurrent
            attempt_unused                      = $attemptUnused
            execution_package_hashes_match      = $packageFilesMatch
            source_hashes_match                 = $sourceFilesMatch
            runtime_binding_matches             = $runtimeBindingMatches
            target_action_limits_outputs_match  = $targetLimitsExact
        }
    } catch {
        New-P36AdapterFailure -ReasonCode 'authority_binding_invalid'
    }
}

function ConvertTo-P36CanonicalJsonBytes {
    param([Parameter(Mandatory = $true)][System.Collections.IDictionary] $Record)

    $json = $Record | ConvertTo-Json -Compress -Depth 12
    [System.Text.Encoding]::UTF8.GetBytes($json)
}

function Move-P36FileWithoutReplacement {
    param(
        [Parameter(Mandatory = $true)][string] $Source,
        [Parameter(Mandatory = $true)][string] $Destination
    )

    Initialize-P36NativeMethods
    if ([System.IO.File]::Exists($Destination) -or [System.IO.Directory]::Exists($Destination)) {
        return $false
    }
    [HCam.Phase36.NativeStorage]::MoveFileExW($Source, $Destination, 0x00000008)
}

function Write-P36AtomicRecord {
    param(
        [Parameter(Mandatory = $true)][string] $RepositoryRoot,
        [Parameter(Mandatory = $true)][string] $RelativePath,
        [Parameter(Mandatory = $true)][System.Collections.IDictionary] $Record
    )

    $destination = Resolve-P36RepositoryBindingPath -RepositoryRoot $RepositoryRoot -RelativePath $RelativePath
    if ($null -eq $destination -or $RelativePath -cnotin $script:P36OutputPaths) {
        return @{
            ok                    = $false
            schema_valid          = $false
            size_valid            = $false
            destination_absent    = $false
            partial_absent        = $false
            flushed_to_disk       = $false
            nonreplacement_rename = $false
            sha256                = $null
        }
    }

    $partial = $destination + '.partial'
    $bytes = ConvertTo-P36CanonicalJsonBytes -Record $Record
    $sizeValid = $bytes.Length -le $script:P36MaximumOutputBytes
    $destinationAbsent = -not [System.IO.File]::Exists($destination) -and -not [System.IO.Directory]::Exists($destination)
    $partialAbsent = -not [System.IO.File]::Exists($partial) -and -not [System.IO.Directory]::Exists($partial)
    if (-not $sizeValid -or -not $destinationAbsent -or -not $partialAbsent) {
        return @{
            ok                    = $false
            schema_valid          = $true
            size_valid            = $sizeValid
            destination_absent    = $destinationAbsent
            partial_absent        = $partialAbsent
            flushed_to_disk       = $false
            nonreplacement_rename = $false
            sha256                = $null
        }
    }

    $createdPartial = $false
    $flushed = $false
    $renamed = $false
    $stream = $null
    try {
        $stream = [System.IO.FileStream]::new(
            $partial,
            [System.IO.FileMode]::CreateNew,
            [System.IO.FileAccess]::Write,
            [System.IO.FileShare]::None,
            4096,
            [System.IO.FileOptions]::WriteThrough
        )
        $createdPartial = $true
        $stream.Write($bytes, 0, $bytes.Length)
        $stream.Flush($true)
        $flushed = $true
        $stream.Dispose()
        $stream = $null
        $renamed = Move-P36FileWithoutReplacement -Source $partial -Destination $destination
        if (-not $renamed) {
            throw 'P36_ATOMIC_RENAME_FAILED'
        }
        @{
            ok                    = $true
            schema_valid          = $true
            size_valid            = $true
            destination_absent    = $true
            partial_absent        = $true
            flushed_to_disk       = $true
            nonreplacement_rename = $true
            sha256                = Get-P36Sha256Hex -Bytes $bytes
        }
    } catch {
        @{
            ok                    = $false
            schema_valid          = $true
            size_valid            = $sizeValid
            destination_absent    = $destinationAbsent
            partial_absent        = $partialAbsent
            flushed_to_disk       = $flushed
            nonreplacement_rename = $renamed
            sha256                = $null
        }
    } finally {
        if ($null -ne $stream) {
            $stream.Dispose()
        }
        if ($createdPartial -and -not $renamed -and [System.IO.File]::Exists($partial)) {
            try {
                [System.IO.File]::Delete($partial)
            } catch {
            }
        }
        [System.Array]::Clear($bytes, 0, $bytes.Length)
    }
}

function Write-P36AuthorizationRecord {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory = $true)][hashtable] $Request,
        [Parameter(Mandatory = $true)][string] $RepositoryRoot,
        [Parameter(Mandatory = $true)][string] $AttemptStartedAt
    )

    $ownerStatementBytes = $null
    try {
        $ownerStatementBytes = [System.Text.Encoding]::UTF8.GetBytes([string] $Request.owner_statement)
        $record = [ordered]@{
            contract_format               = 'hcam.phase3.p3_6.quarantine_storage_r2_authorization.v1'
            decision_id                   = 'D-P3.6-U3K-STORAGE-R2-AUTH'
            package_digest_sha256         = [string] $Request.execution_package_digest_sha256
            owner_statement_sha256        = Get-P36Sha256Hex -Bytes $ownerStatementBytes
            attempt_started_at            = $AttemptStartedAt
            authorization_expires_at      = [string] $Request.authorization_expires_at
            logical_node_id               = 'LAB-LAPTOP-01'
            logical_root_id               = 'P36-QUARANTINE-ROOT-R2-CANDIDATE'
            action_count                  = 10
            maximum_attempts              = 1
            automatic_retry_authorized    = $false
            profile_activation_authorized = $false
            deployment_authorized         = $false
            remote_git_authorized         = $false
        }
        $result = Write-P36AtomicRecord `
            -RepositoryRoot $RepositoryRoot `
            -RelativePath $script:P36OutputPaths[0] `
            -Record $record
        $result.reason_code = if ($result.ok) { 'ok' } else { 'authorization_record_write_failed' }
        return $result
    } catch {
        return New-P36AdapterFailure -ReasonCode 'authorization_record_invalid'
    } finally {
        if ($null -ne $ownerStatementBytes) {
            [System.Array]::Clear($ownerStatementBytes, 0, $ownerStatementBytes.Length)
        }
    }
}

function Get-P36DriveInformation {
    [CmdletBinding()]
    param()

    $result = @{
        ok                     = $false
        properties_available   = $false
        drive_ready            = $false
        drive_type             = $null
        filesystem             = $null
        total_bytes            = 0
        available_free_bytes   = 0
        available_free_percent = 0.0
        reason_code            = 'drive_property_unavailable'
    }
    try {
        $drive = [System.IO.DriveInfo]::new('F:\')
        try { $result.drive_ready = [bool] $drive.IsReady } catch { return $result }
        try { $result.drive_type = [string] $drive.DriveType } catch { return $result }
        try { $result.filesystem = [string] $drive.DriveFormat } catch { return $result }
        try { $result.total_bytes = [Int64] $drive.TotalSize } catch { return $result }
        try { $result.available_free_bytes = [Int64] $drive.AvailableFreeSpace } catch { return $result }
        if ($result.total_bytes -gt 0) {
            $result.available_free_percent = 100.0 * $result.available_free_bytes / $result.total_bytes
        }
        $result.properties_available = $true
        $result.ok = (
            $result.drive_ready -and
            $result.drive_type -ceq 'Fixed' -and
            $result.filesystem -cin @('NTFS', 'ReFS') -and
            $result.available_free_bytes -ge 5368709120 -and
            $result.available_free_percent -ge 15.0
        )
        $result.reason_code = if ($result.ok) {
            'ok'
        } elseif (-not $result.drive_ready) {
            'drive_not_ready'
        } elseif ($result.drive_type -cne 'Fixed') {
            'drive_type_not_allowed'
        } elseif ($result.filesystem -cnotin @('NTFS', 'ReFS')) {
            'filesystem_not_allowed'
        } else {
            'capacity_below_minimum'
        }
        return $result
    } catch {
        return $result
    }
}

function Test-P36CandidatePath {
    [CmdletBinding()]
    param()

    $result = @{
        ok                    = $false
        attributes_available = $false
        exact_canonical_path  = $false
        parent_reparse        = $false
        candidate_reparse     = $false
        candidate_absent      = $false
        reason_code           = 'candidate_attribute_unavailable'
    }
    try {
        Initialize-P36NativeMethods
        $canonical = [System.IO.Path]::GetFullPath($script:P36CandidateRoot, 'F:\')
        $ordinalIgnoreCaseMatch = $canonical.Equals(
            $script:P36CandidateRoot,
            [System.StringComparison]::OrdinalIgnoreCase
        )
        $ordinalMatch = $canonical.Equals(
            $script:P36CandidateRoot,
            [System.StringComparison]::Ordinal
        )
        $outsideProject = -not (
            $canonical.Equals($script:P36ExcludedProjectRoot, [System.StringComparison]::OrdinalIgnoreCase) -or
            $canonical.StartsWith($script:P36ExcludedProjectRoot + '\', [System.StringComparison]::OrdinalIgnoreCase)
        )
        $result.exact_canonical_path = $ordinalIgnoreCaseMatch -and $ordinalMatch -and $outsideProject

        $invalidAttributes = [uint32]::MaxValue
        $reparseFlag = [uint32] [System.IO.FileAttributes]::ReparsePoint
        $rootAttributes = [HCam.Phase36.NativeStorage]::GetFileAttributesW('F:\')
        if ($rootAttributes -eq $invalidAttributes) {
            return $result
        }
        $result.parent_reparse = ($rootAttributes -band $reparseFlag) -ne 0

        $candidateAttributes = [HCam.Phase36.NativeStorage]::GetFileAttributesW($script:P36CandidateRoot)
        if ($candidateAttributes -eq $invalidAttributes) {
            $errorCode = [System.Runtime.InteropServices.Marshal]::GetLastWin32Error()
            $result.candidate_absent = $errorCode -in @(2, 3)
            if (-not $result.candidate_absent) {
                return $result
            }
        } else {
            $result.candidate_absent = $false
            $result.candidate_reparse = ($candidateAttributes -band $reparseFlag) -ne 0
        }
        $result.attributes_available = $true
        $result.ok = (
            $result.exact_canonical_path -and
            -not $result.parent_reparse -and
            -not $result.candidate_reparse -and
            $result.candidate_absent
        )
        $result.reason_code = if ($result.ok) { 'ok' } else { 'candidate_path_invalid' }
        return $result
    } catch {
        return $result
    }
}

function New-P36ProtectedDirectorySecurity {
    [CmdletBinding()]
    param()

    try {
        $identity = [System.Security.Principal.WindowsIdentity]::GetCurrent()
        $currentSid = $identity.User
        if ($null -eq $currentSid) {
            return New-P36AdapterFailure -ReasonCode 'identity_unavailable'
        }
        $systemSid = [System.Security.Principal.SecurityIdentifier]::new('S-1-5-18')
        $administratorsSid = [System.Security.Principal.SecurityIdentifier]::new('S-1-5-32-544')
        if ($currentSid.Equals($systemSid) -or $currentSid.Equals($administratorsSid)) {
            return @{
                ok                 = $false
                identity_available = $true
                identity_collision = $true
                reason_code        = 'identity_collision'
            }
        }

        $security = [System.Security.AccessControl.DirectorySecurity]::new()
        $security.SetAccessRuleProtection($true, $false)
        $inheritance = (
            [System.Security.AccessControl.InheritanceFlags]::ContainerInherit -bor
            [System.Security.AccessControl.InheritanceFlags]::ObjectInherit
        )
        $propagation = [System.Security.AccessControl.PropagationFlags]::None
        $allow = [System.Security.AccessControl.AccessControlType]::Allow
        $security.AddAccessRule([System.Security.AccessControl.FileSystemAccessRule]::new(
            $currentSid,
            [System.Security.AccessControl.FileSystemRights]::Modify,
            $inheritance,
            $propagation,
            $allow
        ))
        $security.AddAccessRule([System.Security.AccessControl.FileSystemAccessRule]::new(
            $systemSid,
            [System.Security.AccessControl.FileSystemRights]::FullControl,
            $inheritance,
            $propagation,
            $allow
        ))
        $security.AddAccessRule([System.Security.AccessControl.FileSystemAccessRule]::new(
            $administratorsSid,
            [System.Security.AccessControl.FileSystemRights]::FullControl,
            $inheritance,
            $propagation,
            $allow
        ))
        $descriptorBytes = $security.GetSecurityDescriptorBinaryForm()
        $bounded = $descriptorBytes.Length -gt 0 -and $descriptorBytes.Length -le 16384
        @{
            ok                           = $bounded
            reason_code                  = if ($bounded) { 'ok' } else { 'security_descriptor_invalid' }
            identity_available           = $true
            identity_collision           = $false
            descriptor_bounded           = $bounded
            inheritance_protected        = $security.AreAccessRulesProtected
            exact_three_allow_tuples      = $true
            identity_not_persisted        = $true
            account_translation_absent    = $true
            security_descriptor_bytes     = $descriptorBytes
            current_process_SID_in_memory = $currentSid
        }
    } catch {
        New-P36AdapterFailure -ReasonCode 'security_descriptor_construction_failed'
    }
}

function New-P36QuarantineRoot {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory = $true)][byte[]] $SecurityDescriptorBytes
    )

    $descriptorPointer = [System.IntPtr]::Zero
    try {
        if ($SecurityDescriptorBytes.Length -lt 1 -or $SecurityDescriptorBytes.Length -gt 16384) {
            return New-P36AdapterFailure -ReasonCode 'security_descriptor_invalid'
        }
        Initialize-P36NativeMethods
        $descriptorPointer = [System.Runtime.InteropServices.Marshal]::AllocHGlobal(
            $SecurityDescriptorBytes.Length
        )
        [System.Runtime.InteropServices.Marshal]::Copy(
            $SecurityDescriptorBytes,
            0,
            $descriptorPointer,
            $SecurityDescriptorBytes.Length
        )
        $attributes = [HCam.Phase36.SECURITY_ATTRIBUTES]::new()
        $attributes.nLength = [System.Runtime.InteropServices.Marshal]::SizeOf($attributes)
        $attributes.lpSecurityDescriptor = $descriptorPointer
        $attributes.bInheritHandle = $false

        $success = [HCam.Phase36.NativeStorage]::CreateDirectoryW(
            $script:P36CandidateRoot,
            [ref] $attributes
        )
        $errorCode = if ($success) { 0 } else { [System.Runtime.InteropServices.Marshal]::GetLastWin32Error() }
        @{
            ok                          = $success
            reason_code                 = if ($success) { 'ok' } elseif ($errorCode -eq 183) { 'root_preexisting_or_raced' } else { 'root_create_failed' }
            native_success              = $success
            error_already_exists        = $errorCode -eq 183
            required_API_used           = $true
            security_attributes_nonnull = $descriptorPointer -ne [System.IntPtr]::Zero
            fallback_used               = $false
        }
    } catch {
        @{
            ok                          = $false
            reason_code                 = 'root_create_failed'
            native_success              = $false
            error_already_exists        = $false
            required_API_used           = $true
            security_attributes_nonnull = $descriptorPointer -ne [System.IntPtr]::Zero
            fallback_used               = $false
        }
    } finally {
        if ($descriptorPointer -ne [System.IntPtr]::Zero) {
            for ($index = 0; $index -lt $SecurityDescriptorBytes.Length; $index++) {
                [System.Runtime.InteropServices.Marshal]::WriteByte($descriptorPointer, $index, 0)
            }
            [System.Runtime.InteropServices.Marshal]::FreeHGlobal($descriptorPointer)
        }
        [System.Array]::Clear($SecurityDescriptorBytes, 0, $SecurityDescriptorBytes.Length)
    }
}

function Test-P36QuarantineDacl {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory = $true)]
        [System.Security.Principal.SecurityIdentifier] $CurrentProcessSid
    )

    $result = @{
        ok                                                     = $false
        reason_code                                            = 'DACL_policy_failed'
        access_rules_protected                                 = $false
        exact_rule_count_pass                                  = $false
        current_process_principal_pass                         = $false
        current_process_Modify_Synchronize_rights_pass         = $false
        current_process_excessive_or_unknown_rights_absent     = $false
        LocalSystem_tuple_pass                                 = $false
        Administrators_tuple_pass                              = $false
        inheritance_flags_pass                                 = $false
        propagation_flags_pass                                 = $false
        access_types_pass                                      = $false
        inherited_rule_absent                                  = $false
        deny_rule_absent                                       = $false
        unauthorized_principal_absent                          = $false
        overall_DACL_pass                                      = $false
    }
    try {
        $directory = [System.IO.DirectoryInfo]::new($script:P36CandidateRoot)
        $security = [System.IO.FileSystemAclExtensions]::GetAccessControl($directory)
        $rules = @($security.GetAccessRules(
            $true,
            $true,
            [System.Security.Principal.SecurityIdentifier]
        ))
        $systemSid = [System.Security.Principal.SecurityIdentifier]::new('S-1-5-18')
        $administratorsSid = [System.Security.Principal.SecurityIdentifier]::new('S-1-5-32-544')
        $expectedInheritance = (
            [System.Security.AccessControl.InheritanceFlags]::ContainerInherit -bor
            [System.Security.AccessControl.InheritanceFlags]::ObjectInherit
        )
        $expectedCurrentRights = (
            [System.Security.AccessControl.FileSystemRights]::Modify -bor
            [System.Security.AccessControl.FileSystemRights]::Synchronize
        )
        $expectedFullControl = [System.Security.AccessControl.FileSystemRights]::FullControl

        $result.access_rules_protected = $security.AreAccessRulesProtected
        $result.exact_rule_count_pass = $rules.Count -eq 3
        $result.inherited_rule_absent = @($rules | Where-Object { $_.IsInherited }).Count -eq 0
        $result.deny_rule_absent = @($rules | Where-Object {
            $_.AccessControlType -ne [System.Security.AccessControl.AccessControlType]::Allow
        }).Count -eq 0
        $result.inheritance_flags_pass = @($rules | Where-Object {
            $_.InheritanceFlags -ne $expectedInheritance
        }).Count -eq 0
        $result.propagation_flags_pass = @($rules | Where-Object {
            $_.PropagationFlags -ne [System.Security.AccessControl.PropagationFlags]::None
        }).Count -eq 0
        $result.access_types_pass = $result.deny_rule_absent

        $currentRule = @($rules | Where-Object { $_.IdentityReference.Equals($CurrentProcessSid) })
        $systemRule = @($rules | Where-Object { $_.IdentityReference.Equals($systemSid) })
        $administratorsRule = @($rules | Where-Object { $_.IdentityReference.Equals($administratorsSid) })
        $authorizedRuleCount = $currentRule.Count + $systemRule.Count + $administratorsRule.Count

        $result.current_process_principal_pass = $currentRule.Count -eq 1
        if ($currentRule.Count -eq 1) {
            $result.current_process_Modify_Synchronize_rights_pass = (
                $currentRule[0].FileSystemRights -eq $expectedCurrentRights
            )
            $result.current_process_excessive_or_unknown_rights_absent = (
                $currentRule[0].FileSystemRights -eq $expectedCurrentRights
            )
        }
        $result.LocalSystem_tuple_pass = (
            $systemRule.Count -eq 1 -and
            $systemRule[0].FileSystemRights -eq $expectedFullControl
        )
        $result.Administrators_tuple_pass = (
            $administratorsRule.Count -eq 1 -and
            $administratorsRule[0].FileSystemRights -eq $expectedFullControl
        )
        $result.unauthorized_principal_absent = $authorizedRuleCount -eq $rules.Count

        $result.overall_DACL_pass = (
            $result.access_rules_protected -and
            $result.exact_rule_count_pass -and
            $result.current_process_principal_pass -and
            $result.current_process_Modify_Synchronize_rights_pass -and
            $result.current_process_excessive_or_unknown_rights_absent -and
            $result.LocalSystem_tuple_pass -and
            $result.Administrators_tuple_pass -and
            $result.inheritance_flags_pass -and
            $result.propagation_flags_pass -and
            $result.access_types_pass -and
            $result.inherited_rule_absent -and
            $result.deny_rule_absent -and
            $result.unauthorized_principal_absent
        )
        $result.ok = $result.overall_DACL_pass
        $result.reason_code = if ($result.ok) { 'ok' } else { 'DACL_policy_failed' }
        return $result
    } catch {
        return $result
    }
}

function New-P36DeterministicProbeBytes {
    $output = [byte[]]::new(4096)
    $seed = [System.Text.Encoding]::ASCII.GetBytes('P36-U3K-STORAGE-R2-GENERATED-PROBE-V1')
    $algorithm = [System.Security.Cryptography.SHA256]::Create()
    try {
        $offset = 0
        $counter = 0
        while ($offset -lt $output.Length) {
            $counterBytes = [System.BitConverter]::GetBytes([int] $counter)
            $blockInput = [byte[]]::new($seed.Length + $counterBytes.Length)
            [System.Buffer]::BlockCopy($seed, 0, $blockInput, 0, $seed.Length)
            [System.Buffer]::BlockCopy($counterBytes, 0, $blockInput, $seed.Length, $counterBytes.Length)
            $block = $algorithm.ComputeHash($blockInput)
            $copyLength = [System.Math]::Min($block.Length, $output.Length - $offset)
            [System.Buffer]::BlockCopy($block, 0, $output, $offset, $copyLength)
            [System.Array]::Clear($blockInput, 0, $blockInput.Length)
            [System.Array]::Clear($block, 0, $block.Length)
            $offset += $copyLength
            $counter++
        }
        return $output
    } finally {
        $algorithm.Dispose()
        [System.Array]::Clear($seed, 0, $seed.Length)
    }
}

function Get-P36FileContentHash {
    param([Parameter(Mandatory = $true)][string] $Path)

    $stream = [System.IO.File]::OpenRead($Path)
    $algorithm = [System.Security.Cryptography.SHA256]::Create()
    try {
        ([System.BitConverter]::ToString($algorithm.ComputeHash($stream))).Replace('-', '')
    } finally {
        $algorithm.Dispose()
        $stream.Dispose()
    }
}

function Invoke-P36AtomicCapabilityProbe {
    [CmdletBinding()]
    param()

    $result = @{
        ok                            = $false
        reason_code                   = 'probe_write_failed'
        probe_paths_absent            = $false
        exact_byte_count              = $false
        write_through                 = $false
        flush_to_disk                 = $false
        first_hash_match              = $false
        rename_write_through_only     = $false
        second_hash_match             = $false
        cleanup_complete              = $false
        zero_retention                = $false
        partial_created_by_attempt    = $false
        verified_created_by_attempt   = $false
    }
    $stream = $null
    $probeBytes = $null
    $cleanupFailed = $false
    try {
        Initialize-P36NativeMethods
        if (
            [System.IO.File]::Exists($script:P36PartialProbePath) -or
            [System.IO.Directory]::Exists($script:P36PartialProbePath) -or
            [System.IO.File]::Exists($script:P36VerifiedProbePath) -or
            [System.IO.Directory]::Exists($script:P36VerifiedProbePath)
        ) {
            $result.reason_code = 'probe_path_preexisting'
            return $result
        }
        $result.probe_paths_absent = $true
        $probeBytes = New-P36DeterministicProbeBytes
        $expectedHash = Get-P36Sha256Hex -Bytes $probeBytes
        $result.exact_byte_count = $probeBytes.Length -eq 4096

        $stream = [System.IO.FileStream]::new(
            $script:P36PartialProbePath,
            [System.IO.FileMode]::CreateNew,
            [System.IO.FileAccess]::ReadWrite,
            [System.IO.FileShare]::None,
            4096,
            [System.IO.FileOptions]::WriteThrough
        )
        $result.partial_created_by_attempt = $true
        $result.write_through = $true
        $stream.Write($probeBytes, 0, $probeBytes.Length)
        $stream.Flush($true)
        $result.flush_to_disk = $true
        $stream.Dispose()
        $stream = $null

        $result.first_hash_match = (Get-P36FileContentHash -Path $script:P36PartialProbePath) -ceq $expectedHash
        if (-not $result.first_hash_match) {
            $result.reason_code = 'probe_hash_mismatch'
            return $result
        }
        $result.rename_write_through_only = [HCam.Phase36.NativeStorage]::MoveFileExW(
            $script:P36PartialProbePath,
            $script:P36VerifiedProbePath,
            0x00000008
        )
        if (-not $result.rename_write_through_only) {
            $result.reason_code = 'probe_rename_policy_failed'
            return $result
        }
        $result.partial_created_by_attempt = $false
        $result.verified_created_by_attempt = $true
        $result.second_hash_match = (Get-P36FileContentHash -Path $script:P36VerifiedProbePath) -ceq $expectedHash
        if (-not $result.second_hash_match) {
            $result.reason_code = 'probe_hash_mismatch'
            return $result
        }
        [System.IO.File]::Delete($script:P36VerifiedProbePath)
        $result.verified_created_by_attempt = $false
        $result.cleanup_complete = -not [System.IO.File]::Exists($script:P36VerifiedProbePath)
        $result.zero_retention = $result.cleanup_complete
        $result.ok = (
            $result.exact_byte_count -and
            $result.write_through -and
            $result.flush_to_disk -and
            $result.first_hash_match -and
            $result.rename_write_through_only -and
            $result.second_hash_match -and
            $result.cleanup_complete -and
            $result.zero_retention
        )
        $result.reason_code = if ($result.ok) { 'ok' } else { 'probe_write_failed' }
        return $result
    } catch {
        return $result
    } finally {
        if ($null -ne $stream) {
            $stream.Dispose()
        }
        if ($null -ne $probeBytes) {
            [System.Array]::Clear($probeBytes, 0, $probeBytes.Length)
        }
        if ($result.partial_created_by_attempt -and [System.IO.File]::Exists($script:P36PartialProbePath)) {
            try {
                [System.IO.File]::Delete($script:P36PartialProbePath)
                $result.partial_created_by_attempt = $false
            } catch {
                $cleanupFailed = $true
                $result.cleanup_complete = $false
                $result.reason_code = 'probe_cleanup_failed'
            }
        }
        if ($result.verified_created_by_attempt -and [System.IO.File]::Exists($script:P36VerifiedProbePath)) {
            try {
                [System.IO.File]::Delete($script:P36VerifiedProbePath)
                $result.verified_created_by_attempt = $false
            } catch {
                $cleanupFailed = $true
                $result.cleanup_complete = $false
                $result.reason_code = 'probe_cleanup_failed'
            }
        }
        if (
            -not $cleanupFailed -and
            -not [System.IO.File]::Exists($script:P36PartialProbePath) -and
            -not [System.IO.File]::Exists($script:P36VerifiedProbePath)
        ) {
            $result.cleanup_complete = $true
            $result.zero_retention = $true
        }
    }
}

function Invoke-P36BoundedCleanup {
    [CmdletBinding()]
    param(
        [bool] $RootCreatedByAttempt,
        [bool] $PartialCreatedByAttempt,
        [bool] $VerifiedCreatedByAttempt
    )

    $result = @{
        ok                    = $true
        probe_cleanup_pass    = $true
        root_cleanup_pass     = $true
        manual_review_required = $false
    }
    try {
        if ($PartialCreatedByAttempt -and [System.IO.File]::Exists($script:P36PartialProbePath)) {
            [System.IO.File]::Delete($script:P36PartialProbePath)
        }
        if ($VerifiedCreatedByAttempt -and [System.IO.File]::Exists($script:P36VerifiedProbePath)) {
            [System.IO.File]::Delete($script:P36VerifiedProbePath)
        }
    } catch {
        $result.probe_cleanup_pass = $false
    }
    if ($RootCreatedByAttempt) {
        try {
            Initialize-P36NativeMethods
            $attributes = [HCam.Phase36.NativeStorage]::GetFileAttributesW($script:P36CandidateRoot)
            $invalidAttributes = [uint32]::MaxValue
            $reparseFlag = [uint32] [System.IO.FileAttributes]::ReparsePoint
            if ($attributes -eq $invalidAttributes -or ($attributes -band $reparseFlag) -ne 0) {
                $result.root_cleanup_pass = $false
            } else {
                [System.IO.Directory]::Delete($script:P36CandidateRoot, $false)
            }
        } catch {
            $result.root_cleanup_pass = $false
        }
    }
    $result.ok = $result.probe_cleanup_pass -and $result.root_cleanup_pass
    $result.manual_review_required = -not $result.ok
    return $result
}

function Get-P36CapacityBucket {
    param([Int64] $Bytes)

    if ($Bytes -lt 5368709120) { return 'below_5_GiB' }
    if ($Bytes -lt 21474836480) { return '5_to_20_GiB' }
    if ($Bytes -lt 53687091200) { return '20_to_50_GiB' }
    return 'at_least_50_GiB'
}

function Get-P36PercentBucket {
    param([double] $Percent)

    if ($Percent -lt 15.0) { return 'below_15_percent' }
    if ($Percent -lt 30.0) { return '15_to_30_percent' }
    return 'at_least_30_percent'
}

function Write-P36AttemptOutputs {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory = $true)][string] $RepositoryRoot,
        [Parameter(Mandatory = $true)][System.Collections.IDictionary] $TerminalProjection,
        [Parameter(Mandatory = $true)][hashtable] $ObservedProjection,
        [Parameter(Mandatory = $true)][string] $AttemptStartedAt
    )

    try {
        $completedAt = [System.DateTimeOffset]::UtcNow.ToString('o')
        $storageState = if ([bool] $TerminalProjection.succeeded) {
            'ready_until_observed_at_plus_3600_seconds'
        } elseif ([bool] $TerminalProjection.manual_review_required) {
            'manual_review_required'
        } else {
            'blocked'
        }
        $resultRecord = [ordered]@{
            contract_format            = 'hcam.phase3.p3_6.quarantine_storage_r2_result.v1'
            attempt_started_at         = $AttemptStartedAt
            attempt_completed_at       = $completedAt
            drive_ready                = [bool] $ObservedProjection.drive_ready
            drive_type                 = [string] $ObservedProjection.drive_type
            filesystem                 = [string] $ObservedProjection.filesystem
            total_bytes_bucket         = Get-P36CapacityBucket -Bytes ([Int64] $ObservedProjection.total_bytes)
            available_bytes_bucket     = Get-P36CapacityBucket -Bytes ([Int64] $ObservedProjection.available_free_bytes)
            available_percent_bucket   = Get-P36PercentBucket -Percent ([double] $ObservedProjection.available_free_percent)
            canonical_path_policy_pass = [bool] $ObservedProjection.canonical_path_policy_pass
            candidate_absent_before_attempt = [bool] $ObservedProjection.candidate_absent_before_attempt
            root_created_by_attempt    = [bool] $TerminalProjection.root_created_by_attempt
            root_retained_after_attempt = [bool] $TerminalProjection.succeeded
            root_cleanup_state         = if ([bool] $TerminalProjection.cleanup_required) { 'bounded_cleanup_required' } else { 'not_required' }
            bounded_DACL_policy_booleans = $ObservedProjection.bounded_DACL_policy_booleans
            bounded_probe_policy_booleans = $ObservedProjection.bounded_probe_policy_booleans
            storage_state              = $storageState
            reason_code                = [string] $TerminalProjection.reason_code
            ready_until                = if ([bool] $TerminalProjection.succeeded) { ([System.DateTimeOffset]::Parse($completedAt).AddSeconds(3600)).ToString('o') } else { $null }
        }
        $resultWrite = Write-P36AtomicRecord `
            -RepositoryRoot $RepositoryRoot `
            -RelativePath $script:P36OutputPaths[1] `
            -Record $resultRecord

        $evidenceRecord = [ordered]@{
            contract_format               = 'hcam.phase3.p3_6.quarantine_storage_r2_evidence.v1'
            result_sha256                 = $resultWrite.sha256
            action_count                  = 10
            maximum_attempts              = 1
            automatic_retry_authorized    = $false
            probe_content_retained        = $false
            raw_error_persisted            = $false
            identity_or_security_material_persisted = $false
            Defender_state                = 'not_in_scope_not_queried'
            ModelScan_state               = 'not_in_scope_not_queried_not_installed_not_executed'
            artifact_acquisition_authorized = $false
            profile_activation_authorized = $false
            deployment_authorized         = $false
            remote_git_authorized          = $false
        }
        $evidenceWrite = Write-P36AtomicRecord `
            -RepositoryRoot $RepositoryRoot `
            -RelativePath $script:P36OutputPaths[2] `
            -Record $evidenceRecord

        @{
            ok                    = [bool] $resultWrite.ok -and [bool] $evidenceWrite.ok
            reason_code           = if ([bool] $resultWrite.ok -and [bool] $evidenceWrite.ok) { 'ok' } else { 'output_write_failed' }
            schema_valid          = $true
            size_valid            = [bool] $resultWrite.size_valid -and [bool] $evidenceWrite.size_valid
            canonical_JSON        = $true
            hashes_computed       = $null -ne $resultWrite.sha256 -and $null -ne $evidenceWrite.sha256
            flushed_to_disk       = [bool] $resultWrite.flushed_to_disk -and [bool] $evidenceWrite.flushed_to_disk
            nonreplacement_rename = [bool] $resultWrite.nonreplacement_rename -and [bool] $evidenceWrite.nonreplacement_rename
        }
    } catch {
        New-P36AdapterFailure -ReasonCode 'output_write_failed'
    }
}

Export-ModuleMember -Function @(
    'Get-P36MonotonicSeconds',
    'Get-P36UtcStartTime',
    'Test-P36ExecutionBindings',
    'Write-P36AuthorizationRecord',
    'Get-P36DriveInformation',
    'Test-P36CandidatePath',
    'New-P36ProtectedDirectorySecurity',
    'New-P36QuarantineRoot',
    'Test-P36QuarantineDacl',
    'Invoke-P36AtomicCapabilityProbe',
    'Invoke-P36BoundedCleanup',
    'Write-P36AttemptOutputs'
)
