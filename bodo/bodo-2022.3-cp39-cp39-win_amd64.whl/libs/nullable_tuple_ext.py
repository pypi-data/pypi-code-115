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
        ueth__hvd = [('data', fe_type.tuple_typ), ('null_values', fe_type.
            null_typ)]
        super(NullableTupleModel, self).__init__(dmm, fe_type, ueth__hvd)


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
        vqclq__zztt = cgutils.create_struct_proxy(signature.return_type)(
            context, builder)
        vqclq__zztt.data = data_tuple
        vqclq__zztt.null_values = null_values
        context.nrt.incref(builder, signature.args[0], data_tuple)
        context.nrt.incref(builder, signature.args[1], null_values)
        return vqclq__zztt._getvalue()
    sig = NullableTupleType(data_tuple, null_values)(data_tuple, null_values)
    return sig, codegen


@box(NullableTupleType)
def box_nullable_tuple(typ, val, c):
    xncfb__hmo = cgutils.create_struct_proxy(typ)(c.context, c.builder,
        value=val)
    c.context.nrt.incref(c.builder, typ.tuple_typ, xncfb__hmo.data)
    c.context.nrt.incref(c.builder, typ.null_typ, xncfb__hmo.null_values)
    tyzl__gtoa = c.pyapi.from_native_value(typ.tuple_typ, xncfb__hmo.data,
        c.env_manager)
    fplz__mwo = c.pyapi.from_native_value(typ.null_typ, xncfb__hmo.
        null_values, c.env_manager)
    rhh__odi = c.context.get_constant(types.int64, len(typ.tuple_typ))
    eck__idatt = c.pyapi.list_new(rhh__odi)
    with cgutils.for_range(c.builder, rhh__odi) as oknen__egg:
        i = oknen__egg.index
        edgal__pje = c.pyapi.long_from_longlong(i)
        xcyym__txpu = c.pyapi.object_getitem(fplz__mwo, edgal__pje)
        ucxa__gbyah = c.pyapi.to_native_value(types.bool_, xcyym__txpu).value
        with c.builder.if_else(ucxa__gbyah) as (rgwb__yzkt, ftwi__qkg):
            with rgwb__yzkt:
                c.pyapi.list_setitem(eck__idatt, i, c.pyapi.make_none())
            with ftwi__qkg:
                eaufj__llq = c.pyapi.object_getitem(tyzl__gtoa, edgal__pje)
                c.pyapi.list_setitem(eck__idatt, i, eaufj__llq)
        c.pyapi.decref(edgal__pje)
        c.pyapi.decref(xcyym__txpu)
    zxf__jogs = c.pyapi.unserialize(c.pyapi.serialize_object(tuple))
    jog__yfz = c.pyapi.call_function_objargs(zxf__jogs, (eck__idatt,))
    c.pyapi.decref(tyzl__gtoa)
    c.pyapi.decref(fplz__mwo)
    c.pyapi.decref(zxf__jogs)
    c.pyapi.decref(eck__idatt)
    c.context.nrt.decref(c.builder, typ, val)
    return jog__yfz


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
    vqclq__zztt = cgutils.create_struct_proxy(sig.args[0])(context, builder,
        value=args[0])
    impl = context.get_function('getiter', sig.return_type(sig.args[0].
        tuple_typ))
    return impl(builder, (vqclq__zztt.data,))


@overload(operator.eq)
def nullable_tuple_eq(val1, val2):
    if not isinstance(val1, NullableTupleType) or not isinstance(val2,
        NullableTupleType):
        return
    if val1 != val2:
        return lambda val1, val2: False
    hbg__bbxtc = 'def impl(val1, val2):\n'
    hbg__bbxtc += '    data_tup1 = val1._data\n'
    hbg__bbxtc += '    null_tup1 = val1._null_values\n'
    hbg__bbxtc += '    data_tup2 = val2._data\n'
    hbg__bbxtc += '    null_tup2 = val2._null_values\n'
    recby__xtjb = val1._tuple_typ
    for i in range(len(recby__xtjb)):
        hbg__bbxtc += f'    null1_{i} = null_tup1[{i}]\n'
        hbg__bbxtc += f'    null2_{i} = null_tup2[{i}]\n'
        hbg__bbxtc += f'    data1_{i} = data_tup1[{i}]\n'
        hbg__bbxtc += f'    data2_{i} = data_tup2[{i}]\n'
        hbg__bbxtc += f'    if null1_{i} != null2_{i}:\n'
        hbg__bbxtc += '        return False\n'
        hbg__bbxtc += f'    if null1_{i} and (data1_{i} != data2_{i}):\n'
        hbg__bbxtc += f'        return False\n'
    hbg__bbxtc += f'    return True\n'
    fgxs__gqn = {}
    exec(hbg__bbxtc, {}, fgxs__gqn)
    impl = fgxs__gqn['impl']
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
    hbg__bbxtc = 'def impl(nullable_tup):\n'
    hbg__bbxtc += '    data_tup = nullable_tup._data\n'
    hbg__bbxtc += '    null_tup = nullable_tup._null_values\n'
    hbg__bbxtc += '    tl = numba.cpython.hashing._Py_uhash_t(len(data_tup))\n'
    hbg__bbxtc += '    acc = _PyHASH_XXPRIME_5\n'
    recby__xtjb = nullable_tup._tuple_typ
    for i in range(len(recby__xtjb)):
        hbg__bbxtc += f'    null_val_{i} = null_tup[{i}]\n'
        hbg__bbxtc += f'    null_lane_{i} = hash(null_val_{i})\n'
        hbg__bbxtc += (
            f'    if null_lane_{i} == numba.cpython.hashing._Py_uhash_t(-1):\n'
            )
        hbg__bbxtc += '        return -1\n'
        hbg__bbxtc += f'    acc += null_lane_{i} * _PyHASH_XXPRIME_2\n'
        hbg__bbxtc += '    acc = numba.cpython.hashing._PyHASH_XXROTATE(acc)\n'
        hbg__bbxtc += '    acc *= _PyHASH_XXPRIME_1\n'
        hbg__bbxtc += f'    if not null_val_{i}:\n'
        hbg__bbxtc += f'        lane_{i} = hash(data_tup[{i}])\n'
        hbg__bbxtc += (
            f'        if lane_{i} == numba.cpython.hashing._Py_uhash_t(-1):\n')
        hbg__bbxtc += f'            return -1\n'
        hbg__bbxtc += f'        acc += lane_{i} * _PyHASH_XXPRIME_2\n'
        hbg__bbxtc += (
            '        acc = numba.cpython.hashing._PyHASH_XXROTATE(acc)\n')
        hbg__bbxtc += '        acc *= _PyHASH_XXPRIME_1\n'
    hbg__bbxtc += """    acc += tl ^ (_PyHASH_XXPRIME_5 ^ numba.cpython.hashing._Py_uhash_t(3527539))
"""
    hbg__bbxtc += '    if acc == numba.cpython.hashing._Py_uhash_t(-1):\n'
    hbg__bbxtc += (
        '        return numba.cpython.hashing.process_return(1546275796)\n')
    hbg__bbxtc += '    return numba.cpython.hashing.process_return(acc)\n'
    fgxs__gqn = {}
    exec(hbg__bbxtc, {'numba': numba, '_PyHASH_XXPRIME_1':
        _PyHASH_XXPRIME_1, '_PyHASH_XXPRIME_2': _PyHASH_XXPRIME_2,
        '_PyHASH_XXPRIME_5': _PyHASH_XXPRIME_5}, fgxs__gqn)
    impl = fgxs__gqn['impl']
    return impl
