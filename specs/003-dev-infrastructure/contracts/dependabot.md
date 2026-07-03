# Contract: Dependabot update configuration

**File**: `.github/dependabot.yml`

## Shape

```yaml
version: 2
updates:
  - package-ecosystem: "uv"
    directory: "/"
    schedule:
      interval: "monthly"
    groups:
      python-dependencies:
        patterns: ["*"]
  - package-ecosystem: "github-actions"
    directory: "/"
    schedule:
      interval: "monthly"
    groups:
      github-actions:
        patterns: ["*"]
```

## Guarantees

- Two ecosystems: `uv` (reads `pyproject.toml` + `uv.lock`) and `github-actions`.
- Monthly cadence; each ecosystem produces a single **grouped** PR.
- Action-update PRs bump the pinned SHA and preserve the `# vX.Y.Z` comment.
- No secrets referenced; nothing to store.
- PRs run the existing required checks (`check` + `zizmor`) and merge only when green.

## Verification

1. `.github/dependabot.yml` is valid YAML with the two ecosystems, monthly + grouped.
2. `uv.lock` is committed (present).
3. (Post-merge, GitHub-side) Dependabot lists the two update configs under Insights →
   Dependency graph → Dependabot, with no parse errors.
