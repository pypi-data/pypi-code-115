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
        trdv__wwdcy = (
            f'CSVIteratorType({df_type}, {out_colnames}, {out_types}, {usecols}, {sep}, {index_ind}, {index_arr_typ}, {index_name}, {escapechar})'
            )
        super(types.SimpleIteratorType, self).__init__(trdv__wwdcy)
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
        ukbi__vdwjy = [('csv_reader', bodo.ir.connector.stream_reader_type),
            ('index', types.EphemeralPointer(types.uintp))]
        super(CSVIteratorModel, self).__init__(dmm, fe_type, ukbi__vdwjy)


@lower_builtin('getiter', CSVIteratorType)
def getiter_csv_iterator(context, builder, sig, args):
    utqmy__cmzh = cgutils.create_struct_proxy(sig.args[0])(context, builder,
        value=args[0])
    zokbf__volw = lir.FunctionType(lir.VoidType(), [lir.IntType(8).
        as_pointer()])
    lrxw__jva = cgutils.get_or_insert_function(builder.module, zokbf__volw,
        name='initialize_csv_reader')
    builder.call(lrxw__jva, [utqmy__cmzh.csv_reader])
    builder.store(context.get_constant(types.uint64, 0), utqmy__cmzh.index)
    return impl_ret_borrowed(context, builder, sig.return_type, args[0])


@lower_builtin('iternext', CSVIteratorType)
@iternext_impl(RefType.NEW)
def iternext_csv_iterator(context, builder, sig, args, result):
    [voy__putbi] = sig.args
    [pvh__crra] = args
    utqmy__cmzh = cgutils.create_struct_proxy(voy__putbi)(context, builder,
        value=pvh__crra)
    zokbf__volw = lir.FunctionType(lir.IntType(1), [lir.IntType(8).
        as_pointer()])
    lrxw__jva = cgutils.get_or_insert_function(builder.module, zokbf__volw,
        name='update_csv_reader')
    rwdr__eumey = builder.call(lrxw__jva, [utqmy__cmzh.csv_reader])
    result.set_valid(rwdr__eumey)
    with builder.if_then(rwdr__eumey):
        fjqfb__irwrm = builder.load(utqmy__cmzh.index)
        rjal__ofhv = types.Tuple([sig.return_type.first_type, types.int64])
        jyw__icp = gen_read_csv_objmode(sig.args[0])
        emc__uum = signature(rjal__ofhv, bodo.ir.connector.
            stream_reader_type, types.int64)
        mnz__ingo = context.compile_internal(builder, jyw__icp, emc__uum, [
            utqmy__cmzh.csv_reader, fjqfb__irwrm])
        apdhg__delch, pylls__slu = cgutils.unpack_tuple(builder, mnz__ingo)
        vwev__hhz = builder.add(fjqfb__irwrm, pylls__slu, flags=['nsw'])
        builder.store(vwev__hhz, utqmy__cmzh.index)
        result.yield_(apdhg__delch)


@intrinsic
def init_csv_iterator(typingctx, csv_reader, csv_iterator_typeref):

    def codegen(context, builder, signature, args):
        hice__gamhy = cgutils.create_struct_proxy(signature.return_type)(
            context, builder)
        hice__gamhy.csv_reader = args[0]
        rbz__wbh = context.get_constant(types.uintp, 0)
        hice__gamhy.index = cgutils.alloca_once_value(builder, rbz__wbh)
        return hice__gamhy._getvalue()
    assert isinstance(csv_iterator_typeref, types.TypeRef
        ), 'Initializing a csv iterator requires a typeref'
    gzl__rrsqg = csv_iterator_typeref.instance_type
    sig = signature(gzl__rrsqg, csv_reader, csv_iterator_typeref)
    return sig, codegen


def gen_read_csv_objmode(csv_iterator_type):
    kpd__imxio = 'def read_csv_objmode(f_reader):\n'
    ufwg__nhrt = [sanitize_varname(euer__hyzuz) for euer__hyzuz in
        csv_iterator_type._out_colnames]
    lqprh__ogqu = ir_utils.next_label()
    xbl__dgwqd = globals()
    out_types = csv_iterator_type._out_types
    xbl__dgwqd[f'table_type_{lqprh__ogqu}'] = TableType(tuple(out_types))
    xbl__dgwqd[f'idx_array_typ'] = csv_iterator_type._index_arr_typ
    wilry__sacsw = list(range(len(csv_iterator_type._usecols)))
    kpd__imxio += _gen_read_csv_objmode(csv_iterator_type._out_colnames,
        ufwg__nhrt, out_types, csv_iterator_type._usecols, wilry__sacsw,
        csv_iterator_type._sep, csv_iterator_type._escapechar, lqprh__ogqu,
        xbl__dgwqd, parallel=False, check_parallel_runtime=True,
        idx_col_index=csv_iterator_type._index_ind, idx_col_typ=
        csv_iterator_type._index_arr_typ)
    hjpm__mpct = bodo.ir.csv_ext._gen_parallel_flag_name(ufwg__nhrt)
    xkh__wgqu = ['T'] + (['idx_arr'] if csv_iterator_type._index_ind is not
        None else []) + [hjpm__mpct]
    kpd__imxio += f"  return {', '.join(xkh__wgqu)}"
    xbl__dgwqd = globals()
    tdys__cscq = {}
    exec(kpd__imxio, xbl__dgwqd, tdys__cscq)
    wrykj__rhg = tdys__cscq['read_csv_objmode']
    ywzsc__sggi = numba.njit(wrykj__rhg)
    bodo.ir.csv_ext.compiled_funcs.append(ywzsc__sggi)
    lhqp__gusab = 'def read_func(reader, local_start):\n'
    lhqp__gusab += f"  {', '.join(xkh__wgqu)} = objmode_func(reader)\n"
    index_ind = csv_iterator_type._index_ind
    if index_ind is None:
        lhqp__gusab += f'  local_len = len(T)\n'
        lhqp__gusab += '  total_size = local_len\n'
        lhqp__gusab += f'  if ({hjpm__mpct}):\n'
        lhqp__gusab += """    local_start = local_start + bodo.libs.distributed_api.dist_exscan(local_len, _op)
"""
        lhqp__gusab += (
            '    total_size = bodo.libs.distributed_api.dist_reduce(local_len, _op)\n'
            )
        llo__kcc = (
            f'bodo.hiframes.pd_index_ext.init_range_index(local_start, local_start + local_len, 1, None)'
            )
    else:
        lhqp__gusab += '  total_size = 0\n'
        llo__kcc = (
            f'bodo.utils.conversion.convert_to_index({xkh__wgqu[1]}, {csv_iterator_type._index_name!r})'
            )
    lhqp__gusab += f"""  return (bodo.hiframes.pd_dataframe_ext.init_dataframe(({xkh__wgqu[0]},), {llo__kcc}, out_df_typ), total_size)
"""
    exec(lhqp__gusab, {'bodo': bodo, 'objmode_func': ywzsc__sggi, '_op': np
        .int32(bodo.libs.distributed_api.Reduce_Type.Sum.value),
        'out_df_typ': csv_iterator_type.yield_type}, tdys__cscq)
    return tdys__cscq['read_func']
