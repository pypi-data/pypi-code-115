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
        tjm__lvfoe = [('data', fe_type.data), ('name', fe_type.name_typ), (
            'dict', types.DictType(_dt_index_data_typ.dtype, types.int64))]
        super(DatetimeIndexModel, self).__init__(dmm, fe_type, tjm__lvfoe)


make_attribute_wrapper(DatetimeIndexType, 'data', '_data')
make_attribute_wrapper(DatetimeIndexType, 'name', '_name')
make_attribute_wrapper(DatetimeIndexType, 'dict', '_dict')


@overload_method(DatetimeIndexType, 'copy', no_unliteral=True)
def overload_datetime_index_copy(A, name=None, deep=False, dtype=None,
    names=None):
    tfc__wge = dict(deep=deep, dtype=dtype, names=names)
    hxy__qkqgr = idx_typ_to_format_str_map[DatetimeIndexType].format('copy()')
    check_unsupported_args('copy', tfc__wge, idx_cpy_arg_defaults, fn_str=
        hxy__qkqgr, package_name='pandas', module_name='Index')
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
    hth__aarjq = c.context.insert_const_string(c.builder.module, 'pandas')
    spreo__avjz = c.pyapi.import_module_noblock(hth__aarjq)
    hao__jhrbz = numba.core.cgutils.create_struct_proxy(typ)(c.context, c.
        builder, val)
    c.context.nrt.incref(c.builder, typ.data, hao__jhrbz.data)
    kfs__pnckl = c.pyapi.from_native_value(typ.data, hao__jhrbz.data, c.
        env_manager)
    c.context.nrt.incref(c.builder, typ.name_typ, hao__jhrbz.name)
    amou__uchkv = c.pyapi.from_native_value(typ.name_typ, hao__jhrbz.name,
        c.env_manager)
    args = c.pyapi.tuple_pack([kfs__pnckl])
    qyj__qgrty = c.pyapi.object_getattr_string(spreo__avjz, 'DatetimeIndex')
    kws = c.pyapi.dict_pack([('name', amou__uchkv)])
    qrqq__pqa = c.pyapi.call(qyj__qgrty, args, kws)
    c.pyapi.decref(kfs__pnckl)
    c.pyapi.decref(amou__uchkv)
    c.pyapi.decref(spreo__avjz)
    c.pyapi.decref(qyj__qgrty)
    c.pyapi.decref(args)
    c.pyapi.decref(kws)
    c.context.nrt.decref(c.builder, typ, val)
    return qrqq__pqa


@unbox(DatetimeIndexType)
def unbox_datetime_index(typ, val, c):
    if isinstance(typ.data, DatetimeArrayType):
        fdxy__css = c.pyapi.object_getattr_string(val, 'array')
    else:
        fdxy__css = c.pyapi.object_getattr_string(val, 'values')
    data = c.pyapi.to_native_value(typ.data, fdxy__css).value
    amou__uchkv = c.pyapi.object_getattr_string(val, 'name')
    name = c.pyapi.to_native_value(typ.name_typ, amou__uchkv).value
    hhw__eisvp = cgutils.create_struct_proxy(typ)(c.context, c.builder)
    hhw__eisvp.data = data
    hhw__eisvp.name = name
    dtype = _dt_index_data_typ.dtype
    acs__glaz, kvqz__tcwt = c.pyapi.call_jit_code(lambda : numba.typed.Dict
        .empty(dtype, types.int64), types.DictType(dtype, types.int64)(), [])
    hhw__eisvp.dict = kvqz__tcwt
    c.pyapi.decref(fdxy__css)
    c.pyapi.decref(amou__uchkv)
    return NativeValue(hhw__eisvp._getvalue())


@intrinsic
def init_datetime_index(typingctx, data, name):
    name = types.none if name is None else name

    def codegen(context, builder, signature, args):
        xxt__bezu, fxkiw__qcve = args
        hao__jhrbz = cgutils.create_struct_proxy(signature.return_type)(context
            , builder)
        hao__jhrbz.data = xxt__bezu
        hao__jhrbz.name = fxkiw__qcve
        context.nrt.incref(builder, signature.args[0], xxt__bezu)
        context.nrt.incref(builder, signature.args[1], fxkiw__qcve)
        dtype = _dt_index_data_typ.dtype
        hao__jhrbz.dict = context.compile_internal(builder, lambda : numba.
            typed.Dict.empty(dtype, types.int64), types.DictType(dtype,
            types.int64)(), [])
        return hao__jhrbz._getvalue()
    gyqdm__ywx = DatetimeIndexType(name, data)
    sig = signature(gyqdm__ywx, data, name)
    return sig, codegen


def init_index_equiv(self, scope, equiv_set, loc, args, kws):
    assert len(args) >= 1 and not kws
    gtvf__ygjfm = args[0]
    if equiv_set.has_shape(gtvf__ygjfm):
        return ArrayAnalysis.AnalyzeResult(shape=gtvf__ygjfm, pre=[])
    return None


(ArrayAnalysis._analyze_op_call_bodo_hiframes_pd_index_ext_init_datetime_index
    ) = init_index_equiv


def gen_dti_field_impl(field):
    prfxn__ely = 'def impl(dti):\n'
    prfxn__ely += '    numba.parfors.parfor.init_prange()\n'
    prfxn__ely += '    A = bodo.hiframes.pd_index_ext.get_index_data(dti)\n'
    prfxn__ely += '    name = bodo.hiframes.pd_index_ext.get_index_name(dti)\n'
    prfxn__ely += '    n = len(A)\n'
    prfxn__ely += '    S = np.empty(n, np.int64)\n'
    prfxn__ely += '    for i in numba.parfors.parfor.internal_prange(n):\n'
    prfxn__ely += '        val = A[i]\n'
    prfxn__ely += '        ts = bodo.utils.conversion.box_if_dt64(val)\n'
    if field in ['weekday']:
        prfxn__ely += '        S[i] = ts.' + field + '()\n'
    else:
        prfxn__ely += '        S[i] = ts.' + field + '\n'
    prfxn__ely += (
        '    return bodo.hiframes.pd_index_ext.init_numeric_index(S, name)\n')
    igxy__ymmm = {}
    exec(prfxn__ely, {'numba': numba, 'np': np, 'bodo': bodo}, igxy__ymmm)
    impl = igxy__ymmm['impl']
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
        jblrw__yysf = len(A)
        S = np.empty(jblrw__yysf, np.bool_)
        for i in numba.parfors.parfor.internal_prange(jblrw__yysf):
            val = A[i]
            paw__irwzl = bodo.utils.conversion.box_if_dt64(val)
            S[i] = bodo.hiframes.pd_timestamp_ext.is_leap_year(paw__irwzl.year)
        return S
    return impl


@overload_attribute(DatetimeIndexType, 'date')
def overload_datetime_index_date(dti):

    def impl(dti):
        numba.parfors.parfor.init_prange()
        A = bodo.hiframes.pd_index_ext.get_index_data(dti)
        jblrw__yysf = len(A)
        S = bodo.hiframes.datetime_date_ext.alloc_datetime_date_array(
            jblrw__yysf)
        for i in numba.parfors.parfor.internal_prange(jblrw__yysf):
            val = A[i]
            paw__irwzl = bodo.utils.conversion.box_if_dt64(val)
            S[i] = datetime.date(paw__irwzl.year, paw__irwzl.month,
                paw__irwzl.day)
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
    irn__yjzud = dict(axis=axis, skipna=skipna)
    teagu__tcwtq = dict(axis=None, skipna=True)
    check_unsupported_args('DatetimeIndex.min', irn__yjzud, teagu__tcwtq,
        package_name='pandas', module_name='Index')
    bodo.hiframes.pd_timestamp_ext.check_tz_aware_unsupported(dti,
        'Index.min()')

    def impl(dti, axis=None, skipna=True):
        numba.parfors.parfor.init_prange()
        rbz__qbfo = bodo.hiframes.pd_index_ext.get_index_data(dti)
        s = numba.cpython.builtins.get_type_max_value(numba.core.types.int64)
        count = 0
        for i in numba.parfors.parfor.internal_prange(len(rbz__qbfo)):
            if not bodo.libs.array_kernels.isna(rbz__qbfo, i):
                val = bodo.hiframes.pd_timestamp_ext.dt64_to_integer(rbz__qbfo
                    [i])
                s = min(s, val)
                count += 1
        return bodo.hiframes.pd_index_ext._dti_val_finalize(s, count)
    return impl


@overload_method(DatetimeIndexType, 'max', no_unliteral=True)
def overload_datetime_index_max(dti, axis=None, skipna=True):
    irn__yjzud = dict(axis=axis, skipna=skipna)
    teagu__tcwtq = dict(axis=None, skipna=True)
    check_unsupported_args('DatetimeIndex.max', irn__yjzud, teagu__tcwtq,
        package_name='pandas', module_name='Index')
    bodo.hiframes.pd_timestamp_ext.check_tz_aware_unsupported(dti,
        'Index.max()')

    def impl(dti, axis=None, skipna=True):
        numba.parfors.parfor.init_prange()
        rbz__qbfo = bodo.hiframes.pd_index_ext.get_index_data(dti)
        s = numba.cpython.builtins.get_type_min_value(numba.core.types.int64)
        count = 0
        for i in numba.parfors.parfor.internal_prange(len(rbz__qbfo)):
            if not bodo.libs.array_kernels.isna(rbz__qbfo, i):
                val = bodo.hiframes.pd_timestamp_ext.dt64_to_integer(rbz__qbfo
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
    irn__yjzud = dict(freq=freq, tz=tz, normalize=normalize, closed=closed,
        ambiguous=ambiguous, dayfirst=dayfirst, yearfirst=yearfirst, dtype=
        dtype, copy=copy)
    teagu__tcwtq = dict(freq=None, tz=None, normalize=False, closed=None,
        ambiguous='raise', dayfirst=False, yearfirst=False, dtype=None,
        copy=False)
    check_unsupported_args('pandas.DatetimeIndex', irn__yjzud, teagu__tcwtq,
        package_name='pandas', module_name='Index')

    def f(data=None, freq=None, tz=None, normalize=False, closed=None,
        ambiguous='raise', dayfirst=False, yearfirst=False, dtype=None,
        copy=False, name=None):
        bqtn__fngsm = bodo.utils.conversion.coerce_to_array(data)
        S = bodo.utils.conversion.convert_to_dt64ns(bqtn__fngsm)
        return bodo.hiframes.pd_index_ext.init_datetime_index(S, name)
    return f


def overload_sub_operator_datetime_index(lhs, rhs):
    if isinstance(lhs, DatetimeIndexType
        ) and rhs == bodo.hiframes.pd_timestamp_ext.pd_timestamp_type:
        ezj__ukrov = np.dtype('timedelta64[ns]')

        def impl(lhs, rhs):
            numba.parfors.parfor.init_prange()
            rbz__qbfo = bodo.hiframes.pd_index_ext.get_index_data(lhs)
            name = bodo.hiframes.pd_index_ext.get_index_name(lhs)
            jblrw__yysf = len(rbz__qbfo)
            S = np.empty(jblrw__yysf, ezj__ukrov)
            svq__vqs = rhs.value
            for i in numba.parfors.parfor.internal_prange(jblrw__yysf):
                S[i] = bodo.hiframes.pd_timestamp_ext.integer_to_timedelta64(
                    bodo.hiframes.pd_timestamp_ext.dt64_to_integer(
                    rbz__qbfo[i]) - svq__vqs)
            return bodo.hiframes.pd_index_ext.init_timedelta_index(S, name)
        return impl
    if isinstance(rhs, DatetimeIndexType
        ) and lhs == bodo.hiframes.pd_timestamp_ext.pd_timestamp_type:
        ezj__ukrov = np.dtype('timedelta64[ns]')

        def impl(lhs, rhs):
            numba.parfors.parfor.init_prange()
            rbz__qbfo = bodo.hiframes.pd_index_ext.get_index_data(rhs)
            name = bodo.hiframes.pd_index_ext.get_index_name(rhs)
            jblrw__yysf = len(rbz__qbfo)
            S = np.empty(jblrw__yysf, ezj__ukrov)
            svq__vqs = lhs.value
            for i in numba.parfors.parfor.internal_prange(jblrw__yysf):
                S[i] = bodo.hiframes.pd_timestamp_ext.integer_to_timedelta64(
                    svq__vqs - bodo.hiframes.pd_timestamp_ext.
                    dt64_to_integer(rbz__qbfo[i]))
            return bodo.hiframes.pd_index_ext.init_timedelta_index(S, name)
        return impl


def gen_dti_str_binop_impl(op, is_lhs_dti):
    lark__cnmt = numba.core.utils.OPERATORS_TO_BUILTINS[op]
    prfxn__ely = 'def impl(lhs, rhs):\n'
    if is_lhs_dti:
        prfxn__ely += '  dt_index, _str = lhs, rhs\n'
        hov__wopk = 'arr[i] {} other'.format(lark__cnmt)
    else:
        prfxn__ely += '  dt_index, _str = rhs, lhs\n'
        hov__wopk = 'other {} arr[i]'.format(lark__cnmt)
    prfxn__ely += (
        '  arr = bodo.hiframes.pd_index_ext.get_index_data(dt_index)\n')
    prfxn__ely += '  l = len(arr)\n'
    prfxn__ely += (
        '  other = bodo.hiframes.pd_timestamp_ext.parse_datetime_str(_str)\n')
    prfxn__ely += '  S = bodo.libs.bool_arr_ext.alloc_bool_array(l)\n'
    prfxn__ely += '  for i in numba.parfors.parfor.internal_prange(l):\n'
    prfxn__ely += '    S[i] = {}\n'.format(hov__wopk)
    prfxn__ely += '  return S\n'
    igxy__ymmm = {}
    exec(prfxn__ely, {'bodo': bodo, 'numba': numba, 'np': np}, igxy__ymmm)
    impl = igxy__ymmm['impl']
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
    harci__mkd = getattr(data, 'dtype', None)
    if not is_overload_none(dtype):
        mifyr__xeblz = parse_dtype(dtype, 'pandas.Index')
    else:
        mifyr__xeblz = harci__mkd
    if isinstance(mifyr__xeblz, types.misc.PyObject):
        raise BodoError(
            "pd.Index() object 'dtype' is not specific enough for typing. Please provide a more exact type (e.g. str)."
            )
    if isinstance(data, RangeIndexType):

        def impl(data=None, dtype=None, copy=False, name=None,
            tupleize_cols=True):
            return pd.RangeIndex(data, name=name)
    elif isinstance(data, DatetimeIndexType
        ) or mifyr__xeblz == types.NPDatetime('ns'):

        def impl(data=None, dtype=None, copy=False, name=None,
            tupleize_cols=True):
            return pd.DatetimeIndex(data, name=name)
    elif isinstance(data, TimedeltaIndexType
        ) or mifyr__xeblz == types.NPTimedelta('ns'):

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
        if isinstance(mifyr__xeblz, (types.Integer, types.Float, types.Boolean)
            ):

            def impl(data=None, dtype=None, copy=False, name=None,
                tupleize_cols=True):
                bqtn__fngsm = bodo.utils.conversion.coerce_to_array(data)
                othz__zxc = bodo.utils.conversion.fix_arr_dtype(bqtn__fngsm,
                    mifyr__xeblz)
                return bodo.hiframes.pd_index_ext.init_numeric_index(othz__zxc,
                    name)
        elif mifyr__xeblz in [types.string, bytes_type]:

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
                fme__rhwp = bodo.hiframes.pd_index_ext.get_index_data(dti)
                val = fme__rhwp[ind]
                return bodo.utils.conversion.box_if_dt64(val)
            return impl
        else:

            def impl(dti, ind):
                fme__rhwp = bodo.hiframes.pd_index_ext.get_index_data(dti)
                name = bodo.hiframes.pd_index_ext.get_index_name(dti)
                wharn__kjs = fme__rhwp[ind]
                return bodo.hiframes.pd_index_ext.init_datetime_index(
                    wharn__kjs, name)
            return impl


@overload(operator.getitem, no_unliteral=True)
def overload_timedelta_index_getitem(I, ind):
    if not isinstance(I, TimedeltaIndexType):
        return
    if isinstance(ind, types.Integer):

        def impl(I, ind):
            bgt__jpoml = bodo.hiframes.pd_index_ext.get_index_data(I)
            return pd.Timedelta(bgt__jpoml[ind])
        return impl

    def impl(I, ind):
        bgt__jpoml = bodo.hiframes.pd_index_ext.get_index_data(I)
        name = bodo.hiframes.pd_index_ext.get_index_name(I)
        wharn__kjs = bgt__jpoml[ind]
        return bodo.hiframes.pd_index_ext.init_timedelta_index(wharn__kjs, name
            )
    return impl


@numba.njit(no_cpython_wrapper=True)
def validate_endpoints(closed):
    nnbed__ltd = False
    kob__wno = False
    if closed is None:
        nnbed__ltd = True
        kob__wno = True
    elif closed == 'left':
        nnbed__ltd = True
    elif closed == 'right':
        kob__wno = True
    else:
        raise ValueError("Closed has to be either 'left', 'right' or None")
    return nnbed__ltd, kob__wno


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
    irn__yjzud = dict(tz=tz, normalize=normalize)
    teagu__tcwtq = dict(tz=None, normalize=False)
    check_unsupported_args('pandas.date_range', irn__yjzud, teagu__tcwtq,
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
        vax__pwmq = pd.Timestamp('2018-01-01')
        if start is not None:
            vax__pwmq = pd.Timestamp(start)
        vtlz__sxvzf = pd.Timestamp('2018-01-01')
        if end is not None:
            vtlz__sxvzf = pd.Timestamp(end)
        if start is None and end is None and closed is not None:
            raise ValueError(
                'Closed has to be None if not both of startand end are defined'
                )
        nnbed__ltd, kob__wno = bodo.hiframes.pd_index_ext.validate_endpoints(
            closed)
        if freq is not None:
            wywr__miey = _dummy_convert_none_to_int(freq)
            if periods is None:
                b = vax__pwmq.value
                fpyh__vda = b + (vtlz__sxvzf.value - b
                    ) // wywr__miey * wywr__miey + wywr__miey // 2 + 1
            elif start is not None:
                periods = _dummy_convert_none_to_int(periods)
                b = vax__pwmq.value
                vdzi__yxbb = np.int64(periods) * np.int64(wywr__miey)
                fpyh__vda = np.int64(b) + vdzi__yxbb
            elif end is not None:
                periods = _dummy_convert_none_to_int(periods)
                fpyh__vda = vtlz__sxvzf.value + wywr__miey
                vdzi__yxbb = np.int64(periods) * np.int64(-wywr__miey)
                b = np.int64(fpyh__vda) + vdzi__yxbb
            else:
                raise ValueError(
                    "at least 'start' or 'end' should be specified if a 'period' is given."
                    )
            rewo__oioi = np.arange(b, fpyh__vda, wywr__miey, np.int64)
        else:
            periods = _dummy_convert_none_to_int(periods)
            xjfjx__jnyn = vtlz__sxvzf.value - vax__pwmq.value
            step = xjfjx__jnyn / (periods - 1)
            pen__fvjo = np.arange(0, periods, 1, np.float64)
            pen__fvjo *= step
            pen__fvjo += vax__pwmq.value
            rewo__oioi = pen__fvjo.astype(np.int64)
            rewo__oioi[-1] = vtlz__sxvzf.value
        if not nnbed__ltd and len(rewo__oioi) and rewo__oioi[0
            ] == vax__pwmq.value:
            rewo__oioi = rewo__oioi[1:]
        if not kob__wno and len(rewo__oioi) and rewo__oioi[-1
            ] == vtlz__sxvzf.value:
            rewo__oioi = rewo__oioi[:-1]
        S = bodo.utils.conversion.convert_to_dt64ns(rewo__oioi)
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
        vax__pwmq = pd.Timedelta('1 day')
        if start is not None:
            vax__pwmq = pd.Timedelta(start)
        vtlz__sxvzf = pd.Timedelta('1 day')
        if end is not None:
            vtlz__sxvzf = pd.Timedelta(end)
        if start is None and end is None and closed is not None:
            raise ValueError(
                'Closed has to be None if not both of start and end are defined'
                )
        nnbed__ltd, kob__wno = bodo.hiframes.pd_index_ext.validate_endpoints(
            closed)
        if freq is not None:
            wywr__miey = _dummy_convert_none_to_int(freq)
            if periods is None:
                b = vax__pwmq.value
                fpyh__vda = b + (vtlz__sxvzf.value - b
                    ) // wywr__miey * wywr__miey + wywr__miey // 2 + 1
            elif start is not None:
                periods = _dummy_convert_none_to_int(periods)
                b = vax__pwmq.value
                vdzi__yxbb = np.int64(periods) * np.int64(wywr__miey)
                fpyh__vda = np.int64(b) + vdzi__yxbb
            elif end is not None:
                periods = _dummy_convert_none_to_int(periods)
                fpyh__vda = vtlz__sxvzf.value + wywr__miey
                vdzi__yxbb = np.int64(periods) * np.int64(-wywr__miey)
                b = np.int64(fpyh__vda) + vdzi__yxbb
            else:
                raise ValueError(
                    "at least 'start' or 'end' should be specified if a 'period' is given."
                    )
            rewo__oioi = np.arange(b, fpyh__vda, wywr__miey, np.int64)
        else:
            periods = _dummy_convert_none_to_int(periods)
            xjfjx__jnyn = vtlz__sxvzf.value - vax__pwmq.value
            step = xjfjx__jnyn / (periods - 1)
            pen__fvjo = np.arange(0, periods, 1, np.float64)
            pen__fvjo *= step
            pen__fvjo += vax__pwmq.value
            rewo__oioi = pen__fvjo.astype(np.int64)
            rewo__oioi[-1] = vtlz__sxvzf.value
        if not nnbed__ltd and len(rewo__oioi) and rewo__oioi[0
            ] == vax__pwmq.value:
            rewo__oioi = rewo__oioi[1:]
        if not kob__wno and len(rewo__oioi) and rewo__oioi[-1
            ] == vtlz__sxvzf.value:
            rewo__oioi = rewo__oioi[:-1]
        S = bodo.utils.conversion.convert_to_dt64ns(rewo__oioi)
        return bodo.hiframes.pd_index_ext.init_timedelta_index(S, name)
    return f


@overload_method(DatetimeIndexType, 'isocalendar', inline='always',
    no_unliteral=True)
def overload_pd_timestamp_isocalendar(idx):

    def impl(idx):
        A = bodo.hiframes.pd_index_ext.get_index_data(idx)
        numba.parfors.parfor.init_prange()
        jblrw__yysf = len(A)
        ulvje__abp = bodo.libs.int_arr_ext.alloc_int_array(jblrw__yysf, np.
            uint32)
        ywf__jeh = bodo.libs.int_arr_ext.alloc_int_array(jblrw__yysf, np.uint32
            )
        ixh__kgpyr = bodo.libs.int_arr_ext.alloc_int_array(jblrw__yysf, np.
            uint32)
        for i in numba.parfors.parfor.internal_prange(jblrw__yysf):
            if bodo.libs.array_kernels.isna(A, i):
                bodo.libs.array_kernels.setna(ulvje__abp, i)
                bodo.libs.array_kernels.setna(ywf__jeh, i)
                bodo.libs.array_kernels.setna(ixh__kgpyr, i)
                continue
            ulvje__abp[i], ywf__jeh[i], ixh__kgpyr[i
                ] = bodo.utils.conversion.box_if_dt64(A[i]).isocalendar()
        return bodo.hiframes.pd_dataframe_ext.init_dataframe((ulvje__abp,
            ywf__jeh, ixh__kgpyr), idx, ('year', 'week', 'day'))
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
        tjm__lvfoe = [('data', _timedelta_index_data_typ), ('name', fe_type
            .name_typ), ('dict', types.DictType(_timedelta_index_data_typ.
            dtype, types.int64))]
        super(TimedeltaIndexTypeModel, self).__init__(dmm, fe_type, tjm__lvfoe)


@typeof_impl.register(pd.TimedeltaIndex)
def typeof_timedelta_index(val, c):
    return TimedeltaIndexType(get_val_type_maybe_str_literal(val.name))


@box(TimedeltaIndexType)
def box_timedelta_index(typ, val, c):
    hth__aarjq = c.context.insert_const_string(c.builder.module, 'pandas')
    spreo__avjz = c.pyapi.import_module_noblock(hth__aarjq)
    timedelta_index = numba.core.cgutils.create_struct_proxy(typ)(c.context,
        c.builder, val)
    c.context.nrt.incref(c.builder, _timedelta_index_data_typ,
        timedelta_index.data)
    kfs__pnckl = c.pyapi.from_native_value(_timedelta_index_data_typ,
        timedelta_index.data, c.env_manager)
    c.context.nrt.incref(c.builder, typ.name_typ, timedelta_index.name)
    amou__uchkv = c.pyapi.from_native_value(typ.name_typ, timedelta_index.
        name, c.env_manager)
    args = c.pyapi.tuple_pack([kfs__pnckl])
    kws = c.pyapi.dict_pack([('name', amou__uchkv)])
    qyj__qgrty = c.pyapi.object_getattr_string(spreo__avjz, 'TimedeltaIndex')
    qrqq__pqa = c.pyapi.call(qyj__qgrty, args, kws)
    c.pyapi.decref(kfs__pnckl)
    c.pyapi.decref(amou__uchkv)
    c.pyapi.decref(spreo__avjz)
    c.pyapi.decref(qyj__qgrty)
    c.pyapi.decref(args)
    c.pyapi.decref(kws)
    c.context.nrt.decref(c.builder, typ, val)
    return qrqq__pqa


@unbox(TimedeltaIndexType)
def unbox_timedelta_index(typ, val, c):
    rph__yxla = c.pyapi.object_getattr_string(val, 'values')
    data = c.pyapi.to_native_value(_timedelta_index_data_typ, rph__yxla).value
    amou__uchkv = c.pyapi.object_getattr_string(val, 'name')
    name = c.pyapi.to_native_value(typ.name_typ, amou__uchkv).value
    c.pyapi.decref(rph__yxla)
    c.pyapi.decref(amou__uchkv)
    hhw__eisvp = cgutils.create_struct_proxy(typ)(c.context, c.builder)
    hhw__eisvp.data = data
    hhw__eisvp.name = name
    dtype = _timedelta_index_data_typ.dtype
    acs__glaz, kvqz__tcwt = c.pyapi.call_jit_code(lambda : numba.typed.Dict
        .empty(dtype, types.int64), types.DictType(dtype, types.int64)(), [])
    hhw__eisvp.dict = kvqz__tcwt
    return NativeValue(hhw__eisvp._getvalue())


@intrinsic
def init_timedelta_index(typingctx, data, name=None):
    name = types.none if name is None else name

    def codegen(context, builder, signature, args):
        xxt__bezu, fxkiw__qcve = args
        timedelta_index = cgutils.create_struct_proxy(signature.return_type)(
            context, builder)
        timedelta_index.data = xxt__bezu
        timedelta_index.name = fxkiw__qcve
        context.nrt.incref(builder, signature.args[0], xxt__bezu)
        context.nrt.incref(builder, signature.args[1], fxkiw__qcve)
        dtype = _timedelta_index_data_typ.dtype
        timedelta_index.dict = context.compile_internal(builder, lambda :
            numba.typed.Dict.empty(dtype, types.int64), types.DictType(
            dtype, types.int64)(), [])
        return timedelta_index._getvalue()
    gyqdm__ywx = TimedeltaIndexType(name)
    sig = signature(gyqdm__ywx, data, name)
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
    tfc__wge = dict(deep=deep, dtype=dtype, names=names)
    hxy__qkqgr = idx_typ_to_format_str_map[TimedeltaIndexType].format('copy()')
    check_unsupported_args('TimedeltaIndex.copy', tfc__wge,
        idx_cpy_arg_defaults, fn_str=hxy__qkqgr, package_name='pandas',
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
    irn__yjzud = dict(axis=axis, skipna=skipna)
    teagu__tcwtq = dict(axis=None, skipna=True)
    check_unsupported_args('TimedeltaIndex.min', irn__yjzud, teagu__tcwtq,
        package_name='pandas', module_name='Index')

    def impl(tdi, axis=None, skipna=True):
        numba.parfors.parfor.init_prange()
        data = bodo.hiframes.pd_index_ext.get_index_data(tdi)
        jblrw__yysf = len(data)
        epcg__vwgdq = numba.cpython.builtins.get_type_max_value(numba.core.
            types.int64)
        count = 0
        for i in numba.parfors.parfor.internal_prange(jblrw__yysf):
            if bodo.libs.array_kernels.isna(data, i):
                continue
            val = (bodo.hiframes.datetime_timedelta_ext.
                cast_numpy_timedelta_to_int(data[i]))
            count += 1
            epcg__vwgdq = min(epcg__vwgdq, val)
        mlnyh__kriv = bodo.hiframes.pd_timestamp_ext.integer_to_timedelta64(
            epcg__vwgdq)
        return bodo.hiframes.pd_index_ext._tdi_val_finalize(mlnyh__kriv, count)
    return impl


@overload_method(TimedeltaIndexType, 'max', inline='always', no_unliteral=True)
def overload_timedelta_index_max(tdi, axis=None, skipna=True):
    irn__yjzud = dict(axis=axis, skipna=skipna)
    teagu__tcwtq = dict(axis=None, skipna=True)
    check_unsupported_args('TimedeltaIndex.max', irn__yjzud, teagu__tcwtq,
        package_name='pandas', module_name='Index')
    if not is_overload_none(axis) or not is_overload_true(skipna):
        raise BodoError(
            'Index.min(): axis and skipna arguments not supported yet')

    def impl(tdi, axis=None, skipna=True):
        numba.parfors.parfor.init_prange()
        data = bodo.hiframes.pd_index_ext.get_index_data(tdi)
        jblrw__yysf = len(data)
        hry__sqv = numba.cpython.builtins.get_type_min_value(numba.core.
            types.int64)
        count = 0
        for i in numba.parfors.parfor.internal_prange(jblrw__yysf):
            if bodo.libs.array_kernels.isna(data, i):
                continue
            val = (bodo.hiframes.datetime_timedelta_ext.
                cast_numpy_timedelta_to_int(data[i]))
            count += 1
            hry__sqv = max(hry__sqv, val)
        mlnyh__kriv = bodo.hiframes.pd_timestamp_ext.integer_to_timedelta64(
            hry__sqv)
        return bodo.hiframes.pd_index_ext._tdi_val_finalize(mlnyh__kriv, count)
    return impl


def gen_tdi_field_impl(field):
    prfxn__ely = 'def impl(tdi):\n'
    prfxn__ely += '    numba.parfors.parfor.init_prange()\n'
    prfxn__ely += '    A = bodo.hiframes.pd_index_ext.get_index_data(tdi)\n'
    prfxn__ely += '    name = bodo.hiframes.pd_index_ext.get_index_name(tdi)\n'
    prfxn__ely += '    n = len(A)\n'
    prfxn__ely += '    S = np.empty(n, np.int64)\n'
    prfxn__ely += '    for i in numba.parfors.parfor.internal_prange(n):\n'
    prfxn__ely += (
        '        td64 = bodo.hiframes.pd_timestamp_ext.timedelta64_to_integer(A[i])\n'
        )
    if field == 'nanoseconds':
        prfxn__ely += '        S[i] = td64 % 1000\n'
    elif field == 'microseconds':
        prfxn__ely += '        S[i] = td64 // 1000 % 100000\n'
    elif field == 'seconds':
        prfxn__ely += (
            '        S[i] = td64 // (1000 * 1000000) % (60 * 60 * 24)\n')
    elif field == 'days':
        prfxn__ely += (
            '        S[i] = td64 // (1000 * 1000000 * 60 * 60 * 24)\n')
    else:
        assert False, 'invalid timedelta field'
    prfxn__ely += (
        '    return bodo.hiframes.pd_index_ext.init_numeric_index(S, name)\n')
    igxy__ymmm = {}
    exec(prfxn__ely, {'numba': numba, 'np': np, 'bodo': bodo}, igxy__ymmm)
    impl = igxy__ymmm['impl']
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
    irn__yjzud = dict(unit=unit, freq=freq, dtype=dtype, copy=copy)
    teagu__tcwtq = dict(unit=None, freq=None, dtype=None, copy=False)
    check_unsupported_args('pandas.TimedeltaIndex', irn__yjzud,
        teagu__tcwtq, package_name='pandas', module_name='Index')

    def impl(data=None, unit=None, freq=None, dtype=None, copy=False, name=None
        ):
        bqtn__fngsm = bodo.utils.conversion.coerce_to_array(data)
        S = bodo.utils.conversion.convert_to_td64ns(bqtn__fngsm)
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
        tjm__lvfoe = [('start', types.int64), ('stop', types.int64), (
            'step', types.int64), ('name', fe_type.name_typ)]
        super(RangeIndexModel, self).__init__(dmm, fe_type, tjm__lvfoe)


make_attribute_wrapper(RangeIndexType, 'start', '_start')
make_attribute_wrapper(RangeIndexType, 'stop', '_stop')
make_attribute_wrapper(RangeIndexType, 'step', '_step')
make_attribute_wrapper(RangeIndexType, 'name', '_name')


@overload_method(RangeIndexType, 'copy', no_unliteral=True)
def overload_range_index_copy(A, name=None, deep=False, dtype=None, names=None
    ):
    tfc__wge = dict(deep=deep, dtype=dtype, names=names)
    hxy__qkqgr = idx_typ_to_format_str_map[RangeIndexType].format('copy()')
    check_unsupported_args('RangeIndex.copy', tfc__wge,
        idx_cpy_arg_defaults, fn_str=hxy__qkqgr, package_name='pandas',
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
    hth__aarjq = c.context.insert_const_string(c.builder.module, 'pandas')
    zna__iicym = c.pyapi.import_module_noblock(hth__aarjq)
    qhma__grl = cgutils.create_struct_proxy(typ)(c.context, c.builder, val)
    pydr__pax = c.pyapi.from_native_value(types.int64, qhma__grl.start, c.
        env_manager)
    snu__ekv = c.pyapi.from_native_value(types.int64, qhma__grl.stop, c.
        env_manager)
    frmu__pacs = c.pyapi.from_native_value(types.int64, qhma__grl.step, c.
        env_manager)
    c.context.nrt.incref(c.builder, typ.name_typ, qhma__grl.name)
    amou__uchkv = c.pyapi.from_native_value(typ.name_typ, qhma__grl.name, c
        .env_manager)
    args = c.pyapi.tuple_pack([pydr__pax, snu__ekv, frmu__pacs])
    kws = c.pyapi.dict_pack([('name', amou__uchkv)])
    qyj__qgrty = c.pyapi.object_getattr_string(zna__iicym, 'RangeIndex')
    lewj__rlz = c.pyapi.call(qyj__qgrty, args, kws)
    c.pyapi.decref(pydr__pax)
    c.pyapi.decref(snu__ekv)
    c.pyapi.decref(frmu__pacs)
    c.pyapi.decref(amou__uchkv)
    c.pyapi.decref(zna__iicym)
    c.pyapi.decref(qyj__qgrty)
    c.pyapi.decref(args)
    c.pyapi.decref(kws)
    c.context.nrt.decref(c.builder, typ, val)
    return lewj__rlz


@intrinsic
def init_range_index(typingctx, start, stop, step, name=None):
    name = types.none if name is None else name

    def codegen(context, builder, signature, args):
        assert len(args) == 4
        qhma__grl = cgutils.create_struct_proxy(signature.return_type)(context,
            builder)
        qhma__grl.start = args[0]
        qhma__grl.stop = args[1]
        qhma__grl.step = args[2]
        qhma__grl.name = args[3]
        context.nrt.incref(builder, signature.return_type.name_typ, args[3])
        return qhma__grl._getvalue()
    return RangeIndexType(name)(start, stop, step, name), codegen


def init_range_index_equiv(self, scope, equiv_set, loc, args, kws):
    assert len(args) == 4 and not kws
    start, stop, step, pazl__dcm = args
    if self.typemap[start.name] == types.IntegerLiteral(0) and self.typemap[
        step.name] == types.IntegerLiteral(1) and equiv_set.has_shape(stop):
        return ArrayAnalysis.AnalyzeResult(shape=stop, pre=[])
    return None


(ArrayAnalysis._analyze_op_call_bodo_hiframes_pd_index_ext_init_range_index
    ) = init_range_index_equiv


@unbox(RangeIndexType)
def unbox_range_index(typ, val, c):
    pydr__pax = c.pyapi.object_getattr_string(val, 'start')
    start = c.pyapi.to_native_value(types.int64, pydr__pax).value
    snu__ekv = c.pyapi.object_getattr_string(val, 'stop')
    stop = c.pyapi.to_native_value(types.int64, snu__ekv).value
    frmu__pacs = c.pyapi.object_getattr_string(val, 'step')
    step = c.pyapi.to_native_value(types.int64, frmu__pacs).value
    amou__uchkv = c.pyapi.object_getattr_string(val, 'name')
    name = c.pyapi.to_native_value(typ.name_typ, amou__uchkv).value
    c.pyapi.decref(pydr__pax)
    c.pyapi.decref(snu__ekv)
    c.pyapi.decref(frmu__pacs)
    c.pyapi.decref(amou__uchkv)
    qhma__grl = cgutils.create_struct_proxy(typ)(c.context, c.builder)
    qhma__grl.start = start
    qhma__grl.stop = stop
    qhma__grl.step = step
    qhma__grl.name = name
    return NativeValue(qhma__grl._getvalue())


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
        niako__rhsw = (
            'RangeIndex(...) must be called with integers, {value} was passed for {field}'
            )
        if not is_overload_none(value) and not isinstance(value, types.
            IntegerLiteral) and not isinstance(value, types.Integer):
            raise BodoError(niako__rhsw.format(value=value, field=field))
    _ensure_int_or_none(start, 'start')
    _ensure_int_or_none(stop, 'stop')
    _ensure_int_or_none(step, 'step')
    if is_overload_none(start) and is_overload_none(stop) and is_overload_none(
        step):
        niako__rhsw = 'RangeIndex(...) must be called with integers'
        raise BodoError(niako__rhsw)
    wiwn__rradj = 'start'
    mki__kenq = 'stop'
    itxtn__xdn = 'step'
    if is_overload_none(start):
        wiwn__rradj = '0'
    if is_overload_none(stop):
        mki__kenq = 'start'
        wiwn__rradj = '0'
    if is_overload_none(step):
        itxtn__xdn = '1'
    prfxn__ely = """def _pd_range_index_imp(start=None, stop=None, step=None, dtype=None, copy=False, name=None):
"""
    prfxn__ely += '  return init_range_index({}, {}, {}, name)\n'.format(
        wiwn__rradj, mki__kenq, itxtn__xdn)
    igxy__ymmm = {}
    exec(prfxn__ely, {'init_range_index': init_range_index}, igxy__ymmm)
    shfmw__dor = igxy__ymmm['_pd_range_index_imp']
    return shfmw__dor


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
                pimrp__tqmz = numba.cpython.unicode._normalize_slice(idx,
                    len(I))
                name = bodo.hiframes.pd_index_ext.get_index_name(I)
                start = I._start + I._step * pimrp__tqmz.start
                stop = I._start + I._step * pimrp__tqmz.stop
                step = I._step * pimrp__tqmz.step
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
        tjm__lvfoe = [('data', bodo.IntegerArrayType(types.int64)), ('name',
            fe_type.name_typ), ('dict', types.DictType(types.int64, types.
            int64))]
        super(PeriodIndexModel, self).__init__(dmm, fe_type, tjm__lvfoe)


make_attribute_wrapper(PeriodIndexType, 'data', '_data')
make_attribute_wrapper(PeriodIndexType, 'name', '_name')
make_attribute_wrapper(PeriodIndexType, 'dict', '_dict')


@overload_method(PeriodIndexType, 'copy', no_unliteral=True)
def overload_period_index_copy(A, name=None, deep=False, dtype=None, names=None
    ):
    freq = A.freq
    tfc__wge = dict(deep=deep, dtype=dtype, names=names)
    hxy__qkqgr = idx_typ_to_format_str_map[PeriodIndexType].format('copy()')
    check_unsupported_args('PeriodIndex.copy', tfc__wge,
        idx_cpy_arg_defaults, fn_str=hxy__qkqgr, package_name='pandas',
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
        xxt__bezu, fxkiw__qcve, pazl__dcm = args
        uplm__zpnq = signature.return_type
        jjc__ubb = cgutils.create_struct_proxy(uplm__zpnq)(context, builder)
        jjc__ubb.data = xxt__bezu
        jjc__ubb.name = fxkiw__qcve
        context.nrt.incref(builder, signature.args[0], args[0])
        context.nrt.incref(builder, signature.args[1], args[1])
        jjc__ubb.dict = context.compile_internal(builder, lambda : numba.
            typed.Dict.empty(types.int64, types.int64), types.DictType(
            types.int64, types.int64)(), [])
        return jjc__ubb._getvalue()
    nsl__utw = get_overload_const_str(freq)
    gyqdm__ywx = PeriodIndexType(nsl__utw, name)
    sig = signature(gyqdm__ywx, data, name, freq)
    return sig, codegen


@box(PeriodIndexType)
def box_period_index(typ, val, c):
    hth__aarjq = c.context.insert_const_string(c.builder.module, 'pandas')
    zna__iicym = c.pyapi.import_module_noblock(hth__aarjq)
    hhw__eisvp = cgutils.create_struct_proxy(typ)(c.context, c.builder, val)
    c.context.nrt.incref(c.builder, bodo.IntegerArrayType(types.int64),
        hhw__eisvp.data)
    fdxy__css = c.pyapi.from_native_value(bodo.IntegerArrayType(types.int64
        ), hhw__eisvp.data, c.env_manager)
    c.context.nrt.incref(c.builder, typ.name_typ, hhw__eisvp.name)
    amou__uchkv = c.pyapi.from_native_value(typ.name_typ, hhw__eisvp.name,
        c.env_manager)
    hzhn__sdqd = c.pyapi.string_from_constant_string(typ.freq)
    args = c.pyapi.tuple_pack([])
    kws = c.pyapi.dict_pack([('ordinal', fdxy__css), ('name', amou__uchkv),
        ('freq', hzhn__sdqd)])
    qyj__qgrty = c.pyapi.object_getattr_string(zna__iicym, 'PeriodIndex')
    lewj__rlz = c.pyapi.call(qyj__qgrty, args, kws)
    c.pyapi.decref(fdxy__css)
    c.pyapi.decref(amou__uchkv)
    c.pyapi.decref(hzhn__sdqd)
    c.pyapi.decref(zna__iicym)
    c.pyapi.decref(qyj__qgrty)
    c.pyapi.decref(args)
    c.pyapi.decref(kws)
    c.context.nrt.decref(c.builder, typ, val)
    return lewj__rlz


@unbox(PeriodIndexType)
def unbox_period_index(typ, val, c):
    arr_typ = bodo.IntegerArrayType(types.int64)
    ynb__hdswl = c.pyapi.object_getattr_string(val, 'asi8')
    iqj__wio = c.pyapi.call_method(val, 'isna', ())
    amou__uchkv = c.pyapi.object_getattr_string(val, 'name')
    name = c.pyapi.to_native_value(typ.name_typ, amou__uchkv).value
    hth__aarjq = c.context.insert_const_string(c.builder.module, 'pandas')
    spreo__avjz = c.pyapi.import_module_noblock(hth__aarjq)
    ezpd__sboy = c.pyapi.object_getattr_string(spreo__avjz, 'arrays')
    fdxy__css = c.pyapi.call_method(ezpd__sboy, 'IntegerArray', (ynb__hdswl,
        iqj__wio))
    data = c.pyapi.to_native_value(arr_typ, fdxy__css).value
    c.pyapi.decref(ynb__hdswl)
    c.pyapi.decref(iqj__wio)
    c.pyapi.decref(amou__uchkv)
    c.pyapi.decref(spreo__avjz)
    c.pyapi.decref(ezpd__sboy)
    c.pyapi.decref(fdxy__css)
    hhw__eisvp = cgutils.create_struct_proxy(typ)(c.context, c.builder)
    hhw__eisvp.data = data
    hhw__eisvp.name = name
    acs__glaz, kvqz__tcwt = c.pyapi.call_jit_code(lambda : numba.typed.Dict
        .empty(types.int64, types.int64), types.DictType(types.int64, types
        .int64)(), [])
    hhw__eisvp.dict = kvqz__tcwt
    return NativeValue(hhw__eisvp._getvalue())


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
        znep__ywns = get_categories_int_type(fe_type.data.dtype)
        tjm__lvfoe = [('data', fe_type.data), ('name', fe_type.name_typ), (
            'dict', types.DictType(znep__ywns, types.int64))]
        super(CategoricalIndexTypeModel, self).__init__(dmm, fe_type,
            tjm__lvfoe)


@typeof_impl.register(pd.CategoricalIndex)
def typeof_categorical_index(val, c):
    return CategoricalIndexType(bodo.typeof(val.values),
        get_val_type_maybe_str_literal(val.name))


@box(CategoricalIndexType)
def box_categorical_index(typ, val, c):
    hth__aarjq = c.context.insert_const_string(c.builder.module, 'pandas')
    spreo__avjz = c.pyapi.import_module_noblock(hth__aarjq)
    modec__poor = numba.core.cgutils.create_struct_proxy(typ)(c.context, c.
        builder, val)
    c.context.nrt.incref(c.builder, typ.data, modec__poor.data)
    kfs__pnckl = c.pyapi.from_native_value(typ.data, modec__poor.data, c.
        env_manager)
    c.context.nrt.incref(c.builder, typ.name_typ, modec__poor.name)
    amou__uchkv = c.pyapi.from_native_value(typ.name_typ, modec__poor.name,
        c.env_manager)
    args = c.pyapi.tuple_pack([kfs__pnckl])
    kws = c.pyapi.dict_pack([('name', amou__uchkv)])
    qyj__qgrty = c.pyapi.object_getattr_string(spreo__avjz, 'CategoricalIndex')
    qrqq__pqa = c.pyapi.call(qyj__qgrty, args, kws)
    c.pyapi.decref(kfs__pnckl)
    c.pyapi.decref(amou__uchkv)
    c.pyapi.decref(spreo__avjz)
    c.pyapi.decref(qyj__qgrty)
    c.pyapi.decref(args)
    c.pyapi.decref(kws)
    c.context.nrt.decref(c.builder, typ, val)
    return qrqq__pqa


@unbox(CategoricalIndexType)
def unbox_categorical_index(typ, val, c):
    from bodo.hiframes.pd_categorical_ext import get_categories_int_type
    rph__yxla = c.pyapi.object_getattr_string(val, 'values')
    data = c.pyapi.to_native_value(typ.data, rph__yxla).value
    amou__uchkv = c.pyapi.object_getattr_string(val, 'name')
    name = c.pyapi.to_native_value(typ.name_typ, amou__uchkv).value
    c.pyapi.decref(rph__yxla)
    c.pyapi.decref(amou__uchkv)
    hhw__eisvp = cgutils.create_struct_proxy(typ)(c.context, c.builder)
    hhw__eisvp.data = data
    hhw__eisvp.name = name
    dtype = get_categories_int_type(typ.data.dtype)
    acs__glaz, kvqz__tcwt = c.pyapi.call_jit_code(lambda : numba.typed.Dict
        .empty(dtype, types.int64), types.DictType(dtype, types.int64)(), [])
    hhw__eisvp.dict = kvqz__tcwt
    return NativeValue(hhw__eisvp._getvalue())


@intrinsic
def init_categorical_index(typingctx, data, name=None):
    name = types.none if name is None else name

    def codegen(context, builder, signature, args):
        from bodo.hiframes.pd_categorical_ext import get_categories_int_type
        xxt__bezu, fxkiw__qcve = args
        modec__poor = cgutils.create_struct_proxy(signature.return_type)(
            context, builder)
        modec__poor.data = xxt__bezu
        modec__poor.name = fxkiw__qcve
        context.nrt.incref(builder, signature.args[0], xxt__bezu)
        context.nrt.incref(builder, signature.args[1], fxkiw__qcve)
        dtype = get_categories_int_type(signature.return_type.data.dtype)
        modec__poor.dict = context.compile_internal(builder, lambda : numba
            .typed.Dict.empty(dtype, types.int64), types.DictType(dtype,
            types.int64)(), [])
        return modec__poor._getvalue()
    gyqdm__ywx = CategoricalIndexType(data, name)
    sig = signature(gyqdm__ywx, data, name)
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
    hxy__qkqgr = idx_typ_to_format_str_map[CategoricalIndexType].format(
        'copy()')
    tfc__wge = dict(deep=deep, dtype=dtype, names=names)
    check_unsupported_args('CategoricalIndex.copy', tfc__wge,
        idx_cpy_arg_defaults, fn_str=hxy__qkqgr, package_name='pandas',
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
        tjm__lvfoe = [('data', fe_type.data), ('name', fe_type.name_typ), (
            'dict', types.DictType(types.UniTuple(fe_type.data.arr_type.
            dtype, 2), types.int64))]
        super(IntervalIndexTypeModel, self).__init__(dmm, fe_type, tjm__lvfoe)


@typeof_impl.register(pd.IntervalIndex)
def typeof_interval_index(val, c):
    return IntervalIndexType(bodo.typeof(val.values),
        get_val_type_maybe_str_literal(val.name))


@box(IntervalIndexType)
def box_interval_index(typ, val, c):
    hth__aarjq = c.context.insert_const_string(c.builder.module, 'pandas')
    spreo__avjz = c.pyapi.import_module_noblock(hth__aarjq)
    fpp__yzwj = numba.core.cgutils.create_struct_proxy(typ)(c.context, c.
        builder, val)
    c.context.nrt.incref(c.builder, typ.data, fpp__yzwj.data)
    kfs__pnckl = c.pyapi.from_native_value(typ.data, fpp__yzwj.data, c.
        env_manager)
    c.context.nrt.incref(c.builder, typ.name_typ, fpp__yzwj.name)
    amou__uchkv = c.pyapi.from_native_value(typ.name_typ, fpp__yzwj.name, c
        .env_manager)
    args = c.pyapi.tuple_pack([kfs__pnckl])
    kws = c.pyapi.dict_pack([('name', amou__uchkv)])
    qyj__qgrty = c.pyapi.object_getattr_string(spreo__avjz, 'IntervalIndex')
    qrqq__pqa = c.pyapi.call(qyj__qgrty, args, kws)
    c.pyapi.decref(kfs__pnckl)
    c.pyapi.decref(amou__uchkv)
    c.pyapi.decref(spreo__avjz)
    c.pyapi.decref(qyj__qgrty)
    c.pyapi.decref(args)
    c.pyapi.decref(kws)
    c.context.nrt.decref(c.builder, typ, val)
    return qrqq__pqa


@unbox(IntervalIndexType)
def unbox_interval_index(typ, val, c):
    rph__yxla = c.pyapi.object_getattr_string(val, 'values')
    data = c.pyapi.to_native_value(typ.data, rph__yxla).value
    amou__uchkv = c.pyapi.object_getattr_string(val, 'name')
    name = c.pyapi.to_native_value(typ.name_typ, amou__uchkv).value
    c.pyapi.decref(rph__yxla)
    c.pyapi.decref(amou__uchkv)
    hhw__eisvp = cgutils.create_struct_proxy(typ)(c.context, c.builder)
    hhw__eisvp.data = data
    hhw__eisvp.name = name
    dtype = types.UniTuple(typ.data.arr_type.dtype, 2)
    acs__glaz, kvqz__tcwt = c.pyapi.call_jit_code(lambda : numba.typed.Dict
        .empty(dtype, types.int64), types.DictType(dtype, types.int64)(), [])
    hhw__eisvp.dict = kvqz__tcwt
    return NativeValue(hhw__eisvp._getvalue())


@intrinsic
def init_interval_index(typingctx, data, name=None):
    name = types.none if name is None else name

    def codegen(context, builder, signature, args):
        xxt__bezu, fxkiw__qcve = args
        fpp__yzwj = cgutils.create_struct_proxy(signature.return_type)(context,
            builder)
        fpp__yzwj.data = xxt__bezu
        fpp__yzwj.name = fxkiw__qcve
        context.nrt.incref(builder, signature.args[0], xxt__bezu)
        context.nrt.incref(builder, signature.args[1], fxkiw__qcve)
        dtype = types.UniTuple(data.arr_type.dtype, 2)
        fpp__yzwj.dict = context.compile_internal(builder, lambda : numba.
            typed.Dict.empty(dtype, types.int64), types.DictType(dtype,
            types.int64)(), [])
        return fpp__yzwj._getvalue()
    gyqdm__ywx = IntervalIndexType(data, name)
    sig = signature(gyqdm__ywx, data, name)
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
        tjm__lvfoe = [('data', fe_type.data), ('name', fe_type.name_typ), (
            'dict', types.DictType(fe_type.dtype, types.int64))]
        super(NumericIndexModel, self).__init__(dmm, fe_type, tjm__lvfoe)


make_attribute_wrapper(NumericIndexType, 'data', '_data')
make_attribute_wrapper(NumericIndexType, 'name', '_name')
make_attribute_wrapper(NumericIndexType, 'dict', '_dict')


@overload_method(NumericIndexType, 'copy', no_unliteral=True)
def overload_numeric_index_copy(A, name=None, deep=False, dtype=None, names
    =None):
    hxy__qkqgr = idx_typ_to_format_str_map[NumericIndexType].format('copy()')
    tfc__wge = dict(deep=deep, dtype=dtype, names=names)
    check_unsupported_args('Index.copy', tfc__wge, idx_cpy_arg_defaults,
        fn_str=hxy__qkqgr, package_name='pandas', module_name='Index')
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
    hth__aarjq = c.context.insert_const_string(c.builder.module, 'pandas')
    zna__iicym = c.pyapi.import_module_noblock(hth__aarjq)
    hhw__eisvp = cgutils.create_struct_proxy(typ)(c.context, c.builder, val)
    c.context.nrt.incref(c.builder, typ.data, hhw__eisvp.data)
    fdxy__css = c.pyapi.from_native_value(typ.data, hhw__eisvp.data, c.
        env_manager)
    c.context.nrt.incref(c.builder, typ.name_typ, hhw__eisvp.name)
    amou__uchkv = c.pyapi.from_native_value(typ.name_typ, hhw__eisvp.name,
        c.env_manager)
    esvn__bul = c.pyapi.make_none()
    zmdoy__uhlm = c.pyapi.bool_from_bool(c.context.get_constant(types.bool_,
        False))
    lewj__rlz = c.pyapi.call_method(zna__iicym, 'Index', (fdxy__css,
        esvn__bul, zmdoy__uhlm, amou__uchkv))
    c.pyapi.decref(fdxy__css)
    c.pyapi.decref(esvn__bul)
    c.pyapi.decref(zmdoy__uhlm)
    c.pyapi.decref(amou__uchkv)
    c.pyapi.decref(zna__iicym)
    c.context.nrt.decref(c.builder, typ, val)
    return lewj__rlz


@intrinsic
def init_numeric_index(typingctx, data, name=None):
    name = types.none if is_overload_none(name) else name

    def codegen(context, builder, signature, args):
        assert len(args) == 2
        uplm__zpnq = signature.return_type
        hhw__eisvp = cgutils.create_struct_proxy(uplm__zpnq)(context, builder)
        hhw__eisvp.data = args[0]
        hhw__eisvp.name = args[1]
        context.nrt.incref(builder, uplm__zpnq.data, args[0])
        context.nrt.incref(builder, uplm__zpnq.name_typ, args[1])
        dtype = uplm__zpnq.dtype
        hhw__eisvp.dict = context.compile_internal(builder, lambda : numba.
            typed.Dict.empty(dtype, types.int64), types.DictType(dtype,
            types.int64)(), [])
        return hhw__eisvp._getvalue()
    return NumericIndexType(data.dtype, name, data)(data, name), codegen


(ArrayAnalysis._analyze_op_call_bodo_hiframes_pd_index_ext_init_numeric_index
    ) = init_index_equiv


@unbox(NumericIndexType)
def unbox_numeric_index(typ, val, c):
    rph__yxla = c.pyapi.object_getattr_string(val, 'values')
    data = c.pyapi.to_native_value(typ.data, rph__yxla).value
    amou__uchkv = c.pyapi.object_getattr_string(val, 'name')
    name = c.pyapi.to_native_value(typ.name_typ, amou__uchkv).value
    c.pyapi.decref(rph__yxla)
    c.pyapi.decref(amou__uchkv)
    hhw__eisvp = cgutils.create_struct_proxy(typ)(c.context, c.builder)
    hhw__eisvp.data = data
    hhw__eisvp.name = name
    dtype = typ.dtype
    acs__glaz, kvqz__tcwt = c.pyapi.call_jit_code(lambda : numba.typed.Dict
        .empty(dtype, types.int64), types.DictType(dtype, types.int64)(), [])
    hhw__eisvp.dict = kvqz__tcwt
    return NativeValue(hhw__eisvp._getvalue())


def create_numeric_constructor(func, func_str, default_dtype):

    def overload_impl(data=None, dtype=None, copy=False, name=None):
        jwj__vhoe = dict(dtype=dtype)
        hmrwi__qsbuo = dict(dtype=None)
        check_unsupported_args(func_str, jwj__vhoe, hmrwi__qsbuo,
            package_name='pandas', module_name='Index')
        if is_overload_false(copy):

            def impl(data=None, dtype=None, copy=False, name=None):
                bqtn__fngsm = bodo.utils.conversion.coerce_to_ndarray(data)
                ptvjb__wrni = bodo.utils.conversion.fix_arr_dtype(bqtn__fngsm,
                    np.dtype(default_dtype))
                return bodo.hiframes.pd_index_ext.init_numeric_index(
                    ptvjb__wrni, name)
        else:

            def impl(data=None, dtype=None, copy=False, name=None):
                bqtn__fngsm = bodo.utils.conversion.coerce_to_ndarray(data)
                if copy:
                    bqtn__fngsm = bqtn__fngsm.copy()
                ptvjb__wrni = bodo.utils.conversion.fix_arr_dtype(bqtn__fngsm,
                    np.dtype(default_dtype))
                return bodo.hiframes.pd_index_ext.init_numeric_index(
                    ptvjb__wrni, name)
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
        tjm__lvfoe = [('data', fe_type.data), ('name', fe_type.name_typ), (
            'dict', types.DictType(string_type, types.int64))]
        super(StringIndexModel, self).__init__(dmm, fe_type, tjm__lvfoe)


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
        tjm__lvfoe = [('data', binary_array_type), ('name', fe_type.
            name_typ), ('dict', types.DictType(bytes_type, types.int64))]
        super(BinaryIndexModel, self).__init__(dmm, fe_type, tjm__lvfoe)


make_attribute_wrapper(BinaryIndexType, 'data', '_data')
make_attribute_wrapper(BinaryIndexType, 'name', '_name')
make_attribute_wrapper(BinaryIndexType, 'dict', '_dict')


@unbox(BinaryIndexType)
@unbox(StringIndexType)
def unbox_binary_str_index(typ, val, c):
    hrewp__vyobi = typ.data
    scalar_type = typ.data.dtype
    rph__yxla = c.pyapi.object_getattr_string(val, 'values')
    data = c.pyapi.to_native_value(hrewp__vyobi, rph__yxla).value
    amou__uchkv = c.pyapi.object_getattr_string(val, 'name')
    name = c.pyapi.to_native_value(typ.name_typ, amou__uchkv).value
    c.pyapi.decref(rph__yxla)
    c.pyapi.decref(amou__uchkv)
    hhw__eisvp = cgutils.create_struct_proxy(typ)(c.context, c.builder)
    hhw__eisvp.data = data
    hhw__eisvp.name = name
    acs__glaz, kvqz__tcwt = c.pyapi.call_jit_code(lambda : numba.typed.Dict
        .empty(scalar_type, types.int64), types.DictType(scalar_type, types
        .int64)(), [])
    hhw__eisvp.dict = kvqz__tcwt
    return NativeValue(hhw__eisvp._getvalue())


@box(BinaryIndexType)
@box(StringIndexType)
def box_binary_str_index(typ, val, c):
    hrewp__vyobi = typ.data
    hth__aarjq = c.context.insert_const_string(c.builder.module, 'pandas')
    zna__iicym = c.pyapi.import_module_noblock(hth__aarjq)
    hhw__eisvp = cgutils.create_struct_proxy(typ)(c.context, c.builder, val)
    c.context.nrt.incref(c.builder, hrewp__vyobi, hhw__eisvp.data)
    fdxy__css = c.pyapi.from_native_value(hrewp__vyobi, hhw__eisvp.data, c.
        env_manager)
    c.context.nrt.incref(c.builder, typ.name_typ, hhw__eisvp.name)
    amou__uchkv = c.pyapi.from_native_value(typ.name_typ, hhw__eisvp.name,
        c.env_manager)
    esvn__bul = c.pyapi.make_none()
    zmdoy__uhlm = c.pyapi.bool_from_bool(c.context.get_constant(types.bool_,
        False))
    lewj__rlz = c.pyapi.call_method(zna__iicym, 'Index', (fdxy__css,
        esvn__bul, zmdoy__uhlm, amou__uchkv))
    c.pyapi.decref(fdxy__css)
    c.pyapi.decref(esvn__bul)
    c.pyapi.decref(zmdoy__uhlm)
    c.pyapi.decref(amou__uchkv)
    c.pyapi.decref(zna__iicym)
    c.context.nrt.decref(c.builder, typ, val)
    return lewj__rlz


@intrinsic
def init_binary_str_index(typingctx, data, name=None):
    name = types.none if name is None else name
    sig = type(bodo.utils.typing.get_index_type_from_dtype(data.dtype))(name,
        data)(data, name)
    ivg__gcrwh = get_binary_str_codegen(is_binary=data.dtype == bytes_type)
    return sig, ivg__gcrwh


(ArrayAnalysis.
    _analyze_op_call_bodo_hiframes_pd_index_ext_init_binary_str_index
    ) = init_index_equiv


def get_binary_str_codegen(is_binary=False):
    if is_binary:
        nifow__qjoe = 'bytes_type'
    else:
        nifow__qjoe = 'string_type'
    prfxn__ely = 'def impl(context, builder, signature, args):\n'
    prfxn__ely += '    assert len(args) == 2\n'
    prfxn__ely += '    index_typ = signature.return_type\n'
    prfxn__ely += (
        '    index_val = cgutils.create_struct_proxy(index_typ)(context, builder)\n'
        )
    prfxn__ely += '    index_val.data = args[0]\n'
    prfxn__ely += '    index_val.name = args[1]\n'
    prfxn__ely += '    # increase refcount of stored values\n'
    prfxn__ely += (
        '    context.nrt.incref(builder, signature.args[0], args[0])\n')
    prfxn__ely += (
        '    context.nrt.incref(builder, index_typ.name_typ, args[1])\n')
    prfxn__ely += '    # create empty dict for get_loc hashmap\n'
    prfxn__ely += '    index_val.dict = context.compile_internal(\n'
    prfxn__ely += '       builder,\n'
    prfxn__ely += (
        f'       lambda: numba.typed.Dict.empty({nifow__qjoe}, types.int64),\n'
        )
    prfxn__ely += (
        f'        types.DictType({nifow__qjoe}, types.int64)(), [],)\n')
    prfxn__ely += '    return index_val._getvalue()\n'
    igxy__ymmm = {}
    exec(prfxn__ely, {'bodo': bodo, 'signature': signature, 'cgutils':
        cgutils, 'numba': numba, 'types': types, 'bytes_type': bytes_type,
        'string_type': string_type}, igxy__ymmm)
    impl = igxy__ymmm['impl']
    return impl


@overload_method(BinaryIndexType, 'copy', no_unliteral=True)
@overload_method(StringIndexType, 'copy', no_unliteral=True)
def overload_binary_string_index_copy(A, name=None, deep=False, dtype=None,
    names=None):
    typ = type(A)
    hxy__qkqgr = idx_typ_to_format_str_map[typ].format('copy()')
    tfc__wge = dict(deep=deep, dtype=dtype, names=names)
    check_unsupported_args('Index.copy', tfc__wge, idx_cpy_arg_defaults,
        fn_str=hxy__qkqgr, package_name='pandas', module_name='Index')
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
    irn__yjzud = dict(axis=axis, allow_fill=allow_fill, fill_value=fill_value)
    pjb__yqjx = dict(axis=0, allow_fill=True, fill_value=None)
    check_unsupported_args('Index.take', irn__yjzud, pjb__yqjx,
        package_name='pandas', module_name='Index')
    return lambda I, indices: I[indices]


@numba.njit(no_cpython_wrapper=True)
def _init_engine(I):
    if len(I) > 0 and not I._dict:
        rewo__oioi = bodo.utils.conversion.coerce_to_array(I)
        for i in range(len(rewo__oioi)):
            val = rewo__oioi[i]
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
            niako__rhsw = (
                'Global Index objects can be slow (pass as argument to JIT function for better performance).'
                )
            warnings.warn(niako__rhsw)
            rewo__oioi = bodo.utils.conversion.coerce_to_array(I)
            ind = -1
            for i in range(len(rewo__oioi)):
                if rewo__oioi[i] == key:
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
    irn__yjzud = dict(method=method, tolerance=tolerance)
    teagu__tcwtq = dict(method=None, tolerance=None)
    check_unsupported_args('Index.get_loc', irn__yjzud, teagu__tcwtq,
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
            niako__rhsw = (
                'Index.get_loc() can be slow for global Index objects (pass as argument to JIT function for better performance).'
                )
            warnings.warn(niako__rhsw)
            rewo__oioi = bodo.utils.conversion.coerce_to_array(I)
            ind = -1
            for i in range(len(rewo__oioi)):
                if rewo__oioi[i] == key:
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
        ovzgo__qral = overload_name in {'isna', 'isnull'}
        if isinstance(I, RangeIndexType):

            def impl(I):
                numba.parfors.parfor.init_prange()
                jblrw__yysf = len(I)
                yhk__xgx = np.empty(jblrw__yysf, np.bool_)
                for i in numba.parfors.parfor.internal_prange(jblrw__yysf):
                    yhk__xgx[i] = not ovzgo__qral
                return yhk__xgx
            return impl
        prfxn__ely = f"""def impl(I):
    numba.parfors.parfor.init_prange()
    arr = bodo.hiframes.pd_index_ext.get_index_data(I)
    n = len(arr)
    out_arr = np.empty(n, np.bool_)
    for i in numba.parfors.parfor.internal_prange(n):
       out_arr[i] = {'' if ovzgo__qral else 'not '}bodo.libs.array_kernels.isna(arr, i)
    return out_arr
"""
        igxy__ymmm = {}
        exec(prfxn__ely, {'bodo': bodo, 'np': np, 'numba': numba}, igxy__ymmm)
        impl = igxy__ymmm['impl']
        return impl
    return overload_index_isna_specific_method


isna_overload_types = (RangeIndexType, NumericIndexType, StringIndexType,
    BinaryIndexType, CategoricalIndexType, PeriodIndexType,
    DatetimeIndexType, TimedeltaIndexType)
isna_specific_methods = 'isna', 'notna', 'isnull', 'notnull'


def _install_isna_specific_methods():
    for voun__mrv in isna_overload_types:
        for overload_name in isna_specific_methods:
            overload_impl = create_isna_specific_method(overload_name)
            overload_method(voun__mrv, overload_name, no_unliteral=True,
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
            rewo__oioi = bodo.hiframes.pd_index_ext.get_index_data(I)
            return bodo.libs.array_kernels.series_monotonicity(rewo__oioi, 1)
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
            rewo__oioi = bodo.hiframes.pd_index_ext.get_index_data(I)
            return bodo.libs.array_kernels.series_monotonicity(rewo__oioi, 2)
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
        rewo__oioi = bodo.hiframes.pd_index_ext.get_index_data(I)
        yhk__xgx = bodo.libs.array_kernels.duplicated((rewo__oioi,))
        return yhk__xgx
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
    irn__yjzud = dict(keep=keep)
    teagu__tcwtq = dict(keep='first')
    check_unsupported_args('Index.drop_duplicates', irn__yjzud,
        teagu__tcwtq, package_name='pandas', module_name='Index')
    if isinstance(I, RangeIndexType):
        return lambda I, keep='first': I.copy()
    prfxn__ely = """def impl(I, keep='first'):
    data = bodo.hiframes.pd_index_ext.get_index_data(I)
    arr = bodo.libs.array_kernels.drop_duplicates_array(data)
    name = bodo.hiframes.pd_index_ext.get_index_name(I)
"""
    if isinstance(I, PeriodIndexType):
        prfxn__ely += f"""    return bodo.hiframes.pd_index_ext.init_period_index(arr, name, '{I.freq}')
"""
    else:
        prfxn__ely += (
            '    return bodo.utils.conversion.index_from_array(arr, name)')
    igxy__ymmm = {}
    exec(prfxn__ely, {'bodo': bodo}, igxy__ymmm)
    impl = igxy__ymmm['impl']
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
    gtvf__ygjfm = args[0]
    if isinstance(self.typemap[gtvf__ygjfm.name], HeterogeneousIndexType):
        return None
    if equiv_set.has_shape(gtvf__ygjfm):
        return ArrayAnalysis.AnalyzeResult(shape=gtvf__ygjfm, pre=[])
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
    irn__yjzud = dict(na_action=na_action)
    pzf__qrk = dict(na_action=None)
    check_unsupported_args('Index.map', irn__yjzud, pzf__qrk, package_name=
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
    unhys__pidi = numba.core.registry.cpu_target.typing_context
    wlo__ans = numba.core.registry.cpu_target.target_context
    try:
        siavd__avnog = get_const_func_output_type(mapper, (dtype,), {},
            unhys__pidi, wlo__ans)
    except Exception as fpyh__vda:
        raise_bodo_error(get_udf_error_msg('Index.map()', fpyh__vda))
    soht__pypgq = get_udf_out_arr_type(siavd__avnog)
    func = get_overload_const_func(mapper, None)
    prfxn__ely = 'def f(I, mapper, na_action=None):\n'
    prfxn__ely += '  name = bodo.hiframes.pd_index_ext.get_index_name(I)\n'
    prfxn__ely += '  A = bodo.utils.conversion.coerce_to_array(I)\n'
    prfxn__ely += '  numba.parfors.parfor.init_prange()\n'
    prfxn__ely += '  n = len(A)\n'
    prfxn__ely += '  S = bodo.utils.utils.alloc_type(n, _arr_typ, (-1,))\n'
    prfxn__ely += '  for i in numba.parfors.parfor.internal_prange(n):\n'
    prfxn__ely += '    t2 = bodo.utils.conversion.box_if_dt64(A[i])\n'
    prfxn__ely += '    v = map_func(t2)\n'
    prfxn__ely += '    S[i] = bodo.utils.conversion.unbox_if_timestamp(v)\n'
    prfxn__ely += '  return bodo.utils.conversion.index_from_array(S, name)\n'
    vlca__iscdb = bodo.compiler.udf_jit(func)
    igxy__ymmm = {}
    exec(prfxn__ely, {'numba': numba, 'np': np, 'pd': pd, 'bodo': bodo,
        'map_func': vlca__iscdb, '_arr_typ': soht__pypgq,
        'init_nested_counts': bodo.utils.indexing.init_nested_counts,
        'add_nested_counts': bodo.utils.indexing.add_nested_counts,
        'data_arr_type': soht__pypgq.dtype}, igxy__ymmm)
    f = igxy__ymmm['f']
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
    ocuw__hzxr, vrfcq__hay = sig.args
    if ocuw__hzxr != vrfcq__hay:
        return cgutils.false_bit

    def index_is_impl(a, b):
        return a._data is b._data and a._name is b._name
    return context.compile_internal(builder, index_is_impl, sig, args)


@lower_builtin(operator.is_, RangeIndexType, RangeIndexType)
def range_index_is(context, builder, sig, args):
    ocuw__hzxr, vrfcq__hay = sig.args
    if ocuw__hzxr != vrfcq__hay:
        return cgutils.false_bit

    def index_is_impl(a, b):
        return (a._start == b._start and a._stop == b._stop and a._step ==
            b._step and a._name is b._name)
    return context.compile_internal(builder, index_is_impl, sig, args)


def create_binary_op_overload(op):

    def overload_index_binary_op(lhs, rhs):
        if is_index_type(lhs):
            prfxn__ely = """def impl(lhs, rhs):
  arr = bodo.utils.conversion.coerce_to_array(lhs)
"""
            if rhs in [bodo.hiframes.pd_timestamp_ext.pd_timestamp_type,
                bodo.hiframes.pd_timestamp_ext.pd_timedelta_type]:
                prfxn__ely += """  dt = bodo.utils.conversion.unbox_if_timestamp(rhs)
  return op(arr, dt)
"""
            else:
                prfxn__ely += """  rhs_arr = bodo.utils.conversion.get_array_if_series_or_index(rhs)
  return op(arr, rhs_arr)
"""
            igxy__ymmm = {}
            exec(prfxn__ely, {'bodo': bodo, 'op': op}, igxy__ymmm)
            impl = igxy__ymmm['impl']
            return impl
        if is_index_type(rhs):
            prfxn__ely = """def impl(lhs, rhs):
  arr = bodo.utils.conversion.coerce_to_array(rhs)
"""
            if lhs in [bodo.hiframes.pd_timestamp_ext.pd_timestamp_type,
                bodo.hiframes.pd_timestamp_ext.pd_timedelta_type]:
                prfxn__ely += """  dt = bodo.utils.conversion.unbox_if_timestamp(lhs)
  return op(dt, arr)
"""
            else:
                prfxn__ely += """  lhs_arr = bodo.utils.conversion.get_array_if_series_or_index(lhs)
  return op(lhs_arr, arr)
"""
            igxy__ymmm = {}
            exec(prfxn__ely, {'bodo': bodo, 'op': op}, igxy__ymmm)
            impl = igxy__ymmm['impl']
            return impl
        if isinstance(lhs, HeterogeneousIndexType):
            if not is_heterogeneous_tuple_type(lhs.data):

                def impl3(lhs, rhs):
                    data = bodo.utils.conversion.coerce_to_array(lhs)
                    rewo__oioi = bodo.utils.conversion.coerce_to_array(data)
                    hrfig__njnnn = (bodo.utils.conversion.
                        get_array_if_series_or_index(rhs))
                    yhk__xgx = op(rewo__oioi, hrfig__njnnn)
                    return yhk__xgx
                return impl3
            count = len(lhs.data.types)
            prfxn__ely = 'def f(lhs, rhs):\n'
            prfxn__ely += '  return [{}]\n'.format(','.join(
                'op(lhs[{}], rhs{})'.format(i, f'[{i}]' if is_iterable_type
                (rhs) else '') for i in range(count)))
            igxy__ymmm = {}
            exec(prfxn__ely, {'op': op, 'np': np}, igxy__ymmm)
            impl = igxy__ymmm['f']
            return impl
        if isinstance(rhs, HeterogeneousIndexType):
            if not is_heterogeneous_tuple_type(rhs.data):

                def impl4(lhs, rhs):
                    data = bodo.hiframes.pd_index_ext.get_index_data(rhs)
                    rewo__oioi = bodo.utils.conversion.coerce_to_array(data)
                    hrfig__njnnn = (bodo.utils.conversion.
                        get_array_if_series_or_index(lhs))
                    yhk__xgx = op(hrfig__njnnn, rewo__oioi)
                    return yhk__xgx
                return impl4
            count = len(rhs.data.types)
            prfxn__ely = 'def f(lhs, rhs):\n'
            prfxn__ely += '  return [{}]\n'.format(','.join(
                'op(lhs{}, rhs[{}])'.format(f'[{i}]' if is_iterable_type(
                lhs) else '', i) for i in range(count)))
            igxy__ymmm = {}
            exec(prfxn__ely, {'op': op, 'np': np}, igxy__ymmm)
            impl = igxy__ymmm['f']
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
        tjm__lvfoe = [('data', fe_type.data), ('name', fe_type.name_typ)]
        super(HeterogeneousIndexModel, self).__init__(dmm, fe_type, tjm__lvfoe)


make_attribute_wrapper(HeterogeneousIndexType, 'data', '_data')
make_attribute_wrapper(HeterogeneousIndexType, 'name', '_name')


@overload_method(HeterogeneousIndexType, 'copy', no_unliteral=True)
def overload_heter_index_copy(A, name=None, deep=False, dtype=None, names=None
    ):
    hxy__qkqgr = idx_typ_to_format_str_map[HeterogeneousIndexType].format(
        'copy()')
    tfc__wge = dict(deep=deep, dtype=dtype, names=names)
    check_unsupported_args('Index.copy', tfc__wge, idx_cpy_arg_defaults,
        fn_str=hxy__qkqgr, package_name='pandas', module_name='Index')
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
    hth__aarjq = c.context.insert_const_string(c.builder.module, 'pandas')
    zna__iicym = c.pyapi.import_module_noblock(hth__aarjq)
    hhw__eisvp = cgutils.create_struct_proxy(typ)(c.context, c.builder, val)
    c.context.nrt.incref(c.builder, typ.data, hhw__eisvp.data)
    fdxy__css = c.pyapi.from_native_value(typ.data, hhw__eisvp.data, c.
        env_manager)
    c.context.nrt.incref(c.builder, typ.name_typ, hhw__eisvp.name)
    amou__uchkv = c.pyapi.from_native_value(typ.name_typ, hhw__eisvp.name,
        c.env_manager)
    esvn__bul = c.pyapi.make_none()
    zmdoy__uhlm = c.pyapi.bool_from_bool(c.context.get_constant(types.bool_,
        False))
    lewj__rlz = c.pyapi.call_method(zna__iicym, 'Index', (fdxy__css,
        esvn__bul, zmdoy__uhlm, amou__uchkv))
    c.pyapi.decref(fdxy__css)
    c.pyapi.decref(esvn__bul)
    c.pyapi.decref(zmdoy__uhlm)
    c.pyapi.decref(amou__uchkv)
    c.pyapi.decref(zna__iicym)
    c.context.nrt.decref(c.builder, typ, val)
    return lewj__rlz


@intrinsic
def init_heter_index(typingctx, data, name=None):
    name = types.none if name is None else name

    def codegen(context, builder, signature, args):
        assert len(args) == 2
        uplm__zpnq = signature.return_type
        hhw__eisvp = cgutils.create_struct_proxy(uplm__zpnq)(context, builder)
        hhw__eisvp.data = args[0]
        hhw__eisvp.name = args[1]
        context.nrt.incref(builder, uplm__zpnq.data, args[0])
        context.nrt.incref(builder, uplm__zpnq.name_typ, args[1])
        return hhw__eisvp._getvalue()
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
    dqza__wkwv = {NumericIndexType: bodo.hiframes.pd_index_ext.
        init_numeric_index, DatetimeIndexType: bodo.hiframes.pd_index_ext.
        init_datetime_index, TimedeltaIndexType: bodo.hiframes.pd_index_ext
        .init_timedelta_index, StringIndexType: bodo.hiframes.pd_index_ext.
        init_binary_str_index, BinaryIndexType: bodo.hiframes.pd_index_ext.
        init_binary_str_index, CategoricalIndexType: bodo.hiframes.
        pd_index_ext.init_categorical_index, IntervalIndexType: bodo.
        hiframes.pd_index_ext.init_interval_index}
    if type(I) in dqza__wkwv:
        init_func = dqza__wkwv[type(I)]
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
    ibve__dxal = context.get_constant_null(types.DictType(dtype, types.int64))
    return lir.Constant.literal_struct([data, name, ibve__dxal])


@lower_constant(PeriodIndexType)
def lower_constant_period_index(context, builder, ty, pyval):
    data = context.get_constant_generic(builder, bodo.IntegerArrayType(
        types.int64), pd.arrays.IntegerArray(pyval.asi8, pyval.isna()))
    name = context.get_constant_generic(builder, ty.name_typ, pyval.name)
    ibve__dxal = context.get_constant_null(types.DictType(types.int64,
        types.int64))
    return lir.Constant.literal_struct([data, name, ibve__dxal])


@lower_constant(NumericIndexType)
def lower_constant_numeric_index(context, builder, ty, pyval):
    assert isinstance(ty.dtype, (types.Integer, types.Float, types.Boolean))
    data = context.get_constant_generic(builder, types.Array(ty.dtype, 1,
        'C'), pyval.values)
    name = context.get_constant_generic(builder, ty.name_typ, pyval.name)
    dtype = ty.dtype
    ibve__dxal = context.get_constant_null(types.DictType(dtype, types.int64))
    return lir.Constant.literal_struct([data, name, ibve__dxal])


@lower_constant(StringIndexType)
@lower_constant(BinaryIndexType)
def lower_constant_binary_string_index(context, builder, ty, pyval):
    hrewp__vyobi = ty.data
    scalar_type = ty.data.dtype
    data = context.get_constant_generic(builder, hrewp__vyobi, pyval.values)
    name = context.get_constant_generic(builder, ty.name_typ, pyval.name)
    ibve__dxal = context.get_constant_null(types.DictType(scalar_type,
        types.int64))
    return lir.Constant.literal_struct([data, name, ibve__dxal])


@lower_builtin('getiter', RangeIndexType)
def getiter_range_index(context, builder, sig, args):
    [yfgak__ppr] = sig.args
    [uya__ehala] = args
    rti__nyqn = context.make_helper(builder, yfgak__ppr, value=uya__ehala)
    gabcw__dnwdi = context.make_helper(builder, sig.return_type)
    odvo__gbfvx = cgutils.alloca_once_value(builder, rti__nyqn.start)
    naf__trw = context.get_constant(types.intp, 0)
    vbjv__qgzc = cgutils.alloca_once_value(builder, naf__trw)
    gabcw__dnwdi.iter = odvo__gbfvx
    gabcw__dnwdi.stop = rti__nyqn.stop
    gabcw__dnwdi.step = rti__nyqn.step
    gabcw__dnwdi.count = vbjv__qgzc
    npyt__xvb = builder.sub(rti__nyqn.stop, rti__nyqn.start)
    tazs__fkux = context.get_constant(types.intp, 1)
    cwmo__aqwu = builder.icmp(lc.ICMP_SGT, npyt__xvb, naf__trw)
    dpscj__ljft = builder.icmp(lc.ICMP_SGT, rti__nyqn.step, naf__trw)
    mzik__tkc = builder.not_(builder.xor(cwmo__aqwu, dpscj__ljft))
    with builder.if_then(mzik__tkc):
        dam__vqsfv = builder.srem(npyt__xvb, rti__nyqn.step)
        dam__vqsfv = builder.select(cwmo__aqwu, dam__vqsfv, builder.neg(
            dam__vqsfv))
        ktcbt__orck = builder.icmp(lc.ICMP_SGT, dam__vqsfv, naf__trw)
        xmyfg__syup = builder.add(builder.sdiv(npyt__xvb, rti__nyqn.step),
            builder.select(ktcbt__orck, tazs__fkux, naf__trw))
        builder.store(xmyfg__syup, vbjv__qgzc)
    qrqq__pqa = gabcw__dnwdi._getvalue()
    pde__ryq = impl_ret_new_ref(context, builder, sig.return_type, qrqq__pqa)
    return pde__ryq


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
    for udvo__cqwv in index_unsupported_methods:
        for uipq__dbz, typ in index_types:
            overload_method(typ, udvo__cqwv, no_unliteral=True)(
                create_unsupported_overload(uipq__dbz.format(udvo__cqwv +
                '()')))
    for fco__mijg in index_unsupported_atrs:
        for uipq__dbz, typ in index_types:
            overload_attribute(typ, fco__mijg, no_unliteral=True)(
                create_unsupported_overload(uipq__dbz.format(fco__mijg)))
    exhzo__dnfdu = [(StringIndexType, string_index_unsupported_atrs), (
        BinaryIndexType, binary_index_unsupported_atrs), (
        CategoricalIndexType, cat_idx_unsupported_atrs), (IntervalIndexType,
        interval_idx_unsupported_atrs), (MultiIndexType,
        multi_index_unsupported_atrs), (DatetimeIndexType,
        dt_index_unsupported_atrs), (TimedeltaIndexType,
        td_index_unsupported_atrs), (PeriodIndexType,
        period_index_unsupported_atrs)]
    viv__vwns = [(CategoricalIndexType, cat_idx_unsupported_methods), (
        IntervalIndexType, interval_idx_unsupported_methods), (
        MultiIndexType, multi_index_unsupported_methods), (
        DatetimeIndexType, dt_index_unsupported_methods), (
        TimedeltaIndexType, td_index_unsupported_methods), (PeriodIndexType,
        period_index_unsupported_methods)]
    for typ, mpkw__yzd in viv__vwns:
        uipq__dbz = idx_typ_to_format_str_map[typ]
        for qdpc__mndw in mpkw__yzd:
            overload_method(typ, qdpc__mndw, no_unliteral=True)(
                create_unsupported_overload(uipq__dbz.format(qdpc__mndw +
                '()')))
    for typ, lkcm__utnoc in exhzo__dnfdu:
        uipq__dbz = idx_typ_to_format_str_map[typ]
        for fco__mijg in lkcm__utnoc:
            overload_attribute(typ, fco__mijg, no_unliteral=True)(
                create_unsupported_overload(uipq__dbz.format(fco__mijg)))
    for eqku__imj in [RangeIndexType, NumericIndexType, StringIndexType,
        BinaryIndexType, IntervalIndexType, CategoricalIndexType,
        PeriodIndexType, MultiIndexType]:
        for qdpc__mndw in ['max', 'min']:
            uipq__dbz = idx_typ_to_format_str_map[eqku__imj]
            overload_method(eqku__imj, qdpc__mndw, no_unliteral=True)(
                create_unsupported_overload(uipq__dbz.format(qdpc__mndw +
                '()')))


_install_index_unsupported()
