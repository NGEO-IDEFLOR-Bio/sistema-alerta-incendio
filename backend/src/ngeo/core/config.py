"""Configuração do NGEO.

Lê o ``.env`` da raiz do repo (gitignored). Todo caminho de arquivo de
referência é configurável — os arquivos de referência **não** estão no git.
"""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

#: Raiz do repo: .../sistema_alerta_incendio
#: (config.py -> core -> ngeo -> src -> backend -> repo)
REPO_ROOT = Path(__file__).resolve().parents[4]


class Settings(BaseSettings):
    """Ajustes da aplicação."""

    model_config = SettingsConfigDict(
        env_file=REPO_ROOT / ".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    # ---- Banco (PostGIS) -------------------------------------------------
    database_url: str = "postgresql+psycopg2://postgres:postgres@localhost:5433/alerta_fogo"
    postgres_db: str = "alerta_fogo"
    postgres_user: str = "postgres"
    postgres_password: str = "postgres"
    postgres_port: int = 5433

    # ---- Redis (celery broker) -------------------------------------------
    redis_url: str = "redis://localhost:6379/0"
    redis_port: int = 6379

    # ---- Caminhos de referência (fora do git) -----------------------------
    #: Shapes das UCs com gerência (29 UCs, 9 gerências).
    referencia_ucs: Path = REPO_ROOT / "data" / "shapes_de_todas_as_unidades_com_gerencia.geojson"
    #: Zoneamento dos planos de gestão (252 zonas, 16 UCs).
    referencia_zonas: Path = (
        REPO_ROOT.parent / "visualizador" / "data" / "zoneamentos_ucs_estaduais.geojson"
    )

    # ---- Aplicação --------------------------------------------------------
    debug: bool = False
    api_prefix: str = "/api"
    app_name: str = "ngeo-alerta-incendio"

    @property
    def database_target(self) -> dict[str, object]:
        """Alvo do banco **sem senha** — para logs e para o ``/api/health``."""
        return {
            "host": self.database_url.split("@")[-1].split(":")[0] or "localhost",
            "porta": self.postgres_port,
            "banco": self.postgres_db,
        }


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Settings com cache (leitura do .env uma vez)."""
    return Settings()
