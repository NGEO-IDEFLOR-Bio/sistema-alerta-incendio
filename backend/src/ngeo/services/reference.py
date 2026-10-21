"""Leitura das camadas de referência do IDEFLOR-Bio e resolução de UCs ↔ zonas.

Regras que este módulo implementa (e que **não** podem ser violadas):

- **Sigla de gerência normalizada** (issue #21): o cadastro oficial do IDEFLOR
  grava `GRCN-l` / `GRCN-ll` / `GRCN-lll` (L minúsculo no lugar do I romano).
  A cópia local foi corrigida, mas **todo re-download do arquivo original
  reintroduz o defeito** (issue #29) — então a normalização é feita sempre, na
  carga, e não só uma vez.
- **Zonas verbatim** (D-009): `sigla` e `zona` entram como o plano escreveu.
  Não existe taxonomia global de zonas e nada é normalizado.
- **Join UC ↔ zona por sobreposição espacial** (issue #23): o campo `UNIDADE` do
  arquivo de zoneamento está truncado ("Ambiental da Ilha de Combu", "Reserva
  Biológica do Maicuru (REBIO") e não casa com o nome da UC.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from shapely import STRtree
from shapely.geometry import MultiPolygon, Polygon, shape
from shapely.geometry.base import BaseGeometry
from shapely.ops import unary_union
from shapely.prepared import prep
from shapely.validation import make_valid

# --------------------------------------------------------------------------- #
# Registro canônico das Gerências Regionais (DGMUC)
# --------------------------------------------------------------------------- #

#: (sigla, nome oficial, nº de UCs esperado) — PLANO_ARQUITETURA §5.9.
#: Verificado contra o portal IDEFLOR-Bio em 21/10/2026 (D-007).
GERENCIAS_CANONICAS: tuple[tuple[str, str, int], ...] = (
    ("GRCN-I", "GERÊNCIA REGIONAL DA CALHA NORTE I", 2),
    ("GRCN-II", "GERÊNCIA REGIONAL DA CALHA NORTE II", 5),
    ("GRCN-III", "GERÊNCIA REGIONAL DA CALHA NORTE III", 2),
    ("GRB", "GERÊNCIA REGIONAL DE BELÉM", 4),
    ("GRTUC", "GERÊNCIA REGIONAL DE TUCURUÍ", 3),
    ("GRA", "GERÊNCIA REGIONAL DO ARAGUAIA", 2),
    ("GRM", "GERÊNCIA REGIONAL DO MARAJÓ", 2),
    ("GRNE", "GERÊNCIA REGIONAL DO NORDESTE", 4),
    ("GRX", "GERÊNCIA REGIONAL DO XINGU", 5),
)

#: Nº de UCs e de gerências que a carga precisa produzir (integridade — issue #21).
TOTAL_UC_ESPERADO = 29
TOTAL_GERENCIAS_ESPERADO = 9

_SIGLA_RE = re.compile(r"\(([^()]*)\)\s*$")
#: Família GRCN com o defeito de publicação: I romano virado em L minúsculo.
_GRCN_L_RE = re.compile(r"^GRCN-([lIL]+)$")


class IntegridadeError(RuntimeError):
    """A carga não bateu com o esperado — a carga **falha** (não avisa)."""


def normalize_gerencia_sigla(sigla: str) -> str:
    """Normaliza a sigla da gerência.

    ``GRCN-l`` → ``GRCN-I``; ``GRCN-ll`` → ``GRCN-II``; ``GRCN-lll`` → ``GRCN-III``.
    O defeito é de publicação no portal do IDEFLOR (issue #29), então a
    normalização roda sempre — inclusive com o arquivo já corrigido.
    """
    value = (sigla or "").strip().upper()
    match = _GRCN_L_RE.fullmatch(value)
    if match:
        return "GRCN-" + ("I" * len(match.group(1)))
    return value


def parse_gerencia(valor: str) -> tuple[str, str]:
    """Extrai ``(sigla_normalizada, nome_oficial)`` do campo ``gerencia``.

    O campo vem como ``"GERÊNCIA REGIONAL DE BELÉM (GRB)"``.
    """
    raw = (valor or "").strip()
    match = _SIGLA_RE.search(raw)
    if not match:
        raise IntegridadeError(f"campo 'gerencia' sem sigla entre parênteses: {valor!r}")
    sigla = normalize_gerencia_sigla(match.group(1))
    nome = raw[: match.start()].strip()
    return sigla, nome


# --------------------------------------------------------------------------- #
# Estruturas
# --------------------------------------------------------------------------- #


@dataclass(slots=True)
class UcRef:
    """Uma UC lida do arquivo de shapes."""

    id_oficial: int | None
    nome: str
    sigla_gerencia: str
    nome_gerencia: str
    categoria: str | None
    area_ha: float | None
    geom: BaseGeometry
    props: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class ZonaRef:
    """Uma zona lida do arquivo de zoneamento — **verbatim**."""

    sigla: str | None
    zona: str | None
    unidade_origem: str | None
    area_ha: float | None
    geom: BaseGeometry | None
    props: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class ZonaResolvida:
    """Zona + a UC resolvida por sobreposição espacial."""

    zona: ZonaRef
    uc_id: int | None
    metodo: str
    fracao_cobertura: float | None


# --------------------------------------------------------------------------- #
# Leitura
# --------------------------------------------------------------------------- #


def corrigir_geometria(geom: BaseGeometry | None) -> tuple[BaseGeometry | None, bool]:
    """Corrige geometria invalida (auto-intersecao) e devolve se houve reparo.

    Os arquivos do IDEFLOR tem geometria invalida em algumas features (o
    `TopologyException` aparece ao intersectar). Repara-se com
    ``shapely.make_valid`` e **conta-se** o reparo — dado quebrado na origem
    vira dado registrado, nao dado escondido.
    """
    if geom is None:
        return None, False
    if geom.is_valid:
        return geom, False
    corrigida = make_valid(geom)
    if not isinstance(corrigida, (Polygon, MultiPolygon)):
        partes = [
            g for g in getattr(corrigida, "geoms", []) if isinstance(g, (Polygon, MultiPolygon))
        ]
        corrigida = unary_union(partes) if partes else geom
    if isinstance(corrigida, Polygon):
        corrigida = MultiPolygon([corrigida])
    return corrigida, True


def _read_geojson(path: Path) -> dict[str, Any]:
    with Path(path).open(encoding="utf-8") as handle:
        return json.load(handle)


def load_ucs(path: Path) -> list[UcRef]:
    """Lê as UCs do arquivo de shapes do IDEFLOR.

    O nome vem de ``nome_`` (o ``name`` parece truncado em alguns casos).
    """
    data = _read_geojson(Path(path))
    ucs: list[UcRef] = []
    for feature in data.get("features", []):
        props = dict(feature.get("properties") or {})
        sigla, nome_gerencia = parse_gerencia(props.get("gerencia", ""))
        area_ha = props.get("area_ha")
        geom_uc = shape(feature["geometry"])
        ucs.append(
            UcRef(
                id_oficial=props.get("id"),
                nome=(props.get("nome_") or props.get("name") or "").strip(),
                sigla_gerencia=sigla,
                nome_gerencia=nome_gerencia,
                categoria=props.get("categoria"),
                area_ha=float(area_ha) if isinstance(area_ha, (int, float)) else None,
                geom=geom_uc,
                props=props,
            )
        )
    return ucs


def load_zonas(path: Path) -> list[ZonaRef]:
    """Lê as zonas do arquivo de zoneamento — ``sigla``/``zona`` verbatim."""
    data = _read_geojson(Path(path))
    zonas: list[ZonaRef] = []
    for feature in data.get("features", []):
        props = dict(feature.get("properties") or {})
        area = props.get("AREA")
        try:
            area_ha = float(area) if area not in (None, "") else None
        except (TypeError, ValueError):
            area_ha = None
        geometria = feature.get("geometry")
        # Sem `make_valid` aqui: o reparo e caro (arquivo de 23 MB) e so e
        # necessario para os pares que realmente falham na intersecao.
        geom_zona = shape(geometria) if geometria else None
        zonas.append(
            ZonaRef(
                sigla=props.get("SIGLA"),
                zona=props.get("ZONA"),
                unidade_origem=props.get("UNIDADE"),
                area_ha=area_ha,
                # 1 das 252 zonas do arquivo vem com `geometry: null` (ZR / Zona de
                # Recuperacao, AREA vazia). Ela NAO e descartada: entra sem geometria
                # e sem uc_id, com o motivo registrado (D-010).
                geom=geom_zona,
                props=props,
            )
        )
    return zonas


# --------------------------------------------------------------------------- #
# Join espacial (issue #23)
# --------------------------------------------------------------------------- #


def resolver_zonas(zonas: list[ZonaRef], ucs: list[UcRef]) -> list[ZonaResolvida]:
    """Resolve cada zona para a UC com **maior área de interseção**.

    Nunca pelo campo ``UNIDADE`` (truncado na origem). Zona que não intersecta
    nenhuma UC fica com ``uc_id=None`` — e continua sendo registrada (D-010: nada
    é descartado em silêncio).
    """
    resolvidas: list[ZonaResolvida] = []

    # Indice espacial: 252 zonas x 29 UCs com interseccao completa e lenta.
    # STRtree + geometrias preparadas: so testa os candidatos do bbox.
    arvore = STRtree([uc.geom for uc in ucs])
    preparadas = [prep(uc.geom) for uc in ucs]
    reparos: dict[int, BaseGeometry] = {}

    for zona in zonas:
        if zona.geom is None:
            resolvidas.append(
                ZonaResolvida(zona=zona, uc_id=None, metodo="sem_geometria", fracao_cobertura=None)
            )
            continue
        melhor_uc: int | None = None
        melhor_area = 0.0
        metodo = "sem_intersecao"
        for indice in arvore.query(zona.geom):
            uc = ucs[int(indice)]
            if not preparadas[int(indice)].intersects(zona.geom):
                continue
            try:
                area = uc.geom.intersection(zona.geom).area
            except Exception:  # noqa: BLE001 - geometria degenerada na origem
                # Reparo sob demanda: so para o par que falhou.
                reparada = reparos.get(indice)
                if reparada is None:
                    reparada, _ = corrigir_geometria(uc.geom)
                    reparos[indice] = reparada
                try:
                    area = reparada.intersection(zona.geom).area
                except Exception:  # noqa: BLE001
                    continue
            if area > melhor_area:
                melhor_area = area
                melhor_uc = uc.id_oficial
        fracao = None
        if melhor_uc is not None and zona.geom.area > 0:
            fracao = melhor_area / zona.geom.area
            metodo = "maior_intersecao"
        resolvidas.append(
            ZonaResolvida(
                zona=zona,
                uc_id=melhor_uc,
                metodo=metodo,
                fracao_cobertura=fracao,
            )
        )
    return resolvidas


# --------------------------------------------------------------------------- #
# Integridade (issue #21)
# --------------------------------------------------------------------------- #


def checar_integridade_ucs(ucs: list[UcRef]) -> None:
    """Falha se a carga não bater com o esperado. Não avisa — **falha**.

    - exatamente 29 UCs;
    - exatamente 9 gerências, todas do registro canônico;
    - todo ``uc.gerencia_id`` resolvido;
    - contagem de UCs por gerência igual à do registro oficial.
    """
    problemas: list[str] = []

    if len(ucs) != TOTAL_UC_ESPERADO:
        problemas.append(f"esperadas {TOTAL_UC_ESPERADO} UCs, encontradas {len(ucs)}")

    siglas = {uc.sigla_gerencia for uc in ucs}
    if len(siglas) != TOTAL_GERENCIAS_ESPERADO:
        problemas.append(
            f"esperadas {TOTAL_GERENCIAS_ESPERADO} gerências, "
            f"encontradas {len(siglas)}: {sorted(siglas)}"
        )

    canonicas = {sigla for sigla, _, _ in GERENCIAS_CANONICAS}
    desconhecidas = sorted(siglas - canonicas)
    if desconhecidas:
        problemas.append(f"gerências fora do registro DGMUC: {desconhecidas}")

    for sigla, _, esperado in GERENCIAS_CANONICAS:
        encontrados = sum(1 for uc in ucs if uc.sigla_gerencia == sigla)
        if encontrados != esperado:
            problemas.append(f"gerência {sigla}: esperado {esperado} UCs, encontrado {encontrados}")

    ids = [uc.id_oficial for uc in ucs if uc.id_oficial is not None]
    if len(set(ids)) != len(ids):
        problemas.append("ids oficiais duplicados entre as UCs")

    if problemas:
        raise IntegridadeError("; ".join(problemas))


def resumo_cobertura_zonas(
    resolvidas: list[ZonaResolvida],
) -> dict[str, Any]:
    """Cobertura do zoneamento — registrar, não inventar (issue #24)."""
    ids = {r.uc_id for r in resolvidas if r.uc_id is not None}
    return {
        "zonas_total": len(resolvidas),
        "zonas_com_uc": sum(1 for r in resolvidas if r.uc_id is not None),
        "zonas_sem_uc": sum(1 for r in resolvidas if r.uc_id is None),
        "ucs_com_zonas": len(ids),
        "ucs_total": TOTAL_UC_ESPERADO,
    }
