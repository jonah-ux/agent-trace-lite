"""Command line interface for Agent Trace Lite."""

from __future__ import annotations

import argparse
import html
import json
from pathlib import Path
import sys
from typing import Any

from .core import TraceParseError, inspect_trace, query_events, query_trace, read_trace


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="agent-trace", description="Inspect and render redacted local JSONL agent traces.")
    subparsers = parser.add_subparsers(dest="command", required=True)
    view = subparsers.add_parser("view", help="render a redacted offline HTML timeline")
    view.add_argument("events", type=Path, help="input JSONL event file, or - for stdin")
    view.add_argument("--html", "-o", default="trace.html", help="HTML output path")
    _add_filters(view)
    inspect = subparsers.add_parser("inspect", help="print a deterministic integrity summary")
    inspect.add_argument("events", type=Path, help="input JSONL event file, or - for stdin")
    query = subparsers.add_parser("query", help="print matching redacted events as JSON")
    query.add_argument("events", type=Path, help="input JSONL event file, or - for stdin")
    _add_filters(query)
    for command in (view, inspect, query):
        _add_limits(command)
    return parser


def _add_filters(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--type", dest="event_type", help="exact event type, case-insensitive")
    parser.add_argument("--name", help="exact event name, case-insensitive")
    parser.add_argument("--contains", help="case-insensitive text search over redacted event JSON")
    parser.add_argument("--limit", type=int, help="maximum number of matching events")


def _add_limits(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--max-bytes", type=int, help="maximum UTF-8 input bytes to read")
    parser.add_argument("--max-events", type=int, help="maximum non-blank events to read")
    parser.add_argument("--max-line-bytes", type=int, help="maximum UTF-8 bytes in one input line")


def _read(path: Path, args):
    if str(path) == "-":
        return read_trace(sys.stdin, max_bytes=args.max_bytes, max_events=args.max_events, max_line_bytes=args.max_line_bytes)
    with path.open(encoding="utf-8") as handle:
        return read_trace(handle, max_bytes=args.max_bytes, max_events=args.max_events, max_line_bytes=args.max_line_bytes)


def _query(path: Path, args) -> list[dict[str, Any]]:
    kwargs = {
        "event_type": args.event_type,
        "name": args.name,
        "contains": args.contains,
        "limit": args.limit,
        "max_bytes": args.max_bytes,
        "max_events": args.max_events,
        "max_line_bytes": args.max_line_bytes,
    }
    if str(path) == "-":
        return query_trace(sys.stdin, **kwargs)
    with path.open(encoding="utf-8") as handle:
        return query_trace(handle, **kwargs)


def _selected(trace, args) -> list[dict[str, Any]]:
    return query_events(
        trace.events,
        event_type=getattr(args, "event_type", None),
        name=getattr(args, "name", None),
        contains=getattr(args, "contains", None),
        limit=getattr(args, "limit", None),
    )


def _write_html(trace, rows: list[dict[str, Any]], output: Path) -> None:
    output.parent.mkdir(parents=True, exist_ok=True)
    body = "\n".join(
        "<tr><td>"
        + html.escape(str(row.get("type", "event")))
        + "</td><td>"
        + html.escape(str(row.get("name", row.get("message", ""))))
        + "</td><td><pre>"
        + html.escape(json.dumps(row, ensure_ascii=False, sort_keys=True, indent=2))
        + "</pre></td></tr>"
        for row in rows
    )
    summary = inspect_trace(trace)
    output.write_text(
        "<!doctype html><html><head><meta charset='utf-8'><title>Agent trace</title>"
        "<style>body{font-family:system-ui,sans-serif;margin:2rem}table{border-collapse:collapse;width:100%}"
        "td{border:1px solid #ddd;padding:.5rem;vertical-align:top}pre{white-space:pre-wrap;margin:0}</style>"
        "</head><body><h1>Agent trace</h1><p>"
        + html.escape(f"{len(rows)} shown / {summary['events']} events · redactions {summary['redactions']} · raw sha256 {summary['raw_sha256']}")
        + "</p><table><thead><tr><th>Type</th><th>Name/message</th><th>Redacted event</th></tr></thead><tbody>"
        + body
        + "</tbody></table></body></html>",
        encoding="utf-8",
    )


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        trace = None
        if args.command == "query" and args.limit is not None:
            rows = _query(args.events, args)
        else:
            trace = _read(args.events, args)
            rows = _selected(trace, args)
    except (OSError, TraceParseError, ValueError) as exc:
        error = {"schema": "agent-trace/error/v1", "ok": False, "error": str(exc)}
        if isinstance(exc, TraceParseError):
            error["line"] = exc.line_number
        print(json.dumps(error, ensure_ascii=False, sort_keys=True, indent=2))
        print(f"agent-trace: {exc}", file=sys.stderr)
        return 2
    if args.command == "inspect":
        assert trace is not None
        print(json.dumps(inspect_trace(trace), ensure_ascii=False, sort_keys=True, indent=2))
    elif args.command == "query":
        print(json.dumps({"schema": "agent-trace/query/v1", "matched": len(rows), "events": rows}, ensure_ascii=False, sort_keys=True, indent=2))
    else:
        assert trace is not None
        _write_html(trace, rows, Path(args.html))
        print(json.dumps({"schema": "agent-trace/v1", "events": len(rows), "html": args.html, "raw_sha256": trace.raw_sha256}, sort_keys=True))
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
