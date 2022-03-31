from foresight.tracking.harvest_credentials import HarvestCredentials


class Harvest:
    def __init__(self, credentials: HarvestCredentials) -> None:
        self.credentials = credentials

    def is_authenticated(self) -> bool:
        credentials = self.credentials

        return credentials.account_id and credentials.personal_access_token

    def authenticate(self, account_id: str, personal_access_token: str) -> None:
        self.credentials.update_credentials(account_id, personal_access_token)
