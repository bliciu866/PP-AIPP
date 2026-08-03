from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum
from uuid import uuid4


def new_id() -> str:
    return str(uuid4())


class Provenance(StrEnum):
    SOURCE_VERIFIED = "SOURCE_VERIFIED"
    EDITORIAL_DRAFT = "EDITORIAL_DRAFT"
    APPROVED = "APPROVED"


class RecipeStatus(StrEnum):
    DRAFT = "DRAFT"
    NUTRITION_LOCKED = "NUTRITION_LOCKED"
    CONDITIONAL_PASS = "CONDITIONAL_PASS"
    APPROVED = "APPROVED"


class AssetKind(StrEnum):
    HERO_IMAGE = "HERO_IMAGE"
    INGREDIENT_IMAGE = "INGREDIENT_IMAGE"
    COVER = "COVER"
    LOGO = "LOGO"
    MOCKUP = "MOCKUP"
    OTHER = "OTHER"


class QASeverity(StrEnum):
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


@dataclass(slots=True)
class Ingredient:
    name: str
    quantity: float
    unit: str
    id: str = field(default_factory=new_id)
    source_ref: str | None = None
    preparation_state: str | None = None
    provenance: Provenance = Provenance.SOURCE_VERIFIED
    metadata: dict = field(default_factory=dict)


@dataclass(slots=True)
class Nutrition:
    energy_kcal: float
    protein_g: float
    carbohydrate_g: float
    fat_g: float
    fibre_g: float
    id: str = field(default_factory=new_id)
    serving_basis: str = "per serving"
    locked: bool = True
    provenance: Provenance = Provenance.SOURCE_VERIFIED
    metadata: dict = field(default_factory=dict)


@dataclass(slots=True)
class MethodStep:
    number: int
    text: str
    id: str = field(default_factory=new_id)
    provenance: Provenance = Provenance.SOURCE_VERIFIED


@dataclass(slots=True)
class QARecord:
    category: str
    message: str
    severity: QASeverity = QASeverity.INFO
    id: str = field(default_factory=new_id)
    status: str = "OPEN"
    provenance: Provenance = Provenance.SOURCE_VERIFIED
    metadata: dict = field(default_factory=dict)


@dataclass(slots=True)
class Asset:
    kind: AssetKind
    path: str
    id: str = field(default_factory=new_id)
    alt_text: str = ""
    width_px: int | None = None
    height_px: int | None = None
    checksum: str | None = None
    licence: str | None = None
    metadata: dict = field(default_factory=dict)


@dataclass(slots=True)
class Recipe:
    book_id: str
    recipe_id: str
    title: str
    meal: str
    servings: int
    id: str = field(default_factory=new_id)
    description: str = ""
    status: RecipeStatus = RecipeStatus.DRAFT
    meal_prep: str = ""
    chef_tip: str = ""
    ingredient_swap: str = ""
    ingredients: list[Ingredient] = field(default_factory=list)
    method: list[MethodStep] = field(default_factory=list)
    nutrition: Nutrition | None = None
    badges: list[str] = field(default_factory=list)
    qa_records: list[QARecord] = field(default_factory=list)
    assets: list[Asset] = field(default_factory=list)
    provenance: Provenance = Provenance.SOURCE_VERIFIED
    metadata: dict = field(default_factory=dict)
