from sqlalchemy import Column, String, Integer
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy_sqlite_session.tools import get_engine, get_session

Base = declarative_base()


class Power(Base):
    """ table powers """
    __tablename__ = 'powers'
    channel_power_issue = Column(String, primary_key=True)
    channel = Column(String)
    power = Column(String)
    issue = Column(Integer)
    num10 = Column(String)

    def __init__(self, channel, power, issue, num10):
        self.channel_power_issue = f'{channel}_{power}_{issue}'
        self.channel = channel
        self.power = power
        self.issue = issue
        self.num10 = num10

    @classmethod
    def merge_one(cls, channel, power, issue, num10):
        """get issues[list]"""
        session = get_session()
        ins = cls(channel, power, issue, num10)
        session.merge(ins)
        session.commit()
        session.close()
        print(f">>>>>> merge one: {channel} - {power} - {issue} - {num10}")


if __name__ == "__main__":
    # generate tables
    engine = get_engine()
    Base.metadata.create_all(engine)
    pass
