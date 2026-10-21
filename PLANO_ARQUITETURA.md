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

> **Revisado em 21/10/2026 (T0)**, à luz da coleta real do FIRMS e de
> `docs/ESTADO_DA_ARTE.md` §7. As mudanças são: campos de proveniência do sensor
> (`produto`, `satelite_codigo`, `versao_produto`, `scan_angle`, `track_angle`,
> `dia_noite`, `posicao_terreno_corrigida`), **canal de brilho parametrizado por banda**
> (o VIIRS entrega `bright_ti4`/`bright_ti5`, o MODIS `brightness`/`bright_t31`),
> `confianca` canônica (`low|nominal|high`, o FIRMS entrega `l|n|h`), a tabela de
> grupos de dedup (§5.10), a tabela de fontes (§5.11) e o desdobramento de
> `n_focos`/`n_leituras` (§5.2). Decisão: `DECISIONS.md` D-012/D-013/D-014.

```sql
-- 5.1 Focos: canônico, multi-fonte. Uma linha por LEITURA DE SENSOR (não por fogo).
--     O mesmo fogo visto por 2 sensores = 2 linhas em `focos`, ligadas por `grupo_id`
--     (D-013). Nada é apagado: dedup agrupa, não descarta (D-010).
focos (
  id              bigserial primary key,
  fonte           text not null,          -- 'FIRMS_VIIRS' | 'FIRMS_MODIS'
                                        -- | 'NOAA_ABI_FDC' | 'INPE_QUEIMADAS'
  produto         text not null,          -- 'VIIRS_NOAA20_NRT' | 'MODIS_NRT'
                                        -- | 'ABI-L2-FDC' | 'FOCOS_QUEBIMADAS'
  sensor          text,                   -- 'VIIRS' | 'MODIS' | 'ABI'
  satelite        text,                   -- canônico: 'NOAA-20' | 'TERRA' | 'GOES-19'
  satelite_codigo text,                   -- cru, como veio da fonte: 'N20' | 'AQUA'
  versao_produto  text,                   -- cru: '2.0NRT' | '3.0'
  acquisition_time timestamptz not null,  -- UTC; acq_date + acq_time (HHMM sem
                                        -- zero à esquerda: '353' = 03:53)
  lat             double precision not null,
  lon             double precision not null,
  geom            geometry(Point, 4326) not null,
  -- Canal de brilho: o sensor define as bandas. VIIRS -> TI4/TI5; MODIS -> MIR/T31.
  bright_ti_k     numeric,                -- temperatura de brilho (K)
  bright_ti_banda text,                   -- 'TI4' | 'TI5' | 'MIR' | 'T31'
  bright_ti2_k    numeric,                -- canal secundário, quando houver
  bright_ti2_banda text,
  frp_mw          numeric,                -- fire radiative power (MW)
  confianca       text,                   -- canônico: low | nominal | high
                                        -- (a fonte entrega l | n | h)
  confianca_crua  text,                   -- cru, como veio: 'l' | 'n' | 'h'
  dia_noite       text,                   -- 'D' | 'N'
  scan_angle      numeric,                -- ângulo de varredura do sensor
  track_angle     numeric,
  raio_pixel_m    numeric not null,       -- 375 (VIIRS) | 1000 (MODIS) | 2000 (GOES, nadir)
  posicao_terreno_corrigida boolean not null default true,
                                        -- false para GOES ABI: a coordenada L2 não é
                                        -- corrigida para o relevo (offset em terreno alto)
  -- Dedup cross-sensor: grupo do mesmo fogo (D-013)
  grupo_id        bigint references focos_grupos(id),
  raw             jsonb,                  -- payload original da fonte
  criado_em       timestamptz default now()
);
create index on focos using gist (geom);
create index on focos (acquisition_time desc);
create index on focos (grupo_id);
-- Idempotência de ingestão: mesma leitura não entra duas vezes (D-013, nível 1)
create unique index on focos
  (produto, satelite_codigo, acquisition_time, scan_angle, track_angle, lat, lon);

-- 5.2 Evento: agrupamento espacial-temporal de FOCOS (grupos) = "ocorrência de fogo".
--     É agregação, não máquina de estados.
eventos_fogo (
  id            bigserial primary key,
  geom_centro   geometry(Point, 4326) not null,
  bbox          geometry(Polygon, 4326) not null,
  n_focos       int not null,            -- nº de FOGOS distintos (= nº de grupos)
  n_leituras    int not null,            -- nº de leituras de sensor que os viram
  fontes        text[] not null,         -- produtos distintos que viram o evento
  sensores      text[] not null,         -- sensores distintos (concordância)
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
  uc_id     bigint references ucs(id),        -- resolvido por SOBREPOSIÇÃO ESPACIAL
  sigla     text,                            -- código original do zoneamento (verbatim)
  zona      text,                            -- texto original do plano (verbatim)
  unidade_origem text,                       -- nome da UC como veio no arquivo (truncado) — auditoria
  area_ha   numeric,
  join_metodo text,                          -- 'centroide_contido' | 'maior_intersecao'
                                            -- | 'sem_intersecao' | 'sem_geometria'
  join_n_candidatas int,                     -- quantas UCs a zona toca (>=2 = mosaico, revisar)
  geom      geometry(Geometry,4326)          -- GEOMETRY: 44 das 252 zonas sao MultiPolygon
);
-- O `geom` e gravado ja saneado (ST_MakeValid): o arquivo do IDEFLOR tem
-- auto-intersecao em varias features, e o `ST_Intersection` lanca TopologyException
-- com geometria crua. O saneamento e tecnico, nao reinterpreta o zoneamento.

-- 5.8 Curadoria por UC: NAO EXISTE.
--     A zona do plano de gestão é INFORMAÇÃO, não variável. O sistema não avalia
--     nem codifica permissão de fogo em zona alguma (D-009). O único uso da zona
--     é constar do alerta, verbatim.
```

### 5.9 Camada de referência (entradas e proveniência)

| Arquivo | Registros | Uso |
| :--- | :--- | :--- |
| `data/shapes_de_todas_as_unidades_com_gerencia.geojson` | 29 UCs com `gerencia` + `id` 1..29 | `ucs` |
| `visualizador/data/zoneamentos_ucs_estaduais.geojson` | 252 zonas; **20** das 29 UCs com zoneamento (medido na F1, 21/10/2026) | `ucs_zonas` |
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

**Cobertura (medida na F1, 21/10/2026 — não é estimativa):**

| | |
| :--- | :--- |
| Zonas no arquivo | **252** |
| Zonas resolvidas a uma UC | **243** |
| Zonas sem UC | **9** (8 sem sobreposição espacial + 1 **sem geometria** no arquivo) |
| **UCs com zoneamento** | **20 das 29** |
| Gerências com pelo menos uma UC zonada | **8 de 9** (GRM/Marajó não tem) |

> ⚠️ **Correção:** até a F0 o repo afirmava "16 das 29 UCs". Esse número vinha
> da **contagem de strings distintas** no campo `UNIDADE` (16 strings) — exatamente o
> erro que a issue #23 warns contra. O **join espacial** (a fonte da verdade) resolve
> **20 UCs**: 117 das 252 zonas tocam **mais de uma** UC (103 tocam 2, 13 tocam 3, 1 toca
> 4) — são mosaicos como o "Mosaico Lago de Tucuruí". As 9 UCs restantes **não têm**
> classificação de zona → o alerta segue sendo emitido, apenas **sem contexto de zona**,
> e o campo `zona_texto` fica nulo com a limitação explícita. Issue #24.



> **Nota de precisão:** `raio_pixel_m` existe porque a posição do foco é **o centro de
> um pixel**, não uma coordenada de precisão. A interface deve mostrar o círculo de
> incerteza, nunca um pino com falsa exatidão.

### 5.10 Grupos de dedup cross-sensor (D-013)

> **Nova em 21/10/2026 (T0).** Um **grupo** = UM fogo visto por 1 ou mais sensores.
> As leituras continuam **todas** em `focos`; o grupo é a **ligação**. Nada é apagado
> (D-010). `focos.grupo_id` → `focos_grupos.id`.

```sql
focos_grupos (
  id                 bigserial primary key,
  geom               geometry(Point, 4326) not null,   -- coordenada da leitura representante
  leitura_representante_id bigint references focos(id), -- a de maior confiança (h>n>l);
                                                        -- empate -> maior FRP
  n_leituras         int not null,
  sensores           text[] not null,                  -- sensores que viram o fogo
  primeira_hora      timestamptz not null,
  ultima_hora        timestamptz not null,
  frp_max            numeric,
  frp_acumulado      numeric,
  confianca          text not null,                   -- da leitura representante
  derivacao          text not null                    -- regra de dedup (transparência)
);
create index on focos_grupos using gist (geom);
```

**Critério de dedup (explícito, D-013):** duas leituras são o **mesmo fogo** se
`|Δt| ≤ 6 h` **e** `d ≤ max(raio_pixel_m₁, raio_pixel_m₂)`. O limiar temporal é
**parametro** (`parametros_dedup`) e tem de ser **calibrado** contra dados reais na F2.

### 5.11 Fontes: proveniência, licença e atribuição (D-012, issue #07)

> **Nova em 21/10/2026 (T0).** Fonte da verdade do *duty* de atribuição e do *pin* de
> versão de produto (risco RK2 do `docs/ESTADO_DA_ARTE.md`).

```sql
fontes (
  id                  serial primary key,
  fonte               text not null unique,   -- 'FIRMS_VIIRS' | 'NOAA_ABI_FDC' | ...
  nome                text not null,
  produto             text,
  resolucao_m         numeric,
  latencia_horas      numeric,                -- latência-alvo declarada
  intervalo_minutos   int,                    -- cadência de coleta (GOES: 10)
  url                 text,
  termos_url          text,
  atribuicao_requerida text,                  -- texto exato a exibir
  licenca             text,
  chave_requerida     boolean not null default false,
  versao_produto_atual text,                  -- pin de versão
  ativo               boolean not null default true,
  observacao          text
);
```

### 5.12 Parâmetros de dedup e de cluster (D-013)

```sql
parametros_dedup (
  id                 serial primary key,
  chave              text primary key,       -- 'dedup_janela_horas' | 'dedup_raio_m'
                                            -- | 'cluster_raio_m' | 'cluster_janela_h'
  valor              numeric not null,
  justificativa      text,
  atualizado_em      timestamptz default now()
);
```

## 6. Camada de ingestão multi-fonte

> **Revisado em 21/10/2026 (T0)** — `DECISIONS.md` D-012. Ordem de implementação e
> nomes de fonte corrigidos à luz de `docs/ESTADO_DA_ARTE.md` §1.

```
adapters/
├── firms.py          FIRMS VIIRS (NOAA-20/21, S-NPP) e MODIS — API /api/area
├── inpe.py           Programa Queimadas / BDQueimadas (CSV aberto, sem chave)
├── goes_abi.py       NOAA GOES-R ABI L2 FDC (ABI-L2-FDC, bucket público noaa-goes16)
├── mapbiomas.py      FRENTE A — área queimada anual/mensal (NÃO é detecção NRT)
└── base.py           contrato: fetch() -> list[FocoCanonico]
```

Regras do adapter:
1. **Um schema canônico.** Nenhum consumidor sabe qual fonte originou o foco além de
   `fonte`/`produto`/`satelite`/`sensor` — e o `raw` preserva o payload original.
2. **Dedup cross-sensor** — critério explícito em D-013: `|Δt| ≤ 6 h` **e**
   `d ≤ max(raio_pixel_m)`. O dedup **agrupa** (tabela `focos_grupos`); **não apaga**
   (D-010).
3. **Proveniência sempre.** `raw` guarda o payload original; `fonte`/`produto`
   identificam a origem; `versao_produto` fixa a versão do produto.
4. **Falha de uma fonte não derruba as outras.** O coletor isola erros por adapter.
5. **Atribuição/licença por fonte** registrada em `fontes` → issue #07.
6. **Formato da fonte é lido, não presumido.** O schema **difere por sensor** (VIIRS
   traz `bright_ti4`/`bright_ti5`; MODIS traz `brightness`/`bright_t31`; a confiança
   vem como `l`/`n`/`h`; `acq_time` é HHMM **sem zero à esquerda**). Adapter que
   implemente a documentação em vez do payload quebra em produção — ver
   `docs/ESTADO_DA_ARTE.md` §7.2.


## 7. Motor de regras → alertas

Configuração por gerência (`config_alerta`), regras avaliadas a cada ciclo:

| tipo | condição inicial | severidade |
| :--- | :--- | :--- |
| `FOCO_EM_UC` | foco dentro da UC ou da ZA | por nº de focos na janela |
| `FOCO_PROXIMO_UC` | foco a < R metros do limite | por distância e nº de focos |
| `RISCO_ALTO` | score da frente A acima do limiar da gerência **E** há novidade (mudança de faixa desde o último alerta da UC) | por faixa de score |
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

> **O alerta de risco diário não pode virar rotina.** `RISCO_ALTO` dispara quando o
> score cruza o limiar **e** há novidade. Sem a condição de novidade, as 29 UCs
> recebem um alerta por dia e a gerência deixa de olhar — exatamente a perda de
> confiança que D-010 existe para evitar. (D-016)

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

**Objeto primário: a fila de alertas por Gerência Regional.** O heatmap de focos e o mapa
são **contexto** — o lugar onde o fato acontece. A fila ç onde o trabalho acontece, e ç
por isso que a escala de severidade, a confiança e o zoneamento estão lá. (D-016)

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

> **Revisado em 21/10/2026 (T0)** — `DECISIONS.md` D-016 e `docs/ESTADO_DA_ARTE.md`
> §2.5–2.7. Alvo redefinido, desenho do rótulo explicitado, SHAP dentro do alerta,
> e alarme de rotina proibido.

- **Alvo:** `P(ignição na UC nos próximos N dias)`, N ∈ {7, 30}.
  ⚠️ **é risco de IGNiÇÃO, não susceptibilidade.** Susceptibilidade
  ("onde o fogo costuma acontecer") é o que MapBiomas e BDQueimadas já entregam, e o que
  a literatura brasileira já fez (Triunfo do Xingu, doi:10.1016/j.jsames.2025.105366).
  Ignição é condicional ao **acontecer** — e por isso exige horizonte temporal e
  features de pressão antrópica e de combustível.
- **Unidade:** célula de análise (1 km) recortada em UC + ZA; agregação para a UC.
- **Rótulo:** área queimada (dNBR / MCD64A1 v6.1 / MapBiomas Fire Collection 5.1) — com
  cuidado: POINT (foco) herda viés de detecção; área queimada é mais completa, mas
  atrasa (atraso oficial **NÃO VERIFICADO**; observado em GEE: `MODIS/061/MCD64A1` com fim em
  2026-08-01 em 21/10/2026).
  - **Correção de detectabilidade — obrigatória.** Rótulo de área queimada
    carrega o viés do satélite: onde o céu é cronicamente encoberto, quase nada é
    mapeado e o modelo aprende "nuvem = baixo risco". Evidência: Berman et al. 2023
    (*Int. J. Wildland Fire* 32(5):665, doi:10.1071/WF22022) mede ~3.800 ha de
    subestimação por nuvem num caso; Giglio et al. 2016 documenta o viés do
    Collection 6. **Consequência:** as variáveis de detectabilidade (fração de nuvem,
    geometria de visada) entram como *nuisances* e são **retiradas** antes de reportar os
    drivers do alerta — senão a explicação explica o satélite, não o risco.
  - **Validação:** holdout **por UC** (não por AOI equivalente) — é o que separa
    "modelo que generaliza" de "modelo que decorou". Transferência Cerrado→Amazônia não
    é automática (Podschwit et al. 2022, caso peruano, doi:10.1186/s42408-022-00150-7).
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
- **SHAP:** global (drivers do modelo, para o model card) e **local por UC, dentro do
  alerta** (o que puxou o score daquela UC para cima). SHAP explica a **previsão do
  modelo**, não "responsabilidade causal" — a linguagem do alerta e do paper tem de
  respeitar isso.
  - **Não é o mesmo que SHAP sobre detecção.** Explicar por que o sensor disparou
    aqui é explainable-AI de instrumento (geometria de visada, horário da passagem) — para
    o gestor é ruído, e vendê-lo como "por que queimou" seria enganoso.
  - A explicação local de um **modelo global** não é um modelo da UC: é a
    transferência do driver para aquela UC, e tem de ser declarada assim. Recomendação:
    **modelo global + calibração por UC** (29 modelos por UC não tém dados).
- **Repo:** `ml-fire-alert` (recriado). Entrega ao sistema como **artefato versionado** +
  `model_card.json` (D-006).
- **Baseline a bater (e não a copiar):** "Risco de Fogo" do INPE (FWI observado + previsão
  3 dias) e "Perigo de Fogo" do ALARMES (curto prazo 5 dias + sazonal 3 meses). São **perigo
  meteorológico** — condicional à ignição, sem features de pressão
  antrópica nem de combustível. O início do paper tem de ser explicitamente
  **contra esses dois**, e o model card tem de declarar o ganho **por UC**.
- **Ortogonalidade entre as frentes:** a frente A **não** usa "distância ao fogo mais
  próximo" (isso é nowcast = frente B). Risco de ignição e propagação são
  perguntas diferentes.
- **Limitações a declarar no model card e no paper:** SHAP ≠ causal · a explicação
  herda o viés do rótulo · transferência entre biomas · confundidores
  (distância a contrato/estrada é ao mesmo tempo driver e proxy de "onde há gente") ·
  "fogo de manejo" como **limitação declarada** (D-009) · SHAP local de modelo global
  ≠ modelo da UC.

> **Revisado em 21/10/2026 (T0)** — `docs/ESTADO_DA_ARTE.md` §2.5, §2.7 e §4.
>
> - **Rótulo:** usar **área queimada** (MapBiomas Fogo 30 m 1985–2025 / MCD64A1 v6.1 /
>   dNBR), **nunca o ponto de foco** — há viés de detecção documentado
>   (Giglio et al. 2016; Berman et al. 2023). O **atraso** do MCD64A1 não é
>   documentado oficialmente: observado em GEE, o `MODIS/061/MCD64A1` terminava em
>   **2026-08-01** em 21/10/2026 (NÃO VERIFICADO como número oficial).
> - **Features — correções:** `MCD14DL` **não é LST** (é fogo ativo MODIS NRT);
>   LST diária = **MOD11A1/MYD11A1**. Série de NDVI/EVI: **MOD13A2** (1 km, 16 d) ou
>   **MOD13Q1** (250 m, 16 d). Chuva: **CHIRPS v2.0** (0,05°, diário) ou **ERA5-Land**
>   (0,1°, horário). Cobertura: **ESA WorldCover** (10 m, 2020/2021) + **MapBiomas**
>   (30 m). Elevação: **Copernicus DEM GLO-30** (30 m) — **atenção**: o view service
>   GLO-30 passou a exigir registro em **28/07/2026**; alternativa GLO-90/NASADEM.
> - **"SAF/EDMI" — sigla NÃO VERIFICADA.** únicos reais de seca confirmados para a
>   Amazônia: **SPI, SPEI, scPDSI, MCWD, RAI** (JRC) e, no Brasil, **ANA "Monitor de
>   Secas"** e **CEMADEN**. Até que a fonte esteja confirmada, usá-los.
> - **Densidade de raios:** **WWLLN Monthly Thunder Hour Data** (NASA GHRC DAAC, 0,05°,
>   mensal, DOI 10.5067/WWLLN/DATA101) — o dado **bruto** da WWLLN é proprietário
>   (USD 600/ano). Alternativa geostacionária: **NASA GLM**.
> - **Validação:** holdout **por UC** (não por AOI equivalente), além de block CV.
> - **Originalidade:** o "SHAP local por UC" **já existe** no Cerrado (arXiv:2606.04170,
>   com hold-out e SHAP por AOI) e em **uma** UC amazônica (Triunfo do Xingu,
>   doi:10.1016/j.jsames.2025.105366) — mas para **susceptibilidade**, não para
>   **ignição**. A originalidade do NGEO é **ignição com horizonte de dias +
>   risco por UC do IDEFLOR + SHAP dentro do alerta**, não "SHAP por UC" em si.

## 11. Frente B — Propagação (nowcast)

Cadeia de dependências:

```
focos ──▶ cluster ──▶ perímetro estimado ──▶ modelo de propagação ──▶ horizonte 6–24 h
```

- **Perímetro:** (a) acumulo de focos em janela (estimativa rápida, NRT) e/ou
  (b) dNBR sob demanda (Sentinel-2/Landsat — atraso **NÃO VERIFICADO**; serve de
  **validação**, não de nowcast).
- **Propagação:** modelo tipo Rothermel/simplificado, dirigido por **vento** (ERA5/GOES) e
  classe de combustível. Referência de abordagem: EFFIS (produto europeu equivalente —
  **não cobre o Brasil** e não entrega forecast de spread por incêndio: NÃO VERIFICADO).
- **Saída:** polígono de alcance por horizonte → "vai atingir o limite da UC em ~6 h".
- **Alerta `PROPAGACAO`:** a mais acionável de todas — é ela que vira "vá para lá agora".

> **Revisado em 21/10/2026 (T0)** — `docs/ESTADO_DA_ARTE.md` §3.
>
> - **Dependência dura: mapa de combustível.** LANDFIRE (30 m) cobre **só os EUA** e
>   o EFFIS Fuel Map cobre **a Europa**. Para a Amazônia **não foi localizada fuel map
>   padronizada** de resolução operacional — o próprio FISC-Cerrado (UFMG+INPE,
>   doi:10.1038/s41598-023-30560-9) precisou **construir** carga de combustível e umidade de
>   vegetação por sensoriamento remoto.
> - **FARSITE não é mais distribuído** (integrado ao FlamMap 6, Windows) e exige `.LCP`
>   + `.FMS` — a própria NOAA chama a criação do `.FMS` de "by far the most
>   subjective exercise". Não é caminho prático.
> - **Em Python** existem `pyretechnics` (EPL-2.0, ELMFIRE) e ports não oficiais
>   (`rothermel.py`/`farsite.py`); em R, `Rothermel` (GPL-2), `firebehavioR`, `Cell2Fire`.
> - **Plano em dois degraus:** (1) **agora** — perímetro por acúmulo de focos + vetor de
>   deslocamento por vento, sem simulação física (sem insumo novo);
>   (2) **depois** — Rothermel em pontos com fuel model **derivado** do uso do solo
>   (MapBiomas/WorldCover), com confiança degradada e declarada.
> - **Referência brasileira a copiar de estrutura:** FISC-Cerrado — previsão 3×/dia,
>   500 m no Cerrado e **20 m em 9 UCs**, já em uso operacional.

## 12. Fases

> **Revisado em 21/10/2026 (T0).** Acrescenta a fase **F0b** (estado da arte + coleta
> real, já feita) e corrige as dependências de F2 à luz de `DECISIONS.md` D-012/D-015.

| Fase | Entrega | Depende de |
| :--- | :--- | :--- |
| **F0** | Bootstrap: docs, `.gitignore`, `git init`, este plano | — |
| **F0b** | ✅ **Estado da arte + 1ª coleta real** (`docs/ESTADO_DA_ARTE.md`, `scripts/probe_firms.py`, decisões D-012..D-015) | F0 |
| **F1** | ✅ Fundação: docker-compose (PostGIS+Redis), schema (Alembic), seed de geometrias de referência, `/api/health` | F0b, **issue #01** |
| **F2** | Ingestão multi-fonte → `focos` → `focos_grupos` (dedup) → `eventos_fogo` | F1, FIRMS key **reemitida sob e-mail institucional** (#13) |
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

**Ordem dos adapters na F2** (D-012): `firms.py` (VIIRS — já provado por coleta real) →
`inpe.py` (Programa Queimadas) → `goes_abi.py` (recência de 10 min) → `firms.py` (MODIS).
O **GOES-16** do briefing é **GOES-19** desde 07/04/2025 (D-015): o sensor vem do
payload, não da suposição.


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

| R3 | Promessa de tempo real não se sustenta | comunicar "**recência ≤ 30 min (GOES)**" + "**detecção NRT < 3 h (FIRMS VIIRS)**" + "risco diário"; nunca "previsão em tempo real" (D-015) |
| R4 | Chave/licença de fonte de focos | registrar termos por fonte em `fontes` (§5.11) → issue #07 |
| R4b | **Mudança de termos já aconteceu** (Copernicus DEM 30 m exigiu registro em 28/07/2026; GOES-16 → GOES-19 em 07/04/2025) | *pin* de versão por produto (`versao_produto`, `fontes.versao_produto_atual`) + data de validade no `model_card` (D-006). `docs/ESTADO_DA_ARTE.md` §8-RK2 |
| R4c | **Fonte única como ponto de falha** — INPE e EFFIS também usam FIRMS no fundo | terceiro caminho sem FIRMS no fundo: **NOAA ABI L2 FDC** (bucket público, 10 min) + sensores próprios do INPE. Dependência real registrada em D-012 |
| R5 | Volume de tiles / custo de raster | titiler+COG com pyramid; cache; só janelas úteis |
| R6 | Uso offline em campo sem sinal | service worker + Pacote da UC |
| R7 | Deploy/credencial em ambiente institucional | `.env` por ambiente; nada sensível no git (D-003, D-006) |
| R8 | Zoneamento cobre só 16/29 UCs | alerta segue emitido **sem** contexto de zona, com limitação explícita (#24) |
| R9 | Confundidor "fogo de manejo" nos rótulos | **Limitação declarada**, não resolvida: a zona não entra como feature e não é curada. Declarar no model card e no paper (§10) |
| R10 | **Schema da fonte muda** (colunas por sensor, `l`/`n`/`h`, HHMM sem padding) | ler o payload, não a documentação; teste de fixture por sensor; `raw` preservado (§6 regra 6, D-014) |
| R11 | **Mapa de combustãvel inexistente na Amazônia** → frente B sem lastro físico | frente B em dois degraus: (1) perímetro + deslocamento por vento; (2) Rothermel com fuel model **derivado** do uso do solo, com confiança degradada. `docs/ESTADO_DA_ARTE.md` §3.6 |


