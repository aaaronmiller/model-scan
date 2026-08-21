"""MC-002 source-adapter migration tests."""

import json

from source_adapter import (
    build_source_observations,
    diff_source_observations,
    last_known_good_path,
    payload_sha256,
    publish_observations,
    quarantine_receipt,
    refresh_with_retry,
    validate_observations,
)


def _payload(price="0"):
    return {
        "data": [
            {
                "id": "qwen/qwen3-coder:free",
                "name": "Qwen Coder",
                "context_length": 131072,
                "pricing": {"prompt": price, "completion": "0"},
                "supported_parameters": ["tools", "structured_output"],
                "architecture": {"input_modalities": ["text"]},
            }
        ]
    }


def _document(payload=None, retrieved_at="2026-08-15T12:00:00Z"):
    value = payload or _payload()
    raw = json.dumps(value, sort_keys=True).encode()
    return build_source_observations(
        value,
        serving_provider="openrouter",
        source_id="openrouter:/api/v1/models",
        retrieved_at=retrieved_at,
        source_sha256=payload_sha256(raw),
    )


def test_catalog_discovery_does_not_claim_callable_or_reachable():
    document = _document()
    validate_observations(document)
    record = document["records"][0]
    assert record["serving_provider"] == "openrouter"
    assert record["upstream_organization"] == "qwen"
    assert record["api_model"] == "qwen/qwen3-coder:free"
    assert record["states"] == {
        "discoverable": "true",
        "callable": "unknown",
        "probed_reachable": "unknown",
        "policy_eligible": "unknown",
    }
    assert record["pricing"]["input"] == {"state": "known", "value": 0.0}
    assert all(item["provenance"].startswith("openrouter:/api/v1/models") for item in record["features"])


def test_change_events_cover_new_removed_and_price_changes():
    first = _document()
    changed_payload = _payload(price="0.1")
    changed_payload["data"].append(
        {"id": "new/model", "name": "New", "pricing": {"prompt": None, "completion": None}}
    )
    second = _document(changed_payload, retrieved_at="2026-08-16T12:00:00Z")
    events = diff_source_observations(first, second)
    assert {event["event"] for event in events} == {"model-added", "price-changed"}
    assert any(event.get("before") == 0.0 and event.get("after") == 0.1 for event in events)
    removed = diff_source_observations(second, first)
    assert any(event["event"] == "model-removed" and event["api_model"] == "new/model" for event in removed)


def test_publication_preserves_source_time_and_last_good(tmp_path):
    document = _document()
    target = tmp_path / "source-observations.json"
    publish_observations(document, target)
    current = json.loads(target.read_text(encoding="utf-8"))
    known_good = json.loads(last_known_good_path(target).read_text(encoding="utf-8"))
    assert current == known_good == document
    assert current["records"][0]["retrieved_at"] == document["retrieved_at"]
    assert target.stat().st_mode & 0o077 == 0


def test_retry_is_bounded_and_records_failure_classes():
    calls = 0

    def fetch():
        nonlocal calls
        calls += 1
        if calls < 3:
            raise TimeoutError("fixture timeout")
        return b'{"data": []}'

    value, failures = refresh_with_retry(fetch, parse=json.loads, attempts=3)
    assert value == {"data": []}
    assert failures == ["TimeoutError", "TimeoutError"]
    assert calls == 3


def test_quarantine_receipt_keeps_only_digest_size_and_failure_reason():
    payload = b'{"bad":"potentially sensitive source payload"}'
    receipt = quarantine_receipt(
        payload,
        source_id="provider-catalog",
        reason="schema-invalid",
        observed_at="2026-08-15T12:00:00Z",
    )
    assert receipt["payload_bytes"] == len(payload)
    assert receipt["raw_payload_stored"] is False
    assert "potentially sensitive" not in str(receipt)
