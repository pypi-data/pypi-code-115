import hmac
from urllib.parse import urlencode
import requests
from calendar import timegm
from time import gmtime

def send_http_request(url, body=None, form=None, qs=None, method="GET" , headers=None, timeout = (1000 * 30), proxy=None):
    r = None
    if (method+"").upper() == "GET":
        r = requests.get(url=url, params=qs, headers=headers)
    if (method+"").upper() == "POST":
        r = requests.post(url=url, params=qs, headers=headers, data= form, json=body)
    return r

def compute_query_string_signature(qs, secret, algorithm=None):
    query_string = urlencode(qs)
    return sign_hmac(string=query_string, secret=secret,algorithm="md5" if algorithm is None else algorithm)

def sign_hmac(string, secret,algorithm=None):    
    signature = hmac.new(bytes(secret,'utf8'), bytes(string,'utf8'), ("md5",algorithm)[algorithm is None]).hexdigest()
    signature = signature.upper()
    return signature

def sign_query(qs, secret, algorithm=None):
    signature = compute_query_string_signature(qs=qs, secret=secret, algorithm="md5" if algorithm is None else algorithm)
    return signature   

def  get_query_string_mandatory_values(api_key):
    return{
        "sysKey": api_key,        
        "timestamp": timegm(gmtime())
    }

