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
        except OSError as mjr__sdyj:
            if 'non-file path' in str(mjr__sdyj):
                raise FileNotFoundError(str(mjr__sdyj))
            raise


class ParquetHandler:

    def __init__(self, func_ir, typingctx, args, _locals):
        self.func_ir = func_ir
        self.typingctx = typingctx
        self.args = args
        self.locals = _locals

    def gen_parquet_read(self, file_name, lhs, columns, storage_options=
        None, input_file_name_col=None):
        qkeky__mzbjj = lhs.scope
        frn__blqp = lhs.loc
        khbbu__qyuf = None
        if lhs.name in self.locals:
            khbbu__qyuf = self.locals[lhs.name]
            self.locals.pop(lhs.name)
        pnm__cswjb = {}
        if lhs.name + ':convert' in self.locals:
            pnm__cswjb = self.locals[lhs.name + ':convert']
            self.locals.pop(lhs.name + ':convert')
        if khbbu__qyuf is None:
            jrm__zvlzk = (
                'Parquet schema not available. Either path argument should be constant for Bodo to look at the file at compile time or schema should be provided. For more information, see: https://docs.bodo.ai/latest/source/programming_with_bodo/file_io.html#non-constant-filepaths'
                )
            tjzy__jzzj = get_const_value(file_name, self.func_ir,
                jrm__zvlzk, arg_types=self.args, file_info=ParquetFileInfo(
                columns, storage_options=storage_options,
                input_file_name_col=input_file_name_col))
            cjtng__bxhdw = False
            aehk__eulgi = guard(get_definition, self.func_ir, file_name)
            if isinstance(aehk__eulgi, ir.Arg):
                typ = self.args[aehk__eulgi.index]
                if isinstance(typ, types.FilenameType):
                    (col_names, ueov__bpai, kovpm__mzdx, col_indices,
                        partition_names, zvdz__cqxga, pojrr__tve) = typ.schema
                    cjtng__bxhdw = True
            if not cjtng__bxhdw:
                (col_names, ueov__bpai, kovpm__mzdx, col_indices,
                    partition_names, zvdz__cqxga, pojrr__tve) = (
                    parquet_file_schema(tjzy__jzzj, columns,
                    storage_options=storage_options, input_file_name_col=
                    input_file_name_col))
        else:
            ptk__bmj = list(khbbu__qyuf.keys())
            umf__zoii = {c: spltl__ghgsu for spltl__ghgsu, c in enumerate(
                ptk__bmj)}
            oyk__esd = [xvnt__wxmc for xvnt__wxmc in khbbu__qyuf.values()]
            kovpm__mzdx = 'index' if 'index' in umf__zoii else None
            if columns is None:
                selected_columns = ptk__bmj
            else:
                selected_columns = columns
            col_indices = [umf__zoii[c] for c in selected_columns]
            ueov__bpai = [oyk__esd[umf__zoii[c]] for c in selected_columns]
            col_names = selected_columns
            kovpm__mzdx = kovpm__mzdx if kovpm__mzdx in col_names else None
            partition_names = []
            zvdz__cqxga = []
            pojrr__tve = []
        ayqq__mcm = None if isinstance(kovpm__mzdx, dict
            ) or kovpm__mzdx is None else kovpm__mzdx
        index_column_index = None
        index_column_type = types.none
        if ayqq__mcm:
            bage__yje = col_names.index(ayqq__mcm)
            index_column_index = col_indices.pop(bage__yje)
            index_column_type = ueov__bpai.pop(bage__yje)
            col_names.pop(bage__yje)
        for spltl__ghgsu, c in enumerate(col_names):
            if c in pnm__cswjb:
                ueov__bpai[spltl__ghgsu] = pnm__cswjb[c]
        vpevu__mvzn = [ir.Var(qkeky__mzbjj, mk_unique_var('pq_table'),
            frn__blqp), ir.Var(qkeky__mzbjj, mk_unique_var('pq_index'),
            frn__blqp)]
        daasg__knuj = [bodo.ir.parquet_ext.ParquetReader(file_name, lhs.
            name, col_names, col_indices, ueov__bpai, vpevu__mvzn,
            frn__blqp, partition_names, storage_options, index_column_index,
            index_column_type, input_file_name_col, zvdz__cqxga, pojrr__tve)]
        return (col_names, vpevu__mvzn, kovpm__mzdx, daasg__knuj,
            ueov__bpai, index_column_type)


def determine_filter_cast(pq_node, typemap, filter_val, orig_colname_map):
    jii__ckb = filter_val[0]
    mproe__fxknw = pq_node.original_out_types[orig_colname_map[jii__ckb]]
    kgeba__juxmv = bodo.utils.typing.element_type(mproe__fxknw)
    if jii__ckb in pq_node.partition_names:
        if kgeba__juxmv == types.unicode_type:
            rwc__qnd = '.cast(pyarrow.string(), safe=False)'
        elif isinstance(kgeba__juxmv, types.Integer):
            rwc__qnd = f'.cast(pyarrow.{kgeba__juxmv.name}(), safe=False)'
        else:
            rwc__qnd = ''
    else:
        rwc__qnd = ''
    tlxtd__vaxyv = typemap[filter_val[2].name]
    if isinstance(tlxtd__vaxyv, (types.List, types.Set)):
        tyx__epkmf = tlxtd__vaxyv.dtype
    else:
        tyx__epkmf = tlxtd__vaxyv
    bodo.hiframes.pd_timestamp_ext.check_tz_aware_unsupported(kgeba__juxmv,
        'Filter pushdown')
    bodo.hiframes.pd_timestamp_ext.check_tz_aware_unsupported(tyx__epkmf,
        'Filter pushdown')
    if not bodo.utils.typing.is_common_scalar_dtype([kgeba__juxmv, tyx__epkmf]
        ):
        if not bodo.utils.typing.is_safe_arrow_cast(kgeba__juxmv, tyx__epkmf):
            raise BodoError(
                f'Unsupported Arrow cast from {kgeba__juxmv} to {tyx__epkmf} in filter pushdown. Please try a comparison that avoids casting the column.'
                )
        if kgeba__juxmv == types.unicode_type:
            return ".cast(pyarrow.timestamp('ns'), safe=False)", ''
        elif kgeba__juxmv in (bodo.datetime64ns, bodo.pd_timestamp_type):
            if isinstance(tlxtd__vaxyv, (types.List, types.Set)):
                bmttf__glarf = 'list' if isinstance(tlxtd__vaxyv, types.List
                    ) else 'tuple'
                raise BodoError(
                    f'Cannot cast {bmttf__glarf} values with isin filter pushdown.'
                    )
            return rwc__qnd, ".cast(pyarrow.timestamp('ns'), safe=False)"
    return rwc__qnd, ''


def pq_distributed_run(pq_node, array_dists, typemap, calltypes, typingctx,
    targetctx, meta_head_only_info=None):
    vccuv__tuwif = len(pq_node.out_vars)
    extra_args = ''
    dnf_filter_str = 'None'
    expr_filter_str = 'None'
    jmx__idhtp, cpr__ujy = bodo.ir.connector.generate_filter_map(pq_node.
        filters)
    if pq_node.filters:
        ptf__fpor = []
        obz__epqdr = []
        oojw__oji = False
        yiecy__pqdj = None
        orig_colname_map = {c: spltl__ghgsu for spltl__ghgsu, c in
            enumerate(pq_node.original_df_colnames)}
        for fpsxj__nqd in pq_node.filters:
            qfumd__yww = []
            sfzs__idb = []
            njp__aboyl = set()
            for jnszu__ner in fpsxj__nqd:
                if isinstance(jnszu__ner[2], ir.Var):
                    aripj__ogje, wlxb__fyvbu = determine_filter_cast(pq_node,
                        typemap, jnszu__ner, orig_colname_map)
                    if jnszu__ner[1] == 'in':
                        sfzs__idb.append(
                            f"(ds.field('{jnszu__ner[0]}').isin({jmx__idhtp[jnszu__ner[2].name]}))"
                            )
                    else:
                        sfzs__idb.append(
                            f"(ds.field('{jnszu__ner[0]}'){aripj__ogje} {jnszu__ner[1]} ds.scalar({jmx__idhtp[jnszu__ner[2].name]}){wlxb__fyvbu})"
                            )
                else:
                    assert jnszu__ner[2
                        ] == 'NULL', 'unsupport constant used in filter pushdown'
                    if jnszu__ner[1] == 'is not':
                        prefix = '~'
                    else:
                        prefix = ''
                    sfzs__idb.append(
                        f"({prefix}ds.field('{jnszu__ner[0]}').is_null())")
                if jnszu__ner[0] in pq_node.partition_names and isinstance(
                    jnszu__ner[2], ir.Var):
                    jatfz__nnfl = (
                        f"('{jnszu__ner[0]}', '{jnszu__ner[1]}', {jmx__idhtp[jnszu__ner[2].name]})"
                        )
                    qfumd__yww.append(jatfz__nnfl)
                    njp__aboyl.add(jatfz__nnfl)
                else:
                    oojw__oji = True
            if yiecy__pqdj is None:
                yiecy__pqdj = njp__aboyl
            else:
                yiecy__pqdj.intersection_update(njp__aboyl)
            chgf__adzx = ', '.join(qfumd__yww)
            ytks__xaw = ' & '.join(sfzs__idb)
            if chgf__adzx:
                ptf__fpor.append(f'[{chgf__adzx}]')
            obz__epqdr.append(f'({ytks__xaw})')
        vgc__bdlw = ', '.join(ptf__fpor)
        kvsld__itrb = ' | '.join(obz__epqdr)
        if oojw__oji:
            if yiecy__pqdj:
                addh__xuzf = sorted(yiecy__pqdj)
                dnf_filter_str = f"[[{', '.join(addh__xuzf)}]]"
        elif vgc__bdlw:
            dnf_filter_str = f'[{vgc__bdlw}]'
        expr_filter_str = f'({kvsld__itrb})'
        extra_args = ', '.join(jmx__idhtp.values())
    uqe__ztpk = ', '.join(f'out{spltl__ghgsu}' for spltl__ghgsu in range(
        vccuv__tuwif))
    amfoq__zzs = f'def pq_impl(fname, {extra_args}):\n'
    amfoq__zzs += (
        f'    (total_rows, {uqe__ztpk},) = _pq_reader_py(fname, {extra_args})\n'
        )
    zuqd__cav = {}
    exec(amfoq__zzs, {}, zuqd__cav)
    jfu__afly = zuqd__cav['pq_impl']
    if bodo.user_logging.get_verbose_level() >= 1:
        hxx__ytp = pq_node.loc.strformat()
        eblix__zhy = []
        lgvnf__mva = []
        for spltl__ghgsu in pq_node.type_usecol_offset:
            jii__ckb = pq_node.df_colnames[spltl__ghgsu]
            eblix__zhy.append(jii__ckb)
            if isinstance(pq_node.out_types[spltl__ghgsu], bodo.libs.
                dict_arr_ext.DictionaryArrayType):
                lgvnf__mva.append(jii__ckb)
        dgjk__ask = (
            'Finish column pruning on read_parquet node:\n%s\nColumns loaded %s\n'
            )
        bodo.user_logging.log_message('Column Pruning', dgjk__ask, hxx__ytp,
            eblix__zhy)
        if lgvnf__mva:
            jlzx__dtsvl = """Finished optimized encoding on read_parquet node:
%s
Columns %s using dictionary encoding to reduce memory usage.
"""
            bodo.user_logging.log_message('Dictionary Encoding',
                jlzx__dtsvl, hxx__ytp, lgvnf__mva)
    parallel = False
    if array_dists is not None:
        opxs__kjdt = pq_node.out_vars[0].name
        parallel = array_dists[opxs__kjdt] in (distributed_pass.
            Distribution.OneD, distributed_pass.Distribution.OneD_Var)
        uxbjo__ztlks = pq_node.out_vars[1].name
        assert typemap[uxbjo__ztlks
            ] == types.none or not parallel or array_dists[uxbjo__ztlks] in (
            distributed_pass.Distribution.OneD, distributed_pass.
            Distribution.OneD_Var
            ), 'pq data/index parallelization does not match'
    if pq_node.unsupported_columns:
        xyx__ugvwf = set(pq_node.type_usecol_offset)
        xnc__hor = set(pq_node.unsupported_columns)
        mfyq__rghn = xyx__ugvwf & xnc__hor
        if mfyq__rghn:
            xckas__dpx = sorted(mfyq__rghn)
            pvcd__gjp = [
                f'pandas.read_parquet(): 1 or more columns found with Arrow types that are not supported in Bodo and could not be eliminated. '
                 +
                "Please manually remove these columns from your read_parquet with the 'columns' argument. If these "
                 +
                'columns are needed, you will need to modify your dataset to use a supported type.'
                , 'Unsupported Columns:']
            txib__lrynd = 0
            for jelc__gjob in xckas__dpx:
                while pq_node.unsupported_columns[txib__lrynd] != jelc__gjob:
                    txib__lrynd += 1
                pvcd__gjp.append(
                    f"Column '{pq_node.df_colnames[jelc__gjob]}' with unsupported arrow type {pq_node.unsupported_arrow_types[txib__lrynd]}"
                    )
                txib__lrynd += 1
            zslfn__hufcd = '\n'.join(pvcd__gjp)
            raise BodoError(zslfn__hufcd, loc=pq_node.loc)
    gaotg__dxg = _gen_pq_reader_py(pq_node.df_colnames, pq_node.col_indices,
        pq_node.type_usecol_offset, pq_node.out_types, pq_node.
        storage_options, pq_node.partition_names, dnf_filter_str,
        expr_filter_str, extra_args, parallel, meta_head_only_info, pq_node
        .index_column_index, pq_node.index_column_type, pq_node.
        input_file_name_col)
    wytv__xknht = typemap[pq_node.file_name.name]
    qizky__hgytq = (wytv__xknht,) + tuple(typemap[jnszu__ner.name] for
        jnszu__ner in cpr__ujy)
    fnrx__knrog = compile_to_numba_ir(jfu__afly, {'_pq_reader_py':
        gaotg__dxg}, typingctx=typingctx, targetctx=targetctx, arg_typs=
        qizky__hgytq, typemap=typemap, calltypes=calltypes).blocks.popitem()[1]
    replace_arg_nodes(fnrx__knrog, [pq_node.file_name] + cpr__ujy)
    daasg__knuj = fnrx__knrog.body[:-3]
    if meta_head_only_info:
        daasg__knuj[-1 - vccuv__tuwif].target = meta_head_only_info[1]
    daasg__knuj[-2].target = pq_node.out_vars[0]
    daasg__knuj[-1].target = pq_node.out_vars[1]
    return daasg__knuj


distributed_pass.distributed_run_extensions[bodo.ir.parquet_ext.ParquetReader
    ] = pq_distributed_run


def get_filters_pyobject(dnf_filter_str, expr_filter_str, vars):
    pass


@overload(get_filters_pyobject, no_unliteral=True)
def overload_get_filters_pyobject(dnf_filter_str, expr_filter_str, var_tup):
    ylr__ellxu = get_overload_const_str(dnf_filter_str)
    ngluq__zkvw = get_overload_const_str(expr_filter_str)
    fnrzs__vafls = ', '.join(f'f{spltl__ghgsu}' for spltl__ghgsu in range(
        len(var_tup)))
    amfoq__zzs = 'def impl(dnf_filter_str, expr_filter_str, var_tup):\n'
    if len(var_tup):
        amfoq__zzs += f'  {fnrzs__vafls}, = var_tup\n'
    amfoq__zzs += """  with numba.objmode(dnf_filters_py='parquet_predicate_type', expr_filters_py='parquet_predicate_type'):
"""
    amfoq__zzs += f'    dnf_filters_py = {ylr__ellxu}\n'
    amfoq__zzs += f'    expr_filters_py = {ngluq__zkvw}\n'
    amfoq__zzs += '  return (dnf_filters_py, expr_filters_py)\n'
    zuqd__cav = {}
    exec(amfoq__zzs, globals(), zuqd__cav)
    return zuqd__cav['impl']


@numba.njit
def get_fname_pyobject(fname):
    with numba.objmode(fname_py='read_parquet_fpath_type'):
        fname_py = fname
    return fname_py


def get_storage_options_pyobject(storage_options):
    pass


@overload(get_storage_options_pyobject, no_unliteral=True)
def overload_get_storage_options_pyobject(storage_options):
    sptw__mzjnl = get_overload_constant_dict(storage_options)
    amfoq__zzs = 'def impl(storage_options):\n'
    amfoq__zzs += (
        "  with numba.objmode(storage_options_py='storage_options_dict_type'):\n"
        )
    amfoq__zzs += f'    storage_options_py = {str(sptw__mzjnl)}\n'
    amfoq__zzs += '  return storage_options_py\n'
    zuqd__cav = {}
    exec(amfoq__zzs, globals(), zuqd__cav)
    return zuqd__cav['impl']


def _gen_pq_reader_py(col_names, col_indices, type_usecol_offset, out_types,
    storage_options, partition_names, dnf_filter_str, expr_filter_str,
    extra_args, is_parallel, meta_head_only_info, index_column_index,
    index_column_type, input_file_name_col):
    iltns__zhy = next_label()
    nhf__lwjb = ',' if extra_args else ''
    amfoq__zzs = f'def pq_reader_py(fname,{extra_args}):\n'
    amfoq__zzs += (
        f"    ev = bodo.utils.tracing.Event('read_parquet', {is_parallel})\n")
    amfoq__zzs += f"    ev.add_attribute('fname', fname)\n"
    amfoq__zzs += f"""    bucket_region = bodo.io.fs_io.get_s3_bucket_region_njit(fname, parallel={is_parallel})
"""
    amfoq__zzs += f"""    dnf_filters, expr_filters = get_filters_pyobject("{dnf_filter_str}", "{expr_filter_str}", ({extra_args}{nhf__lwjb}))
"""
    amfoq__zzs += '    fname_py = get_fname_pyobject(fname)\n'
    storage_options['bodo_dummy'] = 'dummy'
    amfoq__zzs += (
        f'    storage_options_py = get_storage_options_pyobject({str(storage_options)})\n'
        )
    tot_rows_to_read = -1
    if meta_head_only_info and meta_head_only_info[0] is not None:
        tot_rows_to_read = meta_head_only_info[0]
    kob__kaj = not type_usecol_offset
    uefm__cfy = [sanitize_varname(c) for c in col_names]
    partition_names = [sanitize_varname(c) for c in partition_names]
    input_file_name_col = sanitize_varname(input_file_name_col
        ) if input_file_name_col is not None and col_names.index(
        input_file_name_col) in type_usecol_offset else None
    dycm__phaa = {c: spltl__ghgsu for spltl__ghgsu, c in enumerate(col_indices)
        }
    ggb__uzkx = {c: spltl__ghgsu for spltl__ghgsu, c in enumerate(uefm__cfy)}
    mih__gosm = []
    fakfe__iber = set()
    hpspe__pbhee = partition_names + [input_file_name_col]
    for spltl__ghgsu in type_usecol_offset:
        if uefm__cfy[spltl__ghgsu] not in hpspe__pbhee:
            mih__gosm.append(col_indices[spltl__ghgsu])
        elif not input_file_name_col or uefm__cfy[spltl__ghgsu
            ] != input_file_name_col:
            fakfe__iber.add(col_indices[spltl__ghgsu])
    if index_column_index is not None:
        mih__gosm.append(index_column_index)
    mih__gosm = sorted(mih__gosm)
    rzgqg__vvdjk = {c: spltl__ghgsu for spltl__ghgsu, c in enumerate(mih__gosm)
        }

    def is_nullable(typ):
        return bodo.utils.utils.is_array_typ(typ, False) and (not
            isinstance(typ, types.Array) and not isinstance(typ, bodo.
            DatetimeArrayType))
    bfnal__wmyi = [(int(is_nullable(out_types[dycm__phaa[eshj__zkv]])) if 
        eshj__zkv != index_column_index else int(is_nullable(
        index_column_type))) for eshj__zkv in mih__gosm]
    str_as_dict_cols = []
    for eshj__zkv in mih__gosm:
        if eshj__zkv == index_column_index:
            xvnt__wxmc = index_column_type
        else:
            xvnt__wxmc = out_types[dycm__phaa[eshj__zkv]]
        if xvnt__wxmc == dict_str_arr_type:
            str_as_dict_cols.append(eshj__zkv)
    uilc__gbm = []
    kyzg__ogsfc = {}
    fuc__yavis = []
    kcd__yuvjh = []
    for spltl__ghgsu, jix__ktkto in enumerate(partition_names):
        try:
            weyo__ewqih = ggb__uzkx[jix__ktkto]
            if col_indices[weyo__ewqih] not in fakfe__iber:
                continue
        except (KeyError, ValueError) as ugsv__jppqf:
            continue
        kyzg__ogsfc[jix__ktkto] = len(uilc__gbm)
        uilc__gbm.append(jix__ktkto)
        fuc__yavis.append(spltl__ghgsu)
        svze__wof = out_types[weyo__ewqih].dtype
        xbaeb__vgva = bodo.hiframes.pd_categorical_ext.get_categories_int_type(
            svze__wof)
        kcd__yuvjh.append(numba_to_c_type(xbaeb__vgva))
    amfoq__zzs += f'    total_rows_np = np.array([0], dtype=np.int64)\n'
    amfoq__zzs += f'    out_table = pq_read(\n'
    amfoq__zzs += f'        fname_py, {is_parallel},\n'
    amfoq__zzs += f'        unicode_to_utf8(bucket_region),\n'
    amfoq__zzs += f'        dnf_filters, expr_filters,\n'
    amfoq__zzs += f"""        storage_options_py, {tot_rows_to_read}, selected_cols_arr_{iltns__zhy}.ctypes,
"""
    amfoq__zzs += f'        {len(mih__gosm)},\n'
    amfoq__zzs += f'        nullable_cols_arr_{iltns__zhy}.ctypes,\n'
    if len(fuc__yavis) > 0:
        amfoq__zzs += (
            f'        np.array({fuc__yavis}, dtype=np.int32).ctypes,\n')
        amfoq__zzs += (
            f'        np.array({kcd__yuvjh}, dtype=np.int32).ctypes,\n')
        amfoq__zzs += f'        {len(fuc__yavis)},\n'
    else:
        amfoq__zzs += f'        0, 0, 0,\n'
    if len(str_as_dict_cols) > 0:
        amfoq__zzs += f"""        np.array({str_as_dict_cols}, dtype=np.int32).ctypes, {len(str_as_dict_cols)},
"""
    else:
        amfoq__zzs += f'        0, 0,\n'
    amfoq__zzs += f'        total_rows_np.ctypes,\n'
    amfoq__zzs += f'        {input_file_name_col is not None},\n'
    amfoq__zzs += f'    )\n'
    amfoq__zzs += f'    check_and_propagate_cpp_exception()\n'
    lkok__uyulv = 'None'
    rufqv__ggx = index_column_type
    mubum__byf = TableType(tuple(out_types))
    if kob__kaj:
        mubum__byf = types.none
    if index_column_index is not None:
        yylmu__jph = rzgqg__vvdjk[index_column_index]
        lkok__uyulv = (
            f'info_to_array(info_from_table(out_table, {yylmu__jph}), index_arr_type)'
            )
    amfoq__zzs += f'    index_arr = {lkok__uyulv}\n'
    if kob__kaj:
        fqmjt__pnaq = None
    else:
        fqmjt__pnaq = []
        rrz__frhv = 0
        iob__zel = col_indices[col_names.index(input_file_name_col)
            ] if input_file_name_col is not None else None
        for spltl__ghgsu, jelc__gjob in enumerate(col_indices):
            if rrz__frhv < len(type_usecol_offset
                ) and spltl__ghgsu == type_usecol_offset[rrz__frhv]:
                rwxr__nzb = col_indices[spltl__ghgsu]
                if iob__zel and rwxr__nzb == iob__zel:
                    fqmjt__pnaq.append(len(mih__gosm) + len(uilc__gbm))
                elif rwxr__nzb in fakfe__iber:
                    jxd__mdbl = uefm__cfy[spltl__ghgsu]
                    fqmjt__pnaq.append(len(mih__gosm) + kyzg__ogsfc[jxd__mdbl])
                else:
                    fqmjt__pnaq.append(rzgqg__vvdjk[jelc__gjob])
                rrz__frhv += 1
            else:
                fqmjt__pnaq.append(-1)
        fqmjt__pnaq = np.array(fqmjt__pnaq, dtype=np.int64)
    if kob__kaj:
        amfoq__zzs += '    T = None\n'
    else:
        amfoq__zzs += f"""    T = cpp_table_to_py_table(out_table, table_idx_{iltns__zhy}, py_table_type_{iltns__zhy})
"""
    amfoq__zzs += f'    delete_table(out_table)\n'
    amfoq__zzs += f'    total_rows = total_rows_np[0]\n'
    amfoq__zzs += f'    ev.finalize()\n'
    amfoq__zzs += f'    return (total_rows, T, index_arr)\n'
    zuqd__cav = {}
    afp__qnugb = {f'py_table_type_{iltns__zhy}': mubum__byf,
        f'table_idx_{iltns__zhy}': fqmjt__pnaq,
        f'selected_cols_arr_{iltns__zhy}': np.array(mih__gosm, np.int32),
        f'nullable_cols_arr_{iltns__zhy}': np.array(bfnal__wmyi, np.int32),
        'index_arr_type': rufqv__ggx, 'cpp_table_to_py_table':
        cpp_table_to_py_table, 'info_to_array': info_to_array,
        'info_from_table': info_from_table, 'delete_table': delete_table,
        'check_and_propagate_cpp_exception':
        check_and_propagate_cpp_exception, 'pq_read': _pq_read,
        'unicode_to_utf8': unicode_to_utf8, 'get_filters_pyobject':
        get_filters_pyobject, 'get_storage_options_pyobject':
        get_storage_options_pyobject, 'get_fname_pyobject':
        get_fname_pyobject, 'np': np, 'pd': pd, 'bodo': bodo}
    exec(amfoq__zzs, afp__qnugb, zuqd__cav)
    gaotg__dxg = zuqd__cav['pq_reader_py']
    cky__wfxr = numba.njit(gaotg__dxg, no_cpython_wrapper=True)
    return cky__wfxr


import pyarrow as pa
_pa_numba_typ_map = {pa.bool_(): types.bool_, pa.int8(): types.int8, pa.
    int16(): types.int16, pa.int32(): types.int32, pa.int64(): types.int64,
    pa.uint8(): types.uint8, pa.uint16(): types.uint16, pa.uint32(): types.
    uint32, pa.uint64(): types.uint64, pa.float32(): types.float32, pa.
    float64(): types.float64, pa.string(): string_type, pa.binary():
    bytes_type, pa.date32(): datetime_date_type, pa.date64(): types.
    NPDatetime('ns'), null(): string_type}


def get_arrow_timestamp_type(pa_ts_typ):
    oawap__knzx = 'ns', 'us', 'ms', 's'
    if pa_ts_typ.unit not in oawap__knzx:
        return types.Array(bodo.datetime64ns, 1, 'C'), False
    elif pa_ts_typ.tz is not None:
        xdirw__awl = pa_ts_typ.to_pandas_dtype().tz
        binux__egazc = bodo.libs.pd_datetime_arr_ext.get_pytz_type_info(
            xdirw__awl)
        return bodo.DatetimeArrayType(binux__egazc), True
    else:
        return types.Array(bodo.datetime64ns, 1, 'C'), True


def _get_numba_typ_from_pa_typ(pa_typ, is_index, nullable_from_metadata,
    category_info, str_as_dict=False):
    if isinstance(pa_typ.type, pa.ListType):
        jryca__nrruy, puazg__fmvkj = _get_numba_typ_from_pa_typ(pa_typ.type
            .value_field, is_index, nullable_from_metadata, category_info)
        return ArrayItemArrayType(jryca__nrruy), puazg__fmvkj
    if isinstance(pa_typ.type, pa.StructType):
        bgry__oltqw = []
        agbl__aug = []
        puazg__fmvkj = True
        for mww__myksk in pa_typ.flatten():
            agbl__aug.append(mww__myksk.name.split('.')[-1])
            rsgn__ukcmu, djsso__ebxq = _get_numba_typ_from_pa_typ(mww__myksk,
                is_index, nullable_from_metadata, category_info)
            bgry__oltqw.append(rsgn__ukcmu)
            puazg__fmvkj = puazg__fmvkj and djsso__ebxq
        return StructArrayType(tuple(bgry__oltqw), tuple(agbl__aug)
            ), puazg__fmvkj
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
        kax__lyus = _pa_numba_typ_map[pa_typ.type.index_type]
        lqyda__wkpsu = PDCategoricalDtype(category_info[pa_typ.name], bodo.
            string_type, pa_typ.type.ordered, int_type=kax__lyus)
        return CategoricalArrayType(lqyda__wkpsu), True
    if isinstance(pa_typ.type, pa.lib.TimestampType):
        return get_arrow_timestamp_type(pa_typ.type)
    elif pa_typ.type in _pa_numba_typ_map:
        uvme__czua = _pa_numba_typ_map[pa_typ.type]
        puazg__fmvkj = True
    else:
        raise BodoError('Arrow data type {} not supported yet'.format(
            pa_typ.type))
    if uvme__czua == datetime_date_type:
        return datetime_date_array_type, puazg__fmvkj
    if uvme__czua == bytes_type:
        return binary_array_type, puazg__fmvkj
    jryca__nrruy = (string_array_type if uvme__czua == string_type else
        types.Array(uvme__czua, 1, 'C'))
    if uvme__czua == types.bool_:
        jryca__nrruy = boolean_array
    if nullable_from_metadata is not None:
        frras__zjh = nullable_from_metadata
    else:
        frras__zjh = use_nullable_int_arr
    if frras__zjh and not is_index and isinstance(uvme__czua, types.Integer
        ) and pa_typ.nullable:
        jryca__nrruy = IntegerArrayType(uvme__czua)
    return jryca__nrruy, puazg__fmvkj


def get_parquet_dataset(fpath, get_row_counts=True, dnf_filters=None,
    expr_filters=None, storage_options=None, read_categories=False,
    is_parallel=False, tot_rows_to_read=None):
    if get_row_counts:
        ttuar__jdeu = tracing.Event('get_parquet_dataset')
    import time
    import pyarrow as pa
    import pyarrow.parquet as pq
    from mpi4py import MPI
    eirj__pzax = MPI.COMM_WORLD
    if isinstance(fpath, list):
        ppetu__morn = urlparse(fpath[0])
        protocol = ppetu__morn.scheme
        xrzq__xph = ppetu__morn.netloc
        for spltl__ghgsu in range(len(fpath)):
            dnf__qfyet = fpath[spltl__ghgsu]
            yamq__maxp = urlparse(dnf__qfyet)
            if yamq__maxp.scheme != protocol:
                raise BodoError(
                    'All parquet files must use the same filesystem protocol')
            if yamq__maxp.netloc != xrzq__xph:
                raise BodoError(
                    'All parquet files must be in the same S3 bucket')
            fpath[spltl__ghgsu] = dnf__qfyet.rstrip('/')
    else:
        ppetu__morn = urlparse(fpath)
        protocol = ppetu__morn.scheme
        fpath = fpath.rstrip('/')
    if protocol in {'gcs', 'gs'}:
        try:
            import gcsfs
        except ImportError as ugsv__jppqf:
            dds__myl = """Couldn't import gcsfs, which is required for Google cloud access. gcsfs can be installed by calling 'conda install -c conda-forge gcsfs'.
"""
            raise BodoError(dds__myl)
    if protocol == 'http':
        try:
            import fsspec
        except ImportError as ugsv__jppqf:
            dds__myl = """Couldn't import fsspec, which is required for http access. fsspec can be installed by calling 'conda install -c conda-forge fsspec'.
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
            higm__qyq = gcsfs.GCSFileSystem(token=None)
            fs.append(higm__qyq)
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
                prefix = f'{protocol}://{ppetu__morn.netloc}'
                path = path[len(prefix):]
            uprt__xtpcj = fs.glob(path)
            if protocol == 's3':
                uprt__xtpcj = [('s3://' + dnf__qfyet) for dnf__qfyet in
                    uprt__xtpcj if not dnf__qfyet.startswith('s3://')]
            elif protocol in {'hdfs', 'abfs', 'abfss'}:
                uprt__xtpcj = [(prefix + dnf__qfyet) for dnf__qfyet in
                    uprt__xtpcj]
        except:
            raise BodoError(
                f'glob pattern expansion not supported for {protocol}')
        if len(uprt__xtpcj) == 0:
            raise BodoError('No files found matching glob pattern')
        return uprt__xtpcj
    smx__gshv = False
    if get_row_counts:
        tml__ympho = getfs(parallel=True)
        smx__gshv = bodo.parquet_validate_schema
    if bodo.get_rank() == 0:
        qua__kaiqo = 1
        uzvx__loaqp = os.cpu_count()
        if uzvx__loaqp is not None and uzvx__loaqp > 1:
            qua__kaiqo = uzvx__loaqp // 2
        try:
            if get_row_counts:
                nqym__dljlg = tracing.Event('pq.ParquetDataset',
                    is_parallel=False)
                if tracing.is_tracing():
                    nqym__dljlg.add_attribute('dnf_filter', str(dnf_filters))
            nauo__jygu = pa.io_thread_count()
            pa.set_io_thread_count(qua__kaiqo)
            if '*' in fpath:
                fpath = glob(protocol, getfs(), fpath)
            if protocol == 's3':
                if isinstance(fpath, list):
                    get_legacy_fs().info(fpath[0])
                else:
                    get_legacy_fs().info(fpath)
            if protocol in {'hdfs', 'abfs', 'abfss'}:
                prefix = f'{protocol}://{ppetu__morn.netloc}'
                if isinstance(fpath, list):
                    qct__xsnj = [dnf__qfyet[len(prefix):] for dnf__qfyet in
                        fpath]
                else:
                    qct__xsnj = fpath[len(prefix):]
            else:
                qct__xsnj = fpath
            ycs__dywjr = pq.ParquetDataset(qct__xsnj, filesystem=
                get_legacy_fs(), filters=None, use_legacy_dataset=True,
                validate_schema=False, metadata_nthreads=qua__kaiqo)
            pa.set_io_thread_count(nauo__jygu)
            apw__fjgnv = bodo.io.pa_parquet.get_dataset_schema(ycs__dywjr)
            if dnf_filters:
                if get_row_counts:
                    nqym__dljlg.add_attribute('num_pieces_before_filter',
                        len(ycs__dywjr.pieces))
                kjko__hums = time.time()
                ycs__dywjr._filter(dnf_filters)
                if get_row_counts:
                    nqym__dljlg.add_attribute('dnf_filter_time', time.time(
                        ) - kjko__hums)
                    nqym__dljlg.add_attribute('num_pieces_after_filter',
                        len(ycs__dywjr.pieces))
            if get_row_counts:
                nqym__dljlg.finalize()
            ycs__dywjr._metadata.fs = None
        except Exception as mjr__sdyj:
            eirj__pzax.bcast(mjr__sdyj)
            raise BodoError(
                f'error from pyarrow: {type(mjr__sdyj).__name__}: {str(mjr__sdyj)}\n'
                )
        if get_row_counts:
            dqef__ciqr = tracing.Event('bcast dataset')
        eirj__pzax.bcast(ycs__dywjr)
        eirj__pzax.bcast(apw__fjgnv)
    else:
        if get_row_counts:
            dqef__ciqr = tracing.Event('bcast dataset')
        ycs__dywjr = eirj__pzax.bcast(None)
        if isinstance(ycs__dywjr, Exception):
            kmjfv__mmjl = ycs__dywjr
            raise BodoError(
                f"""error from pyarrow: {type(kmjfv__mmjl).__name__}: {str(kmjfv__mmjl)}
"""
                )
        apw__fjgnv = eirj__pzax.bcast(None)
    if get_row_counts:
        gkknf__ufk = getfs()
    else:
        gkknf__ufk = get_legacy_fs()
    ycs__dywjr._metadata.fs = gkknf__ufk
    if get_row_counts:
        dqef__ciqr.finalize()
    ycs__dywjr._bodo_total_rows = 0
    if get_row_counts and tot_rows_to_read == 0:
        get_row_counts = smx__gshv = False
        for idmv__nawh in ycs__dywjr.pieces:
            idmv__nawh._bodo_num_rows = 0
    if get_row_counts or smx__gshv:
        if get_row_counts and tracing.is_tracing():
            vryrp__uvnaq = tracing.Event('get_row_counts')
            vryrp__uvnaq.add_attribute('g_num_pieces', len(ycs__dywjr.pieces))
            vryrp__uvnaq.add_attribute('g_expr_filters', str(expr_filters))
        icj__dyay = 0.0
        num_pieces = len(ycs__dywjr.pieces)
        start = get_start(num_pieces, bodo.get_size(), bodo.get_rank())
        xaov__fgb = get_end(num_pieces, bodo.get_size(), bodo.get_rank())
        xugqi__mqvg = 0
        nsy__hwjs = 0
        eab__hoii = 0
        bwj__rjak = True
        if expr_filters is not None:
            import random
            random.seed(37)
            enwcx__xmxz = random.sample(ycs__dywjr.pieces, k=len(ycs__dywjr
                .pieces))
        else:
            enwcx__xmxz = ycs__dywjr.pieces
        for idmv__nawh in enwcx__xmxz:
            idmv__nawh._bodo_num_rows = 0
        fpaths = [idmv__nawh.path for idmv__nawh in enwcx__xmxz[start:
            xaov__fgb]]
        if protocol == 's3':
            xrzq__xph = ppetu__morn.netloc
            prefix = 's3://' + xrzq__xph + '/'
            fpaths = [dnf__qfyet[len(prefix):] for dnf__qfyet in fpaths]
            gkknf__ufk = get_s3_subtree_fs(xrzq__xph, region=getfs().region,
                storage_options=storage_options)
        else:
            gkknf__ufk = getfs()
        pa.set_io_thread_count(4)
        pa.set_cpu_count(4)
        kkx__coa = ds.dataset(fpaths, filesystem=gkknf__ufk, partitioning=
            ds.partitioning(flavor='hive'))
        for mub__gbgj, smhx__rlnsx in zip(enwcx__xmxz[start:xaov__fgb],
            kkx__coa.get_fragments()):
            kjko__hums = time.time()
            lgp__yvrd = smhx__rlnsx.scanner(schema=kkx__coa.schema, filter=
                expr_filters, use_threads=True).count_rows()
            icj__dyay += time.time() - kjko__hums
            mub__gbgj._bodo_num_rows = lgp__yvrd
            xugqi__mqvg += lgp__yvrd
            nsy__hwjs += smhx__rlnsx.num_row_groups
            eab__hoii += sum(yazoh__ihaah.total_byte_size for yazoh__ihaah in
                smhx__rlnsx.row_groups)
            if smx__gshv:
                uas__qeula = smhx__rlnsx.metadata.schema.to_arrow_schema()
                if apw__fjgnv != uas__qeula:
                    print('Schema in {!s} was different. \n{!s}\n\nvs\n\n{!s}'
                        .format(mub__gbgj, uas__qeula, apw__fjgnv))
                    bwj__rjak = False
                    break
        if smx__gshv:
            bwj__rjak = eirj__pzax.allreduce(bwj__rjak, op=MPI.LAND)
            if not bwj__rjak:
                raise BodoError("Schema in parquet files don't match")
        if get_row_counts:
            ycs__dywjr._bodo_total_rows = eirj__pzax.allreduce(xugqi__mqvg,
                op=MPI.SUM)
            zgle__awmos = eirj__pzax.allreduce(nsy__hwjs, op=MPI.SUM)
            eef__adm = eirj__pzax.allreduce(eab__hoii, op=MPI.SUM)
            poa__guv = np.array([idmv__nawh._bodo_num_rows for idmv__nawh in
                ycs__dywjr.pieces])
            poa__guv = eirj__pzax.allreduce(poa__guv, op=MPI.SUM)
            for idmv__nawh, fgrio__kkjf in zip(ycs__dywjr.pieces, poa__guv):
                idmv__nawh._bodo_num_rows = fgrio__kkjf
            if is_parallel and bodo.get_rank(
                ) == 0 and zgle__awmos < bodo.get_size() and zgle__awmos != 0:
                warnings.warn(BodoWarning(
                    f"""Total number of row groups in parquet dataset {fpath} ({zgle__awmos}) is too small for effective IO parallelization.
For best performance the number of row groups should be greater than the number of workers ({bodo.get_size()})
"""
                    ))
            if zgle__awmos == 0:
                pugi__xjwme = 0
            else:
                pugi__xjwme = eef__adm // zgle__awmos
            if (bodo.get_rank() == 0 and eef__adm >= 20 * 1048576 and 
                pugi__xjwme < 1048576 and protocol in REMOTE_FILESYSTEMS):
                warnings.warn(BodoWarning(
                    f'Parquet average row group size is small ({pugi__xjwme} bytes) and can have negative impact on performance when reading from remote sources'
                    ))
            if tracing.is_tracing():
                vryrp__uvnaq.add_attribute('g_total_num_row_groups',
                    zgle__awmos)
                if expr_filters is not None:
                    vryrp__uvnaq.add_attribute('total_scan_time', icj__dyay)
                ocqv__hnzr = np.array([idmv__nawh._bodo_num_rows for
                    idmv__nawh in ycs__dywjr.pieces])
                uaimm__wyh = np.percentile(ocqv__hnzr, [25, 50, 75])
                vryrp__uvnaq.add_attribute('g_row_counts_min', ocqv__hnzr.min()
                    )
                vryrp__uvnaq.add_attribute('g_row_counts_Q1', uaimm__wyh[0])
                vryrp__uvnaq.add_attribute('g_row_counts_median', uaimm__wyh[1]
                    )
                vryrp__uvnaq.add_attribute('g_row_counts_Q3', uaimm__wyh[2])
                vryrp__uvnaq.add_attribute('g_row_counts_max', ocqv__hnzr.max()
                    )
                vryrp__uvnaq.add_attribute('g_row_counts_mean', ocqv__hnzr.
                    mean())
                vryrp__uvnaq.add_attribute('g_row_counts_std', ocqv__hnzr.std()
                    )
                vryrp__uvnaq.add_attribute('g_row_counts_sum', ocqv__hnzr.sum()
                    )
                vryrp__uvnaq.finalize()
    ycs__dywjr._prefix = ''
    if protocol in {'hdfs', 'abfs', 'abfss'}:
        prefix = f'{protocol}://{ppetu__morn.netloc}'
        if len(ycs__dywjr.pieces) > 0:
            mub__gbgj = ycs__dywjr.pieces[0]
            if not mub__gbgj.path.startswith(prefix):
                ycs__dywjr._prefix = prefix
    if read_categories:
        _add_categories_to_pq_dataset(ycs__dywjr)
    if get_row_counts:
        ttuar__jdeu.finalize()
    return ycs__dywjr


def get_scanner_batches(fpaths, expr_filters, selected_fields,
    avg_num_pieces, is_parallel, storage_options, region, prefix,
    str_as_dict_cols, start_offset, rows_to_read):
    import pyarrow as pa
    uzvx__loaqp = os.cpu_count()
    if uzvx__loaqp is None or uzvx__loaqp == 0:
        uzvx__loaqp = 2
    bgcee__qxqe = min(4, uzvx__loaqp)
    pdh__sos = min(16, uzvx__loaqp)
    if is_parallel and len(fpaths) > pdh__sos and len(fpaths
        ) / avg_num_pieces >= 2.0:
        pa.set_io_thread_count(pdh__sos)
        pa.set_cpu_count(pdh__sos)
    else:
        pa.set_io_thread_count(bgcee__qxqe)
        pa.set_cpu_count(bgcee__qxqe)
    if fpaths[0].startswith('s3://'):
        xrzq__xph = urlparse(fpaths[0]).netloc
        prefix = 's3://' + xrzq__xph + '/'
        fpaths = [dnf__qfyet[len(prefix):] for dnf__qfyet in fpaths]
        gkknf__ufk = get_s3_subtree_fs(xrzq__xph, region=region,
            storage_options=storage_options)
    elif prefix and prefix.startswith(('hdfs', 'abfs', 'abfss')):
        gkknf__ufk = get_hdfs_fs(prefix + fpaths[0])
    elif fpaths[0].startswith(('gcs', 'gs')):
        import gcsfs
        gkknf__ufk = gcsfs.GCSFileSystem(token=None)
    else:
        gkknf__ufk = None
    ldu__qxyfp = ds.ParquetFileFormat(dictionary_columns=str_as_dict_cols)
    ycs__dywjr = ds.dataset(fpaths, filesystem=gkknf__ufk, partitioning=ds.
        partitioning(flavor='hive'), format=ldu__qxyfp)
    col_names = ycs__dywjr.schema.names
    dqpre__qjxx = [col_names[cajnn__hrnpi] for cajnn__hrnpi in selected_fields]
    lsari__qkldv = len(fpaths) <= 3 or start_offset > 0 and len(fpaths) <= 10
    if lsari__qkldv and expr_filters is None:
        ifwn__jtisp = []
        inx__bhg = 0
        lnrx__rmd = 0
        for smhx__rlnsx in ycs__dywjr.get_fragments():
            phwz__xgus = []
            for yazoh__ihaah in smhx__rlnsx.row_groups:
                fdbd__ydy = yazoh__ihaah.num_rows
                if start_offset < inx__bhg + fdbd__ydy:
                    if lnrx__rmd == 0:
                        ufxl__ucpmf = start_offset - inx__bhg
                        vjptw__ihu = min(fdbd__ydy - ufxl__ucpmf, rows_to_read)
                    else:
                        vjptw__ihu = min(fdbd__ydy, rows_to_read - lnrx__rmd)
                    lnrx__rmd += vjptw__ihu
                    phwz__xgus.append(yazoh__ihaah.id)
                inx__bhg += fdbd__ydy
                if lnrx__rmd == rows_to_read:
                    break
            ifwn__jtisp.append(smhx__rlnsx.subset(row_group_ids=phwz__xgus))
            if lnrx__rmd == rows_to_read:
                break
        ycs__dywjr = ds.FileSystemDataset(ifwn__jtisp, ycs__dywjr.schema,
            ldu__qxyfp, filesystem=ycs__dywjr.filesystem)
        start_offset = ufxl__ucpmf
    kls__xcqm = ycs__dywjr.scanner(columns=dqpre__qjxx, filter=expr_filters,
        use_threads=True).to_reader()
    return ycs__dywjr, kls__xcqm, start_offset


def _add_categories_to_pq_dataset(pq_dataset):
    import pyarrow as pa
    from mpi4py import MPI
    if len(pq_dataset.pieces) < 1:
        raise BodoError(
            'No pieces found in Parquet dataset. Cannot get read categorical values'
            )
    pa_schema = pq_dataset.schema.to_arrow_schema()
    nyw__qwhkk = [c for c in pa_schema.names if isinstance(pa_schema.field(
        c).type, pa.DictionaryType)]
    if len(nyw__qwhkk) == 0:
        pq_dataset._category_info = {}
        return
    eirj__pzax = MPI.COMM_WORLD
    if bodo.get_rank() == 0:
        try:
            dbxn__xvg = pq_dataset.pieces[0].open()
            yazoh__ihaah = dbxn__xvg.read_row_group(0, nyw__qwhkk)
            category_info = {c: tuple(yazoh__ihaah.column(c).chunk(0).
                dictionary.to_pylist()) for c in nyw__qwhkk}
            del dbxn__xvg, yazoh__ihaah
        except Exception as mjr__sdyj:
            eirj__pzax.bcast(mjr__sdyj)
            raise mjr__sdyj
        eirj__pzax.bcast(category_info)
    else:
        category_info = eirj__pzax.bcast(None)
        if isinstance(category_info, Exception):
            kmjfv__mmjl = category_info
            raise kmjfv__mmjl
    pq_dataset._category_info = category_info


def get_pandas_metadata(schema, num_pieces):
    kovpm__mzdx = None
    nullable_from_metadata = defaultdict(lambda : None)
    gnss__jndu = b'pandas'
    if schema.metadata is not None and gnss__jndu in schema.metadata:
        import json
        ihb__xadd = json.loads(schema.metadata[gnss__jndu].decode('utf8'))
        bsbir__ulb = len(ihb__xadd['index_columns'])
        if bsbir__ulb > 1:
            raise BodoError('read_parquet: MultiIndex not supported yet')
        kovpm__mzdx = ihb__xadd['index_columns'][0] if bsbir__ulb else None
        if not isinstance(kovpm__mzdx, str) and (not isinstance(kovpm__mzdx,
            dict) or num_pieces != 1):
            kovpm__mzdx = None
        for bql__rquo in ihb__xadd['columns']:
            yuhul__ljfe = bql__rquo['name']
            if bql__rquo['pandas_type'].startswith('int'
                ) and yuhul__ljfe is not None:
                if bql__rquo['numpy_type'].startswith('Int'):
                    nullable_from_metadata[yuhul__ljfe] = True
                else:
                    nullable_from_metadata[yuhul__ljfe] = False
    return kovpm__mzdx, nullable_from_metadata


def determine_str_as_dict_columns(pq_dataset, pa_schema):
    from mpi4py import MPI
    eirj__pzax = MPI.COMM_WORLD
    mtbns__kmrr = []
    for yuhul__ljfe in pa_schema.names:
        mww__myksk = pa_schema.field(yuhul__ljfe)
        if mww__myksk.type == pa.string():
            mtbns__kmrr.append((yuhul__ljfe, pa_schema.get_field_index(
                yuhul__ljfe)))
    if len(mtbns__kmrr) == 0:
        return set()
    if len(pq_dataset.pieces) > bodo.get_size():
        import random
        random.seed(37)
        enwcx__xmxz = random.sample(pq_dataset.pieces, bodo.get_size())
    else:
        enwcx__xmxz = pq_dataset.pieces
    juf__knirs = np.zeros(len(mtbns__kmrr), dtype=np.int64)
    gbkt__ykya = np.zeros(len(mtbns__kmrr), dtype=np.int64)
    if bodo.get_rank() < len(enwcx__xmxz):
        mub__gbgj = enwcx__xmxz[bodo.get_rank()]
        cve__ulc = mub__gbgj.get_metadata()
        for spltl__ghgsu in range(cve__ulc.num_row_groups):
            for rrz__frhv, (tml__ympho, txib__lrynd) in enumerate(mtbns__kmrr):
                juf__knirs[rrz__frhv] += cve__ulc.row_group(spltl__ghgsu
                    ).column(txib__lrynd).total_uncompressed_size
        kwdxa__saba = cve__ulc.num_rows
    else:
        kwdxa__saba = 0
    der__kiqjj = eirj__pzax.allreduce(kwdxa__saba, op=MPI.SUM)
    if der__kiqjj == 0:
        return set()
    eirj__pzax.Allreduce(juf__knirs, gbkt__ykya, op=MPI.SUM)
    nnh__xtx = gbkt__ykya / der__kiqjj
    str_as_dict = set()
    for spltl__ghgsu, hwth__pet in enumerate(nnh__xtx):
        if hwth__pet < READ_STR_AS_DICT_THRESHOLD:
            yuhul__ljfe = mtbns__kmrr[spltl__ghgsu][0]
            str_as_dict.add(yuhul__ljfe)
    return str_as_dict


def parquet_file_schema(file_name, selected_columns, storage_options=None,
    input_file_name_col=None):
    col_names = []
    ueov__bpai = []
    pq_dataset = get_parquet_dataset(file_name, get_row_counts=False,
        storage_options=storage_options, read_categories=True)
    partition_names = [] if pq_dataset.partitions is None else [pq_dataset.
        partitions.levels[spltl__ghgsu].name for spltl__ghgsu in range(len(
        pq_dataset.partitions.partition_names))]
    pa_schema = pq_dataset.schema.to_arrow_schema()
    num_pieces = len(pq_dataset.pieces)
    str_as_dict = determine_str_as_dict_columns(pq_dataset, pa_schema)
    col_names = pa_schema.names
    kovpm__mzdx, nullable_from_metadata = get_pandas_metadata(pa_schema,
        num_pieces)
    oyk__esd = []
    lcj__zvw = []
    wtey__rpiwk = []
    for spltl__ghgsu, c in enumerate(col_names):
        mww__myksk = pa_schema.field(c)
        uvme__czua, puazg__fmvkj = _get_numba_typ_from_pa_typ(mww__myksk, c ==
            kovpm__mzdx, nullable_from_metadata[c], pq_dataset.
            _category_info, str_as_dict=c in str_as_dict)
        oyk__esd.append(uvme__czua)
        lcj__zvw.append(puazg__fmvkj)
        wtey__rpiwk.append(mww__myksk.type)
    if partition_names:
        col_names += partition_names
        oyk__esd += [_get_partition_cat_dtype(pq_dataset.partitions.levels[
            spltl__ghgsu]) for spltl__ghgsu in range(len(partition_names))]
        lcj__zvw.extend([True] * len(partition_names))
        wtey__rpiwk.extend([None] * len(partition_names))
    if input_file_name_col is not None:
        col_names += [input_file_name_col]
        oyk__esd += [dict_str_arr_type]
        lcj__zvw.append(True)
        wtey__rpiwk.append(None)
    zgiej__mmglg = {c: spltl__ghgsu for spltl__ghgsu, c in enumerate(col_names)
        }
    if selected_columns is None:
        selected_columns = col_names
    for c in selected_columns:
        if c not in zgiej__mmglg:
            raise BodoError(f'Selected column {c} not in Parquet file schema')
    if kovpm__mzdx and not isinstance(kovpm__mzdx, dict
        ) and kovpm__mzdx not in selected_columns:
        selected_columns.append(kovpm__mzdx)
    col_names = selected_columns
    col_indices = []
    ueov__bpai = []
    zvdz__cqxga = []
    pojrr__tve = []
    for spltl__ghgsu, c in enumerate(col_names):
        rwxr__nzb = zgiej__mmglg[c]
        col_indices.append(rwxr__nzb)
        ueov__bpai.append(oyk__esd[rwxr__nzb])
        if not lcj__zvw[rwxr__nzb]:
            zvdz__cqxga.append(spltl__ghgsu)
            pojrr__tve.append(wtey__rpiwk[rwxr__nzb])
    return (col_names, ueov__bpai, kovpm__mzdx, col_indices,
        partition_names, zvdz__cqxga, pojrr__tve)


def _get_partition_cat_dtype(part_set):
    miea__kjdkb = part_set.dictionary.to_pandas()
    thy__rzztc = bodo.typeof(miea__kjdkb).dtype
    lqyda__wkpsu = PDCategoricalDtype(tuple(miea__kjdkb), thy__rzztc, False)
    return CategoricalArrayType(lqyda__wkpsu)


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
        eos__ivs = lir.FunctionType(lir.VoidType(), [lir.IntType(8).
            as_pointer(), lir.IntType(8).as_pointer(), lir.IntType(8).
            as_pointer(), lir.IntType(8).as_pointer(), lir.IntType(1), lir.
            IntType(8).as_pointer(), lir.IntType(8).as_pointer(), lir.
            IntType(1), lir.IntType(1), lir.IntType(32), lir.IntType(32),
            lir.IntType(32), lir.IntType(8).as_pointer(), lir.IntType(8).
            as_pointer()])
        dmw__eivn = cgutils.get_or_insert_function(builder.module, eos__ivs,
            name='pq_write')
        builder.call(dmw__eivn, args)
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
        eos__ivs = lir.FunctionType(lir.VoidType(), [lir.IntType(8).
            as_pointer(), lir.IntType(8).as_pointer(), lir.IntType(8).
            as_pointer(), lir.IntType(8).as_pointer(), lir.IntType(8).
            as_pointer(), lir.IntType(8).as_pointer(), lir.IntType(32), lir
            .IntType(8).as_pointer(), lir.IntType(1), lir.IntType(8).
            as_pointer()])
        dmw__eivn = cgutils.get_or_insert_function(builder.module, eos__ivs,
            name='pq_write_partitioned')
        builder.call(dmw__eivn, args)
        bodo.utils.utils.inlined_check_and_propagate_cpp_exception(context,
            builder)
    return types.void(types.voidptr, data_table_t, col_names_t,
        col_names_no_partitions_t, cat_table_t, types.voidptr, types.int32,
        types.voidptr, types.boolean, types.voidptr), codegen
