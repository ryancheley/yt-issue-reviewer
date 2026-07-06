<!-- SPECKIT START -->
For additional context about technologies to be used, project structure,
shell commands, and other important information, read the current plan:
specs/005-install-cli-fixes/plan.md

Active feature: Cross-platform install & CLI robustness fixes (005),
resolving issues #22/#23/#24. No analysis-behavior change. (a) Drop
youtrack-cli from [project].dependencies — the code never imports it, only
shells out to the `yt` binary on PATH (a documented prerequisite); this
removes the docker→pywin32 native chain that breaks Windows installs.
Regenerate uv.lock. (b) Force UTF-8 subprocess I/O (PYTHONUTF8=1 +
PYTHONIOENCODING=utf-8, encoding="utf-8") on both `yt` invocations in
ingest/youtrack.py so a non-ASCII byte doesn't crash on a cp1252 console.
(c) Make --db/--ollama-host/--config accept documented post-subcommand
placement across all subcommands (shared decorator; subcommand value wins),
preserving Config.load precedence.

Shipped: (001) Related Issue Finder — uv, click CLI, SQLite
(Datasette-friendly), self-hosted Ollama, read-only, no hosted AI.
(002) zizmor GHA security audit as a required CI check + hardened ci.yml.
(003) Dev infrastructure: Dependabot, tag-driven PyPI release workflow,
Markdown docs, justfile whose `check` recipe == the CI gate.
(004) Python 3.11+ support: floor lowered to >=3.11, CI matrix 3.11–3.14.
<!-- SPECKIT END -->
