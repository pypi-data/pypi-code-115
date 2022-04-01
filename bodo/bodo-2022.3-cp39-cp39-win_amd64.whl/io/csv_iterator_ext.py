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
        lhekr__rsbm = (
            f'CSVIteratorType({df_type}, {out_colnames}, {out_types}, {usecols}, {sep}, {index_ind}, {index_arr_typ}, {index_name}, {escapechar})'
            )
        super(types.SimpleIteratorType, self).__init__(lhekr__rsbm)
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
        rsd__ezcnw = [('csv_reader', bodo.ir.connector.stream_reader_type),
            ('index', types.EphemeralPointer(types.uintp))]
        super(CSVIteratorModel, self).__init__(dmm, fe_type, rsd__ezcnw)


@lower_builtin('getiter', CSVIteratorType)
def getiter_csv_iterator(context, builder, sig, args):
    kay__pjojo = cgutils.create_struct_proxy(sig.args[0])(context, builder,
        value=args[0])
    jqlzm__sza = lir.FunctionType(lir.VoidType(), [lir.IntType(8).as_pointer()]
        )
    ubkhc__dmhli = cgutils.get_or_insert_function(builder.module,
        jqlzm__sza, name='initialize_csv_reader')
    builder.call(ubkhc__dmhli, [kay__pjojo.csv_reader])
    builder.store(context.get_constant(types.uint64, 0), kay__pjojo.index)
    return impl_ret_borrowed(context, builder, sig.return_type, args[0])


@lower_builtin('iternext', CSVIteratorType)
@iternext_impl(RefType.NEW)
def iternext_csv_iterator(context, builder, sig, args, result):
    [ekowz__gwnxo] = sig.args
    [cnqbg__wdv] = args
    kay__pjojo = cgutils.create_struct_proxy(ekowz__gwnxo)(context, builder,
        value=cnqbg__wdv)
    jqlzm__sza = lir.FunctionType(lir.IntType(1), [lir.IntType(8).as_pointer()]
        )
    ubkhc__dmhli = cgutils.get_or_insert_function(builder.module,
        jqlzm__sza, name='update_csv_reader')
    lou__yfcut = builder.call(ubkhc__dmhli, [kay__pjojo.csv_reader])
    result.set_valid(lou__yfcut)
    with builder.if_then(lou__yfcut):
        foudj__ielj = builder.load(kay__pjojo.index)
        angl__irxrz = types.Tuple([sig.return_type.first_type, types.int64])
        tawg__ask = gen_read_csv_objmode(sig.args[0])
        cqn__feq = signature(angl__irxrz, bodo.ir.connector.
            stream_reader_type, types.int64)
        opjg__kikof = context.compile_internal(builder, tawg__ask, cqn__feq,
            [kay__pjojo.csv_reader, foudj__ielj])
        yvqij__oohp, klzos__iyfv = cgutils.unpack_tuple(builder, opjg__kikof)
        yolau__ruiy = builder.add(foudj__ielj, klzos__iyfv, flags=['nsw'])
        builder.store(yolau__ruiy, kay__pjojo.index)
        result.yield_(yvqij__oohp)


@intrinsic
def init_csv_iterator(typingctx, csv_reader, csv_iterator_typeref):

    def codegen(context, builder, signature, args):
        sdf__qip = cgutils.create_struct_proxy(signature.return_type)(context,
            builder)
        sdf__qip.csv_reader = args[0]
        mgmn__sxf = context.get_constant(types.uintp, 0)
        sdf__qip.index = cgutils.alloca_once_value(builder, mgmn__sxf)
        return sdf__qip._getvalue()
    assert isinstance(csv_iterator_typeref, types.TypeRef
        ), 'Initializing a csv iterator requires a typeref'
    fawt__degu = csv_iterator_typeref.instance_type
    sig = signature(fawt__degu, csv_reader, csv_iterator_typeref)
    return sig, codegen


def gen_read_csv_objmode(csv_iterator_type):
    spkrx__ojxkt = 'def read_csv_objmode(f_reader):\n'
    ygfrp__gsqp = [sanitize_varname(juxh__ralim) for juxh__ralim in
        csv_iterator_type._out_colnames]
    plhbd__qsue = ir_utils.next_label()
    kxya__tyqm = globals()
    out_types = csv_iterator_type._out_types
    kxya__tyqm[f'table_type_{plhbd__qsue}'] = TableType(tuple(out_types))
    kxya__tyqm[f'idx_array_typ'] = csv_iterator_type._index_arr_typ
    xteq__skui = list(range(len(csv_iterator_type._usecols)))
    spkrx__ojxkt += _gen_read_csv_objmode(csv_iterator_type._out_colnames,
        ygfrp__gsqp, out_types, csv_iterator_type._usecols, xteq__skui,
        csv_iterator_type._sep, csv_iterator_type._escapechar, plhbd__qsue,
        kxya__tyqm, parallel=False, check_parallel_runtime=True,
        idx_col_index=csv_iterator_type._index_ind, idx_col_typ=
        csv_iterator_type._index_arr_typ)
    bxbwb__ojt = bodo.ir.csv_ext._gen_parallel_flag_name(ygfrp__gsqp)
    ngl__pxpo = ['T'] + (['idx_arr'] if csv_iterator_type._index_ind is not
        None else []) + [bxbwb__ojt]
    spkrx__ojxkt += f"  return {', '.join(ngl__pxpo)}"
    kxya__tyqm = globals()
    ywf__llhkz = {}
    exec(spkrx__ojxkt, kxya__tyqm, ywf__llhkz)
    ohd__reakx = ywf__llhkz['read_csv_objmode']
    xeyqe__aqyt = numba.njit(ohd__reakx)
    bodo.ir.csv_ext.compiled_funcs.append(xeyqe__aqyt)
    axew__dyjjy = 'def read_func(reader, local_start):\n'
    axew__dyjjy += f"  {', '.join(ngl__pxpo)} = objmode_func(reader)\n"
    index_ind = csv_iterator_type._index_ind
    if index_ind is None:
        axew__dyjjy += f'  local_len = len(T)\n'
        axew__dyjjy += '  total_size = local_len\n'
        axew__dyjjy += f'  if ({bxbwb__ojt}):\n'
        axew__dyjjy += """    local_start = local_start + bodo.libs.distributed_api.dist_exscan(local_len, _op)
"""
        axew__dyjjy += (
            '    total_size = bodo.libs.distributed_api.dist_reduce(local_len, _op)\n'
            )
        det__aydw = (
            f'bodo.hiframes.pd_index_ext.init_range_index(local_start, local_start + local_len, 1, None)'
            )
    else:
        axew__dyjjy += '  total_size = 0\n'
        det__aydw = (
            f'bodo.utils.conversion.convert_to_index({ngl__pxpo[1]}, {csv_iterator_type._index_name!r})'
            )
    axew__dyjjy += f"""  return (bodo.hiframes.pd_dataframe_ext.init_dataframe(({ngl__pxpo[0]},), {det__aydw}, out_df_typ), total_size)
"""
    exec(axew__dyjjy, {'bodo': bodo, 'objmode_func': xeyqe__aqyt, '_op': np
        .int32(bodo.libs.distributed_api.Reduce_Type.Sum.value),
        'out_df_typ': csv_iterator_type.yield_type}, ywf__llhkz)
    return ywf__llhkz['read_func']
