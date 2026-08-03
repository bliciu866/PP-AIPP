from __future__ import annotations

import argparse
import json
from dataclasses import asdict

from .core.kernel import Kernel
from .core.models import Job
from .registry import BookRecord, ProjectRecord, ReleaseRecord


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

    registry = commands.add_parser("registry")
    registry_sub = registry.add_subparsers(dest="registry_command", required=True)
    registry_sub.add_parser("status")
    project = registry_sub.add_parser("add-project")
    project.add_argument("slug")
    project.add_argument("name")
    project.add_argument("--brand")
    registry_sub.add_parser("list-projects")
    book = registry_sub.add_parser("add-book")
    book.add_argument("project_slug")
    book.add_argument("slug")
    book.add_argument("title")
    book.add_argument("--language", default="en-GB")
    books = registry_sub.add_parser("list-books")
    books.add_argument("--project")
    release = registry_sub.add_parser("add-release")
    release.add_argument("book_id")
    release.add_argument("version")
    release.add_argument("--notes", default="")
    history = registry_sub.add_parser("history")
    history.add_argument("--entity-type")
    history.add_argument("--entity-id")
    return parser


def emit(value: object) -> None:
    print(json.dumps(value, indent=2, ensure_ascii=False, default=str))


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    kernel = Kernel(args.config)
    kernel.start()
    try:
        if args.command == "doctor":
            emit(asdict(kernel.health()))
        elif args.command == "workspace" and args.workspace_command == "create":
            ws = kernel.workspaces.create(args.slug)
            emit({"slug": ws.slug, "root": str(ws.root)})
        elif args.command == "workspace" and args.workspace_command == "list":
            emit(kernel.workspaces.list())
        elif args.command == "plugins" and args.plugins_command == "list":
            emit(kernel.plugins.list())
        elif args.command == "job" and args.job_command == "demo":
            job = kernel.jobs.run(Job("demo", {"message": "kernel operational"}), lambda p: p)
            emit({"id": job.id, "status": job.status, "result": job.result})
        elif args.command == "registry":
            command = args.registry_command
            if command == "status":
                emit(kernel.registry.summary())
            elif command == "add-project":
                emit(asdict(kernel.registry.add_project(ProjectRecord(args.slug, args.name, args.brand))))
            elif command == "list-projects":
                emit(kernel.registry.list_projects())
            elif command == "add-book":
                project = kernel.registry.get_project(args.project_slug)
                if not project:
                    raise SystemExit(f"Unknown project: {args.project_slug}")
                emit(asdict(kernel.registry.add_book(BookRecord(project["id"], args.slug, args.title, args.language))))
            elif command == "list-books":
                emit(kernel.registry.list_books(args.project))
            elif command == "add-release":
                emit(asdict(kernel.registry.add_release(ReleaseRecord(args.book_id, args.version, args.notes))))
            elif command == "history":
                emit(kernel.registry.history(args.entity_type, args.entity_id))
        return 0
    finally:
        kernel.stop()


if __name__ == "__main__":
    raise SystemExit(main())
