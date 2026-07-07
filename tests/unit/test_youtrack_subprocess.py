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
