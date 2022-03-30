# -*- coding: utf-8 -*-
class PayPalTaxes(dict):
    def __init__(self, percentage = None, inclusive: bool = None):
        self.percentage = percentage
        self.inclusive = str(inclusive).lower() if inclusive is not None else inclusive
        self.__dict__ = self