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
    hpad__rtl = typemap[node.file_name.name]
    if types.unliteral(hpad__rtl) != types.unicode_type:
        raise BodoError(
            f"pd.read_csv(): 'filepath_or_buffer' must be a string. Found type: {hpad__rtl}."
            , node.file_name.loc)
    if not isinstance(node.skiprows, ir.Const):
        nstgt__fonjc = typemap[node.skiprows.name]
        if isinstance(nstgt__fonjc, types.Dispatcher):
            raise BodoError(
                f"pd.read_csv(): 'skiprows' callable not supported yet.",
                node.file_name.loc)
        elif not isinstance(nstgt__fonjc, types.Integer) and not (isinstance
            (nstgt__fonjc, (types.List, types.Tuple)) and isinstance(
            nstgt__fonjc.dtype, types.Integer)) and not isinstance(nstgt__fonjc
            , (types.LiteralList, bodo.utils.typing.ListLiteral)):
            raise BodoError(
                f"pd.read_csv(): 'skiprows' must be an integer or list of integers. Found type {nstgt__fonjc}."
                , loc=node.skiprows.loc)
        elif isinstance(nstgt__fonjc, (types.List, types.Tuple)):
            node.is_skiprows_list = True
    if not isinstance(node.nrows, ir.Const):
        fhys__fmys = typemap[node.nrows.name]
        if not isinstance(fhys__fmys, types.Integer):
            raise BodoError(
                f"pd.read_csv(): 'nrows' must be an integer. Found type {fhys__fmys}."
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
        ofqo__oeufr = csv_node.out_vars[0]
        if ofqo__oeufr.name not in lives:
            return None
    else:
        tznat__hfr = csv_node.out_vars[0]
        rrktu__vsr = csv_node.out_vars[1]
        if tznat__hfr.name not in lives and rrktu__vsr.name not in lives:
            return None
        elif rrktu__vsr.name not in lives:
            csv_node.index_column_index = None
            csv_node.index_column_typ = types.none
        elif tznat__hfr.name not in lives:
            csv_node.usecols = []
            csv_node.out_types = []
            csv_node.type_usecol_offset = []
    return csv_node


def csv_distributed_run(csv_node, array_dists, typemap, calltypes,
    typingctx, targetctx):
    parallel = False
    nstgt__fonjc = types.int64 if isinstance(csv_node.skiprows, ir.Const
        ) else types.unliteral(typemap[csv_node.skiprows.name])
    if csv_node.chunksize is not None:
        if bodo.user_logging.get_verbose_level() >= 1:
            lqbd__pkuo = (
                'Finish column pruning on read_csv node:\n%s\nColumns loaded %s\n'
                )
            ibcjz__lmsby = csv_node.loc.strformat()
            oeu__jqjne = csv_node.df_colnames
            bodo.user_logging.log_message('Column Pruning', lqbd__pkuo,
                ibcjz__lmsby, oeu__jqjne)
            irsi__rrlvv = csv_node.out_types[0].yield_type.data
            tbi__dtlpg = [iaur__txt for renvm__bqaf, iaur__txt in enumerate
                (csv_node.df_colnames) if isinstance(irsi__rrlvv[
                renvm__bqaf], bodo.libs.dict_arr_ext.DictionaryArrayType)]
            if tbi__dtlpg:
                sds__tztu = """Finished optimized encoding on read_csv node:
%s
Columns %s using dictionary encoding to reduce memory usage.
"""
                bodo.user_logging.log_message('Dictionary Encoding',
                    sds__tztu, ibcjz__lmsby, tbi__dtlpg)
        if array_dists is not None:
            hpr__bcd = csv_node.out_vars[0].name
            parallel = array_dists[hpr__bcd] in (distributed_pass.
                Distribution.OneD, distributed_pass.Distribution.OneD_Var)
        lvrj__gnnc = 'def csv_iterator_impl(fname, nrows, skiprows):\n'
        lvrj__gnnc += (
            f'    reader = _csv_reader_init(fname, nrows, skiprows)\n')
        lvrj__gnnc += (
            f'    iterator = init_csv_iterator(reader, csv_iterator_type)\n')
        vvgz__yrj = {}
        from bodo.io.csv_iterator_ext import init_csv_iterator
        exec(lvrj__gnnc, {}, vvgz__yrj)
        aqlz__yiibl = vvgz__yrj['csv_iterator_impl']
        sqk__exf = 'def csv_reader_init(fname, nrows, skiprows):\n'
        sqk__exf += _gen_csv_file_reader_init(parallel, csv_node.header,
            csv_node.compression, csv_node.chunksize, csv_node.
            is_skiprows_list, csv_node.pd_low_memory)
        sqk__exf += '  return f_reader\n'
        exec(sqk__exf, globals(), vvgz__yrj)
        qmke__kqoxn = vvgz__yrj['csv_reader_init']
        jnki__nwqst = numba.njit(qmke__kqoxn)
        compiled_funcs.append(jnki__nwqst)
        ochud__ajcnr = compile_to_numba_ir(aqlz__yiibl, {'_csv_reader_init':
            jnki__nwqst, 'init_csv_iterator': init_csv_iterator,
            'csv_iterator_type': typemap[csv_node.out_vars[0].name]},
            typingctx=typingctx, targetctx=targetctx, arg_typs=(string_type,
            types.int64, nstgt__fonjc), typemap=typemap, calltypes=calltypes
            ).blocks.popitem()[1]
        replace_arg_nodes(ochud__ajcnr, [csv_node.file_name, csv_node.nrows,
            csv_node.skiprows])
        mltzl__qwnvt = ochud__ajcnr.body[:-3]
        mltzl__qwnvt[-1].target = csv_node.out_vars[0]
        return mltzl__qwnvt
    if array_dists is not None:
        qkt__wkzcj = csv_node.out_vars[0].name
        parallel = array_dists[qkt__wkzcj] in (distributed_pass.
            Distribution.OneD, distributed_pass.Distribution.OneD_Var)
        ljptk__bpien = csv_node.out_vars[1].name
        assert typemap[ljptk__bpien
            ] == types.none or not parallel or array_dists[ljptk__bpien] in (
            distributed_pass.Distribution.OneD, distributed_pass.
            Distribution.OneD_Var
            ), 'pq data/index parallelization does not match'
    lvrj__gnnc = 'def csv_impl(fname, nrows, skiprows):\n'
    lvrj__gnnc += (
        f'    (table_val, idx_col) = _csv_reader_py(fname, nrows, skiprows)\n')
    vvgz__yrj = {}
    exec(lvrj__gnnc, {}, vvgz__yrj)
    mqko__shbb = vvgz__yrj['csv_impl']
    fagad__uwb = csv_node.usecols
    if fagad__uwb:
        fagad__uwb = [csv_node.usecols[renvm__bqaf] for renvm__bqaf in
            csv_node.type_usecol_offset]
    if bodo.user_logging.get_verbose_level() >= 1:
        lqbd__pkuo = (
            'Finish column pruning on read_csv node:\n%s\nColumns loaded %s\n')
        ibcjz__lmsby = csv_node.loc.strformat()
        oeu__jqjne = []
        tbi__dtlpg = []
        if fagad__uwb:
            for renvm__bqaf in fagad__uwb:
                yavwb__estb = csv_node.df_colnames[renvm__bqaf]
                oeu__jqjne.append(yavwb__estb)
                if isinstance(csv_node.out_types[renvm__bqaf], bodo.libs.
                    dict_arr_ext.DictionaryArrayType):
                    tbi__dtlpg.append(yavwb__estb)
        bodo.user_logging.log_message('Column Pruning', lqbd__pkuo,
            ibcjz__lmsby, oeu__jqjne)
        if tbi__dtlpg:
            sds__tztu = """Finished optimized encoding on read_csv node:
%s
Columns %s using dictionary encoding to reduce memory usage.
"""
            bodo.user_logging.log_message('Dictionary Encoding', sds__tztu,
                ibcjz__lmsby, tbi__dtlpg)
    zypbd__qynsl = _gen_csv_reader_py(csv_node.df_colnames, csv_node.
        out_types, fagad__uwb, csv_node.type_usecol_offset, csv_node.sep,
        parallel, csv_node.header, csv_node.compression, csv_node.
        is_skiprows_list, csv_node.pd_low_memory, csv_node.escapechar,
        idx_col_index=csv_node.index_column_index, idx_col_typ=csv_node.
        index_column_typ)
    ochud__ajcnr = compile_to_numba_ir(mqko__shbb, {'_csv_reader_py':
        zypbd__qynsl}, typingctx=typingctx, targetctx=targetctx, arg_typs=(
        string_type, types.int64, nstgt__fonjc), typemap=typemap, calltypes
        =calltypes).blocks.popitem()[1]
    replace_arg_nodes(ochud__ajcnr, [csv_node.file_name, csv_node.nrows,
        csv_node.skiprows, csv_node.is_skiprows_list])
    mltzl__qwnvt = ochud__ajcnr.body[:-3]
    mltzl__qwnvt[-1].target = csv_node.out_vars[1]
    mltzl__qwnvt[-2].target = csv_node.out_vars[0]
    if csv_node.index_column_index is None:
        mltzl__qwnvt.pop(-1)
    elif not fagad__uwb:
        mltzl__qwnvt.pop(-2)
    return mltzl__qwnvt


def csv_remove_dead_column(csv_node, column_live_map, equiv_vars, typemap):
    if csv_node.chunksize is not None:
        return False
    assert len(csv_node.out_vars) == 2, 'invalid CsvReader node'
    ogac__cbys = csv_node.out_vars[0].name
    if isinstance(typemap[ogac__cbys], TableType) and csv_node.usecols:
        rzula__csal, klkbs__kst = get_live_column_nums_block(column_live_map,
            equiv_vars, ogac__cbys)
        rzula__csal = bodo.ir.connector.trim_extra_used_columns(rzula__csal,
            len(csv_node.usecols))
        if not klkbs__kst and not rzula__csal:
            rzula__csal = [0]
        if not klkbs__kst and len(rzula__csal) != len(csv_node.
            type_usecol_offset):
            csv_node.type_usecol_offset = rzula__csal
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
    pkyb__hdx = t.dtype
    if isinstance(pkyb__hdx, PDCategoricalDtype):
        bbdty__mwyng = CategoricalArrayType(pkyb__hdx)
        dngd__urkr = 'CategoricalArrayType' + str(ir_utils.next_label())
        setattr(types, dngd__urkr, bbdty__mwyng)
        return dngd__urkr
    if pkyb__hdx == types.NPDatetime('ns'):
        pkyb__hdx = 'NPDatetime("ns")'
    if t == string_array_type:
        types.string_array_type = string_array_type
        return 'string_array_type'
    if isinstance(t, IntegerArrayType):
        dbvy__eliv = 'int_arr_{}'.format(pkyb__hdx)
        setattr(types, dbvy__eliv, t)
        return dbvy__eliv
    if t == boolean_array:
        types.boolean_array = boolean_array
        return 'boolean_array'
    if pkyb__hdx == types.bool_:
        pkyb__hdx = 'bool_'
    if pkyb__hdx == datetime_date_type:
        return 'datetime_date_array_type'
    if isinstance(t, ArrayItemArrayType) and isinstance(pkyb__hdx, (
        StringArrayType, ArrayItemArrayType)):
        tqo__ptx = f'ArrayItemArrayType{str(ir_utils.next_label())}'
        setattr(types, tqo__ptx, t)
        return tqo__ptx
    return '{}[::1]'.format(pkyb__hdx)


def _get_pd_dtype_str(t):
    pkyb__hdx = t.dtype
    if isinstance(pkyb__hdx, PDCategoricalDtype):
        return 'pd.CategoricalDtype({})'.format(pkyb__hdx.categories)
    if pkyb__hdx == types.NPDatetime('ns'):
        return 'str'
    if t == string_array_type:
        return 'str'
    if isinstance(t, IntegerArrayType):
        return '"{}Int{}"'.format('' if pkyb__hdx.signed else 'U',
            pkyb__hdx.bitwidth)
    if t == boolean_array:
        return 'np.bool_'
    if isinstance(t, ArrayItemArrayType) and isinstance(pkyb__hdx, (
        StringArrayType, ArrayItemArrayType)):
        return 'object'
    return 'np.{}'.format(pkyb__hdx)


compiled_funcs = []


@numba.njit
def check_nrows_skiprows_value(nrows, skiprows):
    if nrows < -1:
        raise ValueError('pd.read_csv: nrows must be integer >= 0.')
    if skiprows[0] < 0:
        raise ValueError('pd.read_csv: skiprows must be integer >= 0.')


def astype(df, typemap, parallel):
    rmg__zdj = ''
    from collections import defaultdict
    dip__ymvf = defaultdict(list)
    for pgfhz__gnkn, eswj__znq in typemap.items():
        dip__ymvf[eswj__znq].append(pgfhz__gnkn)
    ambp__kmp = df.columns.to_list()
    mvh__qmkne = []
    for eswj__znq, evnul__uadd in dip__ymvf.items():
        try:
            mvh__qmkne.append(df.loc[:, evnul__uadd].astype(eswj__znq, copy
                =False))
            df = df.drop(evnul__uadd, axis=1)
        except (ValueError, TypeError) as trde__fmzi:
            rmg__zdj = (
                f"Caught the runtime error '{trde__fmzi}' on columns {evnul__uadd}. Consider setting the 'dtype' argument in 'read_csv' or investigate if the data is corrupted."
                )
            break
    kkbw__yhiq = bool(rmg__zdj)
    if parallel:
        fedgo__ddd = MPI.COMM_WORLD
        kkbw__yhiq = fedgo__ddd.allreduce(kkbw__yhiq, op=MPI.LOR)
    if kkbw__yhiq:
        kyyjl__pfsd = 'pd.read_csv(): Bodo could not infer dtypes correctly.'
        if rmg__zdj:
            raise TypeError(f'{kyyjl__pfsd}\n{rmg__zdj}')
        else:
            raise TypeError(
                f'{kyyjl__pfsd}\nPlease refer to errors on other ranks.')
    df = pd.concat(mvh__qmkne + [df], axis=1)
    yqk__jsv = df.loc[:, ambp__kmp]
    return yqk__jsv


def _gen_csv_file_reader_init(parallel, header, compression, chunksize,
    is_skiprows_list, pd_low_memory):
    vbcgb__hjw = header == 0
    if compression is None:
        compression = 'uncompressed'
    if is_skiprows_list:
        lvrj__gnnc = '  skiprows = sorted(set(skiprows))\n'
    else:
        lvrj__gnnc = '  skiprows = [skiprows]\n'
    lvrj__gnnc += '  skiprows_list_len = len(skiprows)\n'
    lvrj__gnnc += '  check_nrows_skiprows_value(nrows, skiprows)\n'
    lvrj__gnnc += '  check_java_installation(fname)\n'
    lvrj__gnnc += f"""  bucket_region = bodo.io.fs_io.get_s3_bucket_region_njit(fname, parallel={parallel})
"""
    lvrj__gnnc += (
        '  f_reader = bodo.ir.csv_ext.csv_file_chunk_reader(bodo.libs.str_ext.unicode_to_utf8(fname), '
        )
    lvrj__gnnc += (
        """    {}, bodo.utils.conversion.coerce_to_ndarray(skiprows, scalar_to_arr_len=1).ctypes, nrows, {}, bodo.libs.str_ext.unicode_to_utf8('{}'), bodo.libs.str_ext.unicode_to_utf8(bucket_region), {}, {}, skiprows_list_len, {})
"""
        .format(parallel, vbcgb__hjw, compression, chunksize,
        is_skiprows_list, pd_low_memory))
    lvrj__gnnc += '  bodo.utils.utils.check_and_propagate_cpp_exception()\n'
    lvrj__gnnc += '  if bodo.utils.utils.is_null_pointer(f_reader):\n'
    lvrj__gnnc += "      raise FileNotFoundError('File does not exist')\n"
    return lvrj__gnnc


def _gen_read_csv_objmode(col_names, sanitized_cnames, col_typs, usecols,
    type_usecol_offset, sep, escapechar, call_id, glbs, parallel,
    check_parallel_runtime, idx_col_index, idx_col_typ):
    ezi__kmgbl = [str(xwl__wtyc) for renvm__bqaf, xwl__wtyc in enumerate(
        usecols) if col_typs[type_usecol_offset[renvm__bqaf]].dtype ==
        types.NPDatetime('ns')]
    if idx_col_typ == types.NPDatetime('ns'):
        assert not idx_col_index is None
        ezi__kmgbl.append(str(idx_col_index))
    oaa__qqjec = ', '.join(ezi__kmgbl)
    dga__faka = _gen_parallel_flag_name(sanitized_cnames)
    jcx__ifh = f"{dga__faka}='bool_'" if check_parallel_runtime else ''
    zgqz__iwzif = [_get_pd_dtype_str(col_typs[type_usecol_offset[
        renvm__bqaf]]) for renvm__bqaf in range(len(usecols))]
    osmy__dlalm = None if idx_col_index is None else _get_pd_dtype_str(
        idx_col_typ)
    cbgj__sjj = [xwl__wtyc for renvm__bqaf, xwl__wtyc in enumerate(usecols) if
        zgqz__iwzif[renvm__bqaf] == 'str']
    if idx_col_index is not None and osmy__dlalm == 'str':
        cbgj__sjj.append(idx_col_index)
    edwdn__ssd = np.array(cbgj__sjj, dtype=np.int64)
    glbs[f'str_col_nums_{call_id}'] = edwdn__ssd
    lvrj__gnnc = f'  str_col_nums_{call_id}_2 = str_col_nums_{call_id}\n'
    yojv__zqj = np.array(usecols + ([idx_col_index] if idx_col_index is not
        None else []))
    glbs[f'usecols_arr_{call_id}'] = yojv__zqj
    lvrj__gnnc += f'  usecols_arr_{call_id}_2 = usecols_arr_{call_id}\n'
    iaf__ynd = np.array(type_usecol_offset, dtype=np.int64)
    if usecols:
        glbs[f'type_usecols_offsets_arr_{call_id}'] = iaf__ynd
        lvrj__gnnc += f"""  type_usecols_offsets_arr_{call_id}_2 = type_usecols_offsets_arr_{call_id}
"""
    myi__haty = defaultdict(list)
    for renvm__bqaf, xwl__wtyc in enumerate(usecols):
        if zgqz__iwzif[renvm__bqaf] == 'str':
            continue
        myi__haty[zgqz__iwzif[renvm__bqaf]].append(xwl__wtyc)
    if idx_col_index is not None and osmy__dlalm != 'str':
        myi__haty[osmy__dlalm].append(idx_col_index)
    for renvm__bqaf, pzpx__wxtwm in enumerate(myi__haty.values()):
        glbs[f't_arr_{renvm__bqaf}_{call_id}'] = np.asarray(pzpx__wxtwm)
        lvrj__gnnc += (
            f'  t_arr_{renvm__bqaf}_{call_id}_2 = t_arr_{renvm__bqaf}_{call_id}\n'
            )
    if idx_col_index != None:
        lvrj__gnnc += f"""  with objmode(T=table_type_{call_id}, idx_arr=idx_array_typ, {jcx__ifh}):
"""
    else:
        lvrj__gnnc += f'  with objmode(T=table_type_{call_id}, {jcx__ifh}):\n'
    lvrj__gnnc += f'    typemap = {{}}\n'
    for renvm__bqaf, ksups__dpuy in enumerate(myi__haty.keys()):
        lvrj__gnnc += f"""    typemap.update({{i:{ksups__dpuy} for i in t_arr_{renvm__bqaf}_{call_id}_2}})
"""
    lvrj__gnnc += '    if f_reader.get_chunk_size() == 0:\n'
    lvrj__gnnc += (
        f'      df = pd.DataFrame(columns=usecols_arr_{call_id}_2, dtype=str)\n'
        )
    lvrj__gnnc += '    else:\n'
    lvrj__gnnc += '      df = pd.read_csv(f_reader,\n'
    lvrj__gnnc += '        header=None,\n'
    lvrj__gnnc += '        parse_dates=[{}],\n'.format(oaa__qqjec)
    lvrj__gnnc += (
        f'        dtype={{i:str for i in str_col_nums_{call_id}_2}},\n')
    lvrj__gnnc += f"""        usecols=usecols_arr_{call_id}_2, sep={sep!r}, low_memory=False, escapechar={escapechar!r})
"""
    if check_parallel_runtime:
        lvrj__gnnc += f'    {dga__faka} = f_reader.is_parallel()\n'
    else:
        lvrj__gnnc += f'    {dga__faka} = {parallel}\n'
    lvrj__gnnc += f'    df = astype(df, typemap, {dga__faka})\n'
    if idx_col_index != None:
        xjnds__setgg = sorted(yojv__zqj).index(idx_col_index)
        lvrj__gnnc += f'    idx_arr = df.iloc[:, {xjnds__setgg}].values\n'
        lvrj__gnnc += (
            f'    df.drop(columns=df.columns[{xjnds__setgg}], inplace=True)\n')
    if len(usecols) == 0:
        lvrj__gnnc += f'    T = None\n'
    else:
        lvrj__gnnc += f'    arrs = []\n'
        lvrj__gnnc += f'    for i in range(df.shape[1]):\n'
        lvrj__gnnc += f'      arrs.append(df.iloc[:, i].values)\n'
        lvrj__gnnc += f"""    T = Table(arrs, type_usecols_offsets_arr_{call_id}_2, {len(col_names)})
"""
    return lvrj__gnnc


def _gen_parallel_flag_name(sanitized_cnames):
    dga__faka = '_parallel_value'
    while dga__faka in sanitized_cnames:
        dga__faka = '_' + dga__faka
    return dga__faka


def _gen_csv_reader_py(col_names, col_typs, usecols, type_usecol_offset,
    sep, parallel, header, compression, is_skiprows_list, pd_low_memory,
    escapechar, idx_col_index=None, idx_col_typ=types.none):
    sanitized_cnames = [sanitize_varname(iaur__txt) for iaur__txt in col_names]
    lvrj__gnnc = 'def csv_reader_py(fname, nrows, skiprows):\n'
    lvrj__gnnc += _gen_csv_file_reader_init(parallel, header, compression, 
        -1, is_skiprows_list, pd_low_memory)
    call_id = ir_utils.next_label()
    mles__ntjj = globals()
    if idx_col_typ != types.none:
        mles__ntjj[f'idx_array_typ'] = idx_col_typ
    if len(usecols) == 0:
        mles__ntjj[f'table_type_{call_id}'] = types.none
    else:
        mles__ntjj[f'table_type_{call_id}'] = TableType(tuple(col_typs))
    lvrj__gnnc += _gen_read_csv_objmode(col_names, sanitized_cnames,
        col_typs, usecols, type_usecol_offset, sep, escapechar, call_id,
        mles__ntjj, parallel=parallel, check_parallel_runtime=False,
        idx_col_index=idx_col_index, idx_col_typ=idx_col_typ)
    if idx_col_index != None:
        lvrj__gnnc += '  return (T, idx_arr)\n'
    else:
        lvrj__gnnc += '  return (T, None)\n'
    vvgz__yrj = {}
    exec(lvrj__gnnc, mles__ntjj, vvgz__yrj)
    zypbd__qynsl = vvgz__yrj['csv_reader_py']
    jnki__nwqst = numba.njit(zypbd__qynsl)
    compiled_funcs.append(jnki__nwqst)
    return jnki__nwqst
