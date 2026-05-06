# ADR 001 — Streamlit para o Dashboard MVP

## Status

Aceito

## Contexto

A aplicação final terá um backend e um frontend dedicados, mas precisamos primeiro
de um **dashboard** para validar o modelo de dados, testar importações e analisar
os primeiros conjuntos de dados reais.compartilhar

Precisamos:

- Criar e gerenciar entidades via formulários (proprietários, gestores, imóveis,
  quartos, inquilinos)
- Importar arquivos CSV e Excel
- Exibir gráficos e tabelas básicos

## Decisão

Usar o Streamlit para o dashboard MVP.

## Argumentos

Escolhemos o Streamlit porque:

- tudo é escrito em Python — sem necessidade de conhecimento de frontend
- é fácil de iniciar e de fazer o deploy (Streamlit Community Cloud, plano gratuito)
- formulários, gráficos e tabelas exigem poucas linhas de código
- permite compartilhar uma URL ao vivo com usuários não técnicos para testes

## Consequências

- **Compromisso aceito:** o Streamlit é uma ferramenta temporária. Quando a aplicação
  real for construída, este dashboard será substituído por um frontend dedicado.
  A lógica de negócios em Python (modelos, utilitários de importação) será reutilizada;
  as páginas Streamlit não serão.
- **Limitação:** o Streamlit não é adequado para interações complexas com o usuário
  ou sessões multiusuário com autenticação.

## Decisões Relacionadas

- ADR 002 — Estratégia de isolamento de banco de dados
- ADR 003 — SQLModel como ORM
