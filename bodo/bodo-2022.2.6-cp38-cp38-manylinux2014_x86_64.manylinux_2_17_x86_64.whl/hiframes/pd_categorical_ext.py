import enum
import operator
import numba
import numpy as np
import pandas as pd
from llvmlite import ir as lir
from numba.core import cgutils, types
from numba.core.imputils import lower_constant
from numba.extending import NativeValue, box, intrinsic, lower_cast, make_attribute_wrapper, models, overload, overload_attribute, overload_method, register_jitable, register_model, typeof_impl, unbox
from numba.parfors.array_analysis import ArrayAnalysis
import bodo
from bodo.utils.typing import NOT_CONSTANT, BodoError, MetaType, check_unsupported_args, dtype_to_array_type, get_literal_value, get_overload_const, get_overload_const_bool, is_common_scalar_dtype, is_iterable_type, is_list_like_index_type, is_literal_type, is_overload_constant_bool, is_overload_none, is_overload_true, is_scalar_type, raise_bodo_error


class PDCategoricalDtype(types.Opaque):

    def __init__(self, categories, elem_type, ordered, data=None, int_type=None
        ):
        self.categories = categories
        self.elem_type = elem_type
        self.ordered = ordered
        self.data = _get_cat_index_type(elem_type) if data is None else data
        self.int_type = int_type
        pad__hjts = (
            f'PDCategoricalDtype({self.categories}, {self.elem_type}, {self.ordered}, {self.data}, {self.int_type})'
            )
        super(PDCategoricalDtype, self).__init__(name=pad__hjts)

    @property
    def mangling_args(self):
        return self.__class__.__name__, (self._code,)


@typeof_impl.register(pd.CategoricalDtype)
def _typeof_pd_cat_dtype(val, c):
    tiv__xecx = tuple(val.categories.values)
    elem_type = None if len(tiv__xecx) == 0 else bodo.typeof(val.categories
        .values).dtype
    int_type = getattr(val, '_int_type', None)
    return PDCategoricalDtype(tiv__xecx, elem_type, val.ordered, bodo.
        typeof(val.categories), int_type)


def _get_cat_index_type(elem_type):
    elem_type = bodo.string_type if elem_type is None else elem_type
    return bodo.utils.typing.get_index_type_from_dtype(elem_type)


@lower_constant(PDCategoricalDtype)
def lower_constant_categorical_type(context, builder, typ, pyval):
    categories = context.get_constant_generic(builder, bodo.typeof(pyval.
        categories), pyval.categories)
    ordered = context.get_constant(types.bool_, pyval.ordered)
    return lir.Constant.literal_struct([categories, ordered])


@register_model(PDCategoricalDtype)
class PDCategoricalDtypeModel(models.StructModel):

    def __init__(self, dmm, fe_type):
        gdg__pvipu = [('categories', fe_type.data), ('ordered', types.bool_)]
        models.StructModel.__init__(self, dmm, fe_type, gdg__pvipu)


make_attribute_wrapper(PDCategoricalDtype, 'categories', 'categories')
make_attribute_wrapper(PDCategoricalDtype, 'ordered', 'ordered')


@intrinsic
def init_cat_dtype(typingctx, categories_typ, ordered_typ, int_type,
    cat_vals_typ=None):
    assert bodo.hiframes.pd_index_ext.is_index_type(categories_typ
        ), 'init_cat_dtype requires index type for categories'
    assert is_overload_constant_bool(ordered_typ
        ), 'init_cat_dtype requires constant ordered flag'
    aksl__xbqkg = None if is_overload_none(int_type) else int_type.dtype
    assert is_overload_none(cat_vals_typ) or isinstance(cat_vals_typ, types
        .TypeRef), 'init_cat_dtype requires constant category values'
    pomjn__qekp = None if is_overload_none(cat_vals_typ
        ) else cat_vals_typ.instance_type.meta

    def codegen(context, builder, sig, args):
        categories, ordered, wzv__ezh, wzv__ezh = args
        cat_dtype = cgutils.create_struct_proxy(sig.return_type)(context,
            builder)
        cat_dtype.categories = categories
        context.nrt.incref(builder, sig.args[0], categories)
        context.nrt.incref(builder, sig.args[1], ordered)
        cat_dtype.ordered = ordered
        return cat_dtype._getvalue()
    kcmxi__hzorx = PDCategoricalDtype(pomjn__qekp, categories_typ.dtype,
        is_overload_true(ordered_typ), categories_typ, aksl__xbqkg)
    return kcmxi__hzorx(categories_typ, ordered_typ, int_type, cat_vals_typ
        ), codegen


@unbox(PDCategoricalDtype)
def unbox_cat_dtype(typ, obj, c):
    cat_dtype = cgutils.create_struct_proxy(typ)(c.context, c.builder)
    srgu__pjnb = c.pyapi.object_getattr_string(obj, 'ordered')
    cat_dtype.ordered = c.pyapi.to_native_value(types.bool_, srgu__pjnb).value
    c.pyapi.decref(srgu__pjnb)
    smeq__wqwh = c.pyapi.object_getattr_string(obj, 'categories')
    cat_dtype.categories = c.pyapi.to_native_value(typ.data, smeq__wqwh).value
    c.pyapi.decref(smeq__wqwh)
    upl__sfiiq = cgutils.is_not_null(c.builder, c.pyapi.err_occurred())
    return NativeValue(cat_dtype._getvalue(), is_error=upl__sfiiq)


@box(PDCategoricalDtype)
def box_cat_dtype(typ, val, c):
    cat_dtype = cgutils.create_struct_proxy(typ)(c.context, c.builder, val)
    srgu__pjnb = c.pyapi.from_native_value(types.bool_, cat_dtype.ordered,
        c.env_manager)
    c.context.nrt.incref(c.builder, typ.data, cat_dtype.categories)
    ovgu__usapk = c.pyapi.from_native_value(typ.data, cat_dtype.categories,
        c.env_manager)
    crbt__bzrb = c.context.insert_const_string(c.builder.module, 'pandas')
    phkpr__afyg = c.pyapi.import_module_noblock(crbt__bzrb)
    wctuq__woyva = c.pyapi.call_method(phkpr__afyg, 'CategoricalDtype', (
        ovgu__usapk, srgu__pjnb))
    c.pyapi.decref(srgu__pjnb)
    c.pyapi.decref(ovgu__usapk)
    c.pyapi.decref(phkpr__afyg)
    c.context.nrt.decref(c.builder, typ, val)
    return wctuq__woyva


@overload_attribute(PDCategoricalDtype, 'nbytes')
def pd_categorical_nbytes_overload(A):
    return lambda A: A.categories.nbytes + bodo.io.np_io.get_dtype_size(types
        .bool_)


class CategoricalArrayType(types.ArrayCompatible):

    def __init__(self, dtype):
        self.dtype = dtype
        super(CategoricalArrayType, self).__init__(name=
            f'CategoricalArrayType({dtype})')

    @property
    def as_array(self):
        return types.Array(types.undefined, 1, 'C')

    def copy(self):
        return CategoricalArrayType(self.dtype)

    @property
    def mangling_args(self):
        return self.__class__.__name__, (self._code,)


@typeof_impl.register(pd.Categorical)
def _typeof_pd_cat(val, c):
    return CategoricalArrayType(bodo.typeof(val.dtype))


@register_model(CategoricalArrayType)
class CategoricalArrayModel(models.StructModel):

    def __init__(self, dmm, fe_type):
        lfzo__zjxo = get_categories_int_type(fe_type.dtype)
        gdg__pvipu = [('dtype', fe_type.dtype), ('codes', types.Array(
            lfzo__zjxo, 1, 'C'))]
        super(CategoricalArrayModel, self).__init__(dmm, fe_type, gdg__pvipu)


make_attribute_wrapper(CategoricalArrayType, 'codes', 'codes')
make_attribute_wrapper(CategoricalArrayType, 'dtype', 'dtype')


@unbox(CategoricalArrayType)
def unbox_categorical_array(typ, val, c):
    gqrk__pocws = c.pyapi.object_getattr_string(val, 'codes')
    dtype = get_categories_int_type(typ.dtype)
    codes = c.pyapi.to_native_value(types.Array(dtype, 1, 'C'), gqrk__pocws
        ).value
    c.pyapi.decref(gqrk__pocws)
    wctuq__woyva = c.pyapi.object_getattr_string(val, 'dtype')
    vcvj__lwf = c.pyapi.to_native_value(typ.dtype, wctuq__woyva).value
    c.pyapi.decref(wctuq__woyva)
    dgil__aiev = cgutils.create_struct_proxy(typ)(c.context, c.builder)
    dgil__aiev.codes = codes
    dgil__aiev.dtype = vcvj__lwf
    return NativeValue(dgil__aiev._getvalue())


@lower_constant(CategoricalArrayType)
def lower_constant_categorical_array(context, builder, typ, pyval):
    qrsv__sws = get_categories_int_type(typ.dtype)
    snx__euo = context.get_constant_generic(builder, types.Array(qrsv__sws,
        1, 'C'), pyval.codes)
    cat_dtype = context.get_constant_generic(builder, typ.dtype, pyval.dtype)
    return lir.Constant.literal_struct([cat_dtype, snx__euo])


def get_categories_int_type(cat_dtype):
    dtype = types.int64
    if cat_dtype.int_type is not None:
        return cat_dtype.int_type
    if cat_dtype.categories is None:
        return types.int64
    racqe__jpgh = len(cat_dtype.categories)
    if racqe__jpgh < np.iinfo(np.int8).max:
        dtype = types.int8
    elif racqe__jpgh < np.iinfo(np.int16).max:
        dtype = types.int16
    elif racqe__jpgh < np.iinfo(np.int32).max:
        dtype = types.int32
    return dtype


@box(CategoricalArrayType)
def box_categorical_array(typ, val, c):
    dtype = typ.dtype
    crbt__bzrb = c.context.insert_const_string(c.builder.module, 'pandas')
    phkpr__afyg = c.pyapi.import_module_noblock(crbt__bzrb)
    lfzo__zjxo = get_categories_int_type(dtype)
    med__ykx = cgutils.create_struct_proxy(typ)(c.context, c.builder, val)
    sjcug__vveiv = types.Array(lfzo__zjxo, 1, 'C')
    c.context.nrt.incref(c.builder, sjcug__vveiv, med__ykx.codes)
    gqrk__pocws = c.pyapi.from_native_value(sjcug__vveiv, med__ykx.codes, c
        .env_manager)
    c.context.nrt.incref(c.builder, dtype, med__ykx.dtype)
    wctuq__woyva = c.pyapi.from_native_value(dtype, med__ykx.dtype, c.
        env_manager)
    ebnx__qqmny = c.pyapi.borrow_none()
    ubsfz__xucxi = c.pyapi.object_getattr_string(phkpr__afyg, 'Categorical')
    yziaz__ksre = c.pyapi.call_method(ubsfz__xucxi, 'from_codes', (
        gqrk__pocws, ebnx__qqmny, ebnx__qqmny, wctuq__woyva))
    c.pyapi.decref(ubsfz__xucxi)
    c.pyapi.decref(gqrk__pocws)
    c.pyapi.decref(wctuq__woyva)
    c.pyapi.decref(phkpr__afyg)
    c.context.nrt.decref(c.builder, typ, val)
    return yziaz__ksre


def _to_readonly(t):
    from bodo.hiframes.pd_index_ext import DatetimeIndexType, NumericIndexType, TimedeltaIndexType
    if isinstance(t, CategoricalArrayType):
        return CategoricalArrayType(_to_readonly(t.dtype))
    if isinstance(t, PDCategoricalDtype):
        return PDCategoricalDtype(t.categories, t.elem_type, t.ordered,
            _to_readonly(t.data), t.int_type)
    if isinstance(t, types.Array):
        return types.Array(t.dtype, t.ndim, 'C', True)
    if isinstance(t, NumericIndexType):
        return NumericIndexType(t.dtype, t.name_typ, _to_readonly(t.data))
    if isinstance(t, (DatetimeIndexType, TimedeltaIndexType)):
        return t.__class__(t.name_typ, _to_readonly(t.data))
    return t


@lower_cast(CategoricalArrayType, CategoricalArrayType)
def cast_cat_arr(context, builder, fromty, toty, val):
    if _to_readonly(toty) == fromty:
        return val
    raise BodoError(f'Cannot cast from {fromty} to {toty}')


def create_cmp_op_overload(op):

    def overload_cat_arr_cmp(A, other):
        if not isinstance(A, CategoricalArrayType):
            return
        if A.dtype.categories and is_literal_type(other) and types.unliteral(
            other) == A.dtype.elem_type:
            val = get_literal_value(other)
            mit__qyfap = list(A.dtype.categories).index(val
                ) if val in A.dtype.categories else -2

            def impl_lit(A, other):
                zxx__ldtf = op(bodo.hiframes.pd_categorical_ext.
                    get_categorical_arr_codes(A), mit__qyfap)
                return zxx__ldtf
            return impl_lit

        def impl(A, other):
            mit__qyfap = get_code_for_value(A.dtype, other)
            zxx__ldtf = op(bodo.hiframes.pd_categorical_ext.
                get_categorical_arr_codes(A), mit__qyfap)
            return zxx__ldtf
        return impl
    return overload_cat_arr_cmp


def _install_cmp_ops():
    for op in [operator.eq, operator.ne]:
        mlspn__dnff = create_cmp_op_overload(op)
        overload(op, inline='always', no_unliteral=True)(mlspn__dnff)


_install_cmp_ops()


@register_jitable
def get_code_for_value(cat_dtype, val):
    med__ykx = cat_dtype.categories
    n = len(med__ykx)
    for axt__qskaz in range(n):
        if med__ykx[axt__qskaz] == val:
            return axt__qskaz
    return -2


@overload_method(CategoricalArrayType, 'astype', inline='always',
    no_unliteral=True)
def overload_cat_arr_astype(A, dtype, copy=True, _bodo_nan_to_str=True):
    if dtype == types.unicode_type:
        raise_bodo_error(
            "CategoricalArray.astype(): 'dtype' when passed as string must be a constant value"
            )
    uvhc__grrn = bodo.utils.typing.parse_dtype(dtype, 'CategoricalArray.astype'
        )
    if uvhc__grrn != A.dtype.elem_type and uvhc__grrn != types.unicode_type:
        raise BodoError(
            f'Converting categorical array {A} to dtype {dtype} not supported yet'
            )
    if uvhc__grrn == types.unicode_type:

        def impl(A, dtype, copy=True, _bodo_nan_to_str=True):
            codes = bodo.hiframes.pd_categorical_ext.get_categorical_arr_codes(
                A)
            categories = A.dtype.categories
            n = len(codes)
            zxx__ldtf = bodo.libs.str_arr_ext.pre_alloc_string_array(n, -1)
            for axt__qskaz in numba.parfors.parfor.internal_prange(n):
                tndo__ektfw = codes[axt__qskaz]
                if tndo__ektfw == -1:
                    if _bodo_nan_to_str:
                        bodo.libs.str_arr_ext.str_arr_setitem_NA_str(zxx__ldtf,
                            axt__qskaz)
                    else:
                        bodo.libs.array_kernels.setna(zxx__ldtf, axt__qskaz)
                    continue
                zxx__ldtf[axt__qskaz] = str(bodo.utils.conversion.
                    unbox_if_timestamp(categories[tndo__ektfw]))
            return zxx__ldtf
        return impl
    sjcug__vveiv = dtype_to_array_type(uvhc__grrn)

    def impl(A, dtype, copy=True, _bodo_nan_to_str=True):
        codes = bodo.hiframes.pd_categorical_ext.get_categorical_arr_codes(A)
        categories = A.dtype.categories
        n = len(codes)
        zxx__ldtf = bodo.utils.utils.alloc_type(n, sjcug__vveiv, (-1,))
        for axt__qskaz in numba.parfors.parfor.internal_prange(n):
            tndo__ektfw = codes[axt__qskaz]
            if tndo__ektfw == -1:
                bodo.libs.array_kernels.setna(zxx__ldtf, axt__qskaz)
                continue
            zxx__ldtf[axt__qskaz] = bodo.utils.conversion.unbox_if_timestamp(
                categories[tndo__ektfw])
        return zxx__ldtf
    return impl


@overload(pd.api.types.CategoricalDtype, no_unliteral=True)
def cat_overload_dummy(val_list):
    return lambda val_list: 1


@intrinsic
def init_categorical_array(typingctx, codes, cat_dtype=None):
    assert isinstance(codes, types.Array) and isinstance(codes.dtype, types
        .Integer)

    def codegen(context, builder, signature, args):
        zboj__hiorv, vcvj__lwf = args
        med__ykx = cgutils.create_struct_proxy(signature.return_type)(context,
            builder)
        med__ykx.codes = zboj__hiorv
        med__ykx.dtype = vcvj__lwf
        context.nrt.incref(builder, signature.args[0], zboj__hiorv)
        context.nrt.incref(builder, signature.args[1], vcvj__lwf)
        return med__ykx._getvalue()
    nnit__txce = CategoricalArrayType(cat_dtype)
    sig = nnit__txce(codes, cat_dtype)
    return sig, codegen


def init_categorical_array_equiv(self, scope, equiv_set, loc, args, kws):
    assert len(args) == 2 and not kws
    sfbr__fdu = args[0]
    if equiv_set.has_shape(sfbr__fdu):
        return ArrayAnalysis.AnalyzeResult(shape=sfbr__fdu, pre=[])
    return None


(ArrayAnalysis.
    _analyze_op_call_bodo_hiframes_pd_categorical_ext_init_categorical_array
    ) = init_categorical_array_equiv


def alloc_categorical_array(n, cat_dtype):
    pass


@overload(alloc_categorical_array, no_unliteral=True)
def _alloc_categorical_array(n, cat_dtype):
    lfzo__zjxo = get_categories_int_type(cat_dtype)

    def impl(n, cat_dtype):
        codes = np.empty(n, lfzo__zjxo)
        return init_categorical_array(codes, cat_dtype)
    return impl


def alloc_categorical_array_equiv(self, scope, equiv_set, loc, args, kws):
    assert len(args) == 2 and not kws
    return ArrayAnalysis.AnalyzeResult(shape=args[0], pre=[])


(ArrayAnalysis.
    _analyze_op_call_bodo_hiframes_pd_categorical_ext_alloc_categorical_array
    ) = alloc_categorical_array_equiv


@numba.generated_jit(nopython=True, no_cpython_wrapper=True)
def get_categorical_arr_codes(A):
    return lambda A: A.codes


def alias_ext_dummy_func(lhs_name, args, alias_map, arg_aliases):
    assert len(args) >= 1
    numba.core.ir_utils._add_alias(lhs_name, args[0].name, alias_map,
        arg_aliases)


numba.core.ir_utils.alias_func_extensions['init_categorical_array',
    'bodo.hiframes.pd_categorical_ext'] = alias_ext_dummy_func
numba.core.ir_utils.alias_func_extensions['get_categorical_arr_codes',
    'bodo.hiframes.pd_categorical_ext'] = alias_ext_dummy_func


@overload_method(CategoricalArrayType, 'copy', no_unliteral=True)
def cat_arr_copy_overload(arr):
    return lambda arr: init_categorical_array(arr.codes.copy(), arr.dtype)


def build_replace_dicts(to_replace, value, categories):
    return dict(), np.empty(len(categories) + 1), 0


@overload(build_replace_dicts, no_unliteral=True)
def _build_replace_dicts(to_replace, value, categories):
    if isinstance(to_replace, types.Number) or to_replace == bodo.string_type:

        def impl(to_replace, value, categories):
            return build_replace_dicts([to_replace], value, categories)
        return impl
    else:

        def impl(to_replace, value, categories):
            n = len(categories)
            lylvk__skz = {}
            snx__euo = np.empty(n + 1, np.int64)
            kjdht__myt = {}
            apzl__llfxz = []
            lcqfv__amr = {}
            for axt__qskaz in range(n):
                lcqfv__amr[categories[axt__qskaz]] = axt__qskaz
            for ody__tgii in to_replace:
                if ody__tgii != value:
                    if ody__tgii in lcqfv__amr:
                        if value in lcqfv__amr:
                            lylvk__skz[ody__tgii] = ody__tgii
                            owl__qadj = lcqfv__amr[ody__tgii]
                            kjdht__myt[owl__qadj] = lcqfv__amr[value]
                            apzl__llfxz.append(owl__qadj)
                        else:
                            lylvk__skz[ody__tgii] = value
                            lcqfv__amr[value] = lcqfv__amr[ody__tgii]
            tyh__zmy = np.sort(np.array(apzl__llfxz))
            vbnl__hvg = 0
            lpqf__cyhi = []
            for vwjig__cvr in range(-1, n):
                while vbnl__hvg < len(tyh__zmy) and vwjig__cvr > tyh__zmy[
                    vbnl__hvg]:
                    vbnl__hvg += 1
                lpqf__cyhi.append(vbnl__hvg)
            for fcdi__rjzav in range(-1, n):
                lkq__lfrau = fcdi__rjzav
                if fcdi__rjzav in kjdht__myt:
                    lkq__lfrau = kjdht__myt[fcdi__rjzav]
                snx__euo[fcdi__rjzav + 1] = lkq__lfrau - lpqf__cyhi[
                    lkq__lfrau + 1]
            return lylvk__skz, snx__euo, len(tyh__zmy)
        return impl


@numba.njit
def python_build_replace_dicts(to_replace, value, categories):
    return build_replace_dicts(to_replace, value, categories)


@register_jitable
def reassign_codes(new_codes_arr, old_codes_arr, codes_map_arr):
    for axt__qskaz in range(len(new_codes_arr)):
        new_codes_arr[axt__qskaz] = codes_map_arr[old_codes_arr[axt__qskaz] + 1
            ]


@overload_method(CategoricalArrayType, 'replace', inline='always',
    no_unliteral=True)
def overload_replace(arr, to_replace, value):

    def impl(arr, to_replace, value):
        return bodo.hiframes.pd_categorical_ext.cat_replace(arr, to_replace,
            value)
    return impl


def cat_replace(arr, to_replace, value):
    return


@overload(cat_replace, no_unliteral=True)
def cat_replace_overload(arr, to_replace, value):
    mzft__qvak = arr.dtype.ordered
    ooo__ohf = arr.dtype.elem_type
    hpw__kxx = get_overload_const(to_replace)
    hqjl__gfdez = get_overload_const(value)
    if (arr.dtype.categories is not None and hpw__kxx is not NOT_CONSTANT and
        hqjl__gfdez is not NOT_CONSTANT):
        dgsv__qqtu, codes_map_arr, wzv__ezh = python_build_replace_dicts(
            hpw__kxx, hqjl__gfdez, arr.dtype.categories)
        if len(dgsv__qqtu) == 0:
            return lambda arr, to_replace, value: arr.copy()
        jyaqj__qsgi = []
        for fjmiu__ebl in arr.dtype.categories:
            if fjmiu__ebl in dgsv__qqtu:
                wdy__uiig = dgsv__qqtu[fjmiu__ebl]
                if wdy__uiig != fjmiu__ebl:
                    jyaqj__qsgi.append(wdy__uiig)
            else:
                jyaqj__qsgi.append(fjmiu__ebl)
        ukvc__eqmlt = pd.CategoricalDtype(jyaqj__qsgi, mzft__qvak
            ).categories.values
        ttxoh__act = MetaType(tuple(ukvc__eqmlt))

        def impl_dtype(arr, to_replace, value):
            ysqp__nfxah = init_cat_dtype(bodo.utils.conversion.
                index_from_array(ukvc__eqmlt), mzft__qvak, None, ttxoh__act)
            med__ykx = alloc_categorical_array(len(arr.codes), ysqp__nfxah)
            reassign_codes(med__ykx.codes, arr.codes, codes_map_arr)
            return med__ykx
        return impl_dtype
    ooo__ohf = arr.dtype.elem_type
    if ooo__ohf == types.unicode_type:

        def impl_str(arr, to_replace, value):
            categories = arr.dtype.categories
            lylvk__skz, codes_map_arr, gjmi__isard = build_replace_dicts(
                to_replace, value, categories.values)
            if len(lylvk__skz) == 0:
                return init_categorical_array(arr.codes.copy().astype(np.
                    int64), init_cat_dtype(categories.copy(), mzft__qvak,
                    None, None))
            n = len(categories)
            ukvc__eqmlt = bodo.libs.str_arr_ext.pre_alloc_string_array(n -
                gjmi__isard, -1)
            jfk__ghavd = 0
            for vwjig__cvr in range(n):
                qqn__jknf = categories[vwjig__cvr]
                if qqn__jknf in lylvk__skz:
                    kte__rwuh = lylvk__skz[qqn__jknf]
                    if kte__rwuh != qqn__jknf:
                        ukvc__eqmlt[jfk__ghavd] = kte__rwuh
                        jfk__ghavd += 1
                else:
                    ukvc__eqmlt[jfk__ghavd] = qqn__jknf
                    jfk__ghavd += 1
            med__ykx = alloc_categorical_array(len(arr.codes),
                init_cat_dtype(bodo.utils.conversion.index_from_array(
                ukvc__eqmlt), mzft__qvak, None, None))
            reassign_codes(med__ykx.codes, arr.codes, codes_map_arr)
            return med__ykx
        return impl_str
    eqt__hecn = dtype_to_array_type(ooo__ohf)

    def impl(arr, to_replace, value):
        categories = arr.dtype.categories
        lylvk__skz, codes_map_arr, gjmi__isard = build_replace_dicts(to_replace
            , value, categories.values)
        if len(lylvk__skz) == 0:
            return init_categorical_array(arr.codes.copy().astype(np.int64),
                init_cat_dtype(categories.copy(), mzft__qvak, None, None))
        n = len(categories)
        ukvc__eqmlt = bodo.utils.utils.alloc_type(n - gjmi__isard,
            eqt__hecn, None)
        jfk__ghavd = 0
        for axt__qskaz in range(n):
            qqn__jknf = categories[axt__qskaz]
            if qqn__jknf in lylvk__skz:
                kte__rwuh = lylvk__skz[qqn__jknf]
                if kte__rwuh != qqn__jknf:
                    ukvc__eqmlt[jfk__ghavd] = kte__rwuh
                    jfk__ghavd += 1
            else:
                ukvc__eqmlt[jfk__ghavd] = qqn__jknf
                jfk__ghavd += 1
        med__ykx = alloc_categorical_array(len(arr.codes), init_cat_dtype(
            bodo.utils.conversion.index_from_array(ukvc__eqmlt), mzft__qvak,
            None, None))
        reassign_codes(med__ykx.codes, arr.codes, codes_map_arr)
        return med__ykx
    return impl


@overload(len, no_unliteral=True)
def overload_cat_arr_len(A):
    if isinstance(A, CategoricalArrayType):
        return lambda A: len(A.codes)


@overload_attribute(CategoricalArrayType, 'shape')
def overload_cat_arr_shape(A):
    return lambda A: (len(A.codes),)


@overload_attribute(CategoricalArrayType, 'ndim')
def overload_cat_arr_ndim(A):
    return lambda A: 1


@overload_attribute(CategoricalArrayType, 'nbytes')
def cat_arr_nbytes_overload(A):
    return lambda A: A.codes.nbytes + A.dtype.nbytes


@register_jitable
def get_label_dict_from_categories(vals):
    iyji__djuea = dict()
    auhs__girf = 0
    for axt__qskaz in range(len(vals)):
        val = vals[axt__qskaz]
        if val in iyji__djuea:
            continue
        iyji__djuea[val] = auhs__girf
        auhs__girf += 1
    return iyji__djuea


@register_jitable
def get_label_dict_from_categories_no_duplicates(vals):
    iyji__djuea = dict()
    for axt__qskaz in range(len(vals)):
        val = vals[axt__qskaz]
        iyji__djuea[val] = axt__qskaz
    return iyji__djuea


@overload(pd.Categorical, no_unliteral=True)
def pd_categorical_overload(values, categories=None, ordered=None, dtype=
    None, fastpath=False):
    oype__boh = dict(fastpath=fastpath)
    agfvz__pzr = dict(fastpath=False)
    check_unsupported_args('pd.Categorical', oype__boh, agfvz__pzr)
    if isinstance(dtype, bodo.hiframes.pd_categorical_ext.PDCategoricalDtype):

        def impl_dtype(values, categories=None, ordered=None, dtype=None,
            fastpath=False):
            data = bodo.utils.conversion.coerce_to_array(values)
            return bodo.utils.conversion.fix_arr_dtype(data, dtype)
        return impl_dtype
    if not is_overload_none(categories):
        qou__xos = get_overload_const(categories)
        if qou__xos is not NOT_CONSTANT and get_overload_const(ordered
            ) is not NOT_CONSTANT:
            if is_overload_none(ordered):
                gmo__lran = False
            else:
                gmo__lran = get_overload_const_bool(ordered)
            zvczo__bpb = pd.CategoricalDtype(qou__xos, gmo__lran
                ).categories.values
            ehzq__hsbk = MetaType(tuple(zvczo__bpb))

            def impl_cats_const(values, categories=None, ordered=None,
                dtype=None, fastpath=False):
                data = bodo.utils.conversion.coerce_to_array(values)
                ysqp__nfxah = init_cat_dtype(bodo.utils.conversion.
                    index_from_array(zvczo__bpb), gmo__lran, None, ehzq__hsbk)
                return bodo.utils.conversion.fix_arr_dtype(data, ysqp__nfxah)
            return impl_cats_const

        def impl_cats(values, categories=None, ordered=None, dtype=None,
            fastpath=False):
            ordered = bodo.utils.conversion.false_if_none(ordered)
            data = bodo.utils.conversion.coerce_to_array(values)
            tiv__xecx = bodo.utils.conversion.convert_to_index(categories)
            cat_dtype = bodo.hiframes.pd_categorical_ext.init_cat_dtype(
                tiv__xecx, ordered, None, None)
            return bodo.utils.conversion.fix_arr_dtype(data, cat_dtype)
        return impl_cats
    elif is_overload_none(ordered):

        def impl_auto(values, categories=None, ordered=None, dtype=None,
            fastpath=False):
            data = bodo.utils.conversion.coerce_to_array(values)
            return bodo.utils.conversion.fix_arr_dtype(data, 'category')
        return impl_auto
    raise BodoError(
        f'pd.Categorical(): argument combination not supported yet: {values}, {categories}, {ordered}, {dtype}'
        )


@overload(operator.getitem, no_unliteral=True)
def categorical_array_getitem(arr, ind):
    if not isinstance(arr, CategoricalArrayType):
        return
    if isinstance(ind, types.Integer):

        def categorical_getitem_impl(arr, ind):
            kwpn__bof = arr.codes[ind]
            return arr.dtype.categories[max(kwpn__bof, 0)]
        return categorical_getitem_impl
    if is_list_like_index_type(ind) or isinstance(ind, types.SliceType):

        def impl_bool(arr, ind):
            return init_categorical_array(arr.codes[ind], arr.dtype)
        return impl_bool
    raise BodoError(
        f'getitem for CategoricalArrayType with indexing type {ind} not supported.'
        )


class CategoricalMatchingValues(enum.Enum):
    DIFFERENT_TYPES = -1
    DONT_MATCH = 0
    MAY_MATCH = 1
    DO_MATCH = 2


def categorical_arrs_match(arr1, arr2):
    if not (isinstance(arr1, CategoricalArrayType) and isinstance(arr2,
        CategoricalArrayType)):
        return CategoricalMatchingValues.DIFFERENT_TYPES
    if arr1.dtype.categories is None or arr2.dtype.categories is None:
        return CategoricalMatchingValues.MAY_MATCH
    return (CategoricalMatchingValues.DO_MATCH if arr1.dtype.categories ==
        arr2.dtype.categories and arr1.dtype.ordered == arr2.dtype.ordered else
        CategoricalMatchingValues.DONT_MATCH)


@register_jitable
def cat_dtype_equal(dtype1, dtype2):
    if dtype1.ordered != dtype2.ordered or len(dtype1.categories) != len(dtype2
        .categories):
        return False
    arr1 = dtype1.categories.values
    arr2 = dtype2.categories.values
    for axt__qskaz in range(len(arr1)):
        if arr1[axt__qskaz] != arr2[axt__qskaz]:
            return False
    return True


@overload(operator.setitem, no_unliteral=True)
def categorical_array_setitem(arr, ind, val):
    if not isinstance(arr, CategoricalArrayType):
        return
    if val == types.none or isinstance(val, types.optional):
        return
    gifu__hqyjy = is_scalar_type(val) and is_common_scalar_dtype([types.
        unliteral(val), arr.dtype.elem_type]) and not (isinstance(arr.dtype
        .elem_type, types.Integer) and isinstance(val, types.Float))
    dhcr__hst = not isinstance(val, CategoricalArrayType) and is_iterable_type(
        val) and is_common_scalar_dtype([val.dtype, arr.dtype.elem_type]
        ) and not (isinstance(arr.dtype.elem_type, types.Integer) and
        isinstance(val.dtype, types.Float))
    kls__jwf = categorical_arrs_match(arr, val)
    dca__yyzhy = (
        f"setitem for CategoricalArrayType of dtype {arr.dtype} with indexing type {ind} received an incorrect 'value' type {val}."
        )
    nouq__pmv = (
        'Cannot set a Categorical with another, without identical categories')
    if isinstance(ind, types.Integer):
        if not gifu__hqyjy:
            raise BodoError(dca__yyzhy)

        def impl_scalar(arr, ind, val):
            if val not in arr.dtype.categories:
                raise ValueError(
                    'Cannot setitem on a Categorical with a new category, set the categories first'
                    )
            kwpn__bof = arr.dtype.categories.get_loc(val)
            arr.codes[ind] = kwpn__bof
        return impl_scalar
    if is_list_like_index_type(ind) and isinstance(ind.dtype, types.Integer):
        if not (gifu__hqyjy or dhcr__hst or kls__jwf !=
            CategoricalMatchingValues.DIFFERENT_TYPES):
            raise BodoError(dca__yyzhy)
        if kls__jwf == CategoricalMatchingValues.DONT_MATCH:
            raise BodoError(nouq__pmv)
        if gifu__hqyjy:

            def impl_scalar(arr, ind, val):
                if val not in arr.dtype.categories:
                    raise ValueError(
                        'Cannot setitem on a Categorical with a new category, set the categories first'
                        )
                ccu__uvjl = arr.dtype.categories.get_loc(val)
                n = len(ind)
                for vwjig__cvr in range(n):
                    arr.codes[ind[vwjig__cvr]] = ccu__uvjl
            return impl_scalar
        if kls__jwf == CategoricalMatchingValues.DO_MATCH:

            def impl_arr_ind_mask(arr, ind, val):
                n = len(val.codes)
                for axt__qskaz in range(n):
                    arr.codes[ind[axt__qskaz]] = val.codes[axt__qskaz]
            return impl_arr_ind_mask
        if kls__jwf == CategoricalMatchingValues.MAY_MATCH:

            def impl_arr_ind_mask(arr, ind, val):
                if not cat_dtype_equal(arr.dtype, val.dtype):
                    raise ValueError(nouq__pmv)
                n = len(val.codes)
                for axt__qskaz in range(n):
                    arr.codes[ind[axt__qskaz]] = val.codes[axt__qskaz]
            return impl_arr_ind_mask
        if dhcr__hst:

            def impl_arr_ind_mask_cat_values(arr, ind, val):
                n = len(val)
                categories = arr.dtype.categories
                for vwjig__cvr in range(n):
                    the__hmprn = bodo.utils.conversion.unbox_if_timestamp(val
                        [vwjig__cvr])
                    if the__hmprn not in categories:
                        raise ValueError(
                            'Cannot setitem on a Categorical with a new category, set the categories first'
                            )
                    kwpn__bof = categories.get_loc(the__hmprn)
                    arr.codes[ind[vwjig__cvr]] = kwpn__bof
            return impl_arr_ind_mask_cat_values
    if is_list_like_index_type(ind) and ind.dtype == types.bool_:
        if not (gifu__hqyjy or dhcr__hst or kls__jwf !=
            CategoricalMatchingValues.DIFFERENT_TYPES):
            raise BodoError(dca__yyzhy)
        if kls__jwf == CategoricalMatchingValues.DONT_MATCH:
            raise BodoError(nouq__pmv)
        if gifu__hqyjy:

            def impl_scalar(arr, ind, val):
                if val not in arr.dtype.categories:
                    raise ValueError(
                        'Cannot setitem on a Categorical with a new category, set the categories first'
                        )
                ccu__uvjl = arr.dtype.categories.get_loc(val)
                n = len(ind)
                for vwjig__cvr in range(n):
                    if ind[vwjig__cvr]:
                        arr.codes[vwjig__cvr] = ccu__uvjl
            return impl_scalar
        if kls__jwf == CategoricalMatchingValues.DO_MATCH:

            def impl_bool_ind_mask(arr, ind, val):
                n = len(ind)
                naltz__zqki = 0
                for axt__qskaz in range(n):
                    if ind[axt__qskaz]:
                        arr.codes[axt__qskaz] = val.codes[naltz__zqki]
                        naltz__zqki += 1
            return impl_bool_ind_mask
        if kls__jwf == CategoricalMatchingValues.MAY_MATCH:

            def impl_bool_ind_mask(arr, ind, val):
                if not cat_dtype_equal(arr.dtype, val.dtype):
                    raise ValueError(nouq__pmv)
                n = len(ind)
                naltz__zqki = 0
                for axt__qskaz in range(n):
                    if ind[axt__qskaz]:
                        arr.codes[axt__qskaz] = val.codes[naltz__zqki]
                        naltz__zqki += 1
            return impl_bool_ind_mask
        if dhcr__hst:

            def impl_bool_ind_mask_cat_values(arr, ind, val):
                n = len(ind)
                naltz__zqki = 0
                categories = arr.dtype.categories
                for vwjig__cvr in range(n):
                    if ind[vwjig__cvr]:
                        the__hmprn = bodo.utils.conversion.unbox_if_timestamp(
                            val[naltz__zqki])
                        if the__hmprn not in categories:
                            raise ValueError(
                                'Cannot setitem on a Categorical with a new category, set the categories first'
                                )
                        kwpn__bof = categories.get_loc(the__hmprn)
                        arr.codes[vwjig__cvr] = kwpn__bof
                        naltz__zqki += 1
            return impl_bool_ind_mask_cat_values
    if isinstance(ind, types.SliceType):
        if not (gifu__hqyjy or dhcr__hst or kls__jwf !=
            CategoricalMatchingValues.DIFFERENT_TYPES):
            raise BodoError(dca__yyzhy)
        if kls__jwf == CategoricalMatchingValues.DONT_MATCH:
            raise BodoError(nouq__pmv)
        if gifu__hqyjy:

            def impl_scalar(arr, ind, val):
                if val not in arr.dtype.categories:
                    raise ValueError(
                        'Cannot setitem on a Categorical with a new category, set the categories first'
                        )
                ccu__uvjl = arr.dtype.categories.get_loc(val)
                gxvn__qeemk = numba.cpython.unicode._normalize_slice(ind,
                    len(arr))
                for vwjig__cvr in range(gxvn__qeemk.start, gxvn__qeemk.stop,
                    gxvn__qeemk.step):
                    arr.codes[vwjig__cvr] = ccu__uvjl
            return impl_scalar
        if kls__jwf == CategoricalMatchingValues.DO_MATCH:

            def impl_arr(arr, ind, val):
                arr.codes[ind] = val.codes
            return impl_arr
        if kls__jwf == CategoricalMatchingValues.MAY_MATCH:

            def impl_arr(arr, ind, val):
                if not cat_dtype_equal(arr.dtype, val.dtype):
                    raise ValueError(nouq__pmv)
                arr.codes[ind] = val.codes
            return impl_arr
        if dhcr__hst:

            def impl_slice_cat_values(arr, ind, val):
                categories = arr.dtype.categories
                gxvn__qeemk = numba.cpython.unicode._normalize_slice(ind,
                    len(arr))
                naltz__zqki = 0
                for vwjig__cvr in range(gxvn__qeemk.start, gxvn__qeemk.stop,
                    gxvn__qeemk.step):
                    the__hmprn = bodo.utils.conversion.unbox_if_timestamp(val
                        [naltz__zqki])
                    if the__hmprn not in categories:
                        raise ValueError(
                            'Cannot setitem on a Categorical with a new category, set the categories first'
                            )
                    kwpn__bof = categories.get_loc(the__hmprn)
                    arr.codes[vwjig__cvr] = kwpn__bof
                    naltz__zqki += 1
            return impl_slice_cat_values
    raise BodoError(
        f'setitem for CategoricalArrayType with indexing type {ind} not supported.'
        )
