import json

from PIL import Image

from pp_aipp.photography import import_photo_assets


def _image(path, size):
    Image.new("RGB", size, "#3E8E41").save(path)


def test_import_photos_assigns_ids_and_reports_readiness(tmp_path):
    project = tmp_path / "project"
    source = tmp_path / "incoming"
    source.mkdir()
    _image(source / "PP-R001.jpg", (1200, 1500))
    _image(source / "PP-R002_hero.png", (1600, 1200))
    _image(source / "wrong-name.jpg", (1200, 1500))

    result = import_photo_assets(project, source, recipe_ids=["PP-R001", "PP-R002", "PP-R003"])

    assert result.imported == 2
    assert result.ready == 1
    assert result.needs_crop == 1
    assert result.rejected == 1
    assert result.missing == 1
    assert (project / "images" / "PP-R001.jpg").is_file()
    assert (project / "images" / "PP-R002.png").is_file()
    report = json.loads(result.report_path.read_text(encoding="utf-8"))
    assert report["missing_recipe_ids"] == ["PP-R003"]
    assert report["assets"][0]["status"] == "READY"
    assert report["assets"][1]["status"] == "NEEDS_CROP"


def test_import_photos_rejects_duplicates(tmp_path):
    project = tmp_path / "project"
    source = tmp_path / "incoming"
    source.mkdir()
    _image(source / "PP-R001.jpg", (1200, 1500))
    _image(source / "PP-R001_hero.png", (1200, 1500))

    result = import_photo_assets(project, source, recipe_ids=["PP-R001"])

    assert result.imported == 1
    assert result.rejected == 1
