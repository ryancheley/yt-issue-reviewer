# Interface Contracts: `Embedder` and `Labeler`

Two seams isolate all Ollama access (Constitution I, VII). Production implementations use
the official `ollama` Python client against a configurable, user-controlled host; fakes
back tests. Neither ever contacts a third-party hosted service.

## `Embedder` (`embeddings/ollama.py`)

```python
from typing import Protocol

class Embedder(Protocol):
    model: str
    model_version: str | None
    dim: int

    def embed_batch(self, texts: list[str]) -> list[list[float]]:
        """Return one vector per input text, order-preserving.
        Raises OllamaUnavailable if the host/model is unreachable."""
        ...

    def check_available(self) -> None:
        """Raise OllamaUnavailable if host unreachable or model not pulled."""
        ...
```

### Production: `OllamaEmbedder`

- Wraps `ollama.Client(host=<configured>)`; calls `.embed(model=..., input=texts)`
  (`POST /api/embed`) with **batched** input (~50–100 texts/call) — see research R2.
- Applies the model's required task prefix (nomic → `search_document:` on the corpus).
- Reachability/model-presence checked via `client.list()` (`GET /api/tags`).
- Records `model` and `model_version` (digest) for persistence (FR-011).

### Cosine similarity helper (pure, unit-tested)

```python
def cosine_matrix(vectors: "np.ndarray") -> "np.ndarray":
    """Return the NxN cosine-similarity matrix for row vectors.
    Pure function — no I/O. Tested directly (Constitution VII)."""
```

### Fake: `FakeEmbedder`

- Deterministic vectors from text (e.g. hashed bag-of-words) so known-related fixture
  issues have predictably high cosine similarity. `check_available` configurable to raise
  so the degraded-mode path (structural-only) is testable.

## `Labeler` (`llm/labeler.py`) — flag-gated, presentation-only

```python
class Labeler(Protocol):
    model: str

    def label_group(self, summaries: list[str], evidence: list[str]) -> "GroupLabel":
        """Return a one-line label + short rationale for a group.
        Presentation-only: output MUST NOT feed back into scores or membership."""
        ...

    def check_available(self) -> None: ...

@dataclass(frozen=True)
class GroupLabel:
    label: str
    rationale: str
    is_generated: bool = True   # always True — see FR-014
```

### Production: `OllamaLabeler`

- Calls `ollama` client `.chat(model=..., messages=[...], stream=False,
  options={"temperature": ...})` (`POST /api/chat`) — see research R7.
- Invoked only when `--label` is set. If the chat model is unreachable, the caller skips
  labeling with a warning; labels are never required for a run to succeed.

### Fake: `FakeLabeler`

- Returns a deterministic label/rationale for tests; `is_generated` always `True`.

## Shared error type

```python
class OllamaUnavailable(RuntimeError): ...
```

Raised by both `check_available` and the production call paths when the configured host is
unreachable or the required model is absent. The `analyze` flow catches it to (a) degrade
embeddings to structural-only scoring, or (b) skip labeling — with a clear warning in
both cases, and **never** a hosted-service fallback (Constitution I).

## Contract tests

1. `embed_batch` returns exactly one vector per input, in order, each of length `dim`.
2. `cosine_matrix` is symmetric with 1.0 on the diagonal for normalized inputs.
3. When `check_available` raises `OllamaUnavailable`, `analyze` produces a structural-only
   run with `degraded_structural_only=1` and exit code 0.
4. `Labeler` output never influences `pairs`/`groups` scoring or membership (verified by
   running analysis with and without `--label` over the same fixture → identical groups).
5. `GroupLabel.is_generated` is always `True`.
