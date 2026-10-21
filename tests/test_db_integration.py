"""Teste de integração com o Postgres local (F1).

Roda a migração do Alembic, executa o seed e confere o resultado de ponta a
ponta. **Pulado** quando não há banco local (ou seja: em CI sem Docker, a
suíte continua verde, mas esta parte não é exercitada — e isso é dito no
relatório, não escondido).
"""

from __future__ import annotations

import pytest
from alembic import command
from alembic.config import Config
from ngeo.core.config import get_settings
from ngeo.db.base import build_engine, build_session_factory
from ngeo.services.seed import (
    seed_fontes,
    seed_gerencias,
    seed_ucs,
    seed_zonas,
    verificar_carga,
)
from sqlalchemy import text

SETTINGS = get_settings()
RAIZ_REPO = SETTINGS.database_url  # placeholder para nao importar Path
ALEMBIC_INI = "backend/alembic.ini"


def _banco_disponivel() -> bool:
    try:
        engine = build_engine()
        factory = build_session_factory(engine)
        with factory() as session:
            session.execute(text("SELECT 1"))
        return True
    except Exception:  # noqa: BLE001
        return False


BANCO_DISPONIVEL = _banco_disponivel()
precisa_banco = pytest.mark.skipif(not BANCO_DISPONIVEL, reason="Postgres local indisponivel")
precisa_referencia = pytest.mark.skipif(
    not (SETTINGS.referencia_ucs.exists() and SETTINGS.referencia_zonas.exists()),
    reason="camadas de referencia ausentes",
)


@pytest.fixture(scope="module")
def sessao():
    engine = build_engine()
    factory = build_session_factory(engine)
    session = factory()
    yield session
    session.close()


@precisa_banco
def test_migracao_esta_aplicada(sessao) -> None:
    versao = sessao.execute(text("SELECT version_num FROM alembic_version")).scalar_one()
    assert versao == "20261021_0001"


@precisa_banco
def test_migracao_e_reaplicavel(sessao) -> None:
    """`upgrade head` de novo não pode explodir (idempotência de migração)."""
    config = Config(ALEMBIC_INI)
    command.upgrade(config, "head")
    versao = sessao.execute(text("SELECT version_num FROM alembic_version")).scalar_one()
    assert versao == "20261021_0001"


@precisa_banco
@precisa_referencia
def test_seed_e_idempotente(sessao) -> None:
    seed_gerencias(sessao)
    sessao.commit()
    seed_ucs(sessao, SETTINGS.referencia_ucs)
    sessao.commit()
    seed_zonas(sessao, SETTINGS.referencia_zonas)
    sessao.commit()
    seed_fontes(sessao)
    sessao.commit()

    primeira = dict(verificar_carga(sessao)["contagens"])
    assert primeira["gerencias"] == 9
    assert primeira["ucs"] == 29
    assert primeira["zonas"] == 252

    # Roda de novo: nada duplica.
    seed_gerencias(sessao)
    seed_ucs(sessao, SETTINGS.referencia_ucs)
    seed_zonas(sessao, SETTINGS.referencia_zonas)
    seed_fontes(sessao)
    sessao.commit()
    segunda = dict(verificar_carga(sessao)["contagens"])
    assert segunda == primeira


@precisa_banco
@precisa_referencia
def test_uc_com_gerencia_resolvida(sessao) -> None:
    """Issue #21: todo `uc.gerencia_id` tem que resolver numa gerência do registro."""
    linhas = sessao.execute(
        text(
            """
            SELECT u.nome, u.gerencia_id, g.nome
            FROM ucs u
            JOIN gerencias_regionais g ON g.id = u.gerencia_id
            ORDER BY u.id_oficial
            """
        )
    ).all()
    assert len(linhas) == 29
    for nome, sigla, nome_gerencia in linhas:
        assert sigla, f"UC {nome} sem gerencia"
        assert nome_gerencia, f"gerencia {sigla} sem nome"


@precisa_banco
@precisa_referencia
def test_zonas_verbatim_no_banco(sessao) -> None:
    """D-009: `sigla` e `zona` no banco sao exatamente os do arquivo."""
    linhas = sessao.execute(text("SELECT sigla, zona FROM ucs_zonas")).all()
    assert len(linhas) == 252
    textos_za = {zona for sigla, zona in linhas if sigla == "ZA"}
    assert len(textos_za) == 2, "sigla ZA deve manter os dois textos da origem"


@precisa_banco
@precisa_referencia
def test_zona_sem_uc_ficam_registradas(sessao) -> None:
    """D-010: zona sem correspondência espacial é registrada, não descartada."""
    total, com_uc, sem_uc = sessao.execute(
        text(
            """
            SELECT count(*),
                   count(*) FILTER (WHERE uc_id IS NOT NULL),
                   count(*) FILTER (WHERE uc_id IS NULL)
            FROM ucs_zonas
            """
        )
    ).one()
    assert total == 252
    assert com_uc + sem_uc == total
    assert sem_uc >= 1
    # As sem UC têm o motivo registrado.
    sem_motivo = sessao.execute(
        text("SELECT count(*) FROM ucs_zonas WHERE uc_id IS NULL AND join_metodo IS NULL")
    ).scalar_one()
    assert sem_motivo == 0
