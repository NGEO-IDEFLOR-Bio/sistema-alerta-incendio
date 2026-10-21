"""Carga das 9 Gerências Regionais (DGMUC).

    python scripts/seed_gerencias.py

Idempotente. Falha (não avisa) se o registro não bater.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "backend" / "src"))

from ngeo.db.base import build_engine, build_session_factory  # noqa: E402
from ngeo.services.seed import seed_gerencias, verificar_carga  # noqa: E402


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dry-run", action="store_true", help="nao escreve no banco")
    args = parser.parse_args(argv)

    engine = build_engine()
    factory = build_session_factory(engine)
    with factory() as session:
        if args.dry_run:
            print("[dry-run] nenhuma escrita")
        else:
            resultado = seed_gerencias(session)
            session.commit()
            print(
                f"gerencias: {resultado['gerencias_criadas']} criadas, "
                f"{resultado['gerencias_total']} no registro"
            )
        checagem = verificar_carga(session, escopo="gerencias")
    if checagem["problemas"]:
        print("FALHA de integridade:", file=sys.stderr)
        for problema in checagem["problemas"]:
            print(f"  - {problema}", file=sys.stderr)
        return 1
    print("integridade OK:", checagem["contagens"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
