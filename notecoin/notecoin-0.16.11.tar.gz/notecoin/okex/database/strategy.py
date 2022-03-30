import time

from notecoin.database.base import Base, BaseTable
from sqlalchemy import Column, Float, Integer


class OkexStrategyAutoSeller(Base, BaseTable):
    __tablename__ = 'okex_strategy_auto_seller'
    coin_id = Column(Integer, comment='coin_id', primary_key=True)
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

    def update_worth(self, worth):
        if worth > self.maxWorth:
            self.maxWorth = worth
        if worth < self.minWorth:
            self.minWorth = worth
        self.updateTime = int(time.time() * 1000)

    def check(self, worth):
        self.update_worth(worth)
        if self.maxWorth * 0.95 > worth > self.initWorth * 1.01:
            return True
        else:
            return False
