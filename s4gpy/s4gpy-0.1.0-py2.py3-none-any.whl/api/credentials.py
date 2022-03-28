class CredentialAPI():
    """Wraps credential API."""

    def __init__(self, session):
        """intialiaze a new Credential API"""
        self.session = session

    def get_credentials(self, provider_name):
        """Get a tuple of containing credentials for the supplied provider, chosen at random"""
        res = self.get_credentials_all(provider_name)
        return None if len(res) == 0 else res[0]

    def get_credentials_all(self, provider_name):
        """Get a list of tuples containing credentials for the supplied provider."""
        credentials = self.session.get(f'/providers/{provider_name}').json()
        res = []
        for cred in credentials['links']:
            single_credentials_link = cred['href']
            try:
                single_credentials = self.session.get(
                    single_credentials_link,
                ).json()
                login = single_credentials['credentials']['login']
                password = single_credentials['credentials']['password']
                res.append((login, password))
            except JSONDecodeError:
                continue
        return res

    def get_providers(self):
        """get a tuple containing the names providers for which we have at least a credential available"""
        providers = self.session.get(f'/providers').json()
        providers_links = [provider['name'] for provider in providers]
        return providers_links
