import cameo_fastapi
import json
import gspread
from fastapi import APIRouter
from oauth2client.service_account import ServiceAccountCredentials
from cameo_sheet import base

router = APIRouter()

gspread_client = None


def init(str_api_key_base):
    print('001 cameo_sheet.py, init, str_api_key_base', str_api_key_base)
    global gspread_client
    scope = [
        "https://spreadsheets.google.com/feeds",
        'https://www.googleapis.com/auth/spreadsheets',
        "https://www.googleapis.com/auth/drive.file",
        "https://www.googleapis.com/auth/drive"
    ]
    str_google_sheet_api_base = str_api_key_base
    dic = json.loads(base.decode(str_google_sheet_api_base))
    credentials = ServiceAccountCredentials.from_json_keyfile_dict(dic, scope)
    gspread_client = gspread.authorize(credentials)
    print('002 cameo_sheet.py, gspread_client', gspread_client)
    return gspread_client


@router.get('/api/cameo_sheet/get_all_values/',
            description='Read google sheet content, search by filename<br/>'
                        'command="get_all_values" #return list of list<br/>'
                        'command="get_all_records" #return list of dictionary',
            response_description='lst_values #default list of list')
def get_all_values(
        spreadsheet: str = '植樹遊戲_任務題目.sheet',
        worksheet: str = 'A單選記憶類題目',
        command: str = "get_all_values"):
    global gspread_client
    print('003 cameo_sheet.py, gspread_client', gspread_client)
    if gspread_client == None:
        return 'Error, gspread_client==None, please call cameo_sheet.init(str_api_key_base)'
    spreadsheet = gspread_client.open(spreadsheet)
    if worksheet == '':
        worksheet = spreadsheet.worksheets()[0]
    else:
        worksheet = spreadsheet.worksheet(worksheet)
    lst_values = []
    if command == 'get_all_values':
        lst_values = worksheet.get_all_values()
    if command == 'get_all_records':
        lst_values = worksheet.get_all_records()
    return lst_values


app = cameo_fastapi.init()
app.include_router(router)


def run():
    cameo_fastapi.run('cameo_sheet:app')

# done 2022-04-01 13:23 push to github cameo_sheet2
# done 2020-04-01 13:20 sync to cameo_fastapi package
# change log: 2022-04-01 13:00 init_gspread to init
