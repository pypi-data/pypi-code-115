import boto3
import base64
from botocore.exceptions import ClientError
import pymysql
import json

region_name = "us-east-1"

'''
def auroraCred(env):
    # auroraConnect()
    if env == "INTEG":
        secret_name = "integ/vnet/auroradb"
    elif env == "STAGING":
        secret_name = "staging/vnet/auroradb"
    elif env == "PROD":
        secret_name = "prod/vnet/auroradb"
    else:
        return {"result":"","msg": "input mismatch error"}
        
    # Create a Secrets Manager client   
    session = boto3.session.Session()
    secretmanager_client = session.client(service_name='secretsmanager', region_name=region_name )

    get_secret_value_response = secretmanager_client.get_secret_value(SecretId=secret_name)

    if 'SecretString' in get_secret_value_response:
        secretValue = get_secret_value_response['SecretString']
    else:
        secretValue = base64.b64decode(get_secret_value_response['SecretBinary'])
    
    # Return Secret Value
 
    return {"result":secretValue['result'],"msg":"SUCCESS"} '''

def auroraConnect(env,accessType):

    if env == "INTEG":
        secret_name = "integ/vnet/auroradb"
    elif env == "STAGING":
        secret_name = "staging/vnet/auroradb"
    elif env == "PROD":
        secret_name = "prod/vnet/auroradb"
    else:
        return {"result":"","msg": "input mismatch error"}
        
    # Create a Secrets Manager client   
    session = boto3.session.Session()
    secretmanager_client = session.client(service_name='secretsmanager', region_name=region_name )

    get_secret_value_response = secretmanager_client.get_secret_value(SecretId=secret_name)

    if 'SecretString' in get_secret_value_response:
        secretValue = get_secret_value_response['SecretString']
    else:
        secretValue = base64.b64decode(get_secret_value_response['SecretBinary'])
    
    # Return Secret Value
    type(secretValue)
    dbCreds=json.loads(secretValue)
    try:
        connection = pymysql.connect(host=dbCreds['host'], user=dbCreds['username'], password=dbCreds['password'], database='vnet')
    except BaseException as error:
        return {
                'Error_Flag' : True,
                'Error_UI' : 'An error occurred. Please contact the Administrator',
                'Error_DS' : 'Failed to establish a connection with the database -> %s'%error
                }

    cursor = connection.cursor()
 
    return {"dbCursor":cursor ,"msg":"SUCCESS"}


