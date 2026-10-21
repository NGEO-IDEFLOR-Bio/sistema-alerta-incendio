"""Esquema da resposta de health."""

from __future__ import annotations

from pydantic import BaseModel, Field


class RespostaBanco(BaseModel):
    """Estado do banco — **sem senha**."""

    conectado: bool
    host: str | None = None
    porta: int | None = None
    banco: str | None = None
    erro: str | None = None


class ContagensHealth(BaseModel):
    """Contagens das tabelas de referência e de operação."""

    gerencias: int = 0
    ucs: int = 0
    zonas: int = 0
    zonas_sem_uc: int = 0
    focos: int = 0
    eventos_fogo: int = 0
    alertas: int = 0


class HealthResponse(BaseModel):
    """Health do serviço.

    Resposta tecnica de operação — não é conteúdo de produto (D-011 não se
    aplica a health check).
    """

    status: str = Field(description="ok | degraded")
    servico: str
    versao_esquema: str | None = None
    banco: RespostaBanco
    contagens: ContagensHealth = Field(default_factory=ContagensHealth)
