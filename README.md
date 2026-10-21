# Sistema de Alerta de Incêndio Florestal — NGEO / IDEFLOR-Bio

Detecção de focos de incêndio por satélite, alerta às Gerências Regionais do IDEFLOR-Bio
e previsão de risco de ignição nas 29 Unidades de Conservação estaduais do Pará.

**Escopo:** 29 UCs estaduais · 9 Gerências Regionais (DGMUC) · 19.950.698 ha · EPSG:4326 (SIRGAS 2000)

---

## O que o sistema faz

| Módulo | Função |
| :--- | :--- |
| Ingestão NRT | Focos de incêndio de múltiplos satélites (FIRMS VIIRS 375 m / MODIS 1 km; NOAA GOES ABI FDC 2 km a 10 min; INPE Programa Queimadas). Latência: **&lt; 3 h** (FIRMS NRT) e **≤ 30 min** de recência (GOES) |
| Processamento | Clusterização espaço-temporal de focos em ocorrências; desduplicação entre sensores; incerteza posicional explícita |
| Motor de regras | Geração de alerta por UC e roteamento à Gerência Regional, conforme cadastro oficial DGMUC |
| Entrega | Multicanal (e-mail, Telegram, WhatsApp, webhook) com registro de auditoria das notificações |
| Painel WebGIS | MapLibre GL JS; heatmap de focos; filtros por gerência e janela temporal; modo claro/escuro; pacote offline por UC |
| Risco de ignição | XGBoost com validação espacial (block CV) e calibração de probabilidade; explicabilidade SHAP — repositório de pesquisa próprio |
| Propagação | Nowcast do fogo ativo: perímetro estimado, vento e classe de combustível |

## Responsabilidade

O NGEO **detecta e notifica**. O protocolo de combate e a ação em campo são da **Gerência
Regional**; o sistema não implementa fluxo de atendimento nem avalia o que o plano de
gestão permite em cada zona. O alerta entrega material factual — UC, zona, coordenada,
severidade, confiança — e a decisão é do gestor.

## Estado

Fases **F0 (bootstrap)** e **F0b (estado da arte + 1ª coleta real)** concluídas.
**Sem backend ainda** — a implementação começa na F1.

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
