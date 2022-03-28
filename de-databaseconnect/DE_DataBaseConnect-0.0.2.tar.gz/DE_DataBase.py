import os
import sqlite3 as sq3
import cx_Oracle as ora
import pandas as pd
import psycopg2 as ps2
import mysql.connector as mysql

# Reponsabilidades desta classe:
# Apenas se conectar a uma das bases de dados abaixo especificadas
# Bases conhecidas: SQLITE, ORACLE, MYSQL, POSTGRES

class DATABASE:
    def __init__(self):
        pass

    def ORACLE(self, string_connect: dict):
        pathlib, cnn = None, None
        try:
            # Definindo a Library ORACLE
            if "library" in string_connect.keys():
                if string_connect["library"] is None:
                    pathlib = os.getenv("ORACLE_LIB")
                else:
                    pathlib = string_connect["library"]
            else:
                pathlib = os.getenv("ORACLE_LIB")

            # Consistindo se a biblioteca do oracle ja esta iniciada
            try:
                ora.init_oracle_client(lib_dir=pathlib)
            except:
                pass
                # não faz nada (e para deixar assim se nao da erro)

            # Definindo o tipo de instancia SID/SERVICE_NAME
            if string_connect["sid"] is not None:
                dnsName = ora.makedsn(host=string_connect["host"], port=string_connect["port"], sid=string_connect["sid"])
            else:
                dnsName = ora.makedsn(host=string_connect["host"], port=string_connect["port"], service_name=string_connect["service_name"])

            # Efetuando a conexao com a instancia do BANCO
            cnn = ora.connect(string_connect["username"], string_connect["password"], dnsName, threaded=True)
        except Exception as error:
            msg = f"""Falha ao tentar se conectar com o banco de dados ORACLE [{string_connect["name_conection"]}].\nErro: {error} """
            cnn = msg
        finally:
            return cnn

    def SQLITE(self, database):
        DATABASE_NAME, result, msg, conn = None, False, None, None
        try:
            if os.path.isfile(database):
                conn = sq3.connect(database)
                msg = f"""SQLITE [{database}]- Conexao efetuada com sucesso!"""
            else:
                msg = f"""SQLITE [{database}]- Não existe no local informado!"""
                raise Exception
        except Exception as error:
            msg = f"""Falha ao tentar conectar com o banco de dados SQLITE "{DATABASE_NAME}". Erro: {error} """
            cnn = False
        finally:
            return conn

    def POSTGRES(selfself, string_connect: dict):
        msg, cnn = None, None
        try:
            # Efetuando a conexao com a instancia do BANCO
            cnn = ps2.connect(user=string_connect["username"], password=string_connect["password"], database=string_connect["instance"], host=string_connect["host"])
        except Exception as error:
            msg = f"""Falha ao tentar se conectar com o banco de dados POSTGRES.\n """
            cnn = msg
        finally:
            return cnn

    def MYSQL(selfself, string_connect: dict):
        msg, cnn = None, None
        try:
            # Efetuando a conexao com a instancia do BANCO
            cnn = mysql.connect(user=string_connect["username"], password=string_connect["password"], database=string_connect["instance"], host=string_connect["host"])
        except Exception as error:
            msg = f"""Falha ao tentar se conectar com o banco de dados MYSQL.\n """
            cnn = msg
        finally:
            return cnn

    def METADATA(self,
                 conexao: object,
                 database: str,
                 nome_tabela: str,
                 alias: str = 'x',
                 quoted: bool = False,
                 rowid: bool = False,
                 join: str = None,
                 where: str = None,
                 orderby: str = None,
                 limit: int = 0
                 ) -> str:
        try:
            querys = {"ORACLE":   f"""Select * from all_tab_columns where table_name = '{nome_tabela}' order by column_id""""",
                      "POSTGRES": f"""Select * from information_schema.columns where table_name = '{nome_tabela}' order by ordinal_position""",
                      "SQLITE":   f"""Select * from pragma_table_info('{nome_tabela}') order by cid""",
                      "MYSQL":    f"""Select * from information_schema.columns where table_name = '{nome_tabela}' order by ordinal_position"""}
            qry = querys[database]
            df = pd.read_sql(con=conexao, sql=qry)
            nom_owner, column_list = None, []
            # OBTEM AS COLUNAS
            for index, row in df.iterrows():

                # -----------------------------------------
                # Banco SQLITE
                if database == "SQLITE":
                    column = df.loc[index, "name"]
                    # OWNER
                    nom_owner = ""
                    # QUOTED
                    if quoted:
                        column_list.append(f"""{alias}.\"{column}\"""")
                    else:
                        column_list.append(f"""{alias}.{column}""")
                # -----------------------------------------
                # Banco ORACLE
                elif database == 'ORACLE':
                    column = df.loc[index, "COLUMN_NAME"]
                    # QUOTED
                    if quoted:
                        column_list.append(f"""{alias}.\"{column}\"""")
                    else:
                        column_list.append(f"""{alias}.{column}""")
                    # OWNER
                    nom_owner = f"""{row.OWNER}."""
                # Banco MYSQL
                elif database == "MYSQL":
                    column = df.loc[index, "COLUMN_NAME"]
                    # QUOTED
                    if quoted:
                        column_list.append(f"""{alias}.\"{column}\"""")
                    else:
                        column_list.append(f"""{alias}.{column}""")
                    # OWNER
                    nom_owner = ""
                # -----------------------------------------
                # Banco POSTGRES
                elif database == "POSTGRES":
                    column = df.loc[index, "column_name".lower()]
                    # QUOTED
                    if quoted:
                        column_list.append(f"""{alias}.\"{column}\"""")
                    else:
                        column_list.append(f"""{alias}.{column}""")
                    # OWNER
                    nom_owner = ""

            # ROWID
            if rowid:
                # -----------------------------------------
                # Banco SQLITE
                if database == "SQLITE":
                    column_list.append(f"""{alias}.ROWID ROWID_TABELA""")
                # -----------------------------------------
                # Banco ORACLE
                elif database == "ORACLE":
                    column_list.append(f"""rowidtochar({alias}.Rowid) "ROWID_TABELA" """)
                # -----------------------------------------
                # Banco MYSQL
                elif database == "MYSQL":
                    # não implementado
                    # tem que identificar qual a coluna do MYSQL que representa esta informação
                    pass
                # -----------------------------------------
                # Banco POSTGRES
                elif database == "POSTGRES":
                    column_list.append(f"""{alias}.row_number() OVER () ROWID_TABELA""")

            # Estruturando as colunas
            colunas = "\n      ,".join(column_list)
            select = f"""select {colunas}"""

            # NOME TABELA
            tabela = f"""\n  from {nome_tabela.strip()} {alias.strip()}"""

            # JOIN
            if join is None:
                join = ""
            else:
                join = f"""\n  {join}"""

            #WHERE
            if where is None:
                if database == "ORACLE" and limit > 0:
                    where = f"""\n where rownum <= {limit}"""
                else:
                    where = ""
            else:
                if database == "ORACLE" and limit > 0:
                    where = f"""\n {where.strip()}\n  and rownum <= {limit}"""
                else:
                    where = f"""\n {where.strip()}"""

            #ORDERBY
            if orderby is None:
                orderby = ""
            else:
                orderby = f"""\n {orderby.strip()}"""

            # LIMIT
            if database in ["MYSQL", "SQLITE", "POSTGRES"]:
                if limit > 0:
                    limit = f"""\nlimit {limit}"""
                else:
                    limit = ""
            else:
                limit = ""

            qry = f"""{select}{tabela}{join}{where}{orderby}{limit}""".lstrip()
            msg = qry
        except Exception as error:
            msg = error + qry
        finally:
            return msg

if __name__ == "__main__":
    pass
