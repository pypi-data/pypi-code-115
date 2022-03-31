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
    vyf__sez = typemap[node.file_name.name]
    if types.unliteral(vyf__sez) != types.unicode_type:
        raise BodoError(
            f"pd.read_csv(): 'filepath_or_buffer' must be a string. Found type: {vyf__sez}."
            , node.file_name.loc)
    if not isinstance(node.skiprows, ir.Const):
        kuyls__chch = typemap[node.skiprows.name]
        if isinstance(kuyls__chch, types.Dispatcher):
            raise BodoError(
                f"pd.read_csv(): 'skiprows' callable not supported yet.",
                node.file_name.loc)
        elif not isinstance(kuyls__chch, types.Integer) and not (isinstance
            (kuyls__chch, (types.List, types.Tuple)) and isinstance(
            kuyls__chch.dtype, types.Integer)) and not isinstance(kuyls__chch,
            (types.LiteralList, bodo.utils.typing.ListLiteral)):
            raise BodoError(
                f"pd.read_csv(): 'skiprows' must be an integer or list of integers. Found type {kuyls__chch}."
                , loc=node.skiprows.loc)
        elif isinstance(kuyls__chch, (types.List, types.Tuple)):
            node.is_skiprows_list = True
    if not isinstance(node.nrows, ir.Const):
        urp__vqqdq = typemap[node.nrows.name]
        if not isinstance(urp__vqqdq, types.Integer):
            raise BodoError(
                f"pd.read_csv(): 'nrows' must be an integer. Found type {urp__vqqdq}."
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
        tue__zaah = csv_node.out_vars[0]
        if tue__zaah.name not in lives:
            return None
    else:
        kaeg__qxjla = csv_node.out_vars[0]
        cworh__eed = csv_node.out_vars[1]
        if kaeg__qxjla.name not in lives and cworh__eed.name not in lives:
            return None
        elif cworh__eed.name not in lives:
            csv_node.index_column_index = None
            csv_node.index_column_typ = types.none
        elif kaeg__qxjla.name not in lives:
            csv_node.usecols = []
            csv_node.out_types = []
            csv_node.type_usecol_offset = []
    return csv_node


def csv_distributed_run(csv_node, array_dists, typemap, calltypes,
    typingctx, targetctx):
    parallel = False
    kuyls__chch = types.int64 if isinstance(csv_node.skiprows, ir.Const
        ) else types.unliteral(typemap[csv_node.skiprows.name])
    if csv_node.chunksize is not None:
        if bodo.user_logging.get_verbose_level() >= 1:
            swjy__jtu = (
                'Finish column pruning on read_csv node:\n%s\nColumns loaded %s\n'
                )
            ymqet__btja = csv_node.loc.strformat()
            ebreq__iosu = csv_node.df_colnames
            bodo.user_logging.log_message('Column Pruning', swjy__jtu,
                ymqet__btja, ebreq__iosu)
            mscyl__umuff = csv_node.out_types[0].yield_type.data
            smfrw__vdil = [dpars__mzse for hjd__ocdxm, dpars__mzse in
                enumerate(csv_node.df_colnames) if isinstance(mscyl__umuff[
                hjd__ocdxm], bodo.libs.dict_arr_ext.DictionaryArrayType)]
            if smfrw__vdil:
                zkg__jhriq = """Finished optimized encoding on read_csv node:
%s
Columns %s using dictionary encoding to reduce memory usage.
"""
                bodo.user_logging.log_message('Dictionary Encoding',
                    zkg__jhriq, ymqet__btja, smfrw__vdil)
        if array_dists is not None:
            jrmes__rbzxw = csv_node.out_vars[0].name
            parallel = array_dists[jrmes__rbzxw] in (distributed_pass.
                Distribution.OneD, distributed_pass.Distribution.OneD_Var)
        jwfzl__twj = 'def csv_iterator_impl(fname, nrows, skiprows):\n'
        jwfzl__twj += (
            f'    reader = _csv_reader_init(fname, nrows, skiprows)\n')
        jwfzl__twj += (
            f'    iterator = init_csv_iterator(reader, csv_iterator_type)\n')
        zpn__qajc = {}
        from bodo.io.csv_iterator_ext import init_csv_iterator
        exec(jwfzl__twj, {}, zpn__qajc)
        pcnbp__wpv = zpn__qajc['csv_iterator_impl']
        hdhq__viuz = 'def csv_reader_init(fname, nrows, skiprows):\n'
        hdhq__viuz += _gen_csv_file_reader_init(parallel, csv_node.header,
            csv_node.compression, csv_node.chunksize, csv_node.
            is_skiprows_list, csv_node.pd_low_memory)
        hdhq__viuz += '  return f_reader\n'
        exec(hdhq__viuz, globals(), zpn__qajc)
        bfg__kev = zpn__qajc['csv_reader_init']
        zqwyk__bsoy = numba.njit(bfg__kev)
        compiled_funcs.append(zqwyk__bsoy)
        zvmq__prajm = compile_to_numba_ir(pcnbp__wpv, {'_csv_reader_init':
            zqwyk__bsoy, 'init_csv_iterator': init_csv_iterator,
            'csv_iterator_type': typemap[csv_node.out_vars[0].name]},
            typingctx=typingctx, targetctx=targetctx, arg_typs=(string_type,
            types.int64, kuyls__chch), typemap=typemap, calltypes=calltypes
            ).blocks.popitem()[1]
        replace_arg_nodes(zvmq__prajm, [csv_node.file_name, csv_node.nrows,
            csv_node.skiprows])
        lbjjo__xhygg = zvmq__prajm.body[:-3]
        lbjjo__xhygg[-1].target = csv_node.out_vars[0]
        return lbjjo__xhygg
    if array_dists is not None:
        xsu__yinz = csv_node.out_vars[0].name
        parallel = array_dists[xsu__yinz] in (distributed_pass.Distribution
            .OneD, distributed_pass.Distribution.OneD_Var)
        blnn__orc = csv_node.out_vars[1].name
        assert typemap[blnn__orc] == types.none or not parallel or array_dists[
            blnn__orc] in (distributed_pass.Distribution.OneD,
            distributed_pass.Distribution.OneD_Var
            ), 'pq data/index parallelization does not match'
    jwfzl__twj = 'def csv_impl(fname, nrows, skiprows):\n'
    jwfzl__twj += (
        f'    (table_val, idx_col) = _csv_reader_py(fname, nrows, skiprows)\n')
    zpn__qajc = {}
    exec(jwfzl__twj, {}, zpn__qajc)
    xfh__esx = zpn__qajc['csv_impl']
    ikw__waja = csv_node.usecols
    if ikw__waja:
        ikw__waja = [csv_node.usecols[hjd__ocdxm] for hjd__ocdxm in
            csv_node.type_usecol_offset]
    if bodo.user_logging.get_verbose_level() >= 1:
        swjy__jtu = (
            'Finish column pruning on read_csv node:\n%s\nColumns loaded %s\n')
        ymqet__btja = csv_node.loc.strformat()
        ebreq__iosu = []
        smfrw__vdil = []
        if ikw__waja:
            for hjd__ocdxm in ikw__waja:
                duati__ralpc = csv_node.df_colnames[hjd__ocdxm]
                ebreq__iosu.append(duati__ralpc)
                if isinstance(csv_node.out_types[hjd__ocdxm], bodo.libs.
                    dict_arr_ext.DictionaryArrayType):
                    smfrw__vdil.append(duati__ralpc)
        bodo.user_logging.log_message('Column Pruning', swjy__jtu,
            ymqet__btja, ebreq__iosu)
        if smfrw__vdil:
            zkg__jhriq = """Finished optimized encoding on read_csv node:
%s
Columns %s using dictionary encoding to reduce memory usage.
"""
            bodo.user_logging.log_message('Dictionary Encoding', zkg__jhriq,
                ymqet__btja, smfrw__vdil)
    oojbg__qbvbb = _gen_csv_reader_py(csv_node.df_colnames, csv_node.
        out_types, ikw__waja, csv_node.type_usecol_offset, csv_node.sep,
        parallel, csv_node.header, csv_node.compression, csv_node.
        is_skiprows_list, csv_node.pd_low_memory, csv_node.escapechar,
        idx_col_index=csv_node.index_column_index, idx_col_typ=csv_node.
        index_column_typ)
    zvmq__prajm = compile_to_numba_ir(xfh__esx, {'_csv_reader_py':
        oojbg__qbvbb}, typingctx=typingctx, targetctx=targetctx, arg_typs=(
        string_type, types.int64, kuyls__chch), typemap=typemap, calltypes=
        calltypes).blocks.popitem()[1]
    replace_arg_nodes(zvmq__prajm, [csv_node.file_name, csv_node.nrows,
        csv_node.skiprows, csv_node.is_skiprows_list])
    lbjjo__xhygg = zvmq__prajm.body[:-3]
    lbjjo__xhygg[-1].target = csv_node.out_vars[1]
    lbjjo__xhygg[-2].target = csv_node.out_vars[0]
    if csv_node.index_column_index is None:
        lbjjo__xhygg.pop(-1)
    elif not ikw__waja:
        lbjjo__xhygg.pop(-2)
    return lbjjo__xhygg


def csv_remove_dead_column(csv_node, column_live_map, equiv_vars, typemap):
    if csv_node.chunksize is not None:
        return False
    assert len(csv_node.out_vars) == 2, 'invalid CsvReader node'
    sauv__tikga = csv_node.out_vars[0].name
    if isinstance(typemap[sauv__tikga], TableType) and csv_node.usecols:
        gjn__vrcd, nkqgy__jwlem = get_live_column_nums_block(column_live_map,
            equiv_vars, sauv__tikga)
        gjn__vrcd = bodo.ir.connector.trim_extra_used_columns(gjn__vrcd,
            len(csv_node.usecols))
        if not nkqgy__jwlem and not gjn__vrcd:
            gjn__vrcd = [0]
        if not nkqgy__jwlem and len(gjn__vrcd) != len(csv_node.
            type_usecol_offset):
            csv_node.type_usecol_offset = gjn__vrcd
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
    npfnz__muc = t.dtype
    if isinstance(npfnz__muc, PDCategoricalDtype):
        jgfac__gwfc = CategoricalArrayType(npfnz__muc)
        kzsml__mwrwo = 'CategoricalArrayType' + str(ir_utils.next_label())
        setattr(types, kzsml__mwrwo, jgfac__gwfc)
        return kzsml__mwrwo
    if npfnz__muc == types.NPDatetime('ns'):
        npfnz__muc = 'NPDatetime("ns")'
    if t == string_array_type:
        types.string_array_type = string_array_type
        return 'string_array_type'
    if isinstance(t, IntegerArrayType):
        jyoof__yya = 'int_arr_{}'.format(npfnz__muc)
        setattr(types, jyoof__yya, t)
        return jyoof__yya
    if t == boolean_array:
        types.boolean_array = boolean_array
        return 'boolean_array'
    if npfnz__muc == types.bool_:
        npfnz__muc = 'bool_'
    if npfnz__muc == datetime_date_type:
        return 'datetime_date_array_type'
    if isinstance(t, ArrayItemArrayType) and isinstance(npfnz__muc, (
        StringArrayType, ArrayItemArrayType)):
        pajl__hds = f'ArrayItemArrayType{str(ir_utils.next_label())}'
        setattr(types, pajl__hds, t)
        return pajl__hds
    return '{}[::1]'.format(npfnz__muc)


def _get_pd_dtype_str(t):
    npfnz__muc = t.dtype
    if isinstance(npfnz__muc, PDCategoricalDtype):
        return 'pd.CategoricalDtype({})'.format(npfnz__muc.categories)
    if npfnz__muc == types.NPDatetime('ns'):
        return 'str'
    if t == string_array_type:
        return 'str'
    if isinstance(t, IntegerArrayType):
        return '"{}Int{}"'.format('' if npfnz__muc.signed else 'U',
            npfnz__muc.bitwidth)
    if t == boolean_array:
        return 'np.bool_'
    if isinstance(t, ArrayItemArrayType) and isinstance(npfnz__muc, (
        StringArrayType, ArrayItemArrayType)):
        return 'object'
    return 'np.{}'.format(npfnz__muc)


compiled_funcs = []


@numba.njit
def check_nrows_skiprows_value(nrows, skiprows):
    if nrows < -1:
        raise ValueError('pd.read_csv: nrows must be integer >= 0.')
    if skiprows[0] < 0:
        raise ValueError('pd.read_csv: skiprows must be integer >= 0.')


def astype(df, typemap, parallel):
    ctn__ofe = ''
    from collections import defaultdict
    qabe__fkwc = defaultdict(list)
    for dkgvz__dys, hwx__wjabq in typemap.items():
        qabe__fkwc[hwx__wjabq].append(dkgvz__dys)
    alf__wgml = df.columns.to_list()
    rbw__xpjj = []
    for hwx__wjabq, tpseo__ujfhn in qabe__fkwc.items():
        try:
            rbw__xpjj.append(df.loc[:, tpseo__ujfhn].astype(hwx__wjabq,
                copy=False))
            df = df.drop(tpseo__ujfhn, axis=1)
        except (ValueError, TypeError) as wssua__hgyk:
            ctn__ofe = (
                f"Caught the runtime error '{wssua__hgyk}' on columns {tpseo__ujfhn}. Consider setting the 'dtype' argument in 'read_csv' or investigate if the data is corrupted."
                )
            break
    yofak__yyhvh = bool(ctn__ofe)
    if parallel:
        vow__ooeh = MPI.COMM_WORLD
        yofak__yyhvh = vow__ooeh.allreduce(yofak__yyhvh, op=MPI.LOR)
    if yofak__yyhvh:
        sqbwc__rowrt = 'pd.read_csv(): Bodo could not infer dtypes correctly.'
        if ctn__ofe:
            raise TypeError(f'{sqbwc__rowrt}\n{ctn__ofe}')
        else:
            raise TypeError(
                f'{sqbwc__rowrt}\nPlease refer to errors on other ranks.')
    df = pd.concat(rbw__xpjj + [df], axis=1)
    iblhz__uuf = df.loc[:, alf__wgml]
    return iblhz__uuf


def _gen_csv_file_reader_init(parallel, header, compression, chunksize,
    is_skiprows_list, pd_low_memory):
    ouf__yptc = header == 0
    if compression is None:
        compression = 'uncompressed'
    if is_skiprows_list:
        jwfzl__twj = '  skiprows = sorted(set(skiprows))\n'
    else:
        jwfzl__twj = '  skiprows = [skiprows]\n'
    jwfzl__twj += '  skiprows_list_len = len(skiprows)\n'
    jwfzl__twj += '  check_nrows_skiprows_value(nrows, skiprows)\n'
    jwfzl__twj += '  check_java_installation(fname)\n'
    jwfzl__twj += f"""  bucket_region = bodo.io.fs_io.get_s3_bucket_region_njit(fname, parallel={parallel})
"""
    jwfzl__twj += (
        '  f_reader = bodo.ir.csv_ext.csv_file_chunk_reader(bodo.libs.str_ext.unicode_to_utf8(fname), '
        )
    jwfzl__twj += (
        """    {}, bodo.utils.conversion.coerce_to_ndarray(skiprows, scalar_to_arr_len=1).ctypes, nrows, {}, bodo.libs.str_ext.unicode_to_utf8('{}'), bodo.libs.str_ext.unicode_to_utf8(bucket_region), {}, {}, skiprows_list_len, {})
"""
        .format(parallel, ouf__yptc, compression, chunksize,
        is_skiprows_list, pd_low_memory))
    jwfzl__twj += '  bodo.utils.utils.check_and_propagate_cpp_exception()\n'
    jwfzl__twj += '  if bodo.utils.utils.is_null_pointer(f_reader):\n'
    jwfzl__twj += "      raise FileNotFoundError('File does not exist')\n"
    return jwfzl__twj


def _gen_read_csv_objmode(col_names, sanitized_cnames, col_typs, usecols,
    type_usecol_offset, sep, escapechar, call_id, glbs, parallel,
    check_parallel_runtime, idx_col_index, idx_col_typ):
    mzk__kkiii = [str(xtlz__aese) for hjd__ocdxm, xtlz__aese in enumerate(
        usecols) if col_typs[type_usecol_offset[hjd__ocdxm]].dtype == types
        .NPDatetime('ns')]
    if idx_col_typ == types.NPDatetime('ns'):
        assert not idx_col_index is None
        mzk__kkiii.append(str(idx_col_index))
    rgzpa__bbh = ', '.join(mzk__kkiii)
    htgc__pen = _gen_parallel_flag_name(sanitized_cnames)
    zpjds__ouga = f"{htgc__pen}='bool_'" if check_parallel_runtime else ''
    mqcng__cmpvh = [_get_pd_dtype_str(col_typs[type_usecol_offset[
        hjd__ocdxm]]) for hjd__ocdxm in range(len(usecols))]
    rkdfh__xvc = None if idx_col_index is None else _get_pd_dtype_str(
        idx_col_typ)
    skjtq__jdc = [xtlz__aese for hjd__ocdxm, xtlz__aese in enumerate(
        usecols) if mqcng__cmpvh[hjd__ocdxm] == 'str']
    if idx_col_index is not None and rkdfh__xvc == 'str':
        skjtq__jdc.append(idx_col_index)
    toju__sdc = np.array(skjtq__jdc, dtype=np.int64)
    glbs[f'str_col_nums_{call_id}'] = toju__sdc
    jwfzl__twj = f'  str_col_nums_{call_id}_2 = str_col_nums_{call_id}\n'
    hql__aeamp = np.array(usecols + ([idx_col_index] if idx_col_index is not
        None else []))
    glbs[f'usecols_arr_{call_id}'] = hql__aeamp
    jwfzl__twj += f'  usecols_arr_{call_id}_2 = usecols_arr_{call_id}\n'
    rfh__lmrzw = np.array(type_usecol_offset, dtype=np.int64)
    if usecols:
        glbs[f'type_usecols_offsets_arr_{call_id}'] = rfh__lmrzw
        jwfzl__twj += f"""  type_usecols_offsets_arr_{call_id}_2 = type_usecols_offsets_arr_{call_id}
"""
    nmus__vxp = defaultdict(list)
    for hjd__ocdxm, xtlz__aese in enumerate(usecols):
        if mqcng__cmpvh[hjd__ocdxm] == 'str':
            continue
        nmus__vxp[mqcng__cmpvh[hjd__ocdxm]].append(xtlz__aese)
    if idx_col_index is not None and rkdfh__xvc != 'str':
        nmus__vxp[rkdfh__xvc].append(idx_col_index)
    for hjd__ocdxm, bgz__aadf in enumerate(nmus__vxp.values()):
        glbs[f't_arr_{hjd__ocdxm}_{call_id}'] = np.asarray(bgz__aadf)
        jwfzl__twj += (
            f'  t_arr_{hjd__ocdxm}_{call_id}_2 = t_arr_{hjd__ocdxm}_{call_id}\n'
            )
    if idx_col_index != None:
        jwfzl__twj += f"""  with objmode(T=table_type_{call_id}, idx_arr=idx_array_typ, {zpjds__ouga}):
"""
    else:
        jwfzl__twj += (
            f'  with objmode(T=table_type_{call_id}, {zpjds__ouga}):\n')
    jwfzl__twj += f'    typemap = {{}}\n'
    for hjd__ocdxm, xflnp__nxg in enumerate(nmus__vxp.keys()):
        jwfzl__twj += f"""    typemap.update({{i:{xflnp__nxg} for i in t_arr_{hjd__ocdxm}_{call_id}_2}})
"""
    jwfzl__twj += '    if f_reader.get_chunk_size() == 0:\n'
    jwfzl__twj += (
        f'      df = pd.DataFrame(columns=usecols_arr_{call_id}_2, dtype=str)\n'
        )
    jwfzl__twj += '    else:\n'
    jwfzl__twj += '      df = pd.read_csv(f_reader,\n'
    jwfzl__twj += '        header=None,\n'
    jwfzl__twj += '        parse_dates=[{}],\n'.format(rgzpa__bbh)
    jwfzl__twj += (
        f'        dtype={{i:str for i in str_col_nums_{call_id}_2}},\n')
    jwfzl__twj += f"""        usecols=usecols_arr_{call_id}_2, sep={sep!r}, low_memory=False, escapechar={escapechar!r})
"""
    if check_parallel_runtime:
        jwfzl__twj += f'    {htgc__pen} = f_reader.is_parallel()\n'
    else:
        jwfzl__twj += f'    {htgc__pen} = {parallel}\n'
    jwfzl__twj += f'    df = astype(df, typemap, {htgc__pen})\n'
    if idx_col_index != None:
        psvky__dje = sorted(hql__aeamp).index(idx_col_index)
        jwfzl__twj += f'    idx_arr = df.iloc[:, {psvky__dje}].values\n'
        jwfzl__twj += (
            f'    df.drop(columns=df.columns[{psvky__dje}], inplace=True)\n')
    if len(usecols) == 0:
        jwfzl__twj += f'    T = None\n'
    else:
        jwfzl__twj += f'    arrs = []\n'
        jwfzl__twj += f'    for i in range(df.shape[1]):\n'
        jwfzl__twj += f'      arrs.append(df.iloc[:, i].values)\n'
        jwfzl__twj += f"""    T = Table(arrs, type_usecols_offsets_arr_{call_id}_2, {len(col_names)})
"""
    return jwfzl__twj


def _gen_parallel_flag_name(sanitized_cnames):
    htgc__pen = '_parallel_value'
    while htgc__pen in sanitized_cnames:
        htgc__pen = '_' + htgc__pen
    return htgc__pen


def _gen_csv_reader_py(col_names, col_typs, usecols, type_usecol_offset,
    sep, parallel, header, compression, is_skiprows_list, pd_low_memory,
    escapechar, idx_col_index=None, idx_col_typ=types.none):
    sanitized_cnames = [sanitize_varname(dpars__mzse) for dpars__mzse in
        col_names]
    jwfzl__twj = 'def csv_reader_py(fname, nrows, skiprows):\n'
    jwfzl__twj += _gen_csv_file_reader_init(parallel, header, compression, 
        -1, is_skiprows_list, pd_low_memory)
    call_id = ir_utils.next_label()
    nac__zfbr = globals()
    if idx_col_typ != types.none:
        nac__zfbr[f'idx_array_typ'] = idx_col_typ
    if len(usecols) == 0:
        nac__zfbr[f'table_type_{call_id}'] = types.none
    else:
        nac__zfbr[f'table_type_{call_id}'] = TableType(tuple(col_typs))
    jwfzl__twj += _gen_read_csv_objmode(col_names, sanitized_cnames,
        col_typs, usecols, type_usecol_offset, sep, escapechar, call_id,
        nac__zfbr, parallel=parallel, check_parallel_runtime=False,
        idx_col_index=idx_col_index, idx_col_typ=idx_col_typ)
    if idx_col_index != None:
        jwfzl__twj += '  return (T, idx_arr)\n'
    else:
        jwfzl__twj += '  return (T, None)\n'
    zpn__qajc = {}
    exec(jwfzl__twj, nac__zfbr, zpn__qajc)
    oojbg__qbvbb = zpn__qajc['csv_reader_py']
    zqwyk__bsoy = numba.njit(oojbg__qbvbb)
    compiled_funcs.append(zqwyk__bsoy)
    return zqwyk__bsoy
