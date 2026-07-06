.. _installation--prerequisites:

Installation & Prerequisites
============================

Prerequisites
-------------

``yt-issue-reviewer`` is read-only against YouTrack and does all AI work on a **self-hosted
Ollama** instance — no third-party hosted AI is ever used.

1. `uv <https://docs.astral.sh/uv/>`__ — Python 3.11+ toolchain and runner.
2. **``youtrack-cli`` authenticated** — this tool reads YouTrack *only* through the ``yt`` CLI
   and reuses its existing auth. Set it up once:
   .. code:: bash

      yt auth login
      yt issues list --project-id PROJ --state Open   # sanity check

   Config lives at ``~/.config/youtrack-cli/.env`` (or ``YOUTRACK_BASE_URL`` / ``YOUTRACK_TOKEN``
   env vars).
3. **A reachable self-hosted Ollama** with the models pulled:
   .. code:: bash

      ollama pull nomic-embed-text     # embeddings (default, 768-dim)
      ollama pull qwen2.5              # only needed for --label (generated group labels)

   Ollama may be on ``localhost`` or reached over Tailscale — set the address with
   ``--ollama-host`` or the ``OLLAMA_HOST`` env var (see :doc:`configuration <configuration>`).

Install
-------

From source (until a released version is on PyPI — see :doc:`releasing <releasing>`):

.. code:: bash

   git clone https://github.com/ryancheley/yt-issue-reviewer
   cd yt-issue-reviewer
   uv sync
   uv run yt-issue-reviewer --help

Once published, it will be installable directly:

.. code:: bash

   uv tool install yt-issue-reviewer     # or: pip install yt-issue-reviewer

Verify connectivity
-------------------

.. code:: bash

   uv run yt-issue-reviewer doctor --ollama-host http://<host>:11434

``doctor`` checks that ``yt`` is present + authenticated and that Ollama is reachable with the
required model pulled. Next: the :doc:`quickstart <quickstart>`.
