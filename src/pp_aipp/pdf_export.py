"""Dependency-free-from-office PDF rendering for publishing exports."""
from __future__ import annotations

from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import (
    KeepTogether,
    PageBreak,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

from .layout.repository import LayoutRecipeRepository

GREEN = colors.HexColor("#3E8E41")
SAGE = colors.HexColor("#EAF5EA")
CHARCOAL = colors.HexColor("#2E2E2E")
GREY = colors.HexColor("#F3F3F3")


def _text(value: object) -> str:
    return str(value or "").replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def _footer(canvas, document) -> None:
    canvas.saveState()
    canvas.setFont("Helvetica", 7)
    canvas.setFillColor(colors.HexColor("#666666"))
    canvas.drawCentredString(letter[0] / 2, 0.32 * inch, f"PROJECT PHYSIQUE™  •  {document.page}")
    canvas.restoreState()


def build_publishing_pdf(database_path: str | Path, output_path: str | Path) -> Path:
    """Render all persisted recipes to a portable US Letter publishing PDF."""
    database = Path(database_path).expanduser().resolve()
    output = Path(output_path).expanduser().resolve()
    recipes = LayoutRecipeRepository(database).list_recipes()
    if not recipes:
        raise ValueError("No recipes found for PDF export")
    output.parent.mkdir(parents=True, exist_ok=True)

    styles = getSampleStyleSheet()
    title = ParagraphStyle(
        "RecipeTitle", parent=styles["Title"], fontName="Helvetica-Bold", fontSize=20,
        leading=22, textColor=CHARCOAL, spaceAfter=5,
    )
    recipe_id = ParagraphStyle(
        "RecipeId", parent=styles["Normal"], fontName="Helvetica-Bold", fontSize=8,
        textColor=GREEN, spaceAfter=2,
    )
    body = ParagraphStyle(
        "Body", parent=styles["BodyText"], fontName="Helvetica", fontSize=8,
        leading=10, textColor=CHARCOAL,
    )
    small = ParagraphStyle(
        "Small", parent=body, fontSize=7, leading=8.5,
    )
    heading = ParagraphStyle(
        "Heading", parent=styles["Heading2"], fontName="Helvetica-Bold", fontSize=11,
        leading=13, textColor=GREEN, spaceBefore=4, spaceAfter=3,
    )
    centered = ParagraphStyle("Centered", parent=small, alignment=TA_CENTER)

    document = SimpleDocTemplate(
        str(output), pagesize=letter, rightMargin=0.62 * inch, leftMargin=0.72 * inch,
        topMargin=0.55 * inch, bottomMargin=0.55 * inch,
        title="Project Physique — 30 Days Fat Loss", author="Project Physique",
    )
    story = []
    for index, recipe in enumerate(recipes):
        if index:
            story.append(PageBreak())
        story.extend([
            Paragraph(_text(recipe.get("recipe_id")), recipe_id),
            Paragraph(_text(recipe.get("title")), title),
            Paragraph(_text(recipe.get("description")), body),
            Spacer(1, 5),
        ])
        badges = "  |  ".join(recipe.get("badges", [])[:6]) or "UK CoFID Verified"
        story.append(Paragraph(_text(badges), recipe_id))
        info = [[
            Paragraph(f"<b>MEAL</b><br/>{_text(recipe.get('meal') or '—')}", centered),
            Paragraph(f"<b>SERVINGS</b><br/>{recipe.get('servings', 1)}", centered),
            Paragraph(f"<b>INGREDIENTS</b><br/>{len(recipe.get('ingredients', []))}", centered),
            Paragraph(f"<b>STATUS</b><br/>{_text(recipe.get('status', '—')).replace('_', ' ')}", centered),
        ]]
        info_table = Table(info, colWidths=[1.78 * inch] * 4)
        info_table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, -1), SAGE), ("BOX", (0, 0), (-1, -1), 0.35, colors.white),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"), ("TOPPADDING", (0, 0), (-1, -1), 5),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ]))
        story.extend([info_table, Spacer(1, 5)])

        ingredients = [Paragraph("<b>Ingredients</b>", heading)]
        for item in recipe.get("ingredients", []):
            ingredients.append(Paragraph(
                f"<font color='#3E8E41'><b>{item['quantity']:g} {_text(item['unit'])}</b></font>  {_text(item['name'])}",
                body,
            ))
        methods = [Paragraph("<b>Method</b>", heading)]
        for step in recipe.get("method", []):
            methods.append(Paragraph(
                f"<font color='#3E8E41'><b>{step['number']}.</b></font> {_text(step['text'])}", body,
            ))
        content = Table([[ingredients, methods]], colWidths=[2.55 * inch, 4.57 * inch])
        content.setStyle(TableStyle([
            ("VALIGN", (0, 0), (-1, -1), "TOP"), ("LEFTPADDING", (0, 0), (-1, -1), 5),
            ("RIGHTPADDING", (0, 0), (-1, -1), 5), ("BOX", (0, 0), (-1, -1), 0.35, colors.lightgrey),
            ("INNERGRID", (0, 0), (-1, -1), 0.35, colors.lightgrey),
        ]))
        story.extend([content, Spacer(1, 4)])

        nutrition = recipe.get("nutrition")
        if nutrition:
            labels = ("Energy", "Protein", "Carbs", "Fat", "Fibre")
            values = (
                f"{nutrition['energy_kcal']:g} kcal", f"{nutrition['protein_g']:g} g",
                f"{nutrition['carbohydrate_g']:g} g", f"{nutrition['fat_g']:g} g",
                f"{nutrition['fibre_g']:g} g",
            )
            nutrition_table = Table([
                [Paragraph(label, centered) for label in labels],
                [Paragraph(f"<b>{value}</b>", centered) for value in values],
            ], colWidths=[1.424 * inch] * 5)
            nutrition_table.setStyle(TableStyle([
                ("BACKGROUND", (0, 0), (-1, -1), SAGE),
                ("GRID", (0, 0), (-1, -1), 0.35, colors.white),
            ]))
            story.extend([Paragraph("Nutrition per serving", heading), nutrition_table])

        panels = [("Meal Prep", recipe.get("meal_prep"), SAGE)]
        if recipe.get("chef_tip"):
            panels.append(("Chef's Tip", recipe["chef_tip"], colors.HexColor("#FFF4CC")))
        if recipe.get("ingredient_swap"):
            panels.append(("Ingredient Swap", recipe["ingredient_swap"], GREY))
        for label, value, fill in panels:
            if value:
                panel = Table([[Paragraph(f"<b>{label}:</b> {_text(value)}", small)]], colWidths=[7.12 * inch])
                panel.setStyle(TableStyle([
                    ("BACKGROUND", (0, 0), (-1, -1), fill), ("LEFTPADDING", (0, 0), (-1, -1), 6),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 6), ("TOPPADDING", (0, 0), (-1, -1), 4),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
                ]))
                story.append(KeepTogether([Spacer(1, 3), panel]))

    document.build(story, onFirstPage=_footer, onLaterPages=_footer)
    return output
