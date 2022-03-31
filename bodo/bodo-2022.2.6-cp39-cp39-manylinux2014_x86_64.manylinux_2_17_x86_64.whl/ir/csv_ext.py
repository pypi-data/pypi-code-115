from collections import defaultdict
import numba
import numpy as np
import pandas as pd
from mpi4py import MPI
from numba.core import ir, ir_utils, typeinfer, types
from numba.core.ir_utils import compile_to_numba_ir, replace_arg_nodes
import bodo
import bodo.ir.connector
from bodo import objmode
from bodo.hiframes.datetime_date_ext import datetime_date_type
from bodo.hiframes.pd_categorical_ext import CategoricalArrayType, PDCategoricalDtype
from bodo.hiframes.table import Table, TableType
from bodo.libs.array_item_arr_ext import ArrayItemArrayType
from bodo.libs.bool_arr_ext import boolean_array
from bodo.libs.int_arr_ext import IntegerArrayType
from bodo.libs.str_arr_ext import StringArrayType, string_array_type
from bodo.libs.str_ext import string_type
from bodo.transforms import distributed_analysis, distributed_pass
from bodo.transforms.table_column_del_pass import get_live_column_nums_block, ir_extension_table_column_use, remove_dead_column_extensions
from bodo.utils.typing import BodoError
from bodo.utils.utils import check_java_installation
from bodo.utils.utils import sanitize_varname


class CsvReader(ir.Stmt):

    def __init__(self, file_name, df_out, sep, df_colnames, out_vars,
        out_types, usecols, loc, header, compression, nrows, skiprows,
        chunksize, is_skiprows_list, low_memory, escapechar,
        index_column_index=None, index_column_typ=types.none):
        self.connector_typ = 'csv'
        self.file_name = file_name
        self.df_out = df_out
        self.sep = sep
        self.df_colnames = df_colnames
        self.out_vars = out_vars
        self.out_types = out_types
        self.usecols = usecols
        self.loc = loc
        self.skiprows = skiprows
        self.nrows = nrows
        self.header = header
        self.compression = compression
        self.chunksize = chunksize
        self.is_skiprows_list = is_skiprows_list
        self.pd_low_memory = low_memory
        self.escapechar = escapechar
        self.index_column_index = index_column_index
        self.index_column_typ = index_column_typ
        self.type_usecol_offset = list(range(len(usecols)))

    def __repr__(self):
        return (
            '{} = ReadCsv(file={}, col_names={}, types={}, vars={}, nrows={}, skiprows={}, chunksize={}, is_skiprows_list={}, pd_low_memory={}, index_column_index={}, index_colum_typ = {}, type_usecol_offsets={})'
            .format(self.df_out, self.file_name, self.df_colnames, self.
            out_types, self.out_vars, self.nrows, self.skiprows, self.
            chunksize, self.is_skiprows_list, self.pd_low_memory, self.
            index_column_index, self.index_column_typ, self.type_usecol_offset)
            )


def check_node_typing(node, typemap):
    ajsy__cyp = typemap[node.file_name.name]
    if types.unliteral(ajsy__cyp) != types.unicode_type:
        raise BodoError(
            f"pd.read_csv(): 'filepath_or_buffer' must be a string. Found type: {ajsy__cyp}."
            , node.file_name.loc)
    if not isinstance(node.skiprows, ir.Const):
        tyrrc__fkcyj = typemap[node.skiprows.name]
        if isinstance(tyrrc__fkcyj, types.Dispatcher):
            raise BodoError(
                f"pd.read_csv(): 'skiprows' callable not supported yet.",
                node.file_name.loc)
        elif not isinstance(tyrrc__fkcyj, types.Integer) and not (isinstance
            (tyrrc__fkcyj, (types.List, types.Tuple)) and isinstance(
            tyrrc__fkcyj.dtype, types.Integer)) and not isinstance(tyrrc__fkcyj
            , (types.LiteralList, bodo.utils.typing.ListLiteral)):
            raise BodoError(
                f"pd.read_csv(): 'skiprows' must be an integer or list of integers. Found type {tyrrc__fkcyj}."
                , loc=node.skiprows.loc)
        elif isinstance(tyrrc__fkcyj, (types.List, types.Tuple)):
            node.is_skiprows_list = True
    if not isinstance(node.nrows, ir.Const):
        ibegq__naes = typemap[node.nrows.name]
        if not isinstance(ibegq__naes, types.Integer):
            raise BodoError(
                f"pd.read_csv(): 'nrows' must be an integer. Found type {ibegq__naes}."
                , loc=node.nrows.loc)


import llvmlite.binding as ll
from bodo.io import csv_cpp
ll.add_symbol('csv_file_chunk_reader', csv_cpp.csv_file_chunk_reader)
csv_file_chunk_reader = types.ExternalFunction('csv_file_chunk_reader',
    bodo.ir.connector.stream_reader_type(types.voidptr, types.bool_, types.
    voidptr, types.int64, types.bool_, types.voidptr, types.voidptr, types.
    int64, types.bool_, types.int64, types.bool_))


def remove_dead_csv(csv_node, lives_no_aliases, lives, arg_aliases,
    alias_map, func_ir, typemap):
    if csv_node.chunksize is not None:
        emk__twgl = csv_node.out_vars[0]
        if emk__twgl.name not in lives:
            return None
    else:
        ypnhl__rsbqs = csv_node.out_vars[0]
        tmzqm__ekle = csv_node.out_vars[1]
        if ypnhl__rsbqs.name not in lives and tmzqm__ekle.name not in lives:
            return None
        elif tmzqm__ekle.name not in lives:
            csv_node.index_column_index = None
            csv_node.index_column_typ = types.none
        elif ypnhl__rsbqs.name not in lives:
            csv_node.usecols = []
            csv_node.out_types = []
            csv_node.type_usecol_offset = []
    return csv_node


def csv_distributed_run(csv_node, array_dists, typemap, calltypes,
    typingctx, targetctx):
    parallel = False
    tyrrc__fkcyj = types.int64 if isinstance(csv_node.skiprows, ir.Const
        ) else types.unliteral(typemap[csv_node.skiprows.name])
    if csv_node.chunksize is not None:
        if bodo.user_logging.get_verbose_level() >= 1:
            yps__mqr = (
                'Finish column pruning on read_csv node:\n%s\nColumns loaded %s\n'
                )
            vznv__xaix = csv_node.loc.strformat()
            gczdp__omy = csv_node.df_colnames
            bodo.user_logging.log_message('Column Pruning', yps__mqr,
                vznv__xaix, gczdp__omy)
            prmwg__slgcc = csv_node.out_types[0].yield_type.data
            xmin__hzt = [xym__tswd for now__gjvi, xym__tswd in enumerate(
                csv_node.df_colnames) if isinstance(prmwg__slgcc[now__gjvi],
                bodo.libs.dict_arr_ext.DictionaryArrayType)]
            if xmin__hzt:
                nlo__mrxtg = """Finished optimized encoding on read_csv node:
%s
Columns %s using dictionary encoding to reduce memory usage.
"""
                bodo.user_logging.log_message('Dictionary Encoding',
                    nlo__mrxtg, vznv__xaix, xmin__hzt)
        if array_dists is not None:
            gwq__soiqc = csv_node.out_vars[0].name
            parallel = array_dists[gwq__soiqc] in (distributed_pass.
                Distribution.OneD, distributed_pass.Distribution.OneD_Var)
        vqmx__vzt = 'def csv_iterator_impl(fname, nrows, skiprows):\n'
        vqmx__vzt += f'    reader = _csv_reader_init(fname, nrows, skiprows)\n'
        vqmx__vzt += (
            f'    iterator = init_csv_iterator(reader, csv_iterator_type)\n')
        pydde__qkb = {}
        from bodo.io.csv_iterator_ext import init_csv_iterator
        exec(vqmx__vzt, {}, pydde__qkb)
        bji__wcvhy = pydde__qkb['csv_iterator_impl']
        bdgau__hruj = 'def csv_reader_init(fname, nrows, skiprows):\n'
        bdgau__hruj += _gen_csv_file_reader_init(parallel, csv_node.header,
            csv_node.compression, csv_node.chunksize, csv_node.
            is_skiprows_list, csv_node.pd_low_memory)
        bdgau__hruj += '  return f_reader\n'
        exec(bdgau__hruj, globals(), pydde__qkb)
        bvbp__qvp = pydde__qkb['csv_reader_init']
        fyln__doncc = numba.njit(bvbp__qvp)
        compiled_funcs.append(fyln__doncc)
        xnnjb__htf = compile_to_numba_ir(bji__wcvhy, {'_csv_reader_init':
            fyln__doncc, 'init_csv_iterator': init_csv_iterator,
            'csv_iterator_type': typemap[csv_node.out_vars[0].name]},
            typingctx=typingctx, targetctx=targetctx, arg_typs=(string_type,
            types.int64, tyrrc__fkcyj), typemap=typemap, calltypes=calltypes
            ).blocks.popitem()[1]
        replace_arg_nodes(xnnjb__htf, [csv_node.file_name, csv_node.nrows,
            csv_node.skiprows])
        kqy__crv = xnnjb__htf.body[:-3]
        kqy__crv[-1].target = csv_node.out_vars[0]
        return kqy__crv
    if array_dists is not None:
        flaki__ncuo = csv_node.out_vars[0].name
        parallel = array_dists[flaki__ncuo] in (distributed_pass.
            Distribution.OneD, distributed_pass.Distribution.OneD_Var)
        juwug__rwpu = csv_node.out_vars[1].name
        assert typemap[juwug__rwpu
            ] == types.none or not parallel or array_dists[juwug__rwpu] in (
            distributed_pass.Distribution.OneD, distributed_pass.
            Distribution.OneD_Var
            ), 'pq data/index parallelization does not match'
    vqmx__vzt = 'def csv_impl(fname, nrows, skiprows):\n'
    vqmx__vzt += (
        f'    (table_val, idx_col) = _csv_reader_py(fname, nrows, skiprows)\n')
    pydde__qkb = {}
    exec(vqmx__vzt, {}, pydde__qkb)
    wwv__qvwy = pydde__qkb['csv_impl']
    ohrhf__xfca = csv_node.usecols
    if ohrhf__xfca:
        ohrhf__xfca = [csv_node.usecols[now__gjvi] for now__gjvi in
            csv_node.type_usecol_offset]
    if bodo.user_logging.get_verbose_level() >= 1:
        yps__mqr = (
            'Finish column pruning on read_csv node:\n%s\nColumns loaded %s\n')
        vznv__xaix = csv_node.loc.strformat()
        gczdp__omy = []
        xmin__hzt = []
        if ohrhf__xfca:
            for now__gjvi in ohrhf__xfca:
                kbc__pql = csv_node.df_colnames[now__gjvi]
                gczdp__omy.append(kbc__pql)
                if isinstance(csv_node.out_types[now__gjvi], bodo.libs.
                    dict_arr_ext.DictionaryArrayType):
                    xmin__hzt.append(kbc__pql)
        bodo.user_logging.log_message('Column Pruning', yps__mqr,
            vznv__xaix, gczdp__omy)
        if xmin__hzt:
            nlo__mrxtg = """Finished optimized encoding on read_csv node:
%s
Columns %s using dictionary encoding to reduce memory usage.
"""
            bodo.user_logging.log_message('Dictionary Encoding', nlo__mrxtg,
                vznv__xaix, xmin__hzt)
    trej__ksgs = _gen_csv_reader_py(csv_node.df_colnames, csv_node.
        out_types, ohrhf__xfca, csv_node.type_usecol_offset, csv_node.sep,
        parallel, csv_node.header, csv_node.compression, csv_node.
        is_skiprows_list, csv_node.pd_low_memory, csv_node.escapechar,
        idx_col_index=csv_node.index_column_index, idx_col_typ=csv_node.
        index_column_typ)
    xnnjb__htf = compile_to_numba_ir(wwv__qvwy, {'_csv_reader_py':
        trej__ksgs}, typingctx=typingctx, targetctx=targetctx, arg_typs=(
        string_type, types.int64, tyrrc__fkcyj), typemap=typemap, calltypes
        =calltypes).blocks.popitem()[1]
    replace_arg_nodes(xnnjb__htf, [csv_node.file_name, csv_node.nrows,
        csv_node.skiprows, csv_node.is_skiprows_list])
    kqy__crv = xnnjb__htf.body[:-3]
    kqy__crv[-1].target = csv_node.out_vars[1]
    kqy__crv[-2].target = csv_node.out_vars[0]
    if csv_node.index_column_index is None:
        kqy__crv.pop(-1)
    elif not ohrhf__xfca:
        kqy__crv.pop(-2)
    return kqy__crv


def csv_remove_dead_column(csv_node, column_live_map, equiv_vars, typemap):
    if csv_node.chunksize is not None:
        return False
    assert len(csv_node.out_vars) == 2, 'invalid CsvReader node'
    ejax__msh = csv_node.out_vars[0].name
    if isinstance(typemap[ejax__msh], TableType) and csv_node.usecols:
        olm__wuz, vrgxn__oqkn = get_live_column_nums_block(column_live_map,
            equiv_vars, ejax__msh)
        olm__wuz = bodo.ir.connector.trim_extra_used_columns(olm__wuz, len(
            csv_node.usecols))
        if not vrgxn__oqkn and not olm__wuz:
            olm__wuz = [0]
        if not vrgxn__oqkn and len(olm__wuz) != len(csv_node.type_usecol_offset
            ):
            csv_node.type_usecol_offset = olm__wuz
            return True
    return False


def csv_table_column_use(csv_node, block_use_map, equiv_vars, typemap):
    return


numba.parfors.array_analysis.array_analysis_extensions[CsvReader
    ] = bodo.ir.connector.connector_array_analysis
distributed_analysis.distributed_analysis_extensions[CsvReader
    ] = bodo.ir.connector.connector_distributed_analysis
typeinfer.typeinfer_extensions[CsvReader
    ] = bodo.ir.connector.connector_typeinfer
ir_utils.visit_vars_extensions[CsvReader
    ] = bodo.ir.connector.visit_vars_connector
ir_utils.remove_dead_extensions[CsvReader] = remove_dead_csv
numba.core.analysis.ir_extension_usedefs[CsvReader
    ] = bodo.ir.connector.connector_usedefs
ir_utils.copy_propagate_extensions[CsvReader
    ] = bodo.ir.connector.get_copies_connector
ir_utils.apply_copy_propagate_extensions[CsvReader
    ] = bodo.ir.connector.apply_copies_connector
ir_utils.build_defs_extensions[CsvReader
    ] = bodo.ir.connector.build_connector_definitions
distributed_pass.distributed_run_extensions[CsvReader] = csv_distributed_run
remove_dead_column_extensions[CsvReader] = csv_remove_dead_column
ir_extension_table_column_use[CsvReader] = csv_table_column_use


def _get_dtype_str(t):
    bfdea__xncq = t.dtype
    if isinstance(bfdea__xncq, PDCategoricalDtype):
        zrqt__kyhsc = CategoricalArrayType(bfdea__xncq)
        fmtx__lnb = 'CategoricalArrayType' + str(ir_utils.next_label())
        setattr(types, fmtx__lnb, zrqt__kyhsc)
        return fmtx__lnb
    if bfdea__xncq == types.NPDatetime('ns'):
        bfdea__xncq = 'NPDatetime("ns")'
    if t == string_array_type:
        types.string_array_type = string_array_type
        return 'string_array_type'
    if isinstance(t, IntegerArrayType):
        djzf__rjb = 'int_arr_{}'.format(bfdea__xncq)
        setattr(types, djzf__rjb, t)
        return djzf__rjb
    if t == boolean_array:
        types.boolean_array = boolean_array
        return 'boolean_array'
    if bfdea__xncq == types.bool_:
        bfdea__xncq = 'bool_'
    if bfdea__xncq == datetime_date_type:
        return 'datetime_date_array_type'
    if isinstance(t, ArrayItemArrayType) and isinstance(bfdea__xncq, (
        StringArrayType, ArrayItemArrayType)):
        luf__mfyca = f'ArrayItemArrayType{str(ir_utils.next_label())}'
        setattr(types, luf__mfyca, t)
        return luf__mfyca
    return '{}[::1]'.format(bfdea__xncq)


def _get_pd_dtype_str(t):
    bfdea__xncq = t.dtype
    if isinstance(bfdea__xncq, PDCategoricalDtype):
        return 'pd.CategoricalDtype({})'.format(bfdea__xncq.categories)
    if bfdea__xncq == types.NPDatetime('ns'):
        return 'str'
    if t == string_array_type:
        return 'str'
    if isinstance(t, IntegerArrayType):
        return '"{}Int{}"'.format('' if bfdea__xncq.signed else 'U',
            bfdea__xncq.bitwidth)
    if t == boolean_array:
        return 'np.bool_'
    if isinstance(t, ArrayItemArrayType) and isinstance(bfdea__xncq, (
        StringArrayType, ArrayItemArrayType)):
        return 'object'
    return 'np.{}'.format(bfdea__xncq)


compiled_funcs = []


@numba.njit
def check_nrows_skiprows_value(nrows, skiprows):
    if nrows < -1:
        raise ValueError('pd.read_csv: nrows must be integer >= 0.')
    if skiprows[0] < 0:
        raise ValueError('pd.read_csv: skiprows must be integer >= 0.')


def astype(df, typemap, parallel):
    npdx__qbe = ''
    from collections import defaultdict
    nspa__tcic = defaultdict(list)
    for cku__vay, kzim__qijkw in typemap.items():
        nspa__tcic[kzim__qijkw].append(cku__vay)
    hwi__env = df.columns.to_list()
    uljib__reiu = []
    for kzim__qijkw, tmf__dveol in nspa__tcic.items():
        try:
            uljib__reiu.append(df.loc[:, tmf__dveol].astype(kzim__qijkw,
                copy=False))
            df = df.drop(tmf__dveol, axis=1)
        except (ValueError, TypeError) as plef__gmacr:
            npdx__qbe = (
                f"Caught the runtime error '{plef__gmacr}' on columns {tmf__dveol}. Consider setting the 'dtype' argument in 'read_csv' or investigate if the data is corrupted."
                )
            break
    ibeg__zkxt = bool(npdx__qbe)
    if parallel:
        edwf__bacaa = MPI.COMM_WORLD
        ibeg__zkxt = edwf__bacaa.allreduce(ibeg__zkxt, op=MPI.LOR)
    if ibeg__zkxt:
        gtav__avw = 'pd.read_csv(): Bodo could not infer dtypes correctly.'
        if npdx__qbe:
            raise TypeError(f'{gtav__avw}\n{npdx__qbe}')
        else:
            raise TypeError(
                f'{gtav__avw}\nPlease refer to errors on other ranks.')
    df = pd.concat(uljib__reiu + [df], axis=1)
    fttlk__kkqns = df.loc[:, hwi__env]
    return fttlk__kkqns


def _gen_csv_file_reader_init(parallel, header, compression, chunksize,
    is_skiprows_list, pd_low_memory):
    wpux__jlpik = header == 0
    if compression is None:
        compression = 'uncompressed'
    if is_skiprows_list:
        vqmx__vzt = '  skiprows = sorted(set(skiprows))\n'
    else:
        vqmx__vzt = '  skiprows = [skiprows]\n'
    vqmx__vzt += '  skiprows_list_len = len(skiprows)\n'
    vqmx__vzt += '  check_nrows_skiprows_value(nrows, skiprows)\n'
    vqmx__vzt += '  check_java_installation(fname)\n'
    vqmx__vzt += f"""  bucket_region = bodo.io.fs_io.get_s3_bucket_region_njit(fname, parallel={parallel})
"""
    vqmx__vzt += (
        '  f_reader = bodo.ir.csv_ext.csv_file_chunk_reader(bodo.libs.str_ext.unicode_to_utf8(fname), '
        )
    vqmx__vzt += (
        """    {}, bodo.utils.conversion.coerce_to_ndarray(skiprows, scalar_to_arr_len=1).ctypes, nrows, {}, bodo.libs.str_ext.unicode_to_utf8('{}'), bodo.libs.str_ext.unicode_to_utf8(bucket_region), {}, {}, skiprows_list_len, {})
"""
        .format(parallel, wpux__jlpik, compression, chunksize,
        is_skiprows_list, pd_low_memory))
    vqmx__vzt += '  bodo.utils.utils.check_and_propagate_cpp_exception()\n'
    vqmx__vzt += '  if bodo.utils.utils.is_null_pointer(f_reader):\n'
    vqmx__vzt += "      raise FileNotFoundError('File does not exist')\n"
    return vqmx__vzt


def _gen_read_csv_objmode(col_names, sanitized_cnames, col_typs, usecols,
    type_usecol_offset, sep, escapechar, call_id, glbs, parallel,
    check_parallel_runtime, idx_col_index, idx_col_typ):
    udanz__dqmg = [str(uww__parpn) for now__gjvi, uww__parpn in enumerate(
        usecols) if col_typs[type_usecol_offset[now__gjvi]].dtype == types.
        NPDatetime('ns')]
    if idx_col_typ == types.NPDatetime('ns'):
        assert not idx_col_index is None
        udanz__dqmg.append(str(idx_col_index))
    uzpd__jntdr = ', '.join(udanz__dqmg)
    gazvk__qwnzb = _gen_parallel_flag_name(sanitized_cnames)
    ggu__miuav = f"{gazvk__qwnzb}='bool_'" if check_parallel_runtime else ''
    trej__bbkm = [_get_pd_dtype_str(col_typs[type_usecol_offset[now__gjvi]]
        ) for now__gjvi in range(len(usecols))]
    vawf__slhs = None if idx_col_index is None else _get_pd_dtype_str(
        idx_col_typ)
    ltg__mmkon = [uww__parpn for now__gjvi, uww__parpn in enumerate(usecols
        ) if trej__bbkm[now__gjvi] == 'str']
    if idx_col_index is not None and vawf__slhs == 'str':
        ltg__mmkon.append(idx_col_index)
    figzt__ioj = np.array(ltg__mmkon, dtype=np.int64)
    glbs[f'str_col_nums_{call_id}'] = figzt__ioj
    vqmx__vzt = f'  str_col_nums_{call_id}_2 = str_col_nums_{call_id}\n'
    hvyyp__frz = np.array(usecols + ([idx_col_index] if idx_col_index is not
        None else []))
    glbs[f'usecols_arr_{call_id}'] = hvyyp__frz
    vqmx__vzt += f'  usecols_arr_{call_id}_2 = usecols_arr_{call_id}\n'
    rtr__xrew = np.array(type_usecol_offset, dtype=np.int64)
    if usecols:
        glbs[f'type_usecols_offsets_arr_{call_id}'] = rtr__xrew
        vqmx__vzt += f"""  type_usecols_offsets_arr_{call_id}_2 = type_usecols_offsets_arr_{call_id}
"""
    kmo__pkb = defaultdict(list)
    for now__gjvi, uww__parpn in enumerate(usecols):
        if trej__bbkm[now__gjvi] == 'str':
            continue
        kmo__pkb[trej__bbkm[now__gjvi]].append(uww__parpn)
    if idx_col_index is not None and vawf__slhs != 'str':
        kmo__pkb[vawf__slhs].append(idx_col_index)
    for now__gjvi, mdx__kux in enumerate(kmo__pkb.values()):
        glbs[f't_arr_{now__gjvi}_{call_id}'] = np.asarray(mdx__kux)
        vqmx__vzt += (
            f'  t_arr_{now__gjvi}_{call_id}_2 = t_arr_{now__gjvi}_{call_id}\n')
    if idx_col_index != None:
        vqmx__vzt += f"""  with objmode(T=table_type_{call_id}, idx_arr=idx_array_typ, {ggu__miuav}):
"""
    else:
        vqmx__vzt += f'  with objmode(T=table_type_{call_id}, {ggu__miuav}):\n'
    vqmx__vzt += f'    typemap = {{}}\n'
    for now__gjvi, imrnm__vyu in enumerate(kmo__pkb.keys()):
        vqmx__vzt += f"""    typemap.update({{i:{imrnm__vyu} for i in t_arr_{now__gjvi}_{call_id}_2}})
"""
    vqmx__vzt += '    if f_reader.get_chunk_size() == 0:\n'
    vqmx__vzt += (
        f'      df = pd.DataFrame(columns=usecols_arr_{call_id}_2, dtype=str)\n'
        )
    vqmx__vzt += '    else:\n'
    vqmx__vzt += '      df = pd.read_csv(f_reader,\n'
    vqmx__vzt += '        header=None,\n'
    vqmx__vzt += '        parse_dates=[{}],\n'.format(uzpd__jntdr)
    vqmx__vzt += (
        f'        dtype={{i:str for i in str_col_nums_{call_id}_2}},\n')
    vqmx__vzt += f"""        usecols=usecols_arr_{call_id}_2, sep={sep!r}, low_memory=False, escapechar={escapechar!r})
"""
    if check_parallel_runtime:
        vqmx__vzt += f'    {gazvk__qwnzb} = f_reader.is_parallel()\n'
    else:
        vqmx__vzt += f'    {gazvk__qwnzb} = {parallel}\n'
    vqmx__vzt += f'    df = astype(df, typemap, {gazvk__qwnzb})\n'
    if idx_col_index != None:
        ffcp__cgc = sorted(hvyyp__frz).index(idx_col_index)
        vqmx__vzt += f'    idx_arr = df.iloc[:, {ffcp__cgc}].values\n'
        vqmx__vzt += (
            f'    df.drop(columns=df.columns[{ffcp__cgc}], inplace=True)\n')
    if len(usecols) == 0:
        vqmx__vzt += f'    T = None\n'
    else:
        vqmx__vzt += f'    arrs = []\n'
        vqmx__vzt += f'    for i in range(df.shape[1]):\n'
        vqmx__vzt += f'      arrs.append(df.iloc[:, i].values)\n'
        vqmx__vzt += f"""    T = Table(arrs, type_usecols_offsets_arr_{call_id}_2, {len(col_names)})
"""
    return vqmx__vzt


def _gen_parallel_flag_name(sanitized_cnames):
    gazvk__qwnzb = '_parallel_value'
    while gazvk__qwnzb in sanitized_cnames:
        gazvk__qwnzb = '_' + gazvk__qwnzb
    return gazvk__qwnzb


def _gen_csv_reader_py(col_names, col_typs, usecols, type_usecol_offset,
    sep, parallel, header, compression, is_skiprows_list, pd_low_memory,
    escapechar, idx_col_index=None, idx_col_typ=types.none):
    sanitized_cnames = [sanitize_varname(xym__tswd) for xym__tswd in col_names]
    vqmx__vzt = 'def csv_reader_py(fname, nrows, skiprows):\n'
    vqmx__vzt += _gen_csv_file_reader_init(parallel, header, compression, -
        1, is_skiprows_list, pd_low_memory)
    call_id = ir_utils.next_label()
    ymp__pecjs = globals()
    if idx_col_typ != types.none:
        ymp__pecjs[f'idx_array_typ'] = idx_col_typ
    if len(usecols) == 0:
        ymp__pecjs[f'table_type_{call_id}'] = types.none
    else:
        ymp__pecjs[f'table_type_{call_id}'] = TableType(tuple(col_typs))
    vqmx__vzt += _gen_read_csv_objmode(col_names, sanitized_cnames,
        col_typs, usecols, type_usecol_offset, sep, escapechar, call_id,
        ymp__pecjs, parallel=parallel, check_parallel_runtime=False,
        idx_col_index=idx_col_index, idx_col_typ=idx_col_typ)
    if idx_col_index != None:
        vqmx__vzt += '  return (T, idx_arr)\n'
    else:
        vqmx__vzt += '  return (T, None)\n'
    pydde__qkb = {}
    exec(vqmx__vzt, ymp__pecjs, pydde__qkb)
    trej__ksgs = pydde__qkb['csv_reader_py']
    fyln__doncc = numba.njit(trej__ksgs)
    compiled_funcs.append(fyln__doncc)
    return fyln__doncc
