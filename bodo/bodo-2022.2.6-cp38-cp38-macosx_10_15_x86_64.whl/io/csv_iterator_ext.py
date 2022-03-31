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
        oodu__yupt = (
            f'CSVIteratorType({df_type}, {out_colnames}, {out_types}, {usecols}, {sep}, {index_ind}, {index_arr_typ}, {index_name}, {escapechar})'
            )
        super(types.SimpleIteratorType, self).__init__(oodu__yupt)
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
        abz__jptry = [('csv_reader', bodo.ir.connector.stream_reader_type),
            ('index', types.EphemeralPointer(types.uintp))]
        super(CSVIteratorModel, self).__init__(dmm, fe_type, abz__jptry)


@lower_builtin('getiter', CSVIteratorType)
def getiter_csv_iterator(context, builder, sig, args):
    yxila__jznmp = cgutils.create_struct_proxy(sig.args[0])(context,
        builder, value=args[0])
    eedt__pvdk = lir.FunctionType(lir.VoidType(), [lir.IntType(8).as_pointer()]
        )
    xqx__rjsvw = cgutils.get_or_insert_function(builder.module, eedt__pvdk,
        name='initialize_csv_reader')
    builder.call(xqx__rjsvw, [yxila__jznmp.csv_reader])
    builder.store(context.get_constant(types.uint64, 0), yxila__jznmp.index)
    return impl_ret_borrowed(context, builder, sig.return_type, args[0])


@lower_builtin('iternext', CSVIteratorType)
@iternext_impl(RefType.NEW)
def iternext_csv_iterator(context, builder, sig, args, result):
    [osv__yviar] = sig.args
    [pab__eexgg] = args
    yxila__jznmp = cgutils.create_struct_proxy(osv__yviar)(context, builder,
        value=pab__eexgg)
    eedt__pvdk = lir.FunctionType(lir.IntType(1), [lir.IntType(8).as_pointer()]
        )
    xqx__rjsvw = cgutils.get_or_insert_function(builder.module, eedt__pvdk,
        name='update_csv_reader')
    uarax__gsmp = builder.call(xqx__rjsvw, [yxila__jznmp.csv_reader])
    result.set_valid(uarax__gsmp)
    with builder.if_then(uarax__gsmp):
        qrqo__brum = builder.load(yxila__jznmp.index)
        gjb__hbmm = types.Tuple([sig.return_type.first_type, types.int64])
        kay__fgg = gen_read_csv_objmode(sig.args[0])
        qzcfi__tsv = signature(gjb__hbmm, bodo.ir.connector.
            stream_reader_type, types.int64)
        vyze__xvrb = context.compile_internal(builder, kay__fgg, qzcfi__tsv,
            [yxila__jznmp.csv_reader, qrqo__brum])
        xevu__bdh, wqnu__okw = cgutils.unpack_tuple(builder, vyze__xvrb)
        jpmy__oarfr = builder.add(qrqo__brum, wqnu__okw, flags=['nsw'])
        builder.store(jpmy__oarfr, yxila__jznmp.index)
        result.yield_(xevu__bdh)


@intrinsic
def init_csv_iterator(typingctx, csv_reader, csv_iterator_typeref):

    def codegen(context, builder, signature, args):
        hgtq__slrh = cgutils.create_struct_proxy(signature.return_type)(context
            , builder)
        hgtq__slrh.csv_reader = args[0]
        tmej__odp = context.get_constant(types.uintp, 0)
        hgtq__slrh.index = cgutils.alloca_once_value(builder, tmej__odp)
        return hgtq__slrh._getvalue()
    assert isinstance(csv_iterator_typeref, types.TypeRef
        ), 'Initializing a csv iterator requires a typeref'
    ommj__wpgw = csv_iterator_typeref.instance_type
    sig = signature(ommj__wpgw, csv_reader, csv_iterator_typeref)
    return sig, codegen


def gen_read_csv_objmode(csv_iterator_type):
    zwuff__zuh = 'def read_csv_objmode(f_reader):\n'
    usto__dpv = [sanitize_varname(rvq__fhtgc) for rvq__fhtgc in
        csv_iterator_type._out_colnames]
    oqb__mqd = ir_utils.next_label()
    grr__pvj = globals()
    out_types = csv_iterator_type._out_types
    grr__pvj[f'table_type_{oqb__mqd}'] = TableType(tuple(out_types))
    grr__pvj[f'idx_array_typ'] = csv_iterator_type._index_arr_typ
    ypqb__yokkx = list(range(len(csv_iterator_type._usecols)))
    zwuff__zuh += _gen_read_csv_objmode(csv_iterator_type._out_colnames,
        usto__dpv, out_types, csv_iterator_type._usecols, ypqb__yokkx,
        csv_iterator_type._sep, csv_iterator_type._escapechar, oqb__mqd,
        grr__pvj, parallel=False, check_parallel_runtime=True,
        idx_col_index=csv_iterator_type._index_ind, idx_col_typ=
        csv_iterator_type._index_arr_typ)
    pons__okh = bodo.ir.csv_ext._gen_parallel_flag_name(usto__dpv)
    wlf__yiagg = ['T'] + (['idx_arr'] if csv_iterator_type._index_ind is not
        None else []) + [pons__okh]
    zwuff__zuh += f"  return {', '.join(wlf__yiagg)}"
    grr__pvj = globals()
    wvhs__zhqbk = {}
    exec(zwuff__zuh, grr__pvj, wvhs__zhqbk)
    ulsm__duubl = wvhs__zhqbk['read_csv_objmode']
    nflnt__fgsn = numba.njit(ulsm__duubl)
    bodo.ir.csv_ext.compiled_funcs.append(nflnt__fgsn)
    fcx__pgoy = 'def read_func(reader, local_start):\n'
    fcx__pgoy += f"  {', '.join(wlf__yiagg)} = objmode_func(reader)\n"
    index_ind = csv_iterator_type._index_ind
    if index_ind is None:
        fcx__pgoy += f'  local_len = len(T)\n'
        fcx__pgoy += '  total_size = local_len\n'
        fcx__pgoy += f'  if ({pons__okh}):\n'
        fcx__pgoy += """    local_start = local_start + bodo.libs.distributed_api.dist_exscan(local_len, _op)
"""
        fcx__pgoy += (
            '    total_size = bodo.libs.distributed_api.dist_reduce(local_len, _op)\n'
            )
        xjqm__cdy = (
            f'bodo.hiframes.pd_index_ext.init_range_index(local_start, local_start + local_len, 1, None)'
            )
    else:
        fcx__pgoy += '  total_size = 0\n'
        xjqm__cdy = (
            f'bodo.utils.conversion.convert_to_index({wlf__yiagg[1]}, {csv_iterator_type._index_name!r})'
            )
    fcx__pgoy += f"""  return (bodo.hiframes.pd_dataframe_ext.init_dataframe(({wlf__yiagg[0]},), {xjqm__cdy}, out_df_typ), total_size)
"""
    exec(fcx__pgoy, {'bodo': bodo, 'objmode_func': nflnt__fgsn, '_op': np.
        int32(bodo.libs.distributed_api.Reduce_Type.Sum.value),
        'out_df_typ': csv_iterator_type.yield_type}, wvhs__zhqbk)
    return wvhs__zhqbk['read_func']
