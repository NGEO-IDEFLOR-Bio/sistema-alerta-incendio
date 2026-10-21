"""NGEO — Sistema de Alerta de Incêndio Florestal (IDEFLOR-Bio).

O pacote é organizado em camadas:

- ``core``      — configuração e ajustes (pydantic-settings).
- ``db``        — engine, sessão e modelos ORM (SQLAlchemy + GeoAlchemy2).
- ``models``    — esquemas de saída da API (pydantic).
- ``api``       — routers HTTP (FastAPI).
- ``services``  — lógica de domínio (leitura de referência, join espacial, seed).
- ``adapters``  — adapters de fontes de focos (F2 em diante).
- ``workers``   — workers Celery (F2 em diante).
"""

__all__ = ["__version__"]

__version__ = "0.1.0"
