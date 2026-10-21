# TAREFAS — prompts prontos, 1 por sessão

> Copie o bloco de uma tarefa para a sessão nova. Cada sessão = 1 tarefa = 1 commit.
> Ordem de execução = ordem da lista.

---

## T0 — Estado da arte, decisões de fonte de dados e primeira coleta real

```text
Contexto: repo H:\Meu Drive\DEV\sistema_alerta_incendio. Leia AGENTS.md, RETOMADA.md,
ISSUES.md, DECISIONS.md, PLANO_ARQUITETURA.md e README.md. Remote: origin/main.

Tarefa: ANTES de escrever o backend, saber o que já existe e provar que a cadeia de
dados funciona de ponta a ponta.

1. ESTADO DA ARTE — produzir docs/ESTADO_DA_ARTE.md, com fontes citadas (URL + data
   de acesso). Cobrir:
   a. Detecção de fogo NRT: NASA FIRMS (MODIS/VIIRS/GOES), INPE MONITORQUEIMADAS,
      MapBiomas Alerta e Fogo, GOES-16 (produtos de hotspot), GFAS, EFFIS. Para cada
      um: resolução, latência, cobertura do Pará, custo, termos de uso e atribuição.
   b. Modelos de risco: Fire Weather Index (McArthur), Canadian FDS, ITU-R BT.839,
      e o que a literatura de ML faz para risco de incêndio na Amazônia (artigos
      identificáveis). Contrastar com a frente A (PLANO §10) e dizer o que é reuso,
      o que é adapted, o que é original.
   c. Propagação / nowcast: FARSITE, modelos tipo Rothermel/scalar, previsão de
      spread do EFFIS. Dizer o que é viável no escopo e com que dependência.
   d. Datasets de entrada: FIRMS, MCD64A1, MCD14DL, MOD11A1, MOD13, CHIRPS, ERA5,
      SAF/EDMI, ESA WorldCover, MapBiomas, Sentinel-2 / Landsat C2 (dNBR),
      ALOS/SRTM, densidade de raios.
   e. Sistemas de alerta já existentes no Brasil e na Amazônia (INPE, MMA,
      estaduais, acadêmicos) — o que já é feito e em que escala.
   f. LACUNA: o que nenhum sistema existente faz e que o NGEO faria — roteamento
      institucional por Gerência Regional, citação do zoneamento do plano de
      gestão, SHAP local auditável por UC, uso offline em campo. Se essa lacuna
      não se sustentar, dizê-lo.
   g. RISCOS: dependência de terceiro (fonte fora do ar, mudança de termos),
      atribuição/licença, fonte única como ponto de falha.

2. DECISÕES DE FONTE (DECISIONS.md): fonte primária de focos, fontes de fallback,
   ordem de implementação, e o schema canônico definitivo (PLANO §5, §6) à luz do
   que foi apurado. Registrar a política de dedup entre sensores com critério
   explícito.

3. PRIMEIRA COLETA REAL: obter a chave da API FIRMS (https://firms.modaps.eosdis.nasa.gov/
   api/area — registro no site) e escrever scripts/probe_firms.py que faça UMA
   chamada real para o recorte do Pará e despeje: o schema de resposta CRU (não a
   documentação), o número de registros, o recorte de coordenadas, os campos de
   data/hora, satellite, confidence, FRP, e o formato exato do campo de
   coordinate. Salvar uma amostra em data/ (gitignored) e documentar em
   docs/ESTADO_DA_ARTE.md o schema REAL observado.
   Se não houver chave disponível, fazer a chamada via uma fonte sem chave
   (ex.: área pública do FIRMS) ou via INPE, e registrar o bloqueio em ISSUES.md.

4. REFINAR o plano: ajustar PLANO_ARQUITETURA §5/§6/§12 com o que for apurado,
   sem quebrar as decisões já fechadas (D-001..D-011).

Regras:
- NÃO treinar modelo, NÃO implementar o backend, NÃO implementar a ingestão
  completa. O entregável de código é o probe (um script que prova a coleta).
- NÃO inventar referência, número, latência ou metrica. Tudo que não foi
  verificado fica marcado como NÃO VERIFICADO. Se não achou, escreve que não achou.
- Citar URL de toda fonte externa consultada, com data de acesso.
- ruff check . e pytest -q OK (o probe tem teste com fixture gravada, sem rede).
- atualizar ISSUES.md, RETOMADA.md e DECISIONS.md no mesmo commit; commit + push.
```

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
   (focos, eventos_fogo, alertas, entregas, config_alerta, gerencias_regionais, ucs,
   ucs_zonas).
4. scripts/seed_gerencias.py: carga das 9 gerências DGMUC (PLANO_ARQUITETURA §5.9).
   A sigla JÁ VEM CORRIGIDA no arquivo (issue #21, corrigido em 21/10/2026) —
   normalizar mesmo assim, porque o arquivo original volta da instituição.
5. scripts/seed_ucs.py: carga das 29 UCs de
   data/shapes_de_todas_as_unidades_com_gerencia.geojson (EPSG:4326, MultiPolygon),
   ligando uc.gerencia_id -> gerencias_regionais.id. Usar o campo 'nome_'
   (o 'name' parece truncado em alguns casos).
6. scripts/seed_zonas.py: carga das 252 zonas de
   H:\Meu Drive\DEV\visualizador\data\zoneamentos_ucs_estaduais.geojson.
   - resolver uc_id por SOBREPOSIÇÃO ESPACIAL (centroide contido / maior área de
     interseção), NUNCA pelo campo UNIDADE (está truncado) — issue #23
   - guardar sigla e zona VERBATIM. NÃO normalizar, NÃO mapear para classe global,
     NÃO renomear: cada plano de gestão define suas próprias zonas (D-009)
   - a zona é INFORMAÇÃO que consta do alerta. Não criar tabela de curadoria, não
     avaliar permissão de fogo, não codificar classe (issue #26 descartada)

7. Teste de integridade do seed: exatamente 29 UCs, exatamente 9 gerências, todo
   uc.gerencia_id resolvido (issue #21). Falhar se não bater.
8. GET /api/health devolvendo status do DB, versão do schema e contagens
   (ucs, gerencias, zonas, zonas_sem_uc).

Regras: ruff check . e ruff format --check . e pytest -q OK; docker compose config válido;
NÃO buildar imagem de produção; NÃO commitar .env nem dados (data/ é gitignored);
atualizar ISSUES (#03, #04, #21, #23, #24) e RETOMADA.md no mesmo commit;
commit pequeno + push.

Notas:
- os arquivos de referência NÃO estão no git (data/ é ignorado). O seed deve ler de
  data/ e de H:\Meu Drive\DEV\visualizador\data\, com caminho configurável por settings.
- Docker Desktop e Google Drive não se dão bem: NÃO monte H:\Meu Drive no container.
  O seed roda na host, contra o Postgres exposto em localhost.
- O zoneamento cobre só 16/29 UCs — registrar a cobertura, não inventar.
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

````text
Contexto: repo H:\Meu Drive\DEV\sistema_alerta_incendio. Leia AGENTS.md, RETOMADA.md,
ISSUES.md, DECISIONS.md e PLANO_ARQUITETURA.md.

Tarefa: implementar a FASE F4.
1. services/delivery/: registry de canais com interface comum
   (email/SMTP, telegram/bot API, whatsapp/Meta Cloud API, webhook genérico).
2. Canal email é o default e precisa funcionar ponta a ponta.
3. Toda tentativa de entrega é registrada em entregas (canal, destinatario, status,
   resposta_http, erro, enviado_em). NUNCA perder o registro do que foi notificado.
4. Template do alerta — só FATOS, nada instrutivo (D-011):
   ```
   FOCO DETECTADO — <data hora> BRT
   UC ........ <nome> (<sigla>)
   Zona ....... <sigla> <texto>          (se a UC tiver zoneamento)
   Posição .... <lat> <lon>  (±<resolução> m)
   Severidade . <BAIXA|MEDIA|ALTA|CRITICA>   Confiança: <ALTA|MEDIA|BAIXA>
   Focos ...... <n> em <hh:mm>   Fontes: <lista>
   [ abrir no mapa ]
   ```
   PROIBIDO no corpo do alerta: "verifique antes de agir", "atenção", "recomenda-se",
   lembrete sobre o plano de gestão, definição de termo técnico, "quem é o responsável"
   (o roteamento já entrega à gerência certa; fica no registro, não na mensagem).
   Coordenada em decimal E em UTM (SIRGAS 2000, fuso 21S/22S) — EPSG resolvido no
   código via pyproj, não fixado em doc.
5. Idempotência: não reenviar o mesmo alerta no mesmo canal sem justificativa.
6. Testes com servidor SMTP falso / mock do cliente HTTP.
7. Teste de contrato do template: verificar que o corpo NUNCA contém os termos proibidos
   acima. É o que garante que a regra não se perca na próxima refatoração.

Regras: ruff + pytest OK; segredos só via .env/settings; atualizar ISSUES e
RETOMADA.md; commit + push.
````

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

REGRAS DE PRODUTO (D-011) — não negociáveis:
- O app abre DIRETO no mapa. Sem landing page, sem hero, sem scroll-telling, sem CTA.
- Zero texto explicativo: nenhum parágrafo, nenhum tooltip que defina termo técnico
  (FRP, zona de amortecimento, severidade). Legenda de mapa sim (é dado).
- Rótulos curtos e técnicos: focos, FRP, severidade, confiança, janela.
- Densidade alta: números na mesa, sem parágrafo em lugar nenhum.
- Sem tutorial, sem onboarding, sem "saiba mais".

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
