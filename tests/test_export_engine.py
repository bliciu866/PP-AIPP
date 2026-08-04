import hashlib
import json
import zipfile

import pytest

from pp_aipp.export_engine import export_book_package


def test_export_engine_creates_book_manifest_and_zip(tmp_path, monkeypatch):
    project = tmp_path / "30_Days_Fat_Loss"
    build = project / "build"
    qa = project / "qa"
    build.mkdir(parents=True)
    qa.mkdir()
    book = build / "Project_Physique_30_Days_Fat_Loss_Built.docx"
    book.write_bytes(b"controlled-book")
    (qa / "layout_build_report.json").write_text('{"status":"PASS"}', encoding="utf-8")
    monkeypatch.setattr(
        "pp_aipp.export_engine.build_publishing_pdf",
        lambda _database, output: output.write_bytes(b"%PDF-1.4\n") or output,
    )

    result = export_book_package(project, book)

    assert result.book_path.read_bytes() == b"controlled-book"
    assert result.manifest_path.is_file()
    assert result.package_path.is_file()
    manifest = json.loads(result.manifest_path.read_text(encoding="utf-8"))
    expected_hash = hashlib.sha256(b"controlled-book").hexdigest()
    assert manifest["application_version"] == "3.0.0b6.post2"
    assert manifest["files"][0]["sha256"] == expected_hash
    with zipfile.ZipFile(result.package_path) as archive:
        assert set(archive.namelist()) == {
            "Project_Physique_30_Days_Fat_Loss_Export.docx",
            "Project_Physique_30_Days_Fat_Loss_Print.pdf",
            "PUBLISHING_README.txt",
            "qa/layout_build_report.json",
            "export_manifest.json",
        }


def test_export_engine_rejects_missing_book(tmp_path):
    with pytest.raises(FileNotFoundError):
        export_book_package(tmp_path, tmp_path / "missing.docx")
