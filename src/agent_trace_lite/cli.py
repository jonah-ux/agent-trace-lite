"""Command-line interface for agent-trace-lite."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

from .core import content_hash, normalize_records, read_jsonl
from .demo import DEMO_RECORDS
from .viewer import write_html


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="agent-trace", description="Normalize JSONL agent traces and render an offline HTML timeline.")
    subparsers = parser.add_subparsers(dest="command", required=True)
    normalize = subparsers.add_parser("normalize", help="normalize JSONL into deterministic JSONL")
    normalize.add_argument("input", type=Path, help="input JSONL file, or - for stdin")
    normalize.add_argument("-o", "--output", type=Path, help="output JSONL file, or stdout by default")
    normalize.add_argument("--hash", action="store_true", help="print the normalized content hash to stderr")
    view = subparsers.add_parser("view", help="normalize JSONL and render an offline HTML viewer")
    view.add_argument("input", type=Path, help="input JSONL file, or - for stdin")
    view.add_argument("-o", "--output", type=Path, required=True, help="HTML output path")
    view.add_argument("--title", default="Agent Trace Lite", help="HTML document title")
    demo = subparsers.add_parser("demo", help="render the built-in synthetic trace without reading a file")
    demo.add_argument("-o", "--output", type=Path, required=True, help="HTML output path")
    demo.add_argument("--title", default="Agent Trace Lite demo", help="HTML document title")
    return parser


def _read(path: Path) -> list[dict]:
    if str(path) == "-":
        return list(read_jsonl(sys.stdin))
    with path.open(encoding="utf-8") as handle:
        return list(read_jsonl(handle))


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        events = normalize_records(DEMO_RECORDS if args.command == "demo" else _read(args.input))
    except (OSError, ValueError) as exc:
        print(f"agent-trace: {exc}", file=sys.stderr)
        return 2
    if args.command == "normalize":
        text = "\n".join(json.dumps(event, ensure_ascii=False, sort_keys=True) for event in events) + ("\n" if events else "")
        if args.output:
            args.output.write_text(text, encoding="utf-8")
        else:
            sys.stdout.write(text)
        if args.hash:
            print(f"sha256={content_hash(events)}", file=sys.stderr)
    elif args.command == "view":
        write_html(events, args.output, title=args.title)
        print(f"wrote {args.output} ({len(events)} events)")
    else:
        write_html(events, args.output, title=args.title)
        print(f"wrote {args.output} ({len(events)} built-in demo events)")
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
