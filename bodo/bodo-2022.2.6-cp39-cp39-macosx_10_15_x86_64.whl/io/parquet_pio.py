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
        except OSError as ueaax__nrzn:
            if 'non-file path' in str(ueaax__nrzn):
                raise FileNotFoundError(str(ueaax__nrzn))
            raise


class ParquetHandler:

    def __init__(self, func_ir, typingctx, args, _locals):
        self.func_ir = func_ir
        self.typingctx = typingctx
        self.args = args
        self.locals = _locals

    def gen_parquet_read(self, file_name, lhs, columns, storage_options=
        None, input_file_name_col=None):
        btn__yaw = lhs.scope
        ziwh__mta = lhs.loc
        zmvs__vzmb = None
        if lhs.name in self.locals:
            zmvs__vzmb = self.locals[lhs.name]
            self.locals.pop(lhs.name)
        itcz__ulq = {}
        if lhs.name + ':convert' in self.locals:
            itcz__ulq = self.locals[lhs.name + ':convert']
            self.locals.pop(lhs.name + ':convert')
        if zmvs__vzmb is None:
            anq__phvy = (
                'Parquet schema not available. Either path argument should be constant for Bodo to look at the file at compile time or schema should be provided. For more information, see: https://docs.bodo.ai/latest/source/programming_with_bodo/file_io.html#non-constant-filepaths'
                )
            kkrx__ucx = get_const_value(file_name, self.func_ir, anq__phvy,
                arg_types=self.args, file_info=ParquetFileInfo(columns,
                storage_options=storage_options, input_file_name_col=
                input_file_name_col))
            yfd__xcyqv = False
            gsl__hdsva = guard(get_definition, self.func_ir, file_name)
            if isinstance(gsl__hdsva, ir.Arg):
                typ = self.args[gsl__hdsva.index]
                if isinstance(typ, types.FilenameType):
                    (col_names, qhllz__galui, nde__ate, col_indices,
                        partition_names, ejwr__pqj, gox__xbq) = typ.schema
                    yfd__xcyqv = True
            if not yfd__xcyqv:
                (col_names, qhllz__galui, nde__ate, col_indices,
                    partition_names, ejwr__pqj, gox__xbq) = (
                    parquet_file_schema(kkrx__ucx, columns, storage_options
                    =storage_options, input_file_name_col=input_file_name_col))
        else:
            otw__htweg = list(zmvs__vzmb.keys())
            taub__cuov = {c: gjq__opzsk for gjq__opzsk, c in enumerate(
                otw__htweg)}
            sbzhp__xcn = [eqsr__qav for eqsr__qav in zmvs__vzmb.values()]
            nde__ate = 'index' if 'index' in taub__cuov else None
            if columns is None:
                selected_columns = otw__htweg
            else:
                selected_columns = columns
            col_indices = [taub__cuov[c] for c in selected_columns]
            qhllz__galui = [sbzhp__xcn[taub__cuov[c]] for c in selected_columns
                ]
            col_names = selected_columns
            nde__ate = nde__ate if nde__ate in col_names else None
            partition_names = []
            ejwr__pqj = []
            gox__xbq = []
        pgrm__tlue = None if isinstance(nde__ate, dict
            ) or nde__ate is None else nde__ate
        index_column_index = None
        index_column_type = types.none
        if pgrm__tlue:
            wxcp__qfse = col_names.index(pgrm__tlue)
            index_column_index = col_indices.pop(wxcp__qfse)
            index_column_type = qhllz__galui.pop(wxcp__qfse)
            col_names.pop(wxcp__qfse)
        for gjq__opzsk, c in enumerate(col_names):
            if c in itcz__ulq:
                qhllz__galui[gjq__opzsk] = itcz__ulq[c]
        gpxzu__omw = [ir.Var(btn__yaw, mk_unique_var('pq_table'), ziwh__mta
            ), ir.Var(btn__yaw, mk_unique_var('pq_index'), ziwh__mta)]
        uql__rzej = [bodo.ir.parquet_ext.ParquetReader(file_name, lhs.name,
            col_names, col_indices, qhllz__galui, gpxzu__omw, ziwh__mta,
            partition_names, storage_options, index_column_index,
            index_column_type, input_file_name_col, ejwr__pqj, gox__xbq)]
        return (col_names, gpxzu__omw, nde__ate, uql__rzej, qhllz__galui,
            index_column_type)


def determine_filter_cast(pq_node, typemap, filter_val, orig_colname_map):
    jszfz__abjwc = filter_val[0]
    mywa__rsl = pq_node.original_out_types[orig_colname_map[jszfz__abjwc]]
    gjll__fnoc = bodo.utils.typing.element_type(mywa__rsl)
    if jszfz__abjwc in pq_node.partition_names:
        if gjll__fnoc == types.unicode_type:
            ypsps__kksac = '.cast(pyarrow.string(), safe=False)'
        elif isinstance(gjll__fnoc, types.Integer):
            ypsps__kksac = f'.cast(pyarrow.{gjll__fnoc.name}(), safe=False)'
        else:
            ypsps__kksac = ''
    else:
        ypsps__kksac = ''
    mtw__wxjx = typemap[filter_val[2].name]
    if isinstance(mtw__wxjx, (types.List, types.Set)):
        zadpm__xycah = mtw__wxjx.dtype
    else:
        zadpm__xycah = mtw__wxjx
    if not bodo.utils.typing.is_common_scalar_dtype([gjll__fnoc, zadpm__xycah]
        ):
        if not bodo.utils.typing.is_safe_arrow_cast(gjll__fnoc, zadpm__xycah):
            raise BodoError(
                f'Unsupported Arrow cast from {gjll__fnoc} to {zadpm__xycah} in filter pushdown. Please try a comparison that avoids casting the column.'
                )
        if gjll__fnoc == types.unicode_type:
            return ".cast(pyarrow.timestamp('ns'), safe=False)", ''
        elif gjll__fnoc in (bodo.datetime64ns, bodo.pd_timestamp_type):
            if isinstance(mtw__wxjx, (types.List, types.Set)):
                ebnx__oblp = 'list' if isinstance(mtw__wxjx, types.List
                    ) else 'tuple'
                raise BodoError(
                    f'Cannot cast {ebnx__oblp} values with isin filter pushdown.'
                    )
            return ypsps__kksac, ".cast(pyarrow.timestamp('ns'), safe=False)"
    return ypsps__kksac, ''


def pq_distributed_run(pq_node, array_dists, typemap, calltypes, typingctx,
    targetctx, meta_head_only_info=None):
    yhg__mjwvw = len(pq_node.out_vars)
    extra_args = ''
    dnf_filter_str = 'None'
    expr_filter_str = 'None'
    cmrpn__gbvle, fgwe__eybo = bodo.ir.connector.generate_filter_map(pq_node
        .filters)
    if pq_node.filters:
        tnpf__gff = []
        gjx__itlp = []
        hwz__iywpa = False
        rhx__evies = None
        orig_colname_map = {c: gjq__opzsk for gjq__opzsk, c in enumerate(
            pq_node.original_df_colnames)}
        for ccrgv__yxczo in pq_node.filters:
            aywek__pss = []
            xpm__xkjix = []
            jouuc__wrscz = set()
            for tcoe__div in ccrgv__yxczo:
                if isinstance(tcoe__div[2], ir.Var):
                    yfm__ghr, swf__bwya = determine_filter_cast(pq_node,
                        typemap, tcoe__div, orig_colname_map)
                    if tcoe__div[1] == 'in':
                        xpm__xkjix.append(
                            f"(ds.field('{tcoe__div[0]}').isin({cmrpn__gbvle[tcoe__div[2].name]}))"
                            )
                    else:
                        xpm__xkjix.append(
                            f"(ds.field('{tcoe__div[0]}'){yfm__ghr} {tcoe__div[1]} ds.scalar({cmrpn__gbvle[tcoe__div[2].name]}){swf__bwya})"
                            )
                else:
                    assert tcoe__div[2
                        ] == 'NULL', 'unsupport constant used in filter pushdown'
                    if tcoe__div[1] == 'is not':
                        prefix = '~'
                    else:
                        prefix = ''
                    xpm__xkjix.append(
                        f"({prefix}ds.field('{tcoe__div[0]}').is_null())")
                if tcoe__div[0] in pq_node.partition_names and isinstance(
                    tcoe__div[2], ir.Var):
                    btsyc__jlodj = (
                        f"('{tcoe__div[0]}', '{tcoe__div[1]}', {cmrpn__gbvle[tcoe__div[2].name]})"
                        )
                    aywek__pss.append(btsyc__jlodj)
                    jouuc__wrscz.add(btsyc__jlodj)
                else:
                    hwz__iywpa = True
            if rhx__evies is None:
                rhx__evies = jouuc__wrscz
            else:
                rhx__evies.intersection_update(jouuc__wrscz)
            iofz__yoz = ', '.join(aywek__pss)
            ifu__uccp = ' & '.join(xpm__xkjix)
            if iofz__yoz:
                tnpf__gff.append(f'[{iofz__yoz}]')
            gjx__itlp.append(f'({ifu__uccp})')
        tyrxu__gxzu = ', '.join(tnpf__gff)
        bkf__acvj = ' | '.join(gjx__itlp)
        if hwz__iywpa:
            if rhx__evies:
                rvh__bnrix = sorted(rhx__evies)
                dnf_filter_str = f"[[{', '.join(rvh__bnrix)}]]"
        elif tyrxu__gxzu:
            dnf_filter_str = f'[{tyrxu__gxzu}]'
        expr_filter_str = f'({bkf__acvj})'
        extra_args = ', '.join(cmrpn__gbvle.values())
    jfs__csaop = ', '.join(f'out{gjq__opzsk}' for gjq__opzsk in range(
        yhg__mjwvw))
    uma__tqhg = f'def pq_impl(fname, {extra_args}):\n'
    uma__tqhg += (
        f'    (total_rows, {jfs__csaop},) = _pq_reader_py(fname, {extra_args})\n'
        )
    xnr__faif = {}
    exec(uma__tqhg, {}, xnr__faif)
    ymfc__gxzr = xnr__faif['pq_impl']
    if bodo.user_logging.get_verbose_level() >= 1:
        xpdir__yxxn = pq_node.loc.strformat()
        zmtlz__kamue = []
        clhjg__yxni = []
        for gjq__opzsk in pq_node.type_usecol_offset:
            jszfz__abjwc = pq_node.df_colnames[gjq__opzsk]
            zmtlz__kamue.append(jszfz__abjwc)
            if isinstance(pq_node.out_types[gjq__opzsk], bodo.libs.
                dict_arr_ext.DictionaryArrayType):
                clhjg__yxni.append(jszfz__abjwc)
        zrvlv__snl = (
            'Finish column pruning on read_parquet node:\n%s\nColumns loaded %s\n'
            )
        bodo.user_logging.log_message('Column Pruning', zrvlv__snl,
            xpdir__yxxn, zmtlz__kamue)
        if clhjg__yxni:
            aijkv__xdp = """Finished optimized encoding on read_parquet node:
%s
Columns %s using dictionary encoding to reduce memory usage.
"""
            bodo.user_logging.log_message('Dictionary Encoding', aijkv__xdp,
                xpdir__yxxn, clhjg__yxni)
    parallel = False
    if array_dists is not None:
        mzxg__gzdsn = pq_node.out_vars[0].name
        parallel = array_dists[mzxg__gzdsn] in (distributed_pass.
            Distribution.OneD, distributed_pass.Distribution.OneD_Var)
        zvxvw__acb = pq_node.out_vars[1].name
        assert typemap[zvxvw__acb
            ] == types.none or not parallel or array_dists[zvxvw__acb] in (
            distributed_pass.Distribution.OneD, distributed_pass.
            Distribution.OneD_Var
            ), 'pq data/index parallelization does not match'
    if pq_node.unsupported_columns:
        afoz__gszjx = set(pq_node.type_usecol_offset)
        rhoh__ekjax = set(pq_node.unsupported_columns)
        ded__pbf = afoz__gszjx & rhoh__ekjax
        if ded__pbf:
            anjnd__qxw = sorted(ded__pbf)
            pcuhk__udp = [
                f'pandas.read_parquet(): 1 or more columns found with Arrow types that are not supported in Bodo and could not be eliminated. '
                 +
                "Please manually remove these columns from your read_parquet with the 'columns' argument. If these "
                 +
                'columns are needed, you will need to modify your dataset to use a supported type.'
                , 'Unsupported Columns:']
            dniy__lrfmp = 0
            for zwqty__eqws in anjnd__qxw:
                while pq_node.unsupported_columns[dniy__lrfmp] != zwqty__eqws:
                    dniy__lrfmp += 1
                pcuhk__udp.append(
                    f"Column '{pq_node.df_colnames[zwqty__eqws]}' with unsupported arrow type {pq_node.unsupported_arrow_types[dniy__lrfmp]}"
                    )
                dniy__lrfmp += 1
            kaxy__bef = '\n'.join(pcuhk__udp)
            raise BodoError(kaxy__bef, loc=pq_node.loc)
    axn__xpdc = _gen_pq_reader_py(pq_node.df_colnames, pq_node.col_indices,
        pq_node.type_usecol_offset, pq_node.out_types, pq_node.
        storage_options, pq_node.partition_names, dnf_filter_str,
        expr_filter_str, extra_args, parallel, meta_head_only_info, pq_node
        .index_column_index, pq_node.index_column_type, pq_node.
        input_file_name_col)
    jirzu__hnp = typemap[pq_node.file_name.name]
    brt__gdc = (jirzu__hnp,) + tuple(typemap[tcoe__div.name] for tcoe__div in
        fgwe__eybo)
    gym__bew = compile_to_numba_ir(ymfc__gxzr, {'_pq_reader_py': axn__xpdc},
        typingctx=typingctx, targetctx=targetctx, arg_typs=brt__gdc,
        typemap=typemap, calltypes=calltypes).blocks.popitem()[1]
    replace_arg_nodes(gym__bew, [pq_node.file_name] + fgwe__eybo)
    uql__rzej = gym__bew.body[:-3]
    if meta_head_only_info:
        uql__rzej[-1 - yhg__mjwvw].target = meta_head_only_info[1]
    uql__rzej[-2].target = pq_node.out_vars[0]
    uql__rzej[-1].target = pq_node.out_vars[1]
    return uql__rzej


distributed_pass.distributed_run_extensions[bodo.ir.parquet_ext.ParquetReader
    ] = pq_distributed_run


def get_filters_pyobject(dnf_filter_str, expr_filter_str, vars):
    pass


@overload(get_filters_pyobject, no_unliteral=True)
def overload_get_filters_pyobject(dnf_filter_str, expr_filter_str, var_tup):
    gqwt__daul = get_overload_const_str(dnf_filter_str)
    jqzdl__wfrey = get_overload_const_str(expr_filter_str)
    emc__zmeg = ', '.join(f'f{gjq__opzsk}' for gjq__opzsk in range(len(
        var_tup)))
    uma__tqhg = 'def impl(dnf_filter_str, expr_filter_str, var_tup):\n'
    if len(var_tup):
        uma__tqhg += f'  {emc__zmeg}, = var_tup\n'
    uma__tqhg += """  with numba.objmode(dnf_filters_py='parquet_predicate_type', expr_filters_py='parquet_predicate_type'):
"""
    uma__tqhg += f'    dnf_filters_py = {gqwt__daul}\n'
    uma__tqhg += f'    expr_filters_py = {jqzdl__wfrey}\n'
    uma__tqhg += '  return (dnf_filters_py, expr_filters_py)\n'
    xnr__faif = {}
    exec(uma__tqhg, globals(), xnr__faif)
    return xnr__faif['impl']


@numba.njit
def get_fname_pyobject(fname):
    with numba.objmode(fname_py='read_parquet_fpath_type'):
        fname_py = fname
    return fname_py


def get_storage_options_pyobject(storage_options):
    pass


@overload(get_storage_options_pyobject, no_unliteral=True)
def overload_get_storage_options_pyobject(storage_options):
    tza__qyd = get_overload_constant_dict(storage_options)
    uma__tqhg = 'def impl(storage_options):\n'
    uma__tqhg += (
        "  with numba.objmode(storage_options_py='storage_options_dict_type'):\n"
        )
    uma__tqhg += f'    storage_options_py = {str(tza__qyd)}\n'
    uma__tqhg += '  return storage_options_py\n'
    xnr__faif = {}
    exec(uma__tqhg, globals(), xnr__faif)
    return xnr__faif['impl']


def _gen_pq_reader_py(col_names, col_indices, type_usecol_offset, out_types,
    storage_options, partition_names, dnf_filter_str, expr_filter_str,
    extra_args, is_parallel, meta_head_only_info, index_column_index,
    index_column_type, input_file_name_col):
    gwemz__pkzyf = next_label()
    edh__tgu = ',' if extra_args else ''
    uma__tqhg = f'def pq_reader_py(fname,{extra_args}):\n'
    uma__tqhg += (
        f"    ev = bodo.utils.tracing.Event('read_parquet', {is_parallel})\n")
    uma__tqhg += f"    ev.add_attribute('fname', fname)\n"
    uma__tqhg += f"""    bucket_region = bodo.io.fs_io.get_s3_bucket_region_njit(fname, parallel={is_parallel})
"""
    uma__tqhg += f"""    dnf_filters, expr_filters = get_filters_pyobject("{dnf_filter_str}", "{expr_filter_str}", ({extra_args}{edh__tgu}))
"""
    uma__tqhg += '    fname_py = get_fname_pyobject(fname)\n'
    storage_options['bodo_dummy'] = 'dummy'
    uma__tqhg += (
        f'    storage_options_py = get_storage_options_pyobject({str(storage_options)})\n'
        )
    tot_rows_to_read = -1
    if meta_head_only_info and meta_head_only_info[0] is not None:
        tot_rows_to_read = meta_head_only_info[0]
    tim__ful = not type_usecol_offset
    nvx__xqqd = [sanitize_varname(c) for c in col_names]
    partition_names = [sanitize_varname(c) for c in partition_names]
    input_file_name_col = sanitize_varname(input_file_name_col
        ) if input_file_name_col is not None and col_names.index(
        input_file_name_col) in type_usecol_offset else None
    pugoa__wwm = {c: gjq__opzsk for gjq__opzsk, c in enumerate(col_indices)}
    irgwy__dcrvq = {c: gjq__opzsk for gjq__opzsk, c in enumerate(nvx__xqqd)}
    iaj__ljd = []
    egn__oyafi = set()
    drbm__wrvyl = partition_names + [input_file_name_col]
    for gjq__opzsk in type_usecol_offset:
        if nvx__xqqd[gjq__opzsk] not in drbm__wrvyl:
            iaj__ljd.append(col_indices[gjq__opzsk])
        elif not input_file_name_col or nvx__xqqd[gjq__opzsk
            ] != input_file_name_col:
            egn__oyafi.add(col_indices[gjq__opzsk])
    if index_column_index is not None:
        iaj__ljd.append(index_column_index)
    iaj__ljd = sorted(iaj__ljd)
    bcp__zgm = {c: gjq__opzsk for gjq__opzsk, c in enumerate(iaj__ljd)}

    def is_nullable(typ):
        return bodo.utils.utils.is_array_typ(typ, False) and (not
            isinstance(typ, types.Array) and not isinstance(typ, bodo.
            DatetimeArrayType))
    dkky__jgn = [(int(is_nullable(out_types[pugoa__wwm[ufqf__imy]])) if 
        ufqf__imy != index_column_index else int(is_nullable(
        index_column_type))) for ufqf__imy in iaj__ljd]
    str_as_dict_cols = []
    for ufqf__imy in iaj__ljd:
        if ufqf__imy == index_column_index:
            eqsr__qav = index_column_type
        else:
            eqsr__qav = out_types[pugoa__wwm[ufqf__imy]]
        if eqsr__qav == dict_str_arr_type:
            str_as_dict_cols.append(ufqf__imy)
    oltoa__upi = []
    hryy__vcylp = {}
    uig__nijzf = []
    frlh__ntf = []
    for gjq__opzsk, bxsz__fchj in enumerate(partition_names):
        try:
            kfanv__ngyj = irgwy__dcrvq[bxsz__fchj]
            if col_indices[kfanv__ngyj] not in egn__oyafi:
                continue
        except (KeyError, ValueError) as oud__ukm:
            continue
        hryy__vcylp[bxsz__fchj] = len(oltoa__upi)
        oltoa__upi.append(bxsz__fchj)
        uig__nijzf.append(gjq__opzsk)
        alzr__ehepd = out_types[kfanv__ngyj].dtype
        yvyu__ptku = bodo.hiframes.pd_categorical_ext.get_categories_int_type(
            alzr__ehepd)
        frlh__ntf.append(numba_to_c_type(yvyu__ptku))
    uma__tqhg += f'    total_rows_np = np.array([0], dtype=np.int64)\n'
    uma__tqhg += f'    out_table = pq_read(\n'
    uma__tqhg += f'        fname_py, {is_parallel},\n'
    uma__tqhg += f'        unicode_to_utf8(bucket_region),\n'
    uma__tqhg += f'        dnf_filters, expr_filters,\n'
    uma__tqhg += f"""        storage_options_py, {tot_rows_to_read}, selected_cols_arr_{gwemz__pkzyf}.ctypes,
"""
    uma__tqhg += f'        {len(iaj__ljd)},\n'
    uma__tqhg += f'        nullable_cols_arr_{gwemz__pkzyf}.ctypes,\n'
    if len(uig__nijzf) > 0:
        uma__tqhg += (
            f'        np.array({uig__nijzf}, dtype=np.int32).ctypes,\n')
        uma__tqhg += f'        np.array({frlh__ntf}, dtype=np.int32).ctypes,\n'
        uma__tqhg += f'        {len(uig__nijzf)},\n'
    else:
        uma__tqhg += f'        0, 0, 0,\n'
    if len(str_as_dict_cols) > 0:
        uma__tqhg += f"""        np.array({str_as_dict_cols}, dtype=np.int32).ctypes, {len(str_as_dict_cols)},
"""
    else:
        uma__tqhg += f'        0, 0,\n'
    uma__tqhg += f'        total_rows_np.ctypes,\n'
    uma__tqhg += f'        {input_file_name_col is not None},\n'
    uma__tqhg += f'    )\n'
    uma__tqhg += f'    check_and_propagate_cpp_exception()\n'
    ezwfj__ast = 'None'
    ean__uavjv = index_column_type
    rtnc__ueu = TableType(tuple(out_types))
    if tim__ful:
        rtnc__ueu = types.none
    if index_column_index is not None:
        thuq__kcho = bcp__zgm[index_column_index]
        ezwfj__ast = (
            f'info_to_array(info_from_table(out_table, {thuq__kcho}), index_arr_type)'
            )
    uma__tqhg += f'    index_arr = {ezwfj__ast}\n'
    if tim__ful:
        jnz__jfz = None
    else:
        jnz__jfz = []
        ygb__dyi = 0
        nuu__bvur = col_indices[col_names.index(input_file_name_col)
            ] if input_file_name_col is not None else None
        for gjq__opzsk, zwqty__eqws in enumerate(col_indices):
            if ygb__dyi < len(type_usecol_offset
                ) and gjq__opzsk == type_usecol_offset[ygb__dyi]:
                hmw__kxtj = col_indices[gjq__opzsk]
                if nuu__bvur and hmw__kxtj == nuu__bvur:
                    jnz__jfz.append(len(iaj__ljd) + len(oltoa__upi))
                elif hmw__kxtj in egn__oyafi:
                    ydn__ojuc = nvx__xqqd[gjq__opzsk]
                    jnz__jfz.append(len(iaj__ljd) + hryy__vcylp[ydn__ojuc])
                else:
                    jnz__jfz.append(bcp__zgm[zwqty__eqws])
                ygb__dyi += 1
            else:
                jnz__jfz.append(-1)
        jnz__jfz = np.array(jnz__jfz, dtype=np.int64)
    if tim__ful:
        uma__tqhg += '    T = None\n'
    else:
        uma__tqhg += f"""    T = cpp_table_to_py_table(out_table, table_idx_{gwemz__pkzyf}, py_table_type_{gwemz__pkzyf})
"""
    uma__tqhg += f'    delete_table(out_table)\n'
    uma__tqhg += f'    total_rows = total_rows_np[0]\n'
    uma__tqhg += f'    ev.finalize()\n'
    uma__tqhg += f'    return (total_rows, T, index_arr)\n'
    xnr__faif = {}
    jmf__ueu = {f'py_table_type_{gwemz__pkzyf}': rtnc__ueu,
        f'table_idx_{gwemz__pkzyf}': jnz__jfz,
        f'selected_cols_arr_{gwemz__pkzyf}': np.array(iaj__ljd, np.int32),
        f'nullable_cols_arr_{gwemz__pkzyf}': np.array(dkky__jgn, np.int32),
        'index_arr_type': ean__uavjv, 'cpp_table_to_py_table':
        cpp_table_to_py_table, 'info_to_array': info_to_array,
        'info_from_table': info_from_table, 'delete_table': delete_table,
        'check_and_propagate_cpp_exception':
        check_and_propagate_cpp_exception, 'pq_read': _pq_read,
        'unicode_to_utf8': unicode_to_utf8, 'get_filters_pyobject':
        get_filters_pyobject, 'get_storage_options_pyobject':
        get_storage_options_pyobject, 'get_fname_pyobject':
        get_fname_pyobject, 'np': np, 'pd': pd, 'bodo': bodo}
    exec(uma__tqhg, jmf__ueu, xnr__faif)
    axn__xpdc = xnr__faif['pq_reader_py']
    fez__btk = numba.njit(axn__xpdc, no_cpython_wrapper=True)
    return fez__btk


import pyarrow as pa
_pa_numba_typ_map = {pa.bool_(): types.bool_, pa.int8(): types.int8, pa.
    int16(): types.int16, pa.int32(): types.int32, pa.int64(): types.int64,
    pa.uint8(): types.uint8, pa.uint16(): types.uint16, pa.uint32(): types.
    uint32, pa.uint64(): types.uint64, pa.float32(): types.float32, pa.
    float64(): types.float64, pa.string(): string_type, pa.binary():
    bytes_type, pa.date32(): datetime_date_type, pa.date64(): types.
    NPDatetime('ns'), null(): string_type}


def get_arrow_timestamp_type(pa_ts_typ):
    ohw__hsnl = 'ns', 'us', 'ms', 's'
    if pa_ts_typ.unit not in ohw__hsnl:
        return types.Array(bodo.datetime64ns, 1, 'C'), False
    elif pa_ts_typ.tz is not None:
        snmoq__tibbj = pa_ts_typ.to_pandas_dtype().tz
        gpqsa__krzt = bodo.libs.pd_datetime_arr_ext.get_pytz_type_info(
            snmoq__tibbj)
        return bodo.DatetimeArrayType(gpqsa__krzt), True
    else:
        return types.Array(bodo.datetime64ns, 1, 'C'), True


def _get_numba_typ_from_pa_typ(pa_typ, is_index, nullable_from_metadata,
    category_info, str_as_dict=False):
    if isinstance(pa_typ.type, pa.ListType):
        buh__qawey, ygl__dlpko = _get_numba_typ_from_pa_typ(pa_typ.type.
            value_field, is_index, nullable_from_metadata, category_info)
        return ArrayItemArrayType(buh__qawey), ygl__dlpko
    if isinstance(pa_typ.type, pa.StructType):
        fkn__btcbu = []
        tah__sict = []
        ygl__dlpko = True
        for jpbpm__rfwnc in pa_typ.flatten():
            tah__sict.append(jpbpm__rfwnc.name.split('.')[-1])
            fpz__hggg, fyt__qkqs = _get_numba_typ_from_pa_typ(jpbpm__rfwnc,
                is_index, nullable_from_metadata, category_info)
            fkn__btcbu.append(fpz__hggg)
            ygl__dlpko = ygl__dlpko and fyt__qkqs
        return StructArrayType(tuple(fkn__btcbu), tuple(tah__sict)), ygl__dlpko
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
        tzkf__jysyf = _pa_numba_typ_map[pa_typ.type.index_type]
        hyd__uyk = PDCategoricalDtype(category_info[pa_typ.name], bodo.
            string_type, pa_typ.type.ordered, int_type=tzkf__jysyf)
        return CategoricalArrayType(hyd__uyk), True
    if isinstance(pa_typ.type, pa.lib.TimestampType):
        return get_arrow_timestamp_type(pa_typ.type)
    elif pa_typ.type in _pa_numba_typ_map:
        hhhsm__zmv = _pa_numba_typ_map[pa_typ.type]
        ygl__dlpko = True
    else:
        raise BodoError('Arrow data type {} not supported yet'.format(
            pa_typ.type))
    if hhhsm__zmv == datetime_date_type:
        return datetime_date_array_type, ygl__dlpko
    if hhhsm__zmv == bytes_type:
        return binary_array_type, ygl__dlpko
    buh__qawey = (string_array_type if hhhsm__zmv == string_type else types
        .Array(hhhsm__zmv, 1, 'C'))
    if hhhsm__zmv == types.bool_:
        buh__qawey = boolean_array
    if nullable_from_metadata is not None:
        ufx__brf = nullable_from_metadata
    else:
        ufx__brf = use_nullable_int_arr
    if ufx__brf and not is_index and isinstance(hhhsm__zmv, types.Integer
        ) and pa_typ.nullable:
        buh__qawey = IntegerArrayType(hhhsm__zmv)
    return buh__qawey, ygl__dlpko


def get_parquet_dataset(fpath, get_row_counts=True, dnf_filters=None,
    expr_filters=None, storage_options=None, read_categories=False,
    is_parallel=False, tot_rows_to_read=None):
    if get_row_counts:
        mnrc__oavia = tracing.Event('get_parquet_dataset')
    import time
    import pyarrow as pa
    import pyarrow.parquet as pq
    from mpi4py import MPI
    vgjg__uedh = MPI.COMM_WORLD
    if isinstance(fpath, list):
        waebv__vwnyy = urlparse(fpath[0])
        protocol = waebv__vwnyy.scheme
        rrgsv__mqtf = waebv__vwnyy.netloc
        for gjq__opzsk in range(len(fpath)):
            pve__muv = fpath[gjq__opzsk]
            drllx__jpmtt = urlparse(pve__muv)
            if drllx__jpmtt.scheme != protocol:
                raise BodoError(
                    'All parquet files must use the same filesystem protocol')
            if drllx__jpmtt.netloc != rrgsv__mqtf:
                raise BodoError(
                    'All parquet files must be in the same S3 bucket')
            fpath[gjq__opzsk] = pve__muv.rstrip('/')
    else:
        waebv__vwnyy = urlparse(fpath)
        protocol = waebv__vwnyy.scheme
        fpath = fpath.rstrip('/')
    if protocol in {'gcs', 'gs'}:
        try:
            import gcsfs
        except ImportError as oud__ukm:
            jepef__wjkbp = """Couldn't import gcsfs, which is required for Google cloud access. gcsfs can be installed by calling 'conda install -c conda-forge gcsfs'.
"""
            raise BodoError(jepef__wjkbp)
    if protocol == 'http':
        try:
            import fsspec
        except ImportError as oud__ukm:
            jepef__wjkbp = """Couldn't import fsspec, which is required for http access. fsspec can be installed by calling 'conda install -c conda-forge fsspec'.
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
            mbat__coqc = gcsfs.GCSFileSystem(token=None)
            fs.append(mbat__coqc)
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
                prefix = f'{protocol}://{waebv__vwnyy.netloc}'
                path = path[len(prefix):]
            gdso__eiyz = fs.glob(path)
            if protocol == 's3':
                gdso__eiyz = [('s3://' + pve__muv) for pve__muv in
                    gdso__eiyz if not pve__muv.startswith('s3://')]
            elif protocol in {'hdfs', 'abfs', 'abfss'}:
                gdso__eiyz = [(prefix + pve__muv) for pve__muv in gdso__eiyz]
        except:
            raise BodoError(
                f'glob pattern expansion not supported for {protocol}')
        if len(gdso__eiyz) == 0:
            raise BodoError('No files found matching glob pattern')
        return gdso__eiyz
    clp__kjb = False
    if get_row_counts:
        escwl__dnnb = getfs(parallel=True)
        clp__kjb = bodo.parquet_validate_schema
    if bodo.get_rank() == 0:
        kqcl__vnb = 1
        jdi__npm = os.cpu_count()
        if jdi__npm is not None and jdi__npm > 1:
            kqcl__vnb = jdi__npm // 2
        try:
            if get_row_counts:
                rfhtd__bso = tracing.Event('pq.ParquetDataset', is_parallel
                    =False)
                if tracing.is_tracing():
                    rfhtd__bso.add_attribute('dnf_filter', str(dnf_filters))
            ljkl__ywt = pa.io_thread_count()
            pa.set_io_thread_count(kqcl__vnb)
            if '*' in fpath:
                fpath = glob(protocol, getfs(), fpath)
            if protocol == 's3':
                if isinstance(fpath, list):
                    get_legacy_fs().info(fpath[0])
                else:
                    get_legacy_fs().info(fpath)
            if protocol in {'hdfs', 'abfs', 'abfss'}:
                prefix = f'{protocol}://{waebv__vwnyy.netloc}'
                if isinstance(fpath, list):
                    ywceg__amnir = [pve__muv[len(prefix):] for pve__muv in
                        fpath]
                else:
                    ywceg__amnir = fpath[len(prefix):]
            else:
                ywceg__amnir = fpath
            nhwwk__wpb = pq.ParquetDataset(ywceg__amnir, filesystem=
                get_legacy_fs(), filters=None, use_legacy_dataset=True,
                validate_schema=False, metadata_nthreads=kqcl__vnb)
            pa.set_io_thread_count(ljkl__ywt)
            yaswo__djvz = bodo.io.pa_parquet.get_dataset_schema(nhwwk__wpb)
            if dnf_filters:
                if get_row_counts:
                    rfhtd__bso.add_attribute('num_pieces_before_filter',
                        len(nhwwk__wpb.pieces))
                twz__kwflj = time.time()
                nhwwk__wpb._filter(dnf_filters)
                if get_row_counts:
                    rfhtd__bso.add_attribute('dnf_filter_time', time.time() -
                        twz__kwflj)
                    rfhtd__bso.add_attribute('num_pieces_after_filter', len
                        (nhwwk__wpb.pieces))
            if get_row_counts:
                rfhtd__bso.finalize()
            nhwwk__wpb._metadata.fs = None
        except Exception as ueaax__nrzn:
            vgjg__uedh.bcast(ueaax__nrzn)
            raise BodoError(
                f"""error from pyarrow: {type(ueaax__nrzn).__name__}: {str(ueaax__nrzn)}
"""
                )
        if get_row_counts:
            frr__eeu = tracing.Event('bcast dataset')
        vgjg__uedh.bcast(nhwwk__wpb)
        vgjg__uedh.bcast(yaswo__djvz)
    else:
        if get_row_counts:
            frr__eeu = tracing.Event('bcast dataset')
        nhwwk__wpb = vgjg__uedh.bcast(None)
        if isinstance(nhwwk__wpb, Exception):
            cdji__rghsr = nhwwk__wpb
            raise BodoError(
                f"""error from pyarrow: {type(cdji__rghsr).__name__}: {str(cdji__rghsr)}
"""
                )
        yaswo__djvz = vgjg__uedh.bcast(None)
    if get_row_counts:
        bzj__mkkgs = getfs()
    else:
        bzj__mkkgs = get_legacy_fs()
    nhwwk__wpb._metadata.fs = bzj__mkkgs
    if get_row_counts:
        frr__eeu.finalize()
    nhwwk__wpb._bodo_total_rows = 0
    if get_row_counts and tot_rows_to_read == 0:
        get_row_counts = clp__kjb = False
        for tnug__bwno in nhwwk__wpb.pieces:
            tnug__bwno._bodo_num_rows = 0
    if get_row_counts or clp__kjb:
        if get_row_counts and tracing.is_tracing():
            uov__emzmq = tracing.Event('get_row_counts')
            uov__emzmq.add_attribute('g_num_pieces', len(nhwwk__wpb.pieces))
            uov__emzmq.add_attribute('g_expr_filters', str(expr_filters))
        mjyh__jxols = 0.0
        num_pieces = len(nhwwk__wpb.pieces)
        start = get_start(num_pieces, bodo.get_size(), bodo.get_rank())
        uvmmn__qdjz = get_end(num_pieces, bodo.get_size(), bodo.get_rank())
        tpmq__hhgl = 0
        rkdui__azckq = 0
        kir__ykl = 0
        rif__jgxyq = True
        if expr_filters is not None:
            import random
            random.seed(37)
            opo__yfd = random.sample(nhwwk__wpb.pieces, k=len(nhwwk__wpb.
                pieces))
        else:
            opo__yfd = nhwwk__wpb.pieces
        for tnug__bwno in opo__yfd:
            tnug__bwno._bodo_num_rows = 0
        fpaths = [tnug__bwno.path for tnug__bwno in opo__yfd[start:uvmmn__qdjz]
            ]
        if protocol == 's3':
            rrgsv__mqtf = waebv__vwnyy.netloc
            prefix = 's3://' + rrgsv__mqtf + '/'
            fpaths = [pve__muv[len(prefix):] for pve__muv in fpaths]
            bzj__mkkgs = get_s3_subtree_fs(rrgsv__mqtf, region=getfs().
                region, storage_options=storage_options)
        else:
            bzj__mkkgs = getfs()
        pa.set_io_thread_count(4)
        pa.set_cpu_count(4)
        hxgxt__ntexh = ds.dataset(fpaths, filesystem=bzj__mkkgs,
            partitioning=ds.partitioning(flavor='hive'))
        for mwa__rebl, qnv__xxv in zip(opo__yfd[start:uvmmn__qdjz],
            hxgxt__ntexh.get_fragments()):
            twz__kwflj = time.time()
            gqxc__nax = qnv__xxv.scanner(schema=hxgxt__ntexh.schema, filter
                =expr_filters, use_threads=True).count_rows()
            mjyh__jxols += time.time() - twz__kwflj
            mwa__rebl._bodo_num_rows = gqxc__nax
            tpmq__hhgl += gqxc__nax
            rkdui__azckq += qnv__xxv.num_row_groups
            kir__ykl += sum(khg__ualq.total_byte_size for khg__ualq in
                qnv__xxv.row_groups)
            if clp__kjb:
                fti__jzhbr = qnv__xxv.metadata.schema.to_arrow_schema()
                if yaswo__djvz != fti__jzhbr:
                    print('Schema in {!s} was different. \n{!s}\n\nvs\n\n{!s}'
                        .format(mwa__rebl, fti__jzhbr, yaswo__djvz))
                    rif__jgxyq = False
                    break
        if clp__kjb:
            rif__jgxyq = vgjg__uedh.allreduce(rif__jgxyq, op=MPI.LAND)
            if not rif__jgxyq:
                raise BodoError("Schema in parquet files don't match")
        if get_row_counts:
            nhwwk__wpb._bodo_total_rows = vgjg__uedh.allreduce(tpmq__hhgl,
                op=MPI.SUM)
            mxmf__rylhe = vgjg__uedh.allreduce(rkdui__azckq, op=MPI.SUM)
            avx__jmx = vgjg__uedh.allreduce(kir__ykl, op=MPI.SUM)
            wgg__kka = np.array([tnug__bwno._bodo_num_rows for tnug__bwno in
                nhwwk__wpb.pieces])
            wgg__kka = vgjg__uedh.allreduce(wgg__kka, op=MPI.SUM)
            for tnug__bwno, xugzj__euq in zip(nhwwk__wpb.pieces, wgg__kka):
                tnug__bwno._bodo_num_rows = xugzj__euq
            if is_parallel and bodo.get_rank(
                ) == 0 and mxmf__rylhe < bodo.get_size() and mxmf__rylhe != 0:
                warnings.warn(BodoWarning(
                    f"""Total number of row groups in parquet dataset {fpath} ({mxmf__rylhe}) is too small for effective IO parallelization.
For best performance the number of row groups should be greater than the number of workers ({bodo.get_size()})
"""
                    ))
            if mxmf__rylhe == 0:
                yrf__xds = 0
            else:
                yrf__xds = avx__jmx // mxmf__rylhe
            if (bodo.get_rank() == 0 and avx__jmx >= 20 * 1048576 and 
                yrf__xds < 1048576 and protocol in REMOTE_FILESYSTEMS):
                warnings.warn(BodoWarning(
                    f'Parquet average row group size is small ({yrf__xds} bytes) and can have negative impact on performance when reading from remote sources'
                    ))
            if tracing.is_tracing():
                uov__emzmq.add_attribute('g_total_num_row_groups', mxmf__rylhe)
                if expr_filters is not None:
                    uov__emzmq.add_attribute('total_scan_time', mjyh__jxols)
                hput__ijxpn = np.array([tnug__bwno._bodo_num_rows for
                    tnug__bwno in nhwwk__wpb.pieces])
                ztei__ibqo = np.percentile(hput__ijxpn, [25, 50, 75])
                uov__emzmq.add_attribute('g_row_counts_min', hput__ijxpn.min())
                uov__emzmq.add_attribute('g_row_counts_Q1', ztei__ibqo[0])
                uov__emzmq.add_attribute('g_row_counts_median', ztei__ibqo[1])
                uov__emzmq.add_attribute('g_row_counts_Q3', ztei__ibqo[2])
                uov__emzmq.add_attribute('g_row_counts_max', hput__ijxpn.max())
                uov__emzmq.add_attribute('g_row_counts_mean', hput__ijxpn.
                    mean())
                uov__emzmq.add_attribute('g_row_counts_std', hput__ijxpn.std())
                uov__emzmq.add_attribute('g_row_counts_sum', hput__ijxpn.sum())
                uov__emzmq.finalize()
    nhwwk__wpb._prefix = ''
    if protocol in {'hdfs', 'abfs', 'abfss'}:
        prefix = f'{protocol}://{waebv__vwnyy.netloc}'
        if len(nhwwk__wpb.pieces) > 0:
            mwa__rebl = nhwwk__wpb.pieces[0]
            if not mwa__rebl.path.startswith(prefix):
                nhwwk__wpb._prefix = prefix
    if read_categories:
        _add_categories_to_pq_dataset(nhwwk__wpb)
    if get_row_counts:
        mnrc__oavia.finalize()
    return nhwwk__wpb


def get_scanner_batches(fpaths, expr_filters, selected_fields,
    avg_num_pieces, is_parallel, storage_options, region, prefix,
    str_as_dict_cols, start_offset, rows_to_read):
    import pyarrow as pa
    jdi__npm = os.cpu_count()
    if jdi__npm is None or jdi__npm == 0:
        jdi__npm = 2
    wes__suzy = min(4, jdi__npm)
    bpy__leill = min(16, jdi__npm)
    if is_parallel and len(fpaths) > bpy__leill and len(fpaths
        ) / avg_num_pieces >= 2.0:
        pa.set_io_thread_count(bpy__leill)
        pa.set_cpu_count(bpy__leill)
    else:
        pa.set_io_thread_count(wes__suzy)
        pa.set_cpu_count(wes__suzy)
    if fpaths[0].startswith('s3://'):
        rrgsv__mqtf = urlparse(fpaths[0]).netloc
        prefix = 's3://' + rrgsv__mqtf + '/'
        fpaths = [pve__muv[len(prefix):] for pve__muv in fpaths]
        bzj__mkkgs = get_s3_subtree_fs(rrgsv__mqtf, region=region,
            storage_options=storage_options)
    elif prefix and prefix.startswith(('hdfs', 'abfs', 'abfss')):
        bzj__mkkgs = get_hdfs_fs(prefix + fpaths[0])
    elif fpaths[0].startswith(('gcs', 'gs')):
        import gcsfs
        bzj__mkkgs = gcsfs.GCSFileSystem(token=None)
    else:
        bzj__mkkgs = None
    wrais__pty = ds.ParquetFileFormat(dictionary_columns=str_as_dict_cols)
    nhwwk__wpb = ds.dataset(fpaths, filesystem=bzj__mkkgs, partitioning=ds.
        partitioning(flavor='hive'), format=wrais__pty)
    col_names = nhwwk__wpb.schema.names
    eyvu__arwte = [col_names[zmtz__ktnf] for zmtz__ktnf in selected_fields]
    lmmf__scnrw = len(fpaths) <= 3 or start_offset > 0 and len(fpaths) <= 10
    if lmmf__scnrw and expr_filters is None:
        lnjkb__uek = []
        odp__zeq = 0
        khnu__nsea = 0
        for qnv__xxv in nhwwk__wpb.get_fragments():
            swqx__uzthu = []
            for khg__ualq in qnv__xxv.row_groups:
                djmyj__qzis = khg__ualq.num_rows
                if start_offset < odp__zeq + djmyj__qzis:
                    if khnu__nsea == 0:
                        uizjg__jow = start_offset - odp__zeq
                        hqhj__tqf = min(djmyj__qzis - uizjg__jow, rows_to_read)
                    else:
                        hqhj__tqf = min(djmyj__qzis, rows_to_read - khnu__nsea)
                    khnu__nsea += hqhj__tqf
                    swqx__uzthu.append(khg__ualq.id)
                odp__zeq += djmyj__qzis
                if khnu__nsea == rows_to_read:
                    break
            lnjkb__uek.append(qnv__xxv.subset(row_group_ids=swqx__uzthu))
            if khnu__nsea == rows_to_read:
                break
        nhwwk__wpb = ds.FileSystemDataset(lnjkb__uek, nhwwk__wpb.schema,
            wrais__pty, filesystem=nhwwk__wpb.filesystem)
        start_offset = uizjg__jow
    hprx__ekj = nhwwk__wpb.scanner(columns=eyvu__arwte, filter=expr_filters,
        use_threads=True).to_reader()
    return nhwwk__wpb, hprx__ekj, start_offset


def _add_categories_to_pq_dataset(pq_dataset):
    import pyarrow as pa
    from mpi4py import MPI
    if len(pq_dataset.pieces) < 1:
        raise BodoError(
            'No pieces found in Parquet dataset. Cannot get read categorical values'
            )
    pa_schema = pq_dataset.schema.to_arrow_schema()
    fiuj__saka = [c for c in pa_schema.names if isinstance(pa_schema.field(
        c).type, pa.DictionaryType)]
    if len(fiuj__saka) == 0:
        pq_dataset._category_info = {}
        return
    vgjg__uedh = MPI.COMM_WORLD
    if bodo.get_rank() == 0:
        try:
            hpz__xgk = pq_dataset.pieces[0].open()
            khg__ualq = hpz__xgk.read_row_group(0, fiuj__saka)
            category_info = {c: tuple(khg__ualq.column(c).chunk(0).
                dictionary.to_pylist()) for c in fiuj__saka}
            del hpz__xgk, khg__ualq
        except Exception as ueaax__nrzn:
            vgjg__uedh.bcast(ueaax__nrzn)
            raise ueaax__nrzn
        vgjg__uedh.bcast(category_info)
    else:
        category_info = vgjg__uedh.bcast(None)
        if isinstance(category_info, Exception):
            cdji__rghsr = category_info
            raise cdji__rghsr
    pq_dataset._category_info = category_info


def get_pandas_metadata(schema, num_pieces):
    nde__ate = None
    nullable_from_metadata = defaultdict(lambda : None)
    pude__kdcq = b'pandas'
    if schema.metadata is not None and pude__kdcq in schema.metadata:
        import json
        otlpr__miy = json.loads(schema.metadata[pude__kdcq].decode('utf8'))
        ccxe__qibs = len(otlpr__miy['index_columns'])
        if ccxe__qibs > 1:
            raise BodoError('read_parquet: MultiIndex not supported yet')
        nde__ate = otlpr__miy['index_columns'][0] if ccxe__qibs else None
        if not isinstance(nde__ate, str) and (not isinstance(nde__ate, dict
            ) or num_pieces != 1):
            nde__ate = None
        for epj__pygbs in otlpr__miy['columns']:
            sli__auu = epj__pygbs['name']
            if epj__pygbs['pandas_type'].startswith('int'
                ) and sli__auu is not None:
                if epj__pygbs['numpy_type'].startswith('Int'):
                    nullable_from_metadata[sli__auu] = True
                else:
                    nullable_from_metadata[sli__auu] = False
    return nde__ate, nullable_from_metadata


def determine_str_as_dict_columns(pq_dataset, pa_schema):
    from mpi4py import MPI
    vgjg__uedh = MPI.COMM_WORLD
    toku__yxi = []
    for sli__auu in pa_schema.names:
        jpbpm__rfwnc = pa_schema.field(sli__auu)
        if jpbpm__rfwnc.type == pa.string():
            toku__yxi.append((sli__auu, pa_schema.get_field_index(sli__auu)))
    if len(toku__yxi) == 0:
        return set()
    if len(pq_dataset.pieces) > bodo.get_size():
        import random
        random.seed(37)
        opo__yfd = random.sample(pq_dataset.pieces, bodo.get_size())
    else:
        opo__yfd = pq_dataset.pieces
    pkkqk__dsgdl = np.zeros(len(toku__yxi), dtype=np.int64)
    hgack__str = np.zeros(len(toku__yxi), dtype=np.int64)
    if bodo.get_rank() < len(opo__yfd):
        mwa__rebl = opo__yfd[bodo.get_rank()]
        pakql__qsgck = mwa__rebl.get_metadata()
        for gjq__opzsk in range(pakql__qsgck.num_row_groups):
            for ygb__dyi, (escwl__dnnb, dniy__lrfmp) in enumerate(toku__yxi):
                pkkqk__dsgdl[ygb__dyi] += pakql__qsgck.row_group(gjq__opzsk
                    ).column(dniy__lrfmp).total_uncompressed_size
        icm__kbs = pakql__qsgck.num_rows
    else:
        icm__kbs = 0
    rae__rfy = vgjg__uedh.allreduce(icm__kbs, op=MPI.SUM)
    if rae__rfy == 0:
        return set()
    vgjg__uedh.Allreduce(pkkqk__dsgdl, hgack__str, op=MPI.SUM)
    hmbq__uypw = hgack__str / rae__rfy
    str_as_dict = set()
    for gjq__opzsk, hdyyg__dne in enumerate(hmbq__uypw):
        if hdyyg__dne < READ_STR_AS_DICT_THRESHOLD:
            sli__auu = toku__yxi[gjq__opzsk][0]
            str_as_dict.add(sli__auu)
    return str_as_dict


def parquet_file_schema(file_name, selected_columns, storage_options=None,
    input_file_name_col=None):
    col_names = []
    qhllz__galui = []
    pq_dataset = get_parquet_dataset(file_name, get_row_counts=False,
        storage_options=storage_options, read_categories=True)
    partition_names = [] if pq_dataset.partitions is None else [pq_dataset.
        partitions.levels[gjq__opzsk].name for gjq__opzsk in range(len(
        pq_dataset.partitions.partition_names))]
    pa_schema = pq_dataset.schema.to_arrow_schema()
    num_pieces = len(pq_dataset.pieces)
    str_as_dict = determine_str_as_dict_columns(pq_dataset, pa_schema)
    col_names = pa_schema.names
    nde__ate, nullable_from_metadata = get_pandas_metadata(pa_schema,
        num_pieces)
    sbzhp__xcn = []
    mqg__bpjxb = []
    vmknz__cjbp = []
    for gjq__opzsk, c in enumerate(col_names):
        jpbpm__rfwnc = pa_schema.field(c)
        hhhsm__zmv, ygl__dlpko = _get_numba_typ_from_pa_typ(jpbpm__rfwnc, c ==
            nde__ate, nullable_from_metadata[c], pq_dataset._category_info,
            str_as_dict=c in str_as_dict)
        sbzhp__xcn.append(hhhsm__zmv)
        mqg__bpjxb.append(ygl__dlpko)
        vmknz__cjbp.append(jpbpm__rfwnc.type)
    if partition_names:
        col_names += partition_names
        sbzhp__xcn += [_get_partition_cat_dtype(pq_dataset.partitions.
            levels[gjq__opzsk]) for gjq__opzsk in range(len(partition_names))]
        mqg__bpjxb.extend([True] * len(partition_names))
        vmknz__cjbp.extend([None] * len(partition_names))
    if input_file_name_col is not None:
        col_names += [input_file_name_col]
        sbzhp__xcn += [dict_str_arr_type]
        mqg__bpjxb.append(True)
        vmknz__cjbp.append(None)
    lsey__fzet = {c: gjq__opzsk for gjq__opzsk, c in enumerate(col_names)}
    if selected_columns is None:
        selected_columns = col_names
    for c in selected_columns:
        if c not in lsey__fzet:
            raise BodoError(f'Selected column {c} not in Parquet file schema')
    if nde__ate and not isinstance(nde__ate, dict
        ) and nde__ate not in selected_columns:
        selected_columns.append(nde__ate)
    col_names = selected_columns
    col_indices = []
    qhllz__galui = []
    ejwr__pqj = []
    gox__xbq = []
    for gjq__opzsk, c in enumerate(col_names):
        hmw__kxtj = lsey__fzet[c]
        col_indices.append(hmw__kxtj)
        qhllz__galui.append(sbzhp__xcn[hmw__kxtj])
        if not mqg__bpjxb[hmw__kxtj]:
            ejwr__pqj.append(gjq__opzsk)
            gox__xbq.append(vmknz__cjbp[hmw__kxtj])
    return (col_names, qhllz__galui, nde__ate, col_indices, partition_names,
        ejwr__pqj, gox__xbq)


def _get_partition_cat_dtype(part_set):
    kgyd__ekpt = part_set.dictionary.to_pandas()
    psck__lpnh = bodo.typeof(kgyd__ekpt).dtype
    hyd__uyk = PDCategoricalDtype(tuple(kgyd__ekpt), psck__lpnh, False)
    return CategoricalArrayType(hyd__uyk)


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
        ybcz__tnwz = lir.FunctionType(lir.VoidType(), [lir.IntType(8).
            as_pointer(), lir.IntType(8).as_pointer(), lir.IntType(8).
            as_pointer(), lir.IntType(8).as_pointer(), lir.IntType(1), lir.
            IntType(8).as_pointer(), lir.IntType(8).as_pointer(), lir.
            IntType(1), lir.IntType(1), lir.IntType(32), lir.IntType(32),
            lir.IntType(32), lir.IntType(8).as_pointer(), lir.IntType(8).
            as_pointer()])
        puidg__por = cgutils.get_or_insert_function(builder.module,
            ybcz__tnwz, name='pq_write')
        builder.call(puidg__por, args)
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
        ybcz__tnwz = lir.FunctionType(lir.VoidType(), [lir.IntType(8).
            as_pointer(), lir.IntType(8).as_pointer(), lir.IntType(8).
            as_pointer(), lir.IntType(8).as_pointer(), lir.IntType(8).
            as_pointer(), lir.IntType(8).as_pointer(), lir.IntType(32), lir
            .IntType(8).as_pointer(), lir.IntType(1), lir.IntType(8).
            as_pointer()])
        puidg__por = cgutils.get_or_insert_function(builder.module,
            ybcz__tnwz, name='pq_write_partitioned')
        builder.call(puidg__por, args)
        bodo.utils.utils.inlined_check_and_propagate_cpp_exception(context,
            builder)
    return types.void(types.voidptr, data_table_t, col_names_t,
        col_names_no_partitions_t, cat_table_t, types.voidptr, types.int32,
        types.voidptr, types.boolean, types.voidptr), codegen
