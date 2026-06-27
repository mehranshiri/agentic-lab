"""Application configuration.

Loads environment variables, validates required settings,
and exposes a configuration object for the rest of the application.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Final

from dotenv import load_dotenv


# ---------------------------------------------------------------------------
# Environment
# ---------------------------------------------------------------------------

#: Path to the project root (two levels up from this file).
PROJECT_ROOT: Final[Path] = Path(__file__).resolve().parent.parent

#: Load the ``.env`` file placed at the project root, if it exists.
load_dotenv(dotenv_path=PROJECT_ROOT / ".env")


# ---------------------------------------------------------------------------
# Required-setting validation helper
# ---------------------------------------------------------------------------

class ConfigurationError(Exception):
    """Raised when a required configuration setting is missing or invalid."""


def _require(name: str) -> str:
    """Return the environment variable *name* or raise ``ConfigurationError``."""
    value = os.environ.get(name)
    if not value:
        raise ConfigurationError(
            f"Required environment variable '{name}' is not set. "
            f"Ensure it is defined in {PROJECT_ROOT / '.env'} "
            f"or exported in your shell."
        )
    return value


# ---------------------------------------------------------------------------
# Settings dataclass
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class Settings:
    """Immutable application settings populated from the environment."""

    # ── DeepSeek / LLM ────────────────────────────────────────────────
    deepseek_api_key: str = field(default_factory=lambda: _require("DEEPSEEK_API_KEY"))
    deepseek_base_url: str = field(default_factory=lambda: _require("DEEPSEEK_BASE_URL"))

    # ── Future settings can be added here ─────────────────────────────
    # e.g. log_level: str = field(default_factory=lambda: os.getenv("LOG_LEVEL", "INFO"))


# ---------------------------------------------------------------------------
# Singleton config object
# ---------------------------------------------------------------------------

settings = Settings()
"""Application-wide configuration singleton.

Usage::

    from core.config import settings

    print(settings.deepseek_api_key)
    print(settings.deepseek_base_url)
"""
