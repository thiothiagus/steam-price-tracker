# Steam Price Tracker

Monitoramento de preços do mercado da Steam com foco em itens de TBH (Task Bar Hero) e CS2 (Counter-Strike 2).

Coleta dados periodicamente, armazena histórico, exibe gráficos e identifica oportunidades de mercado utilizando APIs públicas da Steam.

## Funcionalidades

- Monitoramento automático de preços de itens da Steam
- Histórico completo de preços com gráficos
- Dashboard para visualização de dados com ícones dos itens
- Coleta periódica com controle de rate limit
- Suporte a múltiplos itens e jogos
- Ícones automaticamente baixados da Steam Community Market
- Importação de itens a partir do save do TBH
- Testes automatizados com pytest

## Stack

- **Backend**: Python 3.12+, FastAPI, uvicorn
- **Banco de Dados**: SQLite (PostgreSQL em produção futura)
- **ORM**: SQLAlchemy
- **Scheduler**: APScheduler
- **Frontend**: HTML, Jinja2, Chart.js
- **HTTP Client**: httpx

## Instalação

### Pré-requisitos

- Python 3.12 ou superior
- pip

### Passos

1. Clone o repositório:

```bash
git clone <repository-url>
cd steam-price-tracker
```

2. Instale as dependências:

```bash
pip install -r requirements.txt
```

3. Execute a aplicação:

```bash
python main.py
```

Ou via uvicorn (com hot-reload para desenvolvimento):

```bash
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

4. Acesse o dashboard em `http://localhost:8000`

## Estrutura do Projeto

```
steam-price-tracker/
├── app/
│   ├── api/          # Endpoints da API (routes.py, pages.py)
│   ├── services/     # Lógica de negócio
│   ├── models/       # Modelos SQLAlchemy
│   ├── database/     # Configuração do banco
│   ├── scheduler/    # Jobs agendados (APScheduler)
│   ├── collectors/   # Coleta de dados da Steam
│   ├── data/
│   │   ├── icons/    # Ícones baixados da Steam
│   │   ├── items.json
│   │   └── icon_hashes.json
│   └── utils/        # Utilitários (item_db, steam_api, save_parser)
├── frontend/
│   └── static/icons/ # Ícones servidos ao frontend
├── tests/            # Testes automatizados
├── docs/             # Documentação
├── main.py           # Entry point (FastAPI app)
├── requirements.txt
└── README.md
```

### Sistema de Ícones

Os ícones são gerenciados automaticamente:

| Local | Caminho | Descrição |
|-------|---------|-----------|
| Download | `app/data/icons/` | Baixados da Steam e armazenados localmente |
| Frontend | `frontend/static/icons/` | Cópias servidas via `/static/icons/` |
| Fallback | — | Bolinha colorida pela raridade quando a Steam bloqueia |

Para adicionar ícones manualmente, coloque-os em `app/data/icons/` com o nome correto (ex: `Dimensional Sword (Immortal) A.png`).

## Configuração

### Variáveis de Ambiente

| Variável | Descrição | Padrão |
|----------|-----------|--------|
| DATABASE_URL | URL do banco de dados | `sqlite:///./app/data/steam_tracker.db` |
| STEAM_CURRENCY | Moeda da Steam (7=BRL) | `7` |
| COLLECTOR_DELAY_SECONDS | Delay entre requisições à Steam | `5.0` |
| COLLECTOR_REFRESH_HOURS | Janela de staleness do preço | `1` |
| COLLECTOR_MAX_RETRIES | Tentativas por item | `3` |
| COLLECTOR_BACKOFF_FACTOR | Fator de backoff exponencial | `3.0` |
| RUN_INITIAL_COLLECTION_ON_STARTUP | Coleta inicial no startup | `true` |
| SAVE_SOURCE_PATH | Caminho do save original (auto-detect AppData se vazio) | — |
| SAVE_DEST_PATH | Caminho de destino para cópia do save | project root |
| LOG_LEVEL | Nível de log | `INFO` |

### Frequência de Coleta

| Quantidade de Itens | Intervalo |
|---------------------|-----------|
| 1–20 | 5 minutos |
| 20–100 | 15 minutos |
| 100–500 | 30 minutos |
| 500+ | 1 hora |

## API

Todas as rotas REST são prefixadas com `/api`.

### Itens

| Método | Rota | Descrição |
|--------|------|-----------|
| GET | `/api/items` | Listar itens monitorados |
| GET | `/api/items/archived` | Listar itens arquivados |
| POST | `/api/items` | Adicionar novo item |
| PATCH | `/api/items/{id}/toggle` | Habilitar/desabilitar item |
| DELETE | `/api/items/{id}` | Remover item e histórico |
| POST | `/api/items/{id}/restore` | Restaurar item arquivado |

### Preços

| Método | Rota | Descrição |
|--------|------|-----------|
| GET | `/api/items/{id}/history?limit=N` | Histórico de preços |
| GET | `/api/items/{id}/analytics` | Analytics (variação 24h/7d, média móvel, sparkline) |
| POST | `/api/items/{id}/collect` | Forçar coleta de um item |
| POST | `/api/collect` | Forçar coleta completa |
| GET | `/api/collect/cooldown` | Cooldown restante da Steam |
| GET | `/api/collection/status` | Progresso da coleta |

### Save / Importação

| Método | Rota | Descrição |
|--------|------|-----------|
| GET | `/api/import-preview` | Pré-visualizar itens do save |
| POST | `/api/import-save` | Importar do save do TBH |
| GET | `/api/watcher/status` | Status do SaveWatcher |
| POST | `/api/watcher/start` | Iniciar SaveWatcher |
| POST | `/api/watcher/stop` | Parar SaveWatcher |

### Páginas

| Método | Rota | Descrição |
|--------|------|-----------|
| GET | `/` | Dashboard TBH |
| GET | `/cs2` | Dashboard CS2 |
| GET | `/items/{id}` | Detalhe do item (com gráfico) |

### Exemplo de Uso

```bash
# Adicionar item via API
curl -X POST http://localhost:8000/api/items \
  -H "Content-Type: application/json" \
  -d '{"appid": 730, "market_hash_name": "AK-47 | Redline (Field-Tested)", "enabled": true}'

# Importar itens do save do TBH
curl http://localhost:8000/api/import-preview   # preview
curl -X POST http://localhost:8000/api/import-save  # importar

# Consultar histórico
curl http://localhost:8000/api/items/1/history?limit=100
```

## Limitações

- A Steam não possui API oficial para o Community Market
- Endpoints podem mudar sem aviso prévio
- Rate limits da Steam devem ser respeitados
- Dados podem ter atraso de alguns minutos

## Roadmap

### MVP (Atual)
- [x] Coleta de preços
- [x] Histórico
- [x] Gráficos básicos
- [x] Cadastro de itens via UI
- [x] Testes automatizados

### v2
- [ ] Alertas (Discord, Telegram, Email)
- [ ] Analytics avançado
- [ ] Filtros e busca

### v3
- [ ] Arbitragem entre mercados
- [ ] Multi-market (Skinport, Buff163, CSFloat)

### v4
- [ ] Previsão de preços
- [ ] Detecção de tendências
- [ ] Recomendações automáticas

## Contribuição

1. Fork o projeto
2. Crie uma branch para sua feature (`git checkout -b feature/AmazingFeature`)
3. Commit suas mudanças (`git commit -m 'Add some AmazingFeature'`)
4. Push para a branch (`git push origin feature/AmazingFeature`)
5. Abra um Pull Request

Veja [CONTRIBUTING.md](CONTRIBUTING.md) para mais detalhes.

## Licença

Distribuído sob a licença MIT. Veja `LICENSE` para mais informações.

## Aviso Legal

Este projeto utiliza endpoints não oficiais da Steam Community Market. Não é afiliado, endossado ou suportado pela Valve Corporation. Steam e o logo Steam são marcas registradas da Valve Corporation.
