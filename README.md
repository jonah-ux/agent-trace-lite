# Agent Trace Lite

![offline agent trace viewer workflow](docs/header.svg)

**Turn JSONL events into a clean, redacted local timeline.**

[![CI](https://github.com/jonah-ux/agent-trace-lite/actions/workflows/ci.yml/badge.svg)](https://github.com/jonah-ux/agent-trace-lite/actions/workflows/ci.yml)
[![Python](https://img.shields.io/badge/python-3.11%2B-3776ab)](https://www.python.org/)
[![License](https://img.shields.io/badge/license-MIT-22c55e)](LICENSE)

Agent Trace Lite turns line-oriented event logs into a small HTML timeline. Sensitive-looking
keys such as `token`, `secret`, and `password` are redacted in the rendered view, while the
original JSONL remains under your control on disk.

## Try it in 30 seconds

```bash
python -m pip install git+https://github.com/jonah-ux/agent-trace-lite.git@main
python demos/demo.py
```

Point it at any JSONL event stream:

```bash
agent-trace view events.jsonl --html trace.html
open trace.html
```

## See it work

The demo turns two local events into a redacted HTML artifact and reports exactly what it wrote (the temporary path varies per run):

```json
{"schema":"agent-trace/v1","events":2,"html":"<temporary>/trace.html"}
```

## Related tools

Use [Chatlens](https://github.com/jonah-ux/chatlens) to find the session, [Agent Proof](https://github.com/jonah-ux/agent-proof) to record the investigation, and [Context Pack](https://github.com/jonah-ux/context-pack) to bound the repository context alongside the trace.

The command prints an `agent-trace/v1` summary with the event count and output path. It is a
small local viewer for debugging agent runs, not a hosted telemetry system.

## Development

```bash
python -m unittest discover -s tests
python -m build --sdist --wheel
python demos/demo.py
```

MIT licensed.
