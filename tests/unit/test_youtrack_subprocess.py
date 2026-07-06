"""Both `yt` invocations must force UTF-8 stdio so a non-ASCII byte from the child
does not crash on a legacy Windows console (issue #23)."""

from __future__ import annotations

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
