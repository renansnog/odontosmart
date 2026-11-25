import os
import re
from datetime import timedelta
from secrets import compare_digest, token_hex

import click
from flask import (
    Flask, abort, g, redirect, render_template, request,
    send_from_directory, session, url_for,
)
from mysql.connector import Error, IntegrityError, errorcode
from werkzeug.security import check_password_hash, generate_password_hash

from conexao import RAIZ, fechar_banco
from crud import buscar, gravar, listar_consultas, listar_dentistas, listar_pacientes
from gestao import gestao

app = Flask(__name__, template_folder=str(RAIZ / "2_ADM"), static_folder=None)
chave = os.environ.get("SECRET_KEY", "")
if len(chave) < 32:
    raise RuntimeError("Configure SECRET_KEY com pelo menos 32 caracteres no .env.")

app.config.update(
    SECRET_KEY=chave,
    SESSION_COOKIE_NAME="oblanco_admin",
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SAMESITE="Lax",
    SESSION_COOKIE_SECURE=os.environ.get("SESSION_COOKIE_SECURE") == "1",
    PERMANENT_SESSION_LIFETIME=timedelta(hours=8),
    SESSION_REFRESH_EACH_REQUEST=False,
    MAX_CONTENT_LENGTH=64 * 1024,
)
app.teardown_appcontext(fechar_banco)
app.register_blueprint(gestao)
HASH_INATIVO = generate_password_hash(token_hex(32))


@app.context_processor
def contexto():
    def csrf_token():
        if "csrf" not in session:
            session["csrf"] = token_hex(32)
        return session["csrf"]

    return {"csrf_token": csrf_token}


@app.template_filter()
def data_br(valor):
    return valor.strftime("%d/%m/%Y") if valor else "—"


@app.template_filter()
def hora(valor):
    horas, minutos = divmod(int(valor.total_seconds()) // 60, 60)
    return f"{horas:02d}:{minutos:02d}"


@app.before_request
def proteger_area_administrativa():
    if request.path != "/admin" and not request.path.startswith("/admin/"):
        return None
    if request.endpoint in {"login", "css_admin"}:
        if request.method == "GET":
            return None
    elif "admin_id" not in session:
        return redirect(url_for("login"))

    if request.method == "POST":
        esperado = session.get("csrf")
        recebido = request.form.get("csrf", "")
        if not esperado or not compare_digest(esperado.encode("ascii"), recebido.encode("utf-8")):
            abort(400, description="Formulário expirado. Atualize a página e tente novamente.")

    if request.endpoint != "login":
        g.admin = buscar(
            "SELECT id, username, nome FROM administradores WHERE id = %s",
            (session["admin_id"],),
        )
        if g.admin is None:
            session.clear()
            return redirect(url_for("login"))
    return None


@app.after_request
def cabecalhos(resposta):
    resposta.headers["X-Content-Type-Options"] = "nosniff"
    if request.path == "/admin" or request.path.startswith("/admin/"):
        resposta.headers["Cache-Control"] = "no-store"
        resposta.headers["X-Frame-Options"] = "DENY"
        resposta.headers["Content-Security-Policy"] = (
            "default-src 'self'; form-action 'self'; frame-ancestors 'none'; base-uri 'none'"
        )
    return resposta


@app.errorhandler(Error)
def erro_banco(erro):
    app.logger.error("Falha MySQL (%s, código %s)", type(erro).__name__, erro.errno)
    return render_template("erro.html", mensagem="Banco indisponível. Tente novamente."), 503


@app.get("/")
def institucional():
    return send_from_directory(RAIZ / "1_FRONTEND", "index.html")


@app.get("/css/<path:arquivo>")
def css_publico(arquivo):
    return send_from_directory(RAIZ / "1_FRONTEND" / "css", arquivo)


@app.get("/img/<path:arquivo>")
def imagens_publicas(arquivo):
    return send_from_directory(RAIZ / "1_FRONTEND" / "img", arquivo)


@app.get("/admin/css/<path:arquivo>")
def css_admin(arquivo):
    return send_from_directory(RAIZ / "2_ADM" / "css", arquivo)


@app.route("/admin/login", methods=["GET", "POST"])
def login():
    if request.method == "GET":
        return render_template("login.html")
    usuario = request.form.get("username", "").strip()
    senha = request.form.get("password", "")
    if not usuario or len(usuario) > 50 or not 12 <= len(senha) <= 256:
        return render_template("login.html", erro="Usuário ou senha inválidos."), 401
    admin = buscar(
        "SELECT id, password_hash FROM administradores WHERE username = %s", (usuario,)
    )
    senha_valida = check_password_hash(admin["password_hash"] if admin else HASH_INATIVO, senha)
    if admin is None or not senha_valida:
        return render_template("login.html", erro="Usuário ou senha inválidos."), 401
    session.clear()
    session.permanent = True
    session["admin_id"] = admin["id"]
    return redirect(url_for("painel"), code=303)


@app.post("/admin/sair")
def sair():
    session.clear()
    return redirect(url_for("login"), code=303)


@app.get("/admin")
@app.get("/admin/")
def painel():
    totais = buscar(
        "SELECT (SELECT COUNT(*) FROM pacientes) AS pacientes, "
        "(SELECT COUNT(*) FROM consultas WHERE status = 'Agendada') AS consultas, "
        "(SELECT COUNT(*) FROM dentistas) AS dentistas"
    )
    return render_template("dashboard.html", totais=totais)


@app.cli.command("criar-admin")
@click.argument("usuario")
@click.option("--nome", prompt="Nome")
@click.password_option("--senha", prompt="Senha")
def criar_admin(usuario, nome, senha):
    """Cadastra um administrador com senha armazenada em hash."""
    if not re.fullmatch(r"[A-Za-z0-9_.-]{3,50}", usuario) or not nome.strip() or len(nome) > 100:
        raise click.ClickException("Informe um usuário válido (3 a 50 caracteres) e um nome.")
    if not 12 <= len(senha) <= 256:
        raise click.ClickException("Use uma senha com 12 a 256 caracteres.")
    try:
        gravar(
            "INSERT INTO administradores (username, password_hash, nome) VALUES (%s, %s, %s)",
            (usuario, generate_password_hash(senha), nome.strip()),
        )
    except IntegrityError as erro:
        if erro.errno != errorcode.ER_DUP_ENTRY:
            raise
        raise click.ClickException("Já existe um administrador com esse usuário.") from None
    click.echo("Administrador cadastrado.")
