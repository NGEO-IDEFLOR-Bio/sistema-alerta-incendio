"""Carga completa da F1, na ordem.

    python scripts/seed_all.py

Ordem: gerências → UCs → zonas → fontes. A verificação de integridade roda
no fim e **falha** (não avisa) se algo não bater (issue #21).
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "backend" / "src"))

from ngeo.core.config import get_settings  # noqa: E402
from ngeo.db.base import build_engine, build_session_factory  # noqa: E402
from ngeo.services.seed import (  # noqa: E402
    seed_fontes,
    seed_gerencias,
    seed_ucs,
    seed_zonas,
    verificar_carga,
)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args(argv)

    settings = get_settings()
    for caminho, rotulo in (
        (settings.referencia_ucs, "UCs"),
        (settings.referencia_zonas, "zoneamento"),
    ):
        if not caminho.exists():
            print(f"ERRO: arquivo de {rotulo} nao encontrado: {caminho}", file=sys.stderr)
            return 2

    engine = build_engine()
    factory = build_session_factory(engine)
    with factory() as session:
        if args.dry_run:
            print("[dry-run] nenhuma escrita")
        else:
            g = seed_gerencias(session)
            session.commit()
            print(
                f"gerencias: {g['gerencias_criadas']} criadas ({g['gerencias_total']} no registro)"
            )

            u = seed_ucs(session, settings.referencia_ucs)
            session.commit()
            print(f"ucs: {u['ucs_criadas']} criadas ({u['ucs_total']} lidas)")
            for sigla, total in sorted(u["ucs_por_gerencia"].items()):
                print(f"  {sigla}: {total}")

            z = seed_zonas(session, settings.referencia_zonas)
            session.commit()
            print(
                f"zonas: {z['zonas_total']} | com UC: {z['zonas_com_uc']} "
                f"| sem UC: {z['zonas_sem_uc']} | UCs com zoneamento: "
                f"{z['ucs_com_zonas']}/{z['ucs_total']}"
            )

            f = seed_fontes(session)
            session.commit()
            print(f"fontes: {f['fontes_criadas']} criadas ({f['fontes_total']} no registro)")

        checagem = verificar_carga(session)

    if checagem["problemas"]:
        print("FALHA de integridade:", file=sys.stderr)
        for problema in checagem["problemas"]:
            print(f"  - {problema}", file=sys.stderr)
        return 1
    print("integridade OK:", checagem["contagens"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
