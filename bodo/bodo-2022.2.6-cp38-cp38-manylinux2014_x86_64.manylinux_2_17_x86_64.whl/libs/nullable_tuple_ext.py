"""
Wrapper class for Tuples that supports tracking null entries.
This is primarily used for maintaining null information for
Series values used in df.apply
"""
import operator
import numba
from numba.core import cgutils, types
from numba.extending import box, intrinsic, lower_builtin, make_attribute_wrapper, models, overload, overload_method, register_model


class NullableTupleType(types.IterableType):

    def __init__(self, tuple_typ, null_typ):
        self._tuple_typ = tuple_typ
        self._null_typ = null_typ
        super(NullableTupleType, self).__init__(name=
            f'NullableTupleType({tuple_typ}, {null_typ})')

    @property
    def tuple_typ(self):
        return self._tuple_typ

    @property
    def null_typ(self):
        return self._null_typ

    def __getitem__(self, i):
        return self._tuple_typ[i]

    @property
    def key(self):
        return self._tuple_typ

    @property
    def dtype(self):
        return self.tuple_typ.dtype

    @property
    def mangling_args(self):
        return self.__class__.__name__, (self._code,)

    @property
    def iterator_type(self):
        return self.tuple_typ.iterator_type


@register_model(NullableTupleType)
class NullableTupleModel(models.StructModel):

    def __init__(self, dmm, fe_type):
        vdvp__dygym = [('data', fe_type.tuple_typ), ('null_values', fe_type
            .null_typ)]
        super(NullableTupleModel, self).__init__(dmm, fe_type, vdvp__dygym)


make_attribute_wrapper(NullableTupleType, 'data', '_data')
make_attribute_wrapper(NullableTupleType, 'null_values', '_null_values')


@intrinsic
def build_nullable_tuple(typingctx, data_tuple, null_values):
    assert isinstance(data_tuple, types.BaseTuple
        ), "build_nullable_tuple 'data_tuple' argument must be a tuple"
    assert isinstance(null_values, types.BaseTuple
        ), "build_nullable_tuple 'null_values' argument must be a tuple"
    data_tuple = types.unliteral(data_tuple)
    null_values = types.unliteral(null_values)

    def codegen(context, builder, signature, args):
        data_tuple, null_values = args
        cflzi__jsbp = cgutils.create_struct_proxy(signature.return_type)(
            context, builder)
        cflzi__jsbp.data = data_tuple
        cflzi__jsbp.null_values = null_values
        context.nrt.incref(builder, signature.args[0], data_tuple)
        context.nrt.incref(builder, signature.args[1], null_values)
        return cflzi__jsbp._getvalue()
    sig = NullableTupleType(data_tuple, null_values)(data_tuple, null_values)
    return sig, codegen


@box(NullableTupleType)
def box_nullable_tuple(typ, val, c):
    ykct__vwft = cgutils.create_struct_proxy(typ)(c.context, c.builder,
        value=val)
    c.context.nrt.incref(c.builder, typ.tuple_typ, ykct__vwft.data)
    c.context.nrt.incref(c.builder, typ.null_typ, ykct__vwft.null_values)
    gzuif__dbdc = c.pyapi.from_native_value(typ.tuple_typ, ykct__vwft.data,
        c.env_manager)
    ivxbf__yoj = c.pyapi.from_native_value(typ.null_typ, ykct__vwft.
        null_values, c.env_manager)
    ifal__xpuif = c.context.get_constant(types.int64, len(typ.tuple_typ))
    ecfj__xgxv = c.pyapi.list_new(ifal__xpuif)
    with cgutils.for_range(c.builder, ifal__xpuif) as lgvgy__obtne:
        i = lgvgy__obtne.index
        byt__acyg = c.pyapi.long_from_longlong(i)
        wqfpy__qtysq = c.pyapi.object_getitem(ivxbf__yoj, byt__acyg)
        jhk__jxzff = c.pyapi.to_native_value(types.bool_, wqfpy__qtysq).value
        with c.builder.if_else(jhk__jxzff) as (fooir__wzd, waq__ugksc):
            with fooir__wzd:
                c.pyapi.list_setitem(ecfj__xgxv, i, c.pyapi.make_none())
            with waq__ugksc:
                oxkyx__ksfgw = c.pyapi.object_getitem(gzuif__dbdc, byt__acyg)
                c.pyapi.list_setitem(ecfj__xgxv, i, oxkyx__ksfgw)
        c.pyapi.decref(byt__acyg)
        c.pyapi.decref(wqfpy__qtysq)
    wlyy__mzf = c.pyapi.unserialize(c.pyapi.serialize_object(tuple))
    gxw__kqn = c.pyapi.call_function_objargs(wlyy__mzf, (ecfj__xgxv,))
    c.pyapi.decref(gzuif__dbdc)
    c.pyapi.decref(ivxbf__yoj)
    c.pyapi.decref(wlyy__mzf)
    c.pyapi.decref(ecfj__xgxv)
    c.context.nrt.decref(c.builder, typ, val)
    return gxw__kqn


@overload(operator.getitem)
def overload_getitem(A, idx):
    if not isinstance(A, NullableTupleType):
        return
    return lambda A, idx: A._data[idx]


@overload(len)
def overload_len(A):
    if not isinstance(A, NullableTupleType):
        return
    return lambda A: len(A._data)


@lower_builtin('getiter', NullableTupleType)
def nullable_tuple_getiter(context, builder, sig, args):
    cflzi__jsbp = cgutils.create_struct_proxy(sig.args[0])(context, builder,
        value=args[0])
    impl = context.get_function('getiter', sig.return_type(sig.args[0].
        tuple_typ))
    return impl(builder, (cflzi__jsbp.data,))


@overload(operator.eq)
def nullable_tuple_eq(val1, val2):
    if not isinstance(val1, NullableTupleType) or not isinstance(val2,
        NullableTupleType):
        return
    if val1 != val2:
        return lambda val1, val2: False
    phxpd__ggw = 'def impl(val1, val2):\n'
    phxpd__ggw += '    data_tup1 = val1._data\n'
    phxpd__ggw += '    null_tup1 = val1._null_values\n'
    phxpd__ggw += '    data_tup2 = val2._data\n'
    phxpd__ggw += '    null_tup2 = val2._null_values\n'
    ziy__rjs = val1._tuple_typ
    for i in range(len(ziy__rjs)):
        phxpd__ggw += f'    null1_{i} = null_tup1[{i}]\n'
        phxpd__ggw += f'    null2_{i} = null_tup2[{i}]\n'
        phxpd__ggw += f'    data1_{i} = data_tup1[{i}]\n'
        phxpd__ggw += f'    data2_{i} = data_tup2[{i}]\n'
        phxpd__ggw += f'    if null1_{i} != null2_{i}:\n'
        phxpd__ggw += '        return False\n'
        phxpd__ggw += f'    if null1_{i} and (data1_{i} != data2_{i}):\n'
        phxpd__ggw += f'        return False\n'
    phxpd__ggw += f'    return True\n'
    syhat__gmbzx = {}
    exec(phxpd__ggw, {}, syhat__gmbzx)
    impl = syhat__gmbzx['impl']
    return impl


@overload_method(NullableTupleType, '__hash__')
def nullable_tuple_hash(val):

    def impl(val):
        return _nullable_tuple_hash(val)
    return impl


_PyHASH_XXPRIME_1 = numba.cpython.hashing._PyHASH_XXPRIME_1
_PyHASH_XXPRIME_2 = numba.cpython.hashing._PyHASH_XXPRIME_1
_PyHASH_XXPRIME_5 = numba.cpython.hashing._PyHASH_XXPRIME_1


@numba.generated_jit(nopython=True)
def _nullable_tuple_hash(nullable_tup):
    phxpd__ggw = 'def impl(nullable_tup):\n'
    phxpd__ggw += '    data_tup = nullable_tup._data\n'
    phxpd__ggw += '    null_tup = nullable_tup._null_values\n'
    phxpd__ggw += '    tl = numba.cpython.hashing._Py_uhash_t(len(data_tup))\n'
    phxpd__ggw += '    acc = _PyHASH_XXPRIME_5\n'
    ziy__rjs = nullable_tup._tuple_typ
    for i in range(len(ziy__rjs)):
        phxpd__ggw += f'    null_val_{i} = null_tup[{i}]\n'
        phxpd__ggw += f'    null_lane_{i} = hash(null_val_{i})\n'
        phxpd__ggw += (
            f'    if null_lane_{i} == numba.cpython.hashing._Py_uhash_t(-1):\n'
            )
        phxpd__ggw += '        return -1\n'
        phxpd__ggw += f'    acc += null_lane_{i} * _PyHASH_XXPRIME_2\n'
        phxpd__ggw += '    acc = numba.cpython.hashing._PyHASH_XXROTATE(acc)\n'
        phxpd__ggw += '    acc *= _PyHASH_XXPRIME_1\n'
        phxpd__ggw += f'    if not null_val_{i}:\n'
        phxpd__ggw += f'        lane_{i} = hash(data_tup[{i}])\n'
        phxpd__ggw += (
            f'        if lane_{i} == numba.cpython.hashing._Py_uhash_t(-1):\n')
        phxpd__ggw += f'            return -1\n'
        phxpd__ggw += f'        acc += lane_{i} * _PyHASH_XXPRIME_2\n'
        phxpd__ggw += (
            '        acc = numba.cpython.hashing._PyHASH_XXROTATE(acc)\n')
        phxpd__ggw += '        acc *= _PyHASH_XXPRIME_1\n'
    phxpd__ggw += """    acc += tl ^ (_PyHASH_XXPRIME_5 ^ numba.cpython.hashing._Py_uhash_t(3527539))
"""
    phxpd__ggw += '    if acc == numba.cpython.hashing._Py_uhash_t(-1):\n'
    phxpd__ggw += (
        '        return numba.cpython.hashing.process_return(1546275796)\n')
    phxpd__ggw += '    return numba.cpython.hashing.process_return(acc)\n'
    syhat__gmbzx = {}
    exec(phxpd__ggw, {'numba': numba, '_PyHASH_XXPRIME_1':
        _PyHASH_XXPRIME_1, '_PyHASH_XXPRIME_2': _PyHASH_XXPRIME_2,
        '_PyHASH_XXPRIME_5': _PyHASH_XXPRIME_5}, syhat__gmbzx)
    impl = syhat__gmbzx['impl']
    return impl
