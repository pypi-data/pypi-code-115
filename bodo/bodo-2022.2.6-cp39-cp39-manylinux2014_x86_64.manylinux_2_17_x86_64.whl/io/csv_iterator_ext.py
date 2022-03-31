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
        wirs__nkbqk = (
            f'CSVIteratorType({df_type}, {out_colnames}, {out_types}, {usecols}, {sep}, {index_ind}, {index_arr_typ}, {index_name}, {escapechar})'
            )
        super(types.SimpleIteratorType, self).__init__(wirs__nkbqk)
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
        wqgr__lols = [('csv_reader', bodo.ir.connector.stream_reader_type),
            ('index', types.EphemeralPointer(types.uintp))]
        super(CSVIteratorModel, self).__init__(dmm, fe_type, wqgr__lols)


@lower_builtin('getiter', CSVIteratorType)
def getiter_csv_iterator(context, builder, sig, args):
    yjcth__tjtf = cgutils.create_struct_proxy(sig.args[0])(context, builder,
        value=args[0])
    zxush__jtb = lir.FunctionType(lir.VoidType(), [lir.IntType(8).as_pointer()]
        )
    pczb__bfbpr = cgutils.get_or_insert_function(builder.module, zxush__jtb,
        name='initialize_csv_reader')
    builder.call(pczb__bfbpr, [yjcth__tjtf.csv_reader])
    builder.store(context.get_constant(types.uint64, 0), yjcth__tjtf.index)
    return impl_ret_borrowed(context, builder, sig.return_type, args[0])


@lower_builtin('iternext', CSVIteratorType)
@iternext_impl(RefType.NEW)
def iternext_csv_iterator(context, builder, sig, args, result):
    [fur__eoy] = sig.args
    [xylv__roguc] = args
    yjcth__tjtf = cgutils.create_struct_proxy(fur__eoy)(context, builder,
        value=xylv__roguc)
    zxush__jtb = lir.FunctionType(lir.IntType(1), [lir.IntType(8).as_pointer()]
        )
    pczb__bfbpr = cgutils.get_or_insert_function(builder.module, zxush__jtb,
        name='update_csv_reader')
    qayyi__napi = builder.call(pczb__bfbpr, [yjcth__tjtf.csv_reader])
    result.set_valid(qayyi__napi)
    with builder.if_then(qayyi__napi):
        mze__bhad = builder.load(yjcth__tjtf.index)
        tjfz__wsk = types.Tuple([sig.return_type.first_type, types.int64])
        xydr__auqj = gen_read_csv_objmode(sig.args[0])
        ftxb__zvjux = signature(tjfz__wsk, bodo.ir.connector.
            stream_reader_type, types.int64)
        dlbc__wrp = context.compile_internal(builder, xydr__auqj,
            ftxb__zvjux, [yjcth__tjtf.csv_reader, mze__bhad])
        gtc__dym, lfgei__qleli = cgutils.unpack_tuple(builder, dlbc__wrp)
        pbguy__auy = builder.add(mze__bhad, lfgei__qleli, flags=['nsw'])
        builder.store(pbguy__auy, yjcth__tjtf.index)
        result.yield_(gtc__dym)


@intrinsic
def init_csv_iterator(typingctx, csv_reader, csv_iterator_typeref):

    def codegen(context, builder, signature, args):
        zrfc__kikfg = cgutils.create_struct_proxy(signature.return_type)(
            context, builder)
        zrfc__kikfg.csv_reader = args[0]
        uxpo__cae = context.get_constant(types.uintp, 0)
        zrfc__kikfg.index = cgutils.alloca_once_value(builder, uxpo__cae)
        return zrfc__kikfg._getvalue()
    assert isinstance(csv_iterator_typeref, types.TypeRef
        ), 'Initializing a csv iterator requires a typeref'
    aroj__mqv = csv_iterator_typeref.instance_type
    sig = signature(aroj__mqv, csv_reader, csv_iterator_typeref)
    return sig, codegen


def gen_read_csv_objmode(csv_iterator_type):
    xlvwr__rvg = 'def read_csv_objmode(f_reader):\n'
    rmebu__svyfm = [sanitize_varname(laual__lkm) for laual__lkm in
        csv_iterator_type._out_colnames]
    zwd__goz = ir_utils.next_label()
    lnotr__enpys = globals()
    out_types = csv_iterator_type._out_types
    lnotr__enpys[f'table_type_{zwd__goz}'] = TableType(tuple(out_types))
    lnotr__enpys[f'idx_array_typ'] = csv_iterator_type._index_arr_typ
    vdj__hvg = list(range(len(csv_iterator_type._usecols)))
    xlvwr__rvg += _gen_read_csv_objmode(csv_iterator_type._out_colnames,
        rmebu__svyfm, out_types, csv_iterator_type._usecols, vdj__hvg,
        csv_iterator_type._sep, csv_iterator_type._escapechar, zwd__goz,
        lnotr__enpys, parallel=False, check_parallel_runtime=True,
        idx_col_index=csv_iterator_type._index_ind, idx_col_typ=
        csv_iterator_type._index_arr_typ)
    bczsk__mkcuu = bodo.ir.csv_ext._gen_parallel_flag_name(rmebu__svyfm)
    njc__fshtl = ['T'] + (['idx_arr'] if csv_iterator_type._index_ind is not
        None else []) + [bczsk__mkcuu]
    xlvwr__rvg += f"  return {', '.join(njc__fshtl)}"
    lnotr__enpys = globals()
    vkh__mwcyp = {}
    exec(xlvwr__rvg, lnotr__enpys, vkh__mwcyp)
    ltgt__ecta = vkh__mwcyp['read_csv_objmode']
    jju__bov = numba.njit(ltgt__ecta)
    bodo.ir.csv_ext.compiled_funcs.append(jju__bov)
    fgi__viza = 'def read_func(reader, local_start):\n'
    fgi__viza += f"  {', '.join(njc__fshtl)} = objmode_func(reader)\n"
    index_ind = csv_iterator_type._index_ind
    if index_ind is None:
        fgi__viza += f'  local_len = len(T)\n'
        fgi__viza += '  total_size = local_len\n'
        fgi__viza += f'  if ({bczsk__mkcuu}):\n'
        fgi__viza += """    local_start = local_start + bodo.libs.distributed_api.dist_exscan(local_len, _op)
"""
        fgi__viza += (
            '    total_size = bodo.libs.distributed_api.dist_reduce(local_len, _op)\n'
            )
        bdjlx__qbm = (
            f'bodo.hiframes.pd_index_ext.init_range_index(local_start, local_start + local_len, 1, None)'
            )
    else:
        fgi__viza += '  total_size = 0\n'
        bdjlx__qbm = (
            f'bodo.utils.conversion.convert_to_index({njc__fshtl[1]}, {csv_iterator_type._index_name!r})'
            )
    fgi__viza += f"""  return (bodo.hiframes.pd_dataframe_ext.init_dataframe(({njc__fshtl[0]},), {bdjlx__qbm}, out_df_typ), total_size)
"""
    exec(fgi__viza, {'bodo': bodo, 'objmode_func': jju__bov, '_op': np.
        int32(bodo.libs.distributed_api.Reduce_Type.Sum.value),
        'out_df_typ': csv_iterator_type.yield_type}, vkh__mwcyp)
    return vkh__mwcyp['read_func']
