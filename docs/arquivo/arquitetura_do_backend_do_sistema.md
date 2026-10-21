> Documento HISTORICO (arquivado em 21/10/2026). Substituido por `PLANO_ARQUITETURA.md` na raiz.
> Decisoes que mudaram: RN01 (risco diario) saiu do MVP -> fase F6; RN06 (paywall) descartado;
> maquina de estados de alerta descartada -> ver DECISIONS.md D-003; frontend agora e MapLibre -> D-001.
# Documento de Arquitetura e Requisitos: Sistema de Monitoramento e PrevisÃ£o de Risco de IncÃªndio em UCs

## 1. Escopo e Objetivo
Desenvolvimento de uma plataforma WebGIS preditiva para monitoramento (Near Real-Time) e previsÃ£o de incÃªndios florestais nas Unidades de ConservaÃ§Ã£o (UCs) do ParÃ¡. O sistema foca em alta resoluÃ§Ã£o espacial, baixa latÃªncia e usabilidade tÃ¡tica para gestores ambientais, visando tanto a aplicaÃ§Ã£o em campo quanto a publicaÃ§Ã£o de artigos cientÃ­ficos de alto impacto.

## 2. Stack TecnolÃ³gica
*   **Backend / API:** FastAPI (Python 3.12)
*   **Processamento AssÃ­ncrono:** Celery + Redis (Message Broker) + WebSockets
*   **Motor Geoespacial:** Google Earth Engine (GEE Python API)
*   **Banco de Dados:** PostgreSQL + PostGIS
*   **Machine Learning:** Scikit-Learn / XGBoost
*   **Frontend WebGIS:** Framework JS (Vue.js / React) + MapLibre GL JS
*   **Infraestrutura:** Docker, configuraÃ§Ã£o via `.env` (credenciais GEE via JSON)

## 3. Regras de NegÃ³cio (RN)

*   **RN01 - Abordagem Preditiva:** Calcular e armazenar diariamente a probabilidade de igniÃ§Ã£o (0-100%) baseando-se em clima histÃ³rico, estresse hÃ­drico e pressÃ£o antrÃ³pica.
*   **RN02 - LatÃªncia NRT:** Focos de calor (GOES-16 e VIIRS) atualizados a cada 30-180 minutos.
*   **RN03 - Gatilhos (dNBR):** CÃ¡lculo de cicatrizes de fogo processado sob demanda (manual via usuÃ¡rio) ou automÃ¡tico se densidade de focos atingir limite crÃ­tico.
*   **RN04 - Processamento AssÃ­ncrono:** Nenhuma requisiÃ§Ã£o pesada ao GEE pode travar o backend. Tudo Ã© enviado para o Celery.
*   **RN05 - Recorte Espacial (Clipping):** Processamento estritamente restrito aos polÃ­gonos das UCs e zonas de amortecimento.
*   **RN06 - Paywall CientÃ­fico (Lead Gen):** O download de dados brutos exige preenchimento de formulÃ¡rio (Nome, Email, InstituiÃ§Ã£o) para rastreio e mÃ©tricas de uso do sistema.

## 4. Requisitos Funcionais de Backend (RF)

*   **RF01 - IngestÃ£o NRT (Worker):** Tarefa Celery rodando a cada 1h extraindo dados do GOES-16 e NASA FIRMS, cruzando espacialmente (PostGIS) com as UCs e salvando no banco.
*   **RF02 - Modelo de Risco (Worker):** Tarefa Celery rodando de madrugada consumindo variÃ¡veis diÃ¡rias (ERA5, LST, NDWI) do GEE, aplicando o modelo XGBoost e gerando raster/probabilidade diÃ¡ria.
*   **RF03 - CÃ¡lculo de Cicatriz (Task):** Endpoint sob demanda que calcula o dNBR via Sentinel-2 no GEE, vetoriza a Ã¡rea queimada e salva as geometrias resultantes.
*   **RF04 - Endpoints RESTful:**
    *   `/api/ucs`: Geometrias base.
    *   `/api/focos`: Filtros temporais e espaciais de focos ativos.
    *   `/api/risco`: Time-series e mapas de calor preditivos.
    *   `/api/tarefas`: GestÃ£o e status de processamentos paralelos.
*   **RF05 - Telemetria:** Registro de mÃ©tricas de uso de endpoints e logs de downloads.

## 5. Requisitos de ExperiÃªncia do UsuÃ¡rio (UX/UI) e Frontend

*   **RF06 - Dual-Face System (Scrollytelling vs. TÃ¡tico):**
    *   *PÃ¡gina PÃºblica (`/`):* Landing page com Scrollytelling interativo no mapa, voltada para comunicaÃ§Ã£o cientÃ­fica, explicando o modelo preditivo e a problemÃ¡tica na AmazÃ´nia.
    *   *Dashboard Privado (`/app`):* Tela cheia, focada na gestÃ£o tÃ¡tica e tomada de decisÃ£o rÃ¡pida.
*   **RF07 - Temas de Contraste (Light/Dark Mode):** AlternÃ¢ncia nativa de interface. Dark mode para centro de comando (destaque tÃ©rmico) e Light mode para operaÃ§Ãµes de campo sob sol e exportaÃ§Ã£o de PDFs.
*   **RF08 - Layout TÃ¡tico (HUD):**
    *   *Painel Esquerdo (Fila de UrgÃªncia):* Lista ranqueada de UCs com maior risco/focos no dia, com mini-grÃ¡ficos de tendÃªncia.
    *   *Mapa Central:* MapLibre GL JS para renderizaÃ§Ã£o veloz de polÃ­gonos e rasters.
    *   *Painel Direito (RetrÃ¡til - AnalÃ­tico):* Dados aprofundados ao clicar em uma UC (gauge de risco, variÃ¡veis determinantes, botÃ£o de gerar dNBR).
    *   *RodapÃ© (RetrÃ¡til - Temporal):* GrÃ¡ficos cruzando histÃ³rico de focos vs. chuva.
*   **RF09 - Fila de Tarefas VisÃ­vel (UX AssÃ­ncrona):** 
    *   Sempre que o usuÃ¡rio solicitar um processamento pesado, a interface exibe um toast/snackbar (ex: *"Aguardando satÃ©lite - PosiÃ§Ã£o 2/2"*).
    *   IntegraÃ§Ã£o via WebSockets/SSE atualizarÃ¡ a interface em tempo real quando a tarefa concluir, desenhando a cicatriz no mapa automaticamente.
*   **RF10 - ExportaÃ§Ã£o Multiformato:** BotÃµes flutuantes para download de GeoJSON (vetores), CSV (tabelas) e PDF (relatÃ³rios operacionais para campo).

## 6. Estrutura de DiretÃ³rios Base

```text
/
â”œâ”€â”€ .env
â”œâ”€â”€ secrets/
â”‚   â””â”€â”€ sentinel-landsat-download-c9ec6de8d78c.json
â”œâ”€â”€ docker-compose.yml
â”œâ”€â”€ backend/                    # FastAPI, PostGIS, Celery (Python 3.12)
â”‚   â”œâ”€â”€ src/
â”‚   â”‚   â”œâ”€â”€ api/
â”‚   â”‚   â”œâ”€â”€ core/
â”‚   â”‚   â”œâ”€â”€ services/           # LÃ³gica do GEE e ML
â”‚   â”‚   â”œâ”€â”€ models/
â”‚   â”‚   â””â”€â”€ workers/            # Tarefas assÃ­ncronas do Celery
â”‚   â”œâ”€â”€ notebooks/              # Pesquisa e Treinamento do Modelo (XGBoost)
â”‚   â””â”€â”€ requirements.txt
â””â”€â”€ frontend/                   # Vue/React + MapLibre
    â”œâ”€â”€ src/
    â”‚   â”œâ”€â”€ components/         # MapBox, Panels, Modals, Toasts
    â”‚   â”œâ”€â”€ views/              # Scrollytelling, Dashboard
    â”‚   â”œâ”€â”€ services/           # Axios (API calls), WebSockets
    â”‚   â””â”€â”€ assets/             # Estilos (Light/Dark mode)
    â””â”€â”€ package.json
```