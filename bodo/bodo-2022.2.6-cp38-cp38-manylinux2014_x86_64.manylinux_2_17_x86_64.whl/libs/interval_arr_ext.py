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
        xcdb__pzetu = [('left', fe_type.arr_type), ('right', fe_type.arr_type)]
        models.StructModel.__init__(self, dmm, fe_type, xcdb__pzetu)


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
        jsfn__mqwb, mlapb__dlbg = args
        hdh__qba = cgutils.create_struct_proxy(signature.return_type)(context,
            builder)
        hdh__qba.left = jsfn__mqwb
        hdh__qba.right = mlapb__dlbg
        context.nrt.incref(builder, signature.args[0], jsfn__mqwb)
        context.nrt.incref(builder, signature.args[1], mlapb__dlbg)
        return hdh__qba._getvalue()
    tsoa__fdebw = IntervalArrayType(left)
    ezlyi__cfjvi = tsoa__fdebw(left, right)
    return ezlyi__cfjvi, codegen


def init_interval_array_equiv(self, scope, equiv_set, loc, args, kws):
    assert len(args) == 2 and not kws
    pfpuw__cxsdp = []
    for sdkpm__bqaz in args:
        tas__qce = equiv_set.get_shape(sdkpm__bqaz)
        if tas__qce is not None:
            pfpuw__cxsdp.append(tas__qce[0])
    if len(pfpuw__cxsdp) > 1:
        equiv_set.insert_equiv(*pfpuw__cxsdp)
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
    hdh__qba = cgutils.create_struct_proxy(typ)(c.context, c.builder, val)
    c.context.nrt.incref(c.builder, typ.arr_type, hdh__qba.left)
    oqbo__okjs = c.pyapi.from_native_value(typ.arr_type, hdh__qba.left, c.
        env_manager)
    c.context.nrt.incref(c.builder, typ.arr_type, hdh__qba.right)
    jua__fyykw = c.pyapi.from_native_value(typ.arr_type, hdh__qba.right, c.
        env_manager)
    wlp__mcczm = c.context.insert_const_string(c.builder.module, 'pandas')
    xtfu__owpky = c.pyapi.import_module_noblock(wlp__mcczm)
    nngd__gcfvg = c.pyapi.object_getattr_string(xtfu__owpky, 'arrays')
    qdb__whle = c.pyapi.object_getattr_string(nngd__gcfvg, 'IntervalArray')
    kbvux__lizln = c.pyapi.call_method(qdb__whle, 'from_arrays', (
        oqbo__okjs, jua__fyykw))
    c.pyapi.decref(oqbo__okjs)
    c.pyapi.decref(jua__fyykw)
    c.pyapi.decref(xtfu__owpky)
    c.pyapi.decref(nngd__gcfvg)
    c.pyapi.decref(qdb__whle)
    c.context.nrt.decref(c.builder, typ, val)
    return kbvux__lizln


@unbox(IntervalArrayType)
def unbox_interval_arr(typ, val, c):
    oqbo__okjs = c.pyapi.object_getattr_string(val, '_left')
    left = c.pyapi.to_native_value(typ.arr_type, oqbo__okjs).value
    c.pyapi.decref(oqbo__okjs)
    jua__fyykw = c.pyapi.object_getattr_string(val, '_right')
    right = c.pyapi.to_native_value(typ.arr_type, jua__fyykw).value
    c.pyapi.decref(jua__fyykw)
    hdh__qba = cgutils.create_struct_proxy(typ)(c.context, c.builder)
    hdh__qba.left = left
    hdh__qba.right = right
    mwnh__jsak = cgutils.is_not_null(c.builder, c.pyapi.err_occurred())
    return NativeValue(hdh__qba._getvalue(), is_error=mwnh__jsak)


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
