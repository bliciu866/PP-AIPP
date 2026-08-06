"""Dependency-free-from-office PDF rendering for publishing exports."""
from __future__ import annotations

import json
import re
from collections import defaultdict
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
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
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


def _register_publishing_fonts() -> None:
    """Embed deterministic fonts so KDP and desktop viewers render identically."""
    font_dir = Path(__file__).resolve().parent / "resources" / "fonts"
    regular = font_dir / "DejaVuSans.ttf"
    bold = font_dir / "DejaVuSans-Bold.ttf"
    if regular.is_file() and bold.is_file():
        pdfmetrics.registerFont(TTFont("Helvetica", regular))
        pdfmetrics.registerFont(TTFont("Helvetica-Bold", bold))
        pdfmetrics.registerFont(TTFont("Helvetica-Oblique", regular))


_register_publishing_fonts()


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
    pdf.setFont("Helvetica-Bold", 42)
    pdf.drawString(1.05 * inch, height - 2.35 * inch, "30 DAYS")
    pdf.drawString(1.05 * inch, height - 2.92 * inch, "FAT LOSS")
    pdf.setFillColor(GOLD)
    pdf.setFont("Helvetica-Bold", 15)
    pdf.drawString(1.06 * inch, height - 3.38 * inch, "PREMIUM NUTRITION PROGRAMME")
    pdf.setFillColor(colors.white)
    pdf.setFont("Helvetica", 11)
    pdf.drawString(1.06 * inch, height - 4.08 * inch, "30-day meal plan  /  80 nutrition-verified recipes")
    pdf.drawString(1.06 * inch, height - 4.34 * inch, "Shopping lists, progress tools and real UK ingredients")
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


def _draw_publishing_pages(pdf) -> None:
    """Add consumer-facing navigation, legal and brand pages before the programme."""
    _draw_text_page(pdf, "Before you begin", "Important Information", [
        ("Copyright", "Copyright © 2026 Project Physique™. All rights reserved. This publication may not be reproduced, distributed or transmitted without prior written permission, except for brief quotations permitted by law."),
        ("Health and nutrition disclaimer", "This programme provides general educational information and is not individual medical or dietetic advice. Nutritional needs vary. Consult an appropriately qualified professional before material dietary change if you are pregnant, under 18, managing a medical condition, taking prescribed medication or have a history of disordered eating."),
        ("Food safety and allergens", "Allergen notes are screening aids only. Always check current packaging and avoid cross-contamination according to your needs. Chill cooked food promptly, keep the refrigerator at 5°C or below and cook animal products thoroughly."),
    ])
    _draw_text_page(pdf, "Navigate the programme", "Contents", [
        ("Start strong · pages 6–8", "30-Day Success Guide, Nutrition Basics and the UK Shopping System."),
        ("Plan and shop · pages 9–26", "Five weekly meal-plan pages, five consolidated shopping lists and four practical recipe indexes."),
        ("Cook · pages 27–106", "Eighty photo-led recipes with complete macros, ingredients, method, meal prep and recipe-specific editorial guidance."),
        ("Track and continue · pages 107–108", "30-Day Progress Tracker and Frequently Asked Questions."),
    ])
    _draw_text_page(pdf, "Made for consistency", "About Project Physique™", [
        ("Our purpose", "Project Physique™ creates practical nutrition systems that turn a goal into repeatable daily action. This programme is designed around familiar UK ingredients, clear portions and meals people can cook again."),
        ("How to use this book", "Follow the suggested 30-day rhythm or swap within the same meal category. Use the stated serving as your baseline, keep calorie-dense ingredients measured and repeat the recipes that make consistency easier."),
        ("Production standard", "Recipe nutrition is aligned to the McCance and Widdowson Composition of Foods Integrated Dataset 2021. Documented proxy decisions remain in the internal Nutrition Lock record rather than interrupting the reader experience."),
    ])


def _meta(recipe: dict, key: str, default=""):
    value = recipe.get(key)
    if value not in (None, ""):
        return value
    return (recipe.get("metadata") or {}).get(key, default)


def _recipe_traits(recipe: dict) -> dict:
    """Return conservative, reproducible production metadata for legacy masters."""
    ingredients = " ".join(str(i.get("name", "")).lower() for i in recipe.get("ingredients", []))
    method = " ".join(str(s.get("text", "")) for s in recipe.get("method", []))
    minute_values = [int(v) for v in re.findall(
        r"(\d+)\s*(?:-|–|to)?\s*(?:\d+\s*)?minutes?", method, re.IGNORECASE
    )]
    cook = max(minute_values, default=15)
    prep = 10 if len(recipe.get("ingredients", [])) <= 7 else 15
    difficulty = "Easy" if len(recipe.get("method", [])) <= 4 else "Moderate"
    vegetarian = not any(word in ingredients for word in (
        "chicken", "turkey", "beef", "pork", "salmon", "cod", "haddock", "tuna",
        "prawn", "fish", "lamb", "ham", "bacon", "mince",
    ))
    title = str(recipe.get("title", "")).lower()
    freezer = any(word in title for word in ("curry", "stew", "soup", "bake", "meatball", "chilli"))
    allergens: list[str] = []
    groups = [
        ("Milk", ("milk", "quark", "cheese", "yogurt", "yoghurt", "skyr", "cream")),
        ("Egg", ("egg",)), ("Fish", ("salmon", "cod", "haddock", "tuna", "fish")),
        ("Gluten", ("bread", "pasta", "couscous", "oats", "wrap", "barley")),
        ("Peanuts / nuts", ("peanut", "almond", "walnut", "pecan", "pistachio", "cashew")),
        ("Mustard", ("mustard",)), ("Soya", ("soy", "tofu")), ("Sesame", ("sesame",)),
        ("Crustaceans", ("prawn", "shrimp")),
    ]
    for label, terms in groups:
        if any(term in ingredients for term in terms):
            allergens.append(label)
    return {
        "prep": int(_meta(recipe, "prep_time_minutes", prep)),
        "cook": int(_meta(recipe, "cook_time_minutes", cook)),
        "difficulty": _meta(recipe, "difficulty", difficulty),
        "vegetarian": bool(_meta(recipe, "vegetarian_option", vegetarian)),
        "freezer": bool(_meta(recipe, "freezer_friendly", freezer)),
        "allergens": _meta(recipe, "allergen_note", ", ".join(allergens) or "No major allergens identified; check labels"),
    }


def _contains(ingredients: str, *terms: str) -> bool:
    return any(term in ingredients for term in terms)


def _editorial_content(recipe: dict) -> dict[str, str]:
    """Create concise recipe-aware guidance when a legacy Gold Master has no v5 cards."""
    title = str(recipe.get("title") or "this recipe")
    meal = str(recipe.get("meal") or "meal").lower()
    ingredient_names = [str(i.get("name", "")).strip() for i in recipe.get("ingredients", [])]
    ingredients = " ".join(name.lower() for name in ingredient_names)
    minor = ("salt", "pepper", "oil", "garlic", "cinnamon", "herb", "juice", "zest")
    anchors = [name for name in ingredient_names if not any(word in name.lower() for word in minor)]
    focus = " and ".join(anchors[:2]) if anchors else title

    if _contains(ingredients, "salmon", "cod", "haddock", "tuna", "mackerel", "prawn"):
        chef = "Pat the seafood dry before seasoning so it colours cleanly instead of steaming."
        mistake = "Overcooking seafood; remove it as soon as it is opaque and flakes easily."
        swap = "Use another firm fish or seafood option in the same measured quantity."
    elif _contains(ingredients, "chicken", "turkey", "beef", "pork"):
        chef = "Cut the protein into even pieces and let the pan reheat before the next batch."
        mistake = "Crowding the pan, which traps moisture and prevents proper browning."
        swap = "Use lean turkey, chicken or a plant-based mince in the same measured quantity."
    elif _contains(ingredients, "tofu", "lentil", "chickpea", "bean", "aubergine"):
        chef = "Build flavour in layers: brown the base ingredients before adding liquid or sauce."
        mistake = "Adding everything at once, which leaves the vegetables soft and the flavour flat."
        swap = "Exchange lentils, chickpeas, beans or firm tofu gram for gram where practical."
    elif _contains(ingredients, "oats", "quark", "cottage cheese", "yogurt", "yoghurt"):
        chef = "Rest the mixture before serving so the grains hydrate and the texture becomes creamy."
        mistake = "Guessing the toppings; weigh nuts, seeds and spreads because portions add up quickly."
        swap = "Swap quark, skyr or Greek-style yogurt by weight and recheck the nutrition label."
    elif _contains(ingredients, "egg"):
        chef = "Use moderate heat and stop cooking while the eggs still look slightly glossy."
        mistake = "Using high heat, which makes eggs firm before the centre cooks evenly."
        swap = "Replace part of the egg with measured egg whites for a lighter protein option."
    else:
        chef = "Prepare and measure every ingredient before heating the pan for a calm, even cook."
        mistake = "Changing several quantities while cooking and losing the stated nutrition balance."
        swap = "Use a similar lean protein or wholegrain in the same measured cooked state."

    if meal == "breakfast":
        serving = f"Serve {title} with water, tea or coffee and keep extra toppings measured."
    elif _contains(ingredients, "curry", "stew", "tray", "rice", "pasta", "couscous"):
        serving = "Finish with fresh herbs or lemon and add a generous side of non-starchy vegetables."
    else:
        serving = "Plate with crisp seasonal vegetables and a squeeze of lemon for freshness."

    return {
        "chef_tip": str(recipe.get("chef_tip") or f"With {focus}, {chef[0].lower()}{chef[1:]}"),
        "common_mistake": str(_meta(recipe, "common_mistake") or f"For {focus}, avoid {mistake[0].lower()}{mistake[1:]}"),
        "ingredient_swap": str(recipe.get("ingredient_swap") or f"Swap option for {focus}: {swap[0].lower()}{swap[1:]}"),
        "meal_prep": str(recipe.get("meal_prep") or "Prepare components ahead, chill promptly and assemble when needed."),
        "serving_suggestion": str(_meta(recipe, "serving_suggestion") or serving),
    }


def _page_heading(pdf, eyebrow: str, title: str, subtitle: str = "") -> float:
    width, height = letter
    pdf.setFillColor(CREAM)
    pdf.rect(0, 0, width, height, fill=1, stroke=0)
    pdf.setFillColor(GOLD)
    pdf.setFont("Helvetica-Bold", 9)
    pdf.drawCentredString(width / 2, height - 0.8 * inch, eyebrow.upper())
    pdf.setFillColor(NAVY)
    y = height - 1.35 * inch
    for line in _wrap_canvas_text(pdf, title, "Helvetica-Bold", 24, width - 1.5 * inch):
        pdf.setFont("Helvetica-Bold", 24)
        pdf.drawCentredString(width / 2, y, line)
        y -= 0.36 * inch
    if subtitle:
        y -= 0.08 * inch
        for line in _wrap_canvas_text(pdf, subtitle, "Helvetica", 10, width - 1.6 * inch):
            pdf.setFillColor(CHARCOAL)
            pdf.setFont("Helvetica", 10)
            pdf.drawCentredString(width / 2, y, line)
            y -= 0.18 * inch
    return y - 0.25 * inch


def _draw_text_page(pdf, eyebrow: str, title: str, sections: list[tuple[str, str]]) -> None:
    width, _ = letter
    y = _page_heading(pdf, eyebrow, title)
    x = 0.8 * inch
    content_w = width - 1.6 * inch
    for heading, body in sections:
        pdf.setFillColor(NAVY)
        pdf.setFont("Helvetica-Bold", 13)
        pdf.drawString(x, y, heading)
        y -= 0.22 * inch
        lines = _wrap_canvas_text(pdf, body, "Helvetica", 9.2, content_w)
        y = _draw_lines(pdf, lines, x, y, "Helvetica", 9.2, 13, CHARCOAL) - 0.18 * inch
    pdf.setFillColor(GOLD)
    pdf.rect(1.7 * inch, 0.55 * inch, width - 3.4 * inch, 0.03 * inch, fill=1, stroke=0)
    pdf.showPage()


def _draw_programme_pages(pdf) -> None:
    _draw_text_page(pdf, "Start here", "Your 30-Day Success Guide", [
        ("The simple system", "Choose three planned meals each day, repeat favourites, shop from a written list and review the trend once a week—not after every meal."),
        ("Five success rules", "Plan tomorrow before today ends. Measure calorie-dense ingredients. Keep a protein-led emergency meal ready. Compare weekly averages under similar conditions. If progress stalls for two weeks, review portions and adherence before making a large change."),
        ("Weekly rhythm", "Friday: choose recipes and check supplies. Saturday: shop. Sunday: batch-cook one protein, one starch and one tray of vegetables. Midweek: top up fresh produce. Weekend: record progress and one lesson."),
    ])
    _draw_text_page(pdf, "The foundations", "Nutrition Basics", [
        ("Energy and protein", "Fat loss requires a sustained energy deficit, while protein supports muscle retention and makes meals more satisfying. Nutrition values are per stated serving."),
        ("Fibre, carbohydrate and fat", "Increase fibre gradually and drink enough fluid. Carbohydrate is useful fuel; portion it to the recipe and your needs. Measure oils, dressings, nuts and seeds."),
        ("Safety", "This book provides general education, not individual medical advice. Speak with a GP or registered dietitian if pregnant, under 18, managing a medical condition, taking appetite or glucose medication, or with a history of disordered eating."),
    ])
    _draw_text_page(pdf, "Shop smarter", "UK Shopping System", [
        ("Use any supermarket", "The system is supermarket-neutral and works at Tesco, Aldi, Lidl, Asda, Sainsbury’s, Morrisons and online grocers. Compare the nutrition panel, not the brand name."),
        ("Shop in this order", "Produce; protein; carbohydrates; flavour builders; frozen and cupboard backup. Check your freezer, fridge and cupboards before leaving."),
        ("Reduce waste", "Plan overlapping ingredients, freeze spare portions promptly, use delicate produce first and keep one flexible leftovers meal each week."),
    ])


def _schedule(recipes: list[dict]) -> list[tuple[int, dict, dict, dict]]:
    groups = defaultdict(list)
    for recipe in recipes:
        groups[str(recipe.get("meal") or "Dinner").lower()].append(recipe)
    breakfast = groups["breakfast"] or recipes
    lunch = groups["lunch"] or groups["dinner"] or recipes
    dinner = groups["dinner"] or recipes
    return [(day, breakfast[(day - 1) % len(breakfast)], lunch[(day * 2 - 2) % len(lunch)], dinner[(day * 3 - 3) % len(dinner)]) for day in range(1, 31)]


def _draw_plan_pages(pdf, schedule) -> None:
    for week, start in enumerate(range(0, 30, 7), 1):
        days = schedule[start:start + 7]
        y = _page_heading(pdf, "Your programme", f"Week {week} · Day {days[0][0]}–{days[-1][0]}", "A complete daily rhythm; swap within the same meal category when useful.")
        x = 0.55 * inch
        widths = [0.45 * inch, 2.0 * inch, 2.0 * inch, 2.0 * inch]
        rows = [["DAY", "BREAKFAST", "LUNCH", "DINNER"]]
        for day, breakfast, lunch, dinner in days:
            rows.append([str(day), f"{breakfast['recipe_id']}\n{breakfast['title']}", f"{lunch['recipe_id']}\n{lunch['title']}", f"{dinner['recipe_id']}\n{dinner['title']}"])
        table = Table(rows, colWidths=widths, rowHeights=[0.32 * inch] + [0.7 * inch] * len(days))
        table.setStyle(TableStyle([("BACKGROUND", (0, 0), (-1, 0), NAVY), ("TEXTCOLOR", (0, 0), (-1, 0), colors.white), ("BACKGROUND", (0, 1), (-1, -1), colors.white), ("GRID", (0, 0), (-1, -1), 0.35, colors.HexColor("#D8CBAE")), ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"), ("FONTNAME", (0, 1), (0, -1), "Helvetica-Bold"), ("FONTSIZE", (0, 0), (-1, -1), 7), ("LEADING", (0, 0), (-1, -1), 8.5), ("VALIGN", (0, 0), (-1, -1), "MIDDLE"), ("LEFTPADDING", (0, 0), (-1, -1), 5)]))
        table.wrapOn(pdf, sum(widths), 6 * inch)
        table.drawOn(pdf, x, y - (0.32 + 0.7 * len(days)) * inch)
        pdf.showPage()


def _draw_shopping_pages(pdf, schedule) -> None:
    for week, start in enumerate(range(0, 30, 7), 1):
        selected = schedule[start:start + 7]
        items: dict[str, tuple[float, str]] = {}
        for _, *meals in selected:
            for recipe in meals:
                for item in recipe.get("ingredients", []):
                    key = str(item["name"]).strip()
                    qty, unit = float(item.get("quantity", 0)), str(item.get("unit", ""))
                    previous = items.get(key)
                    items[key] = ((previous[0] + qty) if previous and previous[1] == unit else qty, unit)
        y = _page_heading(pdf, "Weekly shopping list", f"Week {week}", "Quantities follow the scheduled single servings; scale for your household and planned leftovers.")
        columns = [[], []]
        for index, (name, (qty, unit)) in enumerate(sorted(items.items())):
            columns[index % 2].append(f"□  {qty:g} {unit}  {name}")
        for col, lines in enumerate(columns):
            x = (0.65 + col * 3.85) * inch
            yy = y
            for line in lines[:26]:
                yy = _draw_lines(pdf, _wrap_canvas_text(pdf, line, "Helvetica", 8.2, 3.25 * inch), x, yy, "Helvetica", 8.2, 10.2, CHARCOAL) - 2
        pdf.showPage()


def _draw_indexes(pdf, recipes: list[dict]) -> None:
    indexes = [
        ("Recipe Index · Meal", lambda r: (str(r.get("meal")), r["recipe_id"]), lambda r: f"{r['recipe_id']}  {r['meal']}  ·  {r['title']}"),
        ("Recipe Index · Calories", lambda r: ((r.get("nutrition") or {}).get("energy_kcal", 0), r["recipe_id"]), lambda r: f"{r['recipe_id']}  {(r.get('nutrition') or {}).get('energy_kcal', 0):g} kcal  ·  {r['title']}"),
        ("Recipe Index · Protein", lambda r: (-((r.get("nutrition") or {}).get("protein_g", 0)), r["recipe_id"]), lambda r: f"{r['recipe_id']}  {(r.get('nutrition') or {}).get('protein_g', 0):g} g protein  ·  {r['title']}"),
        ("Recipe Index · Total Time", lambda r: (_recipe_traits(r)["prep"] + _recipe_traits(r)["cook"], r["recipe_id"]), lambda r: f"{r['recipe_id']}  {_recipe_traits(r)['prep'] + _recipe_traits(r)['cook']} min  ·  {r['title']}"),
    ]
    for title, key, label in indexes:
        ordered = sorted(recipes, key=key)
        for chunk_index in range(0, len(ordered), 40):
            chunk = ordered[chunk_index:chunk_index + 40]
            y = _page_heading(pdf, "Find your fit", title, f"Part {chunk_index // 40 + 1} of 2")
            for i, recipe in enumerate(chunk):
                x = 0.65 * inch if i < 20 else 4.15 * inch
                yy = y - (i % 20) * 0.27 * inch
                pdf.setFillColor(CHARCOAL)
                pdf.setFont("Helvetica", 7.6)
                pdf.drawString(x, yy, label(recipe)[:62])
            pdf.showPage()


def _draw_tracker_and_faq(pdf) -> None:
    y = _page_heading(pdf, "Track the trend", "30-Day Progress Tracker", "Use weekly averages and simple adherence notes—not single-day noise.")
    rows = [["DAY", "WEIGHT", "WAIST", "ENERGY", "SLEEP", "STEPS", "MEALS ✓"]] + [[str(i), "", "", "", "", "", ""] for i in range(1, 31)]
    table = Table(rows, colWidths=[0.45 * inch] + [0.95 * inch] * 6, rowHeights=[0.25 * inch] + [0.16 * inch] * 30)
    table.setStyle(TableStyle([("BACKGROUND", (0, 0), (-1, 0), NAVY), ("TEXTCOLOR", (0, 0), (-1, 0), colors.white), ("GRID", (0, 0), (-1, -1), 0.3, colors.HexColor("#C9C1B1")), ("FONTSIZE", (0, 0), (-1, -1), 6.5), ("ALIGN", (0, 0), (-1, -1), "CENTER")]))
    table.wrapOn(pdf, 7 * inch, 6 * inch)
    table.drawOn(pdf, 0.65 * inch, y - 5.05 * inch)
    pdf.showPage()
    _draw_text_page(pdf, "Quick answers", "Frequently Asked Questions", [
        ("Do I need to eat every recipe?", "No. The plan is a structured menu, not a rulebook. Swap within breakfast, lunch or dinner and keep portions consistent."),
        ("What if hunger is high?", "Check sleep, hydration, meal timing and fibre. Add non-starchy vegetables or discuss individual needs with a qualified professional."),
        ("Can I batch cook?", "Yes. Follow each Meal Prep card, cool cooked food promptly, refrigerate at 5°C or below and reheat only as directed."),
        ("What if weight stalls?", "Compare weekly averages for at least two consistent weeks, then review adherence and portions before changing the plan."),
        ("How do swaps affect nutrition?", "Ingredient swaps are practical alternatives, not nutrition-equivalent guarantees. Recalculate nutrition when accuracy matters."),
        ("How should allergens be used?", "Allergen notes are screening aids only. Always check packaging and avoid cross-contamination according to your needs."),
    ])


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
    traits = _recipe_traits(recipe)
    meta = [("MEAL", recipe.get("meal") or "-"), ("TOTAL TIME", f"{traits['prep'] + traits['cook']} min"),
            ("DIFFICULTY", traits["difficulty"])]
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
        ("FIBRE", f"{nutrition.get('fibre_g', '-')} g"),
    ]
    card_w = (text_w - 4 * 3) / 5
    for index, (label, value) in enumerate(nutrition_items):
        card_x = info_x + index * (card_w + 4)
        pdf.setFillColor(SAGE)
        pdf.roundRect(card_x, y - 0.48 * inch, card_w, 0.48 * inch, 3, fill=1, stroke=0)
        pdf.setFillColor(GREEN)
        pdf.setFont("Helvetica-Bold", 6)
        pdf.drawCentredString(card_x + card_w / 2, y - 0.14 * inch, label)
        pdf.setFillColor(NAVY)
        pdf.setFont("Helvetica-Bold", 7.4)
        pdf.drawCentredString(card_x + card_w / 2, y - 0.34 * inch, str(value))
    y -= 0.67 * inch

    editorial = _editorial_content(recipe)
    panels = [
        ("CHEF'S TIP", editorial["chef_tip"]),
        ("COMMON MISTAKE", editorial["common_mistake"]),
        ("INGREDIENT SWAP", editorial["ingredient_swap"]),
        ("MEAL PREP", editorial["meal_prep"]),
        ("SERVING SUGGESTION", editorial["serving_suggestion"]),
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

    badge_y = photo_y + 0.08 * inch
    badges = [
        "FREEZER-FRIENDLY" if traits["freezer"] else "BEST FRESH",
        "VEGETARIAN" if traits["vegetarian"] else "VEGETARIAN SWAP AVAILABLE",
    ]
    pdf.setFont("Helvetica-Bold", 5.8)
    pdf.setFillColor(GREEN)
    pdf.drawString(info_x, badge_y, "  •  ".join(badges))
    allergen_lines = _wrap_canvas_text(pdf, f"ALLERGEN NOTE: {traits['allergens']}", "Helvetica", 5.8, text_w)
    _draw_lines(pdf, allergen_lines, info_x, badge_y - 0.12 * inch, "Helvetica", 5.8, 7, CHARCOAL, 2)

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
    _draw_publishing_pages(pdf)
    _draw_programme_pages(pdf)
    schedule = _schedule(recipes)
    _draw_plan_pages(pdf, schedule)
    _draw_shopping_pages(pdf, schedule)
    _draw_indexes(pdf, recipes)
    found_images: list[dict[str, str]] = []
    missing_images: list[str] = []
    for index, recipe in enumerate(recipes):
        image_path = _recipe_image(project_root, recipe)
        if image_path:
            found_images.append({"recipe_id": recipe["recipe_id"], "path": str(image_path)})
        else:
            missing_images.append(recipe["recipe_id"])
        _draw_recipe_page(pdf, recipe, image_path, index + 1, photo_right=bool(index % 2))
    _draw_tracker_and_faq(pdf)
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
