"""Carga das 29 UCs do arquivo de shapes do IDEFLOR.

    python scripts/seed_ucs.py

O nome vem de ``nome_`` (o ``name`` parece truncado em alguns casos) e a
sigla da gerência é **normalizada** (issue #21 — o defeito é de publicação no
portal do IDEFLOR e todo re-download o reintroduz).
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "backend" / "src"))

from ngeo.core.config import get_settings  # noqa: E402
from ngeo.db.base import build_engine, build_session_factory  # noqa: E402
from ngeo.services.seed import seed_ucs, verificar_carga  # noqa: E402


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--arquivo", type=Path, default=None, help="caminho do geojson")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args(argv)

    settings = get_settings()
    caminho = args.arquivo or settings.referencia_ucs
    if not caminho.exists():
        print(f"ERRO: arquivo de UCs nao encontrado: {caminho}", file=sys.stderr)
        return 2

    engine = build_engine()
    factory = build_session_factory(engine)
    with factory() as session:
        if args.dry_run:
            print(f"[dry-run] {caminho}")
        else:
            resultado = seed_ucs(session, caminho)
            session.commit()
            print(f"ucs: {resultado['ucs_criadas']} criadas, {resultado['ucs_total']} lidas")
            for sigla, total in sorted(resultado["ucs_por_gerencia"].items()):
                print(f"  {sigla}: {total}")
        checagem = verificar_carga(session, escopo="ucs")
    if checagem["problemas"]:
        print("FALHA de integridade:", file=sys.stderr)
        for problema in checagem["problemas"]:
            print(f"  - {problema}", file=sys.stderr)
        return 1
    print("integridade OK:", checagem["contagens"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
