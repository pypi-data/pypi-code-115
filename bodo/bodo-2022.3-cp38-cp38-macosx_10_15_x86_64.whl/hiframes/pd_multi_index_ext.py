"""Support for MultiIndex type of Pandas
"""
import operator
import numba
import pandas as pd
from numba.core import cgutils, types
from numba.extending import NativeValue, box, intrinsic, lower_builtin, make_attribute_wrapper, models, overload, register_model, typeof_impl, unbox
from bodo.utils.conversion import ensure_contig_if_np
from bodo.utils.typing import BodoError, check_unsupported_args, dtype_to_array_type, get_val_type_maybe_str_literal, is_overload_none


class MultiIndexType(types.Type):

    def __init__(self, array_types, names_typ=None, name_typ=None):
        names_typ = (types.none,) * len(array_types
            ) if names_typ is None else names_typ
        name_typ = types.none if name_typ is None else name_typ
        self.array_types = array_types
        self.names_typ = names_typ
        self.name_typ = name_typ
        super(MultiIndexType, self).__init__(name=
            'MultiIndexType({}, {}, {})'.format(array_types, names_typ,
            name_typ))
    ndim = 1

    def copy(self):
        return MultiIndexType(self.array_types, self.names_typ, self.name_typ)

    @property
    def nlevels(self):
        return len(self.array_types)

    @property
    def mangling_args(self):
        return self.__class__.__name__, (self._code,)


@register_model(MultiIndexType)
class MultiIndexModel(models.StructModel):

    def __init__(self, dmm, fe_type):
        sux__ifpgj = [('data', types.Tuple(fe_type.array_types)), ('names',
            types.Tuple(fe_type.names_typ)), ('name', fe_type.name_typ)]
        super(MultiIndexModel, self).__init__(dmm, fe_type, sux__ifpgj)


make_attribute_wrapper(MultiIndexType, 'data', '_data')
make_attribute_wrapper(MultiIndexType, 'names', '_names')
make_attribute_wrapper(MultiIndexType, 'name', '_name')


@typeof_impl.register(pd.MultiIndex)
def typeof_multi_index(val, c):
    array_types = tuple(numba.typeof(val.levels[khq__xmmp].values) for
        khq__xmmp in range(val.nlevels))
    return MultiIndexType(array_types, tuple(get_val_type_maybe_str_literal
        (fsth__qnmwr) for fsth__qnmwr in val.names), numba.typeof(val.name))


@box(MultiIndexType)
def box_multi_index(typ, val, c):
    xvnr__deo = c.context.insert_const_string(c.builder.module, 'pandas')
    bqof__abd = c.pyapi.import_module_noblock(xvnr__deo)
    oloj__dgb = c.pyapi.object_getattr_string(bqof__abd, 'MultiIndex')
    dwfj__rplzr = cgutils.create_struct_proxy(typ)(c.context, c.builder, val)
    c.context.nrt.incref(c.builder, types.Tuple(typ.array_types),
        dwfj__rplzr.data)
    aac__efeo = c.pyapi.from_native_value(types.Tuple(typ.array_types),
        dwfj__rplzr.data, c.env_manager)
    c.context.nrt.incref(c.builder, types.Tuple(typ.names_typ), dwfj__rplzr
        .names)
    ykkuu__una = c.pyapi.from_native_value(types.Tuple(typ.names_typ),
        dwfj__rplzr.names, c.env_manager)
    c.context.nrt.incref(c.builder, typ.name_typ, dwfj__rplzr.name)
    xmh__kok = c.pyapi.from_native_value(typ.name_typ, dwfj__rplzr.name, c.
        env_manager)
    uwwgk__bhi = c.pyapi.borrow_none()
    diqlz__ttdt = c.pyapi.call_method(oloj__dgb, 'from_arrays', (aac__efeo,
        uwwgk__bhi, ykkuu__una))
    c.pyapi.object_setattr_string(diqlz__ttdt, 'name', xmh__kok)
    c.pyapi.decref(aac__efeo)
    c.pyapi.decref(ykkuu__una)
    c.pyapi.decref(xmh__kok)
    c.pyapi.decref(bqof__abd)
    c.pyapi.decref(oloj__dgb)
    c.context.nrt.decref(c.builder, typ, val)
    return diqlz__ttdt


@unbox(MultiIndexType)
def unbox_multi_index(typ, val, c):
    cudzl__xnleb = []
    crp__ifnc = []
    for khq__xmmp in range(typ.nlevels):
        svgp__hxpqo = c.pyapi.unserialize(c.pyapi.serialize_object(khq__xmmp))
        ipa__ynov = c.pyapi.call_method(val, 'get_level_values', (svgp__hxpqo,)
            )
        kli__xlw = c.pyapi.object_getattr_string(ipa__ynov, 'values')
        c.pyapi.decref(ipa__ynov)
        c.pyapi.decref(svgp__hxpqo)
        wqozv__kbvmz = c.pyapi.to_native_value(typ.array_types[khq__xmmp],
            kli__xlw).value
        cudzl__xnleb.append(wqozv__kbvmz)
        crp__ifnc.append(kli__xlw)
    if isinstance(types.Tuple(typ.array_types), types.UniTuple):
        data = cgutils.pack_array(c.builder, cudzl__xnleb)
    else:
        data = cgutils.pack_struct(c.builder, cudzl__xnleb)
    ykkuu__una = c.pyapi.object_getattr_string(val, 'names')
    vsc__mlc = c.pyapi.unserialize(c.pyapi.serialize_object(tuple))
    mstc__mpat = c.pyapi.call_function_objargs(vsc__mlc, (ykkuu__una,))
    names = c.pyapi.to_native_value(types.Tuple(typ.names_typ), mstc__mpat
        ).value
    xmh__kok = c.pyapi.object_getattr_string(val, 'name')
    name = c.pyapi.to_native_value(typ.name_typ, xmh__kok).value
    dwfj__rplzr = cgutils.create_struct_proxy(typ)(c.context, c.builder)
    dwfj__rplzr.data = data
    dwfj__rplzr.names = names
    dwfj__rplzr.name = name
    for kli__xlw in crp__ifnc:
        c.pyapi.decref(kli__xlw)
    c.pyapi.decref(ykkuu__una)
    c.pyapi.decref(vsc__mlc)
    c.pyapi.decref(mstc__mpat)
    c.pyapi.decref(xmh__kok)
    return NativeValue(dwfj__rplzr._getvalue())


def from_product_error_checking(iterables, sortorder, names):
    kjhug__pspdr = 'pandas.MultiIndex.from_product'
    eqstf__lyhr = dict(sortorder=sortorder)
    gml__aqkyz = dict(sortorder=None)
    check_unsupported_args(kjhug__pspdr, eqstf__lyhr, gml__aqkyz,
        package_name='pandas', module_name='Index')
    if not (is_overload_none(names) or isinstance(names, types.BaseTuple)):
        raise BodoError(f'{kjhug__pspdr}: names must be None or a tuple.')
    elif not isinstance(iterables, types.BaseTuple):
        raise BodoError(f'{kjhug__pspdr}: iterables must be a tuple.')
    elif not is_overload_none(names) and len(iterables) != len(names):
        raise BodoError(
            f'{kjhug__pspdr}: iterables and names must be of the same length.')


def from_product(iterable, sortorder=None, names=None):
    pass


@overload(from_product)
def from_product_overload(iterables, sortorder=None, names=None):
    from_product_error_checking(iterables, sortorder, names)
    array_types = tuple(dtype_to_array_type(iterable.dtype) for iterable in
        iterables)
    if is_overload_none(names):
        names_typ = tuple([types.none] * len(iterables))
    else:
        names_typ = names.types
    squ__oimb = MultiIndexType(array_types, names_typ)
    jrw__por = f'from_product_multiindex{numba.core.ir_utils.next_label()}'
    setattr(types, jrw__por, squ__oimb)
    rmuog__yqkye = f"""
def impl(iterables, sortorder=None, names=None):
    with numba.objmode(mi='{jrw__por}'):
        mi = pd.MultiIndex.from_product(iterables, names=names)
    return mi
"""
    ufqby__ndom = {}
    exec(rmuog__yqkye, globals(), ufqby__ndom)
    kaqve__urp = ufqby__ndom['impl']
    return kaqve__urp


@intrinsic
def init_multi_index(typingctx, data, names, name=None):
    name = types.none if name is None else name
    names = types.Tuple(names.types)

    def codegen(context, builder, signature, args):
        uzqfa__lrzcf, qgg__aojw, vaj__itvbq = args
        luym__qfuu = cgutils.create_struct_proxy(signature.return_type)(context
            , builder)
        luym__qfuu.data = uzqfa__lrzcf
        luym__qfuu.names = qgg__aojw
        luym__qfuu.name = vaj__itvbq
        context.nrt.incref(builder, signature.args[0], uzqfa__lrzcf)
        context.nrt.incref(builder, signature.args[1], qgg__aojw)
        context.nrt.incref(builder, signature.args[2], vaj__itvbq)
        return luym__qfuu._getvalue()
    bcoh__thaz = MultiIndexType(data.types, names.types, name)
    return bcoh__thaz(data, names, name), codegen


@overload(len, no_unliteral=True)
def overload_len_pd_multiindex(A):
    if isinstance(A, MultiIndexType):
        return lambda A: len(A._data[0])


@overload(operator.getitem, no_unliteral=True)
def overload_multi_index_getitem(I, ind):
    if not isinstance(I, MultiIndexType):
        return
    if not isinstance(ind, types.Integer):
        qimtp__bseec = len(I.array_types)
        rmuog__yqkye = 'def impl(I, ind):\n'
        rmuog__yqkye += '  data = I._data\n'
        rmuog__yqkye += (
            '  return init_multi_index(({},), I._names, I._name)\n'.format(
            ', '.join(f'ensure_contig_if_np(data[{khq__xmmp}][ind])' for
            khq__xmmp in range(qimtp__bseec))))
        ufqby__ndom = {}
        exec(rmuog__yqkye, {'init_multi_index': init_multi_index,
            'ensure_contig_if_np': ensure_contig_if_np}, ufqby__ndom)
        kaqve__urp = ufqby__ndom['impl']
        return kaqve__urp


@lower_builtin(operator.is_, MultiIndexType, MultiIndexType)
def multi_index_is(context, builder, sig, args):
    hzah__sfh, tayz__iiii = sig.args
    if hzah__sfh != tayz__iiii:
        return cgutils.false_bit

    def index_is_impl(a, b):
        return (a._data is b._data and a._names is b._names and a._name is
            b._name)
    return context.compile_internal(builder, index_is_impl, sig, args)
