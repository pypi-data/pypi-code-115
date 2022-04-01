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
        dgs__nir = (
            f'PDCategoricalDtype({self.categories}, {self.elem_type}, {self.ordered}, {self.data}, {self.int_type})'
            )
        super(PDCategoricalDtype, self).__init__(name=dgs__nir)

    @property
    def mangling_args(self):
        return self.__class__.__name__, (self._code,)


@typeof_impl.register(pd.CategoricalDtype)
def _typeof_pd_cat_dtype(val, c):
    wdw__iyfx = tuple(val.categories.values)
    elem_type = None if len(wdw__iyfx) == 0 else bodo.typeof(val.categories
        .values).dtype
    int_type = getattr(val, '_int_type', None)
    return PDCategoricalDtype(wdw__iyfx, elem_type, val.ordered, bodo.
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
        wtbrz__shvx = [('categories', fe_type.data), ('ordered', types.bool_)]
        models.StructModel.__init__(self, dmm, fe_type, wtbrz__shvx)


make_attribute_wrapper(PDCategoricalDtype, 'categories', 'categories')
make_attribute_wrapper(PDCategoricalDtype, 'ordered', 'ordered')


@intrinsic
def init_cat_dtype(typingctx, categories_typ, ordered_typ, int_type,
    cat_vals_typ=None):
    assert bodo.hiframes.pd_index_ext.is_index_type(categories_typ
        ), 'init_cat_dtype requires index type for categories'
    assert is_overload_constant_bool(ordered_typ
        ), 'init_cat_dtype requires constant ordered flag'
    qftf__qhy = None if is_overload_none(int_type) else int_type.dtype
    assert is_overload_none(cat_vals_typ) or isinstance(cat_vals_typ, types
        .TypeRef), 'init_cat_dtype requires constant category values'
    hho__ppmpq = None if is_overload_none(cat_vals_typ
        ) else cat_vals_typ.instance_type.meta

    def codegen(context, builder, sig, args):
        categories, ordered, xbr__ohei, xbr__ohei = args
        cat_dtype = cgutils.create_struct_proxy(sig.return_type)(context,
            builder)
        cat_dtype.categories = categories
        context.nrt.incref(builder, sig.args[0], categories)
        context.nrt.incref(builder, sig.args[1], ordered)
        cat_dtype.ordered = ordered
        return cat_dtype._getvalue()
    tkv__plerp = PDCategoricalDtype(hho__ppmpq, categories_typ.dtype,
        is_overload_true(ordered_typ), categories_typ, qftf__qhy)
    return tkv__plerp(categories_typ, ordered_typ, int_type, cat_vals_typ
        ), codegen


@unbox(PDCategoricalDtype)
def unbox_cat_dtype(typ, obj, c):
    cat_dtype = cgutils.create_struct_proxy(typ)(c.context, c.builder)
    zexrg__vbuu = c.pyapi.object_getattr_string(obj, 'ordered')
    cat_dtype.ordered = c.pyapi.to_native_value(types.bool_, zexrg__vbuu).value
    c.pyapi.decref(zexrg__vbuu)
    wne__bupag = c.pyapi.object_getattr_string(obj, 'categories')
    cat_dtype.categories = c.pyapi.to_native_value(typ.data, wne__bupag).value
    c.pyapi.decref(wne__bupag)
    kdv__uboe = cgutils.is_not_null(c.builder, c.pyapi.err_occurred())
    return NativeValue(cat_dtype._getvalue(), is_error=kdv__uboe)


@box(PDCategoricalDtype)
def box_cat_dtype(typ, val, c):
    cat_dtype = cgutils.create_struct_proxy(typ)(c.context, c.builder, val)
    zexrg__vbuu = c.pyapi.from_native_value(types.bool_, cat_dtype.ordered,
        c.env_manager)
    c.context.nrt.incref(c.builder, typ.data, cat_dtype.categories)
    cfscl__zeyfb = c.pyapi.from_native_value(typ.data, cat_dtype.categories,
        c.env_manager)
    vbo__ugy = c.context.insert_const_string(c.builder.module, 'pandas')
    cpyxy__xmf = c.pyapi.import_module_noblock(vbo__ugy)
    vemm__udk = c.pyapi.call_method(cpyxy__xmf, 'CategoricalDtype', (
        cfscl__zeyfb, zexrg__vbuu))
    c.pyapi.decref(zexrg__vbuu)
    c.pyapi.decref(cfscl__zeyfb)
    c.pyapi.decref(cpyxy__xmf)
    c.context.nrt.decref(c.builder, typ, val)
    return vemm__udk


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
        ijp__obj = get_categories_int_type(fe_type.dtype)
        wtbrz__shvx = [('dtype', fe_type.dtype), ('codes', types.Array(
            ijp__obj, 1, 'C'))]
        super(CategoricalArrayModel, self).__init__(dmm, fe_type, wtbrz__shvx)


make_attribute_wrapper(CategoricalArrayType, 'codes', 'codes')
make_attribute_wrapper(CategoricalArrayType, 'dtype', 'dtype')


@unbox(CategoricalArrayType)
def unbox_categorical_array(typ, val, c):
    mwucr__pop = c.pyapi.object_getattr_string(val, 'codes')
    dtype = get_categories_int_type(typ.dtype)
    codes = c.pyapi.to_native_value(types.Array(dtype, 1, 'C'), mwucr__pop
        ).value
    c.pyapi.decref(mwucr__pop)
    vemm__udk = c.pyapi.object_getattr_string(val, 'dtype')
    iro__swmhs = c.pyapi.to_native_value(typ.dtype, vemm__udk).value
    c.pyapi.decref(vemm__udk)
    ycvbn__ttco = cgutils.create_struct_proxy(typ)(c.context, c.builder)
    ycvbn__ttco.codes = codes
    ycvbn__ttco.dtype = iro__swmhs
    return NativeValue(ycvbn__ttco._getvalue())


@lower_constant(CategoricalArrayType)
def lower_constant_categorical_array(context, builder, typ, pyval):
    owgk__fxj = get_categories_int_type(typ.dtype)
    ohjrv__asuk = context.get_constant_generic(builder, types.Array(
        owgk__fxj, 1, 'C'), pyval.codes)
    cat_dtype = context.get_constant_generic(builder, typ.dtype, pyval.dtype)
    return lir.Constant.literal_struct([cat_dtype, ohjrv__asuk])


def get_categories_int_type(cat_dtype):
    dtype = types.int64
    if cat_dtype.int_type is not None:
        return cat_dtype.int_type
    if cat_dtype.categories is None:
        return types.int64
    pihtm__dbfon = len(cat_dtype.categories)
    if pihtm__dbfon < np.iinfo(np.int8).max:
        dtype = types.int8
    elif pihtm__dbfon < np.iinfo(np.int16).max:
        dtype = types.int16
    elif pihtm__dbfon < np.iinfo(np.int32).max:
        dtype = types.int32
    return dtype


@box(CategoricalArrayType)
def box_categorical_array(typ, val, c):
    dtype = typ.dtype
    vbo__ugy = c.context.insert_const_string(c.builder.module, 'pandas')
    cpyxy__xmf = c.pyapi.import_module_noblock(vbo__ugy)
    ijp__obj = get_categories_int_type(dtype)
    utqc__zjsby = cgutils.create_struct_proxy(typ)(c.context, c.builder, val)
    hzp__qbl = types.Array(ijp__obj, 1, 'C')
    c.context.nrt.incref(c.builder, hzp__qbl, utqc__zjsby.codes)
    mwucr__pop = c.pyapi.from_native_value(hzp__qbl, utqc__zjsby.codes, c.
        env_manager)
    c.context.nrt.incref(c.builder, dtype, utqc__zjsby.dtype)
    vemm__udk = c.pyapi.from_native_value(dtype, utqc__zjsby.dtype, c.
        env_manager)
    cjxb__ukhm = c.pyapi.borrow_none()
    cvtjz__tlba = c.pyapi.object_getattr_string(cpyxy__xmf, 'Categorical')
    ogr__lrgh = c.pyapi.call_method(cvtjz__tlba, 'from_codes', (mwucr__pop,
        cjxb__ukhm, cjxb__ukhm, vemm__udk))
    c.pyapi.decref(cvtjz__tlba)
    c.pyapi.decref(mwucr__pop)
    c.pyapi.decref(vemm__udk)
    c.pyapi.decref(cpyxy__xmf)
    c.context.nrt.decref(c.builder, typ, val)
    return ogr__lrgh


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
            bgj__slo = list(A.dtype.categories).index(val
                ) if val in A.dtype.categories else -2

            def impl_lit(A, other):
                jhjoy__nqt = op(bodo.hiframes.pd_categorical_ext.
                    get_categorical_arr_codes(A), bgj__slo)
                return jhjoy__nqt
            return impl_lit

        def impl(A, other):
            bgj__slo = get_code_for_value(A.dtype, other)
            jhjoy__nqt = op(bodo.hiframes.pd_categorical_ext.
                get_categorical_arr_codes(A), bgj__slo)
            return jhjoy__nqt
        return impl
    return overload_cat_arr_cmp


def _install_cmp_ops():
    for op in [operator.eq, operator.ne]:
        uge__cuf = create_cmp_op_overload(op)
        overload(op, inline='always', no_unliteral=True)(uge__cuf)


_install_cmp_ops()


@register_jitable
def get_code_for_value(cat_dtype, val):
    utqc__zjsby = cat_dtype.categories
    n = len(utqc__zjsby)
    for cdr__slxk in range(n):
        if utqc__zjsby[cdr__slxk] == val:
            return cdr__slxk
    return -2


@overload_method(CategoricalArrayType, 'astype', inline='always',
    no_unliteral=True)
def overload_cat_arr_astype(A, dtype, copy=True, _bodo_nan_to_str=True):
    if dtype == types.unicode_type:
        raise_bodo_error(
            "CategoricalArray.astype(): 'dtype' when passed as string must be a constant value"
            )
    cbko__woas = bodo.utils.typing.parse_dtype(dtype, 'CategoricalArray.astype'
        )
    if cbko__woas != A.dtype.elem_type and cbko__woas != types.unicode_type:
        raise BodoError(
            f'Converting categorical array {A} to dtype {dtype} not supported yet'
            )
    if cbko__woas == types.unicode_type:

        def impl(A, dtype, copy=True, _bodo_nan_to_str=True):
            codes = bodo.hiframes.pd_categorical_ext.get_categorical_arr_codes(
                A)
            categories = A.dtype.categories
            n = len(codes)
            jhjoy__nqt = bodo.libs.str_arr_ext.pre_alloc_string_array(n, -1)
            for cdr__slxk in numba.parfors.parfor.internal_prange(n):
                wtf__noae = codes[cdr__slxk]
                if wtf__noae == -1:
                    if _bodo_nan_to_str:
                        bodo.libs.str_arr_ext.str_arr_setitem_NA_str(jhjoy__nqt
                            , cdr__slxk)
                    else:
                        bodo.libs.array_kernels.setna(jhjoy__nqt, cdr__slxk)
                    continue
                jhjoy__nqt[cdr__slxk] = str(bodo.utils.conversion.
                    unbox_if_timestamp(categories[wtf__noae]))
            return jhjoy__nqt
        return impl
    hzp__qbl = dtype_to_array_type(cbko__woas)

    def impl(A, dtype, copy=True, _bodo_nan_to_str=True):
        codes = bodo.hiframes.pd_categorical_ext.get_categorical_arr_codes(A)
        categories = A.dtype.categories
        n = len(codes)
        jhjoy__nqt = bodo.utils.utils.alloc_type(n, hzp__qbl, (-1,))
        for cdr__slxk in numba.parfors.parfor.internal_prange(n):
            wtf__noae = codes[cdr__slxk]
            if wtf__noae == -1:
                bodo.libs.array_kernels.setna(jhjoy__nqt, cdr__slxk)
                continue
            jhjoy__nqt[cdr__slxk] = bodo.utils.conversion.unbox_if_timestamp(
                categories[wtf__noae])
        return jhjoy__nqt
    return impl


@overload(pd.api.types.CategoricalDtype, no_unliteral=True)
def cat_overload_dummy(val_list):
    return lambda val_list: 1


@intrinsic
def init_categorical_array(typingctx, codes, cat_dtype=None):
    assert isinstance(codes, types.Array) and isinstance(codes.dtype, types
        .Integer)

    def codegen(context, builder, signature, args):
        rws__nrmm, iro__swmhs = args
        utqc__zjsby = cgutils.create_struct_proxy(signature.return_type)(
            context, builder)
        utqc__zjsby.codes = rws__nrmm
        utqc__zjsby.dtype = iro__swmhs
        context.nrt.incref(builder, signature.args[0], rws__nrmm)
        context.nrt.incref(builder, signature.args[1], iro__swmhs)
        return utqc__zjsby._getvalue()
    ijmsp__soe = CategoricalArrayType(cat_dtype)
    sig = ijmsp__soe(codes, cat_dtype)
    return sig, codegen


def init_categorical_array_equiv(self, scope, equiv_set, loc, args, kws):
    assert len(args) == 2 and not kws
    msjp__cye = args[0]
    if equiv_set.has_shape(msjp__cye):
        return ArrayAnalysis.AnalyzeResult(shape=msjp__cye, pre=[])
    return None


(ArrayAnalysis.
    _analyze_op_call_bodo_hiframes_pd_categorical_ext_init_categorical_array
    ) = init_categorical_array_equiv


def alloc_categorical_array(n, cat_dtype):
    pass


@overload(alloc_categorical_array, no_unliteral=True)
def _alloc_categorical_array(n, cat_dtype):
    ijp__obj = get_categories_int_type(cat_dtype)

    def impl(n, cat_dtype):
        codes = np.empty(n, ijp__obj)
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
            rpjpb__shqe = {}
            ohjrv__asuk = np.empty(n + 1, np.int64)
            byqsp__fldu = {}
            nid__yup = []
            dfmh__hwlr = {}
            for cdr__slxk in range(n):
                dfmh__hwlr[categories[cdr__slxk]] = cdr__slxk
            for tkh__rju in to_replace:
                if tkh__rju != value:
                    if tkh__rju in dfmh__hwlr:
                        if value in dfmh__hwlr:
                            rpjpb__shqe[tkh__rju] = tkh__rju
                            wrjr__xmf = dfmh__hwlr[tkh__rju]
                            byqsp__fldu[wrjr__xmf] = dfmh__hwlr[value]
                            nid__yup.append(wrjr__xmf)
                        else:
                            rpjpb__shqe[tkh__rju] = value
                            dfmh__hwlr[value] = dfmh__hwlr[tkh__rju]
            nevg__wmazg = np.sort(np.array(nid__yup))
            avhv__ipef = 0
            yxln__xbhl = []
            for gcyto__taiw in range(-1, n):
                while avhv__ipef < len(nevg__wmazg
                    ) and gcyto__taiw > nevg__wmazg[avhv__ipef]:
                    avhv__ipef += 1
                yxln__xbhl.append(avhv__ipef)
            for epk__ozx in range(-1, n):
                vpyqw__ugtdr = epk__ozx
                if epk__ozx in byqsp__fldu:
                    vpyqw__ugtdr = byqsp__fldu[epk__ozx]
                ohjrv__asuk[epk__ozx + 1] = vpyqw__ugtdr - yxln__xbhl[
                    vpyqw__ugtdr + 1]
            return rpjpb__shqe, ohjrv__asuk, len(nevg__wmazg)
        return impl


@numba.njit
def python_build_replace_dicts(to_replace, value, categories):
    return build_replace_dicts(to_replace, value, categories)


@register_jitable
def reassign_codes(new_codes_arr, old_codes_arr, codes_map_arr):
    for cdr__slxk in range(len(new_codes_arr)):
        new_codes_arr[cdr__slxk] = codes_map_arr[old_codes_arr[cdr__slxk] + 1]


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
    bodo.hiframes.pd_timestamp_ext.check_tz_aware_unsupported(to_replace,
        'CategoricalArray.replace()')
    bodo.hiframes.pd_timestamp_ext.check_tz_aware_unsupported(value,
        'CategoricalArray.replace()')
    mintw__cucis = arr.dtype.ordered
    kbmfs__xabj = arr.dtype.elem_type
    hrqpd__atgy = get_overload_const(to_replace)
    xmnd__ubv = get_overload_const(value)
    if (arr.dtype.categories is not None and hrqpd__atgy is not
        NOT_CONSTANT and xmnd__ubv is not NOT_CONSTANT):
        xuc__eopl, codes_map_arr, xbr__ohei = python_build_replace_dicts(
            hrqpd__atgy, xmnd__ubv, arr.dtype.categories)
        if len(xuc__eopl) == 0:
            return lambda arr, to_replace, value: arr.copy()
        hepvy__ookps = []
        for gjgm__pqs in arr.dtype.categories:
            if gjgm__pqs in xuc__eopl:
                zcb__hcpek = xuc__eopl[gjgm__pqs]
                if zcb__hcpek != gjgm__pqs:
                    hepvy__ookps.append(zcb__hcpek)
            else:
                hepvy__ookps.append(gjgm__pqs)
        rrta__tpq = pd.CategoricalDtype(hepvy__ookps, mintw__cucis
            ).categories.values
        hmica__bnq = MetaType(tuple(rrta__tpq))

        def impl_dtype(arr, to_replace, value):
            may__lns = init_cat_dtype(bodo.utils.conversion.
                index_from_array(rrta__tpq), mintw__cucis, None, hmica__bnq)
            utqc__zjsby = alloc_categorical_array(len(arr.codes), may__lns)
            reassign_codes(utqc__zjsby.codes, arr.codes, codes_map_arr)
            return utqc__zjsby
        return impl_dtype
    kbmfs__xabj = arr.dtype.elem_type
    if kbmfs__xabj == types.unicode_type:

        def impl_str(arr, to_replace, value):
            categories = arr.dtype.categories
            rpjpb__shqe, codes_map_arr, vlc__fuz = build_replace_dicts(
                to_replace, value, categories.values)
            if len(rpjpb__shqe) == 0:
                return init_categorical_array(arr.codes.copy().astype(np.
                    int64), init_cat_dtype(categories.copy(), mintw__cucis,
                    None, None))
            n = len(categories)
            rrta__tpq = bodo.libs.str_arr_ext.pre_alloc_string_array(n -
                vlc__fuz, -1)
            bjafs__bqvw = 0
            for gcyto__taiw in range(n):
                sapkr__gaqif = categories[gcyto__taiw]
                if sapkr__gaqif in rpjpb__shqe:
                    rjcfv__rxewa = rpjpb__shqe[sapkr__gaqif]
                    if rjcfv__rxewa != sapkr__gaqif:
                        rrta__tpq[bjafs__bqvw] = rjcfv__rxewa
                        bjafs__bqvw += 1
                else:
                    rrta__tpq[bjafs__bqvw] = sapkr__gaqif
                    bjafs__bqvw += 1
            utqc__zjsby = alloc_categorical_array(len(arr.codes),
                init_cat_dtype(bodo.utils.conversion.index_from_array(
                rrta__tpq), mintw__cucis, None, None))
            reassign_codes(utqc__zjsby.codes, arr.codes, codes_map_arr)
            return utqc__zjsby
        return impl_str
    mvzmg__nepq = dtype_to_array_type(kbmfs__xabj)

    def impl(arr, to_replace, value):
        categories = arr.dtype.categories
        rpjpb__shqe, codes_map_arr, vlc__fuz = build_replace_dicts(to_replace,
            value, categories.values)
        if len(rpjpb__shqe) == 0:
            return init_categorical_array(arr.codes.copy().astype(np.int64),
                init_cat_dtype(categories.copy(), mintw__cucis, None, None))
        n = len(categories)
        rrta__tpq = bodo.utils.utils.alloc_type(n - vlc__fuz, mvzmg__nepq, None
            )
        bjafs__bqvw = 0
        for cdr__slxk in range(n):
            sapkr__gaqif = categories[cdr__slxk]
            if sapkr__gaqif in rpjpb__shqe:
                rjcfv__rxewa = rpjpb__shqe[sapkr__gaqif]
                if rjcfv__rxewa != sapkr__gaqif:
                    rrta__tpq[bjafs__bqvw] = rjcfv__rxewa
                    bjafs__bqvw += 1
            else:
                rrta__tpq[bjafs__bqvw] = sapkr__gaqif
                bjafs__bqvw += 1
        utqc__zjsby = alloc_categorical_array(len(arr.codes),
            init_cat_dtype(bodo.utils.conversion.index_from_array(rrta__tpq
            ), mintw__cucis, None, None))
        reassign_codes(utqc__zjsby.codes, arr.codes, codes_map_arr)
        return utqc__zjsby
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
    yftio__smw = dict()
    jmjab__obwoh = 0
    for cdr__slxk in range(len(vals)):
        val = vals[cdr__slxk]
        if val in yftio__smw:
            continue
        yftio__smw[val] = jmjab__obwoh
        jmjab__obwoh += 1
    return yftio__smw


@register_jitable
def get_label_dict_from_categories_no_duplicates(vals):
    yftio__smw = dict()
    for cdr__slxk in range(len(vals)):
        val = vals[cdr__slxk]
        yftio__smw[val] = cdr__slxk
    return yftio__smw


@overload(pd.Categorical, no_unliteral=True)
def pd_categorical_overload(values, categories=None, ordered=None, dtype=
    None, fastpath=False):
    nrae__bpwr = dict(fastpath=fastpath)
    hrnd__dvouh = dict(fastpath=False)
    check_unsupported_args('pd.Categorical', nrae__bpwr, hrnd__dvouh)
    if isinstance(dtype, bodo.hiframes.pd_categorical_ext.PDCategoricalDtype):

        def impl_dtype(values, categories=None, ordered=None, dtype=None,
            fastpath=False):
            data = bodo.utils.conversion.coerce_to_array(values)
            return bodo.utils.conversion.fix_arr_dtype(data, dtype)
        return impl_dtype
    if not is_overload_none(categories):
        mkxmv__dllx = get_overload_const(categories)
        if mkxmv__dllx is not NOT_CONSTANT and get_overload_const(ordered
            ) is not NOT_CONSTANT:
            if is_overload_none(ordered):
                pmi__bgn = False
            else:
                pmi__bgn = get_overload_const_bool(ordered)
            pmscn__boeg = pd.CategoricalDtype(mkxmv__dllx, pmi__bgn
                ).categories.values
            kkmsn__xjc = MetaType(tuple(pmscn__boeg))

            def impl_cats_const(values, categories=None, ordered=None,
                dtype=None, fastpath=False):
                data = bodo.utils.conversion.coerce_to_array(values)
                may__lns = init_cat_dtype(bodo.utils.conversion.
                    index_from_array(pmscn__boeg), pmi__bgn, None, kkmsn__xjc)
                return bodo.utils.conversion.fix_arr_dtype(data, may__lns)
            return impl_cats_const

        def impl_cats(values, categories=None, ordered=None, dtype=None,
            fastpath=False):
            ordered = bodo.utils.conversion.false_if_none(ordered)
            data = bodo.utils.conversion.coerce_to_array(values)
            wdw__iyfx = bodo.utils.conversion.convert_to_index(categories)
            cat_dtype = bodo.hiframes.pd_categorical_ext.init_cat_dtype(
                wdw__iyfx, ordered, None, None)
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
            ppzy__bzz = arr.codes[ind]
            return arr.dtype.categories[max(ppzy__bzz, 0)]
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
    for cdr__slxk in range(len(arr1)):
        if arr1[cdr__slxk] != arr2[cdr__slxk]:
            return False
    return True


@overload(operator.setitem, no_unliteral=True)
def categorical_array_setitem(arr, ind, val):
    if not isinstance(arr, CategoricalArrayType):
        return
    if val == types.none or isinstance(val, types.optional):
        return
    uhqnw__yqw = is_scalar_type(val) and is_common_scalar_dtype([types.
        unliteral(val), arr.dtype.elem_type]) and not (isinstance(arr.dtype
        .elem_type, types.Integer) and isinstance(val, types.Float))
    pti__mpj = not isinstance(val, CategoricalArrayType) and is_iterable_type(
        val) and is_common_scalar_dtype([val.dtype, arr.dtype.elem_type]
        ) and not (isinstance(arr.dtype.elem_type, types.Integer) and
        isinstance(val.dtype, types.Float))
    yrzdn__hluib = categorical_arrs_match(arr, val)
    hzls__dldus = (
        f"setitem for CategoricalArrayType of dtype {arr.dtype} with indexing type {ind} received an incorrect 'value' type {val}."
        )
    dvkny__rplz = (
        'Cannot set a Categorical with another, without identical categories')
    if isinstance(ind, types.Integer):
        if not uhqnw__yqw:
            raise BodoError(hzls__dldus)

        def impl_scalar(arr, ind, val):
            if val not in arr.dtype.categories:
                raise ValueError(
                    'Cannot setitem on a Categorical with a new category, set the categories first'
                    )
            ppzy__bzz = arr.dtype.categories.get_loc(val)
            arr.codes[ind] = ppzy__bzz
        return impl_scalar
    if is_list_like_index_type(ind) and isinstance(ind.dtype, types.Integer):
        if not (uhqnw__yqw or pti__mpj or yrzdn__hluib !=
            CategoricalMatchingValues.DIFFERENT_TYPES):
            raise BodoError(hzls__dldus)
        if yrzdn__hluib == CategoricalMatchingValues.DONT_MATCH:
            raise BodoError(dvkny__rplz)
        if uhqnw__yqw:

            def impl_scalar(arr, ind, val):
                if val not in arr.dtype.categories:
                    raise ValueError(
                        'Cannot setitem on a Categorical with a new category, set the categories first'
                        )
                ecp__mycdz = arr.dtype.categories.get_loc(val)
                n = len(ind)
                for gcyto__taiw in range(n):
                    arr.codes[ind[gcyto__taiw]] = ecp__mycdz
            return impl_scalar
        if yrzdn__hluib == CategoricalMatchingValues.DO_MATCH:

            def impl_arr_ind_mask(arr, ind, val):
                n = len(val.codes)
                for cdr__slxk in range(n):
                    arr.codes[ind[cdr__slxk]] = val.codes[cdr__slxk]
            return impl_arr_ind_mask
        if yrzdn__hluib == CategoricalMatchingValues.MAY_MATCH:

            def impl_arr_ind_mask(arr, ind, val):
                if not cat_dtype_equal(arr.dtype, val.dtype):
                    raise ValueError(dvkny__rplz)
                n = len(val.codes)
                for cdr__slxk in range(n):
                    arr.codes[ind[cdr__slxk]] = val.codes[cdr__slxk]
            return impl_arr_ind_mask
        if pti__mpj:

            def impl_arr_ind_mask_cat_values(arr, ind, val):
                n = len(val)
                categories = arr.dtype.categories
                for gcyto__taiw in range(n):
                    wqbh__spgp = bodo.utils.conversion.unbox_if_timestamp(val
                        [gcyto__taiw])
                    if wqbh__spgp not in categories:
                        raise ValueError(
                            'Cannot setitem on a Categorical with a new category, set the categories first'
                            )
                    ppzy__bzz = categories.get_loc(wqbh__spgp)
                    arr.codes[ind[gcyto__taiw]] = ppzy__bzz
            return impl_arr_ind_mask_cat_values
    if is_list_like_index_type(ind) and ind.dtype == types.bool_:
        if not (uhqnw__yqw or pti__mpj or yrzdn__hluib !=
            CategoricalMatchingValues.DIFFERENT_TYPES):
            raise BodoError(hzls__dldus)
        if yrzdn__hluib == CategoricalMatchingValues.DONT_MATCH:
            raise BodoError(dvkny__rplz)
        if uhqnw__yqw:

            def impl_scalar(arr, ind, val):
                if val not in arr.dtype.categories:
                    raise ValueError(
                        'Cannot setitem on a Categorical with a new category, set the categories first'
                        )
                ecp__mycdz = arr.dtype.categories.get_loc(val)
                n = len(ind)
                for gcyto__taiw in range(n):
                    if ind[gcyto__taiw]:
                        arr.codes[gcyto__taiw] = ecp__mycdz
            return impl_scalar
        if yrzdn__hluib == CategoricalMatchingValues.DO_MATCH:

            def impl_bool_ind_mask(arr, ind, val):
                n = len(ind)
                qvzd__zjq = 0
                for cdr__slxk in range(n):
                    if ind[cdr__slxk]:
                        arr.codes[cdr__slxk] = val.codes[qvzd__zjq]
                        qvzd__zjq += 1
            return impl_bool_ind_mask
        if yrzdn__hluib == CategoricalMatchingValues.MAY_MATCH:

            def impl_bool_ind_mask(arr, ind, val):
                if not cat_dtype_equal(arr.dtype, val.dtype):
                    raise ValueError(dvkny__rplz)
                n = len(ind)
                qvzd__zjq = 0
                for cdr__slxk in range(n):
                    if ind[cdr__slxk]:
                        arr.codes[cdr__slxk] = val.codes[qvzd__zjq]
                        qvzd__zjq += 1
            return impl_bool_ind_mask
        if pti__mpj:

            def impl_bool_ind_mask_cat_values(arr, ind, val):
                n = len(ind)
                qvzd__zjq = 0
                categories = arr.dtype.categories
                for gcyto__taiw in range(n):
                    if ind[gcyto__taiw]:
                        wqbh__spgp = bodo.utils.conversion.unbox_if_timestamp(
                            val[qvzd__zjq])
                        if wqbh__spgp not in categories:
                            raise ValueError(
                                'Cannot setitem on a Categorical with a new category, set the categories first'
                                )
                        ppzy__bzz = categories.get_loc(wqbh__spgp)
                        arr.codes[gcyto__taiw] = ppzy__bzz
                        qvzd__zjq += 1
            return impl_bool_ind_mask_cat_values
    if isinstance(ind, types.SliceType):
        if not (uhqnw__yqw or pti__mpj or yrzdn__hluib !=
            CategoricalMatchingValues.DIFFERENT_TYPES):
            raise BodoError(hzls__dldus)
        if yrzdn__hluib == CategoricalMatchingValues.DONT_MATCH:
            raise BodoError(dvkny__rplz)
        if uhqnw__yqw:

            def impl_scalar(arr, ind, val):
                if val not in arr.dtype.categories:
                    raise ValueError(
                        'Cannot setitem on a Categorical with a new category, set the categories first'
                        )
                ecp__mycdz = arr.dtype.categories.get_loc(val)
                iarct__pulx = numba.cpython.unicode._normalize_slice(ind,
                    len(arr))
                for gcyto__taiw in range(iarct__pulx.start, iarct__pulx.
                    stop, iarct__pulx.step):
                    arr.codes[gcyto__taiw] = ecp__mycdz
            return impl_scalar
        if yrzdn__hluib == CategoricalMatchingValues.DO_MATCH:

            def impl_arr(arr, ind, val):
                arr.codes[ind] = val.codes
            return impl_arr
        if yrzdn__hluib == CategoricalMatchingValues.MAY_MATCH:

            def impl_arr(arr, ind, val):
                if not cat_dtype_equal(arr.dtype, val.dtype):
                    raise ValueError(dvkny__rplz)
                arr.codes[ind] = val.codes
            return impl_arr
        if pti__mpj:

            def impl_slice_cat_values(arr, ind, val):
                categories = arr.dtype.categories
                iarct__pulx = numba.cpython.unicode._normalize_slice(ind,
                    len(arr))
                qvzd__zjq = 0
                for gcyto__taiw in range(iarct__pulx.start, iarct__pulx.
                    stop, iarct__pulx.step):
                    wqbh__spgp = bodo.utils.conversion.unbox_if_timestamp(val
                        [qvzd__zjq])
                    if wqbh__spgp not in categories:
                        raise ValueError(
                            'Cannot setitem on a Categorical with a new category, set the categories first'
                            )
                    ppzy__bzz = categories.get_loc(wqbh__spgp)
                    arr.codes[gcyto__taiw] = ppzy__bzz
                    qvzd__zjq += 1
            return impl_slice_cat_values
    raise BodoError(
        f'setitem for CategoricalArrayType with indexing type {ind} not supported.'
        )
