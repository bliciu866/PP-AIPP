from pathlib import Path

from pp_aipp.registry import BookRecord, ProjectRecord, ProjectRegistry, ReleaseRecord


def test_registry_persists_projects_books_and_releases(tmp_path: Path) -> None:
    db_path = tmp_path / "registry.sqlite3"
    registry = ProjectRegistry(db_path)
    project = registry.add_project(ProjectRecord("project-physique", "Project Physique", "Project Physique"))
    book = registry.add_book(BookRecord(project.id, "30-days-fat-loss", "30 Days Fat Loss"))
    registry.add_release(ReleaseRecord(book.id, "4.1.0", "Gold Master Final"))

    reopened = ProjectRegistry(db_path)
    assert reopened.get_project("project-physique")["name"] == "Project Physique"
    assert reopened.list_books("project-physique")[0]["title"] == "30 Days Fat Loss"
    assert reopened.summary()["releases"] == 1
    assert len(reopened.history()) == 3


def test_foreign_keys_reject_orphan_book(tmp_path: Path) -> None:
    registry = ProjectRegistry(tmp_path / "registry.sqlite3")
    try:
        registry.add_book(BookRecord("missing", "orphan", "Orphan"))
    except Exception as exc:
        assert "FOREIGN KEY" in str(exc).upper()
    else:
        raise AssertionError("Expected foreign key failure")
