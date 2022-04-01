"""Array of tuple values, implemented by reusing array of structs implementation.
"""
import operator
import numba
import numpy as np
from numba.core import types
from numba.extending import NativeValue, box, intrinsic, make_attribute_wrapper, models, overload, overload_attribute, overload_method, register_model, unbox
from numba.parfors.array_analysis import ArrayAnalysis
import bodo
from bodo.libs.struct_arr_ext import StructArrayType, box_struct_arr, unbox_struct_array


class TupleArrayType(types.ArrayCompatible):

    def __init__(self, data):
        self.data = data
        super(TupleArrayType, self).__init__(name='TupleArrayType({})'.
            format(data))

    @property
    def as_array(self):
        return types.Array(types.undefined, 1, 'C')

    @property
    def dtype(self):
        return types.BaseTuple.from_types(tuple(iowc__zxmk.dtype for
            iowc__zxmk in self.data))

    def copy(self):
        return TupleArrayType(self.data)

    @property
    def mangling_args(self):
        return self.__class__.__name__, (self._code,)


@register_model(TupleArrayType)
class TupleArrayModel(models.StructModel):

    def __init__(self, dmm, fe_type):
        oul__pvl = [('data', StructArrayType(fe_type.data))]
        models.StructModel.__init__(self, dmm, fe_type, oul__pvl)


make_attribute_wrapper(TupleArrayType, 'data', '_data')


@intrinsic
def init_tuple_arr(typingctx, data_typ=None):
    assert isinstance(data_typ, StructArrayType)
    ojjf__vghn = TupleArrayType(data_typ.data)

    def codegen(context, builder, sig, args):
        jwy__sdx, = args
        tej__qtjt = context.make_helper(builder, ojjf__vghn)
        tej__qtjt.data = jwy__sdx
        context.nrt.incref(builder, data_typ, jwy__sdx)
        return tej__qtjt._getvalue()
    return ojjf__vghn(data_typ), codegen


@unbox(TupleArrayType)
def unbox_tuple_array(typ, val, c):
    data_typ = StructArrayType(typ.data)
    yvv__hoqs = unbox_struct_array(data_typ, val, c, is_tuple_array=True)
    jwy__sdx = yvv__hoqs.value
    tej__qtjt = c.context.make_helper(c.builder, typ)
    tej__qtjt.data = jwy__sdx
    knrcq__jucbw = yvv__hoqs.is_error
    return NativeValue(tej__qtjt._getvalue(), is_error=knrcq__jucbw)


@box(TupleArrayType)
def box_tuple_arr(typ, val, c):
    data_typ = StructArrayType(typ.data)
    tej__qtjt = c.context.make_helper(c.builder, typ, val)
    arr = box_struct_arr(data_typ, tej__qtjt.data, c, is_tuple_array=True)
    return arr


@numba.njit
def pre_alloc_tuple_array(n, nested_counts, dtypes):
    return init_tuple_arr(bodo.libs.struct_arr_ext.pre_alloc_struct_array(n,
        nested_counts, dtypes, None))


def pre_alloc_tuple_array_equiv(self, scope, equiv_set, loc, args, kws):
    assert len(args) == 3 and not kws
    return ArrayAnalysis.AnalyzeResult(shape=args[0], pre=[])


(ArrayAnalysis._analyze_op_call_bodo_libs_tuple_arr_ext_pre_alloc_tuple_array
    ) = pre_alloc_tuple_array_equiv


@overload(operator.getitem, no_unliteral=True)
def tuple_arr_getitem(arr, ind):
    if not isinstance(arr, TupleArrayType):
        return
    if isinstance(ind, types.Integer):
        blucw__undy = 'def impl(arr, ind):\n'
        mwj__epth = ','.join(f'get_data(arr._data)[{uofkt__rpz}][ind]' for
            uofkt__rpz in range(len(arr.data)))
        blucw__undy += f'  return ({mwj__epth})\n'
        duqex__ets = {}
        exec(blucw__undy, {'get_data': bodo.libs.struct_arr_ext.get_data},
            duqex__ets)
        dcn__vqh = duqex__ets['impl']
        return dcn__vqh

    def impl_arr(arr, ind):
        return init_tuple_arr(arr._data[ind])
    return impl_arr


@overload(operator.setitem, no_unliteral=True)
def tuple_arr_setitem(arr, ind, val):
    if not isinstance(arr, TupleArrayType):
        return
    if val == types.none or isinstance(val, types.optional):
        return
    if isinstance(ind, types.Integer):
        oyygg__hoxgp = len(arr.data)
        blucw__undy = 'def impl(arr, ind, val):\n'
        blucw__undy += '  data = get_data(arr._data)\n'
        blucw__undy += '  null_bitmap = get_null_bitmap(arr._data)\n'
        blucw__undy += '  set_bit_to_arr(null_bitmap, ind, 1)\n'
        for uofkt__rpz in range(oyygg__hoxgp):
            blucw__undy += f'  data[{uofkt__rpz}][ind] = val[{uofkt__rpz}]\n'
        duqex__ets = {}
        exec(blucw__undy, {'get_data': bodo.libs.struct_arr_ext.get_data,
            'get_null_bitmap': bodo.libs.struct_arr_ext.get_null_bitmap,
            'set_bit_to_arr': bodo.libs.int_arr_ext.set_bit_to_arr}, duqex__ets
            )
        dcn__vqh = duqex__ets['impl']
        return dcn__vqh

    def impl_arr(arr, ind, val):
        val = bodo.utils.conversion.coerce_to_array(val, use_nullable_array
            =True)
        arr._data[ind] = val._data
    return impl_arr


@overload(len, no_unliteral=True)
def overload_tuple_arr_len(A):
    if isinstance(A, TupleArrayType):
        return lambda A: len(A._data)


@overload_attribute(TupleArrayType, 'shape')
def overload_tuple_arr_shape(A):
    return lambda A: (len(A._data),)


@overload_attribute(TupleArrayType, 'dtype')
def overload_tuple_arr_dtype(A):
    return lambda A: np.object_


@overload_attribute(TupleArrayType, 'ndim')
def overload_tuple_arr_ndim(A):
    return lambda A: 1


@overload_attribute(TupleArrayType, 'nbytes')
def overload_tuple_arr_nbytes(A):
    return lambda A: A._data.nbytes


@overload_method(TupleArrayType, 'copy', no_unliteral=True)
def overload_tuple_arr_copy(A):

    def copy_impl(A):
        return init_tuple_arr(A._data.copy())
    return copy_impl
