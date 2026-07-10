# Research: Surface `yt`'s stdout in failure messages

Reproduced live against youtrack-cli 0.24.5 before speccing.

## Decision: Combine non-empty stdout + stderr in the failure message

- **Decision**: Add `_proc_output(proc)` that returns the non-empty of `proc.stdout.strip()`
  and `proc.stderr.strip()` joined by a newline, and use it in both `yt` failure branches:
  - `check_available()` — the `yt auth token --show` returncode-nonzero path.
  - `_fetch_page()` — the `yt issues list` returncode-nonzero path.
- **Rationale**: `yt` writes actionable reasons to stdout, not always stderr. Confirmed against
  0.24.5: an unauthenticated `yt issues list` prints `❌ Not authenticated` to **stdout**, while
  stderr only had `Error: Failed to list issues`. The tool currently shows only stderr, so the
  real reason is lost. Joining both, dropping empties, keeps messages clean when only one stream
  has content (FR-003).
- **Observed** (0.24.5, before `yt auth login`):
  - `yt issues list ...` → stdout: `❌ Not authenticated` / stderr: `Error: Failed to list issues`.
- **Alternatives considered**:
  - Show stdout only — rejected: stderr sometimes carries useful detail too; show both.
  - Inline the join at each of the two sites — rejected: a one-line helper avoids duplication
    (VI. Simplicity).

## Preserve existing behavior

- `check_available()` keeps its `"youtrack-cli is not authenticated. Run \`yt auth login\`."`
  prefix; only the appended stream text changes from stderr-only to stdout+stderr (FR-004).
- The success path (`returncode == 0`) is untouched; output still flows to `_load_json_issues`
  (FR-005).

## Out of scope

- The auth-detection gap itself (0.24.5's `yt auth token --show` returns 0 even when not
  authenticated, so `check_available` may not catch it — the failure then surfaces at fetch
  time). This change makes that fetch-time failure legible; changing the auth *check* is a
  separate concern.
- The upstream youtrack-cli auth regression (upgrade invalidates stored credentials) — filed
  separately on yt-cli.
