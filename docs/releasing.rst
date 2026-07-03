Releasing
=========

Releases are published to PyPI by the `release.yml <https://github.com/ryancheley/yt-issue-reviewer/blob/main/.github/workflows/release.yml>`__
workflow when a version tag (``vX.Y.Z``) is pushed. Publishing uses **PyPI Trusted
Publishing (OIDC)** — there is no stored PyPI token.

.. _one-time-setup-maintainer-on-pypi--testpypi:

One-time setup (maintainer, on PyPI + TestPyPI)
-----------------------------------------------

Trusted Publishers must be configured once per index before the first release. This is a
manual account action that cannot be automated by this repo.

On **both** https://pypi.org and https://test.pypi.org → *Your projects → Publishing* (or
"pending publisher" if the project doesn't exist yet), add a GitHub Actions publisher:

================= ===============================================
Field             Value
================= ===============================================
Owner             ``ryancheley``
Repository        ``yt-issue-reviewer``
Workflow filename ``release.yml``
Environment       ``pypi`` (on PyPI) / ``testpypi`` (on TestPyPI)
================= ===============================================

Optionally, in GitHub → *Settings → Environments*, create the ``pypi`` and ``testpypi``
environments and add required reviewers to gate the real publish.

The package version is **static** in ``pyproject.toml`` and drives the built artifact — the
tag name does not. You must bump the version *and* tag a matching ``vX.Y.Z``; the release
workflow's ``verify`` job fails fast if the tag and the ``pyproject.toml`` version disagree,
so a forgotten bump can't produce a wrong or duplicate upload. ``__version__`` is read from
the installed package metadata, so it stays in sync automatically — only ``pyproject.toml``
needs bumping.

Cutting a release
-----------------

1. Bump ``version`` in ``pyproject.toml`` (e.g. ``0.1.0`` → ``0.2.0``).
2. Commit via a PR and merge (branch protection + required checks apply).
3. Tag and push:
   .. code:: bash

      git checkout main && git pull
      git tag v0.2.0
      git push origin v0.2.0

The workflow then:

1. Builds sdist + wheel with ``uv build``.
2. Publishes to **TestPyPI** first (``skip-existing: true``) as a dry run.
3. Publishes to **PyPI**.
4. Creates a **GitHub Release** for the tag with auto-generated notes and the artifacts
   attached.

Verify
------

.. code:: bash

   uv tool install yt-issue-reviewer==0.2.0
   yt-issue-reviewer --help

Read the Docs versions
----------------------

Read the Docs builds two versions:

- ``latest`` tracks the ``main`` branch.
- ``stable`` tracks the newest release **tag**.

A release tag must therefore contain the docs build (``.readthedocs.yaml`` and
``docs/conf.py``); every tag cut from ``main`` does, since that setup lives on ``main``.
A tag created *before* the docs build was added (e.g. an early ``v0.1.0``) has no
``docs/conf.py`` and will fail the ``stable`` build — in that case either cut a newer tag
that includes the docs, or deactivate/hide the old ``stable`` version in the Read the Docs
dashboard and set the default version to ``latest``.

Notes
-----

- Version is static (manual bump + matching tag). Dynamic-version-from-tag (hatch-vcs / uv
  dynamic versioning) is a possible future enhancement.
- The release workflow is least-privilege and hash-pinned, and is covered by the required
  ``zizmor`` audit like every other workflow.
