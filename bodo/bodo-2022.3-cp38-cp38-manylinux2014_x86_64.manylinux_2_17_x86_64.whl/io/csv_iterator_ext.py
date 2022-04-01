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
        pzyl__qjr = (
            f'CSVIteratorType({df_type}, {out_colnames}, {out_types}, {usecols}, {sep}, {index_ind}, {index_arr_typ}, {index_name}, {escapechar})'
            )
        super(types.SimpleIteratorType, self).__init__(pzyl__qjr)
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
        epdf__xtdnq = [('csv_reader', bodo.ir.connector.stream_reader_type),
            ('index', types.EphemeralPointer(types.uintp))]
        super(CSVIteratorModel, self).__init__(dmm, fe_type, epdf__xtdnq)


@lower_builtin('getiter', CSVIteratorType)
def getiter_csv_iterator(context, builder, sig, args):
    zxo__cbzvz = cgutils.create_struct_proxy(sig.args[0])(context, builder,
        value=args[0])
    gnw__cihqf = lir.FunctionType(lir.VoidType(), [lir.IntType(8).as_pointer()]
        )
    hcb__xcgjp = cgutils.get_or_insert_function(builder.module, gnw__cihqf,
        name='initialize_csv_reader')
    builder.call(hcb__xcgjp, [zxo__cbzvz.csv_reader])
    builder.store(context.get_constant(types.uint64, 0), zxo__cbzvz.index)
    return impl_ret_borrowed(context, builder, sig.return_type, args[0])


@lower_builtin('iternext', CSVIteratorType)
@iternext_impl(RefType.NEW)
def iternext_csv_iterator(context, builder, sig, args, result):
    [axxqz__pwnjh] = sig.args
    [wtrq__kdn] = args
    zxo__cbzvz = cgutils.create_struct_proxy(axxqz__pwnjh)(context, builder,
        value=wtrq__kdn)
    gnw__cihqf = lir.FunctionType(lir.IntType(1), [lir.IntType(8).as_pointer()]
        )
    hcb__xcgjp = cgutils.get_or_insert_function(builder.module, gnw__cihqf,
        name='update_csv_reader')
    gkh__iqsh = builder.call(hcb__xcgjp, [zxo__cbzvz.csv_reader])
    result.set_valid(gkh__iqsh)
    with builder.if_then(gkh__iqsh):
        hvlh__nils = builder.load(zxo__cbzvz.index)
        zajy__qihaf = types.Tuple([sig.return_type.first_type, types.int64])
        lujj__hnd = gen_read_csv_objmode(sig.args[0])
        teqip__xmi = signature(zajy__qihaf, bodo.ir.connector.
            stream_reader_type, types.int64)
        alc__lbca = context.compile_internal(builder, lujj__hnd, teqip__xmi,
            [zxo__cbzvz.csv_reader, hvlh__nils])
        sqgyk__phtd, ymh__lqmhu = cgutils.unpack_tuple(builder, alc__lbca)
        ixr__bpyul = builder.add(hvlh__nils, ymh__lqmhu, flags=['nsw'])
        builder.store(ixr__bpyul, zxo__cbzvz.index)
        result.yield_(sqgyk__phtd)


@intrinsic
def init_csv_iterator(typingctx, csv_reader, csv_iterator_typeref):

    def codegen(context, builder, signature, args):
        uxdgb__rjo = cgutils.create_struct_proxy(signature.return_type)(context
            , builder)
        uxdgb__rjo.csv_reader = args[0]
        afkjs__asb = context.get_constant(types.uintp, 0)
        uxdgb__rjo.index = cgutils.alloca_once_value(builder, afkjs__asb)
        return uxdgb__rjo._getvalue()
    assert isinstance(csv_iterator_typeref, types.TypeRef
        ), 'Initializing a csv iterator requires a typeref'
    txccr__gux = csv_iterator_typeref.instance_type
    sig = signature(txccr__gux, csv_reader, csv_iterator_typeref)
    return sig, codegen


def gen_read_csv_objmode(csv_iterator_type):
    yqxc__dcvr = 'def read_csv_objmode(f_reader):\n'
    gib__ksfm = [sanitize_varname(ueq__uvvuc) for ueq__uvvuc in
        csv_iterator_type._out_colnames]
    wplok__zhwut = ir_utils.next_label()
    aie__dlbv = globals()
    out_types = csv_iterator_type._out_types
    aie__dlbv[f'table_type_{wplok__zhwut}'] = TableType(tuple(out_types))
    aie__dlbv[f'idx_array_typ'] = csv_iterator_type._index_arr_typ
    rawk__zxn = list(range(len(csv_iterator_type._usecols)))
    yqxc__dcvr += _gen_read_csv_objmode(csv_iterator_type._out_colnames,
        gib__ksfm, out_types, csv_iterator_type._usecols, rawk__zxn,
        csv_iterator_type._sep, csv_iterator_type._escapechar, wplok__zhwut,
        aie__dlbv, parallel=False, check_parallel_runtime=True,
        idx_col_index=csv_iterator_type._index_ind, idx_col_typ=
        csv_iterator_type._index_arr_typ)
    xca__qnu = bodo.ir.csv_ext._gen_parallel_flag_name(gib__ksfm)
    qmka__gumn = ['T'] + (['idx_arr'] if csv_iterator_type._index_ind is not
        None else []) + [xca__qnu]
    yqxc__dcvr += f"  return {', '.join(qmka__gumn)}"
    aie__dlbv = globals()
    adyuq__twew = {}
    exec(yqxc__dcvr, aie__dlbv, adyuq__twew)
    dnq__ctk = adyuq__twew['read_csv_objmode']
    ypqsf__ozy = numba.njit(dnq__ctk)
    bodo.ir.csv_ext.compiled_funcs.append(ypqsf__ozy)
    ekk__wxxe = 'def read_func(reader, local_start):\n'
    ekk__wxxe += f"  {', '.join(qmka__gumn)} = objmode_func(reader)\n"
    index_ind = csv_iterator_type._index_ind
    if index_ind is None:
        ekk__wxxe += f'  local_len = len(T)\n'
        ekk__wxxe += '  total_size = local_len\n'
        ekk__wxxe += f'  if ({xca__qnu}):\n'
        ekk__wxxe += """    local_start = local_start + bodo.libs.distributed_api.dist_exscan(local_len, _op)
"""
        ekk__wxxe += (
            '    total_size = bodo.libs.distributed_api.dist_reduce(local_len, _op)\n'
            )
        tsl__awx = (
            f'bodo.hiframes.pd_index_ext.init_range_index(local_start, local_start + local_len, 1, None)'
            )
    else:
        ekk__wxxe += '  total_size = 0\n'
        tsl__awx = (
            f'bodo.utils.conversion.convert_to_index({qmka__gumn[1]}, {csv_iterator_type._index_name!r})'
            )
    ekk__wxxe += f"""  return (bodo.hiframes.pd_dataframe_ext.init_dataframe(({qmka__gumn[0]},), {tsl__awx}, out_df_typ), total_size)
"""
    exec(ekk__wxxe, {'bodo': bodo, 'objmode_func': ypqsf__ozy, '_op': np.
        int32(bodo.libs.distributed_api.Reduce_Type.Sum.value),
        'out_df_typ': csv_iterator_type.yield_type}, adyuq__twew)
    return adyuq__twew['read_func']
