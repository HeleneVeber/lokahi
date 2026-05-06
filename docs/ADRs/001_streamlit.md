# ADR 001 — Streamlit for the MVP Dashboard

## Status

Accepted

## Context

The final application will have a dedicated backend and frontend, but we first need
a **dashboard** to validate the data model, test data imports, and analyse the first
real data sets.

We need to:

- Create and manage entities via forms (owners, managers, buildings, rooms, tenants)
- Import CSV and Excel files
- Display basic charts and tables

## Decision

Use Streamlit for the MVP dashboard.

## Arguments

We chose Streamlit because:

- everything is written in Python — no frontend knowledge required
- it is easy to start and to deploy (Streamlit Community Cloud, free tier)
- forms, charts, and tables require very few lines of code
- it allows sharing a live URL with non-technical users for testing

## Consequences

- **Accepted trade-off:** Streamlit is a temporary tool. When the real application
  is built, this dashboard will be replaced by a dedicated frontend. The Python
  business logic (models, import utilities) will be reused; the Streamlit pages
  will not.
- **Limitation:** Streamlit is not suited for complex user interactions or
  multi-user sessions with authentication.

## Related Decisions

- ADR 002 — SQLite per account (database isolation strategy)
- ADR 003 — SQLModel as ORM
