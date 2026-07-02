"""
config_loader.py
----------------
Loads configs/config.yaml and injects secrets from .env.

Usage:
    from config_loader import get_config
    cfg = get_config()
    chunk_size = cfg["ingestion"]["chunk_size"]
"""

import os
from pathlib import Path
from typing import Any, Dict

import yaml
from dotenv import load_dotenv
from loguru import logger

# Resolve paths relative to this file so the module works from any cwd
_HERE = Path(__file__).parent
_ENV_PATH = _HERE / ".env"
_CONFIG_PATH = _HERE / "configs" / "config.yaml"
_CONFIG_EXAMPLE = _HERE / "configs" / "config.example.yaml"

load_dotenv(_ENV_PATH)

_config_cache: Dict[str, Any] | None = None


def get_config() -> Dict[str, Any]:
    """
    Returns the parsed config dict, loading from disk on first call
    and returning the cached version on subsequent calls.
    """
    global _config_cache
    if _config_cache is not None:
        return _config_cache

    config_file = _CONFIG_PATH if _CONFIG_PATH.exists() else _CONFIG_EXAMPLE
    if not config_file.exists():
        raise FileNotFoundError(
            f"No config file found. Expected: {_CONFIG_PATH}\n"
            "Copy configs/config.example.yaml to configs/config.yaml and fill in values."
        )

    with open(config_file, "r") as f:
        cfg = yaml.safe_load(f)

    logger.info(f"Config loaded from {config_file}")
    _config_cache = cfg
    return cfg
