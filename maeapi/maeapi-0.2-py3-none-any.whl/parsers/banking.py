
from maeapi.utils import nav


def parse_primary_summary_balance(response):
    return response, ['result']

def parse_all_summary_balance(response):
    return nav(response, ['result', 'accountListings'])

def parse_summary_balance_message(response):
    return response["message"]

