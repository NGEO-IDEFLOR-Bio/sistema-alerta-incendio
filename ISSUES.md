# ISSUES — fonte da verdade das pendências

> Status: ✅ feito · 🟡 parcial · ⏳ pendente · ◔ bloqueado · 🗄️ arquivado · ❌ descartado
> Regra: **atualizar no mesmo commit** em que a issue for resolvida.

## Bloqueantes

| # | Issue | Status | Nota |
| :--- | :--- | :--- | :--- |
| ~~#01~~ | ~~Mapeamento UC → Gerência Regional (DGMUC)~~ | ✅ resolvido | Fornecido em `data/shapes_de_todas_as_unidades_com_gerencia.geojson` — 29 UCs, 9 gerências, `id` 1..29. Digest e procedência em `data/README.md`. **Desbloqueia F1/F3.** Ver #21 e #22 |

## Fundação

| # | Issue | Status | Nota |
| :--- | :--- | :--- | :--- |
| **#02** | Bootstrap do repo (docs, `.gitignore`, `git init`) | ✅ feito | Fase F0 — 21/10/2026 |
| **#03** | `docker-compose.yml` (PostGIS + Redis) + `scripts/` de seed | ✅ **feito** (F1, 21/10/2026) | `docker-compose.yml` (PostGIS 16-3.6 + Redis 7, porta **5433** porque 5432 já tinha um Postgres local) + `scripts/seed_{gerencias,ucs,zonas,fontes,all}.py`. `docker compose config` válido |
| **#04** | Schema das tabelas canônicas | ✅ **feito** (F1, 21/10/2026) | Migração Alembic `20261021_0001` — 13 tabelas do §5 (incl. `focos_grupos`, `fontes`, `parametros_dedup` do D-013/D-014). `upgrade head` e `downgrade base` verificados |
| **#05** | Registro de chaves/licença por fonte de focos | 🟡 **parcial** | T0 (21/10/2026): tabela `fontes` especificada no PLANO §5.11 (resolução, latência, URL, termos, atribuição, licença, pin de versão). Falta popular e exibir a atribuição no painel/relatório — issue #07 |

## Qualidade de dados de referência (NOVO)

| # | Issue | Status | Nota |
| :--- | :--- | :--- | :--- |
| **#21** | Sigla de gerência com L minúsculo (`GRCN-l`/`ll`/`lll`) | ✅ **resolvido** | Corrigido **no arquivo** em 21/10/2026: `CALHA NORTE l/ll/lll` → `I/II/III` no nome e na sigla. 29 features e geometria intactas. Digest original e corrigido em `data/README.md`. O seed mantém a validação 29 UCs / 9 gerências, porque o arquivo original volta da instituição. |
| **#22** | Registry de gerências divergente entre `maps` e o arquivo atual | ✅ **resolvido** | Corrigido em `maps` (commit `72b0eee`, push 21/10/2026): registry de `organize_and_build.py`, `data.js` gerado, `<select>` do `index.html` e tabela do README alinhados às 9 gerências vigentes. GRCN-III/GRTUC/GRM/GRNE incorporadas; GRMR/GRET/GRBA/GRT removidas; GRCN-II e GRX mantiveram ids (17 produtos preservados). `visualizador` verificado: sem resíduo. |

| **#23** | Zoneamento: `SIGLA` não é global; `UNIDADE` truncada; join por nome inviável | 🟡 **parcial** | **Não padronizar** (D-009): cada plano de gestão nomeia e define as suas próprias zonas; taxonomia global destruiria o significado. `sigla` e `zona` ficam **verbatim**. Join UC↔zona por **sobreposição espacial** — `UNIDADE` está truncado ("Ambiental da Ilha de Combu", "Reserva Biológica do Maicuru (REBIO"). Regra de negócio **nunca** por `sigla`. |
| **#27** | Alerta: zona verbatim + coordenada, **sem texto instrutivo** | 🟡 pendente | Requisito de conteúdo (D-009, D-011): `zona_sigla`, `zona_texto`, coordenada decimal + UTM, severidade, confiança, nº de focos, fontes, link do mapa. **Sem** "verifique antes de agir", sem lembrete de plano, sem definição de termo, sem "quem é o responsável" no corpo. Campo `ref_plano` **removido** do payload do alerta. |
| **#29** | Sigla `GRCN-l/ll/lll` **no cadastro oficial** — corrigir na fonte | 🟡 pendente | O erro **não é só do arquivo**: a página oficial "Shapes de cada unidade" (<https://ideflorbio.pa.gov.br/shapes-de-cada-unidade>) grava "Calha Norte l/ll/lll", e o shapefile consolidado reproduz. A mesma substituição I→l aparece no portal em `UMF l/ll/lll`, `UMF Vlll`, `Umf lX`. É sistemático na publicação do IDEFLOR. A cópia local foi corrigida (#21), mas **todo re-download reintroduz o defeito**. Requer ação upstream. |
| **#30** | Sigla **GRM** (Marajó) não consta na página "Shapes de cada unidade" | 🟡 pendente | A página oficial lista "GERÊNCIA REGIONAL DO MARAJÓ" **sem sigla**; a sigla GRM vem apenas do shapefile consolidado. Não é erro, mas é proveniência desigual entre as 9 gerências — vale confirmar com a DGMUC e publicar. |

| **#28** | Autenticação do dashboard | ⏳ pendente | MVP aberto em rede institucional. Autenticação só quando houver dado que exija (PII, por-ACESSO) |

| **#24** | Zoneamento cobre parte das 29 UCs | 🟡 **parcial** | **Medido na F1 (21/10/2026): 20 das 29 UCs** têm zoneamento (o repo afirmava 16 — esse número vinha da contagem de strings do campo `UNIDADE`, truncado). **9 UCs** sem classificação de zona → alerta segue emitido **sem** contexto de zona, com limitação explícita (nunca suprimido) |
| **#25** | Zonas de Amortecimento só para poucas UCs | 🟡 pendente | ZA cartografada em Trombetas, REVIS (setores I/II/III), Paru, Faro. Issue #15 original: **parcialmente resolvida** — ZA não é universal. |



## Identidade visual / DS

| # | Issue | Status | Nota |
| :--- | :--- | :--- | :--- |
| **#08** | Migrar `maps` para `ngeo-ds` | ⏳ pendente | Sessão própria, depois do dashboard |
| **#09** | Migrar `visualizador` para `ngeo-ds` | ⏳ pendente | Sessão própria, depois do dashboard |
| **#10** | Escala semântica de severidade + rampa de calor perceptual | ⏳ pendente | F5 / `ngeo-ds`. Vermelho-amarelo-verde **não** usar |
| **#11** | Repo `ngeo-ds` (tokens, componentes, fontes, logos) | ⏳ pendente | Consumption via CDN pinado por tag |
| **#12** | Canonicalizar nomes de assets (`logo_ngeo.png` vs `logo-ngeo.png`) | ⏳ pendente | Resolvido naturalmente pelo `ngeo-ds` |

## Dados e fontes

| # | Issue | Status | Nota |
| :--- | :--- | :--- | :--- |
| **#07** | Registrar termos de uso, atribuição e redistribuição por fonte (FIRMS, INPE, GOES/AWS, Sentinel Hub) | 🟡 **parcial** | T0 (21/10/2026) coletou o texto de atribuição verificado de FIRMS/LANCE, ESA WorldCover (CC BY 4.0), Copernicus DEM e NOAA GOES-R (em `docs/ESTADO_DA_ARTE.md` §4 e §10). **Falta**: texto legal do INPE (Guia de Estilo) e licença do MapBiomas — ambos **NÃO VERIFICADOS**; e implementar o *duty* no painel/relatório |
| **#13** | Conceder/registrar chaves: FIRMS API, INPE, Sentinel Hub, Telegram bot | 🟡 **parcial** | **FIRMS: OK** — MAP_KEY obtida e testada em 21/10/2026 (ver #31 para a reemissão institucional). **INPE: não precisa de chave** (dados abertos, sem autenticação) — remover `INPE_API_KEY` do `.env.example`. **Sentinel Hub** e **Telegram**: pendentes |
| **#31** | MAP_KEY do FIRMS emitida para **e-mail descartável** | 🟡 pendente | A chave foi obtida em 21/10/2026 e funciona (coleta real: 811 registros). Mas foi emitida para um e-mail temporário — reemitir sob **e-mail institucional**, guardar em `secrets/` e atualizar o `MAP_KEY` no `.env`. Enquanto isso: risco de perda de acesso ao portal de gerenciamento da chave |
| **#32** | **Calibrar a janela temporal do dedup** (6 h, D-013) | ⏳ pendente | O valor de 6 h é uma **inferência** (espaçamento de passagem de órbita polar), **não verificada**. A F2 tem de calibrar contra dados reais (mesmo fogo visto por VIIRS/MODIS/GOES) e registrar o valor escolhido em `DECISIONS.md` (D-013) |
| **#33** | Schema real de **MODIS, GOES e INPE** ainda não coletado | ⏳ pendente | Só o **VIIRS** foi coletado de verdade (21/10/2026). O schema do MODIS difere (`brightness`/`bright_t31`) e o GOES não é SOURCE do `/api/area` do FIRMS (`GOES_NRT` só em `/api/data_availability`). F2 precisa de uma chamada real por fonte antes de fixar o mapeamento |
| **#34** | `DATABASE_URL` **vazio** no `.env` | ✅ resolvido (F1) | Preenchido com `postgresql+psycopg2://postgres:postgres@localhost:5433/alerta_fogo` (driver psycopg2 — o `postgresql+postgis://` do `.env.example` antigo **não existe** no SQLAlchemy; a extensão postgis é criada na migração) |
| **#36** | **Alerta de risco diário pode virar rotina** (e perder a confiança da gerência) | ⏳ pendente | D-016: `RISCO_ALTO` só dispara com **novidade** (mudança de faixa desde o último alerta da UC), além de cruzar o limiar. Implementar e testar na F3 |
| **#37** | **Alerta de concorrência: ALARMES (LASA/UFRJ) tem dois produtos *em breve* na frente A** | ⏳ pendente | *Panorama Ignições Naturais* e *Probabilidade de Excedência de Área Queimada* (ambos "Em breve" em <https://alarmes.lasa.ufrj.br/>). A frente A só se sustenta como **ignição por UC + SHAP local no alerta**, não como "risco de fogo na Amazônia" genérico. Monitorar e posicionar o paper contra eles |
| **#38** | **9 das 252 zonas não intersectam nenhuma das 29 UCs** | 🟡 **pendente** | Medido na F1. 8 não têm sobreposição (A2/OT1–OT5/ZNI) e 1 vem **sem geometria** no arquivo (ZR / Zona de Recuperação). **O campo `UNIDADE` dessas 9 mente**: aponta para Faro, Trombetas e Mosaico Lago de Tucuruí, mas a geometria está a 250 km dali. O join espacial (é o que vale) resolve 243. Registrar a divergência com a DGMUC/IDEFLOR |
| **#35** | INPE: o nome "MONITORQUEIMADAS" não existe | 🟡 resolvido | O INPE mantém o **Programa Queimadas / BDQueimadas** (focos a cada 10 min, CSV/KML, WFS/WMS, **sem autenticação**). Nenhum registro oficial de "MONITORQUEIMADAS" em 21/10/2026. `DECISIONS.md` D-012 e PLANO §6 corrigidos |
| **#14** | Geometria de referência: fonte única | 🟡 parcial | `data/` deste repo (gitignored) + `visualizador/data/`. Consolidar em `ngeo-assets` (issue #11 junto) |
| **#15** | ~~Zonas de amortecimento das UCs~~ | 🟡 parcial | ZA existe para poucas UCs (Trombetas, REVIS, Paru, Faro) — ver #25 |


## Produto

| # | Issue | Status | Nota |
| :--- | :--- | :--- | :--- |
| **#16** | Basemap auto-hospedado (uso institucional + offline) | ⏳ pendente | MVP usa OSM/Esri |
| **#17** | "Pacote da UC" offline (GeoJSON + raster + PDF) | ⏳ pendente | F5/F8 — campo sem sinal |
| **#18** | Relatório PDF operacional por UC | ⏳ pendente | Entregável de campo; já previsto em RF10 |
| **#19** | Posicionamento público: "detecção NRT ≤1 h" + "risco diário" | 🟡 **parcial** | **Corrigido em 21/10/2026 (D-015):** o alvo de 1 h só é viável para o Pará via **GOES (recência ≤ 30 min)**; a **detecção de alta resolução (FIRMS VIIRS) é < 3 h** (URT/RT são só EUA/Canadá). Nunca "previsão em tempo real" (R3) |
| **#20** | Repo `ml-fire-alert` (frente A, pesquisa) | ⏳ pendente | Recriar quando a frente A entrar (F6) |

## Descartado

| # | Item | Status | Nota |
| :--- | :--- | :--- | :--- |
| ~~#00~~ | `ml-fire-alert` como repo de pesquisa inicial | ❌ descartado | Era duplicata de `visualizador/data` (GeoJSON byte-idênticos). Recriar em F6 com escopo de pesquisa (D-006) |
| ~~#00~~ | Máquina de estados do alerta / workflow de atendimento | ❌ descartado | Decisão D-003 — o NGEO notifica; a ação é da gerência regional |
| **#26** | Curadoria por UC do que o plano diz sobre fogo em cada zona | ❌ descartado | Decisão do NGEO (21/10/2026): não há necessidade de explorar se é permitida fogo em alguma zona. A zona é **informação** e nada mais (D-009). Consequência aceita: o confundidor "fogo de manejo" nos rótulos da frente A permanece como **limitação declarada**, não como problema resolvido |
| ~~#00~~ | Paywall / lead-gen no download de dados brutos | ❌ descartado | Inviável/institucionalmente estranho num sistema do IDEFLOR. Se houver portal público, o gate fica lá |
