# -*- coding: utf-8 -*-
import json
import requests

class Endereco:

    result = ''
    
    def __init__(self,descricao):
        self.__descricao = descricao
        self.__call__()

    def __call__(self):
        url = "https://buscacepinter.correios.com.br/app/endereco/carrega-cep-endereco.php"
        payload = {'endereco': self.__descricao,'tipoCEP': 'ALL'}
        response = requests.request("POST", url, headers={}, data=payload)
        self.result = response.text
        return self.result
    
    def __convert__(self):
        return json.loads(self.result)

    def mensagem(self):
        return self.__convert__()["mensagem"]
    
    def total(self):
        return self.__convert__()["total"]
    
    def resultados(self):
        return self.__convert__()["dados"]
