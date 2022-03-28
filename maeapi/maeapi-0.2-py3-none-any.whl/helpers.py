import json

def read_customer_key(x):
    return x["customerKey"]

def initialize_headers():
    return {
        "HOST" : "maya.maybank2u.com.my",
        "Content-Type" : "application/json",
        "Connection" : "close",
        "x-app-platform" : "IOS",
        "Accept" : "application/json",
        "Accept-Language" : "en-US,en;q=0.9",
        "Accept-Encoding" : "gzip, deflate, br",
        "x-app-environment" : "",
       
    }
def get_authorization(header):
    return "bearer " + header["access_token"]
