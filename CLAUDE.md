<!-- SPECKIT START -->
For additional context about technologies to be used, project structure,
shell commands, and other important information, read the current plan:
specs/015-fix-backslash-newline-escape/plan.md

Active feature: Repair a backslash immediately before a newline in `yt` JSON
(015), resolving issue #57. `analyze` still crashes with `Invalid \escape`
when a description ends a line with a literal backslash (yt emits `\` before a
raw newline). The #48 repair `_escape_stray_backslashes` misses it: its
`\\(.)` branch uses `.`, which doesn't match a newline. Fix: add
`flags=re.DOTALL` to the `re.sub` so `\<newline>` → `\\<newline>` (escaped
backslash + raw newline, tolerated by strict=False). Valid escapes and the
#48 cases unaffected. Narrow sub-case of #48; reported on 0.3.9 (line 5439
col 79 on a live NGDEV project).

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
(013) `--version` flag (#51): Click `version_option` on the main group,
`-V` alias, reusing the single-source `__version__`.
(014) Surface `yt`'s stdout in failure messages (#54): `_proc_output` joins
stdout+stderr so the real reason (e.g. "Not authenticated") is shown.
<!-- SPECKIT END -->
