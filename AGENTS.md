# AGENTS.md — Sistema de Alerta de Incêndio Florestal (IDEFLOR-Bio / NGEO)

> Documento **carregado automaticamente** em toda sessão deste repo. Mantenha curto e factual.

## O que é

Plataforma que **detecta focos de incêndio** (múltiplos satélites), **avalia** contra as áreas
geridas pelo IDEFLOR-Bio e **notifica** a Gerência Regional responsável. Também desenvolve
duas frentes analíticas: **risco de ignição** (ML + SHAP) e **propagação** (nowcast).

## Repositórios relacionados

| Repo | Papel |
| :--- | :--- |
| `sistema_alerta_incendio` (este) | Sistema: backend, worker, frontend, alertas |
| `visualizador` | WebGIS institucional (Leaflet). Fonte de geometrias de referência |
| `maps` | Repositório de cartografia (identidade visual) |
| `ngeo-ds` *(a criar)* | Design system compartilhado (tokens, componentes, fontes, logos) |

## Estrutura

```
sistema_alerta_incendio/
├── backend/          FastAPI + workers (ingestão, regras, entrega)
├── frontend/         MapLibre GL JS (dashboard)
├── data/             dados locais (IGNORADO pelo git)
├── scripts/          bootstrap de DB, carga de referência
├── docs/arquivo/     documentos históricos
├── .env              segredos (NUNCA versionar)
└── secrets/          credenciais de serviço (NUNCA versionar)
```

## Comandos (a definir em BUILD.md — Fase F1)

```bash
# ainda não setup; ver BUILD.md
```

## Regra de verificação (OBRIGATÓRIA antes de commitar)

```bash
# backend
python -m pytest -q
ruff check . && ruff format --check .

# frontend
cd frontend && npm run lint && npm run build
```

Se um comando ainda não existe: registre em `ISSUES.md` e **não** declare pronto.

## Fluxo obrigatório

1. **1 tarefa por sessão.** Leia `AGENTS.md` → `RETOMADA.md` → `ISSUES.md` → `TAREFAS.md`.
2. Rode a verificação. Só commite com tudo OK.
3. Commit pequeno e descritivo. Atualize `ISSUES.md` e `RETOMADA.md` **no mesmo commit**.
4. **Não** commite `.env`, `secrets/`, dados brutos ou artefatos pesados.
5. **Não** faça deploy/build pesado sem pedido explícito.
6. Decisões → `DECISIONS.md`. Nada relevante fica só no chat.

## Regras de domínio (não quebrar)

- **Alerta termina na notificação.** O NGEO detecta e avisa; o protocolo de ação é da
  Gerência Regional. O sistema **não** implementa fluxo de atendimento, estados nem
  responsabilização. (ver `DECISIONS.md` D-003)
- **Nunca descartar um foco em silêncio.** Todo evento que toca uma UC **gera alerta**.
  A incerteza é **declarada** (severidade, confiança, `possivel_falso_positivo`), nunca
  escondida por supressão. Falso positivo não se resolve calando — resolve-se graduando
  a confiança e entregando o contexto. (D-010)
- **O sistema não julga o que é permitido.** Quem decide é o **plano de gestão da
  unidade**. A zona do plano entra no alerta como contexto e ponteiro, **nunca** como
  critério de supressão. (D-009)
- **Não padronizar o zoneamento.** Cada plano de gestão nomeia e define as suas zonas;
  `sigla` não é global. Guardar verbatim. (D-009)
- **Posição de foco é pixel, não coordenada.** GOES-16 ~750 m, VIIRS 375 m. Sempre exiba a
  incerteza posicional; nunca afirme precisão que não existe.
- **Sombreamento é só do IDEFLOR.** Áreas de interesse do alerta: UCs estaduais + ZA.

## Economia de tokens

Respostas curtas. Saídas longas → arquivo + `grep`/`Select-String`. Não repita contexto
já documentado; aponte para o doc.
