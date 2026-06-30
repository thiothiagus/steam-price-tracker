# Steam Market Price Tracker

Monitoramento de preços do mercado da Steam com foco em itens de TBH (Task Bar Hero) e CS2 (Counter-Strike 2).

## Visão Geral

Plataforma de monitoramento de preços que coleta dados periodicamente, armazena histórico, exibe gráficos e identifica oportunidades de mercado utilizando APIs públicas da Steam.

## Funcionalidades

- Monitoramento automático de preços de itens da Steam
- Histórico completo de preços com gráficos
- Alertas de preço (em desenvolvimento)
- Dashboard para visualização de dados
- Coleta periódica com controle de rate limit
- Suporte a múltiplos itens e jogos

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
    "market_hash_name": "AK-47 | Redline (Field-Tested)"
}
```

### Consultar Preços

```bash
# Preço atual
GET /api/items/{item_id}/price

# Histórico
GET /api/items/{item_id}/history

# Gráfico
GET /api/items/{item_id}/chart
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
│   └── utils/        # Utilitários
├── frontend/         # Templates e estáticos
├── tests/            # Testes automatizados
├── docs/             # Documentação
├── requirements.txt
├── main.py
└── README.md
```

## Configuração

### Variáveis de Ambiente

| Variável | Descrição | Padrão |
|----------|-----------|--------|
| DATABASE_URL | URL do banco de dados | sqlite:///steam_tracker.db |
| API_HOST | Host da API | 0.0.0.0 |
| API_PORT | Porta da API | 8000 |
| COLLECTION_INTERVAL | Intervalo de coleta (min) | 5 |

## Frequência de Coleta

| Quantidade de Itens | Intervalo |
|---------------------|-----------|
| 1–20 | 5 minutos |
| 20–100 | 15 minutos |
| 100–500 | 30 minutos |
| 500+ | 1 hora |

## API Endpoints

### Itens

- `GET /api/items` - Listar itens monitorados
- `POST /api/items` - Adicionar novo item
- `GET /api/items/{id}` - Detalhes do item
- `PUT /api/items/{id}` - Atualizar item
- `DELETE /api/items/{id}` - Remover item

### Preços

- `GET /api/items/{id}/price` - Preço atual
- `GET /api/items/{id}/history` - Histórico de preços
- `GET /api/items/{id}/chart` - Dados para gráfico

### Saúde

- `GET /health` - Status da API
- `GET /ready` - Pronto para receber requests

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
- [ ] Cadastro de itens via UI

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