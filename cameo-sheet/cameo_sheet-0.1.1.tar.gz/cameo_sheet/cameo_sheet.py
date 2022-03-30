import gspread
from fastapi import APIRouter
from oauth2client.service_account import ServiceAccountCredentials
from starlette.responses import HTMLResponse

router = APIRouter()


def hi():
    print('cameo sheet love you oh~')


@router.get('/sheet/get_rows/')
def get_rows(str_spreadsheet: str = '植樹遊戲_任務題目.sheet',
             str_worksheet: str = 'A單選記憶類題目'
             ):
    return [1, 2, 3]
