from PyZohoBooksAPI.api import API


class Contacts(API):
    def __init__(self, token, organization_id):
        self.token = token
        self.organization_id = organization_id

    def contacts_list(self):
        url = 'https://books.zoho.com/api/v3/contacts'
        params = {'organization_id': self.organization_id}
        headers = {'Authorization': f'Zoho-oauthtoken {self.token}'}
        result = self._start_connection(method='GET', url=url, headers=headers, params=params)
        return self._parse_response(result)

    def get_contact(self, contact_id):
        url = f'https://books.zoho.com/api/v3/contacts/{contact_id}'
        params = {'organization_id': self.organization_id}
        headers = {'Authorization': f'Zoho-oauthtoken {self.token}'}
        result = self._start_connection(method='GET', url=url, headers=headers, params=params)
        return self._parse_response(result)

    def check_by_email(self, email):
        status, contacts = self.contacts_list()
        for contact in contacts['contacts']:
            if email == contact['email']:
                return 200, contact
            else:
                continue
        return 404, 'not found'

    def create_contact(self, contact_data):
        url = 'https://books.zoho.com/api/v3/contacts'
        params = {'organization_id': self.organization_id}
        headers = {'Authorization': f'Zoho-oauthtoken {self.token}'}
        result = self._start_connection(method='POST', url=url, headers=headers, params=params, data=contact_data)
        return self._parse_response(result)

