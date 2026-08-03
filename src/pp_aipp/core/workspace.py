from __future__ import annotations

import json
import re
from dataclasses import asdict
from pathlib import Path

from .models import Workspace


class WorkspaceManager:
    FOLDERS = ("books", "data", "assets", "images", "exports", "marketing", "qa", "archive", "cache")

    def __init__(self, root: str | Path = "workspaces") -> None:
        self.root = Path(root)
        self.root.mkdir(parents=True, exist_ok=True)

    def create(self, slug: str) -> Workspace:
        if not re.fullmatch(r"[a-z0-9][a-z0-9-]{1,62}", slug):
            raise ValueError("Workspace slug must use lowercase letters, digits and hyphens.")
        target = self.root / slug
        target.mkdir(parents=True, exist_ok=False)
        for folder in self.FOLDERS:
            (target / folder).mkdir()
        workspace = Workspace(slug=slug, root=target.resolve())
        manifest = asdict(workspace)
        manifest["root"] = str(workspace.root)
        (target / "workspace.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
        return workspace

    def list(self) -> list[str]:
        return sorted(p.name for p in self.root.iterdir() if p.is_dir() and (p / "workspace.json").exists())
