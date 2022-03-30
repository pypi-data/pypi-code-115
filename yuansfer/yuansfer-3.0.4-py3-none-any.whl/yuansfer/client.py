# -*- coding: utf-8 -*-
from yuansfer.decorators import lazy_property
from yuansfer.configuration import Configuration
from yuansfer.api.online_api import OnlineApi
from yuansfer.api.offline_api import OfflineApi
from yuansfer.api.mobile_api import MobileApi
from yuansfer.api.data_search_api import DataSearchApi
from yuansfer.api.payout_api import PayoutApi
from yuansfer.api.recurring_api import RecurringApi
from yuansfer.api.customer_api import CustomerApi
from yuansfer.api.auth_api import AuthApi
from yuansfer.exception import RequireParamsError

class Client(object):

    @staticmethod
    def sdk_version():
        return '3.0.4'

    @staticmethod
    def yuansfer_version():
        return 'V3'

    @lazy_property
    def online(self):
        return OnlineApi(self.config)

    @lazy_property
    def offline(self):
        return OfflineApi(self.config)

    @lazy_property
    def auth(self):
        return AuthApi(self.config)

    @lazy_property
    def recurring(self):
        return RecurringApi(self.config)

    @lazy_property
    def mobile(self):
        return MobileApi(self.config)

    @lazy_property
    def payout(self):
        return PayoutApi(self.config)

    @lazy_property
    def customer(self):
        return CustomerApi(self.config)

    @lazy_property
    def data_search(self):
        return DataSearchApi(self.config)

    @lazy_property
    def data_search(self):
        return DataSearchApi(self.config)

    def __init__(self, timeout=60, max_retries=3, merchantNo=None,
                 environment='production', storeNo=None, token=None):
        if (merchantNo or storeNo or token) is None:
            raise RequireParamsError('Configs')
        else:
            self.config = Configuration(timeout=timeout,
                                        max_retries=max_retries,
                                        environment=environment,
                                        merchantNo=merchantNo,
                                        storeNo=storeNo,
                                        token=token)