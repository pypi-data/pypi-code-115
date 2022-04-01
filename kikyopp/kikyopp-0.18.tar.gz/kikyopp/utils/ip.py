import requests

from kikyopp.utils.constants import RETRY_API_TIMES, IPSEARCH_HOST
from kikyopp.utils.retry import retry_rest_api


@retry_rest_api(RETRY_API_TIMES)
def get_ip_info(ip: str):
    resp = requests.post(
        f'{IPSEARCH_HOST}/api/ipsearch',
        json={'ip': ip},
        timeout=20,
    )
    resp.raise_for_status()
    return resp.json()['res']
