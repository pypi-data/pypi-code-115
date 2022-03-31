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
        hbpk__tqg = [('data', types.Tuple(fe_type.array_types)), ('names',
            types.Tuple(fe_type.names_typ)), ('name', fe_type.name_typ)]
        super(MultiIndexModel, self).__init__(dmm, fe_type, hbpk__tqg)


make_attribute_wrapper(MultiIndexType, 'data', '_data')
make_attribute_wrapper(MultiIndexType, 'names', '_names')
make_attribute_wrapper(MultiIndexType, 'name', '_name')


@typeof_impl.register(pd.MultiIndex)
def typeof_multi_index(val, c):
    array_types = tuple(numba.typeof(val.levels[wqbly__aul].values) for
        wqbly__aul in range(val.nlevels))
    return MultiIndexType(array_types, tuple(get_val_type_maybe_str_literal
        (hboe__xkfxv) for hboe__xkfxv in val.names), numba.typeof(val.name))


@box(MultiIndexType)
def box_multi_index(typ, val, c):
    aujcs__ddoc = c.context.insert_const_string(c.builder.module, 'pandas')
    znw__tepas = c.pyapi.import_module_noblock(aujcs__ddoc)
    jwovz__eym = c.pyapi.object_getattr_string(znw__tepas, 'MultiIndex')
    ghms__hlik = cgutils.create_struct_proxy(typ)(c.context, c.builder, val)
    c.context.nrt.incref(c.builder, types.Tuple(typ.array_types),
        ghms__hlik.data)
    ovu__gmh = c.pyapi.from_native_value(types.Tuple(typ.array_types),
        ghms__hlik.data, c.env_manager)
    c.context.nrt.incref(c.builder, types.Tuple(typ.names_typ), ghms__hlik.
        names)
    byxn__mvqg = c.pyapi.from_native_value(types.Tuple(typ.names_typ),
        ghms__hlik.names, c.env_manager)
    c.context.nrt.incref(c.builder, typ.name_typ, ghms__hlik.name)
    qgqrk__gur = c.pyapi.from_native_value(typ.name_typ, ghms__hlik.name, c
        .env_manager)
    iyajr__phyi = c.pyapi.borrow_none()
    mvy__hyv = c.pyapi.call_method(jwovz__eym, 'from_arrays', (ovu__gmh,
        iyajr__phyi, byxn__mvqg))
    c.pyapi.object_setattr_string(mvy__hyv, 'name', qgqrk__gur)
    c.pyapi.decref(ovu__gmh)
    c.pyapi.decref(byxn__mvqg)
    c.pyapi.decref(qgqrk__gur)
    c.pyapi.decref(znw__tepas)
    c.pyapi.decref(jwovz__eym)
    c.context.nrt.decref(c.builder, typ, val)
    return mvy__hyv


@unbox(MultiIndexType)
def unbox_multi_index(typ, val, c):
    div__ddnzi = []
    beh__esu = []
    for wqbly__aul in range(typ.nlevels):
        cnmh__nxb = c.pyapi.unserialize(c.pyapi.serialize_object(wqbly__aul))
        qfj__udt = c.pyapi.call_method(val, 'get_level_values', (cnmh__nxb,))
        vla__vxvve = c.pyapi.object_getattr_string(qfj__udt, 'values')
        c.pyapi.decref(qfj__udt)
        c.pyapi.decref(cnmh__nxb)
        hlacj__cmom = c.pyapi.to_native_value(typ.array_types[wqbly__aul],
            vla__vxvve).value
        div__ddnzi.append(hlacj__cmom)
        beh__esu.append(vla__vxvve)
    if isinstance(types.Tuple(typ.array_types), types.UniTuple):
        data = cgutils.pack_array(c.builder, div__ddnzi)
    else:
        data = cgutils.pack_struct(c.builder, div__ddnzi)
    byxn__mvqg = c.pyapi.object_getattr_string(val, 'names')
    pyxex__xpjhh = c.pyapi.unserialize(c.pyapi.serialize_object(tuple))
    nwoak__bhzwu = c.pyapi.call_function_objargs(pyxex__xpjhh, (byxn__mvqg,))
    names = c.pyapi.to_native_value(types.Tuple(typ.names_typ), nwoak__bhzwu
        ).value
    qgqrk__gur = c.pyapi.object_getattr_string(val, 'name')
    name = c.pyapi.to_native_value(typ.name_typ, qgqrk__gur).value
    ghms__hlik = cgutils.create_struct_proxy(typ)(c.context, c.builder)
    ghms__hlik.data = data
    ghms__hlik.names = names
    ghms__hlik.name = name
    for vla__vxvve in beh__esu:
        c.pyapi.decref(vla__vxvve)
    c.pyapi.decref(byxn__mvqg)
    c.pyapi.decref(pyxex__xpjhh)
    c.pyapi.decref(nwoak__bhzwu)
    c.pyapi.decref(qgqrk__gur)
    return NativeValue(ghms__hlik._getvalue())


def from_product_error_checking(iterables, sortorder, names):
    dnuc__umjyb = 'pandas.MultiIndex.from_product'
    iwxwy__ngq = dict(sortorder=sortorder)
    itg__mkghl = dict(sortorder=None)
    check_unsupported_args(dnuc__umjyb, iwxwy__ngq, itg__mkghl,
        package_name='pandas', module_name='Index')
    if not (is_overload_none(names) or isinstance(names, types.BaseTuple)):
        raise BodoError(f'{dnuc__umjyb}: names must be None or a tuple.')
    elif not isinstance(iterables, types.BaseTuple):
        raise BodoError(f'{dnuc__umjyb}: iterables must be a tuple.')
    elif not is_overload_none(names) and len(iterables) != len(names):
        raise BodoError(
            f'{dnuc__umjyb}: iterables and names must be of the same length.')


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
    cwf__ebd = MultiIndexType(array_types, names_typ)
    bmm__kxhzf = f'from_product_multiindex{numba.core.ir_utils.next_label()}'
    setattr(types, bmm__kxhzf, cwf__ebd)
    mhl__urz = f"""
def impl(iterables, sortorder=None, names=None):
    with numba.objmode(mi='{bmm__kxhzf}'):
        mi = pd.MultiIndex.from_product(iterables, names=names)
    return mi
"""
    njl__prdmj = {}
    exec(mhl__urz, globals(), njl__prdmj)
    xpz__wmhie = njl__prdmj['impl']
    return xpz__wmhie


@intrinsic
def init_multi_index(typingctx, data, names, name=None):
    name = types.none if name is None else name
    names = types.Tuple(names.types)

    def codegen(context, builder, signature, args):
        ssenr__ljzrg, vytbp__akzs, dqayk__dhnpn = args
        pwj__hkmi = cgutils.create_struct_proxy(signature.return_type)(context,
            builder)
        pwj__hkmi.data = ssenr__ljzrg
        pwj__hkmi.names = vytbp__akzs
        pwj__hkmi.name = dqayk__dhnpn
        context.nrt.incref(builder, signature.args[0], ssenr__ljzrg)
        context.nrt.incref(builder, signature.args[1], vytbp__akzs)
        context.nrt.incref(builder, signature.args[2], dqayk__dhnpn)
        return pwj__hkmi._getvalue()
    pzrk__usbpa = MultiIndexType(data.types, names.types, name)
    return pzrk__usbpa(data, names, name), codegen


@overload(len, no_unliteral=True)
def overload_len_pd_multiindex(A):
    if isinstance(A, MultiIndexType):
        return lambda A: len(A._data[0])


@overload(operator.getitem, no_unliteral=True)
def overload_multi_index_getitem(I, ind):
    if not isinstance(I, MultiIndexType):
        return
    if not isinstance(ind, types.Integer):
        ftlz__sfi = len(I.array_types)
        mhl__urz = 'def impl(I, ind):\n'
        mhl__urz += '  data = I._data\n'
        mhl__urz += ('  return init_multi_index(({},), I._names, I._name)\n'
            .format(', '.join(
            f'ensure_contig_if_np(data[{wqbly__aul}][ind])' for wqbly__aul in
            range(ftlz__sfi))))
        njl__prdmj = {}
        exec(mhl__urz, {'init_multi_index': init_multi_index,
            'ensure_contig_if_np': ensure_contig_if_np}, njl__prdmj)
        xpz__wmhie = njl__prdmj['impl']
        return xpz__wmhie


@lower_builtin(operator.is_, MultiIndexType, MultiIndexType)
def multi_index_is(context, builder, sig, args):
    wpltb__mobor, ixkw__yobgg = sig.args
    if wpltb__mobor != ixkw__yobgg:
        return cgutils.false_bit

    def index_is_impl(a, b):
        return (a._data is b._data and a._names is b._names and a._name is
            b._name)
    return context.compile_internal(builder, index_is_impl, sig, args)
