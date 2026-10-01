"""Safe parsing, redaction, querying, and integrity summaries for JSONL traces."""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
import re
from typing import IO, Any, Iterable


SENSITIVE_KEY_PARTS = (
    "token",
    "secret",
    "password",
    "api_key",
    "apikey",
    "authorization",
    "cookie",
    "credential",
    "private_key",
)

INLINE_SECRET_PATTERNS = (
    (re.compile(r"(?i)\bbearer\s+[a-z0-9._~+/=-]{8,}"), "Bearer [REDACTED]"),
    (re.compile(r"\b(?:sk|gh[pousr]|xox[baprs])-[_a-z0-9-]{8,}\b", re.I), "[REDACTED]"),
)


class TraceParseError(ValueError):
    """Raised when an input line cannot be represented as a trace event."""

    def __init__(self, line_number: int, reason: str) -> None:
        super().__init__(f"line {line_number}: {reason}")
        self.line_number = line_number
        self.reason = reason


@dataclass(frozen=True)
class Trace:
    """Parsed events plus safe, deterministic integrity metadata."""

    events: tuple[dict[str, Any], ...]
    source_lines: int
    blank_lines: int
    raw_sha256: str
    redacted_sha256: str
    redactions: int


def canonical_json(value: Any) -> str:
    """Return stable JSON for hashing and machine-readable output."""

    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def _is_sensitive_key(key: str) -> bool:
    lowered = key.casefold().replace("-", "_")
    return any(part in lowered for part in SENSITIVE_KEY_PARTS)


def _redact_string(value: str) -> tuple[str, int]:
    redacted = value
    count = 0
    for pattern, replacement in INLINE_SECRET_PATTERNS:
        redacted, replacements = pattern.subn(replacement, redacted)
        count += replacements
    return redacted, count


def redact_value(value: Any, *, key: str | None = None) -> tuple[Any, int]:
    """Recursively redact sensitive keys and recognizable inline credentials."""

    if key is not None and _is_sensitive_key(key):
        return "[REDACTED]", 1
    if isinstance(value, dict):
        output: dict[str, Any] = {}
        count = 0
        for child_key, child_value in value.items():
            safe_value, child_count = redact_value(child_value, key=str(child_key))
            output[str(child_key)] = safe_value
            count += child_count
        return output, count
    if isinstance(value, list):
        output = []
        count = 0
        for child in value:
            safe_value, child_count = redact_value(child)
            output.append(safe_value)
            count += child_count
        return output, count
    if isinstance(value, str):
        return _redact_string(value)
    return value, 0


def redact_event(event: dict[str, Any]) -> tuple[dict[str, Any], int]:
    """Return a deep redacted copy without mutating the caller's event."""

    value, count = redact_value(event)
    return value, count


def read_trace(handle: IO[str]) -> Trace:
    """Read JSONL strictly, preserving sequence and refusing malformed events."""

    events: list[dict[str, Any]] = []
    raw_hasher = hashlib.sha256()
    redacted_hasher = hashlib.sha256()
    source_lines = 0
    blank_lines = 0
    redactions = 0
    for line_number, line in enumerate(handle, start=1):
        source_lines += 1
        raw_hasher.update(line.encode("utf-8"))
        if not line.strip():
            blank_lines += 1
            continue
        try:
            event = json.loads(line)
        except json.JSONDecodeError as exc:
            raise TraceParseError(line_number, f"invalid JSON ({exc.msg})") from exc
        if not isinstance(event, dict):
            raise TraceParseError(line_number, "event must be a JSON object")
        safe_event, count = redact_event(event)
        redacted_hasher.update(canonical_json(safe_event).encode("utf-8"))
        redacted_hasher.update(b"\n")
        events.append(event)
        redactions += count
    return Trace(
        events=tuple(events),
        source_lines=source_lines,
        blank_lines=blank_lines,
        raw_sha256=raw_hasher.hexdigest(),
        redacted_sha256=redacted_hasher.hexdigest(),
        redactions=redactions,
    )


def read_jsonl(handle: IO[str]) -> Iterable[dict[str, Any]]:
    """Compatibility iterator for callers that only need parsed events."""

    yield from read_trace(handle).events


def query_events(
    events: Iterable[dict[str, Any]],
    *,
    event_type: str | None = None,
    name: str | None = None,
    contains: str | None = None,
    limit: int | None = None,
) -> list[dict[str, Any]]:
    """Filter events using redacted, case-insensitive, deterministic matching."""

    if limit is not None and limit < 1:
        raise ValueError("limit must be greater than zero")
    type_filter = event_type.casefold() if event_type else None
    name_filter = name.casefold() if name else None
    contains_filter = contains.casefold() if contains else None
    matches: list[dict[str, Any]] = []
    for event in events:
        safe_event, _ = redact_event(event)
        if type_filter is not None and str(event.get("type", "")).casefold() != type_filter:
            continue
        if name_filter is not None and str(event.get("name", "")).casefold() != name_filter:
            continue
        if contains_filter is not None and contains_filter not in canonical_json(safe_event).casefold():
            continue
        matches.append(safe_event)
        if limit is not None and len(matches) >= limit:
            break
    return matches


def type_counts(events: Iterable[dict[str, Any]]) -> dict[str, int]:
    """Return stable counts keyed by the event's type field."""

    counts: dict[str, int] = {}
    for event in events:
        event_type = str(event.get("type", "event"))
        counts[event_type] = counts.get(event_type, 0) + 1
    return dict(sorted(counts.items()))


def inspect_trace(trace: Trace) -> dict[str, Any]:
    """Build a redacted integrity summary suitable for logs and CI artifacts."""

    return {
        "schema": "agent-trace/inspect/v1",
        "events": len(trace.events),
        "source_lines": trace.source_lines,
        "blank_lines": trace.blank_lines,
        "redactions": trace.redactions,
        "types": type_counts(trace.events),
        "raw_sha256": trace.raw_sha256,
        "redacted_sha256": trace.redacted_sha256,
    }
