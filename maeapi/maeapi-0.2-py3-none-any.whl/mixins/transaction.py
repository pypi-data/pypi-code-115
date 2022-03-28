from maeapi.utils import *
from maeapi.parsers.transaction import *

class TransactionMixin:
    def get_spending_patterns(self, month):
        self._check_auth()
        endpoint = 'creditCard/category/spendingPattern'
        body = {"month": month}
        response = self._send_get_request(endpoint, body)
        return parse_spending_patterns(response)

    def get_transaction_history(self, startDate, endDate):
        self._check_auth()
        endpoint = 'creditCard/transaction/history'
        body = {
            "startDate": startDate,
            "endDate": endDate
            }
        response = self._send_get_request(endpoint, body)
        return parse_transaction_history(response)