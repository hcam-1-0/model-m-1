from __future__ import annotations

import io
import json
from contextlib import redirect_stdout

from hcam.analytics.anpr.contracts import generated_request_fixture
from hcam.analytics.anpr.guardrails import canonical_anpr_evidence_json
from tools import phase35_contracts


def test_p3_5_w1_contract_snapshots_are_current() -> None:
    assert phase35_contracts.check_contracts() == 0


def test_p3_5_w1_contract_writer_requires_review_acknowledgment() -> None:
    with redirect_stdout(io.StringIO()):
        assert phase35_contracts.write_contracts(acknowledged=False) == 2


def test_generated_request_fixture_is_canonical_and_contains_no_plate_text() -> None:
    expected = canonical_anpr_evidence_json(generated_request_fixture())
    actual = phase35_contracts.FIXTURE_PATH.read_text(encoding="utf-8")
    document = json.loads(actual)

    assert actual == expected
    assert "token" not in document
    assert "text" not in document
    assert "path" not in document
    assert "url" not in document
