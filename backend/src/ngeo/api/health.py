"""Rotas HTTP."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, Response, status
from sqlalchemy import text
from sqlalchemy.orm import Session

from ngeo.core.config import Settings, get_settings
from ngeo.db.base import build_engine, build_session_factory
from ngeo.models.health import ContagensHealth, HealthResponse, RespostaBanco

router = APIRouter()

#: (tabela, campo do health) — a contagem é por TABELA, o campo é do schema.
_TABELAS = (
    ("gerencias_regionais", "gerencias"),
    ("ucs", "ucs"),
    ("ucs_zonas", "zonas"),
    ("focos", "focos"),
    ("eventos_fogo", "eventos_fogo"),
    ("alertas", "alertas"),
)


def get_session() -> Session:
    """Sessão para as rotas. Substituível em teste via ``dependency_overrides``."""
    engine = build_engine()
    factory = build_session_factory(engine)
    session = factory()
    try:
        yield session
    finally:
        session.close()


def _versao_esquema(session: Session) -> str | None:
    linha = session.execute(text("SELECT version_num FROM alembic_version")).first()
    return linha[0] if linha else None


def _contagens(session: Session) -> ContagensHealth:
    contagens = ContagensHealth()
    for tabela, campo in _TABELAS:
        total = int(session.execute(text(f"SELECT count(*) FROM {tabela}")).scalar_one())
        setattr(contagens, campo, total)
    contagens.zonas_sem_uc = int(
        session.execute(text("SELECT count(*) FROM ucs_zonas WHERE uc_id IS NULL")).scalar_one()
    )
    return contagens


@router.get("/health", response_model=HealthResponse)
def health(
    response: Response,
    session: Annotated[Session, Depends(get_session)],
    settings: Annotated[Settings, Depends(get_settings)],
) -> HealthResponse:
    """Estado do serviço: banco, versão do schema e contagens."""
    alvo = settings.database_target
    try:
        versao = _versao_esquema(session)
        contagens = _contagens(session)
    except Exception as exc:  # noqa: BLE001 - health não pode subir 500
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
        return HealthResponse(
            status="degraded",
            servico=settings.app_name,
            versao_esquema=None,
            banco=RespostaBanco(
                conectado=False,
                host=str(alvo["host"]),
                porta=int(alvo["porta"]),  # type: ignore[arg-type]
                banco=str(alvo["banco"]),
                erro=f"{type(exc).__name__}: {exc}",
            ),
            contagens=ContagensHealth(),
        )

    return HealthResponse(
        status="ok",
        servico=settings.app_name,
        versao_esquema=versao,
        banco=RespostaBanco(
            conectado=True,
            host=str(alvo["host"]),
            porta=int(alvo["porta"]),  # type: ignore[arg-type]
            banco=str(alvo["banco"]),
        ),
        contagens=contagens,
    )
