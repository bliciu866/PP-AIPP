from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from .models import Provenance


@dataclass(slots=True)
class AIRequest:
    task: str
    content: str
    context: dict


@dataclass(slots=True)
class AIResponse:
    content: str
    provider: str
    model: str
    provenance: Provenance = Provenance.EDITORIAL_DRAFT


class AIProvider(Protocol):
    name: str

    def generate(self, request: AIRequest) -> AIResponse: ...


class AIGateway:
    def __init__(self) -> None:
        self._providers: dict[str, AIProvider] = {}

    def register(self, provider: AIProvider) -> None:
        self._providers[provider.name] = provider

    def generate(self, provider_name: str, request: AIRequest) -> AIResponse:
        if provider_name not in self._providers:
            raise KeyError(f"AI provider not registered: {provider_name}")
        response = self._providers[provider_name].generate(request)
        response.provenance = Provenance.EDITORIAL_DRAFT
        return response
