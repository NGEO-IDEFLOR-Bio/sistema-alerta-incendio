# TAREFAS — prompts prontos, 1 por sessão

> Copie o bloco de uma tarefa para a sessão nova. Cada sessão = 1 tarefa = 1 commit.
> Ordem de execução = ordem da lista.

---

## T1 — Fundação local (PostGIS + Redis + schema + seed)

```text
Contexto: repo H:\Meu Drive\DEV\sistema_alerta_incendio. Leia AGENTS.md, RETOMADA.md,
ISSUES.md, DECISIONS.md e PLANO_ARQUITETURA.md.

Tarefa: implementar a FASE F1 do plano.
1. docker-compose.yml com PostGIS (postgis/postgis) + Redis, volume persistente,
   healthcheck, e porta exposta só em localhost.
2. backend/ com pyproject.toml, estrutura src/ (api/, core/, db/, models/, workers/,
   adapters/, services/), settings via pydantic-settings lendo .env.
3. Implementar o schema de PLANO_ARQUITETURA.md §5 como migração Alembic
   (focos, eventos_fogo, alertas, entregas, config_alerta, gerencias_regionais, ucs).
4. scripts/seed_gerencias.py: carga das 10 gerências regionais da DGMUC
   (GERAL, GRCN-I, GRCN-II, GRX, GRB, GRMR, GRET, GRBA, GRT, GRA).
5. GET /api/health devolvendo status do DB e versão do schema.
6. .env.example já existe; não commitar .env real.

Regras: ruff check . e ruff format --check . e pytest -q OK; docker compose config válido;
NÃO buildar imagem de produção; atualizar ISSUES (#03, #04) e RETOMADA.md no mesmo commit;
commit pequeno + push.

Atenção: issue #01 (mapeamento UC → gerência) está bloqueada e NÃO depende desta tarefa —
deixe a coluna gerencia_id em ucs nullable e siga.
```

---

## T2 — Ingestão multi-fonte de focos (F2)

```text
Contexto: repo H:\Meu Drive\DEV\sistema_alerta_incendio. Leia AGENTS.md, RETOMADA.md,
ISSUES.md, DECISIONS.md e PLANO_ARQUITETURA.md.

Tarefa: implementar a FASE F2.
1. adapters/base.py com o contrato e o dataclass FocoCanonico (PLANO_ARQUETETURA §6).
2. adapters/firms.py: FIRMS (MODIS/VIIRS/GOES), paginação, rate limit, retry com backoff,
   normalização para o schema canônico, preservando raw.
3. Worker Celery com schedule (a cada 5 min) e uma task por fonte; falha isolada por adapter
   (uma fonte fora do ar não derruba as outras).
4. Dedup cross-sensor: o mesmo incêndio visto por MODIS e VIIRS não pode virar dois focos.
   Implementar por janela temporal + proximidade espacial, com regra documentada e testada.
5. Agregação em eventos_fogo (clustering espaço-temporal) com raio e janela parametrizáveis.
6. Testes com fixtures gravadas (sem chamada de rede nos testes).

Regras: ruff + pytest OK; cobertura do dedup e do clustering testada; NÃO fazer deploy;
atualizar ISSUES e RETOMADA.md; commit + push.
```

---

## T3 — Motor de regras e alertas (F3)

```text
Contexto: repo H:\Meu Drive\DEV\sistema_alerta_incendio. Leia AGENTS.md, RETOMADA.md,
ISSUES.md, DECISIONS.md e PLANO_ARQUITETURA.md.

Tarefa: implementar a FASE F3.
1. services/rules.py: motor de regras config-driven por config_alerta (PLANO_ARQUITETURA §7).
   Tipos: FOCO_EM_UC, FOCO_PROXIMO_UC. (RISCO_ALTO e PROPAGACAO ficam para F6/F7.)
2. Filtro de qualidade ANTES da geração do alerta: supressão de foco isolado diurno,
   confirmação por N focos em janela, marcação de área com fogo de manejo, atenuação por
   chuva recente. Este filtro é o que sustenta a confiança do sistema — testá-lo bem.
3. Endpoints: GET /api/alertas (filtros: gerência, tipo, severidade, janela), 
   GET /api/alertas/{id}, GET /api/focos, GET /api/ucs.
4. Alertas são IMUTÁVEIS (D-003): não criar workflow de atendimento, estados ou ack.
5. Testes: cada tipo de regra, cada regra do filtro de qualidade, e o caso "alerta não
   dispara para 1 foco isolado".

Regras: ruff + pytest OK; não introduzir máquina de estados; atualizar ISSUES e
RETOMADA.md; commit + push.
```

---

## T4 — Entrega multi-canal (F4)

```text
Contexto: repo H:\Meu Drive\DEV\sistema_alerta_incendio. Leia AGENTS.md, RETOMADA.md,
ISSUES.md, DECISIONS.md e PLANO_ARQUITETURA.md.

Tarefa: implementar a FASE F4.
1. services/delivery/: registry de canais com interface comum
   (email/SMTP, telegram/bot API, whatsapp/Meta Cloud API, webhook genérico).
2. Canal email é o default e precisa funcionar ponta a ponta.
3. Toda tentativa de entrega é registrada em entregas (canal, destinatario, status,
   resposta_http, erro, enviado_em). NUNCA perder o registro do que foi notificado.
4. Template padrão: o quê (foco/pixel com incerteza), onde (UC + link no mapa), quando,
   severidade, confiança (nº de focos, fontes concordantes), responsável da região.
5. Idempotência: não reenviar o mesmo alerta no mesmo canal sem justificativa.
6. Testes com servidor SMTP falso / mock do cliente HTTP.

Regras: ruff + pytest OK; segredos só via .env/settings; atualizar ISSUES e RETOMADA.md;
commit + push.
```

---

## T5 — Frontend MapLibre: mapa + heatmap + alertas (F5)

```text
Contexto: repo H:\Meu Drive\DEV\sistema_alerta_incendio. Leia AGENTS.md, RETOMADA.md,
ISSUES.md, DECISIONS.md e PLANO_ARQUITETURA.md.

Tarefa: implementar a FASE F5 (primeiro corte).
1. frontend/ com Vite + MapLibre GL JS. Sem framework de UI (o painel tem 3 painéis).
2. Layout HUD de PLANO_ARQUITETURA §9: barra institucional, fila de alertas à esquerda,
   mapa ao centro, painel da UC à direita, rodapé temporal (scrubber 24h–7d + play/pause).
3. Camadas MapLibre: heatmap de focos (nativo), circle de focos individuais com raio =
   raio_pixel_m (incerteza posicional — D-003 do AGENTS), fill/line de UCs e ZA.
4. Fila de alertas: filtrável por gerência, tipo, severidade e janela temporal.
5. Painel da UC: severidade, nº de focos em 24h, série temporal, link para o alerta.
6. Identidade: consumir ngeo-ds via CDN pinado. Se o repo ngeo-ds ainda não existir (#11),
   criar um tokens.css mínimo local com a paleta gov e registrar a issue.
7. Modo claro e escuro.

Regras: npm run lint e npm run build OK; mapa carrega com dado real do backend (não mock);
atualizar ISSUES e RETOMADA.md; commit + push.
```

---

## T6 — Frente A: risco de ignição com ML + SHAP (F6)

```text
Contexto: repo novo ml-fire-alert (a criar). Leia as decisões D-002, D-006 e o schema
de PLANO_ARQUITETURA.md §10 no repo sistema_alerta_incendio.

Tarefa: primeiro corte da frente A.
1. Repo ml-fire-alert com AGENTS.md, RETOMADA.md, ISSUES.md e .gitignore próprios.
2. Construir a grade de análise (1 km) recortada nas UCs + ZA do IDEFLOR.
3. Tabela de features v1 via GEE: LST (MOD11A1), NDVI (MOD13), chuva (CHIRPS/ERA5),
   seca (SAF/EDMI), cobertura de combustível (WorldCover/MapBiomas),
   DISTÂNCIA a contratos de transição e a concessões (feature-chave: pasto em pousio =
   capim seco = combustível), borda de UC, estradas, distância a TI/quilombos,
   histórico de queima.
4. Catálogo de features com fonte, resolução, data de acquisition e proveniência.

Regras: NÃO treinar modelo ainda (é a T7); feature table versionada como parquet com
digest; sem commit de dados brutos; commit + push.
```

---

## T7 — Frente A: modelo, validação espacial, calibração, SHAP (F7)

```text
Contexto: repo ml-fire-alert. Leia D-002, D-006 e PLANO_ARQUITETURA.md §10.

Tarefa: treinar e validar o modelo de risco de ignição.
1. Rótulos: área queimada (MCD64A1 / MapBiomas Fogo / dNBR). Tratar explicitamente o
   confundidor de fogo de manejo (PLANO_ARQUITETURA §10) e o viés de detecção do rótulo.
2. Validação: block CV espacial + holdout temporal. NUNCA split aleatório sobre pixels.
   Comparar contra baseline só-clima.
3. Calibração isotônica/Platt e métricas: AUC-PR, precision@k, Brier, curva de calibração,
   recall@k por UC.
4. SHAP: global (drivers) e local (drivers por UC).
5. Exportar artefato versionado: modelo + model_card.json (digest do dataset, features,
   métricas, data de validade). Entrega ao sistema via PR (D-006).

Regras: reportar métricas com e sem block CV para deixar o vazamento explícito;
não commitar dados brutos; commit + push.
```
