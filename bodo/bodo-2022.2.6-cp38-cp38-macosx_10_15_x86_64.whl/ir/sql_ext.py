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
    sruix__lsriy = []
    cvutd__bjbfz = []
    wncot__flhsa = []
    for okj__jihti, tmg__jeev in enumerate(sql_node.out_vars):
        if tmg__jeev.name in lives:
            sruix__lsriy.append(sql_node.df_colnames[okj__jihti])
            cvutd__bjbfz.append(sql_node.out_vars[okj__jihti])
            wncot__flhsa.append(sql_node.out_types[okj__jihti])
    sql_node.df_colnames = sruix__lsriy
    sql_node.out_vars = cvutd__bjbfz
    sql_node.out_types = wncot__flhsa
    if len(sql_node.out_vars) == 0:
        return None
    return sql_node


def sql_distributed_run(sql_node, array_dists, typemap, calltypes,
    typingctx, targetctx):
    if bodo.user_logging.get_verbose_level() >= 1:
        abzk__vosu = (
            'Finish column pruning on read_sql node:\n%s\nColumns loaded %s\n')
        nkg__dsbmp = sql_node.loc.strformat()
        epk__hfdze = sql_node.df_colnames
        bodo.user_logging.log_message('Column Pruning', abzk__vosu,
            nkg__dsbmp, epk__hfdze)
        xuh__zvd = [pphlh__sweoy for okj__jihti, pphlh__sweoy in enumerate(
            sql_node.df_colnames) if isinstance(sql_node.out_types[
            okj__jihti], bodo.libs.dict_arr_ext.DictionaryArrayType)]
        if xuh__zvd:
            wsto__ripmm = """Finished optimized encoding on read_sql node:
%s
Columns %s using dictionary encoding to reduce memory usage.
"""
            bodo.user_logging.log_message('Dictionary Encoding',
                wsto__ripmm, nkg__dsbmp, xuh__zvd)
    parallel = False
    if array_dists is not None:
        parallel = True
        for xrpke__cltcp in sql_node.out_vars:
            if array_dists[xrpke__cltcp.name
                ] != distributed_pass.Distribution.OneD and array_dists[
                xrpke__cltcp.name] != distributed_pass.Distribution.OneD_Var:
                parallel = False
    if sql_node.unsupported_columns:
        loxwq__fmaa = set(sql_node.unsupported_columns)
        zto__ifq = set()
        pgkm__hklr = 0
        for fxfg__wjek in sql_node.df_colnames:
            while sql_node.original_df_colnames[pgkm__hklr] != fxfg__wjek:
                pgkm__hklr += 1
            if pgkm__hklr in loxwq__fmaa:
                zto__ifq.add(pgkm__hklr)
            pgkm__hklr += 1
        if zto__ifq:
            aoboa__dse = sorted(zto__ifq)
            huqb__vhp = [
                f'pandas.read_sql(): 1 or more columns found with Arrow types that are not supported in Bodo and could not be eliminated. '
                 +
                'Please manually remove these columns from your sql query by specifying the columns you need in your SELECT statement. If these '
                 +
                'columns are needed, you will need to modify your dataset to use a supported type.'
                , 'Unsupported Columns:']
            mbsr__xgs = 0
            for yaga__lcalw in aoboa__dse:
                while sql_node.unsupported_columns[mbsr__xgs] != yaga__lcalw:
                    mbsr__xgs += 1
                huqb__vhp.append(
                    f"Column '{sql_node.original_df_colnames[yaga__lcalw]}' with unsupported arrow type {sql_node.unsupported_arrow_types[mbsr__xgs]}"
                    )
                mbsr__xgs += 1
            sazu__yric = '\n'.join(huqb__vhp)
            raise BodoError(sazu__yric, loc=sql_node.loc)
    wzj__nfuqu = len(sql_node.out_vars)
    wyt__wjp = ', '.join('arr' + str(okj__jihti) for okj__jihti in range(
        wzj__nfuqu))
    vkrba__vxdtv, nipbc__sll = bodo.ir.connector.generate_filter_map(sql_node
        .filters)
    lsf__zpqo = ', '.join(vkrba__vxdtv.values())
    hqgp__funu = f'def sql_impl(sql_request, conn, {lsf__zpqo}):\n'
    if sql_node.filters:
        rbwq__vfzgx = []
        for ajhrt__ijr in sql_node.filters:
            yvwhe__bwgn = [' '.join(['(', atoo__yvj[0], atoo__yvj[1], '{' +
                vkrba__vxdtv[atoo__yvj[2].name] + '}' if isinstance(
                atoo__yvj[2], ir.Var) else atoo__yvj[2], ')']) for
                atoo__yvj in ajhrt__ijr]
            rbwq__vfzgx.append(' ( ' + ' AND '.join(yvwhe__bwgn) + ' ) ')
        hesy__lut = ' WHERE ' + ' OR '.join(rbwq__vfzgx)
        for okj__jihti, gboiz__wkoa in enumerate(vkrba__vxdtv.values()):
            hqgp__funu += (
                f'    {gboiz__wkoa} = get_sql_literal({gboiz__wkoa})\n')
        hqgp__funu += f'    sql_request = f"{{sql_request}} {hesy__lut}"\n'
    hqgp__funu += '    ({},) = _sql_reader_py(sql_request, conn)\n'.format(
        wyt__wjp)
    rlok__liyu = {}
    exec(hqgp__funu, {}, rlok__liyu)
    jxn__erjtz = rlok__liyu['sql_impl']
    diemh__ctdqq = _gen_sql_reader_py(sql_node.df_colnames, sql_node.
        out_types, typingctx, targetctx, sql_node.db_type, sql_node.limit,
        sql_node.converted_colnames, parallel, sql_node.is_select_query)
    uiq__nxz = compile_to_numba_ir(jxn__erjtz, {'_sql_reader_py':
        diemh__ctdqq, 'bcast_scalar': bcast_scalar, 'bcast': bcast,
        'get_sql_literal': _get_snowflake_sql_literal}, typingctx=typingctx,
        targetctx=targetctx, arg_typs=(string_type, string_type) + tuple(
        typemap[xrpke__cltcp.name] for xrpke__cltcp in nipbc__sll), typemap
        =typemap, calltypes=calltypes).blocks.popitem()[1]
    if sql_node.is_select_query:
        miqyy__ztd = escape_column_names(sql_node.df_colnames, sql_node.
            db_type, sql_node.converted_colnames)
        if sql_node.db_type == 'oracle':
            pijp__qabz = ('SELECT ' + miqyy__ztd + ' FROM (' + sql_node.
                sql_request + ') TEMP')
        else:
            pijp__qabz = ('SELECT ' + miqyy__ztd + ' FROM (' + sql_node.
                sql_request + ') as TEMP')
    else:
        pijp__qabz = sql_node.sql_request
    replace_arg_nodes(uiq__nxz, [ir.Const(pijp__qabz, sql_node.loc), ir.
        Const(sql_node.connection, sql_node.loc)] + nipbc__sll)
    rstc__yoaa = uiq__nxz.body[:-3]
    for okj__jihti in range(len(sql_node.out_vars)):
        rstc__yoaa[-len(sql_node.out_vars) + okj__jihti
            ].target = sql_node.out_vars[okj__jihti]
    return rstc__yoaa


def escape_column_names(col_names, db_type, converted_colnames):
    if db_type in ('snowflake', 'oracle'):
        rmpm__ssm = [(stes__qgmm.upper() if stes__qgmm in
            converted_colnames else stes__qgmm) for stes__qgmm in col_names]
        miqyy__ztd = ', '.join([f'"{stes__qgmm}"' for stes__qgmm in rmpm__ssm])
    elif db_type == 'mysql' or db_type == 'mysql+pymysql':
        miqyy__ztd = ', '.join([f'`{stes__qgmm}`' for stes__qgmm in col_names])
    else:
        miqyy__ztd = ', '.join([f'"{stes__qgmm}"' for stes__qgmm in col_names])
    return miqyy__ztd


@numba.generated_jit(nopython=True, no_cpython_wrapper=True)
def _get_snowflake_sql_literal_scalar(filter_value):
    iqrl__gczzp = types.unliteral(filter_value)
    if iqrl__gczzp == types.unicode_type:
        return lambda filter_value: f'$${filter_value}$$'
    elif isinstance(iqrl__gczzp, (types.Integer, types.Float)
        ) or filter_value == types.bool_:
        return lambda filter_value: str(filter_value)
    elif iqrl__gczzp == bodo.pd_timestamp_type:

        def impl(filter_value):
            dydyf__lvf = filter_value.nanosecond
            ftf__dfmh = ''
            if dydyf__lvf < 10:
                ftf__dfmh = '00'
            elif dydyf__lvf < 100:
                ftf__dfmh = '0'
            return (
                f"timestamp '{filter_value.strftime('%Y-%m-%d %H:%M:%S.%f')}{ftf__dfmh}{dydyf__lvf}'"
                )
        return impl
    elif iqrl__gczzp == bodo.datetime_date_type:
        return (lambda filter_value:
            f"date '{filter_value.strftime('%Y-%m-%d')}'")
    else:
        raise BodoError(
            f'pd.read_sql(): Internal error, unsupported scalar type {iqrl__gczzp} used in filter pushdown.'
            )


@numba.generated_jit(nopython=True, no_cpython_wrapper=True)
def _get_snowflake_sql_literal(filter_value):
    scalar_isinstance = types.Integer, types.Float
    lxg__ztub = (bodo.datetime_date_type, bodo.pd_timestamp_type, types.
        unicode_type, types.bool_)
    iqrl__gczzp = types.unliteral(filter_value)
    if isinstance(iqrl__gczzp, types.List) and (isinstance(iqrl__gczzp.
        dtype, scalar_isinstance) or iqrl__gczzp.dtype in lxg__ztub):

        def impl(filter_value):
            iuei__sik = ', '.join([_get_snowflake_sql_literal_scalar(
                stes__qgmm) for stes__qgmm in filter_value])
            return f'({iuei__sik})'
        return impl
    elif isinstance(iqrl__gczzp, scalar_isinstance
        ) or iqrl__gczzp in lxg__ztub:
        return lambda filter_value: _get_snowflake_sql_literal_scalar(
            filter_value)
    else:
        raise BodoError(
            f'pd.read_sql(): Internal error, unsupported type {iqrl__gczzp} used in filter pushdown.'
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
    except ImportError as wduzf__evmb:
        mua__uoiu = (
            "Using URI string without sqlalchemy installed. sqlalchemy can be installed by calling 'conda install -c conda-forge sqlalchemy'."
            )
        raise BodoError(mua__uoiu)


@numba.njit
def pymysql_check():
    with numba.objmode():
        pymysql_check_()


def pymysql_check_():
    try:
        import pymysql
    except ImportError as wduzf__evmb:
        mua__uoiu = (
            "Using MySQL URI string requires pymsql to be installed. It can be installed by calling 'conda install -c conda-forge pymysql' or 'pip install PyMySQL'."
            )
        raise BodoError(mua__uoiu)


@numba.njit
def cx_oracle_check():
    with numba.objmode():
        cx_oracle_check_()


def cx_oracle_check_():
    try:
        import cx_Oracle
    except ImportError as wduzf__evmb:
        mua__uoiu = (
            "Using Oracle URI string requires cx_oracle to be installed. It can be installed by calling 'conda install -c conda-forge cx_oracle' or 'pip install cx-Oracle'."
            )
        raise BodoError(mua__uoiu)


@numba.njit
def psycopg2_check():
    with numba.objmode():
        psycopg2_check_()


def psycopg2_check_():
    try:
        import psycopg2
    except ImportError as wduzf__evmb:
        mua__uoiu = (
            "Using PostgreSQL URI string requires psycopg2 to be installed. It can be installed by calling 'conda install -c conda-forge psycopg2' or 'pip install psycopg2'."
            )
        raise BodoError(mua__uoiu)


def req_limit(sql_request):
    import re
    ehfu__bppk = re.compile('LIMIT\\s+(\\d+)\\s*$', re.IGNORECASE)
    shbxe__khhev = ehfu__bppk.search(sql_request)
    if shbxe__khhev:
        return int(shbxe__khhev.group(1))
    else:
        return None


def _gen_sql_reader_py(col_names, col_typs, typingctx, targetctx, db_type,
    limit, converted_colnames, parallel, is_select_query):
    yhjq__znasv = [sanitize_varname(pphlh__sweoy) for pphlh__sweoy in col_names
        ]
    dyuhr__tnga = ["{}='{}'".format(xdbkz__cgah, _get_dtype_str(nvqqr__dzmf
        )) for xdbkz__cgah, nvqqr__dzmf in zip(yhjq__znasv, col_typs)]
    if bodo.sql_access_method == 'multiple_access_nb_row_first':
        hqgp__funu = 'def sql_reader_py(sql_request, conn):\n'
        if db_type == 'snowflake':
            hfbs__txwww = {}
            for okj__jihti, iddiv__fisx in enumerate(col_typs):
                hfbs__txwww[f'col_{okj__jihti}_type'] = iddiv__fisx
            hqgp__funu += (
                f"  ev = bodo.utils.tracing.Event('read_snowflake', {parallel})\n"
                )

            def is_nullable(typ):
                return bodo.utils.utils.is_array_typ(typ, False
                    ) and not isinstance(typ, types.Array)
            pptcg__fbr = [int(is_nullable(iddiv__fisx)) for iddiv__fisx in
                col_typs]
            hqgp__funu += f"""  out_table = snowflake_read(unicode_to_utf8(sql_request), unicode_to_utf8(conn), {parallel}, {len(col_names)}, np.array({pptcg__fbr}, dtype=np.int32).ctypes)
"""
            hqgp__funu += '  check_and_propagate_cpp_exception()\n'
            for okj__jihti, nrbga__ohe in enumerate(yhjq__znasv):
                hqgp__funu += f"""  {nrbga__ohe} = info_to_array(info_from_table(out_table, {okj__jihti}), col_{okj__jihti}_type)
"""
            hqgp__funu += '  delete_table(out_table)\n'
            hqgp__funu += f'  ev.finalize()\n'
        else:
            hqgp__funu += '  sqlalchemy_check()\n'
            if db_type == 'mysql' or db_type == 'mysql+pymysql':
                hqgp__funu += '  pymysql_check()\n'
            elif db_type == 'oracle':
                hqgp__funu += '  cx_oracle_check()\n'
            elif db_type == 'postgresql' or db_type == 'postgresql+psycopg2':
                hqgp__funu += '  psycopg2_check()\n'
            if parallel and is_select_query:
                hqgp__funu += '  rank = bodo.libs.distributed_api.get_rank()\n'
                if limit is not None:
                    hqgp__funu += f'  nb_row = {limit}\n'
                else:
                    hqgp__funu += '  with objmode(nb_row="int64"):\n'
                    hqgp__funu += f'     if rank == {MPI_ROOT}:\n'
                    hqgp__funu += """         sql_cons = 'select count(*) from (' + sql_request + ') x'
"""
                    hqgp__funu += (
                        '         frame = pd.read_sql(sql_cons, conn)\n')
                    hqgp__funu += '         nb_row = frame.iat[0,0]\n'
                    hqgp__funu += '     else:\n'
                    hqgp__funu += '         nb_row = 0\n'
                    hqgp__funu += '  nb_row = bcast_scalar(nb_row)\n'
                hqgp__funu += '  with objmode({}):\n'.format(', '.join(
                    dyuhr__tnga))
                hqgp__funu += """    offset, limit = bodo.libs.distributed_api.get_start_count(nb_row)
"""
                miqyy__ztd = escape_column_names(col_names, db_type,
                    converted_colnames)
                if db_type == 'oracle':
                    hqgp__funu += f"""    sql_cons = 'select {miqyy__ztd} from (' + sql_request + ') OFFSET ' + str(offset) + ' ROWS FETCH NEXT ' + str(limit) + ' ROWS ONLY'
"""
                else:
                    hqgp__funu += f"""    sql_cons = 'select {miqyy__ztd} from (' + sql_request + ') x LIMIT ' + str(limit) + ' OFFSET ' + str(offset)
"""
                hqgp__funu += '    df_ret = pd.read_sql(sql_cons, conn)\n'
            else:
                hqgp__funu += '  with objmode({}):\n'.format(', '.join(
                    dyuhr__tnga))
                hqgp__funu += '    df_ret = pd.read_sql(sql_request, conn)\n'
            for xdbkz__cgah, kwvwz__foos in zip(yhjq__znasv, col_names):
                hqgp__funu += "    {} = df_ret['{}'].values\n".format(
                    xdbkz__cgah, kwvwz__foos)
        hqgp__funu += '  return ({},)\n'.format(', '.join(tkcm__neif for
            tkcm__neif in yhjq__znasv))
    ocr__ojwxg = {'bodo': bodo}
    if db_type == 'snowflake':
        ocr__ojwxg.update(hfbs__txwww)
        ocr__ojwxg.update({'np': np, 'unicode_to_utf8': unicode_to_utf8,
            'check_and_propagate_cpp_exception':
            check_and_propagate_cpp_exception, 'snowflake_read':
            _snowflake_read, 'info_to_array': info_to_array,
            'info_from_table': info_from_table, 'delete_table': delete_table})
    else:
        ocr__ojwxg.update({'sqlalchemy_check': sqlalchemy_check, 'pd': pd,
            'objmode': objmode, 'bcast_scalar': bcast_scalar,
            'pymysql_check': pymysql_check, 'cx_oracle_check':
            cx_oracle_check, 'psycopg2_check': psycopg2_check})
    rlok__liyu = {}
    exec(hqgp__funu, ocr__ojwxg, rlok__liyu)
    diemh__ctdqq = rlok__liyu['sql_reader_py']
    kwaff__onmk = numba.njit(diemh__ctdqq)
    compiled_funcs.append(kwaff__onmk)
    return kwaff__onmk


_snowflake_read = types.ExternalFunction('snowflake_read', table_type(types
    .voidptr, types.voidptr, types.boolean, types.int64, types.voidptr))
import llvmlite.binding as ll
from bodo.io import arrow_cpp
ll.add_symbol('snowflake_read', arrow_cpp.snowflake_read)
