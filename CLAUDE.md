<!-- SPECKIT START -->
For additional context about technologies to be used, project structure,
shell commands, and other important information, read the current plan:
specs/011-chunked-issue-fetch/plan.md

Active feature: Fetch issues in bounded chunks so slow/gated networks work
(011), resolving issue #45. `analyze` returns 0 issues against instances
behind a gateway that kills any `yt` request > ~20s: `_fetch_project` uses a
single `yt issues list --all` request that exceeds the limit → yt returns
empty → tool reports 0. Fix: replace `--all` with a creation-date cursor loop
of bounded requests — each page fetches the oldest PAGE (~200) issues via
`--top PAGE --query "project: <P> sort by: created asc"`; the cursor advances
to the newest created date in the page minus one day (overlap, never a gap,
survives timezone skew), next page adds `created: <cursor> ..`; dedup by
issue id; stop on a short page. Same-date stall (>PAGE issues share one
created-date) raises YouTrackUnavailable with guidance rather than loop.
`--page-size`/`--after-cursor`/`--start-page` verified useless in JSON mode.

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
(010) Fetch every issue via `yt --all` (#42): pagination so projects with
>100 issues aren't silently capped. (Superseded by 011 for gated networks.)
<!-- SPECKIT END -->
