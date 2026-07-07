<!-- SPECKIT START -->
For additional context about technologies to be used, project structure,
shell commands, and other important information, read the current plan:
specs/009-fix-open-state-filter/plan.md

Active feature: `--state open` must return all genuinely-open issues (009),
resolving issue #39. `analyze --state open` drops legitimately-open issues:
`CliYouTrackSource._fetch_project` passes `--state Open` to `yt`, but the
server-side filter is unreliable — for live project THD (issues all
`State=New`) `yt --state Open` returns zero. Mirror of #35 (there yt leaked
resolved issues IN; here it drops open issues OUT). Fix: delete the
`if state == "open": cmd += ["--state", "Open"]` branch so `yt` returns all
issues; the client-side `_matches_state` filter added in #35 (runs
unconditionally in `fetch_issues`) already keeps New/In Progress and drops
Done/Closed/Resolved. Net deletion + one regression test.

Shipped: (001) Related Issue Finder — uv, click CLI, SQLite
(Datasette-friendly), self-hosted Ollama, read-only, no hosted AI.
(002) zizmor GHA security audit as a required CI check + hardened ci.yml.
(003) Dev infrastructure: Dependabot, tag-driven PyPI release workflow,
Markdown docs, justfile whose `check` recipe == the CI gate.
(004) Python 3.11+ support: floor lowered to >=3.11, CI matrix 3.11–3.14.
(005) Cross-platform install & CLI robustness (#22/#23/#24): drop youtrack-cli
dep, force UTF-8 subprocess I/O, post-subcommand option placement.
(006) Graceful handling of non-JSON `yt` output (#29): strip leading UTF-8
BOM, tolerate control chars (`strict=False`), re-raise `YouTrackUnavailable`
on non-JSON stdout instead of a raw traceback.
(007) Respect `Status` custom-field state (#35): recognize `Status` in
`parse_issue`; apply the client-side `_matches_state` filter on the `yt`
read path so resolved issues stop leaking under `--state open`.
<!-- SPECKIT END -->
