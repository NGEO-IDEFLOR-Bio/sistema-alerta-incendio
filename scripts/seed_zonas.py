"""Carga das zonas de plano de gestão (VERBATIM — D-009).

    python scripts/seed_zonas.py

- ``sigla`` e ``zona`` entram **como o plano escreveu**: sem normalizar, sem
  mapear para classe global, sem renomear (issue #26 descartada).
- ``uc_id`` é resolvido por **sobreposição espacial** (PostGIS), nunca pelo campo
  ``UNIDADE`` — que vem truncado na origem (issue #23).
- Zonas sem correspondência espacial **entram assim mesmo**, com ``uc_id`` nulo e
  o motivo registrado: nada é descartado em silêncio (D-010).
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "backend" / "src"))

from ngeo.core.config import get_settings  # noqa: E402
from ngeo.db.base import build_engine, build_session_factory  # noqa: E402
from ngeo.services.seed import seed_zonas, verificar_carga  # noqa: E402


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--arquivo", type=Path, default=None, help="caminho do geojson")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args(argv)

    settings = get_settings()
    caminho = args.arquivo or settings.referencia_zonas
    if not caminho.exists():
        print(f"ERRO: arquivo de zoneamento nao encontrado: {caminho}", file=sys.stderr)
        return 2

    engine = build_engine()
    factory = build_session_factory(engine)
    with factory() as session:
        if args.dry_run:
            print(f"[dry-run] {caminho}")
        else:
            resultado = seed_zonas(session, caminho)
            session.commit()
            print(
                f"zonas: {resultado['zonas_total']} | com UC: {resultado['zonas_com_uc']} "
                f"| sem UC: {resultado['zonas_sem_uc']} | UCs com zoneamento: "
                f"{resultado['ucs_com_zonas']}/{resultado['ucs_total']}"
            )
        checagem = verificar_carga(session, escopo="zonas")
    if checagem["problemas"]:
        print("FALHA de integridade:", file=sys.stderr)
        for problema in checagem["problemas"]:
            print(f"  - {problema}", file=sys.stderr)
        return 1
    print("integridade OK:", checagem["contagens"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
