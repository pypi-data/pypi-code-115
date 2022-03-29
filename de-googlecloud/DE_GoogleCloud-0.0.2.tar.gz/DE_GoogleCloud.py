import os
import io
import json
import datetime as dt
import pathlib

from google.cloud import storage

class GCP:
    def __init__(self, **kwargs):
        self._avalia_parametros_recebidos(**kwargs)
        os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = self._KEY_BUCKET

    def _avalia_parametros_recebidos(self, **kwargs):
        try:
            if "key_bucket" in kwargs.keys():
                self._KEY_BUCKET = kwargs.get("key_bucket")
            if "nome_bucket" in kwargs.keys():
                self._NOME_BUCKET = kwargs.get("nome_bucket")
            if "path_bucket" in kwargs.keys():
                self._PATH_BUCKET = kwargs.get("path_bucket")
            pass
        except Exception as error:
            raise Exception(error)
        finally:
            pass

    def Upload_Bucket_Single_File(self, filename: str, nome_bucket: str = None, path_bucket: str = None):
        tx_inicio, tx_termino, tx_tempo, msg = None, None, None, None
        try:
            # Avaliando se foi informado um nome de bucket (obrigatorio ser um bucket valido)
            if nome_bucket is None:
                if self._NOME_BUCKET is None:
                    raise Exception("É necessário informar um nome de bucket válido!")
                else:
                    nome_bucket = self._NOME_BUCKET
            # Avaliando se foi informado um path dentro do bucket
            if path_bucket is None:
                if self._PATH_BUCKET is None:
                    path_bucket = ""
                else:
                    path_bucket = self._PATH_BUCKET
            #
            tx_inicio = dt.datetime.now()
            storage_client = storage.Client()
            handle_bucket = storage_client.bucket(nome_bucket)
            # Obtendo o arquivo e preparando para a escrita no bucket
            basefilename = os.path.basename(filename)
            if path_bucket is not None:
                file_write = os.path.join(path_bucket, basefilename).replace("\\", "/")
            else:
                file_write = basefilename
            #
            file_bucket = handle_bucket.blob(file_write)
            file_bucket.upload_from_filename(filename, timeout=300)
            tx_termino = dt.datetime.now()
            tx_tempo = tx_termino - tx_inicio
            msg = "Arquivo transferido com sucesso!"
        except Exception as error:
            msg = error
        finally:
            file_tx_status = {"file": filename, "tx_inicio": tx_inicio, "tx_termino": tx_termino, "tx_tempo": tx_tempo, "msg": msg}
            return file_tx_status

    def Upload_Bucket_Multiples_Files(self, file_list: list, nome_bucket: str = None, path_bucket: str = None):
        status_list = []
        try:
            # Avaliando se foi informado um nome de bucket (obrigatorio ser um bucket valido)
            if nome_bucket is None:
                if self._NOME_BUCKET is None:
                    raise Exception("É necessário informar um nome de bucket válido!")
                else:
                    nome_bucket = self._NOME_BUCKET
            # Avaliando se foi informado um path dentro do bucket
            if path_bucket is None:
                if self._PATH_BUCKET is None:
                    path_bucket = ""
                else:
                    path_bucket = self._PATH_BUCKET

            if file_list is None or not isinstance(file_list, list):
                raise Exception("Não existe uma lista de arquivos a ser transferida para o bucket")
            else:
                for file in file_list:
                    status = self.Upload_Bucket_Single_File(filename=file, nome_bucket=nome_bucket, path_bucket=path_bucket)
                    status_list.append(status)
        except Exception as error:
            msg = error
        finally:
            return status_list

    def Download_Bucket_Single_File(self, bucket_filename: str, nome_bucket: str = None, path_bucket: str = None, path_local: str = None, local_filename: str = None):
        result, rx_inicio, rx_termino, rx_tempo = None, None, None, None
        try:
            # Avaliando se foi informado um nome de bucket (obrigatorio ser um bucket valido)
            if nome_bucket is None:
                if self._NOME_BUCKET is None:
                    raise Exception("É necessário informar um nome de bucket válido!")
                else:
                    nome_bucket = self._NOME_BUCKET
            # Avaliando se foi informado um path dentro do bucket
            if path_bucket is None:
                if self._PATH_BUCKET is None:
                    path_bucket = ""
                else:
                    path_bucket = self._PATH_BUCKET
            file_read = os.path.join(path_bucket, bucket_filename).replace("\\", "/")

            # Avaliando se foi informado o local e nome do arquivo
            if path_local is None:
                path_local = os.getcwd()
            if local_filename is None:
                local_filename = bucket_filename
            file_write = os.path.join(path_local, local_filename)
            # Inicio do Download
            rx_inicio = dt.datetime.now()
            client = storage.Client()
            bucket = client.get_bucket(nome_bucket)
            blob = bucket.blob(file_read)
            blob.download_to_filename(file_write)
            rx_termino = dt.datetime.now()
            rx_tempo = rx_termino - rx_inicio
            msg = "Download concluido com sucesso!"
        except Exception as error:
            msg = error
        finally:
            status = {"rx_inicio": rx_inicio, "rx_termino": rx_termino, "rx_tempo": rx_tempo, "msg": msg}
            return status

    def Download_Bucket_Multiple_file(self, file_list: list, bucket_name: str, bucket_path: str, local_path: str):
        status_list = []
        try:
            if file_list is None or not isinstance(file_list, list):
                raise Exception("Não existe uma lista de arquivos a ser transferida para o bucket")
            else:
                par = {"bucket_name": bucket_name,
                       "bucket_path": bucket_path,
                       "bucket_filename": file_list,
                       "local_filename": local_path,
                       }
                status = self.Download_Single_File(**par)
                status_list.append(status)
        except Exception as error:
            msg = error
        finally:
            return status_list

if __name__ == "__main__":
    status = None
    parametros = {"key_bucket": "C:\Projetos\DASABI\LibDASA\Template\interoper-dataplatform-prd-bd35fd0be08e.json",
                  "nome_bucket": "interoper-dataplatform-prd-landing-dasabi"
                  }
    g = GCP(**parametros)

    # Download de um arquivo
    # par = {"bucket_name": "interoper-dataplatform-prd-landing-dasabi",
    #        "bucket_path": "Testes_almir",
    #        "bucket_filename": "BI_CTRL_PARAMETROS_BIETL_TRACKING.json",
    #        "local_filename": "C:\Tmp\\Testes.json",
    #        "gcp_abs_file": "https://storage.cloud.google.com/interoper-dataplatform-prd-landing-dasabi/volumetria_dados_Motion_Peer_Learning.xlsx"
    #        }
    # status = g.Download_Single_File(**par)

    # Download de multiplos arquivos
    files = ["C:\Tmp\Lista_tabelas_precos.csv",
             "C:\Tmp\PARAMETROS_BI_ETL_TRACKING.json",
             "C:\Tmp\BI_CTRL_PARAMETROS_BIETL_TRACKING.json"
             ]
    status = g.Download_Multiple_file(file_list=files, bucket_path="Testes_almir", local_path="C:\Tmp\Testes_Bucket")

    print(status)