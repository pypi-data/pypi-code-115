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
        except OSError as ngsxg__lnuub:
            if 'non-file path' in str(ngsxg__lnuub):
                raise FileNotFoundError(str(ngsxg__lnuub))
            raise


class ParquetHandler:

    def __init__(self, func_ir, typingctx, args, _locals):
        self.func_ir = func_ir
        self.typingctx = typingctx
        self.args = args
        self.locals = _locals

    def gen_parquet_read(self, file_name, lhs, columns, storage_options=
        None, input_file_name_col=None):
        wjajr__dmn = lhs.scope
        yvs__ztn = lhs.loc
        nuodp__kduum = None
        if lhs.name in self.locals:
            nuodp__kduum = self.locals[lhs.name]
            self.locals.pop(lhs.name)
        jfnp__aglyf = {}
        if lhs.name + ':convert' in self.locals:
            jfnp__aglyf = self.locals[lhs.name + ':convert']
            self.locals.pop(lhs.name + ':convert')
        if nuodp__kduum is None:
            qjmde__krtke = (
                'Parquet schema not available. Either path argument should be constant for Bodo to look at the file at compile time or schema should be provided. For more information, see: https://docs.bodo.ai/latest/source/programming_with_bodo/file_io.html#non-constant-filepaths'
                )
            duq__vvtqf = get_const_value(file_name, self.func_ir,
                qjmde__krtke, arg_types=self.args, file_info=
                ParquetFileInfo(columns, storage_options=storage_options,
                input_file_name_col=input_file_name_col))
            izs__yoti = False
            xfou__ouxeu = guard(get_definition, self.func_ir, file_name)
            if isinstance(xfou__ouxeu, ir.Arg):
                typ = self.args[xfou__ouxeu.index]
                if isinstance(typ, types.FilenameType):
                    (col_names, sdt__eobp, xmd__gchyi, col_indices,
                        partition_names, acn__gkdnd, ywwap__xkxq) = typ.schema
                    izs__yoti = True
            if not izs__yoti:
                (col_names, sdt__eobp, xmd__gchyi, col_indices,
                    partition_names, acn__gkdnd, ywwap__xkxq) = (
                    parquet_file_schema(duq__vvtqf, columns,
                    storage_options=storage_options, input_file_name_col=
                    input_file_name_col))
        else:
            jwnj__sijxx = list(nuodp__kduum.keys())
            ovlgw__qqxa = {c: nqqz__xnyac for nqqz__xnyac, c in enumerate(
                jwnj__sijxx)}
            wvzwr__lbaq = [ass__jkrmr for ass__jkrmr in nuodp__kduum.values()]
            xmd__gchyi = 'index' if 'index' in ovlgw__qqxa else None
            if columns is None:
                selected_columns = jwnj__sijxx
            else:
                selected_columns = columns
            col_indices = [ovlgw__qqxa[c] for c in selected_columns]
            sdt__eobp = [wvzwr__lbaq[ovlgw__qqxa[c]] for c in selected_columns]
            col_names = selected_columns
            xmd__gchyi = xmd__gchyi if xmd__gchyi in col_names else None
            partition_names = []
            acn__gkdnd = []
            ywwap__xkxq = []
        oxfh__pczl = None if isinstance(xmd__gchyi, dict
            ) or xmd__gchyi is None else xmd__gchyi
        index_column_index = None
        index_column_type = types.none
        if oxfh__pczl:
            rjj__rnwrs = col_names.index(oxfh__pczl)
            index_column_index = col_indices.pop(rjj__rnwrs)
            index_column_type = sdt__eobp.pop(rjj__rnwrs)
            col_names.pop(rjj__rnwrs)
        for nqqz__xnyac, c in enumerate(col_names):
            if c in jfnp__aglyf:
                sdt__eobp[nqqz__xnyac] = jfnp__aglyf[c]
        yvv__nqn = [ir.Var(wjajr__dmn, mk_unique_var('pq_table'), yvs__ztn),
            ir.Var(wjajr__dmn, mk_unique_var('pq_index'), yvs__ztn)]
        uov__vqjpf = [bodo.ir.parquet_ext.ParquetReader(file_name, lhs.name,
            col_names, col_indices, sdt__eobp, yvv__nqn, yvs__ztn,
            partition_names, storage_options, index_column_index,
            index_column_type, input_file_name_col, acn__gkdnd, ywwap__xkxq)]
        return (col_names, yvv__nqn, xmd__gchyi, uov__vqjpf, sdt__eobp,
            index_column_type)


def determine_filter_cast(pq_node, typemap, filter_val, orig_colname_map):
    yhjhw__kfug = filter_val[0]
    crb__pjqvy = pq_node.original_out_types[orig_colname_map[yhjhw__kfug]]
    aaqm__jyq = bodo.utils.typing.element_type(crb__pjqvy)
    if yhjhw__kfug in pq_node.partition_names:
        if aaqm__jyq == types.unicode_type:
            ctfrm__vkzke = '.cast(pyarrow.string(), safe=False)'
        elif isinstance(aaqm__jyq, types.Integer):
            ctfrm__vkzke = f'.cast(pyarrow.{aaqm__jyq.name}(), safe=False)'
        else:
            ctfrm__vkzke = ''
    else:
        ctfrm__vkzke = ''
    dtj__dcb = typemap[filter_val[2].name]
    if isinstance(dtj__dcb, (types.List, types.Set)):
        uvvx__jzguk = dtj__dcb.dtype
    else:
        uvvx__jzguk = dtj__dcb
    if not bodo.utils.typing.is_common_scalar_dtype([aaqm__jyq, uvvx__jzguk]):
        if not bodo.utils.typing.is_safe_arrow_cast(aaqm__jyq, uvvx__jzguk):
            raise BodoError(
                f'Unsupported Arrow cast from {aaqm__jyq} to {uvvx__jzguk} in filter pushdown. Please try a comparison that avoids casting the column.'
                )
        if aaqm__jyq == types.unicode_type:
            return ".cast(pyarrow.timestamp('ns'), safe=False)", ''
        elif aaqm__jyq in (bodo.datetime64ns, bodo.pd_timestamp_type):
            if isinstance(dtj__dcb, (types.List, types.Set)):
                yyvlz__jldan = 'list' if isinstance(dtj__dcb, types.List
                    ) else 'tuple'
                raise BodoError(
                    f'Cannot cast {yyvlz__jldan} values with isin filter pushdown.'
                    )
            return ctfrm__vkzke, ".cast(pyarrow.timestamp('ns'), safe=False)"
    return ctfrm__vkzke, ''


def pq_distributed_run(pq_node, array_dists, typemap, calltypes, typingctx,
    targetctx, meta_head_only_info=None):
    hjyuy__xebrm = len(pq_node.out_vars)
    extra_args = ''
    dnf_filter_str = 'None'
    expr_filter_str = 'None'
    ptl__pyo, glpuo__uckmf = bodo.ir.connector.generate_filter_map(pq_node.
        filters)
    if pq_node.filters:
        ept__rurw = []
        vcsjx__jqmh = []
        ayw__wzard = False
        hnk__cxvb = None
        orig_colname_map = {c: nqqz__xnyac for nqqz__xnyac, c in enumerate(
            pq_node.original_df_colnames)}
        for rccn__ldxtw in pq_node.filters:
            jdr__wrb = []
            rxolr__nyzi = []
            tuzyq__rljt = set()
            for ond__zfk in rccn__ldxtw:
                if isinstance(ond__zfk[2], ir.Var):
                    wgk__jzwyf, gexi__vsgl = determine_filter_cast(pq_node,
                        typemap, ond__zfk, orig_colname_map)
                    if ond__zfk[1] == 'in':
                        rxolr__nyzi.append(
                            f"(ds.field('{ond__zfk[0]}').isin({ptl__pyo[ond__zfk[2].name]}))"
                            )
                    else:
                        rxolr__nyzi.append(
                            f"(ds.field('{ond__zfk[0]}'){wgk__jzwyf} {ond__zfk[1]} ds.scalar({ptl__pyo[ond__zfk[2].name]}){gexi__vsgl})"
                            )
                else:
                    assert ond__zfk[2
                        ] == 'NULL', 'unsupport constant used in filter pushdown'
                    if ond__zfk[1] == 'is not':
                        prefix = '~'
                    else:
                        prefix = ''
                    rxolr__nyzi.append(
                        f"({prefix}ds.field('{ond__zfk[0]}').is_null())")
                if ond__zfk[0] in pq_node.partition_names and isinstance(
                    ond__zfk[2], ir.Var):
                    cugu__qzcs = (
                        f"('{ond__zfk[0]}', '{ond__zfk[1]}', {ptl__pyo[ond__zfk[2].name]})"
                        )
                    jdr__wrb.append(cugu__qzcs)
                    tuzyq__rljt.add(cugu__qzcs)
                else:
                    ayw__wzard = True
            if hnk__cxvb is None:
                hnk__cxvb = tuzyq__rljt
            else:
                hnk__cxvb.intersection_update(tuzyq__rljt)
            tzp__wjkl = ', '.join(jdr__wrb)
            aqztu__ckkqe = ' & '.join(rxolr__nyzi)
            if tzp__wjkl:
                ept__rurw.append(f'[{tzp__wjkl}]')
            vcsjx__jqmh.append(f'({aqztu__ckkqe})')
        kbkfy__chrbv = ', '.join(ept__rurw)
        bjwe__lcrd = ' | '.join(vcsjx__jqmh)
        if ayw__wzard:
            if hnk__cxvb:
                fvis__marcw = sorted(hnk__cxvb)
                dnf_filter_str = f"[[{', '.join(fvis__marcw)}]]"
        elif kbkfy__chrbv:
            dnf_filter_str = f'[{kbkfy__chrbv}]'
        expr_filter_str = f'({bjwe__lcrd})'
        extra_args = ', '.join(ptl__pyo.values())
    dkp__cgbri = ', '.join(f'out{nqqz__xnyac}' for nqqz__xnyac in range(
        hjyuy__xebrm))
    dzug__vvs = f'def pq_impl(fname, {extra_args}):\n'
    dzug__vvs += (
        f'    (total_rows, {dkp__cgbri},) = _pq_reader_py(fname, {extra_args})\n'
        )
    fviyp__gwzex = {}
    exec(dzug__vvs, {}, fviyp__gwzex)
    fqjhx__ztg = fviyp__gwzex['pq_impl']
    if bodo.user_logging.get_verbose_level() >= 1:
        rnr__ydksf = pq_node.loc.strformat()
        ngvfe__vze = []
        xxonm__cgfm = []
        for nqqz__xnyac in pq_node.type_usecol_offset:
            yhjhw__kfug = pq_node.df_colnames[nqqz__xnyac]
            ngvfe__vze.append(yhjhw__kfug)
            if isinstance(pq_node.out_types[nqqz__xnyac], bodo.libs.
                dict_arr_ext.DictionaryArrayType):
                xxonm__cgfm.append(yhjhw__kfug)
        tyzfr__zfuur = (
            'Finish column pruning on read_parquet node:\n%s\nColumns loaded %s\n'
            )
        bodo.user_logging.log_message('Column Pruning', tyzfr__zfuur,
            rnr__ydksf, ngvfe__vze)
        if xxonm__cgfm:
            hje__nxzlp = """Finished optimized encoding on read_parquet node:
%s
Columns %s using dictionary encoding to reduce memory usage.
"""
            bodo.user_logging.log_message('Dictionary Encoding', hje__nxzlp,
                rnr__ydksf, xxonm__cgfm)
    parallel = False
    if array_dists is not None:
        izb__ocfdd = pq_node.out_vars[0].name
        parallel = array_dists[izb__ocfdd] in (distributed_pass.
            Distribution.OneD, distributed_pass.Distribution.OneD_Var)
        ktvml__yzga = pq_node.out_vars[1].name
        assert typemap[ktvml__yzga
            ] == types.none or not parallel or array_dists[ktvml__yzga] in (
            distributed_pass.Distribution.OneD, distributed_pass.
            Distribution.OneD_Var
            ), 'pq data/index parallelization does not match'
    if pq_node.unsupported_columns:
        fxvr__sbq = set(pq_node.type_usecol_offset)
        dctac__rbjuc = set(pq_node.unsupported_columns)
        hzw__tyw = fxvr__sbq & dctac__rbjuc
        if hzw__tyw:
            ezwm__yrv = sorted(hzw__tyw)
            kgvdz__mpqn = [
                f'pandas.read_parquet(): 1 or more columns found with Arrow types that are not supported in Bodo and could not be eliminated. '
                 +
                "Please manually remove these columns from your read_parquet with the 'columns' argument. If these "
                 +
                'columns are needed, you will need to modify your dataset to use a supported type.'
                , 'Unsupported Columns:']
            whbs__syjw = 0
            for yxvx__ldcfa in ezwm__yrv:
                while pq_node.unsupported_columns[whbs__syjw] != yxvx__ldcfa:
                    whbs__syjw += 1
                kgvdz__mpqn.append(
                    f"Column '{pq_node.df_colnames[yxvx__ldcfa]}' with unsupported arrow type {pq_node.unsupported_arrow_types[whbs__syjw]}"
                    )
                whbs__syjw += 1
            jix__nkfn = '\n'.join(kgvdz__mpqn)
            raise BodoError(jix__nkfn, loc=pq_node.loc)
    ezzd__pvge = _gen_pq_reader_py(pq_node.df_colnames, pq_node.col_indices,
        pq_node.type_usecol_offset, pq_node.out_types, pq_node.
        storage_options, pq_node.partition_names, dnf_filter_str,
        expr_filter_str, extra_args, parallel, meta_head_only_info, pq_node
        .index_column_index, pq_node.index_column_type, pq_node.
        input_file_name_col)
    rpo__hrka = typemap[pq_node.file_name.name]
    nwyry__sohr = (rpo__hrka,) + tuple(typemap[ond__zfk.name] for ond__zfk in
        glpuo__uckmf)
    ahcs__rwic = compile_to_numba_ir(fqjhx__ztg, {'_pq_reader_py':
        ezzd__pvge}, typingctx=typingctx, targetctx=targetctx, arg_typs=
        nwyry__sohr, typemap=typemap, calltypes=calltypes).blocks.popitem()[1]
    replace_arg_nodes(ahcs__rwic, [pq_node.file_name] + glpuo__uckmf)
    uov__vqjpf = ahcs__rwic.body[:-3]
    if meta_head_only_info:
        uov__vqjpf[-1 - hjyuy__xebrm].target = meta_head_only_info[1]
    uov__vqjpf[-2].target = pq_node.out_vars[0]
    uov__vqjpf[-1].target = pq_node.out_vars[1]
    return uov__vqjpf


distributed_pass.distributed_run_extensions[bodo.ir.parquet_ext.ParquetReader
    ] = pq_distributed_run


def get_filters_pyobject(dnf_filter_str, expr_filter_str, vars):
    pass


@overload(get_filters_pyobject, no_unliteral=True)
def overload_get_filters_pyobject(dnf_filter_str, expr_filter_str, var_tup):
    mhntz__lra = get_overload_const_str(dnf_filter_str)
    yxl__amy = get_overload_const_str(expr_filter_str)
    rvrm__ubsj = ', '.join(f'f{nqqz__xnyac}' for nqqz__xnyac in range(len(
        var_tup)))
    dzug__vvs = 'def impl(dnf_filter_str, expr_filter_str, var_tup):\n'
    if len(var_tup):
        dzug__vvs += f'  {rvrm__ubsj}, = var_tup\n'
    dzug__vvs += """  with numba.objmode(dnf_filters_py='parquet_predicate_type', expr_filters_py='parquet_predicate_type'):
"""
    dzug__vvs += f'    dnf_filters_py = {mhntz__lra}\n'
    dzug__vvs += f'    expr_filters_py = {yxl__amy}\n'
    dzug__vvs += '  return (dnf_filters_py, expr_filters_py)\n'
    fviyp__gwzex = {}
    exec(dzug__vvs, globals(), fviyp__gwzex)
    return fviyp__gwzex['impl']


@numba.njit
def get_fname_pyobject(fname):
    with numba.objmode(fname_py='read_parquet_fpath_type'):
        fname_py = fname
    return fname_py


def get_storage_options_pyobject(storage_options):
    pass


@overload(get_storage_options_pyobject, no_unliteral=True)
def overload_get_storage_options_pyobject(storage_options):
    uurfp__thit = get_overload_constant_dict(storage_options)
    dzug__vvs = 'def impl(storage_options):\n'
    dzug__vvs += (
        "  with numba.objmode(storage_options_py='storage_options_dict_type'):\n"
        )
    dzug__vvs += f'    storage_options_py = {str(uurfp__thit)}\n'
    dzug__vvs += '  return storage_options_py\n'
    fviyp__gwzex = {}
    exec(dzug__vvs, globals(), fviyp__gwzex)
    return fviyp__gwzex['impl']


def _gen_pq_reader_py(col_names, col_indices, type_usecol_offset, out_types,
    storage_options, partition_names, dnf_filter_str, expr_filter_str,
    extra_args, is_parallel, meta_head_only_info, index_column_index,
    index_column_type, input_file_name_col):
    rpip__logsr = next_label()
    lhy__bwl = ',' if extra_args else ''
    dzug__vvs = f'def pq_reader_py(fname,{extra_args}):\n'
    dzug__vvs += (
        f"    ev = bodo.utils.tracing.Event('read_parquet', {is_parallel})\n")
    dzug__vvs += f"    ev.add_attribute('fname', fname)\n"
    dzug__vvs += f"""    bucket_region = bodo.io.fs_io.get_s3_bucket_region_njit(fname, parallel={is_parallel})
"""
    dzug__vvs += f"""    dnf_filters, expr_filters = get_filters_pyobject("{dnf_filter_str}", "{expr_filter_str}", ({extra_args}{lhy__bwl}))
"""
    dzug__vvs += '    fname_py = get_fname_pyobject(fname)\n'
    storage_options['bodo_dummy'] = 'dummy'
    dzug__vvs += (
        f'    storage_options_py = get_storage_options_pyobject({str(storage_options)})\n'
        )
    tot_rows_to_read = -1
    if meta_head_only_info and meta_head_only_info[0] is not None:
        tot_rows_to_read = meta_head_only_info[0]
    kjja__vtk = not type_usecol_offset
    ylmj__xzxa = [sanitize_varname(c) for c in col_names]
    partition_names = [sanitize_varname(c) for c in partition_names]
    input_file_name_col = sanitize_varname(input_file_name_col
        ) if input_file_name_col is not None and col_names.index(
        input_file_name_col) in type_usecol_offset else None
    igan__usnx = {c: nqqz__xnyac for nqqz__xnyac, c in enumerate(col_indices)}
    unj__etz = {c: nqqz__xnyac for nqqz__xnyac, c in enumerate(ylmj__xzxa)}
    mvv__jpeg = []
    lwhr__lhnb = set()
    mxbzh__knx = partition_names + [input_file_name_col]
    for nqqz__xnyac in type_usecol_offset:
        if ylmj__xzxa[nqqz__xnyac] not in mxbzh__knx:
            mvv__jpeg.append(col_indices[nqqz__xnyac])
        elif not input_file_name_col or ylmj__xzxa[nqqz__xnyac
            ] != input_file_name_col:
            lwhr__lhnb.add(col_indices[nqqz__xnyac])
    if index_column_index is not None:
        mvv__jpeg.append(index_column_index)
    mvv__jpeg = sorted(mvv__jpeg)
    ehy__fer = {c: nqqz__xnyac for nqqz__xnyac, c in enumerate(mvv__jpeg)}

    def is_nullable(typ):
        return bodo.utils.utils.is_array_typ(typ, False) and (not
            isinstance(typ, types.Array) and not isinstance(typ, bodo.
            DatetimeArrayType))
    bfi__yxncl = [(int(is_nullable(out_types[igan__usnx[ygc__jwoau]])) if 
        ygc__jwoau != index_column_index else int(is_nullable(
        index_column_type))) for ygc__jwoau in mvv__jpeg]
    str_as_dict_cols = []
    for ygc__jwoau in mvv__jpeg:
        if ygc__jwoau == index_column_index:
            ass__jkrmr = index_column_type
        else:
            ass__jkrmr = out_types[igan__usnx[ygc__jwoau]]
        if ass__jkrmr == dict_str_arr_type:
            str_as_dict_cols.append(ygc__jwoau)
    zdydx__sxv = []
    hkk__tmvx = {}
    pmopi__msocg = []
    oblw__qzpra = []
    for nqqz__xnyac, osky__pwyoj in enumerate(partition_names):
        try:
            lbyer__oze = unj__etz[osky__pwyoj]
            if col_indices[lbyer__oze] not in lwhr__lhnb:
                continue
        except (KeyError, ValueError) as lvorf__dmu:
            continue
        hkk__tmvx[osky__pwyoj] = len(zdydx__sxv)
        zdydx__sxv.append(osky__pwyoj)
        pmopi__msocg.append(nqqz__xnyac)
        znfxb__ayd = out_types[lbyer__oze].dtype
        egn__pbgp = bodo.hiframes.pd_categorical_ext.get_categories_int_type(
            znfxb__ayd)
        oblw__qzpra.append(numba_to_c_type(egn__pbgp))
    dzug__vvs += f'    total_rows_np = np.array([0], dtype=np.int64)\n'
    dzug__vvs += f'    out_table = pq_read(\n'
    dzug__vvs += f'        fname_py, {is_parallel},\n'
    dzug__vvs += f'        unicode_to_utf8(bucket_region),\n'
    dzug__vvs += f'        dnf_filters, expr_filters,\n'
    dzug__vvs += f"""        storage_options_py, {tot_rows_to_read}, selected_cols_arr_{rpip__logsr}.ctypes,
"""
    dzug__vvs += f'        {len(mvv__jpeg)},\n'
    dzug__vvs += f'        nullable_cols_arr_{rpip__logsr}.ctypes,\n'
    if len(pmopi__msocg) > 0:
        dzug__vvs += (
            f'        np.array({pmopi__msocg}, dtype=np.int32).ctypes,\n')
        dzug__vvs += (
            f'        np.array({oblw__qzpra}, dtype=np.int32).ctypes,\n')
        dzug__vvs += f'        {len(pmopi__msocg)},\n'
    else:
        dzug__vvs += f'        0, 0, 0,\n'
    if len(str_as_dict_cols) > 0:
        dzug__vvs += f"""        np.array({str_as_dict_cols}, dtype=np.int32).ctypes, {len(str_as_dict_cols)},
"""
    else:
        dzug__vvs += f'        0, 0,\n'
    dzug__vvs += f'        total_rows_np.ctypes,\n'
    dzug__vvs += f'        {input_file_name_col is not None},\n'
    dzug__vvs += f'    )\n'
    dzug__vvs += f'    check_and_propagate_cpp_exception()\n'
    cuwvd__llucr = 'None'
    vpwrf__pxc = index_column_type
    vrje__jezf = TableType(tuple(out_types))
    if kjja__vtk:
        vrje__jezf = types.none
    if index_column_index is not None:
        emi__exzp = ehy__fer[index_column_index]
        cuwvd__llucr = (
            f'info_to_array(info_from_table(out_table, {emi__exzp}), index_arr_type)'
            )
    dzug__vvs += f'    index_arr = {cuwvd__llucr}\n'
    if kjja__vtk:
        svts__aoe = None
    else:
        svts__aoe = []
        obqp__dqqae = 0
        hhgjr__tcg = col_indices[col_names.index(input_file_name_col)
            ] if input_file_name_col is not None else None
        for nqqz__xnyac, yxvx__ldcfa in enumerate(col_indices):
            if obqp__dqqae < len(type_usecol_offset
                ) and nqqz__xnyac == type_usecol_offset[obqp__dqqae]:
                tvkkn__jzvxj = col_indices[nqqz__xnyac]
                if hhgjr__tcg and tvkkn__jzvxj == hhgjr__tcg:
                    svts__aoe.append(len(mvv__jpeg) + len(zdydx__sxv))
                elif tvkkn__jzvxj in lwhr__lhnb:
                    iyixm__fcbnu = ylmj__xzxa[nqqz__xnyac]
                    svts__aoe.append(len(mvv__jpeg) + hkk__tmvx[iyixm__fcbnu])
                else:
                    svts__aoe.append(ehy__fer[yxvx__ldcfa])
                obqp__dqqae += 1
            else:
                svts__aoe.append(-1)
        svts__aoe = np.array(svts__aoe, dtype=np.int64)
    if kjja__vtk:
        dzug__vvs += '    T = None\n'
    else:
        dzug__vvs += f"""    T = cpp_table_to_py_table(out_table, table_idx_{rpip__logsr}, py_table_type_{rpip__logsr})
"""
    dzug__vvs += f'    delete_table(out_table)\n'
    dzug__vvs += f'    total_rows = total_rows_np[0]\n'
    dzug__vvs += f'    ev.finalize()\n'
    dzug__vvs += f'    return (total_rows, T, index_arr)\n'
    fviyp__gwzex = {}
    fkbsq__eddr = {f'py_table_type_{rpip__logsr}': vrje__jezf,
        f'table_idx_{rpip__logsr}': svts__aoe,
        f'selected_cols_arr_{rpip__logsr}': np.array(mvv__jpeg, np.int32),
        f'nullable_cols_arr_{rpip__logsr}': np.array(bfi__yxncl, np.int32),
        'index_arr_type': vpwrf__pxc, 'cpp_table_to_py_table':
        cpp_table_to_py_table, 'info_to_array': info_to_array,
        'info_from_table': info_from_table, 'delete_table': delete_table,
        'check_and_propagate_cpp_exception':
        check_and_propagate_cpp_exception, 'pq_read': _pq_read,
        'unicode_to_utf8': unicode_to_utf8, 'get_filters_pyobject':
        get_filters_pyobject, 'get_storage_options_pyobject':
        get_storage_options_pyobject, 'get_fname_pyobject':
        get_fname_pyobject, 'np': np, 'pd': pd, 'bodo': bodo}
    exec(dzug__vvs, fkbsq__eddr, fviyp__gwzex)
    ezzd__pvge = fviyp__gwzex['pq_reader_py']
    ngq__gwwq = numba.njit(ezzd__pvge, no_cpython_wrapper=True)
    return ngq__gwwq


import pyarrow as pa
_pa_numba_typ_map = {pa.bool_(): types.bool_, pa.int8(): types.int8, pa.
    int16(): types.int16, pa.int32(): types.int32, pa.int64(): types.int64,
    pa.uint8(): types.uint8, pa.uint16(): types.uint16, pa.uint32(): types.
    uint32, pa.uint64(): types.uint64, pa.float32(): types.float32, pa.
    float64(): types.float64, pa.string(): string_type, pa.binary():
    bytes_type, pa.date32(): datetime_date_type, pa.date64(): types.
    NPDatetime('ns'), null(): string_type}


def get_arrow_timestamp_type(pa_ts_typ):
    fybmn__xaam = 'ns', 'us', 'ms', 's'
    if pa_ts_typ.unit not in fybmn__xaam:
        return types.Array(bodo.datetime64ns, 1, 'C'), False
    elif pa_ts_typ.tz is not None:
        xiseu__nbdl = pa_ts_typ.to_pandas_dtype().tz
        ctmn__ghz = bodo.libs.pd_datetime_arr_ext.get_pytz_type_info(
            xiseu__nbdl)
        return bodo.DatetimeArrayType(ctmn__ghz), True
    else:
        return types.Array(bodo.datetime64ns, 1, 'C'), True


def _get_numba_typ_from_pa_typ(pa_typ, is_index, nullable_from_metadata,
    category_info, str_as_dict=False):
    if isinstance(pa_typ.type, pa.ListType):
        sxvs__rruvb, aiab__fskpx = _get_numba_typ_from_pa_typ(pa_typ.type.
            value_field, is_index, nullable_from_metadata, category_info)
        return ArrayItemArrayType(sxvs__rruvb), aiab__fskpx
    if isinstance(pa_typ.type, pa.StructType):
        bgt__eirqu = []
        rlslj__dopw = []
        aiab__fskpx = True
        for gqqa__txo in pa_typ.flatten():
            rlslj__dopw.append(gqqa__txo.name.split('.')[-1])
            bsdpt__kev, oditn__mlmx = _get_numba_typ_from_pa_typ(gqqa__txo,
                is_index, nullable_from_metadata, category_info)
            bgt__eirqu.append(bsdpt__kev)
            aiab__fskpx = aiab__fskpx and oditn__mlmx
        return StructArrayType(tuple(bgt__eirqu), tuple(rlslj__dopw)
            ), aiab__fskpx
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
        kte__szr = _pa_numba_typ_map[pa_typ.type.index_type]
        hpyt__bpsxh = PDCategoricalDtype(category_info[pa_typ.name], bodo.
            string_type, pa_typ.type.ordered, int_type=kte__szr)
        return CategoricalArrayType(hpyt__bpsxh), True
    if isinstance(pa_typ.type, pa.lib.TimestampType):
        return get_arrow_timestamp_type(pa_typ.type)
    elif pa_typ.type in _pa_numba_typ_map:
        buvr__byt = _pa_numba_typ_map[pa_typ.type]
        aiab__fskpx = True
    else:
        raise BodoError('Arrow data type {} not supported yet'.format(
            pa_typ.type))
    if buvr__byt == datetime_date_type:
        return datetime_date_array_type, aiab__fskpx
    if buvr__byt == bytes_type:
        return binary_array_type, aiab__fskpx
    sxvs__rruvb = (string_array_type if buvr__byt == string_type else types
        .Array(buvr__byt, 1, 'C'))
    if buvr__byt == types.bool_:
        sxvs__rruvb = boolean_array
    if nullable_from_metadata is not None:
        adi__hwky = nullable_from_metadata
    else:
        adi__hwky = use_nullable_int_arr
    if adi__hwky and not is_index and isinstance(buvr__byt, types.Integer
        ) and pa_typ.nullable:
        sxvs__rruvb = IntegerArrayType(buvr__byt)
    return sxvs__rruvb, aiab__fskpx


def get_parquet_dataset(fpath, get_row_counts=True, dnf_filters=None,
    expr_filters=None, storage_options=None, read_categories=False,
    is_parallel=False, tot_rows_to_read=None):
    if get_row_counts:
        pbo__oyc = tracing.Event('get_parquet_dataset')
    import time
    import pyarrow as pa
    import pyarrow.parquet as pq
    from mpi4py import MPI
    uprl__tasse = MPI.COMM_WORLD
    if isinstance(fpath, list):
        sdi__rgx = urlparse(fpath[0])
        protocol = sdi__rgx.scheme
        qvxbx__ldgn = sdi__rgx.netloc
        for nqqz__xnyac in range(len(fpath)):
            miyi__lzn = fpath[nqqz__xnyac]
            wpd__znz = urlparse(miyi__lzn)
            if wpd__znz.scheme != protocol:
                raise BodoError(
                    'All parquet files must use the same filesystem protocol')
            if wpd__znz.netloc != qvxbx__ldgn:
                raise BodoError(
                    'All parquet files must be in the same S3 bucket')
            fpath[nqqz__xnyac] = miyi__lzn.rstrip('/')
    else:
        sdi__rgx = urlparse(fpath)
        protocol = sdi__rgx.scheme
        fpath = fpath.rstrip('/')
    if protocol in {'gcs', 'gs'}:
        try:
            import gcsfs
        except ImportError as lvorf__dmu:
            uynta__zbwql = """Couldn't import gcsfs, which is required for Google cloud access. gcsfs can be installed by calling 'conda install -c conda-forge gcsfs'.
"""
            raise BodoError(uynta__zbwql)
    if protocol == 'http':
        try:
            import fsspec
        except ImportError as lvorf__dmu:
            uynta__zbwql = """Couldn't import fsspec, which is required for http access. fsspec can be installed by calling 'conda install -c conda-forge fsspec'.
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
            erd__hyz = gcsfs.GCSFileSystem(token=None)
            fs.append(erd__hyz)
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
                prefix = f'{protocol}://{sdi__rgx.netloc}'
                path = path[len(prefix):]
            qowln__omfl = fs.glob(path)
            if protocol == 's3':
                qowln__omfl = [('s3://' + miyi__lzn) for miyi__lzn in
                    qowln__omfl if not miyi__lzn.startswith('s3://')]
            elif protocol in {'hdfs', 'abfs', 'abfss'}:
                qowln__omfl = [(prefix + miyi__lzn) for miyi__lzn in
                    qowln__omfl]
        except:
            raise BodoError(
                f'glob pattern expansion not supported for {protocol}')
        if len(qowln__omfl) == 0:
            raise BodoError('No files found matching glob pattern')
        return qowln__omfl
    shjgf__mticy = False
    if get_row_counts:
        auw__zffn = getfs(parallel=True)
        shjgf__mticy = bodo.parquet_validate_schema
    if bodo.get_rank() == 0:
        jpmaq__cee = 1
        nwy__kfhfh = os.cpu_count()
        if nwy__kfhfh is not None and nwy__kfhfh > 1:
            jpmaq__cee = nwy__kfhfh // 2
        try:
            if get_row_counts:
                izw__qqic = tracing.Event('pq.ParquetDataset', is_parallel=
                    False)
                if tracing.is_tracing():
                    izw__qqic.add_attribute('dnf_filter', str(dnf_filters))
            euoct__mzl = pa.io_thread_count()
            pa.set_io_thread_count(jpmaq__cee)
            if '*' in fpath:
                fpath = glob(protocol, getfs(), fpath)
            if protocol == 's3':
                if isinstance(fpath, list):
                    get_legacy_fs().info(fpath[0])
                else:
                    get_legacy_fs().info(fpath)
            if protocol in {'hdfs', 'abfs', 'abfss'}:
                prefix = f'{protocol}://{sdi__rgx.netloc}'
                if isinstance(fpath, list):
                    vrv__vix = [miyi__lzn[len(prefix):] for miyi__lzn in fpath]
                else:
                    vrv__vix = fpath[len(prefix):]
            else:
                vrv__vix = fpath
            qkm__hdp = pq.ParquetDataset(vrv__vix, filesystem=get_legacy_fs
                (), filters=None, use_legacy_dataset=True, validate_schema=
                False, metadata_nthreads=jpmaq__cee)
            pa.set_io_thread_count(euoct__mzl)
            xtvzd__ssgj = bodo.io.pa_parquet.get_dataset_schema(qkm__hdp)
            if dnf_filters:
                if get_row_counts:
                    izw__qqic.add_attribute('num_pieces_before_filter', len
                        (qkm__hdp.pieces))
                qzsp__iya = time.time()
                qkm__hdp._filter(dnf_filters)
                if get_row_counts:
                    izw__qqic.add_attribute('dnf_filter_time', time.time() -
                        qzsp__iya)
                    izw__qqic.add_attribute('num_pieces_after_filter', len(
                        qkm__hdp.pieces))
            if get_row_counts:
                izw__qqic.finalize()
            qkm__hdp._metadata.fs = None
        except Exception as ngsxg__lnuub:
            uprl__tasse.bcast(ngsxg__lnuub)
            raise BodoError(
                f"""error from pyarrow: {type(ngsxg__lnuub).__name__}: {str(ngsxg__lnuub)}
"""
                )
        if get_row_counts:
            isan__gaf = tracing.Event('bcast dataset')
        uprl__tasse.bcast(qkm__hdp)
        uprl__tasse.bcast(xtvzd__ssgj)
    else:
        if get_row_counts:
            isan__gaf = tracing.Event('bcast dataset')
        qkm__hdp = uprl__tasse.bcast(None)
        if isinstance(qkm__hdp, Exception):
            cgyqd__kzlp = qkm__hdp
            raise BodoError(
                f"""error from pyarrow: {type(cgyqd__kzlp).__name__}: {str(cgyqd__kzlp)}
"""
                )
        xtvzd__ssgj = uprl__tasse.bcast(None)
    if get_row_counts:
        njyki__bku = getfs()
    else:
        njyki__bku = get_legacy_fs()
    qkm__hdp._metadata.fs = njyki__bku
    if get_row_counts:
        isan__gaf.finalize()
    qkm__hdp._bodo_total_rows = 0
    if get_row_counts and tot_rows_to_read == 0:
        get_row_counts = shjgf__mticy = False
        for neqhq__vevxv in qkm__hdp.pieces:
            neqhq__vevxv._bodo_num_rows = 0
    if get_row_counts or shjgf__mticy:
        if get_row_counts and tracing.is_tracing():
            zgatl__crviy = tracing.Event('get_row_counts')
            zgatl__crviy.add_attribute('g_num_pieces', len(qkm__hdp.pieces))
            zgatl__crviy.add_attribute('g_expr_filters', str(expr_filters))
        hhs__amq = 0.0
        num_pieces = len(qkm__hdp.pieces)
        start = get_start(num_pieces, bodo.get_size(), bodo.get_rank())
        bslaa__yoysl = get_end(num_pieces, bodo.get_size(), bodo.get_rank())
        tkjq__lgfmi = 0
        lsdkp__ojurw = 0
        quif__werbe = 0
        mkxs__zaptm = True
        if expr_filters is not None:
            import random
            random.seed(37)
            nnshj__rzeta = random.sample(qkm__hdp.pieces, k=len(qkm__hdp.
                pieces))
        else:
            nnshj__rzeta = qkm__hdp.pieces
        for neqhq__vevxv in nnshj__rzeta:
            neqhq__vevxv._bodo_num_rows = 0
        fpaths = [neqhq__vevxv.path for neqhq__vevxv in nnshj__rzeta[start:
            bslaa__yoysl]]
        if protocol == 's3':
            qvxbx__ldgn = sdi__rgx.netloc
            prefix = 's3://' + qvxbx__ldgn + '/'
            fpaths = [miyi__lzn[len(prefix):] for miyi__lzn in fpaths]
            njyki__bku = get_s3_subtree_fs(qvxbx__ldgn, region=getfs().
                region, storage_options=storage_options)
        else:
            njyki__bku = getfs()
        pa.set_io_thread_count(4)
        pa.set_cpu_count(4)
        qjt__emkd = ds.dataset(fpaths, filesystem=njyki__bku, partitioning=
            ds.partitioning(flavor='hive'))
        for cjfvx__lpaa, gqxwe__uedm in zip(nnshj__rzeta[start:bslaa__yoysl
            ], qjt__emkd.get_fragments()):
            qzsp__iya = time.time()
            ngklw__djaht = gqxwe__uedm.scanner(schema=qjt__emkd.schema,
                filter=expr_filters, use_threads=True).count_rows()
            hhs__amq += time.time() - qzsp__iya
            cjfvx__lpaa._bodo_num_rows = ngklw__djaht
            tkjq__lgfmi += ngklw__djaht
            lsdkp__ojurw += gqxwe__uedm.num_row_groups
            quif__werbe += sum(wdc__iayzd.total_byte_size for wdc__iayzd in
                gqxwe__uedm.row_groups)
            if shjgf__mticy:
                tuzko__xfpnz = gqxwe__uedm.metadata.schema.to_arrow_schema()
                if xtvzd__ssgj != tuzko__xfpnz:
                    print('Schema in {!s} was different. \n{!s}\n\nvs\n\n{!s}'
                        .format(cjfvx__lpaa, tuzko__xfpnz, xtvzd__ssgj))
                    mkxs__zaptm = False
                    break
        if shjgf__mticy:
            mkxs__zaptm = uprl__tasse.allreduce(mkxs__zaptm, op=MPI.LAND)
            if not mkxs__zaptm:
                raise BodoError("Schema in parquet files don't match")
        if get_row_counts:
            qkm__hdp._bodo_total_rows = uprl__tasse.allreduce(tkjq__lgfmi,
                op=MPI.SUM)
            fpy__xbu = uprl__tasse.allreduce(lsdkp__ojurw, op=MPI.SUM)
            tdgj__rtuu = uprl__tasse.allreduce(quif__werbe, op=MPI.SUM)
            rgnq__wobdv = np.array([neqhq__vevxv._bodo_num_rows for
                neqhq__vevxv in qkm__hdp.pieces])
            rgnq__wobdv = uprl__tasse.allreduce(rgnq__wobdv, op=MPI.SUM)
            for neqhq__vevxv, qam__jmmf in zip(qkm__hdp.pieces, rgnq__wobdv):
                neqhq__vevxv._bodo_num_rows = qam__jmmf
            if is_parallel and bodo.get_rank(
                ) == 0 and fpy__xbu < bodo.get_size() and fpy__xbu != 0:
                warnings.warn(BodoWarning(
                    f"""Total number of row groups in parquet dataset {fpath} ({fpy__xbu}) is too small for effective IO parallelization.
For best performance the number of row groups should be greater than the number of workers ({bodo.get_size()})
"""
                    ))
            if fpy__xbu == 0:
                brg__cvcww = 0
            else:
                brg__cvcww = tdgj__rtuu // fpy__xbu
            if (bodo.get_rank() == 0 and tdgj__rtuu >= 20 * 1048576 and 
                brg__cvcww < 1048576 and protocol in REMOTE_FILESYSTEMS):
                warnings.warn(BodoWarning(
                    f'Parquet average row group size is small ({brg__cvcww} bytes) and can have negative impact on performance when reading from remote sources'
                    ))
            if tracing.is_tracing():
                zgatl__crviy.add_attribute('g_total_num_row_groups', fpy__xbu)
                if expr_filters is not None:
                    zgatl__crviy.add_attribute('total_scan_time', hhs__amq)
                lvdbk__cieqo = np.array([neqhq__vevxv._bodo_num_rows for
                    neqhq__vevxv in qkm__hdp.pieces])
                gmm__wnmma = np.percentile(lvdbk__cieqo, [25, 50, 75])
                zgatl__crviy.add_attribute('g_row_counts_min', lvdbk__cieqo
                    .min())
                zgatl__crviy.add_attribute('g_row_counts_Q1', gmm__wnmma[0])
                zgatl__crviy.add_attribute('g_row_counts_median', gmm__wnmma[1]
                    )
                zgatl__crviy.add_attribute('g_row_counts_Q3', gmm__wnmma[2])
                zgatl__crviy.add_attribute('g_row_counts_max', lvdbk__cieqo
                    .max())
                zgatl__crviy.add_attribute('g_row_counts_mean',
                    lvdbk__cieqo.mean())
                zgatl__crviy.add_attribute('g_row_counts_std', lvdbk__cieqo
                    .std())
                zgatl__crviy.add_attribute('g_row_counts_sum', lvdbk__cieqo
                    .sum())
                zgatl__crviy.finalize()
    qkm__hdp._prefix = ''
    if protocol in {'hdfs', 'abfs', 'abfss'}:
        prefix = f'{protocol}://{sdi__rgx.netloc}'
        if len(qkm__hdp.pieces) > 0:
            cjfvx__lpaa = qkm__hdp.pieces[0]
            if not cjfvx__lpaa.path.startswith(prefix):
                qkm__hdp._prefix = prefix
    if read_categories:
        _add_categories_to_pq_dataset(qkm__hdp)
    if get_row_counts:
        pbo__oyc.finalize()
    return qkm__hdp


def get_scanner_batches(fpaths, expr_filters, selected_fields,
    avg_num_pieces, is_parallel, storage_options, region, prefix,
    str_as_dict_cols, start_offset, rows_to_read):
    import pyarrow as pa
    nwy__kfhfh = os.cpu_count()
    if nwy__kfhfh is None or nwy__kfhfh == 0:
        nwy__kfhfh = 2
    efp__cskl = min(4, nwy__kfhfh)
    gpk__icxof = min(16, nwy__kfhfh)
    if is_parallel and len(fpaths) > gpk__icxof and len(fpaths
        ) / avg_num_pieces >= 2.0:
        pa.set_io_thread_count(gpk__icxof)
        pa.set_cpu_count(gpk__icxof)
    else:
        pa.set_io_thread_count(efp__cskl)
        pa.set_cpu_count(efp__cskl)
    if fpaths[0].startswith('s3://'):
        qvxbx__ldgn = urlparse(fpaths[0]).netloc
        prefix = 's3://' + qvxbx__ldgn + '/'
        fpaths = [miyi__lzn[len(prefix):] for miyi__lzn in fpaths]
        njyki__bku = get_s3_subtree_fs(qvxbx__ldgn, region=region,
            storage_options=storage_options)
    elif prefix and prefix.startswith(('hdfs', 'abfs', 'abfss')):
        njyki__bku = get_hdfs_fs(prefix + fpaths[0])
    elif fpaths[0].startswith(('gcs', 'gs')):
        import gcsfs
        njyki__bku = gcsfs.GCSFileSystem(token=None)
    else:
        njyki__bku = None
    riz__blx = ds.ParquetFileFormat(dictionary_columns=str_as_dict_cols)
    qkm__hdp = ds.dataset(fpaths, filesystem=njyki__bku, partitioning=ds.
        partitioning(flavor='hive'), format=riz__blx)
    col_names = qkm__hdp.schema.names
    jsoyq__vck = [col_names[akg__xhmbe] for akg__xhmbe in selected_fields]
    oduyj__lpqzx = len(fpaths) <= 3 or start_offset > 0 and len(fpaths) <= 10
    if oduyj__lpqzx and expr_filters is None:
        cbcvq__ogls = []
        vlbev__pio = 0
        cvm__yuv = 0
        for gqxwe__uedm in qkm__hdp.get_fragments():
            fyh__yyk = []
            for wdc__iayzd in gqxwe__uedm.row_groups:
                erid__oqj = wdc__iayzd.num_rows
                if start_offset < vlbev__pio + erid__oqj:
                    if cvm__yuv == 0:
                        wgq__ijy = start_offset - vlbev__pio
                        xxt__dqfop = min(erid__oqj - wgq__ijy, rows_to_read)
                    else:
                        xxt__dqfop = min(erid__oqj, rows_to_read - cvm__yuv)
                    cvm__yuv += xxt__dqfop
                    fyh__yyk.append(wdc__iayzd.id)
                vlbev__pio += erid__oqj
                if cvm__yuv == rows_to_read:
                    break
            cbcvq__ogls.append(gqxwe__uedm.subset(row_group_ids=fyh__yyk))
            if cvm__yuv == rows_to_read:
                break
        qkm__hdp = ds.FileSystemDataset(cbcvq__ogls, qkm__hdp.schema,
            riz__blx, filesystem=qkm__hdp.filesystem)
        start_offset = wgq__ijy
    xlfl__twgwi = qkm__hdp.scanner(columns=jsoyq__vck, filter=expr_filters,
        use_threads=True).to_reader()
    return qkm__hdp, xlfl__twgwi, start_offset


def _add_categories_to_pq_dataset(pq_dataset):
    import pyarrow as pa
    from mpi4py import MPI
    if len(pq_dataset.pieces) < 1:
        raise BodoError(
            'No pieces found in Parquet dataset. Cannot get read categorical values'
            )
    pa_schema = pq_dataset.schema.to_arrow_schema()
    ogvtj__xvlp = [c for c in pa_schema.names if isinstance(pa_schema.field
        (c).type, pa.DictionaryType)]
    if len(ogvtj__xvlp) == 0:
        pq_dataset._category_info = {}
        return
    uprl__tasse = MPI.COMM_WORLD
    if bodo.get_rank() == 0:
        try:
            xezpb__xzw = pq_dataset.pieces[0].open()
            wdc__iayzd = xezpb__xzw.read_row_group(0, ogvtj__xvlp)
            category_info = {c: tuple(wdc__iayzd.column(c).chunk(0).
                dictionary.to_pylist()) for c in ogvtj__xvlp}
            del xezpb__xzw, wdc__iayzd
        except Exception as ngsxg__lnuub:
            uprl__tasse.bcast(ngsxg__lnuub)
            raise ngsxg__lnuub
        uprl__tasse.bcast(category_info)
    else:
        category_info = uprl__tasse.bcast(None)
        if isinstance(category_info, Exception):
            cgyqd__kzlp = category_info
            raise cgyqd__kzlp
    pq_dataset._category_info = category_info


def get_pandas_metadata(schema, num_pieces):
    xmd__gchyi = None
    nullable_from_metadata = defaultdict(lambda : None)
    ahu__qau = b'pandas'
    if schema.metadata is not None and ahu__qau in schema.metadata:
        import json
        qua__khe = json.loads(schema.metadata[ahu__qau].decode('utf8'))
        cusfp__dwkbu = len(qua__khe['index_columns'])
        if cusfp__dwkbu > 1:
            raise BodoError('read_parquet: MultiIndex not supported yet')
        xmd__gchyi = qua__khe['index_columns'][0] if cusfp__dwkbu else None
        if not isinstance(xmd__gchyi, str) and (not isinstance(xmd__gchyi,
            dict) or num_pieces != 1):
            xmd__gchyi = None
        for hyq__fdv in qua__khe['columns']:
            tuybh__lfh = hyq__fdv['name']
            if hyq__fdv['pandas_type'].startswith('int'
                ) and tuybh__lfh is not None:
                if hyq__fdv['numpy_type'].startswith('Int'):
                    nullable_from_metadata[tuybh__lfh] = True
                else:
                    nullable_from_metadata[tuybh__lfh] = False
    return xmd__gchyi, nullable_from_metadata


def determine_str_as_dict_columns(pq_dataset, pa_schema):
    from mpi4py import MPI
    uprl__tasse = MPI.COMM_WORLD
    uata__ave = []
    for tuybh__lfh in pa_schema.names:
        gqqa__txo = pa_schema.field(tuybh__lfh)
        if gqqa__txo.type == pa.string():
            uata__ave.append((tuybh__lfh, pa_schema.get_field_index(
                tuybh__lfh)))
    if len(uata__ave) == 0:
        return set()
    if len(pq_dataset.pieces) > bodo.get_size():
        import random
        random.seed(37)
        nnshj__rzeta = random.sample(pq_dataset.pieces, bodo.get_size())
    else:
        nnshj__rzeta = pq_dataset.pieces
    yes__qnu = np.zeros(len(uata__ave), dtype=np.int64)
    otvco__pjsaw = np.zeros(len(uata__ave), dtype=np.int64)
    if bodo.get_rank() < len(nnshj__rzeta):
        cjfvx__lpaa = nnshj__rzeta[bodo.get_rank()]
        fuja__dfgqu = cjfvx__lpaa.get_metadata()
        for nqqz__xnyac in range(fuja__dfgqu.num_row_groups):
            for obqp__dqqae, (auw__zffn, whbs__syjw) in enumerate(uata__ave):
                yes__qnu[obqp__dqqae] += fuja__dfgqu.row_group(nqqz__xnyac
                    ).column(whbs__syjw).total_uncompressed_size
        xshp__jjpiz = fuja__dfgqu.num_rows
    else:
        xshp__jjpiz = 0
    odk__dvq = uprl__tasse.allreduce(xshp__jjpiz, op=MPI.SUM)
    if odk__dvq == 0:
        return set()
    uprl__tasse.Allreduce(yes__qnu, otvco__pjsaw, op=MPI.SUM)
    kyngb__odnmx = otvco__pjsaw / odk__dvq
    str_as_dict = set()
    for nqqz__xnyac, brmf__utt in enumerate(kyngb__odnmx):
        if brmf__utt < READ_STR_AS_DICT_THRESHOLD:
            tuybh__lfh = uata__ave[nqqz__xnyac][0]
            str_as_dict.add(tuybh__lfh)
    return str_as_dict


def parquet_file_schema(file_name, selected_columns, storage_options=None,
    input_file_name_col=None):
    col_names = []
    sdt__eobp = []
    pq_dataset = get_parquet_dataset(file_name, get_row_counts=False,
        storage_options=storage_options, read_categories=True)
    partition_names = [] if pq_dataset.partitions is None else [pq_dataset.
        partitions.levels[nqqz__xnyac].name for nqqz__xnyac in range(len(
        pq_dataset.partitions.partition_names))]
    pa_schema = pq_dataset.schema.to_arrow_schema()
    num_pieces = len(pq_dataset.pieces)
    str_as_dict = determine_str_as_dict_columns(pq_dataset, pa_schema)
    col_names = pa_schema.names
    xmd__gchyi, nullable_from_metadata = get_pandas_metadata(pa_schema,
        num_pieces)
    wvzwr__lbaq = []
    vhuo__zixiz = []
    bhov__pfm = []
    for nqqz__xnyac, c in enumerate(col_names):
        gqqa__txo = pa_schema.field(c)
        buvr__byt, aiab__fskpx = _get_numba_typ_from_pa_typ(gqqa__txo, c ==
            xmd__gchyi, nullable_from_metadata[c], pq_dataset.
            _category_info, str_as_dict=c in str_as_dict)
        wvzwr__lbaq.append(buvr__byt)
        vhuo__zixiz.append(aiab__fskpx)
        bhov__pfm.append(gqqa__txo.type)
    if partition_names:
        col_names += partition_names
        wvzwr__lbaq += [_get_partition_cat_dtype(pq_dataset.partitions.
            levels[nqqz__xnyac]) for nqqz__xnyac in range(len(partition_names))
            ]
        vhuo__zixiz.extend([True] * len(partition_names))
        bhov__pfm.extend([None] * len(partition_names))
    if input_file_name_col is not None:
        col_names += [input_file_name_col]
        wvzwr__lbaq += [dict_str_arr_type]
        vhuo__zixiz.append(True)
        bhov__pfm.append(None)
    yjfkt__kgx = {c: nqqz__xnyac for nqqz__xnyac, c in enumerate(col_names)}
    if selected_columns is None:
        selected_columns = col_names
    for c in selected_columns:
        if c not in yjfkt__kgx:
            raise BodoError(f'Selected column {c} not in Parquet file schema')
    if xmd__gchyi and not isinstance(xmd__gchyi, dict
        ) and xmd__gchyi not in selected_columns:
        selected_columns.append(xmd__gchyi)
    col_names = selected_columns
    col_indices = []
    sdt__eobp = []
    acn__gkdnd = []
    ywwap__xkxq = []
    for nqqz__xnyac, c in enumerate(col_names):
        tvkkn__jzvxj = yjfkt__kgx[c]
        col_indices.append(tvkkn__jzvxj)
        sdt__eobp.append(wvzwr__lbaq[tvkkn__jzvxj])
        if not vhuo__zixiz[tvkkn__jzvxj]:
            acn__gkdnd.append(nqqz__xnyac)
            ywwap__xkxq.append(bhov__pfm[tvkkn__jzvxj])
    return (col_names, sdt__eobp, xmd__gchyi, col_indices, partition_names,
        acn__gkdnd, ywwap__xkxq)


def _get_partition_cat_dtype(part_set):
    bnlka__lbt = part_set.dictionary.to_pandas()
    wki__pwl = bodo.typeof(bnlka__lbt).dtype
    hpyt__bpsxh = PDCategoricalDtype(tuple(bnlka__lbt), wki__pwl, False)
    return CategoricalArrayType(hpyt__bpsxh)


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
        zatu__ceaoj = lir.FunctionType(lir.VoidType(), [lir.IntType(8).
            as_pointer(), lir.IntType(8).as_pointer(), lir.IntType(8).
            as_pointer(), lir.IntType(8).as_pointer(), lir.IntType(1), lir.
            IntType(8).as_pointer(), lir.IntType(8).as_pointer(), lir.
            IntType(1), lir.IntType(1), lir.IntType(32), lir.IntType(32),
            lir.IntType(32), lir.IntType(8).as_pointer(), lir.IntType(8).
            as_pointer()])
        xuec__dyx = cgutils.get_or_insert_function(builder.module,
            zatu__ceaoj, name='pq_write')
        builder.call(xuec__dyx, args)
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
        zatu__ceaoj = lir.FunctionType(lir.VoidType(), [lir.IntType(8).
            as_pointer(), lir.IntType(8).as_pointer(), lir.IntType(8).
            as_pointer(), lir.IntType(8).as_pointer(), lir.IntType(8).
            as_pointer(), lir.IntType(8).as_pointer(), lir.IntType(32), lir
            .IntType(8).as_pointer(), lir.IntType(1), lir.IntType(8).
            as_pointer()])
        xuec__dyx = cgutils.get_or_insert_function(builder.module,
            zatu__ceaoj, name='pq_write_partitioned')
        builder.call(xuec__dyx, args)
        bodo.utils.utils.inlined_check_and_propagate_cpp_exception(context,
            builder)
    return types.void(types.voidptr, data_table_t, col_names_t,
        col_names_no_partitions_t, cat_table_t, types.voidptr, types.int32,
        types.voidptr, types.boolean, types.voidptr), codegen
