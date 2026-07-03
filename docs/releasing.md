# Releasing

Releases are published to PyPI by the [`release.yml`](../.github/workflows/release.yml)
workflow when a version tag (`vX.Y.Z`) is pushed. Publishing uses **PyPI Trusted
Publishing (OIDC)** — there is no stored PyPI token.

## One-time setup (maintainer, on PyPI + TestPyPI)

Trusted Publishers must be configured once per index before the first release. This is a
manual account action that cannot be automated by this repo.

On **both** https://pypi.org and https://test.pypi.org → *Your projects → Publishing* (or
"pending publisher" if the project doesn't exist yet), add a GitHub Actions publisher:

| Field | Value |
|-------|-------|
| Owner | `ryancheley` |
| Repository | `yt-issue-reviewer` |
| Workflow filename | `release.yml` |
| Environment | `pypi` (on PyPI) / `testpypi` (on TestPyPI) |

Optionally, in GitHub → *Settings → Environments*, create the `pypi` and `testpypi`
environments and add required reviewers to gate the real publish.

## Cutting a release

1. Bump `version` in `pyproject.toml` (e.g. `0.1.0` → `0.2.0`).
2. Commit via a PR and merge (branch protection + required checks apply).
3. Tag and push:
   ```bash
   git checkout main && git pull
   git tag v0.2.0
   git push origin v0.2.0
   ```

The workflow then:
1. Builds sdist + wheel with `uv build`.
2. Publishes to **TestPyPI** first (`skip-existing: true`) as a dry run.
3. Publishes to **PyPI**.
4. Creates a **GitHub Release** for the tag with auto-generated notes and the artifacts
   attached.

## Verify

```bash
uv tool install yt-issue-reviewer==0.2.0
yt-issue-reviewer --help
```

## Notes

- Version is static (manual bump + matching tag). Dynamic-version-from-tag (hatch-vcs / uv
  dynamic versioning) is a possible future enhancement.
- The release workflow is least-privilege and hash-pinned, and is covered by the required
  `zizmor` audit like every other workflow.
