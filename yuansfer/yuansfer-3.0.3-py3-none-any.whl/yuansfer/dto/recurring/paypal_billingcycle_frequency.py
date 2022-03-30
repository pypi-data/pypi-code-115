# -*- coding: utf-8 -*-
class PayPalBillingCycleFrequency(dict):
    def __init__(self, interval_unit = None, interval_count: int = None):
        self.interval_unit = interval_unit
        self.interval_count = interval_count
        self.__dict__ = self