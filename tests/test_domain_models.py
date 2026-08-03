from pp_aipp.domain import Ingredient, Nutrition, Recipe, RecipeStatus


def test_domain_models_hold_recipe_data() -> None:
    recipe = Recipe(
        book_id="book-1",
        recipe_id="PP-R001",
        title="Test Bowl",
        meal="Breakfast",
        servings=1,
        status=RecipeStatus.NUTRITION_LOCKED,
        ingredients=[Ingredient("Quark", 250, "g")],
        nutrition=Nutrition(400, 40, 30, 10, 5),
    )
    assert recipe.recipe_id == "PP-R001"
    assert recipe.ingredients[0].unit == "g"
    assert recipe.nutrition and recipe.nutrition.locked
