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
    cud__vict = c.pyapi.object_getattr_string(val, 'year')
    kdvx__tohpl = c.pyapi.object_getattr_string(val, 'month')
    qbfuf__jvtet = c.pyapi.object_getattr_string(val, 'day')
    aml__etwcd = c.pyapi.long_as_longlong(cud__vict)
    eckd__dtvvf = c.pyapi.long_as_longlong(kdvx__tohpl)
    aayf__jkon = c.pyapi.long_as_longlong(qbfuf__jvtet)
    nfl__rhvi = c.builder.add(aayf__jkon, c.builder.add(c.builder.shl(
        aml__etwcd, lir.Constant(lir.IntType(64), 32)), c.builder.shl(
        eckd__dtvvf, lir.Constant(lir.IntType(64), 16))))
    c.pyapi.decref(cud__vict)
    c.pyapi.decref(kdvx__tohpl)
    c.pyapi.decref(qbfuf__jvtet)
    cwhh__xcmai = cgutils.is_not_null(c.builder, c.pyapi.err_occurred())
    return NativeValue(nfl__rhvi, is_error=cwhh__xcmai)


@lower_constant(DatetimeDateType)
def lower_constant_datetime_date(context, builder, ty, pyval):
    year = context.get_constant(types.int64, pyval.year)
    month = context.get_constant(types.int64, pyval.month)
    day = context.get_constant(types.int64, pyval.day)
    nfl__rhvi = builder.add(day, builder.add(builder.shl(year, lir.Constant
        (lir.IntType(64), 32)), builder.shl(month, lir.Constant(lir.IntType
        (64), 16))))
    return nfl__rhvi


@box(DatetimeDateType)
def box_datetime_date(typ, val, c):
    cud__vict = c.pyapi.long_from_longlong(c.builder.lshr(val, lir.Constant
        (lir.IntType(64), 32)))
    kdvx__tohpl = c.pyapi.long_from_longlong(c.builder.and_(c.builder.lshr(
        val, lir.Constant(lir.IntType(64), 16)), lir.Constant(lir.IntType(
        64), 65535)))
    qbfuf__jvtet = c.pyapi.long_from_longlong(c.builder.and_(val, lir.
        Constant(lir.IntType(64), 65535)))
    nct__mshi = c.pyapi.unserialize(c.pyapi.serialize_object(datetime.date))
    joj__ypplq = c.pyapi.call_function_objargs(nct__mshi, (cud__vict,
        kdvx__tohpl, qbfuf__jvtet))
    c.pyapi.decref(cud__vict)
    c.pyapi.decref(kdvx__tohpl)
    c.pyapi.decref(qbfuf__jvtet)
    c.pyapi.decref(nct__mshi)
    return joj__ypplq


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
    nfl__rhvi = builder.add(day, builder.add(builder.shl(year, lir.Constant
        (lir.IntType(64), 32)), builder.shl(month, lir.Constant(lir.IntType
        (64), 16))))
    return nfl__rhvi


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
    apr__ytg = _days_in_month(year, month)
    return _days_before_year(year) + _days_before_month(year, month) + day


@register_jitable
def _ord2ymd(n):
    n -= 1
    suh__nvipd, n = divmod(n, _DI400Y)
    year = suh__nvipd * 400 + 1
    xvfc__wbaex, n = divmod(n, _DI100Y)
    uhmk__iclk, n = divmod(n, _DI4Y)
    vsf__pen, n = divmod(n, 365)
    year += xvfc__wbaex * 100 + uhmk__iclk * 4 + vsf__pen
    if vsf__pen == 4 or xvfc__wbaex == 4:
        return year - 1, 12, 31
    yql__iadhm = vsf__pen == 3 and (uhmk__iclk != 24 or xvfc__wbaex == 3)
    month = n + 50 >> 5
    xyoc__jego = _DAYS_BEFORE_MONTH[month] + (month > 2 and yql__iadhm)
    if xyoc__jego > n:
        month -= 1
        xyoc__jego -= _DAYS_IN_MONTH[month] + (month == 2 and yql__iadhm)
    n -= xyoc__jego
    return year, month, n + 1


@register_jitable
def _cmp(x, y):
    return 0 if x == y else 1 if x > y else -1


@intrinsic
def get_isocalendar(typingctx, dt_year, dt_month, dt_day):

    def codegen(context, builder, sig, args):
        year = cgutils.alloca_once(builder, lir.IntType(64))
        sje__nufiw = cgutils.alloca_once(builder, lir.IntType(64))
        ihnjg__hgnq = cgutils.alloca_once(builder, lir.IntType(64))
        iymup__dgx = lir.FunctionType(lir.VoidType(), [lir.IntType(64), lir
            .IntType(64), lir.IntType(64), lir.IntType(64).as_pointer(),
            lir.IntType(64).as_pointer(), lir.IntType(64).as_pointer()])
        sggs__fnm = cgutils.get_or_insert_function(builder.module,
            iymup__dgx, name='get_isocalendar')
        builder.call(sggs__fnm, [args[0], args[1], args[2], year,
            sje__nufiw, ihnjg__hgnq])
        return cgutils.pack_array(builder, [builder.load(year), builder.
            load(sje__nufiw), builder.load(ihnjg__hgnq)])
    joj__ypplq = types.Tuple([types.int64, types.int64, types.int64])(types
        .int64, types.int64, types.int64), codegen
    return joj__ypplq


types.datetime_date_type = datetime_date_type


@register_jitable
def today_impl():
    with numba.objmode(d='datetime_date_type'):
        d = datetime.date.today()
    return d


@register_jitable
def fromordinal_impl(n):
    y, nwak__ffnbo, d = _ord2ymd(n)
    return datetime.date(y, nwak__ffnbo, d)


@overload_method(DatetimeDateType, 'replace')
def replace_overload(date, year=None, month=None, day=None):
    if not is_overload_none(year) and not is_overload_int(year):
        raise BodoError('date.replace(): year must be an integer')
    elif not is_overload_none(month) and not is_overload_int(month):
        raise BodoError('date.replace(): month must be an integer')
    elif not is_overload_none(day) and not is_overload_int(day):
        raise BodoError('date.replace(): day must be an integer')

    def impl(date, year=None, month=None, day=None):
        bszhh__uritk = date.year if year is None else year
        ggvb__kaaap = date.month if month is None else month
        jvrql__wzxb = date.day if day is None else day
        return datetime.date(bszhh__uritk, ggvb__kaaap, jvrql__wzxb)
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
        year, sje__nufiw, pie__hdf = get_isocalendar(date.year, date.month,
            date.day)
        return year, sje__nufiw, pie__hdf
    return impl


def overload_add_operator_datetime_date(lhs, rhs):
    if lhs == datetime_date_type and rhs == datetime_timedelta_type:

        def impl(lhs, rhs):
            isj__ykcn = lhs.toordinal() + rhs.days
            if 0 < isj__ykcn <= _MAXORDINAL:
                return fromordinal_impl(isj__ykcn)
            raise OverflowError('result out of range')
        return impl
    elif lhs == datetime_timedelta_type and rhs == datetime_date_type:

        def impl(lhs, rhs):
            isj__ykcn = lhs.days + rhs.toordinal()
            if 0 < isj__ykcn <= _MAXORDINAL:
                return fromordinal_impl(isj__ykcn)
            raise OverflowError('result out of range')
        return impl


def overload_sub_operator_datetime_date(lhs, rhs):
    if lhs == datetime_date_type and rhs == datetime_timedelta_type:

        def impl(lhs, rhs):
            return lhs + datetime.timedelta(-rhs.days)
        return impl
    elif lhs == datetime_date_type and rhs == datetime_date_type:

        def impl(lhs, rhs):
            xgfeb__espt = lhs.toordinal()
            cfpim__myfil = rhs.toordinal()
            return datetime.timedelta(xgfeb__espt - cfpim__myfil)
        return impl
    if lhs == datetime_date_array_type and rhs == datetime_timedelta_type:

        def impl(lhs, rhs):
            axu__mvy = lhs
            numba.parfors.parfor.init_prange()
            n = len(axu__mvy)
            A = alloc_datetime_date_array(n)
            for vdpe__juy in numba.parfors.parfor.internal_prange(n):
                A[vdpe__juy] = axu__mvy[vdpe__juy] - rhs
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
        jsnz__qrmeo = np.uint8(td.year // 256)
        wweff__luc = np.uint8(td.year % 256)
        month = np.uint8(td.month)
        day = np.uint8(td.day)
        rff__whz = jsnz__qrmeo, wweff__luc, month, day
        return hash(rff__whz)
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
        lqvk__tsttr = [('data', data_type), ('null_bitmap', nulls_type)]
        models.StructModel.__init__(self, dmm, fe_type, lqvk__tsttr)


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
    ueb__bwf = types.Array(types.intp, 1, 'C')
    zby__scu = bodo.utils.utils._empty_nd_impl(c.context, c.builder,
        ueb__bwf, [n])
    kvup__xxx = c.builder.udiv(c.builder.add(n, lir.Constant(lir.IntType(64
        ), 7)), lir.Constant(lir.IntType(64), 8))
    cxpak__xwpwz = bodo.utils.utils._empty_nd_impl(c.context, c.builder,
        types.Array(types.uint8, 1, 'C'), [kvup__xxx])
    iymup__dgx = lir.FunctionType(lir.VoidType(), [lir.IntType(8).
        as_pointer(), lir.IntType(64), lir.IntType(64).as_pointer(), lir.
        IntType(8).as_pointer()])
    aqa__rjc = cgutils.get_or_insert_function(c.builder.module, iymup__dgx,
        name='unbox_datetime_date_array')
    c.builder.call(aqa__rjc, [val, n, zby__scu.data, cxpak__xwpwz.data])
    lpo__cmwye = cgutils.create_struct_proxy(typ)(c.context, c.builder)
    lpo__cmwye.data = zby__scu._getvalue()
    lpo__cmwye.null_bitmap = cxpak__xwpwz._getvalue()
    cwhh__xcmai = cgutils.is_not_null(c.builder, c.pyapi.err_occurred())
    return NativeValue(lpo__cmwye._getvalue(), is_error=cwhh__xcmai)


def int_to_datetime_date_python(ia):
    return datetime.date(ia >> 32, ia >> 16 & 65535, ia & 65535)


def int_array_to_datetime_date(ia):
    return np.vectorize(int_to_datetime_date_python, otypes=[object])(ia)


@box(DatetimeDateArrayType)
def box_datetime_date_array(typ, val, c):
    axu__mvy = cgutils.create_struct_proxy(typ)(c.context, c.builder, val)
    zby__scu = c.context.make_array(types.Array(types.int64, 1, 'C'))(c.
        context, c.builder, axu__mvy.data)
    lkgqx__cdk = c.context.make_array(types.Array(types.uint8, 1, 'C'))(c.
        context, c.builder, axu__mvy.null_bitmap).data
    n = c.builder.extract_value(zby__scu.shape, 0)
    iymup__dgx = lir.FunctionType(c.pyapi.pyobj, [lir.IntType(64), lir.
        IntType(64).as_pointer(), lir.IntType(8).as_pointer()])
    ord__ostxa = cgutils.get_or_insert_function(c.builder.module,
        iymup__dgx, name='box_datetime_date_array')
    eskm__mjfmn = c.builder.call(ord__ostxa, [n, zby__scu.data, lkgqx__cdk])
    c.context.nrt.decref(c.builder, typ, val)
    return eskm__mjfmn


@intrinsic
def init_datetime_date_array(typingctx, data, nulls=None):
    assert data == types.Array(types.int64, 1, 'C') or data == types.Array(
        types.NPDatetime('ns'), 1, 'C')
    assert nulls == types.Array(types.uint8, 1, 'C')

    def codegen(context, builder, signature, args):
        pzzgb__lwm, aumii__fhzv = args
        yyxdb__jwlor = cgutils.create_struct_proxy(signature.return_type)(
            context, builder)
        yyxdb__jwlor.data = pzzgb__lwm
        yyxdb__jwlor.null_bitmap = aumii__fhzv
        context.nrt.incref(builder, signature.args[0], pzzgb__lwm)
        context.nrt.incref(builder, signature.args[1], aumii__fhzv)
        return yyxdb__jwlor._getvalue()
    sig = datetime_date_array_type(data, nulls)
    return sig, codegen


@lower_constant(DatetimeDateArrayType)
def lower_constant_datetime_date_arr(context, builder, typ, pyval):
    n = len(pyval)
    awlu__ojhcs = (1970 << 32) + (1 << 16) + 1
    zby__scu = np.full(n, awlu__ojhcs, np.int64)
    tggc__nfxr = np.empty(n + 7 >> 3, np.uint8)
    for vdpe__juy, gcnn__fziq in enumerate(pyval):
        zpm__jhr = pd.isna(gcnn__fziq)
        bodo.libs.int_arr_ext.set_bit_to_arr(tggc__nfxr, vdpe__juy, int(not
            zpm__jhr))
        if not zpm__jhr:
            zby__scu[vdpe__juy] = (gcnn__fziq.year << 32) + (gcnn__fziq.
                month << 16) + gcnn__fziq.day
    ltag__aueku = context.get_constant_generic(builder, data_type, zby__scu)
    owan__fmug = context.get_constant_generic(builder, nulls_type, tggc__nfxr)
    return lir.Constant.literal_struct([ltag__aueku, owan__fmug])


@numba.njit(no_cpython_wrapper=True)
def alloc_datetime_date_array(n):
    zby__scu = np.empty(n, dtype=np.int64)
    nulls = np.full(n + 7 >> 3, 255, np.uint8)
    return init_datetime_date_array(zby__scu, nulls)


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
            fwql__zhgae, iqvg__gjhd = array_getitem_bool_index(A, ind)
            return init_datetime_date_array(fwql__zhgae, iqvg__gjhd)
        return impl_bool
    if is_list_like_index_type(ind) and isinstance(ind.dtype, types.Integer):

        def impl(A, ind):
            fwql__zhgae, iqvg__gjhd = array_getitem_int_index(A, ind)
            return init_datetime_date_array(fwql__zhgae, iqvg__gjhd)
        return impl
    if isinstance(ind, types.SliceType):

        def impl_slice(A, ind):
            fwql__zhgae, iqvg__gjhd = array_getitem_slice_index(A, ind)
            return init_datetime_date_array(fwql__zhgae, iqvg__gjhd)
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
    httxf__rsfsm = (
        f"setitem for DatetimeDateArray with indexing type {idx} received an incorrect 'value' type {val}."
        )
    if isinstance(idx, types.Integer):
        if types.unliteral(val) == datetime_date_type:

            def impl(A, idx, val):
                A._data[idx] = cast_datetime_date_to_int(val)
                bodo.libs.int_arr_ext.set_bit_to_arr(A._null_bitmap, idx, 1)
            return impl
        else:
            raise BodoError(httxf__rsfsm)
    if not (is_iterable_type(val) and val.dtype == bodo.datetime_date_type or
        types.unliteral(val) == datetime_date_type):
        raise BodoError(httxf__rsfsm)
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
                y, szop__gqzjy = lhs.year, rhs.year
                nwak__ffnbo, tknar__fmje = lhs.month, rhs.month
                d, gsqwj__ctec = lhs.day, rhs.day
                return op(_cmp((y, nwak__ffnbo, d), (szop__gqzjy,
                    tknar__fmje, gsqwj__ctec)), 0)
            return impl
    return overload_date_cmp


def create_datetime_date_cmp_op_overload(op):

    def overload_cmp(lhs, rhs):
        zadzp__eel = (
            f'{lhs} {numba.core.utils.OPERATORS_TO_BUILTINS[op]} {rhs} is always {op == operator.ne} in Python. If this is unexpected there may be a bug in your code.'
            )
        warnings.warn(zadzp__eel, bodo.utils.typing.BodoWarning)
        if op == operator.eq:
            return lambda lhs, rhs: False
        elif op == operator.ne:
            return lambda lhs, rhs: True
    return overload_cmp


def create_cmp_op_overload_arr(op):

    def overload_date_arr_cmp(lhs, rhs):
        if op == operator.ne:
            mbhd__bkw = True
        else:
            mbhd__bkw = False
        if lhs == datetime_date_array_type and rhs == datetime_date_array_type:

            def impl(lhs, rhs):
                numba.parfors.parfor.init_prange()
                n = len(lhs)
                xgro__bkden = bodo.libs.bool_arr_ext.alloc_bool_array(n)
                for vdpe__juy in numba.parfors.parfor.internal_prange(n):
                    ejcl__ymf = bodo.libs.array_kernels.isna(lhs, vdpe__juy)
                    ltzta__kfxwm = bodo.libs.array_kernels.isna(rhs, vdpe__juy)
                    if ejcl__ymf or ltzta__kfxwm:
                        osghu__pgiep = mbhd__bkw
                    else:
                        osghu__pgiep = op(lhs[vdpe__juy], rhs[vdpe__juy])
                    xgro__bkden[vdpe__juy] = osghu__pgiep
                return xgro__bkden
            return impl
        elif lhs == datetime_date_array_type:

            def impl(lhs, rhs):
                numba.parfors.parfor.init_prange()
                n = len(lhs)
                xgro__bkden = bodo.libs.bool_arr_ext.alloc_bool_array(n)
                for vdpe__juy in numba.parfors.parfor.internal_prange(n):
                    petu__heny = bodo.libs.array_kernels.isna(lhs, vdpe__juy)
                    if petu__heny:
                        osghu__pgiep = mbhd__bkw
                    else:
                        osghu__pgiep = op(lhs[vdpe__juy], rhs)
                    xgro__bkden[vdpe__juy] = osghu__pgiep
                return xgro__bkden
            return impl
        elif rhs == datetime_date_array_type:

            def impl(lhs, rhs):
                numba.parfors.parfor.init_prange()
                n = len(rhs)
                xgro__bkden = bodo.libs.bool_arr_ext.alloc_bool_array(n)
                for vdpe__juy in numba.parfors.parfor.internal_prange(n):
                    petu__heny = bodo.libs.array_kernels.isna(rhs, vdpe__juy)
                    if petu__heny:
                        osghu__pgiep = mbhd__bkw
                    else:
                        osghu__pgiep = op(lhs, rhs[vdpe__juy])
                    xgro__bkden[vdpe__juy] = osghu__pgiep
                return xgro__bkden
            return impl
    return overload_date_arr_cmp
