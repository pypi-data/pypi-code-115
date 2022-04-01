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
        except OSError as gvgg__fms:
            if 'non-file path' in str(gvgg__fms):
                raise FileNotFoundError(str(gvgg__fms))
            raise


class ParquetHandler:

    def __init__(self, func_ir, typingctx, args, _locals):
        self.func_ir = func_ir
        self.typingctx = typingctx
        self.args = args
        self.locals = _locals

    def gen_parquet_read(self, file_name, lhs, columns, storage_options=
        None, input_file_name_col=None):
        pcohw__innga = lhs.scope
        wadu__ovoz = lhs.loc
        rlgub__yzpk = None
        if lhs.name in self.locals:
            rlgub__yzpk = self.locals[lhs.name]
            self.locals.pop(lhs.name)
        dkf__xwapj = {}
        if lhs.name + ':convert' in self.locals:
            dkf__xwapj = self.locals[lhs.name + ':convert']
            self.locals.pop(lhs.name + ':convert')
        if rlgub__yzpk is None:
            ikgte__nel = (
                'Parquet schema not available. Either path argument should be constant for Bodo to look at the file at compile time or schema should be provided. For more information, see: https://docs.bodo.ai/latest/source/programming_with_bodo/file_io.html#non-constant-filepaths'
                )
            umg__bwlg = get_const_value(file_name, self.func_ir, ikgte__nel,
                arg_types=self.args, file_info=ParquetFileInfo(columns,
                storage_options=storage_options, input_file_name_col=
                input_file_name_col))
            wyw__gvil = False
            msmbz__giwg = guard(get_definition, self.func_ir, file_name)
            if isinstance(msmbz__giwg, ir.Arg):
                typ = self.args[msmbz__giwg.index]
                if isinstance(typ, types.FilenameType):
                    (col_names, vfh__ycnni, jll__kajbm, col_indices,
                        partition_names, zmfp__hatfo, ovl__rfhg) = typ.schema
                    wyw__gvil = True
            if not wyw__gvil:
                (col_names, vfh__ycnni, jll__kajbm, col_indices,
                    partition_names, zmfp__hatfo, ovl__rfhg) = (
                    parquet_file_schema(umg__bwlg, columns, storage_options
                    =storage_options, input_file_name_col=input_file_name_col))
        else:
            fheq__xpif = list(rlgub__yzpk.keys())
            iqhh__heg = {c: lyq__lnhh for lyq__lnhh, c in enumerate(fheq__xpif)
                }
            ytr__xzvw = [imx__jpw for imx__jpw in rlgub__yzpk.values()]
            jll__kajbm = 'index' if 'index' in iqhh__heg else None
            if columns is None:
                selected_columns = fheq__xpif
            else:
                selected_columns = columns
            col_indices = [iqhh__heg[c] for c in selected_columns]
            vfh__ycnni = [ytr__xzvw[iqhh__heg[c]] for c in selected_columns]
            col_names = selected_columns
            jll__kajbm = jll__kajbm if jll__kajbm in col_names else None
            partition_names = []
            zmfp__hatfo = []
            ovl__rfhg = []
        uckam__dbnzm = None if isinstance(jll__kajbm, dict
            ) or jll__kajbm is None else jll__kajbm
        index_column_index = None
        index_column_type = types.none
        if uckam__dbnzm:
            nzzp__oomk = col_names.index(uckam__dbnzm)
            index_column_index = col_indices.pop(nzzp__oomk)
            index_column_type = vfh__ycnni.pop(nzzp__oomk)
            col_names.pop(nzzp__oomk)
        for lyq__lnhh, c in enumerate(col_names):
            if c in dkf__xwapj:
                vfh__ycnni[lyq__lnhh] = dkf__xwapj[c]
        dre__zlsm = [ir.Var(pcohw__innga, mk_unique_var('pq_table'),
            wadu__ovoz), ir.Var(pcohw__innga, mk_unique_var('pq_index'),
            wadu__ovoz)]
        uzvke__ywawz = [bodo.ir.parquet_ext.ParquetReader(file_name, lhs.
            name, col_names, col_indices, vfh__ycnni, dre__zlsm, wadu__ovoz,
            partition_names, storage_options, index_column_index,
            index_column_type, input_file_name_col, zmfp__hatfo, ovl__rfhg)]
        return (col_names, dre__zlsm, jll__kajbm, uzvke__ywawz, vfh__ycnni,
            index_column_type)


def determine_filter_cast(pq_node, typemap, filter_val, orig_colname_map):
    ffe__wyzu = filter_val[0]
    jhz__jnd = pq_node.original_out_types[orig_colname_map[ffe__wyzu]]
    oco__abd = bodo.utils.typing.element_type(jhz__jnd)
    if ffe__wyzu in pq_node.partition_names:
        if oco__abd == types.unicode_type:
            utzt__ewvc = '.cast(pyarrow.string(), safe=False)'
        elif isinstance(oco__abd, types.Integer):
            utzt__ewvc = f'.cast(pyarrow.{oco__abd.name}(), safe=False)'
        else:
            utzt__ewvc = ''
    else:
        utzt__ewvc = ''
    tfsaa__crykx = typemap[filter_val[2].name]
    if isinstance(tfsaa__crykx, (types.List, types.Set)):
        clesr__rbdc = tfsaa__crykx.dtype
    else:
        clesr__rbdc = tfsaa__crykx
    bodo.hiframes.pd_timestamp_ext.check_tz_aware_unsupported(oco__abd,
        'Filter pushdown')
    bodo.hiframes.pd_timestamp_ext.check_tz_aware_unsupported(clesr__rbdc,
        'Filter pushdown')
    if not bodo.utils.typing.is_common_scalar_dtype([oco__abd, clesr__rbdc]):
        if not bodo.utils.typing.is_safe_arrow_cast(oco__abd, clesr__rbdc):
            raise BodoError(
                f'Unsupported Arrow cast from {oco__abd} to {clesr__rbdc} in filter pushdown. Please try a comparison that avoids casting the column.'
                )
        if oco__abd == types.unicode_type:
            return ".cast(pyarrow.timestamp('ns'), safe=False)", ''
        elif oco__abd in (bodo.datetime64ns, bodo.pd_timestamp_type):
            if isinstance(tfsaa__crykx, (types.List, types.Set)):
                lfzr__pvy = 'list' if isinstance(tfsaa__crykx, types.List
                    ) else 'tuple'
                raise BodoError(
                    f'Cannot cast {lfzr__pvy} values with isin filter pushdown.'
                    )
            return utzt__ewvc, ".cast(pyarrow.timestamp('ns'), safe=False)"
    return utzt__ewvc, ''


def pq_distributed_run(pq_node, array_dists, typemap, calltypes, typingctx,
    targetctx, meta_head_only_info=None):
    jogw__vaqaz = len(pq_node.out_vars)
    extra_args = ''
    dnf_filter_str = 'None'
    expr_filter_str = 'None'
    xxaei__yuem, zsjq__dxt = bodo.ir.connector.generate_filter_map(pq_node.
        filters)
    if pq_node.filters:
        ezsc__onv = []
        ekt__uyv = []
        kzctm__sgs = False
        nsj__wlrq = None
        orig_colname_map = {c: lyq__lnhh for lyq__lnhh, c in enumerate(
            pq_node.original_df_colnames)}
        for qhf__xsnqn in pq_node.filters:
            mxhqo__llcno = []
            buii__klvqa = []
            tjwcl__def = set()
            for bjal__zlnf in qhf__xsnqn:
                if isinstance(bjal__zlnf[2], ir.Var):
                    kqcqi__qsx, aoqaz__hao = determine_filter_cast(pq_node,
                        typemap, bjal__zlnf, orig_colname_map)
                    if bjal__zlnf[1] == 'in':
                        buii__klvqa.append(
                            f"(ds.field('{bjal__zlnf[0]}').isin({xxaei__yuem[bjal__zlnf[2].name]}))"
                            )
                    else:
                        buii__klvqa.append(
                            f"(ds.field('{bjal__zlnf[0]}'){kqcqi__qsx} {bjal__zlnf[1]} ds.scalar({xxaei__yuem[bjal__zlnf[2].name]}){aoqaz__hao})"
                            )
                else:
                    assert bjal__zlnf[2
                        ] == 'NULL', 'unsupport constant used in filter pushdown'
                    if bjal__zlnf[1] == 'is not':
                        prefix = '~'
                    else:
                        prefix = ''
                    buii__klvqa.append(
                        f"({prefix}ds.field('{bjal__zlnf[0]}').is_null())")
                if bjal__zlnf[0] in pq_node.partition_names and isinstance(
                    bjal__zlnf[2], ir.Var):
                    bhjn__nhw = (
                        f"('{bjal__zlnf[0]}', '{bjal__zlnf[1]}', {xxaei__yuem[bjal__zlnf[2].name]})"
                        )
                    mxhqo__llcno.append(bhjn__nhw)
                    tjwcl__def.add(bhjn__nhw)
                else:
                    kzctm__sgs = True
            if nsj__wlrq is None:
                nsj__wlrq = tjwcl__def
            else:
                nsj__wlrq.intersection_update(tjwcl__def)
            nub__zarl = ', '.join(mxhqo__llcno)
            aznl__ntpld = ' & '.join(buii__klvqa)
            if nub__zarl:
                ezsc__onv.append(f'[{nub__zarl}]')
            ekt__uyv.append(f'({aznl__ntpld})')
        qtkh__gbxab = ', '.join(ezsc__onv)
        gtv__wsn = ' | '.join(ekt__uyv)
        if kzctm__sgs:
            if nsj__wlrq:
                ianu__cghv = sorted(nsj__wlrq)
                dnf_filter_str = f"[[{', '.join(ianu__cghv)}]]"
        elif qtkh__gbxab:
            dnf_filter_str = f'[{qtkh__gbxab}]'
        expr_filter_str = f'({gtv__wsn})'
        extra_args = ', '.join(xxaei__yuem.values())
    tar__wae = ', '.join(f'out{lyq__lnhh}' for lyq__lnhh in range(jogw__vaqaz))
    rjp__ragd = f'def pq_impl(fname, {extra_args}):\n'
    rjp__ragd += (
        f'    (total_rows, {tar__wae},) = _pq_reader_py(fname, {extra_args})\n'
        )
    dbeb__pzb = {}
    exec(rjp__ragd, {}, dbeb__pzb)
    inu__jvifu = dbeb__pzb['pq_impl']
    if bodo.user_logging.get_verbose_level() >= 1:
        lapzq__slu = pq_node.loc.strformat()
        wqxq__znzs = []
        shh__vqpw = []
        for lyq__lnhh in pq_node.type_usecol_offset:
            ffe__wyzu = pq_node.df_colnames[lyq__lnhh]
            wqxq__znzs.append(ffe__wyzu)
            if isinstance(pq_node.out_types[lyq__lnhh], bodo.libs.
                dict_arr_ext.DictionaryArrayType):
                shh__vqpw.append(ffe__wyzu)
        advg__tha = (
            'Finish column pruning on read_parquet node:\n%s\nColumns loaded %s\n'
            )
        bodo.user_logging.log_message('Column Pruning', advg__tha,
            lapzq__slu, wqxq__znzs)
        if shh__vqpw:
            sqae__pgop = """Finished optimized encoding on read_parquet node:
%s
Columns %s using dictionary encoding to reduce memory usage.
"""
            bodo.user_logging.log_message('Dictionary Encoding', sqae__pgop,
                lapzq__slu, shh__vqpw)
    parallel = False
    if array_dists is not None:
        ecast__zjzi = pq_node.out_vars[0].name
        parallel = array_dists[ecast__zjzi] in (distributed_pass.
            Distribution.OneD, distributed_pass.Distribution.OneD_Var)
        cuv__chrv = pq_node.out_vars[1].name
        assert typemap[cuv__chrv] == types.none or not parallel or array_dists[
            cuv__chrv] in (distributed_pass.Distribution.OneD,
            distributed_pass.Distribution.OneD_Var
            ), 'pq data/index parallelization does not match'
    if pq_node.unsupported_columns:
        zoz__qmy = set(pq_node.type_usecol_offset)
        ryu__lqtz = set(pq_node.unsupported_columns)
        chizj__lpggq = zoz__qmy & ryu__lqtz
        if chizj__lpggq:
            ompn__ofevb = sorted(chizj__lpggq)
            kuck__ixgc = [
                f'pandas.read_parquet(): 1 or more columns found with Arrow types that are not supported in Bodo and could not be eliminated. '
                 +
                "Please manually remove these columns from your read_parquet with the 'columns' argument. If these "
                 +
                'columns are needed, you will need to modify your dataset to use a supported type.'
                , 'Unsupported Columns:']
            turc__txyc = 0
            for fvc__cju in ompn__ofevb:
                while pq_node.unsupported_columns[turc__txyc] != fvc__cju:
                    turc__txyc += 1
                kuck__ixgc.append(
                    f"Column '{pq_node.df_colnames[fvc__cju]}' with unsupported arrow type {pq_node.unsupported_arrow_types[turc__txyc]}"
                    )
                turc__txyc += 1
            zziuq__cnn = '\n'.join(kuck__ixgc)
            raise BodoError(zziuq__cnn, loc=pq_node.loc)
    sbxar__iot = _gen_pq_reader_py(pq_node.df_colnames, pq_node.col_indices,
        pq_node.type_usecol_offset, pq_node.out_types, pq_node.
        storage_options, pq_node.partition_names, dnf_filter_str,
        expr_filter_str, extra_args, parallel, meta_head_only_info, pq_node
        .index_column_index, pq_node.index_column_type, pq_node.
        input_file_name_col)
    othjx__uaa = typemap[pq_node.file_name.name]
    lgb__tef = (othjx__uaa,) + tuple(typemap[bjal__zlnf.name] for
        bjal__zlnf in zsjq__dxt)
    kidaj__unyqt = compile_to_numba_ir(inu__jvifu, {'_pq_reader_py':
        sbxar__iot}, typingctx=typingctx, targetctx=targetctx, arg_typs=
        lgb__tef, typemap=typemap, calltypes=calltypes).blocks.popitem()[1]
    replace_arg_nodes(kidaj__unyqt, [pq_node.file_name] + zsjq__dxt)
    uzvke__ywawz = kidaj__unyqt.body[:-3]
    if meta_head_only_info:
        uzvke__ywawz[-1 - jogw__vaqaz].target = meta_head_only_info[1]
    uzvke__ywawz[-2].target = pq_node.out_vars[0]
    uzvke__ywawz[-1].target = pq_node.out_vars[1]
    return uzvke__ywawz


distributed_pass.distributed_run_extensions[bodo.ir.parquet_ext.ParquetReader
    ] = pq_distributed_run


def get_filters_pyobject(dnf_filter_str, expr_filter_str, vars):
    pass


@overload(get_filters_pyobject, no_unliteral=True)
def overload_get_filters_pyobject(dnf_filter_str, expr_filter_str, var_tup):
    bfa__ictqv = get_overload_const_str(dnf_filter_str)
    xqh__skyop = get_overload_const_str(expr_filter_str)
    goor__pofb = ', '.join(f'f{lyq__lnhh}' for lyq__lnhh in range(len(var_tup))
        )
    rjp__ragd = 'def impl(dnf_filter_str, expr_filter_str, var_tup):\n'
    if len(var_tup):
        rjp__ragd += f'  {goor__pofb}, = var_tup\n'
    rjp__ragd += """  with numba.objmode(dnf_filters_py='parquet_predicate_type', expr_filters_py='parquet_predicate_type'):
"""
    rjp__ragd += f'    dnf_filters_py = {bfa__ictqv}\n'
    rjp__ragd += f'    expr_filters_py = {xqh__skyop}\n'
    rjp__ragd += '  return (dnf_filters_py, expr_filters_py)\n'
    dbeb__pzb = {}
    exec(rjp__ragd, globals(), dbeb__pzb)
    return dbeb__pzb['impl']


@numba.njit
def get_fname_pyobject(fname):
    with numba.objmode(fname_py='read_parquet_fpath_type'):
        fname_py = fname
    return fname_py


def get_storage_options_pyobject(storage_options):
    pass


@overload(get_storage_options_pyobject, no_unliteral=True)
def overload_get_storage_options_pyobject(storage_options):
    wonr__yvfl = get_overload_constant_dict(storage_options)
    rjp__ragd = 'def impl(storage_options):\n'
    rjp__ragd += (
        "  with numba.objmode(storage_options_py='storage_options_dict_type'):\n"
        )
    rjp__ragd += f'    storage_options_py = {str(wonr__yvfl)}\n'
    rjp__ragd += '  return storage_options_py\n'
    dbeb__pzb = {}
    exec(rjp__ragd, globals(), dbeb__pzb)
    return dbeb__pzb['impl']


def _gen_pq_reader_py(col_names, col_indices, type_usecol_offset, out_types,
    storage_options, partition_names, dnf_filter_str, expr_filter_str,
    extra_args, is_parallel, meta_head_only_info, index_column_index,
    index_column_type, input_file_name_col):
    mgfam__sxkfp = next_label()
    aqq__vojp = ',' if extra_args else ''
    rjp__ragd = f'def pq_reader_py(fname,{extra_args}):\n'
    rjp__ragd += (
        f"    ev = bodo.utils.tracing.Event('read_parquet', {is_parallel})\n")
    rjp__ragd += f"    ev.add_attribute('fname', fname)\n"
    rjp__ragd += f"""    bucket_region = bodo.io.fs_io.get_s3_bucket_region_njit(fname, parallel={is_parallel})
"""
    rjp__ragd += f"""    dnf_filters, expr_filters = get_filters_pyobject("{dnf_filter_str}", "{expr_filter_str}", ({extra_args}{aqq__vojp}))
"""
    rjp__ragd += '    fname_py = get_fname_pyobject(fname)\n'
    storage_options['bodo_dummy'] = 'dummy'
    rjp__ragd += (
        f'    storage_options_py = get_storage_options_pyobject({str(storage_options)})\n'
        )
    tot_rows_to_read = -1
    if meta_head_only_info and meta_head_only_info[0] is not None:
        tot_rows_to_read = meta_head_only_info[0]
    djxce__groga = not type_usecol_offset
    nvx__lqr = [sanitize_varname(c) for c in col_names]
    partition_names = [sanitize_varname(c) for c in partition_names]
    input_file_name_col = sanitize_varname(input_file_name_col
        ) if input_file_name_col is not None and col_names.index(
        input_file_name_col) in type_usecol_offset else None
    lxhi__tloi = {c: lyq__lnhh for lyq__lnhh, c in enumerate(col_indices)}
    vtxab__uqlmb = {c: lyq__lnhh for lyq__lnhh, c in enumerate(nvx__lqr)}
    yiq__aqg = []
    mla__vrzfn = set()
    fxs__qehry = partition_names + [input_file_name_col]
    for lyq__lnhh in type_usecol_offset:
        if nvx__lqr[lyq__lnhh] not in fxs__qehry:
            yiq__aqg.append(col_indices[lyq__lnhh])
        elif not input_file_name_col or nvx__lqr[lyq__lnhh
            ] != input_file_name_col:
            mla__vrzfn.add(col_indices[lyq__lnhh])
    if index_column_index is not None:
        yiq__aqg.append(index_column_index)
    yiq__aqg = sorted(yiq__aqg)
    lhi__bouxz = {c: lyq__lnhh for lyq__lnhh, c in enumerate(yiq__aqg)}

    def is_nullable(typ):
        return bodo.utils.utils.is_array_typ(typ, False) and (not
            isinstance(typ, types.Array) and not isinstance(typ, bodo.
            DatetimeArrayType))
    bhkc__uutu = [(int(is_nullable(out_types[lxhi__tloi[cpuv__vfpmo]])) if 
        cpuv__vfpmo != index_column_index else int(is_nullable(
        index_column_type))) for cpuv__vfpmo in yiq__aqg]
    str_as_dict_cols = []
    for cpuv__vfpmo in yiq__aqg:
        if cpuv__vfpmo == index_column_index:
            imx__jpw = index_column_type
        else:
            imx__jpw = out_types[lxhi__tloi[cpuv__vfpmo]]
        if imx__jpw == dict_str_arr_type:
            str_as_dict_cols.append(cpuv__vfpmo)
    eab__rbb = []
    iiyp__ftywi = {}
    xtnfy__ytd = []
    qyoeo__wfg = []
    for lyq__lnhh, gqe__afozs in enumerate(partition_names):
        try:
            wzybe__wvnda = vtxab__uqlmb[gqe__afozs]
            if col_indices[wzybe__wvnda] not in mla__vrzfn:
                continue
        except (KeyError, ValueError) as dciz__tzmoa:
            continue
        iiyp__ftywi[gqe__afozs] = len(eab__rbb)
        eab__rbb.append(gqe__afozs)
        xtnfy__ytd.append(lyq__lnhh)
        cfkc__ibpn = out_types[wzybe__wvnda].dtype
        pqa__jsd = bodo.hiframes.pd_categorical_ext.get_categories_int_type(
            cfkc__ibpn)
        qyoeo__wfg.append(numba_to_c_type(pqa__jsd))
    rjp__ragd += f'    total_rows_np = np.array([0], dtype=np.int64)\n'
    rjp__ragd += f'    out_table = pq_read(\n'
    rjp__ragd += f'        fname_py, {is_parallel},\n'
    rjp__ragd += f'        unicode_to_utf8(bucket_region),\n'
    rjp__ragd += f'        dnf_filters, expr_filters,\n'
    rjp__ragd += f"""        storage_options_py, {tot_rows_to_read}, selected_cols_arr_{mgfam__sxkfp}.ctypes,
"""
    rjp__ragd += f'        {len(yiq__aqg)},\n'
    rjp__ragd += f'        nullable_cols_arr_{mgfam__sxkfp}.ctypes,\n'
    if len(xtnfy__ytd) > 0:
        rjp__ragd += (
            f'        np.array({xtnfy__ytd}, dtype=np.int32).ctypes,\n')
        rjp__ragd += (
            f'        np.array({qyoeo__wfg}, dtype=np.int32).ctypes,\n')
        rjp__ragd += f'        {len(xtnfy__ytd)},\n'
    else:
        rjp__ragd += f'        0, 0, 0,\n'
    if len(str_as_dict_cols) > 0:
        rjp__ragd += f"""        np.array({str_as_dict_cols}, dtype=np.int32).ctypes, {len(str_as_dict_cols)},
"""
    else:
        rjp__ragd += f'        0, 0,\n'
    rjp__ragd += f'        total_rows_np.ctypes,\n'
    rjp__ragd += f'        {input_file_name_col is not None},\n'
    rjp__ragd += f'    )\n'
    rjp__ragd += f'    check_and_propagate_cpp_exception()\n'
    fooa__kpo = 'None'
    gvjz__puww = index_column_type
    wozf__sutr = TableType(tuple(out_types))
    if djxce__groga:
        wozf__sutr = types.none
    if index_column_index is not None:
        encoy__zei = lhi__bouxz[index_column_index]
        fooa__kpo = (
            f'info_to_array(info_from_table(out_table, {encoy__zei}), index_arr_type)'
            )
    rjp__ragd += f'    index_arr = {fooa__kpo}\n'
    if djxce__groga:
        mca__ehpw = None
    else:
        mca__ehpw = []
        peno__vvgd = 0
        vfs__ioz = col_indices[col_names.index(input_file_name_col)
            ] if input_file_name_col is not None else None
        for lyq__lnhh, fvc__cju in enumerate(col_indices):
            if peno__vvgd < len(type_usecol_offset
                ) and lyq__lnhh == type_usecol_offset[peno__vvgd]:
                cgou__xofqr = col_indices[lyq__lnhh]
                if vfs__ioz and cgou__xofqr == vfs__ioz:
                    mca__ehpw.append(len(yiq__aqg) + len(eab__rbb))
                elif cgou__xofqr in mla__vrzfn:
                    bkjvw__sro = nvx__lqr[lyq__lnhh]
                    mca__ehpw.append(len(yiq__aqg) + iiyp__ftywi[bkjvw__sro])
                else:
                    mca__ehpw.append(lhi__bouxz[fvc__cju])
                peno__vvgd += 1
            else:
                mca__ehpw.append(-1)
        mca__ehpw = np.array(mca__ehpw, dtype=np.int64)
    if djxce__groga:
        rjp__ragd += '    T = None\n'
    else:
        rjp__ragd += f"""    T = cpp_table_to_py_table(out_table, table_idx_{mgfam__sxkfp}, py_table_type_{mgfam__sxkfp})
"""
    rjp__ragd += f'    delete_table(out_table)\n'
    rjp__ragd += f'    total_rows = total_rows_np[0]\n'
    rjp__ragd += f'    ev.finalize()\n'
    rjp__ragd += f'    return (total_rows, T, index_arr)\n'
    dbeb__pzb = {}
    yle__hxli = {f'py_table_type_{mgfam__sxkfp}': wozf__sutr,
        f'table_idx_{mgfam__sxkfp}': mca__ehpw,
        f'selected_cols_arr_{mgfam__sxkfp}': np.array(yiq__aqg, np.int32),
        f'nullable_cols_arr_{mgfam__sxkfp}': np.array(bhkc__uutu, np.int32),
        'index_arr_type': gvjz__puww, 'cpp_table_to_py_table':
        cpp_table_to_py_table, 'info_to_array': info_to_array,
        'info_from_table': info_from_table, 'delete_table': delete_table,
        'check_and_propagate_cpp_exception':
        check_and_propagate_cpp_exception, 'pq_read': _pq_read,
        'unicode_to_utf8': unicode_to_utf8, 'get_filters_pyobject':
        get_filters_pyobject, 'get_storage_options_pyobject':
        get_storage_options_pyobject, 'get_fname_pyobject':
        get_fname_pyobject, 'np': np, 'pd': pd, 'bodo': bodo}
    exec(rjp__ragd, yle__hxli, dbeb__pzb)
    sbxar__iot = dbeb__pzb['pq_reader_py']
    ymxhg__mqv = numba.njit(sbxar__iot, no_cpython_wrapper=True)
    return ymxhg__mqv


import pyarrow as pa
_pa_numba_typ_map = {pa.bool_(): types.bool_, pa.int8(): types.int8, pa.
    int16(): types.int16, pa.int32(): types.int32, pa.int64(): types.int64,
    pa.uint8(): types.uint8, pa.uint16(): types.uint16, pa.uint32(): types.
    uint32, pa.uint64(): types.uint64, pa.float32(): types.float32, pa.
    float64(): types.float64, pa.string(): string_type, pa.binary():
    bytes_type, pa.date32(): datetime_date_type, pa.date64(): types.
    NPDatetime('ns'), null(): string_type}


def get_arrow_timestamp_type(pa_ts_typ):
    axd__ennb = 'ns', 'us', 'ms', 's'
    if pa_ts_typ.unit not in axd__ennb:
        return types.Array(bodo.datetime64ns, 1, 'C'), False
    elif pa_ts_typ.tz is not None:
        fhplv__dihnb = pa_ts_typ.to_pandas_dtype().tz
        usgiw__aco = bodo.libs.pd_datetime_arr_ext.get_pytz_type_info(
            fhplv__dihnb)
        return bodo.DatetimeArrayType(usgiw__aco), True
    else:
        return types.Array(bodo.datetime64ns, 1, 'C'), True


def _get_numba_typ_from_pa_typ(pa_typ, is_index, nullable_from_metadata,
    category_info, str_as_dict=False):
    if isinstance(pa_typ.type, pa.ListType):
        zogdj__fgt, hqn__jttpx = _get_numba_typ_from_pa_typ(pa_typ.type.
            value_field, is_index, nullable_from_metadata, category_info)
        return ArrayItemArrayType(zogdj__fgt), hqn__jttpx
    if isinstance(pa_typ.type, pa.StructType):
        nqil__huivm = []
        lecj__qhukg = []
        hqn__jttpx = True
        for ysh__xriw in pa_typ.flatten():
            lecj__qhukg.append(ysh__xriw.name.split('.')[-1])
            kpdkc__vsus, yyah__zfv = _get_numba_typ_from_pa_typ(ysh__xriw,
                is_index, nullable_from_metadata, category_info)
            nqil__huivm.append(kpdkc__vsus)
            hqn__jttpx = hqn__jttpx and yyah__zfv
        return StructArrayType(tuple(nqil__huivm), tuple(lecj__qhukg)
            ), hqn__jttpx
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
        fvl__ckn = _pa_numba_typ_map[pa_typ.type.index_type]
        joh__nqu = PDCategoricalDtype(category_info[pa_typ.name], bodo.
            string_type, pa_typ.type.ordered, int_type=fvl__ckn)
        return CategoricalArrayType(joh__nqu), True
    if isinstance(pa_typ.type, pa.lib.TimestampType):
        return get_arrow_timestamp_type(pa_typ.type)
    elif pa_typ.type in _pa_numba_typ_map:
        jyu__gbek = _pa_numba_typ_map[pa_typ.type]
        hqn__jttpx = True
    else:
        raise BodoError('Arrow data type {} not supported yet'.format(
            pa_typ.type))
    if jyu__gbek == datetime_date_type:
        return datetime_date_array_type, hqn__jttpx
    if jyu__gbek == bytes_type:
        return binary_array_type, hqn__jttpx
    zogdj__fgt = (string_array_type if jyu__gbek == string_type else types.
        Array(jyu__gbek, 1, 'C'))
    if jyu__gbek == types.bool_:
        zogdj__fgt = boolean_array
    if nullable_from_metadata is not None:
        oixwy__uqbwl = nullable_from_metadata
    else:
        oixwy__uqbwl = use_nullable_int_arr
    if oixwy__uqbwl and not is_index and isinstance(jyu__gbek, types.Integer
        ) and pa_typ.nullable:
        zogdj__fgt = IntegerArrayType(jyu__gbek)
    return zogdj__fgt, hqn__jttpx


def get_parquet_dataset(fpath, get_row_counts=True, dnf_filters=None,
    expr_filters=None, storage_options=None, read_categories=False,
    is_parallel=False, tot_rows_to_read=None):
    if get_row_counts:
        twjce__izw = tracing.Event('get_parquet_dataset')
    import time
    import pyarrow as pa
    import pyarrow.parquet as pq
    from mpi4py import MPI
    qaz__zfz = MPI.COMM_WORLD
    if isinstance(fpath, list):
        kny__urtao = urlparse(fpath[0])
        protocol = kny__urtao.scheme
        oey__rgika = kny__urtao.netloc
        for lyq__lnhh in range(len(fpath)):
            vha__lbzx = fpath[lyq__lnhh]
            gfa__ytfm = urlparse(vha__lbzx)
            if gfa__ytfm.scheme != protocol:
                raise BodoError(
                    'All parquet files must use the same filesystem protocol')
            if gfa__ytfm.netloc != oey__rgika:
                raise BodoError(
                    'All parquet files must be in the same S3 bucket')
            fpath[lyq__lnhh] = vha__lbzx.rstrip('/')
    else:
        kny__urtao = urlparse(fpath)
        protocol = kny__urtao.scheme
        fpath = fpath.rstrip('/')
    if protocol in {'gcs', 'gs'}:
        try:
            import gcsfs
        except ImportError as dciz__tzmoa:
            ldy__vqha = """Couldn't import gcsfs, which is required for Google cloud access. gcsfs can be installed by calling 'conda install -c conda-forge gcsfs'.
"""
            raise BodoError(ldy__vqha)
    if protocol == 'http':
        try:
            import fsspec
        except ImportError as dciz__tzmoa:
            ldy__vqha = """Couldn't import fsspec, which is required for http access. fsspec can be installed by calling 'conda install -c conda-forge fsspec'.
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
            pzc__cdza = gcsfs.GCSFileSystem(token=None)
            fs.append(pzc__cdza)
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
                prefix = f'{protocol}://{kny__urtao.netloc}'
                path = path[len(prefix):]
            mrc__kcfw = fs.glob(path)
            if protocol == 's3':
                mrc__kcfw = [('s3://' + vha__lbzx) for vha__lbzx in
                    mrc__kcfw if not vha__lbzx.startswith('s3://')]
            elif protocol in {'hdfs', 'abfs', 'abfss'}:
                mrc__kcfw = [(prefix + vha__lbzx) for vha__lbzx in mrc__kcfw]
        except:
            raise BodoError(
                f'glob pattern expansion not supported for {protocol}')
        if len(mrc__kcfw) == 0:
            raise BodoError('No files found matching glob pattern')
        return mrc__kcfw
    rha__bas = False
    if get_row_counts:
        zpwf__uszyj = getfs(parallel=True)
        rha__bas = bodo.parquet_validate_schema
    if bodo.get_rank() == 0:
        meubn__kzr = 1
        piyqo__bwlh = os.cpu_count()
        if piyqo__bwlh is not None and piyqo__bwlh > 1:
            meubn__kzr = piyqo__bwlh // 2
        try:
            if get_row_counts:
                rrrs__ofjh = tracing.Event('pq.ParquetDataset', is_parallel
                    =False)
                if tracing.is_tracing():
                    rrrs__ofjh.add_attribute('dnf_filter', str(dnf_filters))
            jwgmb__ddp = pa.io_thread_count()
            pa.set_io_thread_count(meubn__kzr)
            if '*' in fpath:
                fpath = glob(protocol, getfs(), fpath)
            if protocol == 's3':
                if isinstance(fpath, list):
                    get_legacy_fs().info(fpath[0])
                else:
                    get_legacy_fs().info(fpath)
            if protocol in {'hdfs', 'abfs', 'abfss'}:
                prefix = f'{protocol}://{kny__urtao.netloc}'
                if isinstance(fpath, list):
                    uiq__hjro = [vha__lbzx[len(prefix):] for vha__lbzx in fpath
                        ]
                else:
                    uiq__hjro = fpath[len(prefix):]
            else:
                uiq__hjro = fpath
            qxhc__cqwp = pq.ParquetDataset(uiq__hjro, filesystem=
                get_legacy_fs(), filters=None, use_legacy_dataset=True,
                validate_schema=False, metadata_nthreads=meubn__kzr)
            pa.set_io_thread_count(jwgmb__ddp)
            htt__ilawt = bodo.io.pa_parquet.get_dataset_schema(qxhc__cqwp)
            if dnf_filters:
                if get_row_counts:
                    rrrs__ofjh.add_attribute('num_pieces_before_filter',
                        len(qxhc__cqwp.pieces))
                bgfz__gia = time.time()
                qxhc__cqwp._filter(dnf_filters)
                if get_row_counts:
                    rrrs__ofjh.add_attribute('dnf_filter_time', time.time() -
                        bgfz__gia)
                    rrrs__ofjh.add_attribute('num_pieces_after_filter', len
                        (qxhc__cqwp.pieces))
            if get_row_counts:
                rrrs__ofjh.finalize()
            qxhc__cqwp._metadata.fs = None
        except Exception as gvgg__fms:
            qaz__zfz.bcast(gvgg__fms)
            raise BodoError(
                f'error from pyarrow: {type(gvgg__fms).__name__}: {str(gvgg__fms)}\n'
                )
        if get_row_counts:
            aej__mox = tracing.Event('bcast dataset')
        qaz__zfz.bcast(qxhc__cqwp)
        qaz__zfz.bcast(htt__ilawt)
    else:
        if get_row_counts:
            aej__mox = tracing.Event('bcast dataset')
        qxhc__cqwp = qaz__zfz.bcast(None)
        if isinstance(qxhc__cqwp, Exception):
            rpd__ervix = qxhc__cqwp
            raise BodoError(
                f'error from pyarrow: {type(rpd__ervix).__name__}: {str(rpd__ervix)}\n'
                )
        htt__ilawt = qaz__zfz.bcast(None)
    if get_row_counts:
        nzy__ilqeb = getfs()
    else:
        nzy__ilqeb = get_legacy_fs()
    qxhc__cqwp._metadata.fs = nzy__ilqeb
    if get_row_counts:
        aej__mox.finalize()
    qxhc__cqwp._bodo_total_rows = 0
    if get_row_counts and tot_rows_to_read == 0:
        get_row_counts = rha__bas = False
        for phlb__hvma in qxhc__cqwp.pieces:
            phlb__hvma._bodo_num_rows = 0
    if get_row_counts or rha__bas:
        if get_row_counts and tracing.is_tracing():
            yer__wev = tracing.Event('get_row_counts')
            yer__wev.add_attribute('g_num_pieces', len(qxhc__cqwp.pieces))
            yer__wev.add_attribute('g_expr_filters', str(expr_filters))
        fdfs__igpk = 0.0
        num_pieces = len(qxhc__cqwp.pieces)
        start = get_start(num_pieces, bodo.get_size(), bodo.get_rank())
        ljyes__iaej = get_end(num_pieces, bodo.get_size(), bodo.get_rank())
        parih__zuil = 0
        zve__heb = 0
        kjbkc__gjk = 0
        lxf__pzrgb = True
        if expr_filters is not None:
            import random
            random.seed(37)
            odsi__aghue = random.sample(qxhc__cqwp.pieces, k=len(qxhc__cqwp
                .pieces))
        else:
            odsi__aghue = qxhc__cqwp.pieces
        for phlb__hvma in odsi__aghue:
            phlb__hvma._bodo_num_rows = 0
        fpaths = [phlb__hvma.path for phlb__hvma in odsi__aghue[start:
            ljyes__iaej]]
        if protocol == 's3':
            oey__rgika = kny__urtao.netloc
            prefix = 's3://' + oey__rgika + '/'
            fpaths = [vha__lbzx[len(prefix):] for vha__lbzx in fpaths]
            nzy__ilqeb = get_s3_subtree_fs(oey__rgika, region=getfs().
                region, storage_options=storage_options)
        else:
            nzy__ilqeb = getfs()
        pa.set_io_thread_count(4)
        pa.set_cpu_count(4)
        azou__bftv = ds.dataset(fpaths, filesystem=nzy__ilqeb, partitioning
            =ds.partitioning(flavor='hive'))
        for sfnqg__vdkb, fpdqo__uowsp in zip(odsi__aghue[start:ljyes__iaej],
            azou__bftv.get_fragments()):
            bgfz__gia = time.time()
            hpzi__ujg = fpdqo__uowsp.scanner(schema=azou__bftv.schema,
                filter=expr_filters, use_threads=True).count_rows()
            fdfs__igpk += time.time() - bgfz__gia
            sfnqg__vdkb._bodo_num_rows = hpzi__ujg
            parih__zuil += hpzi__ujg
            zve__heb += fpdqo__uowsp.num_row_groups
            kjbkc__gjk += sum(aok__dov.total_byte_size for aok__dov in
                fpdqo__uowsp.row_groups)
            if rha__bas:
                nbrs__meu = fpdqo__uowsp.metadata.schema.to_arrow_schema()
                if htt__ilawt != nbrs__meu:
                    print('Schema in {!s} was different. \n{!s}\n\nvs\n\n{!s}'
                        .format(sfnqg__vdkb, nbrs__meu, htt__ilawt))
                    lxf__pzrgb = False
                    break
        if rha__bas:
            lxf__pzrgb = qaz__zfz.allreduce(lxf__pzrgb, op=MPI.LAND)
            if not lxf__pzrgb:
                raise BodoError("Schema in parquet files don't match")
        if get_row_counts:
            qxhc__cqwp._bodo_total_rows = qaz__zfz.allreduce(parih__zuil,
                op=MPI.SUM)
            wpgk__kfhfb = qaz__zfz.allreduce(zve__heb, op=MPI.SUM)
            yyyx__stbr = qaz__zfz.allreduce(kjbkc__gjk, op=MPI.SUM)
            hgt__ndk = np.array([phlb__hvma._bodo_num_rows for phlb__hvma in
                qxhc__cqwp.pieces])
            hgt__ndk = qaz__zfz.allreduce(hgt__ndk, op=MPI.SUM)
            for phlb__hvma, reiux__vyxj in zip(qxhc__cqwp.pieces, hgt__ndk):
                phlb__hvma._bodo_num_rows = reiux__vyxj
            if is_parallel and bodo.get_rank(
                ) == 0 and wpgk__kfhfb < bodo.get_size() and wpgk__kfhfb != 0:
                warnings.warn(BodoWarning(
                    f"""Total number of row groups in parquet dataset {fpath} ({wpgk__kfhfb}) is too small for effective IO parallelization.
For best performance the number of row groups should be greater than the number of workers ({bodo.get_size()})
"""
                    ))
            if wpgk__kfhfb == 0:
                oos__ijdh = 0
            else:
                oos__ijdh = yyyx__stbr // wpgk__kfhfb
            if (bodo.get_rank() == 0 and yyyx__stbr >= 20 * 1048576 and 
                oos__ijdh < 1048576 and protocol in REMOTE_FILESYSTEMS):
                warnings.warn(BodoWarning(
                    f'Parquet average row group size is small ({oos__ijdh} bytes) and can have negative impact on performance when reading from remote sources'
                    ))
            if tracing.is_tracing():
                yer__wev.add_attribute('g_total_num_row_groups', wpgk__kfhfb)
                if expr_filters is not None:
                    yer__wev.add_attribute('total_scan_time', fdfs__igpk)
                clnym__ede = np.array([phlb__hvma._bodo_num_rows for
                    phlb__hvma in qxhc__cqwp.pieces])
                nwivg__jwo = np.percentile(clnym__ede, [25, 50, 75])
                yer__wev.add_attribute('g_row_counts_min', clnym__ede.min())
                yer__wev.add_attribute('g_row_counts_Q1', nwivg__jwo[0])
                yer__wev.add_attribute('g_row_counts_median', nwivg__jwo[1])
                yer__wev.add_attribute('g_row_counts_Q3', nwivg__jwo[2])
                yer__wev.add_attribute('g_row_counts_max', clnym__ede.max())
                yer__wev.add_attribute('g_row_counts_mean', clnym__ede.mean())
                yer__wev.add_attribute('g_row_counts_std', clnym__ede.std())
                yer__wev.add_attribute('g_row_counts_sum', clnym__ede.sum())
                yer__wev.finalize()
    qxhc__cqwp._prefix = ''
    if protocol in {'hdfs', 'abfs', 'abfss'}:
        prefix = f'{protocol}://{kny__urtao.netloc}'
        if len(qxhc__cqwp.pieces) > 0:
            sfnqg__vdkb = qxhc__cqwp.pieces[0]
            if not sfnqg__vdkb.path.startswith(prefix):
                qxhc__cqwp._prefix = prefix
    if read_categories:
        _add_categories_to_pq_dataset(qxhc__cqwp)
    if get_row_counts:
        twjce__izw.finalize()
    return qxhc__cqwp


def get_scanner_batches(fpaths, expr_filters, selected_fields,
    avg_num_pieces, is_parallel, storage_options, region, prefix,
    str_as_dict_cols, start_offset, rows_to_read):
    import pyarrow as pa
    piyqo__bwlh = os.cpu_count()
    if piyqo__bwlh is None or piyqo__bwlh == 0:
        piyqo__bwlh = 2
    akvk__iiecj = min(4, piyqo__bwlh)
    vzzse__jysr = min(16, piyqo__bwlh)
    if is_parallel and len(fpaths) > vzzse__jysr and len(fpaths
        ) / avg_num_pieces >= 2.0:
        pa.set_io_thread_count(vzzse__jysr)
        pa.set_cpu_count(vzzse__jysr)
    else:
        pa.set_io_thread_count(akvk__iiecj)
        pa.set_cpu_count(akvk__iiecj)
    if fpaths[0].startswith('s3://'):
        oey__rgika = urlparse(fpaths[0]).netloc
        prefix = 's3://' + oey__rgika + '/'
        fpaths = [vha__lbzx[len(prefix):] for vha__lbzx in fpaths]
        nzy__ilqeb = get_s3_subtree_fs(oey__rgika, region=region,
            storage_options=storage_options)
    elif prefix and prefix.startswith(('hdfs', 'abfs', 'abfss')):
        nzy__ilqeb = get_hdfs_fs(prefix + fpaths[0])
    elif fpaths[0].startswith(('gcs', 'gs')):
        import gcsfs
        nzy__ilqeb = gcsfs.GCSFileSystem(token=None)
    else:
        nzy__ilqeb = None
    xrhm__jvmle = ds.ParquetFileFormat(dictionary_columns=str_as_dict_cols)
    qxhc__cqwp = ds.dataset(fpaths, filesystem=nzy__ilqeb, partitioning=ds.
        partitioning(flavor='hive'), format=xrhm__jvmle)
    col_names = qxhc__cqwp.schema.names
    sifga__umgs = [col_names[cwa__ehbc] for cwa__ehbc in selected_fields]
    rvk__sfkey = len(fpaths) <= 3 or start_offset > 0 and len(fpaths) <= 10
    if rvk__sfkey and expr_filters is None:
        lxqer__tlws = []
        uwu__nub = 0
        fxvfr__uerob = 0
        for fpdqo__uowsp in qxhc__cqwp.get_fragments():
            skdk__ofkd = []
            for aok__dov in fpdqo__uowsp.row_groups:
                fxww__aptcn = aok__dov.num_rows
                if start_offset < uwu__nub + fxww__aptcn:
                    if fxvfr__uerob == 0:
                        mfva__izjt = start_offset - uwu__nub
                        sxve__spla = min(fxww__aptcn - mfva__izjt, rows_to_read
                            )
                    else:
                        sxve__spla = min(fxww__aptcn, rows_to_read -
                            fxvfr__uerob)
                    fxvfr__uerob += sxve__spla
                    skdk__ofkd.append(aok__dov.id)
                uwu__nub += fxww__aptcn
                if fxvfr__uerob == rows_to_read:
                    break
            lxqer__tlws.append(fpdqo__uowsp.subset(row_group_ids=skdk__ofkd))
            if fxvfr__uerob == rows_to_read:
                break
        qxhc__cqwp = ds.FileSystemDataset(lxqer__tlws, qxhc__cqwp.schema,
            xrhm__jvmle, filesystem=qxhc__cqwp.filesystem)
        start_offset = mfva__izjt
    vntl__gluz = qxhc__cqwp.scanner(columns=sifga__umgs, filter=
        expr_filters, use_threads=True).to_reader()
    return qxhc__cqwp, vntl__gluz, start_offset


def _add_categories_to_pq_dataset(pq_dataset):
    import pyarrow as pa
    from mpi4py import MPI
    if len(pq_dataset.pieces) < 1:
        raise BodoError(
            'No pieces found in Parquet dataset. Cannot get read categorical values'
            )
    pa_schema = pq_dataset.schema.to_arrow_schema()
    urc__swo = [c for c in pa_schema.names if isinstance(pa_schema.field(c)
        .type, pa.DictionaryType)]
    if len(urc__swo) == 0:
        pq_dataset._category_info = {}
        return
    qaz__zfz = MPI.COMM_WORLD
    if bodo.get_rank() == 0:
        try:
            jkgvn__hwak = pq_dataset.pieces[0].open()
            aok__dov = jkgvn__hwak.read_row_group(0, urc__swo)
            category_info = {c: tuple(aok__dov.column(c).chunk(0).
                dictionary.to_pylist()) for c in urc__swo}
            del jkgvn__hwak, aok__dov
        except Exception as gvgg__fms:
            qaz__zfz.bcast(gvgg__fms)
            raise gvgg__fms
        qaz__zfz.bcast(category_info)
    else:
        category_info = qaz__zfz.bcast(None)
        if isinstance(category_info, Exception):
            rpd__ervix = category_info
            raise rpd__ervix
    pq_dataset._category_info = category_info


def get_pandas_metadata(schema, num_pieces):
    jll__kajbm = None
    nullable_from_metadata = defaultdict(lambda : None)
    zjjqv__bjt = b'pandas'
    if schema.metadata is not None and zjjqv__bjt in schema.metadata:
        import json
        kwrqs__iavgw = json.loads(schema.metadata[zjjqv__bjt].decode('utf8'))
        vnp__azn = len(kwrqs__iavgw['index_columns'])
        if vnp__azn > 1:
            raise BodoError('read_parquet: MultiIndex not supported yet')
        jll__kajbm = kwrqs__iavgw['index_columns'][0] if vnp__azn else None
        if not isinstance(jll__kajbm, str) and (not isinstance(jll__kajbm,
            dict) or num_pieces != 1):
            jll__kajbm = None
        for gfbj__wjikw in kwrqs__iavgw['columns']:
            sef__wmkfx = gfbj__wjikw['name']
            if gfbj__wjikw['pandas_type'].startswith('int'
                ) and sef__wmkfx is not None:
                if gfbj__wjikw['numpy_type'].startswith('Int'):
                    nullable_from_metadata[sef__wmkfx] = True
                else:
                    nullable_from_metadata[sef__wmkfx] = False
    return jll__kajbm, nullable_from_metadata


def determine_str_as_dict_columns(pq_dataset, pa_schema):
    from mpi4py import MPI
    qaz__zfz = MPI.COMM_WORLD
    jhz__bdq = []
    for sef__wmkfx in pa_schema.names:
        ysh__xriw = pa_schema.field(sef__wmkfx)
        if ysh__xriw.type == pa.string():
            jhz__bdq.append((sef__wmkfx, pa_schema.get_field_index(sef__wmkfx))
                )
    if len(jhz__bdq) == 0:
        return set()
    if len(pq_dataset.pieces) > bodo.get_size():
        import random
        random.seed(37)
        odsi__aghue = random.sample(pq_dataset.pieces, bodo.get_size())
    else:
        odsi__aghue = pq_dataset.pieces
    jyqbz__fisly = np.zeros(len(jhz__bdq), dtype=np.int64)
    gap__feal = np.zeros(len(jhz__bdq), dtype=np.int64)
    if bodo.get_rank() < len(odsi__aghue):
        sfnqg__vdkb = odsi__aghue[bodo.get_rank()]
        pepy__htei = sfnqg__vdkb.get_metadata()
        for lyq__lnhh in range(pepy__htei.num_row_groups):
            for peno__vvgd, (zpwf__uszyj, turc__txyc) in enumerate(jhz__bdq):
                jyqbz__fisly[peno__vvgd] += pepy__htei.row_group(lyq__lnhh
                    ).column(turc__txyc).total_uncompressed_size
        iyvpi__zrh = pepy__htei.num_rows
    else:
        iyvpi__zrh = 0
    otpd__hbyh = qaz__zfz.allreduce(iyvpi__zrh, op=MPI.SUM)
    if otpd__hbyh == 0:
        return set()
    qaz__zfz.Allreduce(jyqbz__fisly, gap__feal, op=MPI.SUM)
    rwth__ips = gap__feal / otpd__hbyh
    str_as_dict = set()
    for lyq__lnhh, qri__iznt in enumerate(rwth__ips):
        if qri__iznt < READ_STR_AS_DICT_THRESHOLD:
            sef__wmkfx = jhz__bdq[lyq__lnhh][0]
            str_as_dict.add(sef__wmkfx)
    return str_as_dict


def parquet_file_schema(file_name, selected_columns, storage_options=None,
    input_file_name_col=None):
    col_names = []
    vfh__ycnni = []
    pq_dataset = get_parquet_dataset(file_name, get_row_counts=False,
        storage_options=storage_options, read_categories=True)
    partition_names = [] if pq_dataset.partitions is None else [pq_dataset.
        partitions.levels[lyq__lnhh].name for lyq__lnhh in range(len(
        pq_dataset.partitions.partition_names))]
    pa_schema = pq_dataset.schema.to_arrow_schema()
    num_pieces = len(pq_dataset.pieces)
    str_as_dict = determine_str_as_dict_columns(pq_dataset, pa_schema)
    col_names = pa_schema.names
    jll__kajbm, nullable_from_metadata = get_pandas_metadata(pa_schema,
        num_pieces)
    ytr__xzvw = []
    nxxgc__qmi = []
    bvd__hyt = []
    for lyq__lnhh, c in enumerate(col_names):
        ysh__xriw = pa_schema.field(c)
        jyu__gbek, hqn__jttpx = _get_numba_typ_from_pa_typ(ysh__xriw, c ==
            jll__kajbm, nullable_from_metadata[c], pq_dataset.
            _category_info, str_as_dict=c in str_as_dict)
        ytr__xzvw.append(jyu__gbek)
        nxxgc__qmi.append(hqn__jttpx)
        bvd__hyt.append(ysh__xriw.type)
    if partition_names:
        col_names += partition_names
        ytr__xzvw += [_get_partition_cat_dtype(pq_dataset.partitions.levels
            [lyq__lnhh]) for lyq__lnhh in range(len(partition_names))]
        nxxgc__qmi.extend([True] * len(partition_names))
        bvd__hyt.extend([None] * len(partition_names))
    if input_file_name_col is not None:
        col_names += [input_file_name_col]
        ytr__xzvw += [dict_str_arr_type]
        nxxgc__qmi.append(True)
        bvd__hyt.append(None)
    iuwyd__gyaxu = {c: lyq__lnhh for lyq__lnhh, c in enumerate(col_names)}
    if selected_columns is None:
        selected_columns = col_names
    for c in selected_columns:
        if c not in iuwyd__gyaxu:
            raise BodoError(f'Selected column {c} not in Parquet file schema')
    if jll__kajbm and not isinstance(jll__kajbm, dict
        ) and jll__kajbm not in selected_columns:
        selected_columns.append(jll__kajbm)
    col_names = selected_columns
    col_indices = []
    vfh__ycnni = []
    zmfp__hatfo = []
    ovl__rfhg = []
    for lyq__lnhh, c in enumerate(col_names):
        cgou__xofqr = iuwyd__gyaxu[c]
        col_indices.append(cgou__xofqr)
        vfh__ycnni.append(ytr__xzvw[cgou__xofqr])
        if not nxxgc__qmi[cgou__xofqr]:
            zmfp__hatfo.append(lyq__lnhh)
            ovl__rfhg.append(bvd__hyt[cgou__xofqr])
    return (col_names, vfh__ycnni, jll__kajbm, col_indices, partition_names,
        zmfp__hatfo, ovl__rfhg)


def _get_partition_cat_dtype(part_set):
    leucl__hvhi = part_set.dictionary.to_pandas()
    dkyyx__ynusd = bodo.typeof(leucl__hvhi).dtype
    joh__nqu = PDCategoricalDtype(tuple(leucl__hvhi), dkyyx__ynusd, False)
    return CategoricalArrayType(joh__nqu)


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
        vpwu__mbo = lir.FunctionType(lir.VoidType(), [lir.IntType(8).
            as_pointer(), lir.IntType(8).as_pointer(), lir.IntType(8).
            as_pointer(), lir.IntType(8).as_pointer(), lir.IntType(1), lir.
            IntType(8).as_pointer(), lir.IntType(8).as_pointer(), lir.
            IntType(1), lir.IntType(1), lir.IntType(32), lir.IntType(32),
            lir.IntType(32), lir.IntType(8).as_pointer(), lir.IntType(8).
            as_pointer()])
        mpnzz__nzbrn = cgutils.get_or_insert_function(builder.module,
            vpwu__mbo, name='pq_write')
        builder.call(mpnzz__nzbrn, args)
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
        vpwu__mbo = lir.FunctionType(lir.VoidType(), [lir.IntType(8).
            as_pointer(), lir.IntType(8).as_pointer(), lir.IntType(8).
            as_pointer(), lir.IntType(8).as_pointer(), lir.IntType(8).
            as_pointer(), lir.IntType(8).as_pointer(), lir.IntType(32), lir
            .IntType(8).as_pointer(), lir.IntType(1), lir.IntType(8).
            as_pointer()])
        mpnzz__nzbrn = cgutils.get_or_insert_function(builder.module,
            vpwu__mbo, name='pq_write_partitioned')
        builder.call(mpnzz__nzbrn, args)
        bodo.utils.utils.inlined_check_and_propagate_cpp_exception(context,
            builder)
    return types.void(types.voidptr, data_table_t, col_names_t,
        col_names_no_partitions_t, cat_table_t, types.voidptr, types.int32,
        types.voidptr, types.boolean, types.voidptr), codegen
