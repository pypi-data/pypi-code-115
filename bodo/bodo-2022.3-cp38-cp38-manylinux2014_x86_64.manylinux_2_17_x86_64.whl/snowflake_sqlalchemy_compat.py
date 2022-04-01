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
    cbg__gzz = {}
    eyi__ncd, uzffg__lsayo = self._current_database_schema(connection, **kw)
    taujt__lhzbn = self._denormalize_quote_join(eyi__ncd, schema)
    try:
        jhf__hxq = self._get_schema_primary_keys(connection, taujt__lhzbn, **kw
            )
        pis__bhq = connection.execute(text(
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
    except sa_exc.ProgrammingError as eupsp__okih:
        if eupsp__okih.orig.errno == 90030:
            return None
        raise
    for table_name, jknyu__pyaoh, kph__afak, zol__dst, znxah__zlgbt, hokii__vglg, jrf__axdk, roqj__kocb, agmp__lkgp, ebb__otxk in pis__bhq:
        table_name = self.normalize_name(table_name)
        jknyu__pyaoh = self.normalize_name(jknyu__pyaoh)
        if table_name not in cbg__gzz:
            cbg__gzz[table_name] = list()
        if jknyu__pyaoh.startswith('sys_clustering_column'):
            continue
        kgalf__umuu = self.ischema_names.get(kph__afak, None)
        btsfh__srjak = {}
        if kgalf__umuu is None:
            sa_util.warn("Did not recognize type '{}' of column '{}'".
                format(kph__afak, jknyu__pyaoh))
            kgalf__umuu = sqltypes.NULLTYPE
        elif issubclass(kgalf__umuu, sqltypes.FLOAT):
            btsfh__srjak['precision'] = znxah__zlgbt
            btsfh__srjak['decimal_return_scale'] = hokii__vglg
        elif issubclass(kgalf__umuu, sqltypes.Numeric):
            btsfh__srjak['precision'] = znxah__zlgbt
            btsfh__srjak['scale'] = hokii__vglg
        elif issubclass(kgalf__umuu, (sqltypes.String, sqltypes.BINARY)):
            btsfh__srjak['length'] = zol__dst
        jzmny__qql = kgalf__umuu if isinstance(kgalf__umuu, sqltypes.NullType
            ) else kgalf__umuu(**btsfh__srjak)
        qqu__yqow = jhf__hxq.get(table_name)
        cbg__gzz[table_name].append({'name': jknyu__pyaoh, 'type':
            jzmny__qql, 'nullable': jrf__axdk == 'YES', 'default':
            roqj__kocb, 'autoincrement': agmp__lkgp == 'YES', 'comment':
            ebb__otxk, 'primary_key': jknyu__pyaoh in jhf__hxq[table_name][
            'constrained_columns'] if qqu__yqow else False})
    return cbg__gzz


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
    cbg__gzz = []
    eyi__ncd, uzffg__lsayo = self._current_database_schema(connection, **kw)
    taujt__lhzbn = self._denormalize_quote_join(eyi__ncd, schema)
    jhf__hxq = self._get_schema_primary_keys(connection, taujt__lhzbn, **kw)
    pis__bhq = connection.execute(text(
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
    for table_name, jknyu__pyaoh, kph__afak, zol__dst, znxah__zlgbt, hokii__vglg, jrf__axdk, roqj__kocb, agmp__lkgp, ebb__otxk in pis__bhq:
        table_name = self.normalize_name(table_name)
        jknyu__pyaoh = self.normalize_name(jknyu__pyaoh)
        if jknyu__pyaoh.startswith('sys_clustering_column'):
            continue
        kgalf__umuu = self.ischema_names.get(kph__afak, None)
        btsfh__srjak = {}
        if kgalf__umuu is None:
            sa_util.warn("Did not recognize type '{}' of column '{}'".
                format(kph__afak, jknyu__pyaoh))
            kgalf__umuu = sqltypes.NULLTYPE
        elif issubclass(kgalf__umuu, sqltypes.FLOAT):
            btsfh__srjak['precision'] = znxah__zlgbt
            btsfh__srjak['decimal_return_scale'] = hokii__vglg
        elif issubclass(kgalf__umuu, sqltypes.Numeric):
            btsfh__srjak['precision'] = znxah__zlgbt
            btsfh__srjak['scale'] = hokii__vglg
        elif issubclass(kgalf__umuu, (sqltypes.String, sqltypes.BINARY)):
            btsfh__srjak['length'] = zol__dst
        jzmny__qql = kgalf__umuu if isinstance(kgalf__umuu, sqltypes.NullType
            ) else kgalf__umuu(**btsfh__srjak)
        qqu__yqow = jhf__hxq.get(table_name)
        cbg__gzz.append({'name': jknyu__pyaoh, 'type': jzmny__qql,
            'nullable': jrf__axdk == 'YES', 'default': roqj__kocb,
            'autoincrement': agmp__lkgp == 'YES', 'comment': ebb__otxk if 
            ebb__otxk != '' else None, 'primary_key': jknyu__pyaoh in
            jhf__hxq[table_name]['constrained_columns'] if qqu__yqow else 
            False})
    return cbg__gzz


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
