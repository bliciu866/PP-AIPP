from __future__ import annotations

import json
import shutil
import subprocess
from pathlib import Path

from .docx_builder import RecipeDocxBuilder
from .models import LayoutBuildResult, LayoutTheme
from .repository import LayoutRecipeRepository


class LayoutEngine:
    def __init__(self, database_path: str | Path, theme: LayoutTheme | None = None) -> None:
        self.repository = LayoutRecipeRepository(database_path)
        self.builder = RecipeDocxBuilder(theme)

    def build_book(self, output_docx: str | Path, *, book_id: str | None = None, pdf: bool = True) -> LayoutBuildResult:
        recipes = self.repository.list_recipes(book_id)
        if not recipes:
            raise ValueError("No recipes found for layout build")
        docx = self.builder.build(recipes, output_docx)
        warnings: list[str] = []
        pdf_path = self._convert_pdf(docx) if pdf else None
        if pdf and pdf_path is None:
            warnings.append("PDF conversion unavailable; DOCX build completed")
        return LayoutBuildResult(docx, pdf_path, len(recipes), max(0,len(recipes)-1), warnings)

    @staticmethod
    def write_report(result: LayoutBuildResult, path: str | Path) -> Path:
        target=Path(path); target.parent.mkdir(parents=True,exist_ok=True)
        target.write_text(json.dumps(result.to_dict(),indent=2,ensure_ascii=False),encoding="utf-8")
        return target

    @staticmethod
    def _convert_pdf(docx: Path) -> Path | None:
        binary=shutil.which("libreoffice") or shutil.which("soffice")
        if not binary: return None
        out=docx.parent/"rendered"; out.mkdir(parents=True,exist_ok=True)
        completed=subprocess.run([binary,"--headless","--convert-to","pdf","--outdir",str(out),str(docx)],capture_output=True,text=True,timeout=180,check=False)
        candidate=out/(docx.stem+".pdf")
        return candidate if completed.returncode==0 and candidate.exists() else None
