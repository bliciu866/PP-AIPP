from pathlib import Path

from pp_aipp.domain.models import Ingredient, MethodStep, Nutrition, QARecord, Recipe, RecipeStatus
from pp_aipp.domain.service import ProjectDatabase
from pp_aipp.layout.repository import LayoutRecipeRepository
from pp_aipp.layout.service import LayoutEngine


def seed(path: Path) -> None:
    service=ProjectDatabase(path)
    recipe=Recipe(book_id="book-1",recipe_id="PP-R001",title="Test Protein Bowl",meal="Breakfast",servings=1,status=RecipeStatus.NUTRITION_LOCKED,description="A controlled layout test recipe.",meal_prep="Refrigerate for up to 2 days.")
    recipe.ingredients=[Ingredient("Quark",250,"g"),Ingredient("Blueberries",80,"g")]
    recipe.method=[MethodStep(1,"Place the quark in a bowl."),MethodStep(2,"Top with blueberries.")]
    recipe.nutrition=Nutrition(320,38,25,8,5)
    recipe.badges=["Breakfast","High Protein","UK CoFID Verified"]
    recipe.qa_records=[QARecord(category="Nutrition",message="Source verified.")]
    service.save_recipe(recipe, replace=True)


def test_repository_projection(tmp_path):
    db=tmp_path/"book.sqlite3"; seed(db)
    rows=LayoutRecipeRepository(db).list_recipes("book-1")
    assert len(rows)==1
    assert rows[0]["recipe_id"]=="PP-R001"
    assert len(rows[0]["ingredients"])==2
    assert rows[0]["nutrition"]["protein_g"]==38


def test_layout_builds_docx(tmp_path):
    db=tmp_path/"book.sqlite3"; seed(db)
    output=tmp_path/"out"/"book.docx"
    result=LayoutEngine(db).build_book(output,book_id="book-1",pdf=False)
    assert output.exists() and output.stat().st_size>10000
    assert result.recipe_count==1
    assert result.page_breaks==0


def test_layout_report(tmp_path):
    db=tmp_path/"book.sqlite3"; seed(db)
    engine=LayoutEngine(db)
    result=engine.build_book(tmp_path/"book.docx",pdf=False)
    report=engine.write_report(result,tmp_path/"report.json")
    assert '"recipe_count": 1' in report.read_text()
