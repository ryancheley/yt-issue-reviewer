<!-- SPECKIT START -->
For additional context about technologies to be used, project structure,
shell commands, and other important information, read the current plan:
specs/003-dev-infrastructure/plan.md

Active feature: Developer Infrastructure & Release Readiness (003).
Bundles Dependabot (uv + github-actions, monthly, grouped), a tag-driven
PyPI release workflow (uv build + Trusted Publishing OIDC, TestPyPI→PyPI,
GitHub Release), Markdown docs (README + CONTRIBUTING + docs/), and a
justfile whose `check` recipe == the CI gate. New workflows stay
least-privilege + hash-pinned so the zizmor audit stays green. No src/
changes; real PyPI publish + tag push are maintainer actions (out of scope).

Shipped: (001) Related Issue Finder — Python 3.14+, uv, click CLI, SQLite
(Datasette-friendly), self-hosted Ollama, read-only, no hosted AI.
(002) zizmor GHA security audit as a required CI check + hardened ci.yml.
<!-- SPECKIT END -->
