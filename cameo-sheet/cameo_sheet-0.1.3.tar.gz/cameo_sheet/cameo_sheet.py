import json
import gspread
from fastapi import APIRouter
from oauth2client.service_account import ServiceAccountCredentials
from cameo_sheet import base

router = APIRouter()

gspread_client = None

def init_gspread(str_api_key_base):
    global gspread_client
    scope = [
        "https://spreadsheets.google.com/feeds",
        'https://www.googleapis.com/auth/spreadsheets',
        "https://www.googleapis.com/auth/drive.file",
        "https://www.googleapis.com/auth/drive"
    ]
    str_google_sheet_api_base = str_api_key_base
    dic = json.loads(base.decode_file(str_google_sheet_api_base))
    credentials = ServiceAccountCredentials.from_json_keyfile_dict(dic, scope)
    gspread_client = gspread.authorize(credentials)
    return gspread_client




# 2022-03-31 bowen 已經刪除 cache 機制
@router.get('/sheet/get_all_values/')
def get_all_values(
        str_spreadsheet: str = '植樹遊戲_任務題目.sheet',
        str_worksheet: str = 'A單選記憶類題目',
        str_get_command: str = "get_all_values"):
    spreadsheet = gspread_client.open(str_spreadsheet)
    if str_worksheet == '':
        worksheet = spreadsheet.worksheets()[0]
    else:
        worksheet = spreadsheet.worksheet(str_worksheet)
    lst = []
    if str_get_command == 'get_all_values':
        lst = worksheet.get_all_values()
    if str_get_command == 'get_all_records':
        lst = worksheet.get_all_records()
    return lst
