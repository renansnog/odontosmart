import re
from datetime import date, datetime

from flask import Blueprint, abort, flash, redirect, render_template, request, url_for
from mysql.connector import IntegrityError, errorcode

from crud import buscar, gravar, listar_consultas, listar_dentistas, listar_pacientes

gestao = Blueprint("gestao", __name__, url_prefix="/admin")
STATUS = ("Agendada", "Realizada", "Cancelada")


def campos(*nomes):
    return {nome: request.form.get(nome, "").strip() for nome in nomes}


def registro(sql, chave):
    resultado = buscar(sql, (chave,))
    if resultado is None:
        abort(404)
    return resultado


@gestao.get("/pacientes")
def pacientes():
    termo = request.args.get("q", "").strip()[:100]
    return render_template("pacientes.html", pacientes=listar_pacientes(termo), termo=termo)


@gestao.route("/pacientes/novo", defaults={"cpf": None}, methods=["GET", "POST"])
@gestao.route("/pacientes/<cpf>/editar", methods=["GET", "POST"])
def paciente_form(cpf):
    dados = registro("SELECT * FROM pacientes WHERE id_CPF = %s", cpf) if cpf else {}
    if request.method == "GET":
        return render_template("paciente_form.html", dados=dados, cpf=cpf)

    dados = campos("id_CPF", "nome", "endereco", "telefone", "data_de_nascimento", "pcd")
    dados["id_CPF"] = re.sub(r"[.\-\s]", "", dados["id_CPF"])
    try:
        if not re.fullmatch(r"[0-9]{11}", dados["id_CPF"]):
            raise ValueError("Informe um CPF com 11 dígitos.")
        if not dados["nome"] or len(dados["nome"]) > 100:
            raise ValueError("Informe um nome com até 100 caracteres.")
        if len(dados["endereco"]) > 255 or len(dados["telefone"]) > 20:
            raise ValueError("Revise o tamanho do endereço e do telefone.")
        if dados["pcd"] not in ("Sim", "Não"):
            raise ValueError("Informe se o paciente é PCD.")
        nascimento = dados["data_de_nascimento"]
        if nascimento:
            try:
                nascimento = date.fromisoformat(nascimento)
            except ValueError:
                raise ValueError("Informe uma data de nascimento válida.") from None
            if not date(1000, 1, 1) <= nascimento <= date.today():
                raise ValueError("Informe uma data de nascimento válida.")

        valores = (
            dados["id_CPF"], dados["nome"], dados["endereco"] or None,
            dados["telefone"] or None, nascimento or None, dados["pcd"],
        )
        if cpf:
            alterados = gravar(
                "UPDATE pacientes SET id_CPF=%s, nome=%s, endereco=%s, telefone=%s, "
                "data_de_nascimento=%s, pcd=%s WHERE id_CPF=%s",
                (*valores, cpf),
            )
            if not alterados:
                abort(404)
        else:
            gravar(
                "INSERT INTO pacientes (id_CPF, nome, endereco, telefone, "
                "data_de_nascimento, pcd) VALUES (%s, %s, %s, %s, %s, %s)",
                valores,
            )
    except ValueError as erro:
        return render_template("paciente_form.html", dados=dados, cpf=cpf, erro=str(erro)), 422
    except IntegrityError as erro:
        if erro.errno != errorcode.ER_DUP_ENTRY:
            raise
        return render_template(
            "paciente_form.html", dados=dados, cpf=cpf, erro="Já existe um paciente com esse CPF."
        ), 409
    flash("Paciente atualizado." if cpf else "Paciente cadastrado.")
    return redirect(url_for("gestao.pacientes"), code=303)


@gestao.post("/pacientes/<cpf>/excluir")
def excluir_paciente(cpf):
    try:
        if not gravar("DELETE FROM pacientes WHERE id_CPF = %s", (cpf,)):
            abort(404)
        flash("Paciente excluído.")
    except IntegrityError as erro:
        if erro.errno != errorcode.ER_ROW_IS_REFERENCED_2:
            raise
        flash("O paciente possui consultas vinculadas. Resolva os vínculos antes de excluir.", "erro")
    return redirect(url_for("gestao.pacientes"), code=303)


@gestao.get("/consultas")
def consultas():
    return render_template("consultas.html", consultas=listar_consultas())


@gestao.route("/consultas/nova", defaults={"consulta_id": None}, methods=["GET", "POST"])
@gestao.route("/consultas/<int:consulta_id>/editar", methods=["GET", "POST"])
def consulta_form(consulta_id):
    dados = registro("SELECT * FROM consultas WHERE id_Consulta = %s", consulta_id) if consulta_id is not None else {}
    if request.method == "GET":
        return render_template(
            "consulta_form.html", dados=dados, consulta_id=consulta_id,
            pacientes=listar_pacientes(), dentistas=listar_dentistas(), status=STATUS,
        )

    dados = campos("paciente_cpf", "dentista_id", "data_consulta", "horario", "descricao", "status")
    try:
        if not re.fullmatch(r"[0-9]{11}", dados["paciente_cpf"]):
            raise ValueError("Selecione um paciente.")
        if not re.fullmatch(r"[1-9][0-9]{0,9}", dados["dentista_id"]) or int(dados["dentista_id"]) > 2147483647:
            raise ValueError("Selecione um dentista.")
        if dados["status"] not in STATUS or len(dados["descricao"]) > 1000:
            raise ValueError("Revise a situação da consulta e use até 1.000 caracteres na descrição.")
        try:
            inicio = datetime.strptime(
                f'{dados["data_consulta"]} {dados["horario"]}', "%Y-%m-%d %H:%M"
            )
            if inicio.year < 1000:
                raise ValueError
        except ValueError:
            raise ValueError("Informe uma data e um horário válidos.") from None

        valores = (
            dados["paciente_cpf"], int(dados["dentista_id"]), inicio.date(),
            inicio.time(), dados["descricao"] or None, dados["status"],
        )
        if consulta_id:
            alterados = gravar(
                "UPDATE consultas SET paciente_cpf=%s, dentista_id=%s, data_consulta=%s, "
                "horario=%s, descricao=%s, status=%s WHERE id_Consulta=%s",
                (*valores, consulta_id),
            )
            if not alterados:
                abort(404)
        else:
            gravar(
                "INSERT INTO consultas (paciente_cpf, dentista_id, data_consulta, horario, "
                "descricao, status) VALUES (%s, %s, %s, %s, %s, %s)",
                valores,
            )
    except ValueError as excecao:
        erro, codigo = str(excecao), 422
    except IntegrityError as excecao:
        if excecao.errno == errorcode.ER_DUP_ENTRY:
            erro, codigo = "O dentista já tem uma consulta nesse horário.", 409
        elif excecao.errno == errorcode.ER_NO_REFERENCED_ROW_2:
            erro, codigo = "Selecione um paciente e um dentista cadastrados.", 422
        else:
            raise
    else:
        flash("Consulta atualizada." if consulta_id else "Consulta cadastrada.")
        return redirect(url_for("gestao.consultas"), code=303)

    return render_template(
        "consulta_form.html", dados=dados, consulta_id=consulta_id, erro=erro,
        pacientes=listar_pacientes(), dentistas=listar_dentistas(), status=STATUS,
    ), codigo


@gestao.post("/consultas/<int:consulta_id>/excluir")
def excluir_consulta(consulta_id):
    if not gravar("DELETE FROM consultas WHERE id_Consulta = %s", (consulta_id,)):
        abort(404)
    flash("Consulta excluída.")
    return redirect(url_for("gestao.consultas"), code=303)


@gestao.route("/dentistas", methods=["GET", "POST"])
def dentistas():
    dados = {}
    if request.method == "GET":
        return render_template("dentistas.html", dentistas=listar_dentistas(), dados=dados)

    dados = campos("nome", "cro")
    dados["cro"] = dados["cro"].upper()
    if not dados["nome"] or len(dados["nome"]) > 100 or not re.fullmatch(r"[A-Z0-9][A-Z0-9 /.-]{2,29}", dados["cro"]):
        return render_template(
            "dentistas.html", dentistas=listar_dentistas(), dados=dados,
            erro="Informe o nome e o CRO do dentista.",
        ), 422
    try:
        gravar("INSERT INTO dentistas (nome, cro) VALUES (%s, %s)", (dados["nome"], dados["cro"]))
    except IntegrityError as erro:
        if erro.errno != errorcode.ER_DUP_ENTRY:
            raise
        return render_template(
            "dentistas.html", dentistas=listar_dentistas(), dados=dados,
            erro="Já existe um dentista com esse CRO.",
        ), 409
    flash("Dentista cadastrado.")
    return redirect(url_for("gestao.dentistas"), code=303)
