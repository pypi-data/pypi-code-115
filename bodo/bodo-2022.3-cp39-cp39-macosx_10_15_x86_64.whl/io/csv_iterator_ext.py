"""
Class information for DataFrame iterators returned by pd.read_csv. This is used
to handle situations in which pd.read_csv is used to return chunks with separate
read calls instead of just a single read.
"""
import llvmlite.binding as ll
import numba
import numpy as np
import pandas as pd
from llvmlite import ir as lir
from numba.core import cgutils, ir_utils, types
from numba.core.imputils import RefType, impl_ret_borrowed, iternext_impl
from numba.core.typing.templates import signature
from numba.extending import intrinsic, lower_builtin, models, register_model
import bodo
import bodo.ir.connector
import bodo.ir.csv_ext
from bodo import objmode
from bodo.hiframes.pd_dataframe_ext import DataFrameType
from bodo.hiframes.table import Table, TableType
from bodo.io import csv_cpp
from bodo.ir.csv_ext import _gen_read_csv_objmode, astype
from bodo.utils.utils import check_java_installation
from bodo.utils.utils import sanitize_varname
ll.add_symbol('update_csv_reader', csv_cpp.update_csv_reader)
ll.add_symbol('initialize_csv_reader', csv_cpp.initialize_csv_reader)


class CSVIteratorType(types.SimpleIteratorType):

    def __init__(self, df_type, out_colnames, out_types, usecols, sep,
        index_ind, index_arr_typ, index_name, escapechar):
        assert isinstance(df_type, DataFrameType
            ), 'CSVIterator must return a DataFrame'
        lct__blhyb = (
            f'CSVIteratorType({df_type}, {out_colnames}, {out_types}, {usecols}, {sep}, {index_ind}, {index_arr_typ}, {index_name}, {escapechar})'
            )
        super(types.SimpleIteratorType, self).__init__(lct__blhyb)
        self._yield_type = df_type
        self._out_colnames = out_colnames
        self._out_types = out_types
        self._usecols = usecols
        self._sep = sep
        self._index_ind = index_ind
        self._index_arr_typ = index_arr_typ
        self._index_name = index_name
        self._escapechar = escapechar

    @property
    def mangling_args(self):
        return self.__class__.__name__, (self._code,)


@register_model(CSVIteratorType)
class CSVIteratorModel(models.StructModel):

    def __init__(self, dmm, fe_type):
        pew__lxk = [('csv_reader', bodo.ir.connector.stream_reader_type), (
            'index', types.EphemeralPointer(types.uintp))]
        super(CSVIteratorModel, self).__init__(dmm, fe_type, pew__lxk)


@lower_builtin('getiter', CSVIteratorType)
def getiter_csv_iterator(context, builder, sig, args):
    yaxy__rod = cgutils.create_struct_proxy(sig.args[0])(context, builder,
        value=args[0])
    xcnbe__hhbfh = lir.FunctionType(lir.VoidType(), [lir.IntType(8).
        as_pointer()])
    tbwbu__cxyte = cgutils.get_or_insert_function(builder.module,
        xcnbe__hhbfh, name='initialize_csv_reader')
    builder.call(tbwbu__cxyte, [yaxy__rod.csv_reader])
    builder.store(context.get_constant(types.uint64, 0), yaxy__rod.index)
    return impl_ret_borrowed(context, builder, sig.return_type, args[0])


@lower_builtin('iternext', CSVIteratorType)
@iternext_impl(RefType.NEW)
def iternext_csv_iterator(context, builder, sig, args, result):
    [ywsq__rvji] = sig.args
    [nivxg__squw] = args
    yaxy__rod = cgutils.create_struct_proxy(ywsq__rvji)(context, builder,
        value=nivxg__squw)
    xcnbe__hhbfh = lir.FunctionType(lir.IntType(1), [lir.IntType(8).
        as_pointer()])
    tbwbu__cxyte = cgutils.get_or_insert_function(builder.module,
        xcnbe__hhbfh, name='update_csv_reader')
    fpww__adlv = builder.call(tbwbu__cxyte, [yaxy__rod.csv_reader])
    result.set_valid(fpww__adlv)
    with builder.if_then(fpww__adlv):
        ihb__olwzt = builder.load(yaxy__rod.index)
        wyu__uwcnk = types.Tuple([sig.return_type.first_type, types.int64])
        uhils__ntzq = gen_read_csv_objmode(sig.args[0])
        uwca__amgv = signature(wyu__uwcnk, bodo.ir.connector.
            stream_reader_type, types.int64)
        cjozc__eozz = context.compile_internal(builder, uhils__ntzq,
            uwca__amgv, [yaxy__rod.csv_reader, ihb__olwzt])
        nagf__tsb, abm__zwp = cgutils.unpack_tuple(builder, cjozc__eozz)
        cqx__cksg = builder.add(ihb__olwzt, abm__zwp, flags=['nsw'])
        builder.store(cqx__cksg, yaxy__rod.index)
        result.yield_(nagf__tsb)


@intrinsic
def init_csv_iterator(typingctx, csv_reader, csv_iterator_typeref):

    def codegen(context, builder, signature, args):
        bbv__afdi = cgutils.create_struct_proxy(signature.return_type)(context,
            builder)
        bbv__afdi.csv_reader = args[0]
        dsi__tjsh = context.get_constant(types.uintp, 0)
        bbv__afdi.index = cgutils.alloca_once_value(builder, dsi__tjsh)
        return bbv__afdi._getvalue()
    assert isinstance(csv_iterator_typeref, types.TypeRef
        ), 'Initializing a csv iterator requires a typeref'
    dlvss__qqy = csv_iterator_typeref.instance_type
    sig = signature(dlvss__qqy, csv_reader, csv_iterator_typeref)
    return sig, codegen


def gen_read_csv_objmode(csv_iterator_type):
    yhoup__llgy = 'def read_csv_objmode(f_reader):\n'
    muax__byq = [sanitize_varname(llmp__fwql) for llmp__fwql in
        csv_iterator_type._out_colnames]
    zlt__xax = ir_utils.next_label()
    nkt__vcbki = globals()
    out_types = csv_iterator_type._out_types
    nkt__vcbki[f'table_type_{zlt__xax}'] = TableType(tuple(out_types))
    nkt__vcbki[f'idx_array_typ'] = csv_iterator_type._index_arr_typ
    jxr__blzek = list(range(len(csv_iterator_type._usecols)))
    yhoup__llgy += _gen_read_csv_objmode(csv_iterator_type._out_colnames,
        muax__byq, out_types, csv_iterator_type._usecols, jxr__blzek,
        csv_iterator_type._sep, csv_iterator_type._escapechar, zlt__xax,
        nkt__vcbki, parallel=False, check_parallel_runtime=True,
        idx_col_index=csv_iterator_type._index_ind, idx_col_typ=
        csv_iterator_type._index_arr_typ)
    fhtle__ixl = bodo.ir.csv_ext._gen_parallel_flag_name(muax__byq)
    jzjz__sxo = ['T'] + (['idx_arr'] if csv_iterator_type._index_ind is not
        None else []) + [fhtle__ixl]
    yhoup__llgy += f"  return {', '.join(jzjz__sxo)}"
    nkt__vcbki = globals()
    lprh__avcd = {}
    exec(yhoup__llgy, nkt__vcbki, lprh__avcd)
    obl__uclcf = lprh__avcd['read_csv_objmode']
    hsoy__opn = numba.njit(obl__uclcf)
    bodo.ir.csv_ext.compiled_funcs.append(hsoy__opn)
    rslh__vuck = 'def read_func(reader, local_start):\n'
    rslh__vuck += f"  {', '.join(jzjz__sxo)} = objmode_func(reader)\n"
    index_ind = csv_iterator_type._index_ind
    if index_ind is None:
        rslh__vuck += f'  local_len = len(T)\n'
        rslh__vuck += '  total_size = local_len\n'
        rslh__vuck += f'  if ({fhtle__ixl}):\n'
        rslh__vuck += """    local_start = local_start + bodo.libs.distributed_api.dist_exscan(local_len, _op)
"""
        rslh__vuck += (
            '    total_size = bodo.libs.distributed_api.dist_reduce(local_len, _op)\n'
            )
        avf__ertw = (
            f'bodo.hiframes.pd_index_ext.init_range_index(local_start, local_start + local_len, 1, None)'
            )
    else:
        rslh__vuck += '  total_size = 0\n'
        avf__ertw = (
            f'bodo.utils.conversion.convert_to_index({jzjz__sxo[1]}, {csv_iterator_type._index_name!r})'
            )
    rslh__vuck += f"""  return (bodo.hiframes.pd_dataframe_ext.init_dataframe(({jzjz__sxo[0]},), {avf__ertw}, out_df_typ), total_size)
"""
    exec(rslh__vuck, {'bodo': bodo, 'objmode_func': hsoy__opn, '_op': np.
        int32(bodo.libs.distributed_api.Reduce_Type.Sum.value),
        'out_df_typ': csv_iterator_type.yield_type}, lprh__avcd)
    return lprh__avcd['read_func']
