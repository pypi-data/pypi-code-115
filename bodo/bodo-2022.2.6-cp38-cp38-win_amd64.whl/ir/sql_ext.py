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
    kulcw__givtm = []
    ity__bnb = []
    qkrn__cvh = []
    for pccgp__jyf, nue__tqyzi in enumerate(sql_node.out_vars):
        if nue__tqyzi.name in lives:
            kulcw__givtm.append(sql_node.df_colnames[pccgp__jyf])
            ity__bnb.append(sql_node.out_vars[pccgp__jyf])
            qkrn__cvh.append(sql_node.out_types[pccgp__jyf])
    sql_node.df_colnames = kulcw__givtm
    sql_node.out_vars = ity__bnb
    sql_node.out_types = qkrn__cvh
    if len(sql_node.out_vars) == 0:
        return None
    return sql_node


def sql_distributed_run(sql_node, array_dists, typemap, calltypes,
    typingctx, targetctx):
    if bodo.user_logging.get_verbose_level() >= 1:
        caltz__tngmp = (
            'Finish column pruning on read_sql node:\n%s\nColumns loaded %s\n')
        rcucs__dffwb = sql_node.loc.strformat()
        yjiim__acczl = sql_node.df_colnames
        bodo.user_logging.log_message('Column Pruning', caltz__tngmp,
            rcucs__dffwb, yjiim__acczl)
        cly__tepr = [lsrwp__dbo for pccgp__jyf, lsrwp__dbo in enumerate(
            sql_node.df_colnames) if isinstance(sql_node.out_types[
            pccgp__jyf], bodo.libs.dict_arr_ext.DictionaryArrayType)]
        if cly__tepr:
            zyp__binev = """Finished optimized encoding on read_sql node:
%s
Columns %s using dictionary encoding to reduce memory usage.
"""
            bodo.user_logging.log_message('Dictionary Encoding', zyp__binev,
                rcucs__dffwb, cly__tepr)
    parallel = False
    if array_dists is not None:
        parallel = True
        for aruc__bwqot in sql_node.out_vars:
            if array_dists[aruc__bwqot.name
                ] != distributed_pass.Distribution.OneD and array_dists[
                aruc__bwqot.name] != distributed_pass.Distribution.OneD_Var:
                parallel = False
    if sql_node.unsupported_columns:
        jfa__uvp = set(sql_node.unsupported_columns)
        lxlzp__choh = set()
        eqm__dveix = 0
        for vmoiz__hfvws in sql_node.df_colnames:
            while sql_node.original_df_colnames[eqm__dveix] != vmoiz__hfvws:
                eqm__dveix += 1
            if eqm__dveix in jfa__uvp:
                lxlzp__choh.add(eqm__dveix)
            eqm__dveix += 1
        if lxlzp__choh:
            ikyz__ykn = sorted(lxlzp__choh)
            mojk__rcteo = [
                f'pandas.read_sql(): 1 or more columns found with Arrow types that are not supported in Bodo and could not be eliminated. '
                 +
                'Please manually remove these columns from your sql query by specifying the columns you need in your SELECT statement. If these '
                 +
                'columns are needed, you will need to modify your dataset to use a supported type.'
                , 'Unsupported Columns:']
            mwzmn__hpdiz = 0
            for mom__bvv in ikyz__ykn:
                while sql_node.unsupported_columns[mwzmn__hpdiz] != mom__bvv:
                    mwzmn__hpdiz += 1
                mojk__rcteo.append(
                    f"Column '{sql_node.original_df_colnames[mom__bvv]}' with unsupported arrow type {sql_node.unsupported_arrow_types[mwzmn__hpdiz]}"
                    )
                mwzmn__hpdiz += 1
            yjdoy__yqoqp = '\n'.join(mojk__rcteo)
            raise BodoError(yjdoy__yqoqp, loc=sql_node.loc)
    dzv__xxgvh = len(sql_node.out_vars)
    jrb__uwp = ', '.join('arr' + str(pccgp__jyf) for pccgp__jyf in range(
        dzv__xxgvh))
    iewdi__rny, snn__fholl = bodo.ir.connector.generate_filter_map(sql_node
        .filters)
    nkmq__izsk = ', '.join(iewdi__rny.values())
    bipwi__otbkg = f'def sql_impl(sql_request, conn, {nkmq__izsk}):\n'
    if sql_node.filters:
        ajhrx__aebyp = []
        for ixpm__skdx in sql_node.filters:
            mnsuo__qni = [' '.join(['(', rlx__fjggp[0], rlx__fjggp[1], '{' +
                iewdi__rny[rlx__fjggp[2].name] + '}' if isinstance(
                rlx__fjggp[2], ir.Var) else rlx__fjggp[2], ')']) for
                rlx__fjggp in ixpm__skdx]
            ajhrx__aebyp.append(' ( ' + ' AND '.join(mnsuo__qni) + ' ) ')
        naebw__csl = ' WHERE ' + ' OR '.join(ajhrx__aebyp)
        for pccgp__jyf, xfv__divzt in enumerate(iewdi__rny.values()):
            bipwi__otbkg += (
                f'    {xfv__divzt} = get_sql_literal({xfv__divzt})\n')
        bipwi__otbkg += f'    sql_request = f"{{sql_request}} {naebw__csl}"\n'
    bipwi__otbkg += '    ({},) = _sql_reader_py(sql_request, conn)\n'.format(
        jrb__uwp)
    dfho__ifb = {}
    exec(bipwi__otbkg, {}, dfho__ifb)
    wrnjn__bujlr = dfho__ifb['sql_impl']
    yybya__uwj = _gen_sql_reader_py(sql_node.df_colnames, sql_node.
        out_types, typingctx, targetctx, sql_node.db_type, sql_node.limit,
        sql_node.converted_colnames, parallel, sql_node.is_select_query)
    tpuc__lgdu = compile_to_numba_ir(wrnjn__bujlr, {'_sql_reader_py':
        yybya__uwj, 'bcast_scalar': bcast_scalar, 'bcast': bcast,
        'get_sql_literal': _get_snowflake_sql_literal}, typingctx=typingctx,
        targetctx=targetctx, arg_typs=(string_type, string_type) + tuple(
        typemap[aruc__bwqot.name] for aruc__bwqot in snn__fholl), typemap=
        typemap, calltypes=calltypes).blocks.popitem()[1]
    if sql_node.is_select_query:
        thkx__gwd = escape_column_names(sql_node.df_colnames, sql_node.
            db_type, sql_node.converted_colnames)
        if sql_node.db_type == 'oracle':
            szqr__tozq = ('SELECT ' + thkx__gwd + ' FROM (' + sql_node.
                sql_request + ') TEMP')
        else:
            szqr__tozq = ('SELECT ' + thkx__gwd + ' FROM (' + sql_node.
                sql_request + ') as TEMP')
    else:
        szqr__tozq = sql_node.sql_request
    replace_arg_nodes(tpuc__lgdu, [ir.Const(szqr__tozq, sql_node.loc), ir.
        Const(sql_node.connection, sql_node.loc)] + snn__fholl)
    vxoxk__zqhl = tpuc__lgdu.body[:-3]
    for pccgp__jyf in range(len(sql_node.out_vars)):
        vxoxk__zqhl[-len(sql_node.out_vars) + pccgp__jyf
            ].target = sql_node.out_vars[pccgp__jyf]
    return vxoxk__zqhl


def escape_column_names(col_names, db_type, converted_colnames):
    if db_type in ('snowflake', 'oracle'):
        wajv__bzzro = [(aiept__wuyz.upper() if aiept__wuyz in
            converted_colnames else aiept__wuyz) for aiept__wuyz in col_names]
        thkx__gwd = ', '.join([f'"{aiept__wuyz}"' for aiept__wuyz in
            wajv__bzzro])
    elif db_type == 'mysql' or db_type == 'mysql+pymysql':
        thkx__gwd = ', '.join([f'`{aiept__wuyz}`' for aiept__wuyz in col_names]
            )
    else:
        thkx__gwd = ', '.join([f'"{aiept__wuyz}"' for aiept__wuyz in col_names]
            )
    return thkx__gwd


@numba.generated_jit(nopython=True, no_cpython_wrapper=True)
def _get_snowflake_sql_literal_scalar(filter_value):
    ualxu__nezlt = types.unliteral(filter_value)
    if ualxu__nezlt == types.unicode_type:
        return lambda filter_value: f'$${filter_value}$$'
    elif isinstance(ualxu__nezlt, (types.Integer, types.Float)
        ) or filter_value == types.bool_:
        return lambda filter_value: str(filter_value)
    elif ualxu__nezlt == bodo.pd_timestamp_type:

        def impl(filter_value):
            fou__gtgx = filter_value.nanosecond
            qwkig__fenrm = ''
            if fou__gtgx < 10:
                qwkig__fenrm = '00'
            elif fou__gtgx < 100:
                qwkig__fenrm = '0'
            return (
                f"timestamp '{filter_value.strftime('%Y-%m-%d %H:%M:%S.%f')}{qwkig__fenrm}{fou__gtgx}'"
                )
        return impl
    elif ualxu__nezlt == bodo.datetime_date_type:
        return (lambda filter_value:
            f"date '{filter_value.strftime('%Y-%m-%d')}'")
    else:
        raise BodoError(
            f'pd.read_sql(): Internal error, unsupported scalar type {ualxu__nezlt} used in filter pushdown.'
            )


@numba.generated_jit(nopython=True, no_cpython_wrapper=True)
def _get_snowflake_sql_literal(filter_value):
    scalar_isinstance = types.Integer, types.Float
    zdewk__fjs = (bodo.datetime_date_type, bodo.pd_timestamp_type, types.
        unicode_type, types.bool_)
    ualxu__nezlt = types.unliteral(filter_value)
    if isinstance(ualxu__nezlt, types.List) and (isinstance(ualxu__nezlt.
        dtype, scalar_isinstance) or ualxu__nezlt.dtype in zdewk__fjs):

        def impl(filter_value):
            bpgki__ahj = ', '.join([_get_snowflake_sql_literal_scalar(
                aiept__wuyz) for aiept__wuyz in filter_value])
            return f'({bpgki__ahj})'
        return impl
    elif isinstance(ualxu__nezlt, scalar_isinstance
        ) or ualxu__nezlt in zdewk__fjs:
        return lambda filter_value: _get_snowflake_sql_literal_scalar(
            filter_value)
    else:
        raise BodoError(
            f'pd.read_sql(): Internal error, unsupported type {ualxu__nezlt} used in filter pushdown.'
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
    except ImportError as cgy__drygp:
        jek__xxk = (
            "Using URI string without sqlalchemy installed. sqlalchemy can be installed by calling 'conda install -c conda-forge sqlalchemy'."
            )
        raise BodoError(jek__xxk)


@numba.njit
def pymysql_check():
    with numba.objmode():
        pymysql_check_()


def pymysql_check_():
    try:
        import pymysql
    except ImportError as cgy__drygp:
        jek__xxk = (
            "Using MySQL URI string requires pymsql to be installed. It can be installed by calling 'conda install -c conda-forge pymysql' or 'pip install PyMySQL'."
            )
        raise BodoError(jek__xxk)


@numba.njit
def cx_oracle_check():
    with numba.objmode():
        cx_oracle_check_()


def cx_oracle_check_():
    try:
        import cx_Oracle
    except ImportError as cgy__drygp:
        jek__xxk = (
            "Using Oracle URI string requires cx_oracle to be installed. It can be installed by calling 'conda install -c conda-forge cx_oracle' or 'pip install cx-Oracle'."
            )
        raise BodoError(jek__xxk)


@numba.njit
def psycopg2_check():
    with numba.objmode():
        psycopg2_check_()


def psycopg2_check_():
    try:
        import psycopg2
    except ImportError as cgy__drygp:
        jek__xxk = (
            "Using PostgreSQL URI string requires psycopg2 to be installed. It can be installed by calling 'conda install -c conda-forge psycopg2' or 'pip install psycopg2'."
            )
        raise BodoError(jek__xxk)


def req_limit(sql_request):
    import re
    emwb__ikdr = re.compile('LIMIT\\s+(\\d+)\\s*$', re.IGNORECASE)
    ofvpw__mkyzu = emwb__ikdr.search(sql_request)
    if ofvpw__mkyzu:
        return int(ofvpw__mkyzu.group(1))
    else:
        return None


def _gen_sql_reader_py(col_names, col_typs, typingctx, targetctx, db_type,
    limit, converted_colnames, parallel, is_select_query):
    qvqqb__ibiug = [sanitize_varname(lsrwp__dbo) for lsrwp__dbo in col_names]
    ypfix__licuy = ["{}='{}'".format(asuuu__tqgi, _get_dtype_str(hdr__glu)) for
        asuuu__tqgi, hdr__glu in zip(qvqqb__ibiug, col_typs)]
    if bodo.sql_access_method == 'multiple_access_nb_row_first':
        bipwi__otbkg = 'def sql_reader_py(sql_request, conn):\n'
        if db_type == 'snowflake':
            opjg__hmq = {}
            for pccgp__jyf, qgkz__epzor in enumerate(col_typs):
                opjg__hmq[f'col_{pccgp__jyf}_type'] = qgkz__epzor
            bipwi__otbkg += (
                f"  ev = bodo.utils.tracing.Event('read_snowflake', {parallel})\n"
                )

            def is_nullable(typ):
                return bodo.utils.utils.is_array_typ(typ, False
                    ) and not isinstance(typ, types.Array)
            rjm__lbpvd = [int(is_nullable(qgkz__epzor)) for qgkz__epzor in
                col_typs]
            bipwi__otbkg += f"""  out_table = snowflake_read(unicode_to_utf8(sql_request), unicode_to_utf8(conn), {parallel}, {len(col_names)}, np.array({rjm__lbpvd}, dtype=np.int32).ctypes)
"""
            bipwi__otbkg += '  check_and_propagate_cpp_exception()\n'
            for pccgp__jyf, icqqt__tlf in enumerate(qvqqb__ibiug):
                bipwi__otbkg += f"""  {icqqt__tlf} = info_to_array(info_from_table(out_table, {pccgp__jyf}), col_{pccgp__jyf}_type)
"""
            bipwi__otbkg += '  delete_table(out_table)\n'
            bipwi__otbkg += f'  ev.finalize()\n'
        else:
            bipwi__otbkg += '  sqlalchemy_check()\n'
            if db_type == 'mysql' or db_type == 'mysql+pymysql':
                bipwi__otbkg += '  pymysql_check()\n'
            elif db_type == 'oracle':
                bipwi__otbkg += '  cx_oracle_check()\n'
            elif db_type == 'postgresql' or db_type == 'postgresql+psycopg2':
                bipwi__otbkg += '  psycopg2_check()\n'
            if parallel and is_select_query:
                bipwi__otbkg += (
                    '  rank = bodo.libs.distributed_api.get_rank()\n')
                if limit is not None:
                    bipwi__otbkg += f'  nb_row = {limit}\n'
                else:
                    bipwi__otbkg += '  with objmode(nb_row="int64"):\n'
                    bipwi__otbkg += f'     if rank == {MPI_ROOT}:\n'
                    bipwi__otbkg += """         sql_cons = 'select count(*) from (' + sql_request + ') x'
"""
                    bipwi__otbkg += (
                        '         frame = pd.read_sql(sql_cons, conn)\n')
                    bipwi__otbkg += '         nb_row = frame.iat[0,0]\n'
                    bipwi__otbkg += '     else:\n'
                    bipwi__otbkg += '         nb_row = 0\n'
                    bipwi__otbkg += '  nb_row = bcast_scalar(nb_row)\n'
                bipwi__otbkg += '  with objmode({}):\n'.format(', '.join(
                    ypfix__licuy))
                bipwi__otbkg += """    offset, limit = bodo.libs.distributed_api.get_start_count(nb_row)
"""
                thkx__gwd = escape_column_names(col_names, db_type,
                    converted_colnames)
                if db_type == 'oracle':
                    bipwi__otbkg += f"""    sql_cons = 'select {thkx__gwd} from (' + sql_request + ') OFFSET ' + str(offset) + ' ROWS FETCH NEXT ' + str(limit) + ' ROWS ONLY'
"""
                else:
                    bipwi__otbkg += f"""    sql_cons = 'select {thkx__gwd} from (' + sql_request + ') x LIMIT ' + str(limit) + ' OFFSET ' + str(offset)
"""
                bipwi__otbkg += '    df_ret = pd.read_sql(sql_cons, conn)\n'
            else:
                bipwi__otbkg += '  with objmode({}):\n'.format(', '.join(
                    ypfix__licuy))
                bipwi__otbkg += '    df_ret = pd.read_sql(sql_request, conn)\n'
            for asuuu__tqgi, mbpaa__ulznh in zip(qvqqb__ibiug, col_names):
                bipwi__otbkg += "    {} = df_ret['{}'].values\n".format(
                    asuuu__tqgi, mbpaa__ulznh)
        bipwi__otbkg += '  return ({},)\n'.format(', '.join(jam__nfd for
            jam__nfd in qvqqb__ibiug))
    gqq__zbij = {'bodo': bodo}
    if db_type == 'snowflake':
        gqq__zbij.update(opjg__hmq)
        gqq__zbij.update({'np': np, 'unicode_to_utf8': unicode_to_utf8,
            'check_and_propagate_cpp_exception':
            check_and_propagate_cpp_exception, 'snowflake_read':
            _snowflake_read, 'info_to_array': info_to_array,
            'info_from_table': info_from_table, 'delete_table': delete_table})
    else:
        gqq__zbij.update({'sqlalchemy_check': sqlalchemy_check, 'pd': pd,
            'objmode': objmode, 'bcast_scalar': bcast_scalar,
            'pymysql_check': pymysql_check, 'cx_oracle_check':
            cx_oracle_check, 'psycopg2_check': psycopg2_check})
    dfho__ifb = {}
    exec(bipwi__otbkg, gqq__zbij, dfho__ifb)
    yybya__uwj = dfho__ifb['sql_reader_py']
    wiict__ggcje = numba.njit(yybya__uwj)
    compiled_funcs.append(wiict__ggcje)
    return wiict__ggcje


_snowflake_read = types.ExternalFunction('snowflake_read', table_type(types
    .voidptr, types.voidptr, types.boolean, types.int64, types.voidptr))
import llvmlite.binding as ll
from bodo.io import arrow_cpp
ll.add_symbol('snowflake_read', arrow_cpp.snowflake_read)
