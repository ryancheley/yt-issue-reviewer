<!-- SPECKIT START -->
For additional context about technologies to be used, project structure,
shell commands, and other important information, read the current plan:
specs/002-zizmor-gha-security/plan.md

Active feature: zizmor GHA Security Auditing (002). Add zizmor via
`uvx zizmor@<pinned>` as a dedicated, required CI job auditing
.github/workflows/ (--offline, --persona regular, --min-severity medium);
harden ci.yml with least-privilege permissions, hash-pinned actions, and
persist-credentials: false; add the zizmor check to branch protection.

Shipped: Related Issue Finder (001). Python 3.14+, uv, click CLI, SQLite
(Datasette-friendly), self-hosted Ollama for embeddings + optional labels,
YouTrack access only via the youtrack_cli package; read-only, no hosted AI.
<!-- SPECKIT END -->
