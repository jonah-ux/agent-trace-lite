import io
import json
import tempfile
import unittest
from pathlib import Path

from agent_trace_lite.cli import main
from agent_trace_lite.core import TraceParseError, inspect_trace, query_events, read_trace, redact_event


class TraceCoreTests(unittest.TestCase):
    def _trace(self):
        return read_trace(io.StringIO(
            "\n".join([
                json.dumps({"type": "tool", "name": "search", "meta": {"token": "secret-value"}, "items": [{"message": "Bearer abcdefghijk"}]}),
                json.dumps({"type": "result", "message": "done"}),
                "",
            ]) + "\n"
        )
        )

    def test_recursive_redaction_does_not_mutate(self):
        event = {"nested": {"api_key": "hidden"}, "items": [{"authorization": "Bearer abcdefghijk"}]}
        safe, count = redact_event(event)
        self.assertEqual(event["nested"]["api_key"], "hidden")
        self.assertEqual(safe["nested"]["api_key"], "[REDACTED]")
        self.assertEqual(safe["items"][0]["authorization"], "[REDACTED]")
        self.assertEqual(count, 2)

    def test_integrity_summary_is_deterministic_and_redacted(self):
        first = inspect_trace(self._trace())
        second = inspect_trace(self._trace())
        self.assertEqual(first, second)
        self.assertEqual(first["events"], 2)
        self.assertEqual(first["blank_lines"], 1)
        self.assertEqual(first["redactions"], 2)
        self.assertEqual(len(first["raw_sha256"]), 64)

    def test_query_matches_redacted_content_and_filters(self):
        rows = query_events(self._trace().events, event_type="TOOL", contains="bearer [redacted]")
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["meta"]["token"], "[REDACTED]")
        self.assertEqual(query_events(self._trace().events, name="missing"), [])

    def test_raw_digest_tracks_source_bytes(self):
        first = read_trace(io.StringIO('{"type":"result","message":"done"}\n'))
        second = read_trace(io.StringIO('{ "message": "done", "type": "result" }\n'))
        self.assertNotEqual(first.raw_sha256, second.raw_sha256)
        self.assertEqual(first.redacted_sha256, second.redacted_sha256)

    def test_malformed_and_non_object_lines_fail_closed(self):
        with self.assertRaisesRegex(TraceParseError, "line 2"):
            read_trace(io.StringIO('{"type":"ok"}\nnot-json\n'))
        with self.assertRaisesRegex(TraceParseError, "event must be a JSON object"):
            read_trace(io.StringIO('[]\n'))


class CliTests(unittest.TestCase):
    def test_query_and_inspect_commands(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "events.jsonl"
            output = Path(directory) / "trace.html"
            path.write_text(json.dumps({"type": "tool", "name": "search", "secret": "hidden"}) + "\n")
            self.assertEqual(main(["inspect", str(path)]), 0)
            self.assertEqual(main(["query", str(path), "--type", "tool"]), 0)
            self.assertEqual(main(["view", str(path), "--html", str(output)]), 0)
            self.assertIn("[REDACTED]", output.read_text())

    def test_cli_rejects_invalid_limit(self):
        with tempfile.NamedTemporaryFile(mode="w", suffix=".jsonl") as handle:
            handle.write('{"type":"ok"}\n')
            handle.flush()
            self.assertEqual(main(["query", handle.name, "--limit", "0"]), 2)


if __name__ == "__main__":
    unittest.main()
