from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.engine.url import URL

Base = None
engine = None
url = None
db_session = None
attached_entities = None


def init_db(user, password, host, database_name):
    global engine, Base, url, db_session, attached_entities
    postgres_db = {'drivername': 'postgresql',
                   'username': user,
                   'password': password,
                   'host': host,
                   'database': database_name,
                   'port': 5432}
    url = URL.create(**postgres_db)
    engine = create_engine(url, future=True)
    db_session = scoped_session(sessionmaker(autocommit=False, autoflush=False, bind=engine))
    Base = declarative_base()
    Base.query = db_session.query_property()
    from . import entities
    Base.metadata.create_all(bind=engine)
    attached_entities = entities
    return attached_entities


def delete_tables():
    Base.metadata.drop_all(bind=engine)


def get_entities():
    return attached_entities
