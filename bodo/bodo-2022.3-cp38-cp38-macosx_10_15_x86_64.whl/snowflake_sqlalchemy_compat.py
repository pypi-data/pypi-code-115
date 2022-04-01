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
    rqrt__ncquv = {}
    xww__shc, nikss__saz = self._current_database_schema(connection, **kw)
    uaokl__dgw = self._denormalize_quote_join(xww__shc, schema)
    try:
        marl__gltb = self._get_schema_primary_keys(connection, uaokl__dgw, **kw
            )
        kdp__ocbsb = connection.execute(text(
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
    except sa_exc.ProgrammingError as tkc__yhuol:
        if tkc__yhuol.orig.errno == 90030:
            return None
        raise
    for table_name, homkp__dflbm, xrw__kdo, wyw__emdhh, esimt__esg, jeu__ismrp, rgiuq__pnide, bhc__nufy, rye__lsi, jkkeg__bvkuo in kdp__ocbsb:
        table_name = self.normalize_name(table_name)
        homkp__dflbm = self.normalize_name(homkp__dflbm)
        if table_name not in rqrt__ncquv:
            rqrt__ncquv[table_name] = list()
        if homkp__dflbm.startswith('sys_clustering_column'):
            continue
        zih__vroqo = self.ischema_names.get(xrw__kdo, None)
        yqa__svxqz = {}
        if zih__vroqo is None:
            sa_util.warn("Did not recognize type '{}' of column '{}'".
                format(xrw__kdo, homkp__dflbm))
            zih__vroqo = sqltypes.NULLTYPE
        elif issubclass(zih__vroqo, sqltypes.FLOAT):
            yqa__svxqz['precision'] = esimt__esg
            yqa__svxqz['decimal_return_scale'] = jeu__ismrp
        elif issubclass(zih__vroqo, sqltypes.Numeric):
            yqa__svxqz['precision'] = esimt__esg
            yqa__svxqz['scale'] = jeu__ismrp
        elif issubclass(zih__vroqo, (sqltypes.String, sqltypes.BINARY)):
            yqa__svxqz['length'] = wyw__emdhh
        otm__onxxx = zih__vroqo if isinstance(zih__vroqo, sqltypes.NullType
            ) else zih__vroqo(**yqa__svxqz)
        zji__twrwr = marl__gltb.get(table_name)
        rqrt__ncquv[table_name].append({'name': homkp__dflbm, 'type':
            otm__onxxx, 'nullable': rgiuq__pnide == 'YES', 'default':
            bhc__nufy, 'autoincrement': rye__lsi == 'YES', 'comment':
            jkkeg__bvkuo, 'primary_key': homkp__dflbm in marl__gltb[
            table_name]['constrained_columns'] if zji__twrwr else False})
    return rqrt__ncquv


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
    rqrt__ncquv = []
    xww__shc, nikss__saz = self._current_database_schema(connection, **kw)
    uaokl__dgw = self._denormalize_quote_join(xww__shc, schema)
    marl__gltb = self._get_schema_primary_keys(connection, uaokl__dgw, **kw)
    kdp__ocbsb = connection.execute(text(
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
    for table_name, homkp__dflbm, xrw__kdo, wyw__emdhh, esimt__esg, jeu__ismrp, rgiuq__pnide, bhc__nufy, rye__lsi, jkkeg__bvkuo in kdp__ocbsb:
        table_name = self.normalize_name(table_name)
        homkp__dflbm = self.normalize_name(homkp__dflbm)
        if homkp__dflbm.startswith('sys_clustering_column'):
            continue
        zih__vroqo = self.ischema_names.get(xrw__kdo, None)
        yqa__svxqz = {}
        if zih__vroqo is None:
            sa_util.warn("Did not recognize type '{}' of column '{}'".
                format(xrw__kdo, homkp__dflbm))
            zih__vroqo = sqltypes.NULLTYPE
        elif issubclass(zih__vroqo, sqltypes.FLOAT):
            yqa__svxqz['precision'] = esimt__esg
            yqa__svxqz['decimal_return_scale'] = jeu__ismrp
        elif issubclass(zih__vroqo, sqltypes.Numeric):
            yqa__svxqz['precision'] = esimt__esg
            yqa__svxqz['scale'] = jeu__ismrp
        elif issubclass(zih__vroqo, (sqltypes.String, sqltypes.BINARY)):
            yqa__svxqz['length'] = wyw__emdhh
        otm__onxxx = zih__vroqo if isinstance(zih__vroqo, sqltypes.NullType
            ) else zih__vroqo(**yqa__svxqz)
        zji__twrwr = marl__gltb.get(table_name)
        rqrt__ncquv.append({'name': homkp__dflbm, 'type': otm__onxxx,
            'nullable': rgiuq__pnide == 'YES', 'default': bhc__nufy,
            'autoincrement': rye__lsi == 'YES', 'comment': jkkeg__bvkuo if 
            jkkeg__bvkuo != '' else None, 'primary_key': homkp__dflbm in
            marl__gltb[table_name]['constrained_columns'] if zji__twrwr else
            False})
    return rqrt__ncquv


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
