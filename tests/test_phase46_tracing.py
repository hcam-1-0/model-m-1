import pytest

from hcam.operations.platform.tracing import TraceContextError, correlation_context, parse_trace_context


def test_trace_context_is_validated_without_authority() -> None:
    value = parse_trace_context("00-" + "1" * 32 + "-" + "2" * 16 + "-01", "hcam=generated")
    assert value.sampled is True
    assert value.grants_authority is False
    assert correlation_context("generated:correlation").grants_authority is False


@pytest.mark.parametrize(
    "value",
    ["invalid", "00-" + "0" * 32 + "-" + "2" * 16 + "-01", "ff-" + "1" * 32 + "-" + "2" * 16 + "-00"],
)
def test_invalid_trace_context_fails_closed(value: str) -> None:
    with pytest.raises(TraceContextError):
        parse_trace_context(value)


def test_duplicate_tracestate_keys_fail_closed() -> None:
    with pytest.raises(TraceContextError):
        parse_trace_context("00-" + "1" * 32 + "-" + "2" * 16 + "-00", "a=one,a=two")


@pytest.mark.parametrize(
    "state",
    [
        "",
        " hcam=generated",
        "hcam=generated ",
        "hcam=\N{SNOWMAN}",
        "bad member",
        ",".join(f"k{i}=v" for i in range(33)),
    ],
)
def test_invalid_tracestate_fails_closed(state: str) -> None:
    with pytest.raises(TraceContextError):
        parse_trace_context("00-" + "1" * 32 + "-" + "2" * 16 + "-00", state)


def test_trace_flags_are_version_bounded() -> None:
    with pytest.raises(TraceContextError):
        parse_trace_context("00-" + "1" * 32 + "-" + "2" * 16 + "-03")
    assert parse_trace_context("01-" + "1" * 32 + "-" + "2" * 16 + "-03").sampled is True
