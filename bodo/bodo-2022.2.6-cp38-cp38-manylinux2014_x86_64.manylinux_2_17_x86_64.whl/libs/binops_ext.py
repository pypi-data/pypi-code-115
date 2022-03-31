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
        zci__koruj = lhs.data if isinstance(lhs, SeriesType) else lhs
        opzln__pqbn = rhs.data if isinstance(rhs, SeriesType) else rhs
        if zci__koruj in (bodo.pd_timestamp_type, bodo.pd_timedelta_type
            ) and opzln__pqbn.dtype in (bodo.datetime64ns, bodo.timedelta64ns):
            zci__koruj = opzln__pqbn.dtype
        elif opzln__pqbn in (bodo.pd_timestamp_type, bodo.pd_timedelta_type
            ) and zci__koruj.dtype in (bodo.datetime64ns, bodo.timedelta64ns):
            opzln__pqbn = zci__koruj.dtype
        eujs__dcq = zci__koruj, opzln__pqbn
        iff__banh = (
            f'{lhs} {numba.core.utils.OPERATORS_TO_BUILTINS[self.key]} {rhs} not supported'
            )
        try:
            zbk__wuvs = self.context.resolve_function_type(self.key,
                eujs__dcq, {}).return_type
        except Exception as owh__rrvcy:
            raise BodoError(iff__banh)
        if is_overload_bool(zbk__wuvs):
            raise BodoError(iff__banh)
        njdqt__nkwi = lhs.index if isinstance(lhs, SeriesType) else rhs.index
        hlgzc__jlt = lhs.name_typ if isinstance(lhs, SeriesType
            ) else rhs.name_typ
        asbf__exqt = types.bool_
        djsi__vhpe = SeriesType(asbf__exqt, zbk__wuvs, njdqt__nkwi, hlgzc__jlt)
        return djsi__vhpe(*args)


def series_cmp_op_lower(op):

    def lower_impl(context, builder, sig, args):
        yxulk__vlhxh = bodo.hiframes.series_impl.create_binary_op_overload(op)(
            *sig.args)
        if yxulk__vlhxh is None:
            yxulk__vlhxh = create_overload_cmp_operator(op)(*sig.args)
        return context.compile_internal(builder, yxulk__vlhxh, sig, args)
    return lower_impl


class SeriesAndOrTyper(AbstractTemplate):

    def generic(self, args, kws):
        assert len(args) == 2
        assert not kws
        lhs, rhs = args
        if not (isinstance(lhs, SeriesType) or isinstance(rhs, SeriesType)):
            return
        zci__koruj = lhs.data if isinstance(lhs, SeriesType) else lhs
        opzln__pqbn = rhs.data if isinstance(rhs, SeriesType) else rhs
        eujs__dcq = zci__koruj, opzln__pqbn
        iff__banh = (
            f'{lhs} {numba.core.utils.OPERATORS_TO_BUILTINS[self.key]} {rhs} not supported'
            )
        try:
            zbk__wuvs = self.context.resolve_function_type(self.key,
                eujs__dcq, {}).return_type
        except Exception as chqna__smc:
            raise BodoError(iff__banh)
        njdqt__nkwi = lhs.index if isinstance(lhs, SeriesType) else rhs.index
        hlgzc__jlt = lhs.name_typ if isinstance(lhs, SeriesType
            ) else rhs.name_typ
        asbf__exqt = zbk__wuvs.dtype
        djsi__vhpe = SeriesType(asbf__exqt, zbk__wuvs, njdqt__nkwi, hlgzc__jlt)
        return djsi__vhpe(*args)


def lower_series_and_or(op):

    def lower_and_or_impl(context, builder, sig, args):
        yxulk__vlhxh = bodo.hiframes.series_impl.create_binary_op_overload(op)(
            *sig.args)
        if yxulk__vlhxh is None:
            lhs, rhs = sig.args
            if isinstance(lhs, DataFrameType) or isinstance(rhs, DataFrameType
                ):
                yxulk__vlhxh = (bodo.hiframes.dataframe_impl.
                    create_binary_op_overload(op)(*sig.args))
        return context.compile_internal(builder, yxulk__vlhxh, sig, args)
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
            yxulk__vlhxh = (bodo.hiframes.datetime_timedelta_ext.
                create_cmp_op_overload(op))
            return yxulk__vlhxh(lhs, rhs)
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
            yxulk__vlhxh = (bodo.hiframes.datetime_timedelta_ext.
                pd_create_cmp_op_overload(op))
            return yxulk__vlhxh(lhs, rhs)
        if cmp_timestamp_or_date(lhs, rhs):
            return (bodo.hiframes.pd_timestamp_ext.
                create_timestamp_cmp_op_overload(op)(lhs, rhs))
        if cmp_op_supported_by_numba(lhs, rhs):
            return
        raise BodoError(
            f'{op} operator not supported for data types {lhs} and {rhs}.')
    return overload_cmp_operator


def add_dt_td_and_dt_date(lhs, rhs):
    vdh__raera = lhs == datetime_timedelta_type and rhs == datetime_date_type
    kbgfp__tfk = rhs == datetime_timedelta_type and lhs == datetime_date_type
    return vdh__raera or kbgfp__tfk


def add_timestamp(lhs, rhs):
    tzf__hfid = lhs == pd_timestamp_type and is_timedelta_type(rhs)
    oxd__hwdd = is_timedelta_type(lhs) and rhs == pd_timestamp_type
    return tzf__hfid or oxd__hwdd


def add_datetime_and_timedeltas(lhs, rhs):
    ugov__enb = [datetime_timedelta_type, pd_timedelta_type]
    eqjvc__bkj = [datetime_timedelta_type, pd_timedelta_type,
        datetime_datetime_type]
    zxo__njy = lhs in ugov__enb and rhs in ugov__enb
    zms__ztx = (lhs == datetime_datetime_type and rhs in ugov__enb or rhs ==
        datetime_datetime_type and lhs in ugov__enb)
    return zxo__njy or zms__ztx


def mul_string_arr_and_int(lhs, rhs):
    opzln__pqbn = isinstance(lhs, types.Integer) and is_str_arr_type(rhs)
    zci__koruj = is_str_arr_type(lhs) and isinstance(rhs, types.Integer)
    return opzln__pqbn or zci__koruj


def mul_timedelta_and_int(lhs, rhs):
    vdh__raera = lhs in [pd_timedelta_type, datetime_timedelta_type
        ] and isinstance(rhs, types.Integer)
    kbgfp__tfk = rhs in [pd_timedelta_type, datetime_timedelta_type
        ] and isinstance(lhs, types.Integer)
    return vdh__raera or kbgfp__tfk


def mul_date_offset_and_int(lhs, rhs):
    tnj__zin = lhs in [week_type, month_end_type, month_begin_type,
        date_offset_type] and isinstance(rhs, types.Integer)
    ivu__xphn = rhs in [week_type, month_end_type, month_begin_type,
        date_offset_type] and isinstance(lhs, types.Integer)
    return tnj__zin or ivu__xphn


def sub_offset_to_datetime_or_timestamp(lhs, rhs):
    ztv__ptj = [datetime_datetime_type, pd_timestamp_type, datetime_date_type]
    bkna__lki = [date_offset_type, month_begin_type, month_end_type, week_type]
    return rhs in bkna__lki and lhs in ztv__ptj


def sub_dt_index_and_timestamp(lhs, rhs):
    cwf__dgs = isinstance(lhs, DatetimeIndexType) and rhs == pd_timestamp_type
    gbceu__okou = isinstance(rhs, DatetimeIndexType
        ) and lhs == pd_timestamp_type
    return cwf__dgs or gbceu__okou


def sub_dt_or_td(lhs, rhs):
    givm__yblne = lhs == datetime_date_type and rhs == datetime_timedelta_type
    izn__jpl = lhs == datetime_date_type and rhs == datetime_date_type
    ttj__yih = (lhs == datetime_date_array_type and rhs ==
        datetime_timedelta_type)
    return givm__yblne or izn__jpl or ttj__yih


def sub_datetime_and_timedeltas(lhs, rhs):
    tftz__dyqqh = (is_timedelta_type(lhs) or lhs == datetime_datetime_type
        ) and is_timedelta_type(rhs)
    xdef__qnmv = (lhs == datetime_timedelta_array_type and rhs ==
        datetime_timedelta_type)
    return tftz__dyqqh or xdef__qnmv


def div_timedelta_and_int(lhs, rhs):
    zxo__njy = lhs == pd_timedelta_type and rhs == pd_timedelta_type
    cxig__bczyi = lhs == pd_timedelta_type and isinstance(rhs, types.Integer)
    return zxo__njy or cxig__bczyi


def div_datetime_timedelta(lhs, rhs):
    zxo__njy = (lhs == datetime_timedelta_type and rhs ==
        datetime_timedelta_type)
    cxig__bczyi = lhs == datetime_timedelta_type and rhs == types.int64
    return zxo__njy or cxig__bczyi


def mod_timedeltas(lhs, rhs):
    xuh__wnvjv = lhs == pd_timedelta_type and rhs == pd_timedelta_type
    oayjk__dumuc = (lhs == datetime_timedelta_type and rhs ==
        datetime_timedelta_type)
    return xuh__wnvjv or oayjk__dumuc


def cmp_dt_index_to_string(lhs, rhs):
    cwf__dgs = isinstance(lhs, DatetimeIndexType) and types.unliteral(rhs
        ) == string_type
    gbceu__okou = isinstance(rhs, DatetimeIndexType) and types.unliteral(lhs
        ) == string_type
    return cwf__dgs or gbceu__okou


def cmp_timestamp_or_date(lhs, rhs):
    qkbl__btso = (lhs == pd_timestamp_type and rhs == bodo.hiframes.
        datetime_date_ext.datetime_date_type)
    gcw__emcj = (lhs == bodo.hiframes.datetime_date_ext.datetime_date_type and
        rhs == pd_timestamp_type)
    ugban__rbc = lhs == pd_timestamp_type and rhs == pd_timestamp_type
    jkcx__qbv = lhs == pd_timestamp_type and rhs == bodo.datetime64ns
    dtykz__zajj = rhs == pd_timestamp_type and lhs == bodo.datetime64ns
    return qkbl__btso or gcw__emcj or ugban__rbc or jkcx__qbv or dtykz__zajj


def cmp_timeseries(lhs, rhs):
    anmos__nlt = bodo.hiframes.pd_series_ext.is_dt64_series_typ(rhs) and (bodo
        .utils.typing.is_overload_constant_str(lhs) or lhs == bodo.libs.
        str_ext.string_type or lhs == bodo.hiframes.pd_timestamp_ext.
        pd_timestamp_type)
    etohv__jnf = bodo.hiframes.pd_series_ext.is_dt64_series_typ(lhs) and (bodo
        .utils.typing.is_overload_constant_str(rhs) or rhs == bodo.libs.
        str_ext.string_type or rhs == bodo.hiframes.pd_timestamp_ext.
        pd_timestamp_type)
    alqmq__egqio = anmos__nlt or etohv__jnf
    hrmu__wdwm = bodo.hiframes.pd_series_ext.is_timedelta64_series_typ(rhs
        ) and lhs == bodo.hiframes.datetime_timedelta_ext.datetime_timedelta_type
    uzd__nnzs = bodo.hiframes.pd_series_ext.is_timedelta64_series_typ(lhs
        ) and rhs == bodo.hiframes.datetime_timedelta_ext.datetime_timedelta_type
    enkh__mwtzj = hrmu__wdwm or uzd__nnzs
    return alqmq__egqio or enkh__mwtzj


def cmp_timedeltas(lhs, rhs):
    zxo__njy = [pd_timedelta_type, bodo.timedelta64ns]
    return lhs in zxo__njy and rhs in zxo__njy


def operand_is_index(operand):
    return is_index_type(operand) or isinstance(operand, HeterogeneousIndexType
        )


def helper_time_series_checks(operand):
    jajv__vetc = bodo.hiframes.pd_series_ext.is_dt64_series_typ(operand
        ) or bodo.hiframes.pd_series_ext.is_timedelta64_series_typ(operand
        ) or operand in [datetime_timedelta_type, datetime_datetime_type,
        pd_timestamp_type]
    return jajv__vetc


def binary_array_cmp(lhs, rhs):
    return lhs == binary_array_type and rhs in [bytes_type, binary_array_type
        ] or lhs in [bytes_type, binary_array_type
        ] and rhs == binary_array_type


def can_cmp_date_datetime(lhs, rhs, op):
    return op in (operator.eq, operator.ne) and (lhs == datetime_date_type and
        rhs == datetime_datetime_type or lhs == datetime_datetime_type and 
        rhs == datetime_date_type)


def time_series_operation(lhs, rhs):
    ehsp__pjj = bodo.hiframes.pd_series_ext.is_timedelta64_series_typ(lhs
        ) and rhs == datetime_timedelta_type
    gejoa__rhifb = bodo.hiframes.pd_series_ext.is_timedelta64_series_typ(rhs
        ) and lhs == datetime_timedelta_type
    yry__ywenk = bodo.hiframes.pd_series_ext.is_dt64_series_typ(lhs
        ) and helper_time_series_checks(rhs)
    vpfb__wzsev = bodo.hiframes.pd_series_ext.is_dt64_series_typ(rhs
        ) and helper_time_series_checks(lhs)
    return ehsp__pjj or gejoa__rhifb or yry__ywenk or vpfb__wzsev


def args_td_and_int_array(lhs, rhs):
    aefwk__job = (isinstance(lhs, IntegerArrayType) or isinstance(lhs,
        types.Array) and isinstance(lhs.dtype, types.Integer)) or (isinstance
        (rhs, IntegerArrayType) or isinstance(rhs, types.Array) and
        isinstance(rhs.dtype, types.Integer))
    him__ksn = lhs in [pd_timedelta_type] or rhs in [pd_timedelta_type]
    return aefwk__job and him__ksn


def arith_op_supported_by_numba(op, lhs, rhs):
    if op == operator.mul:
        kbgfp__tfk = isinstance(lhs, (types.Integer, types.Float)
            ) and isinstance(rhs, types.NPTimedelta)
        vdh__raera = isinstance(rhs, (types.Integer, types.Float)
            ) and isinstance(lhs, types.NPTimedelta)
        xltb__zkl = kbgfp__tfk or vdh__raera
        jmxmc__pfcua = isinstance(rhs, types.UnicodeType) and isinstance(lhs,
            types.Integer)
        hpxs__pei = isinstance(lhs, types.UnicodeType) and isinstance(rhs,
            types.Integer)
        erg__qcy = jmxmc__pfcua or hpxs__pei
        cdupo__zci = isinstance(lhs, types.Integer) and isinstance(rhs,
            types.Integer)
        ahj__viv = isinstance(lhs, types.Float) and isinstance(rhs, types.Float
            )
        mdt__rddix = isinstance(lhs, types.Complex) and isinstance(rhs,
            types.Complex)
        jooof__cry = cdupo__zci or ahj__viv or mdt__rddix
        jty__vqlj = isinstance(lhs, types.List) and isinstance(rhs, types.
            Integer) or isinstance(lhs, types.Integer) and isinstance(rhs,
            types.List)
        tys = types.UnicodeCharSeq, types.CharSeq, types.Bytes
        pxe__ccnbj = isinstance(lhs, tys) or isinstance(rhs, tys)
        ewqa__lulx = isinstance(lhs, types.Array) or isinstance(rhs, types.
            Array)
        return (xltb__zkl or erg__qcy or jooof__cry or jty__vqlj or
            pxe__ccnbj or ewqa__lulx)
    if op == operator.pow:
        sdqo__zrkqt = isinstance(lhs, types.Integer) and isinstance(rhs, (
            types.IntegerLiteral, types.Integer))
        ads__zooab = isinstance(lhs, types.Float) and isinstance(rhs, (
            types.IntegerLiteral, types.Float, types.Integer) or rhs in
            types.unsigned_domain or rhs in types.signed_domain)
        mdt__rddix = isinstance(lhs, types.Complex) and isinstance(rhs,
            types.Complex)
        ewqa__lulx = isinstance(lhs, types.Array) or isinstance(rhs, types.
            Array)
        return sdqo__zrkqt or ads__zooab or mdt__rddix or ewqa__lulx
    if op == operator.floordiv:
        ahj__viv = lhs in types.real_domain and rhs in types.real_domain
        cdupo__zci = isinstance(lhs, types.Integer) and isinstance(rhs,
            types.Integer)
        qnz__torek = isinstance(lhs, types.Float) and isinstance(rhs, types
            .Float)
        zxo__njy = isinstance(lhs, types.NPTimedelta) and isinstance(rhs, (
            types.Integer, types.Float, types.NPTimedelta))
        ewqa__lulx = isinstance(lhs, types.Array) or isinstance(rhs, types.
            Array)
        return ahj__viv or cdupo__zci or qnz__torek or zxo__njy or ewqa__lulx
    if op == operator.truediv:
        jut__rkvdm = lhs in machine_ints and rhs in machine_ints
        ahj__viv = lhs in types.real_domain and rhs in types.real_domain
        mdt__rddix = (lhs in types.complex_domain and rhs in types.
            complex_domain)
        cdupo__zci = isinstance(lhs, types.Integer) and isinstance(rhs,
            types.Integer)
        qnz__torek = isinstance(lhs, types.Float) and isinstance(rhs, types
            .Float)
        nhzij__tvs = isinstance(lhs, types.Complex) and isinstance(rhs,
            types.Complex)
        zxo__njy = isinstance(lhs, types.NPTimedelta) and isinstance(rhs, (
            types.Integer, types.Float, types.NPTimedelta))
        ewqa__lulx = isinstance(lhs, types.Array) or isinstance(rhs, types.
            Array)
        return (jut__rkvdm or ahj__viv or mdt__rddix or cdupo__zci or
            qnz__torek or nhzij__tvs or zxo__njy or ewqa__lulx)
    if op == operator.mod:
        jut__rkvdm = lhs in machine_ints and rhs in machine_ints
        ahj__viv = lhs in types.real_domain and rhs in types.real_domain
        cdupo__zci = isinstance(lhs, types.Integer) and isinstance(rhs,
            types.Integer)
        qnz__torek = isinstance(lhs, types.Float) and isinstance(rhs, types
            .Float)
        ewqa__lulx = isinstance(lhs, types.Array) or isinstance(rhs, types.
            Array)
        return jut__rkvdm or ahj__viv or cdupo__zci or qnz__torek or ewqa__lulx
    if op == operator.add or op == operator.sub:
        xltb__zkl = isinstance(lhs, types.NPTimedelta) and isinstance(rhs,
            types.NPTimedelta)
        qlybo__tdnzs = isinstance(lhs, types.NPDatetime) and isinstance(rhs,
            types.NPDatetime)
        qshi__hko = isinstance(lhs, types.NPDatetime) and isinstance(rhs,
            types.NPTimedelta)
        pcb__xca = isinstance(lhs, types.Set) and isinstance(rhs, types.Set)
        cdupo__zci = isinstance(lhs, types.Integer) and isinstance(rhs,
            types.Integer)
        ahj__viv = isinstance(lhs, types.Float) and isinstance(rhs, types.Float
            )
        mdt__rddix = isinstance(lhs, types.Complex) and isinstance(rhs,
            types.Complex)
        jooof__cry = cdupo__zci or ahj__viv or mdt__rddix
        ewqa__lulx = isinstance(lhs, types.Array) or isinstance(rhs, types.
            Array)
        lak__csa = isinstance(lhs, types.BaseTuple) and isinstance(rhs,
            types.BaseTuple)
        jty__vqlj = isinstance(lhs, types.List) and isinstance(rhs, types.List)
        eut__cdro = isinstance(lhs, types.UnicodeCharSeq) and isinstance(rhs,
            types.UnicodeType)
        slmab__xfq = isinstance(rhs, types.UnicodeCharSeq) and isinstance(lhs,
            types.UnicodeType)
        pldyx__abyx = isinstance(lhs, types.UnicodeCharSeq) and isinstance(rhs,
            types.UnicodeCharSeq)
        afzjf__cdcmb = isinstance(lhs, (types.CharSeq, types.Bytes)
            ) and isinstance(rhs, (types.CharSeq, types.Bytes))
        qat__cmoh = eut__cdro or slmab__xfq or pldyx__abyx or afzjf__cdcmb
        erg__qcy = isinstance(lhs, types.UnicodeType) and isinstance(rhs,
            types.UnicodeType)
        ugu__etluy = isinstance(lhs, types.UnicodeType) and isinstance(rhs,
            types.UnicodeCharSeq)
        newvi__dzqxk = erg__qcy or ugu__etluy
        rxdmz__shait = lhs == types.NPTimedelta and rhs == types.NPDatetime
        xijnk__rnuai = (lak__csa or jty__vqlj or qat__cmoh or newvi__dzqxk or
            rxdmz__shait)
        yiw__ahx = op == operator.add and xijnk__rnuai
        return (xltb__zkl or qlybo__tdnzs or qshi__hko or pcb__xca or
            jooof__cry or ewqa__lulx or yiw__ahx)


def cmp_op_supported_by_numba(lhs, rhs):
    ewqa__lulx = isinstance(lhs, types.Array) or isinstance(rhs, types.Array)
    jty__vqlj = isinstance(lhs, types.ListType) and isinstance(rhs, types.
        ListType)
    xltb__zkl = isinstance(lhs, types.NPTimedelta) and isinstance(rhs,
        types.NPTimedelta)
    odqv__piva = isinstance(lhs, types.NPDatetime) and isinstance(rhs,
        types.NPDatetime)
    unicode_types = (types.UnicodeType, types.StringLiteral, types.CharSeq,
        types.Bytes, types.UnicodeCharSeq)
    erg__qcy = isinstance(lhs, unicode_types) and isinstance(rhs, unicode_types
        )
    lak__csa = isinstance(lhs, types.BaseTuple) and isinstance(rhs, types.
        BaseTuple)
    pcb__xca = isinstance(lhs, types.Set) and isinstance(rhs, types.Set)
    jooof__cry = isinstance(lhs, types.Number) and isinstance(rhs, types.Number
        )
    lvzfa__oug = isinstance(lhs, types.Boolean) and isinstance(rhs, types.
        Boolean)
    iar__ntlhk = isinstance(lhs, types.NoneType) or isinstance(rhs, types.
        NoneType)
    pkmba__eeace = isinstance(lhs, types.DictType) and isinstance(rhs,
        types.DictType)
    xzyw__jpiwt = isinstance(lhs, types.EnumMember) and isinstance(rhs,
        types.EnumMember)
    tvgj__qpqh = isinstance(lhs, types.Literal) and isinstance(rhs, types.
        Literal)
    return (jty__vqlj or xltb__zkl or odqv__piva or erg__qcy or lak__csa or
        pcb__xca or jooof__cry or lvzfa__oug or iar__ntlhk or pkmba__eeace or
        ewqa__lulx or xzyw__jpiwt or tvgj__qpqh)


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
        eemv__svht = create_overload_cmp_operator(op)
        overload(op, no_unliteral=True)(eemv__svht)


_install_cmp_ops()


def install_arith_ops():
    for op in (operator.add, operator.sub, operator.mul, operator.truediv,
        operator.floordiv, operator.mod, operator.pow):
        eemv__svht = create_overload_arith_op(op)
        overload(op, no_unliteral=True)(eemv__svht)


install_arith_ops()
