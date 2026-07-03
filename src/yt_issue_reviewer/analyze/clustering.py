"""Threshold-based pairwise grouping via union-find (pure, no I/O)."""

from __future__ import annotations

from dataclasses import dataclass

from .scoring import ScoredPair


@dataclass(frozen=True)
class Group:
    members: list[str]
    score: float
    pairs: list[ScoredPair]


class _UnionFind:
    def __init__(self) -> None:
        self._parent: dict[str, str] = {}

    def find(self, x: str) -> str:
        self._parent.setdefault(x, x)
        root = x
        while self._parent[root] != root:
            root = self._parent[root]
        while self._parent[x] != root:
            self._parent[x], x = root, self._parent[x]
        return root

    def union(self, a: str, b: str) -> None:
        ra, rb = self.find(a), self.find(b)
        if ra != rb:
            self._parent[ra] = rb


def group_pairs(pairs: list[ScoredPair]) -> list[Group]:
    """Form connected-component groups from kept pairs, ranked by descending score.

    Group score = mean of member pair combined scores. Issues not in any kept pair
    stay ungrouped (they simply never appear).
    """
    uf = _UnionFind()
    for p in pairs:
        uf.union(p.issue_a, p.issue_b)

    members_by_root: dict[str, set[str]] = {}
    pairs_by_root: dict[str, list[ScoredPair]] = {}
    for p in pairs:
        root = uf.find(p.issue_a)
        members_by_root.setdefault(root, set()).update((p.issue_a, p.issue_b))
        pairs_by_root.setdefault(root, []).append(p)

    groups: list[Group] = []
    for root, members in members_by_root.items():
        group_pairs_ = pairs_by_root[root]
        score = sum(gp.combined_score for gp in group_pairs_) / len(group_pairs_)
        groups.append(Group(members=sorted(members), score=score, pairs=group_pairs_))

    groups.sort(key=lambda g: g.score, reverse=True)
    return groups
