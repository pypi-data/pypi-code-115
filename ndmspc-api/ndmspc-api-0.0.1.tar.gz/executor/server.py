import re
import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from typing import List, Optional
from pydantic import BaseModel
from os import system
from executor import Executor
from enum import Enum

class Pod(BaseModel):
    name: str
    image: str
    labels: str

class Run(BaseModel):
    type: str
    pod: Pod

class Salsa(BaseModel):
    host: str
    job_type: str # either template or command (-t or -c)

class Dirac(BaseModel):
    host: str

class RequestBody(BaseModel):
    type: str
    subtype: str
    command: str
    args: str
    salsa: Optional[Salsa] = None
    dirac: Optional[Dirac] = None
    run: Optional[Run] = None
    bins: Optional[List[dict]] = []
    numberOfTasks: Optional[int] = 1
    indexes: Optional[str] = '1'

app = FastAPI()

origins = ["*"]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)

def execute(command_str):
    print('Executing {}'.format(command_str))
    exit_code = system(command_str)
    exit_code >>= 8
    print("Exit code was {}.".format(exit_code))
    return exit_code

@app.get("/")
def root():
    return {"status": "ok"}

@app.post("/")
async def process(body: RequestBody):
    executor = Executor()
    command_str = executor.execute(body)

    if type(command_str) == list:
        exit_codes = []
        for cmd in command_str:
            exit_codes.append(parse_command_output(cmd + ' 2>&1 | tee stdout.txt', body.type))
        return {'status':'ok', 'rc': exit_codes}
    exit_code = parse_command_output(command_str + ' 2>&1 | tee stdout.txt', body.type)
    if exit_code['job'] == '':
        exit_code['status'] = 'error'
        exit_code['rc'] = 127 if exit_code['rc'] == 0 else exit_code['rc']
    return exit_code

def parse_command_output(cmd, type, cmd_prefix = 'timeout 10s '):
    exit_code = execute(cmd_prefix + cmd)
    regex = "-m (?P<manager>[A-Z0-9]*) -j (?P<job>[A-Z0-9]*)" if type == 'salsa' else "(?P<job>[0-9]*)"
    with open('stdout.txt', 'r') as f:
        filedata = f.read()
        match = re.search(regex, filedata)
        if match is not None:
            manager = match.group('manager') if type == 'salsa' else ''
            job = match.group('job')
        else:
            manager = ''
            job = ''
            exit_code = 1 if exit_code != 124 else exit_code
    return {
        'status': 'ok' if exit_code == 0 else 'error', 
        'rc': exit_code, 
        'manager': manager, 
        'job': job,
        'cmd': cmd
    }


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=3002)
