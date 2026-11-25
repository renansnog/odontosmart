# Descrição técnica do software

| Campo | Informação |
|---|---|
| Software | OdontoSmart |
| Versão | 1.0.0 (MVP) |
| Projeto original | Renan Silva Nogueira |
| Validação | 24 de novembro de 2026 |
| Finalidade | Gestão de cadastros de pacientes e dentistas e de consultas odontológicas |

## Funcionamento

O Flask serve o site institucional e renderiza a área administrativa com templates Jinja. O MySQL armazena administradores, pacientes, dentistas e consultas em tabelas InnoDB. Uma consulta nova vincula um paciente e um dentista. A integridade referencial impede excluir um paciente com consultas vinculadas. Um índice único impede que um dentista tenha duas consultas na mesma data e hora, exceto quando uma delas estiver cancelada.

O painel exibe os totais de pacientes, dentistas e consultas agendadas. A lista de pacientes aceita busca por nome ou CPF e oferece cadastro, edição e exclusão. O módulo de consultas permite agendar, listar, editar, marcar como realizada ou cancelada e excluir. O módulo de dentistas cadastra e lista profissionais pelo nome e CRO.

A área administrativa exige sessão assinada pelo Flask. Os formulários de alteração validam um token contra CSRF. As senhas ficam no MySQL como hash scrypt e as credenciais de banco são carregadas do ambiente. As consultas SQL usam parâmetros e a aplicação acessa o banco com uma conta sem permissões de administração.

## Contribuições

| Origem | Contribuição |
|---|---|
| Desenvolvimento anterior de Renan Silva Nogueira | Site institucional em HTML, CSS e JavaScript, identidade visual, fotos, ampliação da foto da fachada e estrutura original de diretórios. O repositório também já trazia a primeira tela de login, um endpoint Flask de autenticação, scripts Python de acesso ao MySQL e o esquema inicial. O [commit anterior ao MVP](https://github.com/renansnog/odontosmart/commit/5004031eb7618b8d1edc0895b8d690c2f1866db8) registra esse ponto de partida. |
| Desenvolvimento da versão 1.0.0 com auxílio de IA (Codex) | Integração do site ao Flask, correção do botão de contato, substituição do login de protótipo, sessões protegidas, painel, fluxos de pacientes, agenda e cadastro de dentistas. Inclui configuração por ambiente, migração preservando os dados do esquema anterior, execução dos testes e produção da documentação e das capturas. |

## Evidências de funcionamento

Capturas feitas no Chromium durante a execução do Flask com MySQL 8.4.13. Os registros exibidos são fictícios.

| Tela | Evidência |
|---|---|
| Login | [Formulário administrativo](evidencias/01-login.jpg) |
| Painel | [Indicadores de pacientes, consultas e dentistas](evidencias/02-painel.jpg) |
| Pacientes | [Listagem com um cadastro editado durante o teste](evidencias/03-pacientes.jpg) |
| Consultas | [Consulta com paciente, dentista e horário atualizados](evidencias/04-consultas.jpg) |
| Dentistas | [Listagem de profissionais cadastrados](evidencias/05-dentistas.jpg) |

### Resultado dos testes

A validação foi executada localmente com Python 3.12, Flask 3.1.3, MySQL Community Server 8.4.13 e Chromium 156. Os testes funcionais enviaram requisições HTTP à aplicação. A navegação, o formulário de login, a saída e a visualização do painel foram conferidos no Chromium. A instalação no Windows está documentada no README e a validação foi feita em Linux.

| Verificação | Resultado |
|---|---|
| Site institucional | Página, folhas de estilo e fotos servidas pelo Flask. Zoom original da fachada e botão de contato validados no navegador. |
| Autenticação | Login correto, rejeição de senha incorreta, redirecionamento de visitante, rejeição de CSRF inválido e bloqueio após sair. Hash scrypt verificado no MySQL. |
| Pacientes | Cadastro, busca por nome e CPF, edição e exclusão. CPF inválido ou duplicado rejeitado e exclusão com consulta vinculada bloqueada. |
| Consultas | Cadastro, listagem, edição, cancelamento e exclusão. Vínculo inválido e conflito de horário rejeitados. Alteração de CPF refletida na agenda. |
| Dentistas | Cadastro e listagem. CRO duplicado rejeitado. |
| Persistência | Cadastros, alterações e exclusões confirmados após reiniciar o Flask e autenticar novamente. |
| Migração | Estrutura anterior migrada em banco isolado. Vínculo único recuperado e vínculos antigos ambíguos preservados para revisão. |

Consulte também o [registro da execução](evidencias/validacao.txt).

## Validação automatizada local — 25/11/2026

No Windows, com Python 3.14.7 e Pytest 9.2.0, o responsável executou `python -m pytest -v`: **10 passed in 4.97s**. O acesso ao painel administrativo também foi confirmado manualmente no navegador. A suíte `test_clinica.py` verifica site, MySQL, autenticação, controle de acesso, CSRF, pacientes, dentistas, consultas e conflitos de horário.

Para reproduzir no PowerShell, em banco de demonstração:

```powershell
.\.venv\Scripts\python.exe -m pip install pytest
.\.venv\Scripts\python.exe -m pytest -v
```

A evidência é a execução local registrada pelo responsável. Não constitui auditoria de segurança, conformidade LGPD ou homologação para produção. Utilize dados fictícios e renove credenciais expostas antes de qualquer implantação.

## Evolução da identidade

O projeto passou a utilizar a marca OdontoSmart em 25/11/2026, preservando a origem histórica na Clínica O’Blanco. A validação registrada acima antecede a mudança de marca.

## Revalidação da mudança de nome — 25/11/2026

O responsável registrou **10 testes aprovados em 5,60 s** após a primeira alteração de nome. Após a atualização visual posterior, confirmou o funcionamento no navegador; a suíte ainda precisa ser reexecutada nessa revisão final. Os registros anteriores permanecem como evidência histórica.

## Publicação da versão 1.0.0

[Release v1.0.0](https://github.com/renansnog/odontosmart/releases/tag/v1.0.0) — publicação como pre-release confirmada pelo responsável em 25/11/2026. MVP de demonstração local, não homologado para produção.
