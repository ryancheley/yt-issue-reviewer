"""Flag-gated, presentation-only group labeling via Ollama chat.

Labels NEVER affect scores or group membership (Constitution IV). Output is always
marked as generated.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from ..errors import OllamaUnavailable


@dataclass(frozen=True)
class GroupLabel:
    label: str
    rationale: str
    is_generated: bool = True


class Labeler(Protocol):
    model: str

    def label_group(self, summaries: list[str], evidence: list[str]) -> GroupLabel: ...

    def check_available(self) -> None: ...


class FakeLabeler:
    """Deterministic labeler for tests."""

    def __init__(self, model: str = "fake-chat", *, available: bool = True) -> None:
        self.model = model
        self._available = available

    def check_available(self) -> None:
        if not self._available:
            raise OllamaUnavailable("fake labeler configured as unavailable")

    def label_group(self, summaries: list[str], evidence: list[str]) -> GroupLabel:
        self.check_available()
        first = summaries[0] if summaries else "related issues"
        return GroupLabel(
            label=f"Theme: {first[:40]}",
            rationale=f"{len(summaries)} issues share overlapping subject matter.",
            is_generated=True,
        )


_SYSTEM_PROMPT = (
    "You label groups of related software issues. Respond with a single short line: "
    "a <=8 word theme label, a colon, then one sentence of rationale. No preamble."
)


class OllamaLabeler:
    """Production labeler using the ``ollama`` client ``/api/chat`` endpoint."""

    def __init__(self, host: str, model: str, *, temperature: float = 0.2) -> None:
        from ollama import Client

        self._client = Client(host=host)
        self.model = model
        self._temperature = temperature

    def check_available(self) -> None:
        try:
            listing = self._client.list()
        except Exception as exc:  # noqa: BLE001
            raise OllamaUnavailable(f"cannot reach Ollama for labeling: {exc}") from exc
        names = {m.get("model") or m.get("name") for m in getattr(listing, "models", [])}
        base = self.model.split(":", 1)[0]
        if not any(n and n.split(":", 1)[0] == base for n in names):
            raise OllamaUnavailable(
                f"label model '{self.model}' is not pulled. Run `ollama pull {self.model}`."
            )

    def label_group(self, summaries: list[str], evidence: list[str]) -> GroupLabel:
        content = "Issues:\n" + "\n".join(f"- {s}" for s in summaries)
        if evidence:
            content += "\nEvidence:\n" + "\n".join(f"- {e}" for e in evidence)
        try:
            resp = self._client.chat(
                model=self.model,
                messages=[
                    {"role": "system", "content": _SYSTEM_PROMPT},
                    {"role": "user", "content": content},
                ],
                stream=False,
                options={"temperature": self._temperature},
            )
        except Exception as exc:  # noqa: BLE001
            raise OllamaUnavailable(f"label request failed: {exc}") from exc
        text = resp["message"]["content"].strip()
        label, _, rationale = text.partition(":")
        return GroupLabel(
            label=label.strip() or text[:60],
            rationale=rationale.strip(),
            is_generated=True,
        )
