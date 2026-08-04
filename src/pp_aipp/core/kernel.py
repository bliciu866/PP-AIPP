from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from pp_aipp import __version__

from ..domain import ProjectDatabase
from ..registry import ProjectRegistry
from .ai import AIGateway
from .config import ConfigManager
from .jobs import JobEngine
from .logging import configure_logging
from .plugins import PluginManager
from .workspace import WorkspaceManager


@dataclass(slots=True)
class KernelHealth:
    status: str
    version: str
    config: str
    workspace_root: str
    plugins_registered: int
    registry_status: str
    project_database_status: str


class Kernel:
    def __init__(self, config_path: str | Path = "config/default.yaml") -> None:
        self.config = ConfigManager.load(config_path)
        self.logger = configure_logging(
            self.config.get("logging.level", "INFO"),
            self.config.get("paths.log_dir", "logs"),
            self.config.get("logging.filename", "pp-aipp.log"),
        )
        self.workspaces = WorkspaceManager(self.config.get("paths.workspace_root", "workspaces"))
        self.plugins = PluginManager()
        self.jobs = JobEngine()
        self.ai = AIGateway()
        self.registry = ProjectRegistry(self.config.get("paths.registry_db", "data/registry.sqlite3"))
        self.project_database = ProjectDatabase(self.config.get("paths.project_db", "data/project.sqlite3"))
        self.started = False

    def start(self) -> None:
        if self.started:
            return
        self.plugins.discover()
        self.plugins.activate_all(self)
        self.started = True
        self.logger.info("PP-AIPP kernel started: %s", __version__)

    def stop(self) -> None:
        if self.started:
            self.logger.info("PP-AIPP kernel stopped")
        self.started = False

    def health(self) -> KernelHealth:
        return KernelHealth(
            status="READY" if self.started else "INITIALIZED",
            version=__version__,
            config=str(self.config.source),
            workspace_root=str(self.workspaces.root.resolve()),
            plugins_registered=len(self.plugins.list()),
            registry_status=str(self.registry.summary()["status"]),
            project_database_status=str(self.project_database.summary()["status"]),
        )
