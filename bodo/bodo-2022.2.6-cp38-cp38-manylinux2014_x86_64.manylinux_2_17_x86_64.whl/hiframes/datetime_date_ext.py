"""Numba extension support for datetime.date objects and their arrays.
"""
import datetime
import operator
import warnings
import llvmlite.binding as ll
import numba
import numpy as np
import pandas as pd
from llvmlite import ir as lir
from numba.core import cgutils, types
from numba.core.imputils import lower_builtin, lower_constant
from numba.core.typing.templates import AttributeTemplate, infer_getattr
from numba.core.utils import PYVERSION
from numba.extending import NativeValue, box, infer_getattr, intrinsic, lower_builtin, lower_getattr, make_attribute_wrapper, models, overload, overload_attribute, overload_method, register_jitable, register_model, type_callable, typeof_impl, unbox
from numba.parfors.array_analysis import ArrayAnalysis
import bodo
from bodo.hiframes.datetime_datetime_ext import DatetimeDatetimeType
from bodo.hiframes.datetime_timedelta_ext import datetime_timedelta_type
from bodo.libs import hdatetime_ext
from bodo.utils.indexing import array_getitem_bool_index, array_getitem_int_index, array_getitem_slice_index, array_setitem_bool_index, array_setitem_int_index, array_setitem_slice_index
from bodo.utils.typing import BodoError, is_iterable_type, is_list_like_index_type, is_overload_int, is_overload_none
ll.add_symbol('box_datetime_date_array', hdatetime_ext.box_datetime_date_array)
ll.add_symbol('unbox_datetime_date_array', hdatetime_ext.
    unbox_datetime_date_array)
ll.add_symbol('get_isocalendar', hdatetime_ext.get_isocalendar)


class DatetimeDateType(types.Type):

    def __init__(self):
        super(DatetimeDateType, self).__init__(name='DatetimeDateType()')
        self.bitwidth = 64


datetime_date_type = DatetimeDateType()


@typeof_impl.register(datetime.date)
def typeof_datetime_date(val, c):
    return datetime_date_type


register_model(DatetimeDateType)(models.IntegerModel)


@infer_getattr
class DatetimeAttribute(AttributeTemplate):
    key = DatetimeDateType

    def resolve_year(self, typ):
        return types.int64

    def resolve_month(self, typ):
        return types.int64

    def resolve_day(self, typ):
        return types.int64


@lower_getattr(DatetimeDateType, 'year')
def datetime_get_year(context, builder, typ, val):
    return builder.lshr(val, lir.Constant(lir.IntType(64), 32))


@lower_getattr(DatetimeDateType, 'month')
def datetime_get_month(context, builder, typ, val):
    return builder.and_(builder.lshr(val, lir.Constant(lir.IntType(64), 16)
        ), lir.Constant(lir.IntType(64), 65535))


@lower_getattr(DatetimeDateType, 'day')
def datetime_get_day(context, builder, typ, val):
    return builder.and_(val, lir.Constant(lir.IntType(64), 65535))


@unbox(DatetimeDateType)
def unbox_datetime_date(typ, val, c):
    qloui__aefj = c.pyapi.object_getattr_string(val, 'year')
    wdujz__ertee = c.pyapi.object_getattr_string(val, 'month')
    adx__fuona = c.pyapi.object_getattr_string(val, 'day')
    djlld__qbd = c.pyapi.long_as_longlong(qloui__aefj)
    ekza__iijk = c.pyapi.long_as_longlong(wdujz__ertee)
    iva__ozro = c.pyapi.long_as_longlong(adx__fuona)
    uofm__jxaaw = c.builder.add(iva__ozro, c.builder.add(c.builder.shl(
        djlld__qbd, lir.Constant(lir.IntType(64), 32)), c.builder.shl(
        ekza__iijk, lir.Constant(lir.IntType(64), 16))))
    c.pyapi.decref(qloui__aefj)
    c.pyapi.decref(wdujz__ertee)
    c.pyapi.decref(adx__fuona)
    jurm__fvnbd = cgutils.is_not_null(c.builder, c.pyapi.err_occurred())
    return NativeValue(uofm__jxaaw, is_error=jurm__fvnbd)


@lower_constant(DatetimeDateType)
def lower_constant_datetime_date(context, builder, ty, pyval):
    year = context.get_constant(types.int64, pyval.year)
    month = context.get_constant(types.int64, pyval.month)
    day = context.get_constant(types.int64, pyval.day)
    uofm__jxaaw = builder.add(day, builder.add(builder.shl(year, lir.
        Constant(lir.IntType(64), 32)), builder.shl(month, lir.Constant(lir
        .IntType(64), 16))))
    return uofm__jxaaw


@box(DatetimeDateType)
def box_datetime_date(typ, val, c):
    qloui__aefj = c.pyapi.long_from_longlong(c.builder.lshr(val, lir.
        Constant(lir.IntType(64), 32)))
    wdujz__ertee = c.pyapi.long_from_longlong(c.builder.and_(c.builder.lshr
        (val, lir.Constant(lir.IntType(64), 16)), lir.Constant(lir.IntType(
        64), 65535)))
    adx__fuona = c.pyapi.long_from_longlong(c.builder.and_(val, lir.
        Constant(lir.IntType(64), 65535)))
    jmd__zgsef = c.pyapi.unserialize(c.pyapi.serialize_object(datetime.date))
    gol__tphib = c.pyapi.call_function_objargs(jmd__zgsef, (qloui__aefj,
        wdujz__ertee, adx__fuona))
    c.pyapi.decref(qloui__aefj)
    c.pyapi.decref(wdujz__ertee)
    c.pyapi.decref(adx__fuona)
    c.pyapi.decref(jmd__zgsef)
    return gol__tphib


@type_callable(datetime.date)
def type_datetime_date(context):

    def typer(year, month, day):
        return datetime_date_type
    return typer


@lower_builtin(datetime.date, types.IntegerLiteral, types.IntegerLiteral,
    types.IntegerLiteral)
@lower_builtin(datetime.date, types.int64, types.int64, types.int64)
def impl_ctor_datetime_date(context, builder, sig, args):
    year, month, day = args
    uofm__jxaaw = builder.add(day, builder.add(builder.shl(year, lir.
        Constant(lir.IntType(64), 32)), builder.shl(month, lir.Constant(lir
        .IntType(64), 16))))
    return uofm__jxaaw


@intrinsic
def cast_int_to_datetime_date(typingctx, val=None):
    assert val == types.int64

    def codegen(context, builder, signature, args):
        return args[0]
    return datetime_date_type(types.int64), codegen


@intrinsic
def cast_datetime_date_to_int(typingctx, val=None):
    assert val == datetime_date_type

    def codegen(context, builder, signature, args):
        return args[0]
    return types.int64(datetime_date_type), codegen


"""
Following codes are copied from
https://github.com/python/cpython/blob/39a5c889d30d03a88102e56f03ee0c95db198fb3/Lib/datetime.py
"""
_MAXORDINAL = 3652059
_DAYS_IN_MONTH = np.array([-1, 31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 
    31], dtype=np.int64)
_DAYS_BEFORE_MONTH = np.array([-1, 0, 31, 59, 90, 120, 151, 181, 212, 243, 
    273, 304, 334], dtype=np.int64)


@register_jitable
def _is_leap(year):
    return year % 4 == 0 and (year % 100 != 0 or year % 400 == 0)


@register_jitable
def _days_before_year(year):
    y = year - 1
    return y * 365 + y // 4 - y // 100 + y // 400


@register_jitable
def _days_in_month(year, month):
    if month == 2 and _is_leap(year):
        return 29
    return _DAYS_IN_MONTH[month]


@register_jitable
def _days_before_month(year, month):
    return _DAYS_BEFORE_MONTH[month] + (month > 2 and _is_leap(year))


_DI400Y = _days_before_year(401)
_DI100Y = _days_before_year(101)
_DI4Y = _days_before_year(5)


@register_jitable
def _ymd2ord(year, month, day):
    wgtzn__cfg = _days_in_month(year, month)
    return _days_before_year(year) + _days_before_month(year, month) + day


@register_jitable
def _ord2ymd(n):
    n -= 1
    drdu__ewm, n = divmod(n, _DI400Y)
    year = drdu__ewm * 400 + 1
    zxku__faoc, n = divmod(n, _DI100Y)
    kres__tdzio, n = divmod(n, _DI4Y)
    uex__wclq, n = divmod(n, 365)
    year += zxku__faoc * 100 + kres__tdzio * 4 + uex__wclq
    if uex__wclq == 4 or zxku__faoc == 4:
        return year - 1, 12, 31
    wka__roejw = uex__wclq == 3 and (kres__tdzio != 24 or zxku__faoc == 3)
    month = n + 50 >> 5
    yfqeu__apw = _DAYS_BEFORE_MONTH[month] + (month > 2 and wka__roejw)
    if yfqeu__apw > n:
        month -= 1
        yfqeu__apw -= _DAYS_IN_MONTH[month] + (month == 2 and wka__roejw)
    n -= yfqeu__apw
    return year, month, n + 1


@register_jitable
def _cmp(x, y):
    return 0 if x == y else 1 if x > y else -1


@intrinsic
def get_isocalendar(typingctx, dt_year, dt_month, dt_day):

    def codegen(context, builder, sig, args):
        year = cgutils.alloca_once(builder, lir.IntType(64))
        qpwy__vos = cgutils.alloca_once(builder, lir.IntType(64))
        oecyp__dzumn = cgutils.alloca_once(builder, lir.IntType(64))
        aiogo__exvjr = lir.FunctionType(lir.VoidType(), [lir.IntType(64),
            lir.IntType(64), lir.IntType(64), lir.IntType(64).as_pointer(),
            lir.IntType(64).as_pointer(), lir.IntType(64).as_pointer()])
        ymxri__fvgc = cgutils.get_or_insert_function(builder.module,
            aiogo__exvjr, name='get_isocalendar')
        builder.call(ymxri__fvgc, [args[0], args[1], args[2], year,
            qpwy__vos, oecyp__dzumn])
        return cgutils.pack_array(builder, [builder.load(year), builder.
            load(qpwy__vos), builder.load(oecyp__dzumn)])
    gol__tphib = types.Tuple([types.int64, types.int64, types.int64])(types
        .int64, types.int64, types.int64), codegen
    return gol__tphib


types.datetime_date_type = datetime_date_type


@register_jitable
def today_impl():
    with numba.objmode(d='datetime_date_type'):
        d = datetime.date.today()
    return d


@register_jitable
def fromordinal_impl(n):
    y, tekaw__sco, d = _ord2ymd(n)
    return datetime.date(y, tekaw__sco, d)


@overload_method(DatetimeDateType, 'replace')
def replace_overload(date, year=None, month=None, day=None):
    if not is_overload_none(year) and not is_overload_int(year):
        raise BodoError('date.replace(): year must be an integer')
    elif not is_overload_none(month) and not is_overload_int(month):
        raise BodoError('date.replace(): month must be an integer')
    elif not is_overload_none(day) and not is_overload_int(day):
        raise BodoError('date.replace(): day must be an integer')

    def impl(date, year=None, month=None, day=None):
        tfvnk__lvx = date.year if year is None else year
        pcu__cfj = date.month if month is None else month
        nbrrm__jvi = date.day if day is None else day
        return datetime.date(tfvnk__lvx, pcu__cfj, nbrrm__jvi)
    return impl


@overload_method(DatetimeDatetimeType, 'toordinal', no_unliteral=True)
@overload_method(DatetimeDateType, 'toordinal', no_unliteral=True)
def toordinal(date):

    def impl(date):
        return _ymd2ord(date.year, date.month, date.day)
    return impl


@overload_method(DatetimeDatetimeType, 'weekday', no_unliteral=True)
@overload_method(DatetimeDateType, 'weekday', no_unliteral=True)
def weekday(date):

    def impl(date):
        return (date.toordinal() + 6) % 7
    return impl


@overload_method(DatetimeDateType, 'isocalendar', no_unliteral=True)
def overload_pd_timestamp_isocalendar(date):

    def impl(date):
        year, qpwy__vos, ufuou__ygc = get_isocalendar(date.year, date.month,
            date.day)
        return year, qpwy__vos, ufuou__ygc
    return impl


def overload_add_operator_datetime_date(lhs, rhs):
    if lhs == datetime_date_type and rhs == datetime_timedelta_type:

        def impl(lhs, rhs):
            qiw__mxuoy = lhs.toordinal() + rhs.days
            if 0 < qiw__mxuoy <= _MAXORDINAL:
                return fromordinal_impl(qiw__mxuoy)
            raise OverflowError('result out of range')
        return impl
    elif lhs == datetime_timedelta_type and rhs == datetime_date_type:

        def impl(lhs, rhs):
            qiw__mxuoy = lhs.days + rhs.toordinal()
            if 0 < qiw__mxuoy <= _MAXORDINAL:
                return fromordinal_impl(qiw__mxuoy)
            raise OverflowError('result out of range')
        return impl


def overload_sub_operator_datetime_date(lhs, rhs):
    if lhs == datetime_date_type and rhs == datetime_timedelta_type:

        def impl(lhs, rhs):
            return lhs + datetime.timedelta(-rhs.days)
        return impl
    elif lhs == datetime_date_type and rhs == datetime_date_type:

        def impl(lhs, rhs):
            cqx__fnvr = lhs.toordinal()
            gvqs__msr = rhs.toordinal()
            return datetime.timedelta(cqx__fnvr - gvqs__msr)
        return impl
    if lhs == datetime_date_array_type and rhs == datetime_timedelta_type:

        def impl(lhs, rhs):
            lnia__xwojw = lhs
            numba.parfors.parfor.init_prange()
            n = len(lnia__xwojw)
            A = alloc_datetime_date_array(n)
            for abpx__ofigt in numba.parfors.parfor.internal_prange(n):
                A[abpx__ofigt] = lnia__xwojw[abpx__ofigt] - rhs
            return A
        return impl


@overload(min, no_unliteral=True)
def date_min(lhs, rhs):
    if lhs == datetime_date_type and rhs == datetime_date_type:

        def impl(lhs, rhs):
            return lhs if lhs < rhs else rhs
        return impl


@overload(max, no_unliteral=True)
def date_max(lhs, rhs):
    if lhs == datetime_date_type and rhs == datetime_date_type:

        def impl(lhs, rhs):
            return lhs if lhs > rhs else rhs
        return impl


@overload_method(DatetimeDateType, '__hash__', no_unliteral=True)
def __hash__(td):

    def impl(td):
        ocpva__wfl = np.uint8(td.year // 256)
        obomo__wsvdf = np.uint8(td.year % 256)
        month = np.uint8(td.month)
        day = np.uint8(td.day)
        plitv__rny = ocpva__wfl, obomo__wsvdf, month, day
        return hash(plitv__rny)
    return impl


@overload(bool, inline='always', no_unliteral=True)
def date_to_bool(date):
    if date != datetime_date_type:
        return

    def impl(date):
        return True
    return impl


if PYVERSION >= (3, 9):
    IsoCalendarDate = datetime.date(2011, 1, 1).isocalendar().__class__


    class IsoCalendarDateType(types.Type):

        def __init__(self):
            super(IsoCalendarDateType, self).__init__(name=
                'IsoCalendarDateType()')
    iso_calendar_date_type = DatetimeDateType()

    @typeof_impl.register(IsoCalendarDate)
    def typeof_datetime_date(val, c):
        return iso_calendar_date_type


class DatetimeDateArrayType(types.ArrayCompatible):

    def __init__(self):
        super(DatetimeDateArrayType, self).__init__(name=
            'DatetimeDateArrayType()')

    @property
    def as_array(self):
        return types.Array(types.undefined, 1, 'C')

    @property
    def dtype(self):
        return datetime_date_type

    def copy(self):
        return DatetimeDateArrayType()


datetime_date_array_type = DatetimeDateArrayType()
types.datetime_date_array_type = datetime_date_array_type
data_type = types.Array(types.int64, 1, 'C')
nulls_type = types.Array(types.uint8, 1, 'C')


@register_model(DatetimeDateArrayType)
class DatetimeDateArrayModel(models.StructModel):

    def __init__(self, dmm, fe_type):
        arjdi__ukicd = [('data', data_type), ('null_bitmap', nulls_type)]
        models.StructModel.__init__(self, dmm, fe_type, arjdi__ukicd)


make_attribute_wrapper(DatetimeDateArrayType, 'data', '_data')
make_attribute_wrapper(DatetimeDateArrayType, 'null_bitmap', '_null_bitmap')


@overload_method(DatetimeDateArrayType, 'copy', no_unliteral=True)
def overload_datetime_date_arr_copy(A):
    return lambda A: bodo.hiframes.datetime_date_ext.init_datetime_date_array(A
        ._data.copy(), A._null_bitmap.copy())


@overload_attribute(DatetimeDateArrayType, 'dtype')
def overload_datetime_date_arr_dtype(A):
    return lambda A: np.object_


@unbox(DatetimeDateArrayType)
def unbox_datetime_date_array(typ, val, c):
    n = bodo.utils.utils.object_length(c, val)
    hfyb__axn = types.Array(types.intp, 1, 'C')
    mylwp__svf = bodo.utils.utils._empty_nd_impl(c.context, c.builder,
        hfyb__axn, [n])
    hsue__auvox = c.builder.udiv(c.builder.add(n, lir.Constant(lir.IntType(
        64), 7)), lir.Constant(lir.IntType(64), 8))
    tfgeu__jyv = bodo.utils.utils._empty_nd_impl(c.context, c.builder,
        types.Array(types.uint8, 1, 'C'), [hsue__auvox])
    aiogo__exvjr = lir.FunctionType(lir.VoidType(), [lir.IntType(8).
        as_pointer(), lir.IntType(64), lir.IntType(64).as_pointer(), lir.
        IntType(8).as_pointer()])
    wrv__kiu = cgutils.get_or_insert_function(c.builder.module,
        aiogo__exvjr, name='unbox_datetime_date_array')
    c.builder.call(wrv__kiu, [val, n, mylwp__svf.data, tfgeu__jyv.data])
    mdtkz__krqd = cgutils.create_struct_proxy(typ)(c.context, c.builder)
    mdtkz__krqd.data = mylwp__svf._getvalue()
    mdtkz__krqd.null_bitmap = tfgeu__jyv._getvalue()
    jurm__fvnbd = cgutils.is_not_null(c.builder, c.pyapi.err_occurred())
    return NativeValue(mdtkz__krqd._getvalue(), is_error=jurm__fvnbd)


def int_to_datetime_date_python(ia):
    return datetime.date(ia >> 32, ia >> 16 & 65535, ia & 65535)


def int_array_to_datetime_date(ia):
    return np.vectorize(int_to_datetime_date_python, otypes=[object])(ia)


@box(DatetimeDateArrayType)
def box_datetime_date_array(typ, val, c):
    lnia__xwojw = cgutils.create_struct_proxy(typ)(c.context, c.builder, val)
    mylwp__svf = c.context.make_array(types.Array(types.int64, 1, 'C'))(c.
        context, c.builder, lnia__xwojw.data)
    eqgu__dit = c.context.make_array(types.Array(types.uint8, 1, 'C'))(c.
        context, c.builder, lnia__xwojw.null_bitmap).data
    n = c.builder.extract_value(mylwp__svf.shape, 0)
    aiogo__exvjr = lir.FunctionType(c.pyapi.pyobj, [lir.IntType(64), lir.
        IntType(64).as_pointer(), lir.IntType(8).as_pointer()])
    dtru__uftv = cgutils.get_or_insert_function(c.builder.module,
        aiogo__exvjr, name='box_datetime_date_array')
    aiqxl__yre = c.builder.call(dtru__uftv, [n, mylwp__svf.data, eqgu__dit])
    c.context.nrt.decref(c.builder, typ, val)
    return aiqxl__yre


@intrinsic
def init_datetime_date_array(typingctx, data, nulls=None):
    assert data == types.Array(types.int64, 1, 'C') or data == types.Array(
        types.NPDatetime('ns'), 1, 'C')
    assert nulls == types.Array(types.uint8, 1, 'C')

    def codegen(context, builder, signature, args):
        pknf__cbwew, zbrbr__idouw = args
        erk__dfwde = cgutils.create_struct_proxy(signature.return_type)(context
            , builder)
        erk__dfwde.data = pknf__cbwew
        erk__dfwde.null_bitmap = zbrbr__idouw
        context.nrt.incref(builder, signature.args[0], pknf__cbwew)
        context.nrt.incref(builder, signature.args[1], zbrbr__idouw)
        return erk__dfwde._getvalue()
    sig = datetime_date_array_type(data, nulls)
    return sig, codegen


@lower_constant(DatetimeDateArrayType)
def lower_constant_datetime_date_arr(context, builder, typ, pyval):
    n = len(pyval)
    toxz__hhbw = (1970 << 32) + (1 << 16) + 1
    mylwp__svf = np.full(n, toxz__hhbw, np.int64)
    xsi__foer = np.empty(n + 7 >> 3, np.uint8)
    for abpx__ofigt, uunwz__rxgu in enumerate(pyval):
        mruq__riglx = pd.isna(uunwz__rxgu)
        bodo.libs.int_arr_ext.set_bit_to_arr(xsi__foer, abpx__ofigt, int(
            not mruq__riglx))
        if not mruq__riglx:
            mylwp__svf[abpx__ofigt] = (uunwz__rxgu.year << 32) + (uunwz__rxgu
                .month << 16) + uunwz__rxgu.day
    qzlc__iydex = context.get_constant_generic(builder, data_type, mylwp__svf)
    mzvxi__gkx = context.get_constant_generic(builder, nulls_type, xsi__foer)
    return lir.Constant.literal_struct([qzlc__iydex, mzvxi__gkx])


@numba.njit(no_cpython_wrapper=True)
def alloc_datetime_date_array(n):
    mylwp__svf = np.empty(n, dtype=np.int64)
    nulls = np.full(n + 7 >> 3, 255, np.uint8)
    return init_datetime_date_array(mylwp__svf, nulls)


def alloc_datetime_date_array_equiv(self, scope, equiv_set, loc, args, kws):
    assert len(args) == 1 and not kws
    return ArrayAnalysis.AnalyzeResult(shape=args[0], pre=[])


(ArrayAnalysis.
    _analyze_op_call_bodo_hiframes_datetime_date_ext_alloc_datetime_date_array
    ) = alloc_datetime_date_array_equiv


@overload(operator.getitem, no_unliteral=True)
def dt_date_arr_getitem(A, ind):
    if A != datetime_date_array_type:
        return
    if isinstance(types.unliteral(ind), types.Integer):
        return lambda A, ind: cast_int_to_datetime_date(A._data[ind])
    if is_list_like_index_type(ind) and ind.dtype == types.bool_:

        def impl_bool(A, ind):
            bqn__nbo, bmlw__mxbj = array_getitem_bool_index(A, ind)
            return init_datetime_date_array(bqn__nbo, bmlw__mxbj)
        return impl_bool
    if is_list_like_index_type(ind) and isinstance(ind.dtype, types.Integer):

        def impl(A, ind):
            bqn__nbo, bmlw__mxbj = array_getitem_int_index(A, ind)
            return init_datetime_date_array(bqn__nbo, bmlw__mxbj)
        return impl
    if isinstance(ind, types.SliceType):

        def impl_slice(A, ind):
            bqn__nbo, bmlw__mxbj = array_getitem_slice_index(A, ind)
            return init_datetime_date_array(bqn__nbo, bmlw__mxbj)
        return impl_slice
    raise BodoError(
        f'getitem for DatetimeDateArray with indexing type {ind} not supported.'
        )


@overload(operator.setitem, no_unliteral=True)
def dt_date_arr_setitem(A, idx, val):
    if A != datetime_date_array_type:
        return
    if val == types.none or isinstance(val, types.optional):
        return
    wdsa__hexd = (
        f"setitem for DatetimeDateArray with indexing type {idx} received an incorrect 'value' type {val}."
        )
    if isinstance(idx, types.Integer):
        if types.unliteral(val) == datetime_date_type:

            def impl(A, idx, val):
                A._data[idx] = cast_datetime_date_to_int(val)
                bodo.libs.int_arr_ext.set_bit_to_arr(A._null_bitmap, idx, 1)
            return impl
        else:
            raise BodoError(wdsa__hexd)
    if not (is_iterable_type(val) and val.dtype == bodo.datetime_date_type or
        types.unliteral(val) == datetime_date_type):
        raise BodoError(wdsa__hexd)
    if is_list_like_index_type(idx) and isinstance(idx.dtype, types.Integer):
        if types.unliteral(val) == datetime_date_type:
            return lambda A, idx, val: array_setitem_int_index(A, idx,
                cast_datetime_date_to_int(val))

        def impl_arr_ind(A, idx, val):
            array_setitem_int_index(A, idx, val)
        return impl_arr_ind
    if is_list_like_index_type(idx) and idx.dtype == types.bool_:
        if types.unliteral(val) == datetime_date_type:
            return lambda A, idx, val: array_setitem_bool_index(A, idx,
                cast_datetime_date_to_int(val))

        def impl_bool_ind_mask(A, idx, val):
            array_setitem_bool_index(A, idx, val)
        return impl_bool_ind_mask
    if isinstance(idx, types.SliceType):
        if types.unliteral(val) == datetime_date_type:
            return lambda A, idx, val: array_setitem_slice_index(A, idx,
                cast_datetime_date_to_int(val))

        def impl_slice_mask(A, idx, val):
            array_setitem_slice_index(A, idx, val)
        return impl_slice_mask
    raise BodoError(
        f'setitem for DatetimeDateArray with indexing type {idx} not supported.'
        )


@overload(len, no_unliteral=True)
def overload_len_datetime_date_arr(A):
    if A == datetime_date_array_type:
        return lambda A: len(A._data)


@overload_attribute(DatetimeDateArrayType, 'shape')
def overload_datetime_date_arr_shape(A):
    return lambda A: (len(A._data),)


@overload_attribute(DatetimeDateArrayType, 'nbytes')
def datetime_arr_nbytes_overload(A):
    return lambda A: A._data.nbytes + A._null_bitmap.nbytes


def create_cmp_op_overload(op):

    def overload_date_cmp(lhs, rhs):
        if lhs == datetime_date_type and rhs == datetime_date_type:

            def impl(lhs, rhs):
                y, tfcrp__xcnnp = lhs.year, rhs.year
                tekaw__sco, kfyfb__bujxj = lhs.month, rhs.month
                d, qrmdw__onj = lhs.day, rhs.day
                return op(_cmp((y, tekaw__sco, d), (tfcrp__xcnnp,
                    kfyfb__bujxj, qrmdw__onj)), 0)
            return impl
    return overload_date_cmp


def create_datetime_date_cmp_op_overload(op):

    def overload_cmp(lhs, rhs):
        mpbr__xlum = (
            f'{lhs} {numba.core.utils.OPERATORS_TO_BUILTINS[op]} {rhs} is always {op == operator.ne} in Python. If this is unexpected there may be a bug in your code.'
            )
        warnings.warn(mpbr__xlum, bodo.utils.typing.BodoWarning)
        if op == operator.eq:
            return lambda lhs, rhs: False
        elif op == operator.ne:
            return lambda lhs, rhs: True
    return overload_cmp


def create_cmp_op_overload_arr(op):

    def overload_date_arr_cmp(lhs, rhs):
        if op == operator.ne:
            kjq__ftr = True
        else:
            kjq__ftr = False
        if lhs == datetime_date_array_type and rhs == datetime_date_array_type:

            def impl(lhs, rhs):
                numba.parfors.parfor.init_prange()
                n = len(lhs)
                hlce__ery = bodo.libs.bool_arr_ext.alloc_bool_array(n)
                for abpx__ofigt in numba.parfors.parfor.internal_prange(n):
                    rvh__aapd = bodo.libs.array_kernels.isna(lhs, abpx__ofigt)
                    jfxw__cvb = bodo.libs.array_kernels.isna(rhs, abpx__ofigt)
                    if rvh__aapd or jfxw__cvb:
                        dqu__sga = kjq__ftr
                    else:
                        dqu__sga = op(lhs[abpx__ofigt], rhs[abpx__ofigt])
                    hlce__ery[abpx__ofigt] = dqu__sga
                return hlce__ery
            return impl
        elif lhs == datetime_date_array_type:

            def impl(lhs, rhs):
                numba.parfors.parfor.init_prange()
                n = len(lhs)
                hlce__ery = bodo.libs.bool_arr_ext.alloc_bool_array(n)
                for abpx__ofigt in numba.parfors.parfor.internal_prange(n):
                    zajl__haccg = bodo.libs.array_kernels.isna(lhs, abpx__ofigt
                        )
                    if zajl__haccg:
                        dqu__sga = kjq__ftr
                    else:
                        dqu__sga = op(lhs[abpx__ofigt], rhs)
                    hlce__ery[abpx__ofigt] = dqu__sga
                return hlce__ery
            return impl
        elif rhs == datetime_date_array_type:

            def impl(lhs, rhs):
                numba.parfors.parfor.init_prange()
                n = len(rhs)
                hlce__ery = bodo.libs.bool_arr_ext.alloc_bool_array(n)
                for abpx__ofigt in numba.parfors.parfor.internal_prange(n):
                    zajl__haccg = bodo.libs.array_kernels.isna(rhs, abpx__ofigt
                        )
                    if zajl__haccg:
                        dqu__sga = kjq__ftr
                    else:
                        dqu__sga = op(lhs, rhs[abpx__ofigt])
                    hlce__ery[abpx__ofigt] = dqu__sga
                return hlce__ery
            return impl
    return overload_date_arr_cmp
