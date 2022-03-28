import json
import os

import boto3
from botocore.exceptions import ClientError
from botocore.session import Session
from jsonschema import validate
from pynamodb.attributes import JSONAttribute, UnicodeAttribute
from pynamodb.models import Model


class SecretsManager:
    @staticmethod
    def secretize_data(secret_id, data, secret_fields, should_save_secret):
        data = dict(data)
        if should_save_secret:
            SecretsManager.save_secret(secret_id, data, secret_fields)

        for field in secret_fields:
            if field in data:
                del data[field]

        return data

    @staticmethod
    def save_secret(secret_id, data, secret_fields):
        client = boto3.client('secretsmanager')
        secret_dict = {}

        for field in secret_fields:
            secret_dict[field] = data.get(field)

        secret_string = json.dumps(secret_dict)
        try:
            client.update_secret(
                SecretId=secret_id, SecretString=secret_string
            )
        except ClientError as e:
            if e.response['Error']['Code'] == 'ResourceNotFoundException':
                client.create_secret(
                    Name=secret_id, SecretString=secret_string
                )
            else:
                raise e

    @staticmethod
    def unsecretize_data(secret_id, data, secret_fields):
        data = dict(data)
        client = boto3.client('secretsmanager')
        secret_string = client.get_secret_value(SecretId=secret_id)[
            'SecretString'
        ]
        secret_dict = json.loads(secret_string)

        for field in secret_fields:
            data[field] = secret_dict.get(field)

        return data


class Config(Model):
    class Meta:
        table_name = 'LaetitudeConfig'
        host = os.getenv('DYNAMODB_HOST')
        region = os.getenv('AWS_REGION') or Session().get_config_variable('region')

    key = UnicodeAttribute(hash_key=True)
    data = JSONAttribute(null=False)
    secret_data_fields = ['api_key', 'api_secret']

    @classmethod
    def get(cls, key):
        config = super().get(key)
        config.data = SecretsManager.unsecretize_data(
            config.key, config.data, cls.secret_data_fields
        )

        return config

    def save(self, save_secret=False):
        self.validate_data()
        self.data = SecretsManager.secretize_data(
            self.key, self.data, self.secret_data_fields, save_secret
        )
        save_resp = super().save()
        self.data = SecretsManager.unsecretize_data(
            self.key, self.data, self.secret_data_fields
        )

        return save_resp

    def validate_data(self):
        exchange_enum = [
            'bitmex',
            'binance',
            'ftx',
        ]  # TODO: import from exchange list factory
        data_schema = {
            'type': 'object',
            'properties': {
                'time_interval': {'type': 'number'},
                'time_unit': {'type': 'string'},
                'api_key': {'type': 'string'},
                'api_secret': {'type': 'string'},
                'lookback': {'type': 'number'},
                'exchange': {'type': 'string', 'enum': exchange_enum,},
                'context': {
                    'type': 'object',
                    'properties': {
                        'is_shared_balance': {'type': 'boolean'},
                        'assets': {'type': 'object'},
                    },
                    'required': ['assets'],
                },
            },
            'required': [
                'time_interval',
                'time_unit',
                'api_key',
                'api_secret',
                'lookback',
                'exchange',
            ],
        }
        asset_schema = {
            'type': 'object',
            'properties': {
                'balance': {'type': 'number'},
                'exchange': {'type': 'string', 'enum': exchange_enum,},
            },
            'required': ['exchange'],
        }

        validate(instance=self.data, schema=data_schema)

        if not len(self.data['context'].get('assets', {})):
            raise ValueError('Can\'t save config without at least one asset')
        if not self.data['context'].get('is_shared_balance'):
            asset_schema['required'].append('balance')
        for asset in self.data['context']['assets']:
            validate(
                instance=self.data['context']['assets'][asset],
                schema=asset_schema,
            )
