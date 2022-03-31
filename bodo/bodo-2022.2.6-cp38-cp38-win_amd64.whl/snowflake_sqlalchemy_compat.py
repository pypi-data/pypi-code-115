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
    gtqgb__hkdx = {}
    tcup__rzb, kgsp__exjfp = self._current_database_schema(connection, **kw)
    hej__iuihy = self._denormalize_quote_join(tcup__rzb, schema)
    try:
        bwg__mhu = self._get_schema_primary_keys(connection, hej__iuihy, **kw)
        flxfu__jkb = connection.execute(text(
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
    except sa_exc.ProgrammingError as tilc__ejybb:
        if tilc__ejybb.orig.errno == 90030:
            return None
        raise
    for table_name, rdcy__klf, nooo__jwe, ttal__fbktk, sej__bvv, clozv__uqzg, czyve__vbdvi, inh__ljb, jglh__dnzaj, ccb__pgcpd in flxfu__jkb:
        table_name = self.normalize_name(table_name)
        rdcy__klf = self.normalize_name(rdcy__klf)
        if table_name not in gtqgb__hkdx:
            gtqgb__hkdx[table_name] = list()
        if rdcy__klf.startswith('sys_clustering_column'):
            continue
        osrp__wanni = self.ischema_names.get(nooo__jwe, None)
        oatyx__imjhz = {}
        if osrp__wanni is None:
            sa_util.warn("Did not recognize type '{}' of column '{}'".
                format(nooo__jwe, rdcy__klf))
            osrp__wanni = sqltypes.NULLTYPE
        elif issubclass(osrp__wanni, sqltypes.FLOAT):
            oatyx__imjhz['precision'] = sej__bvv
            oatyx__imjhz['decimal_return_scale'] = clozv__uqzg
        elif issubclass(osrp__wanni, sqltypes.Numeric):
            oatyx__imjhz['precision'] = sej__bvv
            oatyx__imjhz['scale'] = clozv__uqzg
        elif issubclass(osrp__wanni, (sqltypes.String, sqltypes.BINARY)):
            oatyx__imjhz['length'] = ttal__fbktk
        vuh__kbyld = osrp__wanni if isinstance(osrp__wanni, sqltypes.NullType
            ) else osrp__wanni(**oatyx__imjhz)
        dedtn__mgy = bwg__mhu.get(table_name)
        gtqgb__hkdx[table_name].append({'name': rdcy__klf, 'type':
            vuh__kbyld, 'nullable': czyve__vbdvi == 'YES', 'default':
            inh__ljb, 'autoincrement': jglh__dnzaj == 'YES', 'comment':
            ccb__pgcpd, 'primary_key': rdcy__klf in bwg__mhu[table_name][
            'constrained_columns'] if dedtn__mgy else False})
    return gtqgb__hkdx


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
    gtqgb__hkdx = []
    tcup__rzb, kgsp__exjfp = self._current_database_schema(connection, **kw)
    hej__iuihy = self._denormalize_quote_join(tcup__rzb, schema)
    bwg__mhu = self._get_schema_primary_keys(connection, hej__iuihy, **kw)
    flxfu__jkb = connection.execute(text(
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
    for table_name, rdcy__klf, nooo__jwe, ttal__fbktk, sej__bvv, clozv__uqzg, czyve__vbdvi, inh__ljb, jglh__dnzaj, ccb__pgcpd in flxfu__jkb:
        table_name = self.normalize_name(table_name)
        rdcy__klf = self.normalize_name(rdcy__klf)
        if rdcy__klf.startswith('sys_clustering_column'):
            continue
        osrp__wanni = self.ischema_names.get(nooo__jwe, None)
        oatyx__imjhz = {}
        if osrp__wanni is None:
            sa_util.warn("Did not recognize type '{}' of column '{}'".
                format(nooo__jwe, rdcy__klf))
            osrp__wanni = sqltypes.NULLTYPE
        elif issubclass(osrp__wanni, sqltypes.FLOAT):
            oatyx__imjhz['precision'] = sej__bvv
            oatyx__imjhz['decimal_return_scale'] = clozv__uqzg
        elif issubclass(osrp__wanni, sqltypes.Numeric):
            oatyx__imjhz['precision'] = sej__bvv
            oatyx__imjhz['scale'] = clozv__uqzg
        elif issubclass(osrp__wanni, (sqltypes.String, sqltypes.BINARY)):
            oatyx__imjhz['length'] = ttal__fbktk
        vuh__kbyld = osrp__wanni if isinstance(osrp__wanni, sqltypes.NullType
            ) else osrp__wanni(**oatyx__imjhz)
        dedtn__mgy = bwg__mhu.get(table_name)
        gtqgb__hkdx.append({'name': rdcy__klf, 'type': vuh__kbyld,
            'nullable': czyve__vbdvi == 'YES', 'default': inh__ljb,
            'autoincrement': jglh__dnzaj == 'YES', 'comment': ccb__pgcpd if
            ccb__pgcpd != '' else None, 'primary_key': rdcy__klf in
            bwg__mhu[table_name]['constrained_columns'] if dedtn__mgy else 
            False})
    return gtqgb__hkdx


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
