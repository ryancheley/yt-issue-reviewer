# Contract: CI Security-Audit Job & Workflow Hardening

Defines the observable contract of the `zizmor` CI job and the hardening required of every
workflow. "Contract tests" here are CI-observable behaviors and a local audit run.

## `zizmor` job contract

**Trigger**: runs on every `pull_request` and every `push` to `main` (same triggers as the
existing `check` job).

**Invocation** (the gating step):

```text
uvx zizmor@${ZIZMOR_VERSION} --offline --persona regular --min-severity medium \
    --format github .github/workflows/
```

- `ZIZMOR_VERSION` is pinned (e.g. `1.26.1`).
- Positional path `.github/workflows/` → audits ALL workflow files (new files auto-covered).
- The gating step MUST NOT use `--format sarif` (SARIF always exits 0 — see research R2).

**Permissions**: the job declares `permissions: { contents: read }`. No token is passed
(offline).

**Pass/fail semantics**:

| Condition | zizmor exit | Job result |
|-----------|-------------|------------|
| No findings ≥ medium | 0 | pass |
| Finding(s) ≥ medium | 13 or 14 | **fail** |
| Tool/argument/collection error | 1–3 | **fail** (never a silent skip — FR-008) |

**Status context name**: the job's context is `zizmor`. It MUST be added to the repo's
required status checks so a failure blocks merge (alongside `check`).

## Workflow hardening contract (applies to `ci.yml`)

Every workflow MUST satisfy, so the baseline audit is clean (FR-006, FR-007):

1. **Top-level** `permissions: {}` (deny-all by default).
2. **Each job** declares explicit least-privilege `permissions` (e.g. `contents: read`).
3. **Every `uses:`** is pinned to a full commit SHA with a trailing `# vX.Y.Z` comment
   (satisfies `unpinned-uses`).
4. **`actions/checkout`** sets `with: { persist-credentials: false }` (satisfies
   `artipacked`).

The existing `check` job MUST keep its context name `check` (branch-protection dependency)
and MUST continue to run ruff, ruff format, ty, and pytest unchanged.

## Branch-protection contract

After implementation, `main`'s required status checks MUST be `["check", "zizmor"]`
(strict). Enforce-admins and existing PR settings remain unchanged.

## Contract checks (how to verify)

1. **Clean baseline**: `uvx zizmor@$V --offline .github/workflows/` exits 0 locally and in
   CI (SC-002).
2. **Gate fires**: introducing a medium+ finding (e.g. a `template-injection` via
   `run: echo "${{ github.event.pull_request.title }}"`) makes the `zizmor` job exit
   non-zero and the check fail (SC-001). Revert restores green.
3. **Automatic**: the job appears on PRs and on pushes to `main` with no manual step
   (SC-003).
4. **Least privilege**: every job in `ci.yml` has an explicit `permissions` block (SC-004).
5. **Required check**: `gh api .../branches/main/protection` lists `zizmor` among required
   contexts.
