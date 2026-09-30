# Contributing

Thanks for helping improve agent-trace-lite.

1. Create a focused branch from the default branch.
2. Keep changes provider-neutral, offline, and dependency-free at runtime.
3. Add or update tests for behavior changes, especially redaction and ordering.
4. Run `python -m pytest` and `python -m build` before opening a pull request.
5. Describe input compatibility, security implications, and exact verification in the pull request.

Please do not include credentials, private traces, generated build artifacts, or unrelated formatting changes. Bug reports should include a minimal synthetic JSONL fixture and the expected normalized output when possible. See [SECURITY.md](SECURITY.md) for private vulnerability reports.
