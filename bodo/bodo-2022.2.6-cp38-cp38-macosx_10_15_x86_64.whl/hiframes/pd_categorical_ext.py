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
        ejtw__zckfu = (
            f'PDCategoricalDtype({self.categories}, {self.elem_type}, {self.ordered}, {self.data}, {self.int_type})'
            )
        super(PDCategoricalDtype, self).__init__(name=ejtw__zckfu)

    @property
    def mangling_args(self):
        return self.__class__.__name__, (self._code,)


@typeof_impl.register(pd.CategoricalDtype)
def _typeof_pd_cat_dtype(val, c):
    aonld__mdcoo = tuple(val.categories.values)
    elem_type = None if len(aonld__mdcoo) == 0 else bodo.typeof(val.
        categories.values).dtype
    int_type = getattr(val, '_int_type', None)
    return PDCategoricalDtype(aonld__mdcoo, elem_type, val.ordered, bodo.
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
        lymay__jikt = [('categories', fe_type.data), ('ordered', types.bool_)]
        models.StructModel.__init__(self, dmm, fe_type, lymay__jikt)


make_attribute_wrapper(PDCategoricalDtype, 'categories', 'categories')
make_attribute_wrapper(PDCategoricalDtype, 'ordered', 'ordered')


@intrinsic
def init_cat_dtype(typingctx, categories_typ, ordered_typ, int_type,
    cat_vals_typ=None):
    assert bodo.hiframes.pd_index_ext.is_index_type(categories_typ
        ), 'init_cat_dtype requires index type for categories'
    assert is_overload_constant_bool(ordered_typ
        ), 'init_cat_dtype requires constant ordered flag'
    ftmu__orj = None if is_overload_none(int_type) else int_type.dtype
    assert is_overload_none(cat_vals_typ) or isinstance(cat_vals_typ, types
        .TypeRef), 'init_cat_dtype requires constant category values'
    gyi__yilmp = None if is_overload_none(cat_vals_typ
        ) else cat_vals_typ.instance_type.meta

    def codegen(context, builder, sig, args):
        categories, ordered, gocx__qzrtq, gocx__qzrtq = args
        cat_dtype = cgutils.create_struct_proxy(sig.return_type)(context,
            builder)
        cat_dtype.categories = categories
        context.nrt.incref(builder, sig.args[0], categories)
        context.nrt.incref(builder, sig.args[1], ordered)
        cat_dtype.ordered = ordered
        return cat_dtype._getvalue()
    zhrhr__zent = PDCategoricalDtype(gyi__yilmp, categories_typ.dtype,
        is_overload_true(ordered_typ), categories_typ, ftmu__orj)
    return zhrhr__zent(categories_typ, ordered_typ, int_type, cat_vals_typ
        ), codegen


@unbox(PDCategoricalDtype)
def unbox_cat_dtype(typ, obj, c):
    cat_dtype = cgutils.create_struct_proxy(typ)(c.context, c.builder)
    qpg__qnnv = c.pyapi.object_getattr_string(obj, 'ordered')
    cat_dtype.ordered = c.pyapi.to_native_value(types.bool_, qpg__qnnv).value
    c.pyapi.decref(qpg__qnnv)
    ikrt__gmpja = c.pyapi.object_getattr_string(obj, 'categories')
    cat_dtype.categories = c.pyapi.to_native_value(typ.data, ikrt__gmpja).value
    c.pyapi.decref(ikrt__gmpja)
    jaknp__txb = cgutils.is_not_null(c.builder, c.pyapi.err_occurred())
    return NativeValue(cat_dtype._getvalue(), is_error=jaknp__txb)


@box(PDCategoricalDtype)
def box_cat_dtype(typ, val, c):
    cat_dtype = cgutils.create_struct_proxy(typ)(c.context, c.builder, val)
    qpg__qnnv = c.pyapi.from_native_value(types.bool_, cat_dtype.ordered, c
        .env_manager)
    c.context.nrt.incref(c.builder, typ.data, cat_dtype.categories)
    fgwvp__kpc = c.pyapi.from_native_value(typ.data, cat_dtype.categories,
        c.env_manager)
    dxqk__jlu = c.context.insert_const_string(c.builder.module, 'pandas')
    gbjz__pqwez = c.pyapi.import_module_noblock(dxqk__jlu)
    jfwxu__mvsu = c.pyapi.call_method(gbjz__pqwez, 'CategoricalDtype', (
        fgwvp__kpc, qpg__qnnv))
    c.pyapi.decref(qpg__qnnv)
    c.pyapi.decref(fgwvp__kpc)
    c.pyapi.decref(gbjz__pqwez)
    c.context.nrt.decref(c.builder, typ, val)
    return jfwxu__mvsu


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
        pdal__lcec = get_categories_int_type(fe_type.dtype)
        lymay__jikt = [('dtype', fe_type.dtype), ('codes', types.Array(
            pdal__lcec, 1, 'C'))]
        super(CategoricalArrayModel, self).__init__(dmm, fe_type, lymay__jikt)


make_attribute_wrapper(CategoricalArrayType, 'codes', 'codes')
make_attribute_wrapper(CategoricalArrayType, 'dtype', 'dtype')


@unbox(CategoricalArrayType)
def unbox_categorical_array(typ, val, c):
    ghx__xcnnu = c.pyapi.object_getattr_string(val, 'codes')
    dtype = get_categories_int_type(typ.dtype)
    codes = c.pyapi.to_native_value(types.Array(dtype, 1, 'C'), ghx__xcnnu
        ).value
    c.pyapi.decref(ghx__xcnnu)
    jfwxu__mvsu = c.pyapi.object_getattr_string(val, 'dtype')
    sujv__ruxu = c.pyapi.to_native_value(typ.dtype, jfwxu__mvsu).value
    c.pyapi.decref(jfwxu__mvsu)
    cunwo__ajzm = cgutils.create_struct_proxy(typ)(c.context, c.builder)
    cunwo__ajzm.codes = codes
    cunwo__ajzm.dtype = sujv__ruxu
    return NativeValue(cunwo__ajzm._getvalue())


@lower_constant(CategoricalArrayType)
def lower_constant_categorical_array(context, builder, typ, pyval):
    xisei__ukiu = get_categories_int_type(typ.dtype)
    mbex__kfh = context.get_constant_generic(builder, types.Array(
        xisei__ukiu, 1, 'C'), pyval.codes)
    cat_dtype = context.get_constant_generic(builder, typ.dtype, pyval.dtype)
    return lir.Constant.literal_struct([cat_dtype, mbex__kfh])


def get_categories_int_type(cat_dtype):
    dtype = types.int64
    if cat_dtype.int_type is not None:
        return cat_dtype.int_type
    if cat_dtype.categories is None:
        return types.int64
    gtt__tgley = len(cat_dtype.categories)
    if gtt__tgley < np.iinfo(np.int8).max:
        dtype = types.int8
    elif gtt__tgley < np.iinfo(np.int16).max:
        dtype = types.int16
    elif gtt__tgley < np.iinfo(np.int32).max:
        dtype = types.int32
    return dtype


@box(CategoricalArrayType)
def box_categorical_array(typ, val, c):
    dtype = typ.dtype
    dxqk__jlu = c.context.insert_const_string(c.builder.module, 'pandas')
    gbjz__pqwez = c.pyapi.import_module_noblock(dxqk__jlu)
    pdal__lcec = get_categories_int_type(dtype)
    lvy__rpgfb = cgutils.create_struct_proxy(typ)(c.context, c.builder, val)
    jsup__eoko = types.Array(pdal__lcec, 1, 'C')
    c.context.nrt.incref(c.builder, jsup__eoko, lvy__rpgfb.codes)
    ghx__xcnnu = c.pyapi.from_native_value(jsup__eoko, lvy__rpgfb.codes, c.
        env_manager)
    c.context.nrt.incref(c.builder, dtype, lvy__rpgfb.dtype)
    jfwxu__mvsu = c.pyapi.from_native_value(dtype, lvy__rpgfb.dtype, c.
        env_manager)
    nuudv__ebal = c.pyapi.borrow_none()
    wrx__eoz = c.pyapi.object_getattr_string(gbjz__pqwez, 'Categorical')
    bpuj__uhozi = c.pyapi.call_method(wrx__eoz, 'from_codes', (ghx__xcnnu,
        nuudv__ebal, nuudv__ebal, jfwxu__mvsu))
    c.pyapi.decref(wrx__eoz)
    c.pyapi.decref(ghx__xcnnu)
    c.pyapi.decref(jfwxu__mvsu)
    c.pyapi.decref(gbjz__pqwez)
    c.context.nrt.decref(c.builder, typ, val)
    return bpuj__uhozi


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
            hhbj__mydud = list(A.dtype.categories).index(val
                ) if val in A.dtype.categories else -2

            def impl_lit(A, other):
                wit__mozhk = op(bodo.hiframes.pd_categorical_ext.
                    get_categorical_arr_codes(A), hhbj__mydud)
                return wit__mozhk
            return impl_lit

        def impl(A, other):
            hhbj__mydud = get_code_for_value(A.dtype, other)
            wit__mozhk = op(bodo.hiframes.pd_categorical_ext.
                get_categorical_arr_codes(A), hhbj__mydud)
            return wit__mozhk
        return impl
    return overload_cat_arr_cmp


def _install_cmp_ops():
    for op in [operator.eq, operator.ne]:
        oqed__zyz = create_cmp_op_overload(op)
        overload(op, inline='always', no_unliteral=True)(oqed__zyz)


_install_cmp_ops()


@register_jitable
def get_code_for_value(cat_dtype, val):
    lvy__rpgfb = cat_dtype.categories
    n = len(lvy__rpgfb)
    for rdxq__uyn in range(n):
        if lvy__rpgfb[rdxq__uyn] == val:
            return rdxq__uyn
    return -2


@overload_method(CategoricalArrayType, 'astype', inline='always',
    no_unliteral=True)
def overload_cat_arr_astype(A, dtype, copy=True, _bodo_nan_to_str=True):
    if dtype == types.unicode_type:
        raise_bodo_error(
            "CategoricalArray.astype(): 'dtype' when passed as string must be a constant value"
            )
    lxvbl__vny = bodo.utils.typing.parse_dtype(dtype, 'CategoricalArray.astype'
        )
    if lxvbl__vny != A.dtype.elem_type and lxvbl__vny != types.unicode_type:
        raise BodoError(
            f'Converting categorical array {A} to dtype {dtype} not supported yet'
            )
    if lxvbl__vny == types.unicode_type:

        def impl(A, dtype, copy=True, _bodo_nan_to_str=True):
            codes = bodo.hiframes.pd_categorical_ext.get_categorical_arr_codes(
                A)
            categories = A.dtype.categories
            n = len(codes)
            wit__mozhk = bodo.libs.str_arr_ext.pre_alloc_string_array(n, -1)
            for rdxq__uyn in numba.parfors.parfor.internal_prange(n):
                llqq__fbmhn = codes[rdxq__uyn]
                if llqq__fbmhn == -1:
                    if _bodo_nan_to_str:
                        bodo.libs.str_arr_ext.str_arr_setitem_NA_str(wit__mozhk
                            , rdxq__uyn)
                    else:
                        bodo.libs.array_kernels.setna(wit__mozhk, rdxq__uyn)
                    continue
                wit__mozhk[rdxq__uyn] = str(bodo.utils.conversion.
                    unbox_if_timestamp(categories[llqq__fbmhn]))
            return wit__mozhk
        return impl
    jsup__eoko = dtype_to_array_type(lxvbl__vny)

    def impl(A, dtype, copy=True, _bodo_nan_to_str=True):
        codes = bodo.hiframes.pd_categorical_ext.get_categorical_arr_codes(A)
        categories = A.dtype.categories
        n = len(codes)
        wit__mozhk = bodo.utils.utils.alloc_type(n, jsup__eoko, (-1,))
        for rdxq__uyn in numba.parfors.parfor.internal_prange(n):
            llqq__fbmhn = codes[rdxq__uyn]
            if llqq__fbmhn == -1:
                bodo.libs.array_kernels.setna(wit__mozhk, rdxq__uyn)
                continue
            wit__mozhk[rdxq__uyn] = bodo.utils.conversion.unbox_if_timestamp(
                categories[llqq__fbmhn])
        return wit__mozhk
    return impl


@overload(pd.api.types.CategoricalDtype, no_unliteral=True)
def cat_overload_dummy(val_list):
    return lambda val_list: 1


@intrinsic
def init_categorical_array(typingctx, codes, cat_dtype=None):
    assert isinstance(codes, types.Array) and isinstance(codes.dtype, types
        .Integer)

    def codegen(context, builder, signature, args):
        bugq__plr, sujv__ruxu = args
        lvy__rpgfb = cgutils.create_struct_proxy(signature.return_type)(context
            , builder)
        lvy__rpgfb.codes = bugq__plr
        lvy__rpgfb.dtype = sujv__ruxu
        context.nrt.incref(builder, signature.args[0], bugq__plr)
        context.nrt.incref(builder, signature.args[1], sujv__ruxu)
        return lvy__rpgfb._getvalue()
    kbw__sxzfn = CategoricalArrayType(cat_dtype)
    sig = kbw__sxzfn(codes, cat_dtype)
    return sig, codegen


def init_categorical_array_equiv(self, scope, equiv_set, loc, args, kws):
    assert len(args) == 2 and not kws
    uzj__qcq = args[0]
    if equiv_set.has_shape(uzj__qcq):
        return ArrayAnalysis.AnalyzeResult(shape=uzj__qcq, pre=[])
    return None


(ArrayAnalysis.
    _analyze_op_call_bodo_hiframes_pd_categorical_ext_init_categorical_array
    ) = init_categorical_array_equiv


def alloc_categorical_array(n, cat_dtype):
    pass


@overload(alloc_categorical_array, no_unliteral=True)
def _alloc_categorical_array(n, cat_dtype):
    pdal__lcec = get_categories_int_type(cat_dtype)

    def impl(n, cat_dtype):
        codes = np.empty(n, pdal__lcec)
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
            wwtwe__jmwlt = {}
            mbex__kfh = np.empty(n + 1, np.int64)
            rzcaa__agxnb = {}
            ebq__idr = []
            lohed__euif = {}
            for rdxq__uyn in range(n):
                lohed__euif[categories[rdxq__uyn]] = rdxq__uyn
            for ulu__fxry in to_replace:
                if ulu__fxry != value:
                    if ulu__fxry in lohed__euif:
                        if value in lohed__euif:
                            wwtwe__jmwlt[ulu__fxry] = ulu__fxry
                            hcd__pci = lohed__euif[ulu__fxry]
                            rzcaa__agxnb[hcd__pci] = lohed__euif[value]
                            ebq__idr.append(hcd__pci)
                        else:
                            wwtwe__jmwlt[ulu__fxry] = value
                            lohed__euif[value] = lohed__euif[ulu__fxry]
            mpn__wugo = np.sort(np.array(ebq__idr))
            mtzct__crgaw = 0
            lvmb__zbfg = []
            for ptd__nnjwz in range(-1, n):
                while mtzct__crgaw < len(mpn__wugo) and ptd__nnjwz > mpn__wugo[
                    mtzct__crgaw]:
                    mtzct__crgaw += 1
                lvmb__zbfg.append(mtzct__crgaw)
            for ilwi__ifvb in range(-1, n):
                mizk__pqb = ilwi__ifvb
                if ilwi__ifvb in rzcaa__agxnb:
                    mizk__pqb = rzcaa__agxnb[ilwi__ifvb]
                mbex__kfh[ilwi__ifvb + 1] = mizk__pqb - lvmb__zbfg[
                    mizk__pqb + 1]
            return wwtwe__jmwlt, mbex__kfh, len(mpn__wugo)
        return impl


@numba.njit
def python_build_replace_dicts(to_replace, value, categories):
    return build_replace_dicts(to_replace, value, categories)


@register_jitable
def reassign_codes(new_codes_arr, old_codes_arr, codes_map_arr):
    for rdxq__uyn in range(len(new_codes_arr)):
        new_codes_arr[rdxq__uyn] = codes_map_arr[old_codes_arr[rdxq__uyn] + 1]


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
    difk__rujmj = arr.dtype.ordered
    kcadc__gtor = arr.dtype.elem_type
    czpe__gakco = get_overload_const(to_replace)
    cki__fhrn = get_overload_const(value)
    if (arr.dtype.categories is not None and czpe__gakco is not
        NOT_CONSTANT and cki__fhrn is not NOT_CONSTANT):
        jfs__ggoi, codes_map_arr, gocx__qzrtq = python_build_replace_dicts(
            czpe__gakco, cki__fhrn, arr.dtype.categories)
        if len(jfs__ggoi) == 0:
            return lambda arr, to_replace, value: arr.copy()
        wjheo__njwl = []
        for zsbu__kyzf in arr.dtype.categories:
            if zsbu__kyzf in jfs__ggoi:
                oxvnm__yeq = jfs__ggoi[zsbu__kyzf]
                if oxvnm__yeq != zsbu__kyzf:
                    wjheo__njwl.append(oxvnm__yeq)
            else:
                wjheo__njwl.append(zsbu__kyzf)
        nezk__tnehb = pd.CategoricalDtype(wjheo__njwl, difk__rujmj
            ).categories.values
        tonm__skvf = MetaType(tuple(nezk__tnehb))

        def impl_dtype(arr, to_replace, value):
            vca__kxnrc = init_cat_dtype(bodo.utils.conversion.
                index_from_array(nezk__tnehb), difk__rujmj, None, tonm__skvf)
            lvy__rpgfb = alloc_categorical_array(len(arr.codes), vca__kxnrc)
            reassign_codes(lvy__rpgfb.codes, arr.codes, codes_map_arr)
            return lvy__rpgfb
        return impl_dtype
    kcadc__gtor = arr.dtype.elem_type
    if kcadc__gtor == types.unicode_type:

        def impl_str(arr, to_replace, value):
            categories = arr.dtype.categories
            wwtwe__jmwlt, codes_map_arr, phjli__ypk = build_replace_dicts(
                to_replace, value, categories.values)
            if len(wwtwe__jmwlt) == 0:
                return init_categorical_array(arr.codes.copy().astype(np.
                    int64), init_cat_dtype(categories.copy(), difk__rujmj,
                    None, None))
            n = len(categories)
            nezk__tnehb = bodo.libs.str_arr_ext.pre_alloc_string_array(n -
                phjli__ypk, -1)
            amr__mbrmd = 0
            for ptd__nnjwz in range(n):
                dgu__dvn = categories[ptd__nnjwz]
                if dgu__dvn in wwtwe__jmwlt:
                    nsjw__yuxb = wwtwe__jmwlt[dgu__dvn]
                    if nsjw__yuxb != dgu__dvn:
                        nezk__tnehb[amr__mbrmd] = nsjw__yuxb
                        amr__mbrmd += 1
                else:
                    nezk__tnehb[amr__mbrmd] = dgu__dvn
                    amr__mbrmd += 1
            lvy__rpgfb = alloc_categorical_array(len(arr.codes),
                init_cat_dtype(bodo.utils.conversion.index_from_array(
                nezk__tnehb), difk__rujmj, None, None))
            reassign_codes(lvy__rpgfb.codes, arr.codes, codes_map_arr)
            return lvy__rpgfb
        return impl_str
    dgf__upp = dtype_to_array_type(kcadc__gtor)

    def impl(arr, to_replace, value):
        categories = arr.dtype.categories
        wwtwe__jmwlt, codes_map_arr, phjli__ypk = build_replace_dicts(
            to_replace, value, categories.values)
        if len(wwtwe__jmwlt) == 0:
            return init_categorical_array(arr.codes.copy().astype(np.int64),
                init_cat_dtype(categories.copy(), difk__rujmj, None, None))
        n = len(categories)
        nezk__tnehb = bodo.utils.utils.alloc_type(n - phjli__ypk, dgf__upp,
            None)
        amr__mbrmd = 0
        for rdxq__uyn in range(n):
            dgu__dvn = categories[rdxq__uyn]
            if dgu__dvn in wwtwe__jmwlt:
                nsjw__yuxb = wwtwe__jmwlt[dgu__dvn]
                if nsjw__yuxb != dgu__dvn:
                    nezk__tnehb[amr__mbrmd] = nsjw__yuxb
                    amr__mbrmd += 1
            else:
                nezk__tnehb[amr__mbrmd] = dgu__dvn
                amr__mbrmd += 1
        lvy__rpgfb = alloc_categorical_array(len(arr.codes), init_cat_dtype
            (bodo.utils.conversion.index_from_array(nezk__tnehb),
            difk__rujmj, None, None))
        reassign_codes(lvy__rpgfb.codes, arr.codes, codes_map_arr)
        return lvy__rpgfb
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
    gzas__tfwt = dict()
    fmx__hqtyi = 0
    for rdxq__uyn in range(len(vals)):
        val = vals[rdxq__uyn]
        if val in gzas__tfwt:
            continue
        gzas__tfwt[val] = fmx__hqtyi
        fmx__hqtyi += 1
    return gzas__tfwt


@register_jitable
def get_label_dict_from_categories_no_duplicates(vals):
    gzas__tfwt = dict()
    for rdxq__uyn in range(len(vals)):
        val = vals[rdxq__uyn]
        gzas__tfwt[val] = rdxq__uyn
    return gzas__tfwt


@overload(pd.Categorical, no_unliteral=True)
def pd_categorical_overload(values, categories=None, ordered=None, dtype=
    None, fastpath=False):
    qew__tvkkx = dict(fastpath=fastpath)
    tpd__lewlh = dict(fastpath=False)
    check_unsupported_args('pd.Categorical', qew__tvkkx, tpd__lewlh)
    if isinstance(dtype, bodo.hiframes.pd_categorical_ext.PDCategoricalDtype):

        def impl_dtype(values, categories=None, ordered=None, dtype=None,
            fastpath=False):
            data = bodo.utils.conversion.coerce_to_array(values)
            return bodo.utils.conversion.fix_arr_dtype(data, dtype)
        return impl_dtype
    if not is_overload_none(categories):
        lnvl__sdbb = get_overload_const(categories)
        if lnvl__sdbb is not NOT_CONSTANT and get_overload_const(ordered
            ) is not NOT_CONSTANT:
            if is_overload_none(ordered):
                wqe__psox = False
            else:
                wqe__psox = get_overload_const_bool(ordered)
            sqo__ywkez = pd.CategoricalDtype(lnvl__sdbb, wqe__psox
                ).categories.values
            upqns__fqgc = MetaType(tuple(sqo__ywkez))

            def impl_cats_const(values, categories=None, ordered=None,
                dtype=None, fastpath=False):
                data = bodo.utils.conversion.coerce_to_array(values)
                vca__kxnrc = init_cat_dtype(bodo.utils.conversion.
                    index_from_array(sqo__ywkez), wqe__psox, None, upqns__fqgc)
                return bodo.utils.conversion.fix_arr_dtype(data, vca__kxnrc)
            return impl_cats_const

        def impl_cats(values, categories=None, ordered=None, dtype=None,
            fastpath=False):
            ordered = bodo.utils.conversion.false_if_none(ordered)
            data = bodo.utils.conversion.coerce_to_array(values)
            aonld__mdcoo = bodo.utils.conversion.convert_to_index(categories)
            cat_dtype = bodo.hiframes.pd_categorical_ext.init_cat_dtype(
                aonld__mdcoo, ordered, None, None)
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
            opx__wul = arr.codes[ind]
            return arr.dtype.categories[max(opx__wul, 0)]
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
    for rdxq__uyn in range(len(arr1)):
        if arr1[rdxq__uyn] != arr2[rdxq__uyn]:
            return False
    return True


@overload(operator.setitem, no_unliteral=True)
def categorical_array_setitem(arr, ind, val):
    if not isinstance(arr, CategoricalArrayType):
        return
    if val == types.none or isinstance(val, types.optional):
        return
    qpbo__mgrw = is_scalar_type(val) and is_common_scalar_dtype([types.
        unliteral(val), arr.dtype.elem_type]) and not (isinstance(arr.dtype
        .elem_type, types.Integer) and isinstance(val, types.Float))
    osegh__rzpoy = not isinstance(val, CategoricalArrayType
        ) and is_iterable_type(val) and is_common_scalar_dtype([val.dtype,
        arr.dtype.elem_type]) and not (isinstance(arr.dtype.elem_type,
        types.Integer) and isinstance(val.dtype, types.Float))
    casnq__ftle = categorical_arrs_match(arr, val)
    qjim__wdio = (
        f"setitem for CategoricalArrayType of dtype {arr.dtype} with indexing type {ind} received an incorrect 'value' type {val}."
        )
    bry__fine = (
        'Cannot set a Categorical with another, without identical categories')
    if isinstance(ind, types.Integer):
        if not qpbo__mgrw:
            raise BodoError(qjim__wdio)

        def impl_scalar(arr, ind, val):
            if val not in arr.dtype.categories:
                raise ValueError(
                    'Cannot setitem on a Categorical with a new category, set the categories first'
                    )
            opx__wul = arr.dtype.categories.get_loc(val)
            arr.codes[ind] = opx__wul
        return impl_scalar
    if is_list_like_index_type(ind) and isinstance(ind.dtype, types.Integer):
        if not (qpbo__mgrw or osegh__rzpoy or casnq__ftle !=
            CategoricalMatchingValues.DIFFERENT_TYPES):
            raise BodoError(qjim__wdio)
        if casnq__ftle == CategoricalMatchingValues.DONT_MATCH:
            raise BodoError(bry__fine)
        if qpbo__mgrw:

            def impl_scalar(arr, ind, val):
                if val not in arr.dtype.categories:
                    raise ValueError(
                        'Cannot setitem on a Categorical with a new category, set the categories first'
                        )
                jlxke__jqtlq = arr.dtype.categories.get_loc(val)
                n = len(ind)
                for ptd__nnjwz in range(n):
                    arr.codes[ind[ptd__nnjwz]] = jlxke__jqtlq
            return impl_scalar
        if casnq__ftle == CategoricalMatchingValues.DO_MATCH:

            def impl_arr_ind_mask(arr, ind, val):
                n = len(val.codes)
                for rdxq__uyn in range(n):
                    arr.codes[ind[rdxq__uyn]] = val.codes[rdxq__uyn]
            return impl_arr_ind_mask
        if casnq__ftle == CategoricalMatchingValues.MAY_MATCH:

            def impl_arr_ind_mask(arr, ind, val):
                if not cat_dtype_equal(arr.dtype, val.dtype):
                    raise ValueError(bry__fine)
                n = len(val.codes)
                for rdxq__uyn in range(n):
                    arr.codes[ind[rdxq__uyn]] = val.codes[rdxq__uyn]
            return impl_arr_ind_mask
        if osegh__rzpoy:

            def impl_arr_ind_mask_cat_values(arr, ind, val):
                n = len(val)
                categories = arr.dtype.categories
                for ptd__nnjwz in range(n):
                    hhs__mow = bodo.utils.conversion.unbox_if_timestamp(val
                        [ptd__nnjwz])
                    if hhs__mow not in categories:
                        raise ValueError(
                            'Cannot setitem on a Categorical with a new category, set the categories first'
                            )
                    opx__wul = categories.get_loc(hhs__mow)
                    arr.codes[ind[ptd__nnjwz]] = opx__wul
            return impl_arr_ind_mask_cat_values
    if is_list_like_index_type(ind) and ind.dtype == types.bool_:
        if not (qpbo__mgrw or osegh__rzpoy or casnq__ftle !=
            CategoricalMatchingValues.DIFFERENT_TYPES):
            raise BodoError(qjim__wdio)
        if casnq__ftle == CategoricalMatchingValues.DONT_MATCH:
            raise BodoError(bry__fine)
        if qpbo__mgrw:

            def impl_scalar(arr, ind, val):
                if val not in arr.dtype.categories:
                    raise ValueError(
                        'Cannot setitem on a Categorical with a new category, set the categories first'
                        )
                jlxke__jqtlq = arr.dtype.categories.get_loc(val)
                n = len(ind)
                for ptd__nnjwz in range(n):
                    if ind[ptd__nnjwz]:
                        arr.codes[ptd__nnjwz] = jlxke__jqtlq
            return impl_scalar
        if casnq__ftle == CategoricalMatchingValues.DO_MATCH:

            def impl_bool_ind_mask(arr, ind, val):
                n = len(ind)
                unupj__ytjq = 0
                for rdxq__uyn in range(n):
                    if ind[rdxq__uyn]:
                        arr.codes[rdxq__uyn] = val.codes[unupj__ytjq]
                        unupj__ytjq += 1
            return impl_bool_ind_mask
        if casnq__ftle == CategoricalMatchingValues.MAY_MATCH:

            def impl_bool_ind_mask(arr, ind, val):
                if not cat_dtype_equal(arr.dtype, val.dtype):
                    raise ValueError(bry__fine)
                n = len(ind)
                unupj__ytjq = 0
                for rdxq__uyn in range(n):
                    if ind[rdxq__uyn]:
                        arr.codes[rdxq__uyn] = val.codes[unupj__ytjq]
                        unupj__ytjq += 1
            return impl_bool_ind_mask
        if osegh__rzpoy:

            def impl_bool_ind_mask_cat_values(arr, ind, val):
                n = len(ind)
                unupj__ytjq = 0
                categories = arr.dtype.categories
                for ptd__nnjwz in range(n):
                    if ind[ptd__nnjwz]:
                        hhs__mow = bodo.utils.conversion.unbox_if_timestamp(val
                            [unupj__ytjq])
                        if hhs__mow not in categories:
                            raise ValueError(
                                'Cannot setitem on a Categorical with a new category, set the categories first'
                                )
                        opx__wul = categories.get_loc(hhs__mow)
                        arr.codes[ptd__nnjwz] = opx__wul
                        unupj__ytjq += 1
            return impl_bool_ind_mask_cat_values
    if isinstance(ind, types.SliceType):
        if not (qpbo__mgrw or osegh__rzpoy or casnq__ftle !=
            CategoricalMatchingValues.DIFFERENT_TYPES):
            raise BodoError(qjim__wdio)
        if casnq__ftle == CategoricalMatchingValues.DONT_MATCH:
            raise BodoError(bry__fine)
        if qpbo__mgrw:

            def impl_scalar(arr, ind, val):
                if val not in arr.dtype.categories:
                    raise ValueError(
                        'Cannot setitem on a Categorical with a new category, set the categories first'
                        )
                jlxke__jqtlq = arr.dtype.categories.get_loc(val)
                xjzn__dexcx = numba.cpython.unicode._normalize_slice(ind,
                    len(arr))
                for ptd__nnjwz in range(xjzn__dexcx.start, xjzn__dexcx.stop,
                    xjzn__dexcx.step):
                    arr.codes[ptd__nnjwz] = jlxke__jqtlq
            return impl_scalar
        if casnq__ftle == CategoricalMatchingValues.DO_MATCH:

            def impl_arr(arr, ind, val):
                arr.codes[ind] = val.codes
            return impl_arr
        if casnq__ftle == CategoricalMatchingValues.MAY_MATCH:

            def impl_arr(arr, ind, val):
                if not cat_dtype_equal(arr.dtype, val.dtype):
                    raise ValueError(bry__fine)
                arr.codes[ind] = val.codes
            return impl_arr
        if osegh__rzpoy:

            def impl_slice_cat_values(arr, ind, val):
                categories = arr.dtype.categories
                xjzn__dexcx = numba.cpython.unicode._normalize_slice(ind,
                    len(arr))
                unupj__ytjq = 0
                for ptd__nnjwz in range(xjzn__dexcx.start, xjzn__dexcx.stop,
                    xjzn__dexcx.step):
                    hhs__mow = bodo.utils.conversion.unbox_if_timestamp(val
                        [unupj__ytjq])
                    if hhs__mow not in categories:
                        raise ValueError(
                            'Cannot setitem on a Categorical with a new category, set the categories first'
                            )
                    opx__wul = categories.get_loc(hhs__mow)
                    arr.codes[ptd__nnjwz] = opx__wul
                    unupj__ytjq += 1
            return impl_slice_cat_values
    raise BodoError(
        f'setitem for CategoricalArrayType with indexing type {ind} not supported.'
        )
