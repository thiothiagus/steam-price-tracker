# Steam Market Price Tracker

Monitoramento de preços do mercado da Steam com foco em itens de TBH (Task Bar Hero) e CS2 (Counter-Strike 2).

## Visão Geral

Plataforma de monitoramento de preços que coleta dados periodicamente, armazena histórico, exibe gráficos e identifica oportunidades de mercado utilizando APIs públicas da Steam.

## Funcionalidades

- Monitoramento automático de preços de itens da Steam
- Histórico completo de preços com gráficos
- Dashboard para visualização de dados com ícones dos itens
- Coleta periódica com controle de rate limit
- Suporte a múltiplos itens e jogos
- Ícones automaticamente baixados da Steam Community Market
- Testes automatizados com pytest

## Stack Tecnológica

- **Backend**: Python 3.12+, FastAPI
- **Banco de Dados**: SQLite (PostgreSQL em produção futura)
- **ORM**: SQLAlchemy
- **Scheduler**: APScheduler
- **Frontend**: HTML, Jinja2, Chart.js
- **HTTP Client**: requests/httpx

## Instalação

### Pré-requisitos

- Python 3.12 ou superior
- pip (gerenciador de pacotes Python)

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

4. Acesse o dashboard em `http://localhost:8000`

## Uso

### Adicionar Item para Monitoramento

```bash
# Via API
POST /api/items
{
    "appid": 730,
    "market_hash_name": "AK-47 | Redline (Field-Tested)",
    "enabled": true
}
```

Outra forma é importar automaticamente a partir do save do TBH:

```bash
# Preview antes de importar
GET /api/import-preview

# Importar todos os itens negociáveis do save
POST /api/import-save
```

### Consultar Preços

```bash
# Histórico
GET /api/items/{item_id}/history?limit=100

# Forçar coleta de um item
POST /api/items/{item_id}/collect

# Forçar coleta de todos (respeitando rate limit)
POST /api/collect
```

## Estrutura do Projeto

```
steam-price-tracker/
├── app/
│   ├── api/          # Endpoints da API
│   ├── services/     # Lógica de negócio
│   ├── models/       # Modelos SQLAlchemy
│   ├── database/     # Configuração do banco
│   ├── scheduler/    # Jobs agendados
│   ├── collectors/   # Coleta de dados da Steam
│   ├── data/
│   │   ├── icons/    # Ícones baixados localmente
│   │   ├── items.json
│   │   └── icon_hashes.json
│   └── utils/        # Utilitários (item_db, steam_api, save_parser)
├── frontend/         # Templates e estáticos
│   └── static/icons/ # Ícones servidos ao frontend
├── tests/            # Testes automatizados
├── docs/             # Documentação
├── requirements.txt
├── main.py
└── README.md
```

### Sistema de Ícones

Os ícones dos itens são gerenciados automaticamente:
- **Local**: `app/data/icons/` -下载ados da Steam e armazenados localmente
- **Frontend**: `frontend/static/icons/` - cópias para servir via URL `/static/icons/`
- **Fallback**: Quando Steam bloqueia, mostra bolinha colorida pela raridade

Para adicionar novos ícones manualmente, basta colocá-los em `app/data/icons/` com o nome correto (ex: `Dimensional Sword (Immortal) A.png`).

## Configuração

### Variáveis de Ambiente

| Variável | Descrição | Padrão |
|----------|-----------|--------|
| DATABASE_URL | URL do banco de dados | sqlite:///./app/data/steam_tracker.db |
| STEAM_CURRENCY | Moeda da Steam (7=BRL) | 7 |
| COLLECTOR_DELAY_SECONDS | Delay entre requisições à Steam | 5.0 |
| COLLECTOR_REFRESH_HOURS | Janela de staleness do preço | 1 |
| COLLECTOR_MAX_RETRIES | Tentativas por item | 3 |
| COLLECTOR_BACKOFF_FACTOR | Fator de backoff exponencial | 3.0 |
| RUN_INITIAL_COLLECTION_ON_STARTUP | Disparar coleta inicial no lifespan | true |
| SAVE_SOURCE_PATH | Caminho do save original (vazio = auto-detect AppData) | (vazio) |
| SAVE_DEST_PATH | Caminho de destino para cópia do save | (project root) |
| LOG_LEVEL | Nível de log (DEBUG/INFO/WARNING/ERROR) | INFO |

## Frequência de Coleta

| Quantidade de Itens | Intervalo |
|---------------------|-----------|
| 1–20 | 5 minutos |
| 20–100 | 15 minutos |
| 100–500 | 30 minutos |
| 500+ | 1 hora |

## API Endpoints

Todas as rotas REST são prefixadas com `/api`.

### Itens

- `GET /api/items` — listar itens monitorados (não arquivados)
- `GET /api/items/archived` — listar itens arquivados/soft-deleted
- `POST /api/items` — adicionar novo item
- `PATCH /api/items/{id}/toggle` — habilitar/desabilitar item
- `DELETE /api/items/{id}` — remover item e todo seu histórico
- `POST /api/items/{id}/restore` — restaurar item arquivado

### Preços

- `GET /api/items/{id}/history?limit=N` — histórico de preços
- `GET /api/items/{id}/analytics` — analytics (variação 24h/7d, média móvel, sparkline)
- `POST /api/items/{id}/collect` — forçar coleta de um item
- `POST /api/collect` — forçar coleta completa (respeitando rate limit)
- `GET /api/collect/cooldown` — tempo restante de cooldown da Steam
- `GET /api/collection/status` — progresso de coleta em andamento

### Save / Importação

- `GET /api/import-preview` — pré-visualizar itens do save
- `POST /api/import-save` — importar do save do TBH
- `GET /api/watcher/status` — status do SaveWatcher
- `POST /api/watcher/start` — iniciar SaveWatcher
- `POST /api/watcher/stop` — parar SaveWatcher

### Páginas

- `GET /` — dashboard TBH
- `GET /cs2` — dashboard CS2
- `GET /items/{id}` — detalhe do item (com gráfico)

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
- [ ] Machine learning

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

## Contato

- Issues: [GitHub Issues](https://github.com/yourusername/steam-price-tracker/issues)

## Agradecimentos

- Steam Community Market pelos dados
- Contribuidores do projeto