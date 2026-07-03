# Phase 0 Research: zizmor GitHub Actions Security Auditing

Facts verified against docs.zizmor.sh and the `woodruffw/zizmor` repo (zizmor **v1.26.1**,
June 2026). All Technical Context unknowns are resolved.

## R1. How to run zizmor in a uv-based CI

**Decision**: Run `uvx zizmor@<pinned-version>` as a dedicated CI step. Pin the version in
an env var (e.g. `ZIZMOR_VERSION: 1.26.1`).

**Rationale**: zizmor is on PyPI (a Rust binary shipped as wheels), so `uvx` fetches a
prebuilt binary — fast, no compile, no new language runtime, and nothing added to
`pyproject.toml`. Docs explicitly recommend `uvx "zizmor@${ZIZMOR_VERSION}"` for CI.
Pinning keeps CI reproducible (Constitution IV).

**Alternatives considered**:
- Official `zizmorcore/zizmor-action` — clean, but adds another third-party action to pin
  and audit; `uvx` reuses tooling we already have (Constitution VI).
- `uv tool install` / `pip install` — unnecessary persistence; `uvx` is ephemeral.

## R2. Invocation, threshold, and exit-code semantics

**Decision**: `uvx zizmor@$V --offline --persona regular --min-severity medium --format github .github/workflows/`

**Rationale**:
- **Positional path** `.github/workflows/` audits every workflow file (directory scan
  respects `.gitignore`), so new workflows are covered automatically (FR-005).
- **`--min-severity medium`** reports findings at medium/high and drops low/informational
  noise; the requested starting threshold (FR-003, FR-009).
- **`--persona regular`** = high-signal, actionable findings (default persona).
- **`--format github`** emits GitHub annotations so findings surface inline on the PR.
- **Exit codes**: 0 = clean; **11–14 = findings** (11 informational … 14 high). With
  `--min-severity medium`, only medium/high findings are reported, so the job exits
  non-zero (13/14) exactly when a gating finding exists → CI fails (FR-003, SC-001).
  A tool/argument error exits 1–3, which also fails the job (FR-008, SC-006).

**Gotcha recorded**: `--format=sarif` and successful `--fix` runs always exit 0 even with
findings. So the **gating** step MUST NOT use SARIF output. If SARIF upload to code
scanning is added later, it must be a *separate, non-gating* step.

**Alternatives considered**: default `--min-severity` (informational) — too noisy for a
first rollout; medium is the agreed starting policy and can be tightened later (US3).

## R3. Offline mode and tokens

**Decision**: Run with `--offline`; do not pass any GitHub token.

**Rationale**: Offline disables all network calls but still fully audits local workflow
files — which is all we need for our own workflows. It removes the need for `GH_TOKEN`,
keeps the audit deterministic and network-free, and matches the project's
no-external-egress posture (Constitution I). Online audits (which resolve action refs
remotely) would need a token and add nondeterminism.

**Alternatives considered**: Online mode with the ambient `GITHUB_TOKEN` — deferred; note
as a possible follow-up if we later want online-only audits (e.g., stronger ref
resolution). Not needed for the baseline.

## R4. Expected findings on the current `ci.yml` and remediations

The current workflow uses `actions/checkout@v5` and `astral-sh/setup-uv@v6` with no
`permissions:` block. Anticipated findings and fixes:

| Finding (rule) | Cause | Remediation |
|----------------|-------|-------------|
| `unpinned-uses` | actions pinned to tags (`@v5`, `@v6`) — since v1.20 the default policy requires full-SHA hash pins | Pin each action to a full commit SHA with a trailing `# vX` version comment |
| `excessive-permissions` | no `permissions:` block → jobs inherit broad default `GITHUB_TOKEN` | Add top-level `permissions: {}` and per-job `permissions: { contents: read }` |
| `artipacked` | `actions/checkout` persists credentials by default (pre-v6) | Add `with: { persist-credentials: false }` to the checkout step |

**Decision**: Remediate all three so the baseline is clean at `--min-severity medium`
(indeed at any severity) with **no suppressions** (FR-006, SC-002). `template-injection`
and `cache-poisoning` are not expected to fire (no untrusted `${{ }}` in run contexts, no
release/publish caching).

**Rationale**: Fixing the root causes is preferable to suppressing (Constitution IV /
FR-010). Hash-pinning is the strongest supply-chain posture and satisfies `unpinned-uses`
outright.

**Follow-up noted**: Hash pins are harder to update by hand — recommend enabling Dependabot
for `github-actions` later so pinned SHAs are bumped automatically (out of scope here).

## R5. Config file and suppressions

**Decision**: Do **not** add `zizmor.yml` unless a real, unavoidable finding remains after
remediation. If one does, use `rules.<audit-id>.ignore` (with `file:line`) or an inline
`# zizmor: ignore[<rule>] <justification>` comment, always with a written justification
(FR-010, SC-005).

**Rationale**: The baseline is expected to be clean, so no config is needed (Constitution
VI — don't add files without cause). Keeping suppressions justified preserves transparency.

**Config schema (for reference, if needed)**:
```yaml
rules:
  <audit-id>:
    ignore:
      - ci.yml:42          # file[:line[:column]] — MUST be justified in a nearby comment
```
Inline: `uses: ... # zizmor: ignore[unpinned-uses] pinned by digest below`.

## R6. CI job placement and branch protection

**Decision**: Add a **separate `zizmor` job** to `ci.yml` (parallel to `check`) and add
`zizmor` to the repo's required status checks so it gates merges.

**Rationale**: A dedicated job gives a distinct, readable check name and runs in parallel;
keeping it out of `check` leaves the existing required context (`check`) untouched. Because
branch protection currently requires only `check`, the implementation must explicitly add
`zizmor` to the required contexts (`["check", "zizmor"]`) — otherwise a failing audit
wouldn't block merge (FR-003, SC-001, spec assumption on branch protection).

**Alternatives considered**: Add zizmor as a step inside `check` — simplest (no
branch-protection change) and still gates, but muddies the single job and gives a less
clear signal. Chosen the dedicated job for clarity; the branch-protection update is a small,
explicit task.

## Resolved unknowns summary

| Unknown | Resolution |
|---------|------------|
| Run method | `uvx zizmor@1.26.1` (ephemeral, no project dep) |
| Threshold | `--min-severity medium`, `--persona regular` |
| Network/token | `--offline`, no token |
| Gating | Non-zero exit (11–14 / 1–3); do NOT gate on SARIF output |
| Expected findings | `unpinned-uses`, `excessive-permissions`, `artipacked` |
| Remediation | Hash-pin actions, `permissions: {}` + `contents: read`, `persist-credentials: false` |
| Config | None unless a real finding needs a justified suppression |
| Placement | Dedicated `zizmor` job; add to required status checks |
