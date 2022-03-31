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
        except OSError as dpmc__nobu:
            if 'non-file path' in str(dpmc__nobu):
                raise FileNotFoundError(str(dpmc__nobu))
            raise


class ParquetHandler:

    def __init__(self, func_ir, typingctx, args, _locals):
        self.func_ir = func_ir
        self.typingctx = typingctx
        self.args = args
        self.locals = _locals

    def gen_parquet_read(self, file_name, lhs, columns, storage_options=
        None, input_file_name_col=None):
        wcgu__iwuqb = lhs.scope
        esddf__jbaj = lhs.loc
        qtdp__mjgr = None
        if lhs.name in self.locals:
            qtdp__mjgr = self.locals[lhs.name]
            self.locals.pop(lhs.name)
        qcbj__qrxq = {}
        if lhs.name + ':convert' in self.locals:
            qcbj__qrxq = self.locals[lhs.name + ':convert']
            self.locals.pop(lhs.name + ':convert')
        if qtdp__mjgr is None:
            lcx__ley = (
                'Parquet schema not available. Either path argument should be constant for Bodo to look at the file at compile time or schema should be provided. For more information, see: https://docs.bodo.ai/latest/source/programming_with_bodo/file_io.html#non-constant-filepaths'
                )
            cqb__ucq = get_const_value(file_name, self.func_ir, lcx__ley,
                arg_types=self.args, file_info=ParquetFileInfo(columns,
                storage_options=storage_options, input_file_name_col=
                input_file_name_col))
            godjg__epfpj = False
            arnzf__xuvvx = guard(get_definition, self.func_ir, file_name)
            if isinstance(arnzf__xuvvx, ir.Arg):
                typ = self.args[arnzf__xuvvx.index]
                if isinstance(typ, types.FilenameType):
                    (col_names, lcjy__sipuz, ohpg__saw, col_indices,
                        partition_names, iwvch__uvit, joqq__rdev) = typ.schema
                    godjg__epfpj = True
            if not godjg__epfpj:
                (col_names, lcjy__sipuz, ohpg__saw, col_indices,
                    partition_names, iwvch__uvit, joqq__rdev) = (
                    parquet_file_schema(cqb__ucq, columns, storage_options=
                    storage_options, input_file_name_col=input_file_name_col))
        else:
            uwgcr__pevsp = list(qtdp__mjgr.keys())
            mtzbx__nxa = {c: unzph__hzaes for unzph__hzaes, c in enumerate(
                uwgcr__pevsp)}
            fxcp__tbc = [kakrj__gjhiz for kakrj__gjhiz in qtdp__mjgr.values()]
            ohpg__saw = 'index' if 'index' in mtzbx__nxa else None
            if columns is None:
                selected_columns = uwgcr__pevsp
            else:
                selected_columns = columns
            col_indices = [mtzbx__nxa[c] for c in selected_columns]
            lcjy__sipuz = [fxcp__tbc[mtzbx__nxa[c]] for c in selected_columns]
            col_names = selected_columns
            ohpg__saw = ohpg__saw if ohpg__saw in col_names else None
            partition_names = []
            iwvch__uvit = []
            joqq__rdev = []
        pewq__uqq = None if isinstance(ohpg__saw, dict
            ) or ohpg__saw is None else ohpg__saw
        index_column_index = None
        index_column_type = types.none
        if pewq__uqq:
            emvfg__pahlt = col_names.index(pewq__uqq)
            index_column_index = col_indices.pop(emvfg__pahlt)
            index_column_type = lcjy__sipuz.pop(emvfg__pahlt)
            col_names.pop(emvfg__pahlt)
        for unzph__hzaes, c in enumerate(col_names):
            if c in qcbj__qrxq:
                lcjy__sipuz[unzph__hzaes] = qcbj__qrxq[c]
        qxwt__wfp = [ir.Var(wcgu__iwuqb, mk_unique_var('pq_table'),
            esddf__jbaj), ir.Var(wcgu__iwuqb, mk_unique_var('pq_index'),
            esddf__jbaj)]
        hmwco__njf = [bodo.ir.parquet_ext.ParquetReader(file_name, lhs.name,
            col_names, col_indices, lcjy__sipuz, qxwt__wfp, esddf__jbaj,
            partition_names, storage_options, index_column_index,
            index_column_type, input_file_name_col, iwvch__uvit, joqq__rdev)]
        return (col_names, qxwt__wfp, ohpg__saw, hmwco__njf, lcjy__sipuz,
            index_column_type)


def determine_filter_cast(pq_node, typemap, filter_val, orig_colname_map):
    tqho__qjsv = filter_val[0]
    arpxk__hvvq = pq_node.original_out_types[orig_colname_map[tqho__qjsv]]
    icd__zgc = bodo.utils.typing.element_type(arpxk__hvvq)
    if tqho__qjsv in pq_node.partition_names:
        if icd__zgc == types.unicode_type:
            gitjt__twzwa = '.cast(pyarrow.string(), safe=False)'
        elif isinstance(icd__zgc, types.Integer):
            gitjt__twzwa = f'.cast(pyarrow.{icd__zgc.name}(), safe=False)'
        else:
            gitjt__twzwa = ''
    else:
        gitjt__twzwa = ''
    wldy__irdbi = typemap[filter_val[2].name]
    if isinstance(wldy__irdbi, (types.List, types.Set)):
        cjttl__sxpkq = wldy__irdbi.dtype
    else:
        cjttl__sxpkq = wldy__irdbi
    if not bodo.utils.typing.is_common_scalar_dtype([icd__zgc, cjttl__sxpkq]):
        if not bodo.utils.typing.is_safe_arrow_cast(icd__zgc, cjttl__sxpkq):
            raise BodoError(
                f'Unsupported Arrow cast from {icd__zgc} to {cjttl__sxpkq} in filter pushdown. Please try a comparison that avoids casting the column.'
                )
        if icd__zgc == types.unicode_type:
            return ".cast(pyarrow.timestamp('ns'), safe=False)", ''
        elif icd__zgc in (bodo.datetime64ns, bodo.pd_timestamp_type):
            if isinstance(wldy__irdbi, (types.List, types.Set)):
                nsh__kvt = 'list' if isinstance(wldy__irdbi, types.List
                    ) else 'tuple'
                raise BodoError(
                    f'Cannot cast {nsh__kvt} values with isin filter pushdown.'
                    )
            return gitjt__twzwa, ".cast(pyarrow.timestamp('ns'), safe=False)"
    return gitjt__twzwa, ''


def pq_distributed_run(pq_node, array_dists, typemap, calltypes, typingctx,
    targetctx, meta_head_only_info=None):
    xwnwx__rooi = len(pq_node.out_vars)
    extra_args = ''
    dnf_filter_str = 'None'
    expr_filter_str = 'None'
    rtd__atq, gcaoi__qatg = bodo.ir.connector.generate_filter_map(pq_node.
        filters)
    if pq_node.filters:
        eff__avb = []
        lbr__albt = []
        nooyb__epdf = False
        ucau__izfp = None
        orig_colname_map = {c: unzph__hzaes for unzph__hzaes, c in
            enumerate(pq_node.original_df_colnames)}
        for cqatu__gil in pq_node.filters:
            rmsfv__ihw = []
            psyrr__thy = []
            godf__lwj = set()
            for xltr__eue in cqatu__gil:
                if isinstance(xltr__eue[2], ir.Var):
                    wzf__nuvwk, kmhy__bivdp = determine_filter_cast(pq_node,
                        typemap, xltr__eue, orig_colname_map)
                    if xltr__eue[1] == 'in':
                        psyrr__thy.append(
                            f"(ds.field('{xltr__eue[0]}').isin({rtd__atq[xltr__eue[2].name]}))"
                            )
                    else:
                        psyrr__thy.append(
                            f"(ds.field('{xltr__eue[0]}'){wzf__nuvwk} {xltr__eue[1]} ds.scalar({rtd__atq[xltr__eue[2].name]}){kmhy__bivdp})"
                            )
                else:
                    assert xltr__eue[2
                        ] == 'NULL', 'unsupport constant used in filter pushdown'
                    if xltr__eue[1] == 'is not':
                        prefix = '~'
                    else:
                        prefix = ''
                    psyrr__thy.append(
                        f"({prefix}ds.field('{xltr__eue[0]}').is_null())")
                if xltr__eue[0] in pq_node.partition_names and isinstance(
                    xltr__eue[2], ir.Var):
                    azvcs__dyk = (
                        f"('{xltr__eue[0]}', '{xltr__eue[1]}', {rtd__atq[xltr__eue[2].name]})"
                        )
                    rmsfv__ihw.append(azvcs__dyk)
                    godf__lwj.add(azvcs__dyk)
                else:
                    nooyb__epdf = True
            if ucau__izfp is None:
                ucau__izfp = godf__lwj
            else:
                ucau__izfp.intersection_update(godf__lwj)
            ang__kovw = ', '.join(rmsfv__ihw)
            scjzo__vett = ' & '.join(psyrr__thy)
            if ang__kovw:
                eff__avb.append(f'[{ang__kovw}]')
            lbr__albt.append(f'({scjzo__vett})')
        ept__igmlg = ', '.join(eff__avb)
        ntjit__tjwxe = ' | '.join(lbr__albt)
        if nooyb__epdf:
            if ucau__izfp:
                wmsv__bfzg = sorted(ucau__izfp)
                dnf_filter_str = f"[[{', '.join(wmsv__bfzg)}]]"
        elif ept__igmlg:
            dnf_filter_str = f'[{ept__igmlg}]'
        expr_filter_str = f'({ntjit__tjwxe})'
        extra_args = ', '.join(rtd__atq.values())
    ekcsq__xdil = ', '.join(f'out{unzph__hzaes}' for unzph__hzaes in range(
        xwnwx__rooi))
    nkxxd__mcyil = f'def pq_impl(fname, {extra_args}):\n'
    nkxxd__mcyil += (
        f'    (total_rows, {ekcsq__xdil},) = _pq_reader_py(fname, {extra_args})\n'
        )
    lzw__izjuo = {}
    exec(nkxxd__mcyil, {}, lzw__izjuo)
    ldgl__yam = lzw__izjuo['pq_impl']
    if bodo.user_logging.get_verbose_level() >= 1:
        hcho__iyae = pq_node.loc.strformat()
        xput__ejq = []
        vhpkz__tpgy = []
        for unzph__hzaes in pq_node.type_usecol_offset:
            tqho__qjsv = pq_node.df_colnames[unzph__hzaes]
            xput__ejq.append(tqho__qjsv)
            if isinstance(pq_node.out_types[unzph__hzaes], bodo.libs.
                dict_arr_ext.DictionaryArrayType):
                vhpkz__tpgy.append(tqho__qjsv)
        bidt__sbd = (
            'Finish column pruning on read_parquet node:\n%s\nColumns loaded %s\n'
            )
        bodo.user_logging.log_message('Column Pruning', bidt__sbd,
            hcho__iyae, xput__ejq)
        if vhpkz__tpgy:
            kialn__aopr = """Finished optimized encoding on read_parquet node:
%s
Columns %s using dictionary encoding to reduce memory usage.
"""
            bodo.user_logging.log_message('Dictionary Encoding',
                kialn__aopr, hcho__iyae, vhpkz__tpgy)
    parallel = False
    if array_dists is not None:
        wvjed__zsc = pq_node.out_vars[0].name
        parallel = array_dists[wvjed__zsc] in (distributed_pass.
            Distribution.OneD, distributed_pass.Distribution.OneD_Var)
        fbj__nixm = pq_node.out_vars[1].name
        assert typemap[fbj__nixm] == types.none or not parallel or array_dists[
            fbj__nixm] in (distributed_pass.Distribution.OneD,
            distributed_pass.Distribution.OneD_Var
            ), 'pq data/index parallelization does not match'
    if pq_node.unsupported_columns:
        jfi__eonu = set(pq_node.type_usecol_offset)
        lxr__ayyb = set(pq_node.unsupported_columns)
        xxatq__pzltp = jfi__eonu & lxr__ayyb
        if xxatq__pzltp:
            yjbkn__ejf = sorted(xxatq__pzltp)
            vfk__wsl = [
                f'pandas.read_parquet(): 1 or more columns found with Arrow types that are not supported in Bodo and could not be eliminated. '
                 +
                "Please manually remove these columns from your read_parquet with the 'columns' argument. If these "
                 +
                'columns are needed, you will need to modify your dataset to use a supported type.'
                , 'Unsupported Columns:']
            dlxee__ovjmd = 0
            for aeff__ivgb in yjbkn__ejf:
                while pq_node.unsupported_columns[dlxee__ovjmd] != aeff__ivgb:
                    dlxee__ovjmd += 1
                vfk__wsl.append(
                    f"Column '{pq_node.df_colnames[aeff__ivgb]}' with unsupported arrow type {pq_node.unsupported_arrow_types[dlxee__ovjmd]}"
                    )
                dlxee__ovjmd += 1
            hfdtz__tdj = '\n'.join(vfk__wsl)
            raise BodoError(hfdtz__tdj, loc=pq_node.loc)
    wfzid__xoyya = _gen_pq_reader_py(pq_node.df_colnames, pq_node.
        col_indices, pq_node.type_usecol_offset, pq_node.out_types, pq_node
        .storage_options, pq_node.partition_names, dnf_filter_str,
        expr_filter_str, extra_args, parallel, meta_head_only_info, pq_node
        .index_column_index, pq_node.index_column_type, pq_node.
        input_file_name_col)
    jvcwl__bxto = typemap[pq_node.file_name.name]
    kuo__agy = (jvcwl__bxto,) + tuple(typemap[xltr__eue.name] for xltr__eue in
        gcaoi__qatg)
    sxmtr__eltmb = compile_to_numba_ir(ldgl__yam, {'_pq_reader_py':
        wfzid__xoyya}, typingctx=typingctx, targetctx=targetctx, arg_typs=
        kuo__agy, typemap=typemap, calltypes=calltypes).blocks.popitem()[1]
    replace_arg_nodes(sxmtr__eltmb, [pq_node.file_name] + gcaoi__qatg)
    hmwco__njf = sxmtr__eltmb.body[:-3]
    if meta_head_only_info:
        hmwco__njf[-1 - xwnwx__rooi].target = meta_head_only_info[1]
    hmwco__njf[-2].target = pq_node.out_vars[0]
    hmwco__njf[-1].target = pq_node.out_vars[1]
    return hmwco__njf


distributed_pass.distributed_run_extensions[bodo.ir.parquet_ext.ParquetReader
    ] = pq_distributed_run


def get_filters_pyobject(dnf_filter_str, expr_filter_str, vars):
    pass


@overload(get_filters_pyobject, no_unliteral=True)
def overload_get_filters_pyobject(dnf_filter_str, expr_filter_str, var_tup):
    jjbke__dhy = get_overload_const_str(dnf_filter_str)
    piysg__xgad = get_overload_const_str(expr_filter_str)
    ugtr__bcndm = ', '.join(f'f{unzph__hzaes}' for unzph__hzaes in range(
        len(var_tup)))
    nkxxd__mcyil = 'def impl(dnf_filter_str, expr_filter_str, var_tup):\n'
    if len(var_tup):
        nkxxd__mcyil += f'  {ugtr__bcndm}, = var_tup\n'
    nkxxd__mcyil += """  with numba.objmode(dnf_filters_py='parquet_predicate_type', expr_filters_py='parquet_predicate_type'):
"""
    nkxxd__mcyil += f'    dnf_filters_py = {jjbke__dhy}\n'
    nkxxd__mcyil += f'    expr_filters_py = {piysg__xgad}\n'
    nkxxd__mcyil += '  return (dnf_filters_py, expr_filters_py)\n'
    lzw__izjuo = {}
    exec(nkxxd__mcyil, globals(), lzw__izjuo)
    return lzw__izjuo['impl']


@numba.njit
def get_fname_pyobject(fname):
    with numba.objmode(fname_py='read_parquet_fpath_type'):
        fname_py = fname
    return fname_py


def get_storage_options_pyobject(storage_options):
    pass


@overload(get_storage_options_pyobject, no_unliteral=True)
def overload_get_storage_options_pyobject(storage_options):
    odiyv__udel = get_overload_constant_dict(storage_options)
    nkxxd__mcyil = 'def impl(storage_options):\n'
    nkxxd__mcyil += (
        "  with numba.objmode(storage_options_py='storage_options_dict_type'):\n"
        )
    nkxxd__mcyil += f'    storage_options_py = {str(odiyv__udel)}\n'
    nkxxd__mcyil += '  return storage_options_py\n'
    lzw__izjuo = {}
    exec(nkxxd__mcyil, globals(), lzw__izjuo)
    return lzw__izjuo['impl']


def _gen_pq_reader_py(col_names, col_indices, type_usecol_offset, out_types,
    storage_options, partition_names, dnf_filter_str, expr_filter_str,
    extra_args, is_parallel, meta_head_only_info, index_column_index,
    index_column_type, input_file_name_col):
    ixvcq__hlkck = next_label()
    hax__nphtj = ',' if extra_args else ''
    nkxxd__mcyil = f'def pq_reader_py(fname,{extra_args}):\n'
    nkxxd__mcyil += (
        f"    ev = bodo.utils.tracing.Event('read_parquet', {is_parallel})\n")
    nkxxd__mcyil += f"    ev.add_attribute('fname', fname)\n"
    nkxxd__mcyil += f"""    bucket_region = bodo.io.fs_io.get_s3_bucket_region_njit(fname, parallel={is_parallel})
"""
    nkxxd__mcyil += f"""    dnf_filters, expr_filters = get_filters_pyobject("{dnf_filter_str}", "{expr_filter_str}", ({extra_args}{hax__nphtj}))
"""
    nkxxd__mcyil += '    fname_py = get_fname_pyobject(fname)\n'
    storage_options['bodo_dummy'] = 'dummy'
    nkxxd__mcyil += f"""    storage_options_py = get_storage_options_pyobject({str(storage_options)})
"""
    tot_rows_to_read = -1
    if meta_head_only_info and meta_head_only_info[0] is not None:
        tot_rows_to_read = meta_head_only_info[0]
    lbs__asd = not type_usecol_offset
    wjnsv__fxmna = [sanitize_varname(c) for c in col_names]
    partition_names = [sanitize_varname(c) for c in partition_names]
    input_file_name_col = sanitize_varname(input_file_name_col
        ) if input_file_name_col is not None and col_names.index(
        input_file_name_col) in type_usecol_offset else None
    cyp__mbtej = {c: unzph__hzaes for unzph__hzaes, c in enumerate(col_indices)
        }
    wydn__jyk = {c: unzph__hzaes for unzph__hzaes, c in enumerate(wjnsv__fxmna)
        }
    lzen__zielq = []
    waupc__pwy = set()
    zcp__fghv = partition_names + [input_file_name_col]
    for unzph__hzaes in type_usecol_offset:
        if wjnsv__fxmna[unzph__hzaes] not in zcp__fghv:
            lzen__zielq.append(col_indices[unzph__hzaes])
        elif not input_file_name_col or wjnsv__fxmna[unzph__hzaes
            ] != input_file_name_col:
            waupc__pwy.add(col_indices[unzph__hzaes])
    if index_column_index is not None:
        lzen__zielq.append(index_column_index)
    lzen__zielq = sorted(lzen__zielq)
    ttaa__gvzou = {c: unzph__hzaes for unzph__hzaes, c in enumerate(
        lzen__zielq)}

    def is_nullable(typ):
        return bodo.utils.utils.is_array_typ(typ, False) and (not
            isinstance(typ, types.Array) and not isinstance(typ, bodo.
            DatetimeArrayType))
    wra__ogfx = [(int(is_nullable(out_types[cyp__mbtej[qfcp__iem]])) if 
        qfcp__iem != index_column_index else int(is_nullable(
        index_column_type))) for qfcp__iem in lzen__zielq]
    str_as_dict_cols = []
    for qfcp__iem in lzen__zielq:
        if qfcp__iem == index_column_index:
            kakrj__gjhiz = index_column_type
        else:
            kakrj__gjhiz = out_types[cyp__mbtej[qfcp__iem]]
        if kakrj__gjhiz == dict_str_arr_type:
            str_as_dict_cols.append(qfcp__iem)
    dex__yrzq = []
    vcu__ooh = {}
    lolas__zbs = []
    dkfaw__qsw = []
    for unzph__hzaes, wrfox__omzq in enumerate(partition_names):
        try:
            ptsi__otxxr = wydn__jyk[wrfox__omzq]
            if col_indices[ptsi__otxxr] not in waupc__pwy:
                continue
        except (KeyError, ValueError) as gwiq__ggyi:
            continue
        vcu__ooh[wrfox__omzq] = len(dex__yrzq)
        dex__yrzq.append(wrfox__omzq)
        lolas__zbs.append(unzph__hzaes)
        sftfy__lvgl = out_types[ptsi__otxxr].dtype
        vfra__lbp = bodo.hiframes.pd_categorical_ext.get_categories_int_type(
            sftfy__lvgl)
        dkfaw__qsw.append(numba_to_c_type(vfra__lbp))
    nkxxd__mcyil += f'    total_rows_np = np.array([0], dtype=np.int64)\n'
    nkxxd__mcyil += f'    out_table = pq_read(\n'
    nkxxd__mcyil += f'        fname_py, {is_parallel},\n'
    nkxxd__mcyil += f'        unicode_to_utf8(bucket_region),\n'
    nkxxd__mcyil += f'        dnf_filters, expr_filters,\n'
    nkxxd__mcyil += f"""        storage_options_py, {tot_rows_to_read}, selected_cols_arr_{ixvcq__hlkck}.ctypes,
"""
    nkxxd__mcyil += f'        {len(lzen__zielq)},\n'
    nkxxd__mcyil += f'        nullable_cols_arr_{ixvcq__hlkck}.ctypes,\n'
    if len(lolas__zbs) > 0:
        nkxxd__mcyil += (
            f'        np.array({lolas__zbs}, dtype=np.int32).ctypes,\n')
        nkxxd__mcyil += (
            f'        np.array({dkfaw__qsw}, dtype=np.int32).ctypes,\n')
        nkxxd__mcyil += f'        {len(lolas__zbs)},\n'
    else:
        nkxxd__mcyil += f'        0, 0, 0,\n'
    if len(str_as_dict_cols) > 0:
        nkxxd__mcyil += f"""        np.array({str_as_dict_cols}, dtype=np.int32).ctypes, {len(str_as_dict_cols)},
"""
    else:
        nkxxd__mcyil += f'        0, 0,\n'
    nkxxd__mcyil += f'        total_rows_np.ctypes,\n'
    nkxxd__mcyil += f'        {input_file_name_col is not None},\n'
    nkxxd__mcyil += f'    )\n'
    nkxxd__mcyil += f'    check_and_propagate_cpp_exception()\n'
    zdwe__hdq = 'None'
    xxqrz__tying = index_column_type
    nktk__vixbc = TableType(tuple(out_types))
    if lbs__asd:
        nktk__vixbc = types.none
    if index_column_index is not None:
        kex__dtcw = ttaa__gvzou[index_column_index]
        zdwe__hdq = (
            f'info_to_array(info_from_table(out_table, {kex__dtcw}), index_arr_type)'
            )
    nkxxd__mcyil += f'    index_arr = {zdwe__hdq}\n'
    if lbs__asd:
        vvo__ouiec = None
    else:
        vvo__ouiec = []
        zacbi__antys = 0
        ztt__iycwo = col_indices[col_names.index(input_file_name_col)
            ] if input_file_name_col is not None else None
        for unzph__hzaes, aeff__ivgb in enumerate(col_indices):
            if zacbi__antys < len(type_usecol_offset
                ) and unzph__hzaes == type_usecol_offset[zacbi__antys]:
                arjt__dojiz = col_indices[unzph__hzaes]
                if ztt__iycwo and arjt__dojiz == ztt__iycwo:
                    vvo__ouiec.append(len(lzen__zielq) + len(dex__yrzq))
                elif arjt__dojiz in waupc__pwy:
                    kayw__inhfz = wjnsv__fxmna[unzph__hzaes]
                    vvo__ouiec.append(len(lzen__zielq) + vcu__ooh[kayw__inhfz])
                else:
                    vvo__ouiec.append(ttaa__gvzou[aeff__ivgb])
                zacbi__antys += 1
            else:
                vvo__ouiec.append(-1)
        vvo__ouiec = np.array(vvo__ouiec, dtype=np.int64)
    if lbs__asd:
        nkxxd__mcyil += '    T = None\n'
    else:
        nkxxd__mcyil += f"""    T = cpp_table_to_py_table(out_table, table_idx_{ixvcq__hlkck}, py_table_type_{ixvcq__hlkck})
"""
    nkxxd__mcyil += f'    delete_table(out_table)\n'
    nkxxd__mcyil += f'    total_rows = total_rows_np[0]\n'
    nkxxd__mcyil += f'    ev.finalize()\n'
    nkxxd__mcyil += f'    return (total_rows, T, index_arr)\n'
    lzw__izjuo = {}
    isczv__mgq = {f'py_table_type_{ixvcq__hlkck}': nktk__vixbc,
        f'table_idx_{ixvcq__hlkck}': vvo__ouiec,
        f'selected_cols_arr_{ixvcq__hlkck}': np.array(lzen__zielq, np.int32
        ), f'nullable_cols_arr_{ixvcq__hlkck}': np.array(wra__ogfx, np.
        int32), 'index_arr_type': xxqrz__tying, 'cpp_table_to_py_table':
        cpp_table_to_py_table, 'info_to_array': info_to_array,
        'info_from_table': info_from_table, 'delete_table': delete_table,
        'check_and_propagate_cpp_exception':
        check_and_propagate_cpp_exception, 'pq_read': _pq_read,
        'unicode_to_utf8': unicode_to_utf8, 'get_filters_pyobject':
        get_filters_pyobject, 'get_storage_options_pyobject':
        get_storage_options_pyobject, 'get_fname_pyobject':
        get_fname_pyobject, 'np': np, 'pd': pd, 'bodo': bodo}
    exec(nkxxd__mcyil, isczv__mgq, lzw__izjuo)
    wfzid__xoyya = lzw__izjuo['pq_reader_py']
    acx__ctf = numba.njit(wfzid__xoyya, no_cpython_wrapper=True)
    return acx__ctf


import pyarrow as pa
_pa_numba_typ_map = {pa.bool_(): types.bool_, pa.int8(): types.int8, pa.
    int16(): types.int16, pa.int32(): types.int32, pa.int64(): types.int64,
    pa.uint8(): types.uint8, pa.uint16(): types.uint16, pa.uint32(): types.
    uint32, pa.uint64(): types.uint64, pa.float32(): types.float32, pa.
    float64(): types.float64, pa.string(): string_type, pa.binary():
    bytes_type, pa.date32(): datetime_date_type, pa.date64(): types.
    NPDatetime('ns'), null(): string_type}


def get_arrow_timestamp_type(pa_ts_typ):
    rbh__ylsgs = 'ns', 'us', 'ms', 's'
    if pa_ts_typ.unit not in rbh__ylsgs:
        return types.Array(bodo.datetime64ns, 1, 'C'), False
    elif pa_ts_typ.tz is not None:
        uaody__atm = pa_ts_typ.to_pandas_dtype().tz
        aot__brkmw = bodo.libs.pd_datetime_arr_ext.get_pytz_type_info(
            uaody__atm)
        return bodo.DatetimeArrayType(aot__brkmw), True
    else:
        return types.Array(bodo.datetime64ns, 1, 'C'), True


def _get_numba_typ_from_pa_typ(pa_typ, is_index, nullable_from_metadata,
    category_info, str_as_dict=False):
    if isinstance(pa_typ.type, pa.ListType):
        amj__rcl, iycx__aep = _get_numba_typ_from_pa_typ(pa_typ.type.
            value_field, is_index, nullable_from_metadata, category_info)
        return ArrayItemArrayType(amj__rcl), iycx__aep
    if isinstance(pa_typ.type, pa.StructType):
        msokr__jax = []
        flsa__sgnm = []
        iycx__aep = True
        for jxh__mtdp in pa_typ.flatten():
            flsa__sgnm.append(jxh__mtdp.name.split('.')[-1])
            hpluv__ubo, plw__woure = _get_numba_typ_from_pa_typ(jxh__mtdp,
                is_index, nullable_from_metadata, category_info)
            msokr__jax.append(hpluv__ubo)
            iycx__aep = iycx__aep and plw__woure
        return StructArrayType(tuple(msokr__jax), tuple(flsa__sgnm)), iycx__aep
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
        ftk__sqtd = _pa_numba_typ_map[pa_typ.type.index_type]
        jwi__bghou = PDCategoricalDtype(category_info[pa_typ.name], bodo.
            string_type, pa_typ.type.ordered, int_type=ftk__sqtd)
        return CategoricalArrayType(jwi__bghou), True
    if isinstance(pa_typ.type, pa.lib.TimestampType):
        return get_arrow_timestamp_type(pa_typ.type)
    elif pa_typ.type in _pa_numba_typ_map:
        jhp__bfdo = _pa_numba_typ_map[pa_typ.type]
        iycx__aep = True
    else:
        raise BodoError('Arrow data type {} not supported yet'.format(
            pa_typ.type))
    if jhp__bfdo == datetime_date_type:
        return datetime_date_array_type, iycx__aep
    if jhp__bfdo == bytes_type:
        return binary_array_type, iycx__aep
    amj__rcl = string_array_type if jhp__bfdo == string_type else types.Array(
        jhp__bfdo, 1, 'C')
    if jhp__bfdo == types.bool_:
        amj__rcl = boolean_array
    if nullable_from_metadata is not None:
        bah__asm = nullable_from_metadata
    else:
        bah__asm = use_nullable_int_arr
    if bah__asm and not is_index and isinstance(jhp__bfdo, types.Integer
        ) and pa_typ.nullable:
        amj__rcl = IntegerArrayType(jhp__bfdo)
    return amj__rcl, iycx__aep


def get_parquet_dataset(fpath, get_row_counts=True, dnf_filters=None,
    expr_filters=None, storage_options=None, read_categories=False,
    is_parallel=False, tot_rows_to_read=None):
    if get_row_counts:
        ubv__jcae = tracing.Event('get_parquet_dataset')
    import time
    import pyarrow as pa
    import pyarrow.parquet as pq
    from mpi4py import MPI
    qup__mgm = MPI.COMM_WORLD
    if isinstance(fpath, list):
        bociz__qfik = urlparse(fpath[0])
        protocol = bociz__qfik.scheme
        zsezm__eam = bociz__qfik.netloc
        for unzph__hzaes in range(len(fpath)):
            zpc__zaxn = fpath[unzph__hzaes]
            aml__rpepi = urlparse(zpc__zaxn)
            if aml__rpepi.scheme != protocol:
                raise BodoError(
                    'All parquet files must use the same filesystem protocol')
            if aml__rpepi.netloc != zsezm__eam:
                raise BodoError(
                    'All parquet files must be in the same S3 bucket')
            fpath[unzph__hzaes] = zpc__zaxn.rstrip('/')
    else:
        bociz__qfik = urlparse(fpath)
        protocol = bociz__qfik.scheme
        fpath = fpath.rstrip('/')
    if protocol in {'gcs', 'gs'}:
        try:
            import gcsfs
        except ImportError as gwiq__ggyi:
            zcuvy__fcxlr = """Couldn't import gcsfs, which is required for Google cloud access. gcsfs can be installed by calling 'conda install -c conda-forge gcsfs'.
"""
            raise BodoError(zcuvy__fcxlr)
    if protocol == 'http':
        try:
            import fsspec
        except ImportError as gwiq__ggyi:
            zcuvy__fcxlr = """Couldn't import fsspec, which is required for http access. fsspec can be installed by calling 'conda install -c conda-forge fsspec'.
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
            apk__kzjly = gcsfs.GCSFileSystem(token=None)
            fs.append(apk__kzjly)
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
                prefix = f'{protocol}://{bociz__qfik.netloc}'
                path = path[len(prefix):]
            tdbb__vlzpj = fs.glob(path)
            if protocol == 's3':
                tdbb__vlzpj = [('s3://' + zpc__zaxn) for zpc__zaxn in
                    tdbb__vlzpj if not zpc__zaxn.startswith('s3://')]
            elif protocol in {'hdfs', 'abfs', 'abfss'}:
                tdbb__vlzpj = [(prefix + zpc__zaxn) for zpc__zaxn in
                    tdbb__vlzpj]
        except:
            raise BodoError(
                f'glob pattern expansion not supported for {protocol}')
        if len(tdbb__vlzpj) == 0:
            raise BodoError('No files found matching glob pattern')
        return tdbb__vlzpj
    qmtq__dzxhe = False
    if get_row_counts:
        kkp__tfpu = getfs(parallel=True)
        qmtq__dzxhe = bodo.parquet_validate_schema
    if bodo.get_rank() == 0:
        upuw__axydf = 1
        jbqq__til = os.cpu_count()
        if jbqq__til is not None and jbqq__til > 1:
            upuw__axydf = jbqq__til // 2
        try:
            if get_row_counts:
                mpct__flusm = tracing.Event('pq.ParquetDataset',
                    is_parallel=False)
                if tracing.is_tracing():
                    mpct__flusm.add_attribute('dnf_filter', str(dnf_filters))
            ubacq__sutyo = pa.io_thread_count()
            pa.set_io_thread_count(upuw__axydf)
            if '*' in fpath:
                fpath = glob(protocol, getfs(), fpath)
            if protocol == 's3':
                if isinstance(fpath, list):
                    get_legacy_fs().info(fpath[0])
                else:
                    get_legacy_fs().info(fpath)
            if protocol in {'hdfs', 'abfs', 'abfss'}:
                prefix = f'{protocol}://{bociz__qfik.netloc}'
                if isinstance(fpath, list):
                    nyq__tvs = [zpc__zaxn[len(prefix):] for zpc__zaxn in fpath]
                else:
                    nyq__tvs = fpath[len(prefix):]
            else:
                nyq__tvs = fpath
            jfvtu__ggnv = pq.ParquetDataset(nyq__tvs, filesystem=
                get_legacy_fs(), filters=None, use_legacy_dataset=True,
                validate_schema=False, metadata_nthreads=upuw__axydf)
            pa.set_io_thread_count(ubacq__sutyo)
            inj__rhda = bodo.io.pa_parquet.get_dataset_schema(jfvtu__ggnv)
            if dnf_filters:
                if get_row_counts:
                    mpct__flusm.add_attribute('num_pieces_before_filter',
                        len(jfvtu__ggnv.pieces))
                uvqz__fto = time.time()
                jfvtu__ggnv._filter(dnf_filters)
                if get_row_counts:
                    mpct__flusm.add_attribute('dnf_filter_time', time.time(
                        ) - uvqz__fto)
                    mpct__flusm.add_attribute('num_pieces_after_filter',
                        len(jfvtu__ggnv.pieces))
            if get_row_counts:
                mpct__flusm.finalize()
            jfvtu__ggnv._metadata.fs = None
        except Exception as dpmc__nobu:
            qup__mgm.bcast(dpmc__nobu)
            raise BodoError(
                f'error from pyarrow: {type(dpmc__nobu).__name__}: {str(dpmc__nobu)}\n'
                )
        if get_row_counts:
            ltpg__cyp = tracing.Event('bcast dataset')
        qup__mgm.bcast(jfvtu__ggnv)
        qup__mgm.bcast(inj__rhda)
    else:
        if get_row_counts:
            ltpg__cyp = tracing.Event('bcast dataset')
        jfvtu__ggnv = qup__mgm.bcast(None)
        if isinstance(jfvtu__ggnv, Exception):
            mpe__zhww = jfvtu__ggnv
            raise BodoError(
                f'error from pyarrow: {type(mpe__zhww).__name__}: {str(mpe__zhww)}\n'
                )
        inj__rhda = qup__mgm.bcast(None)
    if get_row_counts:
        gppb__ufsj = getfs()
    else:
        gppb__ufsj = get_legacy_fs()
    jfvtu__ggnv._metadata.fs = gppb__ufsj
    if get_row_counts:
        ltpg__cyp.finalize()
    jfvtu__ggnv._bodo_total_rows = 0
    if get_row_counts and tot_rows_to_read == 0:
        get_row_counts = qmtq__dzxhe = False
        for qnjr__tly in jfvtu__ggnv.pieces:
            qnjr__tly._bodo_num_rows = 0
    if get_row_counts or qmtq__dzxhe:
        if get_row_counts and tracing.is_tracing():
            asrw__ycny = tracing.Event('get_row_counts')
            asrw__ycny.add_attribute('g_num_pieces', len(jfvtu__ggnv.pieces))
            asrw__ycny.add_attribute('g_expr_filters', str(expr_filters))
        rmqfs__jzij = 0.0
        num_pieces = len(jfvtu__ggnv.pieces)
        start = get_start(num_pieces, bodo.get_size(), bodo.get_rank())
        lpesc__pumm = get_end(num_pieces, bodo.get_size(), bodo.get_rank())
        dri__oco = 0
        gnppr__gplrt = 0
        jwx__xozo = 0
        qpy__rhmz = True
        if expr_filters is not None:
            import random
            random.seed(37)
            tzl__xtyq = random.sample(jfvtu__ggnv.pieces, k=len(jfvtu__ggnv
                .pieces))
        else:
            tzl__xtyq = jfvtu__ggnv.pieces
        for qnjr__tly in tzl__xtyq:
            qnjr__tly._bodo_num_rows = 0
        fpaths = [qnjr__tly.path for qnjr__tly in tzl__xtyq[start:lpesc__pumm]]
        if protocol == 's3':
            zsezm__eam = bociz__qfik.netloc
            prefix = 's3://' + zsezm__eam + '/'
            fpaths = [zpc__zaxn[len(prefix):] for zpc__zaxn in fpaths]
            gppb__ufsj = get_s3_subtree_fs(zsezm__eam, region=getfs().
                region, storage_options=storage_options)
        else:
            gppb__ufsj = getfs()
        pa.set_io_thread_count(4)
        pa.set_cpu_count(4)
        rco__jflut = ds.dataset(fpaths, filesystem=gppb__ufsj, partitioning
            =ds.partitioning(flavor='hive'))
        for onenx__kjpf, hsk__nqleg in zip(tzl__xtyq[start:lpesc__pumm],
            rco__jflut.get_fragments()):
            uvqz__fto = time.time()
            tsfv__asyy = hsk__nqleg.scanner(schema=rco__jflut.schema,
                filter=expr_filters, use_threads=True).count_rows()
            rmqfs__jzij += time.time() - uvqz__fto
            onenx__kjpf._bodo_num_rows = tsfv__asyy
            dri__oco += tsfv__asyy
            gnppr__gplrt += hsk__nqleg.num_row_groups
            jwx__xozo += sum(yvb__sosa.total_byte_size for yvb__sosa in
                hsk__nqleg.row_groups)
            if qmtq__dzxhe:
                uesm__vuka = hsk__nqleg.metadata.schema.to_arrow_schema()
                if inj__rhda != uesm__vuka:
                    print('Schema in {!s} was different. \n{!s}\n\nvs\n\n{!s}'
                        .format(onenx__kjpf, uesm__vuka, inj__rhda))
                    qpy__rhmz = False
                    break
        if qmtq__dzxhe:
            qpy__rhmz = qup__mgm.allreduce(qpy__rhmz, op=MPI.LAND)
            if not qpy__rhmz:
                raise BodoError("Schema in parquet files don't match")
        if get_row_counts:
            jfvtu__ggnv._bodo_total_rows = qup__mgm.allreduce(dri__oco, op=
                MPI.SUM)
            xfve__atjng = qup__mgm.allreduce(gnppr__gplrt, op=MPI.SUM)
            hsmpt__swgc = qup__mgm.allreduce(jwx__xozo, op=MPI.SUM)
            dcuct__uyzd = np.array([qnjr__tly._bodo_num_rows for qnjr__tly in
                jfvtu__ggnv.pieces])
            dcuct__uyzd = qup__mgm.allreduce(dcuct__uyzd, op=MPI.SUM)
            for qnjr__tly, sxgo__ifhwn in zip(jfvtu__ggnv.pieces, dcuct__uyzd):
                qnjr__tly._bodo_num_rows = sxgo__ifhwn
            if is_parallel and bodo.get_rank(
                ) == 0 and xfve__atjng < bodo.get_size() and xfve__atjng != 0:
                warnings.warn(BodoWarning(
                    f"""Total number of row groups in parquet dataset {fpath} ({xfve__atjng}) is too small for effective IO parallelization.
For best performance the number of row groups should be greater than the number of workers ({bodo.get_size()})
"""
                    ))
            if xfve__atjng == 0:
                krjk__zzjg = 0
            else:
                krjk__zzjg = hsmpt__swgc // xfve__atjng
            if (bodo.get_rank() == 0 and hsmpt__swgc >= 20 * 1048576 and 
                krjk__zzjg < 1048576 and protocol in REMOTE_FILESYSTEMS):
                warnings.warn(BodoWarning(
                    f'Parquet average row group size is small ({krjk__zzjg} bytes) and can have negative impact on performance when reading from remote sources'
                    ))
            if tracing.is_tracing():
                asrw__ycny.add_attribute('g_total_num_row_groups', xfve__atjng)
                if expr_filters is not None:
                    asrw__ycny.add_attribute('total_scan_time', rmqfs__jzij)
                urisg__zypq = np.array([qnjr__tly._bodo_num_rows for
                    qnjr__tly in jfvtu__ggnv.pieces])
                prox__ossr = np.percentile(urisg__zypq, [25, 50, 75])
                asrw__ycny.add_attribute('g_row_counts_min', urisg__zypq.min())
                asrw__ycny.add_attribute('g_row_counts_Q1', prox__ossr[0])
                asrw__ycny.add_attribute('g_row_counts_median', prox__ossr[1])
                asrw__ycny.add_attribute('g_row_counts_Q3', prox__ossr[2])
                asrw__ycny.add_attribute('g_row_counts_max', urisg__zypq.max())
                asrw__ycny.add_attribute('g_row_counts_mean', urisg__zypq.
                    mean())
                asrw__ycny.add_attribute('g_row_counts_std', urisg__zypq.std())
                asrw__ycny.add_attribute('g_row_counts_sum', urisg__zypq.sum())
                asrw__ycny.finalize()
    jfvtu__ggnv._prefix = ''
    if protocol in {'hdfs', 'abfs', 'abfss'}:
        prefix = f'{protocol}://{bociz__qfik.netloc}'
        if len(jfvtu__ggnv.pieces) > 0:
            onenx__kjpf = jfvtu__ggnv.pieces[0]
            if not onenx__kjpf.path.startswith(prefix):
                jfvtu__ggnv._prefix = prefix
    if read_categories:
        _add_categories_to_pq_dataset(jfvtu__ggnv)
    if get_row_counts:
        ubv__jcae.finalize()
    return jfvtu__ggnv


def get_scanner_batches(fpaths, expr_filters, selected_fields,
    avg_num_pieces, is_parallel, storage_options, region, prefix,
    str_as_dict_cols, start_offset, rows_to_read):
    import pyarrow as pa
    jbqq__til = os.cpu_count()
    if jbqq__til is None or jbqq__til == 0:
        jbqq__til = 2
    oxavr__ojz = min(4, jbqq__til)
    mtui__nbgdu = min(16, jbqq__til)
    if is_parallel and len(fpaths) > mtui__nbgdu and len(fpaths
        ) / avg_num_pieces >= 2.0:
        pa.set_io_thread_count(mtui__nbgdu)
        pa.set_cpu_count(mtui__nbgdu)
    else:
        pa.set_io_thread_count(oxavr__ojz)
        pa.set_cpu_count(oxavr__ojz)
    if fpaths[0].startswith('s3://'):
        zsezm__eam = urlparse(fpaths[0]).netloc
        prefix = 's3://' + zsezm__eam + '/'
        fpaths = [zpc__zaxn[len(prefix):] for zpc__zaxn in fpaths]
        gppb__ufsj = get_s3_subtree_fs(zsezm__eam, region=region,
            storage_options=storage_options)
    elif prefix and prefix.startswith(('hdfs', 'abfs', 'abfss')):
        gppb__ufsj = get_hdfs_fs(prefix + fpaths[0])
    elif fpaths[0].startswith(('gcs', 'gs')):
        import gcsfs
        gppb__ufsj = gcsfs.GCSFileSystem(token=None)
    else:
        gppb__ufsj = None
    gzl__zbx = ds.ParquetFileFormat(dictionary_columns=str_as_dict_cols)
    jfvtu__ggnv = ds.dataset(fpaths, filesystem=gppb__ufsj, partitioning=ds
        .partitioning(flavor='hive'), format=gzl__zbx)
    col_names = jfvtu__ggnv.schema.names
    yev__vmjeo = [col_names[gjppt__lqm] for gjppt__lqm in selected_fields]
    zne__qyl = len(fpaths) <= 3 or start_offset > 0 and len(fpaths) <= 10
    if zne__qyl and expr_filters is None:
        twsi__ftzf = []
        quvlq__vbgr = 0
        luaj__vco = 0
        for hsk__nqleg in jfvtu__ggnv.get_fragments():
            gfmlr__xialn = []
            for yvb__sosa in hsk__nqleg.row_groups:
                ahx__raw = yvb__sosa.num_rows
                if start_offset < quvlq__vbgr + ahx__raw:
                    if luaj__vco == 0:
                        coh__jnr = start_offset - quvlq__vbgr
                        pclig__hhl = min(ahx__raw - coh__jnr, rows_to_read)
                    else:
                        pclig__hhl = min(ahx__raw, rows_to_read - luaj__vco)
                    luaj__vco += pclig__hhl
                    gfmlr__xialn.append(yvb__sosa.id)
                quvlq__vbgr += ahx__raw
                if luaj__vco == rows_to_read:
                    break
            twsi__ftzf.append(hsk__nqleg.subset(row_group_ids=gfmlr__xialn))
            if luaj__vco == rows_to_read:
                break
        jfvtu__ggnv = ds.FileSystemDataset(twsi__ftzf, jfvtu__ggnv.schema,
            gzl__zbx, filesystem=jfvtu__ggnv.filesystem)
        start_offset = coh__jnr
    dxjrx__yqf = jfvtu__ggnv.scanner(columns=yev__vmjeo, filter=
        expr_filters, use_threads=True).to_reader()
    return jfvtu__ggnv, dxjrx__yqf, start_offset


def _add_categories_to_pq_dataset(pq_dataset):
    import pyarrow as pa
    from mpi4py import MPI
    if len(pq_dataset.pieces) < 1:
        raise BodoError(
            'No pieces found in Parquet dataset. Cannot get read categorical values'
            )
    pa_schema = pq_dataset.schema.to_arrow_schema()
    vesjz__umge = [c for c in pa_schema.names if isinstance(pa_schema.field
        (c).type, pa.DictionaryType)]
    if len(vesjz__umge) == 0:
        pq_dataset._category_info = {}
        return
    qup__mgm = MPI.COMM_WORLD
    if bodo.get_rank() == 0:
        try:
            tixmw__ccwx = pq_dataset.pieces[0].open()
            yvb__sosa = tixmw__ccwx.read_row_group(0, vesjz__umge)
            category_info = {c: tuple(yvb__sosa.column(c).chunk(0).
                dictionary.to_pylist()) for c in vesjz__umge}
            del tixmw__ccwx, yvb__sosa
        except Exception as dpmc__nobu:
            qup__mgm.bcast(dpmc__nobu)
            raise dpmc__nobu
        qup__mgm.bcast(category_info)
    else:
        category_info = qup__mgm.bcast(None)
        if isinstance(category_info, Exception):
            mpe__zhww = category_info
            raise mpe__zhww
    pq_dataset._category_info = category_info


def get_pandas_metadata(schema, num_pieces):
    ohpg__saw = None
    nullable_from_metadata = defaultdict(lambda : None)
    xdplo__eyhr = b'pandas'
    if schema.metadata is not None and xdplo__eyhr in schema.metadata:
        import json
        sctxe__hdba = json.loads(schema.metadata[xdplo__eyhr].decode('utf8'))
        wshbg__quugo = len(sctxe__hdba['index_columns'])
        if wshbg__quugo > 1:
            raise BodoError('read_parquet: MultiIndex not supported yet')
        ohpg__saw = sctxe__hdba['index_columns'][0] if wshbg__quugo else None
        if not isinstance(ohpg__saw, str) and (not isinstance(ohpg__saw,
            dict) or num_pieces != 1):
            ohpg__saw = None
        for zfknq__omla in sctxe__hdba['columns']:
            jjh__lxr = zfknq__omla['name']
            if zfknq__omla['pandas_type'].startswith('int'
                ) and jjh__lxr is not None:
                if zfknq__omla['numpy_type'].startswith('Int'):
                    nullable_from_metadata[jjh__lxr] = True
                else:
                    nullable_from_metadata[jjh__lxr] = False
    return ohpg__saw, nullable_from_metadata


def determine_str_as_dict_columns(pq_dataset, pa_schema):
    from mpi4py import MPI
    qup__mgm = MPI.COMM_WORLD
    kavpt__dokg = []
    for jjh__lxr in pa_schema.names:
        jxh__mtdp = pa_schema.field(jjh__lxr)
        if jxh__mtdp.type == pa.string():
            kavpt__dokg.append((jjh__lxr, pa_schema.get_field_index(jjh__lxr)))
    if len(kavpt__dokg) == 0:
        return set()
    if len(pq_dataset.pieces) > bodo.get_size():
        import random
        random.seed(37)
        tzl__xtyq = random.sample(pq_dataset.pieces, bodo.get_size())
    else:
        tzl__xtyq = pq_dataset.pieces
    pexd__sat = np.zeros(len(kavpt__dokg), dtype=np.int64)
    ebhm__lna = np.zeros(len(kavpt__dokg), dtype=np.int64)
    if bodo.get_rank() < len(tzl__xtyq):
        onenx__kjpf = tzl__xtyq[bodo.get_rank()]
        fou__trfz = onenx__kjpf.get_metadata()
        for unzph__hzaes in range(fou__trfz.num_row_groups):
            for zacbi__antys, (kkp__tfpu, dlxee__ovjmd) in enumerate(
                kavpt__dokg):
                pexd__sat[zacbi__antys] += fou__trfz.row_group(unzph__hzaes
                    ).column(dlxee__ovjmd).total_uncompressed_size
        iphxu__rpp = fou__trfz.num_rows
    else:
        iphxu__rpp = 0
    teknv__yrlln = qup__mgm.allreduce(iphxu__rpp, op=MPI.SUM)
    if teknv__yrlln == 0:
        return set()
    qup__mgm.Allreduce(pexd__sat, ebhm__lna, op=MPI.SUM)
    dpodq__leip = ebhm__lna / teknv__yrlln
    str_as_dict = set()
    for unzph__hzaes, qrpuk__yake in enumerate(dpodq__leip):
        if qrpuk__yake < READ_STR_AS_DICT_THRESHOLD:
            jjh__lxr = kavpt__dokg[unzph__hzaes][0]
            str_as_dict.add(jjh__lxr)
    return str_as_dict


def parquet_file_schema(file_name, selected_columns, storage_options=None,
    input_file_name_col=None):
    col_names = []
    lcjy__sipuz = []
    pq_dataset = get_parquet_dataset(file_name, get_row_counts=False,
        storage_options=storage_options, read_categories=True)
    partition_names = [] if pq_dataset.partitions is None else [pq_dataset.
        partitions.levels[unzph__hzaes].name for unzph__hzaes in range(len(
        pq_dataset.partitions.partition_names))]
    pa_schema = pq_dataset.schema.to_arrow_schema()
    num_pieces = len(pq_dataset.pieces)
    str_as_dict = determine_str_as_dict_columns(pq_dataset, pa_schema)
    col_names = pa_schema.names
    ohpg__saw, nullable_from_metadata = get_pandas_metadata(pa_schema,
        num_pieces)
    fxcp__tbc = []
    wio__ujjq = []
    wxtbp__sgx = []
    for unzph__hzaes, c in enumerate(col_names):
        jxh__mtdp = pa_schema.field(c)
        jhp__bfdo, iycx__aep = _get_numba_typ_from_pa_typ(jxh__mtdp, c ==
            ohpg__saw, nullable_from_metadata[c], pq_dataset._category_info,
            str_as_dict=c in str_as_dict)
        fxcp__tbc.append(jhp__bfdo)
        wio__ujjq.append(iycx__aep)
        wxtbp__sgx.append(jxh__mtdp.type)
    if partition_names:
        col_names += partition_names
        fxcp__tbc += [_get_partition_cat_dtype(pq_dataset.partitions.levels
            [unzph__hzaes]) for unzph__hzaes in range(len(partition_names))]
        wio__ujjq.extend([True] * len(partition_names))
        wxtbp__sgx.extend([None] * len(partition_names))
    if input_file_name_col is not None:
        col_names += [input_file_name_col]
        fxcp__tbc += [dict_str_arr_type]
        wio__ujjq.append(True)
        wxtbp__sgx.append(None)
    pdpqw__vkc = {c: unzph__hzaes for unzph__hzaes, c in enumerate(col_names)}
    if selected_columns is None:
        selected_columns = col_names
    for c in selected_columns:
        if c not in pdpqw__vkc:
            raise BodoError(f'Selected column {c} not in Parquet file schema')
    if ohpg__saw and not isinstance(ohpg__saw, dict
        ) and ohpg__saw not in selected_columns:
        selected_columns.append(ohpg__saw)
    col_names = selected_columns
    col_indices = []
    lcjy__sipuz = []
    iwvch__uvit = []
    joqq__rdev = []
    for unzph__hzaes, c in enumerate(col_names):
        arjt__dojiz = pdpqw__vkc[c]
        col_indices.append(arjt__dojiz)
        lcjy__sipuz.append(fxcp__tbc[arjt__dojiz])
        if not wio__ujjq[arjt__dojiz]:
            iwvch__uvit.append(unzph__hzaes)
            joqq__rdev.append(wxtbp__sgx[arjt__dojiz])
    return (col_names, lcjy__sipuz, ohpg__saw, col_indices, partition_names,
        iwvch__uvit, joqq__rdev)


def _get_partition_cat_dtype(part_set):
    ind__apnaz = part_set.dictionary.to_pandas()
    plpo__gie = bodo.typeof(ind__apnaz).dtype
    jwi__bghou = PDCategoricalDtype(tuple(ind__apnaz), plpo__gie, False)
    return CategoricalArrayType(jwi__bghou)


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
        ysr__klkh = lir.FunctionType(lir.VoidType(), [lir.IntType(8).
            as_pointer(), lir.IntType(8).as_pointer(), lir.IntType(8).
            as_pointer(), lir.IntType(8).as_pointer(), lir.IntType(1), lir.
            IntType(8).as_pointer(), lir.IntType(8).as_pointer(), lir.
            IntType(1), lir.IntType(1), lir.IntType(32), lir.IntType(32),
            lir.IntType(32), lir.IntType(8).as_pointer(), lir.IntType(8).
            as_pointer()])
        auc__gkgnw = cgutils.get_or_insert_function(builder.module,
            ysr__klkh, name='pq_write')
        builder.call(auc__gkgnw, args)
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
        ysr__klkh = lir.FunctionType(lir.VoidType(), [lir.IntType(8).
            as_pointer(), lir.IntType(8).as_pointer(), lir.IntType(8).
            as_pointer(), lir.IntType(8).as_pointer(), lir.IntType(8).
            as_pointer(), lir.IntType(8).as_pointer(), lir.IntType(32), lir
            .IntType(8).as_pointer(), lir.IntType(1), lir.IntType(8).
            as_pointer()])
        auc__gkgnw = cgutils.get_or_insert_function(builder.module,
            ysr__klkh, name='pq_write_partitioned')
        builder.call(auc__gkgnw, args)
        bodo.utils.utils.inlined_check_and_propagate_cpp_exception(context,
            builder)
    return types.void(types.voidptr, data_table_t, col_names_t,
        col_names_no_partitions_t, cat_table_t, types.voidptr, types.int32,
        types.voidptr, types.boolean, types.voidptr), codegen
