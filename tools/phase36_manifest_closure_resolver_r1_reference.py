"""Machine-disabled reference policy for the Phase 3.6 manifest closure resolver."""

from __future__ import annotations

import ntpath
from collections.abc import Mapping, Sequence
from typing import Any


CONTRACT_VERSION = "1.1.0"
OPERATION = "resolve_manifest_closure_v1"
MAX_ENTRIES = 64
MAX_FILE_BYTES = 64 * 1024 * 1024
MAX_TOTAL_BYTES = 128 * 1024 * 1024
MAX_REFERENCE_CHARS = 260

FIELDS = (
    "RootModule",
    "NestedModules",
    "RequiredAssemblies",
    "ScriptsToProcess",
    "TypesToProcess",
    "FormatsToProcess",
    "FileList",
)
FALLBACK_FIELDS = frozenset({"NestedModules", "RequiredAssemblies"})
CODE_EXTENSIONS = frozenset({".dll", ".exe", ".ps1", ".psm1", ".psd1", ".cdxml"})
REQUEST_FIELDS = frozenset(
    {
        "contract_version",
        "operation",
        "manifest_directory",
        "module_root",
        "ps_home",
        "entries",
        "observations",
    }
)
ENTRY_FIELDS = frozenset({"field", "value"})
OBSERVATION_FIELDS = frozenset(
    {
        "entry_index",
        "base",
        "candidate_path",
        "present",
        "regular",
        "nonreparse",
        "trusted",
        "size_bytes",
    }
)
BASES = ("manifest_directory", "ps_home")
REASONS = (
    "manifest_closure_accepted",
    "resolver_input_invalid",
    "manifest_path_context_invalid",
    "manifest_entry_count_exceeded",
    "manifest_field_unsupported",
    "scripts_to_process_forbidden",
    "manifest_reference_forbidden",
    "manifest_reference_escape",
    "manifest_observation_invalid",
    "manifest_candidate_ambiguous",
    "load_bearing_target_missing",
    "load_bearing_target_invalid",
    "load_bearing_target_untrusted",
    "filelist_code_target_missing",
    "duplicate_canonical_target",
    "aggregate_file_bytes_exceeded",
)


def _exact_mapping(value: Any, fields: frozenset[str]) -> bool:
    return isinstance(value, Mapping) and frozenset(value) == fields


def _is_bool(value: Any) -> bool:
    return isinstance(value, bool)


def _is_nonnegative_int(value: Any) -> bool:
    return isinstance(value, int) and not isinstance(value, bool) and value >= 0


def _canonical(path: str) -> str:
    return ntpath.normcase(ntpath.normpath(path))


def _is_rooted_drive_path(path: Any) -> bool:
    if not isinstance(path, str) or not path or path.startswith(("\\\\", "//")):
        return False
    drive, tail = ntpath.splitdrive(path)
    return (
        len(drive) == 2
        and drive[0].isalpha()
        and drive[1] == ":"
        and tail.startswith(("\\", "/"))
        and _canonical(path) == _canonical(ntpath.abspath(path))
    )


def _is_within(path: str, root: str) -> bool:
    try:
        return ntpath.commonpath((_canonical(path), _canonical(root))) == _canonical(root)
    except ValueError:
        return False


def _path_context_valid(request: Mapping[str, Any]) -> bool:
    manifest = request["manifest_directory"]
    module_root = request["module_root"]
    ps_home = request["ps_home"]
    return (
        all(_is_rooted_drive_path(item) for item in (manifest, module_root, ps_home))
        and _is_within(manifest, module_root)
        and _is_within(module_root, ps_home)
    )


def _forbidden_reference(value: Any) -> bool:
    if not isinstance(value, str) or not value or len(value) > MAX_REFERENCE_CHARS:
        return True
    lowered = value.lower()
    drive, _ = ntpath.splitdrive(value)
    components = value.replace("/", "\\").split("\\")
    return (
        bool(drive)
        or ntpath.isabs(value)
        or value.startswith(("\\", "/"))
        or "://" in lowered
        or lowered.startswith(("file:", "http:", "https:"))
        or any(char in value for char in "*?[]$%`{}()'\"")
        or any(component == ".." for component in components)
    )


def _is_bare_binary_name(field: str, value: str) -> bool:
    return (
        field in FALLBACK_FIELDS
        and "\\" not in value
        and "/" not in value
        and ntpath.splitext(value)[1].lower() in CODE_EXTENSIONS
    )


def candidate_paths(
    field: str, value: str, manifest_directory: str, ps_home: str
) -> tuple[tuple[str, str], ...]:
    """Return ordered candidate base classes and canonical paths."""

    manifest_candidate = _canonical(ntpath.join(manifest_directory, value))
    candidates = [("manifest_directory", manifest_candidate)]
    if _is_bare_binary_name(field, value):
        candidates.append(("ps_home", _canonical(ntpath.join(ps_home, value))))
    return tuple(candidates)


def _default_counts() -> dict[str, int]:
    return {
        "declared_entries": 0,
        "load_bearing_entries": 0,
        "inventory_entries": 0,
        "selected_targets": 0,
        "missing_inventory_entries": 0,
        "selected_total_bytes": 0,
    }


def _terminal(
    reason: str,
    counts: Mapping[str, int],
    field_class: str = "none",
    base_class: str = "none",
) -> dict[str, Any]:
    return {
        "contract_version": CONTRACT_VERSION,
        "terminal": True,
        "succeeded": reason == "manifest_closure_accepted",
        "reason_code": reason,
        "failing_field_class": field_class,
        "candidate_base_class": base_class,
        "counts": dict(counts),
        "retention": {
            "raw_path_or_reference_retained": False,
            "manifest_text_or_parser_token_retained": False,
            "exception_or_security_material_retained": False,
        },
    }


def _request_shape_valid(request: Any) -> bool:
    if not _exact_mapping(request, REQUEST_FIELDS):
        return False
    if request["contract_version"] != CONTRACT_VERSION or request["operation"] != OPERATION:
        return False
    entries = request["entries"]
    observations = request["observations"]
    if not isinstance(entries, Sequence) or isinstance(entries, (str, bytes)):
        return False
    if not isinstance(observations, Sequence) or isinstance(observations, (str, bytes)):
        return False
    return True


def _observation_valid(observation: Any) -> bool:
    return (
        _exact_mapping(observation, OBSERVATION_FIELDS)
        and _is_nonnegative_int(observation["entry_index"])
        and observation["base"] in BASES
        and isinstance(observation["candidate_path"], str)
        and _is_rooted_drive_path(observation["candidate_path"])
        and all(
            _is_bool(observation[field])
            for field in ("present", "regular", "nonreparse", "trusted")
        )
        and _is_nonnegative_int(observation["size_bytes"])
    )


def _observation_index(
    observations: Sequence[Mapping[str, Any]],
) -> dict[tuple[int, str, str], Mapping[str, Any]] | None:
    indexed: dict[tuple[int, str, str], Mapping[str, Any]] = {}
    for observation in observations:
        if not _observation_valid(observation):
            return None
        key = (
            observation["entry_index"],
            observation["base"],
            _canonical(observation["candidate_path"]),
        )
        if key in indexed:
            return None
        indexed[key] = observation
    return indexed


def resolve_manifest_closure(request: Any) -> dict[str, Any]:
    """Resolve supplied observations without filesystem, environment, or process access."""

    counts = _default_counts()
    if not _request_shape_valid(request):
        return _terminal("resolver_input_invalid", counts)
    if not _path_context_valid(request):
        return _terminal("manifest_path_context_invalid", counts)

    entries = request["entries"]
    counts["declared_entries"] = len(entries)
    if len(entries) > MAX_ENTRIES:
        return _terminal("manifest_entry_count_exceeded", counts)
    observations = _observation_index(request["observations"])
    if observations is None:
        return _terminal("manifest_observation_invalid", counts)

    selected_paths: set[str] = set()
    manifest_directory = request["manifest_directory"]
    module_root = request["module_root"]
    ps_home = request["ps_home"]
    for index, entry in enumerate(entries):
        if not _exact_mapping(entry, ENTRY_FIELDS):
            return _terminal("resolver_input_invalid", counts)
        field = entry["field"]
        value = entry["value"]
        if field not in FIELDS:
            return _terminal("manifest_field_unsupported", counts)
        if field == "ScriptsToProcess":
            return _terminal("scripts_to_process_forbidden", counts, "script")
        if _forbidden_reference(value):
            return _terminal("manifest_reference_forbidden", counts, field)

        inventory = field == "FileList"
        if inventory:
            counts["inventory_entries"] += 1
        else:
            counts["load_bearing_entries"] += 1
        candidates = candidate_paths(field, value, manifest_directory, ps_home)
        for base, candidate in candidates:
            required_root = ps_home if base == "ps_home" else module_root
            if not _is_within(candidate, required_root) or not _is_within(candidate, ps_home):
                return _terminal("manifest_reference_escape", counts, field, base)

        observed_candidates: list[tuple[str, str, Mapping[str, Any]]] = []
        for base, candidate in candidates:
            observation = observations.get((index, base, candidate))
            if observation is None:
                return _terminal("manifest_observation_invalid", counts, field, base)
            if observation["present"]:
                observed_candidates.append((base, candidate, observation))
        if len(observed_candidates) > 1:
            return _terminal("manifest_candidate_ambiguous", counts, field, "multiple")
        if not observed_candidates:
            code_like = ntpath.splitext(value)[1].lower() in CODE_EXTENSIONS
            if inventory and not code_like:
                counts["missing_inventory_entries"] += 1
                continue
            reason = "filelist_code_target_missing" if inventory else "load_bearing_target_missing"
            return _terminal(reason, counts, field)

        base, candidate, observation = observed_candidates[0]
        if not observation["regular"] or not observation["nonreparse"]:
            return _terminal("load_bearing_target_invalid", counts, field, base)
        if not observation["trusted"]:
            return _terminal("load_bearing_target_untrusted", counts, field, base)
        if observation["size_bytes"] > MAX_FILE_BYTES:
            return _terminal("load_bearing_target_invalid", counts, field, base)
        if candidate in selected_paths:
            return _terminal("duplicate_canonical_target", counts, field, base)
        selected_paths.add(candidate)
        counts["selected_targets"] += 1
        counts["selected_total_bytes"] += observation["size_bytes"]
        if counts["selected_total_bytes"] > MAX_TOTAL_BYTES:
            return _terminal("aggregate_file_bytes_exceeded", counts, field, base)

    return _terminal("manifest_closure_accepted", counts)


def canonical_projection() -> dict[str, Any]:
    """Return constants that the PowerShell policy source must mirror."""

    return {
        "bases": list(BASES),
        "code_extensions": sorted(CODE_EXTENSIONS),
        "contract_version": CONTRACT_VERSION,
        "fields": list(FIELDS),
        "fallback_fields": sorted(FALLBACK_FIELDS),
        "maximum_entries": MAX_ENTRIES,
        "maximum_file_bytes": MAX_FILE_BYTES,
        "maximum_reference_characters": MAX_REFERENCE_CHARS,
        "maximum_total_bytes": MAX_TOTAL_BYTES,
        "operation": OPERATION,
        "reason_codes": list(REASONS),
    }
