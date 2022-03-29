import os
import datetime as dt
import hashlib
import base64
from google.cloud import storage

class GCP:
    def __init__(self, **kwargs):
        self._avalia_parametros_recebidos(**kwargs)
        os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = self._BUCKET_KEY

    def Upload_Bucket_Single_File(self, filename_read: str, bucket_name: str = None, bucket_path: str = None):
        tx_inicio, tx_termino, tx_tempo, msg, tx_filesize, hash_file_bucket, hash_file_local = None, None, None, None, None, None, None
        try:
            tx_inicio = dt.datetime.now()
            # Avaliando se foi informado um nome de bucket (obrigatorio ser um bucket valido)
            if bucket_name is None:
                if self._BUCKET_NAME is None:
                    raise Exception("É necessário informar um nome de bucket válido!")
                else:
                    bucket_name = self._BUCKET_NAME
            # Avaliando se foi informado um path dentro do bucket
            if bucket_path is None:
                if self._BUCKET_PATH is None:
                    bucket_path = ""
                else:
                    bucket_path = self._BUCKET_PATH
            # Obtendo o arquivo e preparando para a escrita no bucket
            basefilename = os.path.basename(filename_read)
            if bucket_path is not None:
                filename_write = os.path.join(bucket_path, basefilename).replace("\\", "/")
            else:
                filename_write = basefilename
            # Verificando se arquivo existe na origem para começar o Upload
            if os.path.isfile(filename_read):
                tx_filesize = os.path.getsize(filename_read)
                client = storage.Client()
                bucket = client.bucket(bucket_name)
                blob = bucket.blob(filename_write)
                blob.upload_from_filename(filename_read, timeout=60)
                hash_file_bucket = self._hash_file_bucket(bucket_filename=filename_write, bucket_name=bucket_name)

                hash_file_local = self._hash_file_local(filename_read)
                if hash_file_local != hash_file_bucket:
                    msg = "Upload do arquivo foi efetuado, porém os HASH´s estão diferentes, cabe verificacao!"
                else:
                    msg = "Upload do arquivo efetuado com sucesso!"
            else:
                msg = "Arquivo nao existe na origem (LOCAL). Upload não efetuado"
        except Exception as error:
            msg = error
        finally:
            tx_termino = dt.datetime.now()
            tx_tempo = tx_termino - tx_inicio
            file_tx_status = {"bucket": bucket_name, "buckt_path": bucket_path, "file": filename_read, "size": tx_filesize, "hash_file_bucket": str(hash_file_bucket), "hash_file_local": str(hash_file_local),  "tx_inicio": str(tx_inicio), "tx_termino": str(tx_termino), "tx_tempo": str(tx_tempo), "msg": msg}
            return file_tx_status

    def Download_Bucket_Single_File(self, bucket_filename: str, nome_bucket: str = None, path_bucket: str = None, path_local: str = None, local_filename: str = None):
        result, rx_inicio, rx_termino, rx_tempo, tx_filesize, msg, hash_file_bucket, hash_file_local = None, None, None, None, None, None, None, None
        try:
            rx_inicio = dt.datetime.now()

            # Avaliando se foi informado um nome de bucket (obrigatorio ser um bucket valido)
            if nome_bucket is None:
                if self._BUCKET_NAME is None:
                    raise Exception("É necessário informar um nome de bucket válido!")
                else:
                    nome_bucket = self._BUCKET_NAME

            # Avaliando se foi informado um path dentro do bucket
            if path_bucket is None:
                if self._BUCKET_PATH is None:
                    path_bucket = ""
                else:
                    path_bucket = self._BUCKET_PATH
            file_read = os.path.join(path_bucket, bucket_filename).replace("\\", "/")

            # Avaliando se foi informado o local e nome do arquivo
            if path_local is None:
                path_local = os.getcwd()
            if local_filename is None:
                local_filename = bucket_filename
            filename_write = os.path.join(path_local, local_filename)

            # Verificando se arquivo existe na origem
            if self._hash_file_bucket(bucket_filename=file_read, bucket_name=nome_bucket) is not None:
                if os.path.exists(path_local):
                    # Inicio do Download
                    client = storage.Client()
                    bucket = client.get_bucket(nome_bucket)
                    blob = bucket.blob(file_read)
                    blob.download_to_filename(filename_write, timeout=60)
                    hash_file_bucket = self._hash_file_bucket(bucket_filename=file_read, bucket_name=nome_bucket)
                    tx_filesize = os.path.getsize(filename_write)
                    hash_file_local = self._hash_file_local(filename_write)
                    if hash_file_local != hash_file_bucket:
                        msg = "Download do arquivo foi efetuado, porém os HASH´s estao diferentes, cabe verificacao!"
                    else:
                        msg = "Download do arquivo efetuado com sucesso!"
                else:
                    msg = "Pasta local para download não existe. Download nao efetuado!"
            else:
                msg = "Arquivo nao existe na origem (GCP). Download nao efetuado!"
        except Exception as error:
            msg = error
        finally:
            rx_termino = dt.datetime.now()
            rx_tempo = rx_termino - rx_inicio
            status = {"file": bucket_filename, "size": tx_filesize, "hash_file_bucket": str(hash_file_bucket), "hash_file_local": str(hash_file_local), "rx_inicio": str(rx_inicio), "rx_termino": str(rx_termino), "rx_tempo": str(rx_tempo), "msg": msg}
            return status

    def Upload_Bucket_Multiples_Files(self, file_list: list, nome_bucket: str = None, path_bucket: str = None):
        status_list = []
        try:
            # Avaliando se foi informado um nome de bucket (obrigatorio ser um bucket valido)
            if nome_bucket is None:
                if self._BUCKET_NAME is None:
                    raise Exception("É necessário informar um nome de bucket válido!")
                else:
                    nome_bucket = self._BUCKET_NAME
            # Avaliando se foi informado um path dentro do bucket
            if path_bucket is None:
                if self._BUCKET_PATH is None:
                    path_bucket = ""
                else:
                    path_bucket = self._BUCKET_PATH

            if file_list is None or not isinstance(file_list, list):
                raise Exception("Não existe uma lista de arquivos a ser transferida para o bucket")
            else:
                for file in file_list:
                    status = self.Upload_Bucket_Single_File(filename_read=file, bucket_name=nome_bucket, bucket_path=path_bucket)
                    status_list.append(status)

        except Exception as error:
            msg = error
        finally:
            return status_list

    def Download_Bucket_Multiple_file(self, file_list: list, bucket_name: str = None, bucket_path: str = None, local_path: str = None):
        status_list = []
        try:
            if file_list is None or not isinstance(file_list, list):
                raise Exception("Não existe uma lista de arquivos a ser transferida para o bucket")
            else:
                if file_list is None or not isinstance(file_list, list):
                    raise Exception("Não existe uma lista de arquivos a ser transferida para o bucket")
                else:
                    for file in file_list:
                        status = self.Download_Bucket_Single_File(bucket_filename=file, nome_bucket=bucket_name, path_bucket=bucket_path, path_local=local_path)
                        status_list.append(status)
        except Exception as error:
            msg = error
        finally:
            return status_list

    def _hash_file_local(self, filename: str):
        result = None
        try:
            binary_hash = hashlib.md5(open(filename, "rb").read()).digest()
            hash = base64.b64encode(binary_hash)
        except Exception as error:
            hash = error
        finally:
            return hash.decode()

    def _hash_file_bucket(self, bucket_filename: str, bucket_name: str = None):
        result = None
        try:
            #file = os.path.join(bucket_path, bucket_filename).replace("\\", "/")
            client = storage.Client()
            bucket = client.get_bucket(bucket_name)
            blob = bucket.blob(bucket_filename)
            blob.reload()
            result = blob.md5_hash
        except Exception as error:
            result = error
        finally:
            #print(result)
            return result

    def _get_crc32(self, file: str, bucket: str = None):
        # Nao Utilizada
        client = storage.Client()
        bucket = client.get_bucket(self._BUCKET_NAME)
        blob = bucket.blob(file)
        crc32 = blob.crc32c
        print(crc32)
        blob.reload()
        crc32 = blob.crc32c
        print(crc32)
        md5 = blob.md5_hash
        print(md5)
        blob = bucket.get_blob(file)
        crc32 = blob.crc32c
        print(crc32)

    def _avalia_parametros_recebidos(self, **kwargs):
        try:
            if "bucket_key" in kwargs.keys():
                self._BUCKET_KEY = kwargs.get("bucket_key")
            if "bucket_name" in kwargs.keys():
                self._BUCKET_NAME = kwargs.get("bucket_name")
            if "bucket_path" in kwargs.keys():
                self._BUCKET_PATH = kwargs.get("bucket_path")
            pass
        except Exception as error:
            raise Exception(error)
        finally:
            pass

if __name__ == "__main__":
    parametros = {"bucket_key": "C:\Projetos\DASABI\LibDASA\Template\interoper-dataplatform-prd-bd35fd0be08e.json",
                  "bucket_name": "interoper-dataplatform-prd-landing-dasabi",
                  "bucket_path": "Testes_almir"
                  }
    g = GCP(**parametros)
    file_read = os.path.join("CALL_PWD_L000001_CHAMADA_SENHAS_00008.csv").replace("\\", "/")
    g._hash_file_bucket(file_read)