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
    xuala__ssr = typemap[node.file_name.name]
    if types.unliteral(xuala__ssr) != types.unicode_type:
        raise BodoError(
            f"pd.read_csv(): 'filepath_or_buffer' must be a string. Found type: {xuala__ssr}."
            , node.file_name.loc)
    if not isinstance(node.skiprows, ir.Const):
        zqtmo__rtq = typemap[node.skiprows.name]
        if isinstance(zqtmo__rtq, types.Dispatcher):
            raise BodoError(
                f"pd.read_csv(): 'skiprows' callable not supported yet.",
                node.file_name.loc)
        elif not isinstance(zqtmo__rtq, types.Integer) and not (isinstance(
            zqtmo__rtq, (types.List, types.Tuple)) and isinstance(
            zqtmo__rtq.dtype, types.Integer)) and not isinstance(zqtmo__rtq,
            (types.LiteralList, bodo.utils.typing.ListLiteral)):
            raise BodoError(
                f"pd.read_csv(): 'skiprows' must be an integer or list of integers. Found type {zqtmo__rtq}."
                , loc=node.skiprows.loc)
        elif isinstance(zqtmo__rtq, (types.List, types.Tuple)):
            node.is_skiprows_list = True
    if not isinstance(node.nrows, ir.Const):
        lbrym__julg = typemap[node.nrows.name]
        if not isinstance(lbrym__julg, types.Integer):
            raise BodoError(
                f"pd.read_csv(): 'nrows' must be an integer. Found type {lbrym__julg}."
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
        nwfx__xodc = csv_node.out_vars[0]
        if nwfx__xodc.name not in lives:
            return None
    else:
        dwc__izy = csv_node.out_vars[0]
        bunvw__meq = csv_node.out_vars[1]
        if dwc__izy.name not in lives and bunvw__meq.name not in lives:
            return None
        elif bunvw__meq.name not in lives:
            csv_node.index_column_index = None
            csv_node.index_column_typ = types.none
        elif dwc__izy.name not in lives:
            csv_node.usecols = []
            csv_node.out_types = []
            csv_node.type_usecol_offset = []
    return csv_node


def csv_distributed_run(csv_node, array_dists, typemap, calltypes,
    typingctx, targetctx):
    parallel = False
    zqtmo__rtq = types.int64 if isinstance(csv_node.skiprows, ir.Const
        ) else types.unliteral(typemap[csv_node.skiprows.name])
    if csv_node.chunksize is not None:
        if bodo.user_logging.get_verbose_level() >= 1:
            fcz__jjjx = (
                'Finish column pruning on read_csv node:\n%s\nColumns loaded %s\n'
                )
            epdeo__wzjnc = csv_node.loc.strformat()
            ubu__uke = csv_node.df_colnames
            bodo.user_logging.log_message('Column Pruning', fcz__jjjx,
                epdeo__wzjnc, ubu__uke)
            vqh__vpk = csv_node.out_types[0].yield_type.data
            chvgc__opvwy = [oslyd__qhfr for javai__bqzhz, oslyd__qhfr in
                enumerate(csv_node.df_colnames) if isinstance(vqh__vpk[
                javai__bqzhz], bodo.libs.dict_arr_ext.DictionaryArrayType)]
            if chvgc__opvwy:
                ekmr__bihr = """Finished optimized encoding on read_csv node:
%s
Columns %s using dictionary encoding to reduce memory usage.
"""
                bodo.user_logging.log_message('Dictionary Encoding',
                    ekmr__bihr, epdeo__wzjnc, chvgc__opvwy)
        if array_dists is not None:
            dpteo__tdrl = csv_node.out_vars[0].name
            parallel = array_dists[dpteo__tdrl] in (distributed_pass.
                Distribution.OneD, distributed_pass.Distribution.OneD_Var)
        suzy__ymiel = 'def csv_iterator_impl(fname, nrows, skiprows):\n'
        suzy__ymiel += (
            f'    reader = _csv_reader_init(fname, nrows, skiprows)\n')
        suzy__ymiel += (
            f'    iterator = init_csv_iterator(reader, csv_iterator_type)\n')
        bigjs__yymrf = {}
        from bodo.io.csv_iterator_ext import init_csv_iterator
        exec(suzy__ymiel, {}, bigjs__yymrf)
        siq__xri = bigjs__yymrf['csv_iterator_impl']
        mfbb__bcsov = 'def csv_reader_init(fname, nrows, skiprows):\n'
        mfbb__bcsov += _gen_csv_file_reader_init(parallel, csv_node.header,
            csv_node.compression, csv_node.chunksize, csv_node.
            is_skiprows_list, csv_node.pd_low_memory)
        mfbb__bcsov += '  return f_reader\n'
        exec(mfbb__bcsov, globals(), bigjs__yymrf)
        xhde__jtqm = bigjs__yymrf['csv_reader_init']
        kxot__how = numba.njit(xhde__jtqm)
        compiled_funcs.append(kxot__how)
        ypns__tji = compile_to_numba_ir(siq__xri, {'_csv_reader_init':
            kxot__how, 'init_csv_iterator': init_csv_iterator,
            'csv_iterator_type': typemap[csv_node.out_vars[0].name]},
            typingctx=typingctx, targetctx=targetctx, arg_typs=(string_type,
            types.int64, zqtmo__rtq), typemap=typemap, calltypes=calltypes
            ).blocks.popitem()[1]
        replace_arg_nodes(ypns__tji, [csv_node.file_name, csv_node.nrows,
            csv_node.skiprows])
        ifgd__kkg = ypns__tji.body[:-3]
        ifgd__kkg[-1].target = csv_node.out_vars[0]
        return ifgd__kkg
    if array_dists is not None:
        seu__hfw = csv_node.out_vars[0].name
        parallel = array_dists[seu__hfw] in (distributed_pass.Distribution.
            OneD, distributed_pass.Distribution.OneD_Var)
        luaza__ffgs = csv_node.out_vars[1].name
        assert typemap[luaza__ffgs
            ] == types.none or not parallel or array_dists[luaza__ffgs] in (
            distributed_pass.Distribution.OneD, distributed_pass.
            Distribution.OneD_Var
            ), 'pq data/index parallelization does not match'
    suzy__ymiel = 'def csv_impl(fname, nrows, skiprows):\n'
    suzy__ymiel += (
        f'    (table_val, idx_col) = _csv_reader_py(fname, nrows, skiprows)\n')
    bigjs__yymrf = {}
    exec(suzy__ymiel, {}, bigjs__yymrf)
    gvbm__wheb = bigjs__yymrf['csv_impl']
    fts__fan = csv_node.usecols
    if fts__fan:
        fts__fan = [csv_node.usecols[javai__bqzhz] for javai__bqzhz in
            csv_node.type_usecol_offset]
    if bodo.user_logging.get_verbose_level() >= 1:
        fcz__jjjx = (
            'Finish column pruning on read_csv node:\n%s\nColumns loaded %s\n')
        epdeo__wzjnc = csv_node.loc.strformat()
        ubu__uke = []
        chvgc__opvwy = []
        if fts__fan:
            for javai__bqzhz in fts__fan:
                agbc__ggmm = csv_node.df_colnames[javai__bqzhz]
                ubu__uke.append(agbc__ggmm)
                if isinstance(csv_node.out_types[javai__bqzhz], bodo.libs.
                    dict_arr_ext.DictionaryArrayType):
                    chvgc__opvwy.append(agbc__ggmm)
        bodo.user_logging.log_message('Column Pruning', fcz__jjjx,
            epdeo__wzjnc, ubu__uke)
        if chvgc__opvwy:
            ekmr__bihr = """Finished optimized encoding on read_csv node:
%s
Columns %s using dictionary encoding to reduce memory usage.
"""
            bodo.user_logging.log_message('Dictionary Encoding', ekmr__bihr,
                epdeo__wzjnc, chvgc__opvwy)
    lva__ejwv = _gen_csv_reader_py(csv_node.df_colnames, csv_node.out_types,
        fts__fan, csv_node.type_usecol_offset, csv_node.sep, parallel,
        csv_node.header, csv_node.compression, csv_node.is_skiprows_list,
        csv_node.pd_low_memory, csv_node.escapechar, idx_col_index=csv_node
        .index_column_index, idx_col_typ=csv_node.index_column_typ)
    ypns__tji = compile_to_numba_ir(gvbm__wheb, {'_csv_reader_py':
        lva__ejwv}, typingctx=typingctx, targetctx=targetctx, arg_typs=(
        string_type, types.int64, zqtmo__rtq), typemap=typemap, calltypes=
        calltypes).blocks.popitem()[1]
    replace_arg_nodes(ypns__tji, [csv_node.file_name, csv_node.nrows,
        csv_node.skiprows, csv_node.is_skiprows_list])
    ifgd__kkg = ypns__tji.body[:-3]
    ifgd__kkg[-1].target = csv_node.out_vars[1]
    ifgd__kkg[-2].target = csv_node.out_vars[0]
    if csv_node.index_column_index is None:
        ifgd__kkg.pop(-1)
    elif not fts__fan:
        ifgd__kkg.pop(-2)
    return ifgd__kkg


def csv_remove_dead_column(csv_node, column_live_map, equiv_vars, typemap):
    if csv_node.chunksize is not None:
        return False
    assert len(csv_node.out_vars) == 2, 'invalid CsvReader node'
    zvxv__bkpcx = csv_node.out_vars[0].name
    if isinstance(typemap[zvxv__bkpcx], TableType) and csv_node.usecols:
        rurb__esmd, evxbb__jbb = get_live_column_nums_block(column_live_map,
            equiv_vars, zvxv__bkpcx)
        rurb__esmd = bodo.ir.connector.trim_extra_used_columns(rurb__esmd,
            len(csv_node.usecols))
        if not evxbb__jbb and not rurb__esmd:
            rurb__esmd = [0]
        if not evxbb__jbb and len(rurb__esmd) != len(csv_node.
            type_usecol_offset):
            csv_node.type_usecol_offset = rurb__esmd
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
    cilhr__nuw = t.dtype
    if isinstance(cilhr__nuw, PDCategoricalDtype):
        lob__pqo = CategoricalArrayType(cilhr__nuw)
        rcgov__hps = 'CategoricalArrayType' + str(ir_utils.next_label())
        setattr(types, rcgov__hps, lob__pqo)
        return rcgov__hps
    if cilhr__nuw == types.NPDatetime('ns'):
        cilhr__nuw = 'NPDatetime("ns")'
    if t == string_array_type:
        types.string_array_type = string_array_type
        return 'string_array_type'
    if isinstance(t, IntegerArrayType):
        odfw__mlrie = 'int_arr_{}'.format(cilhr__nuw)
        setattr(types, odfw__mlrie, t)
        return odfw__mlrie
    if t == boolean_array:
        types.boolean_array = boolean_array
        return 'boolean_array'
    if cilhr__nuw == types.bool_:
        cilhr__nuw = 'bool_'
    if cilhr__nuw == datetime_date_type:
        return 'datetime_date_array_type'
    if isinstance(t, ArrayItemArrayType) and isinstance(cilhr__nuw, (
        StringArrayType, ArrayItemArrayType)):
        anjzl__eizlx = f'ArrayItemArrayType{str(ir_utils.next_label())}'
        setattr(types, anjzl__eizlx, t)
        return anjzl__eizlx
    return '{}[::1]'.format(cilhr__nuw)


def _get_pd_dtype_str(t):
    cilhr__nuw = t.dtype
    if isinstance(cilhr__nuw, PDCategoricalDtype):
        return 'pd.CategoricalDtype({})'.format(cilhr__nuw.categories)
    if cilhr__nuw == types.NPDatetime('ns'):
        return 'str'
    if t == string_array_type:
        return 'str'
    if isinstance(t, IntegerArrayType):
        return '"{}Int{}"'.format('' if cilhr__nuw.signed else 'U',
            cilhr__nuw.bitwidth)
    if t == boolean_array:
        return 'np.bool_'
    if isinstance(t, ArrayItemArrayType) and isinstance(cilhr__nuw, (
        StringArrayType, ArrayItemArrayType)):
        return 'object'
    return 'np.{}'.format(cilhr__nuw)


compiled_funcs = []


@numba.njit
def check_nrows_skiprows_value(nrows, skiprows):
    if nrows < -1:
        raise ValueError('pd.read_csv: nrows must be integer >= 0.')
    if skiprows[0] < 0:
        raise ValueError('pd.read_csv: skiprows must be integer >= 0.')


def astype(df, typemap, parallel):
    gkyp__zcpe = ''
    from collections import defaultdict
    xwpem__rba = defaultdict(list)
    for umg__jneun, prvfd__snto in typemap.items():
        xwpem__rba[prvfd__snto].append(umg__jneun)
    bnuv__umw = df.columns.to_list()
    hcqv__xaih = []
    for prvfd__snto, eih__coeqj in xwpem__rba.items():
        try:
            hcqv__xaih.append(df.loc[:, eih__coeqj].astype(prvfd__snto,
                copy=False))
            df = df.drop(eih__coeqj, axis=1)
        except (ValueError, TypeError) as ibuq__hvg:
            gkyp__zcpe = (
                f"Caught the runtime error '{ibuq__hvg}' on columns {eih__coeqj}. Consider setting the 'dtype' argument in 'read_csv' or investigate if the data is corrupted."
                )
            break
    eszi__mrwp = bool(gkyp__zcpe)
    if parallel:
        ymlk__zao = MPI.COMM_WORLD
        eszi__mrwp = ymlk__zao.allreduce(eszi__mrwp, op=MPI.LOR)
    if eszi__mrwp:
        kvry__jqpbl = 'pd.read_csv(): Bodo could not infer dtypes correctly.'
        if gkyp__zcpe:
            raise TypeError(f'{kvry__jqpbl}\n{gkyp__zcpe}')
        else:
            raise TypeError(
                f'{kvry__jqpbl}\nPlease refer to errors on other ranks.')
    df = pd.concat(hcqv__xaih + [df], axis=1)
    heat__rzn = df.loc[:, bnuv__umw]
    return heat__rzn


def _gen_csv_file_reader_init(parallel, header, compression, chunksize,
    is_skiprows_list, pd_low_memory):
    fmq__bfzlh = header == 0
    if compression is None:
        compression = 'uncompressed'
    if is_skiprows_list:
        suzy__ymiel = '  skiprows = sorted(set(skiprows))\n'
    else:
        suzy__ymiel = '  skiprows = [skiprows]\n'
    suzy__ymiel += '  skiprows_list_len = len(skiprows)\n'
    suzy__ymiel += '  check_nrows_skiprows_value(nrows, skiprows)\n'
    suzy__ymiel += '  check_java_installation(fname)\n'
    suzy__ymiel += f"""  bucket_region = bodo.io.fs_io.get_s3_bucket_region_njit(fname, parallel={parallel})
"""
    suzy__ymiel += (
        '  f_reader = bodo.ir.csv_ext.csv_file_chunk_reader(bodo.libs.str_ext.unicode_to_utf8(fname), '
        )
    suzy__ymiel += (
        """    {}, bodo.utils.conversion.coerce_to_ndarray(skiprows, scalar_to_arr_len=1).ctypes, nrows, {}, bodo.libs.str_ext.unicode_to_utf8('{}'), bodo.libs.str_ext.unicode_to_utf8(bucket_region), {}, {}, skiprows_list_len, {})
"""
        .format(parallel, fmq__bfzlh, compression, chunksize,
        is_skiprows_list, pd_low_memory))
    suzy__ymiel += '  bodo.utils.utils.check_and_propagate_cpp_exception()\n'
    suzy__ymiel += '  if bodo.utils.utils.is_null_pointer(f_reader):\n'
    suzy__ymiel += "      raise FileNotFoundError('File does not exist')\n"
    return suzy__ymiel


def _gen_read_csv_objmode(col_names, sanitized_cnames, col_typs, usecols,
    type_usecol_offset, sep, escapechar, call_id, glbs, parallel,
    check_parallel_runtime, idx_col_index, idx_col_typ):
    lknlj__xuqah = [str(onr__xhjo) for javai__bqzhz, onr__xhjo in enumerate
        (usecols) if col_typs[type_usecol_offset[javai__bqzhz]].dtype ==
        types.NPDatetime('ns')]
    if idx_col_typ == types.NPDatetime('ns'):
        assert not idx_col_index is None
        lknlj__xuqah.append(str(idx_col_index))
    las__kzqo = ', '.join(lknlj__xuqah)
    zoi__wsx = _gen_parallel_flag_name(sanitized_cnames)
    yhezz__sgqf = f"{zoi__wsx}='bool_'" if check_parallel_runtime else ''
    aow__yxtza = [_get_pd_dtype_str(col_typs[type_usecol_offset[
        javai__bqzhz]]) for javai__bqzhz in range(len(usecols))]
    axhlc__jfje = None if idx_col_index is None else _get_pd_dtype_str(
        idx_col_typ)
    vdb__xsoj = [onr__xhjo for javai__bqzhz, onr__xhjo in enumerate(usecols
        ) if aow__yxtza[javai__bqzhz] == 'str']
    if idx_col_index is not None and axhlc__jfje == 'str':
        vdb__xsoj.append(idx_col_index)
    ndi__llpi = np.array(vdb__xsoj, dtype=np.int64)
    glbs[f'str_col_nums_{call_id}'] = ndi__llpi
    suzy__ymiel = f'  str_col_nums_{call_id}_2 = str_col_nums_{call_id}\n'
    cra__wta = np.array(usecols + ([idx_col_index] if idx_col_index is not
        None else []))
    glbs[f'usecols_arr_{call_id}'] = cra__wta
    suzy__ymiel += f'  usecols_arr_{call_id}_2 = usecols_arr_{call_id}\n'
    eza__zrte = np.array(type_usecol_offset, dtype=np.int64)
    if usecols:
        glbs[f'type_usecols_offsets_arr_{call_id}'] = eza__zrte
        suzy__ymiel += f"""  type_usecols_offsets_arr_{call_id}_2 = type_usecols_offsets_arr_{call_id}
"""
    eccag__zctqe = defaultdict(list)
    for javai__bqzhz, onr__xhjo in enumerate(usecols):
        if aow__yxtza[javai__bqzhz] == 'str':
            continue
        eccag__zctqe[aow__yxtza[javai__bqzhz]].append(onr__xhjo)
    if idx_col_index is not None and axhlc__jfje != 'str':
        eccag__zctqe[axhlc__jfje].append(idx_col_index)
    for javai__bqzhz, qdq__tkb in enumerate(eccag__zctqe.values()):
        glbs[f't_arr_{javai__bqzhz}_{call_id}'] = np.asarray(qdq__tkb)
        suzy__ymiel += (
            f'  t_arr_{javai__bqzhz}_{call_id}_2 = t_arr_{javai__bqzhz}_{call_id}\n'
            )
    if idx_col_index != None:
        suzy__ymiel += f"""  with objmode(T=table_type_{call_id}, idx_arr=idx_array_typ, {yhezz__sgqf}):
"""
    else:
        suzy__ymiel += (
            f'  with objmode(T=table_type_{call_id}, {yhezz__sgqf}):\n')
    suzy__ymiel += f'    typemap = {{}}\n'
    for javai__bqzhz, rlq__lsqr in enumerate(eccag__zctqe.keys()):
        suzy__ymiel += f"""    typemap.update({{i:{rlq__lsqr} for i in t_arr_{javai__bqzhz}_{call_id}_2}})
"""
    suzy__ymiel += '    if f_reader.get_chunk_size() == 0:\n'
    suzy__ymiel += (
        f'      df = pd.DataFrame(columns=usecols_arr_{call_id}_2, dtype=str)\n'
        )
    suzy__ymiel += '    else:\n'
    suzy__ymiel += '      df = pd.read_csv(f_reader,\n'
    suzy__ymiel += '        header=None,\n'
    suzy__ymiel += '        parse_dates=[{}],\n'.format(las__kzqo)
    suzy__ymiel += (
        f'        dtype={{i:str for i in str_col_nums_{call_id}_2}},\n')
    suzy__ymiel += f"""        usecols=usecols_arr_{call_id}_2, sep={sep!r}, low_memory=False, escapechar={escapechar!r})
"""
    if check_parallel_runtime:
        suzy__ymiel += f'    {zoi__wsx} = f_reader.is_parallel()\n'
    else:
        suzy__ymiel += f'    {zoi__wsx} = {parallel}\n'
    suzy__ymiel += f'    df = astype(df, typemap, {zoi__wsx})\n'
    if idx_col_index != None:
        rsl__asrhh = sorted(cra__wta).index(idx_col_index)
        suzy__ymiel += f'    idx_arr = df.iloc[:, {rsl__asrhh}].values\n'
        suzy__ymiel += (
            f'    df.drop(columns=df.columns[{rsl__asrhh}], inplace=True)\n')
    if len(usecols) == 0:
        suzy__ymiel += f'    T = None\n'
    else:
        suzy__ymiel += f'    arrs = []\n'
        suzy__ymiel += f'    for i in range(df.shape[1]):\n'
        suzy__ymiel += f'      arrs.append(df.iloc[:, i].values)\n'
        suzy__ymiel += f"""    T = Table(arrs, type_usecols_offsets_arr_{call_id}_2, {len(col_names)})
"""
    return suzy__ymiel


def _gen_parallel_flag_name(sanitized_cnames):
    zoi__wsx = '_parallel_value'
    while zoi__wsx in sanitized_cnames:
        zoi__wsx = '_' + zoi__wsx
    return zoi__wsx


def _gen_csv_reader_py(col_names, col_typs, usecols, type_usecol_offset,
    sep, parallel, header, compression, is_skiprows_list, pd_low_memory,
    escapechar, idx_col_index=None, idx_col_typ=types.none):
    sanitized_cnames = [sanitize_varname(oslyd__qhfr) for oslyd__qhfr in
        col_names]
    suzy__ymiel = 'def csv_reader_py(fname, nrows, skiprows):\n'
    suzy__ymiel += _gen_csv_file_reader_init(parallel, header, compression,
        -1, is_skiprows_list, pd_low_memory)
    call_id = ir_utils.next_label()
    rtb__qqb = globals()
    if idx_col_typ != types.none:
        rtb__qqb[f'idx_array_typ'] = idx_col_typ
    if len(usecols) == 0:
        rtb__qqb[f'table_type_{call_id}'] = types.none
    else:
        rtb__qqb[f'table_type_{call_id}'] = TableType(tuple(col_typs))
    suzy__ymiel += _gen_read_csv_objmode(col_names, sanitized_cnames,
        col_typs, usecols, type_usecol_offset, sep, escapechar, call_id,
        rtb__qqb, parallel=parallel, check_parallel_runtime=False,
        idx_col_index=idx_col_index, idx_col_typ=idx_col_typ)
    if idx_col_index != None:
        suzy__ymiel += '  return (T, idx_arr)\n'
    else:
        suzy__ymiel += '  return (T, None)\n'
    bigjs__yymrf = {}
    exec(suzy__ymiel, rtb__qqb, bigjs__yymrf)
    lva__ejwv = bigjs__yymrf['csv_reader_py']
    kxot__how = numba.njit(lva__ejwv)
    compiled_funcs.append(kxot__how)
    return kxot__how
