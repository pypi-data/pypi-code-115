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
        fhsmr__vvpp = (
            f'PDCategoricalDtype({self.categories}, {self.elem_type}, {self.ordered}, {self.data}, {self.int_type})'
            )
        super(PDCategoricalDtype, self).__init__(name=fhsmr__vvpp)

    @property
    def mangling_args(self):
        return self.__class__.__name__, (self._code,)


@typeof_impl.register(pd.CategoricalDtype)
def _typeof_pd_cat_dtype(val, c):
    pjln__wvpxt = tuple(val.categories.values)
    elem_type = None if len(pjln__wvpxt) == 0 else bodo.typeof(val.
        categories.values).dtype
    int_type = getattr(val, '_int_type', None)
    return PDCategoricalDtype(pjln__wvpxt, elem_type, val.ordered, bodo.
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
        uzwb__aja = [('categories', fe_type.data), ('ordered', types.bool_)]
        models.StructModel.__init__(self, dmm, fe_type, uzwb__aja)


make_attribute_wrapper(PDCategoricalDtype, 'categories', 'categories')
make_attribute_wrapper(PDCategoricalDtype, 'ordered', 'ordered')


@intrinsic
def init_cat_dtype(typingctx, categories_typ, ordered_typ, int_type,
    cat_vals_typ=None):
    assert bodo.hiframes.pd_index_ext.is_index_type(categories_typ
        ), 'init_cat_dtype requires index type for categories'
    assert is_overload_constant_bool(ordered_typ
        ), 'init_cat_dtype requires constant ordered flag'
    dft__mbt = None if is_overload_none(int_type) else int_type.dtype
    assert is_overload_none(cat_vals_typ) or isinstance(cat_vals_typ, types
        .TypeRef), 'init_cat_dtype requires constant category values'
    zubn__ifo = None if is_overload_none(cat_vals_typ
        ) else cat_vals_typ.instance_type.meta

    def codegen(context, builder, sig, args):
        categories, ordered, cvk__fvolp, cvk__fvolp = args
        cat_dtype = cgutils.create_struct_proxy(sig.return_type)(context,
            builder)
        cat_dtype.categories = categories
        context.nrt.incref(builder, sig.args[0], categories)
        context.nrt.incref(builder, sig.args[1], ordered)
        cat_dtype.ordered = ordered
        return cat_dtype._getvalue()
    gjfak__mlcm = PDCategoricalDtype(zubn__ifo, categories_typ.dtype,
        is_overload_true(ordered_typ), categories_typ, dft__mbt)
    return gjfak__mlcm(categories_typ, ordered_typ, int_type, cat_vals_typ
        ), codegen


@unbox(PDCategoricalDtype)
def unbox_cat_dtype(typ, obj, c):
    cat_dtype = cgutils.create_struct_proxy(typ)(c.context, c.builder)
    peti__ykp = c.pyapi.object_getattr_string(obj, 'ordered')
    cat_dtype.ordered = c.pyapi.to_native_value(types.bool_, peti__ykp).value
    c.pyapi.decref(peti__ykp)
    kgq__bsj = c.pyapi.object_getattr_string(obj, 'categories')
    cat_dtype.categories = c.pyapi.to_native_value(typ.data, kgq__bsj).value
    c.pyapi.decref(kgq__bsj)
    aauio__aint = cgutils.is_not_null(c.builder, c.pyapi.err_occurred())
    return NativeValue(cat_dtype._getvalue(), is_error=aauio__aint)


@box(PDCategoricalDtype)
def box_cat_dtype(typ, val, c):
    cat_dtype = cgutils.create_struct_proxy(typ)(c.context, c.builder, val)
    peti__ykp = c.pyapi.from_native_value(types.bool_, cat_dtype.ordered, c
        .env_manager)
    c.context.nrt.incref(c.builder, typ.data, cat_dtype.categories)
    ihcgc__uumzk = c.pyapi.from_native_value(typ.data, cat_dtype.categories,
        c.env_manager)
    ywr__rzbi = c.context.insert_const_string(c.builder.module, 'pandas')
    qdyv__xac = c.pyapi.import_module_noblock(ywr__rzbi)
    xjv__igt = c.pyapi.call_method(qdyv__xac, 'CategoricalDtype', (
        ihcgc__uumzk, peti__ykp))
    c.pyapi.decref(peti__ykp)
    c.pyapi.decref(ihcgc__uumzk)
    c.pyapi.decref(qdyv__xac)
    c.context.nrt.decref(c.builder, typ, val)
    return xjv__igt


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
        csxf__pefhq = get_categories_int_type(fe_type.dtype)
        uzwb__aja = [('dtype', fe_type.dtype), ('codes', types.Array(
            csxf__pefhq, 1, 'C'))]
        super(CategoricalArrayModel, self).__init__(dmm, fe_type, uzwb__aja)


make_attribute_wrapper(CategoricalArrayType, 'codes', 'codes')
make_attribute_wrapper(CategoricalArrayType, 'dtype', 'dtype')


@unbox(CategoricalArrayType)
def unbox_categorical_array(typ, val, c):
    lehh__tllf = c.pyapi.object_getattr_string(val, 'codes')
    dtype = get_categories_int_type(typ.dtype)
    codes = c.pyapi.to_native_value(types.Array(dtype, 1, 'C'), lehh__tllf
        ).value
    c.pyapi.decref(lehh__tllf)
    xjv__igt = c.pyapi.object_getattr_string(val, 'dtype')
    fhne__xzjq = c.pyapi.to_native_value(typ.dtype, xjv__igt).value
    c.pyapi.decref(xjv__igt)
    mzu__zwaz = cgutils.create_struct_proxy(typ)(c.context, c.builder)
    mzu__zwaz.codes = codes
    mzu__zwaz.dtype = fhne__xzjq
    return NativeValue(mzu__zwaz._getvalue())


@lower_constant(CategoricalArrayType)
def lower_constant_categorical_array(context, builder, typ, pyval):
    gdue__anq = get_categories_int_type(typ.dtype)
    wbemq__qlkex = context.get_constant_generic(builder, types.Array(
        gdue__anq, 1, 'C'), pyval.codes)
    cat_dtype = context.get_constant_generic(builder, typ.dtype, pyval.dtype)
    return lir.Constant.literal_struct([cat_dtype, wbemq__qlkex])


def get_categories_int_type(cat_dtype):
    dtype = types.int64
    if cat_dtype.int_type is not None:
        return cat_dtype.int_type
    if cat_dtype.categories is None:
        return types.int64
    zji__cayg = len(cat_dtype.categories)
    if zji__cayg < np.iinfo(np.int8).max:
        dtype = types.int8
    elif zji__cayg < np.iinfo(np.int16).max:
        dtype = types.int16
    elif zji__cayg < np.iinfo(np.int32).max:
        dtype = types.int32
    return dtype


@box(CategoricalArrayType)
def box_categorical_array(typ, val, c):
    dtype = typ.dtype
    ywr__rzbi = c.context.insert_const_string(c.builder.module, 'pandas')
    qdyv__xac = c.pyapi.import_module_noblock(ywr__rzbi)
    csxf__pefhq = get_categories_int_type(dtype)
    zumh__ygeea = cgutils.create_struct_proxy(typ)(c.context, c.builder, val)
    qhsw__nan = types.Array(csxf__pefhq, 1, 'C')
    c.context.nrt.incref(c.builder, qhsw__nan, zumh__ygeea.codes)
    lehh__tllf = c.pyapi.from_native_value(qhsw__nan, zumh__ygeea.codes, c.
        env_manager)
    c.context.nrt.incref(c.builder, dtype, zumh__ygeea.dtype)
    xjv__igt = c.pyapi.from_native_value(dtype, zumh__ygeea.dtype, c.
        env_manager)
    sita__mugdt = c.pyapi.borrow_none()
    rfdwd__csjp = c.pyapi.object_getattr_string(qdyv__xac, 'Categorical')
    lsrji__frdt = c.pyapi.call_method(rfdwd__csjp, 'from_codes', (
        lehh__tllf, sita__mugdt, sita__mugdt, xjv__igt))
    c.pyapi.decref(rfdwd__csjp)
    c.pyapi.decref(lehh__tllf)
    c.pyapi.decref(xjv__igt)
    c.pyapi.decref(qdyv__xac)
    c.context.nrt.decref(c.builder, typ, val)
    return lsrji__frdt


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
            jwvg__rkt = list(A.dtype.categories).index(val
                ) if val in A.dtype.categories else -2

            def impl_lit(A, other):
                suyvu__huj = op(bodo.hiframes.pd_categorical_ext.
                    get_categorical_arr_codes(A), jwvg__rkt)
                return suyvu__huj
            return impl_lit

        def impl(A, other):
            jwvg__rkt = get_code_for_value(A.dtype, other)
            suyvu__huj = op(bodo.hiframes.pd_categorical_ext.
                get_categorical_arr_codes(A), jwvg__rkt)
            return suyvu__huj
        return impl
    return overload_cat_arr_cmp


def _install_cmp_ops():
    for op in [operator.eq, operator.ne]:
        hxk__zprze = create_cmp_op_overload(op)
        overload(op, inline='always', no_unliteral=True)(hxk__zprze)


_install_cmp_ops()


@register_jitable
def get_code_for_value(cat_dtype, val):
    zumh__ygeea = cat_dtype.categories
    n = len(zumh__ygeea)
    for syuf__jbj in range(n):
        if zumh__ygeea[syuf__jbj] == val:
            return syuf__jbj
    return -2


@overload_method(CategoricalArrayType, 'astype', inline='always',
    no_unliteral=True)
def overload_cat_arr_astype(A, dtype, copy=True, _bodo_nan_to_str=True):
    if dtype == types.unicode_type:
        raise_bodo_error(
            "CategoricalArray.astype(): 'dtype' when passed as string must be a constant value"
            )
    vki__crtx = bodo.utils.typing.parse_dtype(dtype, 'CategoricalArray.astype')
    if vki__crtx != A.dtype.elem_type and vki__crtx != types.unicode_type:
        raise BodoError(
            f'Converting categorical array {A} to dtype {dtype} not supported yet'
            )
    if vki__crtx == types.unicode_type:

        def impl(A, dtype, copy=True, _bodo_nan_to_str=True):
            codes = bodo.hiframes.pd_categorical_ext.get_categorical_arr_codes(
                A)
            categories = A.dtype.categories
            n = len(codes)
            suyvu__huj = bodo.libs.str_arr_ext.pre_alloc_string_array(n, -1)
            for syuf__jbj in numba.parfors.parfor.internal_prange(n):
                hlpb__ybhb = codes[syuf__jbj]
                if hlpb__ybhb == -1:
                    if _bodo_nan_to_str:
                        bodo.libs.str_arr_ext.str_arr_setitem_NA_str(suyvu__huj
                            , syuf__jbj)
                    else:
                        bodo.libs.array_kernels.setna(suyvu__huj, syuf__jbj)
                    continue
                suyvu__huj[syuf__jbj] = str(bodo.utils.conversion.
                    unbox_if_timestamp(categories[hlpb__ybhb]))
            return suyvu__huj
        return impl
    qhsw__nan = dtype_to_array_type(vki__crtx)

    def impl(A, dtype, copy=True, _bodo_nan_to_str=True):
        codes = bodo.hiframes.pd_categorical_ext.get_categorical_arr_codes(A)
        categories = A.dtype.categories
        n = len(codes)
        suyvu__huj = bodo.utils.utils.alloc_type(n, qhsw__nan, (-1,))
        for syuf__jbj in numba.parfors.parfor.internal_prange(n):
            hlpb__ybhb = codes[syuf__jbj]
            if hlpb__ybhb == -1:
                bodo.libs.array_kernels.setna(suyvu__huj, syuf__jbj)
                continue
            suyvu__huj[syuf__jbj] = bodo.utils.conversion.unbox_if_timestamp(
                categories[hlpb__ybhb])
        return suyvu__huj
    return impl


@overload(pd.api.types.CategoricalDtype, no_unliteral=True)
def cat_overload_dummy(val_list):
    return lambda val_list: 1


@intrinsic
def init_categorical_array(typingctx, codes, cat_dtype=None):
    assert isinstance(codes, types.Array) and isinstance(codes.dtype, types
        .Integer)

    def codegen(context, builder, signature, args):
        trt__dhvn, fhne__xzjq = args
        zumh__ygeea = cgutils.create_struct_proxy(signature.return_type)(
            context, builder)
        zumh__ygeea.codes = trt__dhvn
        zumh__ygeea.dtype = fhne__xzjq
        context.nrt.incref(builder, signature.args[0], trt__dhvn)
        context.nrt.incref(builder, signature.args[1], fhne__xzjq)
        return zumh__ygeea._getvalue()
    wouih__itx = CategoricalArrayType(cat_dtype)
    sig = wouih__itx(codes, cat_dtype)
    return sig, codegen


def init_categorical_array_equiv(self, scope, equiv_set, loc, args, kws):
    assert len(args) == 2 and not kws
    dekur__zfvot = args[0]
    if equiv_set.has_shape(dekur__zfvot):
        return ArrayAnalysis.AnalyzeResult(shape=dekur__zfvot, pre=[])
    return None


(ArrayAnalysis.
    _analyze_op_call_bodo_hiframes_pd_categorical_ext_init_categorical_array
    ) = init_categorical_array_equiv


def alloc_categorical_array(n, cat_dtype):
    pass


@overload(alloc_categorical_array, no_unliteral=True)
def _alloc_categorical_array(n, cat_dtype):
    csxf__pefhq = get_categories_int_type(cat_dtype)

    def impl(n, cat_dtype):
        codes = np.empty(n, csxf__pefhq)
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
            ect__wapc = {}
            wbemq__qlkex = np.empty(n + 1, np.int64)
            demia__kvjnb = {}
            npd__ycrto = []
            gcd__ayt = {}
            for syuf__jbj in range(n):
                gcd__ayt[categories[syuf__jbj]] = syuf__jbj
            for qvy__bnokz in to_replace:
                if qvy__bnokz != value:
                    if qvy__bnokz in gcd__ayt:
                        if value in gcd__ayt:
                            ect__wapc[qvy__bnokz] = qvy__bnokz
                            shwa__ivuw = gcd__ayt[qvy__bnokz]
                            demia__kvjnb[shwa__ivuw] = gcd__ayt[value]
                            npd__ycrto.append(shwa__ivuw)
                        else:
                            ect__wapc[qvy__bnokz] = value
                            gcd__ayt[value] = gcd__ayt[qvy__bnokz]
            cms__hlh = np.sort(np.array(npd__ycrto))
            ddagp__vms = 0
            otsi__rdq = []
            for djqsf__rars in range(-1, n):
                while ddagp__vms < len(cms__hlh) and djqsf__rars > cms__hlh[
                    ddagp__vms]:
                    ddagp__vms += 1
                otsi__rdq.append(ddagp__vms)
            for cypf__tcckm in range(-1, n):
                ryh__raz = cypf__tcckm
                if cypf__tcckm in demia__kvjnb:
                    ryh__raz = demia__kvjnb[cypf__tcckm]
                wbemq__qlkex[cypf__tcckm + 1] = ryh__raz - otsi__rdq[
                    ryh__raz + 1]
            return ect__wapc, wbemq__qlkex, len(cms__hlh)
        return impl


@numba.njit
def python_build_replace_dicts(to_replace, value, categories):
    return build_replace_dicts(to_replace, value, categories)


@register_jitable
def reassign_codes(new_codes_arr, old_codes_arr, codes_map_arr):
    for syuf__jbj in range(len(new_codes_arr)):
        new_codes_arr[syuf__jbj] = codes_map_arr[old_codes_arr[syuf__jbj] + 1]


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
    dit__qec = arr.dtype.ordered
    qhjt__lze = arr.dtype.elem_type
    orkg__apj = get_overload_const(to_replace)
    kstf__cpzk = get_overload_const(value)
    if (arr.dtype.categories is not None and orkg__apj is not NOT_CONSTANT and
        kstf__cpzk is not NOT_CONSTANT):
        qqjs__qbtcx, codes_map_arr, cvk__fvolp = python_build_replace_dicts(
            orkg__apj, kstf__cpzk, arr.dtype.categories)
        if len(qqjs__qbtcx) == 0:
            return lambda arr, to_replace, value: arr.copy()
        qzjv__cmxtu = []
        for efi__jynvc in arr.dtype.categories:
            if efi__jynvc in qqjs__qbtcx:
                awxj__ieeoj = qqjs__qbtcx[efi__jynvc]
                if awxj__ieeoj != efi__jynvc:
                    qzjv__cmxtu.append(awxj__ieeoj)
            else:
                qzjv__cmxtu.append(efi__jynvc)
        rpyt__imva = pd.CategoricalDtype(qzjv__cmxtu, dit__qec
            ).categories.values
        pbh__woypv = MetaType(tuple(rpyt__imva))

        def impl_dtype(arr, to_replace, value):
            remap__xtc = init_cat_dtype(bodo.utils.conversion.
                index_from_array(rpyt__imva), dit__qec, None, pbh__woypv)
            zumh__ygeea = alloc_categorical_array(len(arr.codes), remap__xtc)
            reassign_codes(zumh__ygeea.codes, arr.codes, codes_map_arr)
            return zumh__ygeea
        return impl_dtype
    qhjt__lze = arr.dtype.elem_type
    if qhjt__lze == types.unicode_type:

        def impl_str(arr, to_replace, value):
            categories = arr.dtype.categories
            ect__wapc, codes_map_arr, nynt__nqpee = build_replace_dicts(
                to_replace, value, categories.values)
            if len(ect__wapc) == 0:
                return init_categorical_array(arr.codes.copy().astype(np.
                    int64), init_cat_dtype(categories.copy(), dit__qec,
                    None, None))
            n = len(categories)
            rpyt__imva = bodo.libs.str_arr_ext.pre_alloc_string_array(n -
                nynt__nqpee, -1)
            axnng__rcr = 0
            for djqsf__rars in range(n):
                ctl__addtk = categories[djqsf__rars]
                if ctl__addtk in ect__wapc:
                    sqep__vquq = ect__wapc[ctl__addtk]
                    if sqep__vquq != ctl__addtk:
                        rpyt__imva[axnng__rcr] = sqep__vquq
                        axnng__rcr += 1
                else:
                    rpyt__imva[axnng__rcr] = ctl__addtk
                    axnng__rcr += 1
            zumh__ygeea = alloc_categorical_array(len(arr.codes),
                init_cat_dtype(bodo.utils.conversion.index_from_array(
                rpyt__imva), dit__qec, None, None))
            reassign_codes(zumh__ygeea.codes, arr.codes, codes_map_arr)
            return zumh__ygeea
        return impl_str
    gqdi__gyxf = dtype_to_array_type(qhjt__lze)

    def impl(arr, to_replace, value):
        categories = arr.dtype.categories
        ect__wapc, codes_map_arr, nynt__nqpee = build_replace_dicts(to_replace,
            value, categories.values)
        if len(ect__wapc) == 0:
            return init_categorical_array(arr.codes.copy().astype(np.int64),
                init_cat_dtype(categories.copy(), dit__qec, None, None))
        n = len(categories)
        rpyt__imva = bodo.utils.utils.alloc_type(n - nynt__nqpee,
            gqdi__gyxf, None)
        axnng__rcr = 0
        for syuf__jbj in range(n):
            ctl__addtk = categories[syuf__jbj]
            if ctl__addtk in ect__wapc:
                sqep__vquq = ect__wapc[ctl__addtk]
                if sqep__vquq != ctl__addtk:
                    rpyt__imva[axnng__rcr] = sqep__vquq
                    axnng__rcr += 1
            else:
                rpyt__imva[axnng__rcr] = ctl__addtk
                axnng__rcr += 1
        zumh__ygeea = alloc_categorical_array(len(arr.codes),
            init_cat_dtype(bodo.utils.conversion.index_from_array(
            rpyt__imva), dit__qec, None, None))
        reassign_codes(zumh__ygeea.codes, arr.codes, codes_map_arr)
        return zumh__ygeea
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
    tfkey__sxmk = dict()
    zafbx__qki = 0
    for syuf__jbj in range(len(vals)):
        val = vals[syuf__jbj]
        if val in tfkey__sxmk:
            continue
        tfkey__sxmk[val] = zafbx__qki
        zafbx__qki += 1
    return tfkey__sxmk


@register_jitable
def get_label_dict_from_categories_no_duplicates(vals):
    tfkey__sxmk = dict()
    for syuf__jbj in range(len(vals)):
        val = vals[syuf__jbj]
        tfkey__sxmk[val] = syuf__jbj
    return tfkey__sxmk


@overload(pd.Categorical, no_unliteral=True)
def pd_categorical_overload(values, categories=None, ordered=None, dtype=
    None, fastpath=False):
    tza__rqj = dict(fastpath=fastpath)
    oec__tlwz = dict(fastpath=False)
    check_unsupported_args('pd.Categorical', tza__rqj, oec__tlwz)
    if isinstance(dtype, bodo.hiframes.pd_categorical_ext.PDCategoricalDtype):

        def impl_dtype(values, categories=None, ordered=None, dtype=None,
            fastpath=False):
            data = bodo.utils.conversion.coerce_to_array(values)
            return bodo.utils.conversion.fix_arr_dtype(data, dtype)
        return impl_dtype
    if not is_overload_none(categories):
        qvpam__tiey = get_overload_const(categories)
        if qvpam__tiey is not NOT_CONSTANT and get_overload_const(ordered
            ) is not NOT_CONSTANT:
            if is_overload_none(ordered):
                lfle__fodf = False
            else:
                lfle__fodf = get_overload_const_bool(ordered)
            oxwaw__fouj = pd.CategoricalDtype(qvpam__tiey, lfle__fodf
                ).categories.values
            dqjt__yvqq = MetaType(tuple(oxwaw__fouj))

            def impl_cats_const(values, categories=None, ordered=None,
                dtype=None, fastpath=False):
                data = bodo.utils.conversion.coerce_to_array(values)
                remap__xtc = init_cat_dtype(bodo.utils.conversion.
                    index_from_array(oxwaw__fouj), lfle__fodf, None, dqjt__yvqq
                    )
                return bodo.utils.conversion.fix_arr_dtype(data, remap__xtc)
            return impl_cats_const

        def impl_cats(values, categories=None, ordered=None, dtype=None,
            fastpath=False):
            ordered = bodo.utils.conversion.false_if_none(ordered)
            data = bodo.utils.conversion.coerce_to_array(values)
            pjln__wvpxt = bodo.utils.conversion.convert_to_index(categories)
            cat_dtype = bodo.hiframes.pd_categorical_ext.init_cat_dtype(
                pjln__wvpxt, ordered, None, None)
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
            kjogt__jgcps = arr.codes[ind]
            return arr.dtype.categories[max(kjogt__jgcps, 0)]
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
    for syuf__jbj in range(len(arr1)):
        if arr1[syuf__jbj] != arr2[syuf__jbj]:
            return False
    return True


@overload(operator.setitem, no_unliteral=True)
def categorical_array_setitem(arr, ind, val):
    if not isinstance(arr, CategoricalArrayType):
        return
    if val == types.none or isinstance(val, types.optional):
        return
    uebt__rlfrj = is_scalar_type(val) and is_common_scalar_dtype([types.
        unliteral(val), arr.dtype.elem_type]) and not (isinstance(arr.dtype
        .elem_type, types.Integer) and isinstance(val, types.Float))
    tvu__hqzah = not isinstance(val, CategoricalArrayType
        ) and is_iterable_type(val) and is_common_scalar_dtype([val.dtype,
        arr.dtype.elem_type]) and not (isinstance(arr.dtype.elem_type,
        types.Integer) and isinstance(val.dtype, types.Float))
    onw__ulf = categorical_arrs_match(arr, val)
    nddtn__nhv = (
        f"setitem for CategoricalArrayType of dtype {arr.dtype} with indexing type {ind} received an incorrect 'value' type {val}."
        )
    nhf__nabyd = (
        'Cannot set a Categorical with another, without identical categories')
    if isinstance(ind, types.Integer):
        if not uebt__rlfrj:
            raise BodoError(nddtn__nhv)

        def impl_scalar(arr, ind, val):
            if val not in arr.dtype.categories:
                raise ValueError(
                    'Cannot setitem on a Categorical with a new category, set the categories first'
                    )
            kjogt__jgcps = arr.dtype.categories.get_loc(val)
            arr.codes[ind] = kjogt__jgcps
        return impl_scalar
    if is_list_like_index_type(ind) and isinstance(ind.dtype, types.Integer):
        if not (uebt__rlfrj or tvu__hqzah or onw__ulf !=
            CategoricalMatchingValues.DIFFERENT_TYPES):
            raise BodoError(nddtn__nhv)
        if onw__ulf == CategoricalMatchingValues.DONT_MATCH:
            raise BodoError(nhf__nabyd)
        if uebt__rlfrj:

            def impl_scalar(arr, ind, val):
                if val not in arr.dtype.categories:
                    raise ValueError(
                        'Cannot setitem on a Categorical with a new category, set the categories first'
                        )
                zoau__zoxt = arr.dtype.categories.get_loc(val)
                n = len(ind)
                for djqsf__rars in range(n):
                    arr.codes[ind[djqsf__rars]] = zoau__zoxt
            return impl_scalar
        if onw__ulf == CategoricalMatchingValues.DO_MATCH:

            def impl_arr_ind_mask(arr, ind, val):
                n = len(val.codes)
                for syuf__jbj in range(n):
                    arr.codes[ind[syuf__jbj]] = val.codes[syuf__jbj]
            return impl_arr_ind_mask
        if onw__ulf == CategoricalMatchingValues.MAY_MATCH:

            def impl_arr_ind_mask(arr, ind, val):
                if not cat_dtype_equal(arr.dtype, val.dtype):
                    raise ValueError(nhf__nabyd)
                n = len(val.codes)
                for syuf__jbj in range(n):
                    arr.codes[ind[syuf__jbj]] = val.codes[syuf__jbj]
            return impl_arr_ind_mask
        if tvu__hqzah:

            def impl_arr_ind_mask_cat_values(arr, ind, val):
                n = len(val)
                categories = arr.dtype.categories
                for djqsf__rars in range(n):
                    udyl__hocua = bodo.utils.conversion.unbox_if_timestamp(val
                        [djqsf__rars])
                    if udyl__hocua not in categories:
                        raise ValueError(
                            'Cannot setitem on a Categorical with a new category, set the categories first'
                            )
                    kjogt__jgcps = categories.get_loc(udyl__hocua)
                    arr.codes[ind[djqsf__rars]] = kjogt__jgcps
            return impl_arr_ind_mask_cat_values
    if is_list_like_index_type(ind) and ind.dtype == types.bool_:
        if not (uebt__rlfrj or tvu__hqzah or onw__ulf !=
            CategoricalMatchingValues.DIFFERENT_TYPES):
            raise BodoError(nddtn__nhv)
        if onw__ulf == CategoricalMatchingValues.DONT_MATCH:
            raise BodoError(nhf__nabyd)
        if uebt__rlfrj:

            def impl_scalar(arr, ind, val):
                if val not in arr.dtype.categories:
                    raise ValueError(
                        'Cannot setitem on a Categorical with a new category, set the categories first'
                        )
                zoau__zoxt = arr.dtype.categories.get_loc(val)
                n = len(ind)
                for djqsf__rars in range(n):
                    if ind[djqsf__rars]:
                        arr.codes[djqsf__rars] = zoau__zoxt
            return impl_scalar
        if onw__ulf == CategoricalMatchingValues.DO_MATCH:

            def impl_bool_ind_mask(arr, ind, val):
                n = len(ind)
                xolpk__rlh = 0
                for syuf__jbj in range(n):
                    if ind[syuf__jbj]:
                        arr.codes[syuf__jbj] = val.codes[xolpk__rlh]
                        xolpk__rlh += 1
            return impl_bool_ind_mask
        if onw__ulf == CategoricalMatchingValues.MAY_MATCH:

            def impl_bool_ind_mask(arr, ind, val):
                if not cat_dtype_equal(arr.dtype, val.dtype):
                    raise ValueError(nhf__nabyd)
                n = len(ind)
                xolpk__rlh = 0
                for syuf__jbj in range(n):
                    if ind[syuf__jbj]:
                        arr.codes[syuf__jbj] = val.codes[xolpk__rlh]
                        xolpk__rlh += 1
            return impl_bool_ind_mask
        if tvu__hqzah:

            def impl_bool_ind_mask_cat_values(arr, ind, val):
                n = len(ind)
                xolpk__rlh = 0
                categories = arr.dtype.categories
                for djqsf__rars in range(n):
                    if ind[djqsf__rars]:
                        udyl__hocua = bodo.utils.conversion.unbox_if_timestamp(
                            val[xolpk__rlh])
                        if udyl__hocua not in categories:
                            raise ValueError(
                                'Cannot setitem on a Categorical with a new category, set the categories first'
                                )
                        kjogt__jgcps = categories.get_loc(udyl__hocua)
                        arr.codes[djqsf__rars] = kjogt__jgcps
                        xolpk__rlh += 1
            return impl_bool_ind_mask_cat_values
    if isinstance(ind, types.SliceType):
        if not (uebt__rlfrj or tvu__hqzah or onw__ulf !=
            CategoricalMatchingValues.DIFFERENT_TYPES):
            raise BodoError(nddtn__nhv)
        if onw__ulf == CategoricalMatchingValues.DONT_MATCH:
            raise BodoError(nhf__nabyd)
        if uebt__rlfrj:

            def impl_scalar(arr, ind, val):
                if val not in arr.dtype.categories:
                    raise ValueError(
                        'Cannot setitem on a Categorical with a new category, set the categories first'
                        )
                zoau__zoxt = arr.dtype.categories.get_loc(val)
                xjg__yugmu = numba.cpython.unicode._normalize_slice(ind,
                    len(arr))
                for djqsf__rars in range(xjg__yugmu.start, xjg__yugmu.stop,
                    xjg__yugmu.step):
                    arr.codes[djqsf__rars] = zoau__zoxt
            return impl_scalar
        if onw__ulf == CategoricalMatchingValues.DO_MATCH:

            def impl_arr(arr, ind, val):
                arr.codes[ind] = val.codes
            return impl_arr
        if onw__ulf == CategoricalMatchingValues.MAY_MATCH:

            def impl_arr(arr, ind, val):
                if not cat_dtype_equal(arr.dtype, val.dtype):
                    raise ValueError(nhf__nabyd)
                arr.codes[ind] = val.codes
            return impl_arr
        if tvu__hqzah:

            def impl_slice_cat_values(arr, ind, val):
                categories = arr.dtype.categories
                xjg__yugmu = numba.cpython.unicode._normalize_slice(ind,
                    len(arr))
                xolpk__rlh = 0
                for djqsf__rars in range(xjg__yugmu.start, xjg__yugmu.stop,
                    xjg__yugmu.step):
                    udyl__hocua = bodo.utils.conversion.unbox_if_timestamp(val
                        [xolpk__rlh])
                    if udyl__hocua not in categories:
                        raise ValueError(
                            'Cannot setitem on a Categorical with a new category, set the categories first'
                            )
                    kjogt__jgcps = categories.get_loc(udyl__hocua)
                    arr.codes[djqsf__rars] = kjogt__jgcps
                    xolpk__rlh += 1
            return impl_slice_cat_values
    raise BodoError(
        f'setitem for CategoricalArrayType with indexing type {ind} not supported.'
        )
