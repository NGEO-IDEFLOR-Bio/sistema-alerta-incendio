"""Carga das camadas de referência no PostGIS.

- **Gerências**: as 9 do registro DGMUC (PLANO §5.9).
- **UCs**: as 29 do arquivo de shapes, com o ``id`` oficial preservado.
- **Zonas**: as 252 do zoneamento, **verbatim** (D-009), com ``uc_id`` resolvido
  por **sobreposição espacial no PostGIS** (issue #23) — nunca pelo campo
  ``UNIDADE``, que vem truncado.

O join fica em SQL de propósito: `ST_MakeValid`/`ST_Intersection` do PostGIS são
robustos e indexados, e o join em Python sobre os arquivos oficiais é lento
(~3 min) e sensível à estratégia de reparo de geometria inválida.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from shapely import force_2d
from sqlalchemy import text
from sqlalchemy.orm import Session

from ngeo.db.orm import Fonte, GerenciaRegional, Uc
from ngeo.services.reference import (
    GERENCIAS_CANONICAS,
    UcRef,
    ZonaRef,
    checar_integridade_ucs,
    load_ucs,
    load_zonas,
)

# --------------------------------------------------------------------------- #
# Gerências
# --------------------------------------------------------------------------- #


def seed_gerencias(session: Session) -> dict[str, Any]:
    """Carga (idempotente) as 9 Gerências Regionais."""
    existentes = {g.id: g for g in session.query(GerenciaRegional).all()}
    criadas = 0
    for sigla, nome, _ in GERENCIAS_CANONICAS:
        if sigla in existentes:
            existentes[sigla].nome = nome
            existentes[sigla].ativa = True
            continue
        session.add(GerenciaRegional(id=sigla, nome=nome, ativa=True))
        criadas += 1
    session.flush()
    return {"gerencias_criadas": criadas, "gerencias_total": len(GERENCIAS_CANONICAS)}


# --------------------------------------------------------------------------- #
# UCs
# --------------------------------------------------------------------------- #


def seed_ucs(session: Session, path: Path) -> dict[str, Any]:
    """Carga (idempotente) as 29 UCs.

    O ``id`` oficial (1..29) vai para ``ucs.id_oficial``; a PK é a ser do banco.
    O nome vem de ``nome_`` (o ``name`` parece truncado em alguns casos).
    """
    uCs: list[UcRef] = load_ucs(path)
    checar_integridade_ucs(uCs)  # falha se não bater (issue #21)

    existentes = {u.id_oficial: u for u in session.query(Uc).all()}
    criadas = 0
    for ref in uCs:
        # O arquivo oficial traz coordenadas Z (todas zeradas). O schema e 2D
        # (PLANO §5), entao o Z e descartado na carga.
        wkt = force_2d(ref.geom).wkt
        uc = existentes.get(ref.id_oficial)
        if uc is None:
            session.execute(
                text(
                    """
                    INSERT INTO ucs (id_oficial, nome, categoria, area_ha, gerencia_id,
                                     geom, props)
                    VALUES (:id_oficial, :nome, :categoria, :area_ha, :gerencia_id,
                            ST_MakeValid(ST_GeomFromText(:wkt, 4326)),
                            CAST(:props AS jsonb))
                    """
                ),
                {
                    "id_oficial": ref.id_oficial,
                    "nome": ref.nome,
                    "categoria": ref.categoria,
                    "area_ha": ref.area_ha,
                    "gerencia_id": ref.sigla_gerencia,
                    "wkt": wkt,
                    "props": json.dumps(ref.props, ensure_ascii=False),
                },
            )
            criadas += 1
        else:
            session.execute(
                text(
                    """
                    UPDATE ucs SET nome = :nome, categoria = :categoria, area_ha = :area_ha,
                                    gerencia_id = :gerencia_id,
                                    geom = ST_MakeValid(ST_GeomFromText(:wkt, 4326)),
                                    props = CAST(:props AS jsonb)
                    WHERE id_oficial = :id_oficial
                    """
                ),
                {
                    "id_oficial": ref.id_oficial,
                    "nome": ref.nome,
                    "categoria": ref.categoria,
                    "area_ha": ref.area_ha,
                    "gerencia_id": ref.sigla_gerencia,
                    "wkt": wkt,
                    "props": json.dumps(ref.props, ensure_ascii=False),
                },
            )
    session.flush()
    por_gerencia: dict[str, int] = {}
    for ref in uCs:
        por_gerencia[ref.sigla_gerencia] = por_gerencia.get(ref.sigla_gerencia, 0) + 1
    return {"ucs_criadas": criadas, "ucs_total": len(uCs), "ucs_por_gerencia": por_gerencia}


# --------------------------------------------------------------------------- #
# Zonas
# --------------------------------------------------------------------------- #


def seed_zonas(session: Session, path: Path) -> dict[str, Any]:
    """Carga (idempotente) as 252 zonas e resolve ``uc_id`` por sobreposição.

    ``sigla`` e ``zona`` entram **verbatim** (D-009). Não existe coluna de
    classe, de normalização ou de curadoria (issue #26 descartada).
    """
    zonas: list[ZonaRef] = load_zonas(path)

    session.execute(text("DELETE FROM ucs_zonas"))
    for zona in zonas:
        wkt = force_2d(zona.geom).wkt if zona.geom is not None else None
        session.execute(
            text(
                """
                INSERT INTO ucs_zonas (sigla, zona, unidade_origem, area_ha, geom)
                VALUES (:sigla, :zona, :unidade, :area_ha,
                        CASE WHEN :wkt IS NULL THEN NULL
                             ELSE ST_MakeValid(ST_GeomFromText(:wkt, 4326)) END)
                """
            ),
            {
                "sigla": zona.sigla,
                "zona": zona.zona,
                "unidade": zona.unidade_origem,
                "area_ha": zona.area_ha,
                "wkt": wkt,
            },
        )
    session.flush()

    # ---- Join espacial (issue #23): maior área de interseção ---------------
    # `ST_MakeValid` dos dois lados porque os arquivos do IDEFLOR têm geometria
    # inválida (auto-interseção) em algumas features.
    # --- Join espacial (issue #23) -----------------------------------------
    # Regra do PLANO/T1: **centroide contido** ou, na falta, **maior area de
    # intersecao**. Nunca pelo campo `UNIDADE` (truncado — e, em 9 casos, Wrong).
    #
    # A geometria foi sanitizada na carga (ST_MakeValid), porque os arquivos do
    # IDEFLOR tem auto-intersecao e o `ST_Intersection` lanca TopologyException
    # com a geometria crua. Sanear as 252 zonas custa ~21 s — aceitavel numa
    # carga, inviavel se repetido por par.
    #
    # A auditoria do join fica em `join_n_candidatas`: quantas UCs a zona
    # toca. Uma zona que toca 3 UCs e um mosaico — e precisa de revisao.
    session.execute(
        text(
            """
            WITH candidatas AS (
                SELECT z.id AS zona_id, u.id AS uc_pk,
                       ST_Contains(u.geom, ST_Centroid(z.geom)) AS centroide_dentro
                FROM ucs_zonas z
                JOIN ucs u ON u.geom && z.geom AND ST_Intersects(u.geom, z.geom)
                WHERE z.geom IS NOT NULL
            )
            UPDATE ucs_zonas z
            SET uc_id = r.uc_pk,
                join_metodo = r.metodo,
                join_n_candidatas = r.n_candidatas
            FROM (
                SELECT c.zona_id,
                       COALESCE(
                           (SELECT c2.uc_pk FROM candidatas c2
                            WHERE c2.zona_id = c.zona_id AND c2.centroide_dentro
                            ORDER BY ST_Area((SELECT geom FROM ucs u2 WHERE u2.id = c2.uc_pk)) ASC
                            LIMIT 1),
                           (SELECT c3.uc_pk FROM candidatas c3
                            WHERE c3.zona_id = c.zona_id
                            ORDER BY ST_Area(ST_Intersection(
                                       (SELECT geom FROM ucs u3 WHERE u3.id = c3.uc_pk),
                                       (SELECT geom FROM ucs_zonas z3 WHERE z3.id = c3.zona_id)
                                   )) DESC
                            LIMIT 1)
                       ) AS uc_pk,
                       CASE
                           WHEN EXISTS (SELECT 1 FROM candidatas c4
                                        WHERE c4.zona_id = c.zona_id AND c4.centroide_dentro)
                           THEN 'centroide_contido'
                           ELSE 'maior_intersecao'
                       END AS metodo,
                       (SELECT count(*) FROM candidatas c5
                         WHERE c5.zona_id = c.zona_id) AS n_candidatas
                FROM candidatas c
                GROUP BY c.zona_id
            ) r
            WHERE r.zona_id = z.id AND r.uc_pk IS NOT NULL
            """
        )
    )

    session.execute(
        text(
            """
            UPDATE ucs_zonas SET join_metodo = 'sem_geometria'
            WHERE geom IS NULL AND join_metodo IS NULL
            """
        )
    )
    # Sem sobreposicao com nenhuma UC: registrado, nao descartado (D-010).
    session.execute(
        text(
            """
            UPDATE ucs_zonas SET join_metodo = 'sem_intersecao', join_n_candidatas = 0
            WHERE geom IS NOT NULL AND join_metodo IS NULL
            """
        )
    )
    session.flush()

    contagens = (
        session.execute(
            text(
                """
            SELECT
              (SELECT count(*) FROM ucs_zonas)                          AS zonas_total,
              (SELECT count(*) FROM ucs_zonas WHERE uc_id IS NOT NULL)  AS zonas_com_uc,
              (SELECT count(*) FROM ucs_zonas WHERE uc_id IS NULL)      AS zonas_sem_uc,
              (SELECT count(DISTINCT uc_id) FROM ucs_zonas
                 WHERE uc_id IS NOT NULL)                              AS ucs_com_zonas
            """
            )
        )
        .mappings()
        .one()
    )
    return {
        "zonas_total": int(contagens["zonas_total"]),
        "zonas_com_uc": int(contagens["zonas_com_uc"]),
        "zonas_sem_uc": int(contagens["zonas_sem_uc"]),
        "ucs_com_zonas": int(contagens["ucs_com_zonas"]),
        "ucs_total": 29,
    }


# --------------------------------------------------------------------------- #
# Fontes (proveniência, licença, atribuição — PLANO §5.11)
# --------------------------------------------------------------------------- #

#: Metadados verificados em `docs/ESTADO_DA_ARTE.md` (21/10/2026).
FONTES_CONHECIDAS: tuple[dict[str, Any], ...] = (
    {
        "fonte": "FIRMS_VIIRS",
        "nome": "NASA FIRMS — VIIRS (375 m)",
        "produto": "VIIRS_NOAA20_NRT",
        "resolucao_m": 375,
        "latencia_horas": 3,
        "url": "https://firms.modaps.eosdis.nasa.gov/api/area",
        "termos_url": "https://firms.modaps.eosdis.nasa.gov/api/map_key/",
        "atribuicao_requerida": (
            "We acknowledge the use of imagery from the NASA LANCE FIRMS "
            "(https://earthdata.nasa.gov/firms), part of the NASA Earth Science Data "
            "and Information System (ESDIS)."
        ),
        "licenca": (
            "NASA promotes full and open sharing of data (EOSDIS Data Use and Citation Guidance)"
        ),
        "chave_requerida": True,
        "versao_produto_atual": "2.0NRT",
        "observacao": "NRT < 3 h. URT/RT so para EUA e Canada (D-015).",
    },
    {
        "fonte": "FIRMS_MODIS",
        "nome": "NASA FIRMS — MODIS (1 km)",
        "produto": "MODIS_NRT",
        "resolucao_m": 1000,
        "latencia_horas": 3,
        "url": "https://firms.modaps.eosdis.nasa.gov/api/area",
        "termos_url": "https://firms.modaps.eosdis.nasa.gov/api/map_key/",
        "atribuicao_requerida": (
            "We acknowledge the use of imagery from the NASA LANCE FIRMS "
            "(https://earthdata.nasa.gov/firms), part of the NASA Earth Science Data "
            "and Information System (ESDIS)."
        ),
        "licenca": "NASA promotes full and open sharing of data",
        "chave_requerida": True,
        "versao_produto_atual": None,
        "observacao": "Confirmacao por sensor de resolucao menor quando o VIIRS falha (nuvem).",
    },
    {
        "fonte": "NOAA_ABI_FDC",
        "nome": "NOAA GOES-R ABI Level 2 Fire/Hot Spot Characterization (FDC)",
        "produto": "ABI-L2-FDC",
        "resolucao_m": 2000,
        "latencia_horas": 0.25,
        "intervalo_minutos": 10,
        "url": "https://www.star.nesdis.noaa.gov/atmospheric-composition-training/documents/G16_ABI_FDC_ReadMe.pdf",
        "termos_url": "https://catalog.data.gov/dataset/noaa-goes-r-series-advanced-baseline-imager-abi-level-2-fire-hot-spot-characterization-fdc",
        "atribuicao_requerida": (
            "GOES-R Algorithm Working Group and GOES-R Program Office, (2018): NOAA GOES-R "
            "Series Advanced Baseline Imager (ABI) Level 2 Fire/Hot Spot Characterization (FDC)."
        ),
        "licenca": "NOAA data — sem copyright (US Government Work)",
        "chave_requerida": False,
        "versao_produto_atual": None,
        "observacao": (
            "Bucket publico noaa-goes16. Coordenada L2 nao corrigida para o terreno "
            "(posicao_terreno_corrigida = false). GOES-19 e o GOES East desde 07/04/2025."
        ),
    },
    {
        "fonte": "INPE_QUEIMADAS",
        "nome": "INPE — Programa Queimadas / BDQueimadas",
        "produto": "FOCOS_QUEBIMADAS",
        "resolucao_m": 375,
        "latencia_horas": 0.17,
        "intervalo_minutos": 10,
        "url": "https://data.inpe.br/queimadas/dados-abertos/",
        "termos_url": "https://data.inpe.br/queimadas/",
        "atribuicao_requerida": "Programa Queimadas do INPE — Dados Abertos para Uso Publico",
        "licenca": "NÃO VERIFICADA — texto legal do INPE pendente (issue #07)",
        "chave_requerida": False,
        "versao_produto_atual": None,
        "observacao": (
            "Sem autenticacao. Processa 10 satelites proprios (inclui GOES, MetOp, Meteosat)."
        ),
    },
    {
        "fonte": "MAPBIOMAS_FOGO",
        "nome": "MapBiomas Fire Collection 5/5.1 (area queimada)",
        "produto": "mapbiomas_fire_collection5",
        "resolucao_m": 30,
        "latencia_horas": None,
        "url": "https://brasil.mapbiomas.org/en/mapbiomas-fogo/",
        "termos_url": "https://brasil.mapbiomas.org/wp-content/uploads/sites/4/2026/05/ATBD-MapBiomas-Fogo-Colecao-5.pdf",
        "atribuicao_requerida": "MapBiomas Fire Collection 5 (Landsat 30 m)",
        "licenca": "NÃO VERIFICADA — licença especifica pendente (issue #07)",
        "chave_requerida": False,
        "versao_produto_atual": "5.1",
        "observacao": "ROTULO da frente A (anual/mensal). NAO e deteccao NRT.",
    },
)


def seed_fontes(session: Session) -> dict[str, Any]:
    """Carga (idempotente) o registro de fontes, termos e atribuicoes."""
    existentes = {f.fonte: f for f in session.query(Fonte).all()}
    criadas = 0
    for dados in FONTES_CONHECIDAS:
        atual = existentes.get(dados["fonte"])
        if atual is None:
            session.add(Fonte(**dados))
            criadas += 1
        else:
            for chave, valor in dados.items():
                setattr(atual, chave, valor)
    session.flush()
    return {"fontes_criadas": criadas, "fontes_total": len(FONTES_CONHECIDAS)}


# --------------------------------------------------------------------------- #
# Verificacao
# --------------------------------------------------------------------------- #


def verificar_carga(session: Session, escopo: str = "completo") -> dict[str, Any]:
    """Confere a carga no banco. **Falha** se não bater (issue #21).

    ``escopo`` limita o que é conferido: ``"gerencias"``, ``"ucs"`` ou
    ``"completo"`` (default). O seed completo confere tudo.
    """
    contagens = (
        session.execute(
            text(
                """
            SELECT
              (SELECT count(*) FROM gerencias_regionais) AS gerencias,
              (SELECT count(*) FROM ucs)                   AS ucs,
              (SELECT count(*) FROM ucs_zonas)             AS zonas,
              (SELECT count(*) FROM ucs_zonas WHERE uc_id IS NULL) AS zonas_sem_uc,
              (SELECT count(*) FROM ucs WHERE gerencia_id IS NULL) AS ucs_sem_gerencia
            """
            )
        )
        .mappings()
        .one()
    )

    problemas: list[str] = []
    if escopo in ("gerencias", "completo") and int(contagens["gerencias"]) != 9:
        problemas.append(f"gerencias: esperado 9, encontrado {contagens['gerencias']}")
    if escopo in ("ucs", "completo"):
        if int(contagens["ucs"]) != 29:
            problemas.append(f"ucs: esperado 29, encontrado {contagens['ucs']}")
        if int(contagens["ucs_sem_gerencia"]):
            problemas.append(
                f"{contagens['ucs_sem_gerencia']} UCs sem gerencia resolvida (issue #21)"
            )
        ids_oficiais = [
            int(linha["id_oficial"])
            for linha in session.execute(
                text("SELECT id_oficial FROM ucs WHERE id_oficial IS NOT NULL ORDER BY id_oficial")
            )
            .mappings()
            .all()
        ]
        if ids_oficiais != list(range(1, 30)):
            problemas.append(f"ids oficiais das UCs fora de 1..29: {ids_oficiais}")

    return {
        "contagens": {k: int(v) for k, v in contagens.items()},
        "problemas": problemas,
    }
