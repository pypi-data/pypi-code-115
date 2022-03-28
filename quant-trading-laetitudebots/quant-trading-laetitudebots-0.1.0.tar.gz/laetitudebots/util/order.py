# -*- encoding: utf-8 -*-

from .decorators import accepts


class Order:
    def __init__(self, symbol):
        self._symbol = symbol
        self._size = 0
        self._side = None
        self._order_type = None
        self._is_reduce_only = False

    @property
    def symbol(self):
        return self._symbol

    @symbol.setter
    @accepts(object, str)
    def symbol(self, value):
        self._symbol = value

    @property
    def size(self):
        return self._size

    @size.setter
    @accepts(object, (int, float))
    def size(self, value):
        if value < 0:
            raise ValueError(
                'Negative size not accepted.'
                'Indicate a positive size with sell side for short orders'
            )
        self._size = value

    @property
    def side(self):
        return self._side

    @side.setter
    @accepts(object, str)
    def side(self, value):
        accepted_values = ['buy', 'sell']
        if value not in accepted_values:
            raise ValueError(f'{value} not in {accepted_values}')
        self._side = value

    @property
    def order_type(self):
        return self._order_type

    @order_type.setter
    @accepts(object, str)
    def order_type(self, value):
        accepted_values = ['market', 'limit']
        if value not in accepted_values:
            raise ValueError(f'{value} not in {accepted_values}')
        self._order_type = value

    @property
    def is_reduce_only(self):
        return self._is_reduce_only

    @is_reduce_only.setter
    @accepts(object, bool)
    def is_reduce_only(self, value):
        self._is_reduce_only = value

