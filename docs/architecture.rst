How It Works (Architecture)
===========================

``yt-issue-reviewer`` finds related issues with a **hybrid, explainable** relatedness score,
computed entirely on infrastructure you control.

Pipeline
--------

.. code:: text

   ingest → embed (cached) → score → group → report

1. **Ingest** — fetch issues through the ``youtrack_cli`` (``yt``) CLI and cache them in SQLite.
   ``state`` and ``assignee`` are parsed out of YouTrack custom fields. Existing issue links
   are recorded so they can be excluded from *new* findings.
2. **Embed** — each issue's ``title + description`` is embedded via self-hosted Ollama
   (``/api/embed``, batched). Vectors are cached keyed on ``(issue_id, content_hash, model)``,
   so unchanged issues are never re-embedded → near-instant repeat runs.
3. **Score** — for each pair of issues:

   - **Semantic**: cosine similarity of the embedding vectors.
   - **Structural** (local, no LLM): shared tags/components, same reporter, and temporal
     proximity.
   - **Combined**: a configurable weighted blend
     (``weight_semantic`` × semantic + ``weight_structural`` × structural).
     Pairs below ``min_score``, and pairs already linked in YouTrack, are dropped.

4. **Group** — remaining pairs are merged into groups via union-find (connected
   components), ranked by score.
5. **Report** — ranked groups are rendered as rich terminal tables, each with its member
   issues, score, and **human-readable evidence** (the shared terms / tags / reporter /
   proximity / semantic score that justified it). With ``--label``, a generated theme label
   is added — clearly marked and never affecting scores or membership.

Storage (Datasette-friendly SQLite)
-----------------------------------

Results persist to a single SQLite file that is both the cache and the durable, shareable
export. Tables: ``issues``, ``issue_links``, ``embeddings``, ``pairs``, ``groups``, ``group_members``,
``evidence``, ``run_metadata``. All columns are plain TEXT/INTEGER/REAL (vectors stored as JSON
text), so ``datasette yir.db`` browses everything with no extensions.

Degraded mode
-------------

If Ollama is unreachable, ``analyze`` warns and scores with **structural signals only**
(``run_metadata.degraded_structural_only = 1``) rather than failing or contacting any hosted
service.

Deeper detail
-------------

Full entity definitions and the data model are in
`specs/001-related-issue-finder/data-model.md <https://github.com/ryancheley/yt-issue-reviewer/blob/main/specs/001-related-issue-finder/data-model.md>`__;
the design rationale is in
`specs/001-related-issue-finder/plan.md <https://github.com/ryancheley/yt-issue-reviewer/blob/main/specs/001-related-issue-finder/plan.md>`__.
