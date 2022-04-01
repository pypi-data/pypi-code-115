"""
Implement pd.Series typing and data model handling.
"""
import operator
import llvmlite.binding as ll
import numba
import numpy as np
import pandas as pd
from llvmlite import ir as lir
from numba.core import cgutils, types
from numba.core.imputils import impl_ret_borrowed, lower_constant
from numba.core.typing.templates import bound_function, signature
from numba.extending import infer_getattr, intrinsic, lower_builtin, lower_cast, models, overload, overload_attribute, overload_method, register_model
from numba.parfors.array_analysis import ArrayAnalysis
import bodo
from bodo.hiframes.datetime_date_ext import datetime_date_type
from bodo.hiframes.datetime_timedelta_ext import pd_timedelta_type
from bodo.hiframes.pd_timestamp_ext import pd_timestamp_type
from bodo.io import csv_cpp
from bodo.libs.int_arr_ext import IntDtype
from bodo.libs.pd_datetime_arr_ext import PandasDatetimeTZDtype
from bodo.libs.str_ext import string_type, unicode_to_utf8
from bodo.utils.templates import OverloadedKeyAttributeTemplate
from bodo.utils.transform import get_const_func_output_type
from bodo.utils.typing import BodoError, check_unsupported_args, create_unsupported_overload, dtype_to_array_type, get_overload_const_str, get_overload_const_tuple, get_udf_error_msg, get_udf_out_arr_type, is_heterogeneous_tuple_type, is_overload_constant_str, is_overload_constant_tuple, is_overload_false, is_overload_int, is_overload_none, raise_bodo_error
_csv_output_is_dir = types.ExternalFunction('csv_output_is_dir', types.int8
    (types.voidptr))
ll.add_symbol('csv_output_is_dir', csv_cpp.csv_output_is_dir)


class SeriesType(types.IterableType, types.ArrayCompatible):
    ndim = 1

    def __init__(self, dtype, data=None, index=None, name_typ=None, dist=None):
        from bodo.hiframes.pd_index_ext import RangeIndexType
        from bodo.transforms.distributed_analysis import Distribution
        data = dtype_to_array_type(dtype) if data is None else data
        dtype = dtype.dtype if isinstance(dtype, IntDtype) else dtype
        self.dtype = dtype
        self.data = data
        name_typ = types.none if name_typ is None else name_typ
        index = RangeIndexType(types.none) if index is None else index
        self.index = index
        self.name_typ = name_typ
        dist = Distribution.OneD_Var if dist is None else dist
        self.dist = dist
        super(SeriesType, self).__init__(name=
            f'series({dtype}, {data}, {index}, {name_typ}, {dist})')

    @property
    def as_array(self):
        return types.Array(types.undefined, 1, 'C')

    def copy(self, dtype=None, index=None, dist=None):
        if index is None:
            index = self.index
        if dist is None:
            dist = self.dist
        if dtype is None:
            dtype = self.dtype
            data = self.data
        else:
            data = dtype_to_array_type(dtype)
        return SeriesType(dtype, data, index, self.name_typ, dist)

    @property
    def key(self):
        return self.dtype, self.data, self.index, self.name_typ, self.dist

    def unify(self, typingctx, other):
        from bodo.transforms.distributed_analysis import Distribution
        if isinstance(other, SeriesType):
            ybfx__hcvb = (self.index if self.index == other.index else self
                .index.unify(typingctx, other.index))
            dist = Distribution(min(self.dist.value, other.dist.value))
            if other.dtype == self.dtype or not other.dtype.is_precise():
                return SeriesType(self.dtype, self.data.unify(typingctx,
                    other.data), ybfx__hcvb, dist=dist)
        return super(SeriesType, self).unify(typingctx, other)

    def can_convert_to(self, typingctx, other):
        from numba.core.typeconv import Conversion
        if (isinstance(other, SeriesType) and self.dtype == other.dtype and
            self.data == other.data and self.index == other.index and self.
            name_typ == other.name_typ and self.dist != other.dist):
            return Conversion.safe

    def is_precise(self):
        return self.dtype.is_precise()

    @property
    def iterator_type(self):
        return self.data.iterator_type

    @property
    def mangling_args(self):
        return self.__class__.__name__, (self._code,)


class HeterogeneousSeriesType(types.Type):
    ndim = 1

    def __init__(self, data=None, index=None, name_typ=None):
        from bodo.hiframes.pd_index_ext import RangeIndexType
        from bodo.transforms.distributed_analysis import Distribution
        self.data = data
        name_typ = types.none if name_typ is None else name_typ
        index = RangeIndexType(types.none) if index is None else index
        self.index = index
        self.name_typ = name_typ
        self.dist = Distribution.REP
        super(HeterogeneousSeriesType, self).__init__(name=
            f'heter_series({data}, {index}, {name_typ})')

    def copy(self, index=None, dist=None):
        from bodo.transforms.distributed_analysis import Distribution
        assert dist == Distribution.REP, 'invalid distribution for HeterogeneousSeriesType'
        if index is None:
            index = self.index.copy()
        return HeterogeneousSeriesType(self.data, index, self.name_typ)

    @property
    def key(self):
        return self.data, self.index, self.name_typ

    @property
    def mangling_args(self):
        return self.__class__.__name__, (self._code,)


@lower_builtin('getiter', SeriesType)
def series_getiter(context, builder, sig, args):
    ymghw__jqxq = get_series_payload(context, builder, sig.args[0], args[0])
    impl = context.get_function('getiter', sig.return_type(sig.args[0].data))
    return impl(builder, (ymghw__jqxq.data,))


@infer_getattr
class HeterSeriesAttribute(OverloadedKeyAttributeTemplate):
    key = HeterogeneousSeriesType

    def generic_resolve(self, S, attr):
        from bodo.hiframes.pd_index_ext import HeterogeneousIndexType
        if self._is_existing_attr(attr):
            return
        if isinstance(S.index, HeterogeneousIndexType
            ) and is_overload_constant_tuple(S.index.data):
            fawm__kmke = get_overload_const_tuple(S.index.data)
            if attr in fawm__kmke:
                qides__sedr = fawm__kmke.index(attr)
                return S.data[qides__sedr]


def is_str_series_typ(t):
    return isinstance(t, SeriesType) and t.dtype == string_type


def is_dt64_series_typ(t):
    return isinstance(t, SeriesType) and (t.dtype == types.NPDatetime('ns') or
        isinstance(t.dtype, PandasDatetimeTZDtype))


def is_timedelta64_series_typ(t):
    return isinstance(t, SeriesType) and t.dtype == types.NPTimedelta('ns')


def is_datetime_date_series_typ(t):
    return isinstance(t, SeriesType) and t.dtype == datetime_date_type


class SeriesPayloadType(types.Type):

    def __init__(self, series_type):
        self.series_type = series_type
        super(SeriesPayloadType, self).__init__(name=
            f'SeriesPayloadType({series_type})')

    @property
    def mangling_args(self):
        return self.__class__.__name__, (self._code,)


@register_model(SeriesPayloadType)
class SeriesPayloadModel(models.StructModel):

    def __init__(self, dmm, fe_type):
        iaaat__kmw = [('data', fe_type.series_type.data), ('index', fe_type
            .series_type.index), ('name', fe_type.series_type.name_typ)]
        super(SeriesPayloadModel, self).__init__(dmm, fe_type, iaaat__kmw)


@register_model(HeterogeneousSeriesType)
@register_model(SeriesType)
class SeriesModel(models.StructModel):

    def __init__(self, dmm, fe_type):
        payload_type = SeriesPayloadType(fe_type)
        iaaat__kmw = [('meminfo', types.MemInfoPointer(payload_type)), (
            'parent', types.pyobject)]
        super(SeriesModel, self).__init__(dmm, fe_type, iaaat__kmw)


def define_series_dtor(context, builder, series_type, payload_type):
    bqx__jmozm = builder.module
    zono__tqb = lir.FunctionType(lir.VoidType(), [cgutils.voidptr_t])
    qbzye__rnw = cgutils.get_or_insert_function(bqx__jmozm, zono__tqb, name
        ='.dtor.series.{}'.format(series_type))
    if not qbzye__rnw.is_declaration:
        return qbzye__rnw
    qbzye__rnw.linkage = 'linkonce_odr'
    builder = lir.IRBuilder(qbzye__rnw.append_basic_block())
    qrd__zbzfr = qbzye__rnw.args[0]
    jzq__cnu = context.get_value_type(payload_type).as_pointer()
    dia__fix = builder.bitcast(qrd__zbzfr, jzq__cnu)
    nibpk__iwpr = context.make_helper(builder, payload_type, ref=dia__fix)
    context.nrt.decref(builder, series_type.data, nibpk__iwpr.data)
    context.nrt.decref(builder, series_type.index, nibpk__iwpr.index)
    context.nrt.decref(builder, series_type.name_typ, nibpk__iwpr.name)
    builder.ret_void()
    return qbzye__rnw


def construct_series(context, builder, series_type, data_val, index_val,
    name_val):
    payload_type = SeriesPayloadType(series_type)
    ymghw__jqxq = cgutils.create_struct_proxy(payload_type)(context, builder)
    ymghw__jqxq.data = data_val
    ymghw__jqxq.index = index_val
    ymghw__jqxq.name = name_val
    ukc__ivjz = context.get_value_type(payload_type)
    wzigs__wht = context.get_abi_sizeof(ukc__ivjz)
    mbf__ujew = define_series_dtor(context, builder, series_type, payload_type)
    iflzf__cpqht = context.nrt.meminfo_alloc_dtor(builder, context.
        get_constant(types.uintp, wzigs__wht), mbf__ujew)
    ict__kqg = context.nrt.meminfo_data(builder, iflzf__cpqht)
    yehk__zpv = builder.bitcast(ict__kqg, ukc__ivjz.as_pointer())
    builder.store(ymghw__jqxq._getvalue(), yehk__zpv)
    series = cgutils.create_struct_proxy(series_type)(context, builder)
    series.meminfo = iflzf__cpqht
    series.parent = cgutils.get_null_value(series.parent.type)
    return series._getvalue()


@intrinsic
def init_series(typingctx, data, index, name=None):
    from bodo.hiframes.pd_index_ext import is_pd_index_type
    from bodo.hiframes.pd_multi_index_ext import MultiIndexType
    assert is_pd_index_type(index) or isinstance(index, MultiIndexType)
    name = types.none if name is None else name

    def codegen(context, builder, signature, args):
        data_val, index_val, name_val = args
        series_type = signature.return_type
        mhzm__zua = construct_series(context, builder, series_type,
            data_val, index_val, name_val)
        context.nrt.incref(builder, signature.args[0], data_val)
        context.nrt.incref(builder, signature.args[1], index_val)
        context.nrt.incref(builder, signature.args[2], name_val)
        return mhzm__zua
    if is_heterogeneous_tuple_type(data):
        bpvmk__uog = HeterogeneousSeriesType(data, index, name)
    else:
        dtype = data.dtype
        data = if_series_to_array_type(data)
        bpvmk__uog = SeriesType(dtype, data, index, name)
    sig = signature(bpvmk__uog, data, index, name)
    return sig, codegen


def init_series_equiv(self, scope, equiv_set, loc, args, kws):
    from bodo.hiframes.pd_index_ext import HeterogeneousIndexType
    assert len(args) >= 2 and not kws
    data = args[0]
    index = args[1]
    mva__yuuot = self.typemap[data.name]
    if is_heterogeneous_tuple_type(mva__yuuot) or isinstance(mva__yuuot,
        types.BaseTuple):
        return None
    inc__blqm = self.typemap[index.name]
    if not isinstance(inc__blqm, HeterogeneousIndexType
        ) and equiv_set.has_shape(data) and equiv_set.has_shape(index):
        equiv_set.insert_equiv(data, index)
    if equiv_set.has_shape(data):
        return ArrayAnalysis.AnalyzeResult(shape=data, pre=[])
    return None


ArrayAnalysis._analyze_op_call_bodo_hiframes_pd_series_ext_init_series = (
    init_series_equiv)


def get_series_payload(context, builder, series_type, value):
    iflzf__cpqht = cgutils.create_struct_proxy(series_type)(context,
        builder, value).meminfo
    payload_type = SeriesPayloadType(series_type)
    nibpk__iwpr = context.nrt.meminfo_data(builder, iflzf__cpqht)
    jzq__cnu = context.get_value_type(payload_type).as_pointer()
    nibpk__iwpr = builder.bitcast(nibpk__iwpr, jzq__cnu)
    return context.make_helper(builder, payload_type, ref=nibpk__iwpr)


@intrinsic
def get_series_data(typingctx, series_typ=None):

    def codegen(context, builder, signature, args):
        ymghw__jqxq = get_series_payload(context, builder, signature.args[0
            ], args[0])
        return impl_ret_borrowed(context, builder, series_typ.data,
            ymghw__jqxq.data)
    bpvmk__uog = series_typ.data
    sig = signature(bpvmk__uog, series_typ)
    return sig, codegen


@intrinsic
def get_series_index(typingctx, series_typ=None):

    def codegen(context, builder, signature, args):
        ymghw__jqxq = get_series_payload(context, builder, signature.args[0
            ], args[0])
        return impl_ret_borrowed(context, builder, series_typ.index,
            ymghw__jqxq.index)
    bpvmk__uog = series_typ.index
    sig = signature(bpvmk__uog, series_typ)
    return sig, codegen


@intrinsic
def get_series_name(typingctx, series_typ=None):

    def codegen(context, builder, signature, args):
        ymghw__jqxq = get_series_payload(context, builder, signature.args[0
            ], args[0])
        return impl_ret_borrowed(context, builder, signature.return_type,
            ymghw__jqxq.name)
    sig = signature(series_typ.name_typ, series_typ)
    return sig, codegen


def get_series_data_equiv(self, scope, equiv_set, loc, args, kws):
    assert len(args) == 1 and not kws
    kqpvl__hoxn = args[0]
    mva__yuuot = self.typemap[kqpvl__hoxn.name].data
    if is_heterogeneous_tuple_type(mva__yuuot) or isinstance(mva__yuuot,
        types.BaseTuple):
        return None
    if equiv_set.has_shape(kqpvl__hoxn):
        return ArrayAnalysis.AnalyzeResult(shape=kqpvl__hoxn, pre=[])
    return None


(ArrayAnalysis._analyze_op_call_bodo_hiframes_pd_series_ext_get_series_data
    ) = get_series_data_equiv


def get_series_index_equiv(self, scope, equiv_set, loc, args, kws):
    from bodo.hiframes.pd_index_ext import HeterogeneousIndexType
    assert len(args) == 1 and not kws
    kqpvl__hoxn = args[0]
    inc__blqm = self.typemap[kqpvl__hoxn.name].index
    if isinstance(inc__blqm, HeterogeneousIndexType):
        return None
    if equiv_set.has_shape(kqpvl__hoxn):
        return ArrayAnalysis.AnalyzeResult(shape=kqpvl__hoxn, pre=[])
    return None


(ArrayAnalysis._analyze_op_call_bodo_hiframes_pd_series_ext_get_series_index
    ) = get_series_index_equiv


def alias_ext_init_series(lhs_name, args, alias_map, arg_aliases):
    assert len(args) >= 1
    numba.core.ir_utils._add_alias(lhs_name, args[0].name, alias_map,
        arg_aliases)
    if len(args) > 1:
        numba.core.ir_utils._add_alias(lhs_name, args[1].name, alias_map,
            arg_aliases)


numba.core.ir_utils.alias_func_extensions['init_series',
    'bodo.hiframes.pd_series_ext'] = alias_ext_init_series


def alias_ext_dummy_func(lhs_name, args, alias_map, arg_aliases):
    assert len(args) >= 1
    numba.core.ir_utils._add_alias(lhs_name, args[0].name, alias_map,
        arg_aliases)


numba.core.ir_utils.alias_func_extensions['get_series_data',
    'bodo.hiframes.pd_series_ext'] = alias_ext_dummy_func
numba.core.ir_utils.alias_func_extensions['get_series_index',
    'bodo.hiframes.pd_series_ext'] = alias_ext_dummy_func


def is_series_type(typ):
    return isinstance(typ, SeriesType)


def if_series_to_array_type(typ):
    if isinstance(typ, SeriesType):
        return typ.data
    return typ


@lower_cast(SeriesType, SeriesType)
def cast_series(context, builder, fromty, toty, val):
    if fromty.copy(index=toty.index) == toty and isinstance(fromty.index,
        bodo.hiframes.pd_index_ext.RangeIndexType) and isinstance(toty.
        index, bodo.hiframes.pd_index_ext.NumericIndexType):
        ymghw__jqxq = get_series_payload(context, builder, fromty, val)
        ybfx__hcvb = context.cast(builder, ymghw__jqxq.index, fromty.index,
            toty.index)
        context.nrt.incref(builder, fromty.data, ymghw__jqxq.data)
        context.nrt.incref(builder, fromty.name_typ, ymghw__jqxq.name)
        return construct_series(context, builder, toty, ymghw__jqxq.data,
            ybfx__hcvb, ymghw__jqxq.name)
    if (fromty.dtype == toty.dtype and fromty.data == toty.data and fromty.
        index == toty.index and fromty.name_typ == toty.name_typ and fromty
        .dist != toty.dist):
        return val
    return val


@infer_getattr
class SeriesAttribute(OverloadedKeyAttributeTemplate):
    key = SeriesType

    @bound_function('series.head')
    def resolve_head(self, ary, args, kws):
        unt__vhtpu = 'Series.head'
        espua__lisc = 'n',
        fimd__liv = {'n': 5}
        pysig, xxke__mok = bodo.utils.typing.fold_typing_args(unt__vhtpu,
            args, kws, espua__lisc, fimd__liv)
        kjppk__xifd = xxke__mok[0]
        if not is_overload_int(kjppk__xifd):
            raise BodoError(f"{unt__vhtpu}(): 'n' must be an Integer")
        ablk__xxs = ary
        return ablk__xxs(*xxke__mok).replace(pysig=pysig)

    def _resolve_map_func(self, ary, func, pysig, fname, f_args=None, kws=None
        ):
        dtype = ary.dtype
        bodo.hiframes.pd_timestamp_ext.check_tz_aware_unsupported(ary,
            'Series.map()')
        if dtype == types.NPDatetime('ns'):
            dtype = pd_timestamp_type
        if dtype == types.NPTimedelta('ns'):
            dtype = pd_timedelta_type
        dvo__wje = dtype,
        if f_args is not None:
            dvo__wje += tuple(f_args.types)
        if kws is None:
            kws = {}
        rmxsi__xwwh = False
        xuh__safb = True
        if fname == 'map' and isinstance(func, types.DictType):
            ogi__fqom = func.value_type
            rmxsi__xwwh = True
        else:
            try:
                if types.unliteral(func) == types.unicode_type:
                    if not is_overload_constant_str(func):
                        raise BodoError(
                            f'Series.apply(): string argument (for builtins) must be a compile time constant'
                            )
                    ogi__fqom = bodo.utils.transform.get_udf_str_return_type(
                        ary, get_overload_const_str(func), self.context,
                        'Series.apply')
                    xuh__safb = False
                elif bodo.utils.typing.is_numpy_ufunc(func):
                    ogi__fqom = func.get_call_type(self.context, (ary,), {}
                        ).return_type
                    xuh__safb = False
                else:
                    ogi__fqom = get_const_func_output_type(func, dvo__wje,
                        kws, self.context, numba.core.registry.cpu_target.
                        target_context)
            except Exception as fqn__dkctp:
                raise BodoError(get_udf_error_msg(f'Series.{fname}()',
                    fqn__dkctp))
        if xuh__safb:
            if isinstance(ogi__fqom, (SeriesType, HeterogeneousSeriesType)
                ) and ogi__fqom.const_info is None:
                raise BodoError(
                    'Invalid Series output in UDF (Series with constant length and constant Index value expected)'
                    )
            if isinstance(ogi__fqom, HeterogeneousSeriesType):
                yuz__tmymg, redrd__ufg = ogi__fqom.const_info
                rsyt__item = tuple(dtype_to_array_type(t) for t in
                    ogi__fqom.data.types)
                mdof__ogl = bodo.DataFrameType(rsyt__item, ary.index,
                    redrd__ufg)
            elif isinstance(ogi__fqom, SeriesType):
                qbql__qfrvz, redrd__ufg = ogi__fqom.const_info
                rsyt__item = tuple(dtype_to_array_type(ogi__fqom.dtype) for
                    yuz__tmymg in range(qbql__qfrvz))
                mdof__ogl = bodo.DataFrameType(rsyt__item, ary.index,
                    redrd__ufg)
            else:
                xazrx__iii = get_udf_out_arr_type(ogi__fqom, rmxsi__xwwh)
                mdof__ogl = SeriesType(xazrx__iii.dtype, xazrx__iii, ary.
                    index, ary.name_typ)
        else:
            mdof__ogl = ogi__fqom
        return signature(mdof__ogl, (func,)).replace(pysig=pysig)

    @bound_function('series.map', no_unliteral=True)
    def resolve_map(self, ary, args, kws):
        kws = dict(kws)
        func = args[0] if len(args) > 0 else kws['arg']
        kws.pop('arg', None)
        na_action = args[1] if len(args) > 1 else kws.pop('na_action',
            types.none)
        betcz__jirp = dict(na_action=na_action)
        flf__gwa = dict(na_action=None)
        check_unsupported_args('Series.map', betcz__jirp, flf__gwa,
            package_name='pandas', module_name='Series')

        def map_stub(arg, na_action=None):
            pass
        pysig = numba.core.utils.pysignature(map_stub)
        return self._resolve_map_func(ary, func, pysig, 'map')

    @bound_function('series.apply', no_unliteral=True)
    def resolve_apply(self, ary, args, kws):
        kws = dict(kws)
        func = args[0] if len(args) > 0 else kws['func']
        kws.pop('func', None)
        rja__wlkwb = args[1] if len(args) > 1 else kws.pop('convert_dtype',
            types.literal(True))
        f_args = args[2] if len(args) > 2 else kws.pop('args', None)
        betcz__jirp = dict(convert_dtype=rja__wlkwb)
        hvc__yfh = dict(convert_dtype=True)
        check_unsupported_args('Series.apply', betcz__jirp, hvc__yfh,
            package_name='pandas', module_name='Series')
        qbiu__qac = ', '.join("{} = ''".format(cupk__emce) for cupk__emce in
            kws.keys())
        tvwmo__aazd = (
            f'def apply_stub(func, convert_dtype=True, args=(), {qbiu__qac}):\n'
            )
        tvwmo__aazd += '    pass\n'
        zbq__vkcal = {}
        exec(tvwmo__aazd, {}, zbq__vkcal)
        yqtxg__poenr = zbq__vkcal['apply_stub']
        pysig = numba.core.utils.pysignature(yqtxg__poenr)
        return self._resolve_map_func(ary, func, pysig, 'apply', f_args, kws)

    def _resolve_combine_func(self, ary, args, kws):
        kwargs = dict(kws)
        other = args[0] if len(args) > 0 else types.unliteral(kwargs['other'])
        func = args[1] if len(args) > 1 else kwargs['func']
        fill_value = args[2] if len(args) > 2 else types.unliteral(kwargs.
            get('fill_value', types.none))

        def combine_stub(other, func, fill_value=None):
            pass
        pysig = numba.core.utils.pysignature(combine_stub)
        xpkcu__fyd = ary.dtype
        bodo.hiframes.pd_timestamp_ext.check_tz_aware_unsupported(ary,
            'Series.combine()')
        bodo.hiframes.pd_timestamp_ext.check_tz_aware_unsupported(other,
            'Series.combine()')
        if xpkcu__fyd == types.NPDatetime('ns'):
            xpkcu__fyd = pd_timestamp_type
        jhx__ffwf = other.dtype
        if jhx__ffwf == types.NPDatetime('ns'):
            jhx__ffwf = pd_timestamp_type
        ogi__fqom = get_const_func_output_type(func, (xpkcu__fyd, jhx__ffwf
            ), {}, self.context, numba.core.registry.cpu_target.target_context)
        sig = signature(SeriesType(ogi__fqom, index=ary.index, name_typ=
            types.none), (other, func, fill_value))
        return sig.replace(pysig=pysig)

    @bound_function('series.combine', no_unliteral=True)
    def resolve_combine(self, ary, args, kws):
        return self._resolve_combine_func(ary, args, kws)

    @bound_function('series.pipe', no_unliteral=True)
    def resolve_pipe(self, ary, args, kws):
        bodo.hiframes.pd_timestamp_ext.check_tz_aware_unsupported(ary,
            'Series.pipe()')
        return bodo.hiframes.pd_groupby_ext.resolve_obj_pipe(self, ary,
            args, kws, 'Series')

    def generic_resolve(self, S, attr):
        from bodo.hiframes.pd_index_ext import HeterogeneousIndexType
        if self._is_existing_attr(attr):
            return
        if isinstance(S.index, HeterogeneousIndexType
            ) and is_overload_constant_tuple(S.index.data):
            fawm__kmke = get_overload_const_tuple(S.index.data)
            if attr in fawm__kmke:
                qides__sedr = fawm__kmke.index(attr)
                return S.data[qides__sedr]


series_binary_ops = tuple(op for op in numba.core.typing.npydecl.
    NumpyRulesArrayOperator._op_map.keys() if op not in (operator.lshift,
    operator.rshift))
series_inplace_binary_ops = tuple(op for op in numba.core.typing.npydecl.
    NumpyRulesInplaceArrayOperator._op_map.keys() if op not in (operator.
    ilshift, operator.irshift, operator.itruediv))
inplace_binop_to_imm = {operator.iadd: operator.add, operator.isub:
    operator.sub, operator.imul: operator.mul, operator.ifloordiv: operator
    .floordiv, operator.imod: operator.mod, operator.ipow: operator.pow,
    operator.iand: operator.and_, operator.ior: operator.or_, operator.ixor:
    operator.xor}
series_unary_ops = operator.neg, operator.invert, operator.pos
str2str_methods = ('capitalize', 'lower', 'lstrip', 'rstrip', 'strip',
    'swapcase', 'title', 'upper')
str2bool_methods = ('isalnum', 'isalpha', 'isdigit', 'isspace', 'islower',
    'isupper', 'istitle', 'isnumeric', 'isdecimal')


@overload(pd.Series, no_unliteral=True)
def pd_series_overload(data=None, index=None, dtype=None, name=None, copy=
    False, fastpath=False):
    if not is_overload_false(fastpath):
        raise BodoError("pd.Series(): 'fastpath' argument not supported.")
    kkc__ebfs = is_overload_none(data)
    gylai__chzip = is_overload_none(index)
    sxyh__bth = is_overload_none(dtype)
    if kkc__ebfs and gylai__chzip and sxyh__bth:
        raise BodoError(
            'pd.Series() requires at least 1 of data, index, and dtype to not be none'
            )
    if is_series_type(data) and not gylai__chzip:
        raise BodoError(
            'pd.Series() does not support index value when input data is a Series'
            )
    if isinstance(data, types.DictType):
        raise_bodo_error(
            'pd.Series(): When intializing series with a dictionary, it is required that the dict has constant keys'
            )
    if is_heterogeneous_tuple_type(data) and is_overload_none(dtype):

        def impl_heter(data=None, index=None, dtype=None, name=None, copy=
            False, fastpath=False):
            ljmz__lwnl = bodo.utils.conversion.extract_index_if_none(data,
                index)
            ojrx__pymqb = bodo.utils.conversion.to_tuple(data)
            return bodo.hiframes.pd_series_ext.init_series(ojrx__pymqb,
                bodo.utils.conversion.convert_to_index(ljmz__lwnl), name)
        return impl_heter
    if kkc__ebfs:
        if sxyh__bth:

            def impl(data=None, index=None, dtype=None, name=None, copy=
                False, fastpath=False):
                eisi__aklx = bodo.utils.conversion.extract_name_if_none(data,
                    name)
                ljmz__lwnl = bodo.utils.conversion.extract_index_if_none(data,
                    index)
                numba.parfors.parfor.init_prange()
                vfqs__kixe = len(ljmz__lwnl)
                ojrx__pymqb = np.empty(vfqs__kixe, np.float64)
                for shce__wrg in numba.parfors.parfor.internal_prange(
                    vfqs__kixe):
                    bodo.libs.array_kernels.setna(ojrx__pymqb, shce__wrg)
                return bodo.hiframes.pd_series_ext.init_series(ojrx__pymqb,
                    bodo.utils.conversion.convert_to_index(ljmz__lwnl),
                    eisi__aklx)
            return impl
        if bodo.utils.conversion._is_str_dtype(dtype):
            ztmw__vqxs = bodo.string_array_type
        else:
            wwq__cexb = bodo.utils.typing.parse_dtype(dtype, 'pandas.Series')
            if isinstance(wwq__cexb, bodo.libs.int_arr_ext.IntDtype):
                ztmw__vqxs = bodo.IntegerArrayType(wwq__cexb.dtype)
            elif wwq__cexb == bodo.libs.bool_arr_ext.boolean_dtype:
                ztmw__vqxs = bodo.boolean_array
            elif isinstance(wwq__cexb, types.Number) or wwq__cexb in [bodo.
                datetime64ns, bodo.timedelta64ns]:
                ztmw__vqxs = types.Array(wwq__cexb, 1, 'C')
            else:
                raise BodoError(
                    'pd.Series with dtype: {dtype} not currently supported')
        if gylai__chzip:

            def impl(data=None, index=None, dtype=None, name=None, copy=
                False, fastpath=False):
                eisi__aklx = bodo.utils.conversion.extract_name_if_none(data,
                    name)
                ljmz__lwnl = bodo.hiframes.pd_index_ext.init_range_index(0,
                    0, 1, None)
                numba.parfors.parfor.init_prange()
                vfqs__kixe = len(ljmz__lwnl)
                ojrx__pymqb = bodo.utils.utils.alloc_type(vfqs__kixe,
                    ztmw__vqxs, (-1,))
                return bodo.hiframes.pd_series_ext.init_series(ojrx__pymqb,
                    ljmz__lwnl, eisi__aklx)
            return impl
        else:

            def impl(data=None, index=None, dtype=None, name=None, copy=
                False, fastpath=False):
                eisi__aklx = bodo.utils.conversion.extract_name_if_none(data,
                    name)
                ljmz__lwnl = bodo.utils.conversion.extract_index_if_none(data,
                    index)
                numba.parfors.parfor.init_prange()
                vfqs__kixe = len(ljmz__lwnl)
                ojrx__pymqb = bodo.utils.utils.alloc_type(vfqs__kixe,
                    ztmw__vqxs, (-1,))
                for shce__wrg in numba.parfors.parfor.internal_prange(
                    vfqs__kixe):
                    bodo.libs.array_kernels.setna(ojrx__pymqb, shce__wrg)
                return bodo.hiframes.pd_series_ext.init_series(ojrx__pymqb,
                    bodo.utils.conversion.convert_to_index(ljmz__lwnl),
                    eisi__aklx)
            return impl

    def impl(data=None, index=None, dtype=None, name=None, copy=False,
        fastpath=False):
        eisi__aklx = bodo.utils.conversion.extract_name_if_none(data, name)
        ljmz__lwnl = bodo.utils.conversion.extract_index_if_none(data, index)
        scw__mxxc = bodo.utils.conversion.coerce_to_array(data, True,
            scalar_to_arr_len=len(ljmz__lwnl))
        xdy__ryqh = bodo.utils.conversion.fix_arr_dtype(scw__mxxc, dtype,
            None, False)
        return bodo.hiframes.pd_series_ext.init_series(xdy__ryqh, bodo.
            utils.conversion.convert_to_index(ljmz__lwnl), eisi__aklx)
    return impl


@overload_method(SeriesType, 'to_csv', no_unliteral=True)
def to_csv_overload(series, path_or_buf=None, sep=',', na_rep='',
    float_format=None, columns=None, header=True, index=True, index_label=
    None, mode='w', encoding=None, compression='infer', quoting=None,
    quotechar='"', line_terminator=None, chunksize=None, date_format=None,
    doublequote=True, escapechar=None, decimal='.', errors='strict',
    _is_parallel=False):
    if not (is_overload_none(path_or_buf) or is_overload_constant_str(
        path_or_buf) or path_or_buf == string_type):
        raise BodoError(
            "Series.to_csv(): 'path_or_buf' argument should be None or string")
    if is_overload_none(path_or_buf):

        def _impl(series, path_or_buf=None, sep=',', na_rep='',
            float_format=None, columns=None, header=True, index=True,
            index_label=None, mode='w', encoding=None, compression='infer',
            quoting=None, quotechar='"', line_terminator=None, chunksize=
            None, date_format=None, doublequote=True, escapechar=None,
            decimal='.', errors='strict', _is_parallel=False):
            with numba.objmode(D='unicode_type'):
                D = series.to_csv(None, sep, na_rep, float_format, columns,
                    header, index, index_label, mode, encoding, compression,
                    quoting, quotechar, line_terminator, chunksize,
                    date_format, doublequote, escapechar, decimal, errors)
            return D
        return _impl

    def _impl(series, path_or_buf=None, sep=',', na_rep='', float_format=
        None, columns=None, header=True, index=True, index_label=None, mode
        ='w', encoding=None, compression='infer', quoting=None, quotechar=
        '"', line_terminator=None, chunksize=None, date_format=None,
        doublequote=True, escapechar=None, decimal='.', errors='strict',
        _is_parallel=False):
        if _is_parallel:
            header &= (bodo.libs.distributed_api.get_rank() == 0
                ) | _csv_output_is_dir(unicode_to_utf8(path_or_buf))
        with numba.objmode(D='unicode_type'):
            D = series.to_csv(None, sep, na_rep, float_format, columns,
                header, index, index_label, mode, encoding, compression,
                quoting, quotechar, line_terminator, chunksize, date_format,
                doublequote, escapechar, decimal, errors)
        bodo.io.fs_io.csv_write(path_or_buf, D, _is_parallel)
    return _impl


@lower_constant(SeriesType)
def lower_constant_series(context, builder, series_type, pyval):
    if isinstance(series_type.data, bodo.DatetimeArrayType):
        ndaa__enva = pyval.array
    else:
        ndaa__enva = pyval.values
    data_val = context.get_constant_generic(builder, series_type.data,
        ndaa__enva)
    index_val = context.get_constant_generic(builder, series_type.index,
        pyval.index)
    name_val = context.get_constant_generic(builder, series_type.name_typ,
        pyval.name)
    nibpk__iwpr = lir.Constant.literal_struct([data_val, index_val, name_val])
    nibpk__iwpr = cgutils.global_constant(builder, '.const.payload',
        nibpk__iwpr).bitcast(cgutils.voidptr_t)
    advp__djri = context.get_constant(types.int64, -1)
    jopfz__wjjt = context.get_constant_null(types.voidptr)
    iflzf__cpqht = lir.Constant.literal_struct([advp__djri, jopfz__wjjt,
        jopfz__wjjt, nibpk__iwpr, advp__djri])
    iflzf__cpqht = cgutils.global_constant(builder, '.const.meminfo',
        iflzf__cpqht).bitcast(cgutils.voidptr_t)
    mhzm__zua = lir.Constant.literal_struct([iflzf__cpqht, jopfz__wjjt])
    return mhzm__zua


series_unsupported_attrs = {'axes', 'array', 'flags', 'at', 'is_unique',
    'sparse', 'attrs'}
series_unsupported_methods = ('set_flags', 'convert_dtypes', 'bool',
    'to_period', 'to_timestamp', '__array__', 'get', 'at', '__iter__',
    'items', 'iteritems', 'pop', 'item', 'xs', 'combine_first', 'agg',
    'aggregate', 'transform', 'expanding', 'ewm', 'clip', 'factorize',
    'mode', 'rank', 'align', 'drop', 'droplevel', 'reindex', 'reindex_like',
    'sample', 'set_axis', 'truncate', 'add_prefix', 'add_suffix', 'filter',
    'interpolate', 'argmin', 'argmax', 'reorder_levels', 'swaplevel',
    'unstack', 'searchsorted', 'ravel', 'squeeze', 'view', 'compare',
    'update', 'asfreq', 'asof', 'resample', 'tz_convert', 'tz_localize',
    'at_time', 'between_time', 'tshift', 'slice_shift', 'plot', 'hist',
    'to_pickle', 'to_excel', 'to_xarray', 'to_hdf', 'to_sql', 'to_json',
    'to_string', 'to_clipboard', 'to_latex', 'to_markdown')


def _install_series_unsupported():
    for ryvr__kcjs in series_unsupported_attrs:
        qjil__cazqm = 'Series.' + ryvr__kcjs
        overload_attribute(SeriesType, ryvr__kcjs)(create_unsupported_overload
            (qjil__cazqm))
    for fname in series_unsupported_methods:
        qjil__cazqm = 'Series.' + fname
        overload_method(SeriesType, fname, no_unliteral=True)(
            create_unsupported_overload(qjil__cazqm))


_install_series_unsupported()
heter_series_unsupported_attrs = {'axes', 'array', 'dtype', 'nbytes',
    'memory_usage', 'hasnans', 'dtypes', 'flags', 'at', 'is_unique',
    'is_monotonic', 'is_monotonic_increasing', 'is_monotonic_decreasing',
    'dt', 'str', 'cat', 'sparse', 'attrs'}
heter_series_unsupported_methods = {'set_flags', 'astype', 'convert_dtypes',
    'infer_objects', 'copy', 'bool', 'to_numpy', 'to_period',
    'to_timestamp', 'to_list', 'tolist', '__array__', 'get', 'at', 'iat',
    'iloc', 'loc', '__iter__', 'items', 'iteritems', 'keys', 'pop', 'item',
    'xs', 'add', 'sub', 'mul', 'div', 'truediv', 'floordiv', 'mod', 'pow',
    'radd', 'rsub', 'rmul', 'rdiv', 'rtruediv', 'rfloordiv', 'rmod', 'rpow',
    'combine', 'combine_first', 'round', 'lt', 'gt', 'le', 'ge', 'ne', 'eq',
    'product', 'dot', 'apply', 'agg', 'aggregate', 'transform', 'map',
    'groupby', 'rolling', 'expanding', 'ewm', 'pipe', 'abs', 'all', 'any',
    'autocorr', 'between', 'clip', 'corr', 'count', 'cov', 'cummax',
    'cummin', 'cumprod', 'cumsum', 'describe', 'diff', 'factorize', 'kurt',
    'mad', 'max', 'mean', 'median', 'min', 'mode', 'nlargest', 'nsmallest',
    'pct_change', 'prod', 'quantile', 'rank', 'sem', 'skew', 'std', 'sum',
    'var', 'kurtosis', 'unique', 'nunique', 'value_counts', 'align', 'drop',
    'droplevel', 'drop_duplicates', 'duplicated', 'equals', 'first', 'head',
    'idxmax', 'idxmin', 'isin', 'last', 'reindex', 'reindex_like', 'rename',
    'rename_axis', 'reset_index', 'sample', 'set_axis', 'take', 'tail',
    'truncate', 'where', 'mask', 'add_prefix', 'add_suffix', 'filter',
    'backfill', 'bfill', 'dropna', 'ffill', 'fillna', 'interpolate', 'isna',
    'isnull', 'notna', 'notnull', 'pad', 'replace', 'argsort', 'argmin',
    'argmax', 'reorder_levels', 'sort_values', 'sort_index', 'swaplevel',
    'unstack', 'explode', 'searchsorted', 'ravel', 'repeat', 'squeeze',
    'view', 'append', 'compare', 'update', 'asfreq', 'asof', 'shift',
    'first_valid_index', 'last_valid_index', 'resample', 'tz_convert',
    'tz_localize', 'at_time', 'between_time', 'tshift', 'slice_shift',
    'plot', 'hist', 'to_pickle', 'to_csv', 'to_dict', 'to_excel',
    'to_frame', 'to_xarray', 'to_hdf', 'to_sql', 'to_json', 'to_string',
    'to_clipboard', 'to_latex', 'to_markdown'}


def _install_heter_series_unsupported():
    for ryvr__kcjs in heter_series_unsupported_attrs:
        qjil__cazqm = 'HeterogeneousSeries.' + ryvr__kcjs
        overload_attribute(HeterogeneousSeriesType, ryvr__kcjs)(
            create_unsupported_overload(qjil__cazqm))
    for fname in heter_series_unsupported_methods:
        qjil__cazqm = 'HeterogeneousSeries.' + fname
        overload_method(HeterogeneousSeriesType, fname, no_unliteral=True)(
            create_unsupported_overload(qjil__cazqm))


_install_heter_series_unsupported()
