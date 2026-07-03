Quickstart
==========

Get from zero to a first related-issue analysis. Assumes the
:doc:`prerequisites <installation>` are met (uv, authenticated ``yt``, reachable Ollama).

.. _1-check-connectivity:

1. Check connectivity
---------------------

.. code:: bash

   uv run yt-issue-reviewer doctor --ollama-host http://<host>:11434

Expect ``YouTrack (yt): OK`` and ``Ollama embeddings (nomic-embed-text): OK``.

.. _2-run-an-analysis:

2. Run an analysis
------------------

.. code:: bash

   uv run yt-issue-reviewer analyze \
     --project PROJ \
     --state open \
     --min-score 0.6 \
     --ollama-host http://<host>:11434 \
     --db ./yir.db

This ingests issues (cached in ``./yir.db``), embeds them, scores relatedness (semantic +
structural), groups the high-scoring pairs, and prints **ranked groups with evidence**.
Existing YouTrack links are excluded from new findings.

Add ``--label`` to get a generated one-line theme label per group (marked *(generated)* —
it never affects scores or membership).

.. _3-re-display-or-browse-results:

3. Re-display or browse results
-------------------------------

.. code:: bash

   uv run yt-issue-reviewer show --db ./yir.db     # re-render the latest run, offline
   uv run yt-issue-reviewer runs --db ./yir.db     # list runs + settings + staleness
   datasette ./yir.db                              # browse all tables in a web UI

Repeat runs over unchanged issues are near-instant thanks to the embedding cache.

What next
---------

- Every command and flag: :doc:`CLI reference <cli-reference>`.
- Tune models, weights, threshold: :doc:`configuration <configuration>`.
- How scoring works: :doc:`architecture <architecture>`.
- What leaves your infrastructure (nothing): :doc:`privacy & security <privacy-and-security>`.

For the full validated walkthrough (including degraded-mode behavior), see
`specs/001-related-issue-finder/quickstart.md <https://github.com/ryancheley/yt-issue-reviewer/blob/main/specs/001-related-issue-finder/quickstart.md>`__.
