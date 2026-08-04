from __future__ import annotations

import argparse
import json
from dataclasses import asdict
from pathlib import Path

from .core.kernel import Kernel
from .core.models import Job
from .parser import GoldMasterImportService
from .registry import BookRecord, ProjectRecord, ReleaseRecord
from .release import MilestonePackBuilder, PackConfig
from .verification import (
    VerificationConfig,
    VerificationRunner,
    write_html,
    write_json,
    write_markdown,
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="pp-aipp", description="PP-AIPP v3.0")
    parser.add_argument("--config", default="config/default.yaml")
    commands = parser.add_subparsers(dest="command", required=True)
    commands.add_parser("doctor")
    commands.add_parser("desktop")

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

    parser_cmd = commands.add_parser("parser")
    parser_sub = parser_cmd.add_subparsers(dest="parser_command", required=True)
    import_docx = parser_sub.add_parser("import-docx")
    import_docx.add_argument("source")
    import_docx.add_argument("--book-id", required=True)
    import_docx.add_argument("--report", default="output/parser_import/import_report.json")
    import_docx.add_argument("--no-replace", action="store_true")
    parser_status = parser_sub.add_parser("status")
    parser_status.add_argument("--book-id", required=True)

    verify = commands.add_parser("verify")
    verify.add_argument("--gold-master")
    verify.add_argument("--report-dir", default="reports/latest")
    verify.add_argument("--skip-lint", action="store_true")
    verify.add_argument("--skip-gold-master", action="store_true")

    release_pack = commands.add_parser("release-pack")
    release_pack.add_argument("--milestone", required=True)
    release_pack.add_argument("--output-dir", default="dist/releases")
    release_pack.add_argument("--version")
    release_pack.add_argument("--verification-report")
    release_pack.add_argument("--allow-dirty", action="store_true")
    release_pack.add_argument("--skip-verification", action="store_true")
    release_pack.add_argument("--git-bundle", action="store_true")
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
        elif args.command == "desktop":
            kernel.stop()
            from .desktop.app import main as desktop_main
            return desktop_main([])
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
        elif args.command == "verify":
            root = Path.cwd()
            report_dir = root / args.report_dir
            gold_master = root / args.gold_master if args.gold_master else None
            report = VerificationRunner(
                VerificationConfig(
                    project_root=root,
                    report_dir=report_dir,
                    gold_master=gold_master,
                    run_lint=not args.skip_lint,
                    run_gold_master=not args.skip_gold_master,
                )
            ).run()
            write_json(report, report_dir / "verification_report.json")
            write_markdown(report, report_dir / "verification_report.md")
            write_html(report, report_dir / "verification_report.html")
            emit(report.to_dict())
            return 0 if report.passed else 1
        elif args.command == "release-pack":
            root = Path.cwd()
            result = MilestonePackBuilder(
                PackConfig(
                    repository=root,
                    output_dir=root / args.output_dir,
                    milestone=args.milestone,
                    version=args.version,
                    require_clean_git=not args.allow_dirty,
                    require_verification=not args.skip_verification,
                    verification_report=(root / args.verification_report if args.verification_report else None),
                    include_git_bundle=args.git_bundle,
                )
            ).build()
            emit(result.to_dict())
        elif args.command == "parser":
            if args.parser_command == "import-docx":
                service = GoldMasterImportService(kernel.project_database)
                summary, result = service.import_docx(
                    args.source,
                    book_id=args.book_id,
                    replace=not args.no_replace,
                    report_path=args.report,
                )
                emit({"summary": asdict(summary), "issues": [asdict(issue) for issue in result.issues]})
                return 1 if summary.errors else 0
            elif args.parser_command == "status":
                recipes = kernel.project_database.db.fetchall(
                    "SELECT recipe_id, title, meal, status FROM recipes WHERE book_id=? ORDER BY recipe_id",
                    (args.book_id,),
                )
                emit({"book_id": args.book_id, "recipe_count": len(recipes), "recipes": recipes})
        return 0
    finally:
        kernel.stop()


if __name__ == "__main__":
    raise SystemExit(main())
