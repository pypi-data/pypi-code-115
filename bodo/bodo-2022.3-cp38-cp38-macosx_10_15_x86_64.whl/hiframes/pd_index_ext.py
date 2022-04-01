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
        xov__rmbmt = [('data', fe_type.data), ('name', fe_type.name_typ), (
            'dict', types.DictType(_dt_index_data_typ.dtype, types.int64))]
        super(DatetimeIndexModel, self).__init__(dmm, fe_type, xov__rmbmt)


make_attribute_wrapper(DatetimeIndexType, 'data', '_data')
make_attribute_wrapper(DatetimeIndexType, 'name', '_name')
make_attribute_wrapper(DatetimeIndexType, 'dict', '_dict')


@overload_method(DatetimeIndexType, 'copy', no_unliteral=True)
def overload_datetime_index_copy(A, name=None, deep=False, dtype=None,
    names=None):
    qumr__nejw = dict(deep=deep, dtype=dtype, names=names)
    nnwq__vgapz = idx_typ_to_format_str_map[DatetimeIndexType].format('copy()')
    check_unsupported_args('copy', qumr__nejw, idx_cpy_arg_defaults, fn_str
        =nnwq__vgapz, package_name='pandas', module_name='Index')
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
    fgl__zvb = c.context.insert_const_string(c.builder.module, 'pandas')
    ldril__isb = c.pyapi.import_module_noblock(fgl__zvb)
    rstd__asy = numba.core.cgutils.create_struct_proxy(typ)(c.context, c.
        builder, val)
    c.context.nrt.incref(c.builder, typ.data, rstd__asy.data)
    oqil__pzr = c.pyapi.from_native_value(typ.data, rstd__asy.data, c.
        env_manager)
    c.context.nrt.incref(c.builder, typ.name_typ, rstd__asy.name)
    lohgw__vravs = c.pyapi.from_native_value(typ.name_typ, rstd__asy.name,
        c.env_manager)
    args = c.pyapi.tuple_pack([oqil__pzr])
    dpr__yqc = c.pyapi.object_getattr_string(ldril__isb, 'DatetimeIndex')
    kws = c.pyapi.dict_pack([('name', lohgw__vravs)])
    eri__aei = c.pyapi.call(dpr__yqc, args, kws)
    c.pyapi.decref(oqil__pzr)
    c.pyapi.decref(lohgw__vravs)
    c.pyapi.decref(ldril__isb)
    c.pyapi.decref(dpr__yqc)
    c.pyapi.decref(args)
    c.pyapi.decref(kws)
    c.context.nrt.decref(c.builder, typ, val)
    return eri__aei


@unbox(DatetimeIndexType)
def unbox_datetime_index(typ, val, c):
    if isinstance(typ.data, DatetimeArrayType):
        uly__abmp = c.pyapi.object_getattr_string(val, 'array')
    else:
        uly__abmp = c.pyapi.object_getattr_string(val, 'values')
    data = c.pyapi.to_native_value(typ.data, uly__abmp).value
    lohgw__vravs = c.pyapi.object_getattr_string(val, 'name')
    name = c.pyapi.to_native_value(typ.name_typ, lohgw__vravs).value
    eax__torbe = cgutils.create_struct_proxy(typ)(c.context, c.builder)
    eax__torbe.data = data
    eax__torbe.name = name
    dtype = _dt_index_data_typ.dtype
    flm__uxwzn, gxpmb__hrb = c.pyapi.call_jit_code(lambda : numba.typed.
        Dict.empty(dtype, types.int64), types.DictType(dtype, types.int64)(
        ), [])
    eax__torbe.dict = gxpmb__hrb
    c.pyapi.decref(uly__abmp)
    c.pyapi.decref(lohgw__vravs)
    return NativeValue(eax__torbe._getvalue())


@intrinsic
def init_datetime_index(typingctx, data, name):
    name = types.none if name is None else name

    def codegen(context, builder, signature, args):
        arj__kulf, cee__oqyni = args
        rstd__asy = cgutils.create_struct_proxy(signature.return_type)(context,
            builder)
        rstd__asy.data = arj__kulf
        rstd__asy.name = cee__oqyni
        context.nrt.incref(builder, signature.args[0], arj__kulf)
        context.nrt.incref(builder, signature.args[1], cee__oqyni)
        dtype = _dt_index_data_typ.dtype
        rstd__asy.dict = context.compile_internal(builder, lambda : numba.
            typed.Dict.empty(dtype, types.int64), types.DictType(dtype,
            types.int64)(), [])
        return rstd__asy._getvalue()
    zebhw__ahe = DatetimeIndexType(name, data)
    sig = signature(zebhw__ahe, data, name)
    return sig, codegen


def init_index_equiv(self, scope, equiv_set, loc, args, kws):
    assert len(args) >= 1 and not kws
    peze__knlz = args[0]
    if equiv_set.has_shape(peze__knlz):
        return ArrayAnalysis.AnalyzeResult(shape=peze__knlz, pre=[])
    return None


(ArrayAnalysis._analyze_op_call_bodo_hiframes_pd_index_ext_init_datetime_index
    ) = init_index_equiv


def gen_dti_field_impl(field):
    rqumw__lytx = 'def impl(dti):\n'
    rqumw__lytx += '    numba.parfors.parfor.init_prange()\n'
    rqumw__lytx += '    A = bodo.hiframes.pd_index_ext.get_index_data(dti)\n'
    rqumw__lytx += (
        '    name = bodo.hiframes.pd_index_ext.get_index_name(dti)\n')
    rqumw__lytx += '    n = len(A)\n'
    rqumw__lytx += '    S = np.empty(n, np.int64)\n'
    rqumw__lytx += '    for i in numba.parfors.parfor.internal_prange(n):\n'
    rqumw__lytx += '        val = A[i]\n'
    rqumw__lytx += '        ts = bodo.utils.conversion.box_if_dt64(val)\n'
    if field in ['weekday']:
        rqumw__lytx += '        S[i] = ts.' + field + '()\n'
    else:
        rqumw__lytx += '        S[i] = ts.' + field + '\n'
    rqumw__lytx += (
        '    return bodo.hiframes.pd_index_ext.init_numeric_index(S, name)\n')
    ibq__mgcs = {}
    exec(rqumw__lytx, {'numba': numba, 'np': np, 'bodo': bodo}, ibq__mgcs)
    impl = ibq__mgcs['impl']
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
        kqb__hylq = len(A)
        S = np.empty(kqb__hylq, np.bool_)
        for i in numba.parfors.parfor.internal_prange(kqb__hylq):
            val = A[i]
            gxtn__qyo = bodo.utils.conversion.box_if_dt64(val)
            S[i] = bodo.hiframes.pd_timestamp_ext.is_leap_year(gxtn__qyo.year)
        return S
    return impl


@overload_attribute(DatetimeIndexType, 'date')
def overload_datetime_index_date(dti):

    def impl(dti):
        numba.parfors.parfor.init_prange()
        A = bodo.hiframes.pd_index_ext.get_index_data(dti)
        kqb__hylq = len(A)
        S = bodo.hiframes.datetime_date_ext.alloc_datetime_date_array(kqb__hylq
            )
        for i in numba.parfors.parfor.internal_prange(kqb__hylq):
            val = A[i]
            gxtn__qyo = bodo.utils.conversion.box_if_dt64(val)
            S[i] = datetime.date(gxtn__qyo.year, gxtn__qyo.month, gxtn__qyo.day
                )
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
    dfbxq__jtb = dict(axis=axis, skipna=skipna)
    izzuy__jgfb = dict(axis=None, skipna=True)
    check_unsupported_args('DatetimeIndex.min', dfbxq__jtb, izzuy__jgfb,
        package_name='pandas', module_name='Index')
    bodo.hiframes.pd_timestamp_ext.check_tz_aware_unsupported(dti,
        'Index.min()')

    def impl(dti, axis=None, skipna=True):
        numba.parfors.parfor.init_prange()
        wszvj__qoxlm = bodo.hiframes.pd_index_ext.get_index_data(dti)
        s = numba.cpython.builtins.get_type_max_value(numba.core.types.int64)
        count = 0
        for i in numba.parfors.parfor.internal_prange(len(wszvj__qoxlm)):
            if not bodo.libs.array_kernels.isna(wszvj__qoxlm, i):
                val = bodo.hiframes.pd_timestamp_ext.dt64_to_integer(
                    wszvj__qoxlm[i])
                s = min(s, val)
                count += 1
        return bodo.hiframes.pd_index_ext._dti_val_finalize(s, count)
    return impl


@overload_method(DatetimeIndexType, 'max', no_unliteral=True)
def overload_datetime_index_max(dti, axis=None, skipna=True):
    dfbxq__jtb = dict(axis=axis, skipna=skipna)
    izzuy__jgfb = dict(axis=None, skipna=True)
    check_unsupported_args('DatetimeIndex.max', dfbxq__jtb, izzuy__jgfb,
        package_name='pandas', module_name='Index')
    bodo.hiframes.pd_timestamp_ext.check_tz_aware_unsupported(dti,
        'Index.max()')

    def impl(dti, axis=None, skipna=True):
        numba.parfors.parfor.init_prange()
        wszvj__qoxlm = bodo.hiframes.pd_index_ext.get_index_data(dti)
        s = numba.cpython.builtins.get_type_min_value(numba.core.types.int64)
        count = 0
        for i in numba.parfors.parfor.internal_prange(len(wszvj__qoxlm)):
            if not bodo.libs.array_kernels.isna(wszvj__qoxlm, i):
                val = bodo.hiframes.pd_timestamp_ext.dt64_to_integer(
                    wszvj__qoxlm[i])
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
    dfbxq__jtb = dict(freq=freq, tz=tz, normalize=normalize, closed=closed,
        ambiguous=ambiguous, dayfirst=dayfirst, yearfirst=yearfirst, dtype=
        dtype, copy=copy)
    izzuy__jgfb = dict(freq=None, tz=None, normalize=False, closed=None,
        ambiguous='raise', dayfirst=False, yearfirst=False, dtype=None,
        copy=False)
    check_unsupported_args('pandas.DatetimeIndex', dfbxq__jtb, izzuy__jgfb,
        package_name='pandas', module_name='Index')

    def f(data=None, freq=None, tz=None, normalize=False, closed=None,
        ambiguous='raise', dayfirst=False, yearfirst=False, dtype=None,
        copy=False, name=None):
        umvj__qen = bodo.utils.conversion.coerce_to_array(data)
        S = bodo.utils.conversion.convert_to_dt64ns(umvj__qen)
        return bodo.hiframes.pd_index_ext.init_datetime_index(S, name)
    return f


def overload_sub_operator_datetime_index(lhs, rhs):
    if isinstance(lhs, DatetimeIndexType
        ) and rhs == bodo.hiframes.pd_timestamp_ext.pd_timestamp_type:
        jdut__riknk = np.dtype('timedelta64[ns]')

        def impl(lhs, rhs):
            numba.parfors.parfor.init_prange()
            wszvj__qoxlm = bodo.hiframes.pd_index_ext.get_index_data(lhs)
            name = bodo.hiframes.pd_index_ext.get_index_name(lhs)
            kqb__hylq = len(wszvj__qoxlm)
            S = np.empty(kqb__hylq, jdut__riknk)
            xfvdy__sxx = rhs.value
            for i in numba.parfors.parfor.internal_prange(kqb__hylq):
                S[i] = bodo.hiframes.pd_timestamp_ext.integer_to_timedelta64(
                    bodo.hiframes.pd_timestamp_ext.dt64_to_integer(
                    wszvj__qoxlm[i]) - xfvdy__sxx)
            return bodo.hiframes.pd_index_ext.init_timedelta_index(S, name)
        return impl
    if isinstance(rhs, DatetimeIndexType
        ) and lhs == bodo.hiframes.pd_timestamp_ext.pd_timestamp_type:
        jdut__riknk = np.dtype('timedelta64[ns]')

        def impl(lhs, rhs):
            numba.parfors.parfor.init_prange()
            wszvj__qoxlm = bodo.hiframes.pd_index_ext.get_index_data(rhs)
            name = bodo.hiframes.pd_index_ext.get_index_name(rhs)
            kqb__hylq = len(wszvj__qoxlm)
            S = np.empty(kqb__hylq, jdut__riknk)
            xfvdy__sxx = lhs.value
            for i in numba.parfors.parfor.internal_prange(kqb__hylq):
                S[i] = bodo.hiframes.pd_timestamp_ext.integer_to_timedelta64(
                    xfvdy__sxx - bodo.hiframes.pd_timestamp_ext.
                    dt64_to_integer(wszvj__qoxlm[i]))
            return bodo.hiframes.pd_index_ext.init_timedelta_index(S, name)
        return impl


def gen_dti_str_binop_impl(op, is_lhs_dti):
    ztnwq__pos = numba.core.utils.OPERATORS_TO_BUILTINS[op]
    rqumw__lytx = 'def impl(lhs, rhs):\n'
    if is_lhs_dti:
        rqumw__lytx += '  dt_index, _str = lhs, rhs\n'
        dpnu__scoo = 'arr[i] {} other'.format(ztnwq__pos)
    else:
        rqumw__lytx += '  dt_index, _str = rhs, lhs\n'
        dpnu__scoo = 'other {} arr[i]'.format(ztnwq__pos)
    rqumw__lytx += (
        '  arr = bodo.hiframes.pd_index_ext.get_index_data(dt_index)\n')
    rqumw__lytx += '  l = len(arr)\n'
    rqumw__lytx += (
        '  other = bodo.hiframes.pd_timestamp_ext.parse_datetime_str(_str)\n')
    rqumw__lytx += '  S = bodo.libs.bool_arr_ext.alloc_bool_array(l)\n'
    rqumw__lytx += '  for i in numba.parfors.parfor.internal_prange(l):\n'
    rqumw__lytx += '    S[i] = {}\n'.format(dpnu__scoo)
    rqumw__lytx += '  return S\n'
    ibq__mgcs = {}
    exec(rqumw__lytx, {'bodo': bodo, 'numba': numba, 'np': np}, ibq__mgcs)
    impl = ibq__mgcs['impl']
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
    wux__tqc = getattr(data, 'dtype', None)
    if not is_overload_none(dtype):
        qpw__xupd = parse_dtype(dtype, 'pandas.Index')
    else:
        qpw__xupd = wux__tqc
    if isinstance(qpw__xupd, types.misc.PyObject):
        raise BodoError(
            "pd.Index() object 'dtype' is not specific enough for typing. Please provide a more exact type (e.g. str)."
            )
    if isinstance(data, RangeIndexType):

        def impl(data=None, dtype=None, copy=False, name=None,
            tupleize_cols=True):
            return pd.RangeIndex(data, name=name)
    elif isinstance(data, DatetimeIndexType) or qpw__xupd == types.NPDatetime(
        'ns'):

        def impl(data=None, dtype=None, copy=False, name=None,
            tupleize_cols=True):
            return pd.DatetimeIndex(data, name=name)
    elif isinstance(data, TimedeltaIndexType
        ) or qpw__xupd == types.NPTimedelta('ns'):

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
        if isinstance(qpw__xupd, (types.Integer, types.Float, types.Boolean)):

            def impl(data=None, dtype=None, copy=False, name=None,
                tupleize_cols=True):
                umvj__qen = bodo.utils.conversion.coerce_to_array(data)
                fly__wqbf = bodo.utils.conversion.fix_arr_dtype(umvj__qen,
                    qpw__xupd)
                return bodo.hiframes.pd_index_ext.init_numeric_index(fly__wqbf,
                    name)
        elif qpw__xupd in [types.string, bytes_type]:

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
                efhh__eeyf = bodo.hiframes.pd_index_ext.get_index_data(dti)
                val = efhh__eeyf[ind]
                return bodo.utils.conversion.box_if_dt64(val)
            return impl
        else:

            def impl(dti, ind):
                efhh__eeyf = bodo.hiframes.pd_index_ext.get_index_data(dti)
                name = bodo.hiframes.pd_index_ext.get_index_name(dti)
                haevf__zddyj = efhh__eeyf[ind]
                return bodo.hiframes.pd_index_ext.init_datetime_index(
                    haevf__zddyj, name)
            return impl


@overload(operator.getitem, no_unliteral=True)
def overload_timedelta_index_getitem(I, ind):
    if not isinstance(I, TimedeltaIndexType):
        return
    if isinstance(ind, types.Integer):

        def impl(I, ind):
            vujr__atmb = bodo.hiframes.pd_index_ext.get_index_data(I)
            return pd.Timedelta(vujr__atmb[ind])
        return impl

    def impl(I, ind):
        vujr__atmb = bodo.hiframes.pd_index_ext.get_index_data(I)
        name = bodo.hiframes.pd_index_ext.get_index_name(I)
        haevf__zddyj = vujr__atmb[ind]
        return bodo.hiframes.pd_index_ext.init_timedelta_index(haevf__zddyj,
            name)
    return impl


@numba.njit(no_cpython_wrapper=True)
def validate_endpoints(closed):
    rfua__zje = False
    qch__xlgux = False
    if closed is None:
        rfua__zje = True
        qch__xlgux = True
    elif closed == 'left':
        rfua__zje = True
    elif closed == 'right':
        qch__xlgux = True
    else:
        raise ValueError("Closed has to be either 'left', 'right' or None")
    return rfua__zje, qch__xlgux


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
    dfbxq__jtb = dict(tz=tz, normalize=normalize)
    izzuy__jgfb = dict(tz=None, normalize=False)
    check_unsupported_args('pandas.date_range', dfbxq__jtb, izzuy__jgfb,
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
        wcv__ouxux = pd.Timestamp('2018-01-01')
        if start is not None:
            wcv__ouxux = pd.Timestamp(start)
        wmkc__fhv = pd.Timestamp('2018-01-01')
        if end is not None:
            wmkc__fhv = pd.Timestamp(end)
        if start is None and end is None and closed is not None:
            raise ValueError(
                'Closed has to be None if not both of startand end are defined'
                )
        rfua__zje, qch__xlgux = bodo.hiframes.pd_index_ext.validate_endpoints(
            closed)
        if freq is not None:
            hfnwu__drrb = _dummy_convert_none_to_int(freq)
            if periods is None:
                b = wcv__ouxux.value
                obf__wglve = b + (wmkc__fhv.value - b
                    ) // hfnwu__drrb * hfnwu__drrb + hfnwu__drrb // 2 + 1
            elif start is not None:
                periods = _dummy_convert_none_to_int(periods)
                b = wcv__ouxux.value
                bcx__otsr = np.int64(periods) * np.int64(hfnwu__drrb)
                obf__wglve = np.int64(b) + bcx__otsr
            elif end is not None:
                periods = _dummy_convert_none_to_int(periods)
                obf__wglve = wmkc__fhv.value + hfnwu__drrb
                bcx__otsr = np.int64(periods) * np.int64(-hfnwu__drrb)
                b = np.int64(obf__wglve) + bcx__otsr
            else:
                raise ValueError(
                    "at least 'start' or 'end' should be specified if a 'period' is given."
                    )
            qqkk__pngrz = np.arange(b, obf__wglve, hfnwu__drrb, np.int64)
        else:
            periods = _dummy_convert_none_to_int(periods)
            lwro__hqh = wmkc__fhv.value - wcv__ouxux.value
            step = lwro__hqh / (periods - 1)
            wdve__kbraa = np.arange(0, periods, 1, np.float64)
            wdve__kbraa *= step
            wdve__kbraa += wcv__ouxux.value
            qqkk__pngrz = wdve__kbraa.astype(np.int64)
            qqkk__pngrz[-1] = wmkc__fhv.value
        if not rfua__zje and len(qqkk__pngrz) and qqkk__pngrz[0
            ] == wcv__ouxux.value:
            qqkk__pngrz = qqkk__pngrz[1:]
        if not qch__xlgux and len(qqkk__pngrz) and qqkk__pngrz[-1
            ] == wmkc__fhv.value:
            qqkk__pngrz = qqkk__pngrz[:-1]
        S = bodo.utils.conversion.convert_to_dt64ns(qqkk__pngrz)
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
        wcv__ouxux = pd.Timedelta('1 day')
        if start is not None:
            wcv__ouxux = pd.Timedelta(start)
        wmkc__fhv = pd.Timedelta('1 day')
        if end is not None:
            wmkc__fhv = pd.Timedelta(end)
        if start is None and end is None and closed is not None:
            raise ValueError(
                'Closed has to be None if not both of start and end are defined'
                )
        rfua__zje, qch__xlgux = bodo.hiframes.pd_index_ext.validate_endpoints(
            closed)
        if freq is not None:
            hfnwu__drrb = _dummy_convert_none_to_int(freq)
            if periods is None:
                b = wcv__ouxux.value
                obf__wglve = b + (wmkc__fhv.value - b
                    ) // hfnwu__drrb * hfnwu__drrb + hfnwu__drrb // 2 + 1
            elif start is not None:
                periods = _dummy_convert_none_to_int(periods)
                b = wcv__ouxux.value
                bcx__otsr = np.int64(periods) * np.int64(hfnwu__drrb)
                obf__wglve = np.int64(b) + bcx__otsr
            elif end is not None:
                periods = _dummy_convert_none_to_int(periods)
                obf__wglve = wmkc__fhv.value + hfnwu__drrb
                bcx__otsr = np.int64(periods) * np.int64(-hfnwu__drrb)
                b = np.int64(obf__wglve) + bcx__otsr
            else:
                raise ValueError(
                    "at least 'start' or 'end' should be specified if a 'period' is given."
                    )
            qqkk__pngrz = np.arange(b, obf__wglve, hfnwu__drrb, np.int64)
        else:
            periods = _dummy_convert_none_to_int(periods)
            lwro__hqh = wmkc__fhv.value - wcv__ouxux.value
            step = lwro__hqh / (periods - 1)
            wdve__kbraa = np.arange(0, periods, 1, np.float64)
            wdve__kbraa *= step
            wdve__kbraa += wcv__ouxux.value
            qqkk__pngrz = wdve__kbraa.astype(np.int64)
            qqkk__pngrz[-1] = wmkc__fhv.value
        if not rfua__zje and len(qqkk__pngrz) and qqkk__pngrz[0
            ] == wcv__ouxux.value:
            qqkk__pngrz = qqkk__pngrz[1:]
        if not qch__xlgux and len(qqkk__pngrz) and qqkk__pngrz[-1
            ] == wmkc__fhv.value:
            qqkk__pngrz = qqkk__pngrz[:-1]
        S = bodo.utils.conversion.convert_to_dt64ns(qqkk__pngrz)
        return bodo.hiframes.pd_index_ext.init_timedelta_index(S, name)
    return f


@overload_method(DatetimeIndexType, 'isocalendar', inline='always',
    no_unliteral=True)
def overload_pd_timestamp_isocalendar(idx):

    def impl(idx):
        A = bodo.hiframes.pd_index_ext.get_index_data(idx)
        numba.parfors.parfor.init_prange()
        kqb__hylq = len(A)
        ehkm__ccfar = bodo.libs.int_arr_ext.alloc_int_array(kqb__hylq, np.
            uint32)
        vlnjo__fdum = bodo.libs.int_arr_ext.alloc_int_array(kqb__hylq, np.
            uint32)
        csn__okaed = bodo.libs.int_arr_ext.alloc_int_array(kqb__hylq, np.uint32
            )
        for i in numba.parfors.parfor.internal_prange(kqb__hylq):
            if bodo.libs.array_kernels.isna(A, i):
                bodo.libs.array_kernels.setna(ehkm__ccfar, i)
                bodo.libs.array_kernels.setna(vlnjo__fdum, i)
                bodo.libs.array_kernels.setna(csn__okaed, i)
                continue
            ehkm__ccfar[i], vlnjo__fdum[i], csn__okaed[i
                ] = bodo.utils.conversion.box_if_dt64(A[i]).isocalendar()
        return bodo.hiframes.pd_dataframe_ext.init_dataframe((ehkm__ccfar,
            vlnjo__fdum, csn__okaed), idx, ('year', 'week', 'day'))
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
        xov__rmbmt = [('data', _timedelta_index_data_typ), ('name', fe_type
            .name_typ), ('dict', types.DictType(_timedelta_index_data_typ.
            dtype, types.int64))]
        super(TimedeltaIndexTypeModel, self).__init__(dmm, fe_type, xov__rmbmt)


@typeof_impl.register(pd.TimedeltaIndex)
def typeof_timedelta_index(val, c):
    return TimedeltaIndexType(get_val_type_maybe_str_literal(val.name))


@box(TimedeltaIndexType)
def box_timedelta_index(typ, val, c):
    fgl__zvb = c.context.insert_const_string(c.builder.module, 'pandas')
    ldril__isb = c.pyapi.import_module_noblock(fgl__zvb)
    timedelta_index = numba.core.cgutils.create_struct_proxy(typ)(c.context,
        c.builder, val)
    c.context.nrt.incref(c.builder, _timedelta_index_data_typ,
        timedelta_index.data)
    oqil__pzr = c.pyapi.from_native_value(_timedelta_index_data_typ,
        timedelta_index.data, c.env_manager)
    c.context.nrt.incref(c.builder, typ.name_typ, timedelta_index.name)
    lohgw__vravs = c.pyapi.from_native_value(typ.name_typ, timedelta_index.
        name, c.env_manager)
    args = c.pyapi.tuple_pack([oqil__pzr])
    kws = c.pyapi.dict_pack([('name', lohgw__vravs)])
    dpr__yqc = c.pyapi.object_getattr_string(ldril__isb, 'TimedeltaIndex')
    eri__aei = c.pyapi.call(dpr__yqc, args, kws)
    c.pyapi.decref(oqil__pzr)
    c.pyapi.decref(lohgw__vravs)
    c.pyapi.decref(ldril__isb)
    c.pyapi.decref(dpr__yqc)
    c.pyapi.decref(args)
    c.pyapi.decref(kws)
    c.context.nrt.decref(c.builder, typ, val)
    return eri__aei


@unbox(TimedeltaIndexType)
def unbox_timedelta_index(typ, val, c):
    yqtt__zyx = c.pyapi.object_getattr_string(val, 'values')
    data = c.pyapi.to_native_value(_timedelta_index_data_typ, yqtt__zyx).value
    lohgw__vravs = c.pyapi.object_getattr_string(val, 'name')
    name = c.pyapi.to_native_value(typ.name_typ, lohgw__vravs).value
    c.pyapi.decref(yqtt__zyx)
    c.pyapi.decref(lohgw__vravs)
    eax__torbe = cgutils.create_struct_proxy(typ)(c.context, c.builder)
    eax__torbe.data = data
    eax__torbe.name = name
    dtype = _timedelta_index_data_typ.dtype
    flm__uxwzn, gxpmb__hrb = c.pyapi.call_jit_code(lambda : numba.typed.
        Dict.empty(dtype, types.int64), types.DictType(dtype, types.int64)(
        ), [])
    eax__torbe.dict = gxpmb__hrb
    return NativeValue(eax__torbe._getvalue())


@intrinsic
def init_timedelta_index(typingctx, data, name=None):
    name = types.none if name is None else name

    def codegen(context, builder, signature, args):
        arj__kulf, cee__oqyni = args
        timedelta_index = cgutils.create_struct_proxy(signature.return_type)(
            context, builder)
        timedelta_index.data = arj__kulf
        timedelta_index.name = cee__oqyni
        context.nrt.incref(builder, signature.args[0], arj__kulf)
        context.nrt.incref(builder, signature.args[1], cee__oqyni)
        dtype = _timedelta_index_data_typ.dtype
        timedelta_index.dict = context.compile_internal(builder, lambda :
            numba.typed.Dict.empty(dtype, types.int64), types.DictType(
            dtype, types.int64)(), [])
        return timedelta_index._getvalue()
    zebhw__ahe = TimedeltaIndexType(name)
    sig = signature(zebhw__ahe, data, name)
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
    qumr__nejw = dict(deep=deep, dtype=dtype, names=names)
    nnwq__vgapz = idx_typ_to_format_str_map[TimedeltaIndexType].format('copy()'
        )
    check_unsupported_args('TimedeltaIndex.copy', qumr__nejw,
        idx_cpy_arg_defaults, fn_str=nnwq__vgapz, package_name='pandas',
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
    dfbxq__jtb = dict(axis=axis, skipna=skipna)
    izzuy__jgfb = dict(axis=None, skipna=True)
    check_unsupported_args('TimedeltaIndex.min', dfbxq__jtb, izzuy__jgfb,
        package_name='pandas', module_name='Index')

    def impl(tdi, axis=None, skipna=True):
        numba.parfors.parfor.init_prange()
        data = bodo.hiframes.pd_index_ext.get_index_data(tdi)
        kqb__hylq = len(data)
        zbd__ymkew = numba.cpython.builtins.get_type_max_value(numba.core.
            types.int64)
        count = 0
        for i in numba.parfors.parfor.internal_prange(kqb__hylq):
            if bodo.libs.array_kernels.isna(data, i):
                continue
            val = (bodo.hiframes.datetime_timedelta_ext.
                cast_numpy_timedelta_to_int(data[i]))
            count += 1
            zbd__ymkew = min(zbd__ymkew, val)
        albu__wpwn = bodo.hiframes.pd_timestamp_ext.integer_to_timedelta64(
            zbd__ymkew)
        return bodo.hiframes.pd_index_ext._tdi_val_finalize(albu__wpwn, count)
    return impl


@overload_method(TimedeltaIndexType, 'max', inline='always', no_unliteral=True)
def overload_timedelta_index_max(tdi, axis=None, skipna=True):
    dfbxq__jtb = dict(axis=axis, skipna=skipna)
    izzuy__jgfb = dict(axis=None, skipna=True)
    check_unsupported_args('TimedeltaIndex.max', dfbxq__jtb, izzuy__jgfb,
        package_name='pandas', module_name='Index')
    if not is_overload_none(axis) or not is_overload_true(skipna):
        raise BodoError(
            'Index.min(): axis and skipna arguments not supported yet')

    def impl(tdi, axis=None, skipna=True):
        numba.parfors.parfor.init_prange()
        data = bodo.hiframes.pd_index_ext.get_index_data(tdi)
        kqb__hylq = len(data)
        awqb__oget = numba.cpython.builtins.get_type_min_value(numba.core.
            types.int64)
        count = 0
        for i in numba.parfors.parfor.internal_prange(kqb__hylq):
            if bodo.libs.array_kernels.isna(data, i):
                continue
            val = (bodo.hiframes.datetime_timedelta_ext.
                cast_numpy_timedelta_to_int(data[i]))
            count += 1
            awqb__oget = max(awqb__oget, val)
        albu__wpwn = bodo.hiframes.pd_timestamp_ext.integer_to_timedelta64(
            awqb__oget)
        return bodo.hiframes.pd_index_ext._tdi_val_finalize(albu__wpwn, count)
    return impl


def gen_tdi_field_impl(field):
    rqumw__lytx = 'def impl(tdi):\n'
    rqumw__lytx += '    numba.parfors.parfor.init_prange()\n'
    rqumw__lytx += '    A = bodo.hiframes.pd_index_ext.get_index_data(tdi)\n'
    rqumw__lytx += (
        '    name = bodo.hiframes.pd_index_ext.get_index_name(tdi)\n')
    rqumw__lytx += '    n = len(A)\n'
    rqumw__lytx += '    S = np.empty(n, np.int64)\n'
    rqumw__lytx += '    for i in numba.parfors.parfor.internal_prange(n):\n'
    rqumw__lytx += (
        '        td64 = bodo.hiframes.pd_timestamp_ext.timedelta64_to_integer(A[i])\n'
        )
    if field == 'nanoseconds':
        rqumw__lytx += '        S[i] = td64 % 1000\n'
    elif field == 'microseconds':
        rqumw__lytx += '        S[i] = td64 // 1000 % 100000\n'
    elif field == 'seconds':
        rqumw__lytx += (
            '        S[i] = td64 // (1000 * 1000000) % (60 * 60 * 24)\n')
    elif field == 'days':
        rqumw__lytx += (
            '        S[i] = td64 // (1000 * 1000000 * 60 * 60 * 24)\n')
    else:
        assert False, 'invalid timedelta field'
    rqumw__lytx += (
        '    return bodo.hiframes.pd_index_ext.init_numeric_index(S, name)\n')
    ibq__mgcs = {}
    exec(rqumw__lytx, {'numba': numba, 'np': np, 'bodo': bodo}, ibq__mgcs)
    impl = ibq__mgcs['impl']
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
    dfbxq__jtb = dict(unit=unit, freq=freq, dtype=dtype, copy=copy)
    izzuy__jgfb = dict(unit=None, freq=None, dtype=None, copy=False)
    check_unsupported_args('pandas.TimedeltaIndex', dfbxq__jtb, izzuy__jgfb,
        package_name='pandas', module_name='Index')

    def impl(data=None, unit=None, freq=None, dtype=None, copy=False, name=None
        ):
        umvj__qen = bodo.utils.conversion.coerce_to_array(data)
        S = bodo.utils.conversion.convert_to_td64ns(umvj__qen)
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
        xov__rmbmt = [('start', types.int64), ('stop', types.int64), (
            'step', types.int64), ('name', fe_type.name_typ)]
        super(RangeIndexModel, self).__init__(dmm, fe_type, xov__rmbmt)


make_attribute_wrapper(RangeIndexType, 'start', '_start')
make_attribute_wrapper(RangeIndexType, 'stop', '_stop')
make_attribute_wrapper(RangeIndexType, 'step', '_step')
make_attribute_wrapper(RangeIndexType, 'name', '_name')


@overload_method(RangeIndexType, 'copy', no_unliteral=True)
def overload_range_index_copy(A, name=None, deep=False, dtype=None, names=None
    ):
    qumr__nejw = dict(deep=deep, dtype=dtype, names=names)
    nnwq__vgapz = idx_typ_to_format_str_map[RangeIndexType].format('copy()')
    check_unsupported_args('RangeIndex.copy', qumr__nejw,
        idx_cpy_arg_defaults, fn_str=nnwq__vgapz, package_name='pandas',
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
    fgl__zvb = c.context.insert_const_string(c.builder.module, 'pandas')
    zhf__kit = c.pyapi.import_module_noblock(fgl__zvb)
    vye__aaw = cgutils.create_struct_proxy(typ)(c.context, c.builder, val)
    ahiu__xstx = c.pyapi.from_native_value(types.int64, vye__aaw.start, c.
        env_manager)
    zto__chuym = c.pyapi.from_native_value(types.int64, vye__aaw.stop, c.
        env_manager)
    ejptr__njuy = c.pyapi.from_native_value(types.int64, vye__aaw.step, c.
        env_manager)
    c.context.nrt.incref(c.builder, typ.name_typ, vye__aaw.name)
    lohgw__vravs = c.pyapi.from_native_value(typ.name_typ, vye__aaw.name, c
        .env_manager)
    args = c.pyapi.tuple_pack([ahiu__xstx, zto__chuym, ejptr__njuy])
    kws = c.pyapi.dict_pack([('name', lohgw__vravs)])
    dpr__yqc = c.pyapi.object_getattr_string(zhf__kit, 'RangeIndex')
    wjr__edcg = c.pyapi.call(dpr__yqc, args, kws)
    c.pyapi.decref(ahiu__xstx)
    c.pyapi.decref(zto__chuym)
    c.pyapi.decref(ejptr__njuy)
    c.pyapi.decref(lohgw__vravs)
    c.pyapi.decref(zhf__kit)
    c.pyapi.decref(dpr__yqc)
    c.pyapi.decref(args)
    c.pyapi.decref(kws)
    c.context.nrt.decref(c.builder, typ, val)
    return wjr__edcg


@intrinsic
def init_range_index(typingctx, start, stop, step, name=None):
    name = types.none if name is None else name

    def codegen(context, builder, signature, args):
        assert len(args) == 4
        vye__aaw = cgutils.create_struct_proxy(signature.return_type)(context,
            builder)
        vye__aaw.start = args[0]
        vye__aaw.stop = args[1]
        vye__aaw.step = args[2]
        vye__aaw.name = args[3]
        context.nrt.incref(builder, signature.return_type.name_typ, args[3])
        return vye__aaw._getvalue()
    return RangeIndexType(name)(start, stop, step, name), codegen


def init_range_index_equiv(self, scope, equiv_set, loc, args, kws):
    assert len(args) == 4 and not kws
    start, stop, step, lmsjn__dafmb = args
    if self.typemap[start.name] == types.IntegerLiteral(0) and self.typemap[
        step.name] == types.IntegerLiteral(1) and equiv_set.has_shape(stop):
        return ArrayAnalysis.AnalyzeResult(shape=stop, pre=[])
    return None


(ArrayAnalysis._analyze_op_call_bodo_hiframes_pd_index_ext_init_range_index
    ) = init_range_index_equiv


@unbox(RangeIndexType)
def unbox_range_index(typ, val, c):
    ahiu__xstx = c.pyapi.object_getattr_string(val, 'start')
    start = c.pyapi.to_native_value(types.int64, ahiu__xstx).value
    zto__chuym = c.pyapi.object_getattr_string(val, 'stop')
    stop = c.pyapi.to_native_value(types.int64, zto__chuym).value
    ejptr__njuy = c.pyapi.object_getattr_string(val, 'step')
    step = c.pyapi.to_native_value(types.int64, ejptr__njuy).value
    lohgw__vravs = c.pyapi.object_getattr_string(val, 'name')
    name = c.pyapi.to_native_value(typ.name_typ, lohgw__vravs).value
    c.pyapi.decref(ahiu__xstx)
    c.pyapi.decref(zto__chuym)
    c.pyapi.decref(ejptr__njuy)
    c.pyapi.decref(lohgw__vravs)
    vye__aaw = cgutils.create_struct_proxy(typ)(c.context, c.builder)
    vye__aaw.start = start
    vye__aaw.stop = stop
    vye__aaw.step = step
    vye__aaw.name = name
    return NativeValue(vye__aaw._getvalue())


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
        stzrf__zgk = (
            'RangeIndex(...) must be called with integers, {value} was passed for {field}'
            )
        if not is_overload_none(value) and not isinstance(value, types.
            IntegerLiteral) and not isinstance(value, types.Integer):
            raise BodoError(stzrf__zgk.format(value=value, field=field))
    _ensure_int_or_none(start, 'start')
    _ensure_int_or_none(stop, 'stop')
    _ensure_int_or_none(step, 'step')
    if is_overload_none(start) and is_overload_none(stop) and is_overload_none(
        step):
        stzrf__zgk = 'RangeIndex(...) must be called with integers'
        raise BodoError(stzrf__zgk)
    ldzra__qhmeq = 'start'
    fuf__vld = 'stop'
    jhk__kvcb = 'step'
    if is_overload_none(start):
        ldzra__qhmeq = '0'
    if is_overload_none(stop):
        fuf__vld = 'start'
        ldzra__qhmeq = '0'
    if is_overload_none(step):
        jhk__kvcb = '1'
    rqumw__lytx = """def _pd_range_index_imp(start=None, stop=None, step=None, dtype=None, copy=False, name=None):
"""
    rqumw__lytx += '  return init_range_index({}, {}, {}, name)\n'.format(
        ldzra__qhmeq, fuf__vld, jhk__kvcb)
    ibq__mgcs = {}
    exec(rqumw__lytx, {'init_range_index': init_range_index}, ibq__mgcs)
    xedxn__pro = ibq__mgcs['_pd_range_index_imp']
    return xedxn__pro


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
                ibng__uwau = numba.cpython.unicode._normalize_slice(idx, len(I)
                    )
                name = bodo.hiframes.pd_index_ext.get_index_name(I)
                start = I._start + I._step * ibng__uwau.start
                stop = I._start + I._step * ibng__uwau.stop
                step = I._step * ibng__uwau.step
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
        xov__rmbmt = [('data', bodo.IntegerArrayType(types.int64)), ('name',
            fe_type.name_typ), ('dict', types.DictType(types.int64, types.
            int64))]
        super(PeriodIndexModel, self).__init__(dmm, fe_type, xov__rmbmt)


make_attribute_wrapper(PeriodIndexType, 'data', '_data')
make_attribute_wrapper(PeriodIndexType, 'name', '_name')
make_attribute_wrapper(PeriodIndexType, 'dict', '_dict')


@overload_method(PeriodIndexType, 'copy', no_unliteral=True)
def overload_period_index_copy(A, name=None, deep=False, dtype=None, names=None
    ):
    freq = A.freq
    qumr__nejw = dict(deep=deep, dtype=dtype, names=names)
    nnwq__vgapz = idx_typ_to_format_str_map[PeriodIndexType].format('copy()')
    check_unsupported_args('PeriodIndex.copy', qumr__nejw,
        idx_cpy_arg_defaults, fn_str=nnwq__vgapz, package_name='pandas',
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
        arj__kulf, cee__oqyni, lmsjn__dafmb = args
        ngc__muj = signature.return_type
        wenjp__fxk = cgutils.create_struct_proxy(ngc__muj)(context, builder)
        wenjp__fxk.data = arj__kulf
        wenjp__fxk.name = cee__oqyni
        context.nrt.incref(builder, signature.args[0], args[0])
        context.nrt.incref(builder, signature.args[1], args[1])
        wenjp__fxk.dict = context.compile_internal(builder, lambda : numba.
            typed.Dict.empty(types.int64, types.int64), types.DictType(
            types.int64, types.int64)(), [])
        return wenjp__fxk._getvalue()
    dkf__ltyzw = get_overload_const_str(freq)
    zebhw__ahe = PeriodIndexType(dkf__ltyzw, name)
    sig = signature(zebhw__ahe, data, name, freq)
    return sig, codegen


@box(PeriodIndexType)
def box_period_index(typ, val, c):
    fgl__zvb = c.context.insert_const_string(c.builder.module, 'pandas')
    zhf__kit = c.pyapi.import_module_noblock(fgl__zvb)
    eax__torbe = cgutils.create_struct_proxy(typ)(c.context, c.builder, val)
    c.context.nrt.incref(c.builder, bodo.IntegerArrayType(types.int64),
        eax__torbe.data)
    uly__abmp = c.pyapi.from_native_value(bodo.IntegerArrayType(types.int64
        ), eax__torbe.data, c.env_manager)
    c.context.nrt.incref(c.builder, typ.name_typ, eax__torbe.name)
    lohgw__vravs = c.pyapi.from_native_value(typ.name_typ, eax__torbe.name,
        c.env_manager)
    zxl__kucb = c.pyapi.string_from_constant_string(typ.freq)
    args = c.pyapi.tuple_pack([])
    kws = c.pyapi.dict_pack([('ordinal', uly__abmp), ('name', lohgw__vravs),
        ('freq', zxl__kucb)])
    dpr__yqc = c.pyapi.object_getattr_string(zhf__kit, 'PeriodIndex')
    wjr__edcg = c.pyapi.call(dpr__yqc, args, kws)
    c.pyapi.decref(uly__abmp)
    c.pyapi.decref(lohgw__vravs)
    c.pyapi.decref(zxl__kucb)
    c.pyapi.decref(zhf__kit)
    c.pyapi.decref(dpr__yqc)
    c.pyapi.decref(args)
    c.pyapi.decref(kws)
    c.context.nrt.decref(c.builder, typ, val)
    return wjr__edcg


@unbox(PeriodIndexType)
def unbox_period_index(typ, val, c):
    arr_typ = bodo.IntegerArrayType(types.int64)
    uub__mkc = c.pyapi.object_getattr_string(val, 'asi8')
    tapz__foz = c.pyapi.call_method(val, 'isna', ())
    lohgw__vravs = c.pyapi.object_getattr_string(val, 'name')
    name = c.pyapi.to_native_value(typ.name_typ, lohgw__vravs).value
    fgl__zvb = c.context.insert_const_string(c.builder.module, 'pandas')
    ldril__isb = c.pyapi.import_module_noblock(fgl__zvb)
    hxv__spk = c.pyapi.object_getattr_string(ldril__isb, 'arrays')
    uly__abmp = c.pyapi.call_method(hxv__spk, 'IntegerArray', (uub__mkc,
        tapz__foz))
    data = c.pyapi.to_native_value(arr_typ, uly__abmp).value
    c.pyapi.decref(uub__mkc)
    c.pyapi.decref(tapz__foz)
    c.pyapi.decref(lohgw__vravs)
    c.pyapi.decref(ldril__isb)
    c.pyapi.decref(hxv__spk)
    c.pyapi.decref(uly__abmp)
    eax__torbe = cgutils.create_struct_proxy(typ)(c.context, c.builder)
    eax__torbe.data = data
    eax__torbe.name = name
    flm__uxwzn, gxpmb__hrb = c.pyapi.call_jit_code(lambda : numba.typed.
        Dict.empty(types.int64, types.int64), types.DictType(types.int64,
        types.int64)(), [])
    eax__torbe.dict = gxpmb__hrb
    return NativeValue(eax__torbe._getvalue())


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
        rsf__zaa = get_categories_int_type(fe_type.data.dtype)
        xov__rmbmt = [('data', fe_type.data), ('name', fe_type.name_typ), (
            'dict', types.DictType(rsf__zaa, types.int64))]
        super(CategoricalIndexTypeModel, self).__init__(dmm, fe_type,
            xov__rmbmt)


@typeof_impl.register(pd.CategoricalIndex)
def typeof_categorical_index(val, c):
    return CategoricalIndexType(bodo.typeof(val.values),
        get_val_type_maybe_str_literal(val.name))


@box(CategoricalIndexType)
def box_categorical_index(typ, val, c):
    fgl__zvb = c.context.insert_const_string(c.builder.module, 'pandas')
    ldril__isb = c.pyapi.import_module_noblock(fgl__zvb)
    gjbr__gwx = numba.core.cgutils.create_struct_proxy(typ)(c.context, c.
        builder, val)
    c.context.nrt.incref(c.builder, typ.data, gjbr__gwx.data)
    oqil__pzr = c.pyapi.from_native_value(typ.data, gjbr__gwx.data, c.
        env_manager)
    c.context.nrt.incref(c.builder, typ.name_typ, gjbr__gwx.name)
    lohgw__vravs = c.pyapi.from_native_value(typ.name_typ, gjbr__gwx.name,
        c.env_manager)
    args = c.pyapi.tuple_pack([oqil__pzr])
    kws = c.pyapi.dict_pack([('name', lohgw__vravs)])
    dpr__yqc = c.pyapi.object_getattr_string(ldril__isb, 'CategoricalIndex')
    eri__aei = c.pyapi.call(dpr__yqc, args, kws)
    c.pyapi.decref(oqil__pzr)
    c.pyapi.decref(lohgw__vravs)
    c.pyapi.decref(ldril__isb)
    c.pyapi.decref(dpr__yqc)
    c.pyapi.decref(args)
    c.pyapi.decref(kws)
    c.context.nrt.decref(c.builder, typ, val)
    return eri__aei


@unbox(CategoricalIndexType)
def unbox_categorical_index(typ, val, c):
    from bodo.hiframes.pd_categorical_ext import get_categories_int_type
    yqtt__zyx = c.pyapi.object_getattr_string(val, 'values')
    data = c.pyapi.to_native_value(typ.data, yqtt__zyx).value
    lohgw__vravs = c.pyapi.object_getattr_string(val, 'name')
    name = c.pyapi.to_native_value(typ.name_typ, lohgw__vravs).value
    c.pyapi.decref(yqtt__zyx)
    c.pyapi.decref(lohgw__vravs)
    eax__torbe = cgutils.create_struct_proxy(typ)(c.context, c.builder)
    eax__torbe.data = data
    eax__torbe.name = name
    dtype = get_categories_int_type(typ.data.dtype)
    flm__uxwzn, gxpmb__hrb = c.pyapi.call_jit_code(lambda : numba.typed.
        Dict.empty(dtype, types.int64), types.DictType(dtype, types.int64)(
        ), [])
    eax__torbe.dict = gxpmb__hrb
    return NativeValue(eax__torbe._getvalue())


@intrinsic
def init_categorical_index(typingctx, data, name=None):
    name = types.none if name is None else name

    def codegen(context, builder, signature, args):
        from bodo.hiframes.pd_categorical_ext import get_categories_int_type
        arj__kulf, cee__oqyni = args
        gjbr__gwx = cgutils.create_struct_proxy(signature.return_type)(context,
            builder)
        gjbr__gwx.data = arj__kulf
        gjbr__gwx.name = cee__oqyni
        context.nrt.incref(builder, signature.args[0], arj__kulf)
        context.nrt.incref(builder, signature.args[1], cee__oqyni)
        dtype = get_categories_int_type(signature.return_type.data.dtype)
        gjbr__gwx.dict = context.compile_internal(builder, lambda : numba.
            typed.Dict.empty(dtype, types.int64), types.DictType(dtype,
            types.int64)(), [])
        return gjbr__gwx._getvalue()
    zebhw__ahe = CategoricalIndexType(data, name)
    sig = signature(zebhw__ahe, data, name)
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
    nnwq__vgapz = idx_typ_to_format_str_map[CategoricalIndexType].format(
        'copy()')
    qumr__nejw = dict(deep=deep, dtype=dtype, names=names)
    check_unsupported_args('CategoricalIndex.copy', qumr__nejw,
        idx_cpy_arg_defaults, fn_str=nnwq__vgapz, package_name='pandas',
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
        xov__rmbmt = [('data', fe_type.data), ('name', fe_type.name_typ), (
            'dict', types.DictType(types.UniTuple(fe_type.data.arr_type.
            dtype, 2), types.int64))]
        super(IntervalIndexTypeModel, self).__init__(dmm, fe_type, xov__rmbmt)


@typeof_impl.register(pd.IntervalIndex)
def typeof_interval_index(val, c):
    return IntervalIndexType(bodo.typeof(val.values),
        get_val_type_maybe_str_literal(val.name))


@box(IntervalIndexType)
def box_interval_index(typ, val, c):
    fgl__zvb = c.context.insert_const_string(c.builder.module, 'pandas')
    ldril__isb = c.pyapi.import_module_noblock(fgl__zvb)
    ghvo__zfqk = numba.core.cgutils.create_struct_proxy(typ)(c.context, c.
        builder, val)
    c.context.nrt.incref(c.builder, typ.data, ghvo__zfqk.data)
    oqil__pzr = c.pyapi.from_native_value(typ.data, ghvo__zfqk.data, c.
        env_manager)
    c.context.nrt.incref(c.builder, typ.name_typ, ghvo__zfqk.name)
    lohgw__vravs = c.pyapi.from_native_value(typ.name_typ, ghvo__zfqk.name,
        c.env_manager)
    args = c.pyapi.tuple_pack([oqil__pzr])
    kws = c.pyapi.dict_pack([('name', lohgw__vravs)])
    dpr__yqc = c.pyapi.object_getattr_string(ldril__isb, 'IntervalIndex')
    eri__aei = c.pyapi.call(dpr__yqc, args, kws)
    c.pyapi.decref(oqil__pzr)
    c.pyapi.decref(lohgw__vravs)
    c.pyapi.decref(ldril__isb)
    c.pyapi.decref(dpr__yqc)
    c.pyapi.decref(args)
    c.pyapi.decref(kws)
    c.context.nrt.decref(c.builder, typ, val)
    return eri__aei


@unbox(IntervalIndexType)
def unbox_interval_index(typ, val, c):
    yqtt__zyx = c.pyapi.object_getattr_string(val, 'values')
    data = c.pyapi.to_native_value(typ.data, yqtt__zyx).value
    lohgw__vravs = c.pyapi.object_getattr_string(val, 'name')
    name = c.pyapi.to_native_value(typ.name_typ, lohgw__vravs).value
    c.pyapi.decref(yqtt__zyx)
    c.pyapi.decref(lohgw__vravs)
    eax__torbe = cgutils.create_struct_proxy(typ)(c.context, c.builder)
    eax__torbe.data = data
    eax__torbe.name = name
    dtype = types.UniTuple(typ.data.arr_type.dtype, 2)
    flm__uxwzn, gxpmb__hrb = c.pyapi.call_jit_code(lambda : numba.typed.
        Dict.empty(dtype, types.int64), types.DictType(dtype, types.int64)(
        ), [])
    eax__torbe.dict = gxpmb__hrb
    return NativeValue(eax__torbe._getvalue())


@intrinsic
def init_interval_index(typingctx, data, name=None):
    name = types.none if name is None else name

    def codegen(context, builder, signature, args):
        arj__kulf, cee__oqyni = args
        ghvo__zfqk = cgutils.create_struct_proxy(signature.return_type)(context
            , builder)
        ghvo__zfqk.data = arj__kulf
        ghvo__zfqk.name = cee__oqyni
        context.nrt.incref(builder, signature.args[0], arj__kulf)
        context.nrt.incref(builder, signature.args[1], cee__oqyni)
        dtype = types.UniTuple(data.arr_type.dtype, 2)
        ghvo__zfqk.dict = context.compile_internal(builder, lambda : numba.
            typed.Dict.empty(dtype, types.int64), types.DictType(dtype,
            types.int64)(), [])
        return ghvo__zfqk._getvalue()
    zebhw__ahe = IntervalIndexType(data, name)
    sig = signature(zebhw__ahe, data, name)
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
        xov__rmbmt = [('data', fe_type.data), ('name', fe_type.name_typ), (
            'dict', types.DictType(fe_type.dtype, types.int64))]
        super(NumericIndexModel, self).__init__(dmm, fe_type, xov__rmbmt)


make_attribute_wrapper(NumericIndexType, 'data', '_data')
make_attribute_wrapper(NumericIndexType, 'name', '_name')
make_attribute_wrapper(NumericIndexType, 'dict', '_dict')


@overload_method(NumericIndexType, 'copy', no_unliteral=True)
def overload_numeric_index_copy(A, name=None, deep=False, dtype=None, names
    =None):
    nnwq__vgapz = idx_typ_to_format_str_map[NumericIndexType].format('copy()')
    qumr__nejw = dict(deep=deep, dtype=dtype, names=names)
    check_unsupported_args('Index.copy', qumr__nejw, idx_cpy_arg_defaults,
        fn_str=nnwq__vgapz, package_name='pandas', module_name='Index')
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
    fgl__zvb = c.context.insert_const_string(c.builder.module, 'pandas')
    zhf__kit = c.pyapi.import_module_noblock(fgl__zvb)
    eax__torbe = cgutils.create_struct_proxy(typ)(c.context, c.builder, val)
    c.context.nrt.incref(c.builder, typ.data, eax__torbe.data)
    uly__abmp = c.pyapi.from_native_value(typ.data, eax__torbe.data, c.
        env_manager)
    c.context.nrt.incref(c.builder, typ.name_typ, eax__torbe.name)
    lohgw__vravs = c.pyapi.from_native_value(typ.name_typ, eax__torbe.name,
        c.env_manager)
    sscpk__imjmn = c.pyapi.make_none()
    urx__ngw = c.pyapi.bool_from_bool(c.context.get_constant(types.bool_, 
        False))
    wjr__edcg = c.pyapi.call_method(zhf__kit, 'Index', (uly__abmp,
        sscpk__imjmn, urx__ngw, lohgw__vravs))
    c.pyapi.decref(uly__abmp)
    c.pyapi.decref(sscpk__imjmn)
    c.pyapi.decref(urx__ngw)
    c.pyapi.decref(lohgw__vravs)
    c.pyapi.decref(zhf__kit)
    c.context.nrt.decref(c.builder, typ, val)
    return wjr__edcg


@intrinsic
def init_numeric_index(typingctx, data, name=None):
    name = types.none if is_overload_none(name) else name

    def codegen(context, builder, signature, args):
        assert len(args) == 2
        ngc__muj = signature.return_type
        eax__torbe = cgutils.create_struct_proxy(ngc__muj)(context, builder)
        eax__torbe.data = args[0]
        eax__torbe.name = args[1]
        context.nrt.incref(builder, ngc__muj.data, args[0])
        context.nrt.incref(builder, ngc__muj.name_typ, args[1])
        dtype = ngc__muj.dtype
        eax__torbe.dict = context.compile_internal(builder, lambda : numba.
            typed.Dict.empty(dtype, types.int64), types.DictType(dtype,
            types.int64)(), [])
        return eax__torbe._getvalue()
    return NumericIndexType(data.dtype, name, data)(data, name), codegen


(ArrayAnalysis._analyze_op_call_bodo_hiframes_pd_index_ext_init_numeric_index
    ) = init_index_equiv


@unbox(NumericIndexType)
def unbox_numeric_index(typ, val, c):
    yqtt__zyx = c.pyapi.object_getattr_string(val, 'values')
    data = c.pyapi.to_native_value(typ.data, yqtt__zyx).value
    lohgw__vravs = c.pyapi.object_getattr_string(val, 'name')
    name = c.pyapi.to_native_value(typ.name_typ, lohgw__vravs).value
    c.pyapi.decref(yqtt__zyx)
    c.pyapi.decref(lohgw__vravs)
    eax__torbe = cgutils.create_struct_proxy(typ)(c.context, c.builder)
    eax__torbe.data = data
    eax__torbe.name = name
    dtype = typ.dtype
    flm__uxwzn, gxpmb__hrb = c.pyapi.call_jit_code(lambda : numba.typed.
        Dict.empty(dtype, types.int64), types.DictType(dtype, types.int64)(
        ), [])
    eax__torbe.dict = gxpmb__hrb
    return NativeValue(eax__torbe._getvalue())


def create_numeric_constructor(func, func_str, default_dtype):

    def overload_impl(data=None, dtype=None, copy=False, name=None):
        ciu__bgu = dict(dtype=dtype)
        odydq__isaf = dict(dtype=None)
        check_unsupported_args(func_str, ciu__bgu, odydq__isaf,
            package_name='pandas', module_name='Index')
        if is_overload_false(copy):

            def impl(data=None, dtype=None, copy=False, name=None):
                umvj__qen = bodo.utils.conversion.coerce_to_ndarray(data)
                iuvan__hscer = bodo.utils.conversion.fix_arr_dtype(umvj__qen,
                    np.dtype(default_dtype))
                return bodo.hiframes.pd_index_ext.init_numeric_index(
                    iuvan__hscer, name)
        else:

            def impl(data=None, dtype=None, copy=False, name=None):
                umvj__qen = bodo.utils.conversion.coerce_to_ndarray(data)
                if copy:
                    umvj__qen = umvj__qen.copy()
                iuvan__hscer = bodo.utils.conversion.fix_arr_dtype(umvj__qen,
                    np.dtype(default_dtype))
                return bodo.hiframes.pd_index_ext.init_numeric_index(
                    iuvan__hscer, name)
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
        xov__rmbmt = [('data', fe_type.data), ('name', fe_type.name_typ), (
            'dict', types.DictType(string_type, types.int64))]
        super(StringIndexModel, self).__init__(dmm, fe_type, xov__rmbmt)


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
        xov__rmbmt = [('data', binary_array_type), ('name', fe_type.
            name_typ), ('dict', types.DictType(bytes_type, types.int64))]
        super(BinaryIndexModel, self).__init__(dmm, fe_type, xov__rmbmt)


make_attribute_wrapper(BinaryIndexType, 'data', '_data')
make_attribute_wrapper(BinaryIndexType, 'name', '_name')
make_attribute_wrapper(BinaryIndexType, 'dict', '_dict')


@unbox(BinaryIndexType)
@unbox(StringIndexType)
def unbox_binary_str_index(typ, val, c):
    ikx__rkafs = typ.data
    scalar_type = typ.data.dtype
    yqtt__zyx = c.pyapi.object_getattr_string(val, 'values')
    data = c.pyapi.to_native_value(ikx__rkafs, yqtt__zyx).value
    lohgw__vravs = c.pyapi.object_getattr_string(val, 'name')
    name = c.pyapi.to_native_value(typ.name_typ, lohgw__vravs).value
    c.pyapi.decref(yqtt__zyx)
    c.pyapi.decref(lohgw__vravs)
    eax__torbe = cgutils.create_struct_proxy(typ)(c.context, c.builder)
    eax__torbe.data = data
    eax__torbe.name = name
    flm__uxwzn, gxpmb__hrb = c.pyapi.call_jit_code(lambda : numba.typed.
        Dict.empty(scalar_type, types.int64), types.DictType(scalar_type,
        types.int64)(), [])
    eax__torbe.dict = gxpmb__hrb
    return NativeValue(eax__torbe._getvalue())


@box(BinaryIndexType)
@box(StringIndexType)
def box_binary_str_index(typ, val, c):
    ikx__rkafs = typ.data
    fgl__zvb = c.context.insert_const_string(c.builder.module, 'pandas')
    zhf__kit = c.pyapi.import_module_noblock(fgl__zvb)
    eax__torbe = cgutils.create_struct_proxy(typ)(c.context, c.builder, val)
    c.context.nrt.incref(c.builder, ikx__rkafs, eax__torbe.data)
    uly__abmp = c.pyapi.from_native_value(ikx__rkafs, eax__torbe.data, c.
        env_manager)
    c.context.nrt.incref(c.builder, typ.name_typ, eax__torbe.name)
    lohgw__vravs = c.pyapi.from_native_value(typ.name_typ, eax__torbe.name,
        c.env_manager)
    sscpk__imjmn = c.pyapi.make_none()
    urx__ngw = c.pyapi.bool_from_bool(c.context.get_constant(types.bool_, 
        False))
    wjr__edcg = c.pyapi.call_method(zhf__kit, 'Index', (uly__abmp,
        sscpk__imjmn, urx__ngw, lohgw__vravs))
    c.pyapi.decref(uly__abmp)
    c.pyapi.decref(sscpk__imjmn)
    c.pyapi.decref(urx__ngw)
    c.pyapi.decref(lohgw__vravs)
    c.pyapi.decref(zhf__kit)
    c.context.nrt.decref(c.builder, typ, val)
    return wjr__edcg


@intrinsic
def init_binary_str_index(typingctx, data, name=None):
    name = types.none if name is None else name
    sig = type(bodo.utils.typing.get_index_type_from_dtype(data.dtype))(name,
        data)(data, name)
    ucbf__qeko = get_binary_str_codegen(is_binary=data.dtype == bytes_type)
    return sig, ucbf__qeko


(ArrayAnalysis.
    _analyze_op_call_bodo_hiframes_pd_index_ext_init_binary_str_index
    ) = init_index_equiv


def get_binary_str_codegen(is_binary=False):
    if is_binary:
        wkei__rgpod = 'bytes_type'
    else:
        wkei__rgpod = 'string_type'
    rqumw__lytx = 'def impl(context, builder, signature, args):\n'
    rqumw__lytx += '    assert len(args) == 2\n'
    rqumw__lytx += '    index_typ = signature.return_type\n'
    rqumw__lytx += (
        '    index_val = cgutils.create_struct_proxy(index_typ)(context, builder)\n'
        )
    rqumw__lytx += '    index_val.data = args[0]\n'
    rqumw__lytx += '    index_val.name = args[1]\n'
    rqumw__lytx += '    # increase refcount of stored values\n'
    rqumw__lytx += (
        '    context.nrt.incref(builder, signature.args[0], args[0])\n')
    rqumw__lytx += (
        '    context.nrt.incref(builder, index_typ.name_typ, args[1])\n')
    rqumw__lytx += '    # create empty dict for get_loc hashmap\n'
    rqumw__lytx += '    index_val.dict = context.compile_internal(\n'
    rqumw__lytx += '       builder,\n'
    rqumw__lytx += (
        f'       lambda: numba.typed.Dict.empty({wkei__rgpod}, types.int64),\n'
        )
    rqumw__lytx += (
        f'        types.DictType({wkei__rgpod}, types.int64)(), [],)\n')
    rqumw__lytx += '    return index_val._getvalue()\n'
    ibq__mgcs = {}
    exec(rqumw__lytx, {'bodo': bodo, 'signature': signature, 'cgutils':
        cgutils, 'numba': numba, 'types': types, 'bytes_type': bytes_type,
        'string_type': string_type}, ibq__mgcs)
    impl = ibq__mgcs['impl']
    return impl


@overload_method(BinaryIndexType, 'copy', no_unliteral=True)
@overload_method(StringIndexType, 'copy', no_unliteral=True)
def overload_binary_string_index_copy(A, name=None, deep=False, dtype=None,
    names=None):
    typ = type(A)
    nnwq__vgapz = idx_typ_to_format_str_map[typ].format('copy()')
    qumr__nejw = dict(deep=deep, dtype=dtype, names=names)
    check_unsupported_args('Index.copy', qumr__nejw, idx_cpy_arg_defaults,
        fn_str=nnwq__vgapz, package_name='pandas', module_name='Index')
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
    dfbxq__jtb = dict(axis=axis, allow_fill=allow_fill, fill_value=fill_value)
    rgobh__riamv = dict(axis=0, allow_fill=True, fill_value=None)
    check_unsupported_args('Index.take', dfbxq__jtb, rgobh__riamv,
        package_name='pandas', module_name='Index')
    return lambda I, indices: I[indices]


@numba.njit(no_cpython_wrapper=True)
def _init_engine(I):
    if len(I) > 0 and not I._dict:
        qqkk__pngrz = bodo.utils.conversion.coerce_to_array(I)
        for i in range(len(qqkk__pngrz)):
            val = qqkk__pngrz[i]
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
            stzrf__zgk = (
                'Global Index objects can be slow (pass as argument to JIT function for better performance).'
                )
            warnings.warn(stzrf__zgk)
            qqkk__pngrz = bodo.utils.conversion.coerce_to_array(I)
            ind = -1
            for i in range(len(qqkk__pngrz)):
                if qqkk__pngrz[i] == key:
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
    dfbxq__jtb = dict(method=method, tolerance=tolerance)
    izzuy__jgfb = dict(method=None, tolerance=None)
    check_unsupported_args('Index.get_loc', dfbxq__jtb, izzuy__jgfb,
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
            stzrf__zgk = (
                'Index.get_loc() can be slow for global Index objects (pass as argument to JIT function for better performance).'
                )
            warnings.warn(stzrf__zgk)
            qqkk__pngrz = bodo.utils.conversion.coerce_to_array(I)
            ind = -1
            for i in range(len(qqkk__pngrz)):
                if qqkk__pngrz[i] == key:
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
        oph__askc = overload_name in {'isna', 'isnull'}
        if isinstance(I, RangeIndexType):

            def impl(I):
                numba.parfors.parfor.init_prange()
                kqb__hylq = len(I)
                gttl__uyce = np.empty(kqb__hylq, np.bool_)
                for i in numba.parfors.parfor.internal_prange(kqb__hylq):
                    gttl__uyce[i] = not oph__askc
                return gttl__uyce
            return impl
        rqumw__lytx = f"""def impl(I):
    numba.parfors.parfor.init_prange()
    arr = bodo.hiframes.pd_index_ext.get_index_data(I)
    n = len(arr)
    out_arr = np.empty(n, np.bool_)
    for i in numba.parfors.parfor.internal_prange(n):
       out_arr[i] = {'' if oph__askc else 'not '}bodo.libs.array_kernels.isna(arr, i)
    return out_arr
"""
        ibq__mgcs = {}
        exec(rqumw__lytx, {'bodo': bodo, 'np': np, 'numba': numba}, ibq__mgcs)
        impl = ibq__mgcs['impl']
        return impl
    return overload_index_isna_specific_method


isna_overload_types = (RangeIndexType, NumericIndexType, StringIndexType,
    BinaryIndexType, CategoricalIndexType, PeriodIndexType,
    DatetimeIndexType, TimedeltaIndexType)
isna_specific_methods = 'isna', 'notna', 'isnull', 'notnull'


def _install_isna_specific_methods():
    for colhm__fkt in isna_overload_types:
        for overload_name in isna_specific_methods:
            overload_impl = create_isna_specific_method(overload_name)
            overload_method(colhm__fkt, overload_name, no_unliteral=True,
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
            qqkk__pngrz = bodo.hiframes.pd_index_ext.get_index_data(I)
            return bodo.libs.array_kernels.series_monotonicity(qqkk__pngrz, 1)
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
            qqkk__pngrz = bodo.hiframes.pd_index_ext.get_index_data(I)
            return bodo.libs.array_kernels.series_monotonicity(qqkk__pngrz, 2)
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
        qqkk__pngrz = bodo.hiframes.pd_index_ext.get_index_data(I)
        gttl__uyce = bodo.libs.array_kernels.duplicated((qqkk__pngrz,))
        return gttl__uyce
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
    dfbxq__jtb = dict(keep=keep)
    izzuy__jgfb = dict(keep='first')
    check_unsupported_args('Index.drop_duplicates', dfbxq__jtb, izzuy__jgfb,
        package_name='pandas', module_name='Index')
    if isinstance(I, RangeIndexType):
        return lambda I, keep='first': I.copy()
    rqumw__lytx = """def impl(I, keep='first'):
    data = bodo.hiframes.pd_index_ext.get_index_data(I)
    arr = bodo.libs.array_kernels.drop_duplicates_array(data)
    name = bodo.hiframes.pd_index_ext.get_index_name(I)
"""
    if isinstance(I, PeriodIndexType):
        rqumw__lytx += f"""    return bodo.hiframes.pd_index_ext.init_period_index(arr, name, '{I.freq}')
"""
    else:
        rqumw__lytx += (
            '    return bodo.utils.conversion.index_from_array(arr, name)')
    ibq__mgcs = {}
    exec(rqumw__lytx, {'bodo': bodo}, ibq__mgcs)
    impl = ibq__mgcs['impl']
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
    peze__knlz = args[0]
    if isinstance(self.typemap[peze__knlz.name], HeterogeneousIndexType):
        return None
    if equiv_set.has_shape(peze__knlz):
        return ArrayAnalysis.AnalyzeResult(shape=peze__knlz, pre=[])
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
    dfbxq__jtb = dict(na_action=na_action)
    yeajd__vjj = dict(na_action=None)
    check_unsupported_args('Index.map', dfbxq__jtb, yeajd__vjj,
        package_name='pandas', module_name='Index')
    dtype = I.dtype
    bodo.hiframes.pd_timestamp_ext.check_tz_aware_unsupported(I,
        'DatetimeIndex.map')
    if dtype == types.NPDatetime('ns'):
        dtype = pd_timestamp_type
    if dtype == types.NPTimedelta('ns'):
        dtype = pd_timedelta_type
    if isinstance(dtype, bodo.hiframes.pd_categorical_ext.PDCategoricalDtype):
        dtype = dtype.elem_type
    niwrt__jin = numba.core.registry.cpu_target.typing_context
    amc__dtf = numba.core.registry.cpu_target.target_context
    try:
        jkf__idc = get_const_func_output_type(mapper, (dtype,), {},
            niwrt__jin, amc__dtf)
    except Exception as obf__wglve:
        raise_bodo_error(get_udf_error_msg('Index.map()', obf__wglve))
    ogfzt__miu = get_udf_out_arr_type(jkf__idc)
    func = get_overload_const_func(mapper, None)
    rqumw__lytx = 'def f(I, mapper, na_action=None):\n'
    rqumw__lytx += '  name = bodo.hiframes.pd_index_ext.get_index_name(I)\n'
    rqumw__lytx += '  A = bodo.utils.conversion.coerce_to_array(I)\n'
    rqumw__lytx += '  numba.parfors.parfor.init_prange()\n'
    rqumw__lytx += '  n = len(A)\n'
    rqumw__lytx += '  S = bodo.utils.utils.alloc_type(n, _arr_typ, (-1,))\n'
    rqumw__lytx += '  for i in numba.parfors.parfor.internal_prange(n):\n'
    rqumw__lytx += '    t2 = bodo.utils.conversion.box_if_dt64(A[i])\n'
    rqumw__lytx += '    v = map_func(t2)\n'
    rqumw__lytx += '    S[i] = bodo.utils.conversion.unbox_if_timestamp(v)\n'
    rqumw__lytx += '  return bodo.utils.conversion.index_from_array(S, name)\n'
    bbny__ysycc = bodo.compiler.udf_jit(func)
    ibq__mgcs = {}
    exec(rqumw__lytx, {'numba': numba, 'np': np, 'pd': pd, 'bodo': bodo,
        'map_func': bbny__ysycc, '_arr_typ': ogfzt__miu,
        'init_nested_counts': bodo.utils.indexing.init_nested_counts,
        'add_nested_counts': bodo.utils.indexing.add_nested_counts,
        'data_arr_type': ogfzt__miu.dtype}, ibq__mgcs)
    f = ibq__mgcs['f']
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
    pmic__qqne, ooz__dwdm = sig.args
    if pmic__qqne != ooz__dwdm:
        return cgutils.false_bit

    def index_is_impl(a, b):
        return a._data is b._data and a._name is b._name
    return context.compile_internal(builder, index_is_impl, sig, args)


@lower_builtin(operator.is_, RangeIndexType, RangeIndexType)
def range_index_is(context, builder, sig, args):
    pmic__qqne, ooz__dwdm = sig.args
    if pmic__qqne != ooz__dwdm:
        return cgutils.false_bit

    def index_is_impl(a, b):
        return (a._start == b._start and a._stop == b._stop and a._step ==
            b._step and a._name is b._name)
    return context.compile_internal(builder, index_is_impl, sig, args)


def create_binary_op_overload(op):

    def overload_index_binary_op(lhs, rhs):
        if is_index_type(lhs):
            rqumw__lytx = """def impl(lhs, rhs):
  arr = bodo.utils.conversion.coerce_to_array(lhs)
"""
            if rhs in [bodo.hiframes.pd_timestamp_ext.pd_timestamp_type,
                bodo.hiframes.pd_timestamp_ext.pd_timedelta_type]:
                rqumw__lytx += """  dt = bodo.utils.conversion.unbox_if_timestamp(rhs)
  return op(arr, dt)
"""
            else:
                rqumw__lytx += """  rhs_arr = bodo.utils.conversion.get_array_if_series_or_index(rhs)
  return op(arr, rhs_arr)
"""
            ibq__mgcs = {}
            exec(rqumw__lytx, {'bodo': bodo, 'op': op}, ibq__mgcs)
            impl = ibq__mgcs['impl']
            return impl
        if is_index_type(rhs):
            rqumw__lytx = """def impl(lhs, rhs):
  arr = bodo.utils.conversion.coerce_to_array(rhs)
"""
            if lhs in [bodo.hiframes.pd_timestamp_ext.pd_timestamp_type,
                bodo.hiframes.pd_timestamp_ext.pd_timedelta_type]:
                rqumw__lytx += """  dt = bodo.utils.conversion.unbox_if_timestamp(lhs)
  return op(dt, arr)
"""
            else:
                rqumw__lytx += """  lhs_arr = bodo.utils.conversion.get_array_if_series_or_index(lhs)
  return op(lhs_arr, arr)
"""
            ibq__mgcs = {}
            exec(rqumw__lytx, {'bodo': bodo, 'op': op}, ibq__mgcs)
            impl = ibq__mgcs['impl']
            return impl
        if isinstance(lhs, HeterogeneousIndexType):
            if not is_heterogeneous_tuple_type(lhs.data):

                def impl3(lhs, rhs):
                    data = bodo.utils.conversion.coerce_to_array(lhs)
                    qqkk__pngrz = bodo.utils.conversion.coerce_to_array(data)
                    dfyiy__cgzs = (bodo.utils.conversion.
                        get_array_if_series_or_index(rhs))
                    gttl__uyce = op(qqkk__pngrz, dfyiy__cgzs)
                    return gttl__uyce
                return impl3
            count = len(lhs.data.types)
            rqumw__lytx = 'def f(lhs, rhs):\n'
            rqumw__lytx += '  return [{}]\n'.format(','.join(
                'op(lhs[{}], rhs{})'.format(i, f'[{i}]' if is_iterable_type
                (rhs) else '') for i in range(count)))
            ibq__mgcs = {}
            exec(rqumw__lytx, {'op': op, 'np': np}, ibq__mgcs)
            impl = ibq__mgcs['f']
            return impl
        if isinstance(rhs, HeterogeneousIndexType):
            if not is_heterogeneous_tuple_type(rhs.data):

                def impl4(lhs, rhs):
                    data = bodo.hiframes.pd_index_ext.get_index_data(rhs)
                    qqkk__pngrz = bodo.utils.conversion.coerce_to_array(data)
                    dfyiy__cgzs = (bodo.utils.conversion.
                        get_array_if_series_or_index(lhs))
                    gttl__uyce = op(dfyiy__cgzs, qqkk__pngrz)
                    return gttl__uyce
                return impl4
            count = len(rhs.data.types)
            rqumw__lytx = 'def f(lhs, rhs):\n'
            rqumw__lytx += '  return [{}]\n'.format(','.join(
                'op(lhs{}, rhs[{}])'.format(f'[{i}]' if is_iterable_type(
                lhs) else '', i) for i in range(count)))
            ibq__mgcs = {}
            exec(rqumw__lytx, {'op': op, 'np': np}, ibq__mgcs)
            impl = ibq__mgcs['f']
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
        xov__rmbmt = [('data', fe_type.data), ('name', fe_type.name_typ)]
        super(HeterogeneousIndexModel, self).__init__(dmm, fe_type, xov__rmbmt)


make_attribute_wrapper(HeterogeneousIndexType, 'data', '_data')
make_attribute_wrapper(HeterogeneousIndexType, 'name', '_name')


@overload_method(HeterogeneousIndexType, 'copy', no_unliteral=True)
def overload_heter_index_copy(A, name=None, deep=False, dtype=None, names=None
    ):
    nnwq__vgapz = idx_typ_to_format_str_map[HeterogeneousIndexType].format(
        'copy()')
    qumr__nejw = dict(deep=deep, dtype=dtype, names=names)
    check_unsupported_args('Index.copy', qumr__nejw, idx_cpy_arg_defaults,
        fn_str=nnwq__vgapz, package_name='pandas', module_name='Index')
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
    fgl__zvb = c.context.insert_const_string(c.builder.module, 'pandas')
    zhf__kit = c.pyapi.import_module_noblock(fgl__zvb)
    eax__torbe = cgutils.create_struct_proxy(typ)(c.context, c.builder, val)
    c.context.nrt.incref(c.builder, typ.data, eax__torbe.data)
    uly__abmp = c.pyapi.from_native_value(typ.data, eax__torbe.data, c.
        env_manager)
    c.context.nrt.incref(c.builder, typ.name_typ, eax__torbe.name)
    lohgw__vravs = c.pyapi.from_native_value(typ.name_typ, eax__torbe.name,
        c.env_manager)
    sscpk__imjmn = c.pyapi.make_none()
    urx__ngw = c.pyapi.bool_from_bool(c.context.get_constant(types.bool_, 
        False))
    wjr__edcg = c.pyapi.call_method(zhf__kit, 'Index', (uly__abmp,
        sscpk__imjmn, urx__ngw, lohgw__vravs))
    c.pyapi.decref(uly__abmp)
    c.pyapi.decref(sscpk__imjmn)
    c.pyapi.decref(urx__ngw)
    c.pyapi.decref(lohgw__vravs)
    c.pyapi.decref(zhf__kit)
    c.context.nrt.decref(c.builder, typ, val)
    return wjr__edcg


@intrinsic
def init_heter_index(typingctx, data, name=None):
    name = types.none if name is None else name

    def codegen(context, builder, signature, args):
        assert len(args) == 2
        ngc__muj = signature.return_type
        eax__torbe = cgutils.create_struct_proxy(ngc__muj)(context, builder)
        eax__torbe.data = args[0]
        eax__torbe.name = args[1]
        context.nrt.incref(builder, ngc__muj.data, args[0])
        context.nrt.incref(builder, ngc__muj.name_typ, args[1])
        return eax__torbe._getvalue()
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
    xcdsb__skqcc = {NumericIndexType: bodo.hiframes.pd_index_ext.
        init_numeric_index, DatetimeIndexType: bodo.hiframes.pd_index_ext.
        init_datetime_index, TimedeltaIndexType: bodo.hiframes.pd_index_ext
        .init_timedelta_index, StringIndexType: bodo.hiframes.pd_index_ext.
        init_binary_str_index, BinaryIndexType: bodo.hiframes.pd_index_ext.
        init_binary_str_index, CategoricalIndexType: bodo.hiframes.
        pd_index_ext.init_categorical_index, IntervalIndexType: bodo.
        hiframes.pd_index_ext.init_interval_index}
    if type(I) in xcdsb__skqcc:
        init_func = xcdsb__skqcc[type(I)]
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
    tram__ywhp = context.get_constant_null(types.DictType(dtype, types.int64))
    return lir.Constant.literal_struct([data, name, tram__ywhp])


@lower_constant(PeriodIndexType)
def lower_constant_period_index(context, builder, ty, pyval):
    data = context.get_constant_generic(builder, bodo.IntegerArrayType(
        types.int64), pd.arrays.IntegerArray(pyval.asi8, pyval.isna()))
    name = context.get_constant_generic(builder, ty.name_typ, pyval.name)
    tram__ywhp = context.get_constant_null(types.DictType(types.int64,
        types.int64))
    return lir.Constant.literal_struct([data, name, tram__ywhp])


@lower_constant(NumericIndexType)
def lower_constant_numeric_index(context, builder, ty, pyval):
    assert isinstance(ty.dtype, (types.Integer, types.Float, types.Boolean))
    data = context.get_constant_generic(builder, types.Array(ty.dtype, 1,
        'C'), pyval.values)
    name = context.get_constant_generic(builder, ty.name_typ, pyval.name)
    dtype = ty.dtype
    tram__ywhp = context.get_constant_null(types.DictType(dtype, types.int64))
    return lir.Constant.literal_struct([data, name, tram__ywhp])


@lower_constant(StringIndexType)
@lower_constant(BinaryIndexType)
def lower_constant_binary_string_index(context, builder, ty, pyval):
    ikx__rkafs = ty.data
    scalar_type = ty.data.dtype
    data = context.get_constant_generic(builder, ikx__rkafs, pyval.values)
    name = context.get_constant_generic(builder, ty.name_typ, pyval.name)
    tram__ywhp = context.get_constant_null(types.DictType(scalar_type,
        types.int64))
    return lir.Constant.literal_struct([data, name, tram__ywhp])


@lower_builtin('getiter', RangeIndexType)
def getiter_range_index(context, builder, sig, args):
    [omzbc__zol] = sig.args
    [tsq__mzik] = args
    ygfev__wlh = context.make_helper(builder, omzbc__zol, value=tsq__mzik)
    afaqq__mplrr = context.make_helper(builder, sig.return_type)
    vlk__kcd = cgutils.alloca_once_value(builder, ygfev__wlh.start)
    irsh__ftt = context.get_constant(types.intp, 0)
    sov__pxka = cgutils.alloca_once_value(builder, irsh__ftt)
    afaqq__mplrr.iter = vlk__kcd
    afaqq__mplrr.stop = ygfev__wlh.stop
    afaqq__mplrr.step = ygfev__wlh.step
    afaqq__mplrr.count = sov__pxka
    ynpo__kft = builder.sub(ygfev__wlh.stop, ygfev__wlh.start)
    ffx__phrsg = context.get_constant(types.intp, 1)
    ogc__fyr = builder.icmp(lc.ICMP_SGT, ynpo__kft, irsh__ftt)
    powfi__mxt = builder.icmp(lc.ICMP_SGT, ygfev__wlh.step, irsh__ftt)
    bgw__ljwu = builder.not_(builder.xor(ogc__fyr, powfi__mxt))
    with builder.if_then(bgw__ljwu):
        lre__afm = builder.srem(ynpo__kft, ygfev__wlh.step)
        lre__afm = builder.select(ogc__fyr, lre__afm, builder.neg(lre__afm))
        bnz__idakv = builder.icmp(lc.ICMP_SGT, lre__afm, irsh__ftt)
        tphob__aqkbm = builder.add(builder.sdiv(ynpo__kft, ygfev__wlh.step),
            builder.select(bnz__idakv, ffx__phrsg, irsh__ftt))
        builder.store(tphob__aqkbm, sov__pxka)
    eri__aei = afaqq__mplrr._getvalue()
    icjev__qpgjf = impl_ret_new_ref(context, builder, sig.return_type, eri__aei
        )
    return icjev__qpgjf


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
    for eda__dqc in index_unsupported_methods:
        for eypf__crfh, typ in index_types:
            overload_method(typ, eda__dqc, no_unliteral=True)(
                create_unsupported_overload(eypf__crfh.format(eda__dqc + '()'))
                )
    for puoal__goq in index_unsupported_atrs:
        for eypf__crfh, typ in index_types:
            overload_attribute(typ, puoal__goq, no_unliteral=True)(
                create_unsupported_overload(eypf__crfh.format(puoal__goq)))
    hnvi__mksjk = [(StringIndexType, string_index_unsupported_atrs), (
        BinaryIndexType, binary_index_unsupported_atrs), (
        CategoricalIndexType, cat_idx_unsupported_atrs), (IntervalIndexType,
        interval_idx_unsupported_atrs), (MultiIndexType,
        multi_index_unsupported_atrs), (DatetimeIndexType,
        dt_index_unsupported_atrs), (TimedeltaIndexType,
        td_index_unsupported_atrs), (PeriodIndexType,
        period_index_unsupported_atrs)]
    igi__jinc = [(CategoricalIndexType, cat_idx_unsupported_methods), (
        IntervalIndexType, interval_idx_unsupported_methods), (
        MultiIndexType, multi_index_unsupported_methods), (
        DatetimeIndexType, dt_index_unsupported_methods), (
        TimedeltaIndexType, td_index_unsupported_methods), (PeriodIndexType,
        period_index_unsupported_methods)]
    for typ, vrjz__dvs in igi__jinc:
        eypf__crfh = idx_typ_to_format_str_map[typ]
        for rui__xxllf in vrjz__dvs:
            overload_method(typ, rui__xxllf, no_unliteral=True)(
                create_unsupported_overload(eypf__crfh.format(rui__xxllf +
                '()')))
    for typ, cyc__amoqu in hnvi__mksjk:
        eypf__crfh = idx_typ_to_format_str_map[typ]
        for puoal__goq in cyc__amoqu:
            overload_attribute(typ, puoal__goq, no_unliteral=True)(
                create_unsupported_overload(eypf__crfh.format(puoal__goq)))
    for cvsj__oudqo in [RangeIndexType, NumericIndexType, StringIndexType,
        BinaryIndexType, IntervalIndexType, CategoricalIndexType,
        PeriodIndexType, MultiIndexType]:
        for rui__xxllf in ['max', 'min']:
            eypf__crfh = idx_typ_to_format_str_map[cvsj__oudqo]
            overload_method(cvsj__oudqo, rui__xxllf, no_unliteral=True)(
                create_unsupported_overload(eypf__crfh.format(rui__xxllf +
                '()')))


_install_index_unsupported()
