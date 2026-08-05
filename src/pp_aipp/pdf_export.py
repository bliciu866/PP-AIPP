"""Dependency-free-from-office PDF rendering for publishing exports."""
from __future__ import annotations

import json
from io import BytesIO
from pathlib import Path

from PIL import Image as PILImage
from PIL import ImageOps
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.lib.utils import ImageReader
from reportlab.pdfgen import canvas
from reportlab.platypus import (
    Image,
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
IMAGE_EXTENSIONS = (".jpg", ".jpeg", ".png", ".webp")
NAVY = colors.HexColor("#102A43")
GOLD = colors.HexColor("#B98216")
CREAM = colors.HexColor("#F7F2E8")
PALE_BLUE = colors.HexColor("#EAF0F5")


def _text(value: object) -> str:
    return str(value or "").replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def _footer(canvas, document) -> None:
    canvas.saveState()
    canvas.setFont("Helvetica", 7)
    canvas.setFillColor(colors.HexColor("#666666"))
    canvas.drawCentredString(letter[0] / 2, 0.32 * inch, f"PROJECT PHYSIQUE™  •  {document.page}")
    canvas.restoreState()


def _recipe_image(project_root: Path, recipe: dict) -> Path | None:
    recipe_id = str(recipe.get("recipe_id") or "").upper()
    candidates: list[Path] = []
    for asset in recipe.get("assets", []):
        value = asset.get("file_path") or asset.get("path")
        if value:
            asset_path = Path(value)
            candidates.append(asset_path if asset_path.is_absolute() else project_root / asset_path)
    for directory in (project_root / "images", project_root / "assets" / "images"):
        for extension in IMAGE_EXTENSIONS:
            candidates.extend((directory / f"{recipe_id}{extension}", directory / f"{recipe_id}_hero{extension}"))
    return next((path.resolve() for path in candidates if path.is_file()), None)


def _hero_block(recipe: dict, image_path: Path | None, styles: dict) -> Table:
    recipe_id = _text(recipe.get("recipe_id"))
    if image_path:
        visual = Image(str(image_path), width=2.4 * inch, height=3.0 * inch)
        caption = Paragraph(f"{recipe_id}  •  PROJECT PHYSIQUE™", styles["hero_caption"])
    else:
        visual = Table(
            [[Paragraph(
                f"<b>HERO PHOTO</b><br/>{recipe_id}<br/><font size='7'>4:5 ASSET SLOT</font>",
                styles["hero_placeholder"],
            )]],
            colWidths=[2.4 * inch], rowHeights=[3.0 * inch],
        )
        visual.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, -1), GREY),
            ("BOX", (0, 0), (-1, -1), 0.8, colors.HexColor("#C8D5C8")),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ]))
        caption = Paragraph("Image pending — add a licensed production asset", styles["hero_caption"])
    block = Table([[visual], [caption]], colWidths=[2.5 * inch], hAlign="CENTER")
    block.setStyle(TableStyle([
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, -1), 2),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 2),
    ]))
    return block


def _wrap_canvas_text(pdf, text: object, font: str, size: float, width: float) -> list[str]:
    words = str(text or "").split()
    lines: list[str] = []
    current = ""
    for word in words:
        candidate = f"{current} {word}".strip()
        if pdf.stringWidth(candidate, font, size) <= width:
            current = candidate
        elif current:
            lines.append(current)
            current = word
        else:
            lines.append(word)
            current = ""
    if current:
        lines.append(current)
    return lines or [""]


def _draw_lines(pdf, lines: list[str], x: float, y: float, font: str, size: float,
                leading: float, colour=CHARCOAL, max_lines: int | None = None) -> float:
    pdf.setFont(font, size)
    pdf.setFillColor(colour)
    selected = lines[:max_lines] if max_lines else lines
    for line in selected:
        pdf.drawString(x, y, line)
        y -= leading
    return y


def _draw_cover(pdf) -> None:
    width, height = letter
    pdf.setFillColor(NAVY)
    pdf.rect(0, 0, width, height, fill=1, stroke=0)
    pdf.setFillColor(GOLD)
    pdf.rect(0.68 * inch, 0.72 * inch, 0.08 * inch, height - 1.44 * inch, fill=1, stroke=0)
    pdf.setFont("Helvetica-Bold", 13)
    pdf.drawString(1.05 * inch, height - 1.15 * inch, "PROJECT PHYSIQUE(TM)")
    pdf.setFillColor(colors.white)
    pdf.setFont("Helvetica-Bold", 38)
    pdf.drawString(1.05 * inch, height - 2.35 * inch, "30 DAYS")
    pdf.drawString(1.05 * inch, height - 2.92 * inch, "FAT LOSS")
    pdf.setFillColor(GOLD)
    pdf.setFont("Helvetica-Bold", 16)
    pdf.drawString(1.06 * inch, height - 3.38 * inch, "LUXURY PHOTO EDITION")
    pdf.setFillColor(colors.white)
    pdf.setFont("Helvetica", 11)
    pdf.drawString(1.06 * inch, height - 4.08 * inch, "80 nutrition-verified recipes")
    pdf.drawString(1.06 * inch, height - 4.34 * inch, "Designed for real UK kitchens")
    pdf.setFillColor(colors.HexColor("#D7E2EA"))
    pdf.setFont("Helvetica", 9)
    pdf.drawString(1.06 * inch, 1.12 * inch, "PREMIUM EDITORIAL SYSTEM  /  UK ENGLISH  /  CoFID-ALIGNED")
    pdf.showPage()


def _draw_collection_intro(pdf) -> None:
    width, height = letter
    pdf.setFillColor(CREAM)
    pdf.rect(0, 0, width, height, fill=1, stroke=0)
    pdf.setFillColor(GOLD)
    pdf.setFont("Helvetica-Bold", 10)
    pdf.drawCentredString(width / 2, height - 1.22 * inch, "THE RECIPE COLLECTION")
    pdf.setFillColor(NAVY)
    pdf.setFont("Helvetica-Bold", 27)
    pdf.drawCentredString(width / 2, height - 2.05 * inch, "Eighty ways to make")
    pdf.drawCentredString(width / 2, height - 2.48 * inch, "consistency taste better")
    pdf.setFillColor(CHARCOAL)
    pdf.setFont("Helvetica", 11)
    pdf.drawCentredString(width / 2, height - 3.25 * inch, "High-protein food, realistic shopping and repeatable progress.")
    pdf.setFillColor(NAVY)
    pdf.roundRect(1.05 * inch, height - 4.35 * inch, width - 2.1 * inch, 0.46 * inch, 5, fill=1, stroke=0)
    pdf.setFillColor(colors.white)
    pdf.setFont("Helvetica-Bold", 9)
    pdf.drawCentredString(width / 2, height - 4.07 * inch, "BREAKFAST     /     LUNCH     /     DINNER")
    pdf.setFillColor(GOLD)
    pdf.rect(2.2 * inch, 1.5 * inch, width - 4.4 * inch, 0.04 * inch, fill=1, stroke=0)
    pdf.showPage()


def _draw_photo(pdf, image_path: Path | None, x: float, y: float, width: float,
                height: float) -> None:
    if not image_path:
        pdf.setFillColor(PALE_BLUE)
        pdf.roundRect(x, y, width, height, 8, fill=1, stroke=0)
        pdf.setFillColor(NAVY)
        pdf.setFont("Helvetica-Bold", 11)
        pdf.drawCentredString(x + width / 2, y + height / 2, "PHOTO ASSET")
        return
    with PILImage.open(image_path) as source:
        fitted = ImageOps.fit(source.convert("RGB"), (900, 1125), method=PILImage.Resampling.LANCZOS)
        buffer = BytesIO()
        fitted.save(buffer, format="JPEG", quality=90, optimize=True)
        buffer.seek(0)
        pdf.drawImage(ImageReader(buffer), x, y, width, height, preserveAspectRatio=False, mask="auto")


def _draw_recipe_page(pdf, recipe: dict, image_path: Path | None, page_number: int,
                      photo_right: bool) -> None:
    page_width, page_height = letter
    margin = 0.58 * inch
    usable = page_width - 2 * margin
    photo_w = 3.05 * inch
    photo_h = 3.81 * inch
    gap = 0.24 * inch
    text_w = usable - photo_w - gap
    photo_x = page_width - margin - photo_w if photo_right else margin
    info_x = margin if photo_right else photo_x + photo_w + gap
    top = page_height - 0.55 * inch

    pdf.setFillColor(NAVY)
    pdf.setFont("Helvetica-Bold", 8)
    pdf.drawString(margin, top, "PROJECT PHYSIQUE(TM)  /  LUXURY PHOTO EDITION")
    pdf.setFillColor(GOLD)
    pdf.drawRightString(page_width - margin, top, str(recipe.get("recipe_id") or ""))
    top -= 0.23 * inch
    pdf.setStrokeColor(GOLD)
    pdf.setLineWidth(1.2)
    pdf.line(margin, top, page_width - margin, top)
    # Leave a deliberate editorial gutter between the rule and the headline.
    # The previous offset let tall Helvetica capitals visually touch the rule.
    top -= 0.30 * inch

    title_lines = _wrap_canvas_text(pdf, recipe.get("title"), "Helvetica-Bold", 20, usable)
    top = _draw_lines(pdf, title_lines, margin, top, "Helvetica-Bold", 20, 22, NAVY, 2)
    description = _wrap_canvas_text(pdf, recipe.get("description"), "Helvetica-Oblique", 8, usable)
    top = _draw_lines(pdf, description, margin, top - 2, "Helvetica-Oblique", 8, 10, colors.HexColor("#65727C"), 2)
    block_top = min(top - 0.14 * inch, page_height - 1.65 * inch)
    photo_y = block_top - photo_h
    _draw_photo(pdf, image_path, photo_x, photo_y, photo_w, photo_h)
    pdf.setFillColor(NAVY)
    pdf.setFont("Helvetica-Bold", 7)
    pdf.drawCentredString(photo_x + photo_w / 2, photo_y - 0.13 * inch,
                          f"{recipe.get('recipe_id')}  /  SIGNATURE RECIPE")

    y = block_top
    pdf.setFillColor(CREAM)
    pdf.roundRect(info_x, y - 0.55 * inch, text_w, 0.55 * inch, 5, fill=1, stroke=0)
    meta = [("MEAL", recipe.get("meal") or "-"), ("SERVES", recipe.get("servings", 1)),
            ("INGREDIENTS", len(recipe.get("ingredients", [])))]
    cell = text_w / 3
    for index, (label, value) in enumerate(meta):
        centre = info_x + cell * index + cell / 2
        pdf.setFillColor(GOLD)
        pdf.setFont("Helvetica-Bold", 6.5)
        pdf.drawCentredString(centre, y - 0.17 * inch, label)
        pdf.setFillColor(NAVY)
        pdf.setFont("Helvetica-Bold", 9)
        pdf.drawCentredString(centre, y - 0.37 * inch, str(value).title())
    y -= 0.72 * inch

    nutrition = recipe.get("nutrition") or {}
    pdf.setFillColor(NAVY)
    pdf.setFont("Helvetica-Bold", 11)
    pdf.drawString(info_x, y, "NUTRITION PER SERVING")
    y -= 0.18 * inch
    nutrition_items = [
        ("KCAL", nutrition.get("energy_kcal", "-")),
        ("PROTEIN", f"{nutrition.get('protein_g', '-')} g"),
        ("CARBS", f"{nutrition.get('carbohydrate_g', '-')} g"),
        ("FAT", f"{nutrition.get('fat_g', '-')} g"),
    ]
    card_w = (text_w - 3 * 4) / 4
    for index, (label, value) in enumerate(nutrition_items):
        card_x = info_x + index * (card_w + 4)
        pdf.setFillColor(SAGE)
        pdf.roundRect(card_x, y - 0.48 * inch, card_w, 0.48 * inch, 3, fill=1, stroke=0)
        pdf.setFillColor(GREEN)
        pdf.setFont("Helvetica-Bold", 6)
        pdf.drawCentredString(card_x + card_w / 2, y - 0.14 * inch, label)
        pdf.setFillColor(NAVY)
        pdf.setFont("Helvetica-Bold", 8)
        pdf.drawCentredString(card_x + card_w / 2, y - 0.34 * inch, str(value))
    y -= 0.67 * inch

    panels = [
        ("CHEF'S TIP", recipe.get("chef_tip")),
        ("INGREDIENT SWAP", recipe.get("ingredient_swap")),
        ("MEAL PREP", recipe.get("meal_prep")),
        ("SERVING IDEA", recipe.get("serving_suggestion") or recipe.get("serving")),
    ]
    for label, value in panels:
        if not value:
            continue
        pdf.setFillColor(GOLD if label == "CHEF'S TIP" else NAVY)
        pdf.setFont("Helvetica-Bold", 6.5)
        pdf.drawString(info_x, y, label)
        lines = _wrap_canvas_text(pdf, value, "Helvetica", 7.2, text_w)
        y = _draw_lines(pdf, lines, info_x, y - 0.13 * inch, "Helvetica", 7.2, 8.5,
                        CHARCOAL, 3) - 0.08 * inch
        if y < photo_y + 0.12 * inch:
            break

    lower_top = photo_y - 0.38 * inch
    lower_bottom = 0.62 * inch
    lower_height = lower_top - lower_bottom
    col_gap = 0.28 * inch
    col_w = (usable - col_gap) / 2
    left_x = margin
    right_x = margin + col_w + col_gap
    pdf.setFillColor(CREAM)
    pdf.roundRect(left_x, lower_bottom, col_w, lower_height, 6, fill=1, stroke=0)
    pdf.setFillColor(PALE_BLUE)
    pdf.roundRect(right_x, lower_bottom, col_w, lower_height, 6, fill=1, stroke=0)
    pdf.setFillColor(NAVY)
    pdf.setFont("Helvetica-Bold", 11)
    pdf.drawString(left_x + 0.13 * inch, lower_top - 0.22 * inch, "INGREDIENTS")
    pdf.drawString(right_x + 0.13 * inch, lower_top - 0.22 * inch, "METHOD")
    ing_y = lower_top - 0.42 * inch
    for item in recipe.get("ingredients", []):
        quantity = f"{item['quantity']:g} {item['unit']}"
        line = f"{quantity}  {item['name']}"
        wrapped = _wrap_canvas_text(pdf, line, "Helvetica", 7.2, col_w - 0.26 * inch)
        if ing_y - len(wrapped) * 8 < lower_bottom + 0.08 * inch:
            break
        ing_y = _draw_lines(pdf, wrapped, left_x + 0.13 * inch, ing_y, "Helvetica", 7.2, 8.2,
                            CHARCOAL) - 1.5
    method_y = lower_top - 0.42 * inch
    for step in recipe.get("method", []):
        line = f"{step['number']}. {step['text']}"
        wrapped = _wrap_canvas_text(pdf, line, "Helvetica", 7.1, col_w - 0.26 * inch)
        if method_y - len(wrapped) * 8 < lower_bottom + 0.08 * inch:
            break
        method_y = _draw_lines(pdf, wrapped, right_x + 0.13 * inch, method_y, "Helvetica", 7.1,
                               8.1, CHARCOAL) - 3
    pdf.setFillColor(colors.HexColor("#66727C"))
    pdf.setFont("Helvetica", 7)
    pdf.drawCentredString(page_width / 2, 0.28 * inch,
                          f"PROJECT PHYSIQUE(TM)  /  30 DAYS FAT LOSS  /  {page_number}")
    pdf.showPage()


def _build_luxury_pdf(database: Path, output: Path, coverage_report_path=None) -> Path:
    project_root = database.parent.parent
    recipes = LayoutRecipeRepository(database).list_recipes()
    if not recipes:
        raise ValueError("No recipes found for PDF export")
    output.parent.mkdir(parents=True, exist_ok=True)
    pdf = canvas.Canvas(str(output), pagesize=letter, pageCompression=1)
    pdf.setTitle("Project Physique - 30 Days Fat Loss - Luxury Photo Edition")
    pdf.setAuthor("Project Physique")
    _draw_cover(pdf)
    _draw_collection_intro(pdf)
    found_images: list[dict[str, str]] = []
    missing_images: list[str] = []
    for index, recipe in enumerate(recipes):
        image_path = _recipe_image(project_root, recipe)
        if image_path:
            found_images.append({"recipe_id": recipe["recipe_id"], "path": str(image_path)})
        else:
            missing_images.append(recipe["recipe_id"])
        _draw_recipe_page(pdf, recipe, image_path, index + 1, photo_right=bool(index % 2))
    pdf.save()
    if coverage_report_path:
        report = Path(coverage_report_path).expanduser().resolve()
        report.parent.mkdir(parents=True, exist_ok=True)
        report.write_text(json.dumps({
            "schema_version": 2,
            "layout": "luxury_editorial_photo",
            "total_recipes": len(recipes),
            "images_found": len(found_images),
            "images_missing": len(missing_images),
            "found": found_images,
            "missing_recipe_ids": missing_images,
        }, indent=2) + "\n", encoding="utf-8")
    return output


def build_publishing_pdf(
    database_path: str | Path,
    output_path: str | Path,
    *,
    coverage_report_path: str | Path | None = None,
) -> Path:
    """Render all persisted recipes to a portable US Letter publishing PDF."""
    database = Path(database_path).expanduser().resolve()
    output = Path(output_path).expanduser().resolve()
    return _build_luxury_pdf(database, output, coverage_report_path)
    project_root = database.parent.parent
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
    hero_caption = ParagraphStyle(
        "HeroCaption", parent=small, alignment=TA_CENTER, textColor=colors.HexColor("#667266"),
        spaceBefore=2,
    )
    hero_placeholder = ParagraphStyle(
        "HeroPlaceholder", parent=body, alignment=TA_CENTER, textColor=GREEN,
        fontSize=10, leading=16,
    )
    hero_styles = {"hero_caption": hero_caption, "hero_placeholder": hero_placeholder}

    document = SimpleDocTemplate(
        str(output), pagesize=letter, rightMargin=0.62 * inch, leftMargin=0.72 * inch,
        topMargin=0.55 * inch, bottomMargin=0.55 * inch,
        title="Project Physique — 30 Days Fat Loss", author="Project Physique",
    )
    story = []
    found_images: list[dict[str, str]] = []
    missing_images: list[str] = []
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

        image_path = _recipe_image(project_root, recipe)
        if image_path:
            found_images.append({"recipe_id": recipe["recipe_id"], "path": str(image_path)})
        else:
            missing_images.append(recipe["recipe_id"])
        story.extend([Spacer(1, 8), _hero_block(recipe, image_path, hero_styles)])

    document.build(story, onFirstPage=_footer, onLaterPages=_footer)
    if coverage_report_path:
        report = Path(coverage_report_path).expanduser().resolve()
        report.parent.mkdir(parents=True, exist_ok=True)
        report.write_text(json.dumps({
            "schema_version": 1,
            "total_recipes": len(recipes),
            "images_found": len(found_images),
            "images_missing": len(missing_images),
            "found": found_images,
            "missing_recipe_ids": missing_images,
        }, indent=2) + "\n", encoding="utf-8")
    return output
