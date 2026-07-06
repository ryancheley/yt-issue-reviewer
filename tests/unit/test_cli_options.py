"""--db/--ollama-host/--config must work AFTER the subcommand (documented usage, #24),
and the subcommand value must win over the group value."""

from __future__ import annotations

import pytest
from click.testing import CliRunner

from yt_issue_reviewer import cli
from yt_issue_reviewer.config import Config


@pytest.fixture
def captured_config(monkeypatch):
    """Capture the Config each command resolves; stub Repository so no DB/network is touched."""
    seen: list[Config] = []
    real_config = cli._config

    def spy(ctx, **kwargs):
        cfg = real_config(ctx, **kwargs)
        seen.append(cfg)
        return cfg

    class FakeRepo:
        def latest_run_id(self):
            return None

        def list_runs(self):
            return []

        def close(self):
            pass

    monkeypatch.setattr(cli, "_config", spy)
    monkeypatch.setattr(cli.Repository, "open", classmethod(lambda cls, path: FakeRepo()))
    return seen


def test_db_option_accepted_after_subcommand(captured_config) -> None:
    result = CliRunner().invoke(cli.main, ["runs", "--db", "./after.db"])
    assert "No such option" not in result.output
    assert captured_config[-1].db_path == "./after.db"


def test_ollama_host_accepted_after_subcommand(captured_config) -> None:
    # `runs` never contacts Ollama, so this exercises pure option parsing + resolution.
    result = CliRunner().invoke(cli.main, ["runs", "--ollama-host", "http://h:11434"])
    assert "No such option" not in result.output
    assert captured_config[-1].ollama_host == "http://h:11434"


def test_subcommand_value_wins_over_group(captured_config) -> None:
    CliRunner().invoke(cli.main, ["--db", "./group.db", "runs", "--db", "./sub.db"])
    assert captured_config[-1].db_path == "./sub.db"


def test_group_value_still_works_before_subcommand(captured_config) -> None:
    CliRunner().invoke(cli.main, ["--db", "./group.db", "runs"])
    assert captured_config[-1].db_path == "./group.db"
