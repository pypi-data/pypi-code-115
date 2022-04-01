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
        fskz__suo = [('left', fe_type.arr_type), ('right', fe_type.arr_type)]
        models.StructModel.__init__(self, dmm, fe_type, fskz__suo)


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
        mxj__jobfc, dbt__utpzw = args
        luea__pyeow = cgutils.create_struct_proxy(signature.return_type)(
            context, builder)
        luea__pyeow.left = mxj__jobfc
        luea__pyeow.right = dbt__utpzw
        context.nrt.incref(builder, signature.args[0], mxj__jobfc)
        context.nrt.incref(builder, signature.args[1], dbt__utpzw)
        return luea__pyeow._getvalue()
    rwv__wdm = IntervalArrayType(left)
    tjym__kfzs = rwv__wdm(left, right)
    return tjym__kfzs, codegen


def init_interval_array_equiv(self, scope, equiv_set, loc, args, kws):
    assert len(args) == 2 and not kws
    daa__vang = []
    for bef__dqwyx in args:
        anfha__jcny = equiv_set.get_shape(bef__dqwyx)
        if anfha__jcny is not None:
            daa__vang.append(anfha__jcny[0])
    if len(daa__vang) > 1:
        equiv_set.insert_equiv(*daa__vang)
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
    luea__pyeow = cgutils.create_struct_proxy(typ)(c.context, c.builder, val)
    c.context.nrt.incref(c.builder, typ.arr_type, luea__pyeow.left)
    anlb__wjyd = c.pyapi.from_native_value(typ.arr_type, luea__pyeow.left,
        c.env_manager)
    c.context.nrt.incref(c.builder, typ.arr_type, luea__pyeow.right)
    ducg__lwg = c.pyapi.from_native_value(typ.arr_type, luea__pyeow.right,
        c.env_manager)
    hmqj__nyg = c.context.insert_const_string(c.builder.module, 'pandas')
    ofrog__gzdop = c.pyapi.import_module_noblock(hmqj__nyg)
    czu__uwhh = c.pyapi.object_getattr_string(ofrog__gzdop, 'arrays')
    uvh__kwciq = c.pyapi.object_getattr_string(czu__uwhh, 'IntervalArray')
    pdhru__leo = c.pyapi.call_method(uvh__kwciq, 'from_arrays', (anlb__wjyd,
        ducg__lwg))
    c.pyapi.decref(anlb__wjyd)
    c.pyapi.decref(ducg__lwg)
    c.pyapi.decref(ofrog__gzdop)
    c.pyapi.decref(czu__uwhh)
    c.pyapi.decref(uvh__kwciq)
    c.context.nrt.decref(c.builder, typ, val)
    return pdhru__leo


@unbox(IntervalArrayType)
def unbox_interval_arr(typ, val, c):
    anlb__wjyd = c.pyapi.object_getattr_string(val, '_left')
    left = c.pyapi.to_native_value(typ.arr_type, anlb__wjyd).value
    c.pyapi.decref(anlb__wjyd)
    ducg__lwg = c.pyapi.object_getattr_string(val, '_right')
    right = c.pyapi.to_native_value(typ.arr_type, ducg__lwg).value
    c.pyapi.decref(ducg__lwg)
    luea__pyeow = cgutils.create_struct_proxy(typ)(c.context, c.builder)
    luea__pyeow.left = left
    luea__pyeow.right = right
    wgpb__nluk = cgutils.is_not_null(c.builder, c.pyapi.err_occurred())
    return NativeValue(luea__pyeow._getvalue(), is_error=wgpb__nluk)


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
