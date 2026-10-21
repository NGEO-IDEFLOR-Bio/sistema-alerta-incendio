# Sistema de Alerta de Incêndio Florestal — NGEO / IDEFLOR-Bio

Detecção de focos de incêndio por satélite, alerta às Gerências Regionais do IDEFLOR-Bio
e previsão de risco de ignição nas 29 Unidades de Conservação estaduais do Pará.

**Escopo:** 29 UCs estaduais · 9 Gerências Regionais (DGMUC) · 19.950.698 ha · EPSG:4326 (SIRGAS 2000)

---

## O que o sistema faz

| Módulo | Função |
| :--- | :--- |
| Ingestão NRT | Focos de incêndio de múltiplos satélites (FIRMS/MODIS/VIIRS/GOES, INPE MONITORQUEIMADAS). Resolução espacial 375 m–1 km, latência de horas |
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

Fase **F0 (bootstrap)** concluída: documentação, plano de arquitetura, decisões e
issues. **Sem código ainda** — a implementação começa na F1.

Plano completo, decisões e pendências:

| Doc | Conteúdo |
| :--- | :--- |
| [`PLANO_ARQUITETURA.md`](PLANO_ARQUITETURA.md) | Arquitetura, schema do banco, fases, riscos |
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

Geometrias e zoneamentos: IDEFLOR-Bio / NGEO. Dados de focos de incêndio: NASA FIRMS,
INPE MONITORQUEIMADAS e GOES-16 — atribuição e termos de uso por fonte em `ISSUES.md` (#07).
