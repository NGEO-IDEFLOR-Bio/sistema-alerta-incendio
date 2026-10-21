# data/ — geometrias de referência (NÃO versionado)

Esta pasta é **ignorada pelo git** (ver `.gitignore`). Contém arquivos de referência
grandes que não devem entrar no histórico do repositório.

## Procedência dos arquivos

| Arquivo | Origem | SHA-256 | Bytes |
| :--- | :--- | :--- | :--- |
| `shapes_de_todas_as_unidades_com_gerencia.geojson` | Fornecido pelo NGEO (IDEFLOR-Bio), 21/10/2026 | `ce592a39adb69b8da1551efe1f30813ce37288f4ab40ca38ebee1908cb03f819` | 6.883.607 |

**Conteúdo:** 29 UCs estaduais do IDEFLOR-Bio, MultiPolygon EPSG:4326 (SIRGAS 2000),
com atributo `gerencia` (Gerência Regional DGMUC) e `id` sequencial 1..29.

## Fonte canônica de geometrias

O repositório `visualizador` mantém o acervo geoespacial de referência
(`H:\Meu Drive\DEV\visualizador\data\`). Este sistema **consome** dali e **não duplica**
(issue #14). Arquivos de origem:

| Arquivo | Conteúdo | Onde é usado |
| :--- | :--- | :--- |
| `shapes_de_todas_as_unidades_com_gerencia.geojson` (este) | 29 UCs + gerência | `ucs` |
| `ucs_estaduais.geojson` | 29 UCs sem gerência | conferência de nomes |
| `zoneamentos_ucs_estaduais.geojson` | 252 zonas de plano de manejo em 16 UCs | `ucs_zonas` (manejo) |
| `concessoes_florestais_ideflor.geojson` | 11 concessões | features de risco (frente A) |
| `contratos_de_transicao.geojson` | 43 contratos de transição | features de risco (frente A) |
| `terras_indigenas.geojson`, `quilombos_*.geojson` | contexto | camadas do mapa |

## Consumidores

- `scripts/seed_*.py` — carga inicial no PostGIS (F1).
- `backend/src/services/` — leitura via PostGIS em runtime.

**Nada aqui é editado pelo sistema.** Correção de dado é na fonte, com nova versão
do arquivo e digest registrado aqui.
