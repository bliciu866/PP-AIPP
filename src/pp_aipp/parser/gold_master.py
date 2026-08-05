from __future__ import annotations

import re
from collections.abc import Iterator
from dataclasses import asdict, dataclass, field
from pathlib import Path

from docx import Document
from docx.document import Document as DocxDocument
from docx.oxml.table import CT_Tbl
from docx.oxml.text.paragraph import CT_P
from docx.table import Table
from docx.text.paragraph import Paragraph

from ..domain import (
    Ingredient,
    MethodStep,
    Nutrition,
    Provenance,
    QARecord,
    QASeverity,
    Recipe,
    RecipeStatus,
)

RECIPE_ID_RE = re.compile(r"^PP-R(\d{3})$")
NUMBER_RE = re.compile(r"-?\d+(?:[.,]\d+)?")
QUANTITY_RE = re.compile(
    r"^\s*(-?\d+(?:[.,]\d+)?)\s*(g|ml|kg|l|tbsp|tsp|piece|pieces|whole)?\s*$",
    re.IGNORECASE,
)


@dataclass(slots=True)
class ParseIssue:
    severity: str
    code: str
    message: str
    recipe_id: str | None = None


@dataclass(slots=True)
class ParseResult:
    source: str
    recipes: list[Recipe]
    issues: list[ParseIssue] = field(default_factory=list)
    metadata: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "source": self.source,
            "recipes": [recipe_to_dict(recipe) for recipe in self.recipes],
            "issues": [asdict(issue) for issue in self.issues],
            "metadata": self.metadata,
            "summary": {
                "recipe_count": len(self.recipes),
                "ingredient_count": sum(len(recipe.ingredients) for recipe in self.recipes),
                "method_step_count": sum(len(recipe.method) for recipe in self.recipes),
                "errors": sum(issue.severity == "ERROR" for issue in self.issues),
                "warnings": sum(issue.severity == "WARNING" for issue in self.issues),
            },
        }


def recipe_to_dict(recipe: Recipe) -> dict:
    value = asdict(recipe)
    value["status"] = recipe.status.value
    value["provenance"] = recipe.provenance.value
    for item in value["ingredients"]:
        item["provenance"] = str(item["provenance"])
    for step in value["method"]:
        step["provenance"] = str(step["provenance"])
    if value["nutrition"]:
        value["nutrition"]["provenance"] = str(value["nutrition"]["provenance"])
    for record in value["qa_records"]:
        record["severity"] = str(record["severity"])
        record["provenance"] = str(record["provenance"])
    return value


def clean(text: str) -> str:
    return " ".join((text or "").replace("\u00a0", " ").split()).strip()


def iter_blocks(document: DocxDocument) -> Iterator[Paragraph | Table]:
    for child in document.element.body.iterchildren():
        if isinstance(child, CT_P):
            yield Paragraph(child, document)
        elif isinstance(child, CT_Tbl):
            yield Table(child, document)


def rows(table: Table) -> list[list[str]]:
    return [[clean(cell.text) for cell in row.cells] for row in table.rows]


def number(text: str) -> float | None:
    match = NUMBER_RE.search((text or "").replace(",", "."))
    return float(match.group(0)) if match else None


class GoldMasterParser:
    """Parse a Project Physique Gold Master DOCX into PP-AIPP domain objects."""

    def parse(self, path: str | Path, *, book_id: str, strict_collection: bool = True) -> ParseResult:
        source = Path(path).expanduser().resolve()
        if source.suffix.lower() != ".docx" or not source.is_file():
            raise ValueError(f"An existing DOCX file is required: {source}")

        document = Document(source)
        blocks = list(iter_blocks(document))
        all_starts = [
            (position, clean(block.text))
            for position, block in enumerate(blocks)
            if isinstance(block, Paragraph) and RECIPE_ID_RE.fullmatch(clean(block.text))
        ]
        recipe_starts: list[tuple[int, str]] = []
        for index, (position, recipe_id) in enumerate(all_starts):
            end = all_starts[index + 1][0] if index + 1 < len(all_starts) else len(blocks)
            window = blocks[position + 1 : end]
            if self._has_recipe_signature(window[:14]):
                recipe_starts.append((position, recipe_id))

        recipes: list[Recipe] = []
        issues: list[ParseIssue] = []
        for index, (position, recipe_id) in enumerate(recipe_starts):
            end = recipe_starts[index + 1][0] if index + 1 < len(recipe_starts) else len(blocks)
            recipe, recipe_issues = self._parse_recipe(
                book_id, recipe_id, blocks[position + 1 : end]
            )
            recipes.append(recipe)
            issues.extend(recipe_issues)

        if strict_collection:
            issues.extend(self._validate_collection(recipes))
        return ParseResult(
            source=str(source),
            recipes=recipes,
            issues=issues,
            metadata={
                "parser": "PP-AIPP GoldMasterParser",
                "parser_version": "3.0.0-alpha.4",
                "block_count": len(blocks),
                "recipe_candidates": len(all_starts),
                "recipe_sections": len(recipe_starts),
            },
        )

    @staticmethod
    def _has_recipe_signature(blocks: list[Paragraph | Table]) -> bool:
        for block in blocks:
            if isinstance(block, Paragraph) and clean(block.text) in {
                "Ingredients",
                "Nutrition per serving",
            }:
                return True
            if isinstance(block, Table):
                flat = {cell for row in rows(block) for cell in row}
                if {"Meal", "Servings", "Status"} & flat:
                    return True
                if "Ingredient" in flat and "Quantity" in flat:
                    return True
        return False

    def _parse_recipe(
        self, book_id: str, recipe_id: str, blocks: list[Paragraph | Table]
    ) -> tuple[Recipe, list[ParseIssue]]:
        recipe = Recipe(book_id=book_id, recipe_id=recipe_id, title="", meal="", servings=1)
        issues: list[ParseIssue] = []
        section = "header"
        qa_fragments: list[str] = []

        for block in blocks:
            if isinstance(block, Table):
                section = self._consume_table(recipe, rows(block), section)
                continue
            text = clean(block.text)
            if not text:
                continue
            lower = text.lower()
            heading, inline = self._section_heading(text)
            if heading == "ingredients":
                section = "ingredients"
                continue
            if heading == "method":
                section = "method"
                if inline:
                    self._append_method(recipe, inline)
                continue
            if heading == "meal_prep":
                section = "meal_prep"
                if inline:
                    recipe.meal_prep = f"{recipe.meal_prep} {inline}".strip()
                continue
            if lower in {"nutrition per serving", "nutrition"}:
                section = "nutrition"
                continue
            if lower.startswith("qa note:"):
                section = "qa"
                qa_fragments.append(text.split(":", 1)[1].strip())
                continue
            if lower.startswith("hero photo placeholder"):
                continue

            if section == "header":
                if not recipe.title and not self._is_badge_line(text):
                    recipe.title = text
                elif self._is_badge_line(text):
                    recipe.badges = self._parse_badges(text)
                elif not recipe.description and self._looks_like_description(text):
                    recipe.description = text
            elif section == "method":
                self._append_method(recipe, text)
            elif section == "meal_prep":
                recipe.meal_prep = f"{recipe.meal_prep} {text}".strip()
            elif section == "qa":
                qa_fragments.append(text)

        qa_note = " ".join(qa_fragments).strip()
        conditional = qa_note.upper().startswith("CONDITIONAL PASS")
        recipe.status = RecipeStatus.CONDITIONAL_PASS if conditional else RecipeStatus.NUTRITION_LOCKED
        if qa_note:
            recipe.qa_records.append(
                QARecord(
                    category="NUTRITION_LOCK",
                    message=qa_note,
                    severity=QASeverity.WARNING if conditional else QASeverity.INFO,
                    status="DOCUMENTED",
                )
            )

        if not recipe.meal or recipe.meal == "—":
            recipe.meal = self._infer_meal(recipe)
            issues.append(ParseIssue("WARNING", "MEAL_INFERRED", recipe.meal, recipe_id))
        if not recipe.title:
            issues.append(ParseIssue("ERROR", "TITLE_MISSING", "Recipe title missing", recipe_id))
        if not recipe.ingredients:
            issues.append(ParseIssue("ERROR", "INGREDIENTS_MISSING", "No ingredients parsed", recipe_id))
        if recipe.nutrition is None:
            issues.append(ParseIssue("ERROR", "NUTRITION_MISSING", "Nutrition table missing", recipe_id))
        if not recipe.method:
            issues.append(ParseIssue("WARNING", "METHOD_MISSING", "No method in source", recipe_id))
        if not qa_note:
            issues.append(ParseIssue("WARNING", "QA_MISSING", "QA note missing", recipe_id))

        recipe.metadata.update(
            {
                "source_section": recipe_id,
                "ingredient_count": len(recipe.ingredients),
                "method_step_count": len(recipe.method),
                "imported_by": "GoldMasterParser",
            }
        )
        return recipe, issues

    @staticmethod
    def _section_heading(text: str) -> tuple[str | None, str]:
        """Recognise plain, numbered and inline controlled-source headings."""
        match = re.match(
            r"^(?:\d+[.)]\s*)?(ingredients?|method|directions?|instructions?|"
            r"meal[\s-]*prep(?:aration)?)(?:\s*[:\-–—]\s*(.*))?$",
            clean(text),
            re.IGNORECASE,
        )
        if not match:
            return None, ""
        label = match.group(1).lower().replace("-", " ")
        section = "ingredients" if label.startswith("ingredient") else (
            "meal_prep" if label.startswith("meal") else "method"
        )
        return section, clean(match.group(2) or "")

    @staticmethod
    def _append_method(recipe: Recipe, text: str) -> None:
        value = clean(re.sub(r"^(?:step\s*)?\d+[.):\-]\s*", "", text, flags=re.IGNORECASE))
        if value:
            recipe.method.append(MethodStep(number=len(recipe.method) + 1, text=value))

    def _consume_table(
        self, recipe: Recipe, table_rows: list[list[str]], section: str = "header"
    ) -> str:
        if not table_rows:
            return section

        # Premium editorial cards are stored as two-column labelled rows in the
        # controlled Gold Master.  Older builds treated them as unknown tables,
        # which is why only Meal Prep survived into the photographic PDF.
        premium_labels = {
            "chef's tip": "chef_tip",
            "chef’s tip": "chef_tip",
            "chefie’s tip": "chef_tip",  # legacy v6 source typo
            "chefie's tip": "chef_tip",
            "common mistake": "common_mistake",
            "ingredient swap": "ingredient_swap",
            "meal-prep note": "meal_prep",
            "meal prep note": "meal_prep",
            "meal prep": "meal_prep",
            "serving suggestion": "serving_suggestion",
        }
        normalized_labels = {clean(row[0]).lower().rstrip(":") for row in table_rows if row}
        premium_table = bool(normalized_labels & {
            "chef's tip", "chef’s tip", "chefie’s tip", "chefie's tip",
            "common mistake", "ingredient swap", "serving suggestion",
        })
        premium_found = False
        for row in table_rows:
            if len(row) < 2:
                continue
            label = clean(row[0]).lower().rstrip(":")
            field = premium_labels.get(label)
            value = clean(" ".join(row[1:]))
            if not premium_table or not field or not value:
                continue
            premium_found = True
            if field in {"chef_tip", "ingredient_swap", "meal_prep"}:
                setattr(recipe, field, value)
            else:
                recipe.metadata[field] = value
        if premium_found:
            return section

        # Some Gold Masters store Method/Meal Prep as labelled table rows.
        consumed_content = False
        for row in table_rows:
            if not row:
                continue
            heading, inline = self._section_heading(row[0])
            if heading in {"method", "meal_prep"}:
                values = [inline, *row[1:]]
                for value in filter(None, map(clean, values)):
                    if heading == "method":
                        for step in filter(None, re.split(r"\s*(?:\r?\n|(?=\d+[.)]\s+))", value)):
                            self._append_method(recipe, step)
                    else:
                        recipe.meal_prep = f"{recipe.meal_prep} {value}".strip()
                section = heading
                consumed_content = True
        if consumed_content:
            return section
        flat = [cell for row in table_rows for cell in row]
        info_text = " | ".join(flat)
        if any(label in info_text for label in ("Meal", "Servings", "Status")):
            pairs: dict[str, str] = {}
            for label in ("Meal", "Servings", "Ingredients", "Status"):
                match = re.search(
                    rf"{label}\s+(.+?)(?=\s+(?:Meal|Servings|Ingredients|Status)\s+|$)",
                    info_text,
                )
                if match:
                    pairs[label] = clean(match.group(1).strip(" |"))
            recipe.meal = pairs.get("Meal", recipe.meal)
            servings = number(pairs.get("Servings", ""))
            if servings is not None and servings > 0:
                recipe.servings = int(servings)
            return section

        if "Ingredient" in flat and "Quantity" in flat:
            for row in table_rows[1:]:
                if len(row) < 2 or not row[0]:
                    continue
                quantity, unit = self._parse_quantity(row[1])
                if quantity is None:
                    continue
                recipe.ingredients.append(
                    Ingredient(
                        name=row[0],
                        quantity=quantity,
                        unit=unit or "unit",
                        provenance=Provenance.SOURCE_VERIFIED,
                    )
                )
            return section

        if "Energy" in flat and "Protein" in flat:
            labels = table_rows[0]
            values = table_rows[1] if len(table_rows) > 1 else []
            mapping = {labels[i]: values[i] for i in range(min(len(labels), len(values)))}
            parsed = {
                "energy": number(mapping.get("Energy", "")),
                "protein": number(mapping.get("Protein", "")),
                "carbohydrate": number(mapping.get("Carbohydrates", mapping.get("Carbs", ""))),
                "fat": number(mapping.get("Fat", "")),
                "fibre": number(mapping.get("Fibre", "")),
            }
            if all(value is not None for value in parsed.values()):
                recipe.nutrition = Nutrition(
                    energy_kcal=parsed["energy"],
                    protein_g=parsed["protein"],
                    carbohydrate_g=parsed["carbohydrate"],
                    fat_g=parsed["fat"],
                    fibre_g=parsed["fibre"],
                    locked=True,
                )
        return section

    @staticmethod
    def _parse_quantity(text: str) -> tuple[float | None, str | None]:
        match = QUANTITY_RE.fullmatch(text)
        if match:
            return float(match.group(1).replace(",", ".")), match.group(2)
        return number(text), None

    @staticmethod
    def _looks_like_description(text: str) -> bool:
        return len(text) >= 55 and text.endswith(".") and not text.lower().startswith("qa note")

    @staticmethod
    def _is_badge_line(text: str) -> bool:
        lowered = text.lower()
        return "cofid" in lowered and ("|" in text or "high protein" in lowered)

    @staticmethod
    def _parse_badges(text: str) -> list[str]:
        values = []
        for item in text.split("|"):
            badge = clean(re.sub(r"^[^A-Za-zÀ-ž]+", "", item))
            if badge and badge not in values:
                values.append(badge)
        return values[:6]

    @staticmethod
    def _infer_meal(recipe: Recipe) -> str:
        badge_text = " ".join(recipe.badges).lower()
        title = recipe.title.lower()
        if "breakfast" in badge_text or any(
            word in title for word in ("oats", "toast", "breakfast", "pancake", "quark bowl")
        ):
            return "Breakfast"
        if "lunch" in badge_text or any(word in title for word in ("wrap", "salad", "lunch")):
            return "Lunch"
        return "Dinner"

    @staticmethod
    def _validate_collection(recipes: list[Recipe]) -> list[ParseIssue]:
        issues: list[ParseIssue] = []
        ids = [recipe.recipe_id for recipe in recipes]
        if len(ids) != len(set(ids)):
            issues.append(ParseIssue("ERROR", "DUPLICATE_IDS", "Duplicate recipe IDs detected"))
        expected = [f"PP-R{value:03d}" for value in range(1, 81)]
        missing = [recipe_id for recipe_id in expected if recipe_id not in ids]
        unexpected = [recipe_id for recipe_id in ids if recipe_id not in expected]
        if missing:
            issues.append(ParseIssue("ERROR", "MISSING_IDS", ", ".join(missing)))
        if unexpected:
            issues.append(ParseIssue("ERROR", "UNEXPECTED_IDS", ", ".join(unexpected)))
        if ids != sorted(ids):
            issues.append(ParseIssue("WARNING", "ORDER", "Recipe IDs are not in ascending order"))
        return issues
