# ADR 002 — Estratégia de Isolamento de Banco de Dados

## Status

A decidir

## Contexto

A aplicação será multi-tenant (1 deploy, 1 instância para todos os clientes).
Cada conta gerencia dados sensíveis (contas bancárias, CPF, histórico de inquilinos)
e irá gerar boletos de cobrança.
Esses dados não podem ser acessados por outra conta nem por desenvolvedores.
A lei brasileira (LGPD) torna esse isolamento um requisito legal.

Para o MVP (dashboard Streamlit), não há autenticação —
a estratégia de banco de dados é simplificada apenas para fins de teste.
A decisão abaixo se aplica à aplicação em produção.

## Opções de Arquitetura

### Opção 1 — Banco de dados compartilhado: dados acessados filtrando por `account_id`

- Arquitetura usada por: Notion, Trello e muitos produtos SaaS
- Isolamento: lógico — garantido por filtros nas consultas
- Risco: um filtro ausente em uma consulta pode expor dados sensíveis
- Mais adequado para: SaaS de grande escala com dados não sensíveis

### Opção 2 — Schema-per-tenant

No mesmo banco de dados, cada conta tem seu próprio schema com as mesmas tabelas,
mas dados isolados.

- Arquitetura usada por: Shopify (parcialmente), Basecamp
- Isolamento: estrutural — garantido pela separação de schemas
- Risco: um desenvolvedor com acesso ao servidor pode ler todos os schemas
  (mitigado pela criptografia dos dados sensíveis)
- Mais adequado para: aplicações financeiras, apps regulamentados pela LGPD

### Opção 3 — Database-per-tenant

Uma instância ou servidor de banco de dados por cliente.

- Arquitetura usada por: apps médicos, defesa, grandes empresas
- Isolamento: máximo — cada cliente tem seu próprio banco de dados
- Risco: alto custo e complexidade operacional
- Mais adequado para: empresas de segurança, clientes com requisito
  contratuais de isolamento

## Decisão

A ser decidida. Preferência atual: Opção 2.

## Argumentos

Menos custosa e complexa do que a Opção 3, com um bom nível de isolamento
(estrutural por separação de schemas).

## Consequências

A analisar.

## Decisões Relacionadas

- ADR 001 — Streamlit para o dashboard MVP
- ADR 003 — SQLModel como ORM
