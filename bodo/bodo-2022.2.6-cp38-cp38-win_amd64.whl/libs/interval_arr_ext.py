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
        fmgm__yeblm = [('left', fe_type.arr_type), ('right', fe_type.arr_type)]
        models.StructModel.__init__(self, dmm, fe_type, fmgm__yeblm)


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
        exr__iks, qtn__mmu = args
        abwd__nxqha = cgutils.create_struct_proxy(signature.return_type)(
            context, builder)
        abwd__nxqha.left = exr__iks
        abwd__nxqha.right = qtn__mmu
        context.nrt.incref(builder, signature.args[0], exr__iks)
        context.nrt.incref(builder, signature.args[1], qtn__mmu)
        return abwd__nxqha._getvalue()
    xns__pbcqq = IntervalArrayType(left)
    nybas__dxja = xns__pbcqq(left, right)
    return nybas__dxja, codegen


def init_interval_array_equiv(self, scope, equiv_set, loc, args, kws):
    assert len(args) == 2 and not kws
    bigil__ykyd = []
    for jgr__tuux in args:
        bel__klc = equiv_set.get_shape(jgr__tuux)
        if bel__klc is not None:
            bigil__ykyd.append(bel__klc[0])
    if len(bigil__ykyd) > 1:
        equiv_set.insert_equiv(*bigil__ykyd)
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
    abwd__nxqha = cgutils.create_struct_proxy(typ)(c.context, c.builder, val)
    c.context.nrt.incref(c.builder, typ.arr_type, abwd__nxqha.left)
    kdkqo__nhtr = c.pyapi.from_native_value(typ.arr_type, abwd__nxqha.left,
        c.env_manager)
    c.context.nrt.incref(c.builder, typ.arr_type, abwd__nxqha.right)
    qnca__zdeps = c.pyapi.from_native_value(typ.arr_type, abwd__nxqha.right,
        c.env_manager)
    qonm__pux = c.context.insert_const_string(c.builder.module, 'pandas')
    fqpcy__pvzc = c.pyapi.import_module_noblock(qonm__pux)
    wlzqc__jodv = c.pyapi.object_getattr_string(fqpcy__pvzc, 'arrays')
    vka__yav = c.pyapi.object_getattr_string(wlzqc__jodv, 'IntervalArray')
    oqf__ojuiu = c.pyapi.call_method(vka__yav, 'from_arrays', (kdkqo__nhtr,
        qnca__zdeps))
    c.pyapi.decref(kdkqo__nhtr)
    c.pyapi.decref(qnca__zdeps)
    c.pyapi.decref(fqpcy__pvzc)
    c.pyapi.decref(wlzqc__jodv)
    c.pyapi.decref(vka__yav)
    c.context.nrt.decref(c.builder, typ, val)
    return oqf__ojuiu


@unbox(IntervalArrayType)
def unbox_interval_arr(typ, val, c):
    kdkqo__nhtr = c.pyapi.object_getattr_string(val, '_left')
    left = c.pyapi.to_native_value(typ.arr_type, kdkqo__nhtr).value
    c.pyapi.decref(kdkqo__nhtr)
    qnca__zdeps = c.pyapi.object_getattr_string(val, '_right')
    right = c.pyapi.to_native_value(typ.arr_type, qnca__zdeps).value
    c.pyapi.decref(qnca__zdeps)
    abwd__nxqha = cgutils.create_struct_proxy(typ)(c.context, c.builder)
    abwd__nxqha.left = left
    abwd__nxqha.right = right
    rvp__oenj = cgutils.is_not_null(c.builder, c.pyapi.err_occurred())
    return NativeValue(abwd__nxqha._getvalue(), is_error=rvp__oenj)


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
