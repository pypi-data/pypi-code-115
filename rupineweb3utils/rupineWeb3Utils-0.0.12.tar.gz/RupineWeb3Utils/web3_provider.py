from itertools import chain
import os
from web3 import Web3
from RupineWeb3Utils.rupine_db import herokuCredentials, herokuDbAccess
from RupineWeb3Utils.web3_utils import web3_globals

def GetProviderAnkr(chain_id, connection, schema):
    username = herokuCredentials.getCredential(connection, schema, "ankr_prod", "USERNAME", 1) 
    password = herokuCredentials.getCredential(connection, schema, "ankr_prod", "PASSWORD", 1)
    url = herokuCredentials.getCredential(connection, schema, "ankr_prod", "URL", chain_id)

    endpointQuery = url.format(':'.join([username,password]))
    return Web3(Web3.HTTPProvider(endpointQuery))

def GetProviderGetBlock(chain_id, connection, schema):
    if chain_id == 1:
        api_key_getblock = herokuCredentials.getCredential(connection, schema, "GetBlock", "API KEY", 1) 
        url = 'https://eth.getblock.io/mainnet/?api_key={0}'
        endpoint = url.format(api_key_getblock)
        return Web3(Web3.HTTPProvider(endpoint))
    return None

def GetAllProvider(chain_id,prodEnv:bool=True):
    w3s = []
    #if chain_id == 1:
    #    w3s.append(GetProviderGetBlock(chain_id))

    w3s.append(GetProviderAnkr(chain_id,prodEnv))
    return w3s