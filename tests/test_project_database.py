from pathlib import Path

from pp_aipp.domain import (
    Asset,
    AssetKind,
    Ingredient,
    MethodStep,
    Nutrition,
    ProjectDatabase,
    QARecord,
    QASeverity,
    Recipe,
    RecipeStatus,
)


def sample_recipe() -> Recipe:
    return Recipe(
        book_id="book-30dfl",
        recipe_id="PP-R061",
        title="Vanilla Quark, Pear & Walnut Breakfast Bowl",
        meal="Breakfast",
        servings=1,
        description="A smooth, protein-rich breakfast bowl.",
        status=RecipeStatus.NUTRITION_LOCKED,
        meal_prep="Prepare up to 2 days ahead.",
        chef_tip="Add walnuts immediately before serving.",
        ingredient_swap="Replace pear with apple.",
        ingredients=[Ingredient("Quark", 250, "g"), Ingredient("Pear", 150, "g")],
        method=[MethodStep(1, "Place the quark in a bowl."), MethodStep(2, "Top with pear.")],
        nutrition=Nutrition(409, 41.6, 28.4, 15.0, 5.6),
        badges=["High Protein", "Breakfast", "Meal Prep Friendly"],
        qa_records=[QARecord("Nutrition", "Direct CoFID records used.", QASeverity.INFO)],
        assets=[Asset(AssetKind.HERO_IMAGE, "images/PP-R061.jpg", alt_text="Quark bowl with pear")],
    )


def test_project_database_persists_complete_recipe(tmp_path: Path) -> None:
    path = tmp_path / "project.sqlite3"
    database = ProjectDatabase(path)
    database.save_recipe(sample_recipe())

    reopened = ProjectDatabase(path)
    stored = reopened.get_recipe("book-30dfl", "PP-R061")
    assert stored is not None
    assert stored["title"].startswith("Vanilla Quark")
    assert len(stored["ingredients"]) == 2
    assert stored["method"][0]["number"] == 1
    assert stored["nutrition"]["energy_kcal"] == 409
    assert stored["nutrition"]["locked"] is True
    assert stored["badges"][0] == "High Protein"
    assert stored["qa_records"][0]["category"] == "Nutrition"
    assert stored["assets"][0]["kind"] == "HERO_IMAGE"


def test_project_database_search_and_filter(tmp_path: Path) -> None:
    database = ProjectDatabase(tmp_path / "project.sqlite3")
    database.save_recipe(sample_recipe())
    assert database.list_recipes("book-30dfl", meal="Breakfast")[0]["recipe_id"] == "PP-R061"
    assert database.search_ingredients("quark")[0]["recipe_id"] == "PP-R061"


def test_recipe_save_is_atomic(tmp_path: Path) -> None:
    database = ProjectDatabase(tmp_path / "project.sqlite3")
    recipe = sample_recipe()
    recipe.ingredients.append(Ingredient("Broken", -1, "g"))
    try:
        database.save_recipe(recipe)
    except Exception:
        pass
    else:
        raise AssertionError("Expected database constraint failure")
    assert database.summary()["recipes"] == 0
