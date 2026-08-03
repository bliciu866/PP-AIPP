from __future__ import annotations

from importlib.metadata import entry_points
from typing import Iterable

from pp_aipp.plugins.base import Plugin


class PluginManager:
    ENTRYPOINT_GROUP = "pp_aipp.plugins"

    def __init__(self) -> None:
        self._plugins: dict[str, Plugin] = {}

    def register(self, plugin: Plugin) -> None:
        name = plugin.metadata.name
        if name in self._plugins:
            raise ValueError(f"Plugin already registered: {name}")
        self._plugins[name] = plugin

    def discover(self) -> int:
        discovered = entry_points(group=self.ENTRYPOINT_GROUP)
        for item in discovered:
            plugin = item.load()()
            self.register(plugin)
        return len(discovered)

    def activate_all(self, kernel: object) -> None:
        for plugin in self._plugins.values():
            plugin.activate(kernel)

    def list(self) -> list[dict[str, str]]:
        return [
            {"name": p.metadata.name, "version": p.metadata.version, "description": p.metadata.description}
            for p in self._plugins.values()
        ]

    def values(self) -> Iterable[Plugin]:
        return self._plugins.values()
