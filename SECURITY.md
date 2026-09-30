# Security policy

## Reporting a vulnerability

Please do not open a public issue for a suspected vulnerability. Email the maintainers through the security contact listed in the repository's GitHub Security tab, including a description, reproduction steps, affected version, and impact. We will acknowledge reports as soon as practical.

## Scope and safety

agent-trace-lite is designed for offline analysis. It does not make network requests or execute commands while normalizing traces or rendering HTML. Treat input traces as sensitive: redact them before sharing, use the built-in output redaction, and do not commit real credentials or customer data. The optional `sandbox` extra is intentionally not enabled by default and may install platform-specific tooling in downstream applications.

Security fixes should include a regression test where practical. Please allow maintainers time to coordinate a fix before public disclosure.
