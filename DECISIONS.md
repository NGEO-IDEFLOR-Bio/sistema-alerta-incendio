# DECISIONS — decisões de escopo e arquitetura

> Cada decisão: data, o que, por quê, e o que ela **implica**. Data em DD/MM/AAAA.
> Mudou de ideia? Não apague — registre a supersessão.

---

## D-001 — Frontend usa MapLibre GL JS (não Leaflet)

**Data:** 21/10/2026 · **Status:** vigente

**O quê:** o dashboard de alertas é construído com **MapLibre GL JS**. O `visualizador`
existente permanece em Leaflet.

**Por quê:** MapLibre renderiza melhor camadas densas (heatmap de focos, rasters de risco),
tem `heatmap` nativo, `queryRenderedFeatures` para identify, e suporta tiles vetoriais
(MVT) — que é o que o backend vai servir.

**Implica:**
- App **separado** do `visualizador` (código de mapa não é compartilhado; só o design system).
- Precisa de **basemap**: raster (OSM/Esri) no MVP; auto-hospedado para uso institucional
  e offline → issue #06.
- `visualizador` e o novo dashboard **não** compartilham engine. A identidade visual é
  compartilhada via `ngeo-ds` (D-005), não via código.

---

## D-002 — Duas frentes analíticas em paralelo

**Data:** 21/10/2026 · **Status:** vigente

**O quê:** o projeto ataca **as duas** frentes preditivas, sobre a mesma espinha de dados:
- **Frente A — Risco de ignição:** P(fogo na UC nos próximos N dias). ML + SHAP.
- **Frente B — Propagação (nowcast):** onde o fogo ativo vai chegar nas próximas 6–24 h.

**Por quê:** as duas respondem perguntas diferentes do gestor e usam a mesma ingestão,
o mesmo banco e o mesmo painel. Separá-las adia o valor.

**Implica:**
- Frente B depende de **perímetro**, não de ponto. Cadeia: focos → cluster → perímetro
  estimado → simulação de propagação (vento + combustível).
- Frente A depende de **rótulos** (área queimada) e de validação espacial. É a mais
  pesada em pesquisa e a mais lenta a produzir.
- As duas avançam em paralelo a partir de F6; o MVP de F1–F5 **não depende** de nenhuma delas.

---

## D-003 — Alerta termina na notificação; sem máquina de estados

**Data:** 21/10/2026 · **Status:** vigente

**O quê:** o NGEO **detecta e notifica**. O protocolo de ação, a validação em campo e a
responsabilização são **da Gerência Regional**. O sistema **não** implementa workflow de
atendimento, estados (`EM_ATENDIMENTO`), atribuição de responsável nemacknowledgement.

**Por quê:** a ação não depende do setor do NGEO. Modelar o atendimento seria responsibly
errado e atravessa a fronteira institucional.

**Implica:**
- Esquema enxuto: `focos` → `eventos_fogo` → `alertas` → `entregas`. Sem tabela de estados.
- `alertas` é **imutável** (registro do que foi notificado e quando).
- O **roteiro de entrega é configurável por Gerência Regional** (`config_alerta`): canal,
  destinatários, raio, janela, severidade mínima, template.
- O produto passa a ser medido por **precisão do alerta** (taxa de falso positivo
  percebido) e por **cobertura** (focos com alerta emitido), não por SLA de atendimento.
- Consequência de projeto: o **clustering/dedup** deixa de ser "etapa de máquina de estados"
  e vira **filtro de qualidade** — é onde vive o controle de falso positivo.

---

## D-004 — Todas as fontes de focos

**Data:** 21/10/2026 · **Status:** vigente

**O quê:** ingestão **multi-fonte**, adapters para FIRMS (MODIS/VIIRS/GOES), INPE
MONITORQUEIMADAS e GOES-16 via AWS Open Data. Todas desde o início.

**Por quê:** são gratuitas; o custo é integração, não licença. A variedade dá **redundância**
(uma fonte fora do ar não cega o sistema) e cobertura de horário.

**Implica:**
- Camada de adapters com **um schema canônico**; cada fonte só escreve no canônico.
- **Dedup cross-sensor é obrigatório**: o mesmo incêndio aparece no MODIS e no VIIRS com
  timestamps e resolução diferentes. Sem dedup, a contagem de focos é inflada e o
  agrupamento geográfico quebra.
- Cada fonte tem **latência, resolução e esquema próprios** → tabelas de proveniência
  (`fonte`, `satelite`, `sensor`) obrigatórias na tabela canônica.
- **Atribuição/licença por fonte** precisa ser documentada (issue #07).

---

## D-005 — Design system compartilhado no repo `ngeo-ds`

**Data:** 21/10/2026 · **Status:** vigente

**O quê:** tokens, componentes, fontes Rawline e logos institucionais passam a viver num
repositório único (`ngeo-ds`), consumido via CDN pinado por versão.

**Por quê:** hoje `maps` (CSS próprio, tokens `--gov-*`) e `visualizador` (Tailwind CDN)
implementam **a mesma paleta** (`#1351b4`, `#071d41`, `#0c326f`) por dois mecanismos
diferentes, com fontes e logos duplicados e nomes inconsistentes
(`logo_ngeo.png` vs `logo-ngeo.png`). Divergência vai crescer.

**Implica:**
- O dashboard novo consome `ngeo-ds` desde o dia 1.
- `maps` e `visualizador` migram em **sessões separadas** depois (issues #08, #09).
- Precisa de **escala semântica de severidade** (baixa/média/alta/crítica) e de **rampa
  de calor perceptualmente uniforme** (não vermelho-amarelo-verde) — ver issue #10.

---

## D-006 — Separação entre sistema e pesquisa

**Data:** 21/10/2026 · **Status:** vigente

**O quê:** este repo é o **sistema**. O trabalho de pesquisa (datasets, treinamento,
avaliação, notebooks da frente A) vive em repo próprio (`ml-fire-alert`, a ser recriado).

**Por quê:** churn de pesquisa não deve contaminar o ritmo do sistema, e o modelo
publicado precisa de procedência auditável (digest do dataset + métricas + data de
validade).

**Implica:**
- O sistema consome o modelo como **artefato versionado** (binário + `model_card.json`).
- O modelo entra em produção via *pull request* com card revisado — não via deploy manual.

---

## D-007 — Roteamento do alerta é por Gerência Regional (DGMUC)

**Data:** 21/10/2026 · **Status:** vigente, **bloqueado por dependência institucional**

**O quê:** cada alerta é roteado à Gerência Regional que responde pela área.

**Por quê:** é quem executa o protocolo de ação. Sem isso a notificação não tem dono.

**Implica:** exige o **mapeamento UC → Gerência Regional (DGMUC)**, que hoje não existe
estruturado em nenhum repo do NGEO → **issue #01 (bloqueante)**.

---

## D-008 — Latência-alvo do alerta

**Data:** 21/10/2026 · **Status:** vigente

**O quê:** notificação de detecção em **≤ 1 h** a partir da aquisição do satélite;
risco (frente A) em ciclo **diário**.

**Por quê:** 1 h é defensável institucionalmente com GOES-16/FIRMS e útil para turno de
campo; a frente A é intrinsecamente diária e não pode ser vendida como "tempo real".

**Implica:** D-004 é pré-requisito. A promessa pública deve ser "detecção NRT" e
"risco diário", nunca "previsão em tempo real".
