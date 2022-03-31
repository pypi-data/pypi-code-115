from pathlib import Path
from typing import Any, Optional

from cleo.io.io import IO
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

from foresight.calendar.google_calendar import GoogleCalendar
from foresight.locations import CONFIG_DIR
from foresight.tracking.harvest import Harvest
from foresight.tracking.harvest_credentials import HarvestCredentials


class Factory:
    def __init__(self, io: IO) -> None:
        self.io = io

    def create_google_calendar(self, service: Optional[Any] = None) -> GoogleCalendar:
        if service is not None:
            return GoogleCalendar(service)

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
            return GoogleCalendar(build("calendar", "v3", credentials=creds))

        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                self.io.write_line("Refreshing your google credentials token...")
                creds.refresh(Request())
            else:
                self.io.write_line(
                    "Beginning Oauth2 flow to authenticate with the Google Calendar API..."
                )
                client_secrets = Path(__file__).parent / "credentials.json"
                flow = InstalledAppFlow.from_client_secrets_file(client_secrets, scopes)
                creds = flow.run_local_server(port=0)

            # Save the credentials for the next run
            file.write_text(creds.to_json())
            self.io.write_line(f"Saved your credentials to {file!s}")

        return GoogleCalendar(build("calendar", "v3", credentials=creds))

    def create_harvest(self) -> Harvest:
        credentials = HarvestCredentials()

        return Harvest(credentials)
