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

**Data:** 21/10/2026 · **Status:** vigente — **dependência resolvida**

**O quê:** cada alerta é roteado à Gerência Regional que responde pela área.

**Por quê:** é quem executa o protocolo de ação. Sem isso a notificação não tem dono.

**Implica:** o mapeamento UC → Gerência Regional (DGMUC) foi fornecido em
`data/shapes_de_todas_as_unidades_com_gerencia.geojson` — 29 UCs, 9 gerências,
`id` sequencial 1..29. Digest e procedência em `data/README.md`.

**Fonte oficial verificada (21/10/2026):** a página "Shapes de cada unidade" do portal
IDEFLOR-Bio (<https://ideflorbio.pa.gov.br/shapes-de-cada-unidade>) publica exatamente
as **9** gerências — GRA (2 UCs), GRB (4), GRCN-I (2), GRCN-II (5), GRCN-III (2),
Marajó (2), GRNE (4), GRTUC (3), GRX (5) = **29**, casando 1:1 com o shapefile. O
portal as chama "Região Administrativa" no menu. A estrutura do repo `maps`, que
publicava GRMR, GRET, GRBA e GRT, **não tinha respaldo no cadastro oficial** e foi
corrigida (commit `618feae`).

⚠️ A sigla vem com **L minúsculo** no lugar do I romano (`GRCN-l`, `GRCN-ll`,
`GRCN-lll`) — e o defeito está **no cadastro oficial**, não só no arquivo local: o
portal grafa "Calha Norte l/ll/lll" e repete a mesma substituição em `UMF l/ll/lll`.
**Normalização no seed é obrigatória**, com teste de integridade (29 UCs / 9 gerências)
— sem isso o roteamento falha em silêncio. Issues #21 (corrigido localmente) e #29
(correção upstream).


---

## D-009 — O zoneamento de plano de manejo é contexto que aponta para o plano, não filtro

**Data:** 21/10/2026 · **Status:** vigente (revisado na mesma data)

**O quê:** `visualizador/data/zoneamentos_ucs_estaduais.geojson` (252 zonas em 16 das
29 UCs) entra no banco como `ucs_zonas`, com `sigla` e `zona` **verbatim**.

**Por quê (duas razões):**

1. **O sistema sempre alerta — mesmo em zona de manejo.** Quem diz o que pode ou não
   pode é o **plano de gestão da unidade**, não o software. A zona entra no alerta como
   *contexto e ponteiro* para o instrumento que governa aquela área, não como critério
   de supressão. Suprimir alerta por zona seria o sistema decidindo o que é permitido —
   competência que não é dele (coerente com D-003: o NGEO notifica, a gerência executa).
2. **Não existe taxonomia global de zonas.** Cada plano de gestão nomeia e define as
   suas próprias zonas. `SIGLA` não é global: `ZA` = "Alta Intervenção" em
   Algodoal-Maiandeua e = "Zonas de Amortecimento" em Trombetas. Normalizar, mapear para
   uma classe única ou casar por nome **destrói o significado** de cada plano.

**Implica:**
- `ucs_zonas` guarda os valores **como o plano os escreveu**. Sem `zona_norm`, sem
  `classe` global, sem renomear nada.
- Regra de negócio **nunca** usa `sigla` como chave. Issue #23.
- **Não existe tabela de curadoria.** O sistema não avalia, não codifica e não infere
  permissão de fogo em zona alguma. A zona é **informação** que consta do alerta.
  Issue #26 (descartada).
- Join UC ↔ zona por **sobreposição espacial** (o campo `UNIDADE` está truncado).
  Issue #23.
- O alerta **informa a zona e a coordenada. Só.** Sem "verificar antes de agir", sem
  lembrete sobre o plano, sem interpretação. O gestor sabe qual é o plano da própria
  unidade — chamá-lo de instruir é chamar de imbecil (D-011).
- Zona de Amortecimento (ZA) existe para poucas UCs — não é universal. Issue #25.
- **A zona não é feature** da frente A. O confundidor "fogo de manejo" nos rótulos
  permanece como **limitação declarada**, não como problema resolvido (§10).


---

## D-011 — O sistema entrega instrumento, não instrução

**Data:** 21/10/2026 · **Status:** vigente

**O quê:** nenhum artefato do sistema — alerta, painel, mensagem, documento — **instrui,
lembra, explica ou interpreta**. O sistema entrega **material factual** para tomada de
decisão rápida; a leitura e a ação são do destinatário.

**Por quê:** o destinatário é gestor de gerência regional do IDEFLOR-Bio. Ele conhece a
unidade, o plano de gestão, o terreno e o que é um foco de calor. Um sistema que
reescreve o plano para o gestor, ou que explica o básico, é paternalismo — e pior, é
ruído que atrasa a decisão no momento em que ela precisa ser rápida.

**Implica:**
- **Alerta:** só fatos — UC, zona (verbatim), coordenada (decimal + UTM), horário,
  severidade, confiança, nº de focos, fontes, link do mapa. Sem imperativo, sem
  "atenção", sem "recomenda-se", sem definição de termo técnico, sem lembrete de plano.
- **Sem "quem é o responsável" no corpo da mensagem** — o roteamento já entrega à
  gerência certa. Fica no registro.
- **Sem "ref_plano"** no payload do alerta: apontar para o plano é o começo da
  instrução. A zona entra como informação verbatim e só.
- **Interface:** o app abre no mapa. Sem landing page, sem hero, sem scroll-telling,
  sem CTA institucional, sem parágrafo explicativo, sem tooltip que defina termo.
  Legenda de mapa é dado, não narrativa — permanece. Densidade alta, rótulos técnicos.
- **Dashboard** é ferramenta de trabalho, não vitrine institucional.
- **Escala de severidade permanece** — é uma leitura derivada da evidência, útil e
  factual, não uma instrução. Mas os fatos brutos vão junto, para o gestor re-derivar.
- **O portal público / scrollytelling saiu do plano** (F9 removido). Se um dia
  precisar, é artefato da frente A, fora do caminho crítico.
- Coerente com D-003 (a ação não é do NGEO) e D-010 (a incerteza é declarada, não
  hideada por supressão).


---

## D-010 — O sistema nunca descarta um foco em silêncio; ele classifica a confiança

**Data:** 21/10/2026 · **Status:** vigente

**O quê:** todo evento de fogo que toca uma UC **gera alerta**. O que muda é a
**severidade** e a **confiança** declaradas no alerta — não a existência do alerta.

**Por quê:** supressão silenciosa destrói confiança mais rápido que excesso de alerta.
O gestor precisa poder confiar que "não recebi nada" significa "não houve nada", não
"o filtro comeu". A fila é ordenada por severidade, então o ruído desce sozinho.

**Implica:**
- **Agregação ≠ supressão.** N focos do mesmo incêndio viram **um evento, um alerta**
  (evita 20 e-mails do mesmo pixel). Isso é anti-spam, não supressão.
- Todo alerta carrega: nº de focos, fontes concordantes, persistência temporal,
  e a flag `possivel_falso_positivo` quando o sinal é fraco (foco isolado, diurno).
- Severidade é **graduada**, não binária: `baixa` (sinal fraco, possível falso positivo)
  → `critica` (múltiplos focos, persistência, concordância entre fontes).
- Filtros de **geometria/qualidade** (nuvem, chuva recente) continuam, mas só para
  **qualificar a confiança**, nunca para descartar.
- Coerente com D-003 e D-009: o sistema **informa e qualifica**; a decisão é do
  gestor, com base no plano.



---

## D-012 — Fontes de focos: primária, fallback e ordem de implementação

**Data:** 21/10/2026 · **Status:** vigente (completa D-004)

**Apurado em:** `docs/ESTADO_DA_ARTE.md` (21/10/2026, com URLs e data de acesso).

### 12.1 Fontes e papéis

| Papel | Fonte | Por quê |
| :--- | :--- | :--- |
| **Primária de detecção (alta resolução)** | **FIRMS VIIRS** (`VIIRS_NOAA20_NRT`, com `VIIRS_NOAA21_NRT` e `VIIRS_SNPP_NRT`) | 375 m; **< 3 h** de latência para o mundo todo; cobertura do Pará **confirmada por coleta real** (§7 do ESTADO_DA_ARTE); gratuito, com MAP_KEY |
| **Primária de recência (alta cadência)** | **NOAA GOES ABI L2 FDC** (`ABI-L2-FDC`, bucket público `noaa-goes16`) | FHS a cada **10 min**; cobre as Américas (Pará incluído). É o único caminho para "o fogo ainda está lá?" — mas 2 km e **viés de terreno não corrigido** |
| **Fallback / fonte independente parcial** | **INPE — Programa Queimadas / BDQueimadas** (focos a cada 10 min, CSV/KML/GeoServer WFS-WMS, **sem autenticação**) | Processa **10 satélites** próprios (inclui GOES, MetOp B/C, Meteosat). ⚠️ **Não é 100% independente do FIRMS**: o INPE também incorpora cobertura FIRMS. É fallback de *formato e de sensor*, não de cadeia |
| **Fallback de resolução (1 km)** | **FIRMS MODIS** (`MODIS_NRT`) | 1 km, mesma chave, mesma latência; serve para **confirmar persistência** quando o VIIRS falha (nuvem) |
| **Rótulo histórico (frente A)** | **MapBiomas Fogo** (30 m, Landsat, 1985–2025) + **MCD64A1 v6.1** + **dNBR** (Landsat C2 L2 / Sentinel-2 L2A) | Área queimada, não detecção NRT |
| **Risco meteorológico (baseline comparativo)** | **Risco de Fogo do INPE** (FWI observado + previsão 3 dias) | Já existe, é público e é o *baseline* contra o qual a frente A precisa se posicionar |
| **Não usar como detecção NRT** | MapBiomas **Alerta** (é **desmatamento**), GFAS (é **emissão assimilada**, 0.1°, ~7,5 h), EFFIS (só Europa e **redistribui o FIRMS**) | Ver ESTADO_DA_ARTE §1 |

### 12.2 Correções de premissa (obrigatórias)

| Premissa | Correção |
| :--- | :--- |
| `INPE_MONITORQUEIMADAS` | **Não existe com esse nome.** O INPE mantém o **Programa Queimadas / BDQueimadas**, com **dados abertos e sem chave**. O adapter `inpe.py` passa a ler de lá. `INPE_API_KEY` do `.env.example` **não tem** contraparte real — remover |
| `MapBiomas Alerta` como fonte de fogo | É **desmatamento**. O produto de fogo é **MapBiomas Fogo** (anual/mensal) |
| `FIRMS_GOES` / `GOES16_ABI` como SOURCE do FIRMS | O `/api/area` **não lista GOES** (`GOES_NRT` só aparece em `/api/data_availability`). O caminho de GOES é o **produto NOAA `ABI-L2-FDC`**, adapter próprio |
| `GOES-16` | **Foi substituído pelo GOES-19 como GOES East em 07/04/2025.** O adapter nomeia o **sensor** que vier no payload, não o satélite presumido. O INPE ainda rotula "GOES-16 BR" — não copiar esse rótulo |
| `MCD14DL` como LST | É **fogo ativo MODIS NRT**. LST diária = **MOD11A1 / MYD11A1** |
| "SAF/EDMI" | Sigla **não verificada**. Usar índices reais: SPI/SPEI/scPDSI/MCWD (JRC) + ANA "Monitor de Secas" + CEMADEN |
| "ITU-R BT.839" | **Não localizada** (T.839 da ITU-T é JPEG XR). O padrão real de mensagem de alerta é **CAP — ITU-T X.1303 / OASIS CAP v1.2** (ver D-014) |

### 12.3 Ordem de implementação dos adapters

1. `firms.py` — VIIRS NOAA-20 NRT (já provado por coleta real em 21/10/2026: 811 registros,
   14 colunas). Base: `scripts/probe_firms.py`.
2. `inpe.py` — Programa Queimadas (CSV público). **Independência real do FIRMS** precisa ser
   verificada na F2 (o INPE processa sensores próprios).
3. `goes_abi.py` — NOAA `ABI-L2-FDC` do bucket `noaa-goes16`. Alto valor (10 min) e
   **alto risco** (viés de terreno; coordenada deslocada em relevo — marcar no registro).
4. `firms.py` (segunda rota) — MODIS NRT, para confirmação por sensor de resolução menor.
5. `mapbiomas.py` / `dnb.r` — **frente A**, não F2.

### 12.4 Implica

- **D-004 é mantida** (multi-fonte desde o início) e **corrigida quanto aos nomes**.
- A cadeia tem **dois** caminhos de dados com **latências diferentes** (NRT < 3 h e GOES
  10 min) — o schema canônico precisa suportar explicitamente "releitura" do mesmo fogo
  por sensores distintos (D-013).
- **Chave FIRMS**: obtida em 21/10/2026 e gravada em `.env` (gitignored). Foi emitida
  para um e-mail descartável — **reemitir sob e-mail institucional** (issue #13) e mover
  para `secrets/`.
- Atribuição/licença por fonte → issue **#07** (continua pendente, agora com conteúdo).

---

## D-013 — Dedup entre sensores: o que é "o mesmo fogo" e o que é "outro fogo"

**Data:** 21/10/2026 · **Status:** vigente (implementa D-004 e D-010)

**Por quê:** o mesmo incêndio aparece no VIIRS, no MODIS e no GOES, com instantes e
resoluções diferentes. Sem dedup, a contagem de focos é inflada e o agrupamento geográfico
quebra (D-004). Mas D-010 proíbe **descartar em silêncio** — e dedup que apaga linha é
descarte.

**O quê:** três níveis, cada um com critério explícito e auditável.

### Nível 1 — leitura duplicada (mesmo sensor, mesma passagem)

Chave natural: `produto + satelite + acq_date + acq_time + scan + track + lat + lon`.
Índice **UNIQUE** em `focos`. É idempotência de ingestão, não decisão de domínio.

### Nível 2 — mesmo fogo visto por sensores diferentes (**dedup cross-sensor**)

Duas leituras são **o mesmo fogo** se, e somente se:

```
|Δt|  ≤  6 h          (tempo entre as duas aquisições)
d     ≤  max(raio_pixel_m1, raio_pixel_m2)   (distância entre as coordenadas)
```

- `raio_pixel_m` por sensor: **VIIRS 375 m**, **MODIS 1 000 m**, **GOES ABI 2 000 m**
  (no sub-satélite; cresce até a borda do disco — por isso GOES nunca "ganha" a
  coordenação de um registro de outro sensor).
- O limiar espacial é o do sensor **mais grosseiro**: um pixel MODIS (1 km) e um pixel
  VIIRS (375 m) do mesmo incêndio podem diferir em quase 1 km.
- O limiar temporal de 6 h é **parâmetro configurável** (`dedup_janela_horas`), com
  valor inicial justificado pelo espaçamento de passagem de uma bacia polar (INFERÊNCIA —
  **não verificada nesta sessão**): a F2 tem de **calibrar** contra dados reais e
  registrar o valor escolhido no `DECISIONS.md`.

**O que o dedup NÃO faz:** não apaga nada. As leituras continuam em `focos`, cada uma com
seu `raw`. O dedup as **agrupa**: `focos.grupo_id` aponta para `focos_grupos`, que guarda
o grupo (uma manhã). Um grupo tem:
- `leitura_representante` — a leitura de **maior confiança** (`h` > `n` > `l`); em empate,
  a de maior FRP; o `grupo_id` aponta para ela;
- `sensores` — a lista de sensores que viram o fogo (é isso que alimenta
  `fontes_concordantes` no alerta);
- `n_leituras` — quantas leituras de sensor compuseram o grupo.

### Nível 3 — evento (vários fogos próximos)

Clustering espaço-temporal sobre **grupos**, não sobre leituras:
`d ≤ 1 500 m` e `janela ≤ 6 h` (parâmetros de `eventos_fogo`, §5.2 do PLANO).
`eventos_fogo.n_focos` = **número de grupos** (fogos distintos), e
`eventos_fogo.n_leituras` = número de leituras de sensor.

### O que isso compra

- A contagem de focos de um incêndio **não** infla por sensor.
- A concordância entre fontes vira **fato verificável** (`fontes_concordantes`), não
  adjetivo.
- **Nada é suprimido** (D-010): um evento com uma única leitura isolada continua
  gerando alerta, com confiança baixa e `possivel_falso_positivo = true`.

**Implica:**
- `focos` ganha `grupo_id` (FK para `focos_grupos`), `confianca` canônica
  (`low|nominal|high`), `scan_angle`, `track_angle`, `dia_noite`, `versao_produto`.
- Nova tabela `focos_grupos` (§5.10 do PLANO).
- A F2 implementa isso com **teste de fixture** (mesmo fogo em 2 sensores → 1 grupo,
  2 leituras preservadas).

---

## D-014 — Schema canônico definitivo e padrão de mensagem

**Data:** 21/10/2026 · **Status:** vigente (fecha o §5 do PLANO)

**Por quê:** a coleta real de 21/10/2026 provou que o schema **documentado** e o
**observado** divergem em nomes, em unidades e em formato (`docs/ESTADO_DA_ARTE.md` §7).
Adapter que implemente a documentação quebra em produção.

### 14.1 Regras que a coleta real impôs

| Observado | Regra no canônico |
| :--- | :--- |
| `acq_time` = `353` (HHMM **sem zero à esquerda**) | parsear como inteiro e recompor `03:53`; **UTC** |
| `confidence` = `l`/`n`/`h` | canônico `low`/`nominal`/`high`; guarda-se o valor cru no `raw` |
| `satellite` = `N20` | `satelite` canônico = `NOAA-20`; `satelite_codigo` = `N20` (cru) |
| `bright_ti4`/`bright_ti5` (VIIRS) vs `brightness`/`bright_t31` (MODIS) | `bright_ti_k` + `bright_ti_banda` + `bright_ti2_k` + `bright_ti2_banda` |
| lat/lon com **2 a 5 decimais** variáveis | `double precision` + `raio_pixel_m` **obrigatório** |
| `frp` em **MW** | `frp_mw numeric` |
| `scan`/`track` presentes | `scan_angle`, `track_angle` |
| `version` = `2.0NRT` | `versao_produto` |
| `daynight` = `D`/`N` | `dia_noite` |
| GOES: coordenada **não corrigida para o terreno** | `posicao_terreno_corrigida boolean not null default true` — GOES entra como `false`, e o alerta declara a incerteza maior |
| Não existem `type`, `country`, `state`, `icao_id` no `/api/area` | não depender deles; `fonte` + `raw` bastam |

### 14.2 Tabela de proveniência por fonte

Nova tabela `fontes` (`fonte`, `nome`, `produto`, `resolucao_m`, `latencia_horas`,
`url`, `termos`, `atribuicao_requerida`, `licenca`, `chave_requerida`, `ativo`).
É a **fonte da verdade** para o duty de atribuição (issue #07) e para a camada de
referência do PLANO §5.9.

### 14.3 Padrão de mensagem: CAP, não BT.839

O briefing apontava "ITU-R BT.839" como padrão de alerta de incêndio. **A norma não foi
localizada** — `T.839` da ITU-T é *Still-image compression — JPEG XR*
(<https://www.itu.int/ITU-T/recommendations/rec.aspx?id=13914>, 21/10/2026).
O padrão **verificado** que existe e serve é o **CAP — Common Alerting Protocol**:
ITU-T X.1303 (CAP 1.1) e OASIS CAP v1.2 —
<https://www.itu.int/ITU-T/recommendations/rec.aspx?rec=12150> ·
<https://docs.oasis-open.org/emergency/cap/v1.2/pr02/CAP-v1.2-PR02.pdf> (21/10/2026).
Ele dá targeting geográfico por **círculo** (casa com a incerteza posicional do foco),
multilíngue, tempos efetivos/expiração, atualização e cancelamento.

**Implica:**
- O payload do alerta **pode** ser serializado em CAP sem mudar o conteúdo — a geometria
  vira um círculo de raio = `raio_pixel_m`, e o `expires` vem da janela do evento.
- **O conteúdo continua sendo "fato, não instrução"** (D-011): CAP define *como* estruturar
  a mensagem, não *o que* dizer. Nenhum campo CAP é usado para introduzir linguagem
  imperativa.
- CAP **não** é adotado como ** interoperabilidade obrigatória** com terceiros agora:
  uso de CAP no Brasil para alerta de incêndio **NÃO VERIFICADO**. Fica como formato
  interno do payload de entrega.

### 14.4 Ajustes no PLANO

`PLANO_ARQUITETURA.md` §5.1 e §5.2 (tabelas `focos`, `eventos_fogo`), §5.10 (nova),
§5.11 (`fontes`), §6 (adapters) e §12 (fases) foram atualizados com o que está acima.

---

## D-015 — Revisão de D-008: o piso de latência para o Pará é < 3 h, não ≤ 1 h

**Data:** 21/10/2026 · **Status:** vigente (revisão de D-008, não revoga D-008)

**O que mudou:** D-008 fixou "notificação de detecção em **≤ 1 h** a partir da aquisição
do satélite". A apuração de 21/10/2026 mostrou que esse número **não é alcançável com
FIRMS fora dos EUA/Canadá**:

- FIRMS define **RT** = até 60 min e **URT** = < 60 s, mas **URT/RT existem só para
  EUA e Canadá** ("for much of the US and Canada") —
  <https://firms.modaps.eosdis.nasa.gov/api/area> ·
  <https://www.earthdata.nasa.gov/data/tools/firms/faq> (21/10/2026).
- Para o resto do mundo (e portanto para o Pará) a modalidade disponível é **NRT, com
  latência < 3 h** — "FIRMS makes the NRT data available within 3 hours of a satellite
  observation (on a best-effort basis)" — mesma fonte.

**Reformulação (mantém o espírito de D-008, corrige o número):**

| Bloco | Latência-alvo | Como |
| :--- | :--- | :--- |
| **Recência** (o fogo está ativo agora?) | **≤ 30 min** | **GOES ABI FDC** (FHS a cada 10 min) |
| **Detecção de alta resolução** (onde, com que tamanho) | **< 3 h** | **FIRMS VIIRS NRT** |
| **Risco (frente A)** | ciclo **diário** | inalterado |

**Por que 30 min e não 1 h:** o GOES-19/16 produz FHS a cada **10 min**
(<https://www.star.nesdis.noaa.gov/atmospheric-composition-training/documents/G16_ABI_FDC_ReadMe.pdf>,
21/10/2026). Um ciclo de coleta de 15 min sobre GOES entrega recência em ≤ 30 min.
O "< 3 h" continua sendo a verdade do VIIRS e é o que a **detecção de alta resolução**
custa.

**Implica:**
- A promessa pública (issue #19) passa a ser **"detecção NRT"** (≤ 3 h) + **"recência
  de atividade por GOES"** (≤ 30 min) — nunca "previsão em tempo real" (D-008, R3).
- **A questão de fundo é mais séria que o número:** GOES-16 é o **GOES East** até
  07/04/2025; **o GOES East operacional hoje é o GOES-19**, enquanto o INPE ainda rotula
  "GOES-16 BR" nos downloads. A instrumentação do produto `ABI-L2-FDC` precisa ser lida
  do payload, não presumida.



---

## D-008 — Latência-alvo do alerta

**Data:** 21/10/2026 · **Status:** vigente — **revisado por D-015** (21/10/2026)

**O quê:** notificação de detecção em **≤ 1 h** a partir da aquisição do satélite;
risco (frente A) em ciclo **diário**.

**Por quê:** 1 h é defensável institucionalmente com GOES-16/FIRMS e útil para turno de
campo; a frente A é intrinsecamente diária e não pode ser vendida como "tempo real".

**Implica:** D-004 é pré-requisito. A promessa pública deve ser "detecção NRT" e
"risco diário", nunca "previsão em tempo real".

> ⚠️ **Revisão D-015 (21/10/2026):** o número "≤ 1 h" **não é alcançável com FIRMS
> fora dos EUA/Canadá** — URT/RT existem só para EUA/Canadá; para o Pará o piso do
> FIRMS NRT é **< 3 h**. O alvo foi **reformulado por bloco** em D-015:
> **recência ≤ 30 min (GOES ABI FDC)** + **detecção de alta resolução < 3 h (FIRMS VIIRS
> NRT)** + **risco diário**. A decisão **não foi revogada** — foi corrigida com a
> evidência da apuração (`docs/ESTADO_DA_ARTE.md` §1.1 e §8-RK6).

