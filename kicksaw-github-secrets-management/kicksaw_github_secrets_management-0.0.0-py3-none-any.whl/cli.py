import click
import json
import os

from kicksaw_github_secrets_management.script import (
    owner_and_repo,
    repository_info,
    encrypt_secret,
    push_secrets_to_github,
)


@click.command("github-secrets-mgmt")
def main():
    """
    1. Get github public auth key from local env
    2. Get current repo name based on current dir
    3. Get repo public key
    4. Loop through `config-github.json` file and:
        - Ask to provide secret value for specific key
        - Encrypt provided secret
        - Save to dictionary
    5. Push secrets to github repo
    """
    # check for the file right away
    with open(
        "config-github.json",
    ) as github_config_file:
        github_config = json.load(github_config_file)

    key = "GITHUB_ACCESS_TOKEN"
    github_access_token = os.getenv(key)

    assert github_access_token, f"Environment variable {key} not set"

    owner_repo_array = owner_and_repo()
    owner = owner_repo_array[0]
    repo_name = owner_repo_array[1]

    repo_key_info = repository_info(github_access_token, owner, repo_name)
    repo_key = repo_key_info[0]
    key_id = repo_key_info[1]

    user_provided_secrets = {}

    # Prompt user for secret and encrypt
    for key in github_config:
        prompt = f"Please provide the secret for key: {key}"
        repo_secret = input(prompt + " (or press enter to skip):\n")
        if not repo_secret:
            continue
        encrypted_secret = encrypt_secret(repo_key, repo_secret)
        user_provided_secrets[key] = encrypted_secret

    push_secrets_to_github(
        owner, repo_name, key_id, user_provided_secrets, github_access_token
    )
