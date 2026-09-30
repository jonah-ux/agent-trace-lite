"""Built-in, synthetic demo events used by the installed CLI demo."""

from __future__ import annotations

DEMO_RECORDS = [
    {
        "timestamp": "2026-09-30T12:00:00Z",
        "type": "model",
        "trace_id": "demo-1",
        "provider": "demo",
        "model": "example",
        "prompt": "hello",
        "api_key": "demo-secret-do-not-use",
    },
    {
        "timestamp": "2026-09-30T12:00:01Z",
        "type": "subprocess",
        "trace_id": "demo-1",
        "command": "printf 'offline demo'",
        "exit_code": 0,
    },
    {
        "timestamp": "2026-09-30T12:00:02Z",
        "type": "tool",
        "trace_id": "demo-1",
        "name": "search",
        "arguments": {"q": "agent trace"},
    },
    {
        "timestamp": "2026-09-30T12:00:03Z",
        "type": "transfer",
        "trace_id": "demo-1",
        "direction": "outbound",
        "bytes": 128,
    },
    {
        "timestamp": "2026-09-30T12:00:04Z",
        "type": "guardrail",
        "trace_id": "demo-1",
        "policy": "safe-output",
        "result": "allow",
    },
    {
        "timestamp": "2026-09-30T12:00:05Z",
        "type": "error",
        "trace_id": "demo-1",
        "message": "illustrative error",
    },
]
