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
        syt__rysbp = (
            f'PDCategoricalDtype({self.categories}, {self.elem_type}, {self.ordered}, {self.data}, {self.int_type})'
            )
        super(PDCategoricalDtype, self).__init__(name=syt__rysbp)

    @property
    def mangling_args(self):
        return self.__class__.__name__, (self._code,)


@typeof_impl.register(pd.CategoricalDtype)
def _typeof_pd_cat_dtype(val, c):
    rih__xuxbb = tuple(val.categories.values)
    elem_type = None if len(rih__xuxbb) == 0 else bodo.typeof(val.
        categories.values).dtype
    int_type = getattr(val, '_int_type', None)
    return PDCategoricalDtype(rih__xuxbb, elem_type, val.ordered, bodo.
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
        jfyx__lfcv = [('categories', fe_type.data), ('ordered', types.bool_)]
        models.StructModel.__init__(self, dmm, fe_type, jfyx__lfcv)


make_attribute_wrapper(PDCategoricalDtype, 'categories', 'categories')
make_attribute_wrapper(PDCategoricalDtype, 'ordered', 'ordered')


@intrinsic
def init_cat_dtype(typingctx, categories_typ, ordered_typ, int_type,
    cat_vals_typ=None):
    assert bodo.hiframes.pd_index_ext.is_index_type(categories_typ
        ), 'init_cat_dtype requires index type for categories'
    assert is_overload_constant_bool(ordered_typ
        ), 'init_cat_dtype requires constant ordered flag'
    sccw__ivjdd = None if is_overload_none(int_type) else int_type.dtype
    assert is_overload_none(cat_vals_typ) or isinstance(cat_vals_typ, types
        .TypeRef), 'init_cat_dtype requires constant category values'
    ljrp__djed = None if is_overload_none(cat_vals_typ
        ) else cat_vals_typ.instance_type.meta

    def codegen(context, builder, sig, args):
        categories, ordered, aum__rjzq, aum__rjzq = args
        cat_dtype = cgutils.create_struct_proxy(sig.return_type)(context,
            builder)
        cat_dtype.categories = categories
        context.nrt.incref(builder, sig.args[0], categories)
        context.nrt.incref(builder, sig.args[1], ordered)
        cat_dtype.ordered = ordered
        return cat_dtype._getvalue()
    owt__fsqi = PDCategoricalDtype(ljrp__djed, categories_typ.dtype,
        is_overload_true(ordered_typ), categories_typ, sccw__ivjdd)
    return owt__fsqi(categories_typ, ordered_typ, int_type, cat_vals_typ
        ), codegen


@unbox(PDCategoricalDtype)
def unbox_cat_dtype(typ, obj, c):
    cat_dtype = cgutils.create_struct_proxy(typ)(c.context, c.builder)
    tmls__jjkq = c.pyapi.object_getattr_string(obj, 'ordered')
    cat_dtype.ordered = c.pyapi.to_native_value(types.bool_, tmls__jjkq).value
    c.pyapi.decref(tmls__jjkq)
    sir__ubc = c.pyapi.object_getattr_string(obj, 'categories')
    cat_dtype.categories = c.pyapi.to_native_value(typ.data, sir__ubc).value
    c.pyapi.decref(sir__ubc)
    ifvqj__qlbd = cgutils.is_not_null(c.builder, c.pyapi.err_occurred())
    return NativeValue(cat_dtype._getvalue(), is_error=ifvqj__qlbd)


@box(PDCategoricalDtype)
def box_cat_dtype(typ, val, c):
    cat_dtype = cgutils.create_struct_proxy(typ)(c.context, c.builder, val)
    tmls__jjkq = c.pyapi.from_native_value(types.bool_, cat_dtype.ordered,
        c.env_manager)
    c.context.nrt.incref(c.builder, typ.data, cat_dtype.categories)
    rqcf__mqtt = c.pyapi.from_native_value(typ.data, cat_dtype.categories,
        c.env_manager)
    ynx__feea = c.context.insert_const_string(c.builder.module, 'pandas')
    skjhl__igpd = c.pyapi.import_module_noblock(ynx__feea)
    cjyhe__kdtn = c.pyapi.call_method(skjhl__igpd, 'CategoricalDtype', (
        rqcf__mqtt, tmls__jjkq))
    c.pyapi.decref(tmls__jjkq)
    c.pyapi.decref(rqcf__mqtt)
    c.pyapi.decref(skjhl__igpd)
    c.context.nrt.decref(c.builder, typ, val)
    return cjyhe__kdtn


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
        oriu__fjg = get_categories_int_type(fe_type.dtype)
        jfyx__lfcv = [('dtype', fe_type.dtype), ('codes', types.Array(
            oriu__fjg, 1, 'C'))]
        super(CategoricalArrayModel, self).__init__(dmm, fe_type, jfyx__lfcv)


make_attribute_wrapper(CategoricalArrayType, 'codes', 'codes')
make_attribute_wrapper(CategoricalArrayType, 'dtype', 'dtype')


@unbox(CategoricalArrayType)
def unbox_categorical_array(typ, val, c):
    sxp__ogm = c.pyapi.object_getattr_string(val, 'codes')
    dtype = get_categories_int_type(typ.dtype)
    codes = c.pyapi.to_native_value(types.Array(dtype, 1, 'C'), sxp__ogm).value
    c.pyapi.decref(sxp__ogm)
    cjyhe__kdtn = c.pyapi.object_getattr_string(val, 'dtype')
    cadi__hjzp = c.pyapi.to_native_value(typ.dtype, cjyhe__kdtn).value
    c.pyapi.decref(cjyhe__kdtn)
    oqsdm__pjh = cgutils.create_struct_proxy(typ)(c.context, c.builder)
    oqsdm__pjh.codes = codes
    oqsdm__pjh.dtype = cadi__hjzp
    return NativeValue(oqsdm__pjh._getvalue())


@lower_constant(CategoricalArrayType)
def lower_constant_categorical_array(context, builder, typ, pyval):
    vksb__vobw = get_categories_int_type(typ.dtype)
    yxhx__lix = context.get_constant_generic(builder, types.Array(
        vksb__vobw, 1, 'C'), pyval.codes)
    cat_dtype = context.get_constant_generic(builder, typ.dtype, pyval.dtype)
    return lir.Constant.literal_struct([cat_dtype, yxhx__lix])


def get_categories_int_type(cat_dtype):
    dtype = types.int64
    if cat_dtype.int_type is not None:
        return cat_dtype.int_type
    if cat_dtype.categories is None:
        return types.int64
    fvmv__wrdh = len(cat_dtype.categories)
    if fvmv__wrdh < np.iinfo(np.int8).max:
        dtype = types.int8
    elif fvmv__wrdh < np.iinfo(np.int16).max:
        dtype = types.int16
    elif fvmv__wrdh < np.iinfo(np.int32).max:
        dtype = types.int32
    return dtype


@box(CategoricalArrayType)
def box_categorical_array(typ, val, c):
    dtype = typ.dtype
    ynx__feea = c.context.insert_const_string(c.builder.module, 'pandas')
    skjhl__igpd = c.pyapi.import_module_noblock(ynx__feea)
    oriu__fjg = get_categories_int_type(dtype)
    vgzlz__tgxs = cgutils.create_struct_proxy(typ)(c.context, c.builder, val)
    cpzb__rzyux = types.Array(oriu__fjg, 1, 'C')
    c.context.nrt.incref(c.builder, cpzb__rzyux, vgzlz__tgxs.codes)
    sxp__ogm = c.pyapi.from_native_value(cpzb__rzyux, vgzlz__tgxs.codes, c.
        env_manager)
    c.context.nrt.incref(c.builder, dtype, vgzlz__tgxs.dtype)
    cjyhe__kdtn = c.pyapi.from_native_value(dtype, vgzlz__tgxs.dtype, c.
        env_manager)
    vdls__uywtf = c.pyapi.borrow_none()
    ffmge__rvhw = c.pyapi.object_getattr_string(skjhl__igpd, 'Categorical')
    mxmcn__llafv = c.pyapi.call_method(ffmge__rvhw, 'from_codes', (sxp__ogm,
        vdls__uywtf, vdls__uywtf, cjyhe__kdtn))
    c.pyapi.decref(ffmge__rvhw)
    c.pyapi.decref(sxp__ogm)
    c.pyapi.decref(cjyhe__kdtn)
    c.pyapi.decref(skjhl__igpd)
    c.context.nrt.decref(c.builder, typ, val)
    return mxmcn__llafv


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
            dis__vsxo = list(A.dtype.categories).index(val
                ) if val in A.dtype.categories else -2

            def impl_lit(A, other):
                nehp__clpud = op(bodo.hiframes.pd_categorical_ext.
                    get_categorical_arr_codes(A), dis__vsxo)
                return nehp__clpud
            return impl_lit

        def impl(A, other):
            dis__vsxo = get_code_for_value(A.dtype, other)
            nehp__clpud = op(bodo.hiframes.pd_categorical_ext.
                get_categorical_arr_codes(A), dis__vsxo)
            return nehp__clpud
        return impl
    return overload_cat_arr_cmp


def _install_cmp_ops():
    for op in [operator.eq, operator.ne]:
        obkhe__wsy = create_cmp_op_overload(op)
        overload(op, inline='always', no_unliteral=True)(obkhe__wsy)


_install_cmp_ops()


@register_jitable
def get_code_for_value(cat_dtype, val):
    vgzlz__tgxs = cat_dtype.categories
    n = len(vgzlz__tgxs)
    for lvq__jqfhc in range(n):
        if vgzlz__tgxs[lvq__jqfhc] == val:
            return lvq__jqfhc
    return -2


@overload_method(CategoricalArrayType, 'astype', inline='always',
    no_unliteral=True)
def overload_cat_arr_astype(A, dtype, copy=True, _bodo_nan_to_str=True):
    if dtype == types.unicode_type:
        raise_bodo_error(
            "CategoricalArray.astype(): 'dtype' when passed as string must be a constant value"
            )
    kjb__gmxm = bodo.utils.typing.parse_dtype(dtype, 'CategoricalArray.astype')
    if kjb__gmxm != A.dtype.elem_type and kjb__gmxm != types.unicode_type:
        raise BodoError(
            f'Converting categorical array {A} to dtype {dtype} not supported yet'
            )
    if kjb__gmxm == types.unicode_type:

        def impl(A, dtype, copy=True, _bodo_nan_to_str=True):
            codes = bodo.hiframes.pd_categorical_ext.get_categorical_arr_codes(
                A)
            categories = A.dtype.categories
            n = len(codes)
            nehp__clpud = bodo.libs.str_arr_ext.pre_alloc_string_array(n, -1)
            for lvq__jqfhc in numba.parfors.parfor.internal_prange(n):
                ogeyk__jzpvw = codes[lvq__jqfhc]
                if ogeyk__jzpvw == -1:
                    if _bodo_nan_to_str:
                        bodo.libs.str_arr_ext.str_arr_setitem_NA_str(
                            nehp__clpud, lvq__jqfhc)
                    else:
                        bodo.libs.array_kernels.setna(nehp__clpud, lvq__jqfhc)
                    continue
                nehp__clpud[lvq__jqfhc] = str(bodo.utils.conversion.
                    unbox_if_timestamp(categories[ogeyk__jzpvw]))
            return nehp__clpud
        return impl
    cpzb__rzyux = dtype_to_array_type(kjb__gmxm)

    def impl(A, dtype, copy=True, _bodo_nan_to_str=True):
        codes = bodo.hiframes.pd_categorical_ext.get_categorical_arr_codes(A)
        categories = A.dtype.categories
        n = len(codes)
        nehp__clpud = bodo.utils.utils.alloc_type(n, cpzb__rzyux, (-1,))
        for lvq__jqfhc in numba.parfors.parfor.internal_prange(n):
            ogeyk__jzpvw = codes[lvq__jqfhc]
            if ogeyk__jzpvw == -1:
                bodo.libs.array_kernels.setna(nehp__clpud, lvq__jqfhc)
                continue
            nehp__clpud[lvq__jqfhc] = bodo.utils.conversion.unbox_if_timestamp(
                categories[ogeyk__jzpvw])
        return nehp__clpud
    return impl


@overload(pd.api.types.CategoricalDtype, no_unliteral=True)
def cat_overload_dummy(val_list):
    return lambda val_list: 1


@intrinsic
def init_categorical_array(typingctx, codes, cat_dtype=None):
    assert isinstance(codes, types.Array) and isinstance(codes.dtype, types
        .Integer)

    def codegen(context, builder, signature, args):
        dgyb__tmm, cadi__hjzp = args
        vgzlz__tgxs = cgutils.create_struct_proxy(signature.return_type)(
            context, builder)
        vgzlz__tgxs.codes = dgyb__tmm
        vgzlz__tgxs.dtype = cadi__hjzp
        context.nrt.incref(builder, signature.args[0], dgyb__tmm)
        context.nrt.incref(builder, signature.args[1], cadi__hjzp)
        return vgzlz__tgxs._getvalue()
    zcmvr__hvg = CategoricalArrayType(cat_dtype)
    sig = zcmvr__hvg(codes, cat_dtype)
    return sig, codegen


def init_categorical_array_equiv(self, scope, equiv_set, loc, args, kws):
    assert len(args) == 2 and not kws
    izg__xspe = args[0]
    if equiv_set.has_shape(izg__xspe):
        return ArrayAnalysis.AnalyzeResult(shape=izg__xspe, pre=[])
    return None


(ArrayAnalysis.
    _analyze_op_call_bodo_hiframes_pd_categorical_ext_init_categorical_array
    ) = init_categorical_array_equiv


def alloc_categorical_array(n, cat_dtype):
    pass


@overload(alloc_categorical_array, no_unliteral=True)
def _alloc_categorical_array(n, cat_dtype):
    oriu__fjg = get_categories_int_type(cat_dtype)

    def impl(n, cat_dtype):
        codes = np.empty(n, oriu__fjg)
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
            etu__nxcln = {}
            yxhx__lix = np.empty(n + 1, np.int64)
            avtvq__zsshm = {}
            jxy__fva = []
            maox__ideom = {}
            for lvq__jqfhc in range(n):
                maox__ideom[categories[lvq__jqfhc]] = lvq__jqfhc
            for oumlz__awy in to_replace:
                if oumlz__awy != value:
                    if oumlz__awy in maox__ideom:
                        if value in maox__ideom:
                            etu__nxcln[oumlz__awy] = oumlz__awy
                            uzur__vqo = maox__ideom[oumlz__awy]
                            avtvq__zsshm[uzur__vqo] = maox__ideom[value]
                            jxy__fva.append(uzur__vqo)
                        else:
                            etu__nxcln[oumlz__awy] = value
                            maox__ideom[value] = maox__ideom[oumlz__awy]
            anwn__bdw = np.sort(np.array(jxy__fva))
            pgv__dxu = 0
            yng__mhwz = []
            for nqhy__ptb in range(-1, n):
                while pgv__dxu < len(anwn__bdw) and nqhy__ptb > anwn__bdw[
                    pgv__dxu]:
                    pgv__dxu += 1
                yng__mhwz.append(pgv__dxu)
            for jknnb__tgcgp in range(-1, n):
                qwt__ychfg = jknnb__tgcgp
                if jknnb__tgcgp in avtvq__zsshm:
                    qwt__ychfg = avtvq__zsshm[jknnb__tgcgp]
                yxhx__lix[jknnb__tgcgp + 1] = qwt__ychfg - yng__mhwz[
                    qwt__ychfg + 1]
            return etu__nxcln, yxhx__lix, len(anwn__bdw)
        return impl


@numba.njit
def python_build_replace_dicts(to_replace, value, categories):
    return build_replace_dicts(to_replace, value, categories)


@register_jitable
def reassign_codes(new_codes_arr, old_codes_arr, codes_map_arr):
    for lvq__jqfhc in range(len(new_codes_arr)):
        new_codes_arr[lvq__jqfhc] = codes_map_arr[old_codes_arr[lvq__jqfhc] + 1
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
    bodo.hiframes.pd_timestamp_ext.check_tz_aware_unsupported(to_replace,
        'CategoricalArray.replace()')
    bodo.hiframes.pd_timestamp_ext.check_tz_aware_unsupported(value,
        'CategoricalArray.replace()')
    dczon__hyp = arr.dtype.ordered
    dvv__zjupk = arr.dtype.elem_type
    oxyf__eiz = get_overload_const(to_replace)
    atfau__tnh = get_overload_const(value)
    if (arr.dtype.categories is not None and oxyf__eiz is not NOT_CONSTANT and
        atfau__tnh is not NOT_CONSTANT):
        anw__psrg, codes_map_arr, aum__rjzq = python_build_replace_dicts(
            oxyf__eiz, atfau__tnh, arr.dtype.categories)
        if len(anw__psrg) == 0:
            return lambda arr, to_replace, value: arr.copy()
        fwuov__tzyht = []
        for bznmo__des in arr.dtype.categories:
            if bznmo__des in anw__psrg:
                fdheh__bnq = anw__psrg[bznmo__des]
                if fdheh__bnq != bznmo__des:
                    fwuov__tzyht.append(fdheh__bnq)
            else:
                fwuov__tzyht.append(bznmo__des)
        gknk__ptzd = pd.CategoricalDtype(fwuov__tzyht, dczon__hyp
            ).categories.values
        znawa__bzw = MetaType(tuple(gknk__ptzd))

        def impl_dtype(arr, to_replace, value):
            dcnr__oqck = init_cat_dtype(bodo.utils.conversion.
                index_from_array(gknk__ptzd), dczon__hyp, None, znawa__bzw)
            vgzlz__tgxs = alloc_categorical_array(len(arr.codes), dcnr__oqck)
            reassign_codes(vgzlz__tgxs.codes, arr.codes, codes_map_arr)
            return vgzlz__tgxs
        return impl_dtype
    dvv__zjupk = arr.dtype.elem_type
    if dvv__zjupk == types.unicode_type:

        def impl_str(arr, to_replace, value):
            categories = arr.dtype.categories
            etu__nxcln, codes_map_arr, lyr__khnl = build_replace_dicts(
                to_replace, value, categories.values)
            if len(etu__nxcln) == 0:
                return init_categorical_array(arr.codes.copy().astype(np.
                    int64), init_cat_dtype(categories.copy(), dczon__hyp,
                    None, None))
            n = len(categories)
            gknk__ptzd = bodo.libs.str_arr_ext.pre_alloc_string_array(n -
                lyr__khnl, -1)
            emdr__omfad = 0
            for nqhy__ptb in range(n):
                lagw__dxt = categories[nqhy__ptb]
                if lagw__dxt in etu__nxcln:
                    anlv__mns = etu__nxcln[lagw__dxt]
                    if anlv__mns != lagw__dxt:
                        gknk__ptzd[emdr__omfad] = anlv__mns
                        emdr__omfad += 1
                else:
                    gknk__ptzd[emdr__omfad] = lagw__dxt
                    emdr__omfad += 1
            vgzlz__tgxs = alloc_categorical_array(len(arr.codes),
                init_cat_dtype(bodo.utils.conversion.index_from_array(
                gknk__ptzd), dczon__hyp, None, None))
            reassign_codes(vgzlz__tgxs.codes, arr.codes, codes_map_arr)
            return vgzlz__tgxs
        return impl_str
    qzm__fjsl = dtype_to_array_type(dvv__zjupk)

    def impl(arr, to_replace, value):
        categories = arr.dtype.categories
        etu__nxcln, codes_map_arr, lyr__khnl = build_replace_dicts(to_replace,
            value, categories.values)
        if len(etu__nxcln) == 0:
            return init_categorical_array(arr.codes.copy().astype(np.int64),
                init_cat_dtype(categories.copy(), dczon__hyp, None, None))
        n = len(categories)
        gknk__ptzd = bodo.utils.utils.alloc_type(n - lyr__khnl, qzm__fjsl, None
            )
        emdr__omfad = 0
        for lvq__jqfhc in range(n):
            lagw__dxt = categories[lvq__jqfhc]
            if lagw__dxt in etu__nxcln:
                anlv__mns = etu__nxcln[lagw__dxt]
                if anlv__mns != lagw__dxt:
                    gknk__ptzd[emdr__omfad] = anlv__mns
                    emdr__omfad += 1
            else:
                gknk__ptzd[emdr__omfad] = lagw__dxt
                emdr__omfad += 1
        vgzlz__tgxs = alloc_categorical_array(len(arr.codes),
            init_cat_dtype(bodo.utils.conversion.index_from_array(
            gknk__ptzd), dczon__hyp, None, None))
        reassign_codes(vgzlz__tgxs.codes, arr.codes, codes_map_arr)
        return vgzlz__tgxs
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
    hzde__brics = dict()
    xfsn__kdrob = 0
    for lvq__jqfhc in range(len(vals)):
        val = vals[lvq__jqfhc]
        if val in hzde__brics:
            continue
        hzde__brics[val] = xfsn__kdrob
        xfsn__kdrob += 1
    return hzde__brics


@register_jitable
def get_label_dict_from_categories_no_duplicates(vals):
    hzde__brics = dict()
    for lvq__jqfhc in range(len(vals)):
        val = vals[lvq__jqfhc]
        hzde__brics[val] = lvq__jqfhc
    return hzde__brics


@overload(pd.Categorical, no_unliteral=True)
def pd_categorical_overload(values, categories=None, ordered=None, dtype=
    None, fastpath=False):
    hvyr__ylwmm = dict(fastpath=fastpath)
    yoms__mxg = dict(fastpath=False)
    check_unsupported_args('pd.Categorical', hvyr__ylwmm, yoms__mxg)
    if isinstance(dtype, bodo.hiframes.pd_categorical_ext.PDCategoricalDtype):

        def impl_dtype(values, categories=None, ordered=None, dtype=None,
            fastpath=False):
            data = bodo.utils.conversion.coerce_to_array(values)
            return bodo.utils.conversion.fix_arr_dtype(data, dtype)
        return impl_dtype
    if not is_overload_none(categories):
        pyd__xjx = get_overload_const(categories)
        if pyd__xjx is not NOT_CONSTANT and get_overload_const(ordered
            ) is not NOT_CONSTANT:
            if is_overload_none(ordered):
                iakp__xmj = False
            else:
                iakp__xmj = get_overload_const_bool(ordered)
            nbe__qwcbb = pd.CategoricalDtype(pyd__xjx, iakp__xmj
                ).categories.values
            jzvah__voz = MetaType(tuple(nbe__qwcbb))

            def impl_cats_const(values, categories=None, ordered=None,
                dtype=None, fastpath=False):
                data = bodo.utils.conversion.coerce_to_array(values)
                dcnr__oqck = init_cat_dtype(bodo.utils.conversion.
                    index_from_array(nbe__qwcbb), iakp__xmj, None, jzvah__voz)
                return bodo.utils.conversion.fix_arr_dtype(data, dcnr__oqck)
            return impl_cats_const

        def impl_cats(values, categories=None, ordered=None, dtype=None,
            fastpath=False):
            ordered = bodo.utils.conversion.false_if_none(ordered)
            data = bodo.utils.conversion.coerce_to_array(values)
            rih__xuxbb = bodo.utils.conversion.convert_to_index(categories)
            cat_dtype = bodo.hiframes.pd_categorical_ext.init_cat_dtype(
                rih__xuxbb, ordered, None, None)
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
            ujay__vzfk = arr.codes[ind]
            return arr.dtype.categories[max(ujay__vzfk, 0)]
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
    for lvq__jqfhc in range(len(arr1)):
        if arr1[lvq__jqfhc] != arr2[lvq__jqfhc]:
            return False
    return True


@overload(operator.setitem, no_unliteral=True)
def categorical_array_setitem(arr, ind, val):
    if not isinstance(arr, CategoricalArrayType):
        return
    if val == types.none or isinstance(val, types.optional):
        return
    ods__hvfv = is_scalar_type(val) and is_common_scalar_dtype([types.
        unliteral(val), arr.dtype.elem_type]) and not (isinstance(arr.dtype
        .elem_type, types.Integer) and isinstance(val, types.Float))
    joqca__djcu = not isinstance(val, CategoricalArrayType
        ) and is_iterable_type(val) and is_common_scalar_dtype([val.dtype,
        arr.dtype.elem_type]) and not (isinstance(arr.dtype.elem_type,
        types.Integer) and isinstance(val.dtype, types.Float))
    eae__yehg = categorical_arrs_match(arr, val)
    mtt__oby = (
        f"setitem for CategoricalArrayType of dtype {arr.dtype} with indexing type {ind} received an incorrect 'value' type {val}."
        )
    fwxvm__qkd = (
        'Cannot set a Categorical with another, without identical categories')
    if isinstance(ind, types.Integer):
        if not ods__hvfv:
            raise BodoError(mtt__oby)

        def impl_scalar(arr, ind, val):
            if val not in arr.dtype.categories:
                raise ValueError(
                    'Cannot setitem on a Categorical with a new category, set the categories first'
                    )
            ujay__vzfk = arr.dtype.categories.get_loc(val)
            arr.codes[ind] = ujay__vzfk
        return impl_scalar
    if is_list_like_index_type(ind) and isinstance(ind.dtype, types.Integer):
        if not (ods__hvfv or joqca__djcu or eae__yehg !=
            CategoricalMatchingValues.DIFFERENT_TYPES):
            raise BodoError(mtt__oby)
        if eae__yehg == CategoricalMatchingValues.DONT_MATCH:
            raise BodoError(fwxvm__qkd)
        if ods__hvfv:

            def impl_scalar(arr, ind, val):
                if val not in arr.dtype.categories:
                    raise ValueError(
                        'Cannot setitem on a Categorical with a new category, set the categories first'
                        )
                bzyuj__hcomt = arr.dtype.categories.get_loc(val)
                n = len(ind)
                for nqhy__ptb in range(n):
                    arr.codes[ind[nqhy__ptb]] = bzyuj__hcomt
            return impl_scalar
        if eae__yehg == CategoricalMatchingValues.DO_MATCH:

            def impl_arr_ind_mask(arr, ind, val):
                n = len(val.codes)
                for lvq__jqfhc in range(n):
                    arr.codes[ind[lvq__jqfhc]] = val.codes[lvq__jqfhc]
            return impl_arr_ind_mask
        if eae__yehg == CategoricalMatchingValues.MAY_MATCH:

            def impl_arr_ind_mask(arr, ind, val):
                if not cat_dtype_equal(arr.dtype, val.dtype):
                    raise ValueError(fwxvm__qkd)
                n = len(val.codes)
                for lvq__jqfhc in range(n):
                    arr.codes[ind[lvq__jqfhc]] = val.codes[lvq__jqfhc]
            return impl_arr_ind_mask
        if joqca__djcu:

            def impl_arr_ind_mask_cat_values(arr, ind, val):
                n = len(val)
                categories = arr.dtype.categories
                for nqhy__ptb in range(n):
                    uqdt__mbr = bodo.utils.conversion.unbox_if_timestamp(val
                        [nqhy__ptb])
                    if uqdt__mbr not in categories:
                        raise ValueError(
                            'Cannot setitem on a Categorical with a new category, set the categories first'
                            )
                    ujay__vzfk = categories.get_loc(uqdt__mbr)
                    arr.codes[ind[nqhy__ptb]] = ujay__vzfk
            return impl_arr_ind_mask_cat_values
    if is_list_like_index_type(ind) and ind.dtype == types.bool_:
        if not (ods__hvfv or joqca__djcu or eae__yehg !=
            CategoricalMatchingValues.DIFFERENT_TYPES):
            raise BodoError(mtt__oby)
        if eae__yehg == CategoricalMatchingValues.DONT_MATCH:
            raise BodoError(fwxvm__qkd)
        if ods__hvfv:

            def impl_scalar(arr, ind, val):
                if val not in arr.dtype.categories:
                    raise ValueError(
                        'Cannot setitem on a Categorical with a new category, set the categories first'
                        )
                bzyuj__hcomt = arr.dtype.categories.get_loc(val)
                n = len(ind)
                for nqhy__ptb in range(n):
                    if ind[nqhy__ptb]:
                        arr.codes[nqhy__ptb] = bzyuj__hcomt
            return impl_scalar
        if eae__yehg == CategoricalMatchingValues.DO_MATCH:

            def impl_bool_ind_mask(arr, ind, val):
                n = len(ind)
                xcxk__qrn = 0
                for lvq__jqfhc in range(n):
                    if ind[lvq__jqfhc]:
                        arr.codes[lvq__jqfhc] = val.codes[xcxk__qrn]
                        xcxk__qrn += 1
            return impl_bool_ind_mask
        if eae__yehg == CategoricalMatchingValues.MAY_MATCH:

            def impl_bool_ind_mask(arr, ind, val):
                if not cat_dtype_equal(arr.dtype, val.dtype):
                    raise ValueError(fwxvm__qkd)
                n = len(ind)
                xcxk__qrn = 0
                for lvq__jqfhc in range(n):
                    if ind[lvq__jqfhc]:
                        arr.codes[lvq__jqfhc] = val.codes[xcxk__qrn]
                        xcxk__qrn += 1
            return impl_bool_ind_mask
        if joqca__djcu:

            def impl_bool_ind_mask_cat_values(arr, ind, val):
                n = len(ind)
                xcxk__qrn = 0
                categories = arr.dtype.categories
                for nqhy__ptb in range(n):
                    if ind[nqhy__ptb]:
                        uqdt__mbr = bodo.utils.conversion.unbox_if_timestamp(
                            val[xcxk__qrn])
                        if uqdt__mbr not in categories:
                            raise ValueError(
                                'Cannot setitem on a Categorical with a new category, set the categories first'
                                )
                        ujay__vzfk = categories.get_loc(uqdt__mbr)
                        arr.codes[nqhy__ptb] = ujay__vzfk
                        xcxk__qrn += 1
            return impl_bool_ind_mask_cat_values
    if isinstance(ind, types.SliceType):
        if not (ods__hvfv or joqca__djcu or eae__yehg !=
            CategoricalMatchingValues.DIFFERENT_TYPES):
            raise BodoError(mtt__oby)
        if eae__yehg == CategoricalMatchingValues.DONT_MATCH:
            raise BodoError(fwxvm__qkd)
        if ods__hvfv:

            def impl_scalar(arr, ind, val):
                if val not in arr.dtype.categories:
                    raise ValueError(
                        'Cannot setitem on a Categorical with a new category, set the categories first'
                        )
                bzyuj__hcomt = arr.dtype.categories.get_loc(val)
                yhxko__rox = numba.cpython.unicode._normalize_slice(ind,
                    len(arr))
                for nqhy__ptb in range(yhxko__rox.start, yhxko__rox.stop,
                    yhxko__rox.step):
                    arr.codes[nqhy__ptb] = bzyuj__hcomt
            return impl_scalar
        if eae__yehg == CategoricalMatchingValues.DO_MATCH:

            def impl_arr(arr, ind, val):
                arr.codes[ind] = val.codes
            return impl_arr
        if eae__yehg == CategoricalMatchingValues.MAY_MATCH:

            def impl_arr(arr, ind, val):
                if not cat_dtype_equal(arr.dtype, val.dtype):
                    raise ValueError(fwxvm__qkd)
                arr.codes[ind] = val.codes
            return impl_arr
        if joqca__djcu:

            def impl_slice_cat_values(arr, ind, val):
                categories = arr.dtype.categories
                yhxko__rox = numba.cpython.unicode._normalize_slice(ind,
                    len(arr))
                xcxk__qrn = 0
                for nqhy__ptb in range(yhxko__rox.start, yhxko__rox.stop,
                    yhxko__rox.step):
                    uqdt__mbr = bodo.utils.conversion.unbox_if_timestamp(val
                        [xcxk__qrn])
                    if uqdt__mbr not in categories:
                        raise ValueError(
                            'Cannot setitem on a Categorical with a new category, set the categories first'
                            )
                    ujay__vzfk = categories.get_loc(uqdt__mbr)
                    arr.codes[nqhy__ptb] = ujay__vzfk
                    xcxk__qrn += 1
            return impl_slice_cat_values
    raise BodoError(
        f'setitem for CategoricalArrayType with indexing type {ind} not supported.'
        )
