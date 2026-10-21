"""Testes da API de health.

O caminho de erro (banco fora do ar) roda **sempre**. O caminho de sucesso
depende do Postgres local e e pulado quando nao ha banco.
"""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient
from ngeo.api.health import get_session
from ngeo.core.config import get_settings
from ngeo.db.base import build_engine, build_session_factory
from ngeo.main import create_app

SETTINGS = get_settings()


def _banco_disponivel() -> bool:
    try:
        engine = build_engine()
        factory = build_session_factory(engine)
        with factory() as session:
            session.execute.__self__.connection  # noqa: B018 - apenas toca a conexao
            from sqlalchemy import text

            session.execute(text("SELECT 1"))
        return True
    except Exception:  # noqa: BLE001
        return False


BANCO_DISPONIVEL = _banco_disponivel()
precisa_banco = pytest.mark.skipif(not BANCO_DISPONIVEL, reason="Postgres local indisponivel")


class _SessaoQuebrada:
    """Sessao que falha como se o banco estivesse fora do ar."""

    def execute(self, *args: object, **kwargs: object) -> object:
        raise OSError("connection refused")


def test_health_degradado_quando_o_banco_esta_fora() -> None:
    app = create_app()
    app.dependency_overrides[get_session] = lambda: _SessaoQuebrada()
    with TestClient(app) as client:
        resposta = client.get("/api/health")
    assert resposta.status_code == 503
    corpo = resposta.json()
    assert corpo["status"] == "degraded"
    assert corpo["banco"]["conectado"] is False
    assert corpo["banco"]["erro"]
    # Nenhuma senha no payload.
    assert SETTINGS.database_url not in resposta.text
    assert "password" not in resposta.text.lower()


def test_raiz_aponta_para_o_health() -> None:
    with TestClient(create_app()) as client:
        resposta = client.get("/")
    assert resposta.status_code == 200
    assert resposta.json()["health"].endswith("/health")


@precisa_banco
def test_health_ok_com_banco_real() -> None:
    with TestClient(create_app()) as client:
        resposta = client.get("/api/health")
    assert resposta.status_code == 200
    corpo = resposta.json()
    assert corpo["status"] == "ok"
    assert corpo["banco"]["conectado"] is True
    assert corpo["versao_esquema"]
    assert SETTINGS.database_url not in resposta.text


@precisa_banco
def test_health_conta_a_carga_de_referencia() -> None:
    with TestClient(create_app()) as client:
        corpo = client.get("/api/health").json()
    contagens = corpo["contagens"]
    assert contagens["gerencias"] == 9
    assert contagens["ucs"] == 29
    assert contagens["zonas"] == 252
    assert contagens["zonas_sem_uc"] >= 1
