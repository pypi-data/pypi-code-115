import argparse
import json
import pathlib
from configparser import ConfigParser

from laetitudebots.model.config import Config


def _get_values(config_file_path, stage):
    config_file = ConfigParser()
    config_file.read(config_file_path)

    values = {}
    values['key'] = config_file[stage]['key']
    values['data'] = json.loads(config_file[stage]['data'])

    return values


def migrate(config_file, stage, api_key, api_secret):
    config_file_path = pathlib.Path(config_file).absolute()
    config_values = _get_values(config_file_path, stage)
    config_values['data']['api_key'] = api_key
    config_values['data']['api_secret'] = api_secret
    config = Config(key=config_values['key'], data=config_values['data'])
    resp = config.save(True)

    return resp


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        '--config_file',
        help='A .cfg file containing the key and the config data to migrate',
    )
    parser.add_argument('--stage', help='stage to migrate. dev | prod')
    parser.add_argument('--api_key')
    parser.add_argument('--api_secret')
    args = parser.parse_args()

    migrate_resp = migrate(
        args.config_file, args.stage, args.api_key, args.api_secret
    )
    print(migrate_resp)
