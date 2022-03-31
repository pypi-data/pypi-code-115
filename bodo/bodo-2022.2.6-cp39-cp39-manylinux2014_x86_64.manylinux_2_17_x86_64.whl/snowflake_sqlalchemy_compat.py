import hashlib
import inspect
import warnings
import snowflake.sqlalchemy
import sqlalchemy.types as sqltypes
from sqlalchemy import exc as sa_exc
from sqlalchemy import util as sa_util
from sqlalchemy.sql import text
_check_snowflake_sqlalchemy_change = True


def _get_schema_columns(self, connection, schema, **kw):
    rxcz__gwd = {}
    iuqx__mly, qgb__iitd = self._current_database_schema(connection, **kw)
    betqv__rmuq = self._denormalize_quote_join(iuqx__mly, schema)
    try:
        gys__svwl = self._get_schema_primary_keys(connection, betqv__rmuq, **kw
            )
        nzuw__kbot = connection.execute(text(
            """
        SELECT /* sqlalchemy:_get_schema_columns */
                ic.table_name,
                ic.column_name,
                ic.data_type,
                ic.character_maximum_length,
                ic.numeric_precision,
                ic.numeric_scale,
                ic.is_nullable,
                ic.column_default,
                ic.is_identity,
                ic.comment
            FROM information_schema.columns ic
            WHERE ic.table_schema=:table_schema
            ORDER BY ic.ordinal_position"""
            ), {'table_schema': self.denormalize_name(schema)})
    except sa_exc.ProgrammingError as zndu__tuwkd:
        if zndu__tuwkd.orig.errno == 90030:
            return None
        raise
    for table_name, zsm__gfvss, iio__qtxpw, lxsya__schc, wel__iupn, qmrr__lzra, afmz__wid, kjwn__jdzki, whlgx__yzad, msuz__opbj in nzuw__kbot:
        table_name = self.normalize_name(table_name)
        zsm__gfvss = self.normalize_name(zsm__gfvss)
        if table_name not in rxcz__gwd:
            rxcz__gwd[table_name] = list()
        if zsm__gfvss.startswith('sys_clustering_column'):
            continue
        rmvh__twj = self.ischema_names.get(iio__qtxpw, None)
        xnnq__hbc = {}
        if rmvh__twj is None:
            sa_util.warn("Did not recognize type '{}' of column '{}'".
                format(iio__qtxpw, zsm__gfvss))
            rmvh__twj = sqltypes.NULLTYPE
        elif issubclass(rmvh__twj, sqltypes.FLOAT):
            xnnq__hbc['precision'] = wel__iupn
            xnnq__hbc['decimal_return_scale'] = qmrr__lzra
        elif issubclass(rmvh__twj, sqltypes.Numeric):
            xnnq__hbc['precision'] = wel__iupn
            xnnq__hbc['scale'] = qmrr__lzra
        elif issubclass(rmvh__twj, (sqltypes.String, sqltypes.BINARY)):
            xnnq__hbc['length'] = lxsya__schc
        gses__pjmk = rmvh__twj if isinstance(rmvh__twj, sqltypes.NullType
            ) else rmvh__twj(**xnnq__hbc)
        lnbay__krxk = gys__svwl.get(table_name)
        rxcz__gwd[table_name].append({'name': zsm__gfvss, 'type':
            gses__pjmk, 'nullable': afmz__wid == 'YES', 'default':
            kjwn__jdzki, 'autoincrement': whlgx__yzad == 'YES', 'comment':
            msuz__opbj, 'primary_key': zsm__gfvss in gys__svwl[table_name][
            'constrained_columns'] if lnbay__krxk else False})
    return rxcz__gwd


if _check_snowflake_sqlalchemy_change:
    lines = inspect.getsource(snowflake.sqlalchemy.snowdialect.
        SnowflakeDialect._get_schema_columns)
    if hashlib.sha256(lines.encode()).hexdigest(
        ) != 'fdf39af1ac165319d3b6074e8cf9296a090a21f0e2c05b644ff8ec0e56e2d769':
        warnings.warn(
            'snowflake.sqlalchemy.snowdialect.SnowflakeDialect._get_schema_columns has changed'
            )
snowflake.sqlalchemy.snowdialect.SnowflakeDialect._get_schema_columns = (
    _get_schema_columns)


def _get_table_columns(self, connection, table_name, schema=None, **kw):
    rxcz__gwd = []
    iuqx__mly, qgb__iitd = self._current_database_schema(connection, **kw)
    betqv__rmuq = self._denormalize_quote_join(iuqx__mly, schema)
    gys__svwl = self._get_schema_primary_keys(connection, betqv__rmuq, **kw)
    nzuw__kbot = connection.execute(text(
        """
    SELECT /* sqlalchemy:get_table_columns */
            ic.table_name,
            ic.column_name,
            ic.data_type,
            ic.character_maximum_length,
            ic.numeric_precision,
            ic.numeric_scale,
            ic.is_nullable,
            ic.column_default,
            ic.is_identity,
            ic.comment
        FROM information_schema.columns ic
        WHERE ic.table_schema=:table_schema
        AND ic.table_name=:table_name
        ORDER BY ic.ordinal_position"""
        ), {'table_schema': self.denormalize_name(schema), 'table_name':
        self.denormalize_name(table_name)})
    for table_name, zsm__gfvss, iio__qtxpw, lxsya__schc, wel__iupn, qmrr__lzra, afmz__wid, kjwn__jdzki, whlgx__yzad, msuz__opbj in nzuw__kbot:
        table_name = self.normalize_name(table_name)
        zsm__gfvss = self.normalize_name(zsm__gfvss)
        if zsm__gfvss.startswith('sys_clustering_column'):
            continue
        rmvh__twj = self.ischema_names.get(iio__qtxpw, None)
        xnnq__hbc = {}
        if rmvh__twj is None:
            sa_util.warn("Did not recognize type '{}' of column '{}'".
                format(iio__qtxpw, zsm__gfvss))
            rmvh__twj = sqltypes.NULLTYPE
        elif issubclass(rmvh__twj, sqltypes.FLOAT):
            xnnq__hbc['precision'] = wel__iupn
            xnnq__hbc['decimal_return_scale'] = qmrr__lzra
        elif issubclass(rmvh__twj, sqltypes.Numeric):
            xnnq__hbc['precision'] = wel__iupn
            xnnq__hbc['scale'] = qmrr__lzra
        elif issubclass(rmvh__twj, (sqltypes.String, sqltypes.BINARY)):
            xnnq__hbc['length'] = lxsya__schc
        gses__pjmk = rmvh__twj if isinstance(rmvh__twj, sqltypes.NullType
            ) else rmvh__twj(**xnnq__hbc)
        lnbay__krxk = gys__svwl.get(table_name)
        rxcz__gwd.append({'name': zsm__gfvss, 'type': gses__pjmk,
            'nullable': afmz__wid == 'YES', 'default': kjwn__jdzki,
            'autoincrement': whlgx__yzad == 'YES', 'comment': msuz__opbj if
            msuz__opbj != '' else None, 'primary_key': zsm__gfvss in
            gys__svwl[table_name]['constrained_columns'] if lnbay__krxk else
            False})
    return rxcz__gwd


if _check_snowflake_sqlalchemy_change:
    lines = inspect.getsource(snowflake.sqlalchemy.snowdialect.
        SnowflakeDialect._get_table_columns)
    if hashlib.sha256(lines.encode()).hexdigest(
        ) != '9ecc8a2425c655836ade4008b1b98a8fd1819f3be43ba77b0fbbfc1f8740e2be':
        warnings.warn(
            'snowflake.sqlalchemy.snowdialect.SnowflakeDialect._get_table_columns has changed'
            )
snowflake.sqlalchemy.snowdialect.SnowflakeDialect._get_table_columns = (
    _get_table_columns)
