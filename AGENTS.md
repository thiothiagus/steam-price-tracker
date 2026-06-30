# Steam Market Price Tracker — Contexto Inicial do Projeto

## Objetivo do Projeto

Criar uma plataforma de monitoramento de preços do mercado da Steam focada inicialmente em itens de TBH (Task Bar Hero) e CS2 (Counter-Strike 2), utilizando APIs públicas gratuitas da Steam.

O sistema deve:

* coletar preços periodicamente;
* armazenar histórico;
* exibir gráficos;
* permitir alertas;
* identificar oportunidades de mercado;
* operar com baixo custo;
* funcionar inicialmente com infraestrutura gratuita.

---

# Visão Geral do Sistema

O projeto será dividido em 4 partes principais:

1. Coletor de dados (Crawler/Tracker)
2. Banco de dados
3. API Backend
4. Frontend Dashboard

---

# Stack Inicial

## Backend

* Python 3.12+

## Framework API

* FastAPI

## Banco de Dados

* SQLite inicialmente
* PostgreSQL futuramente

## ORM

* SQLAlchemy

## Scheduler

* APScheduler

## Frontend

* HTML + Jinja inicialmente
* Chart.js para gráficos

## HTTP Requests

* requests ou httpx

## Deploy Gratuito

* Render
* Railway
* Fly.io

---

# Fonte dos Dados

## Endpoint principal

```text
https://steamcommunity.com/market/priceoverview/
```

### Parâmetros

| Nome             | Descrição    |
| ---------------- | ------------ |
| appid            | ID do jogo   |
| currency         | Moeda        |
| market_hash_name | Nome do item |

### Exemplo

```text
https://steamcommunity.com/market/priceoverview/?appid=730&currency=7&market_hash_name=AK-47%20|%20Redline%20(Field-Tested)
```

---

# Endpoints Utilizados

## 1. priceoverview

Retorna:

* menor preço;
* preço mediano;
* volume.

---

## 2. pricehistory

```text
https://steamcommunity.com/market/pricehistory/
```

Retorna:

* histórico temporal;
* preço;
* volume.

---

# Requisitos do Sistema

## Funcionais

### RF001

O sistema deve monitorar preços de itens da Steam.

### RF002

O sistema deve salvar histórico de preços.

### RF003

O sistema deve permitir múltiplos itens monitorados.

### RF004

O sistema deve gerar gráficos históricos.

### RF005

O sistema deve permitir alertas de preço.

### RF006

O sistema deve evitar rate limits da Steam.

### RF007

O sistema deve operar gratuitamente inicialmente.

---

## Não Funcionais

### RNF001

O sistema deve ser modular.

### RNF002

O sistema deve permitir futura migração para PostgreSQL.

### RNF003

O sistema deve suportar expansão futura para múltiplos jogos.

### RNF004

O sistema deve possuir arquitetura preparada para microserviços futuramente.

---

# Estrutura Inicial do Projeto

```text
steam-price-tracker/
│
├── app/
│   ├── api/
│   ├── services/
│   ├── models/
│   ├── database/
│   ├── scheduler/
│   ├── collectors/
│   └── utils/
│
├── frontend/
│
├── tests/
│
├── requirements.txt
├── README.md
└── main.py
```

---

# Modelagem Inicial do Banco

## Tabela: tracked_items

```sql
CREATE TABLE tracked_items (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    appid INTEGER NOT NULL,
    market_hash_name TEXT NOT NULL,
    enabled BOOLEAN DEFAULT TRUE,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);
```

---

## Tabela: price_history

```sql
CREATE TABLE price_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    tracked_item_id INTEGER NOT NULL,
    price REAL,
    median_price REAL,
    volume INTEGER,
    collected_at DATETIME DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (tracked_item_id)
    REFERENCES tracked_items(id)
);
```

---

# Arquitetura de Coleta

## Estratégia

O sistema NÃO deve fazer requests em tempo real para usuários.

Em vez disso:

* um scheduler executa coletas periódicas;
* os dados são armazenados localmente;
* o frontend consulta apenas o banco.

---

# Estratégia Anti Rate Limit

## Regras

### 1.

Nunca fazer muitas requests simultâneas.

### 2.

Adicionar delays entre requests.

### 3.

Usar retry com backoff exponencial.

### 4.

Persistir cache local.

### 5.

Evitar duplicação de requests.

---

# Frequência de Coleta

| Quantidade de Itens | Intervalo  |
| ------------------- | ---------- |
| 1–20                | 5 minutos  |
| 20–100              | 15 minutos |
| 100–500             | 30 minutos |
| 500+                | 1 hora     |

---

# Funcionalidades Futuras

## Fase 2

### Alertas

* Discord
* Telegram
* Email

### Dashboard avançado

* Top gainers
* Top losers
* Volume spikes

### Comparação entre mercados

* Steam
* Skinport
* Buff163
* CSFloat

### Arbitragem

Detectar diferença de preço entre plataformas.

---

# Regras Técnicas Importantes

## IMPORTANTE

A Steam NÃO possui API oficial pública documentada para o Community Market.

Os endpoints utilizados são endpoints públicos não oficiais.

Portanto:

* o sistema deve ser resiliente;
* o código deve prever mudanças;
* o código deve tratar falhas da Steam;
* o sistema deve possuir logs robustos.

---

# Convenções de Código

## Python

* PEP8
* type hints obrigatórios
* docstrings obrigatórias

## API

* RESTful
* JSON padronizado

## Banco

* migrations obrigatórias
* timestamps em UTC

---

# Objetivo do MVP

O MVP deve permitir:

1. cadastrar itens;
2. coletar preços;
3. salvar histórico;
4. visualizar gráficos;
5. consultar preços atuais;
6. exibir histórico simples.

---

# Prioridades de Desenvolvimento

## Prioridade 1

* Estrutura do projeto
* Banco
* Coletor
* Scheduler

## Prioridade 2

* API REST
* Frontend básico

## Prioridade 3

* Alertas
* Analytics
* Dashboard avançado

---

# Perfil do Projeto

## Características desejadas

* modular;
* escalável;
* resiliente;
* econômico;
* fácil manutenção;
* preparado para IA-assisted development.

---

# Instruções para Agentes de IA

## Sempre:

* manter arquitetura modular;
* evitar acoplamento;
* criar código limpo;
* documentar funções;
* criar tipagem;
* evitar hardcodes;
* usar boas práticas;
* prever falhas da Steam.

## Nunca:

* fazer scraping agressivo;
* criar loops infinitos sem controle;
* ignorar tratamento de erro;
* fazer requests massivas paralelas.

---

# Roadmap

## MVP

* coleta de preços;
* histórico;
* gráficos básicos.

## v2

* alertas;
* analytics;
* filtros.

## v3

* arbitragem;
* multi-market;
* machine learning.

## v4

* previsão de preços;
* detecção de tendências;
* recomendações automáticas.
