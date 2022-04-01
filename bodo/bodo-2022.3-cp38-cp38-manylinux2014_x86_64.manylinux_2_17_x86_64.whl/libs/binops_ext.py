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
        gal__kyx = lhs.data if isinstance(lhs, SeriesType) else lhs
        cffnf__cppir = rhs.data if isinstance(rhs, SeriesType) else rhs
        if gal__kyx in (bodo.pd_timestamp_type, bodo.pd_timedelta_type
            ) and cffnf__cppir.dtype in (bodo.datetime64ns, bodo.timedelta64ns
            ):
            gal__kyx = cffnf__cppir.dtype
        elif cffnf__cppir in (bodo.pd_timestamp_type, bodo.pd_timedelta_type
            ) and gal__kyx.dtype in (bodo.datetime64ns, bodo.timedelta64ns):
            cffnf__cppir = gal__kyx.dtype
        cnbln__qogaf = gal__kyx, cffnf__cppir
        lpxm__juyrj = (
            f'{lhs} {numba.core.utils.OPERATORS_TO_BUILTINS[self.key]} {rhs} not supported'
            )
        try:
            qlpcr__snlyt = self.context.resolve_function_type(self.key,
                cnbln__qogaf, {}).return_type
        except Exception as wrfqh__xpm:
            raise BodoError(lpxm__juyrj)
        if is_overload_bool(qlpcr__snlyt):
            raise BodoError(lpxm__juyrj)
        tzvmp__zsyc = lhs.index if isinstance(lhs, SeriesType) else rhs.index
        zugz__pra = lhs.name_typ if isinstance(lhs, SeriesType
            ) else rhs.name_typ
        eupy__gfenv = types.bool_
        fgcw__rbi = SeriesType(eupy__gfenv, qlpcr__snlyt, tzvmp__zsyc,
            zugz__pra)
        return fgcw__rbi(*args)


def series_cmp_op_lower(op):

    def lower_impl(context, builder, sig, args):
        fqpx__uynj = bodo.hiframes.series_impl.create_binary_op_overload(op)(*
            sig.args)
        if fqpx__uynj is None:
            fqpx__uynj = create_overload_cmp_operator(op)(*sig.args)
        return context.compile_internal(builder, fqpx__uynj, sig, args)
    return lower_impl


class SeriesAndOrTyper(AbstractTemplate):

    def generic(self, args, kws):
        assert len(args) == 2
        assert not kws
        lhs, rhs = args
        if not (isinstance(lhs, SeriesType) or isinstance(rhs, SeriesType)):
            return
        gal__kyx = lhs.data if isinstance(lhs, SeriesType) else lhs
        cffnf__cppir = rhs.data if isinstance(rhs, SeriesType) else rhs
        cnbln__qogaf = gal__kyx, cffnf__cppir
        lpxm__juyrj = (
            f'{lhs} {numba.core.utils.OPERATORS_TO_BUILTINS[self.key]} {rhs} not supported'
            )
        try:
            qlpcr__snlyt = self.context.resolve_function_type(self.key,
                cnbln__qogaf, {}).return_type
        except Exception as fmc__zyuga:
            raise BodoError(lpxm__juyrj)
        tzvmp__zsyc = lhs.index if isinstance(lhs, SeriesType) else rhs.index
        zugz__pra = lhs.name_typ if isinstance(lhs, SeriesType
            ) else rhs.name_typ
        eupy__gfenv = qlpcr__snlyt.dtype
        fgcw__rbi = SeriesType(eupy__gfenv, qlpcr__snlyt, tzvmp__zsyc,
            zugz__pra)
        return fgcw__rbi(*args)


def lower_series_and_or(op):

    def lower_and_or_impl(context, builder, sig, args):
        fqpx__uynj = bodo.hiframes.series_impl.create_binary_op_overload(op)(*
            sig.args)
        if fqpx__uynj is None:
            lhs, rhs = sig.args
            if isinstance(lhs, DataFrameType) or isinstance(rhs, DataFrameType
                ):
                fqpx__uynj = (bodo.hiframes.dataframe_impl.
                    create_binary_op_overload(op)(*sig.args))
        return context.compile_internal(builder, fqpx__uynj, sig, args)
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
            fqpx__uynj = (bodo.hiframes.datetime_timedelta_ext.
                create_cmp_op_overload(op))
            return fqpx__uynj(lhs, rhs)
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
            fqpx__uynj = (bodo.hiframes.datetime_timedelta_ext.
                pd_create_cmp_op_overload(op))
            return fqpx__uynj(lhs, rhs)
        if cmp_timestamp_or_date(lhs, rhs):
            return (bodo.hiframes.pd_timestamp_ext.
                create_timestamp_cmp_op_overload(op)(lhs, rhs))
        if cmp_op_supported_by_numba(lhs, rhs):
            return
        raise BodoError(
            f'{op} operator not supported for data types {lhs} and {rhs}.')
    return overload_cmp_operator


def add_dt_td_and_dt_date(lhs, rhs):
    ppq__mgrsc = lhs == datetime_timedelta_type and rhs == datetime_date_type
    zfmb__fpydz = rhs == datetime_timedelta_type and lhs == datetime_date_type
    return ppq__mgrsc or zfmb__fpydz


def add_timestamp(lhs, rhs):
    zknkh__sogbv = lhs == pd_timestamp_type and is_timedelta_type(rhs)
    tdn__jgt = is_timedelta_type(lhs) and rhs == pd_timestamp_type
    return zknkh__sogbv or tdn__jgt


def add_datetime_and_timedeltas(lhs, rhs):
    xtfpf__ihmok = [datetime_timedelta_type, pd_timedelta_type]
    alqz__qbvs = [datetime_timedelta_type, pd_timedelta_type,
        datetime_datetime_type]
    yvo__qxygj = lhs in xtfpf__ihmok and rhs in xtfpf__ihmok
    nviqp__alwnu = (lhs == datetime_datetime_type and rhs in xtfpf__ihmok or
        rhs == datetime_datetime_type and lhs in xtfpf__ihmok)
    return yvo__qxygj or nviqp__alwnu


def mul_string_arr_and_int(lhs, rhs):
    cffnf__cppir = isinstance(lhs, types.Integer) and is_str_arr_type(rhs)
    gal__kyx = is_str_arr_type(lhs) and isinstance(rhs, types.Integer)
    return cffnf__cppir or gal__kyx


def mul_timedelta_and_int(lhs, rhs):
    ppq__mgrsc = lhs in [pd_timedelta_type, datetime_timedelta_type
        ] and isinstance(rhs, types.Integer)
    zfmb__fpydz = rhs in [pd_timedelta_type, datetime_timedelta_type
        ] and isinstance(lhs, types.Integer)
    return ppq__mgrsc or zfmb__fpydz


def mul_date_offset_and_int(lhs, rhs):
    wmlqa__otl = lhs in [week_type, month_end_type, month_begin_type,
        date_offset_type] and isinstance(rhs, types.Integer)
    azl__ozdjy = rhs in [week_type, month_end_type, month_begin_type,
        date_offset_type] and isinstance(lhs, types.Integer)
    return wmlqa__otl or azl__ozdjy


def sub_offset_to_datetime_or_timestamp(lhs, rhs):
    edsx__joil = [datetime_datetime_type, pd_timestamp_type, datetime_date_type
        ]
    dpo__okx = [date_offset_type, month_begin_type, month_end_type, week_type]
    return rhs in dpo__okx and lhs in edsx__joil


def sub_dt_index_and_timestamp(lhs, rhs):
    yazg__ggd = isinstance(lhs, DatetimeIndexType) and rhs == pd_timestamp_type
    bcmae__qeptf = isinstance(rhs, DatetimeIndexType
        ) and lhs == pd_timestamp_type
    return yazg__ggd or bcmae__qeptf


def sub_dt_or_td(lhs, rhs):
    xbjke__teoj = lhs == datetime_date_type and rhs == datetime_timedelta_type
    tnvwe__hsew = lhs == datetime_date_type and rhs == datetime_date_type
    cgwp__rzdq = (lhs == datetime_date_array_type and rhs ==
        datetime_timedelta_type)
    return xbjke__teoj or tnvwe__hsew or cgwp__rzdq


def sub_datetime_and_timedeltas(lhs, rhs):
    fctu__gkiv = (is_timedelta_type(lhs) or lhs == datetime_datetime_type
        ) and is_timedelta_type(rhs)
    xdb__dvxnb = (lhs == datetime_timedelta_array_type and rhs ==
        datetime_timedelta_type)
    return fctu__gkiv or xdb__dvxnb


def div_timedelta_and_int(lhs, rhs):
    yvo__qxygj = lhs == pd_timedelta_type and rhs == pd_timedelta_type
    logt__fovf = lhs == pd_timedelta_type and isinstance(rhs, types.Integer)
    return yvo__qxygj or logt__fovf


def div_datetime_timedelta(lhs, rhs):
    yvo__qxygj = (lhs == datetime_timedelta_type and rhs ==
        datetime_timedelta_type)
    logt__fovf = lhs == datetime_timedelta_type and rhs == types.int64
    return yvo__qxygj or logt__fovf


def mod_timedeltas(lhs, rhs):
    sxbv__xrrl = lhs == pd_timedelta_type and rhs == pd_timedelta_type
    oftc__fyb = (lhs == datetime_timedelta_type and rhs ==
        datetime_timedelta_type)
    return sxbv__xrrl or oftc__fyb


def cmp_dt_index_to_string(lhs, rhs):
    yazg__ggd = isinstance(lhs, DatetimeIndexType) and types.unliteral(rhs
        ) == string_type
    bcmae__qeptf = isinstance(rhs, DatetimeIndexType) and types.unliteral(lhs
        ) == string_type
    return yazg__ggd or bcmae__qeptf


def cmp_timestamp_or_date(lhs, rhs):
    vudwa__xiyg = (lhs == pd_timestamp_type and rhs == bodo.hiframes.
        datetime_date_ext.datetime_date_type)
    hpyj__ynh = (lhs == bodo.hiframes.datetime_date_ext.datetime_date_type and
        rhs == pd_timestamp_type)
    qpq__axvmt = lhs == pd_timestamp_type and rhs == pd_timestamp_type
    lozqy__cqeij = lhs == pd_timestamp_type and rhs == bodo.datetime64ns
    jed__kyuvk = rhs == pd_timestamp_type and lhs == bodo.datetime64ns
    return vudwa__xiyg or hpyj__ynh or qpq__axvmt or lozqy__cqeij or jed__kyuvk


def cmp_timeseries(lhs, rhs):
    awjlf__hccdm = bodo.hiframes.pd_series_ext.is_dt64_series_typ(rhs) and (
        bodo.utils.typing.is_overload_constant_str(lhs) or lhs == bodo.libs
        .str_ext.string_type or lhs == bodo.hiframes.pd_timestamp_ext.
        pd_timestamp_type)
    qiax__reggy = bodo.hiframes.pd_series_ext.is_dt64_series_typ(lhs) and (bodo
        .utils.typing.is_overload_constant_str(rhs) or rhs == bodo.libs.
        str_ext.string_type or rhs == bodo.hiframes.pd_timestamp_ext.
        pd_timestamp_type)
    mdqcw__rxq = awjlf__hccdm or qiax__reggy
    pwxy__ytsl = bodo.hiframes.pd_series_ext.is_timedelta64_series_typ(rhs
        ) and lhs == bodo.hiframes.datetime_timedelta_ext.datetime_timedelta_type
    erd__zddz = bodo.hiframes.pd_series_ext.is_timedelta64_series_typ(lhs
        ) and rhs == bodo.hiframes.datetime_timedelta_ext.datetime_timedelta_type
    bkpf__rhda = pwxy__ytsl or erd__zddz
    return mdqcw__rxq or bkpf__rhda


def cmp_timedeltas(lhs, rhs):
    yvo__qxygj = [pd_timedelta_type, bodo.timedelta64ns]
    return lhs in yvo__qxygj and rhs in yvo__qxygj


def operand_is_index(operand):
    return is_index_type(operand) or isinstance(operand, HeterogeneousIndexType
        )


def helper_time_series_checks(operand):
    hnm__mxeh = bodo.hiframes.pd_series_ext.is_dt64_series_typ(operand
        ) or bodo.hiframes.pd_series_ext.is_timedelta64_series_typ(operand
        ) or operand in [datetime_timedelta_type, datetime_datetime_type,
        pd_timestamp_type]
    return hnm__mxeh


def binary_array_cmp(lhs, rhs):
    return lhs == binary_array_type and rhs in [bytes_type, binary_array_type
        ] or lhs in [bytes_type, binary_array_type
        ] and rhs == binary_array_type


def can_cmp_date_datetime(lhs, rhs, op):
    return op in (operator.eq, operator.ne) and (lhs == datetime_date_type and
        rhs == datetime_datetime_type or lhs == datetime_datetime_type and 
        rhs == datetime_date_type)


def time_series_operation(lhs, rhs):
    iqg__plp = bodo.hiframes.pd_series_ext.is_timedelta64_series_typ(lhs
        ) and rhs == datetime_timedelta_type
    nhyf__burc = bodo.hiframes.pd_series_ext.is_timedelta64_series_typ(rhs
        ) and lhs == datetime_timedelta_type
    tbcze__tgx = bodo.hiframes.pd_series_ext.is_dt64_series_typ(lhs
        ) and helper_time_series_checks(rhs)
    vhxia__lxnm = bodo.hiframes.pd_series_ext.is_dt64_series_typ(rhs
        ) and helper_time_series_checks(lhs)
    return iqg__plp or nhyf__burc or tbcze__tgx or vhxia__lxnm


def args_td_and_int_array(lhs, rhs):
    jfd__ewi = (isinstance(lhs, IntegerArrayType) or isinstance(lhs, types.
        Array) and isinstance(lhs.dtype, types.Integer)) or (isinstance(rhs,
        IntegerArrayType) or isinstance(rhs, types.Array) and isinstance(
        rhs.dtype, types.Integer))
    rlx__kakj = lhs in [pd_timedelta_type] or rhs in [pd_timedelta_type]
    return jfd__ewi and rlx__kakj


def arith_op_supported_by_numba(op, lhs, rhs):
    if op == operator.mul:
        zfmb__fpydz = isinstance(lhs, (types.Integer, types.Float)
            ) and isinstance(rhs, types.NPTimedelta)
        ppq__mgrsc = isinstance(rhs, (types.Integer, types.Float)
            ) and isinstance(lhs, types.NPTimedelta)
        ubv__rlxma = zfmb__fpydz or ppq__mgrsc
        xylvd__sbyom = isinstance(rhs, types.UnicodeType) and isinstance(lhs,
            types.Integer)
        mksr__sstdj = isinstance(lhs, types.UnicodeType) and isinstance(rhs,
            types.Integer)
        epbmd__vbe = xylvd__sbyom or mksr__sstdj
        uuq__qbvv = isinstance(lhs, types.Integer) and isinstance(rhs,
            types.Integer)
        csx__msgn = isinstance(lhs, types.Float) and isinstance(rhs, types.
            Float)
        xkr__tlnwm = isinstance(lhs, types.Complex) and isinstance(rhs,
            types.Complex)
        tig__ctvs = uuq__qbvv or csx__msgn or xkr__tlnwm
        cckq__zgllr = isinstance(lhs, types.List) and isinstance(rhs, types
            .Integer) or isinstance(lhs, types.Integer) and isinstance(rhs,
            types.List)
        tys = types.UnicodeCharSeq, types.CharSeq, types.Bytes
        lwda__uvgm = isinstance(lhs, tys) or isinstance(rhs, tys)
        njtj__wlzs = isinstance(lhs, types.Array) or isinstance(rhs, types.
            Array)
        return (ubv__rlxma or epbmd__vbe or tig__ctvs or cckq__zgllr or
            lwda__uvgm or njtj__wlzs)
    if op == operator.pow:
        vnsul__qcges = isinstance(lhs, types.Integer) and isinstance(rhs, (
            types.IntegerLiteral, types.Integer))
        sqwk__ccts = isinstance(lhs, types.Float) and isinstance(rhs, (
            types.IntegerLiteral, types.Float, types.Integer) or rhs in
            types.unsigned_domain or rhs in types.signed_domain)
        xkr__tlnwm = isinstance(lhs, types.Complex) and isinstance(rhs,
            types.Complex)
        njtj__wlzs = isinstance(lhs, types.Array) or isinstance(rhs, types.
            Array)
        return vnsul__qcges or sqwk__ccts or xkr__tlnwm or njtj__wlzs
    if op == operator.floordiv:
        csx__msgn = lhs in types.real_domain and rhs in types.real_domain
        uuq__qbvv = isinstance(lhs, types.Integer) and isinstance(rhs,
            types.Integer)
        fga__lystv = isinstance(lhs, types.Float) and isinstance(rhs, types
            .Float)
        yvo__qxygj = isinstance(lhs, types.NPTimedelta) and isinstance(rhs,
            (types.Integer, types.Float, types.NPTimedelta))
        njtj__wlzs = isinstance(lhs, types.Array) or isinstance(rhs, types.
            Array)
        return csx__msgn or uuq__qbvv or fga__lystv or yvo__qxygj or njtj__wlzs
    if op == operator.truediv:
        eanb__bmay = lhs in machine_ints and rhs in machine_ints
        csx__msgn = lhs in types.real_domain and rhs in types.real_domain
        xkr__tlnwm = (lhs in types.complex_domain and rhs in types.
            complex_domain)
        uuq__qbvv = isinstance(lhs, types.Integer) and isinstance(rhs,
            types.Integer)
        fga__lystv = isinstance(lhs, types.Float) and isinstance(rhs, types
            .Float)
        xkxx__uew = isinstance(lhs, types.Complex) and isinstance(rhs,
            types.Complex)
        yvo__qxygj = isinstance(lhs, types.NPTimedelta) and isinstance(rhs,
            (types.Integer, types.Float, types.NPTimedelta))
        njtj__wlzs = isinstance(lhs, types.Array) or isinstance(rhs, types.
            Array)
        return (eanb__bmay or csx__msgn or xkr__tlnwm or uuq__qbvv or
            fga__lystv or xkxx__uew or yvo__qxygj or njtj__wlzs)
    if op == operator.mod:
        eanb__bmay = lhs in machine_ints and rhs in machine_ints
        csx__msgn = lhs in types.real_domain and rhs in types.real_domain
        uuq__qbvv = isinstance(lhs, types.Integer) and isinstance(rhs,
            types.Integer)
        fga__lystv = isinstance(lhs, types.Float) and isinstance(rhs, types
            .Float)
        njtj__wlzs = isinstance(lhs, types.Array) or isinstance(rhs, types.
            Array)
        return eanb__bmay or csx__msgn or uuq__qbvv or fga__lystv or njtj__wlzs
    if op == operator.add or op == operator.sub:
        ubv__rlxma = isinstance(lhs, types.NPTimedelta) and isinstance(rhs,
            types.NPTimedelta)
        jsh__bdsg = isinstance(lhs, types.NPDatetime) and isinstance(rhs,
            types.NPDatetime)
        fcnhl__ohlj = isinstance(lhs, types.NPDatetime) and isinstance(rhs,
            types.NPTimedelta)
        cco__hzcko = isinstance(lhs, types.Set) and isinstance(rhs, types.Set)
        uuq__qbvv = isinstance(lhs, types.Integer) and isinstance(rhs,
            types.Integer)
        csx__msgn = isinstance(lhs, types.Float) and isinstance(rhs, types.
            Float)
        xkr__tlnwm = isinstance(lhs, types.Complex) and isinstance(rhs,
            types.Complex)
        tig__ctvs = uuq__qbvv or csx__msgn or xkr__tlnwm
        njtj__wlzs = isinstance(lhs, types.Array) or isinstance(rhs, types.
            Array)
        wgfk__emaci = isinstance(lhs, types.BaseTuple) and isinstance(rhs,
            types.BaseTuple)
        cckq__zgllr = isinstance(lhs, types.List) and isinstance(rhs, types
            .List)
        bxpq__pthx = isinstance(lhs, types.UnicodeCharSeq) and isinstance(rhs,
            types.UnicodeType)
        koqq__uvn = isinstance(rhs, types.UnicodeCharSeq) and isinstance(lhs,
            types.UnicodeType)
        ulwas__akc = isinstance(lhs, types.UnicodeCharSeq) and isinstance(rhs,
            types.UnicodeCharSeq)
        uypnk__rzcmq = isinstance(lhs, (types.CharSeq, types.Bytes)
            ) and isinstance(rhs, (types.CharSeq, types.Bytes))
        clb__oxj = bxpq__pthx or koqq__uvn or ulwas__akc or uypnk__rzcmq
        epbmd__vbe = isinstance(lhs, types.UnicodeType) and isinstance(rhs,
            types.UnicodeType)
        loyb__srsvc = isinstance(lhs, types.UnicodeType) and isinstance(rhs,
            types.UnicodeCharSeq)
        dqubi__ana = epbmd__vbe or loyb__srsvc
        vocm__dlnbl = lhs == types.NPTimedelta and rhs == types.NPDatetime
        pgg__egr = (wgfk__emaci or cckq__zgllr or clb__oxj or dqubi__ana or
            vocm__dlnbl)
        uxe__avp = op == operator.add and pgg__egr
        return (ubv__rlxma or jsh__bdsg or fcnhl__ohlj or cco__hzcko or
            tig__ctvs or njtj__wlzs or uxe__avp)


def cmp_op_supported_by_numba(lhs, rhs):
    njtj__wlzs = isinstance(lhs, types.Array) or isinstance(rhs, types.Array)
    cckq__zgllr = isinstance(lhs, types.ListType) and isinstance(rhs, types
        .ListType)
    ubv__rlxma = isinstance(lhs, types.NPTimedelta) and isinstance(rhs,
        types.NPTimedelta)
    imm__ufu = isinstance(lhs, types.NPDatetime) and isinstance(rhs, types.
        NPDatetime)
    unicode_types = (types.UnicodeType, types.StringLiteral, types.CharSeq,
        types.Bytes, types.UnicodeCharSeq)
    epbmd__vbe = isinstance(lhs, unicode_types) and isinstance(rhs,
        unicode_types)
    wgfk__emaci = isinstance(lhs, types.BaseTuple) and isinstance(rhs,
        types.BaseTuple)
    cco__hzcko = isinstance(lhs, types.Set) and isinstance(rhs, types.Set)
    tig__ctvs = isinstance(lhs, types.Number) and isinstance(rhs, types.Number)
    vvehz__tsh = isinstance(lhs, types.Boolean) and isinstance(rhs, types.
        Boolean)
    mjmnm__fvnu = isinstance(lhs, types.NoneType) or isinstance(rhs, types.
        NoneType)
    dfyxg__sie = isinstance(lhs, types.DictType) and isinstance(rhs, types.
        DictType)
    rce__wiri = isinstance(lhs, types.EnumMember) and isinstance(rhs, types
        .EnumMember)
    odoh__vxp = isinstance(lhs, types.Literal) and isinstance(rhs, types.
        Literal)
    return (cckq__zgllr or ubv__rlxma or imm__ufu or epbmd__vbe or
        wgfk__emaci or cco__hzcko or tig__ctvs or vvehz__tsh or mjmnm__fvnu or
        dfyxg__sie or njtj__wlzs or rce__wiri or odoh__vxp)


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
        ttnpg__xry = create_overload_cmp_operator(op)
        overload(op, no_unliteral=True)(ttnpg__xry)


_install_cmp_ops()


def install_arith_ops():
    for op in (operator.add, operator.sub, operator.mul, operator.truediv,
        operator.floordiv, operator.mod, operator.pow):
        ttnpg__xry = create_overload_arith_op(op)
        overload(op, no_unliteral=True)(ttnpg__xry)


install_arith_ops()
