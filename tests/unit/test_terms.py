"""Term extraction and shared-term evidence."""

from __future__ import annotations

from tests.conftest import load_fixture_issues
from yt_issue_reviewer.analyze import terms


def test_significant_terms_drops_stopwords_and_short_tokens() -> None:
    result = terms.significant_terms("The login page returns a 500 error on submit")
    assert "login" in result
    assert "error" in result
    assert "the" not in result  # stopword
    assert "on" not in result  # stopword / short


def test_shared_terms_between_related_issues() -> None:
    issues = {i.issue_id: i for i in load_fixture_issues()}
    common = terms.shared_terms(issues["PROJ-1"], issues["PROJ-2"])
    assert "login" in common
    assert "500" in common


def test_unrelated_issues_share_few_terms() -> None:
    issues = {i.issue_id: i for i in load_fixture_issues()}
    common = terms.shared_terms(issues["PROJ-1"], issues["PROJ-5"])
    assert "login" not in common
