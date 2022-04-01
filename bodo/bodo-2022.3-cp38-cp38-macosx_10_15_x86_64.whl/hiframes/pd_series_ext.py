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
            kwdy__yzss = (self.index if self.index == other.index else self
                .index.unify(typingctx, other.index))
            dist = Distribution(min(self.dist.value, other.dist.value))
            if other.dtype == self.dtype or not other.dtype.is_precise():
                return SeriesType(self.dtype, self.data.unify(typingctx,
                    other.data), kwdy__yzss, dist=dist)
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
    tlm__kyki = get_series_payload(context, builder, sig.args[0], args[0])
    impl = context.get_function('getiter', sig.return_type(sig.args[0].data))
    return impl(builder, (tlm__kyki.data,))


@infer_getattr
class HeterSeriesAttribute(OverloadedKeyAttributeTemplate):
    key = HeterogeneousSeriesType

    def generic_resolve(self, S, attr):
        from bodo.hiframes.pd_index_ext import HeterogeneousIndexType
        if self._is_existing_attr(attr):
            return
        if isinstance(S.index, HeterogeneousIndexType
            ) and is_overload_constant_tuple(S.index.data):
            fdmp__vxmh = get_overload_const_tuple(S.index.data)
            if attr in fdmp__vxmh:
                pzbwi__jqb = fdmp__vxmh.index(attr)
                return S.data[pzbwi__jqb]


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
        vhlnp__fpyg = [('data', fe_type.series_type.data), ('index',
            fe_type.series_type.index), ('name', fe_type.series_type.name_typ)]
        super(SeriesPayloadModel, self).__init__(dmm, fe_type, vhlnp__fpyg)


@register_model(HeterogeneousSeriesType)
@register_model(SeriesType)
class SeriesModel(models.StructModel):

    def __init__(self, dmm, fe_type):
        payload_type = SeriesPayloadType(fe_type)
        vhlnp__fpyg = [('meminfo', types.MemInfoPointer(payload_type)), (
            'parent', types.pyobject)]
        super(SeriesModel, self).__init__(dmm, fe_type, vhlnp__fpyg)


def define_series_dtor(context, builder, series_type, payload_type):
    zzt__tozr = builder.module
    erk__wpc = lir.FunctionType(lir.VoidType(), [cgutils.voidptr_t])
    rar__okor = cgutils.get_or_insert_function(zzt__tozr, erk__wpc, name=
        '.dtor.series.{}'.format(series_type))
    if not rar__okor.is_declaration:
        return rar__okor
    rar__okor.linkage = 'linkonce_odr'
    builder = lir.IRBuilder(rar__okor.append_basic_block())
    zcfog__xpnzb = rar__okor.args[0]
    wtz__sex = context.get_value_type(payload_type).as_pointer()
    qgcyy__ivyzm = builder.bitcast(zcfog__xpnzb, wtz__sex)
    jkvpg__ooo = context.make_helper(builder, payload_type, ref=qgcyy__ivyzm)
    context.nrt.decref(builder, series_type.data, jkvpg__ooo.data)
    context.nrt.decref(builder, series_type.index, jkvpg__ooo.index)
    context.nrt.decref(builder, series_type.name_typ, jkvpg__ooo.name)
    builder.ret_void()
    return rar__okor


def construct_series(context, builder, series_type, data_val, index_val,
    name_val):
    payload_type = SeriesPayloadType(series_type)
    tlm__kyki = cgutils.create_struct_proxy(payload_type)(context, builder)
    tlm__kyki.data = data_val
    tlm__kyki.index = index_val
    tlm__kyki.name = name_val
    suvw__paori = context.get_value_type(payload_type)
    rkkeh__uusl = context.get_abi_sizeof(suvw__paori)
    kshp__vcwt = define_series_dtor(context, builder, series_type, payload_type
        )
    igqic__fwj = context.nrt.meminfo_alloc_dtor(builder, context.
        get_constant(types.uintp, rkkeh__uusl), kshp__vcwt)
    ukes__hkmys = context.nrt.meminfo_data(builder, igqic__fwj)
    vifie__dwcsc = builder.bitcast(ukes__hkmys, suvw__paori.as_pointer())
    builder.store(tlm__kyki._getvalue(), vifie__dwcsc)
    series = cgutils.create_struct_proxy(series_type)(context, builder)
    series.meminfo = igqic__fwj
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
        sewp__dvwo = construct_series(context, builder, series_type,
            data_val, index_val, name_val)
        context.nrt.incref(builder, signature.args[0], data_val)
        context.nrt.incref(builder, signature.args[1], index_val)
        context.nrt.incref(builder, signature.args[2], name_val)
        return sewp__dvwo
    if is_heterogeneous_tuple_type(data):
        eups__uhu = HeterogeneousSeriesType(data, index, name)
    else:
        dtype = data.dtype
        data = if_series_to_array_type(data)
        eups__uhu = SeriesType(dtype, data, index, name)
    sig = signature(eups__uhu, data, index, name)
    return sig, codegen


def init_series_equiv(self, scope, equiv_set, loc, args, kws):
    from bodo.hiframes.pd_index_ext import HeterogeneousIndexType
    assert len(args) >= 2 and not kws
    data = args[0]
    index = args[1]
    rjlzf__qnpp = self.typemap[data.name]
    if is_heterogeneous_tuple_type(rjlzf__qnpp) or isinstance(rjlzf__qnpp,
        types.BaseTuple):
        return None
    ftxpx__kmbd = self.typemap[index.name]
    if not isinstance(ftxpx__kmbd, HeterogeneousIndexType
        ) and equiv_set.has_shape(data) and equiv_set.has_shape(index):
        equiv_set.insert_equiv(data, index)
    if equiv_set.has_shape(data):
        return ArrayAnalysis.AnalyzeResult(shape=data, pre=[])
    return None


ArrayAnalysis._analyze_op_call_bodo_hiframes_pd_series_ext_init_series = (
    init_series_equiv)


def get_series_payload(context, builder, series_type, value):
    igqic__fwj = cgutils.create_struct_proxy(series_type)(context, builder,
        value).meminfo
    payload_type = SeriesPayloadType(series_type)
    jkvpg__ooo = context.nrt.meminfo_data(builder, igqic__fwj)
    wtz__sex = context.get_value_type(payload_type).as_pointer()
    jkvpg__ooo = builder.bitcast(jkvpg__ooo, wtz__sex)
    return context.make_helper(builder, payload_type, ref=jkvpg__ooo)


@intrinsic
def get_series_data(typingctx, series_typ=None):

    def codegen(context, builder, signature, args):
        tlm__kyki = get_series_payload(context, builder, signature.args[0],
            args[0])
        return impl_ret_borrowed(context, builder, series_typ.data,
            tlm__kyki.data)
    eups__uhu = series_typ.data
    sig = signature(eups__uhu, series_typ)
    return sig, codegen


@intrinsic
def get_series_index(typingctx, series_typ=None):

    def codegen(context, builder, signature, args):
        tlm__kyki = get_series_payload(context, builder, signature.args[0],
            args[0])
        return impl_ret_borrowed(context, builder, series_typ.index,
            tlm__kyki.index)
    eups__uhu = series_typ.index
    sig = signature(eups__uhu, series_typ)
    return sig, codegen


@intrinsic
def get_series_name(typingctx, series_typ=None):

    def codegen(context, builder, signature, args):
        tlm__kyki = get_series_payload(context, builder, signature.args[0],
            args[0])
        return impl_ret_borrowed(context, builder, signature.return_type,
            tlm__kyki.name)
    sig = signature(series_typ.name_typ, series_typ)
    return sig, codegen


def get_series_data_equiv(self, scope, equiv_set, loc, args, kws):
    assert len(args) == 1 and not kws
    cuv__ymoc = args[0]
    rjlzf__qnpp = self.typemap[cuv__ymoc.name].data
    if is_heterogeneous_tuple_type(rjlzf__qnpp) or isinstance(rjlzf__qnpp,
        types.BaseTuple):
        return None
    if equiv_set.has_shape(cuv__ymoc):
        return ArrayAnalysis.AnalyzeResult(shape=cuv__ymoc, pre=[])
    return None


(ArrayAnalysis._analyze_op_call_bodo_hiframes_pd_series_ext_get_series_data
    ) = get_series_data_equiv


def get_series_index_equiv(self, scope, equiv_set, loc, args, kws):
    from bodo.hiframes.pd_index_ext import HeterogeneousIndexType
    assert len(args) == 1 and not kws
    cuv__ymoc = args[0]
    ftxpx__kmbd = self.typemap[cuv__ymoc.name].index
    if isinstance(ftxpx__kmbd, HeterogeneousIndexType):
        return None
    if equiv_set.has_shape(cuv__ymoc):
        return ArrayAnalysis.AnalyzeResult(shape=cuv__ymoc, pre=[])
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
        tlm__kyki = get_series_payload(context, builder, fromty, val)
        kwdy__yzss = context.cast(builder, tlm__kyki.index, fromty.index,
            toty.index)
        context.nrt.incref(builder, fromty.data, tlm__kyki.data)
        context.nrt.incref(builder, fromty.name_typ, tlm__kyki.name)
        return construct_series(context, builder, toty, tlm__kyki.data,
            kwdy__yzss, tlm__kyki.name)
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
        kvt__ofcx = 'Series.head'
        zhi__ruciv = 'n',
        iyqj__olkp = {'n': 5}
        pysig, alwg__vdzqh = bodo.utils.typing.fold_typing_args(kvt__ofcx,
            args, kws, zhi__ruciv, iyqj__olkp)
        tvyr__dwknz = alwg__vdzqh[0]
        if not is_overload_int(tvyr__dwknz):
            raise BodoError(f"{kvt__ofcx}(): 'n' must be an Integer")
        chvwa__joe = ary
        return chvwa__joe(*alwg__vdzqh).replace(pysig=pysig)

    def _resolve_map_func(self, ary, func, pysig, fname, f_args=None, kws=None
        ):
        dtype = ary.dtype
        bodo.hiframes.pd_timestamp_ext.check_tz_aware_unsupported(ary,
            'Series.map()')
        if dtype == types.NPDatetime('ns'):
            dtype = pd_timestamp_type
        if dtype == types.NPTimedelta('ns'):
            dtype = pd_timedelta_type
        tkaii__ktu = dtype,
        if f_args is not None:
            tkaii__ktu += tuple(f_args.types)
        if kws is None:
            kws = {}
        ubcgu__rfr = False
        oxz__cdao = True
        if fname == 'map' and isinstance(func, types.DictType):
            otky__xjmf = func.value_type
            ubcgu__rfr = True
        else:
            try:
                if types.unliteral(func) == types.unicode_type:
                    if not is_overload_constant_str(func):
                        raise BodoError(
                            f'Series.apply(): string argument (for builtins) must be a compile time constant'
                            )
                    otky__xjmf = bodo.utils.transform.get_udf_str_return_type(
                        ary, get_overload_const_str(func), self.context,
                        'Series.apply')
                    oxz__cdao = False
                elif bodo.utils.typing.is_numpy_ufunc(func):
                    otky__xjmf = func.get_call_type(self.context, (ary,), {}
                        ).return_type
                    oxz__cdao = False
                else:
                    otky__xjmf = get_const_func_output_type(func,
                        tkaii__ktu, kws, self.context, numba.core.registry.
                        cpu_target.target_context)
            except Exception as gem__zozj:
                raise BodoError(get_udf_error_msg(f'Series.{fname}()',
                    gem__zozj))
        if oxz__cdao:
            if isinstance(otky__xjmf, (SeriesType, HeterogeneousSeriesType)
                ) and otky__xjmf.const_info is None:
                raise BodoError(
                    'Invalid Series output in UDF (Series with constant length and constant Index value expected)'
                    )
            if isinstance(otky__xjmf, HeterogeneousSeriesType):
                clqpg__smgj, ksuww__fju = otky__xjmf.const_info
                ckdz__vij = tuple(dtype_to_array_type(t) for t in
                    otky__xjmf.data.types)
                dde__soijc = bodo.DataFrameType(ckdz__vij, ary.index,
                    ksuww__fju)
            elif isinstance(otky__xjmf, SeriesType):
                vdui__mnksu, ksuww__fju = otky__xjmf.const_info
                ckdz__vij = tuple(dtype_to_array_type(otky__xjmf.dtype) for
                    clqpg__smgj in range(vdui__mnksu))
                dde__soijc = bodo.DataFrameType(ckdz__vij, ary.index,
                    ksuww__fju)
            else:
                xmmhi__refcn = get_udf_out_arr_type(otky__xjmf, ubcgu__rfr)
                dde__soijc = SeriesType(xmmhi__refcn.dtype, xmmhi__refcn,
                    ary.index, ary.name_typ)
        else:
            dde__soijc = otky__xjmf
        return signature(dde__soijc, (func,)).replace(pysig=pysig)

    @bound_function('series.map', no_unliteral=True)
    def resolve_map(self, ary, args, kws):
        kws = dict(kws)
        func = args[0] if len(args) > 0 else kws['arg']
        kws.pop('arg', None)
        na_action = args[1] if len(args) > 1 else kws.pop('na_action',
            types.none)
        xoan__ojgs = dict(na_action=na_action)
        wjv__wrswh = dict(na_action=None)
        check_unsupported_args('Series.map', xoan__ojgs, wjv__wrswh,
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
        alid__owlkp = args[1] if len(args) > 1 else kws.pop('convert_dtype',
            types.literal(True))
        f_args = args[2] if len(args) > 2 else kws.pop('args', None)
        xoan__ojgs = dict(convert_dtype=alid__owlkp)
        fldug__njik = dict(convert_dtype=True)
        check_unsupported_args('Series.apply', xoan__ojgs, fldug__njik,
            package_name='pandas', module_name='Series')
        pzrf__egcph = ', '.join("{} = ''".format(fjemc__aabx) for
            fjemc__aabx in kws.keys())
        zbhdv__grwbn = (
            f'def apply_stub(func, convert_dtype=True, args=(), {pzrf__egcph}):\n'
            )
        zbhdv__grwbn += '    pass\n'
        tvx__dst = {}
        exec(zbhdv__grwbn, {}, tvx__dst)
        glx__hji = tvx__dst['apply_stub']
        pysig = numba.core.utils.pysignature(glx__hji)
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
        ved__kuoo = ary.dtype
        bodo.hiframes.pd_timestamp_ext.check_tz_aware_unsupported(ary,
            'Series.combine()')
        bodo.hiframes.pd_timestamp_ext.check_tz_aware_unsupported(other,
            'Series.combine()')
        if ved__kuoo == types.NPDatetime('ns'):
            ved__kuoo = pd_timestamp_type
        eprp__wmp = other.dtype
        if eprp__wmp == types.NPDatetime('ns'):
            eprp__wmp = pd_timestamp_type
        otky__xjmf = get_const_func_output_type(func, (ved__kuoo, eprp__wmp
            ), {}, self.context, numba.core.registry.cpu_target.target_context)
        sig = signature(SeriesType(otky__xjmf, index=ary.index, name_typ=
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
            fdmp__vxmh = get_overload_const_tuple(S.index.data)
            if attr in fdmp__vxmh:
                pzbwi__jqb = fdmp__vxmh.index(attr)
                return S.data[pzbwi__jqb]


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
    fpd__viar = is_overload_none(data)
    pvn__xiclj = is_overload_none(index)
    bdfw__syvi = is_overload_none(dtype)
    if fpd__viar and pvn__xiclj and bdfw__syvi:
        raise BodoError(
            'pd.Series() requires at least 1 of data, index, and dtype to not be none'
            )
    if is_series_type(data) and not pvn__xiclj:
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
            tkq__iazh = bodo.utils.conversion.extract_index_if_none(data, index
                )
            vgdga__bacv = bodo.utils.conversion.to_tuple(data)
            return bodo.hiframes.pd_series_ext.init_series(vgdga__bacv,
                bodo.utils.conversion.convert_to_index(tkq__iazh), name)
        return impl_heter
    if fpd__viar:
        if bdfw__syvi:

            def impl(data=None, index=None, dtype=None, name=None, copy=
                False, fastpath=False):
                opg__hbhyc = bodo.utils.conversion.extract_name_if_none(data,
                    name)
                tkq__iazh = bodo.utils.conversion.extract_index_if_none(data,
                    index)
                numba.parfors.parfor.init_prange()
                cnh__jfy = len(tkq__iazh)
                vgdga__bacv = np.empty(cnh__jfy, np.float64)
                for rnik__qppva in numba.parfors.parfor.internal_prange(
                    cnh__jfy):
                    bodo.libs.array_kernels.setna(vgdga__bacv, rnik__qppva)
                return bodo.hiframes.pd_series_ext.init_series(vgdga__bacv,
                    bodo.utils.conversion.convert_to_index(tkq__iazh),
                    opg__hbhyc)
            return impl
        if bodo.utils.conversion._is_str_dtype(dtype):
            ktom__uobk = bodo.string_array_type
        else:
            egm__dvwg = bodo.utils.typing.parse_dtype(dtype, 'pandas.Series')
            if isinstance(egm__dvwg, bodo.libs.int_arr_ext.IntDtype):
                ktom__uobk = bodo.IntegerArrayType(egm__dvwg.dtype)
            elif egm__dvwg == bodo.libs.bool_arr_ext.boolean_dtype:
                ktom__uobk = bodo.boolean_array
            elif isinstance(egm__dvwg, types.Number) or egm__dvwg in [bodo.
                datetime64ns, bodo.timedelta64ns]:
                ktom__uobk = types.Array(egm__dvwg, 1, 'C')
            else:
                raise BodoError(
                    'pd.Series with dtype: {dtype} not currently supported')
        if pvn__xiclj:

            def impl(data=None, index=None, dtype=None, name=None, copy=
                False, fastpath=False):
                opg__hbhyc = bodo.utils.conversion.extract_name_if_none(data,
                    name)
                tkq__iazh = bodo.hiframes.pd_index_ext.init_range_index(0, 
                    0, 1, None)
                numba.parfors.parfor.init_prange()
                cnh__jfy = len(tkq__iazh)
                vgdga__bacv = bodo.utils.utils.alloc_type(cnh__jfy,
                    ktom__uobk, (-1,))
                return bodo.hiframes.pd_series_ext.init_series(vgdga__bacv,
                    tkq__iazh, opg__hbhyc)
            return impl
        else:

            def impl(data=None, index=None, dtype=None, name=None, copy=
                False, fastpath=False):
                opg__hbhyc = bodo.utils.conversion.extract_name_if_none(data,
                    name)
                tkq__iazh = bodo.utils.conversion.extract_index_if_none(data,
                    index)
                numba.parfors.parfor.init_prange()
                cnh__jfy = len(tkq__iazh)
                vgdga__bacv = bodo.utils.utils.alloc_type(cnh__jfy,
                    ktom__uobk, (-1,))
                for rnik__qppva in numba.parfors.parfor.internal_prange(
                    cnh__jfy):
                    bodo.libs.array_kernels.setna(vgdga__bacv, rnik__qppva)
                return bodo.hiframes.pd_series_ext.init_series(vgdga__bacv,
                    bodo.utils.conversion.convert_to_index(tkq__iazh),
                    opg__hbhyc)
            return impl

    def impl(data=None, index=None, dtype=None, name=None, copy=False,
        fastpath=False):
        opg__hbhyc = bodo.utils.conversion.extract_name_if_none(data, name)
        tkq__iazh = bodo.utils.conversion.extract_index_if_none(data, index)
        pnep__ovql = bodo.utils.conversion.coerce_to_array(data, True,
            scalar_to_arr_len=len(tkq__iazh))
        misl__orx = bodo.utils.conversion.fix_arr_dtype(pnep__ovql, dtype,
            None, False)
        return bodo.hiframes.pd_series_ext.init_series(misl__orx, bodo.
            utils.conversion.convert_to_index(tkq__iazh), opg__hbhyc)
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
        rqbg__ciqqs = pyval.array
    else:
        rqbg__ciqqs = pyval.values
    data_val = context.get_constant_generic(builder, series_type.data,
        rqbg__ciqqs)
    index_val = context.get_constant_generic(builder, series_type.index,
        pyval.index)
    name_val = context.get_constant_generic(builder, series_type.name_typ,
        pyval.name)
    jkvpg__ooo = lir.Constant.literal_struct([data_val, index_val, name_val])
    jkvpg__ooo = cgutils.global_constant(builder, '.const.payload', jkvpg__ooo
        ).bitcast(cgutils.voidptr_t)
    ghejr__qmnd = context.get_constant(types.int64, -1)
    lnh__wlvyv = context.get_constant_null(types.voidptr)
    igqic__fwj = lir.Constant.literal_struct([ghejr__qmnd, lnh__wlvyv,
        lnh__wlvyv, jkvpg__ooo, ghejr__qmnd])
    igqic__fwj = cgutils.global_constant(builder, '.const.meminfo', igqic__fwj
        ).bitcast(cgutils.voidptr_t)
    sewp__dvwo = lir.Constant.literal_struct([igqic__fwj, lnh__wlvyv])
    return sewp__dvwo


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
    for czgl__pxg in series_unsupported_attrs:
        nbp__xrsz = 'Series.' + czgl__pxg
        overload_attribute(SeriesType, czgl__pxg)(create_unsupported_overload
            (nbp__xrsz))
    for fname in series_unsupported_methods:
        nbp__xrsz = 'Series.' + fname
        overload_method(SeriesType, fname, no_unliteral=True)(
            create_unsupported_overload(nbp__xrsz))


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
    for czgl__pxg in heter_series_unsupported_attrs:
        nbp__xrsz = 'HeterogeneousSeries.' + czgl__pxg
        overload_attribute(HeterogeneousSeriesType, czgl__pxg)(
            create_unsupported_overload(nbp__xrsz))
    for fname in heter_series_unsupported_methods:
        nbp__xrsz = 'HeterogeneousSeries.' + fname
        overload_method(HeterogeneousSeriesType, fname, no_unliteral=True)(
            create_unsupported_overload(nbp__xrsz))


_install_heter_series_unsupported()
