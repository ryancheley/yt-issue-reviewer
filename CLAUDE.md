<!-- SPECKIT START -->
For additional context about technologies to be used, project structure,
shell commands, and other important information, read the current plan:
specs/010-fetch-all-issues/plan.md

Active feature: Fetch every issue in a project, not just the first page
(010), resolving issue #42. `analyze` silently ingests at most 100 issues
per project — `CliYouTrackSource._fetch_project` runs `yt issues list`
without a pagination flag and yt's `--page-size` defaults to 100, so issues
past the first page are dropped (surfaced on a large Jira-imported project on
a remote instance). Fix: add `--all` to the `yt issues list` command so yt
pages through the full result set; client-side state/date filters already run
over the complete set, so they compose unchanged. One added CLI arg + one
regression test asserting the issued command includes `--all`.

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
(009) `--state open` returns all genuinely-open issues (#39): drop the
unreliable server-side `yt --state Open`; the client-side `_matches_state`
filter is the sole authority for open vs resolved.
<!-- SPECKIT END -->
