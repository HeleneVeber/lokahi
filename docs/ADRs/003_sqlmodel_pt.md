# ADR 003 — SQLModel como ORM

## Status

Aceito

## Contexto

A aplicação precisa interagir com um banco de dados SQLite (MVP) e um banco de dados
PostgreSQL (produção). Precisamos de um ORM para evitar escrever SQL puro e para
definir o modelo de dados em Python.

No futuro, a aplicação irá expor uma API REST (provavelmente FastAPI).
Os modelos de dados precisarão ser compartilhados entre a camada de banco de dados
e a camada de API.

## Opções Consideradas

### Opção 1 — SQLAlchemy sozinho

O ORM de referência para Python. Maduro, amplamente utilizado, suporta SQLite
e PostgreSQL.

- Exige escrever modelos separados para o banco de dados e para a validação
  de API (Pydantic)
- Mais verboso
- Sem integração nativa com FastAPI

### Opção 2 — SQLModel ✓ escolhido

Construído sobre SQLAlchemy e Pydantic. Uma classe define tanto a tabela do
banco de dados quanto o schema de validação da API.

- Menos código — um modelo serve tanto para o banco de dados quanto para a API
- Integração nativa com FastAPI
- Mesmo caminho de migração que o SQLAlchemy (apenas a string de conexão muda entre
  SQLite e PostgreSQL)

## Decisão

Usar o SQLModel como ORM.

## Argumentos

O SQLModel reduz a duplicação: a mesma classe de modelo é usada para o banco
de dados (SQLAlchemy) e para a validação de dados (Pydantic).
Quando a API REST for construída com FastAPI, nenhuma reescrita será
necessária — os modelos já são compatíveis.

## Consequências

- **Vantagem:** um modelo para banco de dados + validação de API — sem duplicação
- **Vantagem:** migração tranquila de SQLite (MVP) para PostgreSQL (produção)
- **Compromisso aceito:** o SQLModel é menos maduro que o SQLAlchemy sozinho;
  para consultas complexas, a sintaxe direta do SQLAlchemy ainda pode ser necessária

## Decisões Relacionadas

- ADR 001 — Streamlit para o dashboard MVP
- ADR 002 — Estratégia de isolamento de banco de dados
