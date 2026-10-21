# PLANO_ARQUITETURA — Sistema de Alerta de Incêndio Florestal

> Documento canônico de arquitetura. Substitui `docs/arquivo/arquitetura_do_backend_do_sistema.md`.
> Decisões com data e justificativa → `DECISIONS.md`.

---

## 1. Objetivo

Detectar **focos de incêndio** por satélite sobre as áreas geridas pelo IDEFLOR-Bio,
**avaliar** e **notificar** a Gerência Regional responsável, com painel WebGIS.
Em paralelo, duas frentes analíticas: **risco de ignição** (ML + SHAP) e **propagação**
(nowcast) do fogo ativo.

## 2. Conceito: três frentes sobre uma espinha

```
                     ┌──────────────────────────────────────────┐
   FRENTE 0          │  ESPINHA (F1–F5)                        │
   (detecção)        │  Satellite → adapter → focos canônicos   │
                     │  → dedup/cluster → eventos → regras       │
                     │  → alertas → entrega                      │
                     └──────────────────────────────────────────┘
                          │                  │                 │
              ┌───────────┘                  │                 └────────────┐
              ▼                              ▼                              ▼
   ┌────────────────────┐      ┌──────────────────────┐      ┌────────────────────┐
   │ A — Risco ignição  │      │ B — Propagação       │      │ Painel MapLibre    │
   │ ML + SHAP (diário) │      │ nowcast (6–24 h)     │      │ + entrega/alerta   │
   └────────────────────┘      └──────────────────────┘      └────────────────────┘
```

**A frente 0 é o produto.** A e B somam valor quando existirem, mas **nenhuma delas
bloqueia** F1–F5. Se o ML nunca sair, o sistema de detecção e alerta continua útil e
publicável.

## 3. Carta de responsabilidade

| Ator | Faz | Não faz |
| :--- | :--- | :--- |
| **NGEO / IDEFLOR** | Detecta, avalia, **notifica**, publica painel e relatório | Executa ação de combate; não assume o atendimento |
| **Gerência Regional** | Recebe alerta, executa protocolo de ação, reporta | Não é fonte detruth do dado |

**Consequência de modelagem:** `alertas` é registro imutável do que foi notificado.
Não existe estado de atendimento, nem atribuição, nem SLA. O que mede o produto é
**precisão do alerta** e **cobertura**. (D-003)

## 4. Arquitetura de alto nível

```
┌───────────────┐   ┌───────────────┐   ┌────────────────┐   ┌──────────────┐
│  Fontes de    │   │  Coletor      │   │  PostGIS       │   │  Motor de    │
│  focos        │──▶│  (Celery)     │──▶│  focos         │──▶│  regras      │
│  FIRMS        │   │  scheduler    │   │  eventos_fogo  │   │  config_alerta│
│  INPE MQ      │   │  1–5 min      │   │  alertas       │   │              │
│  GOES-16 AWS  │   └───────────────┘   │  entregas      │   └──────┬───────┘
└───────────────┘                       │  config_alerta │          │
                                        │  geometrias    │          ▼
                                        └────────┬───────┘   ┌─────────────┐
                                                 │           │  Entregador  │
                              ┌──────────────────┼───────┐   │  SMTP /     │
                              ▼                  ▼       ▼   │  Telegram / │
                        ┌──────────┐      ┌──────────┐ ┌────┐│  WhatsApp / │
                        │ pg_tileserv│      │ titiler  │ │MVT ││  Webhook    │
                        │ (vetor)  │      │ (raster) │ └────┘└─────────────┘
                        └────┬─────┘      └────┬─────┘
                             └───────┬─────────┘
                                     ▼
                        ┌────────────────────────┐
                        │ Frontend MapLibre GL JS │
                        │ (dashboard/alertas)     │
                        └────────────────────────┘
```

## 5. Schema canônico (PostGIS)

```sql
-- 5.1 Focos: canônico, multi-fonte. Uma linha por leitura de sensor.
focos (
  id              bigserial primary key,
  fonte           text not null,          -- 'FIRMS_MODIS' | 'FIRMS_VIIRS' | 'FIRMS_GOES'
                                        -- | 'INPE_MONITORQUEIMADAS' | 'GOES16_ABI'
  satelite        text,
  sensor          text,
  swath           text,
  acquisition_time timestamptz not null,
  lat             double precision not null,
  lon             double precision not null,
  geom            geometry(Point, 4326) not null,
  bright_ti_k     numeric,                -- temperatura de brilho (K)
  frp_mw          numeric,                -- fire radiative power (MW)
  confianca       text,                   -- low | nominal | high
  raio_pixel_m    numeric,                -- 375 (VIIRS) | 750 (GOES) | 1000 (MODIS)
  raw             jsonb,                  -- payload original da fonte
  criado_em       timestamptz default now()
);
create index on focos using gist (geom);
create index on focos (acquisition_time desc);

-- 5.2 Evento: agrupamento espacial-temporal de focos = "ocorrência de fogo".
--     É agregação, não máquina de estados.
eventos_fogo (
  id            bigserial primary key,
  geom_centro   geometry(Point, 4326) not null,
  bbox          geometry(Polygon, 4326) not null,
  n_focos       int not null,
  fontes        text[] not null,
  primeira_hora timestamptz not null,
  ultima_hora   timestamptz not null,
  frp_max       numeric,
  frp_acumulado numeric,
  raio_estimado_m numeric,
  uc_id         bigint,                  -- null se fora de UC/ZA
  distancia_uc_m numeric,
  derivacao     text not null             -- regra de cluster usada (transparência)
);

-- 5.3 Alerta: registro imutável do que foi notificado.
--     Sempre emitido quando o evento toca uma UC (D-010). A incerteza é declarada,
--     nunca escondida por supressão.
alertas (
  id              uuid primary key default gen_random_uuid(),
  evento_fogo_id  bigint references eventos_fogo(id),
  tipo            text not null,          -- 'FOCO_EM_UC' | 'FOCO_PROXIMO_UC'
                                        -- | 'RISCO_ALTO' | 'PROPAGACAO'
  gerencia_id     text not null,
  uc_id           bigint,
  uc_nome         text,
  severidade      text not null,          -- baixa | media | alta | critica
  confianca       text not null,          -- alta | media | baixa
  possivel_falso_positivo boolean not null default false,
  n_focos         int not null,
  fontes_concordantes text[],             -- ex.: {FIRMS_VIIRS, GOES16}
  -- contexto do plano de gestão (verbatim; pode ser nulo). Fato, nunca instrução (D-011).
  zona_sigla      text,
  zona_texto      text,
  zona_disponivel boolean not null default false,  -- false = UC sem zoneamento
  regra_id        text not null,
  titulo          text not null,
  mensagem        text not null,
  geom            geometry(Geometry, 4326),
  janela_ini      timestamptz,
  janela_fim      timestamptz,
  gerado_em       timestamptz not null default now()
);

-- 5.4 Entregas: log de envio (append-only).
entregas (
  id           bigserial primary key,
  alerta_id    uuid not null references alertas(id),
  canal        text not null,             -- email | telegram | whatsapp | webhook
  destinatario text not null,
  status       text not null,             -- enviado | erro | suprimido
  resposta_http int,
  erro         text,
  enviado_em   timestamptz not null default now()
);

-- 5.5 Configuração por Gerência Regional (o "protocolo" do D-003, versionado).
config_alerta (
  id            serial primary key,
  gerencia_id   text not null,
  tipo_alerta   text not null,
  severidade_min text not null,
  raio_buffer_m int not null default 0,
  janela_h      int not null default 6,
  canal         text not null,
  destinatarios text[] not null,
  ativo         boolean not null default true,
  template      jsonb,
  unique (gerencia_id, tipo_alerta, canal)
);

-- 5.6 Referência geográfica
gerencias_regionais (
  id       text primary key,          -- 'GRB', 'GRX', 'GRCN-I', ... (canônico)
  nome     text not null,             -- 'Gerência Regional de Belém'
  ativa    bool not null default true
);
ucs (
  id        bigserial primary key,
  nome      text not null,
  geom      geometry(MultiPolygon,4326),
  gerencia_id text not null references gerencias_regionais(id),
  zona_amortecimento geometry(MultiPolygon,4326),   -- NULL onde não há ZA cartografada
  props    jsonb
);

-- 5.7 Zonas de plano de manejo (camada de referência do IDEFLOR).
--     VERBATIM. Cada plano de gestão nomeia e define as suas próprias zonas —
--     NÃO existe taxonomia global e nada aqui é padronizado (D-009).
--     `sigla` NÃO é global: 'ZA' = 'Alta Intervenção' em Algodoal-Maiandeua
--     e = 'Zonas de Amortecimento' em Trombetas. Nunca usar como chave de regra.
ucs_zonas (
  id        bigserial primary key,
  uc_id     bigint references ucs(id),        -- resolvido por sobreposição espacial
  sigla     text,                            -- código original do zoneamento (verbatim)
  zona      text,                            -- texto original do plano (verbatim)
  area_ha   numeric,
  geom      geometry(Polygon,4326)
);

-- 5.8 Curadoria por UC: NAO EXISTE.
--     A zona do plano de gestão é INFORMAÇÃO, não variável. O sistema não avalia
--     nem codifica permissão de fogo em zona alguma (D-009). O único uso da zona
--     é constar do alerta, verbatim.
```

### 5.9 Camada de referência (entradas e proveniência)

| Arquivo | Registros | Uso |
| :--- | :--- | :--- |
| `data/shapes_de_todas_as_unidades_com_gerencia.geojson` | 29 UCs com `gerencia` + `id` 1..29 | `ucs` |
| `visualizador/data/zoneamentos_ucs_estaduais.geojson` | 252 zonas em **16** das 29 UCs | `ucs_zonas` |
| `visualizador/data/concessoes_florestais_ideflor.geojson` | 11 concessões | feature de risco (frente A) |
| `visualizador/data/contratos_de_transicao.geojson` | 43 contratos de transição | feature de risco (frente A) |
| `visualizador/data/{terras_indigenas,quilombos_*,regioes_integracao}.geojson` | contexto | camadas do mapa |

**Gerências (DGMUC) — 9, cobrindo as 29 UCs:**

| id | nome | UCs |
| :--- | :--- | :--: |
| `GRCN-I` | Gerência Regional da Calha Norte I | 2 |
| `GRCN-II` | Gerência Regional da Calha Norte II | 5 |
| `GRCN-III` | Gerência Regional da Calha Norte III | 2 |
| `GRB` | Gerência Regional de Belém | 4 |
| `GRTUC` | Gerência Regional de Tucuruí | 3 |
| `GRA` | Gerência Regional do Araguaia | 2 |
| `GRM` | Gerência Regional do Marajó | 2 |
| `GRNE` | Gerência Regional do Nordeste | 4 |
| `GRX` | Gerência Regional do Xingu | 5 |

> ✅ **Issue #21 resolvida no arquivo.** A sigla vinha como `GRCN-l`, `GRCN-ll`,
> `GRCN-lll` (L minúsculo no lugar do I romano). O arquivo foi corrigido em 21/10/2026
> (digest original e digest corrigido registrados em `data/README.md`). O seed ainda
> valida 29 UCs / 9 gerências, porque o arquivo original volta da instituição.

**Join das zonas → UCs: por SOBREPOSIÇÃO ESPACIAL, nunca por nome.** O campo `UNIDADE`
do zoneamento está **truncado** ("Ambiental da Ilha de Combu", "Reserva Biológica do
Maicuru (REBIO") e não casa com o nome da UC. Issue #23.

**Cobertura:** o zoneamento cobre **16 das 29 UCs**. As 13 restantes **não têm**
classificação de zona → o alerta segue sendo emitido, apenas **sem contexto de zona**,
e o campo `zona_texto` fica nulo com a limitação explícita. Issue #24.



> **Nota de precisão:** `raio_pixel_m` existe porque a posição do foco é **o centro de
> um pixel**, não uma coordenada de precisão. A interface deve mostrar o círculo de
> incerteza, nunca um pino com falsa exatidão.

## 6. Camada de ingestão multi-fonte

```
adapters/
├── firms.py          MODIS / VIIRS / GOES via API FIRMS
├── inpe.py           MONITORQUEIMADAS
├── goes16.py         AWS Open Data (noaa-goes16) + detecção própria OU produto FIRMS
└── base.py           contrato: fetch() -> list[FocoCanonico]
```

Regras do adapter:
1. **Um schema canônico.** Nenhum consumidor sabe qual fonte originou o foco além de
   `fonte`/`satelite`/`sensor`.
2. **Dedup cross-sensor.** O mesmo incêndio aparece no MODIS e no VIIRS. Deduplicação por
   **janela temporal + proximidade espacial**, não por igualdade de coordenada.
3. **Proveniência sempre.** `raw` guarda o payload original; `fonte` identifica a origem.
4. **Falha de uma fonte não derruba as outras.** O coletor isola erros por adapter.
5. **Atribuição/licença por fonte** registrada → issue #07.

## 7. Motor de regras → alertas

Configuração por gerência (`config_alerta`), regras avaliadas a cada ciclo:

| tipo | condição inicial | severidade |
| :--- | :--- | :--- |
| `FOCO_EM_UC` | foco dentro da UC ou da ZA | por nº de focos na janela |
| `FOCO_PROXIMO_UC` | foco a < R metros do limite | por distância e nº de focos |
| `RISCO_ALTO` | score da frente A acima do limiar da gerência | por faixa de score |
| `PROPAGACAO` | frente B estima alcance da UC | por tempo até o limite |

**Qualificação da confiança (obrigatória — e é o que substitui a supressão, D-010):**

O sistema **nunca descarta um foco em silêncio**. Todo evento que toca uma UC **gera
alerta**. O que muda é a severidade e a confiança declaradas:

| sinal observado | severidade | `possivel_falso_positivo` |
| :--- | :--- | :--- |
| 1 foco isolado, diurno, sem concordância entre fontes | `baixa` | sim |
| 1 foco, noturno, fonte única | `media` | sim |
| N focos em janela curta, mesma área | `alta` | não |
| N focos + persistência temporal + concordância entre fontes | `critica` | não |

**Agregação ≠ supressão.** N focos do mesmo incêndio viram **um evento, um alerta**
(anti-spam, não descarte). Filtros de geometria e qualidade (nuvem, chuva recente,
fogo possivelmente de manejo) **qualificam a confiança**; nunca descartam.

**A zona do plano de gestão entra como fato, nunca como interpretação:**

- Foco dentro de uma zona de plano de manejo → **alerta é emitido do mesmo jeito**.
- O alerta carrega `zona_sigla` e `zona_texto` (verbatim do plano) e a coordenada.
- Mensagem: *"Foco em <UC> — zona *<texto do plano>*. Posição <lat/lon> (±<resolução>)."*
- **Nada de instrução.** Nada de "verifique antes de agir", nada de lembrete sobre o
  plano, nada de interpretação. O gestor sabe qual é o plano da própria unidade; o
  sistema entrega o fato (D-011).
- Se a UC **não tem** zoneamento (13 de 29), o alerta é emitido **sem contexto de zona**,
  com a limitação explícita, e não com suposição.



> Sem esse filtro, o sistema queima a confiança da gerência em poucas semanas.
> Ver `AGENTS.md` → Regras de domínio.

## 8. Canais de entrega

Registry de canais, todos com log em `entregas`:

| canal | uso | notas |
| :--- | :--- | :--- |
| `email` | **default** | SMTP; plantilla com link pro painel |
| `telegram` | baixo atrito, resposta rápida | bot API; MVP do canal assíncrono |
| `whatsapp` | canal operacional no campo | Meta Cloud API; exige URL pública — o **Cloudflare Tunnel** já configurado no `.env` resolve |
| `webhook` | integração com sistemas da gerência | genérico |

**O alerta é um instrumento, não uma mensagem.** Ele entrega **material** para decisão
rápida e nada mais:

```
FOCO DETECTADO — 21/10 14:22 BRT
UC ........ Floresta Estadual do Trombetas (GRCN-II)
Zona ....... Zonas de Amortecimento
Posição .... 1.4587°S 56.7321°W  (±375 m)
Severidade . ALTA        Confiança: ALTA
Focos ...... 7 em 2h10   Fontes: FIRMS_VIIRS, GOES16
[ abrir no mapa ]
```

- **Fatos, não conselhos.** Sem "verifique antes de agir", sem "recomenda-se", sem
  "atenção", sem explicação de termo técnico. O destinatário é gestor de gerência
  regional: conhece a unidade, o plano e o terreno.
- **Só o que não é óbvio.** A UC e a zona identify o lugar; a severidade e a confiança
  dizem o grau de certeza; o link abre o mapa. O resto é ruído.
- **Coordenada em decimal e em UTM** (SIRGAS 2000, fuso 21S/22S) — é o que vai para o
  GPS da equipe de campo. O EPSG exato fica resolvido no código (pyproj), não fixado
  em doc.
- Sem "quem é o responsável" no corpo: o **roteamento** já entrega à gerência certa.
  A gerência responsável fica no registro do alerta, não na mensagem.


## 9. Frontend — MapLibre GL JS

**Princípio de interface: instrumento, não narrativa (D-011).**

O dashboard é para quem já sabe o que é uma UC, um foco de calor e uma gerência
regional. Não é vitrine, não é tutorial, não é página institucional.

- **Sem landing page.** O app abre direto no mapa, com a fila de alertas. Nada de
  hero, scroll-telling, "saiba mais" ou CTA institucional.
- **Sem texto explicativo.** Nenhum parágrafo, nenhum tooltip que explique o que é FRP
  ou o que é zona de amortecimento. Legenda de mapa sim (é dado, não narrativa).
- **Densidade alta.** Números na mesa. Gráfico mínimo. Sem parágrafo em lugar nenhum.
- **Rótulos técnicos e curtos** — vocabulário do domínio, não de marketing:
  `focos`, `FRP`, `severidade`, `confiança`, `janela`.
- **Filtros e atalhos**, não tutoriais. O gestor que volta toda semana não quer ler
  instruções.
- **O mapa é a tela.** Painéis são secundários e retráteis.
- **Aberto, sem login no MVP** (rede institucional). Autenticação só quando houver dado
  que exija (issue #28).

**Layout (HUD de centro de comando):**

```
┌──────────────────────────────────────────────────────────────────────┐
│ barra institucional (gov.br) + status de frescor dos dados           │
├───────────────┬──────────────────────────────────┬───────────────────┤
│ FILA DE       │                                  │ PAINEL DA UC      │
│ ALERTAS       │        MAPA MAPLIBRE             │ (ao clicar)       │
│ (ordenada     │   • heatmap de focos             │ • severidade      │
│  por data)    │   • camada UCs + ZA             │ • nº focos 24h    │
│ • filtro por  │   • pontos de foco (círculo de   │ • série temporal  │
│   gerência    │     incerteza)                  │ • driver do risco   │
│ • filtros     │   • camada de alertas           │   (frente A)      │
│   temporal    │   • camada de propagação (B)    │ • exportar        │
├───────────────┴──────────────────────────────────┴───────────────────┤
│ RODAPÉ TEMPORAL: scrubber 24h–7d · play/pause · sincronizado ao mapa  │
└──────────────────────────────────────────────────────────────────────┘
```

**Camadas MapLibre:**
- `heatmap` — densidade de focos (nativo do MapLibre; recria o "onde está concentrate o calor").
- `circle` — focos individuais, com raio = `raio_pixel_m` (incerteza).
- `fill`/`line` — UCs, ZA, área de amortecimento do alerta.
- `raster` — risco (frente A) e propagação (frente B), servido por `titiler`.

**Serviços:**
- Vetorial (UCs, ZA, alertas): **MVT** via `pg_tileserv` (ou Martin) a partir do PostGIS.
- Raster (risco, propagação): **XYZ** via `titiler`/rio-tiler sobre COG.
- Basemap: raster OSM/Esri no MVP → auto-hospedado (issue #06).

**Offline (para campo):** service worker + cache de tiles da janela recente + **"Pacote da UC"**
(GeoJSON + raster + PDF) baixável. O `.env` já tem `TUNNEL_TOKEN` para URL pública.

## 10. Frente A — Risco de ignição (ML + SHAP)

- **Alvo:** `P(ocorrência de fogo na UC nos próximos N dias)`, N ∈ {7, 30}.
- **Unidade:** célula de análise (1 km) recortada em UC + ZA; agregação para a UC.
- **Rótulo:** área queimada (dNBR / MCD64A1 / MapBiomas Fogo) — com cuidado: POINT
  (foco) herda viés de detecção; área queimada é mais completa mas atrasa 16–30 dias.
- **Features:** LST (MOD11A1), NDVI, chuva (CHIRPS/ERA5), seca (SAF/EDMI), cobertura de
  combustível (WorldCover/MapBiomas), distância a contratos de transição *(pasto em pousio =
  capim seco = combustível)*, distância a concessões *(TIPO A = pressão alta)*, borda de UC,
  estradas, distância a TI/quilombos, histórico de queima, densidade de raios.
- **Zonas de plano de manejo: não entram como feature.** A zona é **informação** que
  consta do alerta, verbatim (D-009). O sistema não avalia, não codifica e não infere
  permissão de fogo em zona alguma — quem diz o que o plano permite é o plano.
  Consequência aceita: o confundidor "fogo de manejo" **permanece como limitação
  declarada** nos rótulos da frente A (§10), não como problema resolvido.

- **Modelo:** XGBoost/LightGBM. **Validação:** *block CV espacial* + holdout temporal —
  nunca split aleatório sobre pixels (vazamento espacial).
- **Calibração:** isotônica/Platt → o número em % precisa significar algo.
- **Métricas:** AUC-PR, **precision@k** ("dos 10% de maior risco, quanto queimou?"),
  Brier/curva de calibração, recall@k por UC.
- **SHAP:** global (drivers do modelo) e local (drivers do alerta daquela UC).
- **Repo:** `ml-fire-alert` (recriado). Entrega ao sistema como **artefato versionado** +
  `model_card.json` (D-006).

## 11. Frente B — Propagação (nowcast)

Cadeia de dependências:

```
focos ──▶ cluster ──▶ perímetro estimado ──▶ modelo de propagação ──▶ horizonte 6–24 h
```

- **Perímetro:** (a) acumulo de focos em janela (estimativa rápida, NRT) e/ou
  (b) dNBR sob demanda (Sentinel-2/Landsat, 16–30 dias de atraso — serve de **validação**,
  não de nowcast).
- **Propagação:** modelo tipo Rothermel/simplificado, dirigido por **vento** (ERA5/GOES) e
  classe de combustível. Referência de abordagem: EFFIS (produto europeu equivalente).
- **Saída:** polígono de alcance por horizonte → "vai atingir o limite da UC em ~6 h".
- **Alerta `PROPAGACAO`:** a mais acionável de todas — é ela que vira "vá para lá agora".

## 12. Fases

| Fase | Entrega | Depende de |
| :--- | :--- | :--- |
| **F0** | Bootstrap: docs, `.gitignore`, `git init`, este plano | — |
| **F1** | Fundação: docker-compose (PostGIS+Redis), schema, seed de geometrias de referência, `/api/health` | F0, **issue #01** |
| **F2** | Ingestão multi-fonte → `focos` + dedup → `eventos_fogo` | F1, FIRMS key |
| **F3** | Motor de regras + `alertas` + `config_alerta` + `/api/alertas` | F2, **issue #01** |
| **F4** | Entrega multi-canal (email → telegram/whatsapp/webhook) + log | F3 |
| **F5** | Frontend MapLibre: mapa, heatmap, alertas, painel de UC, scrubber temporal | F2/F3 |
| **F6** | **Frente A** em paralelo: dataset, labels, block CV, calibração, SHAP | repo `ml-fire-alert` |
| **F7** | **Frente B** em paralelo: perímetro estimado + propagação por vento | F2, F5 |
| **F8** | Confirmação dNBR sob demanda → relatório de área queimada | F5, Sentinel Hub |
| **F9** | *(não previsto)* | — |

**MVP = F0–F5.** O portal público / scrollytelling **não está no plano**: a decisão é
ferramenta funcional, não página institucional (D-011). Se um dia precisar existir, sai
como artefato da frente A, fora do caminho crítico.


## 13. Identidade visual — `ngeo-ds` (D-005)

- `tokens.css` — custom properties: paleta gov, espaçamento, tipografia, z-index, **escala de severidade**.
- `components.css` — barra institucional, header, card, painel, botão, badge, tabela.
- `fonts/rawline/*.woff2` + `img/` (brasão, logos) — elimina duplicação entre `maps` e `visualizador`.
- Consumo via CDN pinado por tag; sem build; compatível com os três repos.
- **Rampa de calor:** perceptualmente uniforme (inferno/viridis). **Não** usar
  vermelho-amarelo-verde — hostil a daltônicos e com semântica "bom/ruim" errada para
  variável contínua.
- **Severidade:** discreta (baixa/média/alta/crítica) com **ícone + rótulo + cor**,
  funcionando em light e dark. Nunca só cor.

## 14. Riscos e dependências

| # | Risco | Mitigação |
| :--- | :--- | :--- |
| R1 | ~~Mapeamento UC → gerência inexistente~~ **RESOLVIDO** | `data/shapes_de_todas_as_unidades_com_gerencia.geojson` (29 UCs, 9 gerências). Issue #21 resolvida no arquivo |
| R1b | Sigla `GRCN-l` × `GRCN-I` criam gerências fantasma | ✅ corrigido no arquivo (21/10/2026); seed mantém validação 29 UCs / 9 gerências (#21) |
| R1c | `SIGLA` do zoneamento não é global (`ZA` = 2 coisas diferentes) | Regra **nunca** por `sigla`; sem taxonomia global (D-009, #23) |
| R2 | Falso positivo derruba a confiança | **Nunca descartar em silêncio** (D-010): severidade graduada + `possivel_falso_positivo`; alerta entrega o material, o gestor decide |
| R2b | Sistema decidir o que é permitido | Não decidir: **informar** a zona verbatim e a coordenada, sem interpretação e sem instrução (D-009, D-011) |
| R2c | Produto virar landing page / babá | Princípio de interface "instrumento, sem narrativa" (§9, D-011). Sem texto explicativo, sem tutorial, sem CTA |

| R3 | Promessa de tempo real não se sustenta | comunicar "detecção NRT ≤1 h" + "risco diário"; nunca "previsão em tempo real" |
| R4 | Chave/licença de fonte de focos | registrar termos por fonte → issue #07 |
| R5 | Volume de tiles / custo de raster | titiler+COG com pyramid; cache; só janelas úteis |
| R6 | Uso offline em campo sem sinal | service worker + Pacote da UC |
| R7 | Deploy/credencial em ambiente institucional | `.env` por ambiente; nada sensível no git (D-003, D-006) |
| R8 | Zoneamento cobre só 16/29 UCs | alerta segue emitido **sem** contexto de zona, com limitação explícita (#24) |
| R9 | Confundidor "fogo de manejo" nos rótulos | **Limitação declarada**, não resolvida: a zona não entra como feature e não é curada. Declarar no model card e no paper (§10) |


