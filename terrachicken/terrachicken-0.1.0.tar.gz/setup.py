# -*- coding: utf-8 -*-
from setuptools import setup

packages = \
['terrachicken',
 'terrachicken.functions',
 'terrachicken.src',
 'terrachicken.utils']

package_data = \
{'': ['*'], 'terrachicken': ['templates/*']}

install_requires = \
['Jinja2==3.0.3',
 'PyGithub==1.55',
 'python-dotenv==0.19.2',
 'terrasnek==0.1.9',
 'typer==0.3.2']

entry_points = \
{'console_scripts': ['terrachicken = terrachicken.main:app']}

setup_kwargs = {
    'name': 'terrachicken',
    'version': '0.1.0',
    'description': 'CLI Tool to configure Terraform Cloud Workspaces and Git Repos',
    'long_description': '# TerraChicken (Terra🐓)\n\nTerrachicken is a `cli` tool for interacting with Terraform Cloud Workspaces. Terra🐓 allows users to create, list, and delete TFC Workspaces. Terra🐓 supports configuring VCS backed workspaces for Github and Gitlab (Future Version). Terra🐓 was developed to help solve the 🐓 and 🥚 problem with Terraform Cloud automation. Allowing developers and practitioners an easy way to create and destroy workspaces from the command line. Terra🐓 even generates `Terraform Backend` configurations. *This project was created to help solve problems but more so to learn Python and CLI development*\n\n## Prerequisites \n1. `Python 3.6+`\n2. Terraform Cloud Account [Here](https://app.terraform.io/signup/account) - Free Account Works\n3. Github Account \n\n## Installation\n\nTo install Terra🐓 you can pull the package down for PyPi with the pip using the command below \n**Note** Terra🐓 uses libraries that have a hard dependency on `Python 3.6+`. You will need to have that version or newer\n\n`pip install terrachicken` \n\n## Configuration \n\nTerraChicken only supports Environment Variables currently. Future versions will have built in functionality to support initial configuration.\n\n1. `Environment Variables` \n\n\n### Environment Variables\n\n- `TFC_TOKEN` - API Token generated from Terraform Cloud Settings. \n- `TFC_URL` - Terraform Cloud URL (app.terraform.io) unless using Terraform Enterprise\n- `TFC_ORG` - Terraform Cloud Organiztion Name\n- `GIT_TOKEN` - Github Developer Access Token (Repo CRUD Perms at minimum)\n\nTo set an environment token use the following `export TFC_URL=\'app.terraform.io\'`\n\n\nHint: *After you set your tokens. You can install the built in `auto completion` with the `terrachicken --install-completion` command.*\n\n## Using Terra🐓\n\n## Creating Workspaces\n\nTerra🐓 supports creating `Local` and `VCS` or Version Control System (Github/Gitlab) workspaces. \n\n### Local Workspaces\nExample:\n\n`terrachicken create workspace local` \n\nYou will be prompted to enter a `name` for your workspace. After a successful completion your new Workspace ID will be printed to the terminal.\n\n### VCS Workspace\n\n`terrachicken create workspace vcs`\n\n**Note: The Github OAuth provider must be configured in Terraform Cloud prior to building VCS workspaces.**\n\nCreating a VCS backed workspace requires you to either create a repo or link and existing repo to the workspace. The default is to create a Github Repo along side the workspace. \n\n\n## Generating Terraform Block Configurations\nExample:\n\n`terrachicken create workspace vcs --name TerrachickenTest1 --generate`\n\nExample `rendered_main.tf`:\n\n```hcl\nterraform {\n  cloud { \n    organization = "aBakersDozen"\n\n    workspaces {\n      name = "TerrachickenTest1"\n    }\n  }\n}\n```\n\nBoth `create workspace local` and `create workspace vcs` support generating a Terraform Block configuration to be implemented inside of your Terraform code. To read more about the Terraform Block Syntax click [here](https://www.terraform.io/language/settings). Using the `--generate` or `-g` option at the end of the command will output a `rendered_main.tf` file to your current working directory. \n\nThe Terraform Block settings will differ based on your workspace type. If you are creating a `local` workspace. The configuration sets `backend` with your workspace name. If you are creating a `vcs` workspace the configuration sets the `cloud` block. To use the VCS generated main.tf file, you will need to run the `terraform login` command if you want to execute cli commands for terraform. Click [here](https://www.terraform.io/cli/cloud/settings) to read about `cloud block` and `terraform login`.\n\n#### Create Workspace VCS Options\n\n- `--name`: Name of Workspace\n- `--generate`: Generate Terraform Block Configuration\n- `--out`: Exports TFC Configuration via `payload.json` \n- `--tfversion`: Set Terraform Version in Workspace\n- `--create_repo`: Create Repo or nah\n- `--private`: Set Github Repo to Private\n- `--public`: Set Github Repo to Public\n  \n\n## TO-DO\n\n2. `terrachicken init` command allows you to add your tokens. **Note** If you are using an Env Var labeled `TFC_TOKEN` , `TFC_URL` or `GIT_TOKEN`. Those ENV Vars will take priority\n\nTO-DO: Add TC backstory\nTO-DO: Add init configurations to set default OAuth Client\nTO-DO: Add --repo flag to copy --name flag\nTO-DO: Add Gitlab VCS Options\nTO-DO: Remove the utils.bcolors class, sub for the rich library\nTO-DO: Add option to delete workspace and repo at same time.\nTO-DO: Add more options to the TF Workspace Configuration.',
    'author': 'Thaley17',
    'author_email': 'tyler.haley.17@outlook.com',
    'maintainer': None,
    'maintainer_email': None,
    'url': 'https://github.com/Thaley17/TerraChicken',
    'packages': packages,
    'package_data': package_data,
    'install_requires': install_requires,
    'entry_points': entry_points,
    'python_requires': '>=3.9,<4.0',
}


setup(**setup_kwargs)
