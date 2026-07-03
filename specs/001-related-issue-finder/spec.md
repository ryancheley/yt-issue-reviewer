# Feature Specification: Related Issue Finder

**Feature Branch**: `001-related-issue-finder`

**Created**: 2026-07-02

**Status**: Draft

**Input**: User description: "Build a tool that helps a team lead identify related issues across a YouTrack instance so that duplicates can be merged, recurring problems can be recognized, and scattered work on the same underlying topic can be consolidated."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Surface related-issue groups with evidence (Priority: P1)

A team lead points the tool at one or more YouTrack projects and runs an analysis.
The tool retrieves the issues, compares them, and presents ranked groups of issues
that appear to be related — probable duplicates, issues about the same
feature/component/root cause, and issues with strongly overlapping subject matter even
when worded differently. Each group shows its member issues, a relatedness score, the
human-readable evidence for why they were grouped, and a short generated label
describing the group's common theme. Relationships that already exist as explicit links
in YouTrack are treated as known and excluded from the "new findings."

**Why this priority**: This is the core value of the tool. Without it, there is no
product. A team lead who cannot read every issue gets a curated, evidence-backed
shortlist of candidate groupings to review. Every other capability (filtering, export)
exists to serve this one.

**Independent Test**: Run the tool against a project containing a mix of clearly
related issues and unrelated issues; confirm it returns ranked groups where each group
lists its members, a score, at least one piece of human-readable evidence, and a
generated theme label, and that pre-existing YouTrack links do not appear as new
findings. A human reviewer agrees that at least some surfaced groups are genuinely
related.

**Acceptance Scenarios**:

1. **Given** a project with two near-duplicate issues describing the same bug in
   different words, **When** the analysis runs, **Then** those two issues appear in the
   same group with a high relatedness score and evidence citing their shared
   significant terms.
2. **Given** a group of related issues, **When** the results are presented, **Then**
   each group displays its member issues, a relatedness score, human-readable evidence,
   and a short generated theme label that is clearly marked as generated.
3. **Given** two issues already connected by an explicit YouTrack link, **When** the
   analysis runs, **Then** that pair is not reported as a new finding.
4. **Given** a group whose theme label was produced by a language model, **When** the
   group is shown, **Then** the label is labeled as generated and the underlying score
   and evidence remain visible alongside it.
5. **Given** an issue that is not meaningfully related to any other issue, **When** the
   analysis runs, **Then** it is not forced into a group.

---

### User Story 2 - Scope the analysis with filters (Priority: P2)

Before or while running an analysis, the team lead narrows what is analyzed: by project,
by issue state (e.g., only open issues), by a created/updated date range, and by a
minimum relatedness threshold below which groups are not reported. This keeps results
focused and relevant to the review the lead is actually doing.

**Why this priority**: A few thousand issues produce too much noise if analyzed
wholesale. Filtering makes the results actionable and lets the lead focus a review
session (e.g., "only open issues in Project X from this quarter"). It builds directly on
P1 but the tool delivers value without it.

**Independent Test**: Run the same analysis twice with different filters (e.g.,
all issues vs. open-only, or two different date ranges, or two different thresholds) and
confirm the reported groups change accordingly — filtered-out issues never appear, and
groups scoring below the threshold are omitted.

**Acceptance Scenarios**:

1. **Given** a filter limiting analysis to open issues, **When** the analysis runs,
   **Then** no closed/resolved issue appears in any reported group.
2. **Given** a minimum relatedness threshold, **When** the analysis runs, **Then** no
   group scoring below the threshold is reported.
3. **Given** a date-range filter, **When** the analysis runs, **Then** only issues whose
   created/updated date falls within the range are considered.
4. **Given** multiple selected projects, **When** the analysis runs, **Then** issues
   from all selected projects are considered and groups may span projects.

---

### User Story 3 - Export results for later review and sharing (Priority: P2)

After a run, the team lead saves the results in a durable, queryable format so the
findings can be reviewed later, revisited across sessions, and shared with the team —
without re-running the analysis.

**Why this priority**: A review is rarely finished in one sitting, and findings need to
be communicated to the people who will act on them (merging duplicates, consolidating
work). Durable output turns a transient analysis into a shareable artifact. It depends
on P1's results but is independent of P2's filtering.

**Independent Test**: Run an analysis, export the results, and confirm the exported
artifact contains the groups, member issues, scores, evidence, and labels, and can be
reopened/queried later to reproduce the same view without contacting YouTrack again.

**Acceptance Scenarios**:

1. **Given** a completed analysis, **When** the user exports the results, **Then** a
   durable artifact is produced containing every reported group with its members,
   score, evidence, and theme label.
2. **Given** an exported artifact, **When** the user reopens it later, **Then** the
   findings are readable without re-running the analysis or contacting YouTrack.
3. **Given** an exported artifact, **When** it is shared with a teammate, **Then** the
   teammate can review the same groupings and evidence.

---

### User Story 4 - Fast repeat runs over unchanged issues (Priority: P3)

When the team lead re-runs an analysis over issues that have not changed since the last
run, results return near-instantly because previously fetched issue data is reused
rather than re-retrieved and re-analyzed from scratch. The tool makes clear how fresh
the underlying data is so the lead knows whether a refresh is warranted.

**Why this priority**: It is a strong quality-of-life and success criterion (repeat runs
near-instant) but the tool is still useful on first run without it. It also underpins an
interactive workflow where the lead adjusts filters and re-runs frequently.

**Independent Test**: Run an analysis once (measuring time), then run it again over the
same unchanged issues and confirm the second run is dramatically faster, and that the
tool displays how stale the reused data is.

**Acceptance Scenarios**:

1. **Given** a completed analysis, **When** the same analysis is run again over
   unchanged issues, **Then** it completes near-instantly compared to the first run.
2. **Given** reused issue data, **When** results are presented, **Then** the age/staleness
   of the underlying data is visible to the user.
3. **Given** issues that have changed since the last run, **When** the analysis is run
   again, **Then** the changed issues are re-analyzed and reflected in the results.

---

### Edge Cases

- **No related issues found**: When no groups meet the relatedness threshold, the tool
  reports zero findings clearly rather than fabricating weak groups.
- **Very large scope**: When the selected scope contains several thousand issues, the
  run still completes within an interactive-workflow time budget (minutes, not hours).
- **Sparse issues**: Issues with empty or near-empty descriptions (title only) are still
  handled without error, though they may produce weaker evidence.
- **Local AI service unavailable**: When the self-hosted analysis/labeling service is
  unreachable, the tool fails clearly and does not send issue content to any external
  service as a fallback.
- **Multi-project grouping**: A group may legitimately contain issues from more than one
  project; the report must make each member's project identifiable.
- **Overlapping groups**: An issue may plausibly relate to more than one theme; the tool
  must define and apply a consistent, explainable rule for how an issue is assigned to
  group(s).
- **Existing links that are wrong**: The tool excludes already-linked pairs from new
  findings even if the existing link is questionable (it does not second-guess existing
  YouTrack links in this version).
- **Stale cache with deleted issues**: When previously cached issues no longer exist in
  YouTrack after a refresh, results reflect current issues without erroring on the
  removed ones.

## Requirements *(mandatory)*

### Functional Requirements

#### Ingest

- **FR-001**: System MUST retrieve issues from one or more selected YouTrack projects.
- **FR-002**: For each issue, System MUST capture title, description, state,
  tags/components, reporter, assignee, created date, updated date, and existing issue
  links.
- **FR-003**: System MUST cache fetched issue data locally so that analysis can be
  re-run without re-retrieving from YouTrack.
- **FR-004**: System MUST make the staleness (age) of cached/reused issue data visible to
  the user.
- **FR-005**: System MUST re-fetch and re-analyze issues that have changed since the
  previous run while reusing unchanged issues.

#### Analyze

- **FR-006**: System MUST identify candidate relationships between issues, covering
  probable duplicates, issues about the same feature/component/root cause, and issues
  with strongly overlapping subject matter even when worded differently.
- **FR-007**: System MUST treat relationships already recorded as explicit YouTrack
  links as known and exclude them from newly reported findings.
- **FR-008**: System MUST assign each candidate relationship/group a relatedness score
  used for ranking.
- **FR-009**: Every surfaced relationship MUST be accompanied by human-readable evidence
  (for example: shared significant terms, shared tag/component, same reporter within a
  short time window, structural signals).
- **FR-010**: System MUST NOT force unrelated issues into groups; issues with no
  meaningful relationship remain ungrouped.
- **FR-011**: System MUST record the identity and version of the model used to compute
  similarity for each analysis run, so that a run can be reproduced.

#### Report

- **FR-012**: System MUST present findings as groups ranked by relatedness score.
- **FR-013**: Each group MUST display its member issues (identifiable, including which
  project each belongs to), the group's relatedness score, the supporting evidence, and
  a short generated label describing the common theme.
- **FR-014**: Any label or rationale produced by a language model MUST be clearly marked
  as generated, and the underlying score and evidence MUST remain visible alongside it.

#### Filter

- **FR-015**: Users MUST be able to scope analysis by project.
- **FR-016**: Users MUST be able to scope analysis by issue state (for example, open
  issues only).
- **FR-017**: Users MUST be able to scope analysis by a created/updated date range.
- **FR-018**: Users MUST be able to set a minimum relatedness threshold below which
  groups are not reported.

#### Export

- **FR-019**: Users MUST be able to save analysis results in a durable, queryable format
  for later review and sharing.
- **FR-020**: Exported results MUST include, for each group, its member issues, score,
  evidence, and theme label, and MUST be readable later without contacting YouTrack.

#### Boundaries

- **FR-021**: System MUST be read-only with respect to YouTrack: it MUST NOT create
  links, merge, tag, comment on, transition, or close issues. (Automatic link creation
  and merging are explicitly out of scope for this version.)
- **FR-022**: System MUST NOT transmit issue content to any third-party hosted service;
  all analysis and label generation MUST occur within infrastructure the user controls.
- **FR-023**: System MUST operate as a run-on-demand analysis; continuous/real-time
  monitoring is out of scope for this version.

### Key Entities *(include if feature involves data)*

- **Issue**: A single YouTrack issue under review. Attributes: identifier, project,
  title, description, state, tags/components, reporter, assignee, created date, updated
  date, and its existing links to other issues.
- **Existing Link**: A relationship already recorded in YouTrack between two issues.
  Treated as a known relationship and excluded from new findings.
- **Related Group**: A set of issues the analysis judges to be related. Attributes:
  member issues, relatedness score, supporting evidence, and a generated theme label
  (marked as generated).
- **Evidence**: The human-readable justification for a group or pairing (e.g., shared
  significant terms, shared tag/component, same reporter within a short window,
  structural signals).
- **Analysis Run**: A single execution of the analysis. Attributes: the scope/filters
  applied (projects, state, date range, threshold), the model identity and version used,
  the timestamp, and the data-staleness information for the issues considered.
- **Export Artifact**: The durable, queryable saved output of an analysis run,
  containing its groups and their details for later review and sharing.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: When run against a real project, the tool surfaces at least some groupings
  that a human reviewer agrees are genuinely related.
- **SC-002**: A full analysis over approximately 1,000 issues completes within an
  interactive-workflow time budget — minutes, not hours.
- **SC-003**: A repeat run over unchanged issues completes near-instantly relative to the
  first run.
- **SC-004**: 100% of surfaced relationships include at least one piece of
  human-readable evidence.
- **SC-005**: Every reported group includes a relatedness score and a theme label, with
  any model-generated label clearly marked as generated.
- **SC-006**: Relationships already present as explicit YouTrack links are never reported
  as new findings.
- **SC-007**: The team lead can scope a run by project, state, date range, and minimum
  threshold, and the reported groups reflect those filters.
- **SC-008**: Results from a run can be saved and reopened later — including on another
  person's review — without re-running the analysis or contacting YouTrack.
- **SC-009**: No issue content leaves infrastructure the user controls during any run.

## Assumptions

- **Primary user**: A single manager/team lead runs the tool on demand; multi-user
  access control is out of scope for this version.
- **Scale**: The target instance holds from several hundred to a few thousand issues
  across multiple projects; performance targets are anchored to ~1,000 issues per run.
- **Read-only intent**: The user wants candidate groupings to review and act on manually;
  the tool never modifies YouTrack. Acting on findings (merging, linking) happens outside
  this tool.
- **Self-hosted analysis**: Similarity scoring and label generation run on
  infrastructure the user controls, consistent with the project's privacy constraints;
  no third-party hosted AI service is used, even as a fallback.
- **Access to YouTrack**: The user has valid credentials/permission to read the projects
  and issues they want to analyze.
- **Evidence over black-box scores**: A relatedness score alone is never sufficient;
  scores are always paired with human-readable evidence so the user can judge them.
- **"Short time window" for reporter-proximity evidence**: A reasonable default window
  (e.g., issues filed by the same reporter within a few days) is used and can be revisited;
  the exact value is a tuning detail, not a scope decision.
- **Durability of export**: Exported results persist locally in a format that can be
  queried and shared as a file/artifact; publishing to a shared external system is out of
  scope for this version.
