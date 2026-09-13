from __future__ import annotations

import pytest

from hcam.intelligence.integrations.contracts import GeneratedProviderPayload
from hcam.intelligence.integrations.parser import (
    ProviderResponseError,
    ProviderTransientError,
    parse_generated_response,
)


def test_parser_minimizes_fields_and_returns_digest_without_raw_response() -> None:
    records, normalized_digest, completeness = parse_generated_response(
        GeneratedProviderPayload(
            records=[
                {
                    "record_key": "gen_record_001",
                    "category": "gen_category_a",
                    "unused": "gen_discarded",
                }
            ]
        ),
        allowed_fields=["record_key", "category"],
    )
    assert records == [
        {"record_key": "gen_record_001", "category": "gen_category_a"}
    ]
    assert normalized_digest.startswith("sha256:")
    assert completeness == "complete"


@pytest.mark.parametrize(
    ("fault", "error"),
    [("transient", ProviderTransientError), ("slow", ProviderTransientError), ("malformed", ProviderResponseError), ("revoked", ProviderResponseError)],
)
def test_parser_classifies_generated_faults(fault: str, error: type[Exception]) -> None:
    with pytest.raises(error):
        parse_generated_response(
            GeneratedProviderPayload(records=[], fault=fault), allowed_fields=["record_key"]
        )
