import os
from pathlib import Path

import mysql.connector
from dotenv import load_dotenv
from flask import g
from mysql.connector.constants import ClientFlag

RAIZ = Path(__file__).resolve().parent.parent
load_dotenv(RAIZ / ".env")


def conectar():
    return mysql.connector.connect(
        host=os.environ.get("DB_HOST", "127.0.0.1"),
        port=int(os.environ.get("DB_PORT", "3306")),
        user=os.environ["DB_USER"],
        password=os.environ["DB_PASSWORD"],
        database=os.environ.get("DB_NAME", "clinica_oblanco"),
        charset="utf8mb4",
        client_flags=[ClientFlag.FOUND_ROWS],
        connection_timeout=5,
    )


def banco():
    if "banco" not in g:
        g.banco = conectar()
    return g.banco


def fechar_banco(_erro=None):
    conexao = g.pop("banco", None)
    if conexao is not None:
        conexao.close()
