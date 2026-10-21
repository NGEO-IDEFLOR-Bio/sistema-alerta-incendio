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
alertas (
  id              uuid primary key default gen_random_uuid(),
  evento_fogo_id  bigint references eventos_fogo(id),
  tipo            text not null,          -- 'FOCO_EM_UC' | 'FOCO_PROXIMO_UC'
                                        -- | 'RISCO_ALTO' | 'PROPAGACAO'
  gerencia_id     text not null,
  uc_id           bigint,
  uc_nome         text,
  severidade      text not null,          -- baixa | media | alta | critica
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
gerencias_regionais (id text primary key, nome text not null, ativa bool default true);
ucs (id bigserial primary key, nome text, geom geometry(MultiPolygon,4326),
      gerencia_id text references gerencias_regionais(id),   -- <- depende da issue #01
      zona_amortecimento geometry(MultiPolygon,4326),
      props jsonb);
```

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

**Filtro de qualidade (obrigatório, e é o que define a confiança do sistema):**
- 1 foco isolado, diurno, em área de pasto/capim → suprimir (ruído).
- N focos em janela curta, mesma área → **confirmar** (início de incêndio).
- Sobreposição com área de manejo/fogo programado → marcar como *manejado*, não alertar.
- Chuva recente na célula → reduzir severidade.

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

Template padrão: *o que* (foco/pixel, com incerteza), *onde* (UC, coordenada, link no mapa),
*quando*, *severidade*, *confiança* (nº de focos, fontes, Agreement), *quem é o responsável*.

## 9. Frontend — MapLibre GL JS

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
| **F9** | Portal público / artefatos de paper (a partir da frente A) | F6 |

**MVP = F0–F5.** F9 (público) sai como **artefato da análise**, não como produto à parte:
mapa retrospectivo + drivers SHAP globais.

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
| R1 | **Mapeamento UC → gerência inexistente** | issue #01 — dependência institucional (DGMUC) |
| R2 | Falso positivo derruba a confiança | filtro de qualidade §7 antes de qualquer entrega |
| R3 | Promessa de tempo real não se sustenta | comunicar "detecção NRT ≤1 h" + "risco diário"; nunca "previsão em tempo real" |
| R4 | Chave/licença de fonte de focos | registrar termos por fonte → issue #07 |
| R5 | Volume de tiles / custo de raster | titiler+COG com pyramid; cache; só janelas úteis |
| R6 | Uso offline em campo sem sinal | service worker + Pacote da UC |
| R7 | Deploy/credencial em ambiente institucional | `.env` por ambiente; nada sensível no git (D-003, D-006) |
