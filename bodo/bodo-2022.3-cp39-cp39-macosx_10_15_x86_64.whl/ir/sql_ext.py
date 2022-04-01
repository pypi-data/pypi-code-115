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
    hnwdb__gydg = []
    ycja__ryphk = []
    yvbk__msjd = []
    for sdl__hkh, apu__ybgcq in enumerate(sql_node.out_vars):
        if apu__ybgcq.name in lives:
            hnwdb__gydg.append(sql_node.df_colnames[sdl__hkh])
            ycja__ryphk.append(sql_node.out_vars[sdl__hkh])
            yvbk__msjd.append(sql_node.out_types[sdl__hkh])
    sql_node.df_colnames = hnwdb__gydg
    sql_node.out_vars = ycja__ryphk
    sql_node.out_types = yvbk__msjd
    if len(sql_node.out_vars) == 0:
        return None
    return sql_node


def sql_distributed_run(sql_node, array_dists, typemap, calltypes,
    typingctx, targetctx):
    if bodo.user_logging.get_verbose_level() >= 1:
        njhy__twmcf = (
            'Finish column pruning on read_sql node:\n%s\nColumns loaded %s\n')
        cez__kadar = sql_node.loc.strformat()
        klbrk__qod = sql_node.df_colnames
        bodo.user_logging.log_message('Column Pruning', njhy__twmcf,
            cez__kadar, klbrk__qod)
        yqt__ebm = [muvbf__zeh for sdl__hkh, muvbf__zeh in enumerate(
            sql_node.df_colnames) if isinstance(sql_node.out_types[sdl__hkh
            ], bodo.libs.dict_arr_ext.DictionaryArrayType)]
        if yqt__ebm:
            hljkk__wthcd = """Finished optimized encoding on read_sql node:
%s
Columns %s using dictionary encoding to reduce memory usage.
"""
            bodo.user_logging.log_message('Dictionary Encoding',
                hljkk__wthcd, cez__kadar, yqt__ebm)
    parallel = False
    if array_dists is not None:
        parallel = True
        for mxrx__nfmc in sql_node.out_vars:
            if array_dists[mxrx__nfmc.name
                ] != distributed_pass.Distribution.OneD and array_dists[
                mxrx__nfmc.name] != distributed_pass.Distribution.OneD_Var:
                parallel = False
    if sql_node.unsupported_columns:
        tmayk__kzp = set(sql_node.unsupported_columns)
        hymfw__loqip = set()
        veqq__plfqa = 0
        for xjetc__rzon in sql_node.df_colnames:
            while sql_node.original_df_colnames[veqq__plfqa] != xjetc__rzon:
                veqq__plfqa += 1
            if veqq__plfqa in tmayk__kzp:
                hymfw__loqip.add(veqq__plfqa)
            veqq__plfqa += 1
        if hymfw__loqip:
            mpoen__gjyip = sorted(hymfw__loqip)
            omw__lwmyn = [
                f'pandas.read_sql(): 1 or more columns found with Arrow types that are not supported in Bodo and could not be eliminated. '
                 +
                'Please manually remove these columns from your sql query by specifying the columns you need in your SELECT statement. If these '
                 +
                'columns are needed, you will need to modify your dataset to use a supported type.'
                , 'Unsupported Columns:']
            wybz__qmemg = 0
            for iun__qrirm in mpoen__gjyip:
                while sql_node.unsupported_columns[wybz__qmemg] != iun__qrirm:
                    wybz__qmemg += 1
                omw__lwmyn.append(
                    f"Column '{sql_node.original_df_colnames[iun__qrirm]}' with unsupported arrow type {sql_node.unsupported_arrow_types[wybz__qmemg]}"
                    )
                wybz__qmemg += 1
            hbnu__vij = '\n'.join(omw__lwmyn)
            raise BodoError(hbnu__vij, loc=sql_node.loc)
    mlsoc__raif = len(sql_node.out_vars)
    tqx__hvtd = ', '.join('arr' + str(sdl__hkh) for sdl__hkh in range(
        mlsoc__raif))
    mbu__zwyx, vhlg__xindo = bodo.ir.connector.generate_filter_map(sql_node
        .filters)
    bcefe__dnzxq = ', '.join(mbu__zwyx.values())
    ejn__yll = f'def sql_impl(sql_request, conn, {bcefe__dnzxq}):\n'
    if sql_node.filters:
        rwzru__jgj = []
        for xppd__bcnw in sql_node.filters:
            hwg__wofse = [' '.join(['(', dbu__navtk[0], dbu__navtk[1], '{' +
                mbu__zwyx[dbu__navtk[2].name] + '}' if isinstance(
                dbu__navtk[2], ir.Var) else dbu__navtk[2], ')']) for
                dbu__navtk in xppd__bcnw]
            rwzru__jgj.append(' ( ' + ' AND '.join(hwg__wofse) + ' ) ')
        owk__bdkit = ' WHERE ' + ' OR '.join(rwzru__jgj)
        for sdl__hkh, schm__iyykw in enumerate(mbu__zwyx.values()):
            ejn__yll += f'    {schm__iyykw} = get_sql_literal({schm__iyykw})\n'
        ejn__yll += f'    sql_request = f"{{sql_request}} {owk__bdkit}"\n'
    ejn__yll += '    ({},) = _sql_reader_py(sql_request, conn)\n'.format(
        tqx__hvtd)
    ljwsr__dxkdx = {}
    exec(ejn__yll, {}, ljwsr__dxkdx)
    mxzzc__tqi = ljwsr__dxkdx['sql_impl']
    ttk__rfa = _gen_sql_reader_py(sql_node.df_colnames, sql_node.out_types,
        typingctx, targetctx, sql_node.db_type, sql_node.limit, sql_node.
        converted_colnames, parallel, sql_node.is_select_query)
    txq__rey = compile_to_numba_ir(mxzzc__tqi, {'_sql_reader_py': ttk__rfa,
        'bcast_scalar': bcast_scalar, 'bcast': bcast, 'get_sql_literal':
        _get_snowflake_sql_literal}, typingctx=typingctx, targetctx=
        targetctx, arg_typs=(string_type, string_type) + tuple(typemap[
        mxrx__nfmc.name] for mxrx__nfmc in vhlg__xindo), typemap=typemap,
        calltypes=calltypes).blocks.popitem()[1]
    if sql_node.is_select_query:
        lfhpd__ukoxz = escape_column_names(sql_node.df_colnames, sql_node.
            db_type, sql_node.converted_colnames)
        if sql_node.db_type == 'oracle':
            pkag__bwhrb = ('SELECT ' + lfhpd__ukoxz + ' FROM (' + sql_node.
                sql_request + ') TEMP')
        else:
            pkag__bwhrb = ('SELECT ' + lfhpd__ukoxz + ' FROM (' + sql_node.
                sql_request + ') as TEMP')
    else:
        pkag__bwhrb = sql_node.sql_request
    replace_arg_nodes(txq__rey, [ir.Const(pkag__bwhrb, sql_node.loc), ir.
        Const(sql_node.connection, sql_node.loc)] + vhlg__xindo)
    zqs__zsxd = txq__rey.body[:-3]
    for sdl__hkh in range(len(sql_node.out_vars)):
        zqs__zsxd[-len(sql_node.out_vars) + sdl__hkh
            ].target = sql_node.out_vars[sdl__hkh]
    return zqs__zsxd


def escape_column_names(col_names, db_type, converted_colnames):
    if db_type in ('snowflake', 'oracle'):
        vlbhu__esz = [(oiv__pghcw.upper() if oiv__pghcw in
            converted_colnames else oiv__pghcw) for oiv__pghcw in col_names]
        lfhpd__ukoxz = ', '.join([f'"{oiv__pghcw}"' for oiv__pghcw in
            vlbhu__esz])
    elif db_type == 'mysql' or db_type == 'mysql+pymysql':
        lfhpd__ukoxz = ', '.join([f'`{oiv__pghcw}`' for oiv__pghcw in
            col_names])
    else:
        lfhpd__ukoxz = ', '.join([f'"{oiv__pghcw}"' for oiv__pghcw in
            col_names])
    return lfhpd__ukoxz


@numba.generated_jit(nopython=True, no_cpython_wrapper=True)
def _get_snowflake_sql_literal_scalar(filter_value):
    ooyl__zvvwh = types.unliteral(filter_value)
    bodo.hiframes.pd_timestamp_ext.check_tz_aware_unsupported(ooyl__zvvwh,
        'Filter pushdown')
    if ooyl__zvvwh == types.unicode_type:
        return lambda filter_value: f'$${filter_value}$$'
    elif isinstance(ooyl__zvvwh, (types.Integer, types.Float)
        ) or filter_value == types.bool_:
        return lambda filter_value: str(filter_value)
    elif ooyl__zvvwh == bodo.pd_timestamp_type:

        def impl(filter_value):
            iyuv__ohkyb = filter_value.nanosecond
            flsm__azvav = ''
            if iyuv__ohkyb < 10:
                flsm__azvav = '00'
            elif iyuv__ohkyb < 100:
                flsm__azvav = '0'
            return (
                f"timestamp '{filter_value.strftime('%Y-%m-%d %H:%M:%S.%f')}{flsm__azvav}{iyuv__ohkyb}'"
                )
        return impl
    elif ooyl__zvvwh == bodo.datetime_date_type:
        return (lambda filter_value:
            f"date '{filter_value.strftime('%Y-%m-%d')}'")
    else:
        raise BodoError(
            f'pd.read_sql(): Internal error, unsupported scalar type {ooyl__zvvwh} used in filter pushdown.'
            )


@numba.generated_jit(nopython=True, no_cpython_wrapper=True)
def _get_snowflake_sql_literal(filter_value):
    scalar_isinstance = types.Integer, types.Float
    qroyu__uyi = (bodo.datetime_date_type, bodo.pd_timestamp_type, types.
        unicode_type, types.bool_)
    ooyl__zvvwh = types.unliteral(filter_value)
    if isinstance(ooyl__zvvwh, types.List) and (isinstance(ooyl__zvvwh.
        dtype, scalar_isinstance) or ooyl__zvvwh.dtype in qroyu__uyi):

        def impl(filter_value):
            wbi__ebeoz = ', '.join([_get_snowflake_sql_literal_scalar(
                oiv__pghcw) for oiv__pghcw in filter_value])
            return f'({wbi__ebeoz})'
        return impl
    elif isinstance(ooyl__zvvwh, scalar_isinstance
        ) or ooyl__zvvwh in qroyu__uyi:
        return lambda filter_value: _get_snowflake_sql_literal_scalar(
            filter_value)
    else:
        raise BodoError(
            f'pd.read_sql(): Internal error, unsupported type {ooyl__zvvwh} used in filter pushdown.'
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
    except ImportError as ogk__vsvrr:
        hvvv__gubg = (
            "Using URI string without sqlalchemy installed. sqlalchemy can be installed by calling 'conda install -c conda-forge sqlalchemy'."
            )
        raise BodoError(hvvv__gubg)


@numba.njit
def pymysql_check():
    with numba.objmode():
        pymysql_check_()


def pymysql_check_():
    try:
        import pymysql
    except ImportError as ogk__vsvrr:
        hvvv__gubg = (
            "Using MySQL URI string requires pymsql to be installed. It can be installed by calling 'conda install -c conda-forge pymysql' or 'pip install PyMySQL'."
            )
        raise BodoError(hvvv__gubg)


@numba.njit
def cx_oracle_check():
    with numba.objmode():
        cx_oracle_check_()


def cx_oracle_check_():
    try:
        import cx_Oracle
    except ImportError as ogk__vsvrr:
        hvvv__gubg = (
            "Using Oracle URI string requires cx_oracle to be installed. It can be installed by calling 'conda install -c conda-forge cx_oracle' or 'pip install cx-Oracle'."
            )
        raise BodoError(hvvv__gubg)


@numba.njit
def psycopg2_check():
    with numba.objmode():
        psycopg2_check_()


def psycopg2_check_():
    try:
        import psycopg2
    except ImportError as ogk__vsvrr:
        hvvv__gubg = (
            "Using PostgreSQL URI string requires psycopg2 to be installed. It can be installed by calling 'conda install -c conda-forge psycopg2' or 'pip install psycopg2'."
            )
        raise BodoError(hvvv__gubg)


def req_limit(sql_request):
    import re
    jvps__fxibg = re.compile('LIMIT\\s+(\\d+)\\s*$', re.IGNORECASE)
    gjzr__toim = jvps__fxibg.search(sql_request)
    if gjzr__toim:
        return int(gjzr__toim.group(1))
    else:
        return None


def _gen_sql_reader_py(col_names, col_typs, typingctx, targetctx, db_type,
    limit, converted_colnames, parallel, is_select_query):
    wcse__uuoh = [sanitize_varname(muvbf__zeh) for muvbf__zeh in col_names]
    wijpi__nxk = ["{}='{}'".format(ibji__xes, _get_dtype_str(fwr__isa)) for
        ibji__xes, fwr__isa in zip(wcse__uuoh, col_typs)]
    if bodo.sql_access_method == 'multiple_access_nb_row_first':
        ejn__yll = 'def sql_reader_py(sql_request, conn):\n'
        if db_type == 'snowflake':
            cyg__qtue = {}
            for sdl__hkh, whqrp__dtwmc in enumerate(col_typs):
                cyg__qtue[f'col_{sdl__hkh}_type'] = whqrp__dtwmc
            ejn__yll += (
                f"  ev = bodo.utils.tracing.Event('read_snowflake', {parallel})\n"
                )

            def is_nullable(typ):
                return bodo.utils.utils.is_array_typ(typ, False
                    ) and not isinstance(typ, types.Array) and not isinstance(
                    typ, bodo.DatetimeArrayType)
            zkg__hnaz = [int(is_nullable(whqrp__dtwmc)) for whqrp__dtwmc in
                col_typs]
            ejn__yll += f"""  out_table = snowflake_read(unicode_to_utf8(sql_request), unicode_to_utf8(conn), {parallel}, {len(col_names)}, np.array({zkg__hnaz}, dtype=np.int32).ctypes)
"""
            ejn__yll += '  check_and_propagate_cpp_exception()\n'
            for sdl__hkh, zmby__akw in enumerate(wcse__uuoh):
                ejn__yll += f"""  {zmby__akw} = info_to_array(info_from_table(out_table, {sdl__hkh}), col_{sdl__hkh}_type)
"""
            ejn__yll += '  delete_table(out_table)\n'
            ejn__yll += f'  ev.finalize()\n'
        else:
            ejn__yll += '  sqlalchemy_check()\n'
            if db_type == 'mysql' or db_type == 'mysql+pymysql':
                ejn__yll += '  pymysql_check()\n'
            elif db_type == 'oracle':
                ejn__yll += '  cx_oracle_check()\n'
            elif db_type == 'postgresql' or db_type == 'postgresql+psycopg2':
                ejn__yll += '  psycopg2_check()\n'
            if parallel and is_select_query:
                ejn__yll += '  rank = bodo.libs.distributed_api.get_rank()\n'
                if limit is not None:
                    ejn__yll += f'  nb_row = {limit}\n'
                else:
                    ejn__yll += '  with objmode(nb_row="int64"):\n'
                    ejn__yll += f'     if rank == {MPI_ROOT}:\n'
                    ejn__yll += """         sql_cons = 'select count(*) from (' + sql_request + ') x'
"""
                    ejn__yll += (
                        '         frame = pd.read_sql(sql_cons, conn)\n')
                    ejn__yll += '         nb_row = frame.iat[0,0]\n'
                    ejn__yll += '     else:\n'
                    ejn__yll += '         nb_row = 0\n'
                    ejn__yll += '  nb_row = bcast_scalar(nb_row)\n'
                ejn__yll += '  with objmode({}):\n'.format(', '.join(
                    wijpi__nxk))
                ejn__yll += """    offset, limit = bodo.libs.distributed_api.get_start_count(nb_row)
"""
                lfhpd__ukoxz = escape_column_names(col_names, db_type,
                    converted_colnames)
                if db_type == 'oracle':
                    ejn__yll += f"""    sql_cons = 'select {lfhpd__ukoxz} from (' + sql_request + ') OFFSET ' + str(offset) + ' ROWS FETCH NEXT ' + str(limit) + ' ROWS ONLY'
"""
                else:
                    ejn__yll += f"""    sql_cons = 'select {lfhpd__ukoxz} from (' + sql_request + ') x LIMIT ' + str(limit) + ' OFFSET ' + str(offset)
"""
                ejn__yll += '    df_ret = pd.read_sql(sql_cons, conn)\n'
            else:
                ejn__yll += '  with objmode({}):\n'.format(', '.join(
                    wijpi__nxk))
                ejn__yll += '    df_ret = pd.read_sql(sql_request, conn)\n'
            for ibji__xes, shic__eizi in zip(wcse__uuoh, col_names):
                ejn__yll += "    {} = df_ret['{}'].values\n".format(ibji__xes,
                    shic__eizi)
        ejn__yll += '  return ({},)\n'.format(', '.join(ptw__hucc for
            ptw__hucc in wcse__uuoh))
    uvxl__hnwl = {'bodo': bodo}
    if db_type == 'snowflake':
        uvxl__hnwl.update(cyg__qtue)
        uvxl__hnwl.update({'np': np, 'unicode_to_utf8': unicode_to_utf8,
            'check_and_propagate_cpp_exception':
            check_and_propagate_cpp_exception, 'snowflake_read':
            _snowflake_read, 'info_to_array': info_to_array,
            'info_from_table': info_from_table, 'delete_table': delete_table})
    else:
        uvxl__hnwl.update({'sqlalchemy_check': sqlalchemy_check, 'pd': pd,
            'objmode': objmode, 'bcast_scalar': bcast_scalar,
            'pymysql_check': pymysql_check, 'cx_oracle_check':
            cx_oracle_check, 'psycopg2_check': psycopg2_check})
    ljwsr__dxkdx = {}
    exec(ejn__yll, uvxl__hnwl, ljwsr__dxkdx)
    ttk__rfa = ljwsr__dxkdx['sql_reader_py']
    hcflw__mzn = numba.njit(ttk__rfa)
    compiled_funcs.append(hcflw__mzn)
    return hcflw__mzn


_snowflake_read = types.ExternalFunction('snowflake_read', table_type(types
    .voidptr, types.voidptr, types.boolean, types.int64, types.voidptr))
import llvmlite.binding as ll
from bodo.io import arrow_cpp
ll.add_symbol('snowflake_read', arrow_cpp.snowflake_read)
