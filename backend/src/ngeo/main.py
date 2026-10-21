"""Aplicação FastAPI do NGEO.

Instrumento de trabalho, não vitrine (D-011): sem landing page, sem texto
explicativo, sem CTA. A API expõe dados e health.
"""

from __future__ import annotations

from fastapi import FastAPI
from fastapi.responses import JSONResponse

from ngeo.api.health import router as health_router
from ngeo.core.config import get_settings


def create_app() -> FastAPI:
    """Cria a aplicação."""
    settings = get_settings()
    app = FastAPI(
        title="NGEO — Alerta de Incêndio Florestal",
        version="0.1.0",
        docs_url="/docs",
        openapi_url="/openapi.json",
        debug=settings.debug,
    )
    app.include_router(health_router, prefix=settings.api_prefix, tags=["operacao"])

    @app.get("/", include_in_schema=False)
    def raiz() -> JSONResponse:
        """A API não tem landing page: aponta para o health."""
        return JSONResponse(
            {"servico": settings.app_name, "health": f"{settings.api_prefix}/health"}
        )

    return app


app = create_app()
