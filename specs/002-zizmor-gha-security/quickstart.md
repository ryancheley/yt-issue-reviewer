# Quickstart & Validation Guide: zizmor GHA Security Auditing

Proves the audit works: a clean baseline, an automatic gate, and a negative test.

## Prerequisites

- [uv](https://docs.astral.sh/uv/) installed (already used by this project).
- Network access to fetch the pinned zizmor wheel the first time (`uvx` caches it).

## Run the audit locally (clean-baseline check)

```bash
# From the repo root, same invocation CI uses:
uvx zizmor@1.26.1 --offline --persona regular --min-severity medium .github/workflows/
echo "exit: $?"
```

**Expected**: no findings at/above medium, exit `0`. (Codes 11–14 mean findings; 1–3 mean a
tool/usage error.)

If zizmor reports `unpinned-uses`, `excessive-permissions`, or `artipacked`, apply the
remediations from `research.md` (hash-pin actions, add `permissions:`, set
`persist-credentials: false`) until the run is clean — do **not** suppress unless a real
finding is truly unavoidable (and then add a justified `zizmor.yml`/inline entry).

## Validation scenarios

### US1 — the gate blocks insecure workflow changes (negative test)

1. On a scratch branch, add a deliberately unsafe step to a workflow, e.g.:
   ```yaml
   - name: unsafe
     run: echo "Title is ${{ github.event.pull_request.title }}"
   ```
2. Run the audit locally:
   ```bash
   uvx zizmor@1.26.1 --offline --min-severity medium .github/workflows/
   ```
   **Expected**: a `template-injection` finding and a **non-zero exit** (gate fails).
3. Push the branch and open a PR → the `zizmor` check fails and, via branch protection, the
   PR is not mergeable.
4. Revert the unsafe step → audit exits 0, check passes, PR mergeable. (SC-001)

### US2 — existing workflows pass cleanly

```bash
uvx zizmor@1.26.1 --offline --min-severity medium .github/workflows/   # exit 0 (SC-002)
grep -nE '^\s*permissions:' .github/workflows/ci.yml                    # each job has one (SC-004)
```

### US1/US3 — automatic + policy visible

- Confirm the `zizmor` job appears on the PR checks and on pushes to `main` (no manual step,
  SC-003).
- Confirm the threshold is explicit in `ci.yml` (`--min-severity medium`) and reviewable.
- Confirm the required status checks include `zizmor`:
  ```bash
  gh api repos/ryancheley/yt-issue-reviewer/branches/main/protection \
    --jq '.required_status_checks.contexts'
  # → ["check","zizmor"]
  ```

### Tool-failure is not a silent pass (SC-006)

Run with a bogus flag and confirm a non-zero exit (the CI check would fail, not skip):
```bash
uvx zizmor@1.26.1 --definitely-not-a-flag .github/workflows/; echo "exit: $?"   # non-zero
```

## CI reference

The audit is the `zizmor` job in `.github/workflows/ci.yml`; the existing `check` job
(ruff, ruff format, ty, pytest) is unchanged except for hardening (permissions, pinned
actions, `persist-credentials: false`). See `contracts/ci-audit.md` for the full contract.
