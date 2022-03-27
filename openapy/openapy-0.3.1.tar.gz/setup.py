# -*- coding: utf-8 -*-
from setuptools import setup

packages = \
['openapy', 'openapy.commands']

package_data = \
{'': ['*'], 'openapy': ['examples/*']}

install_requires = \
['single-source>=0.2,<0.4']

entry_points = \
{'console_scripts': ['openapy = openapy.main:main']}

setup_kwargs = {
    'name': 'openapy',
    'version': '0.3.1',
    'description': '',
    'long_description': '![openapy Logo](https://raw.githubusercontent.com/edge-minato/openapy/main/docs/img/logo.jpg)\n\n[![pypi version](https://img.shields.io/pypi/v/openapy.svg?style=flat)](https://pypi.org/pypi/openapy/)\n[![python versions](https://img.shields.io/pypi/pyversions/openapy.svg?style=flat)](https://pypi.org/pypi/openapy/)\n[![license](https://img.shields.io/pypi/l/openapy.svg?style=flat)](https://github.com/edge-minato/openapy/blob/master/LICENSE)\n[![Unittest](https://github.com/edge-minato/openapy/actions/workflows/unittest.yml/badge.svg)](https://github.com/edge-minato/openapy/actions/workflows/unittest.yml)\n[![codecov](https://codecov.io/gh/edge-minato/openapy/branch/main/graph/badge.svg?token=YDZAMKUNS0)](https://codecov.io/gh/edge-minato/openapy)\n[![Code style](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black")\n[![Downloads](https://pepy.tech/badge/openapy)](https://pepy.tech/project/openapy)\n[![Downloads](https://pepy.tech/badge/openapy/week)](https://pepy.tech/project/openapy)\n\n`Openapy` simplifies continuous development with [OpenAPI generator](https://github.com/OpenAPITools/openapi-generator).\nWhat this tool does is reading python source files and copying functions into individual files.\nThis will prevent the openapi generator from overwriting the code you have written.\n\n- **Documentation**: https://openapy.readthedocs.io\n- **Dockerhub**: https://hub.docker.com/r/edgem/openapy\n- **Source Code**: https://github.com/edge-minato/openapy\n\n## Quick start\n\n```sh\ndocker run --rm -v "$PWD:/src" edgem/openapy \\\nopenapy generate --src /src/openapi-server/apis\n```\n\n```sh\npip install openapy\nopenapy generate --src ./openapi-server/apis\n```\n\n## What openapy does\n\n`Openapy` just splits each of the functions into a single file under `processor` directory.\n\n```sh\n# processor directory and the files will be generated\n .\n ├── api\n │   └── source.py\n#└── processor\n#    ├── __init__.py\n#    ├── function_a.py\n#    └── function_b.py\n```\n\n```python\n# api/source.py\ndef function_a(name: str, age: int)->None:\n    ...\n\ndef function_b(height: int, weight: int)-> int:\n    ...\n```\n\nThis command generates following files\n\n```sh\nopenapy generate --src ./api\n```\n\n```python\n# processor/__init__.py\nfrom .function_a import function_a # noqa: F401\nfrom .function_b import function_b # noqa: F401\n```\n\n```python\n# processor/function_a.py\ndef function_a(name: str, age: int)->None:\n    ...\n```\n\n```python\n# processor/function_b.py\ndef function_b(height: int, weight: int)-> int:\n    ...\n```\n\n## Working with `OpenAPI generator`\n\nThe expected usage is using the file generated with `OpenAPI Generator` as interfaces, and using the file generated with `Openapy` as the implementation.\n\n```python\n# apis/pet_api.py\nimport .processor\nfrom fastapi import APIRouter\nrouter = APIRouter()\n\n@router.get("/pet/{petId}")\nasync def get_pet_by_id(petId: int = Path(None, description="ID of pet to return")) -> Pet:\n    return processor.get_pet_by_id(petId)\n```\n\n```python\n# processor/get_pet_by_id.py\ndef get_pet_by_id(petId: int) -> Pet:\n    """Returns a single pet"""\n    # implement me\n    ...\n```\n\nIn this use case, `api.mustache` file should be customized. It is possible to generate an example of mustache file with following command.\n\n```sh\nopenapy example mustache > ./mustache/api.mustache\n```\n\n**NOTE**: Without this structure, which means writing the implementation of apis on the files generated by `OpenAPI generator`, a regeneration of `OpenAPI generator` will overwrite any existing code you have written, even if only one api has been updated. This is because the `OpenAPI generator` aggregates apis into a file with a `tag`.\n\n## Features\n\n### Custom Template\n\nIt is possible to define the format of generated code with `Openapy` just like the mustache for `OpenAPI generator`. For more details, see the [documentation](https://openapy.readthedocs.io).\n\n### Difference Detection\n\nTBD\n\n### Move to docs\n\nFollowing variables with `{}` brackets are available.\n\n- **IMPORTS**: All of imports of the source file like `import X`, `from X import Y`\n- **ASSIGNS**: All assigns of the source file like `var = "string"`\n- **DEF**: `async def` or `def` of the function\n- **NAME**: The function name\n- **ARGS**: Arguments of the function with type annotations\n- **RETURN_TYPE**: A type annotation for the return of the function\n- **COMMENT**: A comment inside of the function\n- **BODY**: A body of the function, like assign statement\n- **RETURN**: A return statement of the function\n',
    'author': 'edge-minato',
    'author_email': 'edge.minato@gmail.com',
    'maintainer': None,
    'maintainer_email': None,
    'url': 'https://github.com/edge-minato/openapy',
    'packages': packages,
    'package_data': package_data,
    'install_requires': install_requires,
    'entry_points': entry_points,
    'python_requires': '>=3.9,<4.0',
}


setup(**setup_kwargs)
