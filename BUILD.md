# BUILD — como rodar, verificar e armadilhas do ambiente

> Estado: **F1 implementada** (21/10/2026) — PostGIS + Redis + schema Alembic + seeds
> + `/api/health`. F2 (ingestão) ainda não implementada.
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

## Setup (F1)

```powershell
Copy-Item .env.example .env
# editar .env com as chaves reais (DATABASE_URL, REDIS_URL, chaves de fonte)

docker compose up -d
docker compose ps          # esperar postgis e redis healthy

# Python (uma unica venv na raiz do repo)
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -e ".[dev]"

# schema
python -m alembic -c backend/alembic.ini upgrade head

# carga da referencia (idempotente; ~28 s)
python scripts/seed_all.py          # ou seed_gerencias / seed_ucs / seed_zonas / seed_fontes

# API
uvicorn ngeo.main:app --reload --port 8000
# http://127.0.0.1:8000/api/health
```

**O seed roda na HOST**, contra o Postgres exposto em `127.0.0.1:5433`. Os arquivos de
referência (`data/`, `../visualizador/data/`) **não** são montados no container
(armadilha #3).

## Verificação (OBRIGATÓRIA antes de commit)

```powershell
# raiz do repo — vale para TUDO (backend, scripts, tests): é o unico projeto Python
python -m pytest -q
ruff check .
ruff format --check .

# frontend (a partir da T5) — ainda não existe
cd frontend
npm run lint
npm run build
```

**Sobre a suíte:** 48 testes. Os que dependem do Postgres local são **pulados** se o
banco não estiver no ar (`docker compose ps` mostra `healthy`). Com o banco no ar, a
suíte inteira leva **~65 s** — o seed roda duas vezes (idempotência) e custa ~28 s por
vez. Para pular os testes de banco: `python -m pytest -q -m "not banco"`.

**Ferramentas:** Python ≥ 3.12, `pytest` ≥ 8, `ruff` ≥ 0.6 (ambos em `pip install -e ".[dev]"`
ou `pip install pytest ruff`). Config em `pyproject.toml` (linha 100, `target-version = py312`).

## Probe do FIRMS (T0)

```powershell
$env:FIRMS_API_KEY = "<MAP_KEY>"          # chave gratuita: https://firms.modaps.eosdis.nasa.gov/api/map_key/
python scripts/probe_firms.py --source VIIRS_NOAA20_NRT --date 2026-10-19
```

Grava o payload cru e o relatório de schema em `data/probes/` (**gitignored**).
O teste (`tests/test_probe_firms.py`) roda **sem rede**, com a fixture gravada.

## Rodar

```powershell
# API
uvicorn app.main:app --reload --port 8000     # docs em /docs

# workers (ingestão, regras, entrega)
celery -A app.workers.celery_app worker -l info
celery -A app.workers.celery_app beat -l info
```

## Armadilhas conhecidas

1. **`DATABASE_URL` usa o driver do SQLAlchemy, não um "driver PostGIS".** O dialeto
   `postgresql+postgis://` **não existe** (erro em tempo de import). Use
   `postgresql+psycopg2://` (ou `postgresql+psycopg://`) e crie a extensão na migração:
   `CREATE EXTENSION IF NOT EXISTS postgis`. Corrigido em 21/10/2026 (issue #34).
   A migração também remove o `postgis_tiger_geocoder` que a imagem instala por
   padrão (schema `tiger` no `search_path`, tabelas de nome genérico).
2. **`.env` não é lido por caminhos relativos.** `GEE_CREDENTIALS_JSON` é um caminho: use
   caminho **absoluto** ou resolva relativo à raiz do repo no `settings`.
3. **Google Drive (`H:\Meu Drive\`) é sync, não disco local.** Docker Desktop precisa
   do arquivo compartilhado explicitamente; para volumes, prefira bind mount em caminho
   local. Também pode dar *file sharing violation* em bind mount do Drive — **não monte
   `H:\Meu Drive` dentro do container**.
4. **Postgres e porta 5432.** Já havia um Postgres local na 5432 (21/10/2026) — o
   compose usa **5433**. Ajustar `POSTGRES_PORT` e `DATABASE_URL` juntos.
   `POSTGRES_PORT`/`REDIS_PORT` controlam o bind; o container sempre escuta em 5432/6379
   dentro do compose.
5. **FIRMS tem rate limit.** O adapter precisa de backoff; não usar workers concorrentes
   sobre a mesma chave.
6. **Cron do Celery no Windows** não é nativo. Usar `celery beat` com `-S` ou o
   `celery beat` em container.
7. **NUNCA** `docker compose down -v` se o volume tem dado de teste que importa. (Usado
   em 21/10/2026 para recriar o volume limpo durante a F1.)
8. **Bind mount de arquivo do `H:\Meu Drive` não funciona** (o Docker cria um
   diretório vazio no lugar do arquivo). Por isso a normalização do
   `postgis_tiger_geocoder` foi feita **na migração**, e não por init script.
9. **Geometria inválida nos arquivos do IDEFLOR.** Varias features tîm
   auto-interseção; `ST_Intersection` lça `TopologyException` com a geometria crua.
   A geometria é gravada já saneada (`ST_MakeValid`) na carga. O **join espacial roda
   em SQL**, não em Python: em Python o mesmo join leva ~3 min (e depende da
   estratégia de reparo); em SQL, a carga completa leva ~28 s.
10. **`ST_MakeValid` custa ~21 s** nas 252 zonas — é o custo dominante da carga. Não
   repetir por par de geometria.
