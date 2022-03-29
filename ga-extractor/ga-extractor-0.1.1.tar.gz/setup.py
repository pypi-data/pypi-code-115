# -*- coding: utf-8 -*-
from setuptools import setup

packages = \
['ga_extractor']

package_data = \
{'': ['*']}

install_requires = \
['PyYAML>=6.0,<7.0',
 'colorama>=0.4.4,<0.5.0',
 'coverage[toml]>=6.3.2,<7.0.0',
 'google-api-python-client>=2.41.0,<3.0.0',
 'google-auth-oauthlib>=0.5.1,<0.6.0',
 'shellingham>=1.4.0,<2.0.0',
 'typer>=0.4.0,<0.5.0',
 'validators>=0.18.2,<0.19.0']

entry_points = \
{'console_scripts': ['ga-extractor = ga_extractor.extractor:extractor']}

setup_kwargs = {
    'name': 'ga-extractor',
    'version': '0.1.1',
    'description': 'Tool for extracting Google Analytics data suitable for migrating to other platforms',
    'long_description': '# Google Analytics Extractor\n\n[![PyPI version](https://badge.fury.io/py/ga-extractor.svg)](https://badge.fury.io/py/ga-extractor)\n\nA CLI tool for extracting Google Analytics data using Google Reporting API. Can be also used to transform data to various formats suitable for migration to other analytics platforms.\n\n## Setup\n\nYou will need Google Cloud API access for run the CLI:\n\n- Navigate to [Cloud Resource Manager](https://console.cloud.google.com/cloud-resource-manager) and click _Create Project_\n    - alternatively create project with `gcloud projects create $PROJECT_ID`\n- Navigate to [Reporting API](https://console.cloud.google.com/apis/library/analyticsreporting.googleapis.com) and click _Enable_\n- Create credentials:\n    - Go to [credentials page](https://console.cloud.google.com/apis/credentials)\n    - Click _Create credentials_, select _Service account_\n    - Give it a name and make note of service account email. Click _Create and Continue_\n\n    - Open [Service account page](https://console.cloud.google.com/iam-admin/serviceaccounts)\n    - Select previously created service account, Open _Keys_ tab\n    - Click _Add Key_ and _Create New Key_. Choose JSON format and download it. (store this **securely**)\n\n- Give SA permissions to GA - [guide](https://support.google.com/analytics/answer/1009702#Add)\n    - email: SA email from earlier\n    - role: _Viewer_\n  \nAlternatively see <https://martinheinz.dev/blog/62>.\n\nTo install and run:\n\n```bash\npip install ga-extractor\nga-extractor --help\n```\n  \n## Running\n\n```bash\nga-extractor --help\n# Usage: ga-extractor [OPTIONS] COMMAND [ARGS]...\n# ...\n\n# Create config file:\nga-extractor setup \\\n  --sa-key-path="analytics-api-24102021-4edf0b7270c0.json" \\\n  --table-id="123456789" \\\n  --metrics="ga:sessions" \\\n  --dimensions="ga:browser" \\\n  --start-date="2022-03-15" \\\n  --end-date="2022-03-19"\n  \ncat ~/.config/ga-extractor/config.yaml  # Optionally, check config\n\nga-extractor auth  # Test authentication\n# Successfully authenticated with user: ...\n\nga-extractor setup --help  # For options and flags\n```\n\n- Value for `--table-id` can be found in GA web console - Click on _Admin_ section, _View Settings_ and see _View ID_ field\n- All configurations and generated extracts/reports are stored in `~/.config/ga-extrator/...`\n- You can also use metrics and dimensions presets using `--preset` with `FULL` or `BASIC`, if you\'re not sure which data to extract\n\n### Extract\n\n```bash\nga-extractor extract\n# Report written to /home/some-user/.config/ga-extractor/report.json\n```\n\n`extract` perform raw extraction of dimensions and metrics using the provided configs\n\n### Migrate\n\nYou can directly extract and transform data to various formats. Available options are:\n\n- JSON (Default option; Default API output)\n- CSV\n- SQL (compatible with _Umami_ Analytics PostgreSQL backend)\n\n```bash\nga-extractor migrate --format=CSV\n# Report written to /home/user/.config/ga-extractor/02c2db1a-1ff0-47af-bad3-9c8bc51c1d13_extract.csv\n\nhead /home/user/.config/ga-extractor/02c2db1a-1ff0-47af-bad3-9c8bc51c1d13_extract.csv\n# path,browser,os,device,screen,language,country,referral_path,count,date\n# /,Chrome,Android,mobile,1370x1370,zh-cn,China,(direct),1,2022-03-18\n# /,Chrome,Android,mobile,340x620,en-gb,United Kingdom,t.co/,1,2022-03-18\n\nga-extractor migrate --format=UMAMI\n# Report written to /home/user/.config/ga-extractor/cee9e1d0-3b87-4052-a295-1b7224c5ba78_extract.sql\n\n# IMPORTANT: Verify the data and check test database before inserting into production instance \n# To insert into DB (This should be run against clean database):\ncat cee9e1d0-3b87-4052-a295-1b7224c5ba78_extract.sql | psql -Upostgres -a some-db\n```\n\nYou can verify the data is correct in Umami web console and GA web console:\n\n- [Umami extract](./assets/umami-migration.png)\n- [GA Pageviews](./assets/ga-pageviews.png)\n\n_Note: Some data in GA and Umami web console might be little off, because GA displays many metrics based on sessions (e.g. Sessions by device), but data is extracted/migrated based on page views. You can however confirm that percentage breakdown of browser or OS usage does match._\n\n## Development\n\n### Setup\n\nRequirements:\n\n- Poetry (+ virtual environment)\n\n```bash\npoetry install\npython -m ga_extractor --help\n```\n\n### Testing\n\n```bash\npytest\n```\n\n### Building Package\n\n```bash\npoetry install\nga-extractor --help\n\n# Usage: ga-extractor [OPTIONS] COMMAND [ARGS]...\n# ...\n```',
    'author': 'Martin-Heinz1',
    'author_email': 'martin.heinz1@ibm.com',
    'maintainer': None,
    'maintainer_email': None,
    'url': 'https://github.com/MartinHeinz/ga-extractor',
    'packages': packages,
    'package_data': package_data,
    'install_requires': install_requires,
    'entry_points': entry_points,
    'python_requires': '>=3.8,<4.0',
}


setup(**setup_kwargs)
