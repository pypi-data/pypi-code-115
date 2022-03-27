from sqlalchemy import MetaData, engine, create_engine, select, inspect
from sqlalchemy.orm import sessionmaker

from timelink.mhk.models import base  # noqa
from timelink.mhk.models.base_class import Base
from timelink.mhk.models.pom_som_mapper import PomSomMapper
from timelink.mhk.models.base_mappings import pom_som_base_mappings

SQLALCHEMY_ECHO = False


class TimelinkDB:
    """
    Provide access to a Timelink-MHK database

    Usage

    dbsys = TimelinkDB("sql alchemy connection string")



    """

    db_engine: engine = None
    conn_string = None
    metadata: MetaData = None

    def __init__(self, conn_string=None):
        """
        For the interaction of "engine" and "session" alternative
        configurations see
        https://docs.sqlalchemy.org/en/14/orm/session_basics.html

        :param conn_string: a sqlalchemy connection URL, str.
        """

        self.init_db(conn_string)

    def init_db(self, conn_string):
        """
        Create an engine from a connection string.
        Check if database is properly setup up
        by creating core tables, PomSomMappers
        and ORM classes. Database should be ready
        for import after this method is called.

        :param conn_string: SQLAlchemy connection string
        :return:
        """

        if conn_string is not None:
            self.db_engine = create_engine(
                conn_string or self.conn_string, future=True, echo=SQLALCHEMY_ECHO
            )
            self.conn_string = conn_string
        if self.conn_string is None:
            raise ValueError("No connection string available")

        Session = sessionmaker(self.db_engine)
        with Session() as session:
            self.create_tables()
            session.commit()
            self.load_database_classes(session)
            self.ensure_all_mappings(session)
            session.commit()

    def engine(self):
        return self.db_engine

    def create_tables(self):
        """
        Creates the tables from the current ORM metadata if needed

        :return: None
        """
        self.metadata = Base.metadata
        self.metadata.create_all(self.db_engine)  # only creates if missing

    def load_database_classes(self, session):
        """
        Populates database with core Database classes
        :param session:
        :return:
        """

        # Check if the core tables are there
        existing_tables = self.table_names()
        base_tables = [v[0].table_name for v in pom_som_base_mappings.values()]
        missing = set(base_tables) - set(existing_tables)
        if len(missing) > 0:
            self.create_tables()

        # check if we have the data for the core database entity classes
        stmt = select(PomSomMapper.id)
        available_mappings = session.execute(stmt).scalars().all()
        for k in pom_som_base_mappings.keys():
            if k not in available_mappings:
                data = pom_som_base_mappings[k]
                session.bulk_save_objects(data)
        # this will cache the pomsom mapper objects
        session.commit()

    def ensure_all_mappings(self, session):
        """Ensure that all database classes have a table and ORM class"""
        pom_classes = PomSomMapper.get_pom_classes(session)
        for pom_class in pom_classes:
            pom_class.ensure_mapping(session)

    def table_names(self):
        """Current tables in the current database"""
        insp = inspect(self.db_engine)
        db_tables = insp.get_table_names()  # tables in the database
        return db_tables

    def drop_db(self, session):
        """
        This will drop all timelink related tables from the database.
        It will not touch non timelink tables that might exist.
        :param session:
        :return:
        """
        session.rollback()
        self.load_database_classes(session)
        self.ensure_all_mappings(session)
        self.metadata = Base.metadata
        self.metadata.drop_all(self.db_engine)
