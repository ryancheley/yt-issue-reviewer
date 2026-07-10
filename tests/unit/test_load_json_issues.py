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


def test_control_chars_in_strings_are_tolerated() -> None:
    # yt can leave raw tabs / ANSI escape codes unescaped inside issue text; the default
    # json parser rejects them with "Invalid control character at ..." (issue #29 round 2).
    payload = '[{"summary": "col1\tcol2 \x1b[31mred\x1b[0m", "idReadable": "X-1"}]'
    assert _load_json_issues(payload) == [
        {"summary": "col1\tcol2 \x1b[31mred\x1b[0m", "idReadable": "X-1"}
    ]


def test_multiline_description_is_tolerated() -> None:
    # yt emits raw newlines inside multi-line `description` fields (issue #34); a literal
    # U+000A inside a JSON string is illegal per spec, so strict json.loads rejected it.
    payload = '[{"idReadable": "NG-1", "description": "line 1\nline 2"}]'
    assert _load_json_issues(payload) == [{"idReadable": "NG-1", "description": "line 1\nline 2"}]


def test_unescaped_backslash_in_description_is_tolerated() -> None:
    # yt can emit a backslash that isn't a valid JSON escape — a Windows path or a regex in
    # issue text — which strict=False still rejects with "Invalid \escape" (issue #48).
    payload = r'[{"idReadable": "NG-1", "description": "path C:\Users and regex \d+ here"}]'
    result = _load_json_issues(payload)
    assert len(result) == 1 and result[0]["idReadable"] == "NG-1"
    assert "d+ here" in result[0]["description"]  # parsed, not crashed


def test_backslash_before_newline_is_tolerated() -> None:
    # yt can end a description line with a literal backslash, emitting `\` directly before a
    # raw newline — invalid JSON that the #48 repair missed because `.` skips newlines (#57).
    payload = '[{"idReadable": "NG-1", "description": "line ends with backslash\\\n next line"}]'
    result = _load_json_issues(payload)
    assert len(result) == 1 and result[0]["idReadable"] == "NG-1"
    assert "next line" in result[0]["description"]  # parsed, not crashed


def test_valid_escapes_are_preserved() -> None:
    # The stray-backslash repair must not corrupt genuinely valid JSON escapes.
    import json

    payload = r'[{"a": "tab\there \\ back \" quote \/ slash A unicode"}]'
    assert _load_json_issues(payload) == json.loads(payload)
    assert _load_json_issues(payload)[0]["a"] == 'tab\there \\ back " quote / slash A unicode'


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
