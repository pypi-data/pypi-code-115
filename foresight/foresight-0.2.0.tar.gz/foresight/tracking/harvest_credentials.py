from pathlib import Path
from typing import Optional

from tomlkit.toml_file import TOMLFile

from foresight.locations import CONFIG_DIR

LAYOUT = """\
[credentials]
account_id = ""
personal_access_token = ""
"""


class HarvestCredentials:
    def __init__(self):
        config_dir = Path(CONFIG_DIR)
        if not config_dir.exists():
            config_dir.mkdir()

        self.file = TOMLFile(config_dir / "harvest.toml")

        path = self.file.path
        if not path.exists():
            path.touch(mode=0o600)
            path.write_text(LAYOUT)

        self.credentials = self.file.read()

    @property
    def account_id(self) -> Optional[str]:
        credentials = self.credentials.get("credentials")
        return credentials.get("account_id")

    @property
    def personal_access_token(self) -> Optional[str]:
        credentials = self.credentials.get("credentials")
        return credentials.get("personal_access_token")

    def update_credentials(self, account_id: str, personal_access_token: str) -> None:
        self.credentials["credentials"]["account_id"] = account_id
        self.credentials["credentials"]["personal_access_token"] = personal_access_token
        self.file.write(self.credentials)
