# RETOMADA — estado atual e próximos passos

> Entrada para retomar. Leia: `AGENTS.md` → este arquivo → `ISSUES.md` → `TAREFAS.md` → `BUILD.md`.
> Atualizado: 21/10/2026.

## Estado atual

- **F0 (bootstrap) — ✅ concluída em 21/10/2026.**
  - `AGENTS.md`, `RETOMADA.md`, `ISSUES.md`, `TAREFAS.md`, `BUILD.md`, `DECISIONS.md`,
    `PLANO_ARQUITETURA.md`, `.gitignore`, `.env.example` criados.
  - Repo git inicializado; `.env` e `secrets/` **fora** do versionamento.
  - Arquitetura anterior movida para `docs/arquivo/arquitetura_do_backend_do_sistema.md`.
  - **Nenhum código escrito ainda.** Sem `backend/`, sem `frontend/`, sem docker-compose.
- **Decisões fechadas:** D-001 MapLibre · D-002 duas frentes em paralelo ·
  D-003 alerta termina na notificação, sem máquina de estados · D-004 todas as fontes ·
  D-005 DS compartilhado `ngeo-ds` · D-006 sistema ≠ pesquisa · D-007 roteamento por
  gerência regional · D-008 latência-alvo ≤1 h na detecção, diário no risco.
- **Ativos já disponíveis no `.env`:** `DATABASE_URL` (PostGIS), `GEE_PROJECT_ID` +
  `GEE_CREDENTIALS_JSON`, `TUNNEL_TOKEN` (Cloudflare), e uma chave do Sentinel Hub em
  `secrets/`. `GEMINI_API_KEY` / `OPENROUTER_API_KEY` ficam para a frente A.

## Bloqueio

- **#01 — mapeamento UC → Gerência Regional (DGMUC)** não existe estruturado.
  Dependência institucional. Bloqueia o seed das UCs e o roteamento de alerta (F3),
  **não** bloqueia F1/F2. Enquanto isso: `ucs.gerencia_id` fica nullable.

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
