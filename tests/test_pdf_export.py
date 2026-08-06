import json

from pp_aipp.domain import Ingredient, MethodStep, Nutrition, ProjectDatabase, Recipe
from pp_aipp.pdf_export import _editorial_content, build_publishing_pdf
from pp_aipp.publication_qa import polished_method_steps, polish_method_text


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


def test_b36_seafood_method_does_not_mention_poultry_or_pork():
    source = (
        "Heat the oil in a non-stick pan and cook the Salmon fillet until browned and safely cooked; "
        "poultry and pork must reach 75°C, while fish should flake easily."
    )
    result = polish_method_text(source, ["Salmon fillet", "Basmati rice"])

    assert "poultry" not in result.lower()
    assert "pork" not in result.lower()
    assert "flakes easily" in result


def test_b36_beef_method_does_not_include_poultry_temperature():
    source = "Season and cook the meat until browned and fully cooked; poultry must reach 75°C."

    result = polish_method_text(source, ["Lean beef mince"])

    assert result == "Season and cook the meat until browned and fully cooked."


def test_b36_plant_recipes_receive_real_plant_methods():
    steps = polished_method_steps(
        "PP-R067",
        [{"number": 1, "text": "Pat the main protein dry."}],
        ["Cooked green lentils", "Butternut squash"],
    )

    joined = " ".join(step["text"] for step in steps).lower()
    assert len(steps) == 5
    assert "main protein" not in joined
    assert "meat" not in joined
    assert "lentils" in joined
