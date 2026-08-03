from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path


@dataclass(slots=True)
class LayoutTheme:
    page_width_in: float = 8.5
    page_height_in: float = 11.0
    margin_top_in: float = 0.55
    margin_bottom_in: float = 0.55
    margin_inside_in: float = 0.72
    margin_outside_in: float = 0.62
    primary_hex: str = "3E8E41"
    charcoal_hex: str = "2E2E2E"
    sage_hex: str = "EAF5EA"
    yellow_hex: str = "FFF4CC"
    grey_hex: str = "F3F3F3"
    title_font: str = "Aptos Display"
    body_font: str = "Aptos"


@dataclass(slots=True)
class LayoutBuildResult:
    output_docx: Path
    output_pdf: Path | None
    recipe_count: int
    page_breaks: int
    warnings: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "output_docx": str(self.output_docx),
            "output_pdf": str(self.output_pdf) if self.output_pdf else None,
            "recipe_count": self.recipe_count,
            "page_breaks": self.page_breaks,
            "warnings": self.warnings,
        }
