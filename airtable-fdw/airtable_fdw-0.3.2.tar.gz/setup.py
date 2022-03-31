# -*- coding: utf-8 -*-
from setuptools import setup

packages = \
['airtable_fdw']

package_data = \
{'': ['*']}

install_requires = \
['airtable-python-wrapper==0.15.3']

setup_kwargs = {
    'name': 'airtable-fdw',
    'version': '0.3.2',
    'description': 'Airtable Multicorn FDW for Postgres',
    'long_description': '# Airtable Foreign Data Wrapper\n\n## Installation\n\n### Requirements\n\nPostgreSQL 9.1+ with [Multicorn](http://multicorn.org/) extension installed.\n\n### Loading extension and defining FDW server\n\nEnsure multicorn is loaded and define Foreign Data Wrapper for airtable\n\n```postgresql\ncreate extension if not exists multicorn;\ncreate server if not exists multicorn_airtable_srv foreign data wrapper multicorn options (\n    wrapper \'airtable_fdw.AirtableFDW\'\n);\n```\n\n## Usage\n\nDefine table as\n\n```postgresql\ncreate foreign table schema.table_name (\n    "_id" varchar options (rowid \'true\'),                       -- column used as rowid, may be any name, \n                                                                -- should appear only onece\n    "Some text column" varchar,\n    "Some numeric column" numeric,\n    "Some date column" date,\n    "Some complex column" json,                                 -- can be used for complex fields but see example below \n    "Some json nullable column" json options (nulljson \'true\'), -- keep nulls as json (\'null\'::json instead of null::json)\n    "Some computed column" varchar options (computed \'true\')    -- column that won\'t be modified with update\n                                                                -- may appear multiple times\n) server multicorn_airtable_srv options (\n    api_key \'...\',      -- api access key\n    base_key \'...\',     -- database identifier\n    table_name \'...\',   -- name of table to read from\n    view_name \'...\',    -- optional view name, if not present raw table will be read\n    rowid_column \'...\'  -- optional rowid column name will be used if no column has `rowid` option set \n);\n```\n\nIf complex column - like `Collaborator` - appears in table it is read from AirTable API as a `json` and could be treated as `json` or as a complex, custom defined type.\n\n```postgresql\ncreate type AirtableCollaborator as\n(\n    id     varchar,\n    email  varchar,\n    "name" varchar\n);\ncreate foreign table schema.table_name (\n    "_id" varchar options (rowid \'true\'),\n    "editor" AirtableCollaborator options (complextype_fields \'id,email,name\', complextype_send \'email\')\n) server multicorn_airtable_srv options (\n    api_key \'...\',\n    base_key \'...\',\n    table_name \'...\'\n);\n\n```\n\nwhere:\n* `complextype_fields \'id,email,name\'` indicates how record string should be constructed from `json` - so `{"id": "someid", "email": "me@example.com", "name":"My Name"}` will be converted to `(someid,me@example.com,My Name)` and will be correctly casted to `AirtableCollaborator` type.\n* `complextype_send \'email\'` means that when this field is modified only `email` field will be sent to API\n\n### Usage Tips\n\n* Use `AND` in `WHERE` clause whenever possible, `OR`s are not handled well (at all?) by *multicorn* so unconditional queries are sent to Airtable (watch the quota!).\n* If `OR` is required try to replace it with  `IN (...)`\n\n## Features\n\n* Configurable to read from given base / table / view\n* SQL `WHERE` clause transformed to `formula` query (so number of requests to API is optimized)\n* Batch `INSERT`/`UPDATE`/`DELETE`\n* support for complex types - json is parsed to complex type on read (`SELECT`), and single, selected field is set on write (`INSERT`, `UPDATE`)',
    'author': 'Sebastian Szymbor',
    'author_email': 'thesebas@users.noreply.github.com',
    'maintainer': None,
    'maintainer_email': None,
    'url': None,
    'packages': packages,
    'package_data': package_data,
    'install_requires': install_requires,
    'python_requires': '>=3.7,<4.0',
}


setup(**setup_kwargs)
