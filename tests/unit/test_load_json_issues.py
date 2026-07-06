"""`_load_json_issues` must tolerate a UTF-8 BOM and fail comprehensibly on non-JSON.

Issue #29: on Windows the `yt` CLI can emit a leading BOM (which `str.strip()` does not
remove) or a human-readable banner instead of JSON, and today the operator gets a raw
`json.decoder.JSONDecodeError` traceback.
"""

from __future__ import annotations

import pytest

from yt_issue_reviewer.errors import YouTrackUnavailable
from yt_issue_reviewer.ingest.youtrack import _load_json_issues

BOM = "﻿"


def test_bom_prefixed_json_parses() -> None:
    payload = '[{"idReadable": "X-1"}, {"idReadable": "X-2"}]'
    assert _load_json_issues(BOM + payload) == _load_json_issues(payload)
    assert _load_json_issues(BOM + payload) == [
        {"idReadable": "X-1"},
        {"idReadable": "X-2"},
    ]


def test_bom_then_whitespace_is_empty() -> None:
    assert _load_json_issues(BOM + "  \n") == []


def test_empty_and_whitespace_still_return_empty() -> None:
    assert _load_json_issues("") == []
    assert _load_json_issues("   \n\t") == []


def test_non_json_raises_youtrack_unavailable() -> None:
    banner = "Loading issues... done. No results table available."
    with pytest.raises(YouTrackUnavailable) as exc:
        _load_json_issues(banner)
    # The operator must see what yt actually returned, not Python internals.
    assert "Loading issues" in str(exc.value)


def test_long_non_json_excerpt_truncated() -> None:
    junk = "x" * 5000
    with pytest.raises(YouTrackUnavailable) as exc:
        _load_json_issues(junk)
    assert len(str(exc.value)) < len(junk)
