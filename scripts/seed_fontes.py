"""Carga do registro de fontes (resolução, latência, termos, atribuição).

    python scripts/seed_fontes.py

Popula a tabela ``fontes`` (PLANO §5.11) com os metadados **verificados** em
`docs/ESTADO_DA_ARTE.md` (21/10/2026). É a base do *duty* de atribuição
(issue #07): o texto exibido no painel e no relatório sai daqui.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "backend" / "src"))

from ngeo.db.base import build_engine, build_session_factory  # noqa: E402
from ngeo.services.seed import seed_fontes  # noqa: E402


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args(argv)

    engine = build_engine()
    factory = build_session_factory(engine)
    with factory() as session:
        if args.dry_run:
            print("[dry-run] nenhuma escrita")
        else:
            resultado = seed_fontes(session)
            session.commit()
            print(
                f"fontes: {resultado['fontes_criadas']} criadas, "
                f"{resultado['fontes_total']} no registro"
            )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
