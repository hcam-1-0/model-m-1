from hcam.operations.platform.failures import failure, may_retry


def test_failure_taxonomy_is_closed_and_unknown_fails_closed() -> None:
    assert failure("authorization.denied").retry == "never"
    unknown = failure("future.unknown")
    assert unknown.code == "state.unknown"
    assert unknown.retry == "never"


def test_only_transient_dependencies_retry_within_bound() -> None:
    transient = failure("dependency.timeout", safe_parameters={"attempt": 1})
    assert may_retry(transient, attempt_count=1)
    assert not may_retry(transient, attempt_count=3)
    assert not may_retry(failure("integrity.failed"), attempt_count=0)
