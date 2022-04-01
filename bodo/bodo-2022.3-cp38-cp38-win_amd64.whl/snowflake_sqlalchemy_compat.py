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
    aewmc__trwo = {}
    nopl__wfhse, wxmw__smao = self._current_database_schema(connection, **kw)
    umoo__wrly = self._denormalize_quote_join(nopl__wfhse, schema)
    try:
        bzmfm__sirmq = self._get_schema_primary_keys(connection, umoo__wrly,
            **kw)
        damu__vyqk = connection.execute(text(
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
    except sa_exc.ProgrammingError as jgwga__hntui:
        if jgwga__hntui.orig.errno == 90030:
            return None
        raise
    for table_name, wlff__tysyn, bmbp__vrgzo, xahiz__umhg, cbg__swz, iuikp__ajj, bake__cwb, tbx__ehum, vzkma__odo, hwgiw__fnj in damu__vyqk:
        table_name = self.normalize_name(table_name)
        wlff__tysyn = self.normalize_name(wlff__tysyn)
        if table_name not in aewmc__trwo:
            aewmc__trwo[table_name] = list()
        if wlff__tysyn.startswith('sys_clustering_column'):
            continue
        hwov__sjtgd = self.ischema_names.get(bmbp__vrgzo, None)
        wutm__slgwo = {}
        if hwov__sjtgd is None:
            sa_util.warn("Did not recognize type '{}' of column '{}'".
                format(bmbp__vrgzo, wlff__tysyn))
            hwov__sjtgd = sqltypes.NULLTYPE
        elif issubclass(hwov__sjtgd, sqltypes.FLOAT):
            wutm__slgwo['precision'] = cbg__swz
            wutm__slgwo['decimal_return_scale'] = iuikp__ajj
        elif issubclass(hwov__sjtgd, sqltypes.Numeric):
            wutm__slgwo['precision'] = cbg__swz
            wutm__slgwo['scale'] = iuikp__ajj
        elif issubclass(hwov__sjtgd, (sqltypes.String, sqltypes.BINARY)):
            wutm__slgwo['length'] = xahiz__umhg
        yvqe__jmt = hwov__sjtgd if isinstance(hwov__sjtgd, sqltypes.NullType
            ) else hwov__sjtgd(**wutm__slgwo)
        nzdj__oxr = bzmfm__sirmq.get(table_name)
        aewmc__trwo[table_name].append({'name': wlff__tysyn, 'type':
            yvqe__jmt, 'nullable': bake__cwb == 'YES', 'default': tbx__ehum,
            'autoincrement': vzkma__odo == 'YES', 'comment': hwgiw__fnj,
            'primary_key': wlff__tysyn in bzmfm__sirmq[table_name][
            'constrained_columns'] if nzdj__oxr else False})
    return aewmc__trwo


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
    aewmc__trwo = []
    nopl__wfhse, wxmw__smao = self._current_database_schema(connection, **kw)
    umoo__wrly = self._denormalize_quote_join(nopl__wfhse, schema)
    bzmfm__sirmq = self._get_schema_primary_keys(connection, umoo__wrly, **kw)
    damu__vyqk = connection.execute(text(
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
    for table_name, wlff__tysyn, bmbp__vrgzo, xahiz__umhg, cbg__swz, iuikp__ajj, bake__cwb, tbx__ehum, vzkma__odo, hwgiw__fnj in damu__vyqk:
        table_name = self.normalize_name(table_name)
        wlff__tysyn = self.normalize_name(wlff__tysyn)
        if wlff__tysyn.startswith('sys_clustering_column'):
            continue
        hwov__sjtgd = self.ischema_names.get(bmbp__vrgzo, None)
        wutm__slgwo = {}
        if hwov__sjtgd is None:
            sa_util.warn("Did not recognize type '{}' of column '{}'".
                format(bmbp__vrgzo, wlff__tysyn))
            hwov__sjtgd = sqltypes.NULLTYPE
        elif issubclass(hwov__sjtgd, sqltypes.FLOAT):
            wutm__slgwo['precision'] = cbg__swz
            wutm__slgwo['decimal_return_scale'] = iuikp__ajj
        elif issubclass(hwov__sjtgd, sqltypes.Numeric):
            wutm__slgwo['precision'] = cbg__swz
            wutm__slgwo['scale'] = iuikp__ajj
        elif issubclass(hwov__sjtgd, (sqltypes.String, sqltypes.BINARY)):
            wutm__slgwo['length'] = xahiz__umhg
        yvqe__jmt = hwov__sjtgd if isinstance(hwov__sjtgd, sqltypes.NullType
            ) else hwov__sjtgd(**wutm__slgwo)
        nzdj__oxr = bzmfm__sirmq.get(table_name)
        aewmc__trwo.append({'name': wlff__tysyn, 'type': yvqe__jmt,
            'nullable': bake__cwb == 'YES', 'default': tbx__ehum,
            'autoincrement': vzkma__odo == 'YES', 'comment': hwgiw__fnj if 
            hwgiw__fnj != '' else None, 'primary_key': wlff__tysyn in
            bzmfm__sirmq[table_name]['constrained_columns'] if nzdj__oxr else
            False})
    return aewmc__trwo


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
