from pp_aipp.domain import Ingredient, MethodStep, Nutrition, ProjectDatabase, Recipe
from pp_aipp.pdf_export import build_publishing_pdf


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

    output = build_publishing_pdf(database_path, tmp_path / "book.pdf")

    assert output.is_file()
    assert output.read_bytes().startswith(b"%PDF-")
    assert output.stat().st_size > 1000
