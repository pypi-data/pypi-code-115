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
        znjvo__brr = lhs.data if isinstance(lhs, SeriesType) else lhs
        fvzf__tqb = rhs.data if isinstance(rhs, SeriesType) else rhs
        if znjvo__brr in (bodo.pd_timestamp_type, bodo.pd_timedelta_type
            ) and fvzf__tqb.dtype in (bodo.datetime64ns, bodo.timedelta64ns):
            znjvo__brr = fvzf__tqb.dtype
        elif fvzf__tqb in (bodo.pd_timestamp_type, bodo.pd_timedelta_type
            ) and znjvo__brr.dtype in (bodo.datetime64ns, bodo.timedelta64ns):
            fvzf__tqb = znjvo__brr.dtype
        grc__xoxn = znjvo__brr, fvzf__tqb
        fbcnk__iwqyl = (
            f'{lhs} {numba.core.utils.OPERATORS_TO_BUILTINS[self.key]} {rhs} not supported'
            )
        try:
            nkof__adkcr = self.context.resolve_function_type(self.key,
                grc__xoxn, {}).return_type
        except Exception as yaz__rhik:
            raise BodoError(fbcnk__iwqyl)
        if is_overload_bool(nkof__adkcr):
            raise BodoError(fbcnk__iwqyl)
        zcxp__fspn = lhs.index if isinstance(lhs, SeriesType) else rhs.index
        vjlob__fiogd = lhs.name_typ if isinstance(lhs, SeriesType
            ) else rhs.name_typ
        tdvxc__fxj = types.bool_
        wrazc__vdjve = SeriesType(tdvxc__fxj, nkof__adkcr, zcxp__fspn,
            vjlob__fiogd)
        return wrazc__vdjve(*args)


def series_cmp_op_lower(op):

    def lower_impl(context, builder, sig, args):
        xnjc__lkc = bodo.hiframes.series_impl.create_binary_op_overload(op)(*
            sig.args)
        if xnjc__lkc is None:
            xnjc__lkc = create_overload_cmp_operator(op)(*sig.args)
        return context.compile_internal(builder, xnjc__lkc, sig, args)
    return lower_impl


class SeriesAndOrTyper(AbstractTemplate):

    def generic(self, args, kws):
        assert len(args) == 2
        assert not kws
        lhs, rhs = args
        if not (isinstance(lhs, SeriesType) or isinstance(rhs, SeriesType)):
            return
        znjvo__brr = lhs.data if isinstance(lhs, SeriesType) else lhs
        fvzf__tqb = rhs.data if isinstance(rhs, SeriesType) else rhs
        grc__xoxn = znjvo__brr, fvzf__tqb
        fbcnk__iwqyl = (
            f'{lhs} {numba.core.utils.OPERATORS_TO_BUILTINS[self.key]} {rhs} not supported'
            )
        try:
            nkof__adkcr = self.context.resolve_function_type(self.key,
                grc__xoxn, {}).return_type
        except Exception as lxaur__sjvea:
            raise BodoError(fbcnk__iwqyl)
        zcxp__fspn = lhs.index if isinstance(lhs, SeriesType) else rhs.index
        vjlob__fiogd = lhs.name_typ if isinstance(lhs, SeriesType
            ) else rhs.name_typ
        tdvxc__fxj = nkof__adkcr.dtype
        wrazc__vdjve = SeriesType(tdvxc__fxj, nkof__adkcr, zcxp__fspn,
            vjlob__fiogd)
        return wrazc__vdjve(*args)


def lower_series_and_or(op):

    def lower_and_or_impl(context, builder, sig, args):
        xnjc__lkc = bodo.hiframes.series_impl.create_binary_op_overload(op)(*
            sig.args)
        if xnjc__lkc is None:
            lhs, rhs = sig.args
            if isinstance(lhs, DataFrameType) or isinstance(rhs, DataFrameType
                ):
                xnjc__lkc = (bodo.hiframes.dataframe_impl.
                    create_binary_op_overload(op)(*sig.args))
        return context.compile_internal(builder, xnjc__lkc, sig, args)
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
            return bodo.hiframes.dataframe_impl.create_binary_op_overload(op)(
                lhs, rhs)
        if cmp_timeseries(lhs, rhs):
            return bodo.hiframes.series_dt_impl.create_cmp_op_overload(op)(lhs,
                rhs)
        if isinstance(lhs, SeriesType) or isinstance(rhs, SeriesType):
            return
        if lhs == datetime_date_array_type or rhs == datetime_date_array_type:
            return bodo.hiframes.datetime_date_ext.create_cmp_op_overload_arr(
                op)(lhs, rhs)
        if (lhs == datetime_timedelta_array_type or rhs ==
            datetime_timedelta_array_type):
            xnjc__lkc = (bodo.hiframes.datetime_timedelta_ext.
                create_cmp_op_overload(op))
            return xnjc__lkc(lhs, rhs)
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
            xnjc__lkc = (bodo.hiframes.datetime_timedelta_ext.
                pd_create_cmp_op_overload(op))
            return xnjc__lkc(lhs, rhs)
        if cmp_timestamp_or_date(lhs, rhs):
            return (bodo.hiframes.pd_timestamp_ext.
                create_timestamp_cmp_op_overload(op)(lhs, rhs))
        if cmp_op_supported_by_numba(lhs, rhs):
            return
        raise BodoError(
            f'{op} operator not supported for data types {lhs} and {rhs}.')
    return overload_cmp_operator


def add_dt_td_and_dt_date(lhs, rhs):
    hfs__uaof = lhs == datetime_timedelta_type and rhs == datetime_date_type
    cddz__emdl = rhs == datetime_timedelta_type and lhs == datetime_date_type
    return hfs__uaof or cddz__emdl


def add_timestamp(lhs, rhs):
    igij__gptsg = lhs == pd_timestamp_type and is_timedelta_type(rhs)
    vor__mvy = is_timedelta_type(lhs) and rhs == pd_timestamp_type
    return igij__gptsg or vor__mvy


def add_datetime_and_timedeltas(lhs, rhs):
    tsauy__qvtul = [datetime_timedelta_type, pd_timedelta_type]
    fxg__lmzbe = [datetime_timedelta_type, pd_timedelta_type,
        datetime_datetime_type]
    zdmkz__ljdbw = lhs in tsauy__qvtul and rhs in tsauy__qvtul
    hyazn__venom = (lhs == datetime_datetime_type and rhs in tsauy__qvtul or
        rhs == datetime_datetime_type and lhs in tsauy__qvtul)
    return zdmkz__ljdbw or hyazn__venom


def mul_string_arr_and_int(lhs, rhs):
    fvzf__tqb = isinstance(lhs, types.Integer) and is_str_arr_type(rhs)
    znjvo__brr = is_str_arr_type(lhs) and isinstance(rhs, types.Integer)
    return fvzf__tqb or znjvo__brr


def mul_timedelta_and_int(lhs, rhs):
    hfs__uaof = lhs in [pd_timedelta_type, datetime_timedelta_type
        ] and isinstance(rhs, types.Integer)
    cddz__emdl = rhs in [pd_timedelta_type, datetime_timedelta_type
        ] and isinstance(lhs, types.Integer)
    return hfs__uaof or cddz__emdl


def mul_date_offset_and_int(lhs, rhs):
    bnqv__frt = lhs in [week_type, month_end_type, month_begin_type,
        date_offset_type] and isinstance(rhs, types.Integer)
    knojn__bgag = rhs in [week_type, month_end_type, month_begin_type,
        date_offset_type] and isinstance(lhs, types.Integer)
    return bnqv__frt or knojn__bgag


def sub_offset_to_datetime_or_timestamp(lhs, rhs):
    ceyy__qdb = [datetime_datetime_type, pd_timestamp_type, datetime_date_type]
    fht__nba = [date_offset_type, month_begin_type, month_end_type, week_type]
    return rhs in fht__nba and lhs in ceyy__qdb


def sub_dt_index_and_timestamp(lhs, rhs):
    czq__zwpjg = isinstance(lhs, DatetimeIndexType
        ) and rhs == pd_timestamp_type
    gnbdu__jtn = isinstance(rhs, DatetimeIndexType
        ) and lhs == pd_timestamp_type
    return czq__zwpjg or gnbdu__jtn


def sub_dt_or_td(lhs, rhs):
    bkytt__qjg = lhs == datetime_date_type and rhs == datetime_timedelta_type
    ytxmk__vut = lhs == datetime_date_type and rhs == datetime_date_type
    kiwnj__iatx = (lhs == datetime_date_array_type and rhs ==
        datetime_timedelta_type)
    return bkytt__qjg or ytxmk__vut or kiwnj__iatx


def sub_datetime_and_timedeltas(lhs, rhs):
    nsdbh__ikmmh = (is_timedelta_type(lhs) or lhs == datetime_datetime_type
        ) and is_timedelta_type(rhs)
    dlf__eag = (lhs == datetime_timedelta_array_type and rhs ==
        datetime_timedelta_type)
    return nsdbh__ikmmh or dlf__eag


def div_timedelta_and_int(lhs, rhs):
    zdmkz__ljdbw = lhs == pd_timedelta_type and rhs == pd_timedelta_type
    bunrl__xkh = lhs == pd_timedelta_type and isinstance(rhs, types.Integer)
    return zdmkz__ljdbw or bunrl__xkh


def div_datetime_timedelta(lhs, rhs):
    zdmkz__ljdbw = (lhs == datetime_timedelta_type and rhs ==
        datetime_timedelta_type)
    bunrl__xkh = lhs == datetime_timedelta_type and rhs == types.int64
    return zdmkz__ljdbw or bunrl__xkh


def mod_timedeltas(lhs, rhs):
    mlrl__jtn = lhs == pd_timedelta_type and rhs == pd_timedelta_type
    wtdq__wmc = (lhs == datetime_timedelta_type and rhs ==
        datetime_timedelta_type)
    return mlrl__jtn or wtdq__wmc


def cmp_dt_index_to_string(lhs, rhs):
    czq__zwpjg = isinstance(lhs, DatetimeIndexType) and types.unliteral(rhs
        ) == string_type
    gnbdu__jtn = isinstance(rhs, DatetimeIndexType) and types.unliteral(lhs
        ) == string_type
    return czq__zwpjg or gnbdu__jtn


def cmp_timestamp_or_date(lhs, rhs):
    ofi__iubhz = (lhs == pd_timestamp_type and rhs == bodo.hiframes.
        datetime_date_ext.datetime_date_type)
    zpzw__qwdwr = (lhs == bodo.hiframes.datetime_date_ext.
        datetime_date_type and rhs == pd_timestamp_type)
    vbazk__ilvaw = lhs == pd_timestamp_type and rhs == pd_timestamp_type
    fguvk__llqjv = lhs == pd_timestamp_type and rhs == bodo.datetime64ns
    nrtx__bcj = rhs == pd_timestamp_type and lhs == bodo.datetime64ns
    return (ofi__iubhz or zpzw__qwdwr or vbazk__ilvaw or fguvk__llqjv or
        nrtx__bcj)


def cmp_timeseries(lhs, rhs):
    oxi__gdyza = bodo.hiframes.pd_series_ext.is_dt64_series_typ(rhs) and (bodo
        .utils.typing.is_overload_constant_str(lhs) or lhs == bodo.libs.
        str_ext.string_type or lhs == bodo.hiframes.pd_timestamp_ext.
        pd_timestamp_type)
    bhc__bndyv = bodo.hiframes.pd_series_ext.is_dt64_series_typ(lhs) and (bodo
        .utils.typing.is_overload_constant_str(rhs) or rhs == bodo.libs.
        str_ext.string_type or rhs == bodo.hiframes.pd_timestamp_ext.
        pd_timestamp_type)
    olxf__lowa = oxi__gdyza or bhc__bndyv
    gmepu__myha = bodo.hiframes.pd_series_ext.is_timedelta64_series_typ(rhs
        ) and lhs == bodo.hiframes.datetime_timedelta_ext.datetime_timedelta_type
    bjin__lnwe = bodo.hiframes.pd_series_ext.is_timedelta64_series_typ(lhs
        ) and rhs == bodo.hiframes.datetime_timedelta_ext.datetime_timedelta_type
    fglic__mqwst = gmepu__myha or bjin__lnwe
    return olxf__lowa or fglic__mqwst


def cmp_timedeltas(lhs, rhs):
    zdmkz__ljdbw = [pd_timedelta_type, bodo.timedelta64ns]
    return lhs in zdmkz__ljdbw and rhs in zdmkz__ljdbw


def operand_is_index(operand):
    return is_index_type(operand) or isinstance(operand, HeterogeneousIndexType
        )


def helper_time_series_checks(operand):
    wgj__qfpzd = bodo.hiframes.pd_series_ext.is_dt64_series_typ(operand
        ) or bodo.hiframes.pd_series_ext.is_timedelta64_series_typ(operand
        ) or operand in [datetime_timedelta_type, datetime_datetime_type,
        pd_timestamp_type]
    return wgj__qfpzd


def binary_array_cmp(lhs, rhs):
    return lhs == binary_array_type and rhs in [bytes_type, binary_array_type
        ] or lhs in [bytes_type, binary_array_type
        ] and rhs == binary_array_type


def can_cmp_date_datetime(lhs, rhs, op):
    return op in (operator.eq, operator.ne) and (lhs == datetime_date_type and
        rhs == datetime_datetime_type or lhs == datetime_datetime_type and 
        rhs == datetime_date_type)


def time_series_operation(lhs, rhs):
    eejy__kkwci = bodo.hiframes.pd_series_ext.is_timedelta64_series_typ(lhs
        ) and rhs == datetime_timedelta_type
    xwxmh__dycsu = bodo.hiframes.pd_series_ext.is_timedelta64_series_typ(rhs
        ) and lhs == datetime_timedelta_type
    bya__cvmx = bodo.hiframes.pd_series_ext.is_dt64_series_typ(lhs
        ) and helper_time_series_checks(rhs)
    cto__srs = bodo.hiframes.pd_series_ext.is_dt64_series_typ(rhs
        ) and helper_time_series_checks(lhs)
    return eejy__kkwci or xwxmh__dycsu or bya__cvmx or cto__srs


def args_td_and_int_array(lhs, rhs):
    aic__ccfb = (isinstance(lhs, IntegerArrayType) or isinstance(lhs, types
        .Array) and isinstance(lhs.dtype, types.Integer)) or (isinstance(
        rhs, IntegerArrayType) or isinstance(rhs, types.Array) and
        isinstance(rhs.dtype, types.Integer))
    owmwj__ukler = lhs in [pd_timedelta_type] or rhs in [pd_timedelta_type]
    return aic__ccfb and owmwj__ukler


def arith_op_supported_by_numba(op, lhs, rhs):
    if op == operator.mul:
        cddz__emdl = isinstance(lhs, (types.Integer, types.Float)
            ) and isinstance(rhs, types.NPTimedelta)
        hfs__uaof = isinstance(rhs, (types.Integer, types.Float)
            ) and isinstance(lhs, types.NPTimedelta)
        zfees__fstxy = cddz__emdl or hfs__uaof
        pasw__vytbu = isinstance(rhs, types.UnicodeType) and isinstance(lhs,
            types.Integer)
        vlrb__baw = isinstance(lhs, types.UnicodeType) and isinstance(rhs,
            types.Integer)
        lsiu__fxmg = pasw__vytbu or vlrb__baw
        ygn__gaek = isinstance(lhs, types.Integer) and isinstance(rhs,
            types.Integer)
        qzu__mnni = isinstance(lhs, types.Float) and isinstance(rhs, types.
            Float)
        gxk__hxptm = isinstance(lhs, types.Complex) and isinstance(rhs,
            types.Complex)
        nvi__ohw = ygn__gaek or qzu__mnni or gxk__hxptm
        aoif__bzmp = isinstance(lhs, types.List) and isinstance(rhs, types.
            Integer) or isinstance(lhs, types.Integer) and isinstance(rhs,
            types.List)
        tys = types.UnicodeCharSeq, types.CharSeq, types.Bytes
        kwrwz__vmm = isinstance(lhs, tys) or isinstance(rhs, tys)
        ffoq__zemf = isinstance(lhs, types.Array) or isinstance(rhs, types.
            Array)
        return (zfees__fstxy or lsiu__fxmg or nvi__ohw or aoif__bzmp or
            kwrwz__vmm or ffoq__zemf)
    if op == operator.pow:
        fnnjb__ebim = isinstance(lhs, types.Integer) and isinstance(rhs, (
            types.IntegerLiteral, types.Integer))
        crn__rwv = isinstance(lhs, types.Float) and isinstance(rhs, (types.
            IntegerLiteral, types.Float, types.Integer) or rhs in types.
            unsigned_domain or rhs in types.signed_domain)
        gxk__hxptm = isinstance(lhs, types.Complex) and isinstance(rhs,
            types.Complex)
        ffoq__zemf = isinstance(lhs, types.Array) or isinstance(rhs, types.
            Array)
        return fnnjb__ebim or crn__rwv or gxk__hxptm or ffoq__zemf
    if op == operator.floordiv:
        qzu__mnni = lhs in types.real_domain and rhs in types.real_domain
        ygn__gaek = isinstance(lhs, types.Integer) and isinstance(rhs,
            types.Integer)
        vgop__pllxd = isinstance(lhs, types.Float) and isinstance(rhs,
            types.Float)
        zdmkz__ljdbw = isinstance(lhs, types.NPTimedelta) and isinstance(rhs,
            (types.Integer, types.Float, types.NPTimedelta))
        ffoq__zemf = isinstance(lhs, types.Array) or isinstance(rhs, types.
            Array)
        return (qzu__mnni or ygn__gaek or vgop__pllxd or zdmkz__ljdbw or
            ffoq__zemf)
    if op == operator.truediv:
        lhfw__oahk = lhs in machine_ints and rhs in machine_ints
        qzu__mnni = lhs in types.real_domain and rhs in types.real_domain
        gxk__hxptm = (lhs in types.complex_domain and rhs in types.
            complex_domain)
        ygn__gaek = isinstance(lhs, types.Integer) and isinstance(rhs,
            types.Integer)
        vgop__pllxd = isinstance(lhs, types.Float) and isinstance(rhs,
            types.Float)
        rxrn__weo = isinstance(lhs, types.Complex) and isinstance(rhs,
            types.Complex)
        zdmkz__ljdbw = isinstance(lhs, types.NPTimedelta) and isinstance(rhs,
            (types.Integer, types.Float, types.NPTimedelta))
        ffoq__zemf = isinstance(lhs, types.Array) or isinstance(rhs, types.
            Array)
        return (lhfw__oahk or qzu__mnni or gxk__hxptm or ygn__gaek or
            vgop__pllxd or rxrn__weo or zdmkz__ljdbw or ffoq__zemf)
    if op == operator.mod:
        lhfw__oahk = lhs in machine_ints and rhs in machine_ints
        qzu__mnni = lhs in types.real_domain and rhs in types.real_domain
        ygn__gaek = isinstance(lhs, types.Integer) and isinstance(rhs,
            types.Integer)
        vgop__pllxd = isinstance(lhs, types.Float) and isinstance(rhs,
            types.Float)
        ffoq__zemf = isinstance(lhs, types.Array) or isinstance(rhs, types.
            Array)
        return (lhfw__oahk or qzu__mnni or ygn__gaek or vgop__pllxd or
            ffoq__zemf)
    if op == operator.add or op == operator.sub:
        zfees__fstxy = isinstance(lhs, types.NPTimedelta) and isinstance(rhs,
            types.NPTimedelta)
        hrk__ccvw = isinstance(lhs, types.NPDatetime) and isinstance(rhs,
            types.NPDatetime)
        cekb__acrt = isinstance(lhs, types.NPDatetime) and isinstance(rhs,
            types.NPTimedelta)
        evm__rrze = isinstance(lhs, types.Set) and isinstance(rhs, types.Set)
        ygn__gaek = isinstance(lhs, types.Integer) and isinstance(rhs,
            types.Integer)
        qzu__mnni = isinstance(lhs, types.Float) and isinstance(rhs, types.
            Float)
        gxk__hxptm = isinstance(lhs, types.Complex) and isinstance(rhs,
            types.Complex)
        nvi__ohw = ygn__gaek or qzu__mnni or gxk__hxptm
        ffoq__zemf = isinstance(lhs, types.Array) or isinstance(rhs, types.
            Array)
        ncv__zzz = isinstance(lhs, types.BaseTuple) and isinstance(rhs,
            types.BaseTuple)
        aoif__bzmp = isinstance(lhs, types.List) and isinstance(rhs, types.List
            )
        kac__gss = isinstance(lhs, types.UnicodeCharSeq) and isinstance(rhs,
            types.UnicodeType)
        zmqps__metz = isinstance(rhs, types.UnicodeCharSeq) and isinstance(lhs,
            types.UnicodeType)
        qmd__vehy = isinstance(lhs, types.UnicodeCharSeq) and isinstance(rhs,
            types.UnicodeCharSeq)
        mvx__bbq = isinstance(lhs, (types.CharSeq, types.Bytes)
            ) and isinstance(rhs, (types.CharSeq, types.Bytes))
        yfxtm__tlzt = kac__gss or zmqps__metz or qmd__vehy or mvx__bbq
        lsiu__fxmg = isinstance(lhs, types.UnicodeType) and isinstance(rhs,
            types.UnicodeType)
        nxjvh__uha = isinstance(lhs, types.UnicodeType) and isinstance(rhs,
            types.UnicodeCharSeq)
        qpm__iiw = lsiu__fxmg or nxjvh__uha
        oasn__rcgup = lhs == types.NPTimedelta and rhs == types.NPDatetime
        axdh__oggev = (ncv__zzz or aoif__bzmp or yfxtm__tlzt or qpm__iiw or
            oasn__rcgup)
        gpicp__nfrjb = op == operator.add and axdh__oggev
        return (zfees__fstxy or hrk__ccvw or cekb__acrt or evm__rrze or
            nvi__ohw or ffoq__zemf or gpicp__nfrjb)


def cmp_op_supported_by_numba(lhs, rhs):
    ffoq__zemf = isinstance(lhs, types.Array) or isinstance(rhs, types.Array)
    aoif__bzmp = isinstance(lhs, types.ListType) and isinstance(rhs, types.
        ListType)
    zfees__fstxy = isinstance(lhs, types.NPTimedelta) and isinstance(rhs,
        types.NPTimedelta)
    cuu__qmwpk = isinstance(lhs, types.NPDatetime) and isinstance(rhs,
        types.NPDatetime)
    unicode_types = (types.UnicodeType, types.StringLiteral, types.CharSeq,
        types.Bytes, types.UnicodeCharSeq)
    lsiu__fxmg = isinstance(lhs, unicode_types) and isinstance(rhs,
        unicode_types)
    ncv__zzz = isinstance(lhs, types.BaseTuple) and isinstance(rhs, types.
        BaseTuple)
    evm__rrze = isinstance(lhs, types.Set) and isinstance(rhs, types.Set)
    nvi__ohw = isinstance(lhs, types.Number) and isinstance(rhs, types.Number)
    mnuy__jhgw = isinstance(lhs, types.Boolean) and isinstance(rhs, types.
        Boolean)
    jgc__jlud = isinstance(lhs, types.NoneType) or isinstance(rhs, types.
        NoneType)
    zxrw__mcrr = isinstance(lhs, types.DictType) and isinstance(rhs, types.
        DictType)
    jiizm__ucht = isinstance(lhs, types.EnumMember) and isinstance(rhs,
        types.EnumMember)
    bektg__wzo = isinstance(lhs, types.Literal) and isinstance(rhs, types.
        Literal)
    return (aoif__bzmp or zfees__fstxy or cuu__qmwpk or lsiu__fxmg or
        ncv__zzz or evm__rrze or nvi__ohw or mnuy__jhgw or jgc__jlud or
        zxrw__mcrr or ffoq__zemf or jiizm__ucht or bektg__wzo)


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
        sve__gwlmp = create_overload_cmp_operator(op)
        overload(op, no_unliteral=True)(sve__gwlmp)


_install_cmp_ops()


def install_arith_ops():
    for op in (operator.add, operator.sub, operator.mul, operator.truediv,
        operator.floordiv, operator.mod, operator.pow):
        sve__gwlmp = create_overload_arith_op(op)
        overload(op, no_unliteral=True)(sve__gwlmp)


install_arith_ops()
