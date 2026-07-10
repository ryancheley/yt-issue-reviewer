<!-- SPECKIT START -->
For additional context about technologies to be used, project structure,
shell commands, and other important information, read the current plan:
specs/013-add-version-flag/plan.md

Active feature: `--version` flag for the CLI (013), resolving issue #51.
`yt-issue-reviewer --version` errors today. Fix: attach Click's built-in
`@click.version_option(__version__, "-V", "--version", prog_name=
"yt-issue-reviewer")` to the `main` group in cli.py, importing `__version__`
(already a single source of truth read from installed metadata in
__init__.py). `-v` is already `--verbose`, so the short alias is capital `-V`.
CliRunner test asserts `--version`/`-V` print `yt_issue_reviewer.__version__`
and exit 0.

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
(011) Chunked fetch via created-date cursor (#45): bounded `--top` requests so
no single `yt` request exceeds a ~20s gateway limit; replaces `--all`.
(012) Tolerate invalid backslash escapes in `yt` JSON (#48): repair stray
backslashes and retry in `_load_json_issues`; happy path untouched.
<!-- SPECKIT END -->
