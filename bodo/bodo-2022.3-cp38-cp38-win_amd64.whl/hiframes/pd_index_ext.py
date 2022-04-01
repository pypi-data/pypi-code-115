import datetime
import operator
import warnings
import llvmlite.llvmpy.core as lc
import numba
import numpy as np
import pandas as pd
from llvmlite import ir as lir
from numba.core import cgutils, types
from numba.core.imputils import impl_ret_new_ref, lower_constant
from numba.core.typing.templates import AttributeTemplate, signature
from numba.extending import NativeValue, box, infer_getattr, intrinsic, lower_builtin, lower_cast, make_attribute_wrapper, models, overload, overload_attribute, overload_method, register_jitable, register_model, typeof_impl, unbox
from numba.parfors.array_analysis import ArrayAnalysis
import bodo
import bodo.hiframes
import bodo.utils.conversion
from bodo.hiframes.datetime_timedelta_ext import pd_timedelta_type
from bodo.hiframes.pd_multi_index_ext import MultiIndexType
from bodo.hiframes.pd_series_ext import SeriesType
from bodo.hiframes.pd_timestamp_ext import pd_timestamp_type
from bodo.libs.binary_arr_ext import binary_array_type, bytes_type
from bodo.libs.bool_arr_ext import boolean_array
from bodo.libs.int_arr_ext import IntegerArrayType
from bodo.libs.pd_datetime_arr_ext import DatetimeArrayType
from bodo.libs.str_arr_ext import string_array_type
from bodo.libs.str_ext import string_type
from bodo.utils.transform import get_const_func_output_type
from bodo.utils.typing import BodoError, check_unsupported_args, create_unsupported_overload, dtype_to_array_type, get_overload_const_func, get_overload_const_str, get_udf_error_msg, get_udf_out_arr_type, get_val_type_maybe_str_literal, is_const_func_type, is_heterogeneous_tuple_type, is_iterable_type, is_overload_false, is_overload_none, is_overload_true, is_str_arr_type, parse_dtype, raise_bodo_error
from bodo.utils.utils import is_null_value
_dt_index_data_typ = types.Array(types.NPDatetime('ns'), 1, 'C')
_timedelta_index_data_typ = types.Array(types.NPTimedelta('ns'), 1, 'C')
iNaT = pd._libs.tslibs.iNaT
NaT = types.NPDatetime('ns')('NaT')
idx_cpy_arg_defaults = dict(deep=False, dtype=None, names=None)
idx_typ_to_format_str_map = dict()


@typeof_impl.register(pd.Index)
def typeof_pd_index(val, c):
    if val.inferred_type == 'string' or pd._libs.lib.infer_dtype(val, True
        ) == 'string':
        return StringIndexType(get_val_type_maybe_str_literal(val.name))
    if val.inferred_type == 'bytes' or pd._libs.lib.infer_dtype(val, True
        ) == 'bytes':
        return BinaryIndexType(get_val_type_maybe_str_literal(val.name))
    if val.equals(pd.Index([])):
        return StringIndexType(get_val_type_maybe_str_literal(val.name))
    if val.inferred_type == 'date':
        return DatetimeIndexType(get_val_type_maybe_str_literal(val.name))
    if val.inferred_type == 'integer' or pd._libs.lib.infer_dtype(val, True
        ) == 'integer':
        return NumericIndexType(types.int64, get_val_type_maybe_str_literal
            (val.name), IntegerArrayType(types.int64))
    if val.inferred_type == 'boolean' or pd._libs.lib.infer_dtype(val, True
        ) == 'boolean':
        return NumericIndexType(types.bool_, get_val_type_maybe_str_literal
            (val.name), boolean_array)
    raise NotImplementedError(f'unsupported pd.Index type {val}')


class DatetimeIndexType(types.IterableType, types.ArrayCompatible):

    def __init__(self, name_typ=None, data=None):
        name_typ = types.none if name_typ is None else name_typ
        self.name_typ = name_typ
        if isinstance(data, DatetimeArrayType):
            self.data = data
        else:
            self.data = types.Array(bodo.datetime64ns, 1, 'C')
        super(DatetimeIndexType, self).__init__(name=
            f'DatetimeIndex({name_typ}, {self.data})')
    ndim = 1

    @property
    def as_array(self):
        return types.Array(types.undefined, 1, 'C')

    @property
    def dtype(self):
        return self.data.dtype

    @property
    def tzval(self):
        return self.data.tz if isinstance(self.data, bodo.DatetimeArrayType
            ) else None

    def copy(self):
        return DatetimeIndexType(self.name_typ, self.data)

    @property
    def iterator_type(self):
        return bodo.utils.typing.BodoArrayIterator(self)

    @property
    def pandas_type_name(self):
        return self.data.dtype.type_name

    @property
    def numpy_type_name(self):
        return str(self.data.dtype)


types.datetime_index = DatetimeIndexType()


@typeof_impl.register(pd.DatetimeIndex)
def typeof_datetime_index(val, c):
    if isinstance(val.dtype, pd.DatetimeTZDtype):
        return DatetimeIndexType(get_val_type_maybe_str_literal(val.name),
            DatetimeArrayType(val.tz))
    return DatetimeIndexType(get_val_type_maybe_str_literal(val.name))


@register_model(DatetimeIndexType)
class DatetimeIndexModel(models.StructModel):

    def __init__(self, dmm, fe_type):
        zpl__dxgv = [('data', fe_type.data), ('name', fe_type.name_typ), (
            'dict', types.DictType(_dt_index_data_typ.dtype, types.int64))]
        super(DatetimeIndexModel, self).__init__(dmm, fe_type, zpl__dxgv)


make_attribute_wrapper(DatetimeIndexType, 'data', '_data')
make_attribute_wrapper(DatetimeIndexType, 'name', '_name')
make_attribute_wrapper(DatetimeIndexType, 'dict', '_dict')


@overload_method(DatetimeIndexType, 'copy', no_unliteral=True)
def overload_datetime_index_copy(A, name=None, deep=False, dtype=None,
    names=None):
    yhqk__xya = dict(deep=deep, dtype=dtype, names=names)
    qanl__rehb = idx_typ_to_format_str_map[DatetimeIndexType].format('copy()')
    check_unsupported_args('copy', yhqk__xya, idx_cpy_arg_defaults, fn_str=
        qanl__rehb, package_name='pandas', module_name='Index')
    if not is_overload_none(name):

        def impl(A, name=None, deep=False, dtype=None, names=None):
            return bodo.hiframes.pd_index_ext.init_datetime_index(A._data.
                copy(), name)
    else:

        def impl(A, name=None, deep=False, dtype=None, names=None):
            return bodo.hiframes.pd_index_ext.init_datetime_index(A._data.
                copy(), A._name)
    return impl


@box(DatetimeIndexType)
def box_dt_index(typ, val, c):
    jrfr__obcnn = c.context.insert_const_string(c.builder.module, 'pandas')
    fxnx__xzfzp = c.pyapi.import_module_noblock(jrfr__obcnn)
    alc__khxyb = numba.core.cgutils.create_struct_proxy(typ)(c.context, c.
        builder, val)
    c.context.nrt.incref(c.builder, typ.data, alc__khxyb.data)
    kcb__atfe = c.pyapi.from_native_value(typ.data, alc__khxyb.data, c.
        env_manager)
    c.context.nrt.incref(c.builder, typ.name_typ, alc__khxyb.name)
    phmv__rxy = c.pyapi.from_native_value(typ.name_typ, alc__khxyb.name, c.
        env_manager)
    args = c.pyapi.tuple_pack([kcb__atfe])
    tgjqa__vooh = c.pyapi.object_getattr_string(fxnx__xzfzp, 'DatetimeIndex')
    kws = c.pyapi.dict_pack([('name', phmv__rxy)])
    dohhm__xet = c.pyapi.call(tgjqa__vooh, args, kws)
    c.pyapi.decref(kcb__atfe)
    c.pyapi.decref(phmv__rxy)
    c.pyapi.decref(fxnx__xzfzp)
    c.pyapi.decref(tgjqa__vooh)
    c.pyapi.decref(args)
    c.pyapi.decref(kws)
    c.context.nrt.decref(c.builder, typ, val)
    return dohhm__xet


@unbox(DatetimeIndexType)
def unbox_datetime_index(typ, val, c):
    if isinstance(typ.data, DatetimeArrayType):
        xtrdg__voi = c.pyapi.object_getattr_string(val, 'array')
    else:
        xtrdg__voi = c.pyapi.object_getattr_string(val, 'values')
    data = c.pyapi.to_native_value(typ.data, xtrdg__voi).value
    phmv__rxy = c.pyapi.object_getattr_string(val, 'name')
    name = c.pyapi.to_native_value(typ.name_typ, phmv__rxy).value
    zfq__oyglt = cgutils.create_struct_proxy(typ)(c.context, c.builder)
    zfq__oyglt.data = data
    zfq__oyglt.name = name
    dtype = _dt_index_data_typ.dtype
    hjz__uhuvd, rfc__acua = c.pyapi.call_jit_code(lambda : numba.typed.Dict
        .empty(dtype, types.int64), types.DictType(dtype, types.int64)(), [])
    zfq__oyglt.dict = rfc__acua
    c.pyapi.decref(xtrdg__voi)
    c.pyapi.decref(phmv__rxy)
    return NativeValue(zfq__oyglt._getvalue())


@intrinsic
def init_datetime_index(typingctx, data, name):
    name = types.none if name is None else name

    def codegen(context, builder, signature, args):
        pywrf__udxk, hsle__oro = args
        alc__khxyb = cgutils.create_struct_proxy(signature.return_type)(context
            , builder)
        alc__khxyb.data = pywrf__udxk
        alc__khxyb.name = hsle__oro
        context.nrt.incref(builder, signature.args[0], pywrf__udxk)
        context.nrt.incref(builder, signature.args[1], hsle__oro)
        dtype = _dt_index_data_typ.dtype
        alc__khxyb.dict = context.compile_internal(builder, lambda : numba.
            typed.Dict.empty(dtype, types.int64), types.DictType(dtype,
            types.int64)(), [])
        return alc__khxyb._getvalue()
    dcwo__rfm = DatetimeIndexType(name, data)
    sig = signature(dcwo__rfm, data, name)
    return sig, codegen


def init_index_equiv(self, scope, equiv_set, loc, args, kws):
    assert len(args) >= 1 and not kws
    xcs__ddzwo = args[0]
    if equiv_set.has_shape(xcs__ddzwo):
        return ArrayAnalysis.AnalyzeResult(shape=xcs__ddzwo, pre=[])
    return None


(ArrayAnalysis._analyze_op_call_bodo_hiframes_pd_index_ext_init_datetime_index
    ) = init_index_equiv


def gen_dti_field_impl(field):
    zjcz__ohwiu = 'def impl(dti):\n'
    zjcz__ohwiu += '    numba.parfors.parfor.init_prange()\n'
    zjcz__ohwiu += '    A = bodo.hiframes.pd_index_ext.get_index_data(dti)\n'
    zjcz__ohwiu += (
        '    name = bodo.hiframes.pd_index_ext.get_index_name(dti)\n')
    zjcz__ohwiu += '    n = len(A)\n'
    zjcz__ohwiu += '    S = np.empty(n, np.int64)\n'
    zjcz__ohwiu += '    for i in numba.parfors.parfor.internal_prange(n):\n'
    zjcz__ohwiu += '        val = A[i]\n'
    zjcz__ohwiu += '        ts = bodo.utils.conversion.box_if_dt64(val)\n'
    if field in ['weekday']:
        zjcz__ohwiu += '        S[i] = ts.' + field + '()\n'
    else:
        zjcz__ohwiu += '        S[i] = ts.' + field + '\n'
    zjcz__ohwiu += (
        '    return bodo.hiframes.pd_index_ext.init_numeric_index(S, name)\n')
    flclc__rgw = {}
    exec(zjcz__ohwiu, {'numba': numba, 'np': np, 'bodo': bodo}, flclc__rgw)
    impl = flclc__rgw['impl']
    return impl


def _install_dti_date_fields():
    for field in bodo.hiframes.pd_timestamp_ext.date_fields:
        if field in ['is_leap_year']:
            continue
        impl = gen_dti_field_impl(field)
        overload_attribute(DatetimeIndexType, field)(lambda dti: impl)


_install_dti_date_fields()


@overload_attribute(DatetimeIndexType, 'is_leap_year')
def overload_datetime_index_is_leap_year(dti):

    def impl(dti):
        numba.parfors.parfor.init_prange()
        A = bodo.hiframes.pd_index_ext.get_index_data(dti)
        dnfp__knkq = len(A)
        S = np.empty(dnfp__knkq, np.bool_)
        for i in numba.parfors.parfor.internal_prange(dnfp__knkq):
            val = A[i]
            umj__lkvne = bodo.utils.conversion.box_if_dt64(val)
            S[i] = bodo.hiframes.pd_timestamp_ext.is_leap_year(umj__lkvne.year)
        return S
    return impl


@overload_attribute(DatetimeIndexType, 'date')
def overload_datetime_index_date(dti):

    def impl(dti):
        numba.parfors.parfor.init_prange()
        A = bodo.hiframes.pd_index_ext.get_index_data(dti)
        dnfp__knkq = len(A)
        S = bodo.hiframes.datetime_date_ext.alloc_datetime_date_array(
            dnfp__knkq)
        for i in numba.parfors.parfor.internal_prange(dnfp__knkq):
            val = A[i]
            umj__lkvne = bodo.utils.conversion.box_if_dt64(val)
            S[i] = datetime.date(umj__lkvne.year, umj__lkvne.month,
                umj__lkvne.day)
        return S
    return impl


@numba.njit(no_cpython_wrapper=True)
def _dti_val_finalize(s, count):
    if not count:
        s = iNaT
    return bodo.hiframes.pd_timestamp_ext.convert_datetime64_to_timestamp(s)


@numba.njit(no_cpython_wrapper=True)
def _tdi_val_finalize(s, count):
    return pd.Timedelta('nan') if not count else pd.Timedelta(s)


@overload_method(DatetimeIndexType, 'min', no_unliteral=True)
def overload_datetime_index_min(dti, axis=None, skipna=True):
    jruj__kdq = dict(axis=axis, skipna=skipna)
    ixdt__dtxi = dict(axis=None, skipna=True)
    check_unsupported_args('DatetimeIndex.min', jruj__kdq, ixdt__dtxi,
        package_name='pandas', module_name='Index')
    bodo.hiframes.pd_timestamp_ext.check_tz_aware_unsupported(dti,
        'Index.min()')

    def impl(dti, axis=None, skipna=True):
        numba.parfors.parfor.init_prange()
        fap__xho = bodo.hiframes.pd_index_ext.get_index_data(dti)
        s = numba.cpython.builtins.get_type_max_value(numba.core.types.int64)
        count = 0
        for i in numba.parfors.parfor.internal_prange(len(fap__xho)):
            if not bodo.libs.array_kernels.isna(fap__xho, i):
                val = bodo.hiframes.pd_timestamp_ext.dt64_to_integer(fap__xho
                    [i])
                s = min(s, val)
                count += 1
        return bodo.hiframes.pd_index_ext._dti_val_finalize(s, count)
    return impl


@overload_method(DatetimeIndexType, 'max', no_unliteral=True)
def overload_datetime_index_max(dti, axis=None, skipna=True):
    jruj__kdq = dict(axis=axis, skipna=skipna)
    ixdt__dtxi = dict(axis=None, skipna=True)
    check_unsupported_args('DatetimeIndex.max', jruj__kdq, ixdt__dtxi,
        package_name='pandas', module_name='Index')
    bodo.hiframes.pd_timestamp_ext.check_tz_aware_unsupported(dti,
        'Index.max()')

    def impl(dti, axis=None, skipna=True):
        numba.parfors.parfor.init_prange()
        fap__xho = bodo.hiframes.pd_index_ext.get_index_data(dti)
        s = numba.cpython.builtins.get_type_min_value(numba.core.types.int64)
        count = 0
        for i in numba.parfors.parfor.internal_prange(len(fap__xho)):
            if not bodo.libs.array_kernels.isna(fap__xho, i):
                val = bodo.hiframes.pd_timestamp_ext.dt64_to_integer(fap__xho
                    [i])
                s = max(s, val)
                count += 1
        return bodo.hiframes.pd_index_ext._dti_val_finalize(s, count)
    return impl


@overload_method(DatetimeIndexType, 'tz_convert', no_unliteral=True)
def overload_pd_datetime_tz_convert(A, tz):

    def impl(A, tz):
        return init_datetime_index(A._data.tz_convert(tz), A._name)
    return impl


@infer_getattr
class DatetimeIndexAttribute(AttributeTemplate):
    key = DatetimeIndexType

    def resolve_values(self, ary):
        return _dt_index_data_typ


@overload(pd.DatetimeIndex, no_unliteral=True)
def pd_datetimeindex_overload(data=None, freq=None, tz=None, normalize=
    False, closed=None, ambiguous='raise', dayfirst=False, yearfirst=False,
    dtype=None, copy=False, name=None):
    if is_overload_none(data):
        raise BodoError('data argument in pd.DatetimeIndex() expected')
    bodo.hiframes.pd_timestamp_ext.check_tz_aware_unsupported(data,
        'pandas.DatetimeIndex()')
    jruj__kdq = dict(freq=freq, tz=tz, normalize=normalize, closed=closed,
        ambiguous=ambiguous, dayfirst=dayfirst, yearfirst=yearfirst, dtype=
        dtype, copy=copy)
    ixdt__dtxi = dict(freq=None, tz=None, normalize=False, closed=None,
        ambiguous='raise', dayfirst=False, yearfirst=False, dtype=None,
        copy=False)
    check_unsupported_args('pandas.DatetimeIndex', jruj__kdq, ixdt__dtxi,
        package_name='pandas', module_name='Index')

    def f(data=None, freq=None, tz=None, normalize=False, closed=None,
        ambiguous='raise', dayfirst=False, yearfirst=False, dtype=None,
        copy=False, name=None):
        hykco__zkf = bodo.utils.conversion.coerce_to_array(data)
        S = bodo.utils.conversion.convert_to_dt64ns(hykco__zkf)
        return bodo.hiframes.pd_index_ext.init_datetime_index(S, name)
    return f


def overload_sub_operator_datetime_index(lhs, rhs):
    if isinstance(lhs, DatetimeIndexType
        ) and rhs == bodo.hiframes.pd_timestamp_ext.pd_timestamp_type:
        knivb__aue = np.dtype('timedelta64[ns]')

        def impl(lhs, rhs):
            numba.parfors.parfor.init_prange()
            fap__xho = bodo.hiframes.pd_index_ext.get_index_data(lhs)
            name = bodo.hiframes.pd_index_ext.get_index_name(lhs)
            dnfp__knkq = len(fap__xho)
            S = np.empty(dnfp__knkq, knivb__aue)
            lgdhj__cap = rhs.value
            for i in numba.parfors.parfor.internal_prange(dnfp__knkq):
                S[i] = bodo.hiframes.pd_timestamp_ext.integer_to_timedelta64(
                    bodo.hiframes.pd_timestamp_ext.dt64_to_integer(fap__xho
                    [i]) - lgdhj__cap)
            return bodo.hiframes.pd_index_ext.init_timedelta_index(S, name)
        return impl
    if isinstance(rhs, DatetimeIndexType
        ) and lhs == bodo.hiframes.pd_timestamp_ext.pd_timestamp_type:
        knivb__aue = np.dtype('timedelta64[ns]')

        def impl(lhs, rhs):
            numba.parfors.parfor.init_prange()
            fap__xho = bodo.hiframes.pd_index_ext.get_index_data(rhs)
            name = bodo.hiframes.pd_index_ext.get_index_name(rhs)
            dnfp__knkq = len(fap__xho)
            S = np.empty(dnfp__knkq, knivb__aue)
            lgdhj__cap = lhs.value
            for i in numba.parfors.parfor.internal_prange(dnfp__knkq):
                S[i] = bodo.hiframes.pd_timestamp_ext.integer_to_timedelta64(
                    lgdhj__cap - bodo.hiframes.pd_timestamp_ext.
                    dt64_to_integer(fap__xho[i]))
            return bodo.hiframes.pd_index_ext.init_timedelta_index(S, name)
        return impl


def gen_dti_str_binop_impl(op, is_lhs_dti):
    nalnx__vuy = numba.core.utils.OPERATORS_TO_BUILTINS[op]
    zjcz__ohwiu = 'def impl(lhs, rhs):\n'
    if is_lhs_dti:
        zjcz__ohwiu += '  dt_index, _str = lhs, rhs\n'
        dwjbj__gqo = 'arr[i] {} other'.format(nalnx__vuy)
    else:
        zjcz__ohwiu += '  dt_index, _str = rhs, lhs\n'
        dwjbj__gqo = 'other {} arr[i]'.format(nalnx__vuy)
    zjcz__ohwiu += (
        '  arr = bodo.hiframes.pd_index_ext.get_index_data(dt_index)\n')
    zjcz__ohwiu += '  l = len(arr)\n'
    zjcz__ohwiu += (
        '  other = bodo.hiframes.pd_timestamp_ext.parse_datetime_str(_str)\n')
    zjcz__ohwiu += '  S = bodo.libs.bool_arr_ext.alloc_bool_array(l)\n'
    zjcz__ohwiu += '  for i in numba.parfors.parfor.internal_prange(l):\n'
    zjcz__ohwiu += '    S[i] = {}\n'.format(dwjbj__gqo)
    zjcz__ohwiu += '  return S\n'
    flclc__rgw = {}
    exec(zjcz__ohwiu, {'bodo': bodo, 'numba': numba, 'np': np}, flclc__rgw)
    impl = flclc__rgw['impl']
    return impl


def overload_binop_dti_str(op):

    def overload_impl(lhs, rhs):
        if isinstance(lhs, DatetimeIndexType) and types.unliteral(rhs
            ) == string_type:
            return gen_dti_str_binop_impl(op, True)
        if isinstance(rhs, DatetimeIndexType) and types.unliteral(lhs
            ) == string_type:
            return gen_dti_str_binop_impl(op, False)
    return overload_impl


@overload(pd.Index, inline='always', no_unliteral=True)
def pd_index_overload(data=None, dtype=None, copy=False, name=None,
    tupleize_cols=True):
    bodo.hiframes.pd_timestamp_ext.check_tz_aware_unsupported(data,
        'pandas.Index()')
    data = types.unliteral(data) if not isinstance(data, types.LiteralList
        ) else data
    cibpg__pmuqo = getattr(data, 'dtype', None)
    if not is_overload_none(dtype):
        kisi__vlwm = parse_dtype(dtype, 'pandas.Index')
    else:
        kisi__vlwm = cibpg__pmuqo
    if isinstance(kisi__vlwm, types.misc.PyObject):
        raise BodoError(
            "pd.Index() object 'dtype' is not specific enough for typing. Please provide a more exact type (e.g. str)."
            )
    if isinstance(data, RangeIndexType):

        def impl(data=None, dtype=None, copy=False, name=None,
            tupleize_cols=True):
            return pd.RangeIndex(data, name=name)
    elif isinstance(data, DatetimeIndexType) or kisi__vlwm == types.NPDatetime(
        'ns'):

        def impl(data=None, dtype=None, copy=False, name=None,
            tupleize_cols=True):
            return pd.DatetimeIndex(data, name=name)
    elif isinstance(data, TimedeltaIndexType
        ) or kisi__vlwm == types.NPTimedelta('ns'):

        def impl(data=None, dtype=None, copy=False, name=None,
            tupleize_cols=True):
            return pd.TimedeltaIndex(data, name=name)
    elif is_heterogeneous_tuple_type(data):

        def impl(data=None, dtype=None, copy=False, name=None,
            tupleize_cols=True):
            return bodo.hiframes.pd_index_ext.init_heter_index(data, name)
        return impl
    elif bodo.utils.utils.is_array_typ(data, False) or isinstance(data, (
        SeriesType, types.List, types.UniTuple)):
        if isinstance(kisi__vlwm, (types.Integer, types.Float, types.Boolean)):

            def impl(data=None, dtype=None, copy=False, name=None,
                tupleize_cols=True):
                hykco__zkf = bodo.utils.conversion.coerce_to_array(data)
                xgms__ihs = bodo.utils.conversion.fix_arr_dtype(hykco__zkf,
                    kisi__vlwm)
                return bodo.hiframes.pd_index_ext.init_numeric_index(xgms__ihs,
                    name)
        elif kisi__vlwm in [types.string, bytes_type]:

            def impl(data=None, dtype=None, copy=False, name=None,
                tupleize_cols=True):
                return bodo.hiframes.pd_index_ext.init_binary_str_index(bodo
                    .utils.conversion.coerce_to_array(data), name)
        else:
            raise BodoError(
                'pd.Index(): provided array is of unsupported type.')
    elif is_overload_none(data):
        raise BodoError(
            'data argument in pd.Index() is invalid: None or scalar is not acceptable'
            )
    else:
        raise BodoError(
            f'pd.Index(): the provided argument type {data} is not supported')
    return impl


@overload(operator.getitem, no_unliteral=True)
def overload_datetime_index_getitem(dti, ind):
    if isinstance(dti, DatetimeIndexType):
        if isinstance(ind, types.Integer):

            def impl(dti, ind):
                klilz__ciow = bodo.hiframes.pd_index_ext.get_index_data(dti)
                val = klilz__ciow[ind]
                return bodo.utils.conversion.box_if_dt64(val)
            return impl
        else:

            def impl(dti, ind):
                klilz__ciow = bodo.hiframes.pd_index_ext.get_index_data(dti)
                name = bodo.hiframes.pd_index_ext.get_index_name(dti)
                qdrt__mqdb = klilz__ciow[ind]
                return bodo.hiframes.pd_index_ext.init_datetime_index(
                    qdrt__mqdb, name)
            return impl


@overload(operator.getitem, no_unliteral=True)
def overload_timedelta_index_getitem(I, ind):
    if not isinstance(I, TimedeltaIndexType):
        return
    if isinstance(ind, types.Integer):

        def impl(I, ind):
            soh__hjius = bodo.hiframes.pd_index_ext.get_index_data(I)
            return pd.Timedelta(soh__hjius[ind])
        return impl

    def impl(I, ind):
        soh__hjius = bodo.hiframes.pd_index_ext.get_index_data(I)
        name = bodo.hiframes.pd_index_ext.get_index_name(I)
        qdrt__mqdb = soh__hjius[ind]
        return bodo.hiframes.pd_index_ext.init_timedelta_index(qdrt__mqdb, name
            )
    return impl


@numba.njit(no_cpython_wrapper=True)
def validate_endpoints(closed):
    fpd__ytsq = False
    liu__vkbp = False
    if closed is None:
        fpd__ytsq = True
        liu__vkbp = True
    elif closed == 'left':
        fpd__ytsq = True
    elif closed == 'right':
        liu__vkbp = True
    else:
        raise ValueError("Closed has to be either 'left', 'right' or None")
    return fpd__ytsq, liu__vkbp


@numba.njit(no_cpython_wrapper=True)
def to_offset_value(freq):
    if freq is None:
        return None
    with numba.objmode(r='int64'):
        r = pd.tseries.frequencies.to_offset(freq).nanos
    return r


@numba.generated_jit(nopython=True, no_cpython_wrapper=True)
def _dummy_convert_none_to_int(val):
    if is_overload_none(val):

        def impl(val):
            return 0
        return impl
    if isinstance(val, types.Optional):

        def impl(val):
            if val is None:
                return 0
            return bodo.utils.indexing.unoptional(val)
        return impl
    return lambda val: val


@overload(pd.date_range, no_unliteral=True)
def pd_date_range_overload(start=None, end=None, periods=None, freq=None,
    tz=None, normalize=False, name=None, closed=None):
    jruj__kdq = dict(tz=tz, normalize=normalize)
    ixdt__dtxi = dict(tz=None, normalize=False)
    check_unsupported_args('pandas.date_range', jruj__kdq, ixdt__dtxi,
        package_name='pandas', module_name='General')
    if not is_overload_none(tz):
        raise BodoError('pd.date_range(): tz argument not supported yet')
    if is_overload_none(freq) and any(is_overload_none(t) for t in (start,
        end, periods)):
        freq = 'D'
    if sum(not is_overload_none(t) for t in (start, end, periods, freq)) != 3:
        raise BodoError(
            'Of the four parameters: start, end, periods, and freq, exactly three must be specified'
            )

    def f(start=None, end=None, periods=None, freq=None, tz=None, normalize
        =False, name=None, closed=None):
        if freq is None and (start is None or end is None or periods is None):
            freq = 'D'
        freq = bodo.hiframes.pd_index_ext.to_offset_value(freq)
        jhsb__nmv = pd.Timestamp('2018-01-01')
        if start is not None:
            jhsb__nmv = pd.Timestamp(start)
        txo__nnrlw = pd.Timestamp('2018-01-01')
        if end is not None:
            txo__nnrlw = pd.Timestamp(end)
        if start is None and end is None and closed is not None:
            raise ValueError(
                'Closed has to be None if not both of startand end are defined'
                )
        fpd__ytsq, liu__vkbp = bodo.hiframes.pd_index_ext.validate_endpoints(
            closed)
        if freq is not None:
            umi__jhnuf = _dummy_convert_none_to_int(freq)
            if periods is None:
                b = jhsb__nmv.value
                ohv__agzv = b + (txo__nnrlw.value - b
                    ) // umi__jhnuf * umi__jhnuf + umi__jhnuf // 2 + 1
            elif start is not None:
                periods = _dummy_convert_none_to_int(periods)
                b = jhsb__nmv.value
                jvd__pbrxw = np.int64(periods) * np.int64(umi__jhnuf)
                ohv__agzv = np.int64(b) + jvd__pbrxw
            elif end is not None:
                periods = _dummy_convert_none_to_int(periods)
                ohv__agzv = txo__nnrlw.value + umi__jhnuf
                jvd__pbrxw = np.int64(periods) * np.int64(-umi__jhnuf)
                b = np.int64(ohv__agzv) + jvd__pbrxw
            else:
                raise ValueError(
                    "at least 'start' or 'end' should be specified if a 'period' is given."
                    )
            wtupd__lkel = np.arange(b, ohv__agzv, umi__jhnuf, np.int64)
        else:
            periods = _dummy_convert_none_to_int(periods)
            cnzq__nmemh = txo__nnrlw.value - jhsb__nmv.value
            step = cnzq__nmemh / (periods - 1)
            phha__mmd = np.arange(0, periods, 1, np.float64)
            phha__mmd *= step
            phha__mmd += jhsb__nmv.value
            wtupd__lkel = phha__mmd.astype(np.int64)
            wtupd__lkel[-1] = txo__nnrlw.value
        if not fpd__ytsq and len(wtupd__lkel) and wtupd__lkel[0
            ] == jhsb__nmv.value:
            wtupd__lkel = wtupd__lkel[1:]
        if not liu__vkbp and len(wtupd__lkel) and wtupd__lkel[-1
            ] == txo__nnrlw.value:
            wtupd__lkel = wtupd__lkel[:-1]
        S = bodo.utils.conversion.convert_to_dt64ns(wtupd__lkel)
        return bodo.hiframes.pd_index_ext.init_datetime_index(S, name)
    return f


@overload(pd.timedelta_range, no_unliteral=True)
def pd_timedelta_range_overload(start=None, end=None, periods=None, freq=
    None, name=None, closed=None):
    if is_overload_none(freq) and any(is_overload_none(t) for t in (start,
        end, periods)):
        freq = 'D'
    if sum(not is_overload_none(t) for t in (start, end, periods, freq)) != 3:
        raise BodoError(
            'Of the four parameters: start, end, periods, and freq, exactly three must be specified'
            )

    def f(start=None, end=None, periods=None, freq=None, name=None, closed=None
        ):
        if freq is None and (start is None or end is None or periods is None):
            freq = 'D'
        freq = bodo.hiframes.pd_index_ext.to_offset_value(freq)
        jhsb__nmv = pd.Timedelta('1 day')
        if start is not None:
            jhsb__nmv = pd.Timedelta(start)
        txo__nnrlw = pd.Timedelta('1 day')
        if end is not None:
            txo__nnrlw = pd.Timedelta(end)
        if start is None and end is None and closed is not None:
            raise ValueError(
                'Closed has to be None if not both of start and end are defined'
                )
        fpd__ytsq, liu__vkbp = bodo.hiframes.pd_index_ext.validate_endpoints(
            closed)
        if freq is not None:
            umi__jhnuf = _dummy_convert_none_to_int(freq)
            if periods is None:
                b = jhsb__nmv.value
                ohv__agzv = b + (txo__nnrlw.value - b
                    ) // umi__jhnuf * umi__jhnuf + umi__jhnuf // 2 + 1
            elif start is not None:
                periods = _dummy_convert_none_to_int(periods)
                b = jhsb__nmv.value
                jvd__pbrxw = np.int64(periods) * np.int64(umi__jhnuf)
                ohv__agzv = np.int64(b) + jvd__pbrxw
            elif end is not None:
                periods = _dummy_convert_none_to_int(periods)
                ohv__agzv = txo__nnrlw.value + umi__jhnuf
                jvd__pbrxw = np.int64(periods) * np.int64(-umi__jhnuf)
                b = np.int64(ohv__agzv) + jvd__pbrxw
            else:
                raise ValueError(
                    "at least 'start' or 'end' should be specified if a 'period' is given."
                    )
            wtupd__lkel = np.arange(b, ohv__agzv, umi__jhnuf, np.int64)
        else:
            periods = _dummy_convert_none_to_int(periods)
            cnzq__nmemh = txo__nnrlw.value - jhsb__nmv.value
            step = cnzq__nmemh / (periods - 1)
            phha__mmd = np.arange(0, periods, 1, np.float64)
            phha__mmd *= step
            phha__mmd += jhsb__nmv.value
            wtupd__lkel = phha__mmd.astype(np.int64)
            wtupd__lkel[-1] = txo__nnrlw.value
        if not fpd__ytsq and len(wtupd__lkel) and wtupd__lkel[0
            ] == jhsb__nmv.value:
            wtupd__lkel = wtupd__lkel[1:]
        if not liu__vkbp and len(wtupd__lkel) and wtupd__lkel[-1
            ] == txo__nnrlw.value:
            wtupd__lkel = wtupd__lkel[:-1]
        S = bodo.utils.conversion.convert_to_dt64ns(wtupd__lkel)
        return bodo.hiframes.pd_index_ext.init_timedelta_index(S, name)
    return f


@overload_method(DatetimeIndexType, 'isocalendar', inline='always',
    no_unliteral=True)
def overload_pd_timestamp_isocalendar(idx):

    def impl(idx):
        A = bodo.hiframes.pd_index_ext.get_index_data(idx)
        numba.parfors.parfor.init_prange()
        dnfp__knkq = len(A)
        zcb__ykul = bodo.libs.int_arr_ext.alloc_int_array(dnfp__knkq, np.uint32
            )
        nav__biu = bodo.libs.int_arr_ext.alloc_int_array(dnfp__knkq, np.uint32)
        qbvr__lfx = bodo.libs.int_arr_ext.alloc_int_array(dnfp__knkq, np.uint32
            )
        for i in numba.parfors.parfor.internal_prange(dnfp__knkq):
            if bodo.libs.array_kernels.isna(A, i):
                bodo.libs.array_kernels.setna(zcb__ykul, i)
                bodo.libs.array_kernels.setna(nav__biu, i)
                bodo.libs.array_kernels.setna(qbvr__lfx, i)
                continue
            zcb__ykul[i], nav__biu[i], qbvr__lfx[i
                ] = bodo.utils.conversion.box_if_dt64(A[i]).isocalendar()
        return bodo.hiframes.pd_dataframe_ext.init_dataframe((zcb__ykul,
            nav__biu, qbvr__lfx), idx, ('year', 'week', 'day'))
    return impl


class TimedeltaIndexType(types.IterableType, types.ArrayCompatible):

    def __init__(self, name_typ=None, data=None):
        name_typ = types.none if name_typ is None else name_typ
        self.name_typ = name_typ
        self.data = types.Array(bodo.timedelta64ns, 1, 'C'
            ) if data is None else data
        super(TimedeltaIndexType, self).__init__(name=
            f'TimedeltaIndexType({name_typ}, {self.data})')
    ndim = 1

    def copy(self):
        return TimedeltaIndexType(self.name_typ)

    @property
    def dtype(self):
        return types.NPTimedelta('ns')

    @property
    def as_array(self):
        return types.Array(types.undefined, 1, 'C')

    @property
    def key(self):
        return self.name_typ, self.data

    @property
    def iterator_type(self):
        return bodo.utils.typing.BodoArrayIterator(self)

    @property
    def pandas_type_name(self):
        return 'timedelta'

    @property
    def numpy_type_name(self):
        return 'timedelta64[ns]'


timedelta_index = TimedeltaIndexType()
types.timedelta_index = timedelta_index


@register_model(TimedeltaIndexType)
class TimedeltaIndexTypeModel(models.StructModel):

    def __init__(self, dmm, fe_type):
        zpl__dxgv = [('data', _timedelta_index_data_typ), ('name', fe_type.
            name_typ), ('dict', types.DictType(_timedelta_index_data_typ.
            dtype, types.int64))]
        super(TimedeltaIndexTypeModel, self).__init__(dmm, fe_type, zpl__dxgv)


@typeof_impl.register(pd.TimedeltaIndex)
def typeof_timedelta_index(val, c):
    return TimedeltaIndexType(get_val_type_maybe_str_literal(val.name))


@box(TimedeltaIndexType)
def box_timedelta_index(typ, val, c):
    jrfr__obcnn = c.context.insert_const_string(c.builder.module, 'pandas')
    fxnx__xzfzp = c.pyapi.import_module_noblock(jrfr__obcnn)
    timedelta_index = numba.core.cgutils.create_struct_proxy(typ)(c.context,
        c.builder, val)
    c.context.nrt.incref(c.builder, _timedelta_index_data_typ,
        timedelta_index.data)
    kcb__atfe = c.pyapi.from_native_value(_timedelta_index_data_typ,
        timedelta_index.data, c.env_manager)
    c.context.nrt.incref(c.builder, typ.name_typ, timedelta_index.name)
    phmv__rxy = c.pyapi.from_native_value(typ.name_typ, timedelta_index.
        name, c.env_manager)
    args = c.pyapi.tuple_pack([kcb__atfe])
    kws = c.pyapi.dict_pack([('name', phmv__rxy)])
    tgjqa__vooh = c.pyapi.object_getattr_string(fxnx__xzfzp, 'TimedeltaIndex')
    dohhm__xet = c.pyapi.call(tgjqa__vooh, args, kws)
    c.pyapi.decref(kcb__atfe)
    c.pyapi.decref(phmv__rxy)
    c.pyapi.decref(fxnx__xzfzp)
    c.pyapi.decref(tgjqa__vooh)
    c.pyapi.decref(args)
    c.pyapi.decref(kws)
    c.context.nrt.decref(c.builder, typ, val)
    return dohhm__xet


@unbox(TimedeltaIndexType)
def unbox_timedelta_index(typ, val, c):
    ztohz__wmzqv = c.pyapi.object_getattr_string(val, 'values')
    data = c.pyapi.to_native_value(_timedelta_index_data_typ, ztohz__wmzqv
        ).value
    phmv__rxy = c.pyapi.object_getattr_string(val, 'name')
    name = c.pyapi.to_native_value(typ.name_typ, phmv__rxy).value
    c.pyapi.decref(ztohz__wmzqv)
    c.pyapi.decref(phmv__rxy)
    zfq__oyglt = cgutils.create_struct_proxy(typ)(c.context, c.builder)
    zfq__oyglt.data = data
    zfq__oyglt.name = name
    dtype = _timedelta_index_data_typ.dtype
    hjz__uhuvd, rfc__acua = c.pyapi.call_jit_code(lambda : numba.typed.Dict
        .empty(dtype, types.int64), types.DictType(dtype, types.int64)(), [])
    zfq__oyglt.dict = rfc__acua
    return NativeValue(zfq__oyglt._getvalue())


@intrinsic
def init_timedelta_index(typingctx, data, name=None):
    name = types.none if name is None else name

    def codegen(context, builder, signature, args):
        pywrf__udxk, hsle__oro = args
        timedelta_index = cgutils.create_struct_proxy(signature.return_type)(
            context, builder)
        timedelta_index.data = pywrf__udxk
        timedelta_index.name = hsle__oro
        context.nrt.incref(builder, signature.args[0], pywrf__udxk)
        context.nrt.incref(builder, signature.args[1], hsle__oro)
        dtype = _timedelta_index_data_typ.dtype
        timedelta_index.dict = context.compile_internal(builder, lambda :
            numba.typed.Dict.empty(dtype, types.int64), types.DictType(
            dtype, types.int64)(), [])
        return timedelta_index._getvalue()
    dcwo__rfm = TimedeltaIndexType(name)
    sig = signature(dcwo__rfm, data, name)
    return sig, codegen


(ArrayAnalysis._analyze_op_call_bodo_hiframes_pd_index_ext_init_timedelta_index
    ) = init_index_equiv


@infer_getattr
class TimedeltaIndexAttribute(AttributeTemplate):
    key = TimedeltaIndexType

    def resolve_values(self, ary):
        return _timedelta_index_data_typ


make_attribute_wrapper(TimedeltaIndexType, 'data', '_data')
make_attribute_wrapper(TimedeltaIndexType, 'name', '_name')
make_attribute_wrapper(TimedeltaIndexType, 'dict', '_dict')


@overload_method(TimedeltaIndexType, 'copy', no_unliteral=True)
def overload_timedelta_index_copy(A, name=None, deep=False, dtype=None,
    names=None):
    yhqk__xya = dict(deep=deep, dtype=dtype, names=names)
    qanl__rehb = idx_typ_to_format_str_map[TimedeltaIndexType].format('copy()')
    check_unsupported_args('TimedeltaIndex.copy', yhqk__xya,
        idx_cpy_arg_defaults, fn_str=qanl__rehb, package_name='pandas',
        module_name='Index')
    if not is_overload_none(name):

        def impl(A, name=None, deep=False, dtype=None, names=None):
            return bodo.hiframes.pd_index_ext.init_timedelta_index(A._data.
                copy(), name)
    else:

        def impl(A, name=None, deep=False, dtype=None, names=None):
            return bodo.hiframes.pd_index_ext.init_timedelta_index(A._data.
                copy(), A._name)
    return impl


@overload_method(TimedeltaIndexType, 'min', inline='always', no_unliteral=True)
def overload_timedelta_index_min(tdi, axis=None, skipna=True):
    jruj__kdq = dict(axis=axis, skipna=skipna)
    ixdt__dtxi = dict(axis=None, skipna=True)
    check_unsupported_args('TimedeltaIndex.min', jruj__kdq, ixdt__dtxi,
        package_name='pandas', module_name='Index')

    def impl(tdi, axis=None, skipna=True):
        numba.parfors.parfor.init_prange()
        data = bodo.hiframes.pd_index_ext.get_index_data(tdi)
        dnfp__knkq = len(data)
        hrwxt__zqjht = numba.cpython.builtins.get_type_max_value(numba.core
            .types.int64)
        count = 0
        for i in numba.parfors.parfor.internal_prange(dnfp__knkq):
            if bodo.libs.array_kernels.isna(data, i):
                continue
            val = (bodo.hiframes.datetime_timedelta_ext.
                cast_numpy_timedelta_to_int(data[i]))
            count += 1
            hrwxt__zqjht = min(hrwxt__zqjht, val)
        syjf__cnd = bodo.hiframes.pd_timestamp_ext.integer_to_timedelta64(
            hrwxt__zqjht)
        return bodo.hiframes.pd_index_ext._tdi_val_finalize(syjf__cnd, count)
    return impl


@overload_method(TimedeltaIndexType, 'max', inline='always', no_unliteral=True)
def overload_timedelta_index_max(tdi, axis=None, skipna=True):
    jruj__kdq = dict(axis=axis, skipna=skipna)
    ixdt__dtxi = dict(axis=None, skipna=True)
    check_unsupported_args('TimedeltaIndex.max', jruj__kdq, ixdt__dtxi,
        package_name='pandas', module_name='Index')
    if not is_overload_none(axis) or not is_overload_true(skipna):
        raise BodoError(
            'Index.min(): axis and skipna arguments not supported yet')

    def impl(tdi, axis=None, skipna=True):
        numba.parfors.parfor.init_prange()
        data = bodo.hiframes.pd_index_ext.get_index_data(tdi)
        dnfp__knkq = len(data)
        qmn__vcw = numba.cpython.builtins.get_type_min_value(numba.core.
            types.int64)
        count = 0
        for i in numba.parfors.parfor.internal_prange(dnfp__knkq):
            if bodo.libs.array_kernels.isna(data, i):
                continue
            val = (bodo.hiframes.datetime_timedelta_ext.
                cast_numpy_timedelta_to_int(data[i]))
            count += 1
            qmn__vcw = max(qmn__vcw, val)
        syjf__cnd = bodo.hiframes.pd_timestamp_ext.integer_to_timedelta64(
            qmn__vcw)
        return bodo.hiframes.pd_index_ext._tdi_val_finalize(syjf__cnd, count)
    return impl


def gen_tdi_field_impl(field):
    zjcz__ohwiu = 'def impl(tdi):\n'
    zjcz__ohwiu += '    numba.parfors.parfor.init_prange()\n'
    zjcz__ohwiu += '    A = bodo.hiframes.pd_index_ext.get_index_data(tdi)\n'
    zjcz__ohwiu += (
        '    name = bodo.hiframes.pd_index_ext.get_index_name(tdi)\n')
    zjcz__ohwiu += '    n = len(A)\n'
    zjcz__ohwiu += '    S = np.empty(n, np.int64)\n'
    zjcz__ohwiu += '    for i in numba.parfors.parfor.internal_prange(n):\n'
    zjcz__ohwiu += (
        '        td64 = bodo.hiframes.pd_timestamp_ext.timedelta64_to_integer(A[i])\n'
        )
    if field == 'nanoseconds':
        zjcz__ohwiu += '        S[i] = td64 % 1000\n'
    elif field == 'microseconds':
        zjcz__ohwiu += '        S[i] = td64 // 1000 % 100000\n'
    elif field == 'seconds':
        zjcz__ohwiu += (
            '        S[i] = td64 // (1000 * 1000000) % (60 * 60 * 24)\n')
    elif field == 'days':
        zjcz__ohwiu += (
            '        S[i] = td64 // (1000 * 1000000 * 60 * 60 * 24)\n')
    else:
        assert False, 'invalid timedelta field'
    zjcz__ohwiu += (
        '    return bodo.hiframes.pd_index_ext.init_numeric_index(S, name)\n')
    flclc__rgw = {}
    exec(zjcz__ohwiu, {'numba': numba, 'np': np, 'bodo': bodo}, flclc__rgw)
    impl = flclc__rgw['impl']
    return impl


def _install_tdi_time_fields():
    for field in bodo.hiframes.pd_timestamp_ext.timedelta_fields:
        impl = gen_tdi_field_impl(field)
        overload_attribute(TimedeltaIndexType, field)(lambda tdi: impl)


_install_tdi_time_fields()


@overload(pd.TimedeltaIndex, no_unliteral=True)
def pd_timedelta_index_overload(data=None, unit=None, freq=None, dtype=None,
    copy=False, name=None):
    if is_overload_none(data):
        raise BodoError('data argument in pd.TimedeltaIndex() expected')
    jruj__kdq = dict(unit=unit, freq=freq, dtype=dtype, copy=copy)
    ixdt__dtxi = dict(unit=None, freq=None, dtype=None, copy=False)
    check_unsupported_args('pandas.TimedeltaIndex', jruj__kdq, ixdt__dtxi,
        package_name='pandas', module_name='Index')

    def impl(data=None, unit=None, freq=None, dtype=None, copy=False, name=None
        ):
        hykco__zkf = bodo.utils.conversion.coerce_to_array(data)
        S = bodo.utils.conversion.convert_to_td64ns(hykco__zkf)
        return bodo.hiframes.pd_index_ext.init_timedelta_index(S, name)
    return impl


class RangeIndexType(types.IterableType, types.ArrayCompatible):

    def __init__(self, name_typ=None):
        if name_typ is None:
            name_typ = types.none
        self.name_typ = name_typ
        super(RangeIndexType, self).__init__(name='RangeIndexType({})'.
            format(name_typ))
    ndim = 1

    @property
    def as_array(self):
        return types.Array(types.undefined, 1, 'C')

    def copy(self):
        return RangeIndexType(self.name_typ)

    @property
    def iterator_type(self):
        return types.iterators.RangeIteratorType(types.int64)

    @property
    def dtype(self):
        return types.int64

    @property
    def pandas_type_name(self):
        return str(self.dtype)

    @property
    def numpy_type_name(self):
        return str(self.dtype)

    def unify(self, typingctx, other):
        if isinstance(other, NumericIndexType):
            name_typ = self.name_typ.unify(typingctx, other.name_typ)
            if name_typ is None:
                name_typ = types.none
            return NumericIndexType(types.int64, name_typ)


@typeof_impl.register(pd.RangeIndex)
def typeof_pd_range_index(val, c):
    return RangeIndexType(get_val_type_maybe_str_literal(val.name))


@register_model(RangeIndexType)
class RangeIndexModel(models.StructModel):

    def __init__(self, dmm, fe_type):
        zpl__dxgv = [('start', types.int64), ('stop', types.int64), ('step',
            types.int64), ('name', fe_type.name_typ)]
        super(RangeIndexModel, self).__init__(dmm, fe_type, zpl__dxgv)


make_attribute_wrapper(RangeIndexType, 'start', '_start')
make_attribute_wrapper(RangeIndexType, 'stop', '_stop')
make_attribute_wrapper(RangeIndexType, 'step', '_step')
make_attribute_wrapper(RangeIndexType, 'name', '_name')


@overload_method(RangeIndexType, 'copy', no_unliteral=True)
def overload_range_index_copy(A, name=None, deep=False, dtype=None, names=None
    ):
    yhqk__xya = dict(deep=deep, dtype=dtype, names=names)
    qanl__rehb = idx_typ_to_format_str_map[RangeIndexType].format('copy()')
    check_unsupported_args('RangeIndex.copy', yhqk__xya,
        idx_cpy_arg_defaults, fn_str=qanl__rehb, package_name='pandas',
        module_name='Index')
    if not is_overload_none(name):

        def impl(A, name=None, deep=False, dtype=None, names=None):
            return bodo.hiframes.pd_index_ext.init_range_index(A._start, A.
                _stop, A._step, name)
    else:

        def impl(A, name=None, deep=False, dtype=None, names=None):
            return bodo.hiframes.pd_index_ext.init_range_index(A._start, A.
                _stop, A._step, A._name)
    return impl


@box(RangeIndexType)
def box_range_index(typ, val, c):
    jrfr__obcnn = c.context.insert_const_string(c.builder.module, 'pandas')
    strmv__rojx = c.pyapi.import_module_noblock(jrfr__obcnn)
    qxy__mbyrc = cgutils.create_struct_proxy(typ)(c.context, c.builder, val)
    ajvo__oui = c.pyapi.from_native_value(types.int64, qxy__mbyrc.start, c.
        env_manager)
    dyrdz__yrvab = c.pyapi.from_native_value(types.int64, qxy__mbyrc.stop,
        c.env_manager)
    nbmj__gpk = c.pyapi.from_native_value(types.int64, qxy__mbyrc.step, c.
        env_manager)
    c.context.nrt.incref(c.builder, typ.name_typ, qxy__mbyrc.name)
    phmv__rxy = c.pyapi.from_native_value(typ.name_typ, qxy__mbyrc.name, c.
        env_manager)
    args = c.pyapi.tuple_pack([ajvo__oui, dyrdz__yrvab, nbmj__gpk])
    kws = c.pyapi.dict_pack([('name', phmv__rxy)])
    tgjqa__vooh = c.pyapi.object_getattr_string(strmv__rojx, 'RangeIndex')
    qgy__igrq = c.pyapi.call(tgjqa__vooh, args, kws)
    c.pyapi.decref(ajvo__oui)
    c.pyapi.decref(dyrdz__yrvab)
    c.pyapi.decref(nbmj__gpk)
    c.pyapi.decref(phmv__rxy)
    c.pyapi.decref(strmv__rojx)
    c.pyapi.decref(tgjqa__vooh)
    c.pyapi.decref(args)
    c.pyapi.decref(kws)
    c.context.nrt.decref(c.builder, typ, val)
    return qgy__igrq


@intrinsic
def init_range_index(typingctx, start, stop, step, name=None):
    name = types.none if name is None else name

    def codegen(context, builder, signature, args):
        assert len(args) == 4
        qxy__mbyrc = cgutils.create_struct_proxy(signature.return_type)(context
            , builder)
        qxy__mbyrc.start = args[0]
        qxy__mbyrc.stop = args[1]
        qxy__mbyrc.step = args[2]
        qxy__mbyrc.name = args[3]
        context.nrt.incref(builder, signature.return_type.name_typ, args[3])
        return qxy__mbyrc._getvalue()
    return RangeIndexType(name)(start, stop, step, name), codegen


def init_range_index_equiv(self, scope, equiv_set, loc, args, kws):
    assert len(args) == 4 and not kws
    start, stop, step, fcuxg__nan = args
    if self.typemap[start.name] == types.IntegerLiteral(0) and self.typemap[
        step.name] == types.IntegerLiteral(1) and equiv_set.has_shape(stop):
        return ArrayAnalysis.AnalyzeResult(shape=stop, pre=[])
    return None


(ArrayAnalysis._analyze_op_call_bodo_hiframes_pd_index_ext_init_range_index
    ) = init_range_index_equiv


@unbox(RangeIndexType)
def unbox_range_index(typ, val, c):
    ajvo__oui = c.pyapi.object_getattr_string(val, 'start')
    start = c.pyapi.to_native_value(types.int64, ajvo__oui).value
    dyrdz__yrvab = c.pyapi.object_getattr_string(val, 'stop')
    stop = c.pyapi.to_native_value(types.int64, dyrdz__yrvab).value
    nbmj__gpk = c.pyapi.object_getattr_string(val, 'step')
    step = c.pyapi.to_native_value(types.int64, nbmj__gpk).value
    phmv__rxy = c.pyapi.object_getattr_string(val, 'name')
    name = c.pyapi.to_native_value(typ.name_typ, phmv__rxy).value
    c.pyapi.decref(ajvo__oui)
    c.pyapi.decref(dyrdz__yrvab)
    c.pyapi.decref(nbmj__gpk)
    c.pyapi.decref(phmv__rxy)
    qxy__mbyrc = cgutils.create_struct_proxy(typ)(c.context, c.builder)
    qxy__mbyrc.start = start
    qxy__mbyrc.stop = stop
    qxy__mbyrc.step = step
    qxy__mbyrc.name = name
    return NativeValue(qxy__mbyrc._getvalue())


@lower_constant(RangeIndexType)
def lower_constant_range_index(context, builder, ty, pyval):
    start = context.get_constant(types.int64, pyval.start)
    stop = context.get_constant(types.int64, pyval.stop)
    step = context.get_constant(types.int64, pyval.step)
    name = context.get_constant_generic(builder, ty.name_typ, pyval.name)
    return lir.Constant.literal_struct([start, stop, step, name])


@overload(pd.RangeIndex, no_unliteral=True, inline='always')
def range_index_overload(start=None, stop=None, step=None, dtype=None, copy
    =False, name=None):

    def _ensure_int_or_none(value, field):
        pjkfk__alftd = (
            'RangeIndex(...) must be called with integers, {value} was passed for {field}'
            )
        if not is_overload_none(value) and not isinstance(value, types.
            IntegerLiteral) and not isinstance(value, types.Integer):
            raise BodoError(pjkfk__alftd.format(value=value, field=field))
    _ensure_int_or_none(start, 'start')
    _ensure_int_or_none(stop, 'stop')
    _ensure_int_or_none(step, 'step')
    if is_overload_none(start) and is_overload_none(stop) and is_overload_none(
        step):
        pjkfk__alftd = 'RangeIndex(...) must be called with integers'
        raise BodoError(pjkfk__alftd)
    rwyh__pcfzu = 'start'
    kgbz__wjfp = 'stop'
    ede__dpfr = 'step'
    if is_overload_none(start):
        rwyh__pcfzu = '0'
    if is_overload_none(stop):
        kgbz__wjfp = 'start'
        rwyh__pcfzu = '0'
    if is_overload_none(step):
        ede__dpfr = '1'
    zjcz__ohwiu = """def _pd_range_index_imp(start=None, stop=None, step=None, dtype=None, copy=False, name=None):
"""
    zjcz__ohwiu += '  return init_range_index({}, {}, {}, name)\n'.format(
        rwyh__pcfzu, kgbz__wjfp, ede__dpfr)
    flclc__rgw = {}
    exec(zjcz__ohwiu, {'init_range_index': init_range_index}, flclc__rgw)
    rpbj__poabd = flclc__rgw['_pd_range_index_imp']
    return rpbj__poabd


@overload(pd.CategoricalIndex, no_unliteral=True, inline='always')
def categorical_index_overload(data=None, categories=None, ordered=None,
    dtype=None, copy=False, name=None):
    raise BodoError('pd.CategoricalIndex() initializer not yet supported.')


@overload_attribute(RangeIndexType, 'start')
def rangeIndex_get_start(ri):

    def impl(ri):
        return ri._start
    return impl


@overload_attribute(RangeIndexType, 'stop')
def rangeIndex_get_stop(ri):

    def impl(ri):
        return ri._stop
    return impl


@overload_attribute(RangeIndexType, 'step')
def rangeIndex_get_step(ri):

    def impl(ri):
        return ri._step
    return impl


@overload(operator.getitem, no_unliteral=True)
def overload_range_index_getitem(I, idx):
    if isinstance(I, RangeIndexType):
        if isinstance(types.unliteral(idx), types.Integer):
            return lambda I, idx: idx * I._step + I._start
        if isinstance(idx, types.SliceType):

            def impl(I, idx):
                pjij__haaa = numba.cpython.unicode._normalize_slice(idx, len(I)
                    )
                name = bodo.hiframes.pd_index_ext.get_index_name(I)
                start = I._start + I._step * pjij__haaa.start
                stop = I._start + I._step * pjij__haaa.stop
                step = I._step * pjij__haaa.step
                return bodo.hiframes.pd_index_ext.init_range_index(start,
                    stop, step, name)
            return impl
        return lambda I, idx: bodo.hiframes.pd_index_ext.init_numeric_index(np
            .arange(I._start, I._stop, I._step, np.int64)[idx], bodo.
            hiframes.pd_index_ext.get_index_name(I))


@overload(len, no_unliteral=True)
def overload_range_len(r):
    if isinstance(r, RangeIndexType):
        return lambda r: max(0, -(-(r._stop - r._start) // r._step))


class PeriodIndexType(types.IterableType, types.ArrayCompatible):

    def __init__(self, freq, name_typ=None):
        name_typ = types.none if name_typ is None else name_typ
        self.freq = freq
        self.name_typ = name_typ
        super(PeriodIndexType, self).__init__(name=
            'PeriodIndexType({}, {})'.format(freq, name_typ))
    ndim = 1

    @property
    def as_array(self):
        return types.Array(types.undefined, 1, 'C')

    def copy(self):
        return PeriodIndexType(self.freq, self.name_typ)

    @property
    def iterator_type(self):
        return bodo.utils.typing.BodoArrayIterator(self)

    @property
    def pandas_type_name(self):
        return 'object'

    @property
    def numpy_type_name(self):
        return f'period[{self.freq}]'


@typeof_impl.register(pd.PeriodIndex)
def typeof_pd_period_index(val, c):
    return PeriodIndexType(val.freqstr, get_val_type_maybe_str_literal(val.
        name))


@register_model(PeriodIndexType)
class PeriodIndexModel(models.StructModel):

    def __init__(self, dmm, fe_type):
        zpl__dxgv = [('data', bodo.IntegerArrayType(types.int64)), ('name',
            fe_type.name_typ), ('dict', types.DictType(types.int64, types.
            int64))]
        super(PeriodIndexModel, self).__init__(dmm, fe_type, zpl__dxgv)


make_attribute_wrapper(PeriodIndexType, 'data', '_data')
make_attribute_wrapper(PeriodIndexType, 'name', '_name')
make_attribute_wrapper(PeriodIndexType, 'dict', '_dict')


@overload_method(PeriodIndexType, 'copy', no_unliteral=True)
def overload_period_index_copy(A, name=None, deep=False, dtype=None, names=None
    ):
    freq = A.freq
    yhqk__xya = dict(deep=deep, dtype=dtype, names=names)
    qanl__rehb = idx_typ_to_format_str_map[PeriodIndexType].format('copy()')
    check_unsupported_args('PeriodIndex.copy', yhqk__xya,
        idx_cpy_arg_defaults, fn_str=qanl__rehb, package_name='pandas',
        module_name='Index')
    if not is_overload_none(name):

        def impl(A, name=None, deep=False, dtype=None, names=None):
            return bodo.hiframes.pd_index_ext.init_period_index(A._data.
                copy(), name, freq)
    else:

        def impl(A, name=None, deep=False, dtype=None, names=None):
            return bodo.hiframes.pd_index_ext.init_period_index(A._data.
                copy(), A._name, freq)
    return impl


@intrinsic
def init_period_index(typingctx, data, name, freq):
    name = types.none if name is None else name

    def codegen(context, builder, signature, args):
        pywrf__udxk, hsle__oro, fcuxg__nan = args
        dcki__omyox = signature.return_type
        ani__mshm = cgutils.create_struct_proxy(dcki__omyox)(context, builder)
        ani__mshm.data = pywrf__udxk
        ani__mshm.name = hsle__oro
        context.nrt.incref(builder, signature.args[0], args[0])
        context.nrt.incref(builder, signature.args[1], args[1])
        ani__mshm.dict = context.compile_internal(builder, lambda : numba.
            typed.Dict.empty(types.int64, types.int64), types.DictType(
            types.int64, types.int64)(), [])
        return ani__mshm._getvalue()
    veff__yizbc = get_overload_const_str(freq)
    dcwo__rfm = PeriodIndexType(veff__yizbc, name)
    sig = signature(dcwo__rfm, data, name, freq)
    return sig, codegen


@box(PeriodIndexType)
def box_period_index(typ, val, c):
    jrfr__obcnn = c.context.insert_const_string(c.builder.module, 'pandas')
    strmv__rojx = c.pyapi.import_module_noblock(jrfr__obcnn)
    zfq__oyglt = cgutils.create_struct_proxy(typ)(c.context, c.builder, val)
    c.context.nrt.incref(c.builder, bodo.IntegerArrayType(types.int64),
        zfq__oyglt.data)
    xtrdg__voi = c.pyapi.from_native_value(bodo.IntegerArrayType(types.
        int64), zfq__oyglt.data, c.env_manager)
    c.context.nrt.incref(c.builder, typ.name_typ, zfq__oyglt.name)
    phmv__rxy = c.pyapi.from_native_value(typ.name_typ, zfq__oyglt.name, c.
        env_manager)
    azngp__voaw = c.pyapi.string_from_constant_string(typ.freq)
    args = c.pyapi.tuple_pack([])
    kws = c.pyapi.dict_pack([('ordinal', xtrdg__voi), ('name', phmv__rxy),
        ('freq', azngp__voaw)])
    tgjqa__vooh = c.pyapi.object_getattr_string(strmv__rojx, 'PeriodIndex')
    qgy__igrq = c.pyapi.call(tgjqa__vooh, args, kws)
    c.pyapi.decref(xtrdg__voi)
    c.pyapi.decref(phmv__rxy)
    c.pyapi.decref(azngp__voaw)
    c.pyapi.decref(strmv__rojx)
    c.pyapi.decref(tgjqa__vooh)
    c.pyapi.decref(args)
    c.pyapi.decref(kws)
    c.context.nrt.decref(c.builder, typ, val)
    return qgy__igrq


@unbox(PeriodIndexType)
def unbox_period_index(typ, val, c):
    arr_typ = bodo.IntegerArrayType(types.int64)
    uhqz__mbzhp = c.pyapi.object_getattr_string(val, 'asi8')
    srwuo__lte = c.pyapi.call_method(val, 'isna', ())
    phmv__rxy = c.pyapi.object_getattr_string(val, 'name')
    name = c.pyapi.to_native_value(typ.name_typ, phmv__rxy).value
    jrfr__obcnn = c.context.insert_const_string(c.builder.module, 'pandas')
    fxnx__xzfzp = c.pyapi.import_module_noblock(jrfr__obcnn)
    cruws__tnumy = c.pyapi.object_getattr_string(fxnx__xzfzp, 'arrays')
    xtrdg__voi = c.pyapi.call_method(cruws__tnumy, 'IntegerArray', (
        uhqz__mbzhp, srwuo__lte))
    data = c.pyapi.to_native_value(arr_typ, xtrdg__voi).value
    c.pyapi.decref(uhqz__mbzhp)
    c.pyapi.decref(srwuo__lte)
    c.pyapi.decref(phmv__rxy)
    c.pyapi.decref(fxnx__xzfzp)
    c.pyapi.decref(cruws__tnumy)
    c.pyapi.decref(xtrdg__voi)
    zfq__oyglt = cgutils.create_struct_proxy(typ)(c.context, c.builder)
    zfq__oyglt.data = data
    zfq__oyglt.name = name
    hjz__uhuvd, rfc__acua = c.pyapi.call_jit_code(lambda : numba.typed.Dict
        .empty(types.int64, types.int64), types.DictType(types.int64, types
        .int64)(), [])
    zfq__oyglt.dict = rfc__acua
    return NativeValue(zfq__oyglt._getvalue())


class CategoricalIndexType(types.ArrayCompatible):

    def __init__(self, data, name_typ=None):
        from bodo.hiframes.pd_categorical_ext import CategoricalArrayType
        assert isinstance(data, CategoricalArrayType
            ), 'CategoricalIndexType expects CategoricalArrayType'
        name_typ = types.none if name_typ is None else name_typ
        self.name_typ = name_typ
        self.data = data
        super(CategoricalIndexType, self).__init__(name=
            f'CategoricalIndexType(data={self.data}, name={name_typ})')
    ndim = 1

    def copy(self):
        return CategoricalIndexType(self.data, self.name_typ)

    @property
    def as_array(self):
        return types.Array(types.undefined, 1, 'C')

    @property
    def dtype(self):
        return self.data.dtype

    @property
    def key(self):
        return self.data, self.name_typ

    @property
    def mangling_args(self):
        return self.__class__.__name__, (self._code,)

    @property
    def pandas_type_name(self):
        return 'categorical'

    @property
    def numpy_type_name(self):
        from bodo.hiframes.pd_categorical_ext import get_categories_int_type
        return str(get_categories_int_type(self.dtype))


@register_model(CategoricalIndexType)
class CategoricalIndexTypeModel(models.StructModel):

    def __init__(self, dmm, fe_type):
        from bodo.hiframes.pd_categorical_ext import get_categories_int_type
        pyga__uoibi = get_categories_int_type(fe_type.data.dtype)
        zpl__dxgv = [('data', fe_type.data), ('name', fe_type.name_typ), (
            'dict', types.DictType(pyga__uoibi, types.int64))]
        super(CategoricalIndexTypeModel, self).__init__(dmm, fe_type, zpl__dxgv
            )


@typeof_impl.register(pd.CategoricalIndex)
def typeof_categorical_index(val, c):
    return CategoricalIndexType(bodo.typeof(val.values),
        get_val_type_maybe_str_literal(val.name))


@box(CategoricalIndexType)
def box_categorical_index(typ, val, c):
    jrfr__obcnn = c.context.insert_const_string(c.builder.module, 'pandas')
    fxnx__xzfzp = c.pyapi.import_module_noblock(jrfr__obcnn)
    gpozj__rplts = numba.core.cgutils.create_struct_proxy(typ)(c.context, c
        .builder, val)
    c.context.nrt.incref(c.builder, typ.data, gpozj__rplts.data)
    kcb__atfe = c.pyapi.from_native_value(typ.data, gpozj__rplts.data, c.
        env_manager)
    c.context.nrt.incref(c.builder, typ.name_typ, gpozj__rplts.name)
    phmv__rxy = c.pyapi.from_native_value(typ.name_typ, gpozj__rplts.name,
        c.env_manager)
    args = c.pyapi.tuple_pack([kcb__atfe])
    kws = c.pyapi.dict_pack([('name', phmv__rxy)])
    tgjqa__vooh = c.pyapi.object_getattr_string(fxnx__xzfzp, 'CategoricalIndex'
        )
    dohhm__xet = c.pyapi.call(tgjqa__vooh, args, kws)
    c.pyapi.decref(kcb__atfe)
    c.pyapi.decref(phmv__rxy)
    c.pyapi.decref(fxnx__xzfzp)
    c.pyapi.decref(tgjqa__vooh)
    c.pyapi.decref(args)
    c.pyapi.decref(kws)
    c.context.nrt.decref(c.builder, typ, val)
    return dohhm__xet


@unbox(CategoricalIndexType)
def unbox_categorical_index(typ, val, c):
    from bodo.hiframes.pd_categorical_ext import get_categories_int_type
    ztohz__wmzqv = c.pyapi.object_getattr_string(val, 'values')
    data = c.pyapi.to_native_value(typ.data, ztohz__wmzqv).value
    phmv__rxy = c.pyapi.object_getattr_string(val, 'name')
    name = c.pyapi.to_native_value(typ.name_typ, phmv__rxy).value
    c.pyapi.decref(ztohz__wmzqv)
    c.pyapi.decref(phmv__rxy)
    zfq__oyglt = cgutils.create_struct_proxy(typ)(c.context, c.builder)
    zfq__oyglt.data = data
    zfq__oyglt.name = name
    dtype = get_categories_int_type(typ.data.dtype)
    hjz__uhuvd, rfc__acua = c.pyapi.call_jit_code(lambda : numba.typed.Dict
        .empty(dtype, types.int64), types.DictType(dtype, types.int64)(), [])
    zfq__oyglt.dict = rfc__acua
    return NativeValue(zfq__oyglt._getvalue())


@intrinsic
def init_categorical_index(typingctx, data, name=None):
    name = types.none if name is None else name

    def codegen(context, builder, signature, args):
        from bodo.hiframes.pd_categorical_ext import get_categories_int_type
        pywrf__udxk, hsle__oro = args
        gpozj__rplts = cgutils.create_struct_proxy(signature.return_type)(
            context, builder)
        gpozj__rplts.data = pywrf__udxk
        gpozj__rplts.name = hsle__oro
        context.nrt.incref(builder, signature.args[0], pywrf__udxk)
        context.nrt.incref(builder, signature.args[1], hsle__oro)
        dtype = get_categories_int_type(signature.return_type.data.dtype)
        gpozj__rplts.dict = context.compile_internal(builder, lambda :
            numba.typed.Dict.empty(dtype, types.int64), types.DictType(
            dtype, types.int64)(), [])
        return gpozj__rplts._getvalue()
    dcwo__rfm = CategoricalIndexType(data, name)
    sig = signature(dcwo__rfm, data, name)
    return sig, codegen


(ArrayAnalysis.
    _analyze_op_call_bodo_hiframes_pd_index_ext_init_categorical_index
    ) = init_index_equiv
make_attribute_wrapper(CategoricalIndexType, 'data', '_data')
make_attribute_wrapper(CategoricalIndexType, 'name', '_name')
make_attribute_wrapper(CategoricalIndexType, 'dict', '_dict')


@overload_method(CategoricalIndexType, 'copy', no_unliteral=True)
def overload_categorical_index_copy(A, name=None, deep=False, dtype=None,
    names=None):
    qanl__rehb = idx_typ_to_format_str_map[CategoricalIndexType].format(
        'copy()')
    yhqk__xya = dict(deep=deep, dtype=dtype, names=names)
    check_unsupported_args('CategoricalIndex.copy', yhqk__xya,
        idx_cpy_arg_defaults, fn_str=qanl__rehb, package_name='pandas',
        module_name='Index')
    if not is_overload_none(name):

        def impl(A, name=None, deep=False, dtype=None, names=None):
            return bodo.hiframes.pd_index_ext.init_categorical_index(A.
                _data.copy(), name)
    else:

        def impl(A, name=None, deep=False, dtype=None, names=None):
            return bodo.hiframes.pd_index_ext.init_categorical_index(A.
                _data.copy(), A._name)
    return impl


class IntervalIndexType(types.ArrayCompatible):

    def __init__(self, data, name_typ=None):
        from bodo.libs.interval_arr_ext import IntervalArrayType
        assert isinstance(data, IntervalArrayType
            ), 'IntervalIndexType expects IntervalArrayType'
        name_typ = types.none if name_typ is None else name_typ
        self.name_typ = name_typ
        self.data = data
        super(IntervalIndexType, self).__init__(name=
            f'IntervalIndexType(data={self.data}, name={name_typ})')
    ndim = 1

    def copy(self):
        return IntervalIndexType(self.data, self.name_typ)

    @property
    def as_array(self):
        return types.Array(types.undefined, 1, 'C')

    @property
    def key(self):
        return self.data, self.name_typ

    @property
    def mangling_args(self):
        return self.__class__.__name__, (self._code,)

    @property
    def pandas_type_name(self):
        return 'object'

    @property
    def numpy_type_name(self):
        return f'interval[{self.data.arr_type.dtype}, right]'


@register_model(IntervalIndexType)
class IntervalIndexTypeModel(models.StructModel):

    def __init__(self, dmm, fe_type):
        zpl__dxgv = [('data', fe_type.data), ('name', fe_type.name_typ), (
            'dict', types.DictType(types.UniTuple(fe_type.data.arr_type.
            dtype, 2), types.int64))]
        super(IntervalIndexTypeModel, self).__init__(dmm, fe_type, zpl__dxgv)


@typeof_impl.register(pd.IntervalIndex)
def typeof_interval_index(val, c):
    return IntervalIndexType(bodo.typeof(val.values),
        get_val_type_maybe_str_literal(val.name))


@box(IntervalIndexType)
def box_interval_index(typ, val, c):
    jrfr__obcnn = c.context.insert_const_string(c.builder.module, 'pandas')
    fxnx__xzfzp = c.pyapi.import_module_noblock(jrfr__obcnn)
    bwh__lct = numba.core.cgutils.create_struct_proxy(typ)(c.context, c.
        builder, val)
    c.context.nrt.incref(c.builder, typ.data, bwh__lct.data)
    kcb__atfe = c.pyapi.from_native_value(typ.data, bwh__lct.data, c.
        env_manager)
    c.context.nrt.incref(c.builder, typ.name_typ, bwh__lct.name)
    phmv__rxy = c.pyapi.from_native_value(typ.name_typ, bwh__lct.name, c.
        env_manager)
    args = c.pyapi.tuple_pack([kcb__atfe])
    kws = c.pyapi.dict_pack([('name', phmv__rxy)])
    tgjqa__vooh = c.pyapi.object_getattr_string(fxnx__xzfzp, 'IntervalIndex')
    dohhm__xet = c.pyapi.call(tgjqa__vooh, args, kws)
    c.pyapi.decref(kcb__atfe)
    c.pyapi.decref(phmv__rxy)
    c.pyapi.decref(fxnx__xzfzp)
    c.pyapi.decref(tgjqa__vooh)
    c.pyapi.decref(args)
    c.pyapi.decref(kws)
    c.context.nrt.decref(c.builder, typ, val)
    return dohhm__xet


@unbox(IntervalIndexType)
def unbox_interval_index(typ, val, c):
    ztohz__wmzqv = c.pyapi.object_getattr_string(val, 'values')
    data = c.pyapi.to_native_value(typ.data, ztohz__wmzqv).value
    phmv__rxy = c.pyapi.object_getattr_string(val, 'name')
    name = c.pyapi.to_native_value(typ.name_typ, phmv__rxy).value
    c.pyapi.decref(ztohz__wmzqv)
    c.pyapi.decref(phmv__rxy)
    zfq__oyglt = cgutils.create_struct_proxy(typ)(c.context, c.builder)
    zfq__oyglt.data = data
    zfq__oyglt.name = name
    dtype = types.UniTuple(typ.data.arr_type.dtype, 2)
    hjz__uhuvd, rfc__acua = c.pyapi.call_jit_code(lambda : numba.typed.Dict
        .empty(dtype, types.int64), types.DictType(dtype, types.int64)(), [])
    zfq__oyglt.dict = rfc__acua
    return NativeValue(zfq__oyglt._getvalue())


@intrinsic
def init_interval_index(typingctx, data, name=None):
    name = types.none if name is None else name

    def codegen(context, builder, signature, args):
        pywrf__udxk, hsle__oro = args
        bwh__lct = cgutils.create_struct_proxy(signature.return_type)(context,
            builder)
        bwh__lct.data = pywrf__udxk
        bwh__lct.name = hsle__oro
        context.nrt.incref(builder, signature.args[0], pywrf__udxk)
        context.nrt.incref(builder, signature.args[1], hsle__oro)
        dtype = types.UniTuple(data.arr_type.dtype, 2)
        bwh__lct.dict = context.compile_internal(builder, lambda : numba.
            typed.Dict.empty(dtype, types.int64), types.DictType(dtype,
            types.int64)(), [])
        return bwh__lct._getvalue()
    dcwo__rfm = IntervalIndexType(data, name)
    sig = signature(dcwo__rfm, data, name)
    return sig, codegen


(ArrayAnalysis._analyze_op_call_bodo_hiframes_pd_index_ext_init_interval_index
    ) = init_index_equiv
make_attribute_wrapper(IntervalIndexType, 'data', '_data')
make_attribute_wrapper(IntervalIndexType, 'name', '_name')
make_attribute_wrapper(IntervalIndexType, 'dict', '_dict')


class NumericIndexType(types.IterableType, types.ArrayCompatible):

    def __init__(self, dtype, name_typ=None, data=None):
        name_typ = types.none if name_typ is None else name_typ
        self.dtype = dtype
        self.name_typ = name_typ
        data = dtype_to_array_type(dtype) if data is None else data
        self.data = data
        super(NumericIndexType, self).__init__(name=
            f'NumericIndexType({dtype}, {name_typ}, {data})')
    ndim = 1

    @property
    def as_array(self):
        return types.Array(types.undefined, 1, 'C')

    def copy(self):
        return NumericIndexType(self.dtype, self.name_typ, self.data)

    @property
    def iterator_type(self):
        return bodo.utils.typing.BodoArrayIterator(self)

    @property
    def pandas_type_name(self):
        return str(self.dtype)

    @property
    def numpy_type_name(self):
        return str(self.dtype)


@typeof_impl.register(pd.Int64Index)
def typeof_pd_int64_index(val, c):
    return NumericIndexType(types.int64, get_val_type_maybe_str_literal(val
        .name))


@typeof_impl.register(pd.UInt64Index)
def typeof_pd_uint64_index(val, c):
    return NumericIndexType(types.uint64, get_val_type_maybe_str_literal(
        val.name))


@typeof_impl.register(pd.Float64Index)
def typeof_pd_float64_index(val, c):
    return NumericIndexType(types.float64, get_val_type_maybe_str_literal(
        val.name))


@register_model(NumericIndexType)
class NumericIndexModel(models.StructModel):

    def __init__(self, dmm, fe_type):
        zpl__dxgv = [('data', fe_type.data), ('name', fe_type.name_typ), (
            'dict', types.DictType(fe_type.dtype, types.int64))]
        super(NumericIndexModel, self).__init__(dmm, fe_type, zpl__dxgv)


make_attribute_wrapper(NumericIndexType, 'data', '_data')
make_attribute_wrapper(NumericIndexType, 'name', '_name')
make_attribute_wrapper(NumericIndexType, 'dict', '_dict')


@overload_method(NumericIndexType, 'copy', no_unliteral=True)
def overload_numeric_index_copy(A, name=None, deep=False, dtype=None, names
    =None):
    qanl__rehb = idx_typ_to_format_str_map[NumericIndexType].format('copy()')
    yhqk__xya = dict(deep=deep, dtype=dtype, names=names)
    check_unsupported_args('Index.copy', yhqk__xya, idx_cpy_arg_defaults,
        fn_str=qanl__rehb, package_name='pandas', module_name='Index')
    if not is_overload_none(name):

        def impl(A, name=None, deep=False, dtype=None, names=None):
            return bodo.hiframes.pd_index_ext.init_numeric_index(A._data.
                copy(), name)
    else:

        def impl(A, name=None, deep=False, dtype=None, names=None):
            return bodo.hiframes.pd_index_ext.init_numeric_index(A._data.
                copy(), A._name)
    return impl


@box(NumericIndexType)
def box_numeric_index(typ, val, c):
    jrfr__obcnn = c.context.insert_const_string(c.builder.module, 'pandas')
    strmv__rojx = c.pyapi.import_module_noblock(jrfr__obcnn)
    zfq__oyglt = cgutils.create_struct_proxy(typ)(c.context, c.builder, val)
    c.context.nrt.incref(c.builder, typ.data, zfq__oyglt.data)
    xtrdg__voi = c.pyapi.from_native_value(typ.data, zfq__oyglt.data, c.
        env_manager)
    c.context.nrt.incref(c.builder, typ.name_typ, zfq__oyglt.name)
    phmv__rxy = c.pyapi.from_native_value(typ.name_typ, zfq__oyglt.name, c.
        env_manager)
    siohz__hgs = c.pyapi.make_none()
    bbct__vsuk = c.pyapi.bool_from_bool(c.context.get_constant(types.bool_,
        False))
    qgy__igrq = c.pyapi.call_method(strmv__rojx, 'Index', (xtrdg__voi,
        siohz__hgs, bbct__vsuk, phmv__rxy))
    c.pyapi.decref(xtrdg__voi)
    c.pyapi.decref(siohz__hgs)
    c.pyapi.decref(bbct__vsuk)
    c.pyapi.decref(phmv__rxy)
    c.pyapi.decref(strmv__rojx)
    c.context.nrt.decref(c.builder, typ, val)
    return qgy__igrq


@intrinsic
def init_numeric_index(typingctx, data, name=None):
    name = types.none if is_overload_none(name) else name

    def codegen(context, builder, signature, args):
        assert len(args) == 2
        dcki__omyox = signature.return_type
        zfq__oyglt = cgutils.create_struct_proxy(dcki__omyox)(context, builder)
        zfq__oyglt.data = args[0]
        zfq__oyglt.name = args[1]
        context.nrt.incref(builder, dcki__omyox.data, args[0])
        context.nrt.incref(builder, dcki__omyox.name_typ, args[1])
        dtype = dcki__omyox.dtype
        zfq__oyglt.dict = context.compile_internal(builder, lambda : numba.
            typed.Dict.empty(dtype, types.int64), types.DictType(dtype,
            types.int64)(), [])
        return zfq__oyglt._getvalue()
    return NumericIndexType(data.dtype, name, data)(data, name), codegen


(ArrayAnalysis._analyze_op_call_bodo_hiframes_pd_index_ext_init_numeric_index
    ) = init_index_equiv


@unbox(NumericIndexType)
def unbox_numeric_index(typ, val, c):
    ztohz__wmzqv = c.pyapi.object_getattr_string(val, 'values')
    data = c.pyapi.to_native_value(typ.data, ztohz__wmzqv).value
    phmv__rxy = c.pyapi.object_getattr_string(val, 'name')
    name = c.pyapi.to_native_value(typ.name_typ, phmv__rxy).value
    c.pyapi.decref(ztohz__wmzqv)
    c.pyapi.decref(phmv__rxy)
    zfq__oyglt = cgutils.create_struct_proxy(typ)(c.context, c.builder)
    zfq__oyglt.data = data
    zfq__oyglt.name = name
    dtype = typ.dtype
    hjz__uhuvd, rfc__acua = c.pyapi.call_jit_code(lambda : numba.typed.Dict
        .empty(dtype, types.int64), types.DictType(dtype, types.int64)(), [])
    zfq__oyglt.dict = rfc__acua
    return NativeValue(zfq__oyglt._getvalue())


def create_numeric_constructor(func, func_str, default_dtype):

    def overload_impl(data=None, dtype=None, copy=False, name=None):
        howzn__wbp = dict(dtype=dtype)
        kycgj__borgk = dict(dtype=None)
        check_unsupported_args(func_str, howzn__wbp, kycgj__borgk,
            package_name='pandas', module_name='Index')
        if is_overload_false(copy):

            def impl(data=None, dtype=None, copy=False, name=None):
                hykco__zkf = bodo.utils.conversion.coerce_to_ndarray(data)
                rrg__ercqh = bodo.utils.conversion.fix_arr_dtype(hykco__zkf,
                    np.dtype(default_dtype))
                return bodo.hiframes.pd_index_ext.init_numeric_index(rrg__ercqh
                    , name)
        else:

            def impl(data=None, dtype=None, copy=False, name=None):
                hykco__zkf = bodo.utils.conversion.coerce_to_ndarray(data)
                if copy:
                    hykco__zkf = hykco__zkf.copy()
                rrg__ercqh = bodo.utils.conversion.fix_arr_dtype(hykco__zkf,
                    np.dtype(default_dtype))
                return bodo.hiframes.pd_index_ext.init_numeric_index(rrg__ercqh
                    , name)
        return impl
    return overload_impl


def _install_numeric_constructors():
    for func, func_str, default_dtype in ((pd.Int64Index,
        'pandas.Int64Index', np.int64), (pd.UInt64Index,
        'pandas.UInt64Index', np.uint64), (pd.Float64Index,
        'pandas.Float64Index', np.float64)):
        overload_impl = create_numeric_constructor(func, func_str,
            default_dtype)
        overload(func, no_unliteral=True)(overload_impl)


_install_numeric_constructors()


class StringIndexType(types.IterableType, types.ArrayCompatible):

    def __init__(self, name_typ=None, data_typ=None):
        name_typ = types.none if name_typ is None else name_typ
        self.name_typ = name_typ
        self.data = string_array_type if data_typ is None else data_typ
        super(StringIndexType, self).__init__(name=
            f'StringIndexType({name_typ}, {self.data})')
    ndim = 1

    @property
    def as_array(self):
        return types.Array(types.undefined, 1, 'C')

    def copy(self):
        return StringIndexType(self.name_typ, self.data)

    @property
    def dtype(self):
        return string_type

    @property
    def pandas_type_name(self):
        return 'unicode'

    @property
    def numpy_type_name(self):
        return 'object'

    @property
    def iterator_type(self):
        return bodo.utils.typing.BodoArrayIterator(self)


@register_model(StringIndexType)
class StringIndexModel(models.StructModel):

    def __init__(self, dmm, fe_type):
        zpl__dxgv = [('data', fe_type.data), ('name', fe_type.name_typ), (
            'dict', types.DictType(string_type, types.int64))]
        super(StringIndexModel, self).__init__(dmm, fe_type, zpl__dxgv)


make_attribute_wrapper(StringIndexType, 'data', '_data')
make_attribute_wrapper(StringIndexType, 'name', '_name')
make_attribute_wrapper(StringIndexType, 'dict', '_dict')


class BinaryIndexType(types.IterableType, types.ArrayCompatible):

    def __init__(self, name_typ=None, data_typ=None):
        assert data_typ is None or data_typ == binary_array_type, 'data_typ must be binary_array_type'
        name_typ = types.none if name_typ is None else name_typ
        self.name_typ = name_typ
        self.data = binary_array_type
        super(BinaryIndexType, self).__init__(name='BinaryIndexType({})'.
            format(name_typ))
    ndim = 1

    @property
    def as_array(self):
        return types.Array(types.undefined, 1, 'C')

    def copy(self):
        return BinaryIndexType(self.name_typ)

    @property
    def dtype(self):
        return bytes_type

    @property
    def pandas_type_name(self):
        return 'bytes'

    @property
    def numpy_type_name(self):
        return 'object'

    @property
    def iterator_type(self):
        return bodo.utils.typing.BodoArrayIterator(self)


@register_model(BinaryIndexType)
class BinaryIndexModel(models.StructModel):

    def __init__(self, dmm, fe_type):
        zpl__dxgv = [('data', binary_array_type), ('name', fe_type.name_typ
            ), ('dict', types.DictType(bytes_type, types.int64))]
        super(BinaryIndexModel, self).__init__(dmm, fe_type, zpl__dxgv)


make_attribute_wrapper(BinaryIndexType, 'data', '_data')
make_attribute_wrapper(BinaryIndexType, 'name', '_name')
make_attribute_wrapper(BinaryIndexType, 'dict', '_dict')


@unbox(BinaryIndexType)
@unbox(StringIndexType)
def unbox_binary_str_index(typ, val, c):
    mnw__gpdpw = typ.data
    scalar_type = typ.data.dtype
    ztohz__wmzqv = c.pyapi.object_getattr_string(val, 'values')
    data = c.pyapi.to_native_value(mnw__gpdpw, ztohz__wmzqv).value
    phmv__rxy = c.pyapi.object_getattr_string(val, 'name')
    name = c.pyapi.to_native_value(typ.name_typ, phmv__rxy).value
    c.pyapi.decref(ztohz__wmzqv)
    c.pyapi.decref(phmv__rxy)
    zfq__oyglt = cgutils.create_struct_proxy(typ)(c.context, c.builder)
    zfq__oyglt.data = data
    zfq__oyglt.name = name
    hjz__uhuvd, rfc__acua = c.pyapi.call_jit_code(lambda : numba.typed.Dict
        .empty(scalar_type, types.int64), types.DictType(scalar_type, types
        .int64)(), [])
    zfq__oyglt.dict = rfc__acua
    return NativeValue(zfq__oyglt._getvalue())


@box(BinaryIndexType)
@box(StringIndexType)
def box_binary_str_index(typ, val, c):
    mnw__gpdpw = typ.data
    jrfr__obcnn = c.context.insert_const_string(c.builder.module, 'pandas')
    strmv__rojx = c.pyapi.import_module_noblock(jrfr__obcnn)
    zfq__oyglt = cgutils.create_struct_proxy(typ)(c.context, c.builder, val)
    c.context.nrt.incref(c.builder, mnw__gpdpw, zfq__oyglt.data)
    xtrdg__voi = c.pyapi.from_native_value(mnw__gpdpw, zfq__oyglt.data, c.
        env_manager)
    c.context.nrt.incref(c.builder, typ.name_typ, zfq__oyglt.name)
    phmv__rxy = c.pyapi.from_native_value(typ.name_typ, zfq__oyglt.name, c.
        env_manager)
    siohz__hgs = c.pyapi.make_none()
    bbct__vsuk = c.pyapi.bool_from_bool(c.context.get_constant(types.bool_,
        False))
    qgy__igrq = c.pyapi.call_method(strmv__rojx, 'Index', (xtrdg__voi,
        siohz__hgs, bbct__vsuk, phmv__rxy))
    c.pyapi.decref(xtrdg__voi)
    c.pyapi.decref(siohz__hgs)
    c.pyapi.decref(bbct__vsuk)
    c.pyapi.decref(phmv__rxy)
    c.pyapi.decref(strmv__rojx)
    c.context.nrt.decref(c.builder, typ, val)
    return qgy__igrq


@intrinsic
def init_binary_str_index(typingctx, data, name=None):
    name = types.none if name is None else name
    sig = type(bodo.utils.typing.get_index_type_from_dtype(data.dtype))(name,
        data)(data, name)
    lsuj__sle = get_binary_str_codegen(is_binary=data.dtype == bytes_type)
    return sig, lsuj__sle


(ArrayAnalysis.
    _analyze_op_call_bodo_hiframes_pd_index_ext_init_binary_str_index
    ) = init_index_equiv


def get_binary_str_codegen(is_binary=False):
    if is_binary:
        pxmjk__ucx = 'bytes_type'
    else:
        pxmjk__ucx = 'string_type'
    zjcz__ohwiu = 'def impl(context, builder, signature, args):\n'
    zjcz__ohwiu += '    assert len(args) == 2\n'
    zjcz__ohwiu += '    index_typ = signature.return_type\n'
    zjcz__ohwiu += (
        '    index_val = cgutils.create_struct_proxy(index_typ)(context, builder)\n'
        )
    zjcz__ohwiu += '    index_val.data = args[0]\n'
    zjcz__ohwiu += '    index_val.name = args[1]\n'
    zjcz__ohwiu += '    # increase refcount of stored values\n'
    zjcz__ohwiu += (
        '    context.nrt.incref(builder, signature.args[0], args[0])\n')
    zjcz__ohwiu += (
        '    context.nrt.incref(builder, index_typ.name_typ, args[1])\n')
    zjcz__ohwiu += '    # create empty dict for get_loc hashmap\n'
    zjcz__ohwiu += '    index_val.dict = context.compile_internal(\n'
    zjcz__ohwiu += '       builder,\n'
    zjcz__ohwiu += (
        f'       lambda: numba.typed.Dict.empty({pxmjk__ucx}, types.int64),\n')
    zjcz__ohwiu += (
        f'        types.DictType({pxmjk__ucx}, types.int64)(), [],)\n')
    zjcz__ohwiu += '    return index_val._getvalue()\n'
    flclc__rgw = {}
    exec(zjcz__ohwiu, {'bodo': bodo, 'signature': signature, 'cgutils':
        cgutils, 'numba': numba, 'types': types, 'bytes_type': bytes_type,
        'string_type': string_type}, flclc__rgw)
    impl = flclc__rgw['impl']
    return impl


@overload_method(BinaryIndexType, 'copy', no_unliteral=True)
@overload_method(StringIndexType, 'copy', no_unliteral=True)
def overload_binary_string_index_copy(A, name=None, deep=False, dtype=None,
    names=None):
    typ = type(A)
    qanl__rehb = idx_typ_to_format_str_map[typ].format('copy()')
    yhqk__xya = dict(deep=deep, dtype=dtype, names=names)
    check_unsupported_args('Index.copy', yhqk__xya, idx_cpy_arg_defaults,
        fn_str=qanl__rehb, package_name='pandas', module_name='Index')
    if not is_overload_none(name):

        def impl(A, name=None, deep=False, dtype=None, names=None):
            return bodo.hiframes.pd_index_ext.init_binary_str_index(A._data
                .copy(), name)
    else:

        def impl(A, name=None, deep=False, dtype=None, names=None):
            return bodo.hiframes.pd_index_ext.init_binary_str_index(A._data
                .copy(), A._name)
    return impl


@overload_attribute(BinaryIndexType, 'name')
@overload_attribute(StringIndexType, 'name')
@overload_attribute(DatetimeIndexType, 'name')
@overload_attribute(TimedeltaIndexType, 'name')
@overload_attribute(RangeIndexType, 'name')
@overload_attribute(PeriodIndexType, 'name')
@overload_attribute(NumericIndexType, 'name')
@overload_attribute(IntervalIndexType, 'name')
@overload_attribute(CategoricalIndexType, 'name')
@overload_attribute(MultiIndexType, 'name')
def Index_get_name(i):

    def impl(i):
        return i._name
    return impl


@overload(operator.getitem, no_unliteral=True)
def overload_index_getitem(I, ind):
    if isinstance(I, (NumericIndexType, StringIndexType, BinaryIndexType)
        ) and isinstance(ind, types.Integer):
        return lambda I, ind: bodo.hiframes.pd_index_ext.get_index_data(I)[ind]
    if isinstance(I, NumericIndexType):
        return lambda I, ind: bodo.hiframes.pd_index_ext.init_numeric_index(
            bodo.hiframes.pd_index_ext.get_index_data(I)[ind], bodo.
            hiframes.pd_index_ext.get_index_name(I))
    if isinstance(I, (StringIndexType, BinaryIndexType)):
        return lambda I, ind: bodo.hiframes.pd_index_ext.init_binary_str_index(
            bodo.hiframes.pd_index_ext.get_index_data(I)[ind], bodo.
            hiframes.pd_index_ext.get_index_name(I))


def array_type_to_index(arr_typ, name_typ=None):
    if is_str_arr_type(arr_typ):
        return StringIndexType(name_typ, arr_typ)
    if arr_typ == bodo.binary_array_type:
        return BinaryIndexType(name_typ)
    assert isinstance(arr_typ, (types.Array, IntegerArrayType, bodo.
        CategoricalArrayType)) or arr_typ in (bodo.datetime_date_array_type,
        bodo.boolean_array
        ), f'Converting array type {arr_typ} to index not supported'
    if (arr_typ == bodo.datetime_date_array_type or arr_typ.dtype == types.
        NPDatetime('ns')):
        return DatetimeIndexType(name_typ)
    if isinstance(arr_typ, bodo.DatetimeArrayType):
        return DatetimeIndexType(name_typ, arr_typ)
    if isinstance(arr_typ, bodo.CategoricalArrayType):
        return CategoricalIndexType(arr_typ, name_typ)
    if arr_typ.dtype == types.NPTimedelta('ns'):
        return TimedeltaIndexType(name_typ)
    if isinstance(arr_typ.dtype, (types.Integer, types.Float, types.Boolean)):
        return NumericIndexType(arr_typ.dtype, name_typ, arr_typ)
    raise BodoError(f'invalid index type {arr_typ}')


def is_pd_index_type(t):
    return isinstance(t, (NumericIndexType, DatetimeIndexType,
        TimedeltaIndexType, IntervalIndexType, CategoricalIndexType,
        PeriodIndexType, StringIndexType, BinaryIndexType, RangeIndexType,
        HeterogeneousIndexType))


@overload_method(RangeIndexType, 'take', no_unliteral=True)
@overload_method(NumericIndexType, 'take', no_unliteral=True)
@overload_method(StringIndexType, 'take', no_unliteral=True)
@overload_method(BinaryIndexType, 'take', no_unliteral=True)
@overload_method(CategoricalIndexType, 'take', no_unliteral=True)
@overload_method(PeriodIndexType, 'take', no_unliteral=True)
@overload_method(DatetimeIndexType, 'take', no_unliteral=True)
@overload_method(TimedeltaIndexType, 'take', no_unliteral=True)
def overload_index_take(I, indices, axis=0, allow_fill=True, fill_value=None):
    jruj__kdq = dict(axis=axis, allow_fill=allow_fill, fill_value=fill_value)
    gfy__rcw = dict(axis=0, allow_fill=True, fill_value=None)
    check_unsupported_args('Index.take', jruj__kdq, gfy__rcw, package_name=
        'pandas', module_name='Index')
    return lambda I, indices: I[indices]


@numba.njit(no_cpython_wrapper=True)
def _init_engine(I):
    if len(I) > 0 and not I._dict:
        wtupd__lkel = bodo.utils.conversion.coerce_to_array(I)
        for i in range(len(wtupd__lkel)):
            val = wtupd__lkel[i]
            if val in I._dict:
                raise ValueError(
                    'Index.get_loc(): non-unique Index not supported yet')
            I._dict[val] = i


@overload(operator.contains, no_unliteral=True)
def index_contains(I, val):
    if not is_index_type(I):
        return
    if isinstance(I, RangeIndexType):
        return lambda I, val: range_contains(I.start, I.stop, I.step, val)

    def impl(I, val):
        key = bodo.utils.conversion.unbox_if_timestamp(val)
        if not is_null_value(I._dict):
            _init_engine(I)
            return key in I._dict
        else:
            pjkfk__alftd = (
                'Global Index objects can be slow (pass as argument to JIT function for better performance).'
                )
            warnings.warn(pjkfk__alftd)
            wtupd__lkel = bodo.utils.conversion.coerce_to_array(I)
            ind = -1
            for i in range(len(wtupd__lkel)):
                if wtupd__lkel[i] == key:
                    if ind != -1:
                        raise ValueError(
                            'Index.get_loc(): non-unique Index not supported yet'
                            )
                    ind = i
        return ind != -1
    return impl


@register_jitable
def range_contains(start, stop, step, val):
    if step > 0 and not start <= val < stop:
        return False
    if step < 0 and not stop <= val < start:
        return False
    return (val - start) % step == 0


@overload_method(RangeIndexType, 'get_loc', no_unliteral=True)
@overload_method(NumericIndexType, 'get_loc', no_unliteral=True)
@overload_method(StringIndexType, 'get_loc', no_unliteral=True)
@overload_method(BinaryIndexType, 'get_loc', no_unliteral=True)
@overload_method(PeriodIndexType, 'get_loc', no_unliteral=True)
@overload_method(DatetimeIndexType, 'get_loc', no_unliteral=True)
@overload_method(TimedeltaIndexType, 'get_loc', no_unliteral=True)
def overload_index_get_loc(I, key, method=None, tolerance=None):
    jruj__kdq = dict(method=method, tolerance=tolerance)
    ixdt__dtxi = dict(method=None, tolerance=None)
    check_unsupported_args('Index.get_loc', jruj__kdq, ixdt__dtxi,
        package_name='pandas', module_name='Index')
    key = types.unliteral(key)
    bodo.hiframes.pd_timestamp_ext.check_tz_aware_unsupported(I,
        'DatetimeIndex.get_loc')
    if key == pd_timestamp_type:
        key = bodo.datetime64ns
    if key == pd_timedelta_type:
        key = bodo.timedelta64ns
    if key != I.dtype:
        raise_bodo_error(
            'Index.get_loc(): invalid label type in Index.get_loc()')
    if isinstance(I, RangeIndexType):

        def impl_range(I, key, method=None, tolerance=None):
            if not range_contains(I.start, I.stop, I.step, key):
                raise KeyError('Index.get_loc(): key not found')
            return key - I.start if I.step == 1 else (key - I.start) // I.step
        return impl_range

    def impl(I, key, method=None, tolerance=None):
        key = bodo.utils.conversion.unbox_if_timestamp(key)
        if not is_null_value(I._dict):
            _init_engine(I)
            ind = I._dict.get(key, -1)
        else:
            pjkfk__alftd = (
                'Index.get_loc() can be slow for global Index objects (pass as argument to JIT function for better performance).'
                )
            warnings.warn(pjkfk__alftd)
            wtupd__lkel = bodo.utils.conversion.coerce_to_array(I)
            ind = -1
            for i in range(len(wtupd__lkel)):
                if wtupd__lkel[i] == key:
                    if ind != -1:
                        raise ValueError(
                            'Index.get_loc(): non-unique Index not supported yet'
                            )
                    ind = i
        if ind == -1:
            raise KeyError('Index.get_loc(): key not found')
        return ind
    return impl


def create_isna_specific_method(overload_name):

    def overload_index_isna_specific_method(I):
        dpji__lriys = overload_name in {'isna', 'isnull'}
        if isinstance(I, RangeIndexType):

            def impl(I):
                numba.parfors.parfor.init_prange()
                dnfp__knkq = len(I)
                fodqq__bgo = np.empty(dnfp__knkq, np.bool_)
                for i in numba.parfors.parfor.internal_prange(dnfp__knkq):
                    fodqq__bgo[i] = not dpji__lriys
                return fodqq__bgo
            return impl
        zjcz__ohwiu = f"""def impl(I):
    numba.parfors.parfor.init_prange()
    arr = bodo.hiframes.pd_index_ext.get_index_data(I)
    n = len(arr)
    out_arr = np.empty(n, np.bool_)
    for i in numba.parfors.parfor.internal_prange(n):
       out_arr[i] = {'' if dpji__lriys else 'not '}bodo.libs.array_kernels.isna(arr, i)
    return out_arr
"""
        flclc__rgw = {}
        exec(zjcz__ohwiu, {'bodo': bodo, 'np': np, 'numba': numba}, flclc__rgw)
        impl = flclc__rgw['impl']
        return impl
    return overload_index_isna_specific_method


isna_overload_types = (RangeIndexType, NumericIndexType, StringIndexType,
    BinaryIndexType, CategoricalIndexType, PeriodIndexType,
    DatetimeIndexType, TimedeltaIndexType)
isna_specific_methods = 'isna', 'notna', 'isnull', 'notnull'


def _install_isna_specific_methods():
    for yhsau__epvui in isna_overload_types:
        for overload_name in isna_specific_methods:
            overload_impl = create_isna_specific_method(overload_name)
            overload_method(yhsau__epvui, overload_name, no_unliteral=True,
                inline='always')(overload_impl)


_install_isna_specific_methods()


@overload_attribute(RangeIndexType, 'values')
@overload_attribute(NumericIndexType, 'values')
@overload_attribute(StringIndexType, 'values')
@overload_attribute(BinaryIndexType, 'values')
@overload_attribute(CategoricalIndexType, 'values')
@overload_attribute(PeriodIndexType, 'values')
@overload_attribute(DatetimeIndexType, 'values')
@overload_attribute(TimedeltaIndexType, 'values')
def overload_values(I):
    bodo.hiframes.pd_timestamp_ext.check_tz_aware_unsupported(I, 'Index.values'
        )
    return lambda I: bodo.utils.conversion.coerce_to_array(I)


@overload(len, no_unliteral=True)
def overload_index_len(I):
    if isinstance(I, (NumericIndexType, StringIndexType, BinaryIndexType,
        PeriodIndexType, IntervalIndexType, CategoricalIndexType,
        DatetimeIndexType, TimedeltaIndexType, HeterogeneousIndexType)):
        return lambda I: len(bodo.hiframes.pd_index_ext.get_index_data(I))


@overload_attribute(DatetimeIndexType, 'shape')
@overload_attribute(NumericIndexType, 'shape')
@overload_attribute(StringIndexType, 'shape')
@overload_attribute(BinaryIndexType, 'shape')
@overload_attribute(PeriodIndexType, 'shape')
@overload_attribute(TimedeltaIndexType, 'shape')
@overload_attribute(IntervalIndexType, 'shape')
@overload_attribute(CategoricalIndexType, 'shape')
def overload_index_shape(s):
    return lambda s: (len(bodo.hiframes.pd_index_ext.get_index_data(s)),)


@overload_attribute(RangeIndexType, 'shape')
def overload_range_index_shape(s):
    return lambda s: (len(s),)


@overload_attribute(NumericIndexType, 'is_monotonic', inline='always')
@overload_attribute(RangeIndexType, 'is_monotonic', inline='always')
@overload_attribute(DatetimeIndexType, 'is_monotonic', inline='always')
@overload_attribute(TimedeltaIndexType, 'is_monotonic', inline='always')
@overload_attribute(NumericIndexType, 'is_monotonic_increasing', inline=
    'always')
@overload_attribute(RangeIndexType, 'is_monotonic_increasing', inline='always')
@overload_attribute(DatetimeIndexType, 'is_monotonic_increasing', inline=
    'always')
@overload_attribute(TimedeltaIndexType, 'is_monotonic_increasing', inline=
    'always')
def overload_index_is_montonic(I):
    bodo.hiframes.pd_timestamp_ext.check_tz_aware_unsupported(I,
        'Index.is_monotonic_increasing')
    if isinstance(I, (NumericIndexType, DatetimeIndexType, TimedeltaIndexType)
        ):

        def impl(I):
            wtupd__lkel = bodo.hiframes.pd_index_ext.get_index_data(I)
            return bodo.libs.array_kernels.series_monotonicity(wtupd__lkel, 1)
        return impl
    elif isinstance(I, RangeIndexType):

        def impl(I):
            return I._step > 0 or len(I) <= 1
        return impl


@overload_attribute(NumericIndexType, 'is_monotonic_decreasing', inline=
    'always')
@overload_attribute(RangeIndexType, 'is_monotonic_decreasing', inline='always')
@overload_attribute(DatetimeIndexType, 'is_monotonic_decreasing', inline=
    'always')
@overload_attribute(TimedeltaIndexType, 'is_monotonic_decreasing', inline=
    'always')
def overload_index_is_montonic_decreasing(I):
    bodo.hiframes.pd_timestamp_ext.check_tz_aware_unsupported(I,
        'Index.is_monotonic_decreasing')
    if isinstance(I, (NumericIndexType, DatetimeIndexType, TimedeltaIndexType)
        ):

        def impl(I):
            wtupd__lkel = bodo.hiframes.pd_index_ext.get_index_data(I)
            return bodo.libs.array_kernels.series_monotonicity(wtupd__lkel, 2)
        return impl
    elif isinstance(I, RangeIndexType):

        def impl(I):
            return I._step < 0 or len(I) <= 1
        return impl


@overload_method(NumericIndexType, 'duplicated', inline='always',
    no_unliteral=True)
@overload_method(DatetimeIndexType, 'duplicated', inline='always',
    no_unliteral=True)
@overload_method(TimedeltaIndexType, 'duplicated', inline='always',
    no_unliteral=True)
@overload_method(StringIndexType, 'duplicated', inline='always',
    no_unliteral=True)
@overload_method(PeriodIndexType, 'duplicated', inline='always',
    no_unliteral=True)
@overload_method(CategoricalIndexType, 'duplicated', inline='always',
    no_unliteral=True)
@overload_method(BinaryIndexType, 'duplicated', inline='always',
    no_unliteral=True)
@overload_method(RangeIndexType, 'duplicated', inline='always',
    no_unliteral=True)
def overload_index_duplicated(I, keep='first'):
    if isinstance(I, RangeIndexType):

        def impl(I, keep='first'):
            return np.zeros(len(I), np.bool_)
        return impl

    def impl(I, keep='first'):
        wtupd__lkel = bodo.hiframes.pd_index_ext.get_index_data(I)
        fodqq__bgo = bodo.libs.array_kernels.duplicated((wtupd__lkel,))
        return fodqq__bgo
    return impl


@overload_method(RangeIndexType, 'drop_duplicates', no_unliteral=True,
    inline='always')
@overload_method(NumericIndexType, 'drop_duplicates', no_unliteral=True,
    inline='always')
@overload_method(StringIndexType, 'drop_duplicates', no_unliteral=True,
    inline='always')
@overload_method(BinaryIndexType, 'drop_duplicates', no_unliteral=True,
    inline='always')
@overload_method(CategoricalIndexType, 'drop_duplicates', no_unliteral=True,
    inline='always')
@overload_method(PeriodIndexType, 'drop_duplicates', no_unliteral=True,
    inline='always')
@overload_method(DatetimeIndexType, 'drop_duplicates', no_unliteral=True,
    inline='always')
@overload_method(TimedeltaIndexType, 'drop_duplicates', no_unliteral=True,
    inline='always')
def overload_index_drop_duplicates(I, keep='first'):
    jruj__kdq = dict(keep=keep)
    ixdt__dtxi = dict(keep='first')
    check_unsupported_args('Index.drop_duplicates', jruj__kdq, ixdt__dtxi,
        package_name='pandas', module_name='Index')
    if isinstance(I, RangeIndexType):
        return lambda I, keep='first': I.copy()
    zjcz__ohwiu = """def impl(I, keep='first'):
    data = bodo.hiframes.pd_index_ext.get_index_data(I)
    arr = bodo.libs.array_kernels.drop_duplicates_array(data)
    name = bodo.hiframes.pd_index_ext.get_index_name(I)
"""
    if isinstance(I, PeriodIndexType):
        zjcz__ohwiu += f"""    return bodo.hiframes.pd_index_ext.init_period_index(arr, name, '{I.freq}')
"""
    else:
        zjcz__ohwiu += (
            '    return bodo.utils.conversion.index_from_array(arr, name)')
    flclc__rgw = {}
    exec(zjcz__ohwiu, {'bodo': bodo}, flclc__rgw)
    impl = flclc__rgw['impl']
    return impl


@numba.generated_jit(nopython=True)
def get_index_data(S):
    return lambda S: S._data


@numba.generated_jit(nopython=True)
def get_index_name(S):
    return lambda S: S._name


def alias_ext_dummy_func(lhs_name, args, alias_map, arg_aliases):
    assert len(args) >= 1
    numba.core.ir_utils._add_alias(lhs_name, args[0].name, alias_map,
        arg_aliases)


numba.core.ir_utils.alias_func_extensions['get_index_data',
    'bodo.hiframes.pd_index_ext'] = alias_ext_dummy_func
numba.core.ir_utils.alias_func_extensions['init_datetime_index',
    'bodo.hiframes.pd_index_ext'] = alias_ext_dummy_func
numba.core.ir_utils.alias_func_extensions['init_timedelta_index',
    'bodo.hiframes.pd_index_ext'] = alias_ext_dummy_func
numba.core.ir_utils.alias_func_extensions['init_numeric_index',
    'bodo.hiframes.pd_index_ext'] = alias_ext_dummy_func
numba.core.ir_utils.alias_func_extensions['init_binary_str_index',
    'bodo.hiframes.pd_index_ext'] = alias_ext_dummy_func
numba.core.ir_utils.alias_func_extensions['init_categorical_index',
    'bodo.hiframes.pd_index_ext'] = alias_ext_dummy_func


def get_index_data_equiv(self, scope, equiv_set, loc, args, kws):
    assert len(args) == 1 and not kws
    xcs__ddzwo = args[0]
    if isinstance(self.typemap[xcs__ddzwo.name], HeterogeneousIndexType):
        return None
    if equiv_set.has_shape(xcs__ddzwo):
        return ArrayAnalysis.AnalyzeResult(shape=xcs__ddzwo, pre=[])
    return None


(ArrayAnalysis._analyze_op_call_bodo_hiframes_pd_index_ext_get_index_data
    ) = get_index_data_equiv


@overload_method(RangeIndexType, 'map', inline='always', no_unliteral=True)
@overload_method(NumericIndexType, 'map', inline='always', no_unliteral=True)
@overload_method(StringIndexType, 'map', inline='always', no_unliteral=True)
@overload_method(BinaryIndexType, 'map', inline='always', no_unliteral=True)
@overload_method(CategoricalIndexType, 'map', inline='always', no_unliteral
    =True)
@overload_method(PeriodIndexType, 'map', inline='always', no_unliteral=True)
@overload_method(DatetimeIndexType, 'map', inline='always', no_unliteral=True)
@overload_method(TimedeltaIndexType, 'map', inline='always', no_unliteral=True)
def overload_index_map(I, mapper, na_action=None):
    if not is_const_func_type(mapper):
        raise BodoError("Index.map(): 'mapper' should be a function")
    jruj__kdq = dict(na_action=na_action)
    wkwu__bns = dict(na_action=None)
    check_unsupported_args('Index.map', jruj__kdq, wkwu__bns, package_name=
        'pandas', module_name='Index')
    dtype = I.dtype
    bodo.hiframes.pd_timestamp_ext.check_tz_aware_unsupported(I,
        'DatetimeIndex.map')
    if dtype == types.NPDatetime('ns'):
        dtype = pd_timestamp_type
    if dtype == types.NPTimedelta('ns'):
        dtype = pd_timedelta_type
    if isinstance(dtype, bodo.hiframes.pd_categorical_ext.PDCategoricalDtype):
        dtype = dtype.elem_type
    jzf__npbw = numba.core.registry.cpu_target.typing_context
    fazz__ftdk = numba.core.registry.cpu_target.target_context
    try:
        zqlzf__seecq = get_const_func_output_type(mapper, (dtype,), {},
            jzf__npbw, fazz__ftdk)
    except Exception as ohv__agzv:
        raise_bodo_error(get_udf_error_msg('Index.map()', ohv__agzv))
    prc__cur = get_udf_out_arr_type(zqlzf__seecq)
    func = get_overload_const_func(mapper, None)
    zjcz__ohwiu = 'def f(I, mapper, na_action=None):\n'
    zjcz__ohwiu += '  name = bodo.hiframes.pd_index_ext.get_index_name(I)\n'
    zjcz__ohwiu += '  A = bodo.utils.conversion.coerce_to_array(I)\n'
    zjcz__ohwiu += '  numba.parfors.parfor.init_prange()\n'
    zjcz__ohwiu += '  n = len(A)\n'
    zjcz__ohwiu += '  S = bodo.utils.utils.alloc_type(n, _arr_typ, (-1,))\n'
    zjcz__ohwiu += '  for i in numba.parfors.parfor.internal_prange(n):\n'
    zjcz__ohwiu += '    t2 = bodo.utils.conversion.box_if_dt64(A[i])\n'
    zjcz__ohwiu += '    v = map_func(t2)\n'
    zjcz__ohwiu += '    S[i] = bodo.utils.conversion.unbox_if_timestamp(v)\n'
    zjcz__ohwiu += '  return bodo.utils.conversion.index_from_array(S, name)\n'
    wvx__vxf = bodo.compiler.udf_jit(func)
    flclc__rgw = {}
    exec(zjcz__ohwiu, {'numba': numba, 'np': np, 'pd': pd, 'bodo': bodo,
        'map_func': wvx__vxf, '_arr_typ': prc__cur, 'init_nested_counts':
        bodo.utils.indexing.init_nested_counts, 'add_nested_counts': bodo.
        utils.indexing.add_nested_counts, 'data_arr_type': prc__cur.dtype},
        flclc__rgw)
    f = flclc__rgw['f']
    return f


@lower_builtin(operator.is_, NumericIndexType, NumericIndexType)
@lower_builtin(operator.is_, StringIndexType, StringIndexType)
@lower_builtin(operator.is_, BinaryIndexType, BinaryIndexType)
@lower_builtin(operator.is_, PeriodIndexType, PeriodIndexType)
@lower_builtin(operator.is_, DatetimeIndexType, DatetimeIndexType)
@lower_builtin(operator.is_, TimedeltaIndexType, TimedeltaIndexType)
@lower_builtin(operator.is_, IntervalIndexType, IntervalIndexType)
@lower_builtin(operator.is_, CategoricalIndexType, CategoricalIndexType)
def index_is(context, builder, sig, args):
    xjnx__pdpni, yxpeo__jclp = sig.args
    if xjnx__pdpni != yxpeo__jclp:
        return cgutils.false_bit

    def index_is_impl(a, b):
        return a._data is b._data and a._name is b._name
    return context.compile_internal(builder, index_is_impl, sig, args)


@lower_builtin(operator.is_, RangeIndexType, RangeIndexType)
def range_index_is(context, builder, sig, args):
    xjnx__pdpni, yxpeo__jclp = sig.args
    if xjnx__pdpni != yxpeo__jclp:
        return cgutils.false_bit

    def index_is_impl(a, b):
        return (a._start == b._start and a._stop == b._stop and a._step ==
            b._step and a._name is b._name)
    return context.compile_internal(builder, index_is_impl, sig, args)


def create_binary_op_overload(op):

    def overload_index_binary_op(lhs, rhs):
        if is_index_type(lhs):
            zjcz__ohwiu = """def impl(lhs, rhs):
  arr = bodo.utils.conversion.coerce_to_array(lhs)
"""
            if rhs in [bodo.hiframes.pd_timestamp_ext.pd_timestamp_type,
                bodo.hiframes.pd_timestamp_ext.pd_timedelta_type]:
                zjcz__ohwiu += """  dt = bodo.utils.conversion.unbox_if_timestamp(rhs)
  return op(arr, dt)
"""
            else:
                zjcz__ohwiu += """  rhs_arr = bodo.utils.conversion.get_array_if_series_or_index(rhs)
  return op(arr, rhs_arr)
"""
            flclc__rgw = {}
            exec(zjcz__ohwiu, {'bodo': bodo, 'op': op}, flclc__rgw)
            impl = flclc__rgw['impl']
            return impl
        if is_index_type(rhs):
            zjcz__ohwiu = """def impl(lhs, rhs):
  arr = bodo.utils.conversion.coerce_to_array(rhs)
"""
            if lhs in [bodo.hiframes.pd_timestamp_ext.pd_timestamp_type,
                bodo.hiframes.pd_timestamp_ext.pd_timedelta_type]:
                zjcz__ohwiu += """  dt = bodo.utils.conversion.unbox_if_timestamp(lhs)
  return op(dt, arr)
"""
            else:
                zjcz__ohwiu += """  lhs_arr = bodo.utils.conversion.get_array_if_series_or_index(lhs)
  return op(lhs_arr, arr)
"""
            flclc__rgw = {}
            exec(zjcz__ohwiu, {'bodo': bodo, 'op': op}, flclc__rgw)
            impl = flclc__rgw['impl']
            return impl
        if isinstance(lhs, HeterogeneousIndexType):
            if not is_heterogeneous_tuple_type(lhs.data):

                def impl3(lhs, rhs):
                    data = bodo.utils.conversion.coerce_to_array(lhs)
                    wtupd__lkel = bodo.utils.conversion.coerce_to_array(data)
                    acb__alrvq = (bodo.utils.conversion.
                        get_array_if_series_or_index(rhs))
                    fodqq__bgo = op(wtupd__lkel, acb__alrvq)
                    return fodqq__bgo
                return impl3
            count = len(lhs.data.types)
            zjcz__ohwiu = 'def f(lhs, rhs):\n'
            zjcz__ohwiu += '  return [{}]\n'.format(','.join(
                'op(lhs[{}], rhs{})'.format(i, f'[{i}]' if is_iterable_type
                (rhs) else '') for i in range(count)))
            flclc__rgw = {}
            exec(zjcz__ohwiu, {'op': op, 'np': np}, flclc__rgw)
            impl = flclc__rgw['f']
            return impl
        if isinstance(rhs, HeterogeneousIndexType):
            if not is_heterogeneous_tuple_type(rhs.data):

                def impl4(lhs, rhs):
                    data = bodo.hiframes.pd_index_ext.get_index_data(rhs)
                    wtupd__lkel = bodo.utils.conversion.coerce_to_array(data)
                    acb__alrvq = (bodo.utils.conversion.
                        get_array_if_series_or_index(lhs))
                    fodqq__bgo = op(acb__alrvq, wtupd__lkel)
                    return fodqq__bgo
                return impl4
            count = len(rhs.data.types)
            zjcz__ohwiu = 'def f(lhs, rhs):\n'
            zjcz__ohwiu += '  return [{}]\n'.format(','.join(
                'op(lhs{}, rhs[{}])'.format(f'[{i}]' if is_iterable_type(
                lhs) else '', i) for i in range(count)))
            flclc__rgw = {}
            exec(zjcz__ohwiu, {'op': op, 'np': np}, flclc__rgw)
            impl = flclc__rgw['f']
            return impl
    return overload_index_binary_op


skips = [operator.lt, operator.le, operator.eq, operator.ne, operator.gt,
    operator.ge, operator.add, operator.sub, operator.mul, operator.truediv,
    operator.floordiv, operator.pow, operator.mod]


def _install_binary_ops():
    for op in bodo.hiframes.pd_series_ext.series_binary_ops:
        if op in skips:
            continue
        overload_impl = create_binary_op_overload(op)
        overload(op, inline='always')(overload_impl)


_install_binary_ops()


def is_index_type(t):
    return isinstance(t, (RangeIndexType, NumericIndexType, StringIndexType,
        BinaryIndexType, PeriodIndexType, DatetimeIndexType,
        TimedeltaIndexType, IntervalIndexType, CategoricalIndexType))


@lower_cast(RangeIndexType, NumericIndexType)
def cast_range_index_to_int_index(context, builder, fromty, toty, val):
    f = lambda I: init_numeric_index(np.arange(I._start, I._stop, I._step),
        bodo.hiframes.pd_index_ext.get_index_name(I))
    return context.compile_internal(builder, f, toty(fromty), [val])


class HeterogeneousIndexType(types.Type):
    ndim = 1

    def __init__(self, data=None, name_typ=None):
        self.data = data
        name_typ = types.none if name_typ is None else name_typ
        self.name_typ = name_typ
        super(HeterogeneousIndexType, self).__init__(name=
            f'heter_index({data}, {name_typ})')

    def copy(self):
        return HeterogeneousIndexType(self.data, self.name_typ)

    @property
    def key(self):
        return self.data, self.name_typ

    @property
    def mangling_args(self):
        return self.__class__.__name__, (self._code,)

    @property
    def pandas_type_name(self):
        return 'object'

    @property
    def numpy_type_name(self):
        return 'object'


@register_model(HeterogeneousIndexType)
class HeterogeneousIndexModel(models.StructModel):

    def __init__(self, dmm, fe_type):
        zpl__dxgv = [('data', fe_type.data), ('name', fe_type.name_typ)]
        super(HeterogeneousIndexModel, self).__init__(dmm, fe_type, zpl__dxgv)


make_attribute_wrapper(HeterogeneousIndexType, 'data', '_data')
make_attribute_wrapper(HeterogeneousIndexType, 'name', '_name')


@overload_method(HeterogeneousIndexType, 'copy', no_unliteral=True)
def overload_heter_index_copy(A, name=None, deep=False, dtype=None, names=None
    ):
    qanl__rehb = idx_typ_to_format_str_map[HeterogeneousIndexType].format(
        'copy()')
    yhqk__xya = dict(deep=deep, dtype=dtype, names=names)
    check_unsupported_args('Index.copy', yhqk__xya, idx_cpy_arg_defaults,
        fn_str=qanl__rehb, package_name='pandas', module_name='Index')
    if not is_overload_none(name):

        def impl(A, name=None, deep=False, dtype=None, names=None):
            return bodo.hiframes.pd_index_ext.init_numeric_index(A._data.
                copy(), name)
    else:

        def impl(A, name=None, deep=False, dtype=None, names=None):
            return bodo.hiframes.pd_index_ext.init_numeric_index(A._data.
                copy(), A._name)
    return impl


@box(HeterogeneousIndexType)
def box_heter_index(typ, val, c):
    jrfr__obcnn = c.context.insert_const_string(c.builder.module, 'pandas')
    strmv__rojx = c.pyapi.import_module_noblock(jrfr__obcnn)
    zfq__oyglt = cgutils.create_struct_proxy(typ)(c.context, c.builder, val)
    c.context.nrt.incref(c.builder, typ.data, zfq__oyglt.data)
    xtrdg__voi = c.pyapi.from_native_value(typ.data, zfq__oyglt.data, c.
        env_manager)
    c.context.nrt.incref(c.builder, typ.name_typ, zfq__oyglt.name)
    phmv__rxy = c.pyapi.from_native_value(typ.name_typ, zfq__oyglt.name, c.
        env_manager)
    siohz__hgs = c.pyapi.make_none()
    bbct__vsuk = c.pyapi.bool_from_bool(c.context.get_constant(types.bool_,
        False))
    qgy__igrq = c.pyapi.call_method(strmv__rojx, 'Index', (xtrdg__voi,
        siohz__hgs, bbct__vsuk, phmv__rxy))
    c.pyapi.decref(xtrdg__voi)
    c.pyapi.decref(siohz__hgs)
    c.pyapi.decref(bbct__vsuk)
    c.pyapi.decref(phmv__rxy)
    c.pyapi.decref(strmv__rojx)
    c.context.nrt.decref(c.builder, typ, val)
    return qgy__igrq


@intrinsic
def init_heter_index(typingctx, data, name=None):
    name = types.none if name is None else name

    def codegen(context, builder, signature, args):
        assert len(args) == 2
        dcki__omyox = signature.return_type
        zfq__oyglt = cgutils.create_struct_proxy(dcki__omyox)(context, builder)
        zfq__oyglt.data = args[0]
        zfq__oyglt.name = args[1]
        context.nrt.incref(builder, dcki__omyox.data, args[0])
        context.nrt.incref(builder, dcki__omyox.name_typ, args[1])
        return zfq__oyglt._getvalue()
    return HeterogeneousIndexType(data, name)(data, name), codegen


@overload_attribute(HeterogeneousIndexType, 'name')
def heter_index_get_name(i):

    def impl(i):
        return i._name
    return impl


@overload_attribute(NumericIndexType, 'nbytes')
@overload_attribute(DatetimeIndexType, 'nbytes')
@overload_attribute(TimedeltaIndexType, 'nbytes')
@overload_attribute(RangeIndexType, 'nbytes')
@overload_attribute(StringIndexType, 'nbytes')
@overload_attribute(BinaryIndexType, 'nbytes')
@overload_attribute(CategoricalIndexType, 'nbytes')
@overload_attribute(PeriodIndexType, 'nbytes')
def overload_nbytes(I):
    if isinstance(I, RangeIndexType):

        def _impl_nbytes(I):
            return bodo.io.np_io.get_dtype_size(type(I._start)
                ) + bodo.io.np_io.get_dtype_size(type(I._step)
                ) + bodo.io.np_io.get_dtype_size(type(I._stop))
        return _impl_nbytes
    else:

        def _impl_nbytes(I):
            return I._data.nbytes
        return _impl_nbytes


@overload_method(NumericIndexType, 'rename', inline='always')
@overload_method(DatetimeIndexType, 'rename', inline='always')
@overload_method(TimedeltaIndexType, 'rename', inline='always')
@overload_method(RangeIndexType, 'rename', inline='always')
@overload_method(StringIndexType, 'rename', inline='always')
@overload_method(BinaryIndexType, 'rename', inline='always')
@overload_method(CategoricalIndexType, 'rename', inline='always')
@overload_method(PeriodIndexType, 'rename', inline='always')
@overload_method(IntervalIndexType, 'rename', inline='always')
@overload_method(HeterogeneousIndexType, 'rename', inline='always')
def overload_rename(I, name, inplace=False):
    if is_overload_true(inplace):
        raise BodoError('Index.rename(): inplace index renaming unsupported')
    return init_index(I, name)


def init_index(I, name):
    zdy__svnc = {NumericIndexType: bodo.hiframes.pd_index_ext.
        init_numeric_index, DatetimeIndexType: bodo.hiframes.pd_index_ext.
        init_datetime_index, TimedeltaIndexType: bodo.hiframes.pd_index_ext
        .init_timedelta_index, StringIndexType: bodo.hiframes.pd_index_ext.
        init_binary_str_index, BinaryIndexType: bodo.hiframes.pd_index_ext.
        init_binary_str_index, CategoricalIndexType: bodo.hiframes.
        pd_index_ext.init_categorical_index, IntervalIndexType: bodo.
        hiframes.pd_index_ext.init_interval_index}
    if type(I) in zdy__svnc:
        init_func = zdy__svnc[type(I)]
        return lambda I, name, inplace=False: init_func(bodo.hiframes.
            pd_index_ext.get_index_data(I).copy(), name)
    if isinstance(I, RangeIndexType):
        return lambda I, name, inplace=False: I.copy(name=name)
    if isinstance(I, PeriodIndexType):
        freq = I.freq
        return (lambda I, name, inplace=False: bodo.hiframes.pd_index_ext.
            init_period_index(bodo.hiframes.pd_index_ext.get_index_data(I).
            copy(), name, freq))
    if isinstance(I, HeterogeneousIndexType):
        return (lambda I, name, inplace=False: bodo.hiframes.pd_index_ext.
            init_heter_index(bodo.hiframes.pd_index_ext.get_index_data(I),
            name))
    raise_bodo_error(f'init_index(): Unknown type {type(I)}')


@overload(operator.getitem, no_unliteral=True)
def overload_heter_index_getitem(I, ind):
    if not isinstance(I, HeterogeneousIndexType):
        return
    if isinstance(ind, types.Integer):
        return lambda I, ind: bodo.hiframes.pd_index_ext.get_index_data(I)[ind]
    if isinstance(I, HeterogeneousIndexType):
        return lambda I, ind: bodo.hiframes.pd_index_ext.init_heter_index(bodo
            .hiframes.pd_index_ext.get_index_data(I)[ind], bodo.hiframes.
            pd_index_ext.get_index_name(I))


@lower_constant(DatetimeIndexType)
@lower_constant(TimedeltaIndexType)
def lower_constant_time_index(context, builder, ty, pyval):
    if isinstance(ty.data, bodo.DatetimeArrayType):
        data = context.get_constant_generic(builder, ty.data, pyval.array)
    else:
        data = context.get_constant_generic(builder, types.Array(types.
            int64, 1, 'C'), pyval.values.view(np.int64))
    name = context.get_constant_generic(builder, ty.name_typ, pyval.name)
    dtype = ty.dtype
    jyl__lykt = context.get_constant_null(types.DictType(dtype, types.int64))
    return lir.Constant.literal_struct([data, name, jyl__lykt])


@lower_constant(PeriodIndexType)
def lower_constant_period_index(context, builder, ty, pyval):
    data = context.get_constant_generic(builder, bodo.IntegerArrayType(
        types.int64), pd.arrays.IntegerArray(pyval.asi8, pyval.isna()))
    name = context.get_constant_generic(builder, ty.name_typ, pyval.name)
    jyl__lykt = context.get_constant_null(types.DictType(types.int64, types
        .int64))
    return lir.Constant.literal_struct([data, name, jyl__lykt])


@lower_constant(NumericIndexType)
def lower_constant_numeric_index(context, builder, ty, pyval):
    assert isinstance(ty.dtype, (types.Integer, types.Float, types.Boolean))
    data = context.get_constant_generic(builder, types.Array(ty.dtype, 1,
        'C'), pyval.values)
    name = context.get_constant_generic(builder, ty.name_typ, pyval.name)
    dtype = ty.dtype
    jyl__lykt = context.get_constant_null(types.DictType(dtype, types.int64))
    return lir.Constant.literal_struct([data, name, jyl__lykt])


@lower_constant(StringIndexType)
@lower_constant(BinaryIndexType)
def lower_constant_binary_string_index(context, builder, ty, pyval):
    mnw__gpdpw = ty.data
    scalar_type = ty.data.dtype
    data = context.get_constant_generic(builder, mnw__gpdpw, pyval.values)
    name = context.get_constant_generic(builder, ty.name_typ, pyval.name)
    jyl__lykt = context.get_constant_null(types.DictType(scalar_type, types
        .int64))
    return lir.Constant.literal_struct([data, name, jyl__lykt])


@lower_builtin('getiter', RangeIndexType)
def getiter_range_index(context, builder, sig, args):
    [pvil__gzsxt] = sig.args
    [oteme__dec] = args
    gcvad__hro = context.make_helper(builder, pvil__gzsxt, value=oteme__dec)
    tgpp__psbwh = context.make_helper(builder, sig.return_type)
    ujl__lbaw = cgutils.alloca_once_value(builder, gcvad__hro.start)
    oyvje__xdv = context.get_constant(types.intp, 0)
    wcumt__gwpbo = cgutils.alloca_once_value(builder, oyvje__xdv)
    tgpp__psbwh.iter = ujl__lbaw
    tgpp__psbwh.stop = gcvad__hro.stop
    tgpp__psbwh.step = gcvad__hro.step
    tgpp__psbwh.count = wcumt__gwpbo
    inl__ntb = builder.sub(gcvad__hro.stop, gcvad__hro.start)
    iiijp__akvd = context.get_constant(types.intp, 1)
    juxh__vpib = builder.icmp(lc.ICMP_SGT, inl__ntb, oyvje__xdv)
    pbw__xlqh = builder.icmp(lc.ICMP_SGT, gcvad__hro.step, oyvje__xdv)
    rbn__fjryd = builder.not_(builder.xor(juxh__vpib, pbw__xlqh))
    with builder.if_then(rbn__fjryd):
        isyzi__dwxlr = builder.srem(inl__ntb, gcvad__hro.step)
        isyzi__dwxlr = builder.select(juxh__vpib, isyzi__dwxlr, builder.neg
            (isyzi__dwxlr))
        bomv__mogq = builder.icmp(lc.ICMP_SGT, isyzi__dwxlr, oyvje__xdv)
        qegb__zwxsc = builder.add(builder.sdiv(inl__ntb, gcvad__hro.step),
            builder.select(bomv__mogq, iiijp__akvd, oyvje__xdv))
        builder.store(qegb__zwxsc, wcumt__gwpbo)
    dohhm__xet = tgpp__psbwh._getvalue()
    oje__npk = impl_ret_new_ref(context, builder, sig.return_type, dohhm__xet)
    return oje__npk


def _install_index_getiter():
    index_types = [NumericIndexType, StringIndexType, BinaryIndexType,
        CategoricalIndexType, TimedeltaIndexType, DatetimeIndexType]
    for typ in index_types:
        lower_builtin('getiter', typ)(numba.np.arrayobj.getiter_array)


_install_index_getiter()
index_unsupported_methods = ['all', 'any', 'append', 'argmax', 'argmin',
    'argsort', 'asof', 'asof_locs', 'astype', 'delete', 'difference',
    'drop', 'droplevel', 'dropna', 'equals', 'factorize', 'fillna',
    'format', 'get_indexer', 'get_indexer_for', 'get_indexer_non_unique',
    'get_level_values', 'get_slice_bound', 'get_value', 'groupby',
    'holds_integer', 'identical', 'insert', 'intersection', 'is_',
    'is_boolean', 'is_categorical', 'is_floating', 'is_integer',
    'is_interval', 'is_mixed', 'is_numeric', 'is_object',
    'is_type_compatible', 'isin', 'item', 'join', 'memory_usage', 'nunique',
    'putmask', 'ravel', 'reindex', 'repeat', 'searchsorted', 'set_names',
    'set_value', 'shift', 'slice_indexer', 'slice_locs', 'sort',
    'sort_values', 'sortlevel', 'str', 'symmetric_difference',
    'to_flat_index', 'to_frame', 'to_list', 'to_native_types', 'to_numpy',
    'to_series', 'tolist', 'transpose', 'union', 'unique', 'value_counts',
    'view', 'where']
index_unsupported_atrs = ['T', 'array', 'asi8', 'dtype', 'has_duplicates',
    'hasnans', 'inferred_type', 'is_all_dates', 'is_unique', 'ndim',
    'nlevels', 'size', 'names', 'empty']
cat_idx_unsupported_atrs = ['codes', 'categories', 'ordered',
    'is_monotonic', 'is_monotonic_increasing', 'is_monotonic_decreasing']
cat_idx_unsupported_methods = ['rename_categories', 'reorder_categories',
    'add_categories', 'remove_categories', 'remove_unused_categories',
    'set_categories', 'as_ordered', 'as_unordered', 'get_loc']
interval_idx_unsupported_atrs = ['closed', 'is_empty',
    'is_non_overlapping_monotonic', 'is_overlapping', 'left', 'right',
    'mid', 'length', 'values', 'shape', 'nbytes', 'is_monotonic',
    'is_monotonic_increasing', 'is_monotonic_decreasing']
interval_idx_unsupported_methods = ['contains', 'copy', 'overlaps',
    'set_closed', 'to_tuples', 'take', 'get_loc', 'isna', 'isnull', 'map']
multi_index_unsupported_atrs = ['levshape', 'levels', 'codes', 'dtypes',
    'values', 'shape', 'nbytes', 'is_monotonic', 'is_monotonic_increasing',
    'is_monotonic_decreasing']
multi_index_unsupported_methods = ['copy', 'set_levels', 'set_codes',
    'swaplevel', 'reorder_levels', 'remove_unused_levels', 'get_loc',
    'get_locs', 'get_loc_level', 'take', 'isna', 'isnull', 'map']
dt_index_unsupported_atrs = ['time', 'timez', 'tz', 'freq', 'freqstr',
    'inferred_freq']
dt_index_unsupported_methods = ['normalize', 'strftime', 'snap',
    'tz_localize', 'round', 'floor', 'ceil', 'to_period', 'to_perioddelta',
    'to_pydatetime', 'month_name', 'day_name', 'mean', 'indexer_at_time',
    'indexer_between', 'indexer_between_time']
td_index_unsupported_atrs = ['components', 'inferred_freq']
td_index_unsupported_methods = ['to_pydatetime', 'round', 'floor', 'ceil',
    'mean']
period_index_unsupported_atrs = ['day', 'dayofweek', 'day_of_week',
    'dayofyear', 'day_of_year', 'days_in_month', 'daysinmonth', 'freq',
    'freqstr', 'hour', 'is_leap_year', 'minute', 'month', 'quarter',
    'second', 'week', 'weekday', 'weekofyear', 'year', 'end_time', 'qyear',
    'start_time', 'is_monotonic', 'is_monotonic_increasing',
    'is_monotonic_decreasing']
string_index_unsupported_atrs = ['is_monotonic', 'is_monotonic_increasing',
    'is_monotonic_decreasing']
binary_index_unsupported_atrs = ['is_monotonic', 'is_monotonic_increasing',
    'is_monotonic_decreasing']
period_index_unsupported_methods = ['asfreq', 'strftime', 'to_timestamp']
index_types = [('pandas.RangeIndex.{}', RangeIndexType), (
    'pandas.Index.{} with numeric data', NumericIndexType), (
    'pandas.Index.{} with string data', StringIndexType), (
    'pandas.Index.{} with binary data', BinaryIndexType), (
    'pandas.TimedeltaIndex.{}', TimedeltaIndexType), (
    'pandas.IntervalIndex.{}', IntervalIndexType), (
    'pandas.CategoricalIndex.{}', CategoricalIndexType), (
    'pandas.PeriodIndex.{}', PeriodIndexType), ('pandas.DatetimeIndex.{}',
    DatetimeIndexType), ('pandas.MultiIndex.{}', MultiIndexType)]
for name, typ in index_types:
    idx_typ_to_format_str_map[typ] = name


def _install_index_unsupported():
    for znjd__mnrw in index_unsupported_methods:
        for rad__adoir, typ in index_types:
            overload_method(typ, znjd__mnrw, no_unliteral=True)(
                create_unsupported_overload(rad__adoir.format(znjd__mnrw +
                '()')))
    for koi__zdwz in index_unsupported_atrs:
        for rad__adoir, typ in index_types:
            overload_attribute(typ, koi__zdwz, no_unliteral=True)(
                create_unsupported_overload(rad__adoir.format(koi__zdwz)))
    hopk__yoq = [(StringIndexType, string_index_unsupported_atrs), (
        BinaryIndexType, binary_index_unsupported_atrs), (
        CategoricalIndexType, cat_idx_unsupported_atrs), (IntervalIndexType,
        interval_idx_unsupported_atrs), (MultiIndexType,
        multi_index_unsupported_atrs), (DatetimeIndexType,
        dt_index_unsupported_atrs), (TimedeltaIndexType,
        td_index_unsupported_atrs), (PeriodIndexType,
        period_index_unsupported_atrs)]
    joan__ygbyw = [(CategoricalIndexType, cat_idx_unsupported_methods), (
        IntervalIndexType, interval_idx_unsupported_methods), (
        MultiIndexType, multi_index_unsupported_methods), (
        DatetimeIndexType, dt_index_unsupported_methods), (
        TimedeltaIndexType, td_index_unsupported_methods), (PeriodIndexType,
        period_index_unsupported_methods)]
    for typ, ovepu__bais in joan__ygbyw:
        rad__adoir = idx_typ_to_format_str_map[typ]
        for tjsgg__vou in ovepu__bais:
            overload_method(typ, tjsgg__vou, no_unliteral=True)(
                create_unsupported_overload(rad__adoir.format(tjsgg__vou +
                '()')))
    for typ, fbhyw__cbmp in hopk__yoq:
        rad__adoir = idx_typ_to_format_str_map[typ]
        for koi__zdwz in fbhyw__cbmp:
            overload_attribute(typ, koi__zdwz, no_unliteral=True)(
                create_unsupported_overload(rad__adoir.format(koi__zdwz)))
    for olge__verw in [RangeIndexType, NumericIndexType, StringIndexType,
        BinaryIndexType, IntervalIndexType, CategoricalIndexType,
        PeriodIndexType, MultiIndexType]:
        for tjsgg__vou in ['max', 'min']:
            rad__adoir = idx_typ_to_format_str_map[olge__verw]
            overload_method(olge__verw, tjsgg__vou, no_unliteral=True)(
                create_unsupported_overload(rad__adoir.format(tjsgg__vou +
                '()')))


_install_index_unsupported()
