# ISSUES — fonte da verdade das pendências

> Status: ✅ feito · 🟡 parcial · ⏳ pendente · ◔ bloqueado · 🗄️ arquivado · ❌ descartado
> Regra: **atualizar no mesmo commit** em que a issue for resolvida.

## Bloqueantes

| # | Issue | Status | Nota |
| :--- | :--- | :--- | :--- |
| **#01** | **Mapeamento UC → Gerência Regional (DGMUC)** | ◔ bloqueado | Não existe estruturado em nenhum repo do NGEO. `maps` sabe qual gerência fez cada *carta*; `ucs_estaduais.geojson` traz `Municipios_lista` e `RegioesIntegracao_lista`, mas **não** a gerência. Sem isso o roteamento do alerta (D-007) e o seed do banco (F1/F3) não fecham. **Dependência institucional — precisa vir da DGMUC.** Formato alvo: `gerencias_regionais.csv` + coluna `gerencia_id` nas UCs. |

## Fundação

| # | Issue | Status | Nota |
| :--- | :--- | :--- | :--- |
| **#02** | Bootstrap do repo (docs, `.gitignore`, `git init`) | ✅ feito | Fase F0 — esta sessão |
| **#03** | `docker-compose.yml` (PostGIS + Redis) + `scripts/` de seed | ⏳ pendente | F1 |
| **#04** | Schema das tabelas canônicas | 🏗️ especificado | `PLANO_ARQUITETURA.md` §5 — implementar em F1 |
| **#05** | Registro de chaves/licença por fonte de focos | ⏳ pendente | issue #07 |

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
| **#14** | Geometria de referência: fonte única (hoje `visualizador/data/`) | 🟡 parcial | 4 GeoJSON compartilhados com `ml-fire-alert` (apagado). Migrar para `ngeo-assets` ou seed por script |
| **#15** | Zonas de amortecimento das UCs | ⏳ pendente | Não há no repo. Necessário para `FOCO_EM_UC` na ZA |

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
