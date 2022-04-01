"""
Array of intervals corresponding to IntervalArray of Pandas.
Used for IntervalIndex, which is necessary for Series.value_counts() with 'bins'
argument.
"""
import numba
import pandas as pd
from numba.core import cgutils, types
from numba.extending import NativeValue, box, intrinsic, make_attribute_wrapper, models, overload, overload_attribute, overload_method, register_model, typeof_impl, unbox
from numba.parfors.array_analysis import ArrayAnalysis
import bodo


class IntervalType(types.Type):

    def __init__(self):
        super(IntervalType, self).__init__('IntervalType()')


class IntervalArrayType(types.ArrayCompatible):

    def __init__(self, arr_type):
        self.arr_type = arr_type
        self.dtype = IntervalType()
        super(IntervalArrayType, self).__init__(name=
            f'IntervalArrayType({arr_type})')

    @property
    def as_array(self):
        return types.Array(types.undefined, 1, 'C')

    def copy(self):
        return IntervalArrayType(self.arr_type)

    @property
    def mangling_args(self):
        return self.__class__.__name__, (self._code,)


@register_model(IntervalArrayType)
class IntervalArrayModel(models.StructModel):

    def __init__(self, dmm, fe_type):
        fxq__kike = [('left', fe_type.arr_type), ('right', fe_type.arr_type)]
        models.StructModel.__init__(self, dmm, fe_type, fxq__kike)


make_attribute_wrapper(IntervalArrayType, 'left', '_left')
make_attribute_wrapper(IntervalArrayType, 'right', '_right')


@typeof_impl.register(pd.arrays.IntervalArray)
def typeof_interval_array(val, c):
    arr_type = bodo.typeof(val._left)
    return IntervalArrayType(arr_type)


@intrinsic
def init_interval_array(typingctx, left, right=None):
    assert left == right, 'Interval left/right array types should be the same'

    def codegen(context, builder, signature, args):
        bfrdc__mjlxo, bnh__deyq = args
        girf__xdtze = cgutils.create_struct_proxy(signature.return_type)(
            context, builder)
        girf__xdtze.left = bfrdc__mjlxo
        girf__xdtze.right = bnh__deyq
        context.nrt.incref(builder, signature.args[0], bfrdc__mjlxo)
        context.nrt.incref(builder, signature.args[1], bnh__deyq)
        return girf__xdtze._getvalue()
    oizl__uwv = IntervalArrayType(left)
    syq__gtpt = oizl__uwv(left, right)
    return syq__gtpt, codegen


def init_interval_array_equiv(self, scope, equiv_set, loc, args, kws):
    assert len(args) == 2 and not kws
    ohhgt__kfdny = []
    for eabz__hasy in args:
        mpe__mvi = equiv_set.get_shape(eabz__hasy)
        if mpe__mvi is not None:
            ohhgt__kfdny.append(mpe__mvi[0])
    if len(ohhgt__kfdny) > 1:
        equiv_set.insert_equiv(*ohhgt__kfdny)
    left = args[0]
    if equiv_set.has_shape(left):
        return ArrayAnalysis.AnalyzeResult(shape=left, pre=[])
    return None


(ArrayAnalysis._analyze_op_call_bodo_libs_interval_arr_ext_init_interval_array
    ) = init_interval_array_equiv


def alias_ext_init_interval_array(lhs_name, args, alias_map, arg_aliases):
    assert len(args) == 2
    numba.core.ir_utils._add_alias(lhs_name, args[0].name, alias_map,
        arg_aliases)
    numba.core.ir_utils._add_alias(lhs_name, args[1].name, alias_map,
        arg_aliases)


numba.core.ir_utils.alias_func_extensions['init_interval_array',
    'bodo.libs.int_arr_ext'] = alias_ext_init_interval_array


@box(IntervalArrayType)
def box_interval_arr(typ, val, c):
    girf__xdtze = cgutils.create_struct_proxy(typ)(c.context, c.builder, val)
    c.context.nrt.incref(c.builder, typ.arr_type, girf__xdtze.left)
    nxsso__tspwy = c.pyapi.from_native_value(typ.arr_type, girf__xdtze.left,
        c.env_manager)
    c.context.nrt.incref(c.builder, typ.arr_type, girf__xdtze.right)
    cqdq__ckbjl = c.pyapi.from_native_value(typ.arr_type, girf__xdtze.right,
        c.env_manager)
    sfoyl__xlxq = c.context.insert_const_string(c.builder.module, 'pandas')
    djaxg__ceq = c.pyapi.import_module_noblock(sfoyl__xlxq)
    fux__dzb = c.pyapi.object_getattr_string(djaxg__ceq, 'arrays')
    cuzu__jpuh = c.pyapi.object_getattr_string(fux__dzb, 'IntervalArray')
    qwa__uou = c.pyapi.call_method(cuzu__jpuh, 'from_arrays', (nxsso__tspwy,
        cqdq__ckbjl))
    c.pyapi.decref(nxsso__tspwy)
    c.pyapi.decref(cqdq__ckbjl)
    c.pyapi.decref(djaxg__ceq)
    c.pyapi.decref(fux__dzb)
    c.pyapi.decref(cuzu__jpuh)
    c.context.nrt.decref(c.builder, typ, val)
    return qwa__uou


@unbox(IntervalArrayType)
def unbox_interval_arr(typ, val, c):
    nxsso__tspwy = c.pyapi.object_getattr_string(val, '_left')
    left = c.pyapi.to_native_value(typ.arr_type, nxsso__tspwy).value
    c.pyapi.decref(nxsso__tspwy)
    cqdq__ckbjl = c.pyapi.object_getattr_string(val, '_right')
    right = c.pyapi.to_native_value(typ.arr_type, cqdq__ckbjl).value
    c.pyapi.decref(cqdq__ckbjl)
    girf__xdtze = cgutils.create_struct_proxy(typ)(c.context, c.builder)
    girf__xdtze.left = left
    girf__xdtze.right = right
    kjlmk__gdc = cgutils.is_not_null(c.builder, c.pyapi.err_occurred())
    return NativeValue(girf__xdtze._getvalue(), is_error=kjlmk__gdc)


@overload(len, no_unliteral=True)
def overload_interval_arr_len(A):
    if isinstance(A, IntervalArrayType):
        return lambda A: len(A._left)


@overload_attribute(IntervalArrayType, 'shape')
def overload_interval_arr_shape(A):
    return lambda A: (len(A._left),)


@overload_attribute(IntervalArrayType, 'ndim')
def overload_interval_arr_ndim(A):
    return lambda A: 1


@overload_attribute(IntervalArrayType, 'nbytes')
def overload_interval_arr_nbytes(A):
    return lambda A: A._left.nbytes + A._right.nbytes


@overload_method(IntervalArrayType, 'copy', no_unliteral=True)
def overload_interval_arr_copy(A):
    return lambda A: bodo.libs.interval_arr_ext.init_interval_array(A._left
        .copy(), A._right.copy())
