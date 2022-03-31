import json, os
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from datetime import date, datetime, timedelta

class Client:
    def __init__(self, credentials: str = "credentials.json", token_store: str = "tokens.json", reclaim_task_list_id: str = None):
        if not os.path.isfile(credentials):
            raise Exception(f"{credentials} file was not found.")
        self._creds_file = credentials
        self._tokens = token_store
        self._creds = None
        self._SCOPES = ['https://www.googleapis.com/auth/tasks', 'https://www.googleapis.com/auth/tasks.readonly']
        self._reclaim_list_id = reclaim_task_list_id
    
    @property
    def authorized(self) -> bool:
        return os.path.isfile(self._tokens) and self._creds and self._creds.valid
    

    def do_authorization(self):
        if os.path.isfile(self._tokens):
            self._creds = Credentials.from_authorized_user_file(self._tokens, self._SCOPES)
        if not self._creds or not self._creds.valid:
            if self._creds and self._creds.expired and self._creds.refresh_token:
                self._creds.refresh(Request())
            else:
                print("Authorize the application. Make sure to tick the requested permissions. It is expected that this application is labled 'Unapproved'")
                flow = InstalledAppFlow.from_client_secrets_file(self._creds_file, self._SCOPES)
                self._creds = flow.run_local_server(port=0)

        with open(self._tokens, 'w') as token:
            token.write(self._creds.to_json())


    def create_task(self, is_work: bool, title: str, duration: timedelta, due_at: datetime, not_before: datetime = datetime.now()) -> bool:
        assert self.authorized

        service = build('tasks', 'v1', credentials=self._creds)
        if not self._reclaim_list_id:
            tasklists = service.tasklists().list(maxResults=10).execute()
            list_items = tasklists.get('items', [])
            self._reclaim_list_id = [i["id"] for i in list_items if i["title"] == "🗓 Reclaim"][0]
        _due_at = due_at.strftime("%B %-d %Y %-H:%M %p")
        _not_before = not_before.strftime("%B %-d %Y %-H:%M %p")
        _duration = str(int(duration.total_seconds()/60)) + "min"

        result = service.tasks().insert(tasklist=self._reclaim_list_id, body= {
                "title": f"{title} (for {_duration} due {_due_at} not before {_not_before} type {'work' if is_work else 'personal'})"
            }).execute()
        if result:
            return True
        else:
            return False