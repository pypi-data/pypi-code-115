import demisto_client.demisto_api as demisto_api
import six
import os
import datetime
import tzlocal
import json

from demisto_client.demisto_api import ApiClient
from demisto_client.demisto_api.configuration import Configuration
from pkg_resources import get_distribution, DistributionNotFound
from distutils.version import LooseVersion

try:
    __version__ = get_distribution(__name__).version
except DistributionNotFound:
    # package is not installed
    __version__ = 'dev'


def configure(base_url=None, api_key=None, verify_ssl=None, proxy=None, username=None, password=None,
              ssl_ca_cert=None, debug=False, connection_pool_maxsize=None, auth_id=None):
    """
    This wrapper provides an easier to use method of configuring the API client. The base
    Configuration method is still exposed if you wish to further configure the API Client.

    To avoid hard coding configurations in your code, it is possible to specify configruation params
    as the following environment variables (env variables will be used if parameters are not specified):

    * DEMISTO_BASE_URL
    * DEMISTO_API_KEY
    * DEMISTO_USERNAME
    * DEMISTO_PASSWORD
    * DEMISTO_VERIFY_SSL (true/false. Default: true)
    * XSIAM_AUTH_ID
    * SSL_CERT_FILE (specify an alternate certificate bundle)
    * DEMISTO_CONNECTION_POOL_MAXSIZE (specify a connection pool max size)

    :param base_url: str - Base url of your Demisto instance.
    :param api_key: str - API key generated by your instance.
    :param username: str - Username of the user account.
    :param password: str - Password of the user account.
    :param verify_ssl: bool - Indicates if valid SSLs are required for connection. If not specified (None)
        will default to True.
    :param proxy: dict - Dict object of your proxy settings.
    :param ssl_ca_cert: str - specify an alternate certificate bundle
    :param debug: bool - Include verbose logging.
    :param connection_pool_maxsize: int - specify a connection max pool size
    :param auth_id: str - api_key_id only for the xsiam
    :return: Returns an API client configuration identical to the Configuration() method.
    """
    if base_url is None:
        base_url = os.getenv('DEMISTO_BASE_URL')
    if api_key is None:
        api_key = os.getenv('DEMISTO_API_KEY')
    if auth_id is None:
        auth_id = os.getenv('XSIAM_AUTH_ID')
    if username is None:
        username = os.getenv('DEMISTO_USERNAME')
    if password is None:
        password = os.getenv('DEMISTO_PASSWORD')
    if ssl_ca_cert is None:
        ssl_ca_cert = os.getenv('SSL_CERT_FILE')
    if verify_ssl is None:
        verify_env = os.getenv('DEMISTO_VERIFY_SSL')
        if verify_env:
            verify_ssl = verify_env.lower() not in ['false', '0', 'no']
        else:
            verify_ssl = True
    if connection_pool_maxsize is None:
        connection_pool_maxsize = os.getenv('DEMISTO_CONNECTION_POOL_MAXSIZE')
        if connection_pool_maxsize:
            if not connection_pool_maxsize.isdigit():
                err_msg = ('DEMISTO_CONNECTION_POOL_MAXSIZE env variable should be set to a number'
                           f' but instead received "{connection_pool_maxsize}"')
                raise ValueError(err_msg)
            else:
                connection_pool_maxsize = int(connection_pool_maxsize)
    if not base_url:
        raise ValueError('You must specify base_url either as a parameter or via env variable: DEMISTO_BASE_URL')
    if not api_key and not username:
        raise ValueError('You must specify either api_key or username/password either as parameters or use env variables:\n'
                         '* DEMISTO_API_KEY\n'
                         '* DEMISTO_USERNAME\n'
                         '* DEMISTO_PASSWORD'
                         )
    if auth_id and not api_key:
        raise ValueError('You must specify either api_key or use env variable DEMISTO_API_KEY to use Cortex XSIAM api, '
                         'or remove the auth_id and/or the env variable XSIAM_AUTH_ID to use Cortex XSOAR api:\n')
    configuration = Configuration()
    configuration.api_key['Authorization'] = api_key
    configuration.host = os.path.join(base_url)
    if auth_id:
        configuration.api_key['x-xdr-auth-id'] = auth_id
        configuration.host = os.path.join(configuration.host, 'xsoar')
    configuration.verify_ssl = verify_ssl
    configuration.proxy = proxy
    configuration.debug = debug
    configuration.ssl_ca_cert = ssl_ca_cert
    if connection_pool_maxsize:
        configuration.connection_pool_maxsize = connection_pool_maxsize

    if username is None:
        api_client = ApiClient(configuration)
        api_client.user_agent = 'demisto-py/' + __version__
        api_instance = demisto_api.DefaultApi(api_client)
        return api_instance
    else:
        api_instance = login(base_url=base_url, username=username, password=password,
                             verify_ssl=verify_ssl, proxy=proxy, debug=debug)
        return api_instance


def login(base_url=None, username=None, password=None, verify_ssl=True, proxy=None, debug=False):
    configuration_orig = Configuration()
    configuration_orig.host = base_url or os.getenv('DEMISTO_BASE_URL', None)
    if isinstance(configuration_orig.host, str):
        configuration_orig.host = configuration_orig.host.rstrip('/')
    configuration_orig.verify_ssl = verify_ssl
    configuration_orig.proxy = proxy
    configuration_orig.debug = debug
    connection_pool_maxsize = os.getenv('DEMISTO_CONNECTION_POOL_MAXSIZE')
    if connection_pool_maxsize:
        if connection_pool_maxsize.isdigit():
            connection_pool_maxsize = int(connection_pool_maxsize)
            configuration_orig.connection_pool_maxsize = connection_pool_maxsize
        else:
            err_msg = ('DEMISTO_CONNECTION_POOL_MAXSIZE env variable should be set to a number'
                       f' but instead received "{connection_pool_maxsize}"')
            raise ValueError(err_msg)
    api_client = ApiClient(configuration_orig)
    api_client.user_agent = 'demisto-py/' + __version__
    api_instance = demisto_api.DefaultApi(api_client)
    body = {
        "user": username,
        "password": password
    }
    res = generic_request_func(self=api_instance, path='/', method='GET', body=body,
                               accept='application/json', content_type='application/json')
    cookies = res[2]['Set-Cookie']
    cookie_jar = cookies.split(';')
    xsrf_token_raw = cookie_jar[0]
    xsrf_token = xsrf_token_raw.replace('XSRF-TOKEN=', '')
    configuration = Configuration()
    configuration.host = base_url or os.getenv('DEMISTO_BASE_URL', None)
    if isinstance(configuration.host, str):
        configuration.host = configuration.host.rstrip('/')
    configuration.verify_ssl = verify_ssl
    configuration.proxy = proxy
    configuration.debug = debug
    if connection_pool_maxsize and isinstance(connection_pool_maxsize, int):
        configuration.connection_pool_maxsize = connection_pool_maxsize
    api_client = ApiClient(configuration, header_name="X-XSRF-TOKEN", header_value=xsrf_token,
                           cookie=cookies)
    api_client.user_agent = 'demisto-py/' + __version__
    mid_client = demisto_api.DefaultApi(api_client)
    second_call = generic_request_func(self=mid_client, path='/login', method='POST', body=body,
                                       accept='application/json', content_type='application/json')
    updated_cookies = cookies + '; ' + second_call[2]['Set-Cookie']
    mid_api_client = ApiClient(configuration, header_name="X-XSRF-TOKEN", header_value=xsrf_token,
                               cookie=updated_cookies)
    mid_api_client.user_agent = 'demisto-py/' + __version__
    final_api_client = demisto_api.DefaultApi(mid_api_client)

    return final_api_client


def to_extended_dict(o):
    """
    In some cases, the models do not use the attribute map which causes the server to not return
    valid results. This function checks to see if an attribute map is part of the object and if so,
    will apply the changes to request object. If not, it will default to use the models as defined
    swagger.

    :param o: Request object.
    :return: Formatted request object.
    """
    result = {}

    if hasattr(o, "attribute_map"):
        o_map = o.attribute_map

        for attr, _ in six.iteritems(o.swagger_types):
            value = getattr(o, attr)
            if isinstance(value, list):
                result[o_map[attr]] = list(map(
                    lambda x: to_extended_dict(x) if hasattr(x, "to_dict") else x,
                    value
                ))
            elif hasattr(value, "to_dict"):
                result[o_map[attr]] = to_extended_dict(value)
            elif isinstance(value, dict):
                result[o_map[attr]] = dict(map(
                    lambda item: (item[0], to_extended_dict(item[1]))
                    if hasattr(item[1], "to_dict") else item,
                    value.items()
                ))
            elif isinstance(value, datetime.datetime):
                if not value.tzinfo:  # no tz defined -> use machine local
                    value = tzlocal.get_localzone().localize(value)
                result[o_map[attr]] = value.isoformat()
            else:
                result[o_map[attr]] = value
    else:
        o.to_dict() if hasattr(o, "to_dict") else o
        result = o
    return result


def generic_request_func(self, path, method, body=None, **kwargs):
    """
    This method allows for generic requests to be made against the Demisto server to endpoints that
    may not be exposed directly.
    :param path: str - Path of the endpoint.
    :param method: str - Type of API method to use.
    :param body: dict - Dict object of request body.
    :param content_type: str - optional content type of body.
    :param accept: str/list[str] - optional content type to accept.
    :param response_type: str - optional response type to return. Default: 'str'. To get an object specify 'object'.

    :return: tuple of (response_data, response_code, headers).
    """
    if not path.startswith('/'):
        path = '/' + path

    all_params = ['']  # noqa: E501
    all_params.append('async_req')
    all_params.append('_return_http_data_only')
    all_params.append('_preload_content')
    all_params.append('_request_timeout')
    all_params.append('content_type')
    all_params.append('accept')
    all_params.append('response_type')

    params = locals()
    for key, val in six.iteritems(params['kwargs']):
        if key not in all_params:
            raise TypeError(
                "Got an unexpected keyword argument '%s'"
                " to method" % key
            )
        params[key] = val
    del params['kwargs']

    collection_formats = {}

    path_params = {}

    query_params = []

    header_params = {}

    form_params = []
    local_var_files = {}

    body_params = body
    # HTTP header `Accept`
    accept = params.get('accept', 'application/json')
    if not (isinstance(accept, list) or isinstance(accept, tuple)):
        accept = [accept]
    header_params['Accept'] = self.api_client.select_header_accept(accept)

    # HTTP header `Content-Type`
    header_params['Content-Type'] = self.api_client.select_header_content_type(  # noqa: E501
        [params.get('content_type', 'application/json')])  # noqa: E501

    # Authentication setting
    auth_settings = ['api_key']  # noqa: E501

    return self.api_client.call_api(
        path, method,
        path_params,
        query_params,
        header_params,
        body=body_params,
        post_params=form_params,
        files=local_var_files,
        response_type=params.get('response_type', 'str'),
        auth_settings=auth_settings,
        async_req=params.get('async_req'),
        _return_http_data_only=params.get('_return_http_data_only'),
        _preload_content=params.get('_preload_content', True),
        _request_timeout=params.get('_request_timeout'),
        collection_formats=collection_formats)


def get_layouts_url_for_demisto_version(api_client, params):
    """
    This function returns the correct url to upload a layout according to Demisto version that is being used.
    :param api_client: "ApiClient" instance.
    :param params: dict containing information about the uploaded layout.

    :return: the correct url as string.
    """
    url = '/v2/layouts/import'
    server_details, status_code, response_headers = api_client.call_api('/about', 'GET', header_params={
        'Accept': 'application/json'},
        auth_settings=['api_key'],
        response_type=str,
        _preload_content=params.get(
        '_preload_content', True))
    if 200 == status_code:
        server_details = json.loads(server_details.replace('\'', '"'))
        if LooseVersion(server_details.get('demistoVersion')) >= LooseVersion('6.0.0'):
            url = '/layouts/import'
    return url
