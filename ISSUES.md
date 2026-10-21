# ISSUES — fonte da verdade das pendências

> Status: ✅ feito · 🟡 parcial · ⏳ pendente · ◔ bloqueado · 🗄️ arquivado · ❌ descartado
> Regra: **atualizar no mesmo commit** em que a issue for resolvida.

## Bloqueantes

| # | Issue | Status | Nota |
| :--- | :--- | :--- | :--- |
| ~~#01~~ | ~~Mapeamento UC → Gerência Regional (DGMUC)~~ | ✅ resolvido | Fornecido em `data/shapes_de_todas_as_unidades_com_gerencia.geojson` — 29 UCs, 9 gerências, `id` 1..29. Digest e procedência em `data/README.md`. **Desbloqueia F1/F3.** Ver #21 e #22 |

## Fundação

| # | Issue | Status | Nota |
| :--- | :--- | :--- | :--- |
| **#02** | Bootstrap do repo (docs, `.gitignore`, `git init`) | ✅ feito | Fase F0 — 21/10/2026 |
| **#03** | `docker-compose.yml` (PostGIS + Redis) + `scripts/` de seed | ⏳ pendente | F1 |
| **#04** | Schema das tabelas canônicas | 🏗️ especificado | `PLANO_ARQUITETURA.md` §5 — implementar em F1 |
| **#05** | Registro de chaves/licença por fonte de focos | ⏳ pendente | issue #07 |

## Qualidade de dados de referência (NOVO)

| # | Issue | Status | Nota |
| :--- | :--- | :--- | :--- |
| **#21** | Sigla de gerência com L minúsculo (`GRCN-l`/`ll`/`lll`) | ✅ **resolvido** | Corrigido **no arquivo** em 21/10/2026: `CALHA NORTE l/ll/lll` → `I/II/III` no nome e na sigla. 29 features e geometria intactas. Digest original e corrigido em `data/README.md`. O seed mantém a validação 29 UCs / 9 gerências, porque o arquivo original volta da instituição. |
| **#22** | Registry de gerências divergente entre `maps` e o arquivo atual | 🟡 pendente | `maps/organize_and_build.py` + README listam 9 gerências de **produção cartográfica** (GRCN-I, GRCN-II, GRX, GRB, GRMR, GRET, GRBA, GRT, GRA + escopo GERAL). O arquivo atual é o de **gestão de UC**: GRCN-I, GRCN-II, **GRCN-III**, GRB, **GRTUC**, GRA, **GRM**, **GRNE**, GRX. Diferenças: GRCN-III, GRNE, GRTUC são novos; GRMR→GRM; GRT/GRBA/GRET não existem mais. **Atualizar o `maps`** para não publicar estrutura de gerência desatualizada. |
| **#23** | Zoneamento: `SIGLA` não é global; `UNIDADE` truncada; join por nome inviável | 🟡 **parcial** | **Não padronizar** (D-009): cada plano de gestão nomeia e define as suas próprias zonas; taxonomia global destruiria o significado. `sigla` e `zona` ficam **verbatim**. Join UC↔zona por **sobreposição espacial** — `UNIDADE` está truncado ("Ambiental da Ilha de Combu", "Reserva Biológica do Maicuru (REBIO"). Regra de negócio **nunca** por `sigla`. |
| **#26** | Curadoria por UC do que o plano diz sobre fogo em cada zona | 🔴 **alta** | Tabela `ucs_zonas_decisao` (PLANO §5.8) — preenchida pelo NGEO, **começa vazia**, uma linha por (UC, zona): `permite_queima`, `observacao`, `ref_plano`, `curado_por`. Não é padronização: é o significado do plano, plano a plano. **Não bloqueia o MVP**; é o que habilita a feature de zona na frente A (§10). |
| **#27** | Alerta deve citar o plano de gestão quando o foco cai em zona | 🟡 pendente | Requisito de conteúdo do alerta (D-009): `zona_sigla`, `zona_texto`, `ref_plano` verbatim. Quando a UC não tem zoneamento → alerta **sem** contexto de zona + limitação explícita, nunca com suposição |
| **#24** | Zoneamento cobre só 16 das 29 UCs | 🟡 pendente | 13 UCs sem classificação de zona → alerta segue emitido **sem** contexto de zona (nunca suprimido). Degradar com honestidade + pedir as 13 restantes à DGMUC. |
| **#25** | Zonas de Amortecimento só para poucas UCs | 🟡 pendente | ZA cartografada em Trombetas, REVIS (setores I/II/III), Paru, Faro. Issue #15 original: **parcialmente resolvida** — ZA não é universal. |



## Identidade visual / DS

| # | Issue | Status | Nota |
| :--- | :--- | :--- | :--- |
| **#08** | Migrar `maps` para `ngeo-ds` | ⏳ pendente | Sessão própria, depois do dashboard |
| **#09** | Migrar `visualizador` para `ngeo-ds` | ⏳ pendente | Sessão própria, depois do dashboard |
| **#10** | Escala semântica de severidade + rampa de calor perceptual | ⏳ pendente | F5 / `ngeo-ds`. Vermelho-amarelo-verde **não** usar |
| **#11** | Repo `ngeo-ds` (tokens, componentes, fontes, logos) | ⏳ pendente | Consumption via CDN pinado por tag |
| **#12** | Canonicalizar nomes de assets (`logo_ngeo.png` vs `logo-ngeo.png`) | ⏳ pendente | Resolvido naturalmente pelo `ngeo-ds` |

## Dados e fontes

| # | Issue | Status | Nota |
| :--- | :--- | :--- | :--- |
| **#07** | Registrar termos de uso, atribuição e redistribuição por fonte (FIRMS, INPE, GOES/AWS, Sentinel Hub) | ⏳ pendente | Duty de atribuição no painel e no relatório |
| **#13** | Conceder/registrar chaves: FIRMS API, INPE, Sentinel Hub, Telegram bot | ⏳ pendente | `.env.example` já tem as chaves |
| **#14** | Geometria de referência: fonte única | 🟡 parcial | `data/` deste repo (gitignored) + `visualizador/data/`. Consolidar em `ngeo-assets` (issue #11 junto) |
| **#15** | ~~Zonas de amortecimento das UCs~~ | 🟡 parcial | ZA existe para poucas UCs (Trombetas, REVIS, Paru, Faro) — ver #25 |


## Produto

| # | Issue | Status | Nota |
| :--- | :--- | :--- | :--- |
| **#16** | Basemap auto-hospedado (uso institucional + offline) | ⏳ pendente | MVP usa OSM/Esri |
| **#17** | "Pacote da UC" offline (GeoJSON + raster + PDF) | ⏳ pendente | F5/F8 — campo sem sinal |
| **#18** | Relatório PDF operacional por UC | ⏳ pendente | Entregável de campo; já previsto em RF10 |
| **#19** | Posicionamento público: "detecção NRT ≤1 h" + "risco diário" | ⏳ pendente | Nunca "previsão em tempo real" (R3) |
| **#20** | Repo `ml-fire-alert` (frente A, pesquisa) | ⏳ pendente | Recriar quando a frente A entrar (F6) |

## Descartado

| # | Item | Status | Nota |
| :--- | :--- | :--- | :--- |
| ~~#00~~ | `ml-fire-alert` como repo de pesquisa inicial | ❌ descartado | Era duplicata de `visualizador/data` (GeoJSON byte-idênticos). Recriar em F6 com escopo de pesquisa (D-006) |
| ~~#00~~ | Máquina de estados do alerta / workflow de atendimento | ❌ descartado | Decisão D-003 — o NGEO notifica; a ação é da gerência regional |
| ~~#00~~ | Paywall / lead-gen no download de dados brutos | ❌ descartado | Inviável/institucionalmente estranho num sistema do IDEFLOR. Se houver portal público, o gate fica lá |
