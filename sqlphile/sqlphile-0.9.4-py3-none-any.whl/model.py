from abc import *
from .q import _Q

class AbstractModel:
    @abstractclassmethod
    def get_table_name (self):
        pass

    @abstractclassmethod
    def db (self, *args, **kargs):
        from sqlphile import SQLPhile
        return SQLPhile ()

    # optionals -------------------------------------------
    @classmethod
    def get_columns (self):
        raise NotImplementedError ('return column list like [name, ...]')

    @classmethod
    def validate (self, data, create = False):
        raise NotImplementedError

    @classmethod
    def get_pk (self):
        raise NotImplementedError ('return pk column name like id')

    @classmethod
    def get_fks (self):
        raise NotImplementedError ('return fks like {fk_alias: fk_model} or {fk_alias: (fk_column, fk_model)}')

    # basic CRUD ops --------------------------------------
    @classmethod
    def _check_pk (cls, Qs, filters):
        if Qs and not isinstance (Qs [0], _Q):
            pk = list (Qs).pop (0)
            filters [cls._get_table_info ().pk.column] = pk
        return Qs, filters

    @classmethod
    def add (cls, data):
        with cls.db () as db:
            return (db.insert (cls)
                        .set (**data))

    @classmethod
    def get (cls, *Qs, **filters):
        Qs, filters = cls._check_pk (Qs, filters)
        with cls.db () as db:
            return (db.select (cls)
                        .filter (*Qs, **filters)).execute ().one ()

    @classmethod
    def search (cls, *Qs, **filters):
        Qs, filters = cls._check_pk (Qs, filters)
        with cls.db () as db:
            return (db.select (cls)
                        .filter (*Qs, **filters)).execute ().fetch ()

    @classmethod
    def set (cls, data, *Qs, **filters):
        Qs, filters = cls._check_pk (Qs, filters)
        with cls.db () as db:
            return (db.update (cls)
                        .set (**data)
                        .returning ("*")
                        .filter (*Qs, **filters)).execute ().fetch ()

    @classmethod
    def remove (cls, *Qs, **filters):
        Qs, filters = cls._check_pk (Qs, filters)
        with cls.db () as db:
            return (db.delete (cls)
                        .returning ("*")
                        .filter (*Qs, **filters)).execute ().fetch ()

    @classmethod
    def with_ (cls, alias, cte):
        return cls.db ().with_ (alias, cte)

    @classmethod
    def fromcte (cls, alias):
        # followed by .with_ ()
        return cls.db ().select (alias)

    @classmethod
    def alias (cls, tbl_alias):
        return cls.db ().select (cls, tbl_alias)


    # static methods ------------------------------------------
    @staticmethod
    def utcnow ():
        return utcnow ()

    @staticmethod
    def encodeutc (obj):
        return obj.astimezone (TZ_UTC).strftime ('%Y-%m-%d %H:%M:%S+00')

    @staticmethod
    def decodeutc (s):
        return datetime (*(time.strptime (s, '%Y-%m-%d %H:%M:%S+00')) [:6]).astimezone (TZ_UTC)