from conexao import banco


def consultar(sql, parametros=()):
    with banco().cursor(dictionary=True) as cursor:
        cursor.execute(sql, parametros)
        return cursor.fetchall()


def buscar(sql, parametros=()):
    registros = consultar(sql, parametros)
    return next(iter(registros), None)


def gravar(sql, parametros=()):
    conexao = banco()
    try:
        with conexao.cursor() as cursor:
            cursor.execute(sql, parametros)
            afetados = cursor.rowcount
        conexao.commit()
        return afetados
    except Exception:
        conexao.rollback()
        raise


def listar_pacientes(termo=""):
    return consultar(
        "SELECT * FROM pacientes WHERE LOCATE(%s, nome) > 0 "
        "OR LOCATE(%s, id_CPF) > 0 ORDER BY nome, id_CPF",
        (termo, termo),
    )


def listar_consultas():
    return consultar(
        "SELECT c.*, p.nome AS paciente, d.nome AS dentista "
        "FROM consultas c LEFT JOIN pacientes p ON c.paciente_cpf = p.id_CPF "
        "LEFT JOIN dentistas d ON c.dentista_id = d.id "
        "ORDER BY c.data_consulta DESC, c.horario DESC, c.id_Consulta DESC"
    )


def listar_dentistas():
    return consultar("SELECT id, nome, cro FROM dentistas ORDER BY nome, id")
