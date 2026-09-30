from pathlib import Path
import json

import pytest

from agent_trace_lite.core import normalize_records, read_jsonl
from agent_trace_lite.viewer import render_html


def test_normalization_is_sorted_and_redacts_nested_values():
    events = normalize_records(
        [
            {"timestamp": "2026-01-01T00:00:02Z", "type": "llm", "api_key": "sk-secret-value", "nested": {"password": "pw"}},
            {"timestamp": "2026-01-01T00:00:01Z", "event": "command", "command": "printf 'ok'"},
            {"timestamp": "2026-01-01T00:00:01Z", "type": "error", "message": "Authorization: Bearer topsecretvalue"},
        ]
    )
    assert [event["type"] for event in events] == ["subprocess", "error", "model"]
    assert events[2]["data"]["api_key"] == "[REDACTED]"
    assert events[2]["data"]["nested"]["password"] == "[REDACTED]"
    assert "topsecretvalue" not in json.dumps(events)


def test_same_timestamp_keeps_input_order():
    events = normalize_records([{"timestamp": 1, "id": "b"}, {"timestamp": 1, "id": "a"}])
    assert [event["id"] for event in events] == ["b", "a"]


def test_invalid_timestamp_falls_back_after_valid_events():
    events = normalize_records(
        [{"timestamp": "not-a-date", "id": "unknown"}, {"timestamp": float("inf"), "id": "infinite"}, {"timestamp": 1, "id": "known"}]
    )
    assert [event["id"] for event in events] == ["known", "unknown", "infinite"]
    assert [event["timestamp"] for event in events] == ["1970-01-01T00:00:01.000Z", "", ""]


def test_synthetic_fixture_covers_supported_event_families():
    fixture = Path(__file__).parents[1] / "examples" / "demo.jsonl"
    events = normalize_records(read_jsonl(fixture.read_text(encoding="utf-8").splitlines()))
    assert {event["type"] for event in events} == {"model", "tool", "subprocess", "transfer", "guardrail", "error"}
    assert events[0]["data"]["api_key"] == "[REDACTED]"


def test_jsonl_errors_are_actionable():
    with pytest.raises(ValueError, match="line 2"):
        list(read_jsonl(['{"ok": true}', '{not-json}']))


def test_viewer_is_self_contained_and_escapes_html():
    output = render_html(normalize_records([{"type": "tool", "message": "<script>"}]))
    assert "\\u003cscript\\u003e" in output
    assert "<script>" in output  # the viewer's own script tag remains present
    assert "[REDACTED]" not in output
    assert "const source=" in output
    assert "fetch(" not in output
