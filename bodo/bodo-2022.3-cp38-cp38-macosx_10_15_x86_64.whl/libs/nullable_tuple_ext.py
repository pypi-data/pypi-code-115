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
        azic__kgtp = [('data', fe_type.tuple_typ), ('null_values', fe_type.
            null_typ)]
        super(NullableTupleModel, self).__init__(dmm, fe_type, azic__kgtp)


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
        zpx__tda = cgutils.create_struct_proxy(signature.return_type)(context,
            builder)
        zpx__tda.data = data_tuple
        zpx__tda.null_values = null_values
        context.nrt.incref(builder, signature.args[0], data_tuple)
        context.nrt.incref(builder, signature.args[1], null_values)
        return zpx__tda._getvalue()
    sig = NullableTupleType(data_tuple, null_values)(data_tuple, null_values)
    return sig, codegen


@box(NullableTupleType)
def box_nullable_tuple(typ, val, c):
    ibxax__pupr = cgutils.create_struct_proxy(typ)(c.context, c.builder,
        value=val)
    c.context.nrt.incref(c.builder, typ.tuple_typ, ibxax__pupr.data)
    c.context.nrt.incref(c.builder, typ.null_typ, ibxax__pupr.null_values)
    udh__cmtz = c.pyapi.from_native_value(typ.tuple_typ, ibxax__pupr.data,
        c.env_manager)
    xwgs__ghbaf = c.pyapi.from_native_value(typ.null_typ, ibxax__pupr.
        null_values, c.env_manager)
    ggihy__aztx = c.context.get_constant(types.int64, len(typ.tuple_typ))
    kaoh__bzfb = c.pyapi.list_new(ggihy__aztx)
    with cgutils.for_range(c.builder, ggihy__aztx) as uwwi__zjx:
        i = uwwi__zjx.index
        junsk__hbk = c.pyapi.long_from_longlong(i)
        amfad__axgr = c.pyapi.object_getitem(xwgs__ghbaf, junsk__hbk)
        ojckv__lab = c.pyapi.to_native_value(types.bool_, amfad__axgr).value
        with c.builder.if_else(ojckv__lab) as (wmv__zba, pyzlc__hnzs):
            with wmv__zba:
                c.pyapi.list_setitem(kaoh__bzfb, i, c.pyapi.make_none())
            with pyzlc__hnzs:
                ccesd__gkpsz = c.pyapi.object_getitem(udh__cmtz, junsk__hbk)
                c.pyapi.list_setitem(kaoh__bzfb, i, ccesd__gkpsz)
        c.pyapi.decref(junsk__hbk)
        c.pyapi.decref(amfad__axgr)
    hsqrr__plhbq = c.pyapi.unserialize(c.pyapi.serialize_object(tuple))
    betot__vuns = c.pyapi.call_function_objargs(hsqrr__plhbq, (kaoh__bzfb,))
    c.pyapi.decref(udh__cmtz)
    c.pyapi.decref(xwgs__ghbaf)
    c.pyapi.decref(hsqrr__plhbq)
    c.pyapi.decref(kaoh__bzfb)
    c.context.nrt.decref(c.builder, typ, val)
    return betot__vuns


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
    zpx__tda = cgutils.create_struct_proxy(sig.args[0])(context, builder,
        value=args[0])
    impl = context.get_function('getiter', sig.return_type(sig.args[0].
        tuple_typ))
    return impl(builder, (zpx__tda.data,))


@overload(operator.eq)
def nullable_tuple_eq(val1, val2):
    if not isinstance(val1, NullableTupleType) or not isinstance(val2,
        NullableTupleType):
        return
    if val1 != val2:
        return lambda val1, val2: False
    bbg__lmcqx = 'def impl(val1, val2):\n'
    bbg__lmcqx += '    data_tup1 = val1._data\n'
    bbg__lmcqx += '    null_tup1 = val1._null_values\n'
    bbg__lmcqx += '    data_tup2 = val2._data\n'
    bbg__lmcqx += '    null_tup2 = val2._null_values\n'
    bgh__bec = val1._tuple_typ
    for i in range(len(bgh__bec)):
        bbg__lmcqx += f'    null1_{i} = null_tup1[{i}]\n'
        bbg__lmcqx += f'    null2_{i} = null_tup2[{i}]\n'
        bbg__lmcqx += f'    data1_{i} = data_tup1[{i}]\n'
        bbg__lmcqx += f'    data2_{i} = data_tup2[{i}]\n'
        bbg__lmcqx += f'    if null1_{i} != null2_{i}:\n'
        bbg__lmcqx += '        return False\n'
        bbg__lmcqx += f'    if null1_{i} and (data1_{i} != data2_{i}):\n'
        bbg__lmcqx += f'        return False\n'
    bbg__lmcqx += f'    return True\n'
    rxl__onnmv = {}
    exec(bbg__lmcqx, {}, rxl__onnmv)
    impl = rxl__onnmv['impl']
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
    bbg__lmcqx = 'def impl(nullable_tup):\n'
    bbg__lmcqx += '    data_tup = nullable_tup._data\n'
    bbg__lmcqx += '    null_tup = nullable_tup._null_values\n'
    bbg__lmcqx += '    tl = numba.cpython.hashing._Py_uhash_t(len(data_tup))\n'
    bbg__lmcqx += '    acc = _PyHASH_XXPRIME_5\n'
    bgh__bec = nullable_tup._tuple_typ
    for i in range(len(bgh__bec)):
        bbg__lmcqx += f'    null_val_{i} = null_tup[{i}]\n'
        bbg__lmcqx += f'    null_lane_{i} = hash(null_val_{i})\n'
        bbg__lmcqx += (
            f'    if null_lane_{i} == numba.cpython.hashing._Py_uhash_t(-1):\n'
            )
        bbg__lmcqx += '        return -1\n'
        bbg__lmcqx += f'    acc += null_lane_{i} * _PyHASH_XXPRIME_2\n'
        bbg__lmcqx += '    acc = numba.cpython.hashing._PyHASH_XXROTATE(acc)\n'
        bbg__lmcqx += '    acc *= _PyHASH_XXPRIME_1\n'
        bbg__lmcqx += f'    if not null_val_{i}:\n'
        bbg__lmcqx += f'        lane_{i} = hash(data_tup[{i}])\n'
        bbg__lmcqx += (
            f'        if lane_{i} == numba.cpython.hashing._Py_uhash_t(-1):\n')
        bbg__lmcqx += f'            return -1\n'
        bbg__lmcqx += f'        acc += lane_{i} * _PyHASH_XXPRIME_2\n'
        bbg__lmcqx += (
            '        acc = numba.cpython.hashing._PyHASH_XXROTATE(acc)\n')
        bbg__lmcqx += '        acc *= _PyHASH_XXPRIME_1\n'
    bbg__lmcqx += """    acc += tl ^ (_PyHASH_XXPRIME_5 ^ numba.cpython.hashing._Py_uhash_t(3527539))
"""
    bbg__lmcqx += '    if acc == numba.cpython.hashing._Py_uhash_t(-1):\n'
    bbg__lmcqx += (
        '        return numba.cpython.hashing.process_return(1546275796)\n')
    bbg__lmcqx += '    return numba.cpython.hashing.process_return(acc)\n'
    rxl__onnmv = {}
    exec(bbg__lmcqx, {'numba': numba, '_PyHASH_XXPRIME_1':
        _PyHASH_XXPRIME_1, '_PyHASH_XXPRIME_2': _PyHASH_XXPRIME_2,
        '_PyHASH_XXPRIME_5': _PyHASH_XXPRIME_5}, rxl__onnmv)
    impl = rxl__onnmv['impl']
    return impl
