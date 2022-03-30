import uvicorn
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
import os

app = FastAPI()
if not os.path.exists('static'):
    os.mkdir('static')
app.mount("/static", StaticFiles(directory="static"), name="static")


def run():
    uvicorn.run("cameo_fastapi:app", host='0.0.0.0', port=20330, reload=True, debug=False, workers=1)


if __name__ == '__main__':
    run()

