# data/ — geometrias de referência (NÃO versionado)

Esta pasta é **ignorada pelo git** (ver `.gitignore`). Contém arquivos de referência
grandes que não devem entrar no histórico do repositório.

## Procedência dos arquivos

| Arquivo | Origem | SHA-256 | Bytes |
| :--- | :--- | :--- | :--- |
| `shapes_de_todas_as_unidades_com_gerencia.geojson` **(original, como recebido)** | Fornecido pelo NGEO (IDEFLOR-Bio), 21/10/2026 | `ce592a39adb69b8da1551efe1f30813ce37288f4ab40ca38ebee1908cb03f819` | 6.883.607 |
| `shapes_de_todas_as_unidades_com_gerencia.geojson` **(corrigido, em uso)** | idem + correção da sigla (issue #21) | `46b0128bc8aa40da5373a5915e20e303dd941c600ecbfab328272b6a8d828b08` | 6.883.607 |

**Conteúdo:** 29 UCs estaduais do IDEFLOR-Bio, MultiPolygon EPSG:4326 (SIRGAS 2000),
com atributo `gerencia` (Gerência Regional DGMUC) e `id` sequencial 1..29.

### Correção aplicada (21/10/2026) — issue #21

A sigla vinha com **L minúsculo** no lugar do **I** romano:

| original | corrigido | UCs |
| :--- | :--- | :--: |
| `GERÊNCIA REGIONAL DA CALHA NORTE l (GRCN-l)` | `... CALHA NORTE I (GRCN-I)` | 2 |
| `GERÊNCIA REGIONAL DA CALHA NORTE ll (GRCN-ll)` | `... CALHA NORTE II (GRCN-II)` | 5 |
| `GERÊNCIA REGIONAL DA CALHA NORTE lll (GRCN-lll)` | `... CALHA NORTE III (GRCN-III)` | 2 |

Substituição literal de string, **sem tocar em geometria, atributos ou ordem das
features** (29 features preservadas; contagem de bytes idêntica). Nenhum outro valor
`gerencia` foi afetado — o `L` das demais é de "REGIONAL".

> O seed **normaliza de novo** ao carregar, porque o arquivo original volta da
> instituição. A validação de 29 UCs / 9 gerências é o que garante que a correção
> não se perca na próxima carga.


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
