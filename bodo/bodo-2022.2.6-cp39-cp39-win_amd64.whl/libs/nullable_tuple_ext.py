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
        qck__vsw = [('data', fe_type.tuple_typ), ('null_values', fe_type.
            null_typ)]
        super(NullableTupleModel, self).__init__(dmm, fe_type, qck__vsw)


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
        glyf__ygybk = cgutils.create_struct_proxy(signature.return_type)(
            context, builder)
        glyf__ygybk.data = data_tuple
        glyf__ygybk.null_values = null_values
        context.nrt.incref(builder, signature.args[0], data_tuple)
        context.nrt.incref(builder, signature.args[1], null_values)
        return glyf__ygybk._getvalue()
    sig = NullableTupleType(data_tuple, null_values)(data_tuple, null_values)
    return sig, codegen


@box(NullableTupleType)
def box_nullable_tuple(typ, val, c):
    ikcaa__xcw = cgutils.create_struct_proxy(typ)(c.context, c.builder,
        value=val)
    c.context.nrt.incref(c.builder, typ.tuple_typ, ikcaa__xcw.data)
    c.context.nrt.incref(c.builder, typ.null_typ, ikcaa__xcw.null_values)
    yyo__vsu = c.pyapi.from_native_value(typ.tuple_typ, ikcaa__xcw.data, c.
        env_manager)
    xhng__inba = c.pyapi.from_native_value(typ.null_typ, ikcaa__xcw.
        null_values, c.env_manager)
    anee__hes = c.context.get_constant(types.int64, len(typ.tuple_typ))
    lqix__jcyny = c.pyapi.list_new(anee__hes)
    with cgutils.for_range(c.builder, anee__hes) as pxsz__ofpe:
        i = pxsz__ofpe.index
        idmb__gpwn = c.pyapi.long_from_longlong(i)
        iekr__xtr = c.pyapi.object_getitem(xhng__inba, idmb__gpwn)
        ghhh__rwtrx = c.pyapi.to_native_value(types.bool_, iekr__xtr).value
        with c.builder.if_else(ghhh__rwtrx) as (trulx__ick, ocql__wso):
            with trulx__ick:
                c.pyapi.list_setitem(lqix__jcyny, i, c.pyapi.make_none())
            with ocql__wso:
                kqp__cepy = c.pyapi.object_getitem(yyo__vsu, idmb__gpwn)
                c.pyapi.list_setitem(lqix__jcyny, i, kqp__cepy)
        c.pyapi.decref(idmb__gpwn)
        c.pyapi.decref(iekr__xtr)
    pgqmg__ahb = c.pyapi.unserialize(c.pyapi.serialize_object(tuple))
    wwdvl__qgv = c.pyapi.call_function_objargs(pgqmg__ahb, (lqix__jcyny,))
    c.pyapi.decref(yyo__vsu)
    c.pyapi.decref(xhng__inba)
    c.pyapi.decref(pgqmg__ahb)
    c.pyapi.decref(lqix__jcyny)
    c.context.nrt.decref(c.builder, typ, val)
    return wwdvl__qgv


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
    glyf__ygybk = cgutils.create_struct_proxy(sig.args[0])(context, builder,
        value=args[0])
    impl = context.get_function('getiter', sig.return_type(sig.args[0].
        tuple_typ))
    return impl(builder, (glyf__ygybk.data,))


@overload(operator.eq)
def nullable_tuple_eq(val1, val2):
    if not isinstance(val1, NullableTupleType) or not isinstance(val2,
        NullableTupleType):
        return
    if val1 != val2:
        return lambda val1, val2: False
    jdk__thd = 'def impl(val1, val2):\n'
    jdk__thd += '    data_tup1 = val1._data\n'
    jdk__thd += '    null_tup1 = val1._null_values\n'
    jdk__thd += '    data_tup2 = val2._data\n'
    jdk__thd += '    null_tup2 = val2._null_values\n'
    tphn__kbky = val1._tuple_typ
    for i in range(len(tphn__kbky)):
        jdk__thd += f'    null1_{i} = null_tup1[{i}]\n'
        jdk__thd += f'    null2_{i} = null_tup2[{i}]\n'
        jdk__thd += f'    data1_{i} = data_tup1[{i}]\n'
        jdk__thd += f'    data2_{i} = data_tup2[{i}]\n'
        jdk__thd += f'    if null1_{i} != null2_{i}:\n'
        jdk__thd += '        return False\n'
        jdk__thd += f'    if null1_{i} and (data1_{i} != data2_{i}):\n'
        jdk__thd += f'        return False\n'
    jdk__thd += f'    return True\n'
    onfe__sftbx = {}
    exec(jdk__thd, {}, onfe__sftbx)
    impl = onfe__sftbx['impl']
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
    jdk__thd = 'def impl(nullable_tup):\n'
    jdk__thd += '    data_tup = nullable_tup._data\n'
    jdk__thd += '    null_tup = nullable_tup._null_values\n'
    jdk__thd += '    tl = numba.cpython.hashing._Py_uhash_t(len(data_tup))\n'
    jdk__thd += '    acc = _PyHASH_XXPRIME_5\n'
    tphn__kbky = nullable_tup._tuple_typ
    for i in range(len(tphn__kbky)):
        jdk__thd += f'    null_val_{i} = null_tup[{i}]\n'
        jdk__thd += f'    null_lane_{i} = hash(null_val_{i})\n'
        jdk__thd += (
            f'    if null_lane_{i} == numba.cpython.hashing._Py_uhash_t(-1):\n'
            )
        jdk__thd += '        return -1\n'
        jdk__thd += f'    acc += null_lane_{i} * _PyHASH_XXPRIME_2\n'
        jdk__thd += '    acc = numba.cpython.hashing._PyHASH_XXROTATE(acc)\n'
        jdk__thd += '    acc *= _PyHASH_XXPRIME_1\n'
        jdk__thd += f'    if not null_val_{i}:\n'
        jdk__thd += f'        lane_{i} = hash(data_tup[{i}])\n'
        jdk__thd += (
            f'        if lane_{i} == numba.cpython.hashing._Py_uhash_t(-1):\n')
        jdk__thd += f'            return -1\n'
        jdk__thd += f'        acc += lane_{i} * _PyHASH_XXPRIME_2\n'
        jdk__thd += (
            '        acc = numba.cpython.hashing._PyHASH_XXROTATE(acc)\n')
        jdk__thd += '        acc *= _PyHASH_XXPRIME_1\n'
    jdk__thd += """    acc += tl ^ (_PyHASH_XXPRIME_5 ^ numba.cpython.hashing._Py_uhash_t(3527539))
"""
    jdk__thd += '    if acc == numba.cpython.hashing._Py_uhash_t(-1):\n'
    jdk__thd += (
        '        return numba.cpython.hashing.process_return(1546275796)\n')
    jdk__thd += '    return numba.cpython.hashing.process_return(acc)\n'
    onfe__sftbx = {}
    exec(jdk__thd, {'numba': numba, '_PyHASH_XXPRIME_1': _PyHASH_XXPRIME_1,
        '_PyHASH_XXPRIME_2': _PyHASH_XXPRIME_2, '_PyHASH_XXPRIME_5':
        _PyHASH_XXPRIME_5}, onfe__sftbx)
    impl = onfe__sftbx['impl']
    return impl
