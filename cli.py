from __future__ import annotations

import argparse
import json
from dataclasses import asdict

from .core.kernel import Kernel
from .core.models import Job


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="pp-aipp", description="PP-AIPP v3.0")
    parser.add_argument("--config", default="config/default.yaml")
    commands = parser.add_subparsers(dest="command", required=True)
    commands.add_parser("doctor")

    workspace = commands.add_parser("workspace")
    workspace_sub = workspace.add_subparsers(dest="workspace_command", required=True)
    create = workspace_sub.add_parser("create")
    create.add_argument("slug")
    workspace_sub.add_parser("list")

    plugins = commands.add_parser("plugins")
    plugins.add_subparsers(dest="plugins_command", required=True).add_parser("list")

    job = commands.add_parser("job")
    job.add_subparsers(dest="job_command", required=True).add_parser("demo")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    kernel = Kernel(args.config)
    kernel.start()
    try:
        if args.command == "doctor":
            print(json.dumps(asdict(kernel.health()), indent=2))
        elif args.command == "workspace" and args.workspace_command == "create":
            ws = kernel.workspaces.create(args.slug)
            print(json.dumps({"slug": ws.slug, "root": str(ws.root)}, indent=2))
        elif args.command == "workspace" and args.workspace_command == "list":
            print(json.dumps(kernel.workspaces.list(), indent=2))
        elif args.command == "plugins" and args.plugins_command == "list":
            print(json.dumps(kernel.plugins.list(), indent=2))
        elif args.command == "job" and args.job_command == "demo":
            job = kernel.jobs.run(Job("demo", {"message": "kernel operational"}), lambda p: p)
            print(json.dumps({"id": job.id, "status": job.status, "result": job.result}, indent=2, default=str))
        return 0
    finally:
        kernel.stop()


if __name__ == "__main__":
    raise SystemExit(main())
