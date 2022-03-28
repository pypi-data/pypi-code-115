# -*- encoding: utf-8 -*-

from laetitudebots.util.decorators import accepts


class Position:
    def __init__(self, symbol):
        self.symbol = symbol
        self._size = 0
        self._side = None
        self._avg_price = 0
        self._realised_pnl = 0
        self._unrealised_pnl = 0

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
        self._size = value

    @property
    def side(self):
        return self._side

    @side.setter
    def side(self, value):
        accepted_values = ['buy', 'sell', None]
        if value not in accepted_values:
            raise ValueError(f'{value} not in {accepted_values}')
        self._side = value

    @property
    def avg_price(self):
        return self._avg_price

    @avg_price.setter
    @accepts(object, (int, float))
    def avg_price(self, value):
        if value <= 0:
            raise ValueError('Must be a positive number')
        self._avg_price = value

    @property
    def realised_pnl(self):
        return self._realised_pnl

    @realised_pnl.setter
    @accepts(object, (int, float))
    def realised_pnl(self, value):
        self._realised_pnl = value

    @property
    def unrealised_pnl(self):
        return self._unrealised_pnl

    @unrealised_pnl.setter
    @accepts(object, (int, float))
    def unrealised_pnl(self, value):
        self._unrealised_pnl = value

