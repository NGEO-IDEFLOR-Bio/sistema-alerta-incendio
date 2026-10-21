# RETOMADA — estado atual e próximos passos

> Entrada para retomar. Leia: `AGENTS.md` → este arquivo → `ISSUES.md` → `TAREFAS.md` → `BUILD.md`.
> Atualizado: 21/10/2026 (T0 — estado da arte + 1ª coleta real).

## Estado atual

- **F0 (bootstrap) — ✅ concluída em 21/10/2026.**
  - `AGENTS.md`, `RETOMADA.md`, `ISSUES.md`, `TAREFAS.md`, `BUILD.md`, `DECISIONS.md`,
    `PLANO_ARQUITETURA.md`, `.gitignore`, `.gitattributes`, `.env.example` criados.
  - Repo git inicializado; `.env` e `secrets/` **fora** do versionamento.
  - Arquitetura anterior movida para `docs/arquivo/arquitetura_do_backend_do_sistema.md`.
  - **Nenhum backend escrito ainda.** Sem `backend/`, sem `frontend/`, sem docker-compose.
- **F0b (T0) — ✅ concluída em 21/10/2026.** Estado da arte + 1ª coleta real.
  - **`docs/ESTADO_DA_ARTE.md`** — 11 seções, ~70 fontes externas citadas com URL e data
    de acesso (21/10/2026). Detecção NRT, modelos de risco, propagação, datasets,
    sistemas já existentes no Brasil/Amazônia, lacuna real e riscos.
  - **Coleta real do FIRMS** — `scripts/probe_firms.py`: **uma** chamada a
    `/api/area/csv/<MAP_KEY>/VIIRS_NOAA20_NRT/<bbox do Pará>/1/2026-10-19` → **811 registros**,
    14 colunas. Payload cru + relatório de schema em `data/probes/` (gitignored); recorte de
    6 linhas versionado em `tests/fixtures/` como fixture do teste.
  - `pyproject.toml` (ruff + pytest na raiz), `tests/test_probe_firms.py` (16 testes, **sem rede**).
  - Schema **real** ≠ schema documentado: `acq_time` é HHMM **sem zero à esquerda**
    (`353` = 03:53), `confidence` vem como `l`/`n`/`h`, `satellite` vem como `N20`, VIIRS não
    tem `brightness`/`bright_t31` (tem `bright_ti4`/`bright_ti5`), lat/lon com 2–5 decimais
    variáveis.
- **Dados de referência recebidos (21/10/2026):**
  - `data/shapes_de_todas_as_unidades_com_gerencia.geojson` — **29 UCs com gerência DGMUC**
    (9 gerências), `id` 1..29, EPSG:4326. Digest e procedência em `data/README.md`.
  - `visualizador/data/zoneamentos_ucs_estaduais.geojson` — **252 zonas de plano de manejo
    em 16 UCs**. Entra **verbatim** (D-009): sem taxonomia global, sem normalização.
  - ✅ **Issue #21 resolvida no arquivo**: `GRCN-l/ll/lll` → `GRCN-I/II/III`, sem tocar em
    geometria (29 features, mesmos bytes). Digest original e corrigido no `data/README.md`.
- **Decisões fechadas:** D-001 MapLibre · D-002 duas frentes em paralelo ·
  D-003 alerta termina na notificação, sem máquina de estados · D-004 todas as fontes ·
  D-005 DS compartilhado `ngeo-ds` · D-006 sistema ≠ pesquisa · D-007 roteamento por
  gerência regional (**dependência resolvida**) · D-008 latência-alvo ≤1 h
  (**revisada por D-015**) · D-009 zoneamento = contexto que aponta para o plano, **não** filtro ·
  D-010 o sistema **nunca descarta foco em silêncio** — qualifica a confiança ·
  D-011 instrumento, não instrução ·
  **D-012** fontes de focos (primária/fallback/ordem) · **D-013** política de dedup cross-sensor
  · **D-014** schema canônico definitivo + CAP · **D-015** revisão da latência-alvo ·
  **D-016** fronteira de produto (o que o NGEO é e o que não é).
- **Ativos já disponíveis no `.env`:** `GEE_PROJECT_ID` + `GEE_CREDENTIALS_JSON`,
  `TUNNEL_TOKEN` (Cloudflare), uma chave do Sentinel Hub em `secrets/`, e a **MAP_KEY do
  FIRMS** (obtida em 21/10/2026). `GEMINI_API_KEY` / `OPENROUTER_API_KEY` ficam para a frente A.
  ⚠️ `DATABASE_URL` está **vazia** no `.env` (issue #34) — a `RETOMADA` anterior
  afirmava que estava lá.

## O que a T0 mudou no plano (leitura obrigátoria antes da F1)

1. **Latência-alvo (D-015).** URT/RT do FIRMS são **só EUA/Canadá**; para o Pará o
   piso do FIRMS NRT é **< 3 h**. O alvo de 1 h só vale para **recência via GOES**
   (10 min). Comunicação: *recência ≤ 30 min* + *detecção NRT < 3 h* + *risco diário*.
2. **Fontes (D-012).** Primária: FIRMS **VIIRS** (375 m). Recência: NOAA **GOES ABI L2 FDC**.
   Fallback: **INPE Programa Queimadas / BDQueimadas** (aberto, **sem chave** — o nome
   "MONITORQUEIMADAS" não existe). MapBiomas **Alerta** é **desmatamento**, não fogo.
3. **Dedup (D-013).** Mesmo fogo = `|Δt| ≤ 6 h` **e** `d ≤ max(raio_pixel_m)`. O dedup
   **agrupa** (`focos_grupos`), **não apaga** (D-010). A janela de 6 h ainda tem de ser
   **calibrada** (issue #32).
4. **Schema (D-014).** `focos` ganhou `produto`, `satelite_codigo`, `versao_produto`,
   `scan_angle`, `track_angle`, `dia_noite`, `posicao_terreno_corrigida`, brilho
   parametrizado por banda, `confianca` canônica + `confianca_crua`, `grupo_id`.
   Novas tabelas: `focos_grupos`, `fontes`, `parametros_dedup`.
5. **Padrão de mensagem:** **CAP (ITU-T X.1303 / OASIS v1.2)** — não "ITU-R BT.839",
   que **não foi localizada** (T.839 da ITU-T é JPEG XR).
6. **Lacuna do NGEO:** **se sustenta em 2 de 4** (roteamento por Gerência Regional +
   citação do zoneamento). "SHAP local por UC" **já existe** (Cerrado, preprint
   jun/2026; e Triunfo do Xingu) — a originalidade é **ignição + risco por UC do
   IDEFLOR + SHAP no alerta**. "Offline" é decisão de produto, não lacuna de domínio.
   Ver `docs/ESTADO_DA_ARTE.md` §6-f.
7. **Fronteira de produto gravada (D-016, 21/10/2026).** Reapurado com **ALARMES**
   (LASA/UFRJ), **SIFAU** e **Savana** — que **não abafam** a lacuna, mas ocupam o
   espaço "estatística por ROI/UC" e "alerta por proximidade". O NGEO **não** fará:
   estatística histórica por UC · reprocessamento de área queimada · índice de
   perigo · app de proximidade · ferramenta de campo citizen-science. Objeto primário do
   dashboard: **fila de alertas por gerência**. A frente A passa a ser
   **risco de ignição** (não susceptibilidade), com correção de
   detectabilidade no rótulo e **SHAP local dentro do alerta**.

## Princípio que emerged das correções de 21/10/2026

> **O sistema entrega material; a leitura e a ação são do gestor.**
>
> Quatro consequências concretas:
> 1. Alerta em zona de manejo **é emitido** — quem define o que pode ou não pode é o
>    plano da unidade, não o software (D-009).
> 2. **Não existe taxonomia global de zonas** — cada plano nomeia e define as suas, e
>    nada é padronizado (D-009).
> 3. **Nada é descartado em silêncio** — a incerteza é declarada no alerta (severidade,
>    confiança, `possivel_falso_positivo`), não escondida por supressão (D-010).
> 4. **Instrumento, não instrução** — o produto não orienta, lembra, explica ou
>    interpreta. Sem landing page, sem tutorial, sem "verifique antes de agir". O
>    destinatário é gestor de gerência regional e sabe o que fazer com o material
>    (D-011).


## Bloqueio

- **Nenhum bloqueio técnico.** #01 resolvido, #21 resolvido.
- **#31 — MAP_KEY do FIRMS emitida para e-mail descartável**: funciona, mas tem de ser
  reemitida sob e-mail institucional (e movida para `secrets/`). Não bloqueia a F1.
- **Pendências institucionais (não bloqueiam F1/F2):**
  - ~~#22 — registry de gerências do `maps`~~ ✅ **resolvido** em 21/10/2026
    (`maps` commits `72b0eee` e `618feae`, push).
  - #29 — **sigla `GRCN-l/ll/lll` no cadastro oficial**: o defeito está no portal
    IDEFLOR e no shapefile consolidado, não só no arquivo local. A cópia local foi
    corrigida (#21), mas todo re-download reintroduz. Requer ação upstream.
  - #30 — sigla **GRM** (Marajó) consta do shapefile, não da página "Shapes de cada
    unidade".
  - #24 — zoneamento para as 13 UCs restantes.
  - #25 — Zonas de Amortecimento para as UCs que não têm.
  - #07 — termos de uso/atribuição por fonte de focos.





## Próximo passo (1 item)

1. **T1 — Fundação local (PostGIS + Redis + schema + seed).**
   `docker-compose.yml`, `backend/` com pyproject/Alembic, o schema de
   `PLANO_ARQUITETURA.md` §5 (agora com `focos_grupos`, `fontes` e `parametros_dedup`),
   seeds das 9 gerências, das 29 UCs e das 252 zonas (verbatim, por sobreposição
   espacial), e `GET /api/health`.
   Prompt pronto em `TAREFAS.md` → T1.
   ⚠️ Antes de começar: preencher `DATABASE_URL` no `.env` (issue #34).

## Próximos depois da T1

T2 (ingestão multi-fonte + dedup cross-sensor) → T3 (motor de regras) → T4 (entrega)
→ T5 (frontend).
**Frente A (T6/T7) e Frente B (F7) entram em paralelo** a partir de F6.
Na T2: uma **coleta real por fonte** (VIIRS já feita — issue #33 pede MODIS, GOES e INPE),
calibração da janela de dedup (#32) e reemissão da MAP_KEY (#31).


## Fora de escopo (agora)

- Modelo de ML / SHAP (frente A) — repo próprio, fase F6.
- Nowcast de propagação (frente B) — fase F7.
- **Portal público / landing page / scrollytelling — removido do plano** (D-011).
  Se um dia precisar, sai como artefato da frente A, fora do caminho crítico.
- **Qualquer texto instrutivo no produto** — alerta, painel, relatório (D-011).
- Migração de `maps` e `visualizador` para `ngeo-ds` — issues #08, #09.
- Workflow de atendimento / estados do alerta — **decidido fora** (D-003).


## Como retomar

```
1. ler AGENTS.md, RETOMADA.md, ISSUES.md
2. pegar a próxima tarefa em TAREFAS.md
3. 1 sessão = 1 tarefa = 1 commit; verificação OK antes
4. atualizar ISSUES.md + RETOMADA.md no mesmo commit
```
