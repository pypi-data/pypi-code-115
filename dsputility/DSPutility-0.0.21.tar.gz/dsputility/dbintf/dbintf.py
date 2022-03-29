import sqlalchemy as sa
import sqlalchemy_utils as sau
from sqlalchemy import Table, Column, Boolean, Integer, String, MetaData, DateTime, Float

class dbintf:
    """database interface, create a sqlalchemy engine thourgh customed settings
    """

    def __init__(self, db: str, user: str, password: str, host: str, port: str, vendor: str):
        """initializer, create a sqlalchemy engine thourgh following parameters
        :param db: database name, should be 'process mining'
        :param user: postgres user name
        :param password: postgres user password
        :param host: host url
        :param port: host port
        :param vendor: what kind of batabase
        """
        self.db = db
        self.user, self.password = user, password
        self.host, self.port = host, port
        self.vendor = vendor
        self.sqlalchemy_url = f"{self.vendor}://{self.user}:{self.password}@{self.host}:{self.port}/{self.db}"
        self.engine = sa.create_engine(self.sqlalchemy_url)
        if not sau.database_exists(self.engine.url):
            print(
                f'db {self.engine.url.database} does not exist, create db {self.engine.url.database}')
            sau.create_database(self.engine.url)

    def __str__(self):
        info = (f'db: {self.db}', f'host: {self.host}', f'port:{self.port}', f'vendor:{self.vendor}')
        s = 'dbintf with settings:\n'.join(info)
        return s