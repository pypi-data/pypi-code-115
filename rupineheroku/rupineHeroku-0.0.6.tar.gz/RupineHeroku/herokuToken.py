import requests
from requests.adapters import HTTPAdapter
from urllib3.util import Retry
import json
from RupineHeroku import herokuDbAccess

def getTokenWithouName(connection, schema, chain_id, gteCreatedAt):
    
    sql = "SELECT * FROM {}.token \
           WHERE chain_id = {} AND name = 'n/a' AND created_at >= {}".format(schema, chain_id, gteCreatedAt)
    
    result = herokuDbAccess.fetchDataInDatabase(sql, connection)    
    return result[0][0]