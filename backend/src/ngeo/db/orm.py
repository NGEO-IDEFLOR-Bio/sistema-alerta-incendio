"""Modelos ORM do schema canônico (PLANO_ARQUITETURA.md §5).

Fonte da verdade: `PLANO_ARQUITETURA.md` §5 (revisado em 21/10/2026 — T0/D-014).
Nada aqui interpreta o zoneamento do plano de gestão: as zonas entram
**verbatim** (D-009).
"""

from __future__ import annotations

import datetime as dt
from typing import Any
from uuid import uuid4

from geoalchemy2 import Geometry
from sqlalchemy import (
    Boolean,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import ARRAY, JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ngeo.db.base import Base

# --------------------------------------------------------------------------- #
# Referência institucional
# --------------------------------------------------------------------------- #


class GerenciaRegional(Base):
    """As 9 Gerências Regionais (DGMUC). Fonte: portal IDEFLOR-Bio."""

    __tablename__ = "gerencias_regionais"

    id: Mapped[str] = mapped_column(String(32), primary_key=True)
    nome: Mapped[str] = mapped_column(Text, nullable=False)
    ativa: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    ucs: Mapped[list[Uc]] = relationship(back_populates="gerencia")


class Uc(Base):
    """Unidade de Conservação estadual (29)."""

    __tablename__ = "ucs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    #: `id` sequencial do arquivo oficial do IDEFLOR (1..29) — preservado.
    id_oficial: Mapped[int | None] = mapped_column(Integer, nullable=True, index=True)
    nome: Mapped[str] = mapped_column(Text, nullable=False)
    categoria: Mapped[str | None] = mapped_column(String(32), nullable=True)
    area_ha: Mapped[float | None] = mapped_column(Float, nullable=True)
    gerencia_id: Mapped[str] = mapped_column(
        String(32), ForeignKey("gerencias_regionais.id"), nullable=False, index=True
    )
    geom: Mapped[Any | None] = mapped_column(
        Geometry("MULTIPOLYGON", srid=4326, spatial_index=True)
    )
    zona_amortecimento: Mapped[Any | None] = mapped_column(
        Geometry("MULTIPOLYGON", srid=4326, spatial_index=True)
    )
    props: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False, default=dict)

    gerencia: Mapped[GerenciaRegional] = relationship(back_populates="ucs")
    zonas: Mapped[list[UcZona]] = relationship(back_populates="uc")


class UcZona(Base):
    """Zona de plano de gestão — **VERBATIM** (D-009).

    `sigla` NÃO é global (`ZA` = duas coisas diferentes em planos diferentes) e
    nunca é chave de regra. `uc_id` é resolvido por **sobreposição espacial**
    (issue #23), nunca pelo campo `UNIDADE` (truncado na origem).
    """

    __tablename__ = "ucs_zonas"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    uc_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("ucs.id", ondelete="SET NULL"), nullable=True, index=True
    )
    #: Código original do zoneamento, como o plano escreveu.
    sigla: Mapped[str | None] = mapped_column(Text, nullable=True)
    #: Texto original do plano.
    zona: Mapped[str | None] = mapped_column(Text, nullable=True)
    #: Nome da unidade **como veio no arquivo** (truncado na origem) — auditável.
    unidade_origem: Mapped[str | None] = mapped_column(Text, nullable=True)
    area_ha: Mapped[float | None] = mapped_column(Float, nullable=True)
    #: Auditoria do join espacial: metodo aplicado e quantas UCs a zona toca.
    #: Uma zona que toca varias UCs e um mosaico — e precisa de revisao.
    join_metodo: Mapped[str | None] = mapped_column(String(32), nullable=True)
    join_n_candidatas: Mapped[int | None] = mapped_column(Integer, nullable=True)
    # GEOMETRY (e nao POLYGON): 44 das 252 zonas do arquivo sao MultiPolygon.
    geom: Mapped[Any | None] = mapped_column(Geometry("GEOMETRY", srid=4326, spatial_index=True))

    uc: Mapped[Uc | None] = relationship(back_populates="zonas")


# --------------------------------------------------------------------------- #
# Detecção
# --------------------------------------------------------------------------- #


class FocoGrupo(Base):
    """**Um fogo** visto por 1 ou mais sensores (D-013).

    As leituras continuam todas em `focos`; o grupo é a ligação. Nada é apagado
    (D-010).
    """

    __tablename__ = "focos_grupos"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    geom: Mapped[Any | None] = mapped_column(Geometry("POINT", srid=4326, spatial_index=True))
    leitura_representante_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("focos.id"), nullable=True
    )
    n_leituras: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    sensores: Mapped[list[str]] = mapped_column(ARRAY(Text), nullable=False, default=list)
    primeira_hora: Mapped[dt.datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    ultima_hora: Mapped[dt.datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    frp_max: Mapped[float | None] = mapped_column(Numeric, nullable=True)
    frp_acumulado: Mapped[float | None] = mapped_column(Numeric, nullable=True)
    confianca: Mapped[str | None] = mapped_column(String(16), nullable=True)
    derivacao: Mapped[str] = mapped_column(Text, nullable=False, default="dedup_v1")

    # Dois caminhos de FK entre `focos` e `focos_grupos` (grupo_id e
    # leitura_representante_id) — o caminho precisa ser explicito.
    focos: Mapped[list[Foco]] = relationship(back_populates="grupo", foreign_keys="Foco.grupo_id")


class Foco(Base):
    """Uma **leitura de sensor**. O mesmo fogo visto por 2 sensores = 2 linhas."""

    __tablename__ = "focos"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    fonte: Mapped[str] = mapped_column(String(32), nullable=False, index=True)
    produto: Mapped[str] = mapped_column(String(48), nullable=False, index=True)
    sensor: Mapped[str | None] = mapped_column(String(16), nullable=True)
    satelite: Mapped[str | None] = mapped_column(String(24), nullable=True)
    satelite_codigo: Mapped[str | None] = mapped_column(String(16), nullable=True)
    versao_produto: Mapped[str | None] = mapped_column(String(16), nullable=True)
    acquisition_time: Mapped[dt.datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, index=True
    )
    lat: Mapped[float] = mapped_column(Float, nullable=False)
    lon: Mapped[float] = mapped_column(Float, nullable=False)
    geom: Mapped[Any] = mapped_column(
        Geometry("POINT", srid=4326, spatial_index=True), nullable=False
    )
    bright_ti_k: Mapped[float | None] = mapped_column(Float, nullable=True)
    bright_ti_banda: Mapped[str | None] = mapped_column(String(16), nullable=True)
    bright_ti2_k: Mapped[float | None] = mapped_column(Float, nullable=True)
    bright_ti2_banda: Mapped[str | None] = mapped_column(String(16), nullable=True)
    frp_mw: Mapped[float | None] = mapped_column(Numeric, nullable=True)
    confianca: Mapped[str | None] = mapped_column(String(16), nullable=True)
    confianca_crua: Mapped[str | None] = mapped_column(String(8), nullable=True)
    dia_noite: Mapped[str | None] = mapped_column(String(2), nullable=True)
    scan_angle: Mapped[float | None] = mapped_column(Float, nullable=True)
    track_angle: Mapped[float | None] = mapped_column(Float, nullable=True)
    raio_pixel_m: Mapped[float] = mapped_column(Float, nullable=False)
    posicao_terreno_corrigida: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    grupo_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("focos_grupos.id", use_alter=True), nullable=True, index=True
    )
    raw: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False, default=dict)
    criado_em: Mapped[dt.datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    grupo: Mapped[FocoGrupo | None] = relationship(back_populates="focos", foreign_keys=[grupo_id])


class EventoFogo(Base):
    """Agrupamento espacial-temporal de focos = ocorrência de fogo.

    Agregação, **não** máquina de estados (D-003).
    """

    __tablename__ = "eventos_fogo"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    geom_centro: Mapped[Any] = mapped_column(Geometry("POINT", srid=4326, spatial_index=True))
    bbox: Mapped[Any | None] = mapped_column(Geometry("POLYGON", srid=4326, spatial_index=True))
    n_focos: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    n_leituras: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    fontes: Mapped[list[str]] = mapped_column(ARRAY(Text), nullable=False, default=list)
    sensores: Mapped[list[str]] = mapped_column(ARRAY(Text), nullable=False, default=list)
    primeira_hora: Mapped[dt.datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    ultima_hora: Mapped[dt.datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    frp_max: Mapped[float | None] = mapped_column(Numeric, nullable=True)
    frp_acumulado: Mapped[float | None] = mapped_column(Numeric, nullable=True)
    raio_estimado_m: Mapped[float | None] = mapped_column(Float, nullable=True)
    uc_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("ucs.id"), nullable=True, index=True
    )
    distancia_uc_m: Mapped[float | None] = mapped_column(Float, nullable=True)
    derivacao: Mapped[str] = mapped_column(Text, nullable=False, default="cluster_v1")

    alertas: Mapped[list[Alerta]] = relationship(back_populates="evento")


# --------------------------------------------------------------------------- #
# Alerta e entrega
# --------------------------------------------------------------------------- #


class Alerta(Base):
    """Registro **imutável** do que foi notificado (D-003).

    Sempre emitido quando o evento toca uma UC (D-010). A incerteza é
    declarada, nunca escondida por supressão.
    """

    __tablename__ = "alertas"

    id: Mapped[Any] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    evento_fogo_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("eventos_fogo.id"), nullable=True, index=True
    )
    tipo: Mapped[str] = mapped_column(String(32), nullable=False, index=True)
    gerencia_id: Mapped[str] = mapped_column(String(32), nullable=False, index=True)
    uc_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("ucs.id"), nullable=True)
    uc_nome: Mapped[str | None] = mapped_column(Text, nullable=True)
    severidade: Mapped[str] = mapped_column(String(16), nullable=False, index=True)
    confianca: Mapped[str] = mapped_column(String(16), nullable=False)
    possivel_falso_positivo: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    n_focos: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    fontes_concordantes: Mapped[list[str]] = mapped_column(
        ARRAY(Text), nullable=False, default=list
    )
    # Contexto do plano de gestão — VERBATIM, pode ser nulo (D-009/D-011).
    zona_sigla: Mapped[str | None] = mapped_column(Text, nullable=True)
    zona_texto: Mapped[str | None] = mapped_column(Text, nullable=True)
    zona_disponivel: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    regra_id: Mapped[str] = mapped_column(Text, nullable=False)
    titulo: Mapped[str] = mapped_column(Text, nullable=False)
    mensagem: Mapped[str] = mapped_column(Text, nullable=False)
    geom: Mapped[Any | None] = mapped_column(Geometry("GEOMETRY", srid=4326, spatial_index=True))
    janela_ini: Mapped[dt.datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    janela_fim: Mapped[dt.datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    gerado_em: Mapped[dt.datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    evento: Mapped[EventoFogo | None] = relationship(back_populates="alertas")
    entregas: Mapped[list[Entrega]] = relationship(back_populates="alerta")


class Entrega(Base):
    """Log de envio — append-only (PLANO §5.4)."""

    __tablename__ = "entregas"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    alerta_id: Mapped[Any] = mapped_column(
        UUID(as_uuid=True), ForeignKey("alertas.id"), nullable=False, index=True
    )
    canal: Mapped[str] = mapped_column(String(24), nullable=False)
    destinatario: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(String(16), nullable=False)
    resposta_http: Mapped[int | None] = mapped_column(Integer, nullable=True)
    erro: Mapped[str | None] = mapped_column(Text, nullable=True)
    enviado_em: Mapped[dt.datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    alerta: Mapped[Alerta] = relationship(back_populates="entregas")


class ConfigAlerta(Base):
    """Protocolo por Gerência Regional — versionado (D-003)."""

    __tablename__ = "config_alerta"
    __table_args__ = (
        UniqueConstraint("gerencia_id", "tipo_alerta", "canal", name="uq_config_alerta"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    gerencia_id: Mapped[str] = mapped_column(String(32), nullable=False, index=True)
    tipo_alerta: Mapped[str] = mapped_column(String(32), nullable=False)
    severidade_min: Mapped[str] = mapped_column(String(16), nullable=False)
    raio_buffer_m: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    janela_h: Mapped[int] = mapped_column(Integer, nullable=False, default=6)
    canal: Mapped[str] = mapped_column(String(24), nullable=False)
    destinatarios: Mapped[list[str]] = mapped_column(ARRAY(Text), nullable=False, default=list)
    ativo: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    template: Mapped[dict[str, Any] | None] = mapped_column(JSONB, nullable=True)


# --------------------------------------------------------------------------- #
# Proveniência
# --------------------------------------------------------------------------- #


class Fonte(Base):
    """Fonte de focos: resolução, latência, termos, atribuição, pin de versão."""

    __tablename__ = "fontes"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    fonte: Mapped[str] = mapped_column(String(32), nullable=False, unique=True)
    nome: Mapped[str] = mapped_column(Text, nullable=False)
    produto: Mapped[str | None] = mapped_column(String(48), nullable=True)
    resolucao_m: Mapped[float | None] = mapped_column(Float, nullable=True)
    latencia_horas: Mapped[float | None] = mapped_column(Float, nullable=True)
    intervalo_minutos: Mapped[int | None] = mapped_column(Integer, nullable=True)
    url: Mapped[str | None] = mapped_column(Text, nullable=True)
    termos_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    atribuicao_requerida: Mapped[str | None] = mapped_column(Text, nullable=True)
    licenca: Mapped[str | None] = mapped_column(Text, nullable=True)
    chave_requerida: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    versao_produto_atual: Mapped[str | None] = mapped_column(String(24), nullable=True)
    ativo: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    observacao: Mapped[str | None] = mapped_column(Text, nullable=True)


class ParametroDedup(Base):
    """Parâmetros de dedup/cluster — configuráveis e versionados (D-013)."""

    __tablename__ = "parametros_dedup"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    chave: Mapped[str] = mapped_column(String(48), primary_key=True)
    valor: Mapped[float] = mapped_column(Numeric, nullable=False)
    justificativa: Mapped[str | None] = mapped_column(Text, nullable=True)
    atualizado_em: Mapped[dt.datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )


#: Índices adicionais declarados no PLANO §5.
Index(
    "ix_focos_produto_satelite_leitura", Foco.produto, Foco.satelite_codigo, Foco.acquisition_time
)
Index("ix_eventos_fogo_janela", EventoFogo.primeira_hora, EventoFogo.ultima_hora)
