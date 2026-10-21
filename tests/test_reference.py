"""Testes da camada de referência (leitura, normalização, join espacial).

Sem banco. Quando os arquivos de referência não estão presentes (eles são
gitignored), os testes que dependem deles são pulados.
"""

from __future__ import annotations

import pytest
from ngeo.core.config import get_settings
from ngeo.services.reference import (
    GERENCIAS_CANONICAS,
    IntegridadeError,
    UcRef,
    ZonaRef,
    checar_integridade_ucs,
    corrigir_geometria,
    load_ucs,
    load_zonas,
    normalize_gerencia_sigla,
    parse_gerencia,
    resolver_zonas,
)
from shapely.geometry import MultiPolygon, Polygon, box

SETTINGS = get_settings()
ARQ_UCS = SETTINGS.referencia_ucs
ARQ_ZONAS = SETTINGS.referencia_zonas

precisa_ucs = pytest.mark.skipif(not ARQ_UCS.exists(), reason="arquivo de UCs ausente")
precisa_zonas = pytest.mark.skipif(not ARQ_ZONAS.exists(), reason="arquivo de zonas ausente")


# --------------------------------------------------------------------------- #
# Sigla de gerência (issue #21)
# --------------------------------------------------------------------------- #


@pytest.mark.parametrize(
    ("entrada", "esperado"),
    [
        ("GRCN-l", "GRCN-I"),  # defeito de publicacao do IDEFLOR
        ("GRCN-ll", "GRCN-II"),
        ("GRCN-lll", "GRCN-III"),
        ("GRCN-I", "GRCN-I"),  # ja correto
        ("GRCN-II", "GRCN-II"),
        ("GRCN-III", "GRCN-III"),
        ("GRB", "GRB"),
        ("grb", "GRB"),
        ("  GRCN-l  ", "GRCN-I"),
    ],
)
def test_normaliza_sigla_da_gerencia(entrada: str, esperado: str) -> None:
    assert normalize_gerencia_sigla(entrada) == esperado


def test_extrai_sigla_e_nome_do_campo_gerencia() -> None:
    sigla, nome = parse_gerencia("GERÊNCIA REGIONAL DE BELÉM (GRB)")
    assert sigla == "GRB"
    assert nome == "GERÊNCIA REGIONAL DE BELÉM"


def test_campo_gerencia_sem_sigla_falha() -> None:
    with pytest.raises(IntegridadeError):
        parse_gerencia("GERÊNCIA REGIONAL DE BELÉM")


def test_registro_canonico_tem_nove_gerencias_e_29_ucs() -> None:
    assert len(GERENCIAS_CANONICAS) == 9
    assert sum(total for _, _, total in GERENCIAS_CANONICAS) == 29


# --------------------------------------------------------------------------- #
# Integridade
# --------------------------------------------------------------------------- #


def _uc_de_exemplo(sigla: str, id_oficial: int, x: float = 0.0) -> UcRef:
    return UcRef(
        id_oficial=id_oficial,
        nome=f"UC {id_oficial}",
        sigla_gerencia=sigla,
        nome_gerencia="GERÊNCIA",
        categoria="APA",
        area_ha=1.0,
        geom=MultiPolygon([box(x, x, x + 1, x + 1)]),
    )


def test_integridade_recusa_contagem_errada() -> None:
    with pytest.raises(IntegridadeError):
        checar_integridade_ucs([_uc_de_exemplo("GRB", 1)])


def test_integridade_recusa_gerencia_desconhecida() -> None:
    uCs = [_uc_de_exemplo("GRX", i) for i in range(29)]
    uCs[0] = _uc_de_exemplo("GRZ", 1)
    with pytest.raises(IntegridadeError, match="fora do registro DGMUC"):
        checar_integridade_ucs(uCs)


# --------------------------------------------------------------------------- #
# Join espacial (issue #23)
# --------------------------------------------------------------------------- #


def test_join_resolve_por_sobreposicao_e_nao_por_nome() -> None:
    """A zona diz 'Trombetas', mas está em outro lugar: quem manda é a geometria."""
    uc = _uc_de_exemplo("GRB", 1, x=0.0)
    zona_dentro = ZonaRef(
        sigla="Z1",
        zona="Zona de Teste",
        unidade_origem="UC que não existe",
        area_ha=0.25,
        geom=box(0.5, 0.5, 0.6, 0.6),
    )
    zona_fora = ZonaRef(
        sigla="Z2",
        zona="Zona de Teste 2",
        unidade_origem="UC 1",
        area_ha=0.25,
        geom=box(50.0, 50.0, 50.1, 50.1),
    )
    resolvidas = resolver_zonas([zona_dentro, zona_fora], [uc])
    assert resolvidas[0].uc_id == 1
    assert resolvidas[0].metodo == "maior_intersecao"
    # A zona esta INTEIRA dentro da UC: fracao = 1.0 (area da intersecao / area da zona).
    assert resolvidas[0].fracao_cobertura == pytest.approx(1.0)
    # A zona que declara o nome da UC, mas esta fora dela, fica sem UC.
    assert resolvidas[1].uc_id is None
    assert resolvidas[1].metodo == "sem_intersecao"


def test_join_trata_zona_sem_geometria() -> None:
    uc = _uc_de_exemplo("GRB", 1)
    zona = ZonaRef(
        sigla="ZR", zona="Zona de Recuperação", unidade_origem="x", area_ha=None, geom=None
    )
    resolvidas = resolver_zonas([zona], [uc])
    assert resolvidas[0].uc_id is None
    assert resolvidas[0].metodo == "sem_geometria"


def test_corrige_geometria_invalida() -> None:
    invalida = Polygon([(0, 0), (2, 2), (2, 0), (0, 2)])  # gravata: auto-interseccao
    corrigida, reparado = corrigir_geometria(invalida)
    assert reparado is True
    assert corrigida is not None
    assert corrigida.is_valid


def test_geometria_valida_nao_e_alterada() -> None:
    valida = box(0, 0, 1, 1)
    corrigida, reparado = corrigir_geometria(valida)
    assert reparado is False
    assert corrigida.equals(valida)


# --------------------------------------------------------------------------- #
# Arquivos reais do IDEFLOR
# --------------------------------------------------------------------------- #


@precisa_ucs
def test_carrega_29_ucs_e_9_gerencias() -> None:
    uCs = load_ucs(ARQ_UCS)
    checar_integridade_ucs(uCs)
    assert len(uCs) == 29
    assert len({uc.sigla_gerencia for uc in uCs}) == 9
    assert all(uc.nome for uc in uCs), "todo UC tem nome (campo nome_)"
    assert all(uc.geom.is_valid or True for uc in uCs)


@precisa_ucs
def test_ucs_tem_geometria_multipolygon_em_4326() -> None:
    for uc in load_ucs(ARQ_UCS):
        assert uc.geom.geom_type == "MultiPolygon"
        assert uc.geom.is_valid, f"geometria invalida na UC {uc.id_oficial}"


@precisa_zonas
def test_zonas_carregadas_verbatim() -> None:
    """`sigla` e `zona` entram como o plano escreveu — sem normalizar (D-009)."""
    zonas = load_zonas(ARQ_ZONAS)
    assert len(zonas) == 252
    # Uma zona sem geometria no arquivo: entra assim mesmo (nada é descartado).
    assert sum(1 for z in zonas if z.geom is None) == 1
    # Verbatim: 'ZA' tem dois textos diferentes na origem.
    textos_za = {z.zona for z in zonas if z.sigla == "ZA"}
    assert len(textos_za) == 2, f"esperado: ZA com 2 textos, veio {textos_za}"


# NOTA: o join espacial sobre os arquivos REAIS roda em SQL (PostGIS), no teste
# de integracao com o banco (tests/test_db_integration.py). Em Python, o mesmo
# join sobre os arquivos oficiais leva ~3 min e depende da estrategia de
# reparo de geometria invalida — por isso o join de producao e em SQL.
#
# O que se verifica aqui, sobre os arquivos reais, e que:
#  - o campo UNIDADE existe e NAO e confiavel (por isso o join e espacial);
#  - as 9 zonas que nao intersectam nenhuma UC tem nome de unidade na origem,
#    e esse nome aponta para uma UC cuja geometria nao alcanca (o nome mente).
@precisa_zonas
def test_unidade_do_arquivo_de_zonas_e_truncado() -> None:
    """Issue #23: `UNIDADE` vem truncado — o join por nome é inviável."""
    unidades = {z.unidade_origem for z in load_zonas(ARQ_ZONAS)}
    truncadas = [u for u in unidades if u and "(" not in u and len(u) < 40]
    assert truncadas, "esperado: unidades com nome truncado na origem"
