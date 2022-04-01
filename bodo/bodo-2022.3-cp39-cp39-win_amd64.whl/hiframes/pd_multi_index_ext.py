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
        pvj__vbqwc = [('data', types.Tuple(fe_type.array_types)), ('names',
            types.Tuple(fe_type.names_typ)), ('name', fe_type.name_typ)]
        super(MultiIndexModel, self).__init__(dmm, fe_type, pvj__vbqwc)


make_attribute_wrapper(MultiIndexType, 'data', '_data')
make_attribute_wrapper(MultiIndexType, 'names', '_names')
make_attribute_wrapper(MultiIndexType, 'name', '_name')


@typeof_impl.register(pd.MultiIndex)
def typeof_multi_index(val, c):
    array_types = tuple(numba.typeof(val.levels[cajmk__cnyk].values) for
        cajmk__cnyk in range(val.nlevels))
    return MultiIndexType(array_types, tuple(get_val_type_maybe_str_literal
        (jfqlz__ljw) for jfqlz__ljw in val.names), numba.typeof(val.name))


@box(MultiIndexType)
def box_multi_index(typ, val, c):
    iwyv__yddb = c.context.insert_const_string(c.builder.module, 'pandas')
    hepm__tou = c.pyapi.import_module_noblock(iwyv__yddb)
    gtkl__hvhbe = c.pyapi.object_getattr_string(hepm__tou, 'MultiIndex')
    ackn__bqdk = cgutils.create_struct_proxy(typ)(c.context, c.builder, val)
    c.context.nrt.incref(c.builder, types.Tuple(typ.array_types),
        ackn__bqdk.data)
    rreu__ytjwd = c.pyapi.from_native_value(types.Tuple(typ.array_types),
        ackn__bqdk.data, c.env_manager)
    c.context.nrt.incref(c.builder, types.Tuple(typ.names_typ), ackn__bqdk.
        names)
    hyw__vxe = c.pyapi.from_native_value(types.Tuple(typ.names_typ),
        ackn__bqdk.names, c.env_manager)
    c.context.nrt.incref(c.builder, typ.name_typ, ackn__bqdk.name)
    rghj__gsab = c.pyapi.from_native_value(typ.name_typ, ackn__bqdk.name, c
        .env_manager)
    rhjp__aop = c.pyapi.borrow_none()
    vqs__fyy = c.pyapi.call_method(gtkl__hvhbe, 'from_arrays', (rreu__ytjwd,
        rhjp__aop, hyw__vxe))
    c.pyapi.object_setattr_string(vqs__fyy, 'name', rghj__gsab)
    c.pyapi.decref(rreu__ytjwd)
    c.pyapi.decref(hyw__vxe)
    c.pyapi.decref(rghj__gsab)
    c.pyapi.decref(hepm__tou)
    c.pyapi.decref(gtkl__hvhbe)
    c.context.nrt.decref(c.builder, typ, val)
    return vqs__fyy


@unbox(MultiIndexType)
def unbox_multi_index(typ, val, c):
    anj__jptd = []
    kvkp__mqmbk = []
    for cajmk__cnyk in range(typ.nlevels):
        curx__xjf = c.pyapi.unserialize(c.pyapi.serialize_object(cajmk__cnyk))
        maf__vzdau = c.pyapi.call_method(val, 'get_level_values', (curx__xjf,))
        rgcw__xxpi = c.pyapi.object_getattr_string(maf__vzdau, 'values')
        c.pyapi.decref(maf__vzdau)
        c.pyapi.decref(curx__xjf)
        gjjdd__fagk = c.pyapi.to_native_value(typ.array_types[cajmk__cnyk],
            rgcw__xxpi).value
        anj__jptd.append(gjjdd__fagk)
        kvkp__mqmbk.append(rgcw__xxpi)
    if isinstance(types.Tuple(typ.array_types), types.UniTuple):
        data = cgutils.pack_array(c.builder, anj__jptd)
    else:
        data = cgutils.pack_struct(c.builder, anj__jptd)
    hyw__vxe = c.pyapi.object_getattr_string(val, 'names')
    rczon__hpc = c.pyapi.unserialize(c.pyapi.serialize_object(tuple))
    zvk__owgro = c.pyapi.call_function_objargs(rczon__hpc, (hyw__vxe,))
    names = c.pyapi.to_native_value(types.Tuple(typ.names_typ), zvk__owgro
        ).value
    rghj__gsab = c.pyapi.object_getattr_string(val, 'name')
    name = c.pyapi.to_native_value(typ.name_typ, rghj__gsab).value
    ackn__bqdk = cgutils.create_struct_proxy(typ)(c.context, c.builder)
    ackn__bqdk.data = data
    ackn__bqdk.names = names
    ackn__bqdk.name = name
    for rgcw__xxpi in kvkp__mqmbk:
        c.pyapi.decref(rgcw__xxpi)
    c.pyapi.decref(hyw__vxe)
    c.pyapi.decref(rczon__hpc)
    c.pyapi.decref(zvk__owgro)
    c.pyapi.decref(rghj__gsab)
    return NativeValue(ackn__bqdk._getvalue())


def from_product_error_checking(iterables, sortorder, names):
    etwb__iifgw = 'pandas.MultiIndex.from_product'
    uuj__opu = dict(sortorder=sortorder)
    pmn__uirj = dict(sortorder=None)
    check_unsupported_args(etwb__iifgw, uuj__opu, pmn__uirj, package_name=
        'pandas', module_name='Index')
    if not (is_overload_none(names) or isinstance(names, types.BaseTuple)):
        raise BodoError(f'{etwb__iifgw}: names must be None or a tuple.')
    elif not isinstance(iterables, types.BaseTuple):
        raise BodoError(f'{etwb__iifgw}: iterables must be a tuple.')
    elif not is_overload_none(names) and len(iterables) != len(names):
        raise BodoError(
            f'{etwb__iifgw}: iterables and names must be of the same length.')


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
    tfxsa__rqfbr = MultiIndexType(array_types, names_typ)
    trylb__slcww = f'from_product_multiindex{numba.core.ir_utils.next_label()}'
    setattr(types, trylb__slcww, tfxsa__rqfbr)
    llj__rag = f"""
def impl(iterables, sortorder=None, names=None):
    with numba.objmode(mi='{trylb__slcww}'):
        mi = pd.MultiIndex.from_product(iterables, names=names)
    return mi
"""
    rxoi__ciodu = {}
    exec(llj__rag, globals(), rxoi__ciodu)
    sitmo__pagv = rxoi__ciodu['impl']
    return sitmo__pagv


@intrinsic
def init_multi_index(typingctx, data, names, name=None):
    name = types.none if name is None else name
    names = types.Tuple(names.types)

    def codegen(context, builder, signature, args):
        sfpk__uopn, csu__aqqb, iazan__nuv = args
        iul__ayjie = cgutils.create_struct_proxy(signature.return_type)(context
            , builder)
        iul__ayjie.data = sfpk__uopn
        iul__ayjie.names = csu__aqqb
        iul__ayjie.name = iazan__nuv
        context.nrt.incref(builder, signature.args[0], sfpk__uopn)
        context.nrt.incref(builder, signature.args[1], csu__aqqb)
        context.nrt.incref(builder, signature.args[2], iazan__nuv)
        return iul__ayjie._getvalue()
    zauhr__iea = MultiIndexType(data.types, names.types, name)
    return zauhr__iea(data, names, name), codegen


@overload(len, no_unliteral=True)
def overload_len_pd_multiindex(A):
    if isinstance(A, MultiIndexType):
        return lambda A: len(A._data[0])


@overload(operator.getitem, no_unliteral=True)
def overload_multi_index_getitem(I, ind):
    if not isinstance(I, MultiIndexType):
        return
    if not isinstance(ind, types.Integer):
        gmc__wnrfr = len(I.array_types)
        llj__rag = 'def impl(I, ind):\n'
        llj__rag += '  data = I._data\n'
        llj__rag += ('  return init_multi_index(({},), I._names, I._name)\n'
            .format(', '.join(
            f'ensure_contig_if_np(data[{cajmk__cnyk}][ind])' for
            cajmk__cnyk in range(gmc__wnrfr))))
        rxoi__ciodu = {}
        exec(llj__rag, {'init_multi_index': init_multi_index,
            'ensure_contig_if_np': ensure_contig_if_np}, rxoi__ciodu)
        sitmo__pagv = rxoi__ciodu['impl']
        return sitmo__pagv


@lower_builtin(operator.is_, MultiIndexType, MultiIndexType)
def multi_index_is(context, builder, sig, args):
    mav__ssdp, jipee__ydp = sig.args
    if mav__ssdp != jipee__ydp:
        return cgutils.false_bit

    def index_is_impl(a, b):
        return (a._data is b._data and a._names is b._names and a._name is
            b._name)
    return context.compile_internal(builder, index_is_impl, sig, args)
