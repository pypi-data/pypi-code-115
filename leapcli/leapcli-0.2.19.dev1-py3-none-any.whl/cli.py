"""Tensorleap CLI.

Usage:
  leap init (--tensorflow|--pytorch) (PROJECT) (ORG) (DATASET) [--url=<URL>]
  leap login [API_ID] [API_KEY]
  leap check (--all|--exclude-model|--exclude-dataset)
  leap push (--all|--model|--dataset) [--branch-name=<BRANCH_NAME>]
            [--description=<DESCRIPTION>] [--model-name=<MODEL_NAME>] [--secret=<SECRET_NAME>]
  leap get (secret)

Arguments:
  EXPERIMENT    Name of experiment.
  PROJECT       Project name (default: current directory name).
  ORG           Organization name (default: Git origin).

Options:
  -h --help     Show this screen.
  --version     Show version.
"""

import os
import sys
from typing import Callable, Dict
from pathlib import Path
from docopt import docopt
from openapi_client.exceptions import NotFoundException, UnauthorizedException

from leapcli.enums import ResourceEnum
from leapcli.get import Get
from leapcli.project import Project, Framework, VALID_PROJECT_EXPL, \
    VALID_ORG_EXPL, TENSORLEAP_DIR, CONFIG_FILENAME
from leapcli.exceptions import MalformedKeys, KeysMixedUp, AlreadyInitialized, \
    InvalidProjectName, InvalidOrgName
from leapcli.login import Authenticator
from leapcli.doctor import Doctor
from leapcli.log import configure_logging
from leapcli.push import Push


def __main__():
    # Add user repo path
    sys.path.insert(0, str(Path('.')))

    configure_logging()
    arguments = docopt(__doc__)
    if arguments['init']:
        init_command(arguments)
    if arguments['login']:
        login_command(arguments)
    if arguments['check']:
        check_command(arguments)
    if arguments['push']:
        push_command(arguments)
    if arguments['get']:
        get_command(arguments)


def eof_handler(func: Callable):
    def inner(*args, **kwargs):
        try:
            func(*args, **kwargs)
        except EOFError:
            sys.exit(0)

    return inner


def complain(text: str):
    print(text, file=sys.stderr)
    sys.exit(1)


@eof_handler
def login_command(arguments: dict):
    project = Project(os.getcwd())
    if not project.is_initialized():
        complain('Tensorleap project not initialized.\n'
                 'Did you run `leap init`?')

    if arguments['API_ID'] is not None and arguments['API_KEY'] is None:
        complain(f'Either supply both API_ID and API_KEY or neither.\n'
                 f'{__doc__}')
    try:
        api_id = arguments.get('API_ID')
        api_key = arguments.get('API_KEY')
        if api_id is None:
            api_id = input('API ID: ')
            if api_key is None:
                api_key = input('API Key: ')

        Authenticator.initialize(project, api_id, api_key, should_write_credentials=True)
        print(f'Authenticated as {Authenticator.user.local.email}')

    except MalformedKeys:
        complain(f'Invalid API_ID or API_KEY.\n'
                 f'{__doc__}')
    except KeysMixedUp:
        complain(f'API_ID should come before API_KEY.\n'
                 f'{__doc__}')
    except NotFoundException:
        complain('❗️ Login failed. Check the API_ID provided.')
    except UnauthorizedException:
        complain('❗️ Login failed. Check the API_KEY provided.')


@eof_handler
def check_command(arguments: Dict):
    should_check_model = not arguments['--exclude-model']
    should_check_dataset = not arguments['--exclude-dataset']
    project = Project(os.getcwd())
    Doctor(project).run(should_check_model, should_check_dataset)


@eof_handler
def push_command(arguments):
    should_push_model = arguments['--model']
    should_push_dataset = arguments['--dataset']

    project = Project(os.getcwd())
    Push(project).run(should_push_model, should_push_dataset,
                      arguments.get('--branch-name'),
                      arguments.get('--description'),
                      arguments.get('--model-name'),
                      arguments.get('--secret'))


@eof_handler
def init_command(arguments: Dict):
    framework = Framework.TENSORFLOW if arguments['--tensorflow'] else Framework.PYTORCH
    try:
        initializer = Project(os.getcwd())
        initializer.init_project(framework,
                                 arguments.get('PROJECT'),
                                 arguments.get('ORG'),
                                 arguments.get('DATASET'),
                                 arguments.get('--url'))
        print(f'Tensorleap project initialized in {TENSORLEAP_DIR}')
    except AlreadyInitialized:
        expected_conf = Path(TENSORLEAP_DIR).joinpath(CONFIG_FILENAME)
        complain(f'Tensorleap project already initialized.\n'
                 f'See {expected_conf}')
    except InvalidProjectName:
        complain(f'Invalid project name. Rules:\n{VALID_PROJECT_EXPL}')
    except InvalidOrgName:
        complain(f'Invalid organization name. Rules:\n{VALID_ORG_EXPL}')


@eof_handler
def get_command(arguments: Dict):
    resource = None
    if ResourceEnum.secret.name in arguments:
        resource = ResourceEnum.secret

    project = Project(os.getcwd())
    get = Get(project)
    get.run(resource)


if __name__ == '__main__':
    __main__()
