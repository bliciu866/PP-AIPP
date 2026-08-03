from __future__ import annotations

from .database import DomainDatabase, decode_json, encode_json
from .models import Recipe


class ProjectDatabase:
    def __init__(self, database_path: str) -> None:
        self.db = DomainDatabase(database_path)

    def save_recipe(self, recipe: Recipe, *, replace: bool = False) -> Recipe:
        verb = "INSERT OR REPLACE" if replace else "INSERT"
        with self.db.transaction() as connection:
            if replace:
                connection.execute("DELETE FROM recipes WHERE book_id=? AND recipe_id=?", (recipe.book_id, recipe.recipe_id))
            connection.execute(
                f"{verb} INTO recipes VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (
                    recipe.id, recipe.book_id, recipe.recipe_id, recipe.title, recipe.meal,
                    recipe.servings, recipe.description, recipe.status.value, recipe.meal_prep,
                    recipe.chef_tip, recipe.ingredient_swap, recipe.provenance.value,
                    encode_json(recipe.metadata),
                ),
            )
            for position, item in enumerate(recipe.ingredients, start=1):
                connection.execute(
                    "INSERT INTO ingredients VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                    (
                        item.id, recipe.id, position, item.name, item.quantity, item.unit,
                        item.source_ref, item.preparation_state, item.provenance.value,
                        encode_json(item.metadata),
                    ),
                )
            for step in recipe.method:
                connection.execute(
                    "INSERT INTO method_steps VALUES (?, ?, ?, ?, ?)",
                    (step.id, recipe.id, step.number, step.text, step.provenance.value),
                )
            if recipe.nutrition:
                value = recipe.nutrition
                connection.execute(
                    "INSERT INTO nutrition VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                    (
                        value.id, recipe.id, value.energy_kcal, value.protein_g,
                        value.carbohydrate_g, value.fat_g, value.fibre_g,
                        value.serving_basis, int(value.locked), value.provenance.value,
                        encode_json(value.metadata),
                    ),
                )
            for position, badge in enumerate(recipe.badges, start=1):
                connection.execute(
                    "INSERT INTO recipe_badges VALUES (?, ?, ?)",
                    (recipe.id, badge, position),
                )
            for qa in recipe.qa_records:
                connection.execute(
                    "INSERT INTO qa_records VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                    (
                        qa.id, recipe.id, qa.category, qa.message, qa.severity.value,
                        qa.status, qa.provenance.value, encode_json(qa.metadata),
                    ),
                )
            for asset in recipe.assets:
                connection.execute(
                    "INSERT INTO assets VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                    (
                        asset.id, recipe.id, asset.kind.value, asset.path, asset.alt_text,
                        asset.width_px, asset.height_px, asset.checksum, asset.licence,
                        encode_json(asset.metadata),
                    ),
                )
        return recipe

    def get_recipe(self, book_id: str, recipe_id: str) -> dict | None:
        recipe = self.db.fetchone(
            "SELECT * FROM recipes WHERE book_id=? AND recipe_id=?", (book_id, recipe_id)
        )
        if recipe is None:
            return None
        recipe["metadata"] = decode_json(recipe.pop("metadata_json"))
        pk = recipe["id"]
        recipe["ingredients"] = self._decode_rows(
            self.db.fetchall("SELECT * FROM ingredients WHERE recipe_pk=? ORDER BY position", (pk,))
        )
        recipe["method"] = self.db.fetchall(
            "SELECT id, number, text, provenance FROM method_steps WHERE recipe_pk=? ORDER BY number", (pk,)
        )
        nutrition = self.db.fetchone("SELECT * FROM nutrition WHERE recipe_pk=?", (pk,))
        if nutrition:
            nutrition["locked"] = bool(nutrition["locked"])
            nutrition["metadata"] = decode_json(nutrition.pop("metadata_json"))
        recipe["nutrition"] = nutrition
        recipe["badges"] = [row["badge"] for row in self.db.fetchall(
            "SELECT badge FROM recipe_badges WHERE recipe_pk=? ORDER BY position", (pk,)
        )]
        recipe["qa_records"] = self._decode_rows(
            self.db.fetchall("SELECT * FROM qa_records WHERE recipe_pk=? ORDER BY severity, id", (pk,))
        )
        recipe["assets"] = self._decode_rows(
            self.db.fetchall("SELECT * FROM assets WHERE recipe_pk=? ORDER BY kind, id", (pk,))
        )
        return recipe

    def list_recipes(self, book_id: str, *, meal: str | None = None) -> list[dict]:
        if meal:
            return self.db.fetchall(
                "SELECT recipe_id, title, meal, status FROM recipes WHERE book_id=? AND meal=? ORDER BY recipe_id",
                (book_id, meal),
            )
        return self.db.fetchall(
            "SELECT recipe_id, title, meal, status FROM recipes WHERE book_id=? ORDER BY recipe_id",
            (book_id,),
        )

    def search_ingredients(self, query: str) -> list[dict]:
        return self.db.fetchall(
            "SELECT r.recipe_id, r.title, i.name, i.quantity, i.unit "
            "FROM ingredients i JOIN recipes r ON r.id=i.recipe_pk "
            "WHERE lower(i.name) LIKE lower(?) ORDER BY r.recipe_id, i.position",
            (f"%{query}%",),
        )

    def summary(self) -> dict:
        return self.db.health()

    @staticmethod
    def _decode_rows(rows: list[dict]) -> list[dict]:
        for row in rows:
            if "metadata_json" in row:
                row["metadata"] = decode_json(row.pop("metadata_json"))
        return rows
