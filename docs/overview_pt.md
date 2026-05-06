# Lokahi — Visão Geral do Projeto

## O que é o Lokahi

Lokahi é uma aplicação de gestão de coliving para o mercado brasileiro.
Permite que prestadores de serviço, imobiliárias e proprietários gerenciem
seus imóveis, quartos e inquilinos em um único lugar.

---

## Usuários

Por enquanto, apenas **gestores e proprietários** utilizam a aplicação.
Um mesmo login pode representar uma imobiliária com vários colaboradores.

---

## Funcionalidades

### MVP (dashboard Streamlit — fase atual)

- Cadastro de proprietários, gestores, imóveis, quartos e inquilinos
- Importação de dados via CSV ou Excel (completo ou parcial)
- Visualização de tabelas e gráficos básicos
- Sem autenticação — uso interno para testes e análise de dados

### Aplicação completa (fase futura)

- Autenticação por conta
- Uma conta pode ter vários usuários
- Geração de **boletos de cobrança** para pagamento de aluguel
- Conta bancária vinculada a cada proprietário e gestor
- Histórico completo de inquilinos
- API REST (FastAPI) com frontend dedicado

---

## Modelo de Dados

```text
GESTOR (pessoa — proprietário ou gestor de imóvel)
└── id, nome, cpf/cnpj, telefone
└── [futuro] conta_bancaria_id*
└── [futuro] address_id*
└── boletos gerados em seu nome via conta bancária

ADDRESS [futuro — a criar com ViaCEP]
└── id, cep, logradouro, numero, complemento, bairro, cidade, estado

IMÓVEL
└── id, nome, address_id*
└── vinculado a um ou mais gestores (many-to-many)
└── [futuro — a decidir] papel na ligação: proprietario | gestor
└── tem vários quartos

QUARTO
└── pertence a um imóvel
└── tem um inquilino ativo por vez

INQUILINO
└── ocupa um quarto
└── histórico mantido (data de entrada, data de saída, status)
```

---

## Arquitetura Multi-Tenant

A aplicação é **multi-tenant** : um único deploy serve todas as contas,
mas os dados de cada conta são completamente isolados.

Cada conta possui seu próprio banco de dados isolado :

- **MVP** : um arquivo SQLite por conta
- **Produção** : um schema PostgreSQL por conta

Isso garante que uma conta nunca acesse os dados de outra,
mesmo em caso de bug na aplicação.

---

## Segurança e Conformidade

### Por que a segurança é crítica

A aplicação gerencia dados pessoais (CPF, telefone, histórico de moradia)
e dados financeiros (valores de aluguel, boletos).
A **LGPD** (Lei Geral de Proteção de Dados) torna a proteção desses dados
uma obrigação legal no Brasil.

### O que protegemos

| Dado | Sensibilidade | Motivo |
| --- | --- | --- |
| CPF | Alta | Dado pessoal — LGPD |
| Conta bancária | Alta | Dado financeiro |
| Histórico de inquilino | Média | Dado pessoal — LGPD |
| Valor do aluguel | Média | Dado financeiro |

### Como protegemos (produção)

- **Isolamento estrutural** — schema separado por conta
  (impossível vazar entre contas)
- **Criptografia em repouso** — os arquivos do banco são ilegíveis
  sem a chave de criptografia, mesmo que alguém roube o servidor
- **Gestão de chaves (KMS)** — AWS KMS ou Google Cloud KMS
  gerenciam as chaves de criptografia de forma segura
- **RBAC** — apenas papéis autorizados têm acesso à produção
- **Logs de auditoria** — toda consulta em produção é registrada
- **Staging anonimizado** — desenvolvedores nunca trabalham com dados reais

---

## Glossário

| Termo | Definição |
| --- | --- |
| **Boleto de cobrança** | Documento de pagamento bancário brasileiro |
| **LGPD** | Lei Geral de Proteção de Dados — equivalente ao GDPR europeu |
| **Multi-tenant** | Uma única instalação serve vários clientes isolados |
| **Schema-per-tenant** | Cada cliente tem seu próprio conjunto de tabelas |
| **Criptografia em repouso** | Dados criptografados quando armazenados |
| **KMS** | Key Management Service — gestão de chaves de criptografia |
| **ORM** | Object-Relational Mapper — camada Python que abstrai o banco |
| **MVP** | Minimum Viable Product — versão mínima funcional para testes |
