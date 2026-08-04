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


def test_incremental_batches_keep_existing_coverage(tmp_path):
    project = tmp_path / "project"
    first = tmp_path / "first"
    second = tmp_path / "second"
    first.mkdir()
    second.mkdir()
    _image(first / "PP-R001.jpg", (1200, 1500))
    _image(second / "PP-R002.jpg", (1200, 1500))

    import_photo_assets(project, first, recipe_ids=["PP-R001", "PP-R002", "PP-R003"])
    result = import_photo_assets(
        project, second, recipe_ids=["PP-R001", "PP-R002", "PP-R003"]
    )

    assert result.imported == 1
    assert result.ready == 2
    assert result.missing == 1
    report = json.loads(result.report_path.read_text(encoding="utf-8"))
    assert report["imported_this_batch"] == 1
    assert report["imported_images"] == 2
    assert report["missing_recipe_ids"] == ["PP-R003"]


def test_high_resolution_landscape_is_auto_cropped_to_production_ratio(tmp_path):
    project = tmp_path / "project"
    source = tmp_path / "incoming"
    source.mkdir()
    _image(source / "PP-R001.jpg", (2400, 1800))

    result = import_photo_assets(project, source, recipe_ids=["PP-R001"])

    assert result.ready == 1
    assert result.auto_prepared == 1
    with Image.open(project / "images" / "PP-R001.jpg") as prepared:
        assert prepared.size == (1200, 1500)


def test_reimport_replaces_previous_recipe_photo(tmp_path):
    project = tmp_path / "project"
    first = tmp_path / "first"
    second = tmp_path / "second"
    first.mkdir()
    second.mkdir()
    _image(first / "PP-R001.png", (1200, 1500))
    _image(second / "PP-R001.jpg", (1200, 1500))

    import_photo_assets(project, first, recipe_ids=["PP-R001"])
    result = import_photo_assets(project, second, recipe_ids=["PP-R001"])

    assert result.replaced == 1
    assert not (project / "images" / "PP-R001.png").exists()
    assert (project / "images" / "PP-R001.jpg").is_file()


def test_campaign_tracks_batches_coverage_and_next_missing(tmp_path):
    project = tmp_path / "project"
    first = tmp_path / "batch-01"
    second = tmp_path / "batch-02"
    first.mkdir()
    second.mkdir()
    _image(first / "PP-R001.jpg", (1200, 1500))
    _image(second / "PP-R002.jpg", (1200, 1500))

    one = import_photo_assets(project, first, recipe_ids=["PP-R001", "PP-R002", "PP-R003"])
    two = import_photo_assets(project, second, recipe_ids=["PP-R001", "PP-R002", "PP-R003"])

    assert one.batch_number == 1
    assert one.coverage_percent == 33.3
    assert two.batch_number == 2
    assert two.coverage_percent == 66.7
    assert two.next_missing == ("PP-R003",)
    history = json.loads(
        (project / "qa" / "photography_batch_history.json").read_text(encoding="utf-8")
    )
    assert [batch["imported"] for batch in history] == [1, 1]
    report = json.loads(two.report_path.read_text(encoding="utf-8"))
    assert report["schema_version"] == 3
    assert report["latest_batch_number"] == 2
