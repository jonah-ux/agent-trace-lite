import io
import json
from pathlib import Path

import pytest

from agent_trace_lite.core import TraceParseError, inspect_trace, query_events, read_trace


FIXTURE = Path(__file__).parent / "../conformance/agent-systems-lab.json"


def trace():
    return read_trace(
        io.StringIO(
            json.dumps({"type": "tool", "name": "search", "meta": {"token": "secret-value"}, "message": "Bearer abcdefghijk"})
            + "\n"
            + json.dumps({"type": "result", "message": "done"})
            + "\n"
        )
    )


def test_manifest_pins_native_owner_and_shared_adapter():
    manifest = json.loads(FIXTURE.read_text(encoding="utf-8"))
    assert manifest["schema"] == "agent-systems-lab-trace-conformance/v1"
    assert manifest["owner"] == "agent-trace-lite"
    assert manifest["native_schema"] == "agent-trace/v1"
    assert manifest["inspect_schema"] == "agent-trace/inspect/v1"
    assert manifest["shared_adapter"]["schema"] == "agent-proof/interop/v1"
    assert len(manifest["cases"]) == 5
    assert manifest["privacy"]["query_output_redacted"] is True


def test_trace_integrity_summary_is_deterministic_and_redacted():
    first = inspect_trace(trace())
    second = inspect_trace(trace())
    assert first == second
    assert first["schema"] == "agent-trace/inspect/v1"
    assert first["events"] == 2
    assert first["redactions"] == 2
    assert len(first["raw_sha256"]) == 64
    assert len(first["redacted_sha256"]) == 64

    rows = query_events(trace().events, event_type="TOOL", contains="bearer [redacted]")
    assert len(rows) == 1
    assert rows[0]["meta"]["token"] == "[REDACTED]"
    assert "secret-value" not in json.dumps(rows)
    assert "Bearer abcdefghijk" not in json.dumps(rows)


def test_trace_parser_refuses_malformed_and_non_object_events():
    with pytest.raises(TraceParseError, match="line 2"):
        read_trace(io.StringIO('{"type":"ok"}\nnot-json\n'))
    with pytest.raises(TraceParseError, match="event must be a JSON object"):
        read_trace(io.StringIO("[]\n"))
