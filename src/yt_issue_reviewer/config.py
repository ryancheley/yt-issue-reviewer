"""Configuration resolution: env vars + optional TOML file, with sensible defaults."""

from __future__ import annotations

import os
import tomllib
from dataclasses import dataclass, field
from pathlib import Path

DEFAULT_CONFIG_PATH = Path.home() / ".config" / "yt-issue-reviewer" / "config.toml"
DEFAULT_OLLAMA_HOST = "http://127.0.0.1:11434"
DEFAULT_EMBEDDING_MODEL = "nomic-embed-text"
DEFAULT_LABEL_MODEL = "qwen2.5"

# Per-signal structural weights (normalized at scoring time).
DEFAULT_STRUCTURAL_WEIGHTS: dict[str, float] = {
    "shared_tags": 0.5,
    "same_reporter": 0.2,
    "temporal_proximity": 0.3,
}


@dataclass
class Config:
    """Resolved runtime configuration.

    Precedence: explicit constructor/CLI value > environment variable > TOML file >
    built-in default.
    """

    db_path: str = "yir.db"
    ollama_host: str = DEFAULT_OLLAMA_HOST
    embedding_model: str = DEFAULT_EMBEDDING_MODEL
    label_model: str = DEFAULT_LABEL_MODEL
    weight_semantic: float = 0.7
    weight_structural: float = 0.3
    min_score: float = 0.6
    temporal_window_days: int = 7
    structural_weights: dict[str, float] = field(
        default_factory=lambda: dict(DEFAULT_STRUCTURAL_WEIGHTS)
    )

    @classmethod
    def load(
        cls,
        *,
        config_path: str | os.PathLike[str] | None = None,
        db_path: str | None = None,
        ollama_host: str | None = None,
    ) -> Config:
        """Build a Config from the TOML file (if present) overlaid with env vars and
        the explicit overrides passed here."""
        cfg = cls()

        # 1. TOML file
        path = Path(config_path) if config_path else DEFAULT_CONFIG_PATH
        if path.is_file():
            data = tomllib.loads(path.read_text(encoding="utf-8"))
            _apply_mapping(cfg, data)

        # 2. Environment variables
        env_host = os.environ.get("OLLAMA_HOST")
        if env_host:
            cfg.ollama_host = env_host
        env_db = os.environ.get("YIR_DB")
        if env_db:
            cfg.db_path = env_db

        # 3. Explicit overrides (highest precedence)
        if ollama_host:
            cfg.ollama_host = ollama_host
        if db_path:
            cfg.db_path = db_path

        return cfg


def _apply_mapping(cfg: Config, data: dict[str, object]) -> None:
    """Apply recognized keys from a parsed TOML mapping onto a Config."""
    for key in (
        "db_path",
        "ollama_host",
        "embedding_model",
        "label_model",
        "weight_semantic",
        "weight_structural",
        "min_score",
        "temporal_window_days",
    ):
        if key in data:
            setattr(cfg, key, data[key])
    weights = data.get("structural_weights")
    if isinstance(weights, dict):
        cfg.structural_weights = {
            str(k): float(v) for k, v in weights.items() if isinstance(v, int | float)
        }
