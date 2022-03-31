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
        aqs__mjw = [('data', types.Tuple(fe_type.array_types)), ('names',
            types.Tuple(fe_type.names_typ)), ('name', fe_type.name_typ)]
        super(MultiIndexModel, self).__init__(dmm, fe_type, aqs__mjw)


make_attribute_wrapper(MultiIndexType, 'data', '_data')
make_attribute_wrapper(MultiIndexType, 'names', '_names')
make_attribute_wrapper(MultiIndexType, 'name', '_name')


@typeof_impl.register(pd.MultiIndex)
def typeof_multi_index(val, c):
    array_types = tuple(numba.typeof(val.levels[jwiqj__gqzts].values) for
        jwiqj__gqzts in range(val.nlevels))
    return MultiIndexType(array_types, tuple(get_val_type_maybe_str_literal
        (xwf__hbrl) for xwf__hbrl in val.names), numba.typeof(val.name))


@box(MultiIndexType)
def box_multi_index(typ, val, c):
    vnvoj__nuev = c.context.insert_const_string(c.builder.module, 'pandas')
    irruk__vupx = c.pyapi.import_module_noblock(vnvoj__nuev)
    rjuhp__ghx = c.pyapi.object_getattr_string(irruk__vupx, 'MultiIndex')
    scjha__zwfb = cgutils.create_struct_proxy(typ)(c.context, c.builder, val)
    c.context.nrt.incref(c.builder, types.Tuple(typ.array_types),
        scjha__zwfb.data)
    koc__qsl = c.pyapi.from_native_value(types.Tuple(typ.array_types),
        scjha__zwfb.data, c.env_manager)
    c.context.nrt.incref(c.builder, types.Tuple(typ.names_typ), scjha__zwfb
        .names)
    zke__cwzaf = c.pyapi.from_native_value(types.Tuple(typ.names_typ),
        scjha__zwfb.names, c.env_manager)
    c.context.nrt.incref(c.builder, typ.name_typ, scjha__zwfb.name)
    odzr__rkzps = c.pyapi.from_native_value(typ.name_typ, scjha__zwfb.name,
        c.env_manager)
    cskb__ojfjv = c.pyapi.borrow_none()
    mpd__dinn = c.pyapi.call_method(rjuhp__ghx, 'from_arrays', (koc__qsl,
        cskb__ojfjv, zke__cwzaf))
    c.pyapi.object_setattr_string(mpd__dinn, 'name', odzr__rkzps)
    c.pyapi.decref(koc__qsl)
    c.pyapi.decref(zke__cwzaf)
    c.pyapi.decref(odzr__rkzps)
    c.pyapi.decref(irruk__vupx)
    c.pyapi.decref(rjuhp__ghx)
    c.context.nrt.decref(c.builder, typ, val)
    return mpd__dinn


@unbox(MultiIndexType)
def unbox_multi_index(typ, val, c):
    wkfsb__qpk = []
    til__xau = []
    for jwiqj__gqzts in range(typ.nlevels):
        wpvmu__aipyi = c.pyapi.unserialize(c.pyapi.serialize_object(
            jwiqj__gqzts))
        nuiu__gntki = c.pyapi.call_method(val, 'get_level_values', (
            wpvmu__aipyi,))
        cxb__yfd = c.pyapi.object_getattr_string(nuiu__gntki, 'values')
        c.pyapi.decref(nuiu__gntki)
        c.pyapi.decref(wpvmu__aipyi)
        own__pno = c.pyapi.to_native_value(typ.array_types[jwiqj__gqzts],
            cxb__yfd).value
        wkfsb__qpk.append(own__pno)
        til__xau.append(cxb__yfd)
    if isinstance(types.Tuple(typ.array_types), types.UniTuple):
        data = cgutils.pack_array(c.builder, wkfsb__qpk)
    else:
        data = cgutils.pack_struct(c.builder, wkfsb__qpk)
    zke__cwzaf = c.pyapi.object_getattr_string(val, 'names')
    ixk__rrxtk = c.pyapi.unserialize(c.pyapi.serialize_object(tuple))
    gpdv__kosm = c.pyapi.call_function_objargs(ixk__rrxtk, (zke__cwzaf,))
    names = c.pyapi.to_native_value(types.Tuple(typ.names_typ), gpdv__kosm
        ).value
    odzr__rkzps = c.pyapi.object_getattr_string(val, 'name')
    name = c.pyapi.to_native_value(typ.name_typ, odzr__rkzps).value
    scjha__zwfb = cgutils.create_struct_proxy(typ)(c.context, c.builder)
    scjha__zwfb.data = data
    scjha__zwfb.names = names
    scjha__zwfb.name = name
    for cxb__yfd in til__xau:
        c.pyapi.decref(cxb__yfd)
    c.pyapi.decref(zke__cwzaf)
    c.pyapi.decref(ixk__rrxtk)
    c.pyapi.decref(gpdv__kosm)
    c.pyapi.decref(odzr__rkzps)
    return NativeValue(scjha__zwfb._getvalue())


def from_product_error_checking(iterables, sortorder, names):
    xue__wxjcn = 'pandas.MultiIndex.from_product'
    vvqc__thc = dict(sortorder=sortorder)
    rpf__tosb = dict(sortorder=None)
    check_unsupported_args(xue__wxjcn, vvqc__thc, rpf__tosb, package_name=
        'pandas', module_name='Index')
    if not (is_overload_none(names) or isinstance(names, types.BaseTuple)):
        raise BodoError(f'{xue__wxjcn}: names must be None or a tuple.')
    elif not isinstance(iterables, types.BaseTuple):
        raise BodoError(f'{xue__wxjcn}: iterables must be a tuple.')
    elif not is_overload_none(names) and len(iterables) != len(names):
        raise BodoError(
            f'{xue__wxjcn}: iterables and names must be of the same length.')


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
    aoisd__blmm = MultiIndexType(array_types, names_typ)
    ats__ubb = f'from_product_multiindex{numba.core.ir_utils.next_label()}'
    setattr(types, ats__ubb, aoisd__blmm)
    myhi__urlo = f"""
def impl(iterables, sortorder=None, names=None):
    with numba.objmode(mi='{ats__ubb}'):
        mi = pd.MultiIndex.from_product(iterables, names=names)
    return mi
"""
    zcln__udv = {}
    exec(myhi__urlo, globals(), zcln__udv)
    yquuw__womf = zcln__udv['impl']
    return yquuw__womf


@intrinsic
def init_multi_index(typingctx, data, names, name=None):
    name = types.none if name is None else name
    names = types.Tuple(names.types)

    def codegen(context, builder, signature, args):
        zevp__lhr, jrpe__xss, zqjk__sla = args
        aiy__uxusn = cgutils.create_struct_proxy(signature.return_type)(context
            , builder)
        aiy__uxusn.data = zevp__lhr
        aiy__uxusn.names = jrpe__xss
        aiy__uxusn.name = zqjk__sla
        context.nrt.incref(builder, signature.args[0], zevp__lhr)
        context.nrt.incref(builder, signature.args[1], jrpe__xss)
        context.nrt.incref(builder, signature.args[2], zqjk__sla)
        return aiy__uxusn._getvalue()
    hsjn__xlwcp = MultiIndexType(data.types, names.types, name)
    return hsjn__xlwcp(data, names, name), codegen


@overload(len, no_unliteral=True)
def overload_len_pd_multiindex(A):
    if isinstance(A, MultiIndexType):
        return lambda A: len(A._data[0])


@overload(operator.getitem, no_unliteral=True)
def overload_multi_index_getitem(I, ind):
    if not isinstance(I, MultiIndexType):
        return
    if not isinstance(ind, types.Integer):
        gief__mpz = len(I.array_types)
        myhi__urlo = 'def impl(I, ind):\n'
        myhi__urlo += '  data = I._data\n'
        myhi__urlo += ('  return init_multi_index(({},), I._names, I._name)\n'
            .format(', '.join(
            f'ensure_contig_if_np(data[{jwiqj__gqzts}][ind])' for
            jwiqj__gqzts in range(gief__mpz))))
        zcln__udv = {}
        exec(myhi__urlo, {'init_multi_index': init_multi_index,
            'ensure_contig_if_np': ensure_contig_if_np}, zcln__udv)
        yquuw__womf = zcln__udv['impl']
        return yquuw__womf


@lower_builtin(operator.is_, MultiIndexType, MultiIndexType)
def multi_index_is(context, builder, sig, args):
    wzgqm__afhf, vhdm__bfywv = sig.args
    if wzgqm__afhf != vhdm__bfywv:
        return cgutils.false_bit

    def index_is_impl(a, b):
        return (a._data is b._data and a._names is b._names and a._name is
            b._name)
    return context.compile_internal(builder, index_is_impl, sig, args)
