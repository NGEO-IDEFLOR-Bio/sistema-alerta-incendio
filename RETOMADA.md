# RETOMADA — estado atual e próximos passos

> Entrada para retomar. Leia: `AGENTS.md` → este arquivo → `ISSUES.md` → `TAREFAS.md` → `BUILD.md`.
> Atualizado: 21/10/2026.

## Estado atual

- **F0 (bootstrap) — ✅ concluída em 21/10/2026.**
  - `AGENTS.md`, `RETOMADA.md`, `ISSUES.md`, `TAREFAS.md`, `BUILD.md`, `DECISIONS.md`,
    `PLANO_ARQUITETURA.md`, `.gitignore`, `.gitattributes`, `.env.example` criados.
  - Repo git inicializado; `.env` e `secrets/` **fora** do versionamento.
  - Arquitetura anterior movida para `docs/arquivo/arquitetura_do_backend_do_sistema.md`.
  - **Nenhum código escrito ainda.** Sem `backend/`, sem `frontend/`, sem docker-compose.
- **Dados de referência recebidos (21/10/2026):**
  - `data/shapes_de_todas_as_unidades_com_gerencia.geojson` — **29 UCs com gerência DGMUC**
    (9 gerências), `id` 1..29, EPSG:4326. Digest e procedência em `data/README.md`.
  - `visualizador/data/zoneamentos_ucs_estaduais.geojson` — **252 zonas de plano de manejo
    em 16 UCs**. Entra **verbatim** (D-009): sem taxonomia global, sem normalização.
  - ✅ **Issue #21 resolvida no arquivo**: `GRCN-l/ll/lll` → `GRCN-I/II/III`, sem tocar em
    geometria (29 features, mesmos bytes). Digest original e corrigido no `data/README.md`.
- **Decisões fechadas:** D-001 MapLibre · D-002 duas frentes em paralelo ·
  D-003 alerta termina na notificação, sem máquina de estados · D-004 todas as fontes ·
  D-005 DS compartilhado `ngeo-ds` · D-006 sistema ≠ pesquisa · D-007 roteamento por
  gerência regional (**dependência resolvida**) · D-008 latência-alvo ≤1 h ·
  D-009 zoneamento = contexto que aponta para o plano, **não** filtro ·
  D-010 o sistema **nunca descarta foco em silêncio** — qualifica a confiança.
- **Ativos já disponíveis no `.env`:** `DATABASE_URL` (PostGIS), `GEE_PROJECT_ID` +
  `GEE_CREDENTIALS_JSON`, `TUNNEL_TOKEN` (Cloudflare), e uma chave do Sentinel Hub em
  `secrets/`. `GEMINI_API_KEY` / `OPENROUTER_API_KEY` ficam para a frente A.

## Princípio que emerged das correções de 21/10/2026

> **O sistema entrega material; a leitura e a ação são do gestor.**
>
> Quatro consequências concretas:
> 1. Alerta em zona de manejo **é emitido** — quem define o que pode ou não pode é o
>    plano da unidade, não o software (D-009).
> 2. **Não existe taxonomia global de zonas** — cada plano nomeia e define as suas, e
>    nada é padronizado (D-009).
> 3. **Nada é descartado em silêncio** — a incerteza é declarada no alerta (severidade,
>    confiança, `possivel_falso_positivo`), não escondida por supressão (D-010).
> 4. **Instrumento, não instrução** — o produto não orienta, lembra, explica ou
>    interpreta. Sem landing page, sem tutorial, sem "verifique antes de agir". O
>    destinatário é gestor de gerência regional e sabe o que fazer com o material
>    (D-011).


## Bloqueio

- **Nenhum bloqueio técnico.** #01 resolvido, #21 resolvido.
- **Pendências institucionais (não bloqueiam F1/F2):**
  - ~~#22 — registry de gerências do `maps`~~ ✅ **resolvido** em 21/10/2026
    (`maps` commit `72b0eee`, push). `visualizador` verificado, sem resíduo.
  - #26 — curadoria por UC do que o plano diz sobre fogo em cada zona (preenche
    `ucs_zonas_decisao`, hoje vazia). Não bloqueia o MVP; habilita a feature de zona
    na frente A.
  - #24 — zoneamento para as 13 UCs restantes.
  - #25 — Zonas de Amortecimento para as UCs que não têm.
  - #07 — termos de uso/atribuição por fonte de focos.




## Próximo passo (1 item)

1. **T1 — Fundação local**: `docker-compose.yml` (PostGIS + Redis), estrutura `backend/`,
   migração Alembic do schema (PLANO_ARQUITETURA §5), seed das 9 gerências DGMUC + 29 UCs
   + 252 zonas (verbatim), `/api/health`.
   Prompt pronto em `TAREFAS.md` → T1.

## Próximos depois do T1

T2 (ingestão multi-fonte + dedup) → T3 (motor de regras) → T4 (entrega) → T5 (frontend).
**Frente A (T6/T7) e Frente B (F7) entram em paralelo** a partir de F6.

## Fora de escopo (agora)

- Modelo de ML / SHAP (frente A) — repo próprio, fase F6.
- Nowcast de propagação (frente B) — fase F7.
- **Portal público / landing page / scrollytelling — removido do plano** (D-011).
  Se um dia precisar, sai como artefato da frente A, fora do caminho crítico.
- **Qualquer texto instrutivo no produto** — alerta, painel, relatório (D-011).
- Migração de `maps` e `visualizador` para `ngeo-ds` — issues #08, #09.
- Workflow de atendimento / estados do alerta — **decidido fora** (D-003).


## Como retomar

```
1. ler AGENTS.md, RETOMADA.md, ISSUES.md
2. pegar a próxima tarefa em TAREFAS.md
3. 1 sessão = 1 tarefa = 1 commit; verificação OK antes
4. atualizar ISSUES.md + RETOMADA.md no mesmo commit
```
