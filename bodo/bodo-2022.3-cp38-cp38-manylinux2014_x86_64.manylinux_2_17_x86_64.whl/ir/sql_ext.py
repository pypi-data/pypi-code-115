"""
Implementation of pd.read_sql in BODO.
We piggyback on the pandas implementation. Future plan is to have a faster
version for this task.
"""
import numba
import numpy as np
import pandas as pd
from numba.core import ir, ir_utils, typeinfer, types
from numba.core.ir_utils import compile_to_numba_ir, replace_arg_nodes
import bodo
import bodo.ir.connector
from bodo import objmode
from bodo.ir.csv_ext import _get_dtype_str
from bodo.libs.array import delete_table, info_from_table, info_to_array, table_type
from bodo.libs.distributed_api import bcast, bcast_scalar
from bodo.libs.str_ext import string_type, unicode_to_utf8
from bodo.transforms import distributed_analysis, distributed_pass
from bodo.utils.typing import BodoError
from bodo.utils.utils import check_and_propagate_cpp_exception, sanitize_varname
MPI_ROOT = 0


class SqlReader(ir.Stmt):

    def __init__(self, sql_request, connection, df_out, df_colnames,
        out_vars, out_types, converted_colnames, db_type, loc,
        unsupported_columns, unsupported_arrow_types, is_select_query):
        self.connector_typ = 'sql'
        self.sql_request = sql_request
        self.connection = connection
        self.df_out = df_out
        self.df_colnames = df_colnames
        self.original_df_colnames = df_colnames
        self.out_vars = out_vars
        self.out_types = out_types
        self.converted_colnames = converted_colnames
        self.loc = loc
        self.limit = req_limit(sql_request)
        self.db_type = db_type
        self.filters = None
        self.unsupported_columns = unsupported_columns
        self.unsupported_arrow_types = unsupported_arrow_types
        self.is_select_query = is_select_query

    def __repr__(self):
        return (
            '{} = ReadSql(sql_request={}, connection={}, col_names={}, original_col_names={}, types={}, vars={}, limit={}, unsupported_columns={}, unsupported_arrow_types={})'
            .format(self.df_out, self.sql_request, self.connection, self.
            df_colnames, self.original_df_colnames, self.out_types, self.
            out_vars, self.limit, self.unsupported_columns, self.
            unsupported_arrow_types))


def remove_dead_sql(sql_node, lives_no_aliases, lives, arg_aliases,
    alias_map, func_ir, typemap):
    xsd__wpqu = []
    bdrrh__hddlf = []
    gwy__carlo = []
    for cvvu__otsrh, aaa__edkdv in enumerate(sql_node.out_vars):
        if aaa__edkdv.name in lives:
            xsd__wpqu.append(sql_node.df_colnames[cvvu__otsrh])
            bdrrh__hddlf.append(sql_node.out_vars[cvvu__otsrh])
            gwy__carlo.append(sql_node.out_types[cvvu__otsrh])
    sql_node.df_colnames = xsd__wpqu
    sql_node.out_vars = bdrrh__hddlf
    sql_node.out_types = gwy__carlo
    if len(sql_node.out_vars) == 0:
        return None
    return sql_node


def sql_distributed_run(sql_node, array_dists, typemap, calltypes,
    typingctx, targetctx):
    if bodo.user_logging.get_verbose_level() >= 1:
        wotx__xulra = (
            'Finish column pruning on read_sql node:\n%s\nColumns loaded %s\n')
        ums__lgfzw = sql_node.loc.strformat()
        vilwy__zpzc = sql_node.df_colnames
        bodo.user_logging.log_message('Column Pruning', wotx__xulra,
            ums__lgfzw, vilwy__zpzc)
        ywdes__fspe = [jmc__rtmqf for cvvu__otsrh, jmc__rtmqf in enumerate(
            sql_node.df_colnames) if isinstance(sql_node.out_types[
            cvvu__otsrh], bodo.libs.dict_arr_ext.DictionaryArrayType)]
        if ywdes__fspe:
            ciacp__mnae = """Finished optimized encoding on read_sql node:
%s
Columns %s using dictionary encoding to reduce memory usage.
"""
            bodo.user_logging.log_message('Dictionary Encoding',
                ciacp__mnae, ums__lgfzw, ywdes__fspe)
    parallel = False
    if array_dists is not None:
        parallel = True
        for phc__xnou in sql_node.out_vars:
            if array_dists[phc__xnou.name
                ] != distributed_pass.Distribution.OneD and array_dists[
                phc__xnou.name] != distributed_pass.Distribution.OneD_Var:
                parallel = False
    if sql_node.unsupported_columns:
        vpgnh__pyk = set(sql_node.unsupported_columns)
        uqzs__ozy = set()
        othcs__qlzas = 0
        for dbrd__vdk in sql_node.df_colnames:
            while sql_node.original_df_colnames[othcs__qlzas] != dbrd__vdk:
                othcs__qlzas += 1
            if othcs__qlzas in vpgnh__pyk:
                uqzs__ozy.add(othcs__qlzas)
            othcs__qlzas += 1
        if uqzs__ozy:
            zlfv__zgb = sorted(uqzs__ozy)
            kkqz__yvc = [
                f'pandas.read_sql(): 1 or more columns found with Arrow types that are not supported in Bodo and could not be eliminated. '
                 +
                'Please manually remove these columns from your sql query by specifying the columns you need in your SELECT statement. If these '
                 +
                'columns are needed, you will need to modify your dataset to use a supported type.'
                , 'Unsupported Columns:']
            yzs__anl = 0
            for vaxsd__djg in zlfv__zgb:
                while sql_node.unsupported_columns[yzs__anl] != vaxsd__djg:
                    yzs__anl += 1
                kkqz__yvc.append(
                    f"Column '{sql_node.original_df_colnames[vaxsd__djg]}' with unsupported arrow type {sql_node.unsupported_arrow_types[yzs__anl]}"
                    )
                yzs__anl += 1
            zvdu__goot = '\n'.join(kkqz__yvc)
            raise BodoError(zvdu__goot, loc=sql_node.loc)
    sylc__yrc = len(sql_node.out_vars)
    eubw__ipa = ', '.join('arr' + str(cvvu__otsrh) for cvvu__otsrh in range
        (sylc__yrc))
    tlf__rwn, lenq__poel = bodo.ir.connector.generate_filter_map(sql_node.
        filters)
    xfqhf__sdywi = ', '.join(tlf__rwn.values())
    htfye__qhg = f'def sql_impl(sql_request, conn, {xfqhf__sdywi}):\n'
    if sql_node.filters:
        qwsp__orcn = []
        for dor__gfozv in sql_node.filters:
            ong__dpm = [' '.join(['(', tjen__bunm[0], tjen__bunm[1], '{' +
                tlf__rwn[tjen__bunm[2].name] + '}' if isinstance(tjen__bunm
                [2], ir.Var) else tjen__bunm[2], ')']) for tjen__bunm in
                dor__gfozv]
            qwsp__orcn.append(' ( ' + ' AND '.join(ong__dpm) + ' ) ')
        qewz__zjj = ' WHERE ' + ' OR '.join(qwsp__orcn)
        for cvvu__otsrh, mlmgo__cjj in enumerate(tlf__rwn.values()):
            htfye__qhg += f'    {mlmgo__cjj} = get_sql_literal({mlmgo__cjj})\n'
        htfye__qhg += f'    sql_request = f"{{sql_request}} {qewz__zjj}"\n'
    htfye__qhg += '    ({},) = _sql_reader_py(sql_request, conn)\n'.format(
        eubw__ipa)
    wqyym__uyajd = {}
    exec(htfye__qhg, {}, wqyym__uyajd)
    ydxi__merr = wqyym__uyajd['sql_impl']
    rbin__kyib = _gen_sql_reader_py(sql_node.df_colnames, sql_node.
        out_types, typingctx, targetctx, sql_node.db_type, sql_node.limit,
        sql_node.converted_colnames, parallel, sql_node.is_select_query)
    cpn__kkzq = compile_to_numba_ir(ydxi__merr, {'_sql_reader_py':
        rbin__kyib, 'bcast_scalar': bcast_scalar, 'bcast': bcast,
        'get_sql_literal': _get_snowflake_sql_literal}, typingctx=typingctx,
        targetctx=targetctx, arg_typs=(string_type, string_type) + tuple(
        typemap[phc__xnou.name] for phc__xnou in lenq__poel), typemap=
        typemap, calltypes=calltypes).blocks.popitem()[1]
    if sql_node.is_select_query:
        jpec__yargw = escape_column_names(sql_node.df_colnames, sql_node.
            db_type, sql_node.converted_colnames)
        if sql_node.db_type == 'oracle':
            wbfj__mgdzy = ('SELECT ' + jpec__yargw + ' FROM (' + sql_node.
                sql_request + ') TEMP')
        else:
            wbfj__mgdzy = ('SELECT ' + jpec__yargw + ' FROM (' + sql_node.
                sql_request + ') as TEMP')
    else:
        wbfj__mgdzy = sql_node.sql_request
    replace_arg_nodes(cpn__kkzq, [ir.Const(wbfj__mgdzy, sql_node.loc), ir.
        Const(sql_node.connection, sql_node.loc)] + lenq__poel)
    dpz__arw = cpn__kkzq.body[:-3]
    for cvvu__otsrh in range(len(sql_node.out_vars)):
        dpz__arw[-len(sql_node.out_vars) + cvvu__otsrh
            ].target = sql_node.out_vars[cvvu__otsrh]
    return dpz__arw


def escape_column_names(col_names, db_type, converted_colnames):
    if db_type in ('snowflake', 'oracle'):
        fmy__lniy = [(vsbtx__bukdo.upper() if vsbtx__bukdo in
            converted_colnames else vsbtx__bukdo) for vsbtx__bukdo in col_names
            ]
        jpec__yargw = ', '.join([f'"{vsbtx__bukdo}"' for vsbtx__bukdo in
            fmy__lniy])
    elif db_type == 'mysql' or db_type == 'mysql+pymysql':
        jpec__yargw = ', '.join([f'`{vsbtx__bukdo}`' for vsbtx__bukdo in
            col_names])
    else:
        jpec__yargw = ', '.join([f'"{vsbtx__bukdo}"' for vsbtx__bukdo in
            col_names])
    return jpec__yargw


@numba.generated_jit(nopython=True, no_cpython_wrapper=True)
def _get_snowflake_sql_literal_scalar(filter_value):
    yhuz__lexh = types.unliteral(filter_value)
    bodo.hiframes.pd_timestamp_ext.check_tz_aware_unsupported(yhuz__lexh,
        'Filter pushdown')
    if yhuz__lexh == types.unicode_type:
        return lambda filter_value: f'$${filter_value}$$'
    elif isinstance(yhuz__lexh, (types.Integer, types.Float)
        ) or filter_value == types.bool_:
        return lambda filter_value: str(filter_value)
    elif yhuz__lexh == bodo.pd_timestamp_type:

        def impl(filter_value):
            nmukl__mjcv = filter_value.nanosecond
            kitj__cpcp = ''
            if nmukl__mjcv < 10:
                kitj__cpcp = '00'
            elif nmukl__mjcv < 100:
                kitj__cpcp = '0'
            return (
                f"timestamp '{filter_value.strftime('%Y-%m-%d %H:%M:%S.%f')}{kitj__cpcp}{nmukl__mjcv}'"
                )
        return impl
    elif yhuz__lexh == bodo.datetime_date_type:
        return (lambda filter_value:
            f"date '{filter_value.strftime('%Y-%m-%d')}'")
    else:
        raise BodoError(
            f'pd.read_sql(): Internal error, unsupported scalar type {yhuz__lexh} used in filter pushdown.'
            )


@numba.generated_jit(nopython=True, no_cpython_wrapper=True)
def _get_snowflake_sql_literal(filter_value):
    scalar_isinstance = types.Integer, types.Float
    sulmm__bdu = (bodo.datetime_date_type, bodo.pd_timestamp_type, types.
        unicode_type, types.bool_)
    yhuz__lexh = types.unliteral(filter_value)
    if isinstance(yhuz__lexh, types.List) and (isinstance(yhuz__lexh.dtype,
        scalar_isinstance) or yhuz__lexh.dtype in sulmm__bdu):

        def impl(filter_value):
            hruvr__tdva = ', '.join([_get_snowflake_sql_literal_scalar(
                vsbtx__bukdo) for vsbtx__bukdo in filter_value])
            return f'({hruvr__tdva})'
        return impl
    elif isinstance(yhuz__lexh, scalar_isinstance) or yhuz__lexh in sulmm__bdu:
        return lambda filter_value: _get_snowflake_sql_literal_scalar(
            filter_value)
    else:
        raise BodoError(
            f'pd.read_sql(): Internal error, unsupported type {yhuz__lexh} used in filter pushdown.'
            )


numba.parfors.array_analysis.array_analysis_extensions[SqlReader
    ] = bodo.ir.connector.connector_array_analysis
distributed_analysis.distributed_analysis_extensions[SqlReader
    ] = bodo.ir.connector.connector_distributed_analysis
typeinfer.typeinfer_extensions[SqlReader
    ] = bodo.ir.connector.connector_typeinfer
ir_utils.visit_vars_extensions[SqlReader
    ] = bodo.ir.connector.visit_vars_connector
ir_utils.remove_dead_extensions[SqlReader] = remove_dead_sql
numba.core.analysis.ir_extension_usedefs[SqlReader
    ] = bodo.ir.connector.connector_usedefs
ir_utils.copy_propagate_extensions[SqlReader
    ] = bodo.ir.connector.get_copies_connector
ir_utils.apply_copy_propagate_extensions[SqlReader
    ] = bodo.ir.connector.apply_copies_connector
ir_utils.build_defs_extensions[SqlReader
    ] = bodo.ir.connector.build_connector_definitions
distributed_pass.distributed_run_extensions[SqlReader] = sql_distributed_run
compiled_funcs = []


@numba.njit
def sqlalchemy_check():
    with numba.objmode():
        sqlalchemy_check_()


def sqlalchemy_check_():
    try:
        import sqlalchemy
    except ImportError as dqz__zrk:
        vfgip__mlrhv = (
            "Using URI string without sqlalchemy installed. sqlalchemy can be installed by calling 'conda install -c conda-forge sqlalchemy'."
            )
        raise BodoError(vfgip__mlrhv)


@numba.njit
def pymysql_check():
    with numba.objmode():
        pymysql_check_()


def pymysql_check_():
    try:
        import pymysql
    except ImportError as dqz__zrk:
        vfgip__mlrhv = (
            "Using MySQL URI string requires pymsql to be installed. It can be installed by calling 'conda install -c conda-forge pymysql' or 'pip install PyMySQL'."
            )
        raise BodoError(vfgip__mlrhv)


@numba.njit
def cx_oracle_check():
    with numba.objmode():
        cx_oracle_check_()


def cx_oracle_check_():
    try:
        import cx_Oracle
    except ImportError as dqz__zrk:
        vfgip__mlrhv = (
            "Using Oracle URI string requires cx_oracle to be installed. It can be installed by calling 'conda install -c conda-forge cx_oracle' or 'pip install cx-Oracle'."
            )
        raise BodoError(vfgip__mlrhv)


@numba.njit
def psycopg2_check():
    with numba.objmode():
        psycopg2_check_()


def psycopg2_check_():
    try:
        import psycopg2
    except ImportError as dqz__zrk:
        vfgip__mlrhv = (
            "Using PostgreSQL URI string requires psycopg2 to be installed. It can be installed by calling 'conda install -c conda-forge psycopg2' or 'pip install psycopg2'."
            )
        raise BodoError(vfgip__mlrhv)


def req_limit(sql_request):
    import re
    szdku__rxn = re.compile('LIMIT\\s+(\\d+)\\s*$', re.IGNORECASE)
    pkzd__nssub = szdku__rxn.search(sql_request)
    if pkzd__nssub:
        return int(pkzd__nssub.group(1))
    else:
        return None


def _gen_sql_reader_py(col_names, col_typs, typingctx, targetctx, db_type,
    limit, converted_colnames, parallel, is_select_query):
    nfs__sbhf = [sanitize_varname(jmc__rtmqf) for jmc__rtmqf in col_names]
    iek__mrr = ["{}='{}'".format(olozu__buygl, _get_dtype_str(sepv__mkb)) for
        olozu__buygl, sepv__mkb in zip(nfs__sbhf, col_typs)]
    if bodo.sql_access_method == 'multiple_access_nb_row_first':
        htfye__qhg = 'def sql_reader_py(sql_request, conn):\n'
        if db_type == 'snowflake':
            rylli__upka = {}
            for cvvu__otsrh, bexl__mxbvq in enumerate(col_typs):
                rylli__upka[f'col_{cvvu__otsrh}_type'] = bexl__mxbvq
            htfye__qhg += (
                f"  ev = bodo.utils.tracing.Event('read_snowflake', {parallel})\n"
                )

            def is_nullable(typ):
                return bodo.utils.utils.is_array_typ(typ, False
                    ) and not isinstance(typ, types.Array) and not isinstance(
                    typ, bodo.DatetimeArrayType)
            zobpz__rdol = [int(is_nullable(bexl__mxbvq)) for bexl__mxbvq in
                col_typs]
            htfye__qhg += f"""  out_table = snowflake_read(unicode_to_utf8(sql_request), unicode_to_utf8(conn), {parallel}, {len(col_names)}, np.array({zobpz__rdol}, dtype=np.int32).ctypes)
"""
            htfye__qhg += '  check_and_propagate_cpp_exception()\n'
            for cvvu__otsrh, znja__zak in enumerate(nfs__sbhf):
                htfye__qhg += f"""  {znja__zak} = info_to_array(info_from_table(out_table, {cvvu__otsrh}), col_{cvvu__otsrh}_type)
"""
            htfye__qhg += '  delete_table(out_table)\n'
            htfye__qhg += f'  ev.finalize()\n'
        else:
            htfye__qhg += '  sqlalchemy_check()\n'
            if db_type == 'mysql' or db_type == 'mysql+pymysql':
                htfye__qhg += '  pymysql_check()\n'
            elif db_type == 'oracle':
                htfye__qhg += '  cx_oracle_check()\n'
            elif db_type == 'postgresql' or db_type == 'postgresql+psycopg2':
                htfye__qhg += '  psycopg2_check()\n'
            if parallel and is_select_query:
                htfye__qhg += '  rank = bodo.libs.distributed_api.get_rank()\n'
                if limit is not None:
                    htfye__qhg += f'  nb_row = {limit}\n'
                else:
                    htfye__qhg += '  with objmode(nb_row="int64"):\n'
                    htfye__qhg += f'     if rank == {MPI_ROOT}:\n'
                    htfye__qhg += """         sql_cons = 'select count(*) from (' + sql_request + ') x'
"""
                    htfye__qhg += (
                        '         frame = pd.read_sql(sql_cons, conn)\n')
                    htfye__qhg += '         nb_row = frame.iat[0,0]\n'
                    htfye__qhg += '     else:\n'
                    htfye__qhg += '         nb_row = 0\n'
                    htfye__qhg += '  nb_row = bcast_scalar(nb_row)\n'
                htfye__qhg += '  with objmode({}):\n'.format(', '.join(
                    iek__mrr))
                htfye__qhg += """    offset, limit = bodo.libs.distributed_api.get_start_count(nb_row)
"""
                jpec__yargw = escape_column_names(col_names, db_type,
                    converted_colnames)
                if db_type == 'oracle':
                    htfye__qhg += f"""    sql_cons = 'select {jpec__yargw} from (' + sql_request + ') OFFSET ' + str(offset) + ' ROWS FETCH NEXT ' + str(limit) + ' ROWS ONLY'
"""
                else:
                    htfye__qhg += f"""    sql_cons = 'select {jpec__yargw} from (' + sql_request + ') x LIMIT ' + str(limit) + ' OFFSET ' + str(offset)
"""
                htfye__qhg += '    df_ret = pd.read_sql(sql_cons, conn)\n'
            else:
                htfye__qhg += '  with objmode({}):\n'.format(', '.join(
                    iek__mrr))
                htfye__qhg += '    df_ret = pd.read_sql(sql_request, conn)\n'
            for olozu__buygl, nfinl__kfk in zip(nfs__sbhf, col_names):
                htfye__qhg += "    {} = df_ret['{}'].values\n".format(
                    olozu__buygl, nfinl__kfk)
        htfye__qhg += '  return ({},)\n'.format(', '.join(pbxrt__xpfxb for
            pbxrt__xpfxb in nfs__sbhf))
    mvoi__siulk = {'bodo': bodo}
    if db_type == 'snowflake':
        mvoi__siulk.update(rylli__upka)
        mvoi__siulk.update({'np': np, 'unicode_to_utf8': unicode_to_utf8,
            'check_and_propagate_cpp_exception':
            check_and_propagate_cpp_exception, 'snowflake_read':
            _snowflake_read, 'info_to_array': info_to_array,
            'info_from_table': info_from_table, 'delete_table': delete_table})
    else:
        mvoi__siulk.update({'sqlalchemy_check': sqlalchemy_check, 'pd': pd,
            'objmode': objmode, 'bcast_scalar': bcast_scalar,
            'pymysql_check': pymysql_check, 'cx_oracle_check':
            cx_oracle_check, 'psycopg2_check': psycopg2_check})
    wqyym__uyajd = {}
    exec(htfye__qhg, mvoi__siulk, wqyym__uyajd)
    rbin__kyib = wqyym__uyajd['sql_reader_py']
    rapq__dznm = numba.njit(rbin__kyib)
    compiled_funcs.append(rapq__dznm)
    return rapq__dznm


_snowflake_read = types.ExternalFunction('snowflake_read', table_type(types
    .voidptr, types.voidptr, types.boolean, types.int64, types.voidptr))
import llvmlite.binding as ll
from bodo.io import arrow_cpp
ll.add_symbol('snowflake_read', arrow_cpp.snowflake_read)
