<!-- SPECKIT START -->
For additional context about technologies to be used, project structure,
shell commands, and other important information, read the current plan:
specs/004-python-311-support/plan.md

Active feature: Support Python 3.11+ (004). Lower the floor from >=3.14 to
>=3.11 so the tool installs on 3.11–3.14. Packaging/CI/governance only:
requires-python + classifiers + ty target in pyproject.toml, regenerate
uv.lock, convert the CI check job to a matrix over 3.11–3.14 (fail-fast:
false; zizmor stays single-run + green), and amend the constitution's
"3.12+" wording to "3.11+" (bump to 1.1.0). src/ audited clean — no code
changes expected (uses `from __future__ import annotations`, tomllib is
3.11 stdlib, no PEP 695). Tracked in issue #19.

Shipped: (001) Related Issue Finder — uv, click CLI, SQLite
(Datasette-friendly), self-hosted Ollama, read-only, no hosted AI.
(002) zizmor GHA security audit as a required CI check + hardened ci.yml.
(003) Dev infrastructure: Dependabot, tag-driven PyPI release workflow,
Markdown docs, justfile whose `check` recipe == the CI gate.
<!-- SPECKIT END -->
