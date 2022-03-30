import time

from notecoin.database.base import Base, BaseTable
from sqlalchemy import Column, Float, Integer


class OkexStrategyAutoSeller(Base, BaseTable):
    __tablename__ = 'okex_strategy_auto_seller'
    coin_id = Column(Integer, comment='coin_id', primary_key=True)
    price = Column(Float, comment='price')
    count = Column(Float, comment='count')
    init_worth = Column(Float, comment='init_worth')
    max_worth = Column(Float, comment='max_worth')
    min_worth = Column(Float, comment='min_worth')
    updateTime = Column(Float, comment='updateTime')

    def __init__(self, *args, **kwargs):
        self.coin_id = kwargs.get("coin_id")
        self.price = kwargs.get("price")
        self.count = kwargs.get("count")
        self.init_worth = kwargs.get("init_worth")
        self.max_worth = kwargs.get("max_worth") or kwargs.get("init_worth")
        self.min_worth = kwargs.get("min_worth") or kwargs.get("init_worth")
        self.updateTime = int(time.time() * 1000)
        super(OkexStrategyAutoSeller, self).__init__(*args, **kwargs)

    def update_worth(self, worth, price=None, count=None):
        self.price = price or self.price
        self.count = count or self.count
        if worth > self.max_worth:
            self.max_worth = worth
        if worth < self.min_worth:
            self.min_worth = worth
        self.updateTime = int(time.time() * 1000)

    def check(self, worth):
        if self.max_worth * 0.95 > worth > self.init_worth * 1.01:
            return True
        else:
            return False

    @staticmethod
    def instance(coin_id, price=None, count=None, worth=None):
        return OkexStrategyAutoSeller(coin_id=coin_id, price=price, count=count, init_worth=worth)
