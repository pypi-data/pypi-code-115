from urllib.parse import parse_qs, urlsplit
from json import loads


def get_params(environ):
    try:
        url = environ['fc.request_uri']
        query = urlsplit(url).query
        params = dict(parse_qs(query))
        key_list = params.keys()
        temp_params = {}
        for index in key_list:
            temp_params[index] = params[index][0]
        return temp_params
    except Exception as e:
        return e.args


def get_json(environ):
    # get request_body
    try:
        request_body_size = int(environ.get('CONTENT_LENGTH', 0))
    except ValueError:
        request_body_size = 0

    try:
        # get param here
        request_body = environ['wsgi.input'].read(
            request_body_size).decode('utf-8')

        request_body = loads(request_body)
        return request_body
    except Exception as e:
        return e.args
