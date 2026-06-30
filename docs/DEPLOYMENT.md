# Guia de Implantação (Deployment)

Este guia cobre a implantação do Steam Market Price Tracker em diferentes plataformas.

## Pré-requisitos

- Conta na plataforma de deploy escolhida
- Banco de dados configurado (SQLite para teste, PostgreSQL para produção)
- Variáveis de ambiente configuradas

---

## Render

### Configuração

1. Crie uma conta em [render.com](https://render.com)

2. Crie um novo Web Service:
   - Conecte seu repositório GitHub
   - Configure as variáveis de ambiente

3. `render.yaml`:

```yaml
services:
  - type: web
    name: steam-price-tracker
    env: python
    region: oregon
    plan: free
    buildCommand: pip install -r requirements.txt
    startCommand: uvicorn main:app --host 0.0.0.0 --port $PORT
    envVars:
      - key: DATABASE_URL
        sync: false
      - key: API_HOST
        value: 0.0.0.0
      - key: API_PORT
        fromService:
          name: steam-price-tracker
          type: web
          envVarKey: PORT
```

### Variáveis de Ambiente

```bash
DATABASE_URL=postgresql://user:password@host:5432/steam_tracker
API_HOST=0.0.0.0
COLLECTION_INTERVAL=15
```

### Banco de Dados

Use o PostgreSQL gratuito do Render:

1. Crie um novo PostgreSQL database
2. Copie a connection string
3. Atualize `DATABASE_URL`

---

## Railway

### Configuração

1. Crie uma conta em [railway.app](https://railway.app)

2. Deploy via GitHub:
   - Conecte seu repositório
   - Railway detectará automaticamente o Python

3. `railway.toml`:

```toml
[build]
builder = "NIXPACKS"

[deploy]
startCommand = "uvicorn main:app --host 0.0.0.0 --port $PORT"
restartPolicyType = "ON_FAILURE"
```

### Variáveis de Ambiente

Configure no dashboard do Railway:

```bash
DATABASE_URL=postgresql://...
COLLECTION_INTERVAL=15
```

---

## Fly.io

### Instalação

```bash
# Instalar Fly CLI
curl -L https://fly.io/install.sh | sh

# Login
fly auth login
```

### Configuração

```bash
# Inicializar app
fly launch

# Configurar banco de dados
fly postgres create --name steam-db

# Anexar banco
fly postgres attach --app steam-price-tracker steam-db

# Deploy
fly deploy
```

### fly.toml

```toml
app = "steam-price-tracker"
primary_region = "gru"

[build]
  dockerfile = "Dockerfile"

[env]
  API_HOST = "0.0.0.0"
  COLLECTION_INTERVAL = "15"

[[services]]
  http_checks = []
  internal_port = 8000
  processes = ["app"]
  protocol = "tcp"
  script_checks = []

  [services.concurrency]
    hard_limit = 25
    soft_limit = 20
    type = "connections"

  [[services.ports]]
    force_https = true
    handlers = ["http"]
    port = 80

  [[services.ports]]
    handlers = ["tls", "http"]
    port = 443

  [[services.tcp_checks]]
    grace_period = "1s"
    interval = "15s"
    restart_limit = 0
    timeout = "2s"
```

### Dockerfile

```dockerfile
FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

---

## Docker

### Build Local

```bash
docker build -t steam-price-tracker .
docker run -p 8000:8000 steam-price-tracker
```

### Docker Compose

```yaml
version: '3.8'

services:
  app:
    build: .
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=sqlite:///steam_tracker.db
      - COLLECTION_INTERVAL=5
    volumes:
      - ./data:/app/data
    restart: unless-stopped

  # Opcional: PostgreSQL
  db:
    image: postgres:15
    environment:
      POSTGRES_DB: steam_tracker
      POSTGRES_USER: user
      POSTGRES_PASSWORD: password
    volumes:
      - postgres_data:/var/lib/postgresql/data
    ports:
      - "5432:5432"

volumes:
  postgres_data:
```

---

## Configuração de Produção

### Variáveis de Ambiente

```bash
# Obrigatórias
DATABASE_URL=postgresql://user:pass@host:5432/dbname
API_HOST=0.0.0.0
API_PORT=8000

# Opcionais
COLLECTION_INTERVAL=15  # minutos
LOG_LEVEL=INFO
ENABLE_ALERTS=true
```

### Segurança

1. **HTTPS**: Use sempre em produção
2. **API Keys**: Implemente autenticação
3. **Rate Limiting**: Configure limits adequados
4. **CORS**: Restrinja origens permitidas

### Monitoramento

Configure logs e monitoramento:

```bash
# Logs
tail -f logs/app.log

# Health check
curl https://seu-app.com/health
```

### Backup

```bash
# SQLite
cp steam_tracker.db steam_tracker_backup.db

# PostgreSQL
pg_dump -U user dbname > backup.sql
```

---

## Troubleshooting

### App não inicia

```bash
# Verificar logs
tail -f logs/app.log

# Verificar variáveis
printenv | grep DATABASE
```

### Erros de Banco de Dados

```bash
# Testar conexão
python -c "from app.database import engine; print(engine.connect())"

# Rodar migrations
python -m app.database.migrate
```

### Rate Limit da Steam

- Aumente `COLLECTION_INTERVAL`
- Reduza número de itens monitorados
- Implemente cache mais agressivo

---

## Performance Tips

1. **Use PostgreSQL** em produção
2. **Configure connection pooling**
3. **Use cache** para respostas frequentes
4. **Monitore memory usage**
5. **Ajuste collection interval** baseado no número de itens

---

## Custo Estimado

| Plataforma | Plano | Custo/Mês |
|------------|-------|-----------|
| Render | Free | $0 |
| Render | Starter | $7 |
| Railway | Hobby | $5 |
| Fly.io | Free tier | ~$2 |
| VPS própria | DigitalOcean | $6+ |

*Valores aproximados em USD*