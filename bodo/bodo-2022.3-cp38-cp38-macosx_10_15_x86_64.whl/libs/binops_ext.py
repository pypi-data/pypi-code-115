""" Implementation of binary operators for the different types.
    Currently implemented operators:
        arith: add, sub, mul, truediv, floordiv, mod, pow
        cmp: lt, le, eq, ne, ge, gt
"""
import operator
import numba
from numba.core import types
from numba.core.imputils import lower_builtin
from numba.core.typing.builtins import machine_ints
from numba.core.typing.templates import AbstractTemplate, infer_global
from numba.extending import overload
import bodo
from bodo.hiframes.datetime_date_ext import datetime_date_array_type, datetime_date_type, datetime_timedelta_type
from bodo.hiframes.datetime_timedelta_ext import datetime_datetime_type, datetime_timedelta_array_type, pd_timedelta_type
from bodo.hiframes.pd_dataframe_ext import DataFrameType
from bodo.hiframes.pd_index_ext import DatetimeIndexType, HeterogeneousIndexType, is_index_type
from bodo.hiframes.pd_offsets_ext import date_offset_type, month_begin_type, month_end_type, week_type
from bodo.hiframes.pd_timestamp_ext import pd_timestamp_type
from bodo.hiframes.series_impl import SeriesType
from bodo.libs.binary_arr_ext import binary_array_type, bytes_type
from bodo.libs.bool_arr_ext import boolean_array
from bodo.libs.decimal_arr_ext import Decimal128Type
from bodo.libs.int_arr_ext import IntegerArrayType
from bodo.libs.str_ext import string_type
from bodo.utils.typing import BodoError, is_overload_bool, is_str_arr_type, is_timedelta_type


class SeriesCmpOpTemplate(AbstractTemplate):

    def generic(self, args, kws):
        assert not kws
        assert len(args) == 2
        lhs, rhs = args
        if cmp_timeseries(lhs, rhs) or (isinstance(lhs, DataFrameType) or
            isinstance(rhs, DataFrameType)) or not (isinstance(lhs,
            SeriesType) or isinstance(rhs, SeriesType)):
            return
        dne__uaxyp = lhs.data if isinstance(lhs, SeriesType) else lhs
        zzs__yns = rhs.data if isinstance(rhs, SeriesType) else rhs
        if dne__uaxyp in (bodo.pd_timestamp_type, bodo.pd_timedelta_type
            ) and zzs__yns.dtype in (bodo.datetime64ns, bodo.timedelta64ns):
            dne__uaxyp = zzs__yns.dtype
        elif zzs__yns in (bodo.pd_timestamp_type, bodo.pd_timedelta_type
            ) and dne__uaxyp.dtype in (bodo.datetime64ns, bodo.timedelta64ns):
            zzs__yns = dne__uaxyp.dtype
        ekk__lceg = dne__uaxyp, zzs__yns
        whe__invf = (
            f'{lhs} {numba.core.utils.OPERATORS_TO_BUILTINS[self.key]} {rhs} not supported'
            )
        try:
            ipode__ixgfw = self.context.resolve_function_type(self.key,
                ekk__lceg, {}).return_type
        except Exception as odnvh__vhwr:
            raise BodoError(whe__invf)
        if is_overload_bool(ipode__ixgfw):
            raise BodoError(whe__invf)
        feqv__xaiv = lhs.index if isinstance(lhs, SeriesType) else rhs.index
        cztpp__ctkps = lhs.name_typ if isinstance(lhs, SeriesType
            ) else rhs.name_typ
        tatj__ejfx = types.bool_
        iyg__zfdr = SeriesType(tatj__ejfx, ipode__ixgfw, feqv__xaiv,
            cztpp__ctkps)
        return iyg__zfdr(*args)


def series_cmp_op_lower(op):

    def lower_impl(context, builder, sig, args):
        bwx__pzja = bodo.hiframes.series_impl.create_binary_op_overload(op)(*
            sig.args)
        if bwx__pzja is None:
            bwx__pzja = create_overload_cmp_operator(op)(*sig.args)
        return context.compile_internal(builder, bwx__pzja, sig, args)
    return lower_impl


class SeriesAndOrTyper(AbstractTemplate):

    def generic(self, args, kws):
        assert len(args) == 2
        assert not kws
        lhs, rhs = args
        if not (isinstance(lhs, SeriesType) or isinstance(rhs, SeriesType)):
            return
        dne__uaxyp = lhs.data if isinstance(lhs, SeriesType) else lhs
        zzs__yns = rhs.data if isinstance(rhs, SeriesType) else rhs
        ekk__lceg = dne__uaxyp, zzs__yns
        whe__invf = (
            f'{lhs} {numba.core.utils.OPERATORS_TO_BUILTINS[self.key]} {rhs} not supported'
            )
        try:
            ipode__ixgfw = self.context.resolve_function_type(self.key,
                ekk__lceg, {}).return_type
        except Exception as wbquy__egk:
            raise BodoError(whe__invf)
        feqv__xaiv = lhs.index if isinstance(lhs, SeriesType) else rhs.index
        cztpp__ctkps = lhs.name_typ if isinstance(lhs, SeriesType
            ) else rhs.name_typ
        tatj__ejfx = ipode__ixgfw.dtype
        iyg__zfdr = SeriesType(tatj__ejfx, ipode__ixgfw, feqv__xaiv,
            cztpp__ctkps)
        return iyg__zfdr(*args)


def lower_series_and_or(op):

    def lower_and_or_impl(context, builder, sig, args):
        bwx__pzja = bodo.hiframes.series_impl.create_binary_op_overload(op)(*
            sig.args)
        if bwx__pzja is None:
            lhs, rhs = sig.args
            if isinstance(lhs, DataFrameType) or isinstance(rhs, DataFrameType
                ):
                bwx__pzja = (bodo.hiframes.dataframe_impl.
                    create_binary_op_overload(op)(*sig.args))
        return context.compile_internal(builder, bwx__pzja, sig, args)
    return lower_and_or_impl


def overload_add_operator_scalars(lhs, rhs):
    if lhs == week_type or rhs == week_type:
        return (bodo.hiframes.pd_offsets_ext.
            overload_add_operator_week_offset_type(lhs, rhs))
    if lhs == month_begin_type or rhs == month_begin_type:
        return (bodo.hiframes.pd_offsets_ext.
            overload_add_operator_month_begin_offset_type(lhs, rhs))
    if lhs == month_end_type or rhs == month_end_type:
        return (bodo.hiframes.pd_offsets_ext.
            overload_add_operator_month_end_offset_type(lhs, rhs))
    if lhs == date_offset_type or rhs == date_offset_type:
        return (bodo.hiframes.pd_offsets_ext.
            overload_add_operator_date_offset_type(lhs, rhs))
    if add_timestamp(lhs, rhs):
        return bodo.hiframes.pd_timestamp_ext.overload_add_operator_timestamp(
            lhs, rhs)
    if add_dt_td_and_dt_date(lhs, rhs):
        return (bodo.hiframes.datetime_date_ext.
            overload_add_operator_datetime_date(lhs, rhs))
    if add_datetime_and_timedeltas(lhs, rhs):
        return (bodo.hiframes.datetime_timedelta_ext.
            overload_add_operator_datetime_timedelta(lhs, rhs))
    raise_error_if_not_numba_supported(operator.add, lhs, rhs)


def overload_sub_operator_scalars(lhs, rhs):
    if sub_offset_to_datetime_or_timestamp(lhs, rhs):
        return bodo.hiframes.pd_offsets_ext.overload_sub_operator_offsets(lhs,
            rhs)
    if lhs == pd_timestamp_type and rhs in [pd_timestamp_type,
        datetime_timedelta_type, pd_timedelta_type]:
        return bodo.hiframes.pd_timestamp_ext.overload_sub_operator_timestamp(
            lhs, rhs)
    if sub_dt_or_td(lhs, rhs):
        return (bodo.hiframes.datetime_date_ext.
            overload_sub_operator_datetime_date(lhs, rhs))
    if sub_datetime_and_timedeltas(lhs, rhs):
        return (bodo.hiframes.datetime_timedelta_ext.
            overload_sub_operator_datetime_timedelta(lhs, rhs))
    if lhs == datetime_datetime_type and rhs == datetime_datetime_type:
        return (bodo.hiframes.datetime_datetime_ext.
            overload_sub_operator_datetime_datetime(lhs, rhs))
    raise_error_if_not_numba_supported(operator.sub, lhs, rhs)


def create_overload_arith_op(op):

    def overload_arith_operator(lhs, rhs):
        bodo.hiframes.pd_timestamp_ext.check_tz_aware_unsupported(lhs,
            f'{op} operator')
        bodo.hiframes.pd_timestamp_ext.check_tz_aware_unsupported(rhs,
            f'{op} operator')
        if isinstance(lhs, DataFrameType) or isinstance(rhs, DataFrameType):
            return bodo.hiframes.dataframe_impl.create_binary_op_overload(op)(
                lhs, rhs)
        if time_series_operation(lhs, rhs) and op in [operator.add,
            operator.sub]:
            return bodo.hiframes.series_dt_impl.create_bin_op_overload(op)(lhs,
                rhs)
        if isinstance(lhs, SeriesType) or isinstance(rhs, SeriesType):
            return bodo.hiframes.series_impl.create_binary_op_overload(op)(lhs,
                rhs)
        if sub_dt_index_and_timestamp(lhs, rhs) and op == operator.sub:
            return (bodo.hiframes.pd_index_ext.
                overload_sub_operator_datetime_index(lhs, rhs))
        if operand_is_index(lhs) or operand_is_index(rhs):
            return bodo.hiframes.pd_index_ext.create_binary_op_overload(op)(lhs
                , rhs)
        if args_td_and_int_array(lhs, rhs):
            return bodo.libs.int_arr_ext.get_int_array_op_pd_td(op)(lhs, rhs)
        if isinstance(lhs, IntegerArrayType) or isinstance(rhs,
            IntegerArrayType):
            return bodo.libs.int_arr_ext.create_op_overload(op, 2)(lhs, rhs)
        if lhs == boolean_array or rhs == boolean_array:
            return bodo.libs.bool_arr_ext.create_op_overload(op, 2)(lhs, rhs)
        if op == operator.add and (is_str_arr_type(lhs) or types.unliteral(
            lhs) == string_type):
            return bodo.libs.str_arr_ext.overload_add_operator_string_array(lhs
                , rhs)
        if op == operator.add:
            return overload_add_operator_scalars(lhs, rhs)
        if op == operator.sub:
            return overload_sub_operator_scalars(lhs, rhs)
        if op == operator.mul:
            if mul_timedelta_and_int(lhs, rhs):
                return (bodo.hiframes.datetime_timedelta_ext.
                    overload_mul_operator_timedelta(lhs, rhs))
            if mul_string_arr_and_int(lhs, rhs):
                return bodo.libs.str_arr_ext.overload_mul_operator_str_arr(lhs,
                    rhs)
            if mul_date_offset_and_int(lhs, rhs):
                return (bodo.hiframes.pd_offsets_ext.
                    overload_mul_date_offset_types(lhs, rhs))
            raise_error_if_not_numba_supported(op, lhs, rhs)
        if op in [operator.truediv, operator.floordiv]:
            if div_timedelta_and_int(lhs, rhs):
                if op == operator.truediv:
                    return (bodo.hiframes.datetime_timedelta_ext.
                        overload_truediv_operator_pd_timedelta(lhs, rhs))
                else:
                    return (bodo.hiframes.datetime_timedelta_ext.
                        overload_floordiv_operator_pd_timedelta(lhs, rhs))
            if div_datetime_timedelta(lhs, rhs):
                if op == operator.truediv:
                    return (bodo.hiframes.datetime_timedelta_ext.
                        overload_truediv_operator_dt_timedelta(lhs, rhs))
                else:
                    return (bodo.hiframes.datetime_timedelta_ext.
                        overload_floordiv_operator_dt_timedelta(lhs, rhs))
            raise_error_if_not_numba_supported(op, lhs, rhs)
        if op == operator.mod:
            if mod_timedeltas(lhs, rhs):
                return (bodo.hiframes.datetime_timedelta_ext.
                    overload_mod_operator_timedeltas(lhs, rhs))
            raise_error_if_not_numba_supported(op, lhs, rhs)
        if op == operator.pow:
            raise_error_if_not_numba_supported(op, lhs, rhs)
        raise BodoError(
            f'{op} operator not supported for data types {lhs} and {rhs}.')
    return overload_arith_operator


def create_overload_cmp_operator(op):

    def overload_cmp_operator(lhs, rhs):
        if isinstance(lhs, DataFrameType) or isinstance(rhs, DataFrameType):
            bodo.hiframes.pd_timestamp_ext.check_tz_aware_unsupported(lhs,
                f'{op} operator')
            bodo.hiframes.pd_timestamp_ext.check_tz_aware_unsupported(rhs,
                f'{op} operator')
            return bodo.hiframes.dataframe_impl.create_binary_op_overload(op)(
                lhs, rhs)
        if cmp_timeseries(lhs, rhs):
            return bodo.hiframes.series_dt_impl.create_cmp_op_overload(op)(lhs,
                rhs)
        if isinstance(lhs, SeriesType) or isinstance(rhs, SeriesType):
            return
        bodo.hiframes.pd_timestamp_ext.check_tz_aware_unsupported(lhs,
            f'{op} operator')
        bodo.hiframes.pd_timestamp_ext.check_tz_aware_unsupported(rhs,
            f'{op} operator')
        if lhs == datetime_date_array_type or rhs == datetime_date_array_type:
            return bodo.hiframes.datetime_date_ext.create_cmp_op_overload_arr(
                op)(lhs, rhs)
        if (lhs == datetime_timedelta_array_type or rhs ==
            datetime_timedelta_array_type):
            bwx__pzja = (bodo.hiframes.datetime_timedelta_ext.
                create_cmp_op_overload(op))
            return bwx__pzja(lhs, rhs)
        if is_str_arr_type(lhs) or is_str_arr_type(rhs):
            return bodo.libs.str_arr_ext.create_binary_op_overload(op)(lhs, rhs
                )
        if isinstance(lhs, Decimal128Type) and isinstance(rhs, Decimal128Type):
            return bodo.libs.decimal_arr_ext.decimal_create_cmp_op_overload(op
                )(lhs, rhs)
        if lhs == boolean_array or rhs == boolean_array:
            return bodo.libs.bool_arr_ext.create_op_overload(op, 2)(lhs, rhs)
        if isinstance(lhs, IntegerArrayType) or isinstance(rhs,
            IntegerArrayType):
            return bodo.libs.int_arr_ext.create_op_overload(op, 2)(lhs, rhs)
        if binary_array_cmp(lhs, rhs):
            return bodo.libs.binary_arr_ext.create_binary_cmp_op_overload(op)(
                lhs, rhs)
        if cmp_dt_index_to_string(lhs, rhs):
            return bodo.hiframes.pd_index_ext.overload_binop_dti_str(op)(lhs,
                rhs)
        if operand_is_index(lhs) or operand_is_index(rhs):
            return bodo.hiframes.pd_index_ext.create_binary_op_overload(op)(lhs
                , rhs)
        if lhs == datetime_date_type and rhs == datetime_date_type:
            return bodo.hiframes.datetime_date_ext.create_cmp_op_overload(op)(
                lhs, rhs)
        if can_cmp_date_datetime(lhs, rhs, op):
            return (bodo.hiframes.datetime_date_ext.
                create_datetime_date_cmp_op_overload(op)(lhs, rhs))
        if lhs == datetime_datetime_type and rhs == datetime_datetime_type:
            return bodo.hiframes.datetime_datetime_ext.create_cmp_op_overload(
                op)(lhs, rhs)
        if lhs == datetime_timedelta_type and rhs == datetime_timedelta_type:
            return bodo.hiframes.datetime_timedelta_ext.create_cmp_op_overload(
                op)(lhs, rhs)
        if cmp_timedeltas(lhs, rhs):
            bwx__pzja = (bodo.hiframes.datetime_timedelta_ext.
                pd_create_cmp_op_overload(op))
            return bwx__pzja(lhs, rhs)
        if cmp_timestamp_or_date(lhs, rhs):
            return (bodo.hiframes.pd_timestamp_ext.
                create_timestamp_cmp_op_overload(op)(lhs, rhs))
        if cmp_op_supported_by_numba(lhs, rhs):
            return
        raise BodoError(
            f'{op} operator not supported for data types {lhs} and {rhs}.')
    return overload_cmp_operator


def add_dt_td_and_dt_date(lhs, rhs):
    ptddm__rqag = lhs == datetime_timedelta_type and rhs == datetime_date_type
    asqqq__qwlu = rhs == datetime_timedelta_type and lhs == datetime_date_type
    return ptddm__rqag or asqqq__qwlu


def add_timestamp(lhs, rhs):
    ajisn__snu = lhs == pd_timestamp_type and is_timedelta_type(rhs)
    jqf__ztuho = is_timedelta_type(lhs) and rhs == pd_timestamp_type
    return ajisn__snu or jqf__ztuho


def add_datetime_and_timedeltas(lhs, rhs):
    yvd__cibq = [datetime_timedelta_type, pd_timedelta_type]
    zvc__byif = [datetime_timedelta_type, pd_timedelta_type,
        datetime_datetime_type]
    xotn__jgoyk = lhs in yvd__cibq and rhs in yvd__cibq
    uaiwi__hxgvi = (lhs == datetime_datetime_type and rhs in yvd__cibq or 
        rhs == datetime_datetime_type and lhs in yvd__cibq)
    return xotn__jgoyk or uaiwi__hxgvi


def mul_string_arr_and_int(lhs, rhs):
    zzs__yns = isinstance(lhs, types.Integer) and is_str_arr_type(rhs)
    dne__uaxyp = is_str_arr_type(lhs) and isinstance(rhs, types.Integer)
    return zzs__yns or dne__uaxyp


def mul_timedelta_and_int(lhs, rhs):
    ptddm__rqag = lhs in [pd_timedelta_type, datetime_timedelta_type
        ] and isinstance(rhs, types.Integer)
    asqqq__qwlu = rhs in [pd_timedelta_type, datetime_timedelta_type
        ] and isinstance(lhs, types.Integer)
    return ptddm__rqag or asqqq__qwlu


def mul_date_offset_and_int(lhs, rhs):
    fymq__tqvip = lhs in [week_type, month_end_type, month_begin_type,
        date_offset_type] and isinstance(rhs, types.Integer)
    ynad__ash = rhs in [week_type, month_end_type, month_begin_type,
        date_offset_type] and isinstance(lhs, types.Integer)
    return fymq__tqvip or ynad__ash


def sub_offset_to_datetime_or_timestamp(lhs, rhs):
    pczzj__lhw = [datetime_datetime_type, pd_timestamp_type, datetime_date_type
        ]
    clie__sqt = [date_offset_type, month_begin_type, month_end_type, week_type]
    return rhs in clie__sqt and lhs in pczzj__lhw


def sub_dt_index_and_timestamp(lhs, rhs):
    lztfx__tlbe = isinstance(lhs, DatetimeIndexType
        ) and rhs == pd_timestamp_type
    zii__wjlxy = isinstance(rhs, DatetimeIndexType
        ) and lhs == pd_timestamp_type
    return lztfx__tlbe or zii__wjlxy


def sub_dt_or_td(lhs, rhs):
    zfeze__fakrw = lhs == datetime_date_type and rhs == datetime_timedelta_type
    gxes__wwg = lhs == datetime_date_type and rhs == datetime_date_type
    mxpbq__anh = (lhs == datetime_date_array_type and rhs ==
        datetime_timedelta_type)
    return zfeze__fakrw or gxes__wwg or mxpbq__anh


def sub_datetime_and_timedeltas(lhs, rhs):
    yes__smf = (is_timedelta_type(lhs) or lhs == datetime_datetime_type
        ) and is_timedelta_type(rhs)
    zzgn__lim = (lhs == datetime_timedelta_array_type and rhs ==
        datetime_timedelta_type)
    return yes__smf or zzgn__lim


def div_timedelta_and_int(lhs, rhs):
    xotn__jgoyk = lhs == pd_timedelta_type and rhs == pd_timedelta_type
    lwjc__hcn = lhs == pd_timedelta_type and isinstance(rhs, types.Integer)
    return xotn__jgoyk or lwjc__hcn


def div_datetime_timedelta(lhs, rhs):
    xotn__jgoyk = (lhs == datetime_timedelta_type and rhs ==
        datetime_timedelta_type)
    lwjc__hcn = lhs == datetime_timedelta_type and rhs == types.int64
    return xotn__jgoyk or lwjc__hcn


def mod_timedeltas(lhs, rhs):
    pjn__tgtqo = lhs == pd_timedelta_type and rhs == pd_timedelta_type
    adlcf__zbkg = (lhs == datetime_timedelta_type and rhs ==
        datetime_timedelta_type)
    return pjn__tgtqo or adlcf__zbkg


def cmp_dt_index_to_string(lhs, rhs):
    lztfx__tlbe = isinstance(lhs, DatetimeIndexType) and types.unliteral(rhs
        ) == string_type
    zii__wjlxy = isinstance(rhs, DatetimeIndexType) and types.unliteral(lhs
        ) == string_type
    return lztfx__tlbe or zii__wjlxy


def cmp_timestamp_or_date(lhs, rhs):
    gci__nmpl = (lhs == pd_timestamp_type and rhs == bodo.hiframes.
        datetime_date_ext.datetime_date_type)
    eiqcq__neran = (lhs == bodo.hiframes.datetime_date_ext.
        datetime_date_type and rhs == pd_timestamp_type)
    vfehw__oapdh = lhs == pd_timestamp_type and rhs == pd_timestamp_type
    wpfr__bzkl = lhs == pd_timestamp_type and rhs == bodo.datetime64ns
    vph__nddol = rhs == pd_timestamp_type and lhs == bodo.datetime64ns
    return (gci__nmpl or eiqcq__neran or vfehw__oapdh or wpfr__bzkl or
        vph__nddol)


def cmp_timeseries(lhs, rhs):
    moi__mwiqa = bodo.hiframes.pd_series_ext.is_dt64_series_typ(rhs) and (bodo
        .utils.typing.is_overload_constant_str(lhs) or lhs == bodo.libs.
        str_ext.string_type or lhs == bodo.hiframes.pd_timestamp_ext.
        pd_timestamp_type)
    enl__hhy = bodo.hiframes.pd_series_ext.is_dt64_series_typ(lhs) and (bodo
        .utils.typing.is_overload_constant_str(rhs) or rhs == bodo.libs.
        str_ext.string_type or rhs == bodo.hiframes.pd_timestamp_ext.
        pd_timestamp_type)
    iykt__sqza = moi__mwiqa or enl__hhy
    mzdxi__zwvbp = bodo.hiframes.pd_series_ext.is_timedelta64_series_typ(rhs
        ) and lhs == bodo.hiframes.datetime_timedelta_ext.datetime_timedelta_type
    plsx__kaoqd = bodo.hiframes.pd_series_ext.is_timedelta64_series_typ(lhs
        ) and rhs == bodo.hiframes.datetime_timedelta_ext.datetime_timedelta_type
    ekylc__kzrhf = mzdxi__zwvbp or plsx__kaoqd
    return iykt__sqza or ekylc__kzrhf


def cmp_timedeltas(lhs, rhs):
    xotn__jgoyk = [pd_timedelta_type, bodo.timedelta64ns]
    return lhs in xotn__jgoyk and rhs in xotn__jgoyk


def operand_is_index(operand):
    return is_index_type(operand) or isinstance(operand, HeterogeneousIndexType
        )


def helper_time_series_checks(operand):
    nau__jomn = bodo.hiframes.pd_series_ext.is_dt64_series_typ(operand
        ) or bodo.hiframes.pd_series_ext.is_timedelta64_series_typ(operand
        ) or operand in [datetime_timedelta_type, datetime_datetime_type,
        pd_timestamp_type]
    return nau__jomn


def binary_array_cmp(lhs, rhs):
    return lhs == binary_array_type and rhs in [bytes_type, binary_array_type
        ] or lhs in [bytes_type, binary_array_type
        ] and rhs == binary_array_type


def can_cmp_date_datetime(lhs, rhs, op):
    return op in (operator.eq, operator.ne) and (lhs == datetime_date_type and
        rhs == datetime_datetime_type or lhs == datetime_datetime_type and 
        rhs == datetime_date_type)


def time_series_operation(lhs, rhs):
    vamb__lodc = bodo.hiframes.pd_series_ext.is_timedelta64_series_typ(lhs
        ) and rhs == datetime_timedelta_type
    qrxnb__sag = bodo.hiframes.pd_series_ext.is_timedelta64_series_typ(rhs
        ) and lhs == datetime_timedelta_type
    csnvj__xsxw = bodo.hiframes.pd_series_ext.is_dt64_series_typ(lhs
        ) and helper_time_series_checks(rhs)
    ttl__gepfq = bodo.hiframes.pd_series_ext.is_dt64_series_typ(rhs
        ) and helper_time_series_checks(lhs)
    return vamb__lodc or qrxnb__sag or csnvj__xsxw or ttl__gepfq


def args_td_and_int_array(lhs, rhs):
    ora__cnw = (isinstance(lhs, IntegerArrayType) or isinstance(lhs, types.
        Array) and isinstance(lhs.dtype, types.Integer)) or (isinstance(rhs,
        IntegerArrayType) or isinstance(rhs, types.Array) and isinstance(
        rhs.dtype, types.Integer))
    balw__ebju = lhs in [pd_timedelta_type] or rhs in [pd_timedelta_type]
    return ora__cnw and balw__ebju


def arith_op_supported_by_numba(op, lhs, rhs):
    if op == operator.mul:
        asqqq__qwlu = isinstance(lhs, (types.Integer, types.Float)
            ) and isinstance(rhs, types.NPTimedelta)
        ptddm__rqag = isinstance(rhs, (types.Integer, types.Float)
            ) and isinstance(lhs, types.NPTimedelta)
        crfgg__yorl = asqqq__qwlu or ptddm__rqag
        uiqry__zfwf = isinstance(rhs, types.UnicodeType) and isinstance(lhs,
            types.Integer)
        naxu__mewb = isinstance(lhs, types.UnicodeType) and isinstance(rhs,
            types.Integer)
        aax__fcu = uiqry__zfwf or naxu__mewb
        vqa__lypgl = isinstance(lhs, types.Integer) and isinstance(rhs,
            types.Integer)
        tgs__mord = isinstance(lhs, types.Float) and isinstance(rhs, types.
            Float)
        pkluc__lhe = isinstance(lhs, types.Complex) and isinstance(rhs,
            types.Complex)
        uubat__nmo = vqa__lypgl or tgs__mord or pkluc__lhe
        ktt__unm = isinstance(lhs, types.List) and isinstance(rhs, types.
            Integer) or isinstance(lhs, types.Integer) and isinstance(rhs,
            types.List)
        tys = types.UnicodeCharSeq, types.CharSeq, types.Bytes
        zztu__pubdx = isinstance(lhs, tys) or isinstance(rhs, tys)
        kvcc__oupq = isinstance(lhs, types.Array) or isinstance(rhs, types.
            Array)
        return (crfgg__yorl or aax__fcu or uubat__nmo or ktt__unm or
            zztu__pubdx or kvcc__oupq)
    if op == operator.pow:
        ifd__hxr = isinstance(lhs, types.Integer) and isinstance(rhs, (
            types.IntegerLiteral, types.Integer))
        ajaf__topo = isinstance(lhs, types.Float) and isinstance(rhs, (
            types.IntegerLiteral, types.Float, types.Integer) or rhs in
            types.unsigned_domain or rhs in types.signed_domain)
        pkluc__lhe = isinstance(lhs, types.Complex) and isinstance(rhs,
            types.Complex)
        kvcc__oupq = isinstance(lhs, types.Array) or isinstance(rhs, types.
            Array)
        return ifd__hxr or ajaf__topo or pkluc__lhe or kvcc__oupq
    if op == operator.floordiv:
        tgs__mord = lhs in types.real_domain and rhs in types.real_domain
        vqa__lypgl = isinstance(lhs, types.Integer) and isinstance(rhs,
            types.Integer)
        wfj__shr = isinstance(lhs, types.Float) and isinstance(rhs, types.Float
            )
        xotn__jgoyk = isinstance(lhs, types.NPTimedelta) and isinstance(rhs,
            (types.Integer, types.Float, types.NPTimedelta))
        kvcc__oupq = isinstance(lhs, types.Array) or isinstance(rhs, types.
            Array)
        return tgs__mord or vqa__lypgl or wfj__shr or xotn__jgoyk or kvcc__oupq
    if op == operator.truediv:
        hvoqc__trw = lhs in machine_ints and rhs in machine_ints
        tgs__mord = lhs in types.real_domain and rhs in types.real_domain
        pkluc__lhe = (lhs in types.complex_domain and rhs in types.
            complex_domain)
        vqa__lypgl = isinstance(lhs, types.Integer) and isinstance(rhs,
            types.Integer)
        wfj__shr = isinstance(lhs, types.Float) and isinstance(rhs, types.Float
            )
        uucb__gtm = isinstance(lhs, types.Complex) and isinstance(rhs,
            types.Complex)
        xotn__jgoyk = isinstance(lhs, types.NPTimedelta) and isinstance(rhs,
            (types.Integer, types.Float, types.NPTimedelta))
        kvcc__oupq = isinstance(lhs, types.Array) or isinstance(rhs, types.
            Array)
        return (hvoqc__trw or tgs__mord or pkluc__lhe or vqa__lypgl or
            wfj__shr or uucb__gtm or xotn__jgoyk or kvcc__oupq)
    if op == operator.mod:
        hvoqc__trw = lhs in machine_ints and rhs in machine_ints
        tgs__mord = lhs in types.real_domain and rhs in types.real_domain
        vqa__lypgl = isinstance(lhs, types.Integer) and isinstance(rhs,
            types.Integer)
        wfj__shr = isinstance(lhs, types.Float) and isinstance(rhs, types.Float
            )
        kvcc__oupq = isinstance(lhs, types.Array) or isinstance(rhs, types.
            Array)
        return hvoqc__trw or tgs__mord or vqa__lypgl or wfj__shr or kvcc__oupq
    if op == operator.add or op == operator.sub:
        crfgg__yorl = isinstance(lhs, types.NPTimedelta) and isinstance(rhs,
            types.NPTimedelta)
        zdqc__efsb = isinstance(lhs, types.NPDatetime) and isinstance(rhs,
            types.NPDatetime)
        seox__yml = isinstance(lhs, types.NPDatetime) and isinstance(rhs,
            types.NPTimedelta)
        sun__dmsf = isinstance(lhs, types.Set) and isinstance(rhs, types.Set)
        vqa__lypgl = isinstance(lhs, types.Integer) and isinstance(rhs,
            types.Integer)
        tgs__mord = isinstance(lhs, types.Float) and isinstance(rhs, types.
            Float)
        pkluc__lhe = isinstance(lhs, types.Complex) and isinstance(rhs,
            types.Complex)
        uubat__nmo = vqa__lypgl or tgs__mord or pkluc__lhe
        kvcc__oupq = isinstance(lhs, types.Array) or isinstance(rhs, types.
            Array)
        acbny__oid = isinstance(lhs, types.BaseTuple) and isinstance(rhs,
            types.BaseTuple)
        ktt__unm = isinstance(lhs, types.List) and isinstance(rhs, types.List)
        bthpi__fjjzi = isinstance(lhs, types.UnicodeCharSeq) and isinstance(rhs
            , types.UnicodeType)
        pwfis__brt = isinstance(rhs, types.UnicodeCharSeq) and isinstance(lhs,
            types.UnicodeType)
        sabut__gsh = isinstance(lhs, types.UnicodeCharSeq) and isinstance(rhs,
            types.UnicodeCharSeq)
        ctab__yyew = isinstance(lhs, (types.CharSeq, types.Bytes)
            ) and isinstance(rhs, (types.CharSeq, types.Bytes))
        qicgd__txu = bthpi__fjjzi or pwfis__brt or sabut__gsh or ctab__yyew
        aax__fcu = isinstance(lhs, types.UnicodeType) and isinstance(rhs,
            types.UnicodeType)
        qzsiz__wth = isinstance(lhs, types.UnicodeType) and isinstance(rhs,
            types.UnicodeCharSeq)
        kivj__cyn = aax__fcu or qzsiz__wth
        bjis__zmj = lhs == types.NPTimedelta and rhs == types.NPDatetime
        ktgcu__jre = (acbny__oid or ktt__unm or qicgd__txu or kivj__cyn or
            bjis__zmj)
        ykcbf__lsxlh = op == operator.add and ktgcu__jre
        return (crfgg__yorl or zdqc__efsb or seox__yml or sun__dmsf or
            uubat__nmo or kvcc__oupq or ykcbf__lsxlh)


def cmp_op_supported_by_numba(lhs, rhs):
    kvcc__oupq = isinstance(lhs, types.Array) or isinstance(rhs, types.Array)
    ktt__unm = isinstance(lhs, types.ListType) and isinstance(rhs, types.
        ListType)
    crfgg__yorl = isinstance(lhs, types.NPTimedelta) and isinstance(rhs,
        types.NPTimedelta)
    lfzpw__fzxdy = isinstance(lhs, types.NPDatetime) and isinstance(rhs,
        types.NPDatetime)
    unicode_types = (types.UnicodeType, types.StringLiteral, types.CharSeq,
        types.Bytes, types.UnicodeCharSeq)
    aax__fcu = isinstance(lhs, unicode_types) and isinstance(rhs, unicode_types
        )
    acbny__oid = isinstance(lhs, types.BaseTuple) and isinstance(rhs, types
        .BaseTuple)
    sun__dmsf = isinstance(lhs, types.Set) and isinstance(rhs, types.Set)
    uubat__nmo = isinstance(lhs, types.Number) and isinstance(rhs, types.Number
        )
    ybet__hxpam = isinstance(lhs, types.Boolean) and isinstance(rhs, types.
        Boolean)
    zsux__nxpy = isinstance(lhs, types.NoneType) or isinstance(rhs, types.
        NoneType)
    ywwmf__mcgw = isinstance(lhs, types.DictType) and isinstance(rhs, types
        .DictType)
    jncb__tfg = isinstance(lhs, types.EnumMember) and isinstance(rhs, types
        .EnumMember)
    hun__rhqu = isinstance(lhs, types.Literal) and isinstance(rhs, types.
        Literal)
    return (ktt__unm or crfgg__yorl or lfzpw__fzxdy or aax__fcu or
        acbny__oid or sun__dmsf or uubat__nmo or ybet__hxpam or zsux__nxpy or
        ywwmf__mcgw or kvcc__oupq or jncb__tfg or hun__rhqu)


def raise_error_if_not_numba_supported(op, lhs, rhs):
    if arith_op_supported_by_numba(op, lhs, rhs):
        return
    raise BodoError(
        f'{op} operator not supported for data types {lhs} and {rhs}.')


def _install_series_and_or():
    for op in (operator.or_, operator.and_):
        infer_global(op)(SeriesAndOrTyper)
        lower_impl = lower_series_and_or(op)
        lower_builtin(op, SeriesType, SeriesType)(lower_impl)
        lower_builtin(op, SeriesType, types.Any)(lower_impl)
        lower_builtin(op, types.Any, SeriesType)(lower_impl)


_install_series_and_or()


def _install_cmp_ops():
    for op in (operator.lt, operator.eq, operator.ne, operator.ge, operator
        .gt, operator.le):
        infer_global(op)(SeriesCmpOpTemplate)
        lower_impl = series_cmp_op_lower(op)
        lower_builtin(op, SeriesType, SeriesType)(lower_impl)
        lower_builtin(op, SeriesType, types.Any)(lower_impl)
        lower_builtin(op, types.Any, SeriesType)(lower_impl)
        cskla__bmu = create_overload_cmp_operator(op)
        overload(op, no_unliteral=True)(cskla__bmu)


_install_cmp_ops()


def install_arith_ops():
    for op in (operator.add, operator.sub, operator.mul, operator.truediv,
        operator.floordiv, operator.mod, operator.pow):
        cskla__bmu = create_overload_arith_op(op)
        overload(op, no_unliteral=True)(cskla__bmu)


install_arith_ops()
