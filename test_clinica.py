"""Testes locais com registros fictícios exclusivos e limpeza ao final."""
import sys
from pathlib import Path
from uuid import uuid4
import pytest
from werkzeug.security import generate_password_hash

sys.path.insert(0, str(Path(__file__).resolve().parent / "3_BACKEND"))
from app import app
from crud import buscar, gravar

@pytest.fixture
def client():
    return app.test_client()

def post(client, path, data=None):
    with client.session_transaction() as session:
        token = session["csrf"]
    return client.post(path, data={**(data or {}), "csrf": token})

@pytest.fixture
def dados(client):
    tag = uuid4().hex
    cpf = str(int(tag[:12], 16) % 10**11).zfill(11)
    user = "teste_" + tag
    cro = "TEST-" + tag[:16]
    senha = uuid4().hex
    with app.app_context():
        assert buscar("SELECT id_CPF FROM pacientes WHERE id_CPF=%s", (cpf,)) is None
        gravar("INSERT INTO administradores (username,nome,password_hash) VALUES (%s,%s,%s)", (user,"Teste ficticio",generate_password_hash(senha)))
    try:
        client.get("/admin/login")
        yield client, user, senha, cpf, cro
    finally:
        with app.app_context():
            gravar("DELETE FROM consultas WHERE paciente_cpf=%s AND dentista_id IN (SELECT id FROM dentistas WHERE cro=%s)", (cpf,cro))
            gravar("DELETE FROM pacientes WHERE id_CPF=%s AND nome LIKE %s", (cpf,"Teste ficticio%"))
            gravar("DELETE FROM dentistas WHERE cro=%s", (cro,))
            gravar("DELETE FROM administradores WHERE username=%s", (user,))

def login(dados):
    c,u,s,_,_ = dados
    assert post(c,"/admin/login",{"username":u,"password":s}).status_code == 303
    assert c.get("/admin/").status_code == 200
    return c

def paciente(c,cpf,nome="Teste ficticio"):
    return post(c,"/admin/pacientes/novo",{"id_CPF":cpf,"nome":nome,"pcd":"Não"})

def test_site(client):
    assert client.get("/").status_code == 200

def test_mysql():
    with app.app_context():
        assert buscar("SELECT 1 AS ok")["ok"] == 1

def test_acesso_protegido(client):
    assert client.get("/admin/pacientes").status_code == 302

def test_login_invalido(dados):
    c,u,_,_,_ = dados
    assert post(c,"/admin/login",{"username":u,"password":"senha-incorreta-123"}).status_code == 401

def test_login_logout(dados):
    c = login(dados)
    assert post(c,"/admin/sair").status_code == 303
    assert c.get("/admin/").status_code == 302

def test_csrf(dados):
    c = login(dados)
    assert c.post("/admin/dentistas",data={}).status_code == 400

def test_crud_paciente(dados):
    c = login(dados)
    cpf = dados[3]
    assert paciente(c,cpf).status_code == 303
    assert cpf.encode() in c.get("/admin/pacientes?q="+cpf).data
    assert paciente(c,cpf).status_code == 409
    assert post(c,f"/admin/pacientes/{cpf}/editar",{"id_CPF":cpf,"nome":"Teste ficticio editado","pcd":"Não"}).status_code == 303
    with app.app_context():
        assert buscar("SELECT nome FROM pacientes WHERE id_CPF=%s",(cpf,))["nome"] == "Teste ficticio editado"
    assert post(c,f"/admin/pacientes/{cpf}/excluir").status_code == 303
    with app.app_context():
        assert buscar("SELECT nome FROM pacientes WHERE id_CPF=%s",(cpf,)) is None

def test_paciente_invalido(dados):
    c = login(dados)
    assert paciente(c,"123").status_code == 422

def test_dentista(dados):
    c = login(dados)
    cro = dados[4].upper()
    campos = {"nome":"Teste ficticio dentista","cro":cro}
    assert post(c,"/admin/dentistas",campos).status_code == 303
    assert cro.encode() in c.get("/admin/dentistas").data
    assert post(c,"/admin/dentistas",campos).status_code == 409

def test_crud_consulta(dados):
    c = login(dados)
    cpf,cro = dados[3:]
    assert paciente(c,cpf).status_code == 303
    assert post(c,"/admin/dentistas",{"nome":"Teste ficticio dentista","cro":cro}).status_code == 303
    with app.app_context():
        dentista = buscar("SELECT id FROM dentistas WHERE cro=%s",(cro,))["id"]
    campos = {"paciente_cpf":cpf,"dentista_id":str(dentista),"data_consulta":"2030-01-15","horario":"09:00","descricao":"Teste ficticio consulta","status":"Agendada"}
    assert post(c,"/admin/consultas/nova",campos).status_code == 303
    assert b"Teste ficticio" in c.get("/admin/consultas").data
    assert post(c,"/admin/consultas/nova",campos).status_code == 409
    with app.app_context():
        cid = buscar("SELECT id_Consulta FROM consultas WHERE paciente_cpf=%s AND dentista_id=%s",(cpf,dentista))["id_Consulta"]
    assert post(c,f"/admin/consultas/{cid}/editar",{**campos,"status":"Realizada"}).status_code == 303
    with app.app_context():
        assert buscar("SELECT status FROM consultas WHERE id_Consulta=%s",(cid,))["status"] == "Realizada"
    assert post(c,f"/admin/consultas/{cid}/excluir").status_code == 303
    with app.app_context():
        assert buscar("SELECT id_Consulta FROM consultas WHERE id_Consulta=%s",(cid,)) is None
