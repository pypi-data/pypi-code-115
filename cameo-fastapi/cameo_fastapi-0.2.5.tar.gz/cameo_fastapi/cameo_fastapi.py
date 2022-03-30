import uvicorn
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
import os
from pathlib import Path

from fastapi.middleware.cors import CORSMiddleware


def init_fastapi():
    app = FastAPI(docs_url="/d", redoc_url=None, openapi_url="/o.json")
    app.add_middleware(CORSMiddleware,
                       allow_origins=['*'],
                       allow_credentials=True,
                       allow_methods=['*'],
                       allow_headers=['*'])
    return app


app = init_fastapi()


def run():
    uvicorn.run("cameo_fastapi:app", host='0.0.0.0', port=20330, reload=True, debug=False, workers=1)
