# Research: Fetch issues in bounded chunks

All findings verified empirically against a live instance behind a ~20s gateway and a local
instance with `yt` 0.24.2.

## Decision: Page by a creation-date cursor using `yt --top` + `--query`

- **Decision**: In `_fetch_project`, loop bounded requests:
  `yt issues list --format json --top PAGE --query "project: <P> [created: <cursor> ..] sort by: created asc"`.
  Advance `cursor` to the newest `created` date in the just-fetched page **minus one day**;
  stop when a page returns `< PAGE` issues; de-duplicate by issue id across pages.
- **Rationale**: The gateway kills any request > ~20s. Only `--top N` bounds the server-side
  fetch, and it has no offset, so paging must be driven by a query filter. `created` is the
  only monotonic, filterable, sortable field `yt` exposes. Measured: `--top 100` ≈ 6s,
  `--top 250` ≈ 8s (safe); `--top 500` ≈ 22s → killed. `PAGE ≈ 200` stays well under the limit.
- **Building blocks verified**:
  - `sort by: created asc` returns oldest-first (`--top 3` → NGDEV-1,2,3).
  - `--top N` bounds output to the first N.
  - `created: 2020-01-01 .. 2030-01-01` filters correctly (returned all issues).

## Decision: Cursor = last page's newest created date **minus one day**, with dedup

- **Decision**: Next page's lower bound = (newest `created` in the page, as `YYYY-MM-DD`) − 1 day.
- **Rationale**: `created:` query bounds are **day-granular and timezone-sensitive** (a single-day
  `created: 2026-07-07 .. 2026-07-08` returned 0 for issues stored that day, due to tz skew).
  Subtracting a day guarantees the next window **overlaps** the previous rather than leaving a
  gap, so no issue is skipped across timezone differences. The overlap re-returns already-seen
  issues, which are removed by id-based de-duplication.
- **Alternatives considered**:
  - Exact-date cursor (no minus-a-day) — rejected: timezone skew could skip issues at the boundary.
  - Datetime/sub-day cursor — rejected: `yt`'s `created:` query does not support time-of-day
    (a datetime bound returned 0 / errored).

## Decision: Same-date stall raises `YouTrackUnavailable`, not an infinite loop

- **Decision**: If a full page (`PAGE` issues) yields **no new** ids (all already seen), stop and
  raise the operator-facing `YouTrackUnavailable` explaining that more than `PAGE` issues share
  one creation date on this connection, with remediation (narrow via `--since/--until`, or use a
  faster network).
- **Rationale**: With a day-granular cursor, > `PAGE` issues on a single day would make the window
  never advance. A clear, loud failure beats an infinite loop or silent truncation (Constitution IV).
  With `PAGE ≈ 200`, this only triggers for > 200 issues created on one calendar day on a gated
  connection — rare in practice.

## Rejected alternatives (why not simpler/other approaches)

- **Keep `--all`** (#42) — it is the bug: one long request the gateway kills.
- **`--page-size` / `--after-cursor` / `--start-page`** — verified useless in `--format json`
  mode: `--page-size` is ignored (returns everything), no cursor is exposed, `--start-page`
  is display-only (all pages returned the same issues).
- **Direct REST with `$top`/`$skip`** — robust, but needs the API token, which is stored
  encrypted in the OS keyring and not retrievable from the tool's own environment; would also
  re-couple to `youtrack-cli` internals (removed as a dependency in #22). Rejected per
  Constitution III/VI.
- **Field trimming (`--profile minimal` / `--fields`)** — `minimal` drops `description` (needed
  for analysis); explicit `--fields` gave no reliable speedup. Does not bound request size.

## Out of scope

- Making `--since`/`--until` a paging mechanism (they already filter; unchanged here).
- Parallel page fetches (sequential is simple and the bottleneck is the per-request limit, not throughput).
