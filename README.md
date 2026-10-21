# Sistema de Alerta de Incêndio Florestal — NGEO / IDEFLOR-Bio

Detecção de focos de incêndio por satélite, alerta às Gerências Regionais do IDEFLOR-Bio
e previsão de risco de ignição nas 29 Unidades de Conservação estaduais do Pará.

**Escopo:** 29 UCs estaduais · 9 Gerências Regionais (DGMUC) · 19.950.698 ha · EPSG:4326 (SIRGAS 2000)

---

## O que o sistema faz

**O NGEO é um serviço de notificação institucional.** Detecta fogo por satélite,
avalia contra as áreas do IDEFLOR-Bio e **notifica a Gerência Regional que responde pela
área** — com a zona do plano de gestão citada, a incerteza posicional declarada e o
registro do que foi notificado. Não é um produto de dado de fogo: estatística
histórica por UC, área queimada e índice de perigo meteorológico já existem e são
melhores em outros (BDQueimadas, MapBiomas Fire Collection, INPE, ALARMES) — ver
`docs/ESTADO_DA_ARTE.md` §5 e `DECISIONS.md` D-016.

| Módulo | Função |
| :--- | :--- |
| Ingestão NRT | Focos de incêndio de múltiplos satélites (FIRMS VIIRS 375 m / MODIS 1 km; NOAA GOES ABI FDC 2 km a 10 min; INPE Programa Queimadas). Latência: **&lt; 3 h** (FIRMS NRT) e **≤ 30 min** de recência (GOES) |
| Processamento | Clusterização espaço-temporal de focos em ocorrências; desduplicação entre sensores **por grupo** (nada é apagado); incerteza posicional explícita |
| Motor de regras | Geração de alerta por UC e **encaminhamento** à Gerência Regional, conforme cadastro oficial DGMUC; severidade graduada e confiança declarada |
| Entrega | Multicanal (e-mail, Telegram, WhatsApp, webhook) com **registro imutável** de auditoria das notificações |
| Painel WebGIS | MapLibre GL JS; **fila de alertas por gerência** como objeto primário; mapa e heatmap como contexto; pacote offline por UC |
| Risco de ignição | P(ignição na UC em N dias): XGBoost com validação espacial e holdout **por UC**, calibração de probabilidade e **SHAP local dentro do alerta** — repositório de pesquisa próprio |
| Propagação | Nowcast do fogo ativo: perímetro estimado, vento e classe de combustível |

## Responsabilidade

O NGEO **detecta e notifica**. O protocolo de combate e a ação em campo são da **Gerência
Regional**; o sistema não implementa fluxo de atendimento nem avalia o que o plano de
gestão permite em cada zona. O alerta entrega material factual — UC, zona, coordenada,
severidade, confiança — e a decisão é do gestor.

**Fronteira de produto (D-016):** o NGEO não faz estatística histórica de fogo por UC, não
reprocessa área queimada nem índice de perigo, não faz app de alerta por proximidade e não
faz ferramenta de campo citizen-science. O que ele faz e que ninguém faz: **encaminhar o
evento à instituição que responde pela área**, citando a zona do plano de
gestão, com a incerteza declarada e o registro auditável da notificação.

## Estado

Fases **F0 (bootstrap)**, **F0b (estado da arte + 1ª coleta real)** e **F1 (fundação
local)** concluídas: PostGIS + Redis em `docker compose`, schema do §5 em migração
Alembic, carga das 9 gerências / 29 UCs / 252 zonas de plano (verbatim) e
`GET /api/health`. **A ingestão de focos ainda não existe** — é a F2.

- **`docs/ESTADO_DA_ARTE.md`** — o que já existe (detecção NRT, modelos de risco,
  propagação, datasets, sistemas de alerta no Brasil/Amazônia), com URL e data de
  acesso de cada fonte, e a lacuna real do NGEO (que se sustenta em 2 de 4).
- **Coleta real do FIRMS** (`scripts/probe_firms.py`) — 811 focos no Pará em 19/10/2026,
  schema **observado** (não o documentado) registrado no estado da arte.

Plano completo, decisões e pendências:

| Doc | Conteúdo |
| :--- | :--- |
| [`PLANO_ARQUITETURA.md`](PLANO_ARQUITETURA.md) | Arquitetura, schema do banco, fases, riscos |
| [`docs/ESTADO_DA_ARTE.md`](docs/ESTADO_DA_ARTE.md) | Estado da arte com fontes citadas + schema real observado |
| [`BUILD.md`](BUILD.md) | Setup, verificação e armadilhas do ambiente |
| [`DECISIONS.md`](DECISIONS.md) | Decisões datadas com motivo e implicações |
| [`ISSUES.md`](ISSUES.md) | Pendências priorizadas |
| [`TAREFAS.md`](TAREFAS.md) | Prompt pronto por sessão |
| [`RETOMADA.md`](RETOMADA.md) | Estado atual e próximo passo |
| [`AGENTS.md`](AGENTS.md) | Convenções do repo e regras de domínio |
| [`BUILD.md`](BUILD.md) | Setup, verificação e armadilhas do ambiente |

## Repositórios correlatos

| Repo | Papel |
| :--- | :--- |
| [`NGEO-IDEFLOR-Bio/visualizador`](https://github.com/NGEO-IDEFLOR-Bio/visualizador) | WebGIS institucional (Leaflet) — fonte das geometrias de referência |
| [`NGEO-IDEFLOR-Bio/cartografia-tematica`](https://github.com/NGEO-IDEFLOR-Bio/cartografia-tematica) | Repositório de cartografia temática (identidade visual) |
| `ngeo-ds` *(a criar)* | Design system compartilhado entre os três |

## Licença e dados

Geometrias e zoneamentos: IDEFLOR-Bio / NGEO. Dados de focos de incêndio: **NASA FIRMS**
(VIIRS/MODIS), **NOAA GOES-R ABI** e **INPE Programa Queimadas** — o texto de
atribuição verificado de cada fonte e os termos em `docs/ESTADO_DA_ARTE.md` §4 e §10;
o registro por fonte (tabela `fontes`) está especificado em `PLANO_ARQUITETURA.md` §5.11 e
pendente de implementação (`ISSUES.md` #07).
