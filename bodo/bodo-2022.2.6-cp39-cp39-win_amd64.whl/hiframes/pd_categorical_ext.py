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
        lhg__els = (
            f'PDCategoricalDtype({self.categories}, {self.elem_type}, {self.ordered}, {self.data}, {self.int_type})'
            )
        super(PDCategoricalDtype, self).__init__(name=lhg__els)

    @property
    def mangling_args(self):
        return self.__class__.__name__, (self._code,)


@typeof_impl.register(pd.CategoricalDtype)
def _typeof_pd_cat_dtype(val, c):
    wrcnz__mjuf = tuple(val.categories.values)
    elem_type = None if len(wrcnz__mjuf) == 0 else bodo.typeof(val.
        categories.values).dtype
    int_type = getattr(val, '_int_type', None)
    return PDCategoricalDtype(wrcnz__mjuf, elem_type, val.ordered, bodo.
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
        jvsmh__jsjnf = [('categories', fe_type.data), ('ordered', types.bool_)]
        models.StructModel.__init__(self, dmm, fe_type, jvsmh__jsjnf)


make_attribute_wrapper(PDCategoricalDtype, 'categories', 'categories')
make_attribute_wrapper(PDCategoricalDtype, 'ordered', 'ordered')


@intrinsic
def init_cat_dtype(typingctx, categories_typ, ordered_typ, int_type,
    cat_vals_typ=None):
    assert bodo.hiframes.pd_index_ext.is_index_type(categories_typ
        ), 'init_cat_dtype requires index type for categories'
    assert is_overload_constant_bool(ordered_typ
        ), 'init_cat_dtype requires constant ordered flag'
    aumii__trqq = None if is_overload_none(int_type) else int_type.dtype
    assert is_overload_none(cat_vals_typ) or isinstance(cat_vals_typ, types
        .TypeRef), 'init_cat_dtype requires constant category values'
    mlmw__tze = None if is_overload_none(cat_vals_typ
        ) else cat_vals_typ.instance_type.meta

    def codegen(context, builder, sig, args):
        categories, ordered, ceerk__cpa, ceerk__cpa = args
        cat_dtype = cgutils.create_struct_proxy(sig.return_type)(context,
            builder)
        cat_dtype.categories = categories
        context.nrt.incref(builder, sig.args[0], categories)
        context.nrt.incref(builder, sig.args[1], ordered)
        cat_dtype.ordered = ordered
        return cat_dtype._getvalue()
    epus__qzyxq = PDCategoricalDtype(mlmw__tze, categories_typ.dtype,
        is_overload_true(ordered_typ), categories_typ, aumii__trqq)
    return epus__qzyxq(categories_typ, ordered_typ, int_type, cat_vals_typ
        ), codegen


@unbox(PDCategoricalDtype)
def unbox_cat_dtype(typ, obj, c):
    cat_dtype = cgutils.create_struct_proxy(typ)(c.context, c.builder)
    cjshb__sxo = c.pyapi.object_getattr_string(obj, 'ordered')
    cat_dtype.ordered = c.pyapi.to_native_value(types.bool_, cjshb__sxo).value
    c.pyapi.decref(cjshb__sxo)
    mhai__bxwr = c.pyapi.object_getattr_string(obj, 'categories')
    cat_dtype.categories = c.pyapi.to_native_value(typ.data, mhai__bxwr).value
    c.pyapi.decref(mhai__bxwr)
    rkvjp__ngwm = cgutils.is_not_null(c.builder, c.pyapi.err_occurred())
    return NativeValue(cat_dtype._getvalue(), is_error=rkvjp__ngwm)


@box(PDCategoricalDtype)
def box_cat_dtype(typ, val, c):
    cat_dtype = cgutils.create_struct_proxy(typ)(c.context, c.builder, val)
    cjshb__sxo = c.pyapi.from_native_value(types.bool_, cat_dtype.ordered,
        c.env_manager)
    c.context.nrt.incref(c.builder, typ.data, cat_dtype.categories)
    qpj__gquna = c.pyapi.from_native_value(typ.data, cat_dtype.categories,
        c.env_manager)
    caf__wsr = c.context.insert_const_string(c.builder.module, 'pandas')
    ymxsh__hucv = c.pyapi.import_module_noblock(caf__wsr)
    amb__wnmh = c.pyapi.call_method(ymxsh__hucv, 'CategoricalDtype', (
        qpj__gquna, cjshb__sxo))
    c.pyapi.decref(cjshb__sxo)
    c.pyapi.decref(qpj__gquna)
    c.pyapi.decref(ymxsh__hucv)
    c.context.nrt.decref(c.builder, typ, val)
    return amb__wnmh


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
        eshh__itj = get_categories_int_type(fe_type.dtype)
        jvsmh__jsjnf = [('dtype', fe_type.dtype), ('codes', types.Array(
            eshh__itj, 1, 'C'))]
        super(CategoricalArrayModel, self).__init__(dmm, fe_type, jvsmh__jsjnf)


make_attribute_wrapper(CategoricalArrayType, 'codes', 'codes')
make_attribute_wrapper(CategoricalArrayType, 'dtype', 'dtype')


@unbox(CategoricalArrayType)
def unbox_categorical_array(typ, val, c):
    tkwnp__dgsio = c.pyapi.object_getattr_string(val, 'codes')
    dtype = get_categories_int_type(typ.dtype)
    codes = c.pyapi.to_native_value(types.Array(dtype, 1, 'C'), tkwnp__dgsio
        ).value
    c.pyapi.decref(tkwnp__dgsio)
    amb__wnmh = c.pyapi.object_getattr_string(val, 'dtype')
    vowv__ykgj = c.pyapi.to_native_value(typ.dtype, amb__wnmh).value
    c.pyapi.decref(amb__wnmh)
    emoko__vilj = cgutils.create_struct_proxy(typ)(c.context, c.builder)
    emoko__vilj.codes = codes
    emoko__vilj.dtype = vowv__ykgj
    return NativeValue(emoko__vilj._getvalue())


@lower_constant(CategoricalArrayType)
def lower_constant_categorical_array(context, builder, typ, pyval):
    hji__kdfn = get_categories_int_type(typ.dtype)
    evo__rkdd = context.get_constant_generic(builder, types.Array(hji__kdfn,
        1, 'C'), pyval.codes)
    cat_dtype = context.get_constant_generic(builder, typ.dtype, pyval.dtype)
    return lir.Constant.literal_struct([cat_dtype, evo__rkdd])


def get_categories_int_type(cat_dtype):
    dtype = types.int64
    if cat_dtype.int_type is not None:
        return cat_dtype.int_type
    if cat_dtype.categories is None:
        return types.int64
    ekprl__bhc = len(cat_dtype.categories)
    if ekprl__bhc < np.iinfo(np.int8).max:
        dtype = types.int8
    elif ekprl__bhc < np.iinfo(np.int16).max:
        dtype = types.int16
    elif ekprl__bhc < np.iinfo(np.int32).max:
        dtype = types.int32
    return dtype


@box(CategoricalArrayType)
def box_categorical_array(typ, val, c):
    dtype = typ.dtype
    caf__wsr = c.context.insert_const_string(c.builder.module, 'pandas')
    ymxsh__hucv = c.pyapi.import_module_noblock(caf__wsr)
    eshh__itj = get_categories_int_type(dtype)
    jvgmr__xuldu = cgutils.create_struct_proxy(typ)(c.context, c.builder, val)
    ryggx__brh = types.Array(eshh__itj, 1, 'C')
    c.context.nrt.incref(c.builder, ryggx__brh, jvgmr__xuldu.codes)
    tkwnp__dgsio = c.pyapi.from_native_value(ryggx__brh, jvgmr__xuldu.codes,
        c.env_manager)
    c.context.nrt.incref(c.builder, dtype, jvgmr__xuldu.dtype)
    amb__wnmh = c.pyapi.from_native_value(dtype, jvgmr__xuldu.dtype, c.
        env_manager)
    jhci__uni = c.pyapi.borrow_none()
    rqx__zue = c.pyapi.object_getattr_string(ymxsh__hucv, 'Categorical')
    fvy__wmo = c.pyapi.call_method(rqx__zue, 'from_codes', (tkwnp__dgsio,
        jhci__uni, jhci__uni, amb__wnmh))
    c.pyapi.decref(rqx__zue)
    c.pyapi.decref(tkwnp__dgsio)
    c.pyapi.decref(amb__wnmh)
    c.pyapi.decref(ymxsh__hucv)
    c.context.nrt.decref(c.builder, typ, val)
    return fvy__wmo


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
            kjqy__evd = list(A.dtype.categories).index(val
                ) if val in A.dtype.categories else -2

            def impl_lit(A, other):
                yejix__isfkn = op(bodo.hiframes.pd_categorical_ext.
                    get_categorical_arr_codes(A), kjqy__evd)
                return yejix__isfkn
            return impl_lit

        def impl(A, other):
            kjqy__evd = get_code_for_value(A.dtype, other)
            yejix__isfkn = op(bodo.hiframes.pd_categorical_ext.
                get_categorical_arr_codes(A), kjqy__evd)
            return yejix__isfkn
        return impl
    return overload_cat_arr_cmp


def _install_cmp_ops():
    for op in [operator.eq, operator.ne]:
        yqldg__gopdb = create_cmp_op_overload(op)
        overload(op, inline='always', no_unliteral=True)(yqldg__gopdb)


_install_cmp_ops()


@register_jitable
def get_code_for_value(cat_dtype, val):
    jvgmr__xuldu = cat_dtype.categories
    n = len(jvgmr__xuldu)
    for qacoq__uoay in range(n):
        if jvgmr__xuldu[qacoq__uoay] == val:
            return qacoq__uoay
    return -2


@overload_method(CategoricalArrayType, 'astype', inline='always',
    no_unliteral=True)
def overload_cat_arr_astype(A, dtype, copy=True, _bodo_nan_to_str=True):
    if dtype == types.unicode_type:
        raise_bodo_error(
            "CategoricalArray.astype(): 'dtype' when passed as string must be a constant value"
            )
    jynkf__cuo = bodo.utils.typing.parse_dtype(dtype, 'CategoricalArray.astype'
        )
    if jynkf__cuo != A.dtype.elem_type and jynkf__cuo != types.unicode_type:
        raise BodoError(
            f'Converting categorical array {A} to dtype {dtype} not supported yet'
            )
    if jynkf__cuo == types.unicode_type:

        def impl(A, dtype, copy=True, _bodo_nan_to_str=True):
            codes = bodo.hiframes.pd_categorical_ext.get_categorical_arr_codes(
                A)
            categories = A.dtype.categories
            n = len(codes)
            yejix__isfkn = bodo.libs.str_arr_ext.pre_alloc_string_array(n, -1)
            for qacoq__uoay in numba.parfors.parfor.internal_prange(n):
                zcnf__peq = codes[qacoq__uoay]
                if zcnf__peq == -1:
                    if _bodo_nan_to_str:
                        bodo.libs.str_arr_ext.str_arr_setitem_NA_str(
                            yejix__isfkn, qacoq__uoay)
                    else:
                        bodo.libs.array_kernels.setna(yejix__isfkn, qacoq__uoay
                            )
                    continue
                yejix__isfkn[qacoq__uoay] = str(bodo.utils.conversion.
                    unbox_if_timestamp(categories[zcnf__peq]))
            return yejix__isfkn
        return impl
    ryggx__brh = dtype_to_array_type(jynkf__cuo)

    def impl(A, dtype, copy=True, _bodo_nan_to_str=True):
        codes = bodo.hiframes.pd_categorical_ext.get_categorical_arr_codes(A)
        categories = A.dtype.categories
        n = len(codes)
        yejix__isfkn = bodo.utils.utils.alloc_type(n, ryggx__brh, (-1,))
        for qacoq__uoay in numba.parfors.parfor.internal_prange(n):
            zcnf__peq = codes[qacoq__uoay]
            if zcnf__peq == -1:
                bodo.libs.array_kernels.setna(yejix__isfkn, qacoq__uoay)
                continue
            yejix__isfkn[qacoq__uoay
                ] = bodo.utils.conversion.unbox_if_timestamp(categories[
                zcnf__peq])
        return yejix__isfkn
    return impl


@overload(pd.api.types.CategoricalDtype, no_unliteral=True)
def cat_overload_dummy(val_list):
    return lambda val_list: 1


@intrinsic
def init_categorical_array(typingctx, codes, cat_dtype=None):
    assert isinstance(codes, types.Array) and isinstance(codes.dtype, types
        .Integer)

    def codegen(context, builder, signature, args):
        jkpzv__kgp, vowv__ykgj = args
        jvgmr__xuldu = cgutils.create_struct_proxy(signature.return_type)(
            context, builder)
        jvgmr__xuldu.codes = jkpzv__kgp
        jvgmr__xuldu.dtype = vowv__ykgj
        context.nrt.incref(builder, signature.args[0], jkpzv__kgp)
        context.nrt.incref(builder, signature.args[1], vowv__ykgj)
        return jvgmr__xuldu._getvalue()
    rxsn__fkois = CategoricalArrayType(cat_dtype)
    sig = rxsn__fkois(codes, cat_dtype)
    return sig, codegen


def init_categorical_array_equiv(self, scope, equiv_set, loc, args, kws):
    assert len(args) == 2 and not kws
    zoorg__pit = args[0]
    if equiv_set.has_shape(zoorg__pit):
        return ArrayAnalysis.AnalyzeResult(shape=zoorg__pit, pre=[])
    return None


(ArrayAnalysis.
    _analyze_op_call_bodo_hiframes_pd_categorical_ext_init_categorical_array
    ) = init_categorical_array_equiv


def alloc_categorical_array(n, cat_dtype):
    pass


@overload(alloc_categorical_array, no_unliteral=True)
def _alloc_categorical_array(n, cat_dtype):
    eshh__itj = get_categories_int_type(cat_dtype)

    def impl(n, cat_dtype):
        codes = np.empty(n, eshh__itj)
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
            doikn__oryg = {}
            evo__rkdd = np.empty(n + 1, np.int64)
            haofx__ynz = {}
            umtu__dnwp = []
            wjb__tpkl = {}
            for qacoq__uoay in range(n):
                wjb__tpkl[categories[qacoq__uoay]] = qacoq__uoay
            for uoyh__oxln in to_replace:
                if uoyh__oxln != value:
                    if uoyh__oxln in wjb__tpkl:
                        if value in wjb__tpkl:
                            doikn__oryg[uoyh__oxln] = uoyh__oxln
                            jsbm__twf = wjb__tpkl[uoyh__oxln]
                            haofx__ynz[jsbm__twf] = wjb__tpkl[value]
                            umtu__dnwp.append(jsbm__twf)
                        else:
                            doikn__oryg[uoyh__oxln] = value
                            wjb__tpkl[value] = wjb__tpkl[uoyh__oxln]
            rcb__wojno = np.sort(np.array(umtu__dnwp))
            shmz__qyk = 0
            sykkq__zbiol = []
            for xxied__akfjv in range(-1, n):
                while shmz__qyk < len(rcb__wojno
                    ) and xxied__akfjv > rcb__wojno[shmz__qyk]:
                    shmz__qyk += 1
                sykkq__zbiol.append(shmz__qyk)
            for zbkqc__amp in range(-1, n):
                alh__wcdc = zbkqc__amp
                if zbkqc__amp in haofx__ynz:
                    alh__wcdc = haofx__ynz[zbkqc__amp]
                evo__rkdd[zbkqc__amp + 1] = alh__wcdc - sykkq__zbiol[
                    alh__wcdc + 1]
            return doikn__oryg, evo__rkdd, len(rcb__wojno)
        return impl


@numba.njit
def python_build_replace_dicts(to_replace, value, categories):
    return build_replace_dicts(to_replace, value, categories)


@register_jitable
def reassign_codes(new_codes_arr, old_codes_arr, codes_map_arr):
    for qacoq__uoay in range(len(new_codes_arr)):
        new_codes_arr[qacoq__uoay] = codes_map_arr[old_codes_arr[
            qacoq__uoay] + 1]


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
    pyxw__thj = arr.dtype.ordered
    mew__jeyv = arr.dtype.elem_type
    txen__xkhre = get_overload_const(to_replace)
    hlkd__aey = get_overload_const(value)
    if (arr.dtype.categories is not None and txen__xkhre is not
        NOT_CONSTANT and hlkd__aey is not NOT_CONSTANT):
        rrmzp__lff, codes_map_arr, ceerk__cpa = python_build_replace_dicts(
            txen__xkhre, hlkd__aey, arr.dtype.categories)
        if len(rrmzp__lff) == 0:
            return lambda arr, to_replace, value: arr.copy()
        kkcu__gzdge = []
        for chpog__lqk in arr.dtype.categories:
            if chpog__lqk in rrmzp__lff:
                ufsou__jgmvt = rrmzp__lff[chpog__lqk]
                if ufsou__jgmvt != chpog__lqk:
                    kkcu__gzdge.append(ufsou__jgmvt)
            else:
                kkcu__gzdge.append(chpog__lqk)
        qno__ovofx = pd.CategoricalDtype(kkcu__gzdge, pyxw__thj
            ).categories.values
        tcm__nogj = MetaType(tuple(qno__ovofx))

        def impl_dtype(arr, to_replace, value):
            crw__rdnlj = init_cat_dtype(bodo.utils.conversion.
                index_from_array(qno__ovofx), pyxw__thj, None, tcm__nogj)
            jvgmr__xuldu = alloc_categorical_array(len(arr.codes), crw__rdnlj)
            reassign_codes(jvgmr__xuldu.codes, arr.codes, codes_map_arr)
            return jvgmr__xuldu
        return impl_dtype
    mew__jeyv = arr.dtype.elem_type
    if mew__jeyv == types.unicode_type:

        def impl_str(arr, to_replace, value):
            categories = arr.dtype.categories
            doikn__oryg, codes_map_arr, ifwi__xfb = build_replace_dicts(
                to_replace, value, categories.values)
            if len(doikn__oryg) == 0:
                return init_categorical_array(arr.codes.copy().astype(np.
                    int64), init_cat_dtype(categories.copy(), pyxw__thj,
                    None, None))
            n = len(categories)
            qno__ovofx = bodo.libs.str_arr_ext.pre_alloc_string_array(n -
                ifwi__xfb, -1)
            tfcvw__klph = 0
            for xxied__akfjv in range(n):
                rqj__ucmtm = categories[xxied__akfjv]
                if rqj__ucmtm in doikn__oryg:
                    ual__kkz = doikn__oryg[rqj__ucmtm]
                    if ual__kkz != rqj__ucmtm:
                        qno__ovofx[tfcvw__klph] = ual__kkz
                        tfcvw__klph += 1
                else:
                    qno__ovofx[tfcvw__klph] = rqj__ucmtm
                    tfcvw__klph += 1
            jvgmr__xuldu = alloc_categorical_array(len(arr.codes),
                init_cat_dtype(bodo.utils.conversion.index_from_array(
                qno__ovofx), pyxw__thj, None, None))
            reassign_codes(jvgmr__xuldu.codes, arr.codes, codes_map_arr)
            return jvgmr__xuldu
        return impl_str
    fkxve__eig = dtype_to_array_type(mew__jeyv)

    def impl(arr, to_replace, value):
        categories = arr.dtype.categories
        doikn__oryg, codes_map_arr, ifwi__xfb = build_replace_dicts(to_replace,
            value, categories.values)
        if len(doikn__oryg) == 0:
            return init_categorical_array(arr.codes.copy().astype(np.int64),
                init_cat_dtype(categories.copy(), pyxw__thj, None, None))
        n = len(categories)
        qno__ovofx = bodo.utils.utils.alloc_type(n - ifwi__xfb, fkxve__eig,
            None)
        tfcvw__klph = 0
        for qacoq__uoay in range(n):
            rqj__ucmtm = categories[qacoq__uoay]
            if rqj__ucmtm in doikn__oryg:
                ual__kkz = doikn__oryg[rqj__ucmtm]
                if ual__kkz != rqj__ucmtm:
                    qno__ovofx[tfcvw__klph] = ual__kkz
                    tfcvw__klph += 1
            else:
                qno__ovofx[tfcvw__klph] = rqj__ucmtm
                tfcvw__klph += 1
        jvgmr__xuldu = alloc_categorical_array(len(arr.codes),
            init_cat_dtype(bodo.utils.conversion.index_from_array(
            qno__ovofx), pyxw__thj, None, None))
        reassign_codes(jvgmr__xuldu.codes, arr.codes, codes_map_arr)
        return jvgmr__xuldu
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
    fazxs__ivpsj = dict()
    xihfh__opg = 0
    for qacoq__uoay in range(len(vals)):
        val = vals[qacoq__uoay]
        if val in fazxs__ivpsj:
            continue
        fazxs__ivpsj[val] = xihfh__opg
        xihfh__opg += 1
    return fazxs__ivpsj


@register_jitable
def get_label_dict_from_categories_no_duplicates(vals):
    fazxs__ivpsj = dict()
    for qacoq__uoay in range(len(vals)):
        val = vals[qacoq__uoay]
        fazxs__ivpsj[val] = qacoq__uoay
    return fazxs__ivpsj


@overload(pd.Categorical, no_unliteral=True)
def pd_categorical_overload(values, categories=None, ordered=None, dtype=
    None, fastpath=False):
    zfl__wpn = dict(fastpath=fastpath)
    ryi__jkk = dict(fastpath=False)
    check_unsupported_args('pd.Categorical', zfl__wpn, ryi__jkk)
    if isinstance(dtype, bodo.hiframes.pd_categorical_ext.PDCategoricalDtype):

        def impl_dtype(values, categories=None, ordered=None, dtype=None,
            fastpath=False):
            data = bodo.utils.conversion.coerce_to_array(values)
            return bodo.utils.conversion.fix_arr_dtype(data, dtype)
        return impl_dtype
    if not is_overload_none(categories):
        pabq__gxte = get_overload_const(categories)
        if pabq__gxte is not NOT_CONSTANT and get_overload_const(ordered
            ) is not NOT_CONSTANT:
            if is_overload_none(ordered):
                pta__ayah = False
            else:
                pta__ayah = get_overload_const_bool(ordered)
            dcwt__zcf = pd.CategoricalDtype(pabq__gxte, pta__ayah
                ).categories.values
            vbl__frv = MetaType(tuple(dcwt__zcf))

            def impl_cats_const(values, categories=None, ordered=None,
                dtype=None, fastpath=False):
                data = bodo.utils.conversion.coerce_to_array(values)
                crw__rdnlj = init_cat_dtype(bodo.utils.conversion.
                    index_from_array(dcwt__zcf), pta__ayah, None, vbl__frv)
                return bodo.utils.conversion.fix_arr_dtype(data, crw__rdnlj)
            return impl_cats_const

        def impl_cats(values, categories=None, ordered=None, dtype=None,
            fastpath=False):
            ordered = bodo.utils.conversion.false_if_none(ordered)
            data = bodo.utils.conversion.coerce_to_array(values)
            wrcnz__mjuf = bodo.utils.conversion.convert_to_index(categories)
            cat_dtype = bodo.hiframes.pd_categorical_ext.init_cat_dtype(
                wrcnz__mjuf, ordered, None, None)
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
            fvum__jqfp = arr.codes[ind]
            return arr.dtype.categories[max(fvum__jqfp, 0)]
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
    for qacoq__uoay in range(len(arr1)):
        if arr1[qacoq__uoay] != arr2[qacoq__uoay]:
            return False
    return True


@overload(operator.setitem, no_unliteral=True)
def categorical_array_setitem(arr, ind, val):
    if not isinstance(arr, CategoricalArrayType):
        return
    if val == types.none or isinstance(val, types.optional):
        return
    czg__qbdkp = is_scalar_type(val) and is_common_scalar_dtype([types.
        unliteral(val), arr.dtype.elem_type]) and not (isinstance(arr.dtype
        .elem_type, types.Integer) and isinstance(val, types.Float))
    ydtta__glzw = not isinstance(val, CategoricalArrayType
        ) and is_iterable_type(val) and is_common_scalar_dtype([val.dtype,
        arr.dtype.elem_type]) and not (isinstance(arr.dtype.elem_type,
        types.Integer) and isinstance(val.dtype, types.Float))
    fjvx__fao = categorical_arrs_match(arr, val)
    zquk__rvm = (
        f"setitem for CategoricalArrayType of dtype {arr.dtype} with indexing type {ind} received an incorrect 'value' type {val}."
        )
    qch__izjq = (
        'Cannot set a Categorical with another, without identical categories')
    if isinstance(ind, types.Integer):
        if not czg__qbdkp:
            raise BodoError(zquk__rvm)

        def impl_scalar(arr, ind, val):
            if val not in arr.dtype.categories:
                raise ValueError(
                    'Cannot setitem on a Categorical with a new category, set the categories first'
                    )
            fvum__jqfp = arr.dtype.categories.get_loc(val)
            arr.codes[ind] = fvum__jqfp
        return impl_scalar
    if is_list_like_index_type(ind) and isinstance(ind.dtype, types.Integer):
        if not (czg__qbdkp or ydtta__glzw or fjvx__fao !=
            CategoricalMatchingValues.DIFFERENT_TYPES):
            raise BodoError(zquk__rvm)
        if fjvx__fao == CategoricalMatchingValues.DONT_MATCH:
            raise BodoError(qch__izjq)
        if czg__qbdkp:

            def impl_scalar(arr, ind, val):
                if val not in arr.dtype.categories:
                    raise ValueError(
                        'Cannot setitem on a Categorical with a new category, set the categories first'
                        )
                ewc__nxr = arr.dtype.categories.get_loc(val)
                n = len(ind)
                for xxied__akfjv in range(n):
                    arr.codes[ind[xxied__akfjv]] = ewc__nxr
            return impl_scalar
        if fjvx__fao == CategoricalMatchingValues.DO_MATCH:

            def impl_arr_ind_mask(arr, ind, val):
                n = len(val.codes)
                for qacoq__uoay in range(n):
                    arr.codes[ind[qacoq__uoay]] = val.codes[qacoq__uoay]
            return impl_arr_ind_mask
        if fjvx__fao == CategoricalMatchingValues.MAY_MATCH:

            def impl_arr_ind_mask(arr, ind, val):
                if not cat_dtype_equal(arr.dtype, val.dtype):
                    raise ValueError(qch__izjq)
                n = len(val.codes)
                for qacoq__uoay in range(n):
                    arr.codes[ind[qacoq__uoay]] = val.codes[qacoq__uoay]
            return impl_arr_ind_mask
        if ydtta__glzw:

            def impl_arr_ind_mask_cat_values(arr, ind, val):
                n = len(val)
                categories = arr.dtype.categories
                for xxied__akfjv in range(n):
                    vtetr__xoyvg = bodo.utils.conversion.unbox_if_timestamp(val
                        [xxied__akfjv])
                    if vtetr__xoyvg not in categories:
                        raise ValueError(
                            'Cannot setitem on a Categorical with a new category, set the categories first'
                            )
                    fvum__jqfp = categories.get_loc(vtetr__xoyvg)
                    arr.codes[ind[xxied__akfjv]] = fvum__jqfp
            return impl_arr_ind_mask_cat_values
    if is_list_like_index_type(ind) and ind.dtype == types.bool_:
        if not (czg__qbdkp or ydtta__glzw or fjvx__fao !=
            CategoricalMatchingValues.DIFFERENT_TYPES):
            raise BodoError(zquk__rvm)
        if fjvx__fao == CategoricalMatchingValues.DONT_MATCH:
            raise BodoError(qch__izjq)
        if czg__qbdkp:

            def impl_scalar(arr, ind, val):
                if val not in arr.dtype.categories:
                    raise ValueError(
                        'Cannot setitem on a Categorical with a new category, set the categories first'
                        )
                ewc__nxr = arr.dtype.categories.get_loc(val)
                n = len(ind)
                for xxied__akfjv in range(n):
                    if ind[xxied__akfjv]:
                        arr.codes[xxied__akfjv] = ewc__nxr
            return impl_scalar
        if fjvx__fao == CategoricalMatchingValues.DO_MATCH:

            def impl_bool_ind_mask(arr, ind, val):
                n = len(ind)
                ctah__wdkic = 0
                for qacoq__uoay in range(n):
                    if ind[qacoq__uoay]:
                        arr.codes[qacoq__uoay] = val.codes[ctah__wdkic]
                        ctah__wdkic += 1
            return impl_bool_ind_mask
        if fjvx__fao == CategoricalMatchingValues.MAY_MATCH:

            def impl_bool_ind_mask(arr, ind, val):
                if not cat_dtype_equal(arr.dtype, val.dtype):
                    raise ValueError(qch__izjq)
                n = len(ind)
                ctah__wdkic = 0
                for qacoq__uoay in range(n):
                    if ind[qacoq__uoay]:
                        arr.codes[qacoq__uoay] = val.codes[ctah__wdkic]
                        ctah__wdkic += 1
            return impl_bool_ind_mask
        if ydtta__glzw:

            def impl_bool_ind_mask_cat_values(arr, ind, val):
                n = len(ind)
                ctah__wdkic = 0
                categories = arr.dtype.categories
                for xxied__akfjv in range(n):
                    if ind[xxied__akfjv]:
                        vtetr__xoyvg = (bodo.utils.conversion.
                            unbox_if_timestamp(val[ctah__wdkic]))
                        if vtetr__xoyvg not in categories:
                            raise ValueError(
                                'Cannot setitem on a Categorical with a new category, set the categories first'
                                )
                        fvum__jqfp = categories.get_loc(vtetr__xoyvg)
                        arr.codes[xxied__akfjv] = fvum__jqfp
                        ctah__wdkic += 1
            return impl_bool_ind_mask_cat_values
    if isinstance(ind, types.SliceType):
        if not (czg__qbdkp or ydtta__glzw or fjvx__fao !=
            CategoricalMatchingValues.DIFFERENT_TYPES):
            raise BodoError(zquk__rvm)
        if fjvx__fao == CategoricalMatchingValues.DONT_MATCH:
            raise BodoError(qch__izjq)
        if czg__qbdkp:

            def impl_scalar(arr, ind, val):
                if val not in arr.dtype.categories:
                    raise ValueError(
                        'Cannot setitem on a Categorical with a new category, set the categories first'
                        )
                ewc__nxr = arr.dtype.categories.get_loc(val)
                whuil__mjq = numba.cpython.unicode._normalize_slice(ind,
                    len(arr))
                for xxied__akfjv in range(whuil__mjq.start, whuil__mjq.stop,
                    whuil__mjq.step):
                    arr.codes[xxied__akfjv] = ewc__nxr
            return impl_scalar
        if fjvx__fao == CategoricalMatchingValues.DO_MATCH:

            def impl_arr(arr, ind, val):
                arr.codes[ind] = val.codes
            return impl_arr
        if fjvx__fao == CategoricalMatchingValues.MAY_MATCH:

            def impl_arr(arr, ind, val):
                if not cat_dtype_equal(arr.dtype, val.dtype):
                    raise ValueError(qch__izjq)
                arr.codes[ind] = val.codes
            return impl_arr
        if ydtta__glzw:

            def impl_slice_cat_values(arr, ind, val):
                categories = arr.dtype.categories
                whuil__mjq = numba.cpython.unicode._normalize_slice(ind,
                    len(arr))
                ctah__wdkic = 0
                for xxied__akfjv in range(whuil__mjq.start, whuil__mjq.stop,
                    whuil__mjq.step):
                    vtetr__xoyvg = bodo.utils.conversion.unbox_if_timestamp(val
                        [ctah__wdkic])
                    if vtetr__xoyvg not in categories:
                        raise ValueError(
                            'Cannot setitem on a Categorical with a new category, set the categories first'
                            )
                    fvum__jqfp = categories.get_loc(vtetr__xoyvg)
                    arr.codes[xxied__akfjv] = fvum__jqfp
                    ctah__wdkic += 1
            return impl_slice_cat_values
    raise BodoError(
        f'setitem for CategoricalArrayType with indexing type {ind} not supported.'
        )
