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
    yuwq__wjhn = []
    mvhf__hvxyr = []
    seh__moae = []
    for bmtdu__psm, gmbr__yrdi in enumerate(sql_node.out_vars):
        if gmbr__yrdi.name in lives:
            yuwq__wjhn.append(sql_node.df_colnames[bmtdu__psm])
            mvhf__hvxyr.append(sql_node.out_vars[bmtdu__psm])
            seh__moae.append(sql_node.out_types[bmtdu__psm])
    sql_node.df_colnames = yuwq__wjhn
    sql_node.out_vars = mvhf__hvxyr
    sql_node.out_types = seh__moae
    if len(sql_node.out_vars) == 0:
        return None
    return sql_node


def sql_distributed_run(sql_node, array_dists, typemap, calltypes,
    typingctx, targetctx):
    if bodo.user_logging.get_verbose_level() >= 1:
        uait__bmb = (
            'Finish column pruning on read_sql node:\n%s\nColumns loaded %s\n')
        hmt__dvus = sql_node.loc.strformat()
        gpub__ttae = sql_node.df_colnames
        bodo.user_logging.log_message('Column Pruning', uait__bmb,
            hmt__dvus, gpub__ttae)
        xasjm__xwge = [jyhw__cxrk for bmtdu__psm, jyhw__cxrk in enumerate(
            sql_node.df_colnames) if isinstance(sql_node.out_types[
            bmtdu__psm], bodo.libs.dict_arr_ext.DictionaryArrayType)]
        if xasjm__xwge:
            kpkbv__khflw = """Finished optimized encoding on read_sql node:
%s
Columns %s using dictionary encoding to reduce memory usage.
"""
            bodo.user_logging.log_message('Dictionary Encoding',
                kpkbv__khflw, hmt__dvus, xasjm__xwge)
    parallel = False
    if array_dists is not None:
        parallel = True
        for viwok__amgzc in sql_node.out_vars:
            if array_dists[viwok__amgzc.name
                ] != distributed_pass.Distribution.OneD and array_dists[
                viwok__amgzc.name] != distributed_pass.Distribution.OneD_Var:
                parallel = False
    if sql_node.unsupported_columns:
        zbzg__srf = set(sql_node.unsupported_columns)
        cjpsk__ltq = set()
        upiz__vztgu = 0
        for iaoxa__ixm in sql_node.df_colnames:
            while sql_node.original_df_colnames[upiz__vztgu] != iaoxa__ixm:
                upiz__vztgu += 1
            if upiz__vztgu in zbzg__srf:
                cjpsk__ltq.add(upiz__vztgu)
            upiz__vztgu += 1
        if cjpsk__ltq:
            ipodm__nwp = sorted(cjpsk__ltq)
            uonxq__cnrjy = [
                f'pandas.read_sql(): 1 or more columns found with Arrow types that are not supported in Bodo and could not be eliminated. '
                 +
                'Please manually remove these columns from your sql query by specifying the columns you need in your SELECT statement. If these '
                 +
                'columns are needed, you will need to modify your dataset to use a supported type.'
                , 'Unsupported Columns:']
            ghpf__dvfse = 0
            for teh__tmci in ipodm__nwp:
                while sql_node.unsupported_columns[ghpf__dvfse] != teh__tmci:
                    ghpf__dvfse += 1
                uonxq__cnrjy.append(
                    f"Column '{sql_node.original_df_colnames[teh__tmci]}' with unsupported arrow type {sql_node.unsupported_arrow_types[ghpf__dvfse]}"
                    )
                ghpf__dvfse += 1
            tadz__hknxz = '\n'.join(uonxq__cnrjy)
            raise BodoError(tadz__hknxz, loc=sql_node.loc)
    mkxnq__fneih = len(sql_node.out_vars)
    zpjgu__kmddg = ', '.join('arr' + str(bmtdu__psm) for bmtdu__psm in
        range(mkxnq__fneih))
    ero__bvsj, yiu__yonu = bodo.ir.connector.generate_filter_map(sql_node.
        filters)
    ejm__bychp = ', '.join(ero__bvsj.values())
    dsvqy__jqt = f'def sql_impl(sql_request, conn, {ejm__bychp}):\n'
    if sql_node.filters:
        mspr__pao = []
        for sxp__yrwxu in sql_node.filters:
            gvk__gqie = [' '.join(['(', dobo__timps[0], dobo__timps[1], '{' +
                ero__bvsj[dobo__timps[2].name] + '}' if isinstance(
                dobo__timps[2], ir.Var) else dobo__timps[2], ')']) for
                dobo__timps in sxp__yrwxu]
            mspr__pao.append(' ( ' + ' AND '.join(gvk__gqie) + ' ) ')
        vbdl__udz = ' WHERE ' + ' OR '.join(mspr__pao)
        for bmtdu__psm, obuyg__gpm in enumerate(ero__bvsj.values()):
            dsvqy__jqt += f'    {obuyg__gpm} = get_sql_literal({obuyg__gpm})\n'
        dsvqy__jqt += f'    sql_request = f"{{sql_request}} {vbdl__udz}"\n'
    dsvqy__jqt += '    ({},) = _sql_reader_py(sql_request, conn)\n'.format(
        zpjgu__kmddg)
    dqu__gepte = {}
    exec(dsvqy__jqt, {}, dqu__gepte)
    hmcl__wmc = dqu__gepte['sql_impl']
    xllc__dzw = _gen_sql_reader_py(sql_node.df_colnames, sql_node.out_types,
        typingctx, targetctx, sql_node.db_type, sql_node.limit, sql_node.
        converted_colnames, parallel, sql_node.is_select_query)
    kwhm__qdj = compile_to_numba_ir(hmcl__wmc, {'_sql_reader_py': xllc__dzw,
        'bcast_scalar': bcast_scalar, 'bcast': bcast, 'get_sql_literal':
        _get_snowflake_sql_literal}, typingctx=typingctx, targetctx=
        targetctx, arg_typs=(string_type, string_type) + tuple(typemap[
        viwok__amgzc.name] for viwok__amgzc in yiu__yonu), typemap=typemap,
        calltypes=calltypes).blocks.popitem()[1]
    if sql_node.is_select_query:
        oiaa__wtrt = escape_column_names(sql_node.df_colnames, sql_node.
            db_type, sql_node.converted_colnames)
        if sql_node.db_type == 'oracle':
            lcbx__itsu = ('SELECT ' + oiaa__wtrt + ' FROM (' + sql_node.
                sql_request + ') TEMP')
        else:
            lcbx__itsu = ('SELECT ' + oiaa__wtrt + ' FROM (' + sql_node.
                sql_request + ') as TEMP')
    else:
        lcbx__itsu = sql_node.sql_request
    replace_arg_nodes(kwhm__qdj, [ir.Const(lcbx__itsu, sql_node.loc), ir.
        Const(sql_node.connection, sql_node.loc)] + yiu__yonu)
    mwlwa__knz = kwhm__qdj.body[:-3]
    for bmtdu__psm in range(len(sql_node.out_vars)):
        mwlwa__knz[-len(sql_node.out_vars) + bmtdu__psm
            ].target = sql_node.out_vars[bmtdu__psm]
    return mwlwa__knz


def escape_column_names(col_names, db_type, converted_colnames):
    if db_type in ('snowflake', 'oracle'):
        wubza__erpj = [(ozx__xmea.upper() if ozx__xmea in
            converted_colnames else ozx__xmea) for ozx__xmea in col_names]
        oiaa__wtrt = ', '.join([f'"{ozx__xmea}"' for ozx__xmea in wubza__erpj])
    elif db_type == 'mysql' or db_type == 'mysql+pymysql':
        oiaa__wtrt = ', '.join([f'`{ozx__xmea}`' for ozx__xmea in col_names])
    else:
        oiaa__wtrt = ', '.join([f'"{ozx__xmea}"' for ozx__xmea in col_names])
    return oiaa__wtrt


@numba.generated_jit(nopython=True, no_cpython_wrapper=True)
def _get_snowflake_sql_literal_scalar(filter_value):
    infs__hrhx = types.unliteral(filter_value)
    if infs__hrhx == types.unicode_type:
        return lambda filter_value: f'$${filter_value}$$'
    elif isinstance(infs__hrhx, (types.Integer, types.Float)
        ) or filter_value == types.bool_:
        return lambda filter_value: str(filter_value)
    elif infs__hrhx == bodo.pd_timestamp_type:

        def impl(filter_value):
            zhup__zvjn = filter_value.nanosecond
            wett__efqz = ''
            if zhup__zvjn < 10:
                wett__efqz = '00'
            elif zhup__zvjn < 100:
                wett__efqz = '0'
            return (
                f"timestamp '{filter_value.strftime('%Y-%m-%d %H:%M:%S.%f')}{wett__efqz}{zhup__zvjn}'"
                )
        return impl
    elif infs__hrhx == bodo.datetime_date_type:
        return (lambda filter_value:
            f"date '{filter_value.strftime('%Y-%m-%d')}'")
    else:
        raise BodoError(
            f'pd.read_sql(): Internal error, unsupported scalar type {infs__hrhx} used in filter pushdown.'
            )


@numba.generated_jit(nopython=True, no_cpython_wrapper=True)
def _get_snowflake_sql_literal(filter_value):
    scalar_isinstance = types.Integer, types.Float
    sju__supfm = (bodo.datetime_date_type, bodo.pd_timestamp_type, types.
        unicode_type, types.bool_)
    infs__hrhx = types.unliteral(filter_value)
    if isinstance(infs__hrhx, types.List) and (isinstance(infs__hrhx.dtype,
        scalar_isinstance) or infs__hrhx.dtype in sju__supfm):

        def impl(filter_value):
            qnv__njzsj = ', '.join([_get_snowflake_sql_literal_scalar(
                ozx__xmea) for ozx__xmea in filter_value])
            return f'({qnv__njzsj})'
        return impl
    elif isinstance(infs__hrhx, scalar_isinstance) or infs__hrhx in sju__supfm:
        return lambda filter_value: _get_snowflake_sql_literal_scalar(
            filter_value)
    else:
        raise BodoError(
            f'pd.read_sql(): Internal error, unsupported type {infs__hrhx} used in filter pushdown.'
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
    except ImportError as vxqr__fnd:
        hei__mgrez = (
            "Using URI string without sqlalchemy installed. sqlalchemy can be installed by calling 'conda install -c conda-forge sqlalchemy'."
            )
        raise BodoError(hei__mgrez)


@numba.njit
def pymysql_check():
    with numba.objmode():
        pymysql_check_()


def pymysql_check_():
    try:
        import pymysql
    except ImportError as vxqr__fnd:
        hei__mgrez = (
            "Using MySQL URI string requires pymsql to be installed. It can be installed by calling 'conda install -c conda-forge pymysql' or 'pip install PyMySQL'."
            )
        raise BodoError(hei__mgrez)


@numba.njit
def cx_oracle_check():
    with numba.objmode():
        cx_oracle_check_()


def cx_oracle_check_():
    try:
        import cx_Oracle
    except ImportError as vxqr__fnd:
        hei__mgrez = (
            "Using Oracle URI string requires cx_oracle to be installed. It can be installed by calling 'conda install -c conda-forge cx_oracle' or 'pip install cx-Oracle'."
            )
        raise BodoError(hei__mgrez)


@numba.njit
def psycopg2_check():
    with numba.objmode():
        psycopg2_check_()


def psycopg2_check_():
    try:
        import psycopg2
    except ImportError as vxqr__fnd:
        hei__mgrez = (
            "Using PostgreSQL URI string requires psycopg2 to be installed. It can be installed by calling 'conda install -c conda-forge psycopg2' or 'pip install psycopg2'."
            )
        raise BodoError(hei__mgrez)


def req_limit(sql_request):
    import re
    wcxzy__sur = re.compile('LIMIT\\s+(\\d+)\\s*$', re.IGNORECASE)
    fpa__nkgpb = wcxzy__sur.search(sql_request)
    if fpa__nkgpb:
        return int(fpa__nkgpb.group(1))
    else:
        return None


def _gen_sql_reader_py(col_names, col_typs, typingctx, targetctx, db_type,
    limit, converted_colnames, parallel, is_select_query):
    mmj__ttehl = [sanitize_varname(jyhw__cxrk) for jyhw__cxrk in col_names]
    hyd__yhjhk = ["{}='{}'".format(tanqd__vogtm, _get_dtype_str(frvm__fjc)) for
        tanqd__vogtm, frvm__fjc in zip(mmj__ttehl, col_typs)]
    if bodo.sql_access_method == 'multiple_access_nb_row_first':
        dsvqy__jqt = 'def sql_reader_py(sql_request, conn):\n'
        if db_type == 'snowflake':
            hywyu__qpvfj = {}
            for bmtdu__psm, koby__nydye in enumerate(col_typs):
                hywyu__qpvfj[f'col_{bmtdu__psm}_type'] = koby__nydye
            dsvqy__jqt += (
                f"  ev = bodo.utils.tracing.Event('read_snowflake', {parallel})\n"
                )

            def is_nullable(typ):
                return bodo.utils.utils.is_array_typ(typ, False
                    ) and not isinstance(typ, types.Array)
            saajr__eta = [int(is_nullable(koby__nydye)) for koby__nydye in
                col_typs]
            dsvqy__jqt += f"""  out_table = snowflake_read(unicode_to_utf8(sql_request), unicode_to_utf8(conn), {parallel}, {len(col_names)}, np.array({saajr__eta}, dtype=np.int32).ctypes)
"""
            dsvqy__jqt += '  check_and_propagate_cpp_exception()\n'
            for bmtdu__psm, auhv__kcol in enumerate(mmj__ttehl):
                dsvqy__jqt += f"""  {auhv__kcol} = info_to_array(info_from_table(out_table, {bmtdu__psm}), col_{bmtdu__psm}_type)
"""
            dsvqy__jqt += '  delete_table(out_table)\n'
            dsvqy__jqt += f'  ev.finalize()\n'
        else:
            dsvqy__jqt += '  sqlalchemy_check()\n'
            if db_type == 'mysql' or db_type == 'mysql+pymysql':
                dsvqy__jqt += '  pymysql_check()\n'
            elif db_type == 'oracle':
                dsvqy__jqt += '  cx_oracle_check()\n'
            elif db_type == 'postgresql' or db_type == 'postgresql+psycopg2':
                dsvqy__jqt += '  psycopg2_check()\n'
            if parallel and is_select_query:
                dsvqy__jqt += '  rank = bodo.libs.distributed_api.get_rank()\n'
                if limit is not None:
                    dsvqy__jqt += f'  nb_row = {limit}\n'
                else:
                    dsvqy__jqt += '  with objmode(nb_row="int64"):\n'
                    dsvqy__jqt += f'     if rank == {MPI_ROOT}:\n'
                    dsvqy__jqt += """         sql_cons = 'select count(*) from (' + sql_request + ') x'
"""
                    dsvqy__jqt += (
                        '         frame = pd.read_sql(sql_cons, conn)\n')
                    dsvqy__jqt += '         nb_row = frame.iat[0,0]\n'
                    dsvqy__jqt += '     else:\n'
                    dsvqy__jqt += '         nb_row = 0\n'
                    dsvqy__jqt += '  nb_row = bcast_scalar(nb_row)\n'
                dsvqy__jqt += '  with objmode({}):\n'.format(', '.join(
                    hyd__yhjhk))
                dsvqy__jqt += """    offset, limit = bodo.libs.distributed_api.get_start_count(nb_row)
"""
                oiaa__wtrt = escape_column_names(col_names, db_type,
                    converted_colnames)
                if db_type == 'oracle':
                    dsvqy__jqt += f"""    sql_cons = 'select {oiaa__wtrt} from (' + sql_request + ') OFFSET ' + str(offset) + ' ROWS FETCH NEXT ' + str(limit) + ' ROWS ONLY'
"""
                else:
                    dsvqy__jqt += f"""    sql_cons = 'select {oiaa__wtrt} from (' + sql_request + ') x LIMIT ' + str(limit) + ' OFFSET ' + str(offset)
"""
                dsvqy__jqt += '    df_ret = pd.read_sql(sql_cons, conn)\n'
            else:
                dsvqy__jqt += '  with objmode({}):\n'.format(', '.join(
                    hyd__yhjhk))
                dsvqy__jqt += '    df_ret = pd.read_sql(sql_request, conn)\n'
            for tanqd__vogtm, eviy__oztb in zip(mmj__ttehl, col_names):
                dsvqy__jqt += "    {} = df_ret['{}'].values\n".format(
                    tanqd__vogtm, eviy__oztb)
        dsvqy__jqt += '  return ({},)\n'.format(', '.join(jmesh__veqp for
            jmesh__veqp in mmj__ttehl))
    bhi__hgid = {'bodo': bodo}
    if db_type == 'snowflake':
        bhi__hgid.update(hywyu__qpvfj)
        bhi__hgid.update({'np': np, 'unicode_to_utf8': unicode_to_utf8,
            'check_and_propagate_cpp_exception':
            check_and_propagate_cpp_exception, 'snowflake_read':
            _snowflake_read, 'info_to_array': info_to_array,
            'info_from_table': info_from_table, 'delete_table': delete_table})
    else:
        bhi__hgid.update({'sqlalchemy_check': sqlalchemy_check, 'pd': pd,
            'objmode': objmode, 'bcast_scalar': bcast_scalar,
            'pymysql_check': pymysql_check, 'cx_oracle_check':
            cx_oracle_check, 'psycopg2_check': psycopg2_check})
    dqu__gepte = {}
    exec(dsvqy__jqt, bhi__hgid, dqu__gepte)
    xllc__dzw = dqu__gepte['sql_reader_py']
    acgod__xxr = numba.njit(xllc__dzw)
    compiled_funcs.append(acgod__xxr)
    return acgod__xxr


_snowflake_read = types.ExternalFunction('snowflake_read', table_type(types
    .voidptr, types.voidptr, types.boolean, types.int64, types.voidptr))
import llvmlite.binding as ll
from bodo.io import arrow_cpp
ll.add_symbol('snowflake_read', arrow_cpp.snowflake_read)
