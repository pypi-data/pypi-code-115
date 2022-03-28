from maeapi.utils import *
from maeapi.parsers.banking import *

class BankingMixin:
    def get_primary_summary_balance(self):
        self._check_auth()
        endpoint = 'summary/getBalance'
        response = self._send_banking_get_request(endpoint)
        message = parse_summary_balance_message(response)
        result = parse_primary_summary_balance(response)
        return message, result

    def get_all_summary_balance(self):
        self._check_auth()
        endpoint = 'summary'
        body = {"type": "A",
        "checkMae" : "true"} 
        response = self._send_banking_get_request(endpoint, body)  
        message = parse_summary_balance_message(response)

        res = []
        result = parse_all_summary_balance(response)    
        for i in result:
            res.append({
                'name':i['name'],
                'number':i['number'],
                'balance':i['balance']})
     
        return message, res    
