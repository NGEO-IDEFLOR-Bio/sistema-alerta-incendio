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
    em 16 UCs**. É o que torna "fogo de manejo" observável (D-009).
  - ⚠️ **Dois problemas de qualidade que quebram em silêncio** (issues #21, #23):
    sigla `GRCN-l/ll/lll` (L minúsculo no lugar do I romano) e `SIGLA` do zoneamento
    não ser global (`ZA` = "Alta Intervenção" em uma UC, "Amortecimento" em outra).
- **Decisões fechadas:** D-001 MapLibre · D-002 duas frentes em paralelo ·
  D-003 alerta termina na notificação, sem máquina de estados · D-004 todas as fontes ·
  D-005 DS compartilhado `ngeo-ds` · D-006 sistema ≠ pesquisa · D-007 roteamento por
  gerência regional (**dependência resolvida**) · D-008 latência-alvo ≤1 h ·
  D-009 zoneamento = camada de referência do fogo de manejo.
- **Ativos já disponíveis no `.env`:** `DATABASE_URL` (PostGIS), `GEE_PROJECT_ID` +
  `GEE_CREDENTIALS_JSON`, `TUNNEL_TOKEN` (Cloudflare), e uma chave do Sentinel Hub em
  `secrets/`. `GEMINI_API_KEY` / `OPENROUTER_API_KEY` ficam para a frente A.

## Bloqueio

- **Nenhum bloqueio técnico.** #01 foi resolvido com o arquivo de gerências.
- **Pendências institucionais (não bloqueiam F1/F2):**
  - #22 — o registry de gerências do repo `maps` está **desatualizado** (lista GRCN-III,
    GRNE, GRTUC? não; ainda lista GRT, GRBA, GRET, GRMR). Precisa ser corrigido lá.
  - #24 — zoneamento para as 13 UCs restantes.
  - #25 — Zonas de Amortecimento para as UCs que não têm.
  - #07 — termos de uso/atribuição por fonte de focos.


## Próximo passo (1 item)

1. **T1 — Fundação local**: `docker-compose.yml` (PostGIS + Redis), estrutura `backend/`,
   migração Alembic do schema (PLANO_ARQUITETURA §5), seed das 10 gerências, `/api/health`.
   Prompt pronto em `TAREFAS.md` → T1.

## Próximos depois do T1

T2 (ingestão multi-fonte + dedup) → T3 (motor de regras) → T4 (entrega) → T5 (frontend).
**Frente A (T6/T7) e Frente B (F7) entram em paralelo** a partir de F6.

## Fora de escopo (agora)

- Modelo de ML / SHAP (frente A) — repo próprio, fase F6.
- Nowcast de propagação (frente B) — fase F7.
- Portal público / scrollytelling — fase F9, sai como artefato da análise.
- Migração de `maps` e `visualizador` para `ngeo-ds` — issues #08, #09.
- Workflow de atendimento / estados do alerta — **decidido fora** (D-003).

## Como retomar

```
1. ler AGENTS.md, RETOMADA.md, ISSUES.md
2. pegar a próxima tarefa em TAREFAS.md
3. 1 sessão = 1 tarefa = 1 commit; verificação OK antes
4. atualizar ISSUES.md + RETOMADA.md no mesmo commit
```
