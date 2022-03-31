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
    aodr__yzm = {}
    krsmg__gcb, iucj__uwiz = self._current_database_schema(connection, **kw)
    vjee__vzf = self._denormalize_quote_join(krsmg__gcb, schema)
    try:
        mqv__tfv = self._get_schema_primary_keys(connection, vjee__vzf, **kw)
        qzwmi__jvsvm = connection.execute(text(
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
    except sa_exc.ProgrammingError as zyie__plnmp:
        if zyie__plnmp.orig.errno == 90030:
            return None
        raise
    for table_name, ezaf__kgzph, prhm__czled, dqmp__uhjuc, rkax__xcn, raxg__qwby, xgwcx__qjxik, gaq__rxwt, pte__fingo, lyt__ykn in qzwmi__jvsvm:
        table_name = self.normalize_name(table_name)
        ezaf__kgzph = self.normalize_name(ezaf__kgzph)
        if table_name not in aodr__yzm:
            aodr__yzm[table_name] = list()
        if ezaf__kgzph.startswith('sys_clustering_column'):
            continue
        xht__ujocg = self.ischema_names.get(prhm__czled, None)
        pjk__bfi = {}
        if xht__ujocg is None:
            sa_util.warn("Did not recognize type '{}' of column '{}'".
                format(prhm__czled, ezaf__kgzph))
            xht__ujocg = sqltypes.NULLTYPE
        elif issubclass(xht__ujocg, sqltypes.FLOAT):
            pjk__bfi['precision'] = rkax__xcn
            pjk__bfi['decimal_return_scale'] = raxg__qwby
        elif issubclass(xht__ujocg, sqltypes.Numeric):
            pjk__bfi['precision'] = rkax__xcn
            pjk__bfi['scale'] = raxg__qwby
        elif issubclass(xht__ujocg, (sqltypes.String, sqltypes.BINARY)):
            pjk__bfi['length'] = dqmp__uhjuc
        ppwmm__krt = xht__ujocg if isinstance(xht__ujocg, sqltypes.NullType
            ) else xht__ujocg(**pjk__bfi)
        deej__byax = mqv__tfv.get(table_name)
        aodr__yzm[table_name].append({'name': ezaf__kgzph, 'type':
            ppwmm__krt, 'nullable': xgwcx__qjxik == 'YES', 'default':
            gaq__rxwt, 'autoincrement': pte__fingo == 'YES', 'comment':
            lyt__ykn, 'primary_key': ezaf__kgzph in mqv__tfv[table_name][
            'constrained_columns'] if deej__byax else False})
    return aodr__yzm


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
    aodr__yzm = []
    krsmg__gcb, iucj__uwiz = self._current_database_schema(connection, **kw)
    vjee__vzf = self._denormalize_quote_join(krsmg__gcb, schema)
    mqv__tfv = self._get_schema_primary_keys(connection, vjee__vzf, **kw)
    qzwmi__jvsvm = connection.execute(text(
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
    for table_name, ezaf__kgzph, prhm__czled, dqmp__uhjuc, rkax__xcn, raxg__qwby, xgwcx__qjxik, gaq__rxwt, pte__fingo, lyt__ykn in qzwmi__jvsvm:
        table_name = self.normalize_name(table_name)
        ezaf__kgzph = self.normalize_name(ezaf__kgzph)
        if ezaf__kgzph.startswith('sys_clustering_column'):
            continue
        xht__ujocg = self.ischema_names.get(prhm__czled, None)
        pjk__bfi = {}
        if xht__ujocg is None:
            sa_util.warn("Did not recognize type '{}' of column '{}'".
                format(prhm__czled, ezaf__kgzph))
            xht__ujocg = sqltypes.NULLTYPE
        elif issubclass(xht__ujocg, sqltypes.FLOAT):
            pjk__bfi['precision'] = rkax__xcn
            pjk__bfi['decimal_return_scale'] = raxg__qwby
        elif issubclass(xht__ujocg, sqltypes.Numeric):
            pjk__bfi['precision'] = rkax__xcn
            pjk__bfi['scale'] = raxg__qwby
        elif issubclass(xht__ujocg, (sqltypes.String, sqltypes.BINARY)):
            pjk__bfi['length'] = dqmp__uhjuc
        ppwmm__krt = xht__ujocg if isinstance(xht__ujocg, sqltypes.NullType
            ) else xht__ujocg(**pjk__bfi)
        deej__byax = mqv__tfv.get(table_name)
        aodr__yzm.append({'name': ezaf__kgzph, 'type': ppwmm__krt,
            'nullable': xgwcx__qjxik == 'YES', 'default': gaq__rxwt,
            'autoincrement': pte__fingo == 'YES', 'comment': lyt__ykn if 
            lyt__ykn != '' else None, 'primary_key': ezaf__kgzph in
            mqv__tfv[table_name]['constrained_columns'] if deej__byax else 
            False})
    return aodr__yzm


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
