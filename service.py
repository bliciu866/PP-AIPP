from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from pathlib import Path

from ..domain import ProjectDatabase
from .gold_master import GoldMasterParser, ParseResult


@dataclass(slots=True)
class ImportSummary:
    source: str
    book_id: str
    parsed_recipes: int
    imported_recipes: int
    ingredients: int
    method_steps: int
    conditional_pass: int
    errors: int
    warnings: int
    database: str


class GoldMasterImportService:
    def __init__(self, database: ProjectDatabase, parser: GoldMasterParser | None = None) -> None:
        self.database = database
        self.parser = parser or GoldMasterParser()

    def import_docx(
        self,
        source: str | Path,
        *,
        book_id: str,
        replace: bool = True,
        report_path: str | Path | None = None,
        strict_collection: bool = True,
    ) -> tuple[ImportSummary, ParseResult]:
        result = self.parser.parse(source, book_id=book_id, strict_collection=strict_collection)
        errors = sum(issue.severity == "ERROR" for issue in result.issues)
        if errors:
            summary = self._summary(result, book_id, imported=0)
            self._write_report(result, summary, report_path)
            return summary, result

        imported = 0
        for recipe in result.recipes:
            self.database.save_recipe(recipe, replace=replace)
            imported += 1

        summary = self._summary(result, book_id, imported=imported)
        self._write_report(result, summary, report_path)
        return summary, result

    def _summary(self, result: ParseResult, book_id: str, *, imported: int) -> ImportSummary:
        return ImportSummary(
            source=result.source,
            book_id=book_id,
            parsed_recipes=len(result.recipes),
            imported_recipes=imported,
            ingredients=sum(len(recipe.ingredients) for recipe in result.recipes),
            method_steps=sum(len(recipe.method) for recipe in result.recipes),
            conditional_pass=sum(recipe.status.value == "CONDITIONAL_PASS" for recipe in result.recipes),
            errors=sum(issue.severity == "ERROR" for issue in result.issues),
            warnings=sum(issue.severity == "WARNING" for issue in result.issues),
            database=str(self.database.db.path.resolve()),
        )

    @staticmethod
    def _write_report(
        result: ParseResult,
        summary: ImportSummary,
        report_path: str | Path | None,
    ) -> None:
        if report_path is None:
            return
        target = Path(report_path)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(
            json.dumps(
                {"import": asdict(summary), "parse": result.to_dict()},
                indent=2,
                ensure_ascii=False,
                default=str,
            ),
            encoding="utf-8",
        )
