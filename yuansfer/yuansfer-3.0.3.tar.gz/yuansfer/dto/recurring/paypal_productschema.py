# -*- coding: utf-8 -*-
class PayPalProductSchema(dict):
    def __init__(self, type = None, category = None):
        self.type = type
        self.category = category
        self.__dict__ = self