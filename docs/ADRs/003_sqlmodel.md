# ADR 003 — SQLModel as ORM

## Status

Accepted

## Context

The application needs to interact with a SQLite database (MVP) and a PostgreSQL
database (production). We need an ORM to avoid writing raw SQL and to define
the data model in Python.

In the future, the application will expose a REST API (likely FastAPI).
The data models will need to be shared between the database layer and the API layer.

## Options Considered

### Option 1 — SQLAlchemy alone

The reference ORM for Python. Mature, widely used, supports SQLite and PostgreSQL.

- Requires writing separate models for the database and for API validation (Pydantic)
- More verbose
- No built-in integration with FastAPI

### Option 2 — SQLModel ✓ chosen

Built on top of SQLAlchemy and Pydantic. One class defines both the database table
and the API validation schema.

- Less code — one model serves both the database and the API
- Native integration with FastAPI
- Same migration path as SQLAlchemy (only the connection string changes between
  SQLite and PostgreSQL)

## Decision

Use SQLModel as the ORM.

## Arguments

SQLModel reduces duplication: the same model class is used for the database (SQLAlchemy)
and for data validation (Pydantic). When the REST API is built with FastAPI,
no rewrite is needed — the models are already compatible.

## Consequences

- **Advantage:** one model for database + API validation — no duplication
- **Advantage:** smooth migration from SQLite (MVP) to PostgreSQL (production)
- **Accepted trade-off:** SQLModel is less mature than SQLAlchemy alone;
  for complex queries, raw SQLAlchemy syntax may still be needed

## Related Decisions

- ADR 001 — Streamlit for the MVP dashboard
- ADR 002 — Database isolation strategy
