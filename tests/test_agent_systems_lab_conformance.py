import io
import json
from pathlib import Path
import unittest

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


class AgentSystemsLabConformanceTests(unittest.TestCase):
    def test_manifest_pins_native_owner_and_shared_adapter(self):
        manifest = json.loads(FIXTURE.read_text(encoding="utf-8"))
        self.assertEqual(manifest["schema"], "agent-systems-lab-trace-conformance/v1")
        self.assertEqual(manifest["owner"], "agent-trace-lite")
        self.assertEqual(manifest["native_schema"], "agent-trace/v1")
        self.assertEqual(manifest["inspect_schema"], "agent-trace/inspect/v1")
        self.assertEqual(manifest["shared_adapter"]["schema"], "agent-proof/interop/v1")
        self.assertEqual(len(manifest["cases"]), 5)
        self.assertTrue(manifest["privacy"]["query_output_redacted"])


    def test_trace_integrity_summary_is_deterministic_and_redacted(self):
        first = inspect_trace(trace())
        second = inspect_trace(trace())
        self.assertEqual(first, second)
        self.assertEqual(first["schema"], "agent-trace/inspect/v1")
        self.assertEqual(first["events"], 2)
        self.assertEqual(first["redactions"], 2)
        self.assertEqual(len(first["raw_sha256"]), 64)
        self.assertEqual(len(first["redacted_sha256"]), 64)

        rows = query_events(trace().events, event_type="TOOL", contains="bearer [redacted]")
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["meta"]["token"], "[REDACTED]")
        self.assertNotIn("secret-value", json.dumps(rows))
        self.assertNotIn("Bearer abcdefghijk", json.dumps(rows))


    def test_trace_parser_refuses_malformed_and_non_object_events(self):
        with self.assertRaisesRegex(TraceParseError, "line 2"):
            read_trace(io.StringIO('{"type":"ok"}\nnot-json\n'))
        with self.assertRaisesRegex(TraceParseError, "event must be a JSON object"):
            read_trace(io.StringIO("[]\n"))
