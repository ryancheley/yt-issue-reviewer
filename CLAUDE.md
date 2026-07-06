<!-- SPECKIT START -->
For additional context about technologies to be used, project structure,
shell commands, and other important information, read the current plan:
specs/006-fix-yt-json-parse/plan.md

Active feature: Graceful handling of non-JSON `yt` output (006), resolving
issue #29 (related to #24). No analysis-behavior change. Harden the shared
`_load_json_issues()` in ingest/youtrack.py: (a) strip a leading UTF-8 BOM
before `json.loads` — `.strip()` doesn't remove it — recovering the exact
`Expecting value: line 1 column 1 (char 0)` crash from issue #29; (b) wrap
`json.loads` so a `JSONDecodeError` (banner/table/warning on stdout) re-raises
the existing operator-facing `YouTrackUnavailable` with a truncated excerpt
instead of a raw traceback. Empty/whitespace behavior preserved. Fixing the
one shared function covers all callers/subcommands.

Shipped: (001) Related Issue Finder — uv, click CLI, SQLite
(Datasette-friendly), self-hosted Ollama, read-only, no hosted AI.
(002) zizmor GHA security audit as a required CI check + hardened ci.yml.
(003) Dev infrastructure: Dependabot, tag-driven PyPI release workflow,
Markdown docs, justfile whose `check` recipe == the CI gate.
(004) Python 3.11+ support: floor lowered to >=3.11, CI matrix 3.11–3.14.
(005) Cross-platform install & CLI robustness (#22/#23/#24): drop youtrack-cli
dep, force UTF-8 subprocess I/O, post-subcommand option placement.
<!-- SPECKIT END -->
