from pathlib import Path

from pp_aipp.domain import ProjectDatabase
from pp_aipp.parser import GoldMasterImportService
from test_gold_master_parser import build_sample


def test_import_service_persists_recipe(tmp_path: Path) -> None:
    source = tmp_path / "sample.docx"
    build_sample(source)
    database = ProjectDatabase(tmp_path / "project.sqlite3")
    summary, result = GoldMasterImportService(database).import_docx(
        source, book_id="book-1", report_path=tmp_path / "report.json", strict_collection=False
    )
    assert summary.imported_recipes == 1
    assert summary.errors == 0
    assert database.summary()["recipes"] == 1
    assert result.recipes[0].title == "Sample Protein Breakfast"
