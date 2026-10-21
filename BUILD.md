# BUILD — como rodar, verificar e armadilhas do ambiente

> Estado: **F1 ainda não implementada.** Os comandos abaixo são o alvo da T1.
> Conforme as fases avançam, ATUALIZE este arquivo no mesmo commit.

## Ambiente

| Item | Valor |
| :--- | :--- |
| SO | Windows / PowerShell 5.1 |
| Python | 3.12 |
| Node | 20+ (LTS) |
| Docker | Docker Desktop (PostGIS + Redis) |

## Segredos

- `.env` **nunca** versionado (já no `.gitignore`). `.env.example` é o contrato de chaves.
- `secrets/` **nunca** versionado. Contém chave de serviço do Sentinel Hub.
- Antes de qualquer `git add`: `git status` e confirmar que `.env` e `secrets/` **não**
  aparecem.

## Setup (alvo da T1)

```powershell
Copy-Item .env.example .env
# editar .env com as chaves reais

docker compose up -d
docker compose ps          # esperar postgis e redis healthy

cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -e ".[dev]"
alembic upgrade head
python -m scripts.seed_gerencias
```

## Verificação (OBRIGATÓRIA antes de commit)

```powershell
# backend
python -m pytest -q
ruff check .
ruff format --check .

# frontend (a partir da T5)
cd frontend
npm run lint
npm run build
```

## Rodar

```powershell
# API
uvicorn app.main:app --reload --port 8000     # docs em /docs

# workers (ingestão, regras, entrega)
celery -A app.workers.celery_app worker -l info
celery -A app.workers.celery_app beat -l info
```

## Armadilhas conhecidas

1. **`DATABASE_URL` precisa do driver PostGIS.** `postgresql+postgis://` — não
   `postgresql://` — senão `CREATE EXTENSION postgis` falha no Alembic.
2. **`.env` não é lido por caminhos relativos.** `GEE_CREDENTIALS_JSON` é um caminho: use
   caminho **absoluto** ou resolva relativo à raiz do repo no `settings`.
3. **Google Drive (`H:\Meu Drive\`) é sync, não disco local.** Docker Desktop precisa
   do arquivo compartilhado explicitamente; para volumes, prefira bind mount em caminho
   local. Também pode dar *file sharing violation* em bind mount do Drive — **não monte
   `H:\Meu Drive` dentro do container**.
4. **Postgres e porta 5432.** Se já houver outro Postgres na máquina, usar 5433 e
   ajustar `DATABASE_URL`.
5. **FIRMS tem rate limit.** O adapter precisa de backoff; não usar workers concorrentes
   sobre a mesma chave.
6. **Cron do Celery no Windows** não é nativo. Usar `celery beat` com `-S` ou o
   `celery beat` em container.
7. **NUNCA** `docker compose down -v` se o volume tem dado de teste que importa.
