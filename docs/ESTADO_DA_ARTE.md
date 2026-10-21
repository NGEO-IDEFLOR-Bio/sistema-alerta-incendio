# ESTADO DA ARTE — detecção NRT, risco, propagação e a lacuna do NGEO

> **Data de acesso de todas as fontes externas: 21/10/2026.** Toda afirmação factual
> abaixo tem URL. O que não foi verificado está marcado **NÃO VERIFICADO** — não há
> número, referência ou métrica inventada neste documento.
>
> Este documento **não** decide o que o sistema faz. Ele apura o terreno. As decisões
> ficam em `DECISIONS.md` (D-012 a D-014) e o reflexo no plano, em
> `PLANO_ARQUITETURA.md` §5/§6/§12.
>
> **Escopo do apuro:** o que já existe para detectar fogo por satélite, qual modelo de
> risco e de propagação é reaproveitável, o que já foi publicado sobre a Amazônia, o que
> os sistemas brasileiros e amazônicos já entregam — e, feita essa conta honesta, **se a
> lacuna que o NGEO propose se sustenta**.

---

## 0. Resumo executivo (leitura de 3 minutos)

1. **A detecção NRT já existe e é gratuita.** O NASA FIRMS entrega focos por satélite
   com **< 3 h de latência** para o mundo todo, incluindo o Pará — *desde que se use a
   modalidade NRT* (URT/RT são só EUA/Canadá). O INPE mantém um programa próprio
   ("Programa Queimadas" / BDQueimadas) com **focos a cada 10 minutos** e **estatística
   por Unidade de Conservação estadual** no Infoqueima.
2. **O briefing tinha premissas erradas.** `MONITORQUEIMADAS` **não existe** com esse
   nome no INPE hoje; `MapBiomas Alerta` é **desmatamento**, não fogo; `MCD14DL` **não**
   é LST (é fogo ativo MODIS NRT); a **ITU-R BT.839** **não foi localizada** (o número
   T.839 da ITU-T é JPEG XR). Detalhes em §1.4, §5 e §8.
3. **O risco de ignição já tem literatura brasileira**, mas ela resolve *susceptibilidade*
   (estática), não *ignição* (dinâmica, com horizonte de dias). Não existe, no material
   apurado, **SHAP local auditável por UC para risco de ignição na Amazônia** — o
   precedente mais próximo é fora do escopo (Cerrado).
4. **Propagação é viável, mas cara de insumo.** FARSITE não é mais distribuído (vive
   dentro do FlamMap) e precisa de mapa de combustível; **não existe fuel map padronizado
   para a Amazônia** em resolução operacional. O precedente brasileiro (FISC-Cerrado,
   UFMG+INPE) **construiu** o mapa de combustível. Isso é a dependência dura da frente B.
5. **A lacuna do NGEO se sustenta em 2 de 4 e não em 2 de 4.** (Reapurado em 21/10/2026
   com ALARMES/SIFAU/Savana: o veredito **não muda** — nenhum deles endereça o evento
   à gerência nem cita a zona do plano.)
   - ✅ **Roteamento institucional por Gerência Regional** — nenhum produto audited
     (INPE, Censipam, MMA, SEMA-AM/MT, FISC-Cerrado) endereça o evento à gerência da UC.
   - ✅ **Citação do zoneamento do plano de gestão no alerta** — nenhum produto auditado
     carrega a zona do plano como atributo do evento.
   - ❌ **SHAP local auditável por UC** — existe quase isso no Cerrado (preprint de
     jun/2026, com hold-out por AOI e SHAP por AOI). A originalidade aqui é **parcial e
     frágil**.
   - ❌ **Uso offline em campo** — nenhum produto oficial auditado oferece pacote
     offline; é decisão de produto, não lacuna de domínio.
6. **O risco de terceiro é real e mensurável.** 3 dependências externas cadeadas
   (FIRMS → INPE → NOAA) com termos de uso que **já** mudaram (Copernicus DEM 30 m
   passou a exigir registro em 28/07/2026) e um único provedor que **já foi renomeado**
   (GOES-16 → GOES-19 em 07/04/2025, enquanto o INPE ainda rotula "GOES-16 BR").

---

## 1. Detecção de fogo em tempo quase-real (NRT)

### 1.1 NASA FIRMS — fonte primária de focos

| Atributo | Fato verificado | Fonte | Obs. |
| :--- | :--- | :--- | :--- |
| O que é | Sistema LANCE (MODAPS) da NASA/GSFC/EOS/ESDIS. Detecção de **fogo ativo** por anomalia termal. A coordenada é o **centro do pixel**, não a coordenada do fogo | <https://www.earthdata.nasa.gov/data/tools/firms/faq> | Reforça a regra do AGENTS: "posição de foco é pixel, não coordenada" |
| MODIS — resolução | **1 km** (MODIS Terra/Aqua) | <https://www.earthdata.nasa.gov/data/tools/firms/faq> | |
| MODIS — revisita | "generally these have two overpasses a day" | <https://www.earthdata.nasa.gov/data/tools/firms/faq> | |
| VIIRS — resolução | **375 m** (Suomi-NPP, NOAA-20, NOAA-21) | <https://www.earthdata.nasa.gov/data/tools/firms/faq> · <https://www.earthdata.nasa.gov/learn/find-data/near-real-time/firms/vj114imgtdlnrt> | |
| Latência NRT (global) | **< 3 horas** da observação de satélite | <https://www.earthdata.nasa.gov/data/tools/firms/faq> | |
| RT (Real-Time) | NASA EOSDIS define RT = disponível em até **60 minutos** da passagem | <https://firms.modaps.eosdis.nasa.gov/api/area> | |
| URT (Ultra Real-Time) | "< 60 seconds of satellite fly over **for much of the US and Canada**"; o FAQ diz "URT within 5 minutes" | <https://firms.modaps.eosdis.nasa.gov/api/area> · <https://www.earthdata.nasa.gov/data/tools/firms/faq> | ⚠️ **URT e RT são só EUA/Canadá. Para o Pará só existe NRT.** Isto derruba qualquer promessa de latência abaixo de ~3 h para o Pará |
| Cobertura do Pará | **Sim**, nas modalidades NRT/SP | <https://www.earthdata.nasa.gov/data/tools/firms/faq> | |
| Formatos | NRT: TXT, SHP, KML, WMS + API (`csv`, `json`) | <https://www.earthdata.nasa.gov/learn/find-data/near-real-time/firms/vj114imgtdlnrt> · <https://firms.modaps.eosdis.nasa.gov/api/area> | "only the TXT and SHP files contain all the attributes" |
| Custo / chave | **Gratuito** com MAP_KEY (cadastro por e-mail, limite **5000 transações / 10 min**); download de arquivo exige Earthdata Login | <https://firms.modaps.eosdis.nasa.gov/api/map_key/> · <https://firms.modaps.eosdis.nasa.gov/api/area> | |
| Atribuição (texto) | *"We acknowledge the use of imagery from the NASA LANCE FIRMS (https://earthdata.nasa.gov/firms), part of the NASA Earth Science Data and Information System (ESDIS)."* | <https://www.earthdata.nasa.gov/data/tools/firms/faq> | |

**Endpoint verificado na prática (21/10/2026):**

```
/api/area/csv/[MAP_KEY]/[SOURCE]/[AREA_COORDINATES]/[DAY_RANGE]/[DATE]
```

- `SOURCE` válidos: `MODIS_NRT`, `MODIS_SP`, `VIIRS_NOAA20_NRT`, `VIIRS_NOAA20_SP`,
  `VIIRS_NOAA21_NRT`, `VIIRS_NOAA21_SP`, `VIIRS_SNPP_NRT`, `VIIRS_SNPP_SP`,
  `LANDSAT_NRT` (só EUA/Canadá) — <https://firms.modaps.eosdis.nasa.gov/api/area>.
- `AREA_COORDINATES` = `west,south,east,north` ou `world`; **`DAY_RANGE` 1..5**.
- `GOES_NRT` aparece em `/api/data_availability`, **não** na lista de SOURCE do
  `/api/area` — <https://firms.modaps.eosdis.nasa.gov/content/academy/data_api/firms_api_use.html>.
  ⚠️ O `goesr_abi_c1_nrt` citado no briefing **não existe** como SOURCE documentado.

**Schema observado — ver §7 (coleta real).** O schema **difere por sensor**: VIIRS
traz `bright_ti4`/`bright_ti5`; MODIS traz `brightness`/`bright_t31`.

### 1.2 INPE — "Programa Queimadas" / BDQueimadas

| Atributo | Fato verificado | Fonte |
| :--- | :--- | :--- |
| Nome real | **"Programa Queimadas do INPE"**, base **BDQueimadas** (acervo desde 1998) | <https://data.inpe.br/queimadas/> · <https://data.inpe.br/queimadas/bdqueimadas/> |
| ⚠️ MONITORQUEIMADAS | **NÃO VERIFICADO — nenhum registro oficial.** Nenhuma página do INPE com esse nome foi encontrada em 21/10/2026. O nome parece vir do programa homônimo dos anos 2000 | <https://data.inpe.br/queimadas/> |
| Sensores | 10 satélites, resolução **375 m a 4 km**: NOAA (18, 19, 20), GOES (16), TERRA, AQUA, S-NPP, METOP (B e C), METEOSAT (11) | <https://data.inpe.br/queimadas/portal/pages/secao_relatorio/integrado/index.html> |
| Latência | Focos de Queimada **a cada 10 minutos**; Eventos de Fogo **a cada hora** | <https://data.inpe.br/queimadas/dados-abertos/> |
| Formatos | Focos: CSV (10 min, diários, mensais, anuais) e KML (3 dias, "GOES-16 BR", diários) · Eventos de Fogo: KML e GPKG · Área Queimada AQ1km: TIFF e Shapefile (mensal) · **WFS/WMS via GeoServer** | <https://data.inpe.br/queimadas/dados-abertos/> |
| Cobertura do Pará | **Sim**, com estatística **por estado** (Pará) e **por UC** (camada "Áreas Protegidas" no BDQueimadas; Infoqueima já monitora "Unidades de Conservação Estaduais") | <https://data.inpe.br/queimadas/bdqueimadas/> · <https://www.gov.br/inpe/pt-br/assuntos/ultimas-noticias/boletim-infoqueima-apresenta-panorama-das-queimadas-e-do-risco-de-fogo-no-brasil-em-junho-de-2026> |
| Custo | Gratuito, sem autenticação — "Dados Abertos para Uso Público" | <https://data.inpe.br/queimadas/dados-abertos/> |
| Atribuição | Rodapé "Programa Queimadas do INPE — Dados Abertos para Uso Público". Texto legal completo: **NÃO VERIFICADO** (Guia de Estilo não lido) | <https://data.inpe.br/queimadas/> |
| API REST oficial | **NÃO VERIFICADO** — não há API REST documentada; há WFS/WMS OGC e CSV | <https://data.inpe.br/queimadas/> |
| "Risco de Fogo" | Produto do INPE: **FWI observado + previsão para 3 dias** (risco, precipitação, temperatura, UR, nº de dias sem chuva, fumaça) | <https://data.inpe.br/queimadas/dados-abertos/> |
| Referência técnica | Bernini, H.; Morelli, F.; … Melo, S.L.V.d. *Modeling Multi-Sensor Daily Fire Events in Brazil: the DescrEVE relational framework*. Remote Sens. 2026, 18, 606. doi:10.3390/rs18040606 | <https://data.inpe.br/queimadas/evento-fogo/> |

### 1.3 MapBiomas — "Alerta" e "Fogo"

| Atributo | Fato verificado | Fonte |
| :--- | :--- | :--- |
| ⚠️ MapBiomas **Alerta** | **É desmatamento, não fogo.** "MapBiomas Alerta é um sistema de validação e refinamento de alertas de desmatamento com imagens de satélite de alta resolução"; alertas **semanais** | <https://alerta.mapbiomas.org/> |
| MapBiomas **Fogo** (Coleção 5 / 5.1) | Mapeamento **anual e mensal** de cicatrizes, **1985–2025**; método **Landsat 30 m** + deep neural network; validação contra MCD64A1, GABAM, FIRE CCI, INPE focos, FIRMS, ICMBIO | <https://brasil.mapbiomas.org/en/mapbiomas-fogo> · <https://brasil.mapbiomas.org/wp-content/uploads/sites/4/2026/05/ATBD-MapBiomas-Fogo-Colecao-5.pdf> |
| **Assets GEE** (não é "coleção" é um nome de pasta) | `projects/mapbiomas-public/assets/brazil/fire/collection5/mapbiomas_fire_collection5_annual_burned_v1` (anual) · `.../collection5_1/mapbiomas_fire_collection51_monthly_burned_v1` (mensal, Coleção 5.1) · `..._severity_class_v1` · `..._interval_since_fire_v1` · `..._fire_frequency_v1` · `..._year_last_fire_v1` · `..._time_after_fire_v1` · `.../fire/monitor/mapbiomas_fire_monthly_burned_v1` (Monitor do Fogo, Sentinel-2, mensal, desde 2019) | <https://brasil.mapbiomas.org/en/mapbiomas-fogo> · <https://brasil.mapbiomas.org/downloads/assets-no-google-earth-engine/> |
| ⚠️ **A plataforma MapBiomas já entrega estatísticas por áreas protegidas** | "downloading of tables and charts organized by different territorial units such as biomes, states, and municipalities, as well as land tenure categories like **protected areas**, indigenous territories, rural settlements, and quilombola territories" | <https://brasil.mapbiomas.org/en/mapbiomas-fogo> |
| "Monitor do Fogo" | Mosaicos **Sentinel-2**, periodicidade **mensal**, desde 2019 | <https://brasil.mapbiomas.org/en/mapbiomas-fogo> |
| Uso no NGEO | **Rótulo histórico** de área queimada (frente A) — **não** serve como detecção NRT (mensal/anual) | idem |
| GEE assets | `projects/mapbiomas-public/assets/brazil/fire/collection5/...` | <https://brasil.mapbiomas.org/en/mapbiomas-fogo> |
| Custo/licença | Gratuito. Licença específica (CC BY 4.0?): **NÃO VERIFICADO** | <https://brasil.mapbiomas.org/wp-content/uploads/sites/4/2026/05/ATBD-MapBiomas-Fogo-Colecao-5.pdf> |

### 1.4 GOES-16 / GOES-R ABI — produto de hotspot NOAA

| Atributo | Fato verificado | Fonte |
| :--- | :--- | :--- |
| Produto | **NOAA GOES-R ABI Level 2 Fire/Hot Spot Characterization (FDC)**, `gov.noaa.ncdc:C01520`; prefixo S3 `ABI-L2-FDC`. Saídas: máscara, **FRP**, temperatura instantânea do fogo, tamanho do fogo | <https://catalog.data.gov/dataset/noaa-goes-r-series-advanced-baseline-imager-abi-level-2-fire-hot-spot-characterization-fdc> |
| Resolução | **2 km** na grade fixa do ABI (Full Disk e CONUS); cresce em direção à borda do disco (NCEI registra "1 km - < 10 km") | <https://developers.google.com/earth-engine/datasets/catalog/NOAA_GOES_16_FDCF> · <https://www.ncei.noaa.gov/access/metadata/landing-page/bin/iso?id=gov.noaa.ncdc%3AC01520> |
| Cadência | FHS a cada **10 min** (Full Disk), 5 min (CONUS) | <https://www.star.nesdis.noaa.gov/atmospheric-composition-training/documents/G16_ABI_FDC_ReadMe.pdf> |
| Maturidade | FHS "is considered Full Validation maturity as of March 30, 2020" | idem |
| ⚠️ Cobertura do Pará | **Sim** — GOES East cobre as Américas. Mas **GOES-16 foi substituído pelo GOES-19 como GOES East em 07/04/2025**; o INPE ainda rotula "GOES-16 BR" nos downloads | <https://developers.google.com/earth-engine/datasets/catalog/NOAA_GOES_16_FDCF> |
| ⚠️ Viés de terreno | *"L2 product pixel locations are not corrected for terrain, so GOES fires will appear offset from other data sources, particularly in elevated terrain"* — relevante para UCs do Pará | <https://www.star.nesdis.noaa.gov/atmospheric-composition-training/documents/G16_ABI_FDC_ReadMe.pdf> |
| Custo | Sem custo; bucket público `noaa-goes16` (us-east-1) e GEE. Requer NOAA CLASS / Earthdata Login para download | <https://catalog.data.gov/dataset/noaa-goes-r-series-advanced-baseline-imager-abi-level-2-fire-hot-spot-characterization-fdc> |
| Citação (texto) | *"GOES-R Algorithm Working Group and GOES-R Program Office, (2018): NOAA GOES-R Series Advanced Baseline Imager (ABI) Level 2 Fire/Hot Spot Characterization (FDC)."* | idem |

**Leitura para o NGEO:** o GOES-16 é o sensor de **maior cadência** (10 min) e o único que
dá **cobertura horária real** da Amazônia. Mas a resolução de 2 km e o **viés de
terreno não corrigido** o tornam **complementar**, não substituto do VIIRS (375 m).
Ele é o que permite "o fogo ainda está lá?" em vez de "o fogo existiu às 16:33?".

### 1.5 GFAS

| Atributo | Fato verificado | Fonte |
| :--- | :--- | :--- |
| O que é | *"assimila observações de FRP de sensores satellitais para produzir estimativas de emissões de queima de biomassa"*. **Não é detecção de ponto** — é reanálise/assimilação | <https://confluence.ecmwf.int/spaces/CKB/pages/601301528/CAMS%2Bglobal%2Bbiomass%2Bburning%2Bemissions%2Bbased%2Bon%2Bfire%2Bradiative%2Bpower%2BGFAS%2Bdata%2Bdocumentation> |
| Versão vigente | **CAMS GFAS v1.4.2** (implementação 05/dez/2025), assimila FRP de VIIRS **e** MODIS | idem |
| Resolução | **0.1° × 0.1°** (nativa ~9 km) | idem |
| Granularidade / latência | "runs hourly"; campos horários produzidos **~7,5 h** após o horário válido; médias 24 h ~1 dia + 6,5 h | idem |
| NASA GFAS (GEOS-FP) | `gofas.eosdis.nasa.gov` falhou (erro de transporte) em 3 tentativas em 21/10/2026 — resolução/versão/URL: **NÃO VERIFICADO** | <https://gofas.eosdis.nasa.gov/> |

### 1.6 EFFIS (JRC)

| Atributo | Fato verificado | Fonte |
| :--- | :--- | :--- |
| O que é | European Forest Fire Information System (EC/JRC); componente do Copernicus EMS desde 2015; rede de 43 países | <https://effis.jrc.ec.europa.eu/> · <https://www.copernicus.eu/en/european-forest-fire-information-system> |
| ⚠️ Cobertura do Brasil | **Não.** Europa + Mediterrâneo + Oriente Médio/Norte da África | idem |
| ⚠️ Fonte dos focos | *"EFFIS uses the active fire detection provided by the NASA FIRMS"* — **redistribuição do FIRMS**, não fonte independente (MODIS 1 km / VIIRS 375 m) | <https://data.jrc.ec.europa.eu/dataset/e9d803fe-4426-4a45-9e6f-dd472de5c5f4> |
| Latência | *"normally updated 6 times daily and made available in EFFIS within 2-3 hours of the acquisition"* | idem |
| Área queimada | Só áreas **≥ ~30 ha** detectadas; severidade via NBR pré/pós | <https://data.jrc.ec.europa.eu/dataset/022cdeed-159f-407d-be18-0dface69ef92> |
| Risco de fogo | FWI/ISI/BUI/FFMC/DMC/DC derivados de previsão **ECMWF ~8 km** | <https://forest-fire.emergency.copernicus.eu/applications/data-and-services> |
| Licença | "European Commission reuse notice"; "No limitations"; DOI 10.2905/JRC.N660XDR. Texto literal do Data License: **NÃO VERIFICADO** | <https://data.jrc.ec.europa.eu/dataset/e9d803fe-4426-4a45-9e6f-dd472de5c5f4> |

**Leitura:** o EFFIS é útil como **referência de produto** (o que um painel de perigo
meteorológico precisa ter) e **não** como fonte de dados para o Pará. Também **não**
entrega previsão de propagação por incêndio (ver §3).

### 1.7 Quadro comparativo

| Fonte | Resolução | Latência | Pará | Custo | Tipo |
| :--- | :--- | :--- | :--- | :--- | :--- |
| FIRMS VIIRS (NRT) | 375 m | < 3 h | ✅ | chave gratuita | **detecção de ponto** |
| FIRMS MODIS (NRT) | 1 km | < 3 h | ✅ | chave gratuita | detecção de ponto |
| FIRMS GOES (via FIRMS) | 2 km no sub-satélite | ~20–30 min | ✅ (Américas) | chave gratuita | detecção de ponto, provisória |
| NOAA ABI L2 FDC (GOES-19) | 2 km (borda do disco pior) | 10 min (produção) | ✅ | gratuito, login | detecção + FRP |
| INPE Focos de Queimada | 375 m–4 km | 10 min | ✅ | gratuito | detecção de ponto |
| MapBiomas Fogo | 30 m | mensal/anual | ✅ | gratuito (GEE) | **área queimada** |
| GFAS (CAMS) | 0.1° | ~7,5 h | ✅ | gratuito | **emissões** (não foco) |
| EFFIS | (FIRMS) | 2–3 h | ❌ Europa | gratuito | redistribuição |

---

## 2. Modelos de risco

### 2.1 McArthur (Austrália) — FFDI / AFDRS

| Fato | Fonte |
| :--- | :--- |
| **McArthur FFDI (Forest Fire Danger Index, Mark 5)** combina temperatura do ar, umidade relativa, velocidade do vento e *drought factor*; calibrado para o incêndio de 1939 em Victoria (valor = 100) | <https://data.csiro.au/collection/csiro:72827> · Noble, Gill & Bary (1980), *Aust. J. Ecology* 5(2):201-203, DOI 10.1111/j.1442-9993.1980.tb01243.x |
| **AFDRS** substituiu o sistema McArthur a partir de 2022; **4 níveis**: Moderate / High / Extreme / Catastrophic (FBI 0–11 / 12–23 / 24–49 / 50–99 / 100+) | <https://www.bom.gov.au/resources/learn-and-explore/fire-weather-knowledge-centre/fire-weather-services> · <https://www.afac.com.au/AFDRS> |
| ⚠️ **Limitação declarada**: *"FFDI was historically used to define bushfire hazard… While its use in this context is no longer recommended"* | <https://researchdata.edu.au/nbic-acs-stage-exceedance-probabilities/3952262> |
| "Mark 5" como designação de origem institucional: **NÃO VERIFICADO** (a fonte primária consultada não diz "Australian Bush Fire Research") | <https://wikifire.wsl.ch/tiki-index27fc.html?page=McArthur%20Mark%205%20forest%20fire%20danger%20index> |
| "Kelly (2023), reformulação do FWI": **NÃO VERIFICADO** — buscas no Crossref e no arXiv não retornaram publicação compatível | — |
| Siglas "CFA/CFB/CFC/FFD" como rótulos oficiais: **NÃO VERIFICADO** — a nomenclatura oficial é Moderate/High/Extreme/Catastrophic | <https://www.afac.com.au/AFDRS> |

### 2.2 Canada — CFFDRS

| Fato | Fonte |
| :--- | :--- |
| Sistema oficial do Canadian Forest Service: sub-sistemas FWI System, Fire Behaviour Prediction, Accessory Fuel Moisture. NRCan o chama de *"the most widely applied forest fire danger rating system in the world"* | <https://natural-resources.canada.ca/forests-forestry/wildland-fires/canadian-forest-fire-danger-rating-system> |
| Componentes: FFMC, DMC, DC (códigos de umidade), ISI, BUI, FWI, **DSR**. Equações canônicas: Van Wagner & Pickett (1985); Lawson & Armitage (2008), *Weather Guide for the CFFDRS* | <https://natural-resources.canada.ca/forests-forestry/wildland-fires/canada-fire-weather-index-system> · <https://cwfis.cfs.nrcan.gc.ca/background/summary/fwi> |
| **FWI2025 / CFFDRS2025** em liberação por etapas (o que existe é o *Information Report GLC-X-26 (2021)*). "FFWI 2021 (van Wagner)": **NÃO VERIFICADO — não existe** | <https://natural-resources.canada.ca/forest-forestry/wildland-fires/canadian-forest-fire-danger-rating-system-generation> |
| Limitação declarada: *"The FWI does not directly measure fire occurrence; rather, it functions as a climate-based proxy for fire danger"* | <https://iopscience.iop.org/article/10.1088/2752-5295/ae249a> |
| "FUSI (Fire Under Severity Index)": **NÃO VERIFICADO** | — |

### 2.3 ITU — BT.839 e CAP

| Fato | Fonte |
| :--- | :--- |
| ⚠️ **ITU-R BT.839 "Signal transmission aspects of information for wildfire detection": NÃO VERIFICADO — provavelmente inexistente sob esse número.** (a) busca pelo título exato não retorna norma ITU; (b) na base oficial ITU-T, **T.839 = "Still-image compression — JPEG XR"** (aprovação 29/06/2019, ISO/IEC 29199-2); (c) a série "BT" é ITU-R (rádio/som), não ITU-T | <https://www.itu.int/ITU-T/recommendations/rec.aspx?id=13914> |
| ✅ **CAP — Common Alerting Protocol, ITU-T X.1303** (CAP 1.1, aprovado 13/09/2007) / **OASIS CAP v1.2** (01/07/2010): XML de alerta "all-hazard", targeting geográfico por lat/lon (**polígonos e círculos**), multilíngue, tempos efetivos/expiração, atualização/cancelamento, XSD + ASN.1 | <https://www.itu.int/ITU-T/recommendations/rec.aspx?rec=12150> · <https://docs.oasis-open.org/emergency/cap/v1.2/pr02/CAP-v1.2-PR02.pdf> |
| Uso de CAP para **alerta de incêndio no Brasil**: **NÃO VERIFICADO** | — |

**Leitura:** o briefing queria um padrão internacional de mensagem de alerta de incêndio.
O padrão **verificado** que existe e serve é o **CAP (X.1303 / OASIS v1.2)** — e ele já
geometria por círculo, o que casa com a incerteza posicional do foco.

### 2.4 Outros índices

| Fato | Fonte |
| :--- | :--- |
| **Haines Index** (1988; três variantes por altitude; Winkler et al. 2007, *IJWF* 16:139-152) — indicador de ar seco/instável | <https://research.fs.usda.gov/download/treesearch/45268.pdf> |
| **Keetch–Byram Drought Index (KBDI)** — balanço hídrico diário, 0–800 (Keetch & Byram 1968, Res. Pap. SE-38) | <https://www.drought.gov/data-maps-tools/keetch-byram-drought-index> |
| "Fire Danger Index — Finney": **NÃO VERIFICADO** (o verificável é Finney 2003, *IJWF* 12:167-174, modelagem de propagação) | <https://www.fs.usda.gov/rm/pubs/rmrs_gtr292/2003_finney.pdf> |
| "Capegrass Fire Danger Rating System (Hain)": **NÃO VERIFICADO** | — |

### 2.5 Adaptação ao Brasil / Amazônia — o que já existe

| Fato | Fonte |
| :--- | :--- |
| **Cavalcante, R.B.L. et al. (2021)** — *"Assessment of fire hazard weather indices in the eastern Amazon: a case study for different land uses"*, *Acta Amazonica* 51(4). DOI **10.1590/1809-4392202101172**. Avalia **7 índices** de perigo meteorológico em **Canaã dos Carajás (Pará)** | <https://acta.inpa.gov.br/fasciculos/51-4/PDF/AA-2021-0117.pdf> |
| **Forests 17(4):437 (2026)** — *"Danger of Vegetation Fires in the Cerrado-Amazon Transition Region"*: Ängstrom, FMA, FMA+, EVAP/P, P-EVAP, INMET + reanálise Copernicus, validação por *Skill Score* | <https://www.mdpi.com/1999-4907/17/4/437> |
| **NHESS 26:4257 (2026)** — projeta o FFDI (McArthur) no Brasil, entre—gungão: Austália, Brasil e EUA; transição "preparação → temporada" avança 12–32 d no Brasil a +2 °C | <https://nhess.copernicus.org/articles/26/4257/2026/nhess-26-4257-2026.html> |
| **IOP 10.1088/2752-5295/ae249a (2025)** — FWI na América do Sul: Sul do Brasil, Paraguai, norte da Argentina e Bolívia já excederam limiares de emersão | <https://iopscience.iop.org/article/10.1088/2752-5295/ae249a> |
| ⚠️ **Conclusão honesta:** existe **avaliação e projeção** de índices meteorológicos no Brasil e na Amazônia. **Não foi localizada** uma versão do FWI/FFDI **calibrada para a Amazônia tropical** usada operacionalmente. | idem |

### 2.6 O que a literatura de ML faz para incêndio na Amazônia

**Trabalhos com dados brasileiros/da Amazônia (verificados):**

| # | Referência | Região | O que faz | Observação |
| :--- | :--- | :--- | :--- | :--- |
| B1 | **Freitas, K.M.; Juvanhol, R.S.; Pinheiro, C.J.G.; Meneses, A.A.M. (2025)**. *"Prediction of forest fire susceptibility using machine learning tools in the Triunfo do Xingu Environmental Protection Area, Amazon, Brazil"*. *J. South American Earth Sciences* 153:105366. DOI **10.1016/j.jsames.2025.105366** | **BRASIL — APA Triunfo do Xingu (AM/PA)** | **RF + XGBoost + SHAP** sobre BDQueimadas, MapBiomas, CHIRPS, SRTM, MODIS | É **susceptibilidade** (estática), não ignição. Métricas: **não extraídas** (paywall) |
| B2 | **Cavalcante et al. (2021)**, *Acta Amazonica* 51(4), DOI 10.1590/1809-4392202101172 | **BRASIL — Pará (Canaã dos Carajás)** | 7 índices meteorológicos por classe de uso do solo | ver §2.5 |
| B3 | **Silva, J.L.G.; Capistrano, V.B.; Veiga, J.A.P.; Brito, A.L. (2023)**. *"Regional climate modeling in the Amazon basin to evaluate fire risk"*, *Acta Amazonica*. DOI 10.1590/1809-4392202201881 | **Bacia amazônica** | modelagem regional para avaliar risco | |
| B4 | **Forests 17(4):437 (2026)** | Cerrado-Amazônia | índices + Skill Score | ver §2.5 |
| B5 | **arXiv:2606.04170 (jun/2026)** — *"A Retrospective Benchmark of Spatiotemporal Covariates for Daily Active-Fire Detection in Cerrado Conservation Units"* (preprint) | **BRASIL — Cerrado, UCs** | LogReg/RF/XGBoost; **AUC-PR**, *recall* no limiar 0.5; **hold-out por AOI (unidade de conservação)**; **SHAP por AOI** | Declara explicitamente que **não há benchmark diário em escala de UC no Cerrado** e que B1 é o precedente brasileiro mais próximo |
| B6 | **Podschwit, H. et al. (2022)**. *"Reliability of cross-regional applications of global fire danger models: a Peruvian case study"*, *Fire Ecology* 18. DOI 10.1186/s42408-022-00150-7 | Peru / Amazônia | testa confiabilidade de modelos globais cross-regionais | **Alerta direto** para transferência de modelos treinados fora |
| B7 | **Jiao et al. (2023)**, *Geosci. Model Dev.* 16:869-884. DOI 10.5194/gmd-16-869-2023 | trópicos | ML **interpretável** para área queimada | |
| B8 | **Fodor & Conde (2023)**, arXiv:2307.04916 (CVPR MultiEarth Workshop); código <https://github.com/h2oai/cvpr-multiearth-deforestation-segmentation> | **AMAZÔNIA** | CNN multi-modal p/ área queimada e desmatamento | detecção, não risco |
| B9 | **Mohla, S. et al. (2020)**, IEEE SMC 2020. DOI 10.1109/SMC42975.2020.9283432 (arXiv:2009.04634) | **AMAZÔNIA** | U-Net p/ cicatrizes com rótulos ruidosos | rótulo fracamente supervisionado |
| B10 | **Marli, A. et al. (2020)**, ICCSA 2020, LNCS 12249. DOI 10.1007/978-3-030-58799-4_74 (arXiv:2011.01140) | **AMAZÔNIA** (MODIS) | redes temporais + Louvain | descritivo, não preditivo |
| B11 | **Das, S. et al. (2026)**, *Int. J. Wildland Fire* — <https://research.fs.usda.gov/download/treesearch/81355.pdf> | EUA | **LOFO (leave-one-fire-out)** na CV + **SHAP por incêndio**, dNBR/RdNBR, RF/XGBoost/LightGBM | modelo de referência para "CV por unidade de fogo + SHAP auditável" |
| B12 | **Berman et al. (2023)**, NASA NTRS 20220013847 — <https://ntrs.nasa.gov/api/citations/20220013847/downloads/Berman_et_al_REVISED3_clean.pdf> | EUA (método) | quantifica a **subestimação** de área queimada por detecção de satélite | **evidência quantitativa do viés de rótulo** |
| B13 | **Giglio, L.; Schroeder, W.; Justice, C.O. (2016)**, *Remote Sensing of Environment* 178:31-41 — <https://modis-fire.umd.edu/pubs.html> | global | base do BDQueimadas/FIRMS | resolve a detecção: resolução do pixel MIR, limiar de área efetiva, sub-detecção em floresta |

**Não localizados (NÃO VERIFICADO — não citar):** "González et al. (2021) Fire Prediction
Machine Learning (FPM)"; "Saul et al. (2022) LimeTree-Explain"; "FireGBM"; "Firen";
repositório "Pyre" (o `coreytingley/pyre` retorna 404 e a busca na API do GitHub não
retorna repositório correspondente).

**Métodos (verificados):**

| Método | Referência |
| :--- | :--- |
| SHAP | Lundberg, S.M.; Lee, S.-I. (2017). arXiv:1705.07874 — <https://doi.org/10.48550/arXiv.1705.07874> |
| Explicação local por árvore surrogate | Sokol, K.; Flach, P. (2020), *LIMEtree*. arXiv:2005.01427 |
| Block CV espacial/temporal | Roberts, D.R. et al. (2017), *Ecography* 40:913-929. DOI 10.1111/ecog.02881 |
| Revisão do campo | Jain, A. et al. (2020), *Environmental Reviews* 28(4):478-505. DOI 10.1139/er-2020-0019 |

**Métricas:** **AUC-PR** está em uso real no trabalho brasileiro (B5). **"precision@k"**,
**"recall@k"** e **"Brier score"** como *nomenclaturas reportadas na literatura amazônica*:
**NÃO VERIFICADO** — o observado é "recall at the 0.5 threshold" (B5) e Brier não foi
confirmado em nenhum dos itens acima.

### 2.7 Contraste com a Frente A do NGEO (PLANO §10) — reuso, adaptação, original

| Componente da frente A (§10) | **Reuso** (o que já existe e é reaproveitado) | **Adaptação** (o que precisa ser mudado) | **Original** (o que o NGEO propõe e não foi encontrado) |
| :--- | :--- | :--- | :--- |
| Rótulo (área queimada) | MapBiomas Fogo (30 m, Landsat, 1985–2025); MCD64A1 v6.1; dNBR Landsat C2 L2 | Não usar o **ponto de foco** como rótulo (viés de detecção — B13, B12); área queimada atrasa: atraso oficial **NÃO VERIFICADO**, observado em GEE: `MODIS/061/MCD64A1` com fim em **2026-08-01** em 21/10/2026 (≈ 2–3 meses) | Tratar o confundidor "fogo de manejo" como **limitação declarada** (já decidido, D-009) |
| Features | CHIRPS v2.0 (0,05°, diário), ERA5-Land (0,1°, horário), MOD11A1 (LST 1 km diário), MOD13A2 (NDVI/EVI 1 km 16 d) / MOD13Q1 (250 m 16 d), ESA WorldCover 10 m, MapBiomas uso do solo 30 m, WorldCover | "SAF/EDMI": **NÃO VERIFICADO** — nenhuma sigla oficial de índice de seca amazônico encontrada. Usar índices reais: **SPI/SPEI/scPDSI/MCWD** (JRC) e, no Brasil, **ANA "Monitor de Secas"** e **CEMADEN** | Distância a contratos de transição (pasto em pousio = capim seco = combustível) e a concessões, **justamente para as 29 UCs do IDEFLOR** |
|Modelo | XGBoost/LightGBM (padrão da literatura: B1, B5, B11) | Calibrar para a **Amazônia**, não para o Cerrado (B6 alerta para transferência cross-regional) | — |
| Validação | Block CV espacial (B17) + holdout temporal | **Hold-out por UC**, não por AOI equivalente (B5 usa AOI; B11 usa LOFO por incêndio) | Avaliar **cobertura por UC** (recall@k por UC) como métrica primária, não só global |
| Explicabilidade | SHAP (Lundberg & Lee 2017) | — | ⚠️ **Ver §6-f:** o "SHAP local por UC" **já foi feito** no Cerrado (B5, preprint jun/2026) e em **uma** UC amazônica (B1, Triunfo do Xingu) — **para susceptibilidade, não ignição**. A originalidade aqui é **parcial**, não total |
| Métricas | AUC-PR, Brier, calibração | — | `precision@k` como métrica de **produto** (o gestor pergunta "dos 10% de maior risco, quanto queimou?") — nomenclatura **NÃO VERIFICADA** na literatura amazônica |

---

## 3. Propagação / nowcast

### 3.1 FARSITE

| Fato | Fonte |
| :--- | :--- |
| Simulador 2D **determinístico** de crescimento sob terreno, combustível e clima heterogêneos; expansão vetorial de perímetros (método de Huygens), fogo de superfície, fogo de copa, *spotting*, aceleração por fonte pontual | <https://research.fs.usda.gov/treesearch/4617> · <https://research.fs.usda.gov/download/treesearch/27413.pdf> |
| Modelo: Rothermel (1972) com ajustes de Albini (1976); fogo de copa Van Wagner (1977, 1993) e Rothermel (1991) | <https://www.fs.usda.gov/rm/pubs/rmrs_rp004.pdf> |
| Entradas: `.LCP` (fuel model, slope, aspect, elevation, canopy cover), `.FMS` (umidade inicial), `.WTR`/`.WXS` (meteo), `.WND` (vento), `.FMD`, `.ATM` | <https://owfflammaphelp62.firenet.gov/FileTypes/ug3_Data_Requirements.htm> · <https://preview.weather.gov/media/wrh/online_publications/TAs/TA1006.pdf> |
| ⚠️ **Disponibilidade**: *"FARSITE4 is no longer supported or available for download; it is now integrated into FlamMap 6"* (Windows, USFS). Em 1998 era "free of charge". Software do governo dos EUA = domínio público (17 USC 105) | <https://research.fs.usda.gov/firelab/products/dataandtools/farsite> |
| Repositório oficial: **não existe**. Portes parciais não oficiais: <https://github.com/mbedward/farsite>, <https://github.com/Physis10/wildfire_model> (`rothermel.py`, `farsite.py` em Python) | — |

### 3.2 Rothermel e os fuel models

| Fato | Fonte |
| :--- | :--- |
| **Rothermel (1972)**, Res. Pap. INT-RP-115, DOI **10.2737/INT-RP-115** — `R = (I_B/I_B0)(1 + φ_w + φ_s)`: precisa **vento à altura da chama**, **declividade**, **umidade do combustível** e os parâmetros do *fuel model* | <https://research.fs.usda.gov/download/treesearch/32533.pdf> · <https://www.fs.usda.gov/rm/pubs/int_rp115.pdf> |
| **Scott & Burgan (2005)**, GTR-153, DOI **10.2737/RMRS-GTR-153** — 40 fuel models (13 de Albini + GR grass, SB slash, TL timber-litter, GS, TU, NB não queimável). Observação da própria fonte: a nova série *"does not correct for deficiencies in the surface fire model"* | <https://www.fs.usda.gov/rm/pubs_series/rmrs/gtr/rmrs_gtr153.pdf> |
| **Andrews (2018)**, RMRS-GTR-371 — detalhe de todos os parâmetros e incertezas (Fuel Bed Depth, SAV, umidade de extinção) | <https://research.fs.usda.gov/download/treesearch/55928.pdf> |

### 3.3 Implementações escalares / celulares

| Ferramenta | Linguagem / licença | O que faz | Python | Fonte |
| :--- | :--- | :--- | :--- | :--- |
| **pyretechnics** | Python, **EPL-2.0** | equações de superfície/copa/spotting, *burn cells* em grade, propagação ELMFIRE (level set euleriano) | ✅ | <https://github.com/pyregence/pyretechnics> |
| **firebehavioR** | R (CRAN) | Rothermel (1972) + início de fogo de copa (Van Wagner 1977) + taxa de copa (Rothermel 1991) + Scott & Reinhardt (2001) | ❌ | <https://search.r-project.org/CRAN/refmans/firebehavioR/html/rothermel.html> |
| **Rothermel** | R, **GPL-2** | ROS; 40 fuel models; propagação de incerteza por Monte Carlo | ❌ | <https://cran.r-project.org/web/packages/Rothermel/index.html> |
| **Cell2Fire** | R | simulador **celular** de crescimento, paralelismo, propagação elíptica por célula | ❌ | <https://github.com/cell2fire/Cell2Fire> · <https://www.nature.com/articles/s41598-025-05706-6> |
| **Behave 7** | Java (JAR), USFS + BSD-2 | modelo de **ponto** (ROS, spotting, scorch, mortalidade, umidade, WAF). *"It cannot model spatial fire behavior"* | ❌ | <https://github.com/firelab/behave-app> |
| **Pyre** (Corey Tingley) | — | ⚠️ **NÃO VERIFICADO — repo não localizado** (404 + busca na API do GitHub) | — | <https://api.github.com/search/repositories?q=pyre+fire+spread> |
| "FARSITE-lite", "sfire", "burnDAE", "SOTT" | — | ⚠️ **NÃO VERIFICADO** | — | — |

### 3.4 EFFIS e previsão de propagação

| Fato | Fonte |
| :--- | :--- |
| EFFIS usa **Canadian FWI** harmonicamente, com previsão ECMWF (~8 km, 1–9 dias) e Météo-France (~10 km, até 3 dias); desde 2019 inclui MARK-5, KBDI e NFDRS | <https://forest-fire.emergency.copernicus.eu/about-effis/technical-background/fire-danger-forecast> |
| Camadas/produtos: FWI, ISI, BUI, FFMC, DMC, DC, NFDRS (SC/ERC/BI/IC), **ROS**, FDI, KBDI; *Active Fires*; **Fuels (EFFIS Fuel Map)**; perimeters | <https://forest-fire.emergency.copernicus.eu/applications/data-and-services> |
| ⚠️ **"Fire spread forecast" de 24–48 h por incêndio no EFFIS: NÃO VERIFICADO.** A documentação consultada descreve perigo meteorológico, detecção de focos e perimeters — **não** previsão de propagação por incêndio | idem |

### 3.5 Estado da arte em nowcast

| Trabalho | O que é | Fonte |
| :--- | :--- | :--- |
| **FISC-Cerrado** (Oliveira et al., 2023) — UFMG + INPE | **O caso de referência brasileiro.** Simulação de propagação **3×/dia**; Cerrado a 25 ha (500 m) e **9 UCs a 0,04 ha (20 m)**; 65–89% de correspondência espacial; consome MODIS+Sentinel-2, clima e terreno; **em uso operacional pelas UCs** | <https://www.nature.com/articles/s41598-023-30560-9> (DOI 10.1038/s41598-023-30560-9) · <https://csr.ufmg.br/fipcerrado/en/> |
| **FireCast** (Radke, Hessler & Ellsworth, IJCAI 2019) | CNN sobre satélite+elevação+clima+perimeters; **supera o FARSITE** em acurácia/recall/F-score | <https://www.ijcai.org/proceedings/2019/0636.pdf> (DOI 10.24963/ijcai.2019/636) |
| **ConvLSTM / RCDNN** (Burge et al.) | Emulação do FARSITE com rede convolucional recorrente em passos de **15 min**, estável >24 h simulados (Jaccard 0,89–0,94) | <https://arxiv.org/abs/2012.06679> · <https://arxiv.org/abs/2210.16411> |
| **FireGraphNet** (2026) | GNN em grafos H3, crescimento de 12 h, vento nas arestas | <https://arxiv.org/pdf/2610.19191> |
| **CA estocástico bayesiano** (Grieshop & Wikle 2023) | autômato celular estocástico com incerteza e vizinhança dinâmica | <https://arxiv.org/pdf/2306.03214> |

### 3.6 Viabilidade no escopo do NGEO

**(a) Mapa de combustível — a dependência dura.**

| Fato | Fonte |
| :--- | :--- |
| **LANDFIRE** (30 m, fuels + topografia) cobre **apenas os EUA** | <https://www.landfire.gov/data> |
| O **EFFIS Fuel Map** cobre a Europa | <https://forest-fire.emergency.copernicus.eu/applications/data-and-services> |
| ⚠️ **Para a Amazônia não foi localizada fuel map padronizada de resolução operacional.** O próprio FISC-Cerrado precisou **construir** carga de combustível e umidade de vegetação a partir de MODIS/Sentinel-2 | <https://www.nature.com/articles/s41598-023-30560-9> |
| **Mas existe método publicado e implementação brasileira de mapa de combustível** | O **SIFAU** (Wetlands International + LASA/UFRJ + UFMS) publica **"Material Combustível (Franke et al. 2018), mensal, 100 m"**, gerado a partir de Landsat, "indica a biomassa superficial disponível para queima" | <https://alarmes.lasa.ufrj.br/sifau/> | ⚠️ a citação de Franke et al. (2018) é **do SIFAU**; o artigo **não foi lido** nesta sessão. **Reduz a estimativa de custo da frente B** |
| **Global Fire Atlas** (ORNL DAAC, DOI 10.3334/ORNLDAAC/1642): por incêndio individual, tamanho, duração, **velocidade e direção de propagação**, derivado de MCD64A1 — **alvo empírico de calibração**, não mapa de combustível | <https://www.earthdata.nasa.gov/data/catalog/ornl-cloud-cms-global-fire-atlas-1642-1> |

**(b) Por que sem fuel model local a simulação é frágil.**

| Fato | Fonte |
| :--- | :--- |
| Rothermel (1972) introduz "fuel models" **exatamente para evitar medir parâmetros de campo** | <https://www.fs.usda.gov/rm/pubs/int_rp115.pdf> |
| Scott & Burgan (2005): a escolha do fuel model é dependente do dossiê; a série nova **não corrige** as deficiências do modelo de superfície | <https://www.fs.usda.gov/rm/pubs_series/rmrs/gtr/rmrs_gtr153.pdf> |
| NOAA/NWS (TA1006), usando FARSITE: *"Creating an Initial Fuel Moisture (FMS) file was by far the most subjective exercise encountered during the study"* | <https://preview.weather.gov/media/wrh/online_publications/TAs/TA1006.pdf> |

**Conclusão de escopo (fundamentada nas fontes acima):**

- **Viável agora (F7 inicial):** nowcast de **curto alcance e baixa resolução** —
  perímetro por **acúmulo de focos** (vetorial) + vetor de deslocamento por
  **vento** (ERA5/GOES) → "o fogo está em X, o vento aponta para Y". Sem simulação
  física de propagação. Custo: baixo. Dependência: nenhuma nova.
- **Viável depois (F7 avançado):** propagação tipo Rothermel **em pontos e com
  simplificado de fuel model derivado de uso do solo** (MapBiomas/WorldCover) — com
  degradação explícita de confiança. Dependência: **construir** o mapa de combustível
  (é o que o FISC-Cerrado fez) + vento horário.
- **Não viável:** FARSITE operacional na Amazônia (sem distribuição, sem LCP, sem FMS)
  e GNN de propagação treinada na Amazônia (não verificada na literatura).

---

## 4. Datasets de entrada

| Dataset | Sensor | Resolução espacial | Temporal | Latência | Acesso | Licença | Fonte |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **FIRMS VIIRS NRT** | VIIRS | 375 m | diária (NRT) | < 3 h | API / Earthdata | Earthdata open sharing; atribuição LANCE | <https://www.earthdata.nasa.gov/data/tools/firms/faq> |
| **MCD64A1 v6.1** | MODIS | **500 m** | mensal | atraso **NÃO VERIFICADO**; observado: GEE com fim em 2026-08-01 em 21/10/2026 | LP DAAC | *"no restrictions on subsequent use, sale, or redistribution"* (uso comercial permitido) | <https://developers.google.com/earth-engine/datasets/catalog/MODIS_061_MCD64A1> · <https://catalog.data.gov/dataset/modis-terraaqua-direct-broadcast-burned-area-monthly-l3-global-500m-sin-grid-v061> |
| **MCD14DL** | MODIS Terra+Aqua | 1 km | NRT | — | FIRMS | — | ⚠️ **NÃO é LST**: é o produto de fogo ativo NRT do FIRMS (DOI MCD14DL.NRT.0061). <https://www.earthdata.nasa.gov/learn/find-data/near-real-time/firms/vj114imgtdlnrt> |
| **MOD11A1 / MYD11A1** | MODIS Terra/Aqua | 1 km | diária | **NÃO VERIFICADA** | LAADS DAAC | MODIS open | <https://ladsweb.modaps.eosdis.nasa.gov/missions-and-measurements/products/MOD11A1> |
| **MOD13** | MODIS | **MOD13Q1** 250 m 16 d · **MOD13A2** 1 km 16 d · **MOD13A3** mensal 1 km | 16 d | — | LP DAAC | MODIS open | <https://lpdaac.usgs.gov/documents/621/MOD13_User_Guide_V61.pdf> |
| **CHIRPS v2.0** | precipitação | **0,05°** (~5,5 km), faixa 50°S–50°N | **diária** (existe também mensal) | **NÃO VERIFICADA** | `data.chc.ucsb.edu`; GEE `UCSB-CHG/CHIRPS/DAILY` | *"public domain with all copyright waived"* | <https://www.chc.ucsb.edu/data/chirps> · <https://developers.google.com/earth-engine/datasets/catalog/UCSB-CHG_CHIRPS_DAILY> |
| **CHIRPS v3** | precipitação | 0,05°, 60°N–60°S, 1981→ | diária (`rnl` ERA5 / `sat` IMERG) | — | <https://www.chc.ucsb.edu/data/chirps3> | — | verificar qual versão usar |
| **ERA5-Land** | reanálise ECMWF | **0,1°** (nativa 9 km) | **horária**, jan/1950→ | diária | CDS (cadastro obrigatório) | **CC-BY**, DOI 10.24381/cds.e2161bac | <https://cds.climate.copernicus.eu/datasets/reanalysis-era5-land> |
| **ERA5** | reanálise ECMWF | 0,25° (31 km nativa) | horária, 137 níveis, jan/1940→ | — | CDS | CC-BY | <https://climate.copernicus.eu/climate-reanalysis> |
| ⚠️ **"SAF/EDMI"** | — | — | — | — | — | — | **NÃO VERIFICADO** — nenhuma sigla oficial de índice de seca amazônico encontrada. Em IPCC AR6, "SAF" = *Southern South America*. Índices amazônicos reais e confirmados: **SPI, SPEI, scPDSI, MCWD, RAI** (<https://joint-research-centre.ec.europa.eu/document/download/92dd4de6-6dbf-464b-b268-454b62bef995_en>) + **ANA "Monitor de Secas"** e **CEMADEN** |
| **ESA WorldCover** | Sentinel-1+2 | **10 m**, 11 classes, anos 2020 (v100) e 2021 (v200) | anual | — | `s3://esa-worldcover-s2` (eu-central-1); Terrascope | **CC BY 4.0**; DOI 10.5281/zenodo.7254221; atribuição: *"© ESA WorldCover project [year] / Contains modified Copernicus Sentinel data ([year]) processed by ESA WorldCover consortium"* | <https://esa-worldcover.org/en/data-access> |
| **MapBiomas** | Landsat | **30 m**, 1985–2025 (Coleção 11) | anual | — | GEE / plataforma | **NÃO VERIFICADA** | <https://plataforma.mapbiomas.org/> |
| **Sentinel-2 L2A** | MSI | 10 m (B02,B03,B04,B08), 20 m, 60 m | revisita **5 dias** no Equador | — | Copernicus Data Space (cadastro) | gratuito; *"© contains modified Copernicus Sentinel data (2016), processed by ESA, CC BY-SA 3.0 IGO"*; DOI 10.5270/S2_-znk9xsj | <https://dataspace.copernicus.eu/data-collections/copernicus-sentinel-missions/sentinel-2> |
| **Landsat C2 L2** | OLI/TIRS | **30 m** | — | *"typically available within 24 hours after a scene has been processed"*; Landsat 9 L2 em ~3 dias | USGS EarthExplorer | **no-cost open access policy** (desde 2008); crédito: *"Landsat Collection 2 Level-2 image courtesy of the U.S. Geological Survey."* | <https://www.usgs.gov/landsat-missions/landsat-collection-2-surface-reflectance> |
| **dNBR** | — | 30 m | — | — | derivado | ΔNBR = NBR pré − NBR pós; faixas de severidade em Key & Benson (2006) | <https://data.jrc.ec.europa.eu/dataset/022cdeed-159f-407d-be18-0dface69ef92> |
| **Copernicus DEM GLO-30** | TanDEM-X | **30 m** (DSM, não DTM) | 2011–2015 | — | Copernicus | *"available worldwide with a free license"*; atribuição obrigatória: *"© DLR e.V. 2010-2014 and © Airbus Defence and Space GmbH 2014-2018 provided under COPERNICUS by the European Union and ESA"* | <https://dataspace.copernicus.eu/explore-data/data-collections/copernicus-contributing-missions/collections-description/COP-DEM> |
| ⚠️ **Mudança de licença (risco real)** | — | — | — | — | — | **Desde 28/07/2026 o view service COP-DEM-GLO-30 foi restrito a categorias autorizadas** (exige registro CCM); alternativa: GLO-90 ou NASADEM | <https://dataspace.copernicus.eu/news/2026-7-17-copernicus-dem-30m-view-service-license-acceptance> |
| **ALOS AW3D30 / NASADEM / SRTM** | — | SRTM 30 m (1 arc-second), void-filled | — | SRTM "Timeliness 1 h" | EarthExplorer | Full and Open | <https://www.usgs.gov/landsat-missions/landsat-collection-2> · <https://demo-cis2.02pre.eea.europa.eu/data/383/> — ⚠️ "ALOS AW3D30 acessível como dataset": **NÃO VERIFICADO** (apenas citado como preenchimento do Copernicus DEM) |
| **WWLLN** (NASA derivado) | VLF + receptores UW | **0,05°** | **mensal** (thunder hours), 2013-01→ | — | GHRC DAAC, DOI 10.5067/WWLLN/DATA101 | US Government Work, **acesso público** | <https://www.earthdata.nasa.gov/data/catalog/ghrc-daac-wwllnmth-1> |
| ⚠️ **WWLLN bruto** | — | — | — | — | Universidade de Washington | *"Raw WWLLN data are proprietary and cost USD 600 per year of data"* | <https://essd.copernicus.org/preprints/essd-2021-89/essd-2021-89.pdf> |
| **NASA GLM** | GOES-R/GOES-S | geostacionário | horário | — | NASA Open Data Portal | — | <https://data.nasa.gov/dataset?tags=earth-science-atmospheric-electricity-atmosphere-lightning> |
| ⚠️ **"GLD" / "ELD"** | — | — | — | — | — | — | **NÃO VERIFICADO** como dataset. Existe **GLD360** (Vaisala, **comercial**). "European Lightning Dataset": **NÃO VERIFICADO** |

---

## 5. Sistemas de alerta já existentes (Brasil e Amazônia)

| Sistema | Instituição | O que entrega | Granularidade | Latência | Notifica? | Fonte |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **Programa Queimadas** (focos, AQ1km, Eventos de Fogo, Risco de Fogo) | INPE | focos, área queimada, eventos, FWI observado/previsto | ponto (375 m–4 km); estatística por município/UF/bioma; **BDQueimadas com recorte por UC** | 10 min (focos); horária (eventos); diária (risco) | Parcial (assinatura de e-mail para áreas de monitoramento — fonte de manual CBMGO 2017, **não verificada em página atual**) | <https://data.inpe.br/queimadas/portal/dados-abertos/> |
| **BDQueimadas / Situação Atual** | INPE | acervo 1998→, séries e comparativos | UF, município, bioma | diária | Não | <https://data.inpe.br/queimadas/portal/> |
| **Painel do Fogo + API OpenAPI 3.1** | **Censipam (Ministério da Defesa)** | eventos de fogo, focos, frente 24 h, "Índice de Prioridade para Acionamento", cruzamento com CAR, bases auxiliares | evento/foco; bacia/UC | ~30 min (baixa latência) | Não (ferramenta operacional para equipes) | <https://panorama.sipam.gov.br/painel-do-fogo/api/swagger> |
| **Sisfogo** | Censipam + ICMBio/IBAMA/CBM | registro de ocorrências de incêndio florestal | incidente | operacional | Registro, não alerta | <https://www.gov.br/censipam/pt-br/central-de-conteudos/noticias/seminario-painel-do-fogo-aborda-tecnologias-de-monitoramento-e-enfrentamento-das-queimadas-na-amazonia> |
| **Prevfogo / Ciman / Brigadas Federais** | IBAMA | monitoramento em períodos críticos, brigadas, fiscalização | nacional; UCs/TI/assentamentos | período crítico | Não | <https://www.gov.br/ibama/pt-br/assuntos/fiscalizacao-e-protecao-ambiental/manejo-integrado-do-fogo/prevfogo> |
| **PNMIF / COMIF, PMIF, PPCIF, Boletim do Fogo** | MMA | política nacional, planos, áreas prioritárias por UF, boletim semanal | UF/município/área | semanal | Não | <https://www.gov.br/mma/pt-br/composicao/secd/comite-nacional-de-manejo-integrado-do-fogo-comif/ResoluoCOMIFN2.pdf> |
| **Painel de Risco de Incêndio** (índice 1–5) | INMET | risco por município | municipal | diária | Não | <https://portal.inmet.gov.br/noticias/risco-de-inc%C3%AAndio-no-brasil-ser%C3%A1-monitorado-pelo-inmet-e-disponibilizado-aos-usu%C3%A1rios-em-seu-portal-e-aplicativo> |
| **Operação São Paulo Sem Fogo** (Fundação Florestal, LiDAR, drones, IA) | Governo do SP | alertas automáticos, Painel de Inteligência, planos municipais | UC estadual e município | por temporada | **Sim, internamente** (relatórios georreferenciados a PMA/Bombeiros/DC) | <https://www.gazetasp.com.br/cotidiano/sao-paulo-amplia-tecnologia-descobrir-onde-incendios-florestais-podem-avancar> · <https://semil.sp.gov.br/sma/sp-sem-fogo> |
| **Monitoramento de Focos** (relatórios) | SEMA-MT | focos, densidade, cicatriz por bioma/município | município/bioma | anual | Não | <https://www.sema.mt.gov.br/transparencia/index.php/documentos/583/Queimadas/6234/Relatorio-Focos-de-Calor-e-Cicatriz-de-Queimada2024.pdf> |
| **Panorama das Queimadas** | SEMA-AM | rankings, boletins | município/UF | semanal/mensal | Não | <https://www.sema.am.gov.br/wp-content/uploads/2024/05/PANORAMA_QUEIMADAS_E_DESMATAMENTO_24.04.2022.pdf> |
| **PEPIF** (Pará) | SEMAS/PA | programa estadual de prevenção e combate | UF | anual/temporada | Não | <https://www.gov.br/mma/pt-br/noticias/governo-federal-realiza-alinhamento-para-discutir-medidas-de-prevencao-e-combate-a-incendios-florestais> |
| **FISC-Cerrado** | UFMG + INPE | **previsão de propagação 3×/dia** | 500 m (Cerrado) / 20 m (9 UCs) | ~8 h | Não (painel web) | <https://www.nature.com/articles/s41598-023-30560-9> |
| **"Amazônia em Chamas"** | IPAM | notas técnicas analíticas | UF/município/bioma | mensal | Não | <https://ipam.org.br/bibliotecas/amazonia-em-chamas-a-qualidade-do-ar-em-2024-e-2025> |
| **ALARMES** | LASA / IGEO / UFRJ | Área Queimada (375 m, diário, prob. por pixel 0–1, área mín. detectável 14 ha, atraso ~1 dia) · Estatísticas por ROI · **Perigo de Fogo** (curto prazo 5 dias + sazonal 3 meses) · Dificuldade de Controle de Incêndios · SPEI · **Fogoteca** (registros de campo) · *Panorama Ignições Naturais* e *Probabilidade de Excedência* (em breve) · **alerta por e-mail para ROI** | ponto 375 m; ROI | diário | **Parcial** (e-mail por ROI) | <https://alarmes.lasa.ufrj.br/> · <https://alarmes.lasa.ufrj.br/faq/> |
| **SIFAU** | Wetlands International Brasil + LASA/UFRJ + PELD-NEFAU-UFMS | Sistema de Inteligência do Fogo em áreas úmbidas: ALARMES diário + previsão de perigo 6 dias + **material combustível (Franke et al. 2018, mensal, 100 m)** + LCLU MapBiomas; adotado por **decreto do MS** (9/04/2024) | Pantanal / MIF | diário | Não | <https://alarmes.lasa.ufrj.br/sifau/> |
| **Savana** (privado) | Savana Farms | **FIRMS + raio de proteção + WhatsApp/e-mail/app**, varredura a cada 15 min, com distância até a borda e direção do vento | ponto + raio (1/2/5/10 km) | ~15 min | **Sim** (comercial, R$ 49,90/imóvel/mês) | <https://savanaap.com.br/monitoramento-de-queimadas> |

**Detalhe institucional do próprio IDEFLOR-Bio** (relevante para o NGEO): as Diretrizes
Técnicas 2025 (1ª ed.) exigem, nas Unidades de Recuperação sob concessão, *"programa de
monitoramento e combate ao fogo"* com *"sistema de monitoramento e alerta de focos de
queimadas, com procedimento claro de acionamento da equipe de combate"* —
<https://ideflorbio.pa.gov.br/wp-content/uploads/2025/06/2025-Diretriz-Tecnica-para-Elaboracao-do-Plano-de-Gestao-de-Unidades-de-Recuperacao-sob-Concessao-%E2%80%93-1a-Edicao-1.pdf>.
Isto é **obrigação contratual já existente** — o NGEO não nasce para substituí-la, e
qualquer proposta sua precisa ser compatível com ela.

**NÃO VERIFICADO nesta apuração:** sistemas estaduais de **Rondônia** e **Amapá**;
"PROARMA/AM"; "PROMAT/PRODEAM" (MT); função de **ANEEL** em alerta de incêndio
(nenhuma); produto próprio de **CEMADEN** de alerta de incêndio; uso de **CAP** no
Brasil (meteorologia ou incêndio); estatística oficial do INPE desagregada por **UC
estadual** publicada como produto (plausível via BDQueimadas, **sem produto publicado
confirmado**); existência de qualquer app de alerta de incêndio **institucional** no
Brasil (os apps achados — "Fireguard: Queimadas", "Fire Alert", "Queimadas no Brasil" —
são privados e o primeiro declara explicitamente *"não é um sistema de alerta oficial"*).

**Dúvido relevante:** "**FireEye São Paulo**" **não existe** como sistema de alerta de
incêndio no Brasil — "FireEye" é empresa de cibersegurança. O sistema real do SP é a
Operação São Paulo Sem Fogo / Fundação Florestal.

**Três produtos que a primeira apuração (21/10/2026, manhã) não cobriu e que mudam o
quadro da diferenciação:** ALARMES (LASA/UFRJ), SIFAU e Savana (ver tabela acima).
Eles **não abafam a lacuna** (nenhum endereça à gerência da UC, nenhum cita a zona do
plano, nenhum tem SHAP local por UC), mas **ocupam definitivamente** o espaço "estatística
de fogo por ROI/UC" e "alerta por proximidade" — e o ALARMES já tem dois produtos *em breve*
próximos da frente A (*Panorama Ignições Naturais*, *Probabilidade de Excedência*).
Consequência registrada em `DECISIONS.md` D-016.

---

## 6. A lacuna: o que nenhum sistema faz e o que o NGEO faria

Verificação por ausência nos documentos lidos (§5). "NÃO VERIFICADO" = não encontrado,
não "provavelmente não existe".

| Lacuna proposta | O sistema faz? | Verificação |
| :--- | :--- | :--- |
| **Roteamento institucional por Gerência Regional** | **Não** — nenhum dos produtos auditados (INPE, Censipam, MMA, SEMA-AM/MT, FISC-Cerrado, INMET) endereça o evento à gerência que responde pela UC | ✅ **LACUNA SE SUSTENTA.** É a mais forte das quatro: é uma lacuna de **cadeia institucional**, não de algoritmo. É exatamente o D-007 |
| **Citação do zoneamento do plano de gestão no alerta** | **Não** — nenhuma menção a zona do plano de manejo como atributo do evento de fogo nos produtos auditados. A menção institucional a zoneamento no IDEFLOR é **obrigação contratual** (Diretrizes 2025), não produto de alerta | ✅ **LACUNA SE SUSTENTA** (com a ressalva de que 13 das 29 UCs ainda não têm zoneamento — issue #24) |
| **SHAP local auditável por UC** | **Parcialmente** — B5 (Cerrado, preprint jun/2026) tem hold-out **por AOI** e **SHAP por AOI**; B1 (Triunfo do Xingu, Amazônia) tem SHAP em **uma** UC — mas para **susceptibilidade**, não ignição, e sem horizonte temporal | ⚠️ **LACUNA PARCIAL E FRÁGIL.** A originalidade pretendida precisa ser requantificada: o que é novo é (a) **ignição** com horizonte de dias, (b) **risco por UC do IDEFLOR**, (c) **SHAP local no alerta** (não só no paper). Não é "SHAP por UC", que já existe |
| **Uso offline em campo** | **Não** — nenhum produto oficial auditado oferece pacote offline; as ferramentas são web/API | ⚠️ **NÃO É LACUNA DE DOMÍNIO.** É decisão de produto/engineering do NGEO (issue #17) e, como tal, não sustenta uma alegação de.originalidade científica |

**Veredito (reapurado em 21/10/2026 com ALARMES/SIFAU/Savana):** a lacuna do NGEO **se
sustenta em 2 de 4** — e são as duas que são estruturalmente suas (roteamento +
zoneamento). Nenhum dos três produtos novos (ALARMES, SIFAU, Savana) endereça o evento à
gerência da UC, cita a zona do plano de gestão, ou entrega SHAP local por UC dentro de um
alerta operacional. As outras duas são **parcial** (SHAP) e
**de produto** (offline). Isso é dito aqui para que o README e o paper não afirmem o que
não se sustenta: a originalidade do NGEO está em **conectar dado de satélite a uma
cadeia institucional específica**, não em inventar método de ML.

**Segunda leitura da lacuna, mais forte:** nenhum dos sistemas auditados entrega
**fato de alerta geospatial auditável por UC**. Os produtos entregam estatística
(contagens, risco por município) e perimeters; **não** entregam um registro por UC do
tipo "nesta UC, neste horário, estes focos, estes sensores concordaram, esta
incerteza posicional, esta zona do plano". Isso é o **objeto** do NGEO e é verificável
como diferente de tudo acima.

---

## 7. COLETA REAL — schema observado (não documentado)

**Chamada única, 21/10/2026**, feita por `scripts/probe_firms.py`:

```
GET https://firms.modaps.eosdis.nasa.gov/api/area/csv/<MAP_KEY>/VIIRS_NOAA20_NRT/-58.896,-9.842,-46.063,2.591/1/2026-10-19
```

- `MAP_KEY`: gratuita, obtida em <https://firms.modaps.eosdis.nasa.gov/api/map_key/>
  (cadastro por e-mail; a chave viaja no *path* da URL — nunca em header, nunca em log).
- `bbox`: estado do Pará, derivado da API de malhas do IBGE
  (`https://servicodados.ibge.gov.br/api/v3/malhas/estados/15?formato=application/vnd.geo+json&qualidade=minima&intrarregiao=municipio`,
  144 municípios, bbox calculada em 21/10/2026: lon −58.8956…−46.0634, lat −9.8412…2.5910).
  Convergência: a bbox das 29 UCs do IDEFLOR (`data/shapes_de_todas_as_unidades_com_gerencia.geojson`)
  é **−58.8955…−47.2850 / −9.3110…2.0296** — cabe dentro da do estado.
- Artefatos: `data/probes/firms_VIIRS_NOAA20_NRT_2026-10-19.csv` (68.459 bytes, **gitignored**)
  e `data/probes/firms_VIIRS_NOAA20_NRT_2026-10-19_schema.json`.
- Recorte de 6 linhas em `tests/fixtures/firms_viirs_noaa20_nrt_2026-10-19.csv` (versionado, é a fixture do teste).

### 7.1 Resultado

| Métrica | Valor observado |
| :--- | :--- |
| Registros | **811** |
| Colunas | **14**, nesta ordem exata: `latitude, longitude, bright_ti4, scan, track, acq_date, acq_time, satellite, instrument, confidence, version, bright_ti5, frp, daynight` |
| `latitude` | −9.63172 … 2.48175 · decimais observados: **3, 4, 5** (variável) |
| `longitude` | −58.8941 … −46.0929 · decimais observados: **2, 3, 4, 5** (variável) |
| `acq_date` | `2026-10-19` (único valor; formato `YYYY-MM-DD`) |
| `acq_time` | `353`, `355`, `533`, `536`, `1633`, `1635`… — **HHMM sem zero à esquerda** (`353` = 03:53 UTC) |
| `satellite` | `N20` (único valor) — **código curto**, não o nome do satélite |
| `instrument` | `VIIRS` |
| `confidence` | `h` / `n` / `l` — **letra**, não a palavra (`n`: 645 · `l`: 151 · `h`: 15) |
| `version` | `2.0NRT` |
| `bright_ti4` | 207.93 … 367.00 K (sem negativos) |
| `bright_ti5` | 243.02 … 320.22 K (sem negativos) |
| `frp` | 0.62 … 289.58 MW (sem negativos, sem zeros) |
| `daynight` | `D`: 675 · `N`: 136 |
| `scan` | 0.32 … 0.79 · `track` 0.37 … 0.78 (ângulos de varredura do sensor) |

### 7.2 Divergências entre a documentação e o observado (o que o adapter tem de saber)

| Expectativa comum | Observado | Consequência para o adapter |
| :--- | :--- | :--- |
| Campo "coordinate" combinado | ❌ **não existe** — são `latitude` e `longitude`, colunas separadas | §5 do PLANO já previa `lat`/`lon`; **confirmado** |
| `acquisition_time` com hora | ❌ é `acq_time`, **inteiro HHMM sem padding** (`353`) | parsear como inteiro e recompor `03:53`; **timezone UTC** |
| `confidence` ∈ {low, nominal, high} | ❌ é `l`/`n`/`h` | mapear `l→low, n→nominal, h→high` |
| `satellite` = "NOAA-20" | ❌ é `N20` | mapear por código; manter o nome completo em `fonte`/`sensor` |
| `brightness` / `bright_t31` | ❌ **não existem no VIIRS** — são `bright_ti4` (3.9 µm) e `bright_ti5` (11.45 µm) | o schema canônico precisa de **dois** campos de temperatura de brilho, ou de um `raw` fiel |
| `type`, `country`, `state`, `icao_id` | ❌ **não existem na resposta de `/api/area`** | `country_id` só aparece em `/api/country`; não contar com país/estado no payload |
| `frp` ausente às vezes | ✅ presente, mas **em W/M no payload da API** (o nome `frp` do FIRMS é em MW) | converter para a unidade canônica antes de gravar |
| precisão de coordenada "constante" | ❌ variável (2–5 decimais) | gravar `lat`/`lon` como `double precision` + `raio_pixel_m`; **nunca** apresentar como GPS |

**Regra de ouro que a coleta real confirma:** a coordenada do FIRMS é o **centro do
pixel**. O `scan`/`track` mostram que o pixel varia ao longo da swath. Logo
`raio_pixel_m` (375 m para VIIRS) é **obrigatório** em todo registro, e a interface
tem de mostrar o círculo de incerteza (AGENTS, regra de domínio).

### 7.3 O que a coleta real **não** provou

- Não provou a latência real ponta a ponta (UTC da aquisição → disponibilidade).
- Não provou o comportamento com **MODIS** (schema diferente: `brightness`/`bright_t31` —
  a **estrutura** está documentada, a **observação** não).
- Não provou GOES (`GOES_NRT` não é SOURCE do `/api/area`; o caminho é o produto NOAA
  `ABI-L2-FDC` no bucket `noaa-goes16`).
- Não provou INPE (endpoint público de CSV a confirmar).
- Não provou a **chave** do INPE (`INPE_API_KEY` do `.env.example` **não tem**
  correspondente no INPE apurado — os dados são abertos, sem autenticação).

---

## 8. Riscos

| # | Risco | Evidência | Mitigação |
| :--- | :--- | :--- | :--- |
| **RK1** | **Fonte fora do ar / degradada.** O FIRMS é a espinha do alerta. NRT é *best-effort* ("within 3 hours … on a best-effort basis") | <https://www.earthdata.nasa.gov/data/tools/firms/faq> | D-004 já exige multi-fonte; INPE como fallback **independente** (o INPE também usa FIRMS no fundo, mas tem GOES/MetOp/Meteosat próprios — a independência é **parcial**, não total) |
| **RK2** | **Mudança de termos de uso — já aconteceu.** (a) Copernicus DEM GLO-30 passou a exigir registro a partir de **28/07/2026**; (b) o `version` do FIRMS já mudou (`2.0NRT`); (c) a modalidade de dado do FIRMS já mudou (GOES-16 → GOES-19 em 07/04/2025, enquanto o INPE ainda rotula "GOES-16 BR") | <https://dataspace.copernicus.eu/news/2026-7-17-copernicus-dem-30m-view-service-license-acceptance> · <https://developers.google.com/earth-engine/datasets/catalog/NOAA_GOES_16_FDCF> | "pin de versão" por dataset no catálogo de proveniência (`fonte`, `satelite`, `sensor`, `versao_produto`); data de validade no `model_card` (D-006) |
| **RK3** | **Atribuição/licença.** FIRMS pede atribuição LANCE; WorldCover é CC BY 4.0 com atribuição obrigatória; Copernicus DEM tem texto de crédito obrigatório; MapBiomas tem licença **NÃO VERIFICADA**; WWLLN **bruto** custa USD 600/ano | ver §4 | Issue **#07** (atribuição por fonte) + §5.9 do PLANO (tabela de proveniência) |
| **RK4** | **Fonte única como ponto de falha.** Se o FIRMS cair, o INPE (que tem FIRMS no fundo) cai junto — **não são independentes** | <https://data.jrc.ec.europa.eu/dataset/e9d803fe-4426-4a45-9e6f-dd472de5c5f4> (EFFIS usa FIRMS) | Ter **um terceiro** caminho sem FIRMS no fundo: **NOAA ABI L2 FDC** (bucket público, 10 min) e **INPE** (que também processa GOES/MetOp/Meteosat próprios). Registrar a dependência real no `DECISIONS.md` (D-012) |
| **RK5** | **Chave única e sigilo.** A MAP_KEY do FIRMS é um único segredo, limitando 5000 transações/10 min. A dependência de repositório externo tipo `coreytingley/pyre` não se aplica aqui — mas a **chave em si** é ponto de falha único. Além disso, a chave foi emitida para um **e-mail temporário** (§9) | <https://firms.modaps.eosdis.nasa.gov/api/map_key/> | Reemitir sob e-mail institucional (issue #13) e guardar em `secrets/`, não em `.env` |
| **RK6** | **Latência vs. promessa.** URT/RT são **só EUA/Canadá**. Para o Pará, o piso real é **< 3 h (NRT)** | <https://www.earthdata.nasa.gov/data/tools/firms/faq> | D-008 (≤ 1 h) **precisa ser revisto**: 1 h é defensável só se GOES-16/19 (10 min) entrar como fonte primária de recência, com FIRMS/VIIRS como confirmação |
| **RK7** | **Viés de rótulo.** Ponto de foco como rótulo herda viés de detecção; área queimada atrasa | B12, B13 | Frente A já está correta no desenho (PLANO §10); falta **declarar** o atraso real (NÃO VERIFICADO; observado ~2–3 meses no GEE) |
| **RK8** | **Chuva em região úmida.** Chuva apaga o risco meteorológico; o FWI/FFDI foi calibrado para eucalipto e **já foi desacreditado** como base de rating na Austrália | <https://researchdata.edu.au/nbic-acs-stage-exceedance-probabilities/3952262> | Não usar FWI como feature "de risco" sem recalibração; tratar como baseline comparativo (D-013) |
| **RK9** | **Plano de gestão ausente em 13 das 29 UCs** | issue #24 | Alerta segue emitido **sem** zona, com limitação explícita (D-009/D-010) |

---

## 9. Registro da coleta — o que foi feito, com o que e o que ficou pendente

| Item | Resultado |
| :--- | :--- |
| MAP_KEY do FIRMS | ✅ **Obtida** (21/10/2026) em <https://firms.modaps.eosdis.nasa.gov/api/map_key/>. Cadastro por e-mail; a chave é enviada por e-mail e **não há auto-serviço**. Foi usada uma caixa de e-mail descartável — **pendência**: reemitir sob e-mail institucional (issue #13) |
| Chamada real | ✅ **Uma** chamada a `/api/area/csv/.../VIIRS_NOAA20_NRT/<bbox Pará>/1/2026-10-19` → **811 registros**, payload e relatório gravados em `data/probes/` (gitignored) |
| Probe versionado | ✅ `scripts/probe_firms.py` (stdlib, sem dependência externa) |
| Teste | ✅ `tests/test_probe_firms.py` — **sem rede**, com a fixture gravada da resposta real |
| Chave gravada | `.env` (gitignored) — `FIRMS_API_KEY`. **Não** está no git |
| INPE | ⚠️ **NÃO COLETADO**: nenhuma chamada foi feita ao INPE nesta sessão. Endpoint público de CSV a confirmar na F2 (issue #13) |
| GOES-16 | ⚠️ **NÃO COLETADO**: o caminho FIRMS para GOES (`GOES_NRT`) não é SOURCE do `/api/area`. O caminho a testar é o produto NOAA `ABI-L2-FDC` no bucket `noaa-goes16` |
| MODIS | ⚠️ **NÃO COLETADO**: o schema do MODIS difere (`brightness`/`bright_t31`) e precisa de uma segunda chamada real na F2 para fixar o mapeamento |

---

## 10. Índice de fontes (URL + data de acesso 21/10/2026)

<details>
<summary>Ver a lista completa</summary>

**FIRMS / NASA:** <https://firms.modaps.eosdis.nasa.gov/api/area> ·
<https://firms.modaps.eosdis.nasa.gov/api/map_key/> ·
<https://firms.modaps.eosdis.nasa.gov/content/academy/data_api/firms_api_use.html> ·
<https://www.earthdata.nasa.gov/data/tools/firms/faq> ·
<https://www.earthdata.nasa.gov/learn/find-data/near-real-time/firms/vj114imgtdlnrt> ·
<https://www.earthdata.nasa.gov/data/projects/lance>

**INPE:** <https://data.inpe.br/queimadas/> · <https://data.inpe.br/queimadas/dados-abertos/> ·
<https://data.inpe.br/queimadas/bdqueimadas/> · <https://data.inpe.br/queimadas/evento-fogo/> ·
<https://data.inpe.br/queimadas/portal/pages/secao_relatorio/integrado/index.html> ·
<https://data.inpe.br/queimadas/portal/dados-abertos/> ·
<https://www.gov.br/inpe/pt-br/assuntos/ultimas-noticias/boletim-infoqueima-apresenta-panorama-das-queimadas-e-do-risco-de-fogo-no-brasil-em-junho-de-2026>

**MapBiomas:** <https://alerta.mapbiomas.org/> · <https://brasil.mapbiomas.org/en/mapbiomas-fogo> ·
<https://brasil.mapbiomas.org/wp-content/uploads/sites/4/2026/05/ATBD-MapBiomas-Fogo-Colecao-5.pdf> ·
<https://plataforma.mapbiomas.org/>

**NOAA / GOES:** <https://catalog.data.gov/dataset/noaa-goes-r-series-advanced-baseline-imager-abi-level-2-fire-hot-spot-characterization-fdc> ·
<https://www.ncei.noaa.gov/access/metadata/landing-page/bin/iso?id=gov.noaa.ncdc%3AC01520> ·
<https://www.star.nesdis.noaa.gov/atmospheric-composition-training/documents/G16_ABI_FDC_ReadMe.pdf> ·
<https://developers.google.com/earth-engine/datasets/catalog/NOAA_GOES_16_FDCF>

**GFAS:** <https://confluence.ecmwf.int/spaces/CKB/pages/601301528/CAMS%2Bglobal%2Bbiomass%2Bburning%2Bemissions%2Bbased%2Bon%2Bfire%2Bradiative%2Bpower%2BGFAS%2Bdata%2Bdocumentation>

**EFFIS:** <https://effis.jrc.ec.europa.eu/> · <https://forest-fire.emergency.copernicus.eu/> ·
<https://forest-fire.emergency.copernicus.eu/about-effis/technical-background/fire-danger-forecast> ·
<https://data.jrc.ec.europa.eu/dataset/e9d803fe-4426-4a45-9e6f-dd472de5c5f4> ·
<https://data.jrc.ec.europa.eu/dataset/022cdeed-159f-407d-be18-0dface69ef92>

**Modelos de risco:** <https://data.csiro.au/collection/csiro:72827> ·
<https://www.bom.gov.au/resources/learn-and-explore/fire-weather-knowledge-centre/fire-weather-services> ·
<https://www.afac.com.au/AFDRS> · <https://natural-resources.canada.ca/forests-forestry/wildland-fires/canadian-forest-fire-danger-rating-system> ·
<https://cwfis.cfs.nrcan.gc.ca/background/summary/fwi> ·
<https://www.itu.int/ITU-T/recommendations/rec.aspx?rec=12150> ·
<https://www.itu.int/ITU-T/recommendations/rec.aspx?id=13914> ·
<https://docs.oasis-open.org/emergency/cap/v1.2/pr02/CAP-v1.2-PR02.pdf> ·
<https://acta.inpa.gov.br/fasciculos/51-4/PDF/AA-2021-0117.pdf> ·
<https://www.mdpi.com/1999-4907/17/4/437> · <https://nhess.copernicus.org/articles/26/4257/2026/nhess-26-4257-2026.html> ·
<https://iopscience.iop.org/article/10.1088/2752-5295/ae249a>

**Literatura ML:** <https://doi.org/10.1016/j.jsames.2025.105366> ·
<https://www.mdpi.com/1999-4907/17/4/437> · <https://arxiv.org/pdf/2606.04170> ·
<https://doi.org/10.1186/s42408-022-00150-7> · <https://doi.org/10.5194/gmd-16-869-2023> ·
<https://arxiv.org/abs/2307.04916> · <https://doi.org/10.1109/SMC42975.2020.9283432> ·
<https://doi.org/10.1007/978-3-030-58799-4_74> · <https://research.fs.usda.gov/download/treesearch/81355.pdf> ·
<https://ntrs.nasa.gov/api/citations/20220013847/downloads/Berman_et_al_REVISED3_clean.pdf> ·
<https://modis-fire.umd.edu/pubs.html> · <https://doi.org/10.48550/arXiv.1705.07874> ·
<https://doi.org/10.48550/arXiv.2005.01427> · <https://doi.org/10.1111/ecog.02881> ·
<https://doi.org/10.1139/er-2020-0019>

**Propagação:** <https://research.fs.usda.gov/treesearch/4617> ·
<https://research.fs.usda.gov/firelab/products/dataandtools/farsite> ·
<https://research.fs.usda.gov/download/treesearch/32533.pdf> ·
<https://www.fs.usda.gov/rm/pubs_series/rmrs/gtr/rmrs_gtr153.pdf> ·
<https://research.fs.usda.gov/download/treesearch/55928.pdf> ·
<https://preview.weather.gov/media/wrh/online_publications/TAs/TA1006.pdf> ·
<https://github.com/pyregence/pyretechnics> · <https://cran.r-project.org/web/packages/Rothermel/index.html> ·
<https://search.r-project.org/CRAN/refmans/firebehavioR/html/rothermel.html> ·
<https://github.com/cell2fire/Cell2Fire> · <https://github.com/firelab/behave-app> ·
<https://www.nature.com/articles/s41598-023-30560-9> · <https://csr.ufmg.br/fipcerrado/en/> ·
<https://www.ijcai.org/proceedings/2019/0636.pdf> · <https://arxiv.org/abs/2012.06679> ·
<https://arxiv.org/abs/2210.16411> · <https://arxiv.org/pdf/2610.19191> ·
<https://arxiv.org/pdf/2306.03214> · <https://www.landfire.gov/data> ·
<https://www.earthdata.nasa.gov/data/catalog/ornl-cloud-cms-global-fire-atlas-1642-1>

**Datasets:** <https://developers.google.com/earth-engine/datasets/catalog/MODIS_061_MCD64A1> ·
<https://ladsweb.modaps.eosdis.nasa.gov/missions-and-measurements/products/MOD11A1> ·
<https://lpdaac.usgs.gov/documents/621/MOD13_User_Guide_V61.pdf> ·
<https://www.chc.ucsb.edu/data/chirps> · <https://www.chc.ucsb.edu/data/chirps3> ·
<https://cds.climate.copernicus.eu/datasets/reanalysis-era5-land> ·
<https://cds.climate.copernicus.eu/datasets/reanalysis-era5-complete> ·
<https://esa-worldcover.org/en/data-access> ·
<https://dataspace.copernicus.eu/data-collections/copernicus-sentinel-missions/sentinel-2> ·
<https://www.usgs.gov/landsat-missions/landsat-collection-2-surface-reflectance> ·
<https://dataspace.copernicus.eu/explore-data/data-collections/copernicus-contributing-missions/collections-description/COP-DEM> ·
<https://dataspace.copernicus.eu/news/2026-7-17-copernicus-dem-30m-view-service-license-acceptance> ·
<https://www.earthdata.nasa.gov/data/catalog/ghrc-daac-wwllnmth-1> ·
<https://essd.copernicus.org/preprints/essd-2021-89/essd-2021-89.pdf>

**Sistemas no Brasil (complemento):** <https://alarmes.lasa.ufrj.br/> · <https://alarmes.lasa.ufrj.br/faq/> · <https://alarmes.lasa.ufrj.br/sifau/> · <https://savanaap.com.br/monitoramento-de-queimadas> · <https://brasil.mapbiomas.org/downloads/assets-no-google-earth-engine/> · <https://panorama.sipam.gov.br/painel-do-fogo/api/swagger> ·
<https://www.gov.br/censipam/pt-br/central-de-conteudos/noticias/o-painel-do-fogo-ja-esta-disponivel> ·
<https://www.gov.br/ibama/pt-br/assuntos/fiscalizacao-e-protecao-ambiental/manejo-integrado-do-fogo/prevfogo> ·
<https://www.gov.br/mma/pt-br/composicao/secd/comite-nacional-de-manejo-integrado-do-fogo-comif/ResoluoCOMIFN2.pdf> ·
<https://portal.inmet.gov.br/noticias/risco-de-inc%C3%AAndio-no-brasil-ser%C3%A1-monitorado-pelo-inmet-e-disponibilizado-aos-usu%C3%A1rios-em-seu-portal-e-aplicativo> ·
<https://semil.sp.gov.br/sma/sp-sem-fogo> · <https://www.sema.mt.gov.br/transparencia/index.php/documentos/583/Queimadas/6234/Relatorio-Focos-de-Calor-e-Cicatriz-de-Queimada2024.pdf> ·
<https://www.sema.am.gov.br/wp-content/uploads/2024/05/PANORAMA_QUEIMADAS_E_DESMATAMENTO_24.04.2022.pdf> ·
<https://ipam.org.br/bibliotecas/amazonia-em-chamas-a-qualidade-do-ar-em-2024-e-2025> ·
<https://ideflorbio.pa.gov.br/wp-content/uploads/2025/06/2025-Diretriz-Tecnica-para-Elaboracao-do-Plano-de-Gestao-de-Unidades-de-Recuperacao-sob-Concessao-%E2%80%93-1a-Edicao-1.pdf>

**Geometria de referência (IBGE, para o bbox do Pará):**
<https://servicodados.ibge.gov.br/api/v3/malhas/estados/15?formato=application/vnd.geo+json&qualidade=minima&intrarregiao=municipio>

</details>

---

## 11. Correções de premissa que este documento deixa para o resto do repo

| Premissa antiga | Correção | Onde corrigir |
| :--- | :--- | :--- |
| `MONITORQUEIMADAS` é a fonte do INPE | O INPE mantém o **Programa Queimadas / BDQueimadas**, aberto, sem chave | DECISIONS D-012; PLANO §6 |
| `MapBiomas Alerta e Fogo` como fonte de detecção | Alerta = **desmatamento**; Fogo = área queimada **anual/mensal** | DECISIONS D-012 |
| `MCD14DL` como LST | MCD14DL = fogo ativo MODIS NRT; LST = **MOD11A1** | PLANO §10 |
| `GOES16_ABI` como fonte FIRMS | O SOURCE do FIRMS não lista GOES; o caminho é NOAA `ABI-L2-FDC` | DECISIONS D-012 |
| `acquisition_date`/`acquisition_time`/`confidence`/`FRP` como nomes de campo | São `acq_date`/`acq_time`/`confidence` (letra)/`frp` | PLANO §5.1 (canonical) |
| Latência ≤ 1 h para o Pará (D-008) | URT/RT são **só EUA/Canadá**; piso real NRT < 3 h; ≤ 1 h só com GOES (10 min) | **D-008 precisa de revisão** — ver `DECISIONS.md` |
| "SAF/EDMI" como índice de seca | Sigla **não verificada**; usar SPI/SPEI/scPDSI/MCWD + ANA/CEMADEN | PLANO §10 |
| ITU-R BT.839 como padrão de alerta | **Não localizada**; o padrão real é **CAP (ITU-T X.1303 / OASIS v1.2)** | DECISIONS D-014 |
| "SHAP local auditável por UC" como originalidade | Já existe no Cerrado (arXiv:2606.04170) e em uma UC amazônica (Triunfo do Xingu) | Este doc, §6-f |
| "Alerta de fogo" como produto do MapBiomas | MapBiomas **Alerta** = desmatamento; o de fogo é **Fire Collection 5/5.1** (anual/mensal, Landsat 30 m) | Este doc, §1.3 |
| "Existe produto de risco no Brasil" | Existe **perigo meteorológico** (INPE, ALARMES) — condicional à ignição. **Risco de ignição por UC**: não verificado | Este doc, §2.5, §5 |
