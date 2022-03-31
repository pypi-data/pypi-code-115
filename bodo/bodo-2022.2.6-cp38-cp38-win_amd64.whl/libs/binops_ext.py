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
        mio__bsia = lhs.data if isinstance(lhs, SeriesType) else lhs
        xosn__gmku = rhs.data if isinstance(rhs, SeriesType) else rhs
        if mio__bsia in (bodo.pd_timestamp_type, bodo.pd_timedelta_type
            ) and xosn__gmku.dtype in (bodo.datetime64ns, bodo.timedelta64ns):
            mio__bsia = xosn__gmku.dtype
        elif xosn__gmku in (bodo.pd_timestamp_type, bodo.pd_timedelta_type
            ) and mio__bsia.dtype in (bodo.datetime64ns, bodo.timedelta64ns):
            xosn__gmku = mio__bsia.dtype
        yqa__gxky = mio__bsia, xosn__gmku
        haod__enjea = (
            f'{lhs} {numba.core.utils.OPERATORS_TO_BUILTINS[self.key]} {rhs} not supported'
            )
        try:
            ruz__akyv = self.context.resolve_function_type(self.key,
                yqa__gxky, {}).return_type
        except Exception as ynd__cxn:
            raise BodoError(haod__enjea)
        if is_overload_bool(ruz__akyv):
            raise BodoError(haod__enjea)
        aib__sizm = lhs.index if isinstance(lhs, SeriesType) else rhs.index
        mbbmo__fre = lhs.name_typ if isinstance(lhs, SeriesType
            ) else rhs.name_typ
        cqssp__lviu = types.bool_
        hzq__ybqjv = SeriesType(cqssp__lviu, ruz__akyv, aib__sizm, mbbmo__fre)
        return hzq__ybqjv(*args)


def series_cmp_op_lower(op):

    def lower_impl(context, builder, sig, args):
        bch__lvzmi = bodo.hiframes.series_impl.create_binary_op_overload(op)(*
            sig.args)
        if bch__lvzmi is None:
            bch__lvzmi = create_overload_cmp_operator(op)(*sig.args)
        return context.compile_internal(builder, bch__lvzmi, sig, args)
    return lower_impl


class SeriesAndOrTyper(AbstractTemplate):

    def generic(self, args, kws):
        assert len(args) == 2
        assert not kws
        lhs, rhs = args
        if not (isinstance(lhs, SeriesType) or isinstance(rhs, SeriesType)):
            return
        mio__bsia = lhs.data if isinstance(lhs, SeriesType) else lhs
        xosn__gmku = rhs.data if isinstance(rhs, SeriesType) else rhs
        yqa__gxky = mio__bsia, xosn__gmku
        haod__enjea = (
            f'{lhs} {numba.core.utils.OPERATORS_TO_BUILTINS[self.key]} {rhs} not supported'
            )
        try:
            ruz__akyv = self.context.resolve_function_type(self.key,
                yqa__gxky, {}).return_type
        except Exception as dbeg__hbt:
            raise BodoError(haod__enjea)
        aib__sizm = lhs.index if isinstance(lhs, SeriesType) else rhs.index
        mbbmo__fre = lhs.name_typ if isinstance(lhs, SeriesType
            ) else rhs.name_typ
        cqssp__lviu = ruz__akyv.dtype
        hzq__ybqjv = SeriesType(cqssp__lviu, ruz__akyv, aib__sizm, mbbmo__fre)
        return hzq__ybqjv(*args)


def lower_series_and_or(op):

    def lower_and_or_impl(context, builder, sig, args):
        bch__lvzmi = bodo.hiframes.series_impl.create_binary_op_overload(op)(*
            sig.args)
        if bch__lvzmi is None:
            lhs, rhs = sig.args
            if isinstance(lhs, DataFrameType) or isinstance(rhs, DataFrameType
                ):
                bch__lvzmi = (bodo.hiframes.dataframe_impl.
                    create_binary_op_overload(op)(*sig.args))
        return context.compile_internal(builder, bch__lvzmi, sig, args)
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
            bch__lvzmi = (bodo.hiframes.datetime_timedelta_ext.
                create_cmp_op_overload(op))
            return bch__lvzmi(lhs, rhs)
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
            bch__lvzmi = (bodo.hiframes.datetime_timedelta_ext.
                pd_create_cmp_op_overload(op))
            return bch__lvzmi(lhs, rhs)
        if cmp_timestamp_or_date(lhs, rhs):
            return (bodo.hiframes.pd_timestamp_ext.
                create_timestamp_cmp_op_overload(op)(lhs, rhs))
        if cmp_op_supported_by_numba(lhs, rhs):
            return
        raise BodoError(
            f'{op} operator not supported for data types {lhs} and {rhs}.')
    return overload_cmp_operator


def add_dt_td_and_dt_date(lhs, rhs):
    zupor__dvt = lhs == datetime_timedelta_type and rhs == datetime_date_type
    wsd__qygjf = rhs == datetime_timedelta_type and lhs == datetime_date_type
    return zupor__dvt or wsd__qygjf


def add_timestamp(lhs, rhs):
    idmex__uvpkf = lhs == pd_timestamp_type and is_timedelta_type(rhs)
    bds__amhra = is_timedelta_type(lhs) and rhs == pd_timestamp_type
    return idmex__uvpkf or bds__amhra


def add_datetime_and_timedeltas(lhs, rhs):
    yuqy__onjl = [datetime_timedelta_type, pd_timedelta_type]
    seoff__ivsuy = [datetime_timedelta_type, pd_timedelta_type,
        datetime_datetime_type]
    yexal__dqu = lhs in yuqy__onjl and rhs in yuqy__onjl
    tqa__juoio = (lhs == datetime_datetime_type and rhs in yuqy__onjl or 
        rhs == datetime_datetime_type and lhs in yuqy__onjl)
    return yexal__dqu or tqa__juoio


def mul_string_arr_and_int(lhs, rhs):
    xosn__gmku = isinstance(lhs, types.Integer) and is_str_arr_type(rhs)
    mio__bsia = is_str_arr_type(lhs) and isinstance(rhs, types.Integer)
    return xosn__gmku or mio__bsia


def mul_timedelta_and_int(lhs, rhs):
    zupor__dvt = lhs in [pd_timedelta_type, datetime_timedelta_type
        ] and isinstance(rhs, types.Integer)
    wsd__qygjf = rhs in [pd_timedelta_type, datetime_timedelta_type
        ] and isinstance(lhs, types.Integer)
    return zupor__dvt or wsd__qygjf


def mul_date_offset_and_int(lhs, rhs):
    ocd__cupkh = lhs in [week_type, month_end_type, month_begin_type,
        date_offset_type] and isinstance(rhs, types.Integer)
    ewyfg__ngfzu = rhs in [week_type, month_end_type, month_begin_type,
        date_offset_type] and isinstance(lhs, types.Integer)
    return ocd__cupkh or ewyfg__ngfzu


def sub_offset_to_datetime_or_timestamp(lhs, rhs):
    wfhf__rba = [datetime_datetime_type, pd_timestamp_type, datetime_date_type]
    rvbw__mhz = [date_offset_type, month_begin_type, month_end_type, week_type]
    return rhs in rvbw__mhz and lhs in wfhf__rba


def sub_dt_index_and_timestamp(lhs, rhs):
    rjqzq__bgcvs = isinstance(lhs, DatetimeIndexType
        ) and rhs == pd_timestamp_type
    yfokl__gsba = isinstance(rhs, DatetimeIndexType
        ) and lhs == pd_timestamp_type
    return rjqzq__bgcvs or yfokl__gsba


def sub_dt_or_td(lhs, rhs):
    icmfw__yvc = lhs == datetime_date_type and rhs == datetime_timedelta_type
    xtufv__pni = lhs == datetime_date_type and rhs == datetime_date_type
    tjk__tpkhw = (lhs == datetime_date_array_type and rhs ==
        datetime_timedelta_type)
    return icmfw__yvc or xtufv__pni or tjk__tpkhw


def sub_datetime_and_timedeltas(lhs, rhs):
    xbaw__dkeia = (is_timedelta_type(lhs) or lhs == datetime_datetime_type
        ) and is_timedelta_type(rhs)
    ddr__eouoq = (lhs == datetime_timedelta_array_type and rhs ==
        datetime_timedelta_type)
    return xbaw__dkeia or ddr__eouoq


def div_timedelta_and_int(lhs, rhs):
    yexal__dqu = lhs == pd_timedelta_type and rhs == pd_timedelta_type
    jgxmp__lpt = lhs == pd_timedelta_type and isinstance(rhs, types.Integer)
    return yexal__dqu or jgxmp__lpt


def div_datetime_timedelta(lhs, rhs):
    yexal__dqu = (lhs == datetime_timedelta_type and rhs ==
        datetime_timedelta_type)
    jgxmp__lpt = lhs == datetime_timedelta_type and rhs == types.int64
    return yexal__dqu or jgxmp__lpt


def mod_timedeltas(lhs, rhs):
    tilmg__bpdrb = lhs == pd_timedelta_type and rhs == pd_timedelta_type
    aypop__sqml = (lhs == datetime_timedelta_type and rhs ==
        datetime_timedelta_type)
    return tilmg__bpdrb or aypop__sqml


def cmp_dt_index_to_string(lhs, rhs):
    rjqzq__bgcvs = isinstance(lhs, DatetimeIndexType) and types.unliteral(rhs
        ) == string_type
    yfokl__gsba = isinstance(rhs, DatetimeIndexType) and types.unliteral(lhs
        ) == string_type
    return rjqzq__bgcvs or yfokl__gsba


def cmp_timestamp_or_date(lhs, rhs):
    kli__rgw = (lhs == pd_timestamp_type and rhs == bodo.hiframes.
        datetime_date_ext.datetime_date_type)
    vemgc__gyi = (lhs == bodo.hiframes.datetime_date_ext.datetime_date_type and
        rhs == pd_timestamp_type)
    cfoz__tdv = lhs == pd_timestamp_type and rhs == pd_timestamp_type
    tmtk__qcf = lhs == pd_timestamp_type and rhs == bodo.datetime64ns
    tibsu__ebovb = rhs == pd_timestamp_type and lhs == bodo.datetime64ns
    return kli__rgw or vemgc__gyi or cfoz__tdv or tmtk__qcf or tibsu__ebovb


def cmp_timeseries(lhs, rhs):
    sbf__qdj = bodo.hiframes.pd_series_ext.is_dt64_series_typ(rhs) and (bodo
        .utils.typing.is_overload_constant_str(lhs) or lhs == bodo.libs.
        str_ext.string_type or lhs == bodo.hiframes.pd_timestamp_ext.
        pd_timestamp_type)
    roql__xrjcz = bodo.hiframes.pd_series_ext.is_dt64_series_typ(lhs) and (bodo
        .utils.typing.is_overload_constant_str(rhs) or rhs == bodo.libs.
        str_ext.string_type or rhs == bodo.hiframes.pd_timestamp_ext.
        pd_timestamp_type)
    sbwq__xpd = sbf__qdj or roql__xrjcz
    erxqx__bekr = bodo.hiframes.pd_series_ext.is_timedelta64_series_typ(rhs
        ) and lhs == bodo.hiframes.datetime_timedelta_ext.datetime_timedelta_type
    rede__zluq = bodo.hiframes.pd_series_ext.is_timedelta64_series_typ(lhs
        ) and rhs == bodo.hiframes.datetime_timedelta_ext.datetime_timedelta_type
    aaz__uwhof = erxqx__bekr or rede__zluq
    return sbwq__xpd or aaz__uwhof


def cmp_timedeltas(lhs, rhs):
    yexal__dqu = [pd_timedelta_type, bodo.timedelta64ns]
    return lhs in yexal__dqu and rhs in yexal__dqu


def operand_is_index(operand):
    return is_index_type(operand) or isinstance(operand, HeterogeneousIndexType
        )


def helper_time_series_checks(operand):
    aqcwq__fre = bodo.hiframes.pd_series_ext.is_dt64_series_typ(operand
        ) or bodo.hiframes.pd_series_ext.is_timedelta64_series_typ(operand
        ) or operand in [datetime_timedelta_type, datetime_datetime_type,
        pd_timestamp_type]
    return aqcwq__fre


def binary_array_cmp(lhs, rhs):
    return lhs == binary_array_type and rhs in [bytes_type, binary_array_type
        ] or lhs in [bytes_type, binary_array_type
        ] and rhs == binary_array_type


def can_cmp_date_datetime(lhs, rhs, op):
    return op in (operator.eq, operator.ne) and (lhs == datetime_date_type and
        rhs == datetime_datetime_type or lhs == datetime_datetime_type and 
        rhs == datetime_date_type)


def time_series_operation(lhs, rhs):
    hbqsw__qgnb = bodo.hiframes.pd_series_ext.is_timedelta64_series_typ(lhs
        ) and rhs == datetime_timedelta_type
    muna__vwqv = bodo.hiframes.pd_series_ext.is_timedelta64_series_typ(rhs
        ) and lhs == datetime_timedelta_type
    kldw__bei = bodo.hiframes.pd_series_ext.is_dt64_series_typ(lhs
        ) and helper_time_series_checks(rhs)
    cwgo__muhpc = bodo.hiframes.pd_series_ext.is_dt64_series_typ(rhs
        ) and helper_time_series_checks(lhs)
    return hbqsw__qgnb or muna__vwqv or kldw__bei or cwgo__muhpc


def args_td_and_int_array(lhs, rhs):
    rhu__gmgpj = (isinstance(lhs, IntegerArrayType) or isinstance(lhs,
        types.Array) and isinstance(lhs.dtype, types.Integer)) or (isinstance
        (rhs, IntegerArrayType) or isinstance(rhs, types.Array) and
        isinstance(rhs.dtype, types.Integer))
    btsk__ybub = lhs in [pd_timedelta_type] or rhs in [pd_timedelta_type]
    return rhu__gmgpj and btsk__ybub


def arith_op_supported_by_numba(op, lhs, rhs):
    if op == operator.mul:
        wsd__qygjf = isinstance(lhs, (types.Integer, types.Float)
            ) and isinstance(rhs, types.NPTimedelta)
        zupor__dvt = isinstance(rhs, (types.Integer, types.Float)
            ) and isinstance(lhs, types.NPTimedelta)
        dcbv__cnpd = wsd__qygjf or zupor__dvt
        pbyfb__hecwx = isinstance(rhs, types.UnicodeType) and isinstance(lhs,
            types.Integer)
        qeru__cek = isinstance(lhs, types.UnicodeType) and isinstance(rhs,
            types.Integer)
        rkndm__fobo = pbyfb__hecwx or qeru__cek
        askuj__kmcf = isinstance(lhs, types.Integer) and isinstance(rhs,
            types.Integer)
        jae__oih = isinstance(lhs, types.Float) and isinstance(rhs, types.Float
            )
        wlu__ihpu = isinstance(lhs, types.Complex) and isinstance(rhs,
            types.Complex)
        vzum__qgoi = askuj__kmcf or jae__oih or wlu__ihpu
        tts__kzt = isinstance(lhs, types.List) and isinstance(rhs, types.
            Integer) or isinstance(lhs, types.Integer) and isinstance(rhs,
            types.List)
        tys = types.UnicodeCharSeq, types.CharSeq, types.Bytes
        aym__qczn = isinstance(lhs, tys) or isinstance(rhs, tys)
        cmb__zinul = isinstance(lhs, types.Array) or isinstance(rhs, types.
            Array)
        return (dcbv__cnpd or rkndm__fobo or vzum__qgoi or tts__kzt or
            aym__qczn or cmb__zinul)
    if op == operator.pow:
        mkoi__woer = isinstance(lhs, types.Integer) and isinstance(rhs, (
            types.IntegerLiteral, types.Integer))
        sib__xxqc = isinstance(lhs, types.Float) and isinstance(rhs, (types
            .IntegerLiteral, types.Float, types.Integer) or rhs in types.
            unsigned_domain or rhs in types.signed_domain)
        wlu__ihpu = isinstance(lhs, types.Complex) and isinstance(rhs,
            types.Complex)
        cmb__zinul = isinstance(lhs, types.Array) or isinstance(rhs, types.
            Array)
        return mkoi__woer or sib__xxqc or wlu__ihpu or cmb__zinul
    if op == operator.floordiv:
        jae__oih = lhs in types.real_domain and rhs in types.real_domain
        askuj__kmcf = isinstance(lhs, types.Integer) and isinstance(rhs,
            types.Integer)
        vhprw__enc = isinstance(lhs, types.Float) and isinstance(rhs, types
            .Float)
        yexal__dqu = isinstance(lhs, types.NPTimedelta) and isinstance(rhs,
            (types.Integer, types.Float, types.NPTimedelta))
        cmb__zinul = isinstance(lhs, types.Array) or isinstance(rhs, types.
            Array)
        return (jae__oih or askuj__kmcf or vhprw__enc or yexal__dqu or
            cmb__zinul)
    if op == operator.truediv:
        klwl__hpu = lhs in machine_ints and rhs in machine_ints
        jae__oih = lhs in types.real_domain and rhs in types.real_domain
        wlu__ihpu = lhs in types.complex_domain and rhs in types.complex_domain
        askuj__kmcf = isinstance(lhs, types.Integer) and isinstance(rhs,
            types.Integer)
        vhprw__enc = isinstance(lhs, types.Float) and isinstance(rhs, types
            .Float)
        cvbt__egbk = isinstance(lhs, types.Complex) and isinstance(rhs,
            types.Complex)
        yexal__dqu = isinstance(lhs, types.NPTimedelta) and isinstance(rhs,
            (types.Integer, types.Float, types.NPTimedelta))
        cmb__zinul = isinstance(lhs, types.Array) or isinstance(rhs, types.
            Array)
        return (klwl__hpu or jae__oih or wlu__ihpu or askuj__kmcf or
            vhprw__enc or cvbt__egbk or yexal__dqu or cmb__zinul)
    if op == operator.mod:
        klwl__hpu = lhs in machine_ints and rhs in machine_ints
        jae__oih = lhs in types.real_domain and rhs in types.real_domain
        askuj__kmcf = isinstance(lhs, types.Integer) and isinstance(rhs,
            types.Integer)
        vhprw__enc = isinstance(lhs, types.Float) and isinstance(rhs, types
            .Float)
        cmb__zinul = isinstance(lhs, types.Array) or isinstance(rhs, types.
            Array)
        return klwl__hpu or jae__oih or askuj__kmcf or vhprw__enc or cmb__zinul
    if op == operator.add or op == operator.sub:
        dcbv__cnpd = isinstance(lhs, types.NPTimedelta) and isinstance(rhs,
            types.NPTimedelta)
        ckwh__uhu = isinstance(lhs, types.NPDatetime) and isinstance(rhs,
            types.NPDatetime)
        avbxc__qazv = isinstance(lhs, types.NPDatetime) and isinstance(rhs,
            types.NPTimedelta)
        bjl__bpvu = isinstance(lhs, types.Set) and isinstance(rhs, types.Set)
        askuj__kmcf = isinstance(lhs, types.Integer) and isinstance(rhs,
            types.Integer)
        jae__oih = isinstance(lhs, types.Float) and isinstance(rhs, types.Float
            )
        wlu__ihpu = isinstance(lhs, types.Complex) and isinstance(rhs,
            types.Complex)
        vzum__qgoi = askuj__kmcf or jae__oih or wlu__ihpu
        cmb__zinul = isinstance(lhs, types.Array) or isinstance(rhs, types.
            Array)
        tqvf__ljutd = isinstance(lhs, types.BaseTuple) and isinstance(rhs,
            types.BaseTuple)
        tts__kzt = isinstance(lhs, types.List) and isinstance(rhs, types.List)
        xljr__oua = isinstance(lhs, types.UnicodeCharSeq) and isinstance(rhs,
            types.UnicodeType)
        fuby__tjac = isinstance(rhs, types.UnicodeCharSeq) and isinstance(lhs,
            types.UnicodeType)
        jjr__ryd = isinstance(lhs, types.UnicodeCharSeq) and isinstance(rhs,
            types.UnicodeCharSeq)
        ftqtl__aya = isinstance(lhs, (types.CharSeq, types.Bytes)
            ) and isinstance(rhs, (types.CharSeq, types.Bytes))
        selv__wse = xljr__oua or fuby__tjac or jjr__ryd or ftqtl__aya
        rkndm__fobo = isinstance(lhs, types.UnicodeType) and isinstance(rhs,
            types.UnicodeType)
        gnf__lqbpc = isinstance(lhs, types.UnicodeType) and isinstance(rhs,
            types.UnicodeCharSeq)
        kasv__fdp = rkndm__fobo or gnf__lqbpc
        gtt__tamxc = lhs == types.NPTimedelta and rhs == types.NPDatetime
        qwkjl__ysj = (tqvf__ljutd or tts__kzt or selv__wse or kasv__fdp or
            gtt__tamxc)
        azbh__rvvc = op == operator.add and qwkjl__ysj
        return (dcbv__cnpd or ckwh__uhu or avbxc__qazv or bjl__bpvu or
            vzum__qgoi or cmb__zinul or azbh__rvvc)


def cmp_op_supported_by_numba(lhs, rhs):
    cmb__zinul = isinstance(lhs, types.Array) or isinstance(rhs, types.Array)
    tts__kzt = isinstance(lhs, types.ListType) and isinstance(rhs, types.
        ListType)
    dcbv__cnpd = isinstance(lhs, types.NPTimedelta) and isinstance(rhs,
        types.NPTimedelta)
    nbcy__knv = isinstance(lhs, types.NPDatetime) and isinstance(rhs, types
        .NPDatetime)
    unicode_types = (types.UnicodeType, types.StringLiteral, types.CharSeq,
        types.Bytes, types.UnicodeCharSeq)
    rkndm__fobo = isinstance(lhs, unicode_types) and isinstance(rhs,
        unicode_types)
    tqvf__ljutd = isinstance(lhs, types.BaseTuple) and isinstance(rhs,
        types.BaseTuple)
    bjl__bpvu = isinstance(lhs, types.Set) and isinstance(rhs, types.Set)
    vzum__qgoi = isinstance(lhs, types.Number) and isinstance(rhs, types.Number
        )
    fri__bly = isinstance(lhs, types.Boolean) and isinstance(rhs, types.Boolean
        )
    dawem__cenl = isinstance(lhs, types.NoneType) or isinstance(rhs, types.
        NoneType)
    nhx__gvfxm = isinstance(lhs, types.DictType) and isinstance(rhs, types.
        DictType)
    spp__hvjjp = isinstance(lhs, types.EnumMember) and isinstance(rhs,
        types.EnumMember)
    ebjd__ikh = isinstance(lhs, types.Literal) and isinstance(rhs, types.
        Literal)
    return (tts__kzt or dcbv__cnpd or nbcy__knv or rkndm__fobo or
        tqvf__ljutd or bjl__bpvu or vzum__qgoi or fri__bly or dawem__cenl or
        nhx__gvfxm or cmb__zinul or spp__hvjjp or ebjd__ikh)


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
        dbxqz__dfp = create_overload_cmp_operator(op)
        overload(op, no_unliteral=True)(dbxqz__dfp)


_install_cmp_ops()


def install_arith_ops():
    for op in (operator.add, operator.sub, operator.mul, operator.truediv,
        operator.floordiv, operator.mod, operator.pow):
        dbxqz__dfp = create_overload_arith_op(op)
        overload(op, no_unliteral=True)(dbxqz__dfp)


install_arith_ops()
