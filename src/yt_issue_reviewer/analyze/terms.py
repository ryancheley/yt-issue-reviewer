"""Tokenization and significant-term extraction (pure functions, no I/O)."""

from __future__ import annotations

from ..ingest.models import Issue

# Small, generic English stopword set — enough to keep shared-term evidence meaningful.
STOPWORDS: frozenset[str] = frozenset(
    [
        "a",
        "an",
        "and",
        "are",
        "as",
        "at",
        "be",
        "but",
        "by",
        "for",
        "from",
        "has",
        "have",
        "if",
        "in",
        "into",
        "is",
        "it",
        "its",
        "no",
        "not",
        "of",
        "on",
        "or",
        "that",
        "the",
        "their",
        "then",
        "there",
        "these",
        "this",
        "to",
        "was",
        "were",
        "will",
        "with",
        "when",
        "where",
        "which",
        "who",
        "you",
        "your",
        "user",
        "users",
        "issue",
        "issues",
        "page",
        "screen",
        "when",
        "submit",
    ]
)

MIN_TERM_LEN = 3


def tokenize(text: str) -> list[str]:
    """Lowercase alphanumeric tokens."""
    return [t for t in "".join(c.lower() if c.isalnum() else " " for c in text).split() if t]


def significant_terms(text: str) -> set[str]:
    """Content-bearing terms: not stopwords, length >= MIN_TERM_LEN."""
    return {t for t in tokenize(text) if t not in STOPWORDS and len(t) >= MIN_TERM_LEN}


def issue_terms(issue: Issue) -> set[str]:
    return significant_terms(f"{issue.summary} {issue.description}")


def shared_terms(a: Issue, b: Issue) -> set[str]:
    """Significant terms appearing in both issues."""
    return issue_terms(a) & issue_terms(b)
