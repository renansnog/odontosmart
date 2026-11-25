# OdontoSmart — Sistema Web de Gestão Odontológica

Sistema web de gestão odontológica, versão **1.0.0 (MVP)**, com site institucional e área administrativa para o gerenciamento de pacientes, consultas e dentistas. Projeto de portfólio desenvolvido por **Renan Silva Nogueira**. Use exclusivamente dados fictícios na demonstração.

## Funcionalidades

- Site institucional com a identidade visual, as fotos e as seções do projeto original.
- Login e saída administrativos, senha armazenada como hash e formulários protegidos contra CSRF.
- Cadastro, busca por nome ou CPF, edição e exclusão de pacientes. A exclusão exige resolver primeiro as consultas vinculadas.
- Cadastro, listagem, edição e exclusão de consultas, vinculadas a paciente e dentista. A situação pode ser agendada, realizada ou cancelada. O sistema impede consultas ativas para o mesmo dentista na mesma data e hora.
- Cadastro e listagem de dentistas e prevenção de CRO duplicado.
- Painel com totais de pacientes, consultas agendadas e dentistas.

## Tecnologias e arquitetura

HTML, CSS e JavaScript no site, HTML gerado com Jinja na administração, Python e Flask no servidor e MySQL 8.4 com InnoDB para persistência. MySQL Connector/Python faz a conexão e parametriza as consultas SQL. Git e GitHub registram as alterações.

| Pasta | Responsabilidade |
|---|---|
| `1_FRONTEND` | Site institucional, estilos e fotografias servidos pelo Flask |
| `2_ADM` | Páginas administrativas renderizadas pelo Flask |
| `3_BACKEND` | Rotas, autenticação, regras de cadastro e acesso ao banco |
| `4_DATABASE` | Estrutura inicial do MySQL e migração da estrutura anterior |
| `docs` | Descrição técnica, autoria das contribuições e evidências |

## Executar no Windows

Pré-requisitos: Git, Python 3.12 e MySQL Server 8.4 em execução. O MySQL Workbench é opcional.

1. Clone o repositório e instale as dependências no PowerShell.

   ```powershell
   git clone https://github.com/renansnog/clinica_oblanco.git
   cd clinica_oblanco
   py -3.12 -m venv .venv
   .\.venv\Scripts\python.exe -m pip install -r requirements.txt
   Copy-Item .env.example .env
   .\.venv\Scripts\python.exe -c "import secrets; print(secrets.token_hex(32))"
   ```

2. Em uma instalação nova, abra e execute todo o arquivo `4_DATABASE/schema.sql` no Workbench com um usuário administrador. Na mesma conexão, execute os comandos abaixo e substitua o texto entre aspas por uma senha exclusiva para a aplicação. Se já tiver a estrutura anterior do projeto, siga a seção de migração.

   ```sql
   CREATE USER 'oblanco_app'@'127.0.0.1' IDENTIFIED BY 'SUBSTITUA_POR_UMA_SENHA_FORTE';
   GRANT SELECT, INSERT, UPDATE, DELETE ON clinica_oblanco.*
       TO 'oblanco_app'@'127.0.0.1';
   ```

3. Abra `.env` e cole a chave gerada no passo 1 em `SECRET_KEY`. Preencha `DB_PASSWORD` com a senha da conta MySQL criada no passo 2. Ajuste `DB_PORT` se o servidor usar uma porta diferente de 3306. Use `SESSION_COOKIE_SECURE=0` para acesso local via HTTP.

4. Cadastre o administrador e inicie o Flask. Informe um nome e uma senha de pelo menos 12 caracteres quando solicitado.

   ```powershell
   .\.venv\Scripts\python.exe -m flask --app 3_BACKEND/app.py criar-admin adm.local
   .\.venv\Scripts\python.exe -m flask --app 3_BACKEND/app.py run
   ```

5. Abra o [site institucional](http://127.0.0.1:5000/) ou o [login administrativo](http://127.0.0.1:5000/admin/). Para testar uma consulta, cadastre um paciente e um dentista fictícios primeiro. Exemplos: `Paciente Demonstração`, CPF fictício `00000000001`, e `Dentista Demonstração`, CRO fictício `DEMO-001`.

No Linux ou macOS, use `python3.12 -m venv .venv`, `cp .env.example .env` e `.venv/bin/python` nos comandos Python. Se preferir o terminal ao Workbench, execute o schema com `mysql -u root -p < 4_DATABASE/schema.sql` em um shell com redirecionamento de entrada.

### Migrar a estrutura anterior

Faça backup, pare o aplicativo e execute **uma vez** `4_DATABASE/migrar_0_para_1.sql` em vez de `schema.sql`. A migração preserva os registros existentes e recupera o vínculo das consultas com um único paciente no modelo antigo. Se a mesma consulta tinha múltiplos pacientes, o vínculo anterior fica disponível na coluna `pacientes.id_Consulta` para revisão. Complete o dentista e os vínculos pendentes no painel. Provisione uma nova conta administrativa e troque ou revogue qualquer credencial anterior ainda em uso, inclusive a da conexão MySQL do protótipo.

## Documentação comprobatória

Consulte [a descrição técnica e as evidências](docs/descricao-tecnica.md).

## Validação automatizada local — 25/11/2026

No Windows, com Python 3.14.7 e Pytest 9.2.0, o responsável executou `python -m pytest -v`: **10 passed in 4.97s**. O acesso ao painel administrativo também foi confirmado manualmente no navegador. A suíte `test_clinica.py` verifica site, MySQL, autenticação, controle de acesso, CSRF, pacientes, dentistas, consultas e conflitos de horário.

Para reproduzir no PowerShell, em banco de demonstração:

```powershell
.\.venv\Scripts\python.exe -m pip install pytest
.\.venv\Scripts\python.exe -m pytest -v
```

A evidência é a execução local registrada pelo responsável. Não constitui auditoria de segurança, conformidade LGPD ou homologação para produção. Utilize dados fictícios e renove credenciais expostas antes de qualquer implantação.

## Identidade do projeto

OdontoSmart é o novo nome do projeto originalmente desenvolvido como Clínica O’Blanco. O nome técnico do banco, a pasta e a URL do repositório permanecem inalterados para preservar a compatibilidade. A validação anterior antecede a mudança de marca; execute novamente a suíte após atualizar o projeto.
