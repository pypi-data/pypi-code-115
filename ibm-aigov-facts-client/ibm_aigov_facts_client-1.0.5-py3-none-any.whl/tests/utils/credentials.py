import json
import os


def __load_json_from_file(file_path):
    with open(file_path) as json_file:
        return json.load(json_file)


CREDENTIALS_PATH = os.path.join("tests/credentials", "credentials.json")
CREDENTIALS = __load_json_from_file(CREDENTIALS_PATH)


def get_facts_client_credentials():
    return CREDENTIALS['facts_client_credentials']

def get_wml_client_credentials():
    return CREDENTIALS['wml_credentials']

def get_facts_client_credentials_cp4d():
    return CREDENTIALS['facts_client_credentials_cp4d']

def get_wml_client_credentials_cp4d():
    return CREDENTIALS['wml_credentials_cp4d']
