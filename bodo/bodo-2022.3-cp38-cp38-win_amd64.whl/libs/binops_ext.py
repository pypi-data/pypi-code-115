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
        ykf__osit = lhs.data if isinstance(lhs, SeriesType) else lhs
        ajdl__smbf = rhs.data if isinstance(rhs, SeriesType) else rhs
        if ykf__osit in (bodo.pd_timestamp_type, bodo.pd_timedelta_type
            ) and ajdl__smbf.dtype in (bodo.datetime64ns, bodo.timedelta64ns):
            ykf__osit = ajdl__smbf.dtype
        elif ajdl__smbf in (bodo.pd_timestamp_type, bodo.pd_timedelta_type
            ) and ykf__osit.dtype in (bodo.datetime64ns, bodo.timedelta64ns):
            ajdl__smbf = ykf__osit.dtype
        ljpc__tjfzm = ykf__osit, ajdl__smbf
        qdauw__lpbsw = (
            f'{lhs} {numba.core.utils.OPERATORS_TO_BUILTINS[self.key]} {rhs} not supported'
            )
        try:
            gip__pejk = self.context.resolve_function_type(self.key,
                ljpc__tjfzm, {}).return_type
        except Exception as aum__wncr:
            raise BodoError(qdauw__lpbsw)
        if is_overload_bool(gip__pejk):
            raise BodoError(qdauw__lpbsw)
        agxm__sbzpg = lhs.index if isinstance(lhs, SeriesType) else rhs.index
        eafy__sfh = lhs.name_typ if isinstance(lhs, SeriesType
            ) else rhs.name_typ
        pbg__iwhf = types.bool_
        gwdl__hmav = SeriesType(pbg__iwhf, gip__pejk, agxm__sbzpg, eafy__sfh)
        return gwdl__hmav(*args)


def series_cmp_op_lower(op):

    def lower_impl(context, builder, sig, args):
        aus__mjmul = bodo.hiframes.series_impl.create_binary_op_overload(op)(*
            sig.args)
        if aus__mjmul is None:
            aus__mjmul = create_overload_cmp_operator(op)(*sig.args)
        return context.compile_internal(builder, aus__mjmul, sig, args)
    return lower_impl


class SeriesAndOrTyper(AbstractTemplate):

    def generic(self, args, kws):
        assert len(args) == 2
        assert not kws
        lhs, rhs = args
        if not (isinstance(lhs, SeriesType) or isinstance(rhs, SeriesType)):
            return
        ykf__osit = lhs.data if isinstance(lhs, SeriesType) else lhs
        ajdl__smbf = rhs.data if isinstance(rhs, SeriesType) else rhs
        ljpc__tjfzm = ykf__osit, ajdl__smbf
        qdauw__lpbsw = (
            f'{lhs} {numba.core.utils.OPERATORS_TO_BUILTINS[self.key]} {rhs} not supported'
            )
        try:
            gip__pejk = self.context.resolve_function_type(self.key,
                ljpc__tjfzm, {}).return_type
        except Exception as dbhxe__aqgp:
            raise BodoError(qdauw__lpbsw)
        agxm__sbzpg = lhs.index if isinstance(lhs, SeriesType) else rhs.index
        eafy__sfh = lhs.name_typ if isinstance(lhs, SeriesType
            ) else rhs.name_typ
        pbg__iwhf = gip__pejk.dtype
        gwdl__hmav = SeriesType(pbg__iwhf, gip__pejk, agxm__sbzpg, eafy__sfh)
        return gwdl__hmav(*args)


def lower_series_and_or(op):

    def lower_and_or_impl(context, builder, sig, args):
        aus__mjmul = bodo.hiframes.series_impl.create_binary_op_overload(op)(*
            sig.args)
        if aus__mjmul is None:
            lhs, rhs = sig.args
            if isinstance(lhs, DataFrameType) or isinstance(rhs, DataFrameType
                ):
                aus__mjmul = (bodo.hiframes.dataframe_impl.
                    create_binary_op_overload(op)(*sig.args))
        return context.compile_internal(builder, aus__mjmul, sig, args)
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
            aus__mjmul = (bodo.hiframes.datetime_timedelta_ext.
                create_cmp_op_overload(op))
            return aus__mjmul(lhs, rhs)
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
            aus__mjmul = (bodo.hiframes.datetime_timedelta_ext.
                pd_create_cmp_op_overload(op))
            return aus__mjmul(lhs, rhs)
        if cmp_timestamp_or_date(lhs, rhs):
            return (bodo.hiframes.pd_timestamp_ext.
                create_timestamp_cmp_op_overload(op)(lhs, rhs))
        if cmp_op_supported_by_numba(lhs, rhs):
            return
        raise BodoError(
            f'{op} operator not supported for data types {lhs} and {rhs}.')
    return overload_cmp_operator


def add_dt_td_and_dt_date(lhs, rhs):
    rtju__zgj = lhs == datetime_timedelta_type and rhs == datetime_date_type
    jtfa__lgyx = rhs == datetime_timedelta_type and lhs == datetime_date_type
    return rtju__zgj or jtfa__lgyx


def add_timestamp(lhs, rhs):
    xvjf__hib = lhs == pd_timestamp_type and is_timedelta_type(rhs)
    rqm__jmk = is_timedelta_type(lhs) and rhs == pd_timestamp_type
    return xvjf__hib or rqm__jmk


def add_datetime_and_timedeltas(lhs, rhs):
    kpcps__wei = [datetime_timedelta_type, pd_timedelta_type]
    hep__xqo = [datetime_timedelta_type, pd_timedelta_type,
        datetime_datetime_type]
    coaex__svbuh = lhs in kpcps__wei and rhs in kpcps__wei
    htia__ossv = (lhs == datetime_datetime_type and rhs in kpcps__wei or 
        rhs == datetime_datetime_type and lhs in kpcps__wei)
    return coaex__svbuh or htia__ossv


def mul_string_arr_and_int(lhs, rhs):
    ajdl__smbf = isinstance(lhs, types.Integer) and is_str_arr_type(rhs)
    ykf__osit = is_str_arr_type(lhs) and isinstance(rhs, types.Integer)
    return ajdl__smbf or ykf__osit


def mul_timedelta_and_int(lhs, rhs):
    rtju__zgj = lhs in [pd_timedelta_type, datetime_timedelta_type
        ] and isinstance(rhs, types.Integer)
    jtfa__lgyx = rhs in [pd_timedelta_type, datetime_timedelta_type
        ] and isinstance(lhs, types.Integer)
    return rtju__zgj or jtfa__lgyx


def mul_date_offset_and_int(lhs, rhs):
    eukn__ynw = lhs in [week_type, month_end_type, month_begin_type,
        date_offset_type] and isinstance(rhs, types.Integer)
    zlgf__ujias = rhs in [week_type, month_end_type, month_begin_type,
        date_offset_type] and isinstance(lhs, types.Integer)
    return eukn__ynw or zlgf__ujias


def sub_offset_to_datetime_or_timestamp(lhs, rhs):
    oiq__ddvco = [datetime_datetime_type, pd_timestamp_type, datetime_date_type
        ]
    iauc__ydekq = [date_offset_type, month_begin_type, month_end_type,
        week_type]
    return rhs in iauc__ydekq and lhs in oiq__ddvco


def sub_dt_index_and_timestamp(lhs, rhs):
    pwxqz__ybwp = isinstance(lhs, DatetimeIndexType
        ) and rhs == pd_timestamp_type
    xsm__fpqzn = isinstance(rhs, DatetimeIndexType
        ) and lhs == pd_timestamp_type
    return pwxqz__ybwp or xsm__fpqzn


def sub_dt_or_td(lhs, rhs):
    kitxy__ffat = lhs == datetime_date_type and rhs == datetime_timedelta_type
    fbg__kjt = lhs == datetime_date_type and rhs == datetime_date_type
    mjy__jttzb = (lhs == datetime_date_array_type and rhs ==
        datetime_timedelta_type)
    return kitxy__ffat or fbg__kjt or mjy__jttzb


def sub_datetime_and_timedeltas(lhs, rhs):
    oohvg__lje = (is_timedelta_type(lhs) or lhs == datetime_datetime_type
        ) and is_timedelta_type(rhs)
    ovmk__bjj = (lhs == datetime_timedelta_array_type and rhs ==
        datetime_timedelta_type)
    return oohvg__lje or ovmk__bjj


def div_timedelta_and_int(lhs, rhs):
    coaex__svbuh = lhs == pd_timedelta_type and rhs == pd_timedelta_type
    omzx__mblg = lhs == pd_timedelta_type and isinstance(rhs, types.Integer)
    return coaex__svbuh or omzx__mblg


def div_datetime_timedelta(lhs, rhs):
    coaex__svbuh = (lhs == datetime_timedelta_type and rhs ==
        datetime_timedelta_type)
    omzx__mblg = lhs == datetime_timedelta_type and rhs == types.int64
    return coaex__svbuh or omzx__mblg


def mod_timedeltas(lhs, rhs):
    cqd__npu = lhs == pd_timedelta_type and rhs == pd_timedelta_type
    dxml__mdu = (lhs == datetime_timedelta_type and rhs ==
        datetime_timedelta_type)
    return cqd__npu or dxml__mdu


def cmp_dt_index_to_string(lhs, rhs):
    pwxqz__ybwp = isinstance(lhs, DatetimeIndexType) and types.unliteral(rhs
        ) == string_type
    xsm__fpqzn = isinstance(rhs, DatetimeIndexType) and types.unliteral(lhs
        ) == string_type
    return pwxqz__ybwp or xsm__fpqzn


def cmp_timestamp_or_date(lhs, rhs):
    lbif__lwutl = (lhs == pd_timestamp_type and rhs == bodo.hiframes.
        datetime_date_ext.datetime_date_type)
    qqi__wjfyp = (lhs == bodo.hiframes.datetime_date_ext.datetime_date_type and
        rhs == pd_timestamp_type)
    fdc__zeme = lhs == pd_timestamp_type and rhs == pd_timestamp_type
    dogqo__slkij = lhs == pd_timestamp_type and rhs == bodo.datetime64ns
    wle__nddv = rhs == pd_timestamp_type and lhs == bodo.datetime64ns
    return lbif__lwutl or qqi__wjfyp or fdc__zeme or dogqo__slkij or wle__nddv


def cmp_timeseries(lhs, rhs):
    nvh__gwxog = bodo.hiframes.pd_series_ext.is_dt64_series_typ(rhs) and (bodo
        .utils.typing.is_overload_constant_str(lhs) or lhs == bodo.libs.
        str_ext.string_type or lhs == bodo.hiframes.pd_timestamp_ext.
        pd_timestamp_type)
    utg__amlm = bodo.hiframes.pd_series_ext.is_dt64_series_typ(lhs) and (bodo
        .utils.typing.is_overload_constant_str(rhs) or rhs == bodo.libs.
        str_ext.string_type or rhs == bodo.hiframes.pd_timestamp_ext.
        pd_timestamp_type)
    hib__njhya = nvh__gwxog or utg__amlm
    gsqxe__lwfmm = bodo.hiframes.pd_series_ext.is_timedelta64_series_typ(rhs
        ) and lhs == bodo.hiframes.datetime_timedelta_ext.datetime_timedelta_type
    xmwv__jzh = bodo.hiframes.pd_series_ext.is_timedelta64_series_typ(lhs
        ) and rhs == bodo.hiframes.datetime_timedelta_ext.datetime_timedelta_type
    ntzdq__shkz = gsqxe__lwfmm or xmwv__jzh
    return hib__njhya or ntzdq__shkz


def cmp_timedeltas(lhs, rhs):
    coaex__svbuh = [pd_timedelta_type, bodo.timedelta64ns]
    return lhs in coaex__svbuh and rhs in coaex__svbuh


def operand_is_index(operand):
    return is_index_type(operand) or isinstance(operand, HeterogeneousIndexType
        )


def helper_time_series_checks(operand):
    qxbmq__owe = bodo.hiframes.pd_series_ext.is_dt64_series_typ(operand
        ) or bodo.hiframes.pd_series_ext.is_timedelta64_series_typ(operand
        ) or operand in [datetime_timedelta_type, datetime_datetime_type,
        pd_timestamp_type]
    return qxbmq__owe


def binary_array_cmp(lhs, rhs):
    return lhs == binary_array_type and rhs in [bytes_type, binary_array_type
        ] or lhs in [bytes_type, binary_array_type
        ] and rhs == binary_array_type


def can_cmp_date_datetime(lhs, rhs, op):
    return op in (operator.eq, operator.ne) and (lhs == datetime_date_type and
        rhs == datetime_datetime_type or lhs == datetime_datetime_type and 
        rhs == datetime_date_type)


def time_series_operation(lhs, rhs):
    rreq__fna = bodo.hiframes.pd_series_ext.is_timedelta64_series_typ(lhs
        ) and rhs == datetime_timedelta_type
    apmg__erlh = bodo.hiframes.pd_series_ext.is_timedelta64_series_typ(rhs
        ) and lhs == datetime_timedelta_type
    zzeoe__kfqz = bodo.hiframes.pd_series_ext.is_dt64_series_typ(lhs
        ) and helper_time_series_checks(rhs)
    ukjl__bndtc = bodo.hiframes.pd_series_ext.is_dt64_series_typ(rhs
        ) and helper_time_series_checks(lhs)
    return rreq__fna or apmg__erlh or zzeoe__kfqz or ukjl__bndtc


def args_td_and_int_array(lhs, rhs):
    xubfq__kjyry = (isinstance(lhs, IntegerArrayType) or isinstance(lhs,
        types.Array) and isinstance(lhs.dtype, types.Integer)) or (isinstance
        (rhs, IntegerArrayType) or isinstance(rhs, types.Array) and
        isinstance(rhs.dtype, types.Integer))
    dms__xtk = lhs in [pd_timedelta_type] or rhs in [pd_timedelta_type]
    return xubfq__kjyry and dms__xtk


def arith_op_supported_by_numba(op, lhs, rhs):
    if op == operator.mul:
        jtfa__lgyx = isinstance(lhs, (types.Integer, types.Float)
            ) and isinstance(rhs, types.NPTimedelta)
        rtju__zgj = isinstance(rhs, (types.Integer, types.Float)
            ) and isinstance(lhs, types.NPTimedelta)
        thsj__xxthf = jtfa__lgyx or rtju__zgj
        bfhck__hdo = isinstance(rhs, types.UnicodeType) and isinstance(lhs,
            types.Integer)
        pzncg__eht = isinstance(lhs, types.UnicodeType) and isinstance(rhs,
            types.Integer)
        qpl__fgc = bfhck__hdo or pzncg__eht
        qnid__fubv = isinstance(lhs, types.Integer) and isinstance(rhs,
            types.Integer)
        hzvog__bkl = isinstance(lhs, types.Float) and isinstance(rhs, types
            .Float)
        mhq__vgmu = isinstance(lhs, types.Complex) and isinstance(rhs,
            types.Complex)
        sds__vjgvh = qnid__fubv or hzvog__bkl or mhq__vgmu
        eno__pukl = isinstance(lhs, types.List) and isinstance(rhs, types.
            Integer) or isinstance(lhs, types.Integer) and isinstance(rhs,
            types.List)
        tys = types.UnicodeCharSeq, types.CharSeq, types.Bytes
        tcgv__acfg = isinstance(lhs, tys) or isinstance(rhs, tys)
        ryat__miu = isinstance(lhs, types.Array) or isinstance(rhs, types.Array
            )
        return (thsj__xxthf or qpl__fgc or sds__vjgvh or eno__pukl or
            tcgv__acfg or ryat__miu)
    if op == operator.pow:
        kkzy__smszm = isinstance(lhs, types.Integer) and isinstance(rhs, (
            types.IntegerLiteral, types.Integer))
        cywq__tmubf = isinstance(lhs, types.Float) and isinstance(rhs, (
            types.IntegerLiteral, types.Float, types.Integer) or rhs in
            types.unsigned_domain or rhs in types.signed_domain)
        mhq__vgmu = isinstance(lhs, types.Complex) and isinstance(rhs,
            types.Complex)
        ryat__miu = isinstance(lhs, types.Array) or isinstance(rhs, types.Array
            )
        return kkzy__smszm or cywq__tmubf or mhq__vgmu or ryat__miu
    if op == operator.floordiv:
        hzvog__bkl = lhs in types.real_domain and rhs in types.real_domain
        qnid__fubv = isinstance(lhs, types.Integer) and isinstance(rhs,
            types.Integer)
        hkhdw__fwy = isinstance(lhs, types.Float) and isinstance(rhs, types
            .Float)
        coaex__svbuh = isinstance(lhs, types.NPTimedelta) and isinstance(rhs,
            (types.Integer, types.Float, types.NPTimedelta))
        ryat__miu = isinstance(lhs, types.Array) or isinstance(rhs, types.Array
            )
        return (hzvog__bkl or qnid__fubv or hkhdw__fwy or coaex__svbuh or
            ryat__miu)
    if op == operator.truediv:
        bbjqt__nde = lhs in machine_ints and rhs in machine_ints
        hzvog__bkl = lhs in types.real_domain and rhs in types.real_domain
        mhq__vgmu = lhs in types.complex_domain and rhs in types.complex_domain
        qnid__fubv = isinstance(lhs, types.Integer) and isinstance(rhs,
            types.Integer)
        hkhdw__fwy = isinstance(lhs, types.Float) and isinstance(rhs, types
            .Float)
        fcrcl__okxa = isinstance(lhs, types.Complex) and isinstance(rhs,
            types.Complex)
        coaex__svbuh = isinstance(lhs, types.NPTimedelta) and isinstance(rhs,
            (types.Integer, types.Float, types.NPTimedelta))
        ryat__miu = isinstance(lhs, types.Array) or isinstance(rhs, types.Array
            )
        return (bbjqt__nde or hzvog__bkl or mhq__vgmu or qnid__fubv or
            hkhdw__fwy or fcrcl__okxa or coaex__svbuh or ryat__miu)
    if op == operator.mod:
        bbjqt__nde = lhs in machine_ints and rhs in machine_ints
        hzvog__bkl = lhs in types.real_domain and rhs in types.real_domain
        qnid__fubv = isinstance(lhs, types.Integer) and isinstance(rhs,
            types.Integer)
        hkhdw__fwy = isinstance(lhs, types.Float) and isinstance(rhs, types
            .Float)
        ryat__miu = isinstance(lhs, types.Array) or isinstance(rhs, types.Array
            )
        return (bbjqt__nde or hzvog__bkl or qnid__fubv or hkhdw__fwy or
            ryat__miu)
    if op == operator.add or op == operator.sub:
        thsj__xxthf = isinstance(lhs, types.NPTimedelta) and isinstance(rhs,
            types.NPTimedelta)
        mzlw__dapzt = isinstance(lhs, types.NPDatetime) and isinstance(rhs,
            types.NPDatetime)
        igvir__vwbho = isinstance(lhs, types.NPDatetime) and isinstance(rhs,
            types.NPTimedelta)
        qgal__zicbv = isinstance(lhs, types.Set) and isinstance(rhs, types.Set)
        qnid__fubv = isinstance(lhs, types.Integer) and isinstance(rhs,
            types.Integer)
        hzvog__bkl = isinstance(lhs, types.Float) and isinstance(rhs, types
            .Float)
        mhq__vgmu = isinstance(lhs, types.Complex) and isinstance(rhs,
            types.Complex)
        sds__vjgvh = qnid__fubv or hzvog__bkl or mhq__vgmu
        ryat__miu = isinstance(lhs, types.Array) or isinstance(rhs, types.Array
            )
        rpcuq__japa = isinstance(lhs, types.BaseTuple) and isinstance(rhs,
            types.BaseTuple)
        eno__pukl = isinstance(lhs, types.List) and isinstance(rhs, types.List)
        aew__gwtx = isinstance(lhs, types.UnicodeCharSeq) and isinstance(rhs,
            types.UnicodeType)
        wlmut__euxu = isinstance(rhs, types.UnicodeCharSeq) and isinstance(lhs,
            types.UnicodeType)
        njhia__nrzxa = isinstance(lhs, types.UnicodeCharSeq) and isinstance(rhs
            , types.UnicodeCharSeq)
        gqz__kzsk = isinstance(lhs, (types.CharSeq, types.Bytes)
            ) and isinstance(rhs, (types.CharSeq, types.Bytes))
        wapm__ndn = aew__gwtx or wlmut__euxu or njhia__nrzxa or gqz__kzsk
        qpl__fgc = isinstance(lhs, types.UnicodeType) and isinstance(rhs,
            types.UnicodeType)
        nksrw__joidb = isinstance(lhs, types.UnicodeType) and isinstance(rhs,
            types.UnicodeCharSeq)
        fmqw__umuy = qpl__fgc or nksrw__joidb
        clzfm__wlwsa = lhs == types.NPTimedelta and rhs == types.NPDatetime
        lrc__pkuu = (rpcuq__japa or eno__pukl or wapm__ndn or fmqw__umuy or
            clzfm__wlwsa)
        otreh__skvbc = op == operator.add and lrc__pkuu
        return (thsj__xxthf or mzlw__dapzt or igvir__vwbho or qgal__zicbv or
            sds__vjgvh or ryat__miu or otreh__skvbc)


def cmp_op_supported_by_numba(lhs, rhs):
    ryat__miu = isinstance(lhs, types.Array) or isinstance(rhs, types.Array)
    eno__pukl = isinstance(lhs, types.ListType) and isinstance(rhs, types.
        ListType)
    thsj__xxthf = isinstance(lhs, types.NPTimedelta) and isinstance(rhs,
        types.NPTimedelta)
    svmox__nhupj = isinstance(lhs, types.NPDatetime) and isinstance(rhs,
        types.NPDatetime)
    unicode_types = (types.UnicodeType, types.StringLiteral, types.CharSeq,
        types.Bytes, types.UnicodeCharSeq)
    qpl__fgc = isinstance(lhs, unicode_types) and isinstance(rhs, unicode_types
        )
    rpcuq__japa = isinstance(lhs, types.BaseTuple) and isinstance(rhs,
        types.BaseTuple)
    qgal__zicbv = isinstance(lhs, types.Set) and isinstance(rhs, types.Set)
    sds__vjgvh = isinstance(lhs, types.Number) and isinstance(rhs, types.Number
        )
    vxd__qfj = isinstance(lhs, types.Boolean) and isinstance(rhs, types.Boolean
        )
    luj__ncc = isinstance(lhs, types.NoneType) or isinstance(rhs, types.
        NoneType)
    fnaa__ljrbc = isinstance(lhs, types.DictType) and isinstance(rhs, types
        .DictType)
    nbp__kix = isinstance(lhs, types.EnumMember) and isinstance(rhs, types.
        EnumMember)
    bnd__dfgq = isinstance(lhs, types.Literal) and isinstance(rhs, types.
        Literal)
    return (eno__pukl or thsj__xxthf or svmox__nhupj or qpl__fgc or
        rpcuq__japa or qgal__zicbv or sds__vjgvh or vxd__qfj or luj__ncc or
        fnaa__ljrbc or ryat__miu or nbp__kix or bnd__dfgq)


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
        jiuma__jtm = create_overload_cmp_operator(op)
        overload(op, no_unliteral=True)(jiuma__jtm)


_install_cmp_ops()


def install_arith_ops():
    for op in (operator.add, operator.sub, operator.mul, operator.truediv,
        operator.floordiv, operator.mod, operator.pow):
        jiuma__jtm = create_overload_arith_op(op)
        overload(op, no_unliteral=True)(jiuma__jtm)


install_arith_ops()
