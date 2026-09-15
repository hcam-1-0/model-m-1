from __future__ import annotations

from dataclasses import dataclass


MAX_AUTHORING_BYTES = 128 * 1024
MAX_SEMANTIC_NODES = 128
MAX_GRAPH_DEPTH = 16
MAX_INPUTS_PER_NODE = 16
MAX_CEL_SOURCE_BYTES = 512
MAX_CEL_CHECKED_BYTES = 64 * 1024
MAX_CEL_AST_NODES = 128
MAX_CEL_DEPTH = 16
MAX_TEMPORAL_WINDOW_MS = 15 * 60 * 1000
MAX_EVENTS_PER_WINDOW = 4_096
MAX_STATE_KEYS = 16_384
MAX_RULES_PER_BATCH = 64
MAX_INPUTS_PER_BATCH = 1_000
MAX_REPEAT_LIMIT = 100_000


class RuleLimitError(ValueError):
    """Raised when a rule crosses a declared static or runtime limit."""


@dataclass(frozen=True, slots=True)
class RuleBounds:
    semantic_nodes: int = 32
    graph_depth: int = 8
    inputs_per_node: int = 8
    cel_source_bytes: int = 256
    cel_ast_nodes: int = 64
    cel_depth: int = 8
    temporal_window_ms: int = 60_000
    events_per_window: int = 256
    state_keys: int = 1_024
    rules_per_batch: int = 16
    inputs_per_batch: int = 100

    def __post_init__(self) -> None:
        limits = (
            ("semantic_nodes", self.semantic_nodes, MAX_SEMANTIC_NODES),
            ("graph_depth", self.graph_depth, MAX_GRAPH_DEPTH),
            ("inputs_per_node", self.inputs_per_node, MAX_INPUTS_PER_NODE),
            ("cel_source_bytes", self.cel_source_bytes, MAX_CEL_SOURCE_BYTES),
            ("cel_ast_nodes", self.cel_ast_nodes, MAX_CEL_AST_NODES),
            ("cel_depth", self.cel_depth, MAX_CEL_DEPTH),
            ("temporal_window_ms", self.temporal_window_ms, MAX_TEMPORAL_WINDOW_MS),
            ("events_per_window", self.events_per_window, MAX_EVENTS_PER_WINDOW),
            ("state_keys", self.state_keys, MAX_STATE_KEYS),
            ("rules_per_batch", self.rules_per_batch, MAX_RULES_PER_BATCH),
            ("inputs_per_batch", self.inputs_per_batch, MAX_INPUTS_PER_BATCH),
        )
        for name, value, maximum in limits:
            if not 1 <= value <= maximum:
                raise RuleLimitError(f"{name} is outside the declared bounds")
