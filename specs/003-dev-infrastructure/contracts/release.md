# Contract: Release workflow & package metadata

**Files**: `.github/workflows/release.yml`, `pyproject.toml` (`[project]` metadata),
`LICENSE`.

## Release workflow contract

**Trigger**: `on: push: tags: ['v*']`. Top-level `permissions: {}`.

**Job `testpypi`** (runs first):
- `environment: testpypi`; `permissions: { id-token: write, contents: read }`.
- Steps: checkout (pinned, `persist-credentials: false`) → `astral-sh/setup-uv` (pinned)
  → `uv build` → `pypa/gh-action-pypi-publish` (pinned) with
  `repository-url: https://test.pypi.org/legacy/` and `skip-existing: true`.

**Job `pypi`** (`needs: testpypi`):
- `environment: pypi`; `permissions: { id-token: write, contents: write }`.
- Steps: checkout → setup-uv → `uv build` → publish to PyPI (default url) → create the
  GitHub Release: `gh release create "$GITHUB_REF_NAME" dist/* --verify-tag --generate-notes`
  with `env: GH_TOKEN: ${{ github.token }}`.

**Pinned actions**:
- `actions/checkout@93cb6efe18208431cddfb8368fd83d5badbf9bfd # v5.0.1`
- `astral-sh/setup-uv@d0cc045d04ccac9d8b7881df0226f9e82c39688e # v6.8.0`
- `pypa/gh-action-pypi-publish@cef221092ed1bacb1cc03d23a2d87d1d172e277b # v1.14.0`

**Guarantees**:
- Credential-less publishing (OIDC Trusted Publishing); no stored token.
- TestPyPI validates before PyPI; `skip-existing` tolerates a pre-existing TestPyPI
  version.
- A GitHub Release with generated notes + built artifacts is created on success.
- Passes the `zizmor` audit (least-privilege, pinned).

**Out of scope for automated implementation**: the one-time PyPI/TestPyPI Trusted
Publisher setup and the actual `v*` tag push / publish (maintainer actions).

## Package metadata contract (`pyproject.toml` `[project]`)

Must include: `license = "MIT"` (+ `LICENSE` file), `keywords`, `classifiers` (Dev Status,
Environment :: Console, Intended Audience :: Developers, License :: OSI Approved :: MIT
License, Programming Language :: Python :: 3.14, Topic), and `[project.urls]`
(Homepage/Repository/Issues). Version stays static (`0.1.0`).

## Verification (no external side effects)

1. `release.yml` is valid YAML and passes
   `uvx zizmor@1.26.1 --offline --persona regular --min-severity medium .github/workflows/`
   (0 findings ≥ medium).
2. `uv build` produces `dist/*.whl` + `dist/*.tar.gz`.
3. `uvx twine check dist/*` reports PASS (metadata renders).
4. Every action in `release.yml` is a full 40-hex SHA with a `# vX.Y.Z` comment;
   top-level `permissions: {}`; each job least-privilege; checkout `persist-credentials:
   false`.
5. `docs/releasing.md` documents the Trusted-Publisher setup and the tag-push release step.
