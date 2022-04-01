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
        ldjb__afo = [('data', types.Tuple(fe_type.array_types)), ('names',
            types.Tuple(fe_type.names_typ)), ('name', fe_type.name_typ)]
        super(MultiIndexModel, self).__init__(dmm, fe_type, ldjb__afo)


make_attribute_wrapper(MultiIndexType, 'data', '_data')
make_attribute_wrapper(MultiIndexType, 'names', '_names')
make_attribute_wrapper(MultiIndexType, 'name', '_name')


@typeof_impl.register(pd.MultiIndex)
def typeof_multi_index(val, c):
    array_types = tuple(numba.typeof(val.levels[wxs__odm].values) for
        wxs__odm in range(val.nlevels))
    return MultiIndexType(array_types, tuple(get_val_type_maybe_str_literal
        (orc__yjp) for orc__yjp in val.names), numba.typeof(val.name))


@box(MultiIndexType)
def box_multi_index(typ, val, c):
    xxl__lamo = c.context.insert_const_string(c.builder.module, 'pandas')
    nttev__cmz = c.pyapi.import_module_noblock(xxl__lamo)
    lngn__ljr = c.pyapi.object_getattr_string(nttev__cmz, 'MultiIndex')
    hxc__kqzs = cgutils.create_struct_proxy(typ)(c.context, c.builder, val)
    c.context.nrt.incref(c.builder, types.Tuple(typ.array_types), hxc__kqzs
        .data)
    skbc__bdl = c.pyapi.from_native_value(types.Tuple(typ.array_types),
        hxc__kqzs.data, c.env_manager)
    c.context.nrt.incref(c.builder, types.Tuple(typ.names_typ), hxc__kqzs.names
        )
    zse__kzfmf = c.pyapi.from_native_value(types.Tuple(typ.names_typ),
        hxc__kqzs.names, c.env_manager)
    c.context.nrt.incref(c.builder, typ.name_typ, hxc__kqzs.name)
    orhj__var = c.pyapi.from_native_value(typ.name_typ, hxc__kqzs.name, c.
        env_manager)
    biia__zuvcc = c.pyapi.borrow_none()
    bfqk__ffy = c.pyapi.call_method(lngn__ljr, 'from_arrays', (skbc__bdl,
        biia__zuvcc, zse__kzfmf))
    c.pyapi.object_setattr_string(bfqk__ffy, 'name', orhj__var)
    c.pyapi.decref(skbc__bdl)
    c.pyapi.decref(zse__kzfmf)
    c.pyapi.decref(orhj__var)
    c.pyapi.decref(nttev__cmz)
    c.pyapi.decref(lngn__ljr)
    c.context.nrt.decref(c.builder, typ, val)
    return bfqk__ffy


@unbox(MultiIndexType)
def unbox_multi_index(typ, val, c):
    oxykn__thenr = []
    cyf__uhdl = []
    for wxs__odm in range(typ.nlevels):
        gwsyw__umd = c.pyapi.unserialize(c.pyapi.serialize_object(wxs__odm))
        zsij__nhdy = c.pyapi.call_method(val, 'get_level_values', (gwsyw__umd,)
            )
        ffca__awnly = c.pyapi.object_getattr_string(zsij__nhdy, 'values')
        c.pyapi.decref(zsij__nhdy)
        c.pyapi.decref(gwsyw__umd)
        denu__bxv = c.pyapi.to_native_value(typ.array_types[wxs__odm],
            ffca__awnly).value
        oxykn__thenr.append(denu__bxv)
        cyf__uhdl.append(ffca__awnly)
    if isinstance(types.Tuple(typ.array_types), types.UniTuple):
        data = cgutils.pack_array(c.builder, oxykn__thenr)
    else:
        data = cgutils.pack_struct(c.builder, oxykn__thenr)
    zse__kzfmf = c.pyapi.object_getattr_string(val, 'names')
    bdai__sayp = c.pyapi.unserialize(c.pyapi.serialize_object(tuple))
    sxugw__gylrd = c.pyapi.call_function_objargs(bdai__sayp, (zse__kzfmf,))
    names = c.pyapi.to_native_value(types.Tuple(typ.names_typ), sxugw__gylrd
        ).value
    orhj__var = c.pyapi.object_getattr_string(val, 'name')
    name = c.pyapi.to_native_value(typ.name_typ, orhj__var).value
    hxc__kqzs = cgutils.create_struct_proxy(typ)(c.context, c.builder)
    hxc__kqzs.data = data
    hxc__kqzs.names = names
    hxc__kqzs.name = name
    for ffca__awnly in cyf__uhdl:
        c.pyapi.decref(ffca__awnly)
    c.pyapi.decref(zse__kzfmf)
    c.pyapi.decref(bdai__sayp)
    c.pyapi.decref(sxugw__gylrd)
    c.pyapi.decref(orhj__var)
    return NativeValue(hxc__kqzs._getvalue())


def from_product_error_checking(iterables, sortorder, names):
    ptrec__ztfh = 'pandas.MultiIndex.from_product'
    zbmtg__lur = dict(sortorder=sortorder)
    wyld__lbb = dict(sortorder=None)
    check_unsupported_args(ptrec__ztfh, zbmtg__lur, wyld__lbb, package_name
        ='pandas', module_name='Index')
    if not (is_overload_none(names) or isinstance(names, types.BaseTuple)):
        raise BodoError(f'{ptrec__ztfh}: names must be None or a tuple.')
    elif not isinstance(iterables, types.BaseTuple):
        raise BodoError(f'{ptrec__ztfh}: iterables must be a tuple.')
    elif not is_overload_none(names) and len(iterables) != len(names):
        raise BodoError(
            f'{ptrec__ztfh}: iterables and names must be of the same length.')


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
    sig__kul = MultiIndexType(array_types, names_typ)
    irygb__egen = f'from_product_multiindex{numba.core.ir_utils.next_label()}'
    setattr(types, irygb__egen, sig__kul)
    oxx__rri = f"""
def impl(iterables, sortorder=None, names=None):
    with numba.objmode(mi='{irygb__egen}'):
        mi = pd.MultiIndex.from_product(iterables, names=names)
    return mi
"""
    hohd__ntmtr = {}
    exec(oxx__rri, globals(), hohd__ntmtr)
    kmw__ghy = hohd__ntmtr['impl']
    return kmw__ghy


@intrinsic
def init_multi_index(typingctx, data, names, name=None):
    name = types.none if name is None else name
    names = types.Tuple(names.types)

    def codegen(context, builder, signature, args):
        erp__tzyuw, adz__rio, fbc__tfjx = args
        jzz__nhpov = cgutils.create_struct_proxy(signature.return_type)(context
            , builder)
        jzz__nhpov.data = erp__tzyuw
        jzz__nhpov.names = adz__rio
        jzz__nhpov.name = fbc__tfjx
        context.nrt.incref(builder, signature.args[0], erp__tzyuw)
        context.nrt.incref(builder, signature.args[1], adz__rio)
        context.nrt.incref(builder, signature.args[2], fbc__tfjx)
        return jzz__nhpov._getvalue()
    ocpq__drq = MultiIndexType(data.types, names.types, name)
    return ocpq__drq(data, names, name), codegen


@overload(len, no_unliteral=True)
def overload_len_pd_multiindex(A):
    if isinstance(A, MultiIndexType):
        return lambda A: len(A._data[0])


@overload(operator.getitem, no_unliteral=True)
def overload_multi_index_getitem(I, ind):
    if not isinstance(I, MultiIndexType):
        return
    if not isinstance(ind, types.Integer):
        nzvj__vjrc = len(I.array_types)
        oxx__rri = 'def impl(I, ind):\n'
        oxx__rri += '  data = I._data\n'
        oxx__rri += ('  return init_multi_index(({},), I._names, I._name)\n'
            .format(', '.join(f'ensure_contig_if_np(data[{wxs__odm}][ind])' for
            wxs__odm in range(nzvj__vjrc))))
        hohd__ntmtr = {}
        exec(oxx__rri, {'init_multi_index': init_multi_index,
            'ensure_contig_if_np': ensure_contig_if_np}, hohd__ntmtr)
        kmw__ghy = hohd__ntmtr['impl']
        return kmw__ghy


@lower_builtin(operator.is_, MultiIndexType, MultiIndexType)
def multi_index_is(context, builder, sig, args):
    kcaca__ykrq, fdpfz__oam = sig.args
    if kcaca__ykrq != fdpfz__oam:
        return cgutils.false_bit

    def index_is_impl(a, b):
        return (a._data is b._data and a._names is b._names and a._name is
            b._name)
    return context.compile_internal(builder, index_is_impl, sig, args)
