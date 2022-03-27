from PyZohoBooksAPI.api import API


class Invoices(API):
    def __init__(self, token, organization_id):
        self.token = token
        self.organization_id = organization_id

    def create_invoice(self, invoice_data):
        url = 'https://books.zoho.com/api/v3/invoices'
        params = {'organization_id': self.organization_id}
        headers = {'Authorization': f'Zoho-oauthtoken {self.token}'}
        result = self._start_connection(method='POST', url=url, headers=headers, params=params, data=invoice_data)
        return self._parse_response(result)

    def email_an_invoice(self, invoice_id, email_data):
        url = f'https://books.zoho.com/api/v3/invoices/{invoice_id}/email'
        params = {'organization_id': self.organization_id}
        headers = {'Authorization': f'Zoho-oauthtoken {self.token}'}
        result = self._start_connection(method='POST', url=url, headers=headers, params=params, data=email_data)
        return self._parse_response(result)
