"""Production build pipeline connecting Gold Master import to the layout engine."""
from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

from .domain import ProjectDatabase
from .layout import LayoutBuildResult, LayoutEngine
from .parser import GoldMasterImportService, ImportSummary


@dataclass(frozen=True, slots=True)
class BookBuildPipelineResult:
    book_id: str
    database_path: Path
    import_report_path: Path
    layout_report_path: Path
    import_summary: ImportSummary
    layout: LayoutBuildResult


def _book_id(project_root: Path) -> str:
    value = re.sub(r"[^a-z0-9]+", "-", project_root.name.lower()).strip("-")
    return value or "project-physique-book"


def build_gold_master_book(
    project_root: str | Path,
    source_docx: str | Path,
    *,
    strict_collection: bool = True,
) -> BookBuildPipelineResult:
    """Parse a controlled DOCX, persist recipes, and generate a built book DOCX."""
    root = Path(project_root).expanduser().resolve()
    source = Path(source_docx).expanduser().resolve()
    if not source.is_file():
        raise FileNotFoundError(source)

    data_dir = root / "data"
    qa_dir = root / "qa"
    exports_dir = root / "exports"
    for directory in (data_dir, qa_dir, exports_dir):
        directory.mkdir(parents=True, exist_ok=True)

    book_id = _book_id(root)
    database_path = data_dir / "project.sqlite3"
    import_report = qa_dir / "gold_master_import_report.json"
    layout_report = qa_dir / "layout_build_report.json"
    output_docx = exports_dir / "Project_Physique_30_Days_Fat_Loss_Built.docx"

    database = ProjectDatabase(database_path)
    importer = GoldMasterImportService(database)
    summary, parsed = importer.import_docx(
        source,
        book_id=book_id,
        replace=True,
        report_path=import_report,
        strict_collection=strict_collection,
    )
    if parsed.issues:
        errors = [issue for issue in parsed.issues if issue.severity == "ERROR"]
        if errors:
            detail = "; ".join(f"{issue.code}: {issue.message}" for issue in errors[:5])
            raise ValueError(f"Gold Master parse failed: {detail}")
    if summary.imported_recipes == 0:
        raise ValueError("Gold Master contains no importable recipes")

    layout = LayoutEngine(database_path).build_book(output_docx, book_id=book_id, pdf=False)
    LayoutEngine.write_report(layout, layout_report)
    return BookBuildPipelineResult(
        book_id=book_id,
        database_path=database_path,
        import_report_path=import_report,
        layout_report_path=layout_report,
        import_summary=summary,
        layout=layout,
    )
