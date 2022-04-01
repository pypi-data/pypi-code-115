import os
import warnings
from collections import defaultdict
import llvmlite.binding as ll
import numba
import numpy as np
import pandas as pd
import pyarrow
import pyarrow.dataset as ds
from numba.core import ir, types
from numba.core.ir_utils import compile_to_numba_ir, get_definition, guard, mk_unique_var, next_label, replace_arg_nodes
from numba.extending import NativeValue, intrinsic, models, overload, register_model, unbox
from pyarrow import null
import bodo
import bodo.ir.parquet_ext
import bodo.utils.tracing as tracing
from bodo.hiframes.datetime_date_ext import datetime_date_array_type, datetime_date_type
from bodo.hiframes.pd_categorical_ext import CategoricalArrayType, PDCategoricalDtype
from bodo.hiframes.table import TableType
from bodo.io.fs_io import get_hdfs_fs, get_s3_fs_from_path, get_s3_subtree_fs
from bodo.libs.array import cpp_table_to_py_table, delete_table, info_from_table, info_to_array, table_type
from bodo.libs.array_item_arr_ext import ArrayItemArrayType
from bodo.libs.binary_arr_ext import binary_array_type, bytes_type
from bodo.libs.bool_arr_ext import boolean_array
from bodo.libs.decimal_arr_ext import DecimalArrayType
from bodo.libs.dict_arr_ext import dict_str_arr_type
from bodo.libs.distributed_api import get_end, get_start
from bodo.libs.int_arr_ext import IntegerArrayType
from bodo.libs.str_arr_ext import string_array_type
from bodo.libs.str_ext import string_type, unicode_to_utf8
from bodo.libs.struct_arr_ext import StructArrayType
from bodo.transforms import distributed_pass
from bodo.utils.transform import get_const_value
from bodo.utils.typing import BodoError, BodoWarning, FileInfo, get_overload_const_str, get_overload_constant_dict
from bodo.utils.utils import check_and_propagate_cpp_exception, numba_to_c_type, sanitize_varname
use_nullable_int_arr = True
from urllib.parse import urlparse
import bodo.io.pa_parquet
REMOTE_FILESYSTEMS = {'s3', 'gcs', 'gs', 'http', 'hdfs', 'abfs', 'abfss'}
READ_STR_AS_DICT_THRESHOLD = 1.0


class ParquetPredicateType(types.Type):

    def __init__(self):
        super(ParquetPredicateType, self).__init__(name=
            'ParquetPredicateType()')


parquet_predicate_type = ParquetPredicateType()
types.parquet_predicate_type = parquet_predicate_type
register_model(ParquetPredicateType)(models.OpaqueModel)


@unbox(ParquetPredicateType)
def unbox_parquet_predicate_type(typ, val, c):
    c.pyapi.incref(val)
    return NativeValue(val)


class ReadParquetFilepathType(types.Opaque):

    def __init__(self):
        super(ReadParquetFilepathType, self).__init__(name=
            'ReadParquetFilepathType')


read_parquet_fpath_type = ReadParquetFilepathType()
types.read_parquet_fpath_type = read_parquet_fpath_type
register_model(ReadParquetFilepathType)(models.OpaqueModel)


@unbox(ReadParquetFilepathType)
def unbox_read_parquet_fpath_type(typ, val, c):
    c.pyapi.incref(val)
    return NativeValue(val)


class StorageOptionsDictType(types.Opaque):

    def __init__(self):
        super(StorageOptionsDictType, self).__init__(name=
            'StorageOptionsDictType')


storage_options_dict_type = StorageOptionsDictType()
types.storage_options_dict_type = storage_options_dict_type
register_model(StorageOptionsDictType)(models.OpaqueModel)


@unbox(StorageOptionsDictType)
def unbox_storage_options_dict_type(typ, val, c):
    c.pyapi.incref(val)
    return NativeValue(val)


class ParquetFileInfo(FileInfo):

    def __init__(self, columns, storage_options=None, input_file_name_col=None
        ):
        self.columns = columns
        self.storage_options = storage_options
        self.input_file_name_col = input_file_name_col
        super().__init__()

    def _get_schema(self, fname):
        try:
            return parquet_file_schema(fname, selected_columns=self.columns,
                storage_options=self.storage_options, input_file_name_col=
                self.input_file_name_col)
        except OSError as qst__yibi:
            if 'non-file path' in str(qst__yibi):
                raise FileNotFoundError(str(qst__yibi))
            raise


class ParquetHandler:

    def __init__(self, func_ir, typingctx, args, _locals):
        self.func_ir = func_ir
        self.typingctx = typingctx
        self.args = args
        self.locals = _locals

    def gen_parquet_read(self, file_name, lhs, columns, storage_options=
        None, input_file_name_col=None):
        sipf__grt = lhs.scope
        jzzm__cfc = lhs.loc
        gib__mie = None
        if lhs.name in self.locals:
            gib__mie = self.locals[lhs.name]
            self.locals.pop(lhs.name)
        xom__dyu = {}
        if lhs.name + ':convert' in self.locals:
            xom__dyu = self.locals[lhs.name + ':convert']
            self.locals.pop(lhs.name + ':convert')
        if gib__mie is None:
            nokwq__qiaj = (
                'Parquet schema not available. Either path argument should be constant for Bodo to look at the file at compile time or schema should be provided. For more information, see: https://docs.bodo.ai/latest/source/programming_with_bodo/file_io.html#non-constant-filepaths'
                )
            ipzc__gat = get_const_value(file_name, self.func_ir,
                nokwq__qiaj, arg_types=self.args, file_info=ParquetFileInfo
                (columns, storage_options=storage_options,
                input_file_name_col=input_file_name_col))
            eoej__rpyk = False
            mph__joi = guard(get_definition, self.func_ir, file_name)
            if isinstance(mph__joi, ir.Arg):
                typ = self.args[mph__joi.index]
                if isinstance(typ, types.FilenameType):
                    (col_names, luh__mva, jhbc__mnwz, col_indices,
                        partition_names, gxaph__midlw, kbatm__zof) = typ.schema
                    eoej__rpyk = True
            if not eoej__rpyk:
                (col_names, luh__mva, jhbc__mnwz, col_indices,
                    partition_names, gxaph__midlw, kbatm__zof) = (
                    parquet_file_schema(ipzc__gat, columns, storage_options
                    =storage_options, input_file_name_col=input_file_name_col))
        else:
            fjj__olkgq = list(gib__mie.keys())
            ulzxq__onpz = {c: hylt__vbmoj for hylt__vbmoj, c in enumerate(
                fjj__olkgq)}
            oken__owom = [qlz__fsu for qlz__fsu in gib__mie.values()]
            jhbc__mnwz = 'index' if 'index' in ulzxq__onpz else None
            if columns is None:
                selected_columns = fjj__olkgq
            else:
                selected_columns = columns
            col_indices = [ulzxq__onpz[c] for c in selected_columns]
            luh__mva = [oken__owom[ulzxq__onpz[c]] for c in selected_columns]
            col_names = selected_columns
            jhbc__mnwz = jhbc__mnwz if jhbc__mnwz in col_names else None
            partition_names = []
            gxaph__midlw = []
            kbatm__zof = []
        fudvq__bzrdy = None if isinstance(jhbc__mnwz, dict
            ) or jhbc__mnwz is None else jhbc__mnwz
        index_column_index = None
        index_column_type = types.none
        if fudvq__bzrdy:
            yrl__fpj = col_names.index(fudvq__bzrdy)
            index_column_index = col_indices.pop(yrl__fpj)
            index_column_type = luh__mva.pop(yrl__fpj)
            col_names.pop(yrl__fpj)
        for hylt__vbmoj, c in enumerate(col_names):
            if c in xom__dyu:
                luh__mva[hylt__vbmoj] = xom__dyu[c]
        fsfc__ajsyk = [ir.Var(sipf__grt, mk_unique_var('pq_table'),
            jzzm__cfc), ir.Var(sipf__grt, mk_unique_var('pq_index'), jzzm__cfc)
            ]
        fvi__wqb = [bodo.ir.parquet_ext.ParquetReader(file_name, lhs.name,
            col_names, col_indices, luh__mva, fsfc__ajsyk, jzzm__cfc,
            partition_names, storage_options, index_column_index,
            index_column_type, input_file_name_col, gxaph__midlw, kbatm__zof)]
        return (col_names, fsfc__ajsyk, jhbc__mnwz, fvi__wqb, luh__mva,
            index_column_type)


def determine_filter_cast(pq_node, typemap, filter_val, orig_colname_map):
    wtfn__fbh = filter_val[0]
    nqgd__evb = pq_node.original_out_types[orig_colname_map[wtfn__fbh]]
    jrit__ymcg = bodo.utils.typing.element_type(nqgd__evb)
    if wtfn__fbh in pq_node.partition_names:
        if jrit__ymcg == types.unicode_type:
            lhd__poyy = '.cast(pyarrow.string(), safe=False)'
        elif isinstance(jrit__ymcg, types.Integer):
            lhd__poyy = f'.cast(pyarrow.{jrit__ymcg.name}(), safe=False)'
        else:
            lhd__poyy = ''
    else:
        lhd__poyy = ''
    vuvx__wbdo = typemap[filter_val[2].name]
    if isinstance(vuvx__wbdo, (types.List, types.Set)):
        zng__fvhq = vuvx__wbdo.dtype
    else:
        zng__fvhq = vuvx__wbdo
    bodo.hiframes.pd_timestamp_ext.check_tz_aware_unsupported(jrit__ymcg,
        'Filter pushdown')
    bodo.hiframes.pd_timestamp_ext.check_tz_aware_unsupported(zng__fvhq,
        'Filter pushdown')
    if not bodo.utils.typing.is_common_scalar_dtype([jrit__ymcg, zng__fvhq]):
        if not bodo.utils.typing.is_safe_arrow_cast(jrit__ymcg, zng__fvhq):
            raise BodoError(
                f'Unsupported Arrow cast from {jrit__ymcg} to {zng__fvhq} in filter pushdown. Please try a comparison that avoids casting the column.'
                )
        if jrit__ymcg == types.unicode_type:
            return ".cast(pyarrow.timestamp('ns'), safe=False)", ''
        elif jrit__ymcg in (bodo.datetime64ns, bodo.pd_timestamp_type):
            if isinstance(vuvx__wbdo, (types.List, types.Set)):
                bpiud__vrnu = 'list' if isinstance(vuvx__wbdo, types.List
                    ) else 'tuple'
                raise BodoError(
                    f'Cannot cast {bpiud__vrnu} values with isin filter pushdown.'
                    )
            return lhd__poyy, ".cast(pyarrow.timestamp('ns'), safe=False)"
    return lhd__poyy, ''


def pq_distributed_run(pq_node, array_dists, typemap, calltypes, typingctx,
    targetctx, meta_head_only_info=None):
    ooe__jdip = len(pq_node.out_vars)
    extra_args = ''
    dnf_filter_str = 'None'
    expr_filter_str = 'None'
    bkrci__vdju, wrxy__vceow = bodo.ir.connector.generate_filter_map(pq_node
        .filters)
    if pq_node.filters:
        uztr__uymdi = []
        ocv__cpp = []
        kah__nuy = False
        beh__deopj = None
        orig_colname_map = {c: hylt__vbmoj for hylt__vbmoj, c in enumerate(
            pq_node.original_df_colnames)}
        for toa__yrr in pq_node.filters:
            rzrq__gna = []
            gslu__qluk = []
            fdpif__txog = set()
            for ufy__sxtic in toa__yrr:
                if isinstance(ufy__sxtic[2], ir.Var):
                    wybej__mesy, jhq__vamv = determine_filter_cast(pq_node,
                        typemap, ufy__sxtic, orig_colname_map)
                    if ufy__sxtic[1] == 'in':
                        gslu__qluk.append(
                            f"(ds.field('{ufy__sxtic[0]}').isin({bkrci__vdju[ufy__sxtic[2].name]}))"
                            )
                    else:
                        gslu__qluk.append(
                            f"(ds.field('{ufy__sxtic[0]}'){wybej__mesy} {ufy__sxtic[1]} ds.scalar({bkrci__vdju[ufy__sxtic[2].name]}){jhq__vamv})"
                            )
                else:
                    assert ufy__sxtic[2
                        ] == 'NULL', 'unsupport constant used in filter pushdown'
                    if ufy__sxtic[1] == 'is not':
                        prefix = '~'
                    else:
                        prefix = ''
                    gslu__qluk.append(
                        f"({prefix}ds.field('{ufy__sxtic[0]}').is_null())")
                if ufy__sxtic[0] in pq_node.partition_names and isinstance(
                    ufy__sxtic[2], ir.Var):
                    enb__fnx = (
                        f"('{ufy__sxtic[0]}', '{ufy__sxtic[1]}', {bkrci__vdju[ufy__sxtic[2].name]})"
                        )
                    rzrq__gna.append(enb__fnx)
                    fdpif__txog.add(enb__fnx)
                else:
                    kah__nuy = True
            if beh__deopj is None:
                beh__deopj = fdpif__txog
            else:
                beh__deopj.intersection_update(fdpif__txog)
            mlb__dyvby = ', '.join(rzrq__gna)
            bqupz__sqaef = ' & '.join(gslu__qluk)
            if mlb__dyvby:
                uztr__uymdi.append(f'[{mlb__dyvby}]')
            ocv__cpp.append(f'({bqupz__sqaef})')
        ktmm__etrlk = ', '.join(uztr__uymdi)
        cww__tnsg = ' | '.join(ocv__cpp)
        if kah__nuy:
            if beh__deopj:
                okq__dmrjb = sorted(beh__deopj)
                dnf_filter_str = f"[[{', '.join(okq__dmrjb)}]]"
        elif ktmm__etrlk:
            dnf_filter_str = f'[{ktmm__etrlk}]'
        expr_filter_str = f'({cww__tnsg})'
        extra_args = ', '.join(bkrci__vdju.values())
    lbwk__oumco = ', '.join(f'out{hylt__vbmoj}' for hylt__vbmoj in range(
        ooe__jdip))
    cxqco__ezvuz = f'def pq_impl(fname, {extra_args}):\n'
    cxqco__ezvuz += (
        f'    (total_rows, {lbwk__oumco},) = _pq_reader_py(fname, {extra_args})\n'
        )
    ula__qicuu = {}
    exec(cxqco__ezvuz, {}, ula__qicuu)
    ikque__nziwa = ula__qicuu['pq_impl']
    if bodo.user_logging.get_verbose_level() >= 1:
        ekryh__igzm = pq_node.loc.strformat()
        aay__ekthx = []
        svzfu__mjz = []
        for hylt__vbmoj in pq_node.type_usecol_offset:
            wtfn__fbh = pq_node.df_colnames[hylt__vbmoj]
            aay__ekthx.append(wtfn__fbh)
            if isinstance(pq_node.out_types[hylt__vbmoj], bodo.libs.
                dict_arr_ext.DictionaryArrayType):
                svzfu__mjz.append(wtfn__fbh)
        elper__xoa = (
            'Finish column pruning on read_parquet node:\n%s\nColumns loaded %s\n'
            )
        bodo.user_logging.log_message('Column Pruning', elper__xoa,
            ekryh__igzm, aay__ekthx)
        if svzfu__mjz:
            cbmo__cguxh = """Finished optimized encoding on read_parquet node:
%s
Columns %s using dictionary encoding to reduce memory usage.
"""
            bodo.user_logging.log_message('Dictionary Encoding',
                cbmo__cguxh, ekryh__igzm, svzfu__mjz)
    parallel = False
    if array_dists is not None:
        fushx__kbmb = pq_node.out_vars[0].name
        parallel = array_dists[fushx__kbmb] in (distributed_pass.
            Distribution.OneD, distributed_pass.Distribution.OneD_Var)
        mpros__bmsk = pq_node.out_vars[1].name
        assert typemap[mpros__bmsk
            ] == types.none or not parallel or array_dists[mpros__bmsk] in (
            distributed_pass.Distribution.OneD, distributed_pass.
            Distribution.OneD_Var
            ), 'pq data/index parallelization does not match'
    if pq_node.unsupported_columns:
        xok__ooxqn = set(pq_node.type_usecol_offset)
        aok__hytmm = set(pq_node.unsupported_columns)
        zmvmv__nbed = xok__ooxqn & aok__hytmm
        if zmvmv__nbed:
            jcxox__enpj = sorted(zmvmv__nbed)
            lcp__oxda = [
                f'pandas.read_parquet(): 1 or more columns found with Arrow types that are not supported in Bodo and could not be eliminated. '
                 +
                "Please manually remove these columns from your read_parquet with the 'columns' argument. If these "
                 +
                'columns are needed, you will need to modify your dataset to use a supported type.'
                , 'Unsupported Columns:']
            zyo__zkbpo = 0
            for lcvn__awp in jcxox__enpj:
                while pq_node.unsupported_columns[zyo__zkbpo] != lcvn__awp:
                    zyo__zkbpo += 1
                lcp__oxda.append(
                    f"Column '{pq_node.df_colnames[lcvn__awp]}' with unsupported arrow type {pq_node.unsupported_arrow_types[zyo__zkbpo]}"
                    )
                zyo__zkbpo += 1
            opot__xmsqq = '\n'.join(lcp__oxda)
            raise BodoError(opot__xmsqq, loc=pq_node.loc)
    yoasx__mgw = _gen_pq_reader_py(pq_node.df_colnames, pq_node.col_indices,
        pq_node.type_usecol_offset, pq_node.out_types, pq_node.
        storage_options, pq_node.partition_names, dnf_filter_str,
        expr_filter_str, extra_args, parallel, meta_head_only_info, pq_node
        .index_column_index, pq_node.index_column_type, pq_node.
        input_file_name_col)
    vbhvf__bcyf = typemap[pq_node.file_name.name]
    gkxk__vkj = (vbhvf__bcyf,) + tuple(typemap[ufy__sxtic.name] for
        ufy__sxtic in wrxy__vceow)
    abwe__ttkfw = compile_to_numba_ir(ikque__nziwa, {'_pq_reader_py':
        yoasx__mgw}, typingctx=typingctx, targetctx=targetctx, arg_typs=
        gkxk__vkj, typemap=typemap, calltypes=calltypes).blocks.popitem()[1]
    replace_arg_nodes(abwe__ttkfw, [pq_node.file_name] + wrxy__vceow)
    fvi__wqb = abwe__ttkfw.body[:-3]
    if meta_head_only_info:
        fvi__wqb[-1 - ooe__jdip].target = meta_head_only_info[1]
    fvi__wqb[-2].target = pq_node.out_vars[0]
    fvi__wqb[-1].target = pq_node.out_vars[1]
    return fvi__wqb


distributed_pass.distributed_run_extensions[bodo.ir.parquet_ext.ParquetReader
    ] = pq_distributed_run


def get_filters_pyobject(dnf_filter_str, expr_filter_str, vars):
    pass


@overload(get_filters_pyobject, no_unliteral=True)
def overload_get_filters_pyobject(dnf_filter_str, expr_filter_str, var_tup):
    kytd__mmb = get_overload_const_str(dnf_filter_str)
    owjb__llrtf = get_overload_const_str(expr_filter_str)
    oyrul__zjg = ', '.join(f'f{hylt__vbmoj}' for hylt__vbmoj in range(len(
        var_tup)))
    cxqco__ezvuz = 'def impl(dnf_filter_str, expr_filter_str, var_tup):\n'
    if len(var_tup):
        cxqco__ezvuz += f'  {oyrul__zjg}, = var_tup\n'
    cxqco__ezvuz += """  with numba.objmode(dnf_filters_py='parquet_predicate_type', expr_filters_py='parquet_predicate_type'):
"""
    cxqco__ezvuz += f'    dnf_filters_py = {kytd__mmb}\n'
    cxqco__ezvuz += f'    expr_filters_py = {owjb__llrtf}\n'
    cxqco__ezvuz += '  return (dnf_filters_py, expr_filters_py)\n'
    ula__qicuu = {}
    exec(cxqco__ezvuz, globals(), ula__qicuu)
    return ula__qicuu['impl']


@numba.njit
def get_fname_pyobject(fname):
    with numba.objmode(fname_py='read_parquet_fpath_type'):
        fname_py = fname
    return fname_py


def get_storage_options_pyobject(storage_options):
    pass


@overload(get_storage_options_pyobject, no_unliteral=True)
def overload_get_storage_options_pyobject(storage_options):
    qtfnf__jxxa = get_overload_constant_dict(storage_options)
    cxqco__ezvuz = 'def impl(storage_options):\n'
    cxqco__ezvuz += (
        "  with numba.objmode(storage_options_py='storage_options_dict_type'):\n"
        )
    cxqco__ezvuz += f'    storage_options_py = {str(qtfnf__jxxa)}\n'
    cxqco__ezvuz += '  return storage_options_py\n'
    ula__qicuu = {}
    exec(cxqco__ezvuz, globals(), ula__qicuu)
    return ula__qicuu['impl']


def _gen_pq_reader_py(col_names, col_indices, type_usecol_offset, out_types,
    storage_options, partition_names, dnf_filter_str, expr_filter_str,
    extra_args, is_parallel, meta_head_only_info, index_column_index,
    index_column_type, input_file_name_col):
    sqpot__syp = next_label()
    nud__diam = ',' if extra_args else ''
    cxqco__ezvuz = f'def pq_reader_py(fname,{extra_args}):\n'
    cxqco__ezvuz += (
        f"    ev = bodo.utils.tracing.Event('read_parquet', {is_parallel})\n")
    cxqco__ezvuz += f"    ev.add_attribute('fname', fname)\n"
    cxqco__ezvuz += f"""    bucket_region = bodo.io.fs_io.get_s3_bucket_region_njit(fname, parallel={is_parallel})
"""
    cxqco__ezvuz += f"""    dnf_filters, expr_filters = get_filters_pyobject("{dnf_filter_str}", "{expr_filter_str}", ({extra_args}{nud__diam}))
"""
    cxqco__ezvuz += '    fname_py = get_fname_pyobject(fname)\n'
    storage_options['bodo_dummy'] = 'dummy'
    cxqco__ezvuz += f"""    storage_options_py = get_storage_options_pyobject({str(storage_options)})
"""
    tot_rows_to_read = -1
    if meta_head_only_info and meta_head_only_info[0] is not None:
        tot_rows_to_read = meta_head_only_info[0]
    klykh__ars = not type_usecol_offset
    nda__fxbnt = [sanitize_varname(c) for c in col_names]
    partition_names = [sanitize_varname(c) for c in partition_names]
    input_file_name_col = sanitize_varname(input_file_name_col
        ) if input_file_name_col is not None and col_names.index(
        input_file_name_col) in type_usecol_offset else None
    jvs__mox = {c: hylt__vbmoj for hylt__vbmoj, c in enumerate(col_indices)}
    qipkq__wwhqn = {c: hylt__vbmoj for hylt__vbmoj, c in enumerate(nda__fxbnt)}
    ekn__knksl = []
    dtvff__qwtk = set()
    dyzj__achxz = partition_names + [input_file_name_col]
    for hylt__vbmoj in type_usecol_offset:
        if nda__fxbnt[hylt__vbmoj] not in dyzj__achxz:
            ekn__knksl.append(col_indices[hylt__vbmoj])
        elif not input_file_name_col or nda__fxbnt[hylt__vbmoj
            ] != input_file_name_col:
            dtvff__qwtk.add(col_indices[hylt__vbmoj])
    if index_column_index is not None:
        ekn__knksl.append(index_column_index)
    ekn__knksl = sorted(ekn__knksl)
    hlq__jsj = {c: hylt__vbmoj for hylt__vbmoj, c in enumerate(ekn__knksl)}

    def is_nullable(typ):
        return bodo.utils.utils.is_array_typ(typ, False) and (not
            isinstance(typ, types.Array) and not isinstance(typ, bodo.
            DatetimeArrayType))
    uosfv__txbp = [(int(is_nullable(out_types[jvs__mox[llw__fweur]])) if 
        llw__fweur != index_column_index else int(is_nullable(
        index_column_type))) for llw__fweur in ekn__knksl]
    str_as_dict_cols = []
    for llw__fweur in ekn__knksl:
        if llw__fweur == index_column_index:
            qlz__fsu = index_column_type
        else:
            qlz__fsu = out_types[jvs__mox[llw__fweur]]
        if qlz__fsu == dict_str_arr_type:
            str_as_dict_cols.append(llw__fweur)
    ione__sjaao = []
    vtxz__wuhq = {}
    nxf__lmqcw = []
    scfz__ffbk = []
    for hylt__vbmoj, wlpm__gotn in enumerate(partition_names):
        try:
            nrryp__mhvfl = qipkq__wwhqn[wlpm__gotn]
            if col_indices[nrryp__mhvfl] not in dtvff__qwtk:
                continue
        except (KeyError, ValueError) as ryjiy__dfkvn:
            continue
        vtxz__wuhq[wlpm__gotn] = len(ione__sjaao)
        ione__sjaao.append(wlpm__gotn)
        nxf__lmqcw.append(hylt__vbmoj)
        kesoi__eaj = out_types[nrryp__mhvfl].dtype
        nkgt__lgzn = bodo.hiframes.pd_categorical_ext.get_categories_int_type(
            kesoi__eaj)
        scfz__ffbk.append(numba_to_c_type(nkgt__lgzn))
    cxqco__ezvuz += f'    total_rows_np = np.array([0], dtype=np.int64)\n'
    cxqco__ezvuz += f'    out_table = pq_read(\n'
    cxqco__ezvuz += f'        fname_py, {is_parallel},\n'
    cxqco__ezvuz += f'        unicode_to_utf8(bucket_region),\n'
    cxqco__ezvuz += f'        dnf_filters, expr_filters,\n'
    cxqco__ezvuz += f"""        storage_options_py, {tot_rows_to_read}, selected_cols_arr_{sqpot__syp}.ctypes,
"""
    cxqco__ezvuz += f'        {len(ekn__knksl)},\n'
    cxqco__ezvuz += f'        nullable_cols_arr_{sqpot__syp}.ctypes,\n'
    if len(nxf__lmqcw) > 0:
        cxqco__ezvuz += (
            f'        np.array({nxf__lmqcw}, dtype=np.int32).ctypes,\n')
        cxqco__ezvuz += (
            f'        np.array({scfz__ffbk}, dtype=np.int32).ctypes,\n')
        cxqco__ezvuz += f'        {len(nxf__lmqcw)},\n'
    else:
        cxqco__ezvuz += f'        0, 0, 0,\n'
    if len(str_as_dict_cols) > 0:
        cxqco__ezvuz += f"""        np.array({str_as_dict_cols}, dtype=np.int32).ctypes, {len(str_as_dict_cols)},
"""
    else:
        cxqco__ezvuz += f'        0, 0,\n'
    cxqco__ezvuz += f'        total_rows_np.ctypes,\n'
    cxqco__ezvuz += f'        {input_file_name_col is not None},\n'
    cxqco__ezvuz += f'    )\n'
    cxqco__ezvuz += f'    check_and_propagate_cpp_exception()\n'
    hex__kgxvu = 'None'
    wit__rxg = index_column_type
    uay__ubimf = TableType(tuple(out_types))
    if klykh__ars:
        uay__ubimf = types.none
    if index_column_index is not None:
        cfp__hhow = hlq__jsj[index_column_index]
        hex__kgxvu = (
            f'info_to_array(info_from_table(out_table, {cfp__hhow}), index_arr_type)'
            )
    cxqco__ezvuz += f'    index_arr = {hex__kgxvu}\n'
    if klykh__ars:
        esv__rzqc = None
    else:
        esv__rzqc = []
        sjd__aaeg = 0
        udp__deftm = col_indices[col_names.index(input_file_name_col)
            ] if input_file_name_col is not None else None
        for hylt__vbmoj, lcvn__awp in enumerate(col_indices):
            if sjd__aaeg < len(type_usecol_offset
                ) and hylt__vbmoj == type_usecol_offset[sjd__aaeg]:
                qnhw__ydey = col_indices[hylt__vbmoj]
                if udp__deftm and qnhw__ydey == udp__deftm:
                    esv__rzqc.append(len(ekn__knksl) + len(ione__sjaao))
                elif qnhw__ydey in dtvff__qwtk:
                    svya__qzw = nda__fxbnt[hylt__vbmoj]
                    esv__rzqc.append(len(ekn__knksl) + vtxz__wuhq[svya__qzw])
                else:
                    esv__rzqc.append(hlq__jsj[lcvn__awp])
                sjd__aaeg += 1
            else:
                esv__rzqc.append(-1)
        esv__rzqc = np.array(esv__rzqc, dtype=np.int64)
    if klykh__ars:
        cxqco__ezvuz += '    T = None\n'
    else:
        cxqco__ezvuz += f"""    T = cpp_table_to_py_table(out_table, table_idx_{sqpot__syp}, py_table_type_{sqpot__syp})
"""
    cxqco__ezvuz += f'    delete_table(out_table)\n'
    cxqco__ezvuz += f'    total_rows = total_rows_np[0]\n'
    cxqco__ezvuz += f'    ev.finalize()\n'
    cxqco__ezvuz += f'    return (total_rows, T, index_arr)\n'
    ula__qicuu = {}
    npgkv__uial = {f'py_table_type_{sqpot__syp}': uay__ubimf,
        f'table_idx_{sqpot__syp}': esv__rzqc,
        f'selected_cols_arr_{sqpot__syp}': np.array(ekn__knksl, np.int32),
        f'nullable_cols_arr_{sqpot__syp}': np.array(uosfv__txbp, np.int32),
        'index_arr_type': wit__rxg, 'cpp_table_to_py_table':
        cpp_table_to_py_table, 'info_to_array': info_to_array,
        'info_from_table': info_from_table, 'delete_table': delete_table,
        'check_and_propagate_cpp_exception':
        check_and_propagate_cpp_exception, 'pq_read': _pq_read,
        'unicode_to_utf8': unicode_to_utf8, 'get_filters_pyobject':
        get_filters_pyobject, 'get_storage_options_pyobject':
        get_storage_options_pyobject, 'get_fname_pyobject':
        get_fname_pyobject, 'np': np, 'pd': pd, 'bodo': bodo}
    exec(cxqco__ezvuz, npgkv__uial, ula__qicuu)
    yoasx__mgw = ula__qicuu['pq_reader_py']
    wbdeb__keyzm = numba.njit(yoasx__mgw, no_cpython_wrapper=True)
    return wbdeb__keyzm


import pyarrow as pa
_pa_numba_typ_map = {pa.bool_(): types.bool_, pa.int8(): types.int8, pa.
    int16(): types.int16, pa.int32(): types.int32, pa.int64(): types.int64,
    pa.uint8(): types.uint8, pa.uint16(): types.uint16, pa.uint32(): types.
    uint32, pa.uint64(): types.uint64, pa.float32(): types.float32, pa.
    float64(): types.float64, pa.string(): string_type, pa.binary():
    bytes_type, pa.date32(): datetime_date_type, pa.date64(): types.
    NPDatetime('ns'), null(): string_type}


def get_arrow_timestamp_type(pa_ts_typ):
    ocdf__hsok = 'ns', 'us', 'ms', 's'
    if pa_ts_typ.unit not in ocdf__hsok:
        return types.Array(bodo.datetime64ns, 1, 'C'), False
    elif pa_ts_typ.tz is not None:
        dhbtm__ztxf = pa_ts_typ.to_pandas_dtype().tz
        hst__qlp = bodo.libs.pd_datetime_arr_ext.get_pytz_type_info(dhbtm__ztxf
            )
        return bodo.DatetimeArrayType(hst__qlp), True
    else:
        return types.Array(bodo.datetime64ns, 1, 'C'), True


def _get_numba_typ_from_pa_typ(pa_typ, is_index, nullable_from_metadata,
    category_info, str_as_dict=False):
    if isinstance(pa_typ.type, pa.ListType):
        msp__mznkr, hqwax__ahi = _get_numba_typ_from_pa_typ(pa_typ.type.
            value_field, is_index, nullable_from_metadata, category_info)
        return ArrayItemArrayType(msp__mznkr), hqwax__ahi
    if isinstance(pa_typ.type, pa.StructType):
        uipl__jti = []
        kuir__fibhz = []
        hqwax__ahi = True
        for zzyrn__wlqrx in pa_typ.flatten():
            kuir__fibhz.append(zzyrn__wlqrx.name.split('.')[-1])
            colc__veee, rpf__jcg = _get_numba_typ_from_pa_typ(zzyrn__wlqrx,
                is_index, nullable_from_metadata, category_info)
            uipl__jti.append(colc__veee)
            hqwax__ahi = hqwax__ahi and rpf__jcg
        return StructArrayType(tuple(uipl__jti), tuple(kuir__fibhz)
            ), hqwax__ahi
    if isinstance(pa_typ.type, pa.Decimal128Type):
        return DecimalArrayType(pa_typ.type.precision, pa_typ.type.scale), True
    if str_as_dict:
        if pa_typ.type != pa.string():
            raise BodoError(
                f'Read as dictionary used for non-string column {pa_typ}')
        return dict_str_arr_type, True
    if isinstance(pa_typ.type, pa.DictionaryType):
        if pa_typ.type.value_type != pa.string():
            raise BodoError(
                f'Parquet Categorical data type should be string, not {pa_typ.type.value_type}'
                )
        dckx__xjtgr = _pa_numba_typ_map[pa_typ.type.index_type]
        kwi__iimy = PDCategoricalDtype(category_info[pa_typ.name], bodo.
            string_type, pa_typ.type.ordered, int_type=dckx__xjtgr)
        return CategoricalArrayType(kwi__iimy), True
    if isinstance(pa_typ.type, pa.lib.TimestampType):
        return get_arrow_timestamp_type(pa_typ.type)
    elif pa_typ.type in _pa_numba_typ_map:
        jfo__trp = _pa_numba_typ_map[pa_typ.type]
        hqwax__ahi = True
    else:
        raise BodoError('Arrow data type {} not supported yet'.format(
            pa_typ.type))
    if jfo__trp == datetime_date_type:
        return datetime_date_array_type, hqwax__ahi
    if jfo__trp == bytes_type:
        return binary_array_type, hqwax__ahi
    msp__mznkr = string_array_type if jfo__trp == string_type else types.Array(
        jfo__trp, 1, 'C')
    if jfo__trp == types.bool_:
        msp__mznkr = boolean_array
    if nullable_from_metadata is not None:
        xddkz__daokh = nullable_from_metadata
    else:
        xddkz__daokh = use_nullable_int_arr
    if xddkz__daokh and not is_index and isinstance(jfo__trp, types.Integer
        ) and pa_typ.nullable:
        msp__mznkr = IntegerArrayType(jfo__trp)
    return msp__mznkr, hqwax__ahi


def get_parquet_dataset(fpath, get_row_counts=True, dnf_filters=None,
    expr_filters=None, storage_options=None, read_categories=False,
    is_parallel=False, tot_rows_to_read=None):
    if get_row_counts:
        qgu__uehiq = tracing.Event('get_parquet_dataset')
    import time
    import pyarrow as pa
    import pyarrow.parquet as pq
    from mpi4py import MPI
    jhuye__gyws = MPI.COMM_WORLD
    if isinstance(fpath, list):
        eltx__fotn = urlparse(fpath[0])
        protocol = eltx__fotn.scheme
        wzxgz__ilqtz = eltx__fotn.netloc
        for hylt__vbmoj in range(len(fpath)):
            jgno__iek = fpath[hylt__vbmoj]
            egfzo__ljn = urlparse(jgno__iek)
            if egfzo__ljn.scheme != protocol:
                raise BodoError(
                    'All parquet files must use the same filesystem protocol')
            if egfzo__ljn.netloc != wzxgz__ilqtz:
                raise BodoError(
                    'All parquet files must be in the same S3 bucket')
            fpath[hylt__vbmoj] = jgno__iek.rstrip('/')
    else:
        eltx__fotn = urlparse(fpath)
        protocol = eltx__fotn.scheme
        fpath = fpath.rstrip('/')
    if protocol in {'gcs', 'gs'}:
        try:
            import gcsfs
        except ImportError as ryjiy__dfkvn:
            vgcf__bqbv = """Couldn't import gcsfs, which is required for Google cloud access. gcsfs can be installed by calling 'conda install -c conda-forge gcsfs'.
"""
            raise BodoError(vgcf__bqbv)
    if protocol == 'http':
        try:
            import fsspec
        except ImportError as ryjiy__dfkvn:
            vgcf__bqbv = """Couldn't import fsspec, which is required for http access. fsspec can be installed by calling 'conda install -c conda-forge fsspec'.
"""
    fs = []

    def getfs(parallel=False):
        if len(fs) == 1:
            return fs[0]
        if protocol == 's3':
            fs.append(get_s3_fs_from_path(fpath, parallel=parallel,
                storage_options=storage_options) if not isinstance(fpath,
                list) else get_s3_fs_from_path(fpath[0], parallel=parallel,
                storage_options=storage_options))
        elif protocol in {'gcs', 'gs'}:
            txvx__kiw = gcsfs.GCSFileSystem(token=None)
            fs.append(txvx__kiw)
        elif protocol == 'http':
            fs.append(fsspec.filesystem('http'))
        elif protocol in {'hdfs', 'abfs', 'abfss'}:
            fs.append(get_hdfs_fs(fpath) if not isinstance(fpath, list) else
                get_hdfs_fs(fpath[0]))
        else:
            fs.append(None)
        return fs[0]

    def get_legacy_fs():
        if protocol in {'s3', 'hdfs', 'abfs', 'abfss'}:
            from fsspec.implementations.arrow import ArrowFSWrapper
            return ArrowFSWrapper(getfs())
        else:
            return getfs()

    def glob(protocol, fs, path):
        if not protocol and fs is None:
            from fsspec.implementations.local import LocalFileSystem
            fs = LocalFileSystem()
        if isinstance(fs, pyarrow.fs.FileSystem):
            from fsspec.implementations.arrow import ArrowFSWrapper
            fs = ArrowFSWrapper(fs)
        try:
            if protocol in {'hdfs', 'abfs', 'abfss'}:
                prefix = f'{protocol}://{eltx__fotn.netloc}'
                path = path[len(prefix):]
            ssj__pnb = fs.glob(path)
            if protocol == 's3':
                ssj__pnb = [('s3://' + jgno__iek) for jgno__iek in ssj__pnb if
                    not jgno__iek.startswith('s3://')]
            elif protocol in {'hdfs', 'abfs', 'abfss'}:
                ssj__pnb = [(prefix + jgno__iek) for jgno__iek in ssj__pnb]
        except:
            raise BodoError(
                f'glob pattern expansion not supported for {protocol}')
        if len(ssj__pnb) == 0:
            raise BodoError('No files found matching glob pattern')
        return ssj__pnb
    sig__dgm = False
    if get_row_counts:
        num__ioir = getfs(parallel=True)
        sig__dgm = bodo.parquet_validate_schema
    if bodo.get_rank() == 0:
        ugm__nfs = 1
        vzvb__snvng = os.cpu_count()
        if vzvb__snvng is not None and vzvb__snvng > 1:
            ugm__nfs = vzvb__snvng // 2
        try:
            if get_row_counts:
                jcbx__fklco = tracing.Event('pq.ParquetDataset',
                    is_parallel=False)
                if tracing.is_tracing():
                    jcbx__fklco.add_attribute('dnf_filter', str(dnf_filters))
            rraan__tdpk = pa.io_thread_count()
            pa.set_io_thread_count(ugm__nfs)
            if '*' in fpath:
                fpath = glob(protocol, getfs(), fpath)
            if protocol == 's3':
                if isinstance(fpath, list):
                    get_legacy_fs().info(fpath[0])
                else:
                    get_legacy_fs().info(fpath)
            if protocol in {'hdfs', 'abfs', 'abfss'}:
                prefix = f'{protocol}://{eltx__fotn.netloc}'
                if isinstance(fpath, list):
                    kafip__gbykc = [jgno__iek[len(prefix):] for jgno__iek in
                        fpath]
                else:
                    kafip__gbykc = fpath[len(prefix):]
            else:
                kafip__gbykc = fpath
            ejm__sqv = pq.ParquetDataset(kafip__gbykc, filesystem=
                get_legacy_fs(), filters=None, use_legacy_dataset=True,
                validate_schema=False, metadata_nthreads=ugm__nfs)
            pa.set_io_thread_count(rraan__tdpk)
            oih__sssfq = bodo.io.pa_parquet.get_dataset_schema(ejm__sqv)
            if dnf_filters:
                if get_row_counts:
                    jcbx__fklco.add_attribute('num_pieces_before_filter',
                        len(ejm__sqv.pieces))
                lgsp__qgbs = time.time()
                ejm__sqv._filter(dnf_filters)
                if get_row_counts:
                    jcbx__fklco.add_attribute('dnf_filter_time', time.time(
                        ) - lgsp__qgbs)
                    jcbx__fklco.add_attribute('num_pieces_after_filter',
                        len(ejm__sqv.pieces))
            if get_row_counts:
                jcbx__fklco.finalize()
            ejm__sqv._metadata.fs = None
        except Exception as qst__yibi:
            jhuye__gyws.bcast(qst__yibi)
            raise BodoError(
                f'error from pyarrow: {type(qst__yibi).__name__}: {str(qst__yibi)}\n'
                )
        if get_row_counts:
            betiz__ownz = tracing.Event('bcast dataset')
        jhuye__gyws.bcast(ejm__sqv)
        jhuye__gyws.bcast(oih__sssfq)
    else:
        if get_row_counts:
            betiz__ownz = tracing.Event('bcast dataset')
        ejm__sqv = jhuye__gyws.bcast(None)
        if isinstance(ejm__sqv, Exception):
            elu__ugu = ejm__sqv
            raise BodoError(
                f'error from pyarrow: {type(elu__ugu).__name__}: {str(elu__ugu)}\n'
                )
        oih__sssfq = jhuye__gyws.bcast(None)
    if get_row_counts:
        qche__yapnr = getfs()
    else:
        qche__yapnr = get_legacy_fs()
    ejm__sqv._metadata.fs = qche__yapnr
    if get_row_counts:
        betiz__ownz.finalize()
    ejm__sqv._bodo_total_rows = 0
    if get_row_counts and tot_rows_to_read == 0:
        get_row_counts = sig__dgm = False
        for gerjn__tpive in ejm__sqv.pieces:
            gerjn__tpive._bodo_num_rows = 0
    if get_row_counts or sig__dgm:
        if get_row_counts and tracing.is_tracing():
            klmzl__pzc = tracing.Event('get_row_counts')
            klmzl__pzc.add_attribute('g_num_pieces', len(ejm__sqv.pieces))
            klmzl__pzc.add_attribute('g_expr_filters', str(expr_filters))
        qyd__vrzza = 0.0
        num_pieces = len(ejm__sqv.pieces)
        start = get_start(num_pieces, bodo.get_size(), bodo.get_rank())
        kksn__jox = get_end(num_pieces, bodo.get_size(), bodo.get_rank())
        yswy__qmgt = 0
        gkymf__hxhhr = 0
        nypp__fat = 0
        kawxu__xus = True
        if expr_filters is not None:
            import random
            random.seed(37)
            ulj__ltu = random.sample(ejm__sqv.pieces, k=len(ejm__sqv.pieces))
        else:
            ulj__ltu = ejm__sqv.pieces
        for gerjn__tpive in ulj__ltu:
            gerjn__tpive._bodo_num_rows = 0
        fpaths = [gerjn__tpive.path for gerjn__tpive in ulj__ltu[start:
            kksn__jox]]
        if protocol == 's3':
            wzxgz__ilqtz = eltx__fotn.netloc
            prefix = 's3://' + wzxgz__ilqtz + '/'
            fpaths = [jgno__iek[len(prefix):] for jgno__iek in fpaths]
            qche__yapnr = get_s3_subtree_fs(wzxgz__ilqtz, region=getfs().
                region, storage_options=storage_options)
        else:
            qche__yapnr = getfs()
        pa.set_io_thread_count(4)
        pa.set_cpu_count(4)
        msq__ase = ds.dataset(fpaths, filesystem=qche__yapnr, partitioning=
            ds.partitioning(flavor='hive'))
        for uchzj__ryysf, idlwc__zim in zip(ulj__ltu[start:kksn__jox],
            msq__ase.get_fragments()):
            lgsp__qgbs = time.time()
            vnok__avelc = idlwc__zim.scanner(schema=msq__ase.schema, filter
                =expr_filters, use_threads=True).count_rows()
            qyd__vrzza += time.time() - lgsp__qgbs
            uchzj__ryysf._bodo_num_rows = vnok__avelc
            yswy__qmgt += vnok__avelc
            gkymf__hxhhr += idlwc__zim.num_row_groups
            nypp__fat += sum(pwk__ygogs.total_byte_size for pwk__ygogs in
                idlwc__zim.row_groups)
            if sig__dgm:
                wvohw__vzyl = idlwc__zim.metadata.schema.to_arrow_schema()
                if oih__sssfq != wvohw__vzyl:
                    print('Schema in {!s} was different. \n{!s}\n\nvs\n\n{!s}'
                        .format(uchzj__ryysf, wvohw__vzyl, oih__sssfq))
                    kawxu__xus = False
                    break
        if sig__dgm:
            kawxu__xus = jhuye__gyws.allreduce(kawxu__xus, op=MPI.LAND)
            if not kawxu__xus:
                raise BodoError("Schema in parquet files don't match")
        if get_row_counts:
            ejm__sqv._bodo_total_rows = jhuye__gyws.allreduce(yswy__qmgt,
                op=MPI.SUM)
            vzrrs__ypbm = jhuye__gyws.allreduce(gkymf__hxhhr, op=MPI.SUM)
            fsogq__jxp = jhuye__gyws.allreduce(nypp__fat, op=MPI.SUM)
            ylals__pokxk = np.array([gerjn__tpive._bodo_num_rows for
                gerjn__tpive in ejm__sqv.pieces])
            ylals__pokxk = jhuye__gyws.allreduce(ylals__pokxk, op=MPI.SUM)
            for gerjn__tpive, wosvb__cur in zip(ejm__sqv.pieces, ylals__pokxk):
                gerjn__tpive._bodo_num_rows = wosvb__cur
            if is_parallel and bodo.get_rank(
                ) == 0 and vzrrs__ypbm < bodo.get_size() and vzrrs__ypbm != 0:
                warnings.warn(BodoWarning(
                    f"""Total number of row groups in parquet dataset {fpath} ({vzrrs__ypbm}) is too small for effective IO parallelization.
For best performance the number of row groups should be greater than the number of workers ({bodo.get_size()})
"""
                    ))
            if vzrrs__ypbm == 0:
                evem__xsm = 0
            else:
                evem__xsm = fsogq__jxp // vzrrs__ypbm
            if (bodo.get_rank() == 0 and fsogq__jxp >= 20 * 1048576 and 
                evem__xsm < 1048576 and protocol in REMOTE_FILESYSTEMS):
                warnings.warn(BodoWarning(
                    f'Parquet average row group size is small ({evem__xsm} bytes) and can have negative impact on performance when reading from remote sources'
                    ))
            if tracing.is_tracing():
                klmzl__pzc.add_attribute('g_total_num_row_groups', vzrrs__ypbm)
                if expr_filters is not None:
                    klmzl__pzc.add_attribute('total_scan_time', qyd__vrzza)
                anae__vnhne = np.array([gerjn__tpive._bodo_num_rows for
                    gerjn__tpive in ejm__sqv.pieces])
                bcxw__qysyn = np.percentile(anae__vnhne, [25, 50, 75])
                klmzl__pzc.add_attribute('g_row_counts_min', anae__vnhne.min())
                klmzl__pzc.add_attribute('g_row_counts_Q1', bcxw__qysyn[0])
                klmzl__pzc.add_attribute('g_row_counts_median', bcxw__qysyn[1])
                klmzl__pzc.add_attribute('g_row_counts_Q3', bcxw__qysyn[2])
                klmzl__pzc.add_attribute('g_row_counts_max', anae__vnhne.max())
                klmzl__pzc.add_attribute('g_row_counts_mean', anae__vnhne.
                    mean())
                klmzl__pzc.add_attribute('g_row_counts_std', anae__vnhne.std())
                klmzl__pzc.add_attribute('g_row_counts_sum', anae__vnhne.sum())
                klmzl__pzc.finalize()
    ejm__sqv._prefix = ''
    if protocol in {'hdfs', 'abfs', 'abfss'}:
        prefix = f'{protocol}://{eltx__fotn.netloc}'
        if len(ejm__sqv.pieces) > 0:
            uchzj__ryysf = ejm__sqv.pieces[0]
            if not uchzj__ryysf.path.startswith(prefix):
                ejm__sqv._prefix = prefix
    if read_categories:
        _add_categories_to_pq_dataset(ejm__sqv)
    if get_row_counts:
        qgu__uehiq.finalize()
    return ejm__sqv


def get_scanner_batches(fpaths, expr_filters, selected_fields,
    avg_num_pieces, is_parallel, storage_options, region, prefix,
    str_as_dict_cols, start_offset, rows_to_read):
    import pyarrow as pa
    vzvb__snvng = os.cpu_count()
    if vzvb__snvng is None or vzvb__snvng == 0:
        vzvb__snvng = 2
    biu__pgo = min(4, vzvb__snvng)
    lvgy__fmcr = min(16, vzvb__snvng)
    if is_parallel and len(fpaths) > lvgy__fmcr and len(fpaths
        ) / avg_num_pieces >= 2.0:
        pa.set_io_thread_count(lvgy__fmcr)
        pa.set_cpu_count(lvgy__fmcr)
    else:
        pa.set_io_thread_count(biu__pgo)
        pa.set_cpu_count(biu__pgo)
    if fpaths[0].startswith('s3://'):
        wzxgz__ilqtz = urlparse(fpaths[0]).netloc
        prefix = 's3://' + wzxgz__ilqtz + '/'
        fpaths = [jgno__iek[len(prefix):] for jgno__iek in fpaths]
        qche__yapnr = get_s3_subtree_fs(wzxgz__ilqtz, region=region,
            storage_options=storage_options)
    elif prefix and prefix.startswith(('hdfs', 'abfs', 'abfss')):
        qche__yapnr = get_hdfs_fs(prefix + fpaths[0])
    elif fpaths[0].startswith(('gcs', 'gs')):
        import gcsfs
        qche__yapnr = gcsfs.GCSFileSystem(token=None)
    else:
        qche__yapnr = None
    esbu__txt = ds.ParquetFileFormat(dictionary_columns=str_as_dict_cols)
    ejm__sqv = ds.dataset(fpaths, filesystem=qche__yapnr, partitioning=ds.
        partitioning(flavor='hive'), format=esbu__txt)
    col_names = ejm__sqv.schema.names
    lto__qms = [col_names[zsdjy__vojo] for zsdjy__vojo in selected_fields]
    qeajq__dbory = len(fpaths) <= 3 or start_offset > 0 and len(fpaths) <= 10
    if qeajq__dbory and expr_filters is None:
        pxzsx__kqriz = []
        xqzo__qgbr = 0
        ago__vdfqh = 0
        for idlwc__zim in ejm__sqv.get_fragments():
            ngho__mytzj = []
            for pwk__ygogs in idlwc__zim.row_groups:
                jeq__egq = pwk__ygogs.num_rows
                if start_offset < xqzo__qgbr + jeq__egq:
                    if ago__vdfqh == 0:
                        diqe__ixeg = start_offset - xqzo__qgbr
                        uudi__mjayb = min(jeq__egq - diqe__ixeg, rows_to_read)
                    else:
                        uudi__mjayb = min(jeq__egq, rows_to_read - ago__vdfqh)
                    ago__vdfqh += uudi__mjayb
                    ngho__mytzj.append(pwk__ygogs.id)
                xqzo__qgbr += jeq__egq
                if ago__vdfqh == rows_to_read:
                    break
            pxzsx__kqriz.append(idlwc__zim.subset(row_group_ids=ngho__mytzj))
            if ago__vdfqh == rows_to_read:
                break
        ejm__sqv = ds.FileSystemDataset(pxzsx__kqriz, ejm__sqv.schema,
            esbu__txt, filesystem=ejm__sqv.filesystem)
        start_offset = diqe__ixeg
    xhaax__vmjfi = ejm__sqv.scanner(columns=lto__qms, filter=expr_filters,
        use_threads=True).to_reader()
    return ejm__sqv, xhaax__vmjfi, start_offset


def _add_categories_to_pq_dataset(pq_dataset):
    import pyarrow as pa
    from mpi4py import MPI
    if len(pq_dataset.pieces) < 1:
        raise BodoError(
            'No pieces found in Parquet dataset. Cannot get read categorical values'
            )
    pa_schema = pq_dataset.schema.to_arrow_schema()
    snnxj__tile = [c for c in pa_schema.names if isinstance(pa_schema.field
        (c).type, pa.DictionaryType)]
    if len(snnxj__tile) == 0:
        pq_dataset._category_info = {}
        return
    jhuye__gyws = MPI.COMM_WORLD
    if bodo.get_rank() == 0:
        try:
            ezflk__zbmn = pq_dataset.pieces[0].open()
            pwk__ygogs = ezflk__zbmn.read_row_group(0, snnxj__tile)
            category_info = {c: tuple(pwk__ygogs.column(c).chunk(0).
                dictionary.to_pylist()) for c in snnxj__tile}
            del ezflk__zbmn, pwk__ygogs
        except Exception as qst__yibi:
            jhuye__gyws.bcast(qst__yibi)
            raise qst__yibi
        jhuye__gyws.bcast(category_info)
    else:
        category_info = jhuye__gyws.bcast(None)
        if isinstance(category_info, Exception):
            elu__ugu = category_info
            raise elu__ugu
    pq_dataset._category_info = category_info


def get_pandas_metadata(schema, num_pieces):
    jhbc__mnwz = None
    nullable_from_metadata = defaultdict(lambda : None)
    xev__snltk = b'pandas'
    if schema.metadata is not None and xev__snltk in schema.metadata:
        import json
        sig__qngxp = json.loads(schema.metadata[xev__snltk].decode('utf8'))
        rayn__jpi = len(sig__qngxp['index_columns'])
        if rayn__jpi > 1:
            raise BodoError('read_parquet: MultiIndex not supported yet')
        jhbc__mnwz = sig__qngxp['index_columns'][0] if rayn__jpi else None
        if not isinstance(jhbc__mnwz, str) and (not isinstance(jhbc__mnwz,
            dict) or num_pieces != 1):
            jhbc__mnwz = None
        for amiyp__kwau in sig__qngxp['columns']:
            evxq__iryy = amiyp__kwau['name']
            if amiyp__kwau['pandas_type'].startswith('int'
                ) and evxq__iryy is not None:
                if amiyp__kwau['numpy_type'].startswith('Int'):
                    nullable_from_metadata[evxq__iryy] = True
                else:
                    nullable_from_metadata[evxq__iryy] = False
    return jhbc__mnwz, nullable_from_metadata


def determine_str_as_dict_columns(pq_dataset, pa_schema):
    from mpi4py import MPI
    jhuye__gyws = MPI.COMM_WORLD
    eduvp__rrvkq = []
    for evxq__iryy in pa_schema.names:
        zzyrn__wlqrx = pa_schema.field(evxq__iryy)
        if zzyrn__wlqrx.type == pa.string():
            eduvp__rrvkq.append((evxq__iryy, pa_schema.get_field_index(
                evxq__iryy)))
    if len(eduvp__rrvkq) == 0:
        return set()
    if len(pq_dataset.pieces) > bodo.get_size():
        import random
        random.seed(37)
        ulj__ltu = random.sample(pq_dataset.pieces, bodo.get_size())
    else:
        ulj__ltu = pq_dataset.pieces
    red__uhwrf = np.zeros(len(eduvp__rrvkq), dtype=np.int64)
    ect__naco = np.zeros(len(eduvp__rrvkq), dtype=np.int64)
    if bodo.get_rank() < len(ulj__ltu):
        uchzj__ryysf = ulj__ltu[bodo.get_rank()]
        rep__gsp = uchzj__ryysf.get_metadata()
        for hylt__vbmoj in range(rep__gsp.num_row_groups):
            for sjd__aaeg, (num__ioir, zyo__zkbpo) in enumerate(eduvp__rrvkq):
                red__uhwrf[sjd__aaeg] += rep__gsp.row_group(hylt__vbmoj
                    ).column(zyo__zkbpo).total_uncompressed_size
        gdwhv__zjxo = rep__gsp.num_rows
    else:
        gdwhv__zjxo = 0
    qrl__huuk = jhuye__gyws.allreduce(gdwhv__zjxo, op=MPI.SUM)
    if qrl__huuk == 0:
        return set()
    jhuye__gyws.Allreduce(red__uhwrf, ect__naco, op=MPI.SUM)
    kec__aqzs = ect__naco / qrl__huuk
    str_as_dict = set()
    for hylt__vbmoj, vqyfp__mnx in enumerate(kec__aqzs):
        if vqyfp__mnx < READ_STR_AS_DICT_THRESHOLD:
            evxq__iryy = eduvp__rrvkq[hylt__vbmoj][0]
            str_as_dict.add(evxq__iryy)
    return str_as_dict


def parquet_file_schema(file_name, selected_columns, storage_options=None,
    input_file_name_col=None):
    col_names = []
    luh__mva = []
    pq_dataset = get_parquet_dataset(file_name, get_row_counts=False,
        storage_options=storage_options, read_categories=True)
    partition_names = [] if pq_dataset.partitions is None else [pq_dataset.
        partitions.levels[hylt__vbmoj].name for hylt__vbmoj in range(len(
        pq_dataset.partitions.partition_names))]
    pa_schema = pq_dataset.schema.to_arrow_schema()
    num_pieces = len(pq_dataset.pieces)
    str_as_dict = determine_str_as_dict_columns(pq_dataset, pa_schema)
    col_names = pa_schema.names
    jhbc__mnwz, nullable_from_metadata = get_pandas_metadata(pa_schema,
        num_pieces)
    oken__owom = []
    dbhcf__mysa = []
    bmagn__ceqo = []
    for hylt__vbmoj, c in enumerate(col_names):
        zzyrn__wlqrx = pa_schema.field(c)
        jfo__trp, hqwax__ahi = _get_numba_typ_from_pa_typ(zzyrn__wlqrx, c ==
            jhbc__mnwz, nullable_from_metadata[c], pq_dataset.
            _category_info, str_as_dict=c in str_as_dict)
        oken__owom.append(jfo__trp)
        dbhcf__mysa.append(hqwax__ahi)
        bmagn__ceqo.append(zzyrn__wlqrx.type)
    if partition_names:
        col_names += partition_names
        oken__owom += [_get_partition_cat_dtype(pq_dataset.partitions.
            levels[hylt__vbmoj]) for hylt__vbmoj in range(len(partition_names))
            ]
        dbhcf__mysa.extend([True] * len(partition_names))
        bmagn__ceqo.extend([None] * len(partition_names))
    if input_file_name_col is not None:
        col_names += [input_file_name_col]
        oken__owom += [dict_str_arr_type]
        dbhcf__mysa.append(True)
        bmagn__ceqo.append(None)
    bie__kkfp = {c: hylt__vbmoj for hylt__vbmoj, c in enumerate(col_names)}
    if selected_columns is None:
        selected_columns = col_names
    for c in selected_columns:
        if c not in bie__kkfp:
            raise BodoError(f'Selected column {c} not in Parquet file schema')
    if jhbc__mnwz and not isinstance(jhbc__mnwz, dict
        ) and jhbc__mnwz not in selected_columns:
        selected_columns.append(jhbc__mnwz)
    col_names = selected_columns
    col_indices = []
    luh__mva = []
    gxaph__midlw = []
    kbatm__zof = []
    for hylt__vbmoj, c in enumerate(col_names):
        qnhw__ydey = bie__kkfp[c]
        col_indices.append(qnhw__ydey)
        luh__mva.append(oken__owom[qnhw__ydey])
        if not dbhcf__mysa[qnhw__ydey]:
            gxaph__midlw.append(hylt__vbmoj)
            kbatm__zof.append(bmagn__ceqo[qnhw__ydey])
    return (col_names, luh__mva, jhbc__mnwz, col_indices, partition_names,
        gxaph__midlw, kbatm__zof)


def _get_partition_cat_dtype(part_set):
    ijffl__ktql = part_set.dictionary.to_pandas()
    mmml__gpq = bodo.typeof(ijffl__ktql).dtype
    kwi__iimy = PDCategoricalDtype(tuple(ijffl__ktql), mmml__gpq, False)
    return CategoricalArrayType(kwi__iimy)


_pq_read = types.ExternalFunction('pq_read', table_type(
    read_parquet_fpath_type, types.boolean, types.voidptr,
    parquet_predicate_type, parquet_predicate_type,
    storage_options_dict_type, types.int64, types.voidptr, types.int32,
    types.voidptr, types.voidptr, types.voidptr, types.int32, types.voidptr,
    types.int32, types.voidptr, types.boolean))
from llvmlite import ir as lir
from numba.core import cgutils
if bodo.utils.utils.has_pyarrow():
    from bodo.io import arrow_cpp
    ll.add_symbol('pq_read', arrow_cpp.pq_read)
    ll.add_symbol('pq_write', arrow_cpp.pq_write)
    ll.add_symbol('pq_write_partitioned', arrow_cpp.pq_write_partitioned)


@intrinsic
def parquet_write_table_cpp(typingctx, filename_t, table_t, col_names_t,
    index_t, write_index, metadata_t, compression_t, is_parallel_t,
    write_range_index, start, stop, step, name, bucket_region):

    def codegen(context, builder, sig, args):
        xfzqe__maa = lir.FunctionType(lir.VoidType(), [lir.IntType(8).
            as_pointer(), lir.IntType(8).as_pointer(), lir.IntType(8).
            as_pointer(), lir.IntType(8).as_pointer(), lir.IntType(1), lir.
            IntType(8).as_pointer(), lir.IntType(8).as_pointer(), lir.
            IntType(1), lir.IntType(1), lir.IntType(32), lir.IntType(32),
            lir.IntType(32), lir.IntType(8).as_pointer(), lir.IntType(8).
            as_pointer()])
        mtnuy__vzsd = cgutils.get_or_insert_function(builder.module,
            xfzqe__maa, name='pq_write')
        builder.call(mtnuy__vzsd, args)
        bodo.utils.utils.inlined_check_and_propagate_cpp_exception(context,
            builder)
    return types.void(types.voidptr, table_t, col_names_t, index_t, types.
        boolean, types.voidptr, types.voidptr, types.boolean, types.boolean,
        types.int32, types.int32, types.int32, types.voidptr, types.voidptr
        ), codegen


@intrinsic
def parquet_write_table_partitioned_cpp(typingctx, filename_t, data_table_t,
    col_names_t, col_names_no_partitions_t, cat_table_t, part_col_idxs_t,
    num_part_col_t, compression_t, is_parallel_t, bucket_region):

    def codegen(context, builder, sig, args):
        xfzqe__maa = lir.FunctionType(lir.VoidType(), [lir.IntType(8).
            as_pointer(), lir.IntType(8).as_pointer(), lir.IntType(8).
            as_pointer(), lir.IntType(8).as_pointer(), lir.IntType(8).
            as_pointer(), lir.IntType(8).as_pointer(), lir.IntType(32), lir
            .IntType(8).as_pointer(), lir.IntType(1), lir.IntType(8).
            as_pointer()])
        mtnuy__vzsd = cgutils.get_or_insert_function(builder.module,
            xfzqe__maa, name='pq_write_partitioned')
        builder.call(mtnuy__vzsd, args)
        bodo.utils.utils.inlined_check_and_propagate_cpp_exception(context,
            builder)
    return types.void(types.voidptr, data_table_t, col_names_t,
        col_names_no_partitions_t, cat_table_t, types.voidptr, types.int32,
        types.voidptr, types.boolean, types.voidptr), codegen
