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
    yzkkr__jmuyv = typemap[node.file_name.name]
    if types.unliteral(yzkkr__jmuyv) != types.unicode_type:
        raise BodoError(
            f"pd.read_csv(): 'filepath_or_buffer' must be a string. Found type: {yzkkr__jmuyv}."
            , node.file_name.loc)
    if not isinstance(node.skiprows, ir.Const):
        niz__weh = typemap[node.skiprows.name]
        if isinstance(niz__weh, types.Dispatcher):
            raise BodoError(
                f"pd.read_csv(): 'skiprows' callable not supported yet.",
                node.file_name.loc)
        elif not isinstance(niz__weh, types.Integer) and not (isinstance(
            niz__weh, (types.List, types.Tuple)) and isinstance(niz__weh.
            dtype, types.Integer)) and not isinstance(niz__weh, (types.
            LiteralList, bodo.utils.typing.ListLiteral)):
            raise BodoError(
                f"pd.read_csv(): 'skiprows' must be an integer or list of integers. Found type {niz__weh}."
                , loc=node.skiprows.loc)
        elif isinstance(niz__weh, (types.List, types.Tuple)):
            node.is_skiprows_list = True
    if not isinstance(node.nrows, ir.Const):
        vna__wzfe = typemap[node.nrows.name]
        if not isinstance(vna__wzfe, types.Integer):
            raise BodoError(
                f"pd.read_csv(): 'nrows' must be an integer. Found type {vna__wzfe}."
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
        ezr__upett = csv_node.out_vars[0]
        if ezr__upett.name not in lives:
            return None
    else:
        vcuo__gcr = csv_node.out_vars[0]
        mmpn__bfs = csv_node.out_vars[1]
        if vcuo__gcr.name not in lives and mmpn__bfs.name not in lives:
            return None
        elif mmpn__bfs.name not in lives:
            csv_node.index_column_index = None
            csv_node.index_column_typ = types.none
        elif vcuo__gcr.name not in lives:
            csv_node.usecols = []
            csv_node.out_types = []
            csv_node.type_usecol_offset = []
    return csv_node


def csv_distributed_run(csv_node, array_dists, typemap, calltypes,
    typingctx, targetctx):
    parallel = False
    niz__weh = types.int64 if isinstance(csv_node.skiprows, ir.Const
        ) else types.unliteral(typemap[csv_node.skiprows.name])
    if csv_node.chunksize is not None:
        if bodo.user_logging.get_verbose_level() >= 1:
            ovvsj__czzi = (
                'Finish column pruning on read_csv node:\n%s\nColumns loaded %s\n'
                )
            ckyeb__pczph = csv_node.loc.strformat()
            qrqsh__kxya = csv_node.df_colnames
            bodo.user_logging.log_message('Column Pruning', ovvsj__czzi,
                ckyeb__pczph, qrqsh__kxya)
            ggv__evm = csv_node.out_types[0].yield_type.data
            xzltf__aws = [bewab__ifcs for yoy__fzk, bewab__ifcs in
                enumerate(csv_node.df_colnames) if isinstance(ggv__evm[
                yoy__fzk], bodo.libs.dict_arr_ext.DictionaryArrayType)]
            if xzltf__aws:
                uqk__msj = """Finished optimized encoding on read_csv node:
%s
Columns %s using dictionary encoding to reduce memory usage.
"""
                bodo.user_logging.log_message('Dictionary Encoding',
                    uqk__msj, ckyeb__pczph, xzltf__aws)
        if array_dists is not None:
            imvvc__lrl = csv_node.out_vars[0].name
            parallel = array_dists[imvvc__lrl] in (distributed_pass.
                Distribution.OneD, distributed_pass.Distribution.OneD_Var)
        jadoj__fzp = 'def csv_iterator_impl(fname, nrows, skiprows):\n'
        jadoj__fzp += (
            f'    reader = _csv_reader_init(fname, nrows, skiprows)\n')
        jadoj__fzp += (
            f'    iterator = init_csv_iterator(reader, csv_iterator_type)\n')
        ylgh__ymj = {}
        from bodo.io.csv_iterator_ext import init_csv_iterator
        exec(jadoj__fzp, {}, ylgh__ymj)
        jvhh__fid = ylgh__ymj['csv_iterator_impl']
        sqcm__sjvpz = 'def csv_reader_init(fname, nrows, skiprows):\n'
        sqcm__sjvpz += _gen_csv_file_reader_init(parallel, csv_node.header,
            csv_node.compression, csv_node.chunksize, csv_node.
            is_skiprows_list, csv_node.pd_low_memory)
        sqcm__sjvpz += '  return f_reader\n'
        exec(sqcm__sjvpz, globals(), ylgh__ymj)
        xefea__uaa = ylgh__ymj['csv_reader_init']
        gds__jmvdj = numba.njit(xefea__uaa)
        compiled_funcs.append(gds__jmvdj)
        ufl__hxwga = compile_to_numba_ir(jvhh__fid, {'_csv_reader_init':
            gds__jmvdj, 'init_csv_iterator': init_csv_iterator,
            'csv_iterator_type': typemap[csv_node.out_vars[0].name]},
            typingctx=typingctx, targetctx=targetctx, arg_typs=(string_type,
            types.int64, niz__weh), typemap=typemap, calltypes=calltypes
            ).blocks.popitem()[1]
        replace_arg_nodes(ufl__hxwga, [csv_node.file_name, csv_node.nrows,
            csv_node.skiprows])
        zhb__mxqz = ufl__hxwga.body[:-3]
        zhb__mxqz[-1].target = csv_node.out_vars[0]
        return zhb__mxqz
    if array_dists is not None:
        een__aej = csv_node.out_vars[0].name
        parallel = array_dists[een__aej] in (distributed_pass.Distribution.
            OneD, distributed_pass.Distribution.OneD_Var)
        zgd__bixwf = csv_node.out_vars[1].name
        assert typemap[zgd__bixwf
            ] == types.none or not parallel or array_dists[zgd__bixwf] in (
            distributed_pass.Distribution.OneD, distributed_pass.
            Distribution.OneD_Var
            ), 'pq data/index parallelization does not match'
    jadoj__fzp = 'def csv_impl(fname, nrows, skiprows):\n'
    jadoj__fzp += (
        f'    (table_val, idx_col) = _csv_reader_py(fname, nrows, skiprows)\n')
    ylgh__ymj = {}
    exec(jadoj__fzp, {}, ylgh__ymj)
    mhxjt__npqu = ylgh__ymj['csv_impl']
    rhg__sdok = csv_node.usecols
    if rhg__sdok:
        rhg__sdok = [csv_node.usecols[yoy__fzk] for yoy__fzk in csv_node.
            type_usecol_offset]
    if bodo.user_logging.get_verbose_level() >= 1:
        ovvsj__czzi = (
            'Finish column pruning on read_csv node:\n%s\nColumns loaded %s\n')
        ckyeb__pczph = csv_node.loc.strformat()
        qrqsh__kxya = []
        xzltf__aws = []
        if rhg__sdok:
            for yoy__fzk in rhg__sdok:
                ewgz__jjhb = csv_node.df_colnames[yoy__fzk]
                qrqsh__kxya.append(ewgz__jjhb)
                if isinstance(csv_node.out_types[yoy__fzk], bodo.libs.
                    dict_arr_ext.DictionaryArrayType):
                    xzltf__aws.append(ewgz__jjhb)
        bodo.user_logging.log_message('Column Pruning', ovvsj__czzi,
            ckyeb__pczph, qrqsh__kxya)
        if xzltf__aws:
            uqk__msj = """Finished optimized encoding on read_csv node:
%s
Columns %s using dictionary encoding to reduce memory usage.
"""
            bodo.user_logging.log_message('Dictionary Encoding', uqk__msj,
                ckyeb__pczph, xzltf__aws)
    yuow__imjt = _gen_csv_reader_py(csv_node.df_colnames, csv_node.
        out_types, rhg__sdok, csv_node.type_usecol_offset, csv_node.sep,
        parallel, csv_node.header, csv_node.compression, csv_node.
        is_skiprows_list, csv_node.pd_low_memory, csv_node.escapechar,
        idx_col_index=csv_node.index_column_index, idx_col_typ=csv_node.
        index_column_typ)
    ufl__hxwga = compile_to_numba_ir(mhxjt__npqu, {'_csv_reader_py':
        yuow__imjt}, typingctx=typingctx, targetctx=targetctx, arg_typs=(
        string_type, types.int64, niz__weh), typemap=typemap, calltypes=
        calltypes).blocks.popitem()[1]
    replace_arg_nodes(ufl__hxwga, [csv_node.file_name, csv_node.nrows,
        csv_node.skiprows, csv_node.is_skiprows_list])
    zhb__mxqz = ufl__hxwga.body[:-3]
    zhb__mxqz[-1].target = csv_node.out_vars[1]
    zhb__mxqz[-2].target = csv_node.out_vars[0]
    if csv_node.index_column_index is None:
        zhb__mxqz.pop(-1)
    elif not rhg__sdok:
        zhb__mxqz.pop(-2)
    return zhb__mxqz


def csv_remove_dead_column(csv_node, column_live_map, equiv_vars, typemap):
    if csv_node.chunksize is not None:
        return False
    assert len(csv_node.out_vars) == 2, 'invalid CsvReader node'
    guaf__jpu = csv_node.out_vars[0].name
    if isinstance(typemap[guaf__jpu], TableType) and csv_node.usecols:
        yvg__llu, cwzf__cbau = get_live_column_nums_block(column_live_map,
            equiv_vars, guaf__jpu)
        yvg__llu = bodo.ir.connector.trim_extra_used_columns(yvg__llu, len(
            csv_node.usecols))
        if not cwzf__cbau and not yvg__llu:
            yvg__llu = [0]
        if not cwzf__cbau and len(yvg__llu) != len(csv_node.type_usecol_offset
            ):
            csv_node.type_usecol_offset = yvg__llu
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
    tiw__wyr = t.dtype
    if isinstance(tiw__wyr, PDCategoricalDtype):
        kfqk__bpenb = CategoricalArrayType(tiw__wyr)
        ltw__ozu = 'CategoricalArrayType' + str(ir_utils.next_label())
        setattr(types, ltw__ozu, kfqk__bpenb)
        return ltw__ozu
    if tiw__wyr == types.NPDatetime('ns'):
        tiw__wyr = 'NPDatetime("ns")'
    if t == string_array_type:
        types.string_array_type = string_array_type
        return 'string_array_type'
    if isinstance(t, IntegerArrayType):
        grvev__lcizm = 'int_arr_{}'.format(tiw__wyr)
        setattr(types, grvev__lcizm, t)
        return grvev__lcizm
    if t == boolean_array:
        types.boolean_array = boolean_array
        return 'boolean_array'
    if tiw__wyr == types.bool_:
        tiw__wyr = 'bool_'
    if tiw__wyr == datetime_date_type:
        return 'datetime_date_array_type'
    if isinstance(t, ArrayItemArrayType) and isinstance(tiw__wyr, (
        StringArrayType, ArrayItemArrayType)):
        ivgu__ogl = f'ArrayItemArrayType{str(ir_utils.next_label())}'
        setattr(types, ivgu__ogl, t)
        return ivgu__ogl
    return '{}[::1]'.format(tiw__wyr)


def _get_pd_dtype_str(t):
    tiw__wyr = t.dtype
    if isinstance(tiw__wyr, PDCategoricalDtype):
        return 'pd.CategoricalDtype({})'.format(tiw__wyr.categories)
    if tiw__wyr == types.NPDatetime('ns'):
        return 'str'
    if t == string_array_type:
        return 'str'
    if isinstance(t, IntegerArrayType):
        return '"{}Int{}"'.format('' if tiw__wyr.signed else 'U', tiw__wyr.
            bitwidth)
    if t == boolean_array:
        return 'np.bool_'
    if isinstance(t, ArrayItemArrayType) and isinstance(tiw__wyr, (
        StringArrayType, ArrayItemArrayType)):
        return 'object'
    return 'np.{}'.format(tiw__wyr)


compiled_funcs = []


@numba.njit
def check_nrows_skiprows_value(nrows, skiprows):
    if nrows < -1:
        raise ValueError('pd.read_csv: nrows must be integer >= 0.')
    if skiprows[0] < 0:
        raise ValueError('pd.read_csv: skiprows must be integer >= 0.')


def astype(df, typemap, parallel):
    rfa__lbxz = ''
    from collections import defaultdict
    kugw__geo = defaultdict(list)
    for debkg__bqko, sbrk__webc in typemap.items():
        kugw__geo[sbrk__webc].append(debkg__bqko)
    rrrqg__fgfbh = df.columns.to_list()
    pvi__pha = []
    for sbrk__webc, czdxz__pdme in kugw__geo.items():
        try:
            pvi__pha.append(df.loc[:, czdxz__pdme].astype(sbrk__webc, copy=
                False))
            df = df.drop(czdxz__pdme, axis=1)
        except (ValueError, TypeError) as rpna__qjri:
            rfa__lbxz = (
                f"Caught the runtime error '{rpna__qjri}' on columns {czdxz__pdme}. Consider setting the 'dtype' argument in 'read_csv' or investigate if the data is corrupted."
                )
            break
    hsbe__nqh = bool(rfa__lbxz)
    if parallel:
        ptx__mprq = MPI.COMM_WORLD
        hsbe__nqh = ptx__mprq.allreduce(hsbe__nqh, op=MPI.LOR)
    if hsbe__nqh:
        bgu__iyp = 'pd.read_csv(): Bodo could not infer dtypes correctly.'
        if rfa__lbxz:
            raise TypeError(f'{bgu__iyp}\n{rfa__lbxz}')
        else:
            raise TypeError(
                f'{bgu__iyp}\nPlease refer to errors on other ranks.')
    df = pd.concat(pvi__pha + [df], axis=1)
    mpggl__ohs = df.loc[:, rrrqg__fgfbh]
    return mpggl__ohs


def _gen_csv_file_reader_init(parallel, header, compression, chunksize,
    is_skiprows_list, pd_low_memory):
    dryy__usay = header == 0
    if compression is None:
        compression = 'uncompressed'
    if is_skiprows_list:
        jadoj__fzp = '  skiprows = sorted(set(skiprows))\n'
    else:
        jadoj__fzp = '  skiprows = [skiprows]\n'
    jadoj__fzp += '  skiprows_list_len = len(skiprows)\n'
    jadoj__fzp += '  check_nrows_skiprows_value(nrows, skiprows)\n'
    jadoj__fzp += '  check_java_installation(fname)\n'
    jadoj__fzp += f"""  bucket_region = bodo.io.fs_io.get_s3_bucket_region_njit(fname, parallel={parallel})
"""
    jadoj__fzp += (
        '  f_reader = bodo.ir.csv_ext.csv_file_chunk_reader(bodo.libs.str_ext.unicode_to_utf8(fname), '
        )
    jadoj__fzp += (
        """    {}, bodo.utils.conversion.coerce_to_ndarray(skiprows, scalar_to_arr_len=1).ctypes, nrows, {}, bodo.libs.str_ext.unicode_to_utf8('{}'), bodo.libs.str_ext.unicode_to_utf8(bucket_region), {}, {}, skiprows_list_len, {})
"""
        .format(parallel, dryy__usay, compression, chunksize,
        is_skiprows_list, pd_low_memory))
    jadoj__fzp += '  bodo.utils.utils.check_and_propagate_cpp_exception()\n'
    jadoj__fzp += '  if bodo.utils.utils.is_null_pointer(f_reader):\n'
    jadoj__fzp += "      raise FileNotFoundError('File does not exist')\n"
    return jadoj__fzp


def _gen_read_csv_objmode(col_names, sanitized_cnames, col_typs, usecols,
    type_usecol_offset, sep, escapechar, call_id, glbs, parallel,
    check_parallel_runtime, idx_col_index, idx_col_typ):
    oye__qkri = [str(zzk__zhnw) for yoy__fzk, zzk__zhnw in enumerate(
        usecols) if col_typs[type_usecol_offset[yoy__fzk]].dtype == types.
        NPDatetime('ns')]
    if idx_col_typ == types.NPDatetime('ns'):
        assert not idx_col_index is None
        oye__qkri.append(str(idx_col_index))
    zvzq__ukaj = ', '.join(oye__qkri)
    axnt__pwm = _gen_parallel_flag_name(sanitized_cnames)
    duj__ghkcn = f"{axnt__pwm}='bool_'" if check_parallel_runtime else ''
    nrd__kbso = [_get_pd_dtype_str(col_typs[type_usecol_offset[yoy__fzk]]) for
        yoy__fzk in range(len(usecols))]
    akgk__ovotv = None if idx_col_index is None else _get_pd_dtype_str(
        idx_col_typ)
    nsjlo__wgv = [zzk__zhnw for yoy__fzk, zzk__zhnw in enumerate(usecols) if
        nrd__kbso[yoy__fzk] == 'str']
    if idx_col_index is not None and akgk__ovotv == 'str':
        nsjlo__wgv.append(idx_col_index)
    yuqn__wka = np.array(nsjlo__wgv, dtype=np.int64)
    glbs[f'str_col_nums_{call_id}'] = yuqn__wka
    jadoj__fzp = f'  str_col_nums_{call_id}_2 = str_col_nums_{call_id}\n'
    mzge__pgff = np.array(usecols + ([idx_col_index] if idx_col_index is not
        None else []))
    glbs[f'usecols_arr_{call_id}'] = mzge__pgff
    jadoj__fzp += f'  usecols_arr_{call_id}_2 = usecols_arr_{call_id}\n'
    ibf__rbe = np.array(type_usecol_offset, dtype=np.int64)
    if usecols:
        glbs[f'type_usecols_offsets_arr_{call_id}'] = ibf__rbe
        jadoj__fzp += f"""  type_usecols_offsets_arr_{call_id}_2 = type_usecols_offsets_arr_{call_id}
"""
    cdjeh__yff = defaultdict(list)
    for yoy__fzk, zzk__zhnw in enumerate(usecols):
        if nrd__kbso[yoy__fzk] == 'str':
            continue
        cdjeh__yff[nrd__kbso[yoy__fzk]].append(zzk__zhnw)
    if idx_col_index is not None and akgk__ovotv != 'str':
        cdjeh__yff[akgk__ovotv].append(idx_col_index)
    for yoy__fzk, lgkcw__xeupx in enumerate(cdjeh__yff.values()):
        glbs[f't_arr_{yoy__fzk}_{call_id}'] = np.asarray(lgkcw__xeupx)
        jadoj__fzp += (
            f'  t_arr_{yoy__fzk}_{call_id}_2 = t_arr_{yoy__fzk}_{call_id}\n')
    if idx_col_index != None:
        jadoj__fzp += f"""  with objmode(T=table_type_{call_id}, idx_arr=idx_array_typ, {duj__ghkcn}):
"""
    else:
        jadoj__fzp += (
            f'  with objmode(T=table_type_{call_id}, {duj__ghkcn}):\n')
    jadoj__fzp += f'    typemap = {{}}\n'
    for yoy__fzk, bxx__ertmb in enumerate(cdjeh__yff.keys()):
        jadoj__fzp += f"""    typemap.update({{i:{bxx__ertmb} for i in t_arr_{yoy__fzk}_{call_id}_2}})
"""
    jadoj__fzp += '    if f_reader.get_chunk_size() == 0:\n'
    jadoj__fzp += (
        f'      df = pd.DataFrame(columns=usecols_arr_{call_id}_2, dtype=str)\n'
        )
    jadoj__fzp += '    else:\n'
    jadoj__fzp += '      df = pd.read_csv(f_reader,\n'
    jadoj__fzp += '        header=None,\n'
    jadoj__fzp += '        parse_dates=[{}],\n'.format(zvzq__ukaj)
    jadoj__fzp += (
        f'        dtype={{i:str for i in str_col_nums_{call_id}_2}},\n')
    jadoj__fzp += f"""        usecols=usecols_arr_{call_id}_2, sep={sep!r}, low_memory=False, escapechar={escapechar!r})
"""
    if check_parallel_runtime:
        jadoj__fzp += f'    {axnt__pwm} = f_reader.is_parallel()\n'
    else:
        jadoj__fzp += f'    {axnt__pwm} = {parallel}\n'
    jadoj__fzp += f'    df = astype(df, typemap, {axnt__pwm})\n'
    if idx_col_index != None:
        nqd__zhji = sorted(mzge__pgff).index(idx_col_index)
        jadoj__fzp += f'    idx_arr = df.iloc[:, {nqd__zhji}].values\n'
        jadoj__fzp += (
            f'    df.drop(columns=df.columns[{nqd__zhji}], inplace=True)\n')
    if len(usecols) == 0:
        jadoj__fzp += f'    T = None\n'
    else:
        jadoj__fzp += f'    arrs = []\n'
        jadoj__fzp += f'    for i in range(df.shape[1]):\n'
        jadoj__fzp += f'      arrs.append(df.iloc[:, i].values)\n'
        jadoj__fzp += f"""    T = Table(arrs, type_usecols_offsets_arr_{call_id}_2, {len(col_names)})
"""
    return jadoj__fzp


def _gen_parallel_flag_name(sanitized_cnames):
    axnt__pwm = '_parallel_value'
    while axnt__pwm in sanitized_cnames:
        axnt__pwm = '_' + axnt__pwm
    return axnt__pwm


def _gen_csv_reader_py(col_names, col_typs, usecols, type_usecol_offset,
    sep, parallel, header, compression, is_skiprows_list, pd_low_memory,
    escapechar, idx_col_index=None, idx_col_typ=types.none):
    sanitized_cnames = [sanitize_varname(bewab__ifcs) for bewab__ifcs in
        col_names]
    jadoj__fzp = 'def csv_reader_py(fname, nrows, skiprows):\n'
    jadoj__fzp += _gen_csv_file_reader_init(parallel, header, compression, 
        -1, is_skiprows_list, pd_low_memory)
    call_id = ir_utils.next_label()
    wlvs__ujx = globals()
    if idx_col_typ != types.none:
        wlvs__ujx[f'idx_array_typ'] = idx_col_typ
    if len(usecols) == 0:
        wlvs__ujx[f'table_type_{call_id}'] = types.none
    else:
        wlvs__ujx[f'table_type_{call_id}'] = TableType(tuple(col_typs))
    jadoj__fzp += _gen_read_csv_objmode(col_names, sanitized_cnames,
        col_typs, usecols, type_usecol_offset, sep, escapechar, call_id,
        wlvs__ujx, parallel=parallel, check_parallel_runtime=False,
        idx_col_index=idx_col_index, idx_col_typ=idx_col_typ)
    if idx_col_index != None:
        jadoj__fzp += '  return (T, idx_arr)\n'
    else:
        jadoj__fzp += '  return (T, None)\n'
    ylgh__ymj = {}
    exec(jadoj__fzp, wlvs__ujx, ylgh__ymj)
    yuow__imjt = ylgh__ymj['csv_reader_py']
    gds__jmvdj = numba.njit(yuow__imjt)
    compiled_funcs.append(gds__jmvdj)
    return gds__jmvdj
