from pathlib import Path
from typing import Any

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from tomlkit.toml_file import TOMLFile

from foresight.locations import CONFIG_DIR


def create_google_calendar_service() -> Any:
    scopes = ["https://www.googleapis.com/auth/calendar.events"]

    config_dir = Path(CONFIG_DIR)
    if not config_dir.exists():
        config_dir.mkdir()

    file = config_dir / "credentials.json"
    if not file.exists():
        file.touch(mode=0o600)

    creds = None

    if file.exists():
        creds = Credentials.from_authorized_user_file(str(file))
        return build("calendar", "v3", credentials=creds)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            client_secrets = Path(__file__).parent / "credentials.json"
            flow = InstalledAppFlow.from_client_secrets_file(client_secrets, scopes)
            creds = flow.run_local_server(port=0)

        # Save the credentials for the next run
        file.write_text(creds.to_json())

    return build("calendar", "v3", credentials=creds)


def create_harvest_credentials() -> Any:
    config_dir = Path(CONFIG_DIR)
    if not config_dir.exists():
        config_dir.mkdir()

    file = TOMLFile(config_dir / "harvest.toml")

    path = file.path
    if not path.exists():
        path.touch(mode=0o600)
