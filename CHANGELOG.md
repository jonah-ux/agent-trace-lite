# Changelog

## Unreleased

- add deterministic `inspect/v1` integrity summaries with raw and redacted digests
- add filtered `query/v1` output with recursive key and inline credential redaction
- fail closed on malformed JSONL and non-object events instead of silently dropping input
- expose the parsing and redaction primitives for Python consumers
- add bounded input bytes, events, and line length guards with stable error envelopes
- stream limited queries and stop after the requested number of redacted matches

## 0.1.0 - 2026-09-30

Initial focused release with a stable CLI contract and synthetic demo.
