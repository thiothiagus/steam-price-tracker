# Contribuindo com o Steam Market Price Tracker

Obrigado por considerar contribuir com o Steam Market Price Tracker! Este documento fornece diretrizes para contribuir com o projeto.

## Código de Conduta

- Seja respeitoso e inclusivo
- Aceite críticas construtivas
- Foque no que é melhor para a comunidade
- Mantenha profissionalismo

## Como Contribuir

### 1. Reportando Bugs

Antes de criar um issue, verifique se o bug já foi reportado. Ao criar um novo issue, inclua:

- Descrição clara do bug
- Passos para reproduzir
- Comportamento esperado vs. atual
- Screenshots (se aplicável)
- Informações do ambiente (OS, Python version, etc.)

### 2. Sugerindo Features

Sugestões são bem-vindas! Ao sugerir uma feature, inclua:

- Descrição da feature
- Caso de uso
- Exemplos de como funcionaria
- Alternativas consideradas

### 3. Pull Requests

#### Antes de Enviar

1. Faça fork do repositório
2. Crie uma branch para sua feature/fix:
   ```bash
   git checkout -b feature/nova-feature
   # ou
   git checkout -b fix/corrigir-bug
   ```

3. Siga as convenções de código
4. Escreva testes (quando aplicável)
5. Certifique-se de que todos os testes passam
6. Atualize a documentação (quando necessário)

#### Padrões de Código

- **Python**: Siga PEP 8
- **Type hints**: Obrigatórios em todas as funções
- **Docstrings**: Obrigatórias em todas as funções públicas
- **Comentários**: Use apenas quando necessário para explicar lógica complexa

#### Convenções de Commit

Use mensagens de commit claras e descritivas:

```
feat: adiciona alerta de preço via Discord
fix: corrige erro de rate limit na coleta
docs: atualiza README com novos endpoints
refactor: melhora estrutura do coletor de dados
test: adiciona testes para API de itens
```

#### Checklist do Pull Request

- [ ] O código segue as convenções do projeto
- [ ] Type hints foram adicionados
- [ ] Docstrings foram adicionadas
- [ ] Testes foram escritos (quando aplicável)
- [ ] A documentação foi atualizada (quando necessário)
- [ ] O código foi testado localmente
- [ ] Não há secrets ou chaves no código

### 4. Revisão de Código

Todos os PRs serão revisados. Esteja preparado para:

- Receber feedback construtivo
- Fazer mudanças solicitadas
- Explicar decisões de implementação

## Arquitetura do Projeto

### Estrutura de Diretórios

```
app/
├── api/          # Endpoints FastAPI
├── services/     # Regras de negócio
├── models/       # Modelos SQLAlchemy
├── database/     # Configuração DB
├── scheduler/    # APScheduler jobs
├── collectors/   # Steam API collectors
└── utils/        # Utilitários
```

### Camadas

1. **API Layer**: Endpoints HTTP
2. **Service Layer**: Lógica de negócio
3. **Repository Layer**: Acesso a dados
4. **Collector Layer**: Integração com Steam

## Desenvolvimento Local

### Setup

```bash
# Clone seu fork
git clone https://github.com/seu-usuario/steam-price-tracker.git
cd steam-price-tracker

# Crie um ambiente virtual
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Instale dependências
pip install -r requirements.txt

# Instale dependências de desenvolvimento
pip install -r requirements-dev.txt  # quando disponível
```

### Rodando Testes

```bash
# Rodar todos os testes
pytest

# Com coverage
pytest --cov=app

# Rodar testes específicos
pytest tests/test_api.py
```

### Rodando a API

```bash
# Desenvolvimento
python main.py

# Produção
uvicorn main:app --host 0.0.0.0 --port 8000
```

## Diretrizes Específicas

### Collectors

- Sempre trate erros de conexão com a Steam
- Implemente retry com backoff exponencial
- Respeite rate limits
- Log todas as requisições e respostas

### Models

- Use SQLAlchemy ORM
- Inclua timestamps (created_at, updated_at)
- Defina relações claramente
- Crie migrations para mudanças no schema

### API

- Siga princípios RESTful
- Retorne JSON consistente
- Use códigos HTTP apropriados
- Documente endpoints com OpenAPI/Swagger

### Tests

- Escreva testes unitários para lógica crítica
- Escreva testes de integração para APIs
- Mock chamadas externas (Steam API)
- Mantenha coverage acima de 80%

## Áreas que Precisam de Ajuda

- [ ] Testes automatizados
- [ ] Documentação
- [ ] UI/UX do frontend
- [ ] Performance de queries
- [ ] Monitoramento e logging
- [ ] Deploy automatizado

## Dúvidas?

Sinta-se à vontade para abrir uma issue com a tag `question` ou entrar em contato com os mantenedores.

## Agradecimentos

Todas as contribuições são apreciadas, não importa o tamanho. Cada PR ajuda a tornar o projeto melhor!