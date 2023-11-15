from flask import Flask, jsonify, request
import pyodbc
from flask_pydantic_spec import FlaskPydanticSpec
from flask_cors import CORS

app = Flask(__name__)
spec = FlaskPydanticSpec('flask', title="Endpoints da api de consulta \
                         da Base Nacional Curricular Comum - BNCC")

spec.register(app)
cors = CORS(app, resources={r"/api/*": {"origins": "*"}})

data_for_connection = (
    "Driver={SQL Server Native Client RDA 11.0};"
    "Server=DESKTOP-1698A6Q\SQLEXPRESS;"
    "Database=bncc;"
    "Trusted_connection=YES;"
)

connection = pyodbc.connect(data_for_connection)
cursor = connection.cursor()


@app.route('/diario/aula/registrar', methods=['POST'])
def insert_class():
    obj_cla = request.get_json(force=True)
    id_materia = obj_cla.get('id_materia')
    id_bimestre = obj_cla.get('id_bimestre')
    data_aula = obj_cla.get('data_aula')
    descricao_aula = obj_cla.get('descricao_aula')
    habilidade_bncc = obj_cla.get('habilidade_bncc')
    id_turma = obj_cla.get('id_turma')

    cursor.execute(f"""INSERT INTO tabela_aulas (id_materia, id_bimestre, data_aula, 
                   descricao_aula, habilidade_bncc, id_turma) VALUES ({id_materia}, 
                   {id_bimestre}, {data_aula}, '{descricao_aula}', '{habilidade_bncc}', {id_turma})
                   """)
    cursor.execute(f"SELECT SCOPE_IDENTITY() AS last_insert_id")
    id_aula = cursor.fetchone().last_insert_id
    obj_cla.update({'id_aula': id_aula})
    cursor.commit()

    return jsonify(data=obj_cla, message="Aula inserida com sucesso")


@app.route('/diario/aula/listar/')
def get_classes():
    id_aula = request.values.get("id_aula")
    id_bimestre = request.values.get("id_bimestre")
    id_materia = request.values.get("id_materia")
    id_turma = request.values.get('id_turma')

    if id_aula == None and id_bimestre == None and id_materia == None and id_turma == None:

        db = cursor.execute(f"""SELECT * FROM tabela_aulas""")
        db = db.fetchall()
        db_list = []
        for x in db:
            db_list.append({
                "id_aula": x[0],
                "id_materia": x[1],
                "id_bimestre": x[2],
                "data_aula": x[3],
                "descricao_aula": x[4],
                "habilidade_bncc": x[5]

            })
        return jsonify(data=db_list)
    if id_aula is not None:
        db = cursor.execute(f"""SELECT * FROM tabela_aulas WHERE id_aula = {id_aula}
                            """)
        db = db.fetchone()
        if db is not None:
            resultado = {
                "id_aula": db[0],
                "id_materia": db[1],
                "id_bimestre": db[2],
                "data_aula": db[3],
                "descricao_aula": db[4],
                "habilidade_bncc": db[5]
            }
        print(f"esse é o resultado {resultado}")

        return jsonify(message="Dados da aula solicitada", data=resultado)

    if id_aula is None and id_bimestre is not None and id_materia is not None and id_turma is not None:
        db = cursor.execute(f"""SELECT * from tabela_aulas WHERE id_bimestre = {id_bimestre} and 
                            id_materia = {id_materia} and id_turma {id_turma}
                            """)
        db_list = db.fetchall()
        if len(db_list) > 1:
            db_list = []
            for x in db:
                db_list.append({
                    "id_aula": x[0],
                    "id_materia": x[1],
                    "id_bimestre": x[2],
                    "data_aula": x[3],
                    "descricao_aula": x[4],
                    "habilidade_bncc": x[5]
                })
            return jsonify(data=db_list, message="Todas as aulas retornadas")
        elif len(db_list) == 1:
            resultado = {
                "id_aula": db_list[0][0],
                "id_materia": db_list[0][1],
                "id_bimestre": db_list[0][2],
                "data_aula": db_list[0][3],
                "descricao_aula": db_list[0][4],
                "habilidade_bncc": db_list[0][5]
            }
            return jsonify(data=resultado, message="Apenas 1 aula retornada")


@app.route('/diario/aula/deletar', methods=['DELETE'])
def delete_classes():
    id_aula = request.values('id_aula')
    cursor.execute(f""" DELETE FROM tabela_aulas WHERE id_aula = {id_aula}
                        """)
    cursor.commit()
    return jsonify(message=f"Aula {id_aula} deletada com sucesso")


@app.route('/diario/frequencia/atualizaraula/', methods=["GET", "PUT"])
def update_class():
    id_aula = request.values.get('id_aula')
    try:
        up_obj = request.get_json(force=True)
        up_id_materia = up_obj.get('id_materia')
        up_id_bimestre = up_obj.get('id_bimestre')
        up_data_aula = up_obj.get('data_aula')
        up_descricao_aula = up_obj.get('descricao_aula')
        up_habilidade_bncc = up_obj.get('habilidade_bncc')
        up_id_turma = up_obj.get('id_turma')
    except:
        pass
    cursor.execute(f"""UPDATE tabela_aulas SET id_materia = {up_id_materia},
                   id_bimestre = {up_id_bimestre}, data_aula = '{up_data_aula}',
                   descricao_aula = '{up_descricao_aula}', 
                   habilidade_bncc ='{up_habilidade_bncc}', id_turma = {up_id_turma}
                   WHERE id_aula = {id_aula}
                   """)
    up_obj.update({'id_aula': id_aula})
    cursor.commit()
    return jsonify(message=f"Aula de id = {id_aula} atualizada com sucesso", data=up_obj)


# inserção de frequência na tabela_frequencia a partir daqui
@app.route('/diario/frequencia/inserir', methods=["POST"])
def insert_freq():
    """insere presença para todos de uma turma"""
    payload = request.get_json(force=True)
    id_aula = payload.get('id_aula')
    presente = payload.get('presente')
    db_turma = cursor.execute(f"SELECT id_turma from tabela_aulas WHERE id_aula = {id_aula}")
    db_turma = db_turma.fetchall()
    id_turma = db_turma[0][0]
    db_ids = cursor.execute(f"""SELECT id_aluno FROM tabela_alunos WHERE id_turma = {id_turma}""")
    list_ids = db_ids.fetchall()
    dic_ids = []
    for x in list_ids:
        for y in x:
            dic_ids.append({
                "id_aluno": y
            })
    print(f"esses são os alunos  %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%% {dic_ids}")
    result = []

    id_alunos_adicionados = set()

    for id_aluno in dic_ids:
        if id_aluno["id_aluno"] not in id_alunos_adicionados:
            result.append({
                "id_aluno": id_aluno["id_aluno"],
                "id_aula": id_aula,
                "presente": presente
            })
            id_alunos_adicionados.add(id_aluno["id_aluno"])

    print(f"esse é o result final %%%%%%%%%%$$$$$$$$$$$$$$$$$$$$$$$$$$$$ {result}")
    id_freq_list = []
    for x in result:
        cursor.execute(f"""INSERT INTO tabela_frequencia (id_aluno, id_aula, presente) VALUES (
                           {x['id_aluno']}, {x['id_aula']}, {x['presente']}       
                       ) """)
        cursor.commit()
        cursor.execute(f"SELECT SCOPE_IDENTITY() AS last_insert_id")
        id_freq = cursor.fetchone().last_insert_id
        id_freq_list.append(id_freq)
    id_freq_f = []
    for x in id_freq_list:
        id_freq_f.append({
            "id_frequencia": int(x)
        })
    for i, x in enumerate(result):
        x['id_frequencia'] = id_freq_f[i]['id_frequencia']
        print(f"printando a chave i {i} printando o valor x {x}")

    return jsonify(message="está funcionando", data=result)


@app.route('/diario/frequencia/listar/', methods=['GET'])
def get_frequency():
    id_aula = request.values.get('id_aula')
    db = cursor.execute(f"""SELECT * FROM tabela_frequencia where id_aula = {id_aula}""")
    db = db.fetchall()
    db_list = []
    for x in db:
        db_list.append(
            {
                "id_frequencia": x[0],
                "id_aluno": x[1],
                "id_aula": x[2],
                "presente": x[3]
            }
        )
    return jsonify(data=db_list, message=f"Listagem de frequência da aula de id = {id_aula}")


@app.route('/diario/frequencia/deletar/', methods=['DELETE'])
def delete_frequency():
    id_aula = request.values.get('id_aula')
    cursor.execute(f"""
                   DELETE FROM tabela_frequencia WHERE id_aula = {id_aula}
                   """)
    cursor.commit()


@app.route('/diario/frequencia/atualizar/', methods=['PUT'])
def update_frequency():
    id_aula = request.values.get('id_aula')
    up_obj = request.get_json(force=True)
    up_presente = up_obj.get('presente')
    id_aluno = up_obj.get('id_aluno')

    cursor.execute(f"""UPDATE tabela_frequencia SET presente = {up_presente}
                       WHERE id_aula = {id_aula} and id_aluno = {id_aluno}
                       """)
    cursor.commit()

    return jsonify(message="Tabela frequência atualizada", data=up_obj)


@app.route('/apibncc/<subject>', methods=["GET"])
@app.route('/apibncc/<subject>/<grade>', methods=["GET"])
def list_all(subject, grade=None):
    """Lista todo o currículo por matéria e por ano via path, por matéria e/ou matéria e ano.
Escolha o currículo a ser consultado: \n
bncc_artes_ef \n
bncc_ciencias_ef \n
bncc_educacao_fisica_ef \n
bncc_ensino_religioso_ef \n
bncc_geografia_ef \n
bncc_historia_ef \n
bncc_lingua_inglesa_ef \n
bncc_matematica_ef \n
bncc_lingua_portuguesa_ef \n

Escolha o ano a ser consultado: \n
Ensino fundamental: \n
sexto_ef \n
setimo_ef \n
oitavo_ef \n
nono_ef \n

Ensino Médio:
primeiro_em \n
segundo_em \n
terceiro_em

    """
    try:
        if len(grade) > 0:
            db = cursor.execute(f"SELECT * FROM {subject} where {grade} = 'true'")
            data_get = db.fetchall()
            data_show = []
            if subject == "bncc_lingua_portuguesa_ef":
                pl_list = []
                for x in data_get:
                    pl_list.append({
                        "column1": x[0],
                        "componente": x[1],
                        'ano_faixa': x[2],
                        'campo_atuacao': x[3],
                        'praticas_linguagem': x[4],
                        'objetos_conhecimento': x[5],
                        'habilidades': x[6],
                        'cod_hab': x[7],
                        'descricao_cod': x[8],
                        'primeiro_ef': x[9],
                        'segundo_ef': x[10],
                        'terceiro_ef': x[11],
                        'quarto_ef': x[12],
                        'quinto_ef': x[13],
                        'sexto_ef': x[14],
                        'setimo_ef': x[15],
                        'oitavo_ef': x[16],
                        'nono_ef': x[17]
                    })
                return jsonify(message="Dados solicitados", data=pl_list)
            elif subject == "bncc_lingua_inglesa_ef":
                eng_list = []
                for x in data_get:
                    eng_list.append({
                        'column1': x[0],
                        'componente': x[1],
                        'ano_faixa': x[2],
                        'eixo': x[3],
                        'unidades_tematicas': x[4],
                        'objetos_conhecimento': x[5],
                        'habilidades': x[6],
                        'cod_hab': x[7],
                        'descricao_cod': x[8],
                        'primeiro_ef': x[9],
                        'segundo_ef': x[10],
                        'terceiro_ef': x[11],
                        'quarto_ef': x[12],
                        'quinto_ef': x[13],

                        'sexto_ef': x[14],
                        'setimo_ef': x[15],
                        'oitavo_ef': x[16],
                        'nono_ef': x[17]
                    })
                return jsonify(message="dados", data=eng_list)
            elif subject.endswith("_ef") and subject not in ["bncc_lingua_portuguesa_ef", "bncc_lingua_inglesa_ef"]:
                for x in data_get:
                    data_show.append({
                        'column1': x[0],
                        'componente': x[1],
                        'ano_faixa': x[2],
                        'objetos_conhecimento': x[3],
                        'unidades_tematicas': x[4],
                        'habilidades': x[5],
                        'cod_hab': x[6],
                        'descricao_cod': x[7],
                        'primeiro_ef': x[8],
                        'segundo_ef': x[9],
                        'terceiro_ef': x[10],
                        'quarto_ef': x[11],
                        'quinto_ef': x[12],
                        'sexto_ef': x[13],
                        'setimo_ef': x[14],
                        'oitavo_ef': x[15],
                        'nono_ef': x[16]
                    })
                return jsonify(message="dados", data=data_show)
            elif subject.endswith("_inf") and not subject.startswith("df"):
                inf_list = []
                for x in data_get:
                    inf_list.append({
                        "column1": x[0],
                        "campo_exp": x[1],
                        "faixa_etaria": x[2],
                        "obj": x[3],
                        "cod_apr": x[4],
                        "descricao_cod": x[5],
                        "idade_anos_inicial": x[6],
                        "idade_meses_inicial": x[7],
                        "idade_anos_final": x[8],
                        "idade_meses_final": x[9]

                    })
                return jsonify(message="Esses são os dados solicitados", data=inf_list)
            elif subject == "df_edu_inf":
                df_edu_inf_list = []
                for x in data_get:
                    df_edu_inf_list.append({
                        "column1": x[0],
                        "campo_exp": x[1],
                        "faixa_etaria": x[2],
                        "cod_apr": x[3],
                        "descricao_cod": x[4],
                        "idade_anos_inicial": x[5],
                        "idade_meses_inicial": x[6],
                        "idade_anos_final": x[7],
                        "idade_meses_final": x[8]
                    })
                return jsonify(message="Esses são os dados solicitados do df_edu_inf", data=df_edu_inf_list)
            elif subject.endswith("_em") and not subject.startswith("c"):
                em_list = []
                for x in data_get:
                    em_list.append({
                        'column1': x[0],
                        'ano_faixa': x[1],
                        'cod_hab': x[2],
                        'habilidades': x[3],
                        'primeiro_ano': x[4],
                        'segundo_ano': x[5],
                        'terceiro_ano': x[6],
                        'area': x[7],
                        'competencias_esp': x[8],
                        'campos_atuacao': x[9]
                    })
                return jsonify(message="Dados de df_habilidades_em", data=em_list)
            elif subject.endswith("_em") and subject.startswith("c"):
                em_competencias_list = []
                for x in data_get:
                    em_competencias_list.append({
                        "column1": x[0],
                        "competencias": x[1],
                        "area": x[2]
                    })
                return jsonify(message="Dados solicitados", data=em_competencias_list)
    except:
        if grade == None:
            db = cursor.execute(f"SELECT * FROM {subject}")
            data_get = db.fetchall()
            data_show = []
            if subject == "bncc_lingua_portuguesa_ef":
                pl_list = []
                for x in data_get:
                    pl_list.append({
                        "column1": x[0],
                        "componente": x[1],
                        'ano_faixa': x[2],
                        'campo_atuacao': x[3],
                        'praticas_linguagem': x[4],
                        'objetos_conhecimento': x[5],
                        'habilidades': x[6],
                        'cod_hab': x[7],
                        'descricao_cod': x[8],
                        'primeiro_ef': x[9],
                        'segundo_ef': x[10],
                        'terceiro_ef': x[11],
                        'quarto_ef': x[12],
                        'quinto_ef': x[13],
                        'sexto_ef': x[14],
                        'setimo_ef': x[15],
                        'oitavo_ef': x[16],
                        'nono_ef': x[17]
                    })
                return jsonify(message="Dados solicitados", data=pl_list)
            elif subject == "bncc_lingua_inglesa_ef":
                eng_list = []
                for x in data_get:
                    eng_list.append({
                        'column1': x[0],
                        'componente': x[1],
                        'ano_faixa': x[2],
                        'eixo': x[3],
                        'unidades_tematicas': x[4],
                        'objetos_conhecimento': x[5],
                        'habilidades': x[6],
                        'cod_hab': x[7],
                        'descricao_cod': x[8],
                        'primeiro_ef': x[9],
                        'segundo_ef': x[10],
                        'terceiro_ef': x[11],
                        'quarto_ef': x[12],
                        'quinto_ef': x[13],

                        'sexto_ef': x[14],
                        'setimo_ef': x[15],
                        'oitavo_ef': x[16],
                        'nono_ef': x[17]
                    })
                return jsonify(message="dados", data=eng_list)
            elif subject.endswith("_ef") and subject not in ["bncc_lingua_portuguesa_ef", "bncc_lingua_inglesa_ef"]:
                for x in data_get:
                    data_show.append({
                        'column1': x[0],
                        'componente': x[1],
                        'ano_faixa': x[2],
                        'unidades_tematicas': x[3],
                        'objetos_conhecimento': x[4],
                        'habilidades': x[5],
                        'cod_hab': x[6],
                        'descricao_cod': x[7],
                        'primeiro_ef': x[8],
                        'segundo_ef': x[9],
                        'terceiro_ef': x[10],
                        'quarto_ef': x[11],
                        'quinto_ef': x[12],
                        'sexto_ef': x[13],
                        'setimo_ef': x[14],
                        'oitavo_ef': x[15],
                        'nono_ef': x[16]
                    })
                return jsonify(message="dados", data=data_show)
            elif subject.endswith("_inf") and not subject.startswith("df"):
                inf_list = []
                for x in data_get:
                    inf_list.append({
                        "column1": x[0],
                        "campo_exp": x[1],
                        "faixa_etaria": x[2],
                        "obj": x[3],
                        "cod_apr": x[4],
                        "descricao_cod": x[5],
                        "idade_anos_inicial": x[6],
                        "idade_meses_inicial": x[7],
                        "idade_anos_final": x[8],
                        "idade_meses_final": x[9]

                    })
                return jsonify(message="Esses são os dados solicitados", data=inf_list)
            elif subject == "df_edu_inf":
                df_edu_inf_list = []
                for x in data_get:
                    df_edu_inf_list.append({
                        "column1": x[0],
                        "campo_exp": x[1],
                        "faixa_etaria": x[2],
                        "cod_apr": x[3],
                        "descricao_cod": x[4],
                        "idade_anos_inicial": x[5],
                        "idade_meses_inicial": x[6],
                        "idade_anos_final": x[7],
                        "idade_meses_final": x[8]
                    })
                return jsonify(message="Esses são os dados solicitados do df_edu_inf", data=df_edu_inf_list)
            elif subject.endswith("_em") and not subject.startswith("c"):
                em_list = []
                for x in data_get:
                    em_list.append({
                        'column1': x[0],
                        'ano_faixa': x[1],
                        'cod_hab': x[2],
                        'habilidades': x[3],
                        'primeiro_ano': x[4],
                        'segundo_ano': x[5],
                        'terceiro_ano': x[6],
                        'area': x[7],
                        'competencias_esp': x[8],
                        'campos_atuacao': x[9]
                    })
                return jsonify(message="Dados de df_habilidades_em", data=em_list)
            elif subject.endswith("_em") and subject.startswith("c"):
                em_competencias_list = []
                for x in data_get:
                    em_competencias_list.append({
                        "column1": x[0],
                        "competencias": x[1],
                        "area": x[2]
                    })
                return jsonify(message="Dados solicitados", data=em_competencias_list)


@app.route('/apibncc/', methods=["GET"])
def list_all_two():
    """Lista todo o currículo por matéria e ano via query string"""
    subject = request.args.get('materia', None, type=str)
    grade = request.args.get('ano', None, type=str)

    try:
        if len(grade) > 0:
            db = cursor.execute(f"SELECT * FROM {subject} where {grade} = 'true'")
            data_get = db.fetchall()
            data_show = []
            if subject == "bncc_lingua_portuguesa_ef":
                pl_list = []
                for x in data_get:
                    pl_list.append({
                        "column1": x[0],
                        "componente": x[1],
                        'ano_faixa': x[2],
                        'campo_atuacao': x[3],
                        'praticas_linguagem': x[4],
                        'objetos_conhecimento': x[5],
                        'habilidades': x[6],
                        'cod_hab': x[7],
                        'descricao_cod': x[8],
                        'primeiro_ef': x[9],
                        'segundo_ef': x[10],
                        'terceiro_ef': x[11],
                        'quarto_ef': x[12],
                        'quinto_ef': x[13],
                        'sexto_ef': x[14],
                        'setimo_ef': x[15],
                        'oitavo_ef': x[16],
                        'nono_ef': x[17]
                    })
                return jsonify(message="Dados solicitados", data=pl_list)
            elif subject == "bncc_lingua_inglesa_ef":
                eng_list = []
                for x in data_get:
                    eng_list.append({
                        'column1': x[0],
                        'componente': x[1],
                        'ano_faixa': x[2],
                        'eixo': x[3],
                        'unidades_tematicas': x[4],
                        'objetos_conhecimento': x[5],
                        'habilidades': x[6],
                        'cod_hab': x[7],
                        'descricao_cod': x[8],
                        'primeiro_ef': x[9],
                        'segundo_ef': x[10],
                        'terceiro_ef': x[11],
                        'quarto_ef': x[12],
                        'quinto_ef': x[13],

                        'sexto_ef': x[14],
                        'setimo_ef': x[15],
                        'oitavo_ef': x[16],
                        'nono_ef': x[17]
                    })
                return jsonify(message="dados", data=eng_list)
            elif subject.endswith("_ef") and subject not in ["bncc_lingua_portuguesa_ef", "bncc_lingua_inglesa_ef"]:
                for x in data_get:
                    data_show.append({
                        'column1': x[0],
                        'componente': x[1],
                        'ano_faixa': x[2],
                        'objetos_conhecimento': x[3],
                        'unidades_tematicas': x[4],
                        'habilidades': x[5],
                        'cod_hab': x[6],
                        'descricao_cod': x[7],
                        'primeiro_ef': x[8],
                        'segundo_ef': x[9],
                        'terceiro_ef': x[10],
                        'quarto_ef': x[11],
                        'quinto_ef': x[12],
                        'sexto_ef': x[13],
                        'setimo_ef': x[14],
                        'oitavo_ef': x[15],
                        'nono_ef': x[16]
                    })
                return jsonify(message="dados", data=data_show)
            elif subject.endswith("_inf") and not subject.startswith("df"):
                inf_list = []
                for x in data_get:
                    inf_list.append({
                        "column1": x[0],
                        "campo_exp": x[1],
                        "faixa_etaria": x[2],
                        "obj": x[3],
                        "cod_apr": x[4],
                        "descricao_cod": x[5],
                        "idade_anos_inicial": x[6],
                        "idade_meses_inicial": x[7],
                        "idade_anos_final": x[8],
                        "idade_meses_final": x[9]

                    })
                return jsonify(message="Esses são os dados solicitados", data=inf_list)
            elif subject == "df_edu_inf":
                df_edu_inf_list = []
                for x in data_get:
                    df_edu_inf_list.append({
                        "column1": x[0],
                        "campo_exp": x[1],
                        "faixa_etaria": x[2],
                        "cod_apr": x[3],
                        "descricao_cod": x[4],
                        "idade_anos_inicial": x[5],
                        "idade_meses_inicial": x[6],
                        "idade_anos_final": x[7],
                        "idade_meses_final": x[8]
                    })
                return jsonify(message="Esses são os dados solicitados do df_edu_inf", data=df_edu_inf_list)
            elif subject.endswith("_em") and not subject.startswith("c"):
                em_list = []
                for x in data_get:
                    em_list.append({
                        'column1': x[0],
                        'ano_faixa': x[1],
                        'cod_hab': x[2],
                        'habilidades': x[3],
                        'primeiro_ano': x[4],
                        'segundo_ano': x[5],
                        'terceiro_ano': x[6],
                        'area': x[7],
                        'competencias_esp': x[8],
                        'campos_atuacao': x[9]
                    })
                return jsonify(message="Dados de df_habilidades_em", data=em_list)
            elif subject.endswith("_em") and subject.startswith("c"):
                em_competencias_list = []
                for x in data_get:
                    em_competencias_list.append({
                        "column1": x[0],
                        "competencias": x[1],
                        "area": x[2]
                    })
                return jsonify(message="Dados solicitados", data=em_competencias_list)
    except:
        if grade == None:
            db = cursor.execute(f"SELECT * FROM {subject}")
            data_get = db.fetchall()
            data_show = []
            if subject == "bncc_lingua_portuguesa_ef":
                pl_list = []
                for x in data_get:
                    pl_list.append({
                        "column1": x[0],
                        "componente": x[1],
                        'ano_faixa': x[2],
                        'campo_atuacao': x[3],
                        'praticas_linguagem': x[4],
                        'objetos_conhecimento': x[5],
                        'habilidades': x[6],
                        'cod_hab': x[7],
                        'descricao_cod': x[8],
                        'primeiro_ef': x[9],
                        'segundo_ef': x[10],
                        'terceiro_ef': x[11],
                        'quarto_ef': x[12],
                        'quinto_ef': x[13],
                        'sexto_ef': x[14],
                        'setimo_ef': x[15],
                        'oitavo_ef': x[16],
                        'nono_ef': x[17]
                    })
                return jsonify(message="Dados solicitados", data=pl_list)
            elif subject == "bncc_lingua_inglesa_ef":
                eng_list = []
                for x in data_get:
                    eng_list.append({
                        'column1': x[0],
                        'componente': x[1],
                        'ano_faixa': x[2],
                        'eixo': x[3],
                        'unidades_tematicas': x[4],
                        'objetos_conhecimento': x[5],
                        'habilidades': x[6],
                        'cod_hab': x[7],
                        'descricao_cod': x[8],
                        'primeiro_ef': x[9],
                        'segundo_ef': x[10],
                        'terceiro_ef': x[11],
                        'quarto_ef': x[12],
                        'quinto_ef': x[13],

                        'sexto_ef': x[14],
                        'setimo_ef': x[15],
                        'oitavo_ef': x[16],
                        'nono_ef': x[17]
                    })
                return jsonify(message="dados", data=eng_list)
            elif subject.endswith("_ef") and subject not in ["bncc_lingua_portuguesa_ef", "bncc_lingua_inglesa_ef"]:
                for x in data_get:
                    data_show.append({
                        'column1': x[0],
                        'componente': x[1],
                        'ano_faixa': x[2],
                        'unidades_tematicas': x[3],
                        'objetos_conhecimento': x[4],
                        'habilidades': x[5],
                        'cod_hab': x[6],
                        'descricao_cod': x[7],
                        'primeiro_ef': x[8],
                        'segundo_ef': x[9],
                        'terceiro_ef': x[10],
                        'quarto_ef': x[11],
                        'quinto_ef': x[12],
                        'sexto_ef': x[13],
                        'setimo_ef': x[14],
                        'oitavo_ef': x[15],
                        'nono_ef': x[16]
                    })
                return jsonify(message="dados", data=data_show)
            elif subject.endswith("_inf") and not subject.startswith("df"):
                inf_list = []
                for x in data_get:
                    inf_list.append({
                        "column1": x[0],
                        "campo_exp": x[1],
                        "faixa_etaria": x[2],
                        "obj": x[3],
                        "cod_apr": x[4],
                        "descricao_cod": x[5],
                        "idade_anos_inicial": x[6],
                        "idade_meses_inicial": x[7],
                        "idade_anos_final": x[8],
                        "idade_meses_final": x[9]

                    })
                return jsonify(message="Esses são os dados solicitados", data=inf_list)
            elif subject == "df_edu_inf":
                df_edu_inf_list = []
                for x in data_get:
                    df_edu_inf_list.append({
                        "column1": x[0],
                        "campo_exp": x[1],
                        "faixa_etaria": x[2],
                        "cod_apr": x[3],
                        "descricao_cod": x[4],
                        "idade_anos_inicial": x[5],
                        "idade_meses_inicial": x[6],
                        "idade_anos_final": x[7],
                        "idade_meses_final": x[8]
                    })
                return jsonify(message="Esses são os dados solicitados do df_edu_inf", data=df_edu_inf_list)
            elif subject.endswith("_em") and not subject.startswith("c"):
                em_list = []
                for x in data_get:
                    em_list.append({
                        'column1': x[0],
                        'ano_faixa': x[1],
                        'cod_hab': x[2],
                        'habilidades': x[3],
                        'primeiro_ano': x[4],
                        'segundo_ano': x[5],
                        'terceiro_ano': x[6],
                        'area': x[7],
                        'competencias_esp': x[8],
                        'campos_atuacao': x[9]
                    })
                return jsonify(message="Dados de df_habilidades_em", data=em_list)
            elif subject.endswith("_em") and subject.startswith("c"):
                em_competencias_list = []
                for x in data_get:
                    em_competencias_list.append({
                        "column1": x[0],
                        "competencias": x[1],
                        "area": x[2]
                    })
                return jsonify(message="Dados solicitados", data=em_competencias_list)


@app.route('/apibncc/habilidades/', methods=["GET"])
def list_all_three():
    """Lista todo as habilidades por matéria e ano via query string"""
    subject = request.args.get('materia', None, type=str)
    grade = request.args.get('ano', None, type=str)

    if len(grade) > 0 and len(subject) > 0:
        db = cursor.execute(f"""SELECT habilidades
                                FROM {subject} where {grade} = 'true'""")
        data_get = db.fetchall()
        data_show = []
        if subject == "bncc_lingua_portuguesa_ef":
            pl_list = []
            for x in data_get:
                pl_list.append({
                    'habilidades': x[0],
                })
            return jsonify(message="Dados solicitados", data=pl_list)
        elif subject == "bncc_lingua_inglesa_ef":
            eng_list = []
            for x in data_get:
                eng_list.append({
                    'habilidades': x[0]

                })
            return jsonify(message="dados", data=eng_list)
        elif subject.endswith("_ef") and subject not in ["bncc_lingua_portuguesa_ef", "bncc_lingua_inglesa_ef"]:
            for x in data_get:
                data_show.append({
                    'habilidades': x[0]

                })
            return jsonify(message="dados", data=data_show)

        elif subject.endswith("_em") and not subject.startswith("c"):
            em_list = []
            db = cursor.execute(f"""SELECT habilidades
                            FROM {subject} where {grade} = 'true'""")
            for x in data_get:
                em_list.append({
                    'habilidades': x[0]
                })
            return jsonify(message="Dados de df_habilidades_em", data=em_list)
        elif subject.endswith("_em") and subject.startswith("c"):
            em_competencias_list = []
            db = cursor.execute(f"""SELECT habilidades
                            FROM {subject} where {grade} = 'true'""")
            for x in data_get:
                em_competencias_list.append({
                    'habilidades': x[0]
                })
            return jsonify(message="Dados solicitados", data=em_competencias_list)


@app.route('/diario', methods=['GET'])
# @spec.validate(resp=Response(HTTP_200=Student))
def list_all_students():
    """Lista todos os estudantes da escola """
    db = cursor.execute(f"SELECT * FROM tabela_alunos ORDER BY id_aluno DESC")
    query_st = db.fetchall()
    all_st = []
    for x in query_st:
        all_st.append({
            "nome": x[0],
            "sobrenome": x[1],
            "nome_completo": x[2],
            "ano": x[3],
            "nivel_ensino": x[4],
            "idade": x[5],
            "cpf": x[6],
            "turma": x[7],
            "id_aluno": x[8],
            "status_aluno": x[9],
            "data_cadastro_aln": x[10]

        })
    return jsonify(message="Lista de todos os alunos", lista_total=all_st)


@app.route('/diario/aluno/<id_student>', methods=['GET'])
def list_student_by_id(id_student):
    "Lista os dados de um estudante pelo id"
    db = cursor.execute(f"SELECT * FROM tabela_alunos where id_aluno = ?", (id_student,))
    query_data = db.fetchone()  # Use fetchone() to retrieve a single row

    if query_data is not None:
        student_data = {
            "nome": query_data[0],
            "sobrenome": query_data[1],
            "nome_completo": query_data[2],
            "ano": query_data[3],
            "nivel_ensino": query_data[4],
            "idade": query_data[5],
            "cpf": query_data[6],
            "turma": query_data[7],
            "id_aluno": query_data[8],
            "status_aluno": query_data[9]
            # "data_cadastro_aln": query_data[10]
        }
        return jsonify(data=student_data, message="Aluno solicitado")
    else:
        return jsonify(message="Aluno não encontrado"), 404


@app.route('/diario/', methods=['GET'])
def list_filters():
    """Lista por filtros - id, ano, nivel, nome, sobrenome, nome_c, cpf, idade """
    filter_y = request.values.get('ano')
    filter_y2 = request.values.getlist('ano')
    filter_level = request.values.getlist('nivel')
    filter_full_name = request.values.get('nome_c')
    filter_surname = request.values.get('sobrenome')
    filter_name = request.values.get('nome')
    filter_cpf = request.values.get('cpf')
    filter_age = request.values.get('idade')
    filter_id = request.values.get('id')

    if filter_y2 is not None:
        if len(filter_y2) == 1:
            query_l = cursor.execute(f"SELECT * FROM tabela_alunos WHERE ano = '{filter_y}'")
    if filter_y2 is not None:
        if len(filter_y2) >= 2:

            if 'sexto' and 'setimo' in filter_y2:
                # ok
                query_l = cursor.execute(f"SELECT * FROM tabela_alunos WHERE ano = 'sexto' or ano = 'setimo'")
            if 'sexto' and 'oitavo' in filter_y2:
                query_l = cursor.execute(f"SELECT * FROM tabela_alunos WHERE ano = 'sexto' or ano = 'oitavo'")
            if 'sexto' and 'nono' in filter_y2:
                query_l = cursor.execute(f"""SELECT * FROM tabela_alunos WHERE 
                                        ano = 'sexto' or ano = 'nono'""")
            if 'sexto' and 'setimo' and 'oitavo' in filter_y2:
                query_l = cursor.execute(f"""SELECT * FROM tabela_alunos WHERE ano = 
                                        'sexto' or ano = 'setimo' OR ano = 'oitavo'""")
            if 'sexto' and 'setimo' and 'nono' in filter_y2:
                query_l = cursor.execute(f"""SELECT * FROM tabela_alunos WHERE ano = 
                                        'sexto' or ano = 'setimo' OR ano = 'nono'""")

            if 'setimo' and 'oitavo' in filter_y2:
                query_l = cursor.execute(f"""SELECT * FROM tabela_alunos WHERE ano = 
                                        'setimo' OR ano = 'oitavo'""")

            if 'setimo' and 'oitavo' and 'nono' in filter_y2:
                query_l = cursor.execute(f"""
                                        SELECT * FROM tabela_alunos WHERE ano =
                                        'setimo' OR ano = 'oitavo' OR ano = 'nono'                                     
                                        """)
            if 'oitavo' and 'nono' in filter_y2:
                query_l = cursor.execute(f"""
                                        SELECT * FROM tabela_alunos WHERE ano = 
                                        'oitavo' OR ano = 'nono'                                     
                                        """)
    if filter_level is not None:
        if len(filter_level) > 0:

            if 'em' and 'ef' in filter_level:
                query_l = cursor.execute(f""" SELECT * FROM tabela_alunos WHERE nivel_ensino = 'ef' OR 
                                        nivel_ensino = 'em'
                                        """)
            if 'ef' not in filter_level:
                query_l = cursor.execute(f"""
                                        SELECT * FROM tabela_alunos WHERE nivel_ensino = 'em'                                  
                                        """)
            if 'em' not in filter_level:
                query_l = cursor.execute(f""" SELECT * FROM tabela_alunos WHERE nivel_ensino = 'ef'
                                        """)
    if filter_full_name is not None:
        if len(filter_full_name) > 0:
            query_l = cursor.execute(f"""
                                SELECT * FROM tabela_alunos WHERE nome_completo
                                LIKE ?""", filter_full_name + '%')
    if filter_surname is not None:
        if len(filter_surname) > 0:
            query_l = cursor.execute(f"""
                                SELECT * FROM tabela_alunos WHERE sobrenome
                                LIKE ?""", filter_surname + '%')

    if filter_name is not None:
        if len(filter_name) > 0:
            query_l = cursor.execute(f"""
                            SELECT * FROM tabela_alunos WHERE nome
                            LIKE ?""", filter_name + '%')
    if filter_cpf is not None:
        if len(filter_cpf) > 0:
            query_l = cursor.execute(f"""
                        SELECT * FROM tabela_alunos WHERE cpf
                        LIKE ?""", filter_cpf + '%')
    if filter_age is not None:
        if len(filter_age) > 0:
            query_l = cursor.execute(f"""
                                     SELECT * FROM tabela_alunos WHERE idade
                                     = {filter_age}""")
    if filter_id is not None:
        query_l = cursor.execute(f"""
                                 SELECT * FROM tabela_alunos WHERE id_aluno= {filter_id}""")

    query_l = query_l.fetchall()
    list_y = []

    for x in query_l:
        list_y.append({

            "nome": x[0],
            "sobrenome": x[1],
            "nome_completo": x[2],
            "ano": x[3],
            "nivel_ensino": x[4],
            "idade": x[5],
            "cpf": x[6],
            "id": x[7],
            "turma": x[8],
            "status_aluno": x[9],
            "data_cadastro_aln": x[10]

        })

    return jsonify(message="Alunos por ano cursado", data=list_y)


@app.route('/diario/inserir', methods=['POST'])
def insert_student():
    """Insere um novo estudante"""

    new_std = request.get_json(force=True)
    new_na = new_std['nome']
    new_su = new_std['sobrenome']
    new_fn = new_std['nome'] + ' ' + new_std['sobrenome']
    new_gr = new_std['ano']
    new_l = new_std['nivel_ensino']
    new_ag = new_std['idade']
    new_c = new_std['cpf']
    new_cl = new_std['id_turma']

    cursor.execute(f""" INSERT INTO tabela_alunos (nome, sobrenome, nome_completo,
                   ano, nivel_ensino, idade, cpf, id_turma, status_aluno)
                   VALUES ('{new_na}', '{new_su}', '{new_fn}', '{new_gr}',
                   '{new_l}', {new_ag},
                   '{new_c}', {new_cl}, 'true')
                   """)
    cursor.execute(f"SELECT SCOPE_IDENTITY() AS last_insert_id")
    last_id = cursor.fetchone().last_insert_id
    print(f"o último id inserido foi o {last_id}")
    new_std.update({'id_aluno': last_id})
    cursor.commit()
    return jsonify(message=f"Aluno * {str.upper(new_fn)} * id {last_id}, cadastrado com sucesso", data=new_std)


@app.route('/diario/deletar/<id_student>/<status_aluno>', methods=['PUT'])
def delete_student(id_student, status_aluno):
    """Altera status do estudante"""
    cursor.execute(f"""UPDATE tabela_alunos SET status_aluno = {status_aluno}
                    WHERE id_aluno ={id_student}
                """)
    cursor.commit()
    response_data = {"id_aluno": id_student}
    return jsonify(message="Aluno desativado da lista. ", data=response_data)


@app.route('/diario/atualizar/<id_student>', methods=['PUT'])
def update_std(id_student):
    """Atualiza um estudante da lista"""
    updated_data = request.get_json(force=True)
    up_na = updated_data['nome']
    up_su = updated_data['sobrenome']
    up_fn = updated_data['nome'] + updated_data['sobrenome']
    up_gr = updated_data['ano']
    up_le = updated_data['nivel_ensino']
    up_ag = updated_data['idade']
    up_cpf = updated_data['cpf']
    up_cl = updated_data['turma']

    cursor.execute(f"""UPDATE tabela_alunos SET nome = '{up_na}', 
                   sobrenome = '{up_su}', nome_completo = '{up_fn}',
                   ano = '{up_gr}', nivel_ensino = '{up_le}', 
                   idade = {up_ag}, cpf = '{up_cpf}', turma = {up_cl}
                   WHERE id_aluno ={id_student}
                   """)

    cursor.commit()
    updated_data.update({'id_aluno': id_student})
    return (jsonify(message=f"Estudante {up_fn} atualizado", data=updated_data))


@app.route('/diario/atividades', methods=['GET'])
def get_all_act():
    """Lista todas as atividades de todos os alunos de todas as turmas"""

    db = cursor.execute(f"""SELECT * from tabela_atividade
                        """)
    db = db.fetchall()
    db_l = []
    for x in db:
        db_l.append({
            'id_materia': x[0],
            'id_bimestre': x[1],
            'descricao_at': x[2],
            'id_turma': x[3],
            'id_atividade': x[4],
            'data_cadastro_atv': x[5]
        })
    return jsonify(message="Todas as atividades", data=db_l)


# funcionando
@app.route('/diario/atividade/<int:id_atividade>', methods=['GET'])
def get_act_by_id(id_atividade):
    db = cursor.execute(f"""SELECT * FROM tabela_atividade WHERE id_atividade = {id_atividade}
                       """)
    db = db.fetchone()
    db_l = [{
        'id_materia': db[0],
        'id_bimestre': db[1],
        'descricao_at': db[2],
        'id_turma': db[3],
        'id_atividade': db[4],
        'data_cadastro_atv': db[5]
    }]
    return jsonify(message=f"Atividade solicitada", data=db_l)


# funcionando

@app.route('/diario/inserir/atividades', methods=['POST'])
def insert_act():
    """Insere uma nova atividade"""

    act_obj = request.get_json(force=True)
    id_materia = act_obj.get('id_materia')
    id_bimestre = act_obj.get('id_bimestre')
    turma = act_obj.get('id_turma')
    act_des = act_obj.get('descricao_at')
    data_cadastro_atv = act_obj.get('data_cadastro_atv')

    if id_materia is None or id_bimestre is None or turma is None:
        return jsonify(
            message="Certifique-se de fornecer id_materia, id_bimestre, id_turma e data_cadastro_atv no corpo da solicitação."), 400

    cursor.execute(f"""INSERT INTO tabela_atividade (id_materia, id_bimestre, 
                   id_turma, descricao_at, data_cadastro_atv)
                   VALUES ({id_materia}, {id_bimestre}, {turma},
                   '{act_des}', '{data_cadastro_atv}')""")

    cursor.execute(f"SELECT SCOPE_IDENTITY() AS last_insert_id")
    last_id_act = cursor.fetchone().last_insert_id

    act_obj.update({'id_atividade': last_id_act})

    cursor.commit()

    return jsonify(message=f"Atividade inserida com sucesso e o id inserido é {last_id_act}", data=act_obj)


@app.route('/diario/notas/', methods=['GET'])
def get_list_filters():
    """1) materia=MATERIA(str)&bimestre=BIMESTRE(int) => gera todos os
    boletins para todas as turmas do bimestre de 1 matéria \n
    2) materia=MATERIA(str)&bimestre=BIMESTRE(int)&turma=TURMA(int)=> gera todos os boletins
    de uma matéria, de 1 bimestre para 1 turma \n
    3) materia=MATERIA(str)&ano=ANO(str)&bimestre=BIMESTRE(int) => gera todos os boletins
    de uma matéria para uma série/ano específico, baseado em um bimestre.
    4) materia=MATERIA(str)&ano=ANO(str)&bimestre=BIMESTRE(int)&turma=TURMA(int) => gera os boletins
    de uma matéria, de 1 bimestre, de 1 série específica, de 1 turma.
    5) materia=MATERIA(str) = > gera todas as notas de uma matéria, independente do ano
    6) materia=MATERIA(str)&turma=TURMA(int) => gera todas as notas de uma matéria, de uma turma
    """
    filter_sub = request.args.get('materia')
    filter_cla = request.args.get('turma')
    filter_yea = request.args.get('ano')
    filter_per = request.args.get('bimestre')
    filter_gra = request.args.get('total')
    filter_avg = request.args.get('media')

    # matéria e bimestre
    if filter_sub is not None and filter_per is not None and filter_cla is None:
        query_l = cursor.execute(f"""
                                 SELECT nome_completo, ano, materia, id_turma, 
                                 tabela_bimestre.id_bimestre, total, id_avaliacao, id_atividade
                                 FROM tabela_alunos INNER JOIN tabela_avaliacao
                                 ON tabela_alunos.id_aluno = tabela_avaliacao.id_aluno
                                 INNER JOIN tabela_materias ON 
                                 tabela_avaliacao.id_materia = tabela_materias.id_materia 
                                 INNER JOIN tabela_bimestre ON 
                                 tabela_avaliacao.id_bimestre = tabela_materias.id_materia
                                 WHERE materia ='{filter_sub}' and tabela_avaliacao.id_bimestre = {filter_per}

                             """)
    # matéria, ano
    if filter_sub is not None and filter_yea is not None and filter_per is None:
        query_l = cursor.execute(f"""
                                  SELECT nome_completo, ano, materia, tabela_alunos.id_turma, 
                                  tabela_bimestre.id_bimestre, total, id_avaliacao, id_atividade
                                    FROM tabela_alunos INNER JOIN tabela_avaliacao
                                 ON tabela_alunos.id_aluno = tabela_avaliacao.id_aluno
                                 INNER JOIN tabela_materias ON 
                                 tabela_avaliacao.id_materia = tabela_materias.id_materia 
                                 INNER JOIN tabela_bimestre ON 
                                 tabela_avaliacao.id_bimestre = tabela_materias.id_materia
                                 WHERE tabela_materias.materia ='{filter_sub}' and tabela_alunos.ano = '{filter_yea}'
                                 """)

    # matéria, bimestre e turma
    if filter_sub is not None and filter_per is not None and filter_cla is not None:
        query_l = cursor.execute(f"""
                                 SELECT nome_completo, ano, 
                                 materia, tabela_alunos.id_turma, id_bimestre, total
                                 FROM tabela_alunos INNER JOIN tabela_avaliacao , 
                                 id_avaliacao, id_atividade
                                 ON tabela_alunos.id_aluno = tabela_avaliacao.id_aluno
                                 INNER JOIN tabela_materias ON 
                                 tabela_avaliacao.id_materia = tabela_materias.id_materia
                                 WHERE materia ='{filter_sub}' and tabela_avaliacao.id_bimestre = {filter_per}
                                 AND tabela_alunos.id_turma = {filter_cla}                                 
                                 """)
    # materia, bimestre, ano e turma
    if filter_sub is not None and filter_per is not None and filter_cla is not None and filter_yea is not None:
        query_l = cursor.execute(f"""
                                SELECT nome_completo,  
                                ano, materia, tabela_alunos.id_turma, 
                                id_bimestre, total , id_avaliacao, id_atividade
                                FROM tabela_alunos INNER JOIN tabela_avaliacao
                                ON tabela_alunos.id_aluno = tabela_avaliacao.id_aluno
                                INNER JOIN tabela_materias ON 
                                tabela_avaliacao.id_materia = tabela_materias.id_materia
                                WHERE materia ='{filter_sub}' and tabela_avaliacao.id_bimestre = {filter_per}
                                AND tabela_alunos.id_turma = {filter_cla} AND tabela_alunos.ano = '{filter_yea}'                                
                                """)
    # matéria e turma
    if filter_sub is not None and filter_cla is not None and \
            filter_per is None and filter_gra is None and filter_yea is None:
        query_l = cursor.execute(f"""
                                SELECT nome_completo,  
                                ano, materia, tabela_alunos.id_turma,
                                id_bimestre, total, id_avaliacao, id_atividade
                                FROM tabela_alunos INNER JOIN tabela_avaliacao
                                ON tabela_alunos.id_aluno = tabela_avaliacao.id_aluno
                                INNER JOIN tabela_materias ON 
                                tabela_avaliacao.id_materia = tabela_materias.id_materia
                                WHERE tabela_materias.materia ='{filter_sub}' and tabela_alunos.id_turma = {filter_cla}
                                """)

    query_l = query_l.fetchall()
    print(query_l)
    list_l = []
    for x in query_l:
        list_l.append({
            'nome_completo': x[0],
            'ano': x[1],
            'materia': x[2],
            'id_turma': x[3],
            'id_bimestre': x[4],
            'total': x[5],
            'id_avaliacao': x[6],
            'id_atividade': x[7]
        })
    return jsonify(data=list_l)


@app.route('/diario/notas/media/', methods=['GET'])
def get_mean():
    filter_sub = request.args.get('materia')
    filter_cla = request.args.get('turma')
    filter_yea = request.args.get('ano')
    filter_per = request.args.get('bimestre')

    # média de todas as turmas de uma determinada matéria
    if filter_sub is not None and filter_cla is not None and filter_per is None and filter_yea is None:
        query_l = cursor.execute(f"""
                                 SELECT materia, id_turma, AVG(tabela_avaliacao.nota)
                                 FROM tabela_avaliacao INNER JOIN tabela_materias
                                 ON tabela_avaliacao.id_materia = 
                                 tabela_materias.id_materia  INNER JOIN 
                                 tabela_atividade ON tabela_avaliacao.id_atividade = 
                                 tabela_atividade.id_atividade                             
                                 where materia = '{filter_sub}'
                                 GROUP BY materia, id_turma                                
                                 """)
    query_l = query_l.fetchall()
    print(query_l)
    list_l = []
    for x in query_l:
        list_l.append({
            'materia': x[0],
            'id_turma': x[1],
            'media': x[2],
        })
    return jsonify(message="dados solicitados", data=list_l)


# método inserir gustavo
@app.route('/diario/inserir/nota', methods=['POST'])
def insert_nota():
    """Insere uma nova nota"""

    act_obj = request.get_json(force=True)

    id_aluno = act_obj.get('id_aluno')
    id_materia = act_obj.get('id_materia')
    id_bimestre = act_obj.get('id_bimestre')
    nota = act_obj.get('nota')
    total = act_obj.get('total')
    id_atividade = act_obj.get('id_atividade')

    cursor.execute(f"""INSERT INTO tabela_avaliacao (id_materia, 
                   id_bimestre, id_aluno, id_atividade, nota, total)
                   VALUES ({id_materia}, {id_bimestre}, {id_aluno},
                   {id_atividade}, {nota}, {total})""")

    cursor.commit()

    return jsonify(message=f"Avaliacao inserida com sucesso ", data=act_obj)


@app.route('/diario/notas/inserir/', methods=['GET', 'POST', 'PUT'])
def post_grades():
    new_act = request.get_json(force=True)
    if len(new_act) > 1:
        id_atividade = new_act[0].get('id_atividade')
    else:
        id_atividade = new_act.get('id_atividade')
    db_turma = cursor.execute(f"""SELECT id_turma FROM tabela_atividade WHERE 
                              id_atividade = {id_atividade}""")

    if len(new_act) > 1:
        id_turma = db_turma.fetchone()[0]
    else:
        id_turma = db_turma.fetchone()
    print(f"esse é o id turma {id_turma}")
    db_ids = cursor.execute(f"""
    SELECT id_aluno from tabela_alunos where id_turma = {id_turma}""")
    list_ids = db_ids.fetchall()
    list_ids = [x for y in list_ids for x in y]
    dic_ids = []
    for x in list_ids:
        dic_ids.append({
            'id_aluno': x
        })

    resultado = []
    for new_act_item in new_act:
        # print(f"esse é um elemento de new_act (item) {new_act_item}")
        for dic_ids_item in dic_ids:
            # print(f"esse é um elemento de dic_ids_item {dic_ids_item}")
            combined_dict = {**new_act_item, **dic_ids_item}
            # print(f"esse é combined dict por linha {combined_dict}")
            if combined_dict not in resultado:
                resultado.append(combined_dict)
                # print(f"esse é o resultado de agora {resultado}")

    for x in resultado:
        cursor.execute(f"""
                       INSERT INTO tabela_avaliacao (id_aluno, id_materia, id_bimestre, nota, 
                       id_atividade) VALUES (
                           {x['id_aluno']}, {x['id_materia']}, {x['id_bimestre']}, {x['nota']}, 
                           {id_atividade}
                           )
                       """)
        cursor.commit()

    return jsonify(message="dados inseridos", data=resultado)


@app.route('/diario/notas/atualizar/<int:id_avaliacao>', methods=['PUT'])
def update_grades(id_avaliacao):
    """Atualiza uma atividade criada. Os campos disponíveis para atualização são:
    id_materia(int)= portugues:	1, ingles:	2, artes:	3, matematica:	4, ciencias: 5
    educacao_fisica: 6, ensino_religioso: 7, historia:	8, geografia:	9
    id_bimestre(int)= 1, 2, 3, 4
    nota_5(int) (em breve serão disponibilizadas todas as notas)
    descricao_at(str)

    """
    up_obj = request.get_json(force=True)
    up_per = up_obj['id_bimestre']
    up_gra_5 = up_obj['nota']
    up_sub = up_obj['id_materia']

    if up_per is not None and up_des is not None \
            and up_gra_5 is not None and up_sub is not None:
        cursor.execute(f"""UPDATE tabela_avaliacao SET id_materia = {up_sub} , 
                       id_bimestre = {up_per},
                       nota = {up_gra_5} WHERE
                       id_avaliacao = {id_avaliacao}
                   """)
    cursor.commit()
    up_obj.update({'id_avaliacao': id_avaliacao})
    return jsonify(message="Atividade atualizada", data=up_obj)


@app.route('/diario/notas/deletar/<int:id_avaliacao>', methods=['DELETE'])
def delete_grades(id_avaliacao):
    """Insira o id de alguma atividade e ela será apagada"""
    cursor.execute(f"""DELETE FROM tabela_avaliacao WHERE id_avaliacao = {id_avaliacao}
                   """)
    cursor.commit()

    return jsonify(message=f"Atividade {id_avaliacao} apagada!", dado_deletado=id_avaliacao)


app.run(debug=True)
