import json

from pp_aipp.domain import Ingredient, MethodStep, Nutrition, ProjectDatabase, Recipe
from pp_aipp.pdf_export import _editorial_content, build_publishing_pdf


def test_pdf_export_builds_portable_pdf(tmp_path):
    database_path = tmp_path / "project.sqlite3"
    database = ProjectDatabase(database_path)
    database.save_recipe(Recipe(
        book_id="book", recipe_id="PP-R001", title="PDF Export Recipe",
        meal="Breakfast", servings=1, description="A complete controlled export test recipe.",
        ingredients=[Ingredient("Porridge oats", 60, "g")],
        method=[MethodStep(1, "Mix and serve the recipe.")],
        nutrition=Nutrition(400, 30, 45, 10, 7),
        meal_prep="Prepare the night before.",
    ))

    coverage = tmp_path / "image_coverage_report.json"
    output = build_publishing_pdf(database_path, tmp_path / "book.pdf", coverage_report_path=coverage)

    assert output.is_file()
    assert output.read_bytes().startswith(b"%PDF-")
    assert output.stat().st_size > 1000
    assert b"DejaVuSans" in output.read_bytes()
    report = json.loads(coverage.read_text(encoding="utf-8"))
    assert report["total_recipes"] == 1
    assert report["images_found"] == 0
    assert report["missing_recipe_ids"] == ["PP-R001"]


def test_b34_legacy_recipe_receives_complete_editorial_cards():
    recipe = {
        "title": "Lemon Herb Cod",
        "meal": "Dinner",
        "ingredients": [{"name": "Cod fillet"}, {"name": "Baby potatoes"}],
        "method": [{"number": 1, "text": "Roast and serve."}],
        "meal_prep": "Prepare the vegetables ahead.",
    }

    cards = _editorial_content(recipe)

    assert set(cards) == {
        "chef_tip", "common_mistake", "ingredient_swap", "meal_prep", "serving_suggestion",
    }
    assert all(cards.values())
    assert "Cod fillet" in cards["chef_tip"]
