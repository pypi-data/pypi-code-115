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
    awhh__zimz = typemap[node.file_name.name]
    if types.unliteral(awhh__zimz) != types.unicode_type:
        raise BodoError(
            f"pd.read_csv(): 'filepath_or_buffer' must be a string. Found type: {awhh__zimz}."
            , node.file_name.loc)
    if not isinstance(node.skiprows, ir.Const):
        czn__dphvj = typemap[node.skiprows.name]
        if isinstance(czn__dphvj, types.Dispatcher):
            raise BodoError(
                f"pd.read_csv(): 'skiprows' callable not supported yet.",
                node.file_name.loc)
        elif not isinstance(czn__dphvj, types.Integer) and not (isinstance(
            czn__dphvj, (types.List, types.Tuple)) and isinstance(
            czn__dphvj.dtype, types.Integer)) and not isinstance(czn__dphvj,
            (types.LiteralList, bodo.utils.typing.ListLiteral)):
            raise BodoError(
                f"pd.read_csv(): 'skiprows' must be an integer or list of integers. Found type {czn__dphvj}."
                , loc=node.skiprows.loc)
        elif isinstance(czn__dphvj, (types.List, types.Tuple)):
            node.is_skiprows_list = True
    if not isinstance(node.nrows, ir.Const):
        zgecc__cls = typemap[node.nrows.name]
        if not isinstance(zgecc__cls, types.Integer):
            raise BodoError(
                f"pd.read_csv(): 'nrows' must be an integer. Found type {zgecc__cls}."
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
        pzzah__ectok = csv_node.out_vars[0]
        if pzzah__ectok.name not in lives:
            return None
    else:
        gmyya__cgw = csv_node.out_vars[0]
        lfyh__fjd = csv_node.out_vars[1]
        if gmyya__cgw.name not in lives and lfyh__fjd.name not in lives:
            return None
        elif lfyh__fjd.name not in lives:
            csv_node.index_column_index = None
            csv_node.index_column_typ = types.none
        elif gmyya__cgw.name not in lives:
            csv_node.usecols = []
            csv_node.out_types = []
            csv_node.type_usecol_offset = []
    return csv_node


def csv_distributed_run(csv_node, array_dists, typemap, calltypes,
    typingctx, targetctx):
    parallel = False
    czn__dphvj = types.int64 if isinstance(csv_node.skiprows, ir.Const
        ) else types.unliteral(typemap[csv_node.skiprows.name])
    if csv_node.chunksize is not None:
        if bodo.user_logging.get_verbose_level() >= 1:
            ldmj__qnky = (
                'Finish column pruning on read_csv node:\n%s\nColumns loaded %s\n'
                )
            pzik__qxcxi = csv_node.loc.strformat()
            legr__nnw = csv_node.df_colnames
            bodo.user_logging.log_message('Column Pruning', ldmj__qnky,
                pzik__qxcxi, legr__nnw)
            otrx__bss = csv_node.out_types[0].yield_type.data
            exia__whi = [xpvpr__jyj for bkorv__umjlp, xpvpr__jyj in
                enumerate(csv_node.df_colnames) if isinstance(otrx__bss[
                bkorv__umjlp], bodo.libs.dict_arr_ext.DictionaryArrayType)]
            if exia__whi:
                iedp__wfo = """Finished optimized encoding on read_csv node:
%s
Columns %s using dictionary encoding to reduce memory usage.
"""
                bodo.user_logging.log_message('Dictionary Encoding',
                    iedp__wfo, pzik__qxcxi, exia__whi)
        if array_dists is not None:
            qrnu__glld = csv_node.out_vars[0].name
            parallel = array_dists[qrnu__glld] in (distributed_pass.
                Distribution.OneD, distributed_pass.Distribution.OneD_Var)
        zspqa__mtdiz = 'def csv_iterator_impl(fname, nrows, skiprows):\n'
        zspqa__mtdiz += (
            f'    reader = _csv_reader_init(fname, nrows, skiprows)\n')
        zspqa__mtdiz += (
            f'    iterator = init_csv_iterator(reader, csv_iterator_type)\n')
        iiwal__yzpjk = {}
        from bodo.io.csv_iterator_ext import init_csv_iterator
        exec(zspqa__mtdiz, {}, iiwal__yzpjk)
        mtvfc__mwbzg = iiwal__yzpjk['csv_iterator_impl']
        tiu__rnm = 'def csv_reader_init(fname, nrows, skiprows):\n'
        tiu__rnm += _gen_csv_file_reader_init(parallel, csv_node.header,
            csv_node.compression, csv_node.chunksize, csv_node.
            is_skiprows_list, csv_node.pd_low_memory)
        tiu__rnm += '  return f_reader\n'
        exec(tiu__rnm, globals(), iiwal__yzpjk)
        ayvsm__npkm = iiwal__yzpjk['csv_reader_init']
        bqsz__twklh = numba.njit(ayvsm__npkm)
        compiled_funcs.append(bqsz__twklh)
        azzl__nvlks = compile_to_numba_ir(mtvfc__mwbzg, {'_csv_reader_init':
            bqsz__twklh, 'init_csv_iterator': init_csv_iterator,
            'csv_iterator_type': typemap[csv_node.out_vars[0].name]},
            typingctx=typingctx, targetctx=targetctx, arg_typs=(string_type,
            types.int64, czn__dphvj), typemap=typemap, calltypes=calltypes
            ).blocks.popitem()[1]
        replace_arg_nodes(azzl__nvlks, [csv_node.file_name, csv_node.nrows,
            csv_node.skiprows])
        ibesm__qlav = azzl__nvlks.body[:-3]
        ibesm__qlav[-1].target = csv_node.out_vars[0]
        return ibesm__qlav
    if array_dists is not None:
        aet__yhnh = csv_node.out_vars[0].name
        parallel = array_dists[aet__yhnh] in (distributed_pass.Distribution
            .OneD, distributed_pass.Distribution.OneD_Var)
        zncd__swlp = csv_node.out_vars[1].name
        assert typemap[zncd__swlp
            ] == types.none or not parallel or array_dists[zncd__swlp] in (
            distributed_pass.Distribution.OneD, distributed_pass.
            Distribution.OneD_Var
            ), 'pq data/index parallelization does not match'
    zspqa__mtdiz = 'def csv_impl(fname, nrows, skiprows):\n'
    zspqa__mtdiz += (
        f'    (table_val, idx_col) = _csv_reader_py(fname, nrows, skiprows)\n')
    iiwal__yzpjk = {}
    exec(zspqa__mtdiz, {}, iiwal__yzpjk)
    rhc__sdfi = iiwal__yzpjk['csv_impl']
    vmap__ihx = csv_node.usecols
    if vmap__ihx:
        vmap__ihx = [csv_node.usecols[bkorv__umjlp] for bkorv__umjlp in
            csv_node.type_usecol_offset]
    if bodo.user_logging.get_verbose_level() >= 1:
        ldmj__qnky = (
            'Finish column pruning on read_csv node:\n%s\nColumns loaded %s\n')
        pzik__qxcxi = csv_node.loc.strformat()
        legr__nnw = []
        exia__whi = []
        if vmap__ihx:
            for bkorv__umjlp in vmap__ihx:
                qyozf__nqs = csv_node.df_colnames[bkorv__umjlp]
                legr__nnw.append(qyozf__nqs)
                if isinstance(csv_node.out_types[bkorv__umjlp], bodo.libs.
                    dict_arr_ext.DictionaryArrayType):
                    exia__whi.append(qyozf__nqs)
        bodo.user_logging.log_message('Column Pruning', ldmj__qnky,
            pzik__qxcxi, legr__nnw)
        if exia__whi:
            iedp__wfo = """Finished optimized encoding on read_csv node:
%s
Columns %s using dictionary encoding to reduce memory usage.
"""
            bodo.user_logging.log_message('Dictionary Encoding', iedp__wfo,
                pzik__qxcxi, exia__whi)
    vtbjx__vrfk = _gen_csv_reader_py(csv_node.df_colnames, csv_node.
        out_types, vmap__ihx, csv_node.type_usecol_offset, csv_node.sep,
        parallel, csv_node.header, csv_node.compression, csv_node.
        is_skiprows_list, csv_node.pd_low_memory, csv_node.escapechar,
        idx_col_index=csv_node.index_column_index, idx_col_typ=csv_node.
        index_column_typ)
    azzl__nvlks = compile_to_numba_ir(rhc__sdfi, {'_csv_reader_py':
        vtbjx__vrfk}, typingctx=typingctx, targetctx=targetctx, arg_typs=(
        string_type, types.int64, czn__dphvj), typemap=typemap, calltypes=
        calltypes).blocks.popitem()[1]
    replace_arg_nodes(azzl__nvlks, [csv_node.file_name, csv_node.nrows,
        csv_node.skiprows, csv_node.is_skiprows_list])
    ibesm__qlav = azzl__nvlks.body[:-3]
    ibesm__qlav[-1].target = csv_node.out_vars[1]
    ibesm__qlav[-2].target = csv_node.out_vars[0]
    if csv_node.index_column_index is None:
        ibesm__qlav.pop(-1)
    elif not vmap__ihx:
        ibesm__qlav.pop(-2)
    return ibesm__qlav


def csv_remove_dead_column(csv_node, column_live_map, equiv_vars, typemap):
    if csv_node.chunksize is not None:
        return False
    assert len(csv_node.out_vars) == 2, 'invalid CsvReader node'
    ylwsg__tcq = csv_node.out_vars[0].name
    if isinstance(typemap[ylwsg__tcq], TableType) and csv_node.usecols:
        eurt__cijn, psxgy__fwyc = get_live_column_nums_block(column_live_map,
            equiv_vars, ylwsg__tcq)
        eurt__cijn = bodo.ir.connector.trim_extra_used_columns(eurt__cijn,
            len(csv_node.usecols))
        if not psxgy__fwyc and not eurt__cijn:
            eurt__cijn = [0]
        if not psxgy__fwyc and len(eurt__cijn) != len(csv_node.
            type_usecol_offset):
            csv_node.type_usecol_offset = eurt__cijn
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
    spps__luqid = t.dtype
    if isinstance(spps__luqid, PDCategoricalDtype):
        ckzs__nis = CategoricalArrayType(spps__luqid)
        dvmty__kwshd = 'CategoricalArrayType' + str(ir_utils.next_label())
        setattr(types, dvmty__kwshd, ckzs__nis)
        return dvmty__kwshd
    if spps__luqid == types.NPDatetime('ns'):
        spps__luqid = 'NPDatetime("ns")'
    if t == string_array_type:
        types.string_array_type = string_array_type
        return 'string_array_type'
    if isinstance(t, IntegerArrayType):
        qdg__ieont = 'int_arr_{}'.format(spps__luqid)
        setattr(types, qdg__ieont, t)
        return qdg__ieont
    if t == boolean_array:
        types.boolean_array = boolean_array
        return 'boolean_array'
    if spps__luqid == types.bool_:
        spps__luqid = 'bool_'
    if spps__luqid == datetime_date_type:
        return 'datetime_date_array_type'
    if isinstance(t, ArrayItemArrayType) and isinstance(spps__luqid, (
        StringArrayType, ArrayItemArrayType)):
        seag__pau = f'ArrayItemArrayType{str(ir_utils.next_label())}'
        setattr(types, seag__pau, t)
        return seag__pau
    return '{}[::1]'.format(spps__luqid)


def _get_pd_dtype_str(t):
    spps__luqid = t.dtype
    if isinstance(spps__luqid, PDCategoricalDtype):
        return 'pd.CategoricalDtype({})'.format(spps__luqid.categories)
    if spps__luqid == types.NPDatetime('ns'):
        return 'str'
    if t == string_array_type:
        return 'str'
    if isinstance(t, IntegerArrayType):
        return '"{}Int{}"'.format('' if spps__luqid.signed else 'U',
            spps__luqid.bitwidth)
    if t == boolean_array:
        return 'np.bool_'
    if isinstance(t, ArrayItemArrayType) and isinstance(spps__luqid, (
        StringArrayType, ArrayItemArrayType)):
        return 'object'
    return 'np.{}'.format(spps__luqid)


compiled_funcs = []


@numba.njit
def check_nrows_skiprows_value(nrows, skiprows):
    if nrows < -1:
        raise ValueError('pd.read_csv: nrows must be integer >= 0.')
    if skiprows[0] < 0:
        raise ValueError('pd.read_csv: skiprows must be integer >= 0.')


def astype(df, typemap, parallel):
    zbb__nrpru = ''
    from collections import defaultdict
    pka__kjv = defaultdict(list)
    for jimlg__kfb, otq__cbex in typemap.items():
        pka__kjv[otq__cbex].append(jimlg__kfb)
    nkily__qdbu = df.columns.to_list()
    bteh__ssb = []
    for otq__cbex, iutia__lomv in pka__kjv.items():
        try:
            bteh__ssb.append(df.loc[:, iutia__lomv].astype(otq__cbex, copy=
                False))
            df = df.drop(iutia__lomv, axis=1)
        except (ValueError, TypeError) as tcjl__ahgag:
            zbb__nrpru = (
                f"Caught the runtime error '{tcjl__ahgag}' on columns {iutia__lomv}. Consider setting the 'dtype' argument in 'read_csv' or investigate if the data is corrupted."
                )
            break
    pnd__ikc = bool(zbb__nrpru)
    if parallel:
        fha__ego = MPI.COMM_WORLD
        pnd__ikc = fha__ego.allreduce(pnd__ikc, op=MPI.LOR)
    if pnd__ikc:
        ljz__onaen = 'pd.read_csv(): Bodo could not infer dtypes correctly.'
        if zbb__nrpru:
            raise TypeError(f'{ljz__onaen}\n{zbb__nrpru}')
        else:
            raise TypeError(
                f'{ljz__onaen}\nPlease refer to errors on other ranks.')
    df = pd.concat(bteh__ssb + [df], axis=1)
    aulv__foqkw = df.loc[:, nkily__qdbu]
    return aulv__foqkw


def _gen_csv_file_reader_init(parallel, header, compression, chunksize,
    is_skiprows_list, pd_low_memory):
    vutf__vlipr = header == 0
    if compression is None:
        compression = 'uncompressed'
    if is_skiprows_list:
        zspqa__mtdiz = '  skiprows = sorted(set(skiprows))\n'
    else:
        zspqa__mtdiz = '  skiprows = [skiprows]\n'
    zspqa__mtdiz += '  skiprows_list_len = len(skiprows)\n'
    zspqa__mtdiz += '  check_nrows_skiprows_value(nrows, skiprows)\n'
    zspqa__mtdiz += '  check_java_installation(fname)\n'
    zspqa__mtdiz += f"""  bucket_region = bodo.io.fs_io.get_s3_bucket_region_njit(fname, parallel={parallel})
"""
    zspqa__mtdiz += (
        '  f_reader = bodo.ir.csv_ext.csv_file_chunk_reader(bodo.libs.str_ext.unicode_to_utf8(fname), '
        )
    zspqa__mtdiz += (
        """    {}, bodo.utils.conversion.coerce_to_ndarray(skiprows, scalar_to_arr_len=1).ctypes, nrows, {}, bodo.libs.str_ext.unicode_to_utf8('{}'), bodo.libs.str_ext.unicode_to_utf8(bucket_region), {}, {}, skiprows_list_len, {})
"""
        .format(parallel, vutf__vlipr, compression, chunksize,
        is_skiprows_list, pd_low_memory))
    zspqa__mtdiz += '  bodo.utils.utils.check_and_propagate_cpp_exception()\n'
    zspqa__mtdiz += '  if bodo.utils.utils.is_null_pointer(f_reader):\n'
    zspqa__mtdiz += "      raise FileNotFoundError('File does not exist')\n"
    return zspqa__mtdiz


def _gen_read_csv_objmode(col_names, sanitized_cnames, col_typs, usecols,
    type_usecol_offset, sep, escapechar, call_id, glbs, parallel,
    check_parallel_runtime, idx_col_index, idx_col_typ):
    kqmx__sozz = [str(kvt__behmf) for bkorv__umjlp, kvt__behmf in enumerate
        (usecols) if col_typs[type_usecol_offset[bkorv__umjlp]].dtype ==
        types.NPDatetime('ns')]
    if idx_col_typ == types.NPDatetime('ns'):
        assert not idx_col_index is None
        kqmx__sozz.append(str(idx_col_index))
    tvo__sqr = ', '.join(kqmx__sozz)
    tttg__cllm = _gen_parallel_flag_name(sanitized_cnames)
    grgwj__xwvp = f"{tttg__cllm}='bool_'" if check_parallel_runtime else ''
    hbj__uurk = [_get_pd_dtype_str(col_typs[type_usecol_offset[bkorv__umjlp
        ]]) for bkorv__umjlp in range(len(usecols))]
    kkd__skleg = None if idx_col_index is None else _get_pd_dtype_str(
        idx_col_typ)
    ybec__cblm = [kvt__behmf for bkorv__umjlp, kvt__behmf in enumerate(
        usecols) if hbj__uurk[bkorv__umjlp] == 'str']
    if idx_col_index is not None and kkd__skleg == 'str':
        ybec__cblm.append(idx_col_index)
    hszc__xcmc = np.array(ybec__cblm, dtype=np.int64)
    glbs[f'str_col_nums_{call_id}'] = hszc__xcmc
    zspqa__mtdiz = f'  str_col_nums_{call_id}_2 = str_col_nums_{call_id}\n'
    jhx__nhqiw = np.array(usecols + ([idx_col_index] if idx_col_index is not
        None else []))
    glbs[f'usecols_arr_{call_id}'] = jhx__nhqiw
    zspqa__mtdiz += f'  usecols_arr_{call_id}_2 = usecols_arr_{call_id}\n'
    seu__dszgr = np.array(type_usecol_offset, dtype=np.int64)
    if usecols:
        glbs[f'type_usecols_offsets_arr_{call_id}'] = seu__dszgr
        zspqa__mtdiz += f"""  type_usecols_offsets_arr_{call_id}_2 = type_usecols_offsets_arr_{call_id}
"""
    cvao__xlnb = defaultdict(list)
    for bkorv__umjlp, kvt__behmf in enumerate(usecols):
        if hbj__uurk[bkorv__umjlp] == 'str':
            continue
        cvao__xlnb[hbj__uurk[bkorv__umjlp]].append(kvt__behmf)
    if idx_col_index is not None and kkd__skleg != 'str':
        cvao__xlnb[kkd__skleg].append(idx_col_index)
    for bkorv__umjlp, dlb__gszun in enumerate(cvao__xlnb.values()):
        glbs[f't_arr_{bkorv__umjlp}_{call_id}'] = np.asarray(dlb__gszun)
        zspqa__mtdiz += (
            f'  t_arr_{bkorv__umjlp}_{call_id}_2 = t_arr_{bkorv__umjlp}_{call_id}\n'
            )
    if idx_col_index != None:
        zspqa__mtdiz += f"""  with objmode(T=table_type_{call_id}, idx_arr=idx_array_typ, {grgwj__xwvp}):
"""
    else:
        zspqa__mtdiz += (
            f'  with objmode(T=table_type_{call_id}, {grgwj__xwvp}):\n')
    zspqa__mtdiz += f'    typemap = {{}}\n'
    for bkorv__umjlp, xih__ilifk in enumerate(cvao__xlnb.keys()):
        zspqa__mtdiz += f"""    typemap.update({{i:{xih__ilifk} for i in t_arr_{bkorv__umjlp}_{call_id}_2}})
"""
    zspqa__mtdiz += '    if f_reader.get_chunk_size() == 0:\n'
    zspqa__mtdiz += (
        f'      df = pd.DataFrame(columns=usecols_arr_{call_id}_2, dtype=str)\n'
        )
    zspqa__mtdiz += '    else:\n'
    zspqa__mtdiz += '      df = pd.read_csv(f_reader,\n'
    zspqa__mtdiz += '        header=None,\n'
    zspqa__mtdiz += '        parse_dates=[{}],\n'.format(tvo__sqr)
    zspqa__mtdiz += (
        f'        dtype={{i:str for i in str_col_nums_{call_id}_2}},\n')
    zspqa__mtdiz += f"""        usecols=usecols_arr_{call_id}_2, sep={sep!r}, low_memory=False, escapechar={escapechar!r})
"""
    if check_parallel_runtime:
        zspqa__mtdiz += f'    {tttg__cllm} = f_reader.is_parallel()\n'
    else:
        zspqa__mtdiz += f'    {tttg__cllm} = {parallel}\n'
    zspqa__mtdiz += f'    df = astype(df, typemap, {tttg__cllm})\n'
    if idx_col_index != None:
        mmbg__tqua = sorted(jhx__nhqiw).index(idx_col_index)
        zspqa__mtdiz += f'    idx_arr = df.iloc[:, {mmbg__tqua}].values\n'
        zspqa__mtdiz += (
            f'    df.drop(columns=df.columns[{mmbg__tqua}], inplace=True)\n')
    if len(usecols) == 0:
        zspqa__mtdiz += f'    T = None\n'
    else:
        zspqa__mtdiz += f'    arrs = []\n'
        zspqa__mtdiz += f'    for i in range(df.shape[1]):\n'
        zspqa__mtdiz += f'      arrs.append(df.iloc[:, i].values)\n'
        zspqa__mtdiz += f"""    T = Table(arrs, type_usecols_offsets_arr_{call_id}_2, {len(col_names)})
"""
    return zspqa__mtdiz


def _gen_parallel_flag_name(sanitized_cnames):
    tttg__cllm = '_parallel_value'
    while tttg__cllm in sanitized_cnames:
        tttg__cllm = '_' + tttg__cllm
    return tttg__cllm


def _gen_csv_reader_py(col_names, col_typs, usecols, type_usecol_offset,
    sep, parallel, header, compression, is_skiprows_list, pd_low_memory,
    escapechar, idx_col_index=None, idx_col_typ=types.none):
    sanitized_cnames = [sanitize_varname(xpvpr__jyj) for xpvpr__jyj in
        col_names]
    zspqa__mtdiz = 'def csv_reader_py(fname, nrows, skiprows):\n'
    zspqa__mtdiz += _gen_csv_file_reader_init(parallel, header, compression,
        -1, is_skiprows_list, pd_low_memory)
    call_id = ir_utils.next_label()
    wfeo__smfvj = globals()
    if idx_col_typ != types.none:
        wfeo__smfvj[f'idx_array_typ'] = idx_col_typ
    if len(usecols) == 0:
        wfeo__smfvj[f'table_type_{call_id}'] = types.none
    else:
        wfeo__smfvj[f'table_type_{call_id}'] = TableType(tuple(col_typs))
    zspqa__mtdiz += _gen_read_csv_objmode(col_names, sanitized_cnames,
        col_typs, usecols, type_usecol_offset, sep, escapechar, call_id,
        wfeo__smfvj, parallel=parallel, check_parallel_runtime=False,
        idx_col_index=idx_col_index, idx_col_typ=idx_col_typ)
    if idx_col_index != None:
        zspqa__mtdiz += '  return (T, idx_arr)\n'
    else:
        zspqa__mtdiz += '  return (T, None)\n'
    iiwal__yzpjk = {}
    exec(zspqa__mtdiz, wfeo__smfvj, iiwal__yzpjk)
    vtbjx__vrfk = iiwal__yzpjk['csv_reader_py']
    bqsz__twklh = numba.njit(vtbjx__vrfk)
    compiled_funcs.append(bqsz__twklh)
    return bqsz__twklh
