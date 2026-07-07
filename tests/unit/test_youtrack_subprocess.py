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
