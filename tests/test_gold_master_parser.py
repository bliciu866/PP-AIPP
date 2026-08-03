from pathlib import Path

import pytest
from docx import Document

from pp_aipp.parser import GoldMasterParser


def build_sample(path: Path) -> None:
    doc = Document()
    doc.add_paragraph("PP-R001")
    doc.add_paragraph("Sample Protein Breakfast")
    doc.add_paragraph("🥣 Breakfast | 💪 High Protein | ✓ UK CoFID Verified")
    info = doc.add_table(rows=2, cols=4)
    info.rows[0].cells[0].text = "Meal"
    info.rows[0].cells[1].text = "Breakfast"
    info.rows[0].cells[2].text = "Servings"
    info.rows[0].cells[3].text = "1"
    info.rows[1].cells[0].text = "Ingredients"
    info.rows[1].cells[1].text = "2"
    info.rows[1].cells[2].text = "Status"
    info.rows[1].cells[3].text = "NUTRITION LOCKED"
    doc.add_paragraph("Ingredients")
    ing = doc.add_table(rows=3, cols=2)
    ing.rows[0].cells[0].text = "Ingredient"
    ing.rows[0].cells[1].text = "Quantity"
    ing.rows[1].cells[0].text = "Quark"
    ing.rows[1].cells[1].text = "250 g"
    ing.rows[2].cells[0].text = "Blueberries"
    ing.rows[2].cells[1].text = "80 g"
    doc.add_paragraph("Method")
    doc.add_paragraph("1. Mix and serve.")
    doc.add_paragraph("Nutrition per serving")
    nut = doc.add_table(rows=2, cols=5)
    for i, label in enumerate(("Energy", "Protein", "Carbohydrates", "Fat", "Fibre")):
        nut.rows[0].cells[i].text = label
    for i, value in enumerate(("350 kcal", "35 g", "30 g", "8 g", "5 g")):
        nut.rows[1].cells[i].text = value
    doc.add_paragraph("QA note: direct records used.")
    doc.save(path)


def test_parser_creates_domain_recipe(tmp_path: Path) -> None:
    source = tmp_path / "sample.docx"
    build_sample(source)
    result = GoldMasterParser().parse(source, book_id="book-1")
    assert len(result.recipes) == 1
    recipe = result.recipes[0]
    assert recipe.recipe_id == "PP-R001"
    assert recipe.meal == "Breakfast"
    assert len(recipe.ingredients) == 2
    assert recipe.method[0].number == 1
    assert recipe.nutrition and recipe.nutrition.energy_kcal == 350


def test_parser_rejects_missing_file() -> None:
    with pytest.raises(ValueError):
        GoldMasterParser().parse("missing.docx", book_id="book-1")
