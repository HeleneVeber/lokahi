# ADR 002 — Database Isolation Strategy

## Status

To decide

## Context

The application will be multi-tenant (1 deployment, 1 instance for all clients).
Each account handles sensitive data (bank accounts, CPF, tenant history)
and will generate boletos (rent payment slips).
This data must not be accessible by another account or by developers.
Brazilian law (LGPD) makes this isolation a legal requirement.

For the MVP (Streamlit dashboard), there is no authentication —
the database strategy is simplified for testing purposes only.
The decision below applies to the production application.

## Architecture Options

### Option 1 — Shared database: data accessed by filtering on account_id

- Architecture used by: Notion, Trello, and many SaaS products
- Isolation: logical — enforced by query filters
- Risk: a missing filter in a query can expose sensitive data
- Best suited for: large-scale SaaS with non-sensitive data

### Option 2 — Schema-per-tenant

In the same database, each account has its own schema with the same tables
but isolated data.

- Architecture used by: Shopify (partially), Basecamp
- Isolation: structural — enforced by schema separation
- Risk: a developer with server access can read all schemas
  (mitigated by encrypting sensitive data)
- Best suited for: financial applications, LGPD-regulated apps

### Option 3 — Database-per-tenant

One database instance or server per client.

- Architecture used by: medical apps, defence, large enterprises
- Isolation: maximum — each client has their own database
- Risk: high cost and operational complexity
- Best suited for: cybersecurity firms, clients with contractual isolation requirements

## Decision

To be decided. Current preference: Option 2.

## Arguments

Less costly and complex than Option 3, with a strong level of isolation
(structural by schema separation).

## Consequences

To be analysed.

## Related Decisions

- ADR 001 — Streamlit for the MVP dashboard
- ADR 003 — SQLModel as ORM
