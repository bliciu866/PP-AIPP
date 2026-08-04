from __future__ import annotations

import os
from dataclasses import dataclass
from importlib.resources import files
from pathlib import Path
from typing import Any

import yaml


@dataclass(slots=True)
class ConfigManager:
    data: dict[str, Any]
    source: Path

    @classmethod
    def load(cls, path: str | Path = "config/default.yaml") -> ConfigManager:
        source = Path(path)
        if not source.exists():
            packaged = files("pp_aipp.resources").joinpath("default.yaml")
            source = Path(str(packaged))
        if not source.exists():
            raise FileNotFoundError(f"Configuration file not found: {source}")
        raw = yaml.safe_load(source.read_text(encoding="utf-8")) or {}
        cls._apply_environment(raw)
        return cls(raw, source)

    @staticmethod
    def _apply_environment(data: dict[str, Any]) -> None:
        prefix = "PPAIPP__"
        for key, value in os.environ.items():
            if not key.startswith(prefix):
                continue
            parts = key[len(prefix):].lower().split("__")
            target = data
            for part in parts[:-1]:
                target = target.setdefault(part, {})
            target[parts[-1]] = value

    def get(self, dotted: str, default: Any = None) -> Any:
        value: Any = self.data
        for part in dotted.split("."):
            if not isinstance(value, dict) or part not in value:
                return default
            value = value[part]
        return value
