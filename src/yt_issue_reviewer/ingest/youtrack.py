"""The single seam through which the tool reads YouTrack (read-only, Constitution III).

Production reads go through the ``yt`` CLI as a subprocess with JSON output; a fake backs
tests. No method mutates YouTrack. ``youtrack-cli`` is an external prerequisite the operator
installs and authenticates separately (it is *not* a bundled dependency — see issue #22); this
module only invokes the ``yt`` binary found on PATH.
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
from datetime import UTC, datetime
from typing import Protocol

from ..errors import YouTrackUnavailable
from .models import Issue, IssueLink

# Force UTF-8 stdio in the `yt` child process. Without this, on a legacy Windows console
# (cp1252) the child crashes with UnicodeEncodeError when yt-cli prints a non-ASCII byte
# (e.g. an emoji) — see issue #23. PYTHONUTF8=1 enables UTF-8 mode; PYTHONIOENCODING is a
# belt-and-suspenders. No-op on already-UTF-8 platforms.
_UTF8_ENV = {**os.environ, "PYTHONUTF8": "1", "PYTHONIOENCODING": "utf-8"}


def _iso_ts(value: object) -> str:
    """Normalize a YouTrack timestamp (epoch millis int, or string) to ISO-8601 UTC."""
    if value is None or value == "":
        return ""
    if isinstance(value, int | float):
        return datetime.fromtimestamp(value / 1000, tz=UTC).isoformat()
    text = str(value)
    if text.isdigit():
        return datetime.fromtimestamp(int(text) / 1000, tz=UTC).isoformat()
    return text


def _in_date_range(value: str, since: str | None, until: str | None) -> bool:
    """Compare an ISO-8601 date/datetime string against an inclusive range.

    Comparison is lexical on the date prefix, which is correct for ISO-8601.
    """
    if not value:
        return True
    day = value[:10]
    if since and day < since[:10]:
        return False
    return not (until and day > until[:10])


def _matches_state(issue_state: str, state_filter: str) -> bool:
    if state_filter == "all":
        return True
    # "open" == not resolved/closed/done.
    closed_markers = {"closed", "resolved", "done", "fixed", "verified"}
    return issue_state.strip().lower() not in closed_markers


class YouTrackSource(Protocol):
    """Read-only issue source."""

    def fetch_issues(
        self,
        projects: list[str],
        state: str = "open",
        since: str | None = None,
        until: str | None = None,
    ) -> list[Issue]: ...

    def check_available(self) -> None: ...


class FakeYouTrackSource:
    """In-memory source for tests. Applies the same filtering semantics as production."""

    def __init__(self, issues: list[Issue], *, available: bool = True) -> None:
        self._issues = issues
        self._available = available

    def check_available(self) -> None:
        if not self._available:
            raise YouTrackUnavailable("fake source configured as unavailable")

    def fetch_issues(
        self,
        projects: list[str],
        state: str = "open",
        since: str | None = None,
        until: str | None = None,
    ) -> list[Issue]:
        self.check_available()
        wanted = set(projects)
        result: list[Issue] = []
        for issue in self._issues:
            if issue.project not in wanted:
                continue
            if not _matches_state(issue.state, state):
                continue
            if not _in_date_range(issue.created, since, until) and not _in_date_range(
                issue.updated, since, until
            ):
                continue
            result.append(issue)
        return result


class CliYouTrackSource:
    """Production source: shells out to the ``yt`` binary with JSON output.

    Reuses the operator's existing youtrack-cli auth (shared config / env vars) — this tool
    holds no credentials of its own, and does not bundle youtrack-cli (see module docstring).
    """

    def __init__(self, yt_binary: str = "yt") -> None:
        self._yt = yt_binary

    def check_available(self) -> None:
        if shutil.which(self._yt) is None:
            raise YouTrackUnavailable(
                f"the '{self._yt}' CLI was not found on PATH. Install youtrack-cli and run "
                "`yt auth login`."
            )
        try:
            proc = subprocess.run(
                [self._yt, "auth", "token", "--show"],
                capture_output=True,
                text=True,
                encoding="utf-8",
                env=_UTF8_ENV,
                timeout=30,
                check=False,
            )
        except (OSError, subprocess.SubprocessError) as exc:  # pragma: no cover - env dependent
            raise YouTrackUnavailable(f"failed to invoke '{self._yt}': {exc}") from exc
        if proc.returncode != 0:
            raise YouTrackUnavailable(
                "youtrack-cli is not authenticated. Run `yt auth login`.\n" + proc.stderr.strip()
            )

    def fetch_issues(
        self,
        projects: list[str],
        state: str = "open",
        since: str | None = None,
        until: str | None = None,
    ) -> list[Issue]:
        self.check_available()
        issues: list[Issue] = []
        for project in projects:
            issues.extend(self._fetch_project(project))
        # Server-side `yt --state Open` is a no-op for projects whose state lives in a
        # "Status" custom field (the built-in State it filters on is empty), so Done issues
        # come back anyway. Re-apply the client-side filter as a safety net (issue #35).
        issues = [i for i in issues if _matches_state(i.state, state)]
        # Date-range filtering client-side (YouTrack query date semantics vary).
        if since or until:
            issues = [
                i
                for i in issues
                if _in_date_range(i.created, since, until)
                or _in_date_range(i.updated, since, until)
            ]
        return issues

    def _fetch_project(self, project: str) -> list[Issue]:
        cmd = [
            self._yt,
            "issues",
            "list",
            "--project-id",
            project,
            "--format",
            "json",
        ]
        # Deliberately no server-side `--state Open`: yt's filter is unreliable in both
        # directions — it leaked resolved issues for Status-based projects (#35) and dropped
        # genuinely-open (State=New) issues (#39). fetch_issues applies the client-side
        # _matches_state filter unconditionally, which is the single source of truth.
        try:
            proc = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                encoding="utf-8",
                env=_UTF8_ENV,
                timeout=300,
                check=False,
            )
        except (OSError, subprocess.SubprocessError) as exc:  # pragma: no cover - env dependent
            raise YouTrackUnavailable(f"failed to run '{' '.join(cmd)}': {exc}") from exc
        if proc.returncode != 0:
            raise YouTrackUnavailable(
                f"'yt issues list' failed for project {project}:\n{proc.stderr.strip()}"
            )
        return [parse_issue(raw) for raw in _load_json_issues(proc.stdout)]


def _load_json_issues(stdout: str) -> list[dict]:
    # A leading UTF-8 BOM (common from Windows toolchains) makes json.loads fail with
    # "Expecting value: line 1 column 1 (char 0)" — and str.strip() does NOT remove it,
    # so drop it explicitly before the empty check (issue #29).
    stdout = stdout.removeprefix("﻿").strip()
    if not stdout:
        return []
    try:
        # strict=False tolerates raw control characters (tabs, ANSI colour codes, etc.) that
        # `yt` can leave unescaped inside issue text; the default rejects them with
        # "Invalid control character at ..." (issue #29, second failure mode).
        data = json.loads(stdout, strict=False)
    except json.JSONDecodeError as exc:
        # yt exited 0 but wrote a banner/table/warning instead of JSON. Surface the
        # operator-facing error with the failure position and an excerpt, not a traceback.
        raise YouTrackUnavailable(
            f"'yt' did not return valid JSON ({exc.msg} at line {exc.lineno} "
            f"column {exc.colno}). Got: {stdout[:200]}"
        ) from exc
    if isinstance(data, dict):
        # yt-cli may wrap the payload as {"status":..,"data":[...]} or {"issues":[...]}.
        for key in ("data", "issues", "results"):
            inner = data.get(key)
            if isinstance(inner, list):
                return inner
        return []
    return data if isinstance(data, list) else []


def _extract_custom_field(custom_fields: object, *names: str) -> str | None:
    """Pull a named field value out of YouTrack's custom_fields list-of-dicts."""
    if not isinstance(custom_fields, list):
        return None
    wanted = {n.lower() for n in names}
    for field in custom_fields:
        if not isinstance(field, dict):
            continue
        if str(field.get("name", "")).lower() in wanted:
            value = field.get("value")
            if isinstance(value, dict):
                return str(value.get("name") or value.get("login") or "").strip() or None
            if isinstance(value, list) and value:
                first = value[0]
                if isinstance(first, dict):
                    return str(first.get("name") or first.get("login") or "").strip() or None
                return str(first)
            if value is not None:
                return str(value)
    return None


def _name_of(value: object, *keys: str) -> str:
    if isinstance(value, dict):
        for key in keys:
            found = value.get(key)
            if found:
                return str(found)
    if isinstance(value, str):
        return value
    return ""


def parse_issue(raw: dict) -> Issue:
    """Map one yt-cli JSON issue object into our domain ``Issue``.

    ``state`` and ``assignee`` live inside ``custom_fields`` in YouTrack.
    """
    custom_fields = raw.get("customFields") or raw.get("custom_fields")
    # Some projects model workflow state in a "Status" custom field, not the built-in
    # "State" (issue #35). "State"/"Stage" are checked first so they win when both exist.
    state = _extract_custom_field(custom_fields, "State", "Stage", "Status") or raw.get("state", "")
    assignee = _extract_custom_field(custom_fields, "Assignee") or (
        _name_of(raw.get("assignee"), "name", "login") or None
    )

    tags = [_name_of(t, "name") for t in (raw.get("tags") or []) if _name_of(t, "name")]

    links: list[IssueLink] = []
    for link in raw.get("links") or []:
        if not isinstance(link, dict):
            continue
        link_type = _name_of(link.get("linkType") or link, "name", "directed") or "relates to"
        for target in link.get("issues") or ([link.get("target")] if link.get("target") else []):
            target_id = _name_of(target, "idReadable", "id")
            if target_id:
                links.append(IssueLink(target_id=target_id, link_type=str(link_type)))

    return Issue(
        issue_id=str(raw.get("idReadable") or raw.get("id") or ""),
        project=_name_of(raw.get("project"), "shortName", "name") or raw.get("project", ""),
        number=int(raw.get("numberInProject") or raw.get("number") or 0),
        summary=str(raw.get("summary") or ""),
        description=str(raw.get("description") or ""),
        state=str(state or ""),
        assignee=assignee,
        reporter=_name_of(raw.get("reporter"), "name", "login"),
        tags=tuple(tags),
        created=_iso_ts(raw.get("created")),
        updated=_iso_ts(raw.get("updated")),
        links=tuple(links),
    )
