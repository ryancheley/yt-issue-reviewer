"""Both `yt` invocations must force UTF-8 stdio so a non-ASCII byte from the child
does not crash on a legacy Windows console (issue #23)."""

from __future__ import annotations

import json
import subprocess
from types import SimpleNamespace

import pytest

from yt_issue_reviewer.ingest import youtrack
from yt_issue_reviewer.ingest.youtrack import CliYouTrackSource


@pytest.fixture
def capture_run(monkeypatch):
    """Capture kwargs passed to subprocess.run; return a valid-JSON, rc=0 result."""
    calls: list[dict] = []

    def fake_run(cmd, **kwargs):
        calls.append({"cmd": cmd, **kwargs})
        return SimpleNamespace(returncode=0, stdout="[]", stderr="")

    monkeypatch.setattr(subprocess, "run", fake_run)
    monkeypatch.setattr(youtrack.shutil, "which", lambda _: "/usr/bin/yt")
    return calls


def _assert_utf8(call: dict) -> None:
    assert call["encoding"] == "utf-8"
    env = call["env"]
    assert env["PYTHONUTF8"] == "1"
    assert env["PYTHONIOENCODING"] == "utf-8"


def test_check_available_forces_utf8(capture_run) -> None:
    CliYouTrackSource().check_available()
    assert capture_run, "expected a subprocess.run call"
    _assert_utf8(capture_run[-1])


def test_fetch_project_forces_utf8(capture_run) -> None:
    CliYouTrackSource().fetch_issues(["PROJ"])
    # fetch_issues calls check_available() then _fetch_project(); both must be UTF-8.
    assert len(capture_run) >= 2
    for call in capture_run:
        _assert_utf8(call)


# --- Chunked fetch via created-date cursor (issue #45) -------------------------------------
# On gateways that kill any yt request > ~20s, the tool pages the project in bounded --top
# requests instead of one --all. These stub `yt` like the real thing: filter by a
# `created: DATE ..` clause, sort by created ascending, return the first --top issues.
import re  # noqa: E402
from datetime import UTC, datetime  # noqa: E402

from yt_issue_reviewer.errors import YouTrackUnavailable  # noqa: E402


def _millis(day: str) -> int:
    return int(datetime.strptime(day, "%Y-%m-%d").replace(tzinfo=UTC).timestamp() * 1000)


def _syn_issue(n: int, day: str) -> dict:
    return {"idReadable": f"P-{n}", "created": _millis(day), "summary": f"s{n}", "description": ""}


def _paging_stub(monkeypatch, issues: list[dict]) -> list[list[str]]:
    """Serve `issues` the way `yt` does: honor a `created: DATE ..` lower bound in --query,
    sort by created asc, and return the first --top. Records the issued list commands."""
    commands: list[list[str]] = []

    def fake_run(cmd, **kwargs):
        if "auth" in cmd:  # check_available()
            return SimpleNamespace(returncode=0, stdout="token", stderr="")
        commands.append(cmd)
        query = cmd[cmd.index("--query") + 1]
        top = int(cmd[cmd.index("--top") + 1])
        m = re.search(r"created:\s*(\d{4}-\d{2}-\d{2})\s*\.\.", query)
        lo = _millis(m.group(1)) if m else None
        pool = sorted(
            (i for i in issues if lo is None or i["created"] >= lo), key=lambda i: i["created"]
        )
        return SimpleNamespace(returncode=0, stdout=json.dumps(pool[:top]), stderr="")

    monkeypatch.setattr(subprocess, "run", fake_run)
    monkeypatch.setattr(youtrack.shutil, "which", lambda _: "/usr/bin/yt")
    return commands


def test_paginates_across_bounded_pages(monkeypatch) -> None:
    monkeypatch.setattr(youtrack, "_PAGE_SIZE", 3)
    issues = [_syn_issue(n, f"2024-01-{n:02d}") for n in range(1, 8)]  # 7 issues, distinct days
    cmds = _paging_stub(monkeypatch, issues)
    got = CliYouTrackSource().fetch_issues(["P"], state="all")
    assert {i.issue_id for i in got} == {f"P-{n}" for n in range(1, 8)}  # all assembled
    assert len(cmds) > 1  # actually paged
    for c in cmds:  # every request bounded; never --all
        assert "--all" not in c
        assert c[c.index("--top") + 1] == "3"


def test_overlapping_pages_are_deduplicated(monkeypatch) -> None:
    monkeypatch.setattr(youtrack, "_PAGE_SIZE", 3)
    issues = [_syn_issue(n, f"2024-01-{n:02d}") for n in range(1, 6)]
    _paging_stub(monkeypatch, issues)
    ids = [i.issue_id for i in CliYouTrackSource().fetch_issues(["P"], state="all")]
    assert len(ids) == len(set(ids)) == 5  # boundary overlap collapsed, each issue once


def test_same_date_stall_raises(monkeypatch) -> None:
    monkeypatch.setattr(youtrack, "_PAGE_SIZE", 3)
    issues = [_syn_issue(n, "2024-01-01") for n in range(1, 6)]  # 5 issues, ALL one day
    _paging_stub(monkeypatch, issues)
    with pytest.raises(YouTrackUnavailable, match="created date"):
        CliYouTrackSource().fetch_issues(["P"], state="all")


def test_single_page_project_uses_one_request(monkeypatch) -> None:
    monkeypatch.setattr(youtrack, "_PAGE_SIZE", 3)
    issues = [_syn_issue(1, "2024-01-01"), _syn_issue(2, "2024-01-02")]  # 2 < PAGE
    cmds = _paging_stub(monkeypatch, issues)
    got = CliYouTrackSource().fetch_issues(["P"], state="all")
    assert {i.issue_id for i in got} == {"P-1", "P-2"}
    assert len(cmds) == 1 and "--all" not in cmds[0]  # single bounded request


# yt-cli JSON for a Status-based project: state lives in a `Status` custom field, and the
# server-side `--state Open` filter is a no-op, so `Done` issues come back regardless.
_STATUS_PROJECT_JSON = json.dumps(
    [
        {"idReadable": "NG-1", "customFields": [{"name": "Status", "value": {"name": "Done"}}]},
        {"idReadable": "NG-2", "customFields": [{"name": "Status", "value": {"name": "Waiting"}}]},
    ]
)


@pytest.fixture
def status_project(monkeypatch):
    """Stub `yt` returning a Status-based project's issues (Done + In Progress)."""

    def fake_run(cmd, **kwargs):
        if "auth" in cmd:  # check_available()
            return SimpleNamespace(returncode=0, stdout="token", stderr="")
        return SimpleNamespace(returncode=0, stdout=_STATUS_PROJECT_JSON, stderr="")

    monkeypatch.setattr(subprocess, "run", fake_run)
    monkeypatch.setattr(youtrack.shutil, "which", lambda _: "/usr/bin/yt")


def test_state_open_excludes_status_done_on_cli_path(status_project) -> None:
    # Regression for issue #35: the client-side filter must drop Done issues even though
    # the server returned them.
    issues = CliYouTrackSource().fetch_issues(["NG"], state="open")
    assert {i.issue_id for i in issues} == {"NG-2"}


def test_state_all_keeps_status_done_on_cli_path(status_project) -> None:
    issues = CliYouTrackSource().fetch_issues(["NG"], state="all")
    assert {i.issue_id for i in issues} == {"NG-1", "NG-2"}


_NEW_ISSUE_JSON = json.dumps(
    [{"idReadable": "THD-1", "customFields": [{"name": "State", "value": {"name": "New"}}]}]
)


@pytest.fixture
def open_issues_only_without_state_arg(monkeypatch):
    """Stub `yt` mimicking the live #39 behavior: the New issue is returned only when NO
    `--state` argument is passed; `--state Open` returns [] (drops the genuinely-open issue).
    """
    commands: list[list[str]] = []

    def fake_run(cmd, **kwargs):
        if "auth" in cmd:  # check_available()
            return SimpleNamespace(returncode=0, stdout="token", stderr="")
        commands.append(cmd)
        stdout = "[]" if "--state" in cmd else _NEW_ISSUE_JSON
        return SimpleNamespace(returncode=0, stdout=stdout, stderr="")

    monkeypatch.setattr(subprocess, "run", fake_run)
    monkeypatch.setattr(youtrack.shutil, "which", lambda _: "/usr/bin/yt")
    return commands


def test_state_open_returns_new_issues_without_server_side_filter(
    open_issues_only_without_state_arg,
) -> None:
    # Regression for issue #39: analyze --state open must return genuinely-open (New) issues
    # even though yt's server-side --state Open drops them.
    issues = CliYouTrackSource().fetch_issues(["THD"], state="open")
    assert {i.issue_id for i in issues} == {"THD-1"}
    # The fix: the issues-list command must NOT pass --state Open.
    issues_cmd = open_issues_only_without_state_arg[-1]
    assert "--state" not in issues_cmd


# --- Surface yt's stdout in failure messages (issue #54) ------------------------------------
# yt writes the real reason to stdout (e.g. "❌ Not authenticated" on 0.24.5), while stderr
# only carries a generic message. The raised error must include the stdout reason.


def test_fetch_failure_surfaces_stdout_reason(monkeypatch) -> None:
    def fake_run(cmd, **kwargs):
        if "auth" in cmd:  # check_available()
            return SimpleNamespace(returncode=0, stdout="token", stderr="")
        return SimpleNamespace(
            returncode=1, stdout="❌ Not authenticated", stderr="Error: Failed to list issues"
        )

    monkeypatch.setattr(subprocess, "run", fake_run)
    monkeypatch.setattr(youtrack.shutil, "which", lambda _: "/usr/bin/yt")
    with pytest.raises(YouTrackUnavailable) as exc:
        CliYouTrackSource().fetch_issues(["NGDEV"], state="all")
    assert "Not authenticated" in str(exc.value)  # the actionable reason (from stdout)


def test_fetch_failure_stderr_only_still_shown(monkeypatch) -> None:
    def fake_run(cmd, **kwargs):
        if "auth" in cmd:
            return SimpleNamespace(returncode=0, stdout="token", stderr="")
        return SimpleNamespace(returncode=1, stdout="", stderr="boom on stderr only")

    monkeypatch.setattr(subprocess, "run", fake_run)
    monkeypatch.setattr(youtrack.shutil, "which", lambda _: "/usr/bin/yt")
    with pytest.raises(YouTrackUnavailable) as exc:
        CliYouTrackSource().fetch_issues(["NGDEV"], state="all")
    assert "boom on stderr only" in str(exc.value)


def test_check_available_failure_surfaces_stdout_and_guidance(monkeypatch) -> None:
    def fake_run(cmd, **kwargs):  # `yt auth token --show` fails with reason on stdout
        return SimpleNamespace(returncode=1, stdout="❌ Not authenticated [AUTH_004]", stderr="")

    monkeypatch.setattr(subprocess, "run", fake_run)
    monkeypatch.setattr(youtrack.shutil, "which", lambda _: "/usr/bin/yt")
    with pytest.raises(YouTrackUnavailable) as exc:
        CliYouTrackSource().check_available()
    msg = str(exc.value)
    assert "yt auth login" in msg  # existing guidance preserved
    assert "AUTH_004" in msg  # stdout reason now surfaced
