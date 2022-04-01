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
    sew__irac = []
    dqtef__gvgeo = []
    ruhw__qgppf = []
    for hnu__zetu, ipnv__nir in enumerate(sql_node.out_vars):
        if ipnv__nir.name in lives:
            sew__irac.append(sql_node.df_colnames[hnu__zetu])
            dqtef__gvgeo.append(sql_node.out_vars[hnu__zetu])
            ruhw__qgppf.append(sql_node.out_types[hnu__zetu])
    sql_node.df_colnames = sew__irac
    sql_node.out_vars = dqtef__gvgeo
    sql_node.out_types = ruhw__qgppf
    if len(sql_node.out_vars) == 0:
        return None
    return sql_node


def sql_distributed_run(sql_node, array_dists, typemap, calltypes,
    typingctx, targetctx):
    if bodo.user_logging.get_verbose_level() >= 1:
        eem__flkv = (
            'Finish column pruning on read_sql node:\n%s\nColumns loaded %s\n')
        vnud__vrild = sql_node.loc.strformat()
        nvwyu__oaeib = sql_node.df_colnames
        bodo.user_logging.log_message('Column Pruning', eem__flkv,
            vnud__vrild, nvwyu__oaeib)
        evyx__nnp = [vjq__exdhm for hnu__zetu, vjq__exdhm in enumerate(
            sql_node.df_colnames) if isinstance(sql_node.out_types[
            hnu__zetu], bodo.libs.dict_arr_ext.DictionaryArrayType)]
        if evyx__nnp:
            hkfj__agu = """Finished optimized encoding on read_sql node:
%s
Columns %s using dictionary encoding to reduce memory usage.
"""
            bodo.user_logging.log_message('Dictionary Encoding', hkfj__agu,
                vnud__vrild, evyx__nnp)
    parallel = False
    if array_dists is not None:
        parallel = True
        for mlz__yaz in sql_node.out_vars:
            if array_dists[mlz__yaz.name
                ] != distributed_pass.Distribution.OneD and array_dists[
                mlz__yaz.name] != distributed_pass.Distribution.OneD_Var:
                parallel = False
    if sql_node.unsupported_columns:
        qcx__mbvu = set(sql_node.unsupported_columns)
        nzo__sgva = set()
        uhvy__itiej = 0
        for psqt__jhzch in sql_node.df_colnames:
            while sql_node.original_df_colnames[uhvy__itiej] != psqt__jhzch:
                uhvy__itiej += 1
            if uhvy__itiej in qcx__mbvu:
                nzo__sgva.add(uhvy__itiej)
            uhvy__itiej += 1
        if nzo__sgva:
            xtgt__qnpo = sorted(nzo__sgva)
            ngion__eeyl = [
                f'pandas.read_sql(): 1 or more columns found with Arrow types that are not supported in Bodo and could not be eliminated. '
                 +
                'Please manually remove these columns from your sql query by specifying the columns you need in your SELECT statement. If these '
                 +
                'columns are needed, you will need to modify your dataset to use a supported type.'
                , 'Unsupported Columns:']
            onxfj__cqk = 0
            for qloi__tidl in xtgt__qnpo:
                while sql_node.unsupported_columns[onxfj__cqk] != qloi__tidl:
                    onxfj__cqk += 1
                ngion__eeyl.append(
                    f"Column '{sql_node.original_df_colnames[qloi__tidl]}' with unsupported arrow type {sql_node.unsupported_arrow_types[onxfj__cqk]}"
                    )
                onxfj__cqk += 1
            bmqf__hov = '\n'.join(ngion__eeyl)
            raise BodoError(bmqf__hov, loc=sql_node.loc)
    gij__zcjb = len(sql_node.out_vars)
    txn__xqsfk = ', '.join('arr' + str(hnu__zetu) for hnu__zetu in range(
        gij__zcjb))
    fsigw__hbtdf, rzzp__fbhng = bodo.ir.connector.generate_filter_map(sql_node
        .filters)
    gvkc__qtzh = ', '.join(fsigw__hbtdf.values())
    qkzr__qoejy = f'def sql_impl(sql_request, conn, {gvkc__qtzh}):\n'
    if sql_node.filters:
        siq__eommu = []
        for sxgth__aiwe in sql_node.filters:
            veusn__yfvlx = [' '.join(['(', lxdmz__oawja[0], lxdmz__oawja[1],
                '{' + fsigw__hbtdf[lxdmz__oawja[2].name] + '}' if
                isinstance(lxdmz__oawja[2], ir.Var) else lxdmz__oawja[2],
                ')']) for lxdmz__oawja in sxgth__aiwe]
            siq__eommu.append(' ( ' + ' AND '.join(veusn__yfvlx) + ' ) ')
        res__yjphb = ' WHERE ' + ' OR '.join(siq__eommu)
        for hnu__zetu, zgv__azmmk in enumerate(fsigw__hbtdf.values()):
            qkzr__qoejy += (
                f'    {zgv__azmmk} = get_sql_literal({zgv__azmmk})\n')
        qkzr__qoejy += f'    sql_request = f"{{sql_request}} {res__yjphb}"\n'
    qkzr__qoejy += '    ({},) = _sql_reader_py(sql_request, conn)\n'.format(
        txn__xqsfk)
    yhkob__nfp = {}
    exec(qkzr__qoejy, {}, yhkob__nfp)
    qwf__dba = yhkob__nfp['sql_impl']
    ddpc__zjuqs = _gen_sql_reader_py(sql_node.df_colnames, sql_node.
        out_types, typingctx, targetctx, sql_node.db_type, sql_node.limit,
        sql_node.converted_colnames, parallel, sql_node.is_select_query)
    fmu__mmtq = compile_to_numba_ir(qwf__dba, {'_sql_reader_py':
        ddpc__zjuqs, 'bcast_scalar': bcast_scalar, 'bcast': bcast,
        'get_sql_literal': _get_snowflake_sql_literal}, typingctx=typingctx,
        targetctx=targetctx, arg_typs=(string_type, string_type) + tuple(
        typemap[mlz__yaz.name] for mlz__yaz in rzzp__fbhng), typemap=
        typemap, calltypes=calltypes).blocks.popitem()[1]
    if sql_node.is_select_query:
        vyekz__ryw = escape_column_names(sql_node.df_colnames, sql_node.
            db_type, sql_node.converted_colnames)
        if sql_node.db_type == 'oracle':
            ohea__egzxp = ('SELECT ' + vyekz__ryw + ' FROM (' + sql_node.
                sql_request + ') TEMP')
        else:
            ohea__egzxp = ('SELECT ' + vyekz__ryw + ' FROM (' + sql_node.
                sql_request + ') as TEMP')
    else:
        ohea__egzxp = sql_node.sql_request
    replace_arg_nodes(fmu__mmtq, [ir.Const(ohea__egzxp, sql_node.loc), ir.
        Const(sql_node.connection, sql_node.loc)] + rzzp__fbhng)
    ivcyl__ngot = fmu__mmtq.body[:-3]
    for hnu__zetu in range(len(sql_node.out_vars)):
        ivcyl__ngot[-len(sql_node.out_vars) + hnu__zetu
            ].target = sql_node.out_vars[hnu__zetu]
    return ivcyl__ngot


def escape_column_names(col_names, db_type, converted_colnames):
    if db_type in ('snowflake', 'oracle'):
        rod__aiq = [(zqe__fmye.upper() if zqe__fmye in converted_colnames else
            zqe__fmye) for zqe__fmye in col_names]
        vyekz__ryw = ', '.join([f'"{zqe__fmye}"' for zqe__fmye in rod__aiq])
    elif db_type == 'mysql' or db_type == 'mysql+pymysql':
        vyekz__ryw = ', '.join([f'`{zqe__fmye}`' for zqe__fmye in col_names])
    else:
        vyekz__ryw = ', '.join([f'"{zqe__fmye}"' for zqe__fmye in col_names])
    return vyekz__ryw


@numba.generated_jit(nopython=True, no_cpython_wrapper=True)
def _get_snowflake_sql_literal_scalar(filter_value):
    dmt__cqdr = types.unliteral(filter_value)
    bodo.hiframes.pd_timestamp_ext.check_tz_aware_unsupported(dmt__cqdr,
        'Filter pushdown')
    if dmt__cqdr == types.unicode_type:
        return lambda filter_value: f'$${filter_value}$$'
    elif isinstance(dmt__cqdr, (types.Integer, types.Float)
        ) or filter_value == types.bool_:
        return lambda filter_value: str(filter_value)
    elif dmt__cqdr == bodo.pd_timestamp_type:

        def impl(filter_value):
            lirz__cppu = filter_value.nanosecond
            snnsc__epa = ''
            if lirz__cppu < 10:
                snnsc__epa = '00'
            elif lirz__cppu < 100:
                snnsc__epa = '0'
            return (
                f"timestamp '{filter_value.strftime('%Y-%m-%d %H:%M:%S.%f')}{snnsc__epa}{lirz__cppu}'"
                )
        return impl
    elif dmt__cqdr == bodo.datetime_date_type:
        return (lambda filter_value:
            f"date '{filter_value.strftime('%Y-%m-%d')}'")
    else:
        raise BodoError(
            f'pd.read_sql(): Internal error, unsupported scalar type {dmt__cqdr} used in filter pushdown.'
            )


@numba.generated_jit(nopython=True, no_cpython_wrapper=True)
def _get_snowflake_sql_literal(filter_value):
    scalar_isinstance = types.Integer, types.Float
    qkw__lzb = (bodo.datetime_date_type, bodo.pd_timestamp_type, types.
        unicode_type, types.bool_)
    dmt__cqdr = types.unliteral(filter_value)
    if isinstance(dmt__cqdr, types.List) and (isinstance(dmt__cqdr.dtype,
        scalar_isinstance) or dmt__cqdr.dtype in qkw__lzb):

        def impl(filter_value):
            teuy__dpvk = ', '.join([_get_snowflake_sql_literal_scalar(
                zqe__fmye) for zqe__fmye in filter_value])
            return f'({teuy__dpvk})'
        return impl
    elif isinstance(dmt__cqdr, scalar_isinstance) or dmt__cqdr in qkw__lzb:
        return lambda filter_value: _get_snowflake_sql_literal_scalar(
            filter_value)
    else:
        raise BodoError(
            f'pd.read_sql(): Internal error, unsupported type {dmt__cqdr} used in filter pushdown.'
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
    except ImportError as hoek__bxi:
        jzz__dyq = (
            "Using URI string without sqlalchemy installed. sqlalchemy can be installed by calling 'conda install -c conda-forge sqlalchemy'."
            )
        raise BodoError(jzz__dyq)


@numba.njit
def pymysql_check():
    with numba.objmode():
        pymysql_check_()


def pymysql_check_():
    try:
        import pymysql
    except ImportError as hoek__bxi:
        jzz__dyq = (
            "Using MySQL URI string requires pymsql to be installed. It can be installed by calling 'conda install -c conda-forge pymysql' or 'pip install PyMySQL'."
            )
        raise BodoError(jzz__dyq)


@numba.njit
def cx_oracle_check():
    with numba.objmode():
        cx_oracle_check_()


def cx_oracle_check_():
    try:
        import cx_Oracle
    except ImportError as hoek__bxi:
        jzz__dyq = (
            "Using Oracle URI string requires cx_oracle to be installed. It can be installed by calling 'conda install -c conda-forge cx_oracle' or 'pip install cx-Oracle'."
            )
        raise BodoError(jzz__dyq)


@numba.njit
def psycopg2_check():
    with numba.objmode():
        psycopg2_check_()


def psycopg2_check_():
    try:
        import psycopg2
    except ImportError as hoek__bxi:
        jzz__dyq = (
            "Using PostgreSQL URI string requires psycopg2 to be installed. It can be installed by calling 'conda install -c conda-forge psycopg2' or 'pip install psycopg2'."
            )
        raise BodoError(jzz__dyq)


def req_limit(sql_request):
    import re
    xdit__rickf = re.compile('LIMIT\\s+(\\d+)\\s*$', re.IGNORECASE)
    epj__qjxx = xdit__rickf.search(sql_request)
    if epj__qjxx:
        return int(epj__qjxx.group(1))
    else:
        return None


def _gen_sql_reader_py(col_names, col_typs, typingctx, targetctx, db_type,
    limit, converted_colnames, parallel, is_select_query):
    lnw__uyj = [sanitize_varname(vjq__exdhm) for vjq__exdhm in col_names]
    hck__upo = ["{}='{}'".format(kpwcw__uufpq, _get_dtype_str(fwb__qmikl)) for
        kpwcw__uufpq, fwb__qmikl in zip(lnw__uyj, col_typs)]
    if bodo.sql_access_method == 'multiple_access_nb_row_first':
        qkzr__qoejy = 'def sql_reader_py(sql_request, conn):\n'
        if db_type == 'snowflake':
            sdz__yjzjx = {}
            for hnu__zetu, huuo__mwa in enumerate(col_typs):
                sdz__yjzjx[f'col_{hnu__zetu}_type'] = huuo__mwa
            qkzr__qoejy += (
                f"  ev = bodo.utils.tracing.Event('read_snowflake', {parallel})\n"
                )

            def is_nullable(typ):
                return bodo.utils.utils.is_array_typ(typ, False
                    ) and not isinstance(typ, types.Array) and not isinstance(
                    typ, bodo.DatetimeArrayType)
            vuii__dnoyd = [int(is_nullable(huuo__mwa)) for huuo__mwa in
                col_typs]
            qkzr__qoejy += f"""  out_table = snowflake_read(unicode_to_utf8(sql_request), unicode_to_utf8(conn), {parallel}, {len(col_names)}, np.array({vuii__dnoyd}, dtype=np.int32).ctypes)
"""
            qkzr__qoejy += '  check_and_propagate_cpp_exception()\n'
            for hnu__zetu, ggws__jqous in enumerate(lnw__uyj):
                qkzr__qoejy += f"""  {ggws__jqous} = info_to_array(info_from_table(out_table, {hnu__zetu}), col_{hnu__zetu}_type)
"""
            qkzr__qoejy += '  delete_table(out_table)\n'
            qkzr__qoejy += f'  ev.finalize()\n'
        else:
            qkzr__qoejy += '  sqlalchemy_check()\n'
            if db_type == 'mysql' or db_type == 'mysql+pymysql':
                qkzr__qoejy += '  pymysql_check()\n'
            elif db_type == 'oracle':
                qkzr__qoejy += '  cx_oracle_check()\n'
            elif db_type == 'postgresql' or db_type == 'postgresql+psycopg2':
                qkzr__qoejy += '  psycopg2_check()\n'
            if parallel and is_select_query:
                qkzr__qoejy += (
                    '  rank = bodo.libs.distributed_api.get_rank()\n')
                if limit is not None:
                    qkzr__qoejy += f'  nb_row = {limit}\n'
                else:
                    qkzr__qoejy += '  with objmode(nb_row="int64"):\n'
                    qkzr__qoejy += f'     if rank == {MPI_ROOT}:\n'
                    qkzr__qoejy += """         sql_cons = 'select count(*) from (' + sql_request + ') x'
"""
                    qkzr__qoejy += (
                        '         frame = pd.read_sql(sql_cons, conn)\n')
                    qkzr__qoejy += '         nb_row = frame.iat[0,0]\n'
                    qkzr__qoejy += '     else:\n'
                    qkzr__qoejy += '         nb_row = 0\n'
                    qkzr__qoejy += '  nb_row = bcast_scalar(nb_row)\n'
                qkzr__qoejy += '  with objmode({}):\n'.format(', '.join(
                    hck__upo))
                qkzr__qoejy += """    offset, limit = bodo.libs.distributed_api.get_start_count(nb_row)
"""
                vyekz__ryw = escape_column_names(col_names, db_type,
                    converted_colnames)
                if db_type == 'oracle':
                    qkzr__qoejy += f"""    sql_cons = 'select {vyekz__ryw} from (' + sql_request + ') OFFSET ' + str(offset) + ' ROWS FETCH NEXT ' + str(limit) + ' ROWS ONLY'
"""
                else:
                    qkzr__qoejy += f"""    sql_cons = 'select {vyekz__ryw} from (' + sql_request + ') x LIMIT ' + str(limit) + ' OFFSET ' + str(offset)
"""
                qkzr__qoejy += '    df_ret = pd.read_sql(sql_cons, conn)\n'
            else:
                qkzr__qoejy += '  with objmode({}):\n'.format(', '.join(
                    hck__upo))
                qkzr__qoejy += '    df_ret = pd.read_sql(sql_request, conn)\n'
            for kpwcw__uufpq, wotxd__yekv in zip(lnw__uyj, col_names):
                qkzr__qoejy += "    {} = df_ret['{}'].values\n".format(
                    kpwcw__uufpq, wotxd__yekv)
        qkzr__qoejy += '  return ({},)\n'.format(', '.join(xnlwe__dzx for
            xnlwe__dzx in lnw__uyj))
    crn__vftc = {'bodo': bodo}
    if db_type == 'snowflake':
        crn__vftc.update(sdz__yjzjx)
        crn__vftc.update({'np': np, 'unicode_to_utf8': unicode_to_utf8,
            'check_and_propagate_cpp_exception':
            check_and_propagate_cpp_exception, 'snowflake_read':
            _snowflake_read, 'info_to_array': info_to_array,
            'info_from_table': info_from_table, 'delete_table': delete_table})
    else:
        crn__vftc.update({'sqlalchemy_check': sqlalchemy_check, 'pd': pd,
            'objmode': objmode, 'bcast_scalar': bcast_scalar,
            'pymysql_check': pymysql_check, 'cx_oracle_check':
            cx_oracle_check, 'psycopg2_check': psycopg2_check})
    yhkob__nfp = {}
    exec(qkzr__qoejy, crn__vftc, yhkob__nfp)
    ddpc__zjuqs = yhkob__nfp['sql_reader_py']
    ucyp__uqk = numba.njit(ddpc__zjuqs)
    compiled_funcs.append(ucyp__uqk)
    return ucyp__uqk


_snowflake_read = types.ExternalFunction('snowflake_read', table_type(types
    .voidptr, types.voidptr, types.boolean, types.int64, types.voidptr))
import llvmlite.binding as ll
from bodo.io import arrow_cpp
ll.add_symbol('snowflake_read', arrow_cpp.snowflake_read)
