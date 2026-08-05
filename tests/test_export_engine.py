import hashlib
import json
import zipfile
from pathlib import Path

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
        lambda _database, output, **kwargs: (
            Path(kwargs["coverage_report_path"]).write_text('{"images_missing":80}', encoding="utf-8"),
            output.write_bytes(b"%PDF-1.4\n"),
            output,
        )[-1],
    )

    result = export_book_package(project, book)

    assert result.book_path.read_bytes() == b"controlled-book"
    assert result.manifest_path.is_file()
    assert result.package_path.is_file()
    manifest = json.loads(result.manifest_path.read_text(encoding="utf-8"))
    expected_hash = hashlib.sha256(b"controlled-book").hexdigest()
    assert manifest["application_version"] == "3.0.0b9"
    assert manifest["files"][0]["sha256"] == expected_hash
    with zipfile.ZipFile(result.package_path) as archive:
        assert set(archive.namelist()) == {
            "Project_Physique_30_Days_Fat_Loss_Export.docx",
            "Project_Physique_30_Days_Fat_Loss_Print.pdf",
            "PUBLISHING_README.txt",
            "image_coverage_report.json",
            "qa/layout_build_report.json",
            "export_manifest.json",
        }


def test_export_engine_builds_photo_pdf_and_preserves_layout_reference(tmp_path, monkeypatch):
    project = tmp_path / "30_Days_Fat_Loss"
    build = project / "build"
    images = project / "images"
    build.mkdir(parents=True)
    images.mkdir()
    book = build / "Project_Physique_30_Days_Fat_Loss_Built.docx"
    companion_pdf = book.with_suffix(".pdf")
    book.write_bytes(b"controlled-book")
    companion_pdf.write_bytes(b"%PDF-premium-layout")
    (images / "PP-R001.png").write_bytes(b"recipe-photo")

    calls = []

    def fake_pdf(_database, output, **kwargs):
        calls.append(Path(output))
        Path(kwargs["coverage_report_path"]).write_text(
            '{"images_found":1,"images_missing":0}', encoding="utf-8"
        )
        Path(output).write_bytes(b"%PDF-photo-edition")
        return Path(output)

    monkeypatch.setattr("pp_aipp.export_engine.build_publishing_pdf", fake_pdf)

    result = export_book_package(project, book)

    assert calls == [result.pdf_path]
    assert result.pdf_path.read_bytes() == b"%PDF-photo-edition"
    reference = result.export_dir / "Project_Physique_30_Days_Fat_Loss_Premium_Layout_Reference.pdf"
    assert reference.read_bytes() == b"%PDF-premium-layout"
    with zipfile.ZipFile(result.package_path) as archive:
        assert reference.name in archive.namelist()


def test_export_engine_rejects_missing_book(tmp_path):
    with pytest.raises(FileNotFoundError):
        export_book_package(tmp_path, tmp_path / "missing.docx")
