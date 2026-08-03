from __future__ import annotations

from pathlib import Path

from pp_aipp.domain.database import DomainDatabase, decode_json


class LayoutRecipeRepository:
    """Read-only projection of publishing data from the domain database."""

    def __init__(self, database_path: str | Path) -> None:
        self.db = DomainDatabase(database_path)

    def list_recipes(self, book_id: str | None = None) -> list[dict]:
        sql = "SELECT * FROM recipes"
        params: tuple = ()
        if book_id:
            sql += " WHERE book_id=?"
            params = (book_id,)
        sql += " ORDER BY recipe_id"
        recipes = self.db.fetchall(sql, params)
        for recipe in recipes:
            pk = recipe["id"]
            recipe["metadata"] = decode_json(recipe.pop("metadata_json", "{}"))
            recipe["ingredients"] = self.db.fetchall(
                "SELECT * FROM ingredients WHERE recipe_pk=? ORDER BY position", (pk,)
            )
            recipe["method"] = self.db.fetchall(
                "SELECT * FROM method_steps WHERE recipe_pk=? ORDER BY number", (pk,)
            )
            recipe["nutrition"] = self.db.fetchone(
                "SELECT * FROM nutrition WHERE recipe_pk=?", (pk,)
            )
            recipe["badges"] = [r["badge"] for r in self.db.fetchall(
                "SELECT badge FROM recipe_badges WHERE recipe_pk=? ORDER BY position", (pk,)
            )]
            recipe["qa_records"] = self.db.fetchall(
                "SELECT * FROM qa_records WHERE recipe_pk=? ORDER BY rowid", (pk,)
            )
            recipe["assets"] = self.db.fetchall(
                "SELECT * FROM assets WHERE recipe_pk=? ORDER BY rowid", (pk,)
            )
        return recipes
