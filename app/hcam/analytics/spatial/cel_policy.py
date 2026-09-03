from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass

from cel_expr_python import cel


_VARIABLE_TYPES = {
    "class_id": cel.Type.STRING,
    "confidence": cel.Type.DOUBLE,
    "direction": cel.Type.STRING,
    "scheduled": cel.Type.BOOL,
    "count": cel.Type.INT,
    "line_crossing": cel.Type.BOOL,
    "zone_entry": cel.Type.BOOL,
    "zone_exit": cel.Type.BOOL,
    "zone_presence": cel.Type.BOOL,
    "zone_dwell_threshold": cel.Type.BOOL,
    "zone_occupancy_entered": cel.Type.BOOL,
    "zone_occupancy_exited": cel.Type.BOOL,
}
_TOKEN = re.compile(
    r"\s+|&&|\|\||==|!=|<=|>=|[()!<>+\-*/%]|"
    r"'(?:[^'\\]|\\.)*'|\d+(?:\.\d+)?|[A-Za-z_][A-Za-z0-9_]*"
)
_IDENTIFIER = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")


class CelPolicyError(ValueError):
    pass


@dataclass(frozen=True, slots=True)
class CheckedCelExpression:
    source: str
    serialized: bytes
    digest: str
    static_cost: int


class ConstrainedCelEnvironment:
    """CEL with a closed scalar context and no extensions or custom functions."""

    def __init__(self) -> None:
        self._environment = cel.NewEnv(variables=_VARIABLE_TYPES)

    def compile(self, source: str) -> CheckedCelExpression:
        if source.strip() != source or not source or len(source) > 512:
            raise CelPolicyError("CEL condition must be trimmed and at most 512 bytes")
        tokens: list[str] = []
        cursor = 0
        depth = 0
        maximum_depth = 0
        for match in _TOKEN.finditer(source):
            if match.start() != cursor:
                raise CelPolicyError("CEL condition contains a prohibited token")
            cursor = match.end()
            token = match.group(0)
            if token.isspace():
                continue
            if token == "(":
                depth += 1
                maximum_depth = max(maximum_depth, depth)
            elif token == ")":
                depth -= 1
                if depth < 0:
                    raise CelPolicyError("CEL condition has unbalanced parentheses")
            if _IDENTIFIER.fullmatch(token) and token not in {
                *_VARIABLE_TYPES,
                "true",
                "false",
            }:
                raise CelPolicyError("CEL condition references an unapproved identifier")
            tokens.append(token)
        if cursor != len(source) or depth != 0:
            raise CelPolicyError("CEL condition is not lexically complete")
        if maximum_depth > 8 or len(tokens) > 64:
            raise CelPolicyError("CEL condition exceeds static complexity limits")
        try:
            expression = self._environment.compile(source)
        except Exception as exc:
            raise CelPolicyError("CEL condition did not compile") from exc
        if expression.return_type() != cel.Type.BOOL:
            raise CelPolicyError("CEL condition must return a Boolean")
        serialized = expression.serialize()
        if len(serialized) > 65_536:
            raise CelPolicyError("checked CEL representation exceeds 64 KiB")
        digest_document = json.dumps(
            {
                "profile": "hcam.p3-4.constrained-cel.v1",
                "return_type": "BOOL",
                "source": source,
                "variables": sorted(_VARIABLE_TYPES),
            },
            ensure_ascii=True,
            separators=(",", ":"),
            sort_keys=True,
        ).encode("utf-8")
        return CheckedCelExpression(
            source=source,
            serialized=serialized,
            digest="sha256:" + hashlib.sha256(digest_document).hexdigest(),
            static_cost=len(tokens),
        )

    def evaluate(
        self,
        checked: CheckedCelExpression,
        context: dict[str, object],
    ) -> bool:
        if set(context) != set(_VARIABLE_TYPES):
            raise CelPolicyError("CEL runtime context does not match the closed schema")
        try:
            expression = self._environment.deserialize(checked.serialized)
            result = expression.eval(data=context)
        except Exception as exc:
            raise CelPolicyError("CEL evaluation failed") from exc
        if result.type() != cel.Type.BOOL:
            raise CelPolicyError("CEL runtime result was not Boolean")
        return bool(result.value())
