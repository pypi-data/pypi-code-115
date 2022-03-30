import time

from notecoin.database.base import Base, BaseTable
from sqlalchemy import Column, Float, Integer


class OkexStrategyAutoSeller(Base, BaseTable):
    __tablename__ = 'okex_strategy_auto_seller'
    coin_id = Column(Integer, comment='coin_id', primary_key=True)
    price = Column(Float, comment='price')
    count = Column(Float, comment='count')
    initWorth = Column(Float, comment='initWorth')
    maxWorth = Column(Float, comment='maxWorth')
    minWorth = Column(Float, comment='minWorth')
    updateTime = Column(Float, comment='updateTime')

    def __init__(self, *args, **kwargs):
        self.initWorth = kwargs.get("initWorth")
        self.maxWorth = kwargs.get("maxWorth") or kwargs.get("initWorth")
        self.minWorth = kwargs.get("minWorth") or kwargs.get("initWorth")
        self.updateTime = int(time.time() * 1000)
        super(OkexStrategyAutoSeller, self).__init__(*args, **kwargs)

    def update_worth(self, worth, price=None, count=None):
        self.price = price or self.price
        self.count = count or self.count
        if worth > self.maxWorth:
            self.maxWorth = worth
        if worth < self.minWorth:
            self.minWorth = worth
        self.updateTime = int(time.time() * 1000)

    def check(self, worth):
        if self.maxWorth * 0.95 > worth > self.initWorth * 1.01:
            return True
        else:
            return False
