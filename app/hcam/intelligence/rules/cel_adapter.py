from __future__ import annotations

import base64
import hashlib
import re
from dataclasses import dataclass
from typing import Literal

from cel_expr_python import cel
from google.protobuf.any_pb2 import Any as ProtobufAny

from hcam.intelligence.rules.bounds import (
    MAX_CEL_CHECKED_BYTES,
    RuleBounds,
    RuleLimitError,
)
from hcam.intelligence.rules.canonical import rule_sha256
from hcam.intelligence.rules.contracts import CelCompilationV1, Scalar


PROFILE = "hcam.p4-2.constrained-cel.v1"
ScalarType = Literal["bool", "int", "double", "string"]
_VARIABLE_TYPES: dict[str, tuple[cel.Type, ScalarType]] = {
    "event_kind": (cel.Type.STRING, "string"),
    "object_class": (cel.Type.STRING, "string"),
    "confidence": (cel.Type.DOUBLE, "double"),
    "uncertainty": (cel.Type.DOUBLE, "double"),
    "direction": (cel.Type.STRING, "string"),
    "count": (cel.Type.INT, "int"),
    "rate": (cel.Type.DOUBLE, "double"),
    "chronology_complete": (cel.Type.BOOL, "bool"),
    "contradiction": (cel.Type.BOOL, "bool"),
    "schedule_open": (cel.Type.BOOL, "bool"),
    "prior_result": (cel.Type.BOOL, "bool"),
}
_TOKEN = re.compile(
    r"\s+|&&|\|\||==|!=|<=|>=|[()!<>+\-*/%]|"
    r"'(?:[^'\\\r\n]|\\['\\nrt])*'|"
    r'"(?:[^"\\\r\n]|\\["\\nrt])*"|'
    r"\d+(?:\.\d+)?|[A-Za-z_][A-Za-z0-9_]*"
)
_BINARY_PRECEDENCE = {
    "||": 1,
    "&&": 2,
    "==": 3,
    "!=": 3,
    "<": 4,
    "<=": 4,
    ">": 4,
    ">=": 4,
    "+": 5,
    "-": 5,
    "*": 6,
    "/": 6,
    "%": 6,
}
_CHECKED_TYPE_URL = "type.googleapis.com/cel.expr.CheckedExpr"
_ALLOWED_FUNCTIONS = {
    "_&&_",
    "_||_",
    "_==_",
    "_!=_",
    "_<_",
    "_<=_",
    "_>_",
    "_>=_",
    "_+_",
    "_-_",
    "_*_",
    "_/_",
    "_%_",
    "!_",
    "-_",
}
_ALLOWED_OVERLOADS = {
    "logical_and",
    "logical_or",
    "logical_not",
    "equals",
    "not_equals",
    "less_int64",
    "less_uint64",
    "less_double",
    "less_string",
    "less_equals_int64",
    "less_equals_uint64",
    "less_equals_double",
    "less_equals_string",
    "greater_int64",
    "greater_uint64",
    "greater_double",
    "greater_string",
    "greater_equals_int64",
    "greater_equals_uint64",
    "greater_equals_double",
    "greater_equals_string",
    "add_int64",
    "add_uint64",
    "add_double",
    "subtract_int64",
    "subtract_uint64",
    "subtract_double",
    "multiply_int64",
    "multiply_uint64",
    "multiply_double",
    "divide_int64",
    "divide_uint64",
    "divide_double",
    "modulo_int64",
    "modulo_uint64",
    "negate_int64",
    "negate_double",
}


class RuleCelError(ValueError):
    """A bounded CEL expression failed structural, type, or runtime validation."""


@dataclass(frozen=True, slots=True)
class StructuralNode:
    kind: str
    value: str
    value_type: ScalarType
    children: tuple[StructuralNode, ...] = ()

    def projection(self) -> dict[str, object]:
        return {
            "kind": self.kind,
            "value": self.value,
            "value_type": self.value_type,
            "children": [item.projection() for item in self.children],
        }


@dataclass(frozen=True, slots=True)
class CheckedRuleCel:
    source: str
    structural_ast: StructuralNode
    serialized: bytes
    compilation: CelCompilationV1


@dataclass(frozen=True, slots=True)
class _WireField:
    number: int
    wire_type: int
    value: int | bytes


def _read_varint(payload: bytes, position: int) -> tuple[int, int]:
    value = 0
    shift = 0
    while position < len(payload) and shift <= 63:
        item = payload[position]
        position += 1
        value |= (item & 0x7F) << shift
        if item < 0x80:
            return value, position
        shift += 7
    raise RuleCelError("checked CEL contains an invalid protobuf varint")


def _write_varint(value: int) -> bytes:
    if value < 0:
        raise RuleCelError("checked CEL contains an invalid negative wire value")
    output = bytearray()
    while value >= 0x80:
        output.append((value & 0x7F) | 0x80)
        value >>= 7
    output.append(value)
    return bytes(output)


def _decode_wire(payload: bytes) -> list[_WireField]:
    fields: list[_WireField] = []
    position = 0
    while position < len(payload):
        key, position = _read_varint(payload, position)
        number, wire_type = key >> 3, key & 7
        if number == 0 or wire_type not in {0, 1, 2, 5}:
            raise RuleCelError("checked CEL contains an unsupported protobuf field")
        if wire_type == 0:
            value, position = _read_varint(payload, position)
        elif wire_type == 1:
            if position + 8 > len(payload):
                raise RuleCelError("checked CEL protobuf is truncated")
            value = payload[position : position + 8]
            position += 8
        elif wire_type == 5:
            if position + 4 > len(payload):
                raise RuleCelError("checked CEL protobuf is truncated")
            value = payload[position : position + 4]
            position += 4
        else:
            length, position = _read_varint(payload, position)
            if length > MAX_CEL_CHECKED_BYTES or position + length > len(payload):
                raise RuleCelError("checked CEL protobuf length is invalid")
            value = payload[position : position + length]
            position += length
        fields.append(_WireField(number, wire_type, value))
    return fields


def _encode_wire(fields: list[_WireField]) -> bytes:
    output = bytearray()
    for field in fields:
        output.extend(_write_varint((field.number << 3) | field.wire_type))
        if field.wire_type == 0:
            if not isinstance(field.value, int):
                raise RuleCelError("checked CEL protobuf has an invalid varint")
            output.extend(_write_varint(field.value))
        else:
            if not isinstance(field.value, bytes):
                raise RuleCelError("checked CEL protobuf has an invalid byte field")
            if field.wire_type == 2:
                output.extend(_write_varint(len(field.value)))
            output.extend(field.value)
    return bytes(output)


def _single(fields: list[_WireField], number: int, wire_type: int) -> _WireField:
    selected = [
        item for item in fields if item.number == number and item.wire_type == wire_type
    ]
    if len(selected) != 1:
        raise RuleCelError("checked CEL protobuf has an invalid required field")
    return selected[0]


def _map_key(payload: bytes) -> int:
    field = _single(_decode_wire(payload), 1, 0)
    assert isinstance(field.value, int)
    return field.value


def _normalize_checked(serialized: bytes) -> tuple[bytes, bytes]:
    wrapper = ProtobufAny()
    try:
        wrapper.ParseFromString(serialized)
    except Exception as exc:
        raise RuleCelError("checked CEL wrapper is malformed") from exc
    if wrapper.type_url != _CHECKED_TYPE_URL:
        raise RuleCelError("checked CEL wrapper has an unexpected type")
    fields = _decode_wire(wrapper.value)
    normalized: list[_WireField] = []
    for number in sorted({item.number for item in fields}):
        selected = [item for item in fields if item.number == number]
        if number in {2, 3}:
            if any(
                item.wire_type != 2 or not isinstance(item.value, bytes)
                for item in selected
            ):
                raise RuleCelError("checked CEL map has an invalid wire type")
            selected.sort(key=lambda item: _map_key(item.value))  # type: ignore[arg-type]
        elif number == 5:
            source = _single(selected, 5, 2)
            assert isinstance(source.value, bytes)
            source_fields = _decode_wire(source.value)
            positions = [item for item in source_fields if item.number == 4]
            others = [item for item in source_fields if item.number != 4]
            positions.sort(key=lambda item: _map_key(item.value))  # type: ignore[arg-type]
            selected = [_WireField(5, 2, _encode_wire([*others, *positions]))]
        normalized.extend(selected)
    checked = _encode_wire(normalized)
    canonical_wrapper = ProtobufAny(type_url=_CHECKED_TYPE_URL, value=checked)
    return canonical_wrapper.SerializeToString(deterministic=True), checked


def _utf8(field: _WireField) -> str:
    if not isinstance(field.value, bytes):
        raise RuleCelError("checked CEL text field has an invalid wire type")
    try:
        return field.value.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise RuleCelError("checked CEL text field is not UTF-8") from exc


def _inspect_checked(serialized: bytes, bounds: RuleBounds) -> tuple[int, int]:
    normalized, checked = _normalize_checked(serialized)
    if normalized != serialized:
        raise RuleCelError("checked CEL bytes are not in canonical wire order")
    fields = _decode_wire(checked)
    references: dict[int, tuple[str, tuple[str, ...]]] = {}
    for item in [field for field in fields if field.number == 2]:
        assert isinstance(item.value, bytes)
        entry = _decode_wire(item.value)
        expression_id = _single(entry, 1, 0).value
        reference_bytes = _single(entry, 2, 2).value
        assert isinstance(expression_id, int) and isinstance(reference_bytes, bytes)
        reference = _decode_wire(reference_bytes)
        name = _utf8(_single(reference, 1, 2))
        overloads = tuple(_utf8(value) for value in reference if value.number == 3)
        if name in _VARIABLE_TYPES:
            if overloads:
                raise RuleCelError("checked CEL variable has an unexpected overload")
        elif (
            name not in _ALLOWED_FUNCTIONS
            or not overloads
            or any(value not in _ALLOWED_OVERLOADS for value in overloads)
        ):
            raise RuleCelError("checked CEL reference is not allowlisted")
        references[expression_id] = (name, overloads)

    scalar_type_ids: set[int] = set()
    for item in [field for field in fields if field.number == 3]:
        assert isinstance(item.value, bytes)
        entry = _decode_wire(item.value)
        expression_id = _single(entry, 1, 0).value
        type_bytes = _single(entry, 2, 2).value
        assert isinstance(expression_id, int) and isinstance(type_bytes, bytes)
        type_fields = _decode_wire(type_bytes)
        primitive = _single(type_fields, 3, 0).value
        if primitive not in {1, 2, 3, 4, 5} or len(type_fields) != 1:
            raise RuleCelError("checked CEL contains a non-scalar type")
        scalar_type_ids.add(expression_id)

    root = _single(fields, 4, 2).value
    assert isinstance(root, bytes)
    count = 0
    maximum_depth = 0

    def inspect_expression(payload: bytes, depth: int) -> None:
        nonlocal count, maximum_depth
        count += 1
        maximum_depth = max(maximum_depth, depth)
        if count > bounds.cel_ast_nodes or depth > bounds.cel_depth:
            raise RuleLimitError("checked CEL AST exceeds structural bounds")
        expression = _decode_wire(payload)
        expression_id = _single(expression, 2, 0).value
        if not isinstance(expression_id, int) or expression_id not in scalar_type_ids:
            raise RuleCelError("checked CEL expression has no scalar checked type")
        kinds = [item for item in expression if item.number in {3, 4, 5, 6, 7, 8, 9}]
        if (
            len(kinds) != 1
            or kinds[0].wire_type != 2
            or not isinstance(kinds[0].value, bytes)
        ):
            raise RuleCelError("checked CEL expression kind is invalid")
        kind = kinds[0]
        if kind.number == 3:
            constant = _decode_wire(kind.value)
            if len(constant) != 1 or constant[0].number not in {2, 3, 4, 5, 6}:
                raise RuleCelError("checked CEL literal is not scalar")
        elif kind.number == 4:
            identifier = _utf8(_single(_decode_wire(kind.value), 1, 2))
            if (
                identifier not in _VARIABLE_TYPES
                or references.get(expression_id, (None,))[0] != identifier
            ):
                raise RuleCelError("checked CEL identifier is not declared")
        elif kind.number == 6:
            call = _decode_wire(kind.value)
            if any(item.number == 1 for item in call):
                raise RuleCelError("checked CEL member calls are prohibited")
            function = _utf8(_single(call, 2, 2))
            if (
                function not in _ALLOWED_FUNCTIONS
                or references.get(expression_id, (None,))[0] != function
            ):
                raise RuleCelError("checked CEL call is not allowlisted")
            arguments = [item for item in call if item.number == 3]
            if not 1 <= len(arguments) <= 2:
                raise RuleCelError("checked CEL call arity is invalid")
            for argument in arguments:
                assert isinstance(argument.value, bytes)
                inspect_expression(argument.value, depth + 1)
        else:
            raise RuleCelError("checked CEL contains a prohibited expression kind")

    inspect_expression(root, 1)
    if set(references) - scalar_type_ids:
        raise RuleCelError("checked CEL reference map is inconsistent")
    return count, maximum_depth


class _Parser:
    def __init__(self, source: str, bounds: RuleBounds) -> None:
        self.bounds = bounds
        self.tokens = self._tokens(source)
        self.position = 0
        self.node_count = 0
        self.maximum_depth = 0

    @staticmethod
    def _tokens(source: str) -> list[str]:
        tokens: list[str] = []
        cursor = 0
        for match in _TOKEN.finditer(source):
            if match.start() != cursor:
                raise RuleCelError("CEL expression contains prohibited syntax")
            cursor = match.end()
            if not match.group(0).isspace():
                tokens.append(match.group(0))
        if cursor != len(source):
            raise RuleCelError("CEL expression contains prohibited syntax")
        return tokens

    def parse(self) -> StructuralNode:
        if not self.tokens:
            raise RuleCelError("CEL expression is empty")
        node = self._expression(1, 1)
        if self.position != len(self.tokens):
            raise RuleCelError("CEL expression is structurally incomplete")
        if node.value_type != "bool":
            raise RuleCelError("CEL expression must return a Boolean")
        return node

    def _new(
        self,
        kind: str,
        value: str,
        value_type: ScalarType,
        children: tuple[StructuralNode, ...],
        depth: int,
    ) -> StructuralNode:
        self.node_count += 1
        self.maximum_depth = max(self.maximum_depth, depth)
        if self.node_count > self.bounds.cel_ast_nodes:
            raise RuleLimitError("CEL structural AST exceeds the node limit")
        if depth > self.bounds.cel_depth:
            raise RuleLimitError("CEL structural AST exceeds the depth limit")
        return StructuralNode(kind, value, value_type, children)

    def _expression(self, minimum_precedence: int, depth: int) -> StructuralNode:
        left = self._unary(depth)
        while self.position < len(self.tokens):
            operator = self.tokens[self.position]
            precedence = _BINARY_PRECEDENCE.get(operator)
            if precedence is None or precedence < minimum_precedence:
                break
            self.position += 1
            right = self._expression(precedence + 1, depth + 1)
            result_type = _binary_type(operator, left.value_type, right.value_type)
            left = self._new("binary", operator, result_type, (left, right), depth)
        return left

    def _unary(self, depth: int) -> StructuralNode:
        if self.position < len(self.tokens) and self.tokens[self.position] in {
            "!",
            "-",
        }:
            operator = self.tokens[self.position]
            self.position += 1
            child = self._unary(depth + 1)
            if operator == "!" and child.value_type != "bool":
                raise RuleCelError("logical negation requires a Boolean")
            if operator == "-" and child.value_type not in {"int", "double"}:
                raise RuleCelError("numeric negation requires a number")
            return self._new("unary", operator, child.value_type, (child,), depth)
        return self._primary(depth)

    def _primary(self, depth: int) -> StructuralNode:
        if self.position >= len(self.tokens):
            raise RuleCelError("CEL expression ended unexpectedly")
        token = self.tokens[self.position]
        self.position += 1
        if token == "(":
            node = self._expression(1, depth + 1)
            if self.position >= len(self.tokens) or self.tokens[self.position] != ")":
                raise RuleCelError("CEL expression has unbalanced parentheses")
            self.position += 1
            return node
        if token == ")":
            raise RuleCelError("CEL expression has unbalanced parentheses")
        if token in {"true", "false"}:
            return self._new("literal", token, "bool", (), depth)
        if token[0:1] in {"'", '"'}:
            return self._new("literal", token, "string", (), depth)
        if token[0].isdigit():
            return self._new(
                "literal", token, "double" if "." in token else "int", (), depth
            )
        variable = _VARIABLE_TYPES.get(token)
        if variable is None:
            raise RuleCelError("CEL expression references an undeclared variable")
        return self._new("variable", token, variable[1], (), depth)


def _binary_type(operator: str, left: ScalarType, right: ScalarType) -> ScalarType:
    numeric = {"int", "double"}
    if operator in {"&&", "||"}:
        if left != "bool" or right != "bool":
            raise RuleCelError("logical operators require Boolean operands")
        return "bool"
    if operator in {"==", "!="}:
        if left != right and not ({left, right} <= numeric):
            raise RuleCelError("equality operands have incompatible types")
        return "bool"
    if operator in {"<", "<=", ">", ">="}:
        if not ({left, right} <= numeric or left == right == "string"):
            raise RuleCelError("ordering operands have incompatible types")
        return "bool"
    if operator in {"+", "-", "*", "/", "%"}:
        if not {left, right} <= numeric:
            raise RuleCelError("arithmetic operators require numeric operands")
        return "double" if "double" in {left, right} or operator == "/" else "int"
    raise RuleCelError("CEL operator is not allowed")


class ConstrainedRuleCelEnvironment:
    """A closed scalar CEL host with an independently validated structural AST."""

    def __init__(self, bounds: RuleBounds | None = None) -> None:
        self.bounds = bounds or RuleBounds()
        self._environment = cel.NewEnv(
            variables={name: value[0] for name, value in _VARIABLE_TYPES.items()}
        )

    def compile(self, source: str, canonical_node_id: str) -> CheckedRuleCel:
        if (
            source.strip() != source
            or len(source.encode("utf-8")) > self.bounds.cel_source_bytes
        ):
            raise RuleCelError("CEL source must be trimmed and within the byte limit")
        parser = _Parser(source, self.bounds)
        structural_ast = parser.parse()
        try:
            expression = self._environment.compile(source)
        except Exception as exc:
            raise RuleCelError("CEL checked compilation failed") from exc
        if expression.return_type() != cel.Type.BOOL:
            raise RuleCelError("CEL checked expression must return a Boolean")
        serialized, _checked_payload = _normalize_checked(expression.serialize())
        if len(serialized) > MAX_CEL_CHECKED_BYTES:
            raise RuleLimitError("CEL checked bytes exceed the hard limit")
        checked_node_count, checked_depth = _inspect_checked(serialized, self.bounds)
        if checked_node_count != parser.node_count:
            raise RuleCelError("checked CEL and structural AST node counts differ")
        compilation = CelCompilationV1(
            canonical_node_id=canonical_node_id,
            source_sha256=_bytes_digest(source.encode("utf-8")),
            structural_ast_sha256=rule_sha256(structural_ast.projection()),
            checked_sha256=_bytes_digest(serialized),
            checked_bytes_b64=base64.b64encode(serialized).decode("ascii"),
            ast_node_count=checked_node_count,
            ast_depth=max(parser.maximum_depth, checked_depth),
            static_cost=parser.node_count,
        )
        return CheckedRuleCel(source, structural_ast, serialized, compilation)

    def evaluate(
        self, checked: CheckedRuleCel | CelCompilationV1, context: dict[str, Scalar]
    ) -> bool:
        if set(context) != set(_VARIABLE_TYPES):
            raise RuleCelError("CEL runtime context does not match the closed schema")
        for name, (_cel_type, expected) in _VARIABLE_TYPES.items():
            if not _is_value_type(context[name], expected):
                raise RuleCelError(
                    "CEL runtime context contains an invalid scalar type"
                )
        compilation = (
            checked.compilation if isinstance(checked, CheckedRuleCel) else checked
        )
        serialized = (
            checked.serialized
            if isinstance(checked, CheckedRuleCel)
            else base64.b64decode(compilation.checked_bytes_b64, validate=True)
        )
        if _bytes_digest(serialized) != compilation.checked_sha256:
            raise RuleCelError("CEL checked bytes failed integrity validation")
        _inspect_checked(serialized, self.bounds)
        try:
            expression = self._environment.deserialize(serialized)
            result = expression.eval(data=context)
        except Exception as exc:
            raise RuleCelError("CEL evaluation failed closed") from exc
        if result.type() != cel.Type.BOOL:
            raise RuleCelError("CEL runtime result was not Boolean")
        return bool(result.value())


def _is_value_type(value: Scalar, expected: ScalarType) -> bool:
    if expected == "bool":
        return type(value) is bool
    if expected == "int":
        return type(value) is int
    if expected == "double":
        return type(value) is float
    return type(value) is str


def _bytes_digest(value: bytes) -> str:
    return "sha256:" + hashlib.sha256(value).hexdigest()
