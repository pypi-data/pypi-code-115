import uvicorn
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
import os
from pathlib import Path
from fastapi.middleware.cors import CORSMiddleware


def init():
    app = FastAPI(docs_url="/d", redoc_url=None, openapi_url="/o.json")
    app.add_middleware(CORSMiddleware,
                       allow_origins=['*'],
                       allow_credentials=True,
                       allow_methods=['*'],
                       allow_headers=['*'])
    return app


app = init()


def run(app_name='cameo_fastapi:app'):
    ip='0.0.0.0'
    int_port=20330
    print(f'open http://{ip}:{int_port}/d')
    uvicorn.run(app_name, host=ip, port=int_port, reload=True, debug=False, workers=1)
