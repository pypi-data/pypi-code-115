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
        yys__embvm = [('left', fe_type.arr_type), ('right', fe_type.arr_type)]
        models.StructModel.__init__(self, dmm, fe_type, yys__embvm)


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
        mojw__vqjyd, cxphy__lklw = args
        wqnik__enq = cgutils.create_struct_proxy(signature.return_type)(context
            , builder)
        wqnik__enq.left = mojw__vqjyd
        wqnik__enq.right = cxphy__lklw
        context.nrt.incref(builder, signature.args[0], mojw__vqjyd)
        context.nrt.incref(builder, signature.args[1], cxphy__lklw)
        return wqnik__enq._getvalue()
    eqp__uhfvj = IntervalArrayType(left)
    zamck__vvvgf = eqp__uhfvj(left, right)
    return zamck__vvvgf, codegen


def init_interval_array_equiv(self, scope, equiv_set, loc, args, kws):
    assert len(args) == 2 and not kws
    zov__vevpv = []
    for bzw__rmrmg in args:
        pka__jrch = equiv_set.get_shape(bzw__rmrmg)
        if pka__jrch is not None:
            zov__vevpv.append(pka__jrch[0])
    if len(zov__vevpv) > 1:
        equiv_set.insert_equiv(*zov__vevpv)
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
    wqnik__enq = cgutils.create_struct_proxy(typ)(c.context, c.builder, val)
    c.context.nrt.incref(c.builder, typ.arr_type, wqnik__enq.left)
    pjs__idf = c.pyapi.from_native_value(typ.arr_type, wqnik__enq.left, c.
        env_manager)
    c.context.nrt.incref(c.builder, typ.arr_type, wqnik__enq.right)
    oxrmo__dkn = c.pyapi.from_native_value(typ.arr_type, wqnik__enq.right,
        c.env_manager)
    plbf__pqhss = c.context.insert_const_string(c.builder.module, 'pandas')
    hiv__xsgcz = c.pyapi.import_module_noblock(plbf__pqhss)
    yclbi__oiej = c.pyapi.object_getattr_string(hiv__xsgcz, 'arrays')
    bfo__svz = c.pyapi.object_getattr_string(yclbi__oiej, 'IntervalArray')
    gsvtf__osaaz = c.pyapi.call_method(bfo__svz, 'from_arrays', (pjs__idf,
        oxrmo__dkn))
    c.pyapi.decref(pjs__idf)
    c.pyapi.decref(oxrmo__dkn)
    c.pyapi.decref(hiv__xsgcz)
    c.pyapi.decref(yclbi__oiej)
    c.pyapi.decref(bfo__svz)
    c.context.nrt.decref(c.builder, typ, val)
    return gsvtf__osaaz


@unbox(IntervalArrayType)
def unbox_interval_arr(typ, val, c):
    pjs__idf = c.pyapi.object_getattr_string(val, '_left')
    left = c.pyapi.to_native_value(typ.arr_type, pjs__idf).value
    c.pyapi.decref(pjs__idf)
    oxrmo__dkn = c.pyapi.object_getattr_string(val, '_right')
    right = c.pyapi.to_native_value(typ.arr_type, oxrmo__dkn).value
    c.pyapi.decref(oxrmo__dkn)
    wqnik__enq = cgutils.create_struct_proxy(typ)(c.context, c.builder)
    wqnik__enq.left = left
    wqnik__enq.right = right
    ugnl__pux = cgutils.is_not_null(c.builder, c.pyapi.err_occurred())
    return NativeValue(wqnik__enq._getvalue(), is_error=ugnl__pux)


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
