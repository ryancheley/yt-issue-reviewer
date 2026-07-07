<!-- SPECKIT START -->
For additional context about technologies to be used, project structure,
shell commands, and other important information, read the current plan:
specs/007-fix-status-state-filter/plan.md

Active feature: Respect `Status` custom-field state when filtering open
issues (007), resolving issue #35. `analyze --state open` leaks resolved
(`Done`) issues for projects that model workflow state in a custom field
named `Status` instead of the built-in `State`. Two edits in
ingest/youtrack.py: (B) add `"Status"` to the recognized custom-field names
in `parse_issue` (`_extract_custom_field(cf, "State", "Stage", "Status")`),
appended last so `State`/`Stage` still win; (C) apply the existing
`_matches_state` filter in `CliYouTrackSource.fetch_issues` after parsing —
the production path never ran it, so server-side `yt --state Open` (a no-op
for Status-based projects) let `Done` issues through. Sibling issue #34
(JSONDecodeError on multi-line descriptions) is already fixed by the shipped
#29 work (`strict=False`) and needs no change.

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
<!-- SPECKIT END -->
