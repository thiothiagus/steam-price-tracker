# API Documentation

Documentação completa da API do Steam Market Price Tracker.

## Base URL

```
http://localhost:8000/api
```

## Autenticação

Atualmente a API não requer autenticação. Em produção, endpoints poderão requerer API keys.

---

## Endpoints

### Health Check

#### GET /health

Verifica se a API está online.

**Response:**
```json
{
    "status": "healthy",
    "timestamp": "2026-06-30T12:00:00Z"
}
```

---

### Itens Monitorados

#### GET /items

Lista todos os itens monitorados.

**Query Parameters:**
- `enabled` (boolean): Filtrar por status
- `appid` (integer): Filtrar por jogo
- `limit` (integer): Limite de resultados
- `offset` (integer): Paginação

**Response:**
```json
{
    "items": [
        {
            "id": 1,
            "appid": 730,
            "market_hash_name": "AK-47 | Redline (Field-Tested)",
            "enabled": true,
            "created_at": "2026-06-30T10:00:00Z"
        }
    ],
    "total": 1,
    "limit": 50,
    "offset": 0
}
```

#### GET /items/{item_id}

Obtém detalhes de um item específico.

**Response:**
```json
{
    "id": 1,
    "appid": 730,
    "market_hash_name": "AK-47 | Redline (Field-Tested)",
    "enabled": true,
    "created_at": "2026-06-30T10:00:00Z",
    "current_price": 15.50,
    "median_price": 15.75,
    "volume": 1250
}
```

#### POST /items

Adiciona um novo item para monitoramento.

**Request Body:**
```json
{
    "appid": 730,
    "market_hash_name": "AK-47 | Redline (Field-Tested)"
}
```

**Response (201 Created):**
```json
{
    "id": 1,
    "appid": 730,
    "market_hash_name": "AK-47 | Redline (Field-Tested)",
    "enabled": true,
    "created_at": "2026-06-30T10:00:00Z"
}
```

**Errors:**
- `400`: Dados inválidos
- `409`: Item já existe

#### PUT /items/{item_id}

Atualiza um item existente.

**Request Body:**
```json
{
    "market_hash_name": "AK-47 | Redline (Minimal Wear)",
    "enabled": false
}
```

**Response:**
```json
{
    "id": 1,
    "appid": 730,
    "market_hash_name": "AK-47 | Redline (Minimal Wear)",
    "enabled": false,
    "created_at": "2026-06-30T10:00:00Z",
    "updated_at": "2026-06-30T12:00:00Z"
}
```

#### DELETE /items/{item_id}

Remove um item do monitoramento.

**Response (204 No Content):**
```
(no body)
```

---

### Preços

#### GET /items/{item_id}/price

Obtém o preço atual de um item.

**Response:**
```json
{
    "item_id": 1,
    "price": 15.50,
    "median_price": 15.75,
    "volume": 1250,
    "currency": "BRL",
    "collected_at": "2026-06-30T12:00:00Z"
}
```

**Errors:**
- `404`: Item não encontrado
- `404`: Nenhum preço disponível

#### GET /items/{item_id}/history

Obtém histórico de preços de um item.

**Query Parameters:**
- `start_date` (string): Data inicial (ISO 8601)
- `end_date` (string): Data final (ISO 8601)
- `limit` (integer): Limite de registros

**Response:**
```json
{
    "item_id": 1,
    "history": [
        {
            "price": 15.50,
            "median_price": 15.75,
            "volume": 1250,
            "collected_at": "2026-06-30T12:00:00Z"
        },
        {
            "price": 15.25,
            "median_price": 15.50,
            "volume": 1100,
            "collected_at": "2026-06-30T11:55:00Z"
        }
    ],
    "total": 2
}
```

#### GET /items/{item_id}/chart

Obtém dados formatados para gráficos.

**Query Parameters:**
- `period` (string): Período (1h, 24h, 7d, 30d, 90d, 1y)
- `interval` (string): Intervalo dos pontos (5m, 15m, 1h, 1d)

**Response:**
```json
{
    "item_id": 1,
    "period": "24h",
    "data": {
        "labels": ["10:00", "11:00", "12:00"],
        "prices": [15.25, 15.40, 15.50],
        "medians": [15.50, 15.60, 15.75],
        "volumes": [1100, 1200, 1250]
    }
}
```

---

### Estatísticas

#### GET /stats

Obtém estatísticas gerais do sistema.

**Response:**
```json
{
    "total_items": 50,
    "enabled_items": 45,
    "total_collections": 10000,
    "last_collection": "2026-06-30T12:00:00Z",
    "next_collection": "2026-06-30T12:05:00Z",
    "collection_interval_minutes": 5
}
```

#### GET /stats/top-gainers

Obtém itens com maior valorização.

**Query Parameters:**
- `period` (string): Período (24h, 7d, 30d)
- `limit` (integer): Limite de resultados

**Response:**
```json
{
    "period": "24h",
    "items": [
        {
            "id": 5,
            "market_hash_name": "AWP | Asiimov (Field-Tested)",
            "current_price": 85.00,
            "previous_price": 80.00,
            "change_percent": 6.25
        }
    ]
}
```

#### GET /stats/top-losers

Obtém itens com maior desvalorização.

**Response:** (mesmo formato que top-gainers)

---

## Códigos de Erro

| Código | Descrição |
|--------|-----------|
| 400 | Bad Request - Dados inválidos |
| 404 | Not Found - Recurso não encontrado |
| 409 | Conflict - Item já existe |
| 429 | Too Many Requests - Rate limit |
| 500 | Internal Server Error |
| 503 | Service Unavailable - Steam indisponível |

## Rate Limiting

- Máximo de 100 requests por minuto por IP
- Endpoints de coleta têm limites específicos

## Exemplos de Uso

### Python

```python
import requests

# Listar itens
response = requests.get('http://localhost:8000/api/items')
items = response.json()

# Adicionar item
response = requests.post(
    'http://localhost:8000/api/items',
    json={'appid': 730, 'market_hash_name': 'AK-47 | Redline'}
)

# Obter histórico
response = requests.get(
    'http://localhost:8000/api/items/1/history',
    params={'period': '24h'}
)
```

### JavaScript

```javascript
// Listar itens
const response = await fetch('http://localhost:8000/api/items');
const items = await response.json();

// Adicionar item
await fetch('http://localhost:8000/api/items', {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({
        appid: 730,
        market_hash_name: 'AK-47 | Redline'
    })
});
```

## Swagger/OpenAPI

A documentação interativa está disponível em:
```
http://localhost:8000/docs
```

## Changelog

### v1.0.0
- Endpoints básicos de itens
- Histórico de preços
- Estatísticas simples