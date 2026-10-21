"""F1 — schema canônico (PLANO_ARQUITETURA.md §5)

Revision ID: 20261021_0001
Revises:
Create Date: 2026-10-21

"""

from __future__ import annotations

from collections.abc import Sequence

import geoalchemy2
import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "20261021_0001"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # --- extensão PostGIS -------------------------------------------------
    op.execute("CREATE EXTENSION IF NOT EXISTS postgis")

    # A imagem `postgis/postgis` instala `postgis_tiger_geocoder` por padrao.
    # Ele cria o schema `tiger` e o poe no search_path, com tabelas de nome
    # generico (`bg`, `county`, `edges`, `tract`...) — nada disso faz parte do
    # nosso schema (PLANO §5) e e risco de resolver o nome errado. A
    # normalizacao e feita aqui (e nao por bind mount) porque o repo vive no
    # `H:\Meu Drive`, de onde o Docker nao consegue montar arquivo
    # (BUILD.md, armadilha 3).
    op.execute("DROP EXTENSION IF EXISTS postgis_tiger_geocoder CASCADE")

    # --- 5.6 Referência institucional -------------------------------------
    op.create_table(
        "gerencias_regionais",
        sa.Column("id", sa.String(length=32), primary_key=True),
        sa.Column("nome", sa.Text(), nullable=False),
        sa.Column("ativa", sa.Boolean(), nullable=False, server_default=sa.true()),
    )
    op.create_table(
        "ucs",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("id_oficial", sa.Integer(), nullable=True),
        sa.Column("nome", sa.Text(), nullable=False),
        sa.Column("categoria", sa.String(length=32), nullable=True),
        sa.Column("area_ha", sa.Float(), nullable=True),
        sa.Column(
            "gerencia_id",
            sa.String(length=32),
            sa.ForeignKey("gerencias_regionais.id"),
            nullable=False,
        ),
        sa.Column(
            "geom",
            geoalchemy2.types.Geometry(
                geometry_type="MULTIPOLYGON", srid=4326, spatial_index=False
            ),
            nullable=True,
        ),
        sa.Column(
            "zona_amortecimento",
            geoalchemy2.types.Geometry(
                geometry_type="MULTIPOLYGON", srid=4326, spatial_index=False
            ),
            nullable=True,
        ),
        sa.Column("props", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
    )
    op.create_index("ix_ucs_id_oficial", "ucs", ["id_oficial"])
    op.create_index("ix_ucs_gerencia_id", "ucs", ["gerencia_id"])
    op.create_index("ix_ucs_geom", "ucs", ["geom"], postgresql_using="gist")

    # --- 5.7 Zonas (VERBATIM — D-009) -------------------------------------
    op.create_table(
        "ucs_zonas",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column(
            "uc_id",
            sa.Integer(),
            sa.ForeignKey("ucs.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("sigla", sa.Text(), nullable=True),
        sa.Column("zona", sa.Text(), nullable=True),
        sa.Column("unidade_origem", sa.Text(), nullable=True),
        sa.Column("area_ha", sa.Float(), nullable=True),
        sa.Column("join_metodo", sa.String(length=32), nullable=True),
        sa.Column("join_n_candidatas", sa.Integer(), nullable=True),
        sa.Column(
            "geom",
            geoalchemy2.types.Geometry(geometry_type="GEOMETRY", srid=4326, spatial_index=False),
            nullable=True,
        ),
    )
    op.create_index("ix_ucs_zonas_uc_id", "ucs_zonas", ["uc_id"])
    op.create_index("ix_ucs_zonas_geom", "ucs_zonas", ["geom"], postgresql_using="gist")

    # --- 5.1 Focos ---------------------------------------------------------
    op.create_table(
        "focos",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("fonte", sa.String(length=32), nullable=False),
        sa.Column("produto", sa.String(length=48), nullable=False),
        sa.Column("sensor", sa.String(length=16), nullable=True),
        sa.Column("satelite", sa.String(length=24), nullable=True),
        sa.Column("satelite_codigo", sa.String(length=16), nullable=True),
        sa.Column("versao_produto", sa.String(length=16), nullable=True),
        sa.Column("acquisition_time", sa.DateTime(timezone=True), nullable=False),
        sa.Column("lat", sa.Float(), nullable=False),
        sa.Column("lon", sa.Float(), nullable=False),
        sa.Column(
            "geom",
            geoalchemy2.types.Geometry(geometry_type="POINT", srid=4326, spatial_index=False),
            nullable=False,
        ),
        sa.Column("bright_ti_k", sa.Float(), nullable=True),
        sa.Column("bright_ti_banda", sa.String(length=16), nullable=True),
        sa.Column("bright_ti2_k", sa.Float(), nullable=True),
        sa.Column("bright_ti2_banda", sa.String(length=16), nullable=True),
        sa.Column("frp_mw", sa.Numeric(), nullable=True),
        sa.Column("confianca", sa.String(length=16), nullable=True),
        sa.Column("confianca_crua", sa.String(length=8), nullable=True),
        sa.Column("dia_noite", sa.String(length=2), nullable=True),
        sa.Column("scan_angle", sa.Float(), nullable=True),
        sa.Column("track_angle", sa.Float(), nullable=True),
        sa.Column("raio_pixel_m", sa.Float(), nullable=False),
        sa.Column(
            "posicao_terreno_corrigida", sa.Boolean(), nullable=False, server_default=sa.true()
        ),
        # FK circular (focos <-> focos_grupos): criada depois, com
        # op.create_foreign_key, quando as duas tabelas existirem.
        sa.Column("grupo_id", sa.Integer(), nullable=True),
        sa.Column("raw", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column(
            "criado_em", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
    )
    op.create_index("ix_focos_fonte", "focos", ["fonte"])
    op.create_index("ix_focos_produto", "focos", ["produto"])
    op.create_index("ix_focos_acquisition_time", "focos", ["acquisition_time"])
    op.create_index("ix_focos_grupo_id", "focos", ["grupo_id"])
    op.create_index("ix_focos_geom", "focos", ["geom"], postgresql_using="gist")
    # Idempotência de ingestão: mesma leitura não entra duas vezes (D-013, nível 1)
    op.create_index(
        "uq_focos_leitura",
        "focos",
        [
            "produto",
            "satelite_codigo",
            "acquisition_time",
            "scan_angle",
            "track_angle",
            "lat",
            "lon",
        ],
        unique=True,
    )

    # --- 5.10 Grupos de dedup (D-013) -------------------------------------
    op.create_table(
        "focos_grupos",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column(
            "geom",
            geoalchemy2.types.Geometry(geometry_type="POINT", srid=4326, spatial_index=False),
            nullable=True,
        ),
        sa.Column(
            "leitura_representante_id",
            sa.Integer(),
            sa.ForeignKey("focos.id"),
            nullable=True,
        ),
        sa.Column("n_leituras", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("sensores", postgresql.ARRAY(sa.Text()), nullable=False),
        sa.Column("primeira_hora", sa.DateTime(timezone=True), nullable=False),
        sa.Column("ultima_hora", sa.DateTime(timezone=True), nullable=False),
        sa.Column("frp_max", sa.Numeric(), nullable=True),
        sa.Column("frp_acumulado", sa.Numeric(), nullable=True),
        sa.Column("confianca", sa.String(length=16), nullable=True),
        sa.Column("derivacao", sa.Text(), nullable=False, server_default="dedup_v1"),
    )
    op.create_index("ix_focos_grupos_geom", "focos_grupos", ["geom"], postgresql_using="gist")

    # Fecha o ciclo: focos.grupo_id -> focos_grupos.id
    op.create_foreign_key(
        "fk_focos_grupo_id_focos_grupos", "focos", "focos_grupos", ["grupo_id"], ["id"]
    )

    # --- 5.2 Eventos de fogo ----------------------------------------------
    op.create_table(
        "eventos_fogo",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column(
            "geom_centro",
            geoalchemy2.types.Geometry(geometry_type="POINT", srid=4326, spatial_index=False),
            nullable=True,
        ),
        sa.Column(
            "bbox",
            geoalchemy2.types.Geometry(geometry_type="POLYGON", srid=4326, spatial_index=False),
            nullable=True,
        ),
        sa.Column("n_focos", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("n_leituras", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("fontes", postgresql.ARRAY(sa.Text()), nullable=False),
        sa.Column("sensores", postgresql.ARRAY(sa.Text()), nullable=False),
        sa.Column("primeira_hora", sa.DateTime(timezone=True), nullable=False),
        sa.Column("ultima_hora", sa.DateTime(timezone=True), nullable=False),
        sa.Column("frp_max", sa.Numeric(), nullable=True),
        sa.Column("frp_acumulado", sa.Numeric(), nullable=True),
        sa.Column("raio_estimado_m", sa.Float(), nullable=True),
        sa.Column("uc_id", sa.Integer(), sa.ForeignKey("ucs.id"), nullable=True),
        sa.Column("distancia_uc_m", sa.Float(), nullable=True),
        sa.Column("derivacao", sa.Text(), nullable=False, server_default="cluster_v1"),
    )
    op.create_index("ix_eventos_fogo_uc_id", "eventos_fogo", ["uc_id"])
    op.create_index(
        "ix_eventos_fogo_geom_centro", "eventos_fogo", ["geom_centro"], postgresql_using="gist"
    )
    op.create_index("ix_eventos_fogo_janela", "eventos_fogo", ["primeira_hora", "ultima_hora"])

    # --- 5.3 Alertas (imutáveis — D-003) ----------------------------------
    op.create_table(
        "alertas",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("evento_fogo_id", sa.Integer(), sa.ForeignKey("eventos_fogo.id"), nullable=True),
        sa.Column("tipo", sa.String(length=32), nullable=False),
        sa.Column("gerencia_id", sa.String(length=32), nullable=False),
        sa.Column("uc_id", sa.Integer(), sa.ForeignKey("ucs.id"), nullable=True),
        sa.Column("uc_nome", sa.Text(), nullable=True),
        sa.Column("severidade", sa.String(length=16), nullable=False),
        sa.Column("confianca", sa.String(length=16), nullable=False),
        sa.Column(
            "possivel_falso_positivo", sa.Boolean(), nullable=False, server_default=sa.false()
        ),
        sa.Column("n_focos", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("fontes_concordantes", postgresql.ARRAY(sa.Text()), nullable=False),
        sa.Column("zona_sigla", sa.Text(), nullable=True),
        sa.Column("zona_texto", sa.Text(), nullable=True),
        sa.Column("zona_disponivel", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("regra_id", sa.Text(), nullable=False),
        sa.Column("titulo", sa.Text(), nullable=False),
        sa.Column("mensagem", sa.Text(), nullable=False),
        sa.Column(
            "geom",
            geoalchemy2.types.Geometry(geometry_type="GEOMETRY", srid=4326, spatial_index=False),
            nullable=True,
        ),
        sa.Column("janela_ini", sa.DateTime(timezone=True), nullable=True),
        sa.Column("janela_fim", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "gerado_em", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
    )
    op.create_index("ix_alertas_tipo", "alertas", ["tipo"])
    op.create_index("ix_alertas_gerencia_id", "alertas", ["gerencia_id"])
    op.create_index("ix_alertas_severidade", "alertas", ["severidade"])
    op.create_index("ix_alertas_uc_id", "alertas", ["uc_id"])
    op.create_index("ix_alertas_evento_fogo_id", "alertas", ["evento_fogo_id"])
    op.create_index("ix_alertas_geom", "alertas", ["geom"], postgresql_using="gist")

    # --- 5.4 Entregas (append-only) ---------------------------------------
    op.create_table(
        "entregas",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column(
            "alerta_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("alertas.id"),
            nullable=False,
        ),
        sa.Column("canal", sa.String(length=24), nullable=False),
        sa.Column("destinatario", sa.Text(), nullable=False),
        sa.Column("status", sa.String(length=16), nullable=False),
        sa.Column("resposta_http", sa.Integer(), nullable=True),
        sa.Column("erro", sa.Text(), nullable=True),
        sa.Column(
            "enviado_em", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
    )
    op.create_index("ix_entregas_alerta_id", "entregas", ["alerta_id"])

    # --- 5.5 Configuração por gerência ------------------------------------
    op.create_table(
        "config_alerta",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("gerencia_id", sa.String(length=32), nullable=False),
        sa.Column("tipo_alerta", sa.String(length=32), nullable=False),
        sa.Column("severidade_min", sa.String(length=16), nullable=False),
        sa.Column("raio_buffer_m", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("janela_h", sa.Integer(), nullable=False, server_default="6"),
        sa.Column("canal", sa.String(length=24), nullable=False),
        sa.Column("destinatarios", postgresql.ARRAY(sa.Text()), nullable=False),
        sa.Column("ativo", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("template", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.UniqueConstraint("gerencia_id", "tipo_alerta", "canal", name="uq_config_alerta"),
    )
    op.create_index("ix_config_alerta_gerencia_id", "config_alerta", ["gerencia_id"])

    # --- 5.11 Fontes -------------------------------------------------------
    op.create_table(
        "fontes",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("fonte", sa.String(length=32), nullable=False, unique=True),
        sa.Column("nome", sa.Text(), nullable=False),
        sa.Column("produto", sa.String(length=48), nullable=True),
        sa.Column("resolucao_m", sa.Float(), nullable=True),
        sa.Column("latencia_horas", sa.Float(), nullable=True),
        sa.Column("intervalo_minutos", sa.Integer(), nullable=True),
        sa.Column("url", sa.Text(), nullable=True),
        sa.Column("termos_url", sa.Text(), nullable=True),
        sa.Column("atribuicao_requerida", sa.Text(), nullable=True),
        sa.Column("licenca", sa.Text(), nullable=True),
        sa.Column("chave_requerida", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("versao_produto_atual", sa.String(length=24), nullable=True),
        sa.Column("ativo", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("observacao", sa.Text(), nullable=True),
    )

    # --- 5.12 Parâmetros de dedup -----------------------------------------
    op.create_table(
        "parametros_dedup",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("chave", sa.String(length=48), primary_key=True),
        sa.Column("valor", sa.Numeric(), nullable=False),
        sa.Column("justificativa", sa.Text(), nullable=True),
        sa.Column(
            "atualizado_em",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
    )


def downgrade() -> None:
    op.drop_table("parametros_dedup")
    op.drop_table("fontes")
    op.drop_index("ix_config_alerta_gerencia_id", table_name="config_alerta")
    op.drop_table("config_alerta")
    op.drop_index("ix_entregas_alerta_id", table_name="entregas")
    op.drop_table("entregas")
    op.drop_index("ix_alertas_geom", table_name="alertas")
    op.drop_index("ix_alertas_evento_fogo_id", table_name="alertas")
    op.drop_index("ix_alertas_uc_id", table_name="alertas")
    op.drop_index("ix_alertas_severidade", table_name="alertas")
    op.drop_index("ix_alertas_gerencia_id", table_name="alertas")
    op.drop_index("ix_alertas_tipo", table_name="alertas")
    op.drop_table("alertas")
    op.drop_index("ix_eventos_fogo_janela", table_name="eventos_fogo")
    op.drop_index("ix_eventos_fogo_geom_centro", table_name="eventos_fogo")
    op.drop_index("ix_eventos_fogo_uc_id", table_name="eventos_fogo")
    op.drop_table("eventos_fogo")
    # A FK focos.grupo_id -> focos_grupos e `focos_grupos.leitura_representante_id`
    # -> focos: o ciclo precisa ser desfeito nesta ordem.
    op.drop_constraint("fk_focos_grupo_id_focos_grupos", "focos", type_="foreignkey")
    op.drop_index("uq_focos_leitura", table_name="focos")
    # `focos_grupos` tem FK para `focos` (leitura_representante_id): tem de sair
    # antes de `focos`.
    op.drop_index("ix_focos_grupos_geom", table_name="focos_grupos")
    op.drop_table("focos_grupos")
    op.drop_index("ix_focos_geom", table_name="focos")
    op.drop_index("ix_focos_grupo_id", table_name="focos")
    op.drop_index("ix_focos_acquisition_time", table_name="focos")
    op.drop_index("ix_focos_produto", table_name="focos")
    op.drop_index("ix_focos_fonte", table_name="focos")
    op.drop_table("focos")

    op.drop_index("ix_ucs_zonas_geom", table_name="ucs_zonas")
    op.drop_index("ix_ucs_zonas_uc_id", table_name="ucs_zonas")
    op.drop_table("ucs_zonas")
    op.drop_index("ix_ucs_geom", table_name="ucs")
    op.drop_index("ix_ucs_gerencia_id", table_name="ucs")
    op.drop_index("ix_ucs_id_oficial", table_name="ucs")
    op.drop_table("ucs")
    op.drop_table("gerencias_regionais")
