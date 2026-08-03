from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class PluginMetadata:
    name: str
    version: str
    description: str


class Plugin(ABC):
    metadata: PluginMetadata

    @abstractmethod
    def activate(self, kernel: object) -> None:
        """Activate this plugin against a kernel instance."""
