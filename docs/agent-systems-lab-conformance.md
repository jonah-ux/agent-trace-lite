# Agent Systems Lab trace conformance

Agent Trace Lite remains the owner of the local `agent-trace/v1` view and
`agent-trace/inspect/v1` summary. This fixture and test make its redaction,
digest, query, and refusal boundaries explicit without importing Agent Proof at
runtime.

The owner proves deterministic raw/redacted digests, recursive redaction of
sensitive keys and inline credentials, safe query output, and fail-closed
handling of malformed or non-object JSONL lines. The raw source remains the
caller's local responsibility; the downstream Agent Proof adapter owns any
allowlisted interop projection.

Run the focused conformance test from a fresh checkout. The fixtures contain
synthetic secrets only.
