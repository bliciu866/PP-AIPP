from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import Enum
from typing import Any
from uuid import uuid4


def utc_now() -> str:
    return datetime.now(UTC).isoformat()


class ProjectStatus(str, Enum):
    ACTIVE = "ACTIVE"
    PAUSED = "PAUSED"
    ARCHIVED = "ARCHIVED"


class BookStatus(str, Enum):
    DRAFT = "DRAFT"
    PRODUCTION = "PRODUCTION"
    PUBLISHED = "PUBLISHED"
    ARCHIVED = "ARCHIVED"


class ExportStatus(str, Enum):
    QUEUED = "QUEUED"
    SUCCEEDED = "SUCCEEDED"
    FAILED = "FAILED"


@dataclass(slots=True)
class ProjectRecord:
    slug: str
    name: str
    brand: str | None = None
    status: ProjectStatus = ProjectStatus.ACTIVE
    id: str = field(default_factory=lambda: str(uuid4()))
    created_at: str = field(default_factory=utc_now)
    updated_at: str = field(default_factory=utc_now)
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class BookRecord:
    project_id: str
    slug: str
    title: str
    language: str = "en-GB"
    status: BookStatus = BookStatus.DRAFT
    id: str = field(default_factory=lambda: str(uuid4()))
    created_at: str = field(default_factory=utc_now)
    updated_at: str = field(default_factory=utc_now)
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class ReleaseRecord:
    book_id: str
    version: str
    notes: str = ""
    id: str = field(default_factory=lambda: str(uuid4()))
    created_at: str = field(default_factory=utc_now)


@dataclass(slots=True)
class ExportRecord:
    book_id: str
    format: str
    path: str
    status: ExportStatus = ExportStatus.QUEUED
    id: str = field(default_factory=lambda: str(uuid4()))
    created_at: str = field(default_factory=utc_now)
    completed_at: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class HistoryRecord:
    entity_type: str
    entity_id: str
    action: str
    payload: dict[str, Any] = field(default_factory=dict)
    id: str = field(default_factory=lambda: str(uuid4()))
    created_at: str = field(default_factory=utc_now)
