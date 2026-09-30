"""Core normalization and deterministic redaction for JSONL traces."""

from __future__ import annotations

from collections.abc import Iterable, Iterator, Mapping
from datetime import datetime, timezone
import hashlib
import json
import math
import re
from typing import Any

EVENT_TYPES = frozenset({"model", "tool", "subprocess", "transfer", "guardrail", "error"})
SENSITIVE_KEY_RE = re.compile(
    r"(?:api[_-]?key|access[_-]?token|auth(?:orization)?|cookie|credential|password|passwd|secret|private[_-]?key|session[_-]?token|set-cookie|webhook)",
    re.IGNORECASE,
)
SENSITIVE_VALUE_RE = re.compile(
    r"(?ix)(?:bearer\s+[a-z0-9._~+/=-]{8,}|(?:sk|ghp|xox[baprs]-)[a-z0-9_-]{8,}|(?:api[_-]?key|token|secret|password)\s*[:=]\s*[^\s,;]+)"
)
REDACTED = "[REDACTED]"


def parse_timestamp(value: Any) -> tuple[float, str]:
    """Return a UTC epoch value and stable ISO-8601 display timestamp."""
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        epoch = float(value)
    elif isinstance(value, str) and value.strip():
        text = value.strip().replace("Z", "+00:00")
        try:
            parsed = datetime.fromisoformat(text)
        except ValueError:
            epoch = float("inf")
        else:
            if parsed.tzinfo is None:
                parsed = parsed.replace(tzinfo=timezone.utc)
            epoch = parsed.astimezone(timezone.utc).timestamp()
    else:
        epoch = float("inf")
    if epoch == float("inf") or not math.isfinite(epoch):
        return float("inf"), ""
    try:
        display = datetime.fromtimestamp(epoch, timezone.utc).isoformat(timespec="milliseconds").replace("+00:00", "Z")
    except (OverflowError, OSError, ValueError):
        return float("inf"), ""
    return epoch, display


def _redact_string(value: str) -> str:
    return SENSITIVE_VALUE_RE.sub(REDACTED, value)


def redact(value: Any, *, key: str | None = None) -> Any:
    """Recursively redact secret-like keys and common token values."""
    if key and SENSITIVE_KEY_RE.search(key):
        return REDACTED
    if isinstance(value, Mapping):
        return {str(k): redact(v, key=str(k)) for k, v in value.items()}
    if isinstance(value, list):
        return [redact(item) for item in value]
    if isinstance(value, tuple):
        return [redact(item) for item in value]
    if isinstance(value, str):
        return _redact_string(value)
    return value


def _event_type(record: Mapping[str, Any]) -> str:
    raw = record.get("type", record.get("event", record.get("kind", "event")))
    event_type = str(raw).strip().lower()
    aliases = {"llm": "model", "generation": "model", "command": "subprocess", "process": "subprocess", "policy": "guardrail", "exception": "error"}
    return aliases.get(event_type, event_type if event_type in EVENT_TYPES else "event")


def normalize_record(record: Mapping[str, Any], index: int) -> dict[str, Any]:
    """Normalize one provider-neutral record without mutating its input."""
    cleaned = redact(dict(record))
    epoch, timestamp = parse_timestamp(cleaned.get("timestamp", cleaned.get("time", cleaned.get("ts"))))
    event_type = _event_type(cleaned)
    event_id = str(cleaned.get("id", f"event-{index:06d}"))
    trace_id = str(cleaned.get("trace_id", cleaned.get("traceId", "default")))
    normalized: dict[str, Any] = {
        "id": event_id,
        "trace_id": trace_id,
        "type": event_type,
        "timestamp": timestamp,
        "sequence": index,
        "data": {str(key): value for key, value in cleaned.items() if key not in {"id", "trace_id", "traceId", "type", "event", "kind", "timestamp", "time", "ts"}},
    }
    if epoch != float("inf"):
        normalized["_sort_timestamp"] = epoch
    return normalized


def normalize_records(records: Iterable[Mapping[str, Any]]) -> list[dict[str, Any]]:
    """Normalize and stably sort records by timestamp, then source sequence."""
    normalized = [normalize_record(record, index) for index, record in enumerate(records)]
    normalized.sort(key=lambda item: (item.get("_sort_timestamp", float("inf")), item["sequence"], item["id"]))
    for item in normalized:
        item.pop("_sort_timestamp", None)
    return normalized


def read_jsonl(lines: Iterable[str]) -> Iterator[dict[str, Any]]:
    """Parse non-empty JSONL lines, reporting line numbers for malformed input."""
    for line_number, line in enumerate(lines, 1):
        if not line.strip():
            continue
        try:
            value = json.loads(line)
        except json.JSONDecodeError as exc:
            raise ValueError(f"invalid JSON on line {line_number}: {exc.msg}") from exc
        if not isinstance(value, Mapping):
            raise ValueError(f"line {line_number}: each event must be a JSON object")
        yield dict(value)


def stable_json(value: Any) -> str:
    """Serialize JSON in a reproducible form."""
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def content_hash(events: Iterable[Mapping[str, Any]]) -> str:
    """Return a SHA-256 hash of canonical normalized events."""
    payload = "\n".join(stable_json(event) for event in events).encode()
    return hashlib.sha256(payload).hexdigest()
