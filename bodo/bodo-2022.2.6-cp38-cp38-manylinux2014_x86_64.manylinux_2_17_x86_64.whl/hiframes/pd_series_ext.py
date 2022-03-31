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
from bodo.libs.pd_datetime_arr_ext import PandasDatetimeTZDtype
from bodo.io import csv_cpp
from bodo.libs.int_arr_ext import IntDtype
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
            vrvwc__gnjlw = (self.index if self.index == other.index else
                self.index.unify(typingctx, other.index))
            dist = Distribution(min(self.dist.value, other.dist.value))
            if other.dtype == self.dtype or not other.dtype.is_precise():
                return SeriesType(self.dtype, self.data.unify(typingctx,
                    other.data), vrvwc__gnjlw, dist=dist)
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
    cxps__xkb = get_series_payload(context, builder, sig.args[0], args[0])
    impl = context.get_function('getiter', sig.return_type(sig.args[0].data))
    return impl(builder, (cxps__xkb.data,))


@infer_getattr
class HeterSeriesAttribute(OverloadedKeyAttributeTemplate):
    key = HeterogeneousSeriesType

    def generic_resolve(self, S, attr):
        from bodo.hiframes.pd_index_ext import HeterogeneousIndexType
        if self._is_existing_attr(attr):
            return
        if isinstance(S.index, HeterogeneousIndexType
            ) and is_overload_constant_tuple(S.index.data):
            jgskc__qvx = get_overload_const_tuple(S.index.data)
            if attr in jgskc__qvx:
                xcz__jgxc = jgskc__qvx.index(attr)
                return S.data[xcz__jgxc]


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
        zflv__sovx = [('data', fe_type.series_type.data), ('index', fe_type
            .series_type.index), ('name', fe_type.series_type.name_typ)]
        super(SeriesPayloadModel, self).__init__(dmm, fe_type, zflv__sovx)


@register_model(HeterogeneousSeriesType)
@register_model(SeriesType)
class SeriesModel(models.StructModel):

    def __init__(self, dmm, fe_type):
        payload_type = SeriesPayloadType(fe_type)
        zflv__sovx = [('meminfo', types.MemInfoPointer(payload_type)), (
            'parent', types.pyobject)]
        super(SeriesModel, self).__init__(dmm, fe_type, zflv__sovx)


def define_series_dtor(context, builder, series_type, payload_type):
    rwai__ois = builder.module
    uywka__weuv = lir.FunctionType(lir.VoidType(), [cgutils.voidptr_t])
    wnc__isd = cgutils.get_or_insert_function(rwai__ois, uywka__weuv, name=
        '.dtor.series.{}'.format(series_type))
    if not wnc__isd.is_declaration:
        return wnc__isd
    wnc__isd.linkage = 'linkonce_odr'
    builder = lir.IRBuilder(wnc__isd.append_basic_block())
    ndhff__ggde = wnc__isd.args[0]
    crsx__ysgzu = context.get_value_type(payload_type).as_pointer()
    jltsi__eetw = builder.bitcast(ndhff__ggde, crsx__ysgzu)
    qll__ctxoh = context.make_helper(builder, payload_type, ref=jltsi__eetw)
    context.nrt.decref(builder, series_type.data, qll__ctxoh.data)
    context.nrt.decref(builder, series_type.index, qll__ctxoh.index)
    context.nrt.decref(builder, series_type.name_typ, qll__ctxoh.name)
    builder.ret_void()
    return wnc__isd


def construct_series(context, builder, series_type, data_val, index_val,
    name_val):
    payload_type = SeriesPayloadType(series_type)
    cxps__xkb = cgutils.create_struct_proxy(payload_type)(context, builder)
    cxps__xkb.data = data_val
    cxps__xkb.index = index_val
    cxps__xkb.name = name_val
    mxqo__rxb = context.get_value_type(payload_type)
    oxdm__fbi = context.get_abi_sizeof(mxqo__rxb)
    cfnz__rlr = define_series_dtor(context, builder, series_type, payload_type)
    xfpct__ekcy = context.nrt.meminfo_alloc_dtor(builder, context.
        get_constant(types.uintp, oxdm__fbi), cfnz__rlr)
    gqcq__qicp = context.nrt.meminfo_data(builder, xfpct__ekcy)
    aqik__voql = builder.bitcast(gqcq__qicp, mxqo__rxb.as_pointer())
    builder.store(cxps__xkb._getvalue(), aqik__voql)
    series = cgutils.create_struct_proxy(series_type)(context, builder)
    series.meminfo = xfpct__ekcy
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
        iyv__pfj = construct_series(context, builder, series_type, data_val,
            index_val, name_val)
        context.nrt.incref(builder, signature.args[0], data_val)
        context.nrt.incref(builder, signature.args[1], index_val)
        context.nrt.incref(builder, signature.args[2], name_val)
        return iyv__pfj
    if is_heterogeneous_tuple_type(data):
        asygf__mjd = HeterogeneousSeriesType(data, index, name)
    else:
        dtype = data.dtype
        data = if_series_to_array_type(data)
        asygf__mjd = SeriesType(dtype, data, index, name)
    sig = signature(asygf__mjd, data, index, name)
    return sig, codegen


def init_series_equiv(self, scope, equiv_set, loc, args, kws):
    from bodo.hiframes.pd_index_ext import HeterogeneousIndexType
    assert len(args) >= 2 and not kws
    data = args[0]
    index = args[1]
    cmud__cbv = self.typemap[data.name]
    if is_heterogeneous_tuple_type(cmud__cbv) or isinstance(cmud__cbv,
        types.BaseTuple):
        return None
    zzmw__fuu = self.typemap[index.name]
    if not isinstance(zzmw__fuu, HeterogeneousIndexType
        ) and equiv_set.has_shape(data) and equiv_set.has_shape(index):
        equiv_set.insert_equiv(data, index)
    if equiv_set.has_shape(data):
        return ArrayAnalysis.AnalyzeResult(shape=data, pre=[])
    return None


ArrayAnalysis._analyze_op_call_bodo_hiframes_pd_series_ext_init_series = (
    init_series_equiv)


def get_series_payload(context, builder, series_type, value):
    xfpct__ekcy = cgutils.create_struct_proxy(series_type)(context, builder,
        value).meminfo
    payload_type = SeriesPayloadType(series_type)
    qll__ctxoh = context.nrt.meminfo_data(builder, xfpct__ekcy)
    crsx__ysgzu = context.get_value_type(payload_type).as_pointer()
    qll__ctxoh = builder.bitcast(qll__ctxoh, crsx__ysgzu)
    return context.make_helper(builder, payload_type, ref=qll__ctxoh)


@intrinsic
def get_series_data(typingctx, series_typ=None):

    def codegen(context, builder, signature, args):
        cxps__xkb = get_series_payload(context, builder, signature.args[0],
            args[0])
        return impl_ret_borrowed(context, builder, series_typ.data,
            cxps__xkb.data)
    asygf__mjd = series_typ.data
    sig = signature(asygf__mjd, series_typ)
    return sig, codegen


@intrinsic
def get_series_index(typingctx, series_typ=None):

    def codegen(context, builder, signature, args):
        cxps__xkb = get_series_payload(context, builder, signature.args[0],
            args[0])
        return impl_ret_borrowed(context, builder, series_typ.index,
            cxps__xkb.index)
    asygf__mjd = series_typ.index
    sig = signature(asygf__mjd, series_typ)
    return sig, codegen


@intrinsic
def get_series_name(typingctx, series_typ=None):

    def codegen(context, builder, signature, args):
        cxps__xkb = get_series_payload(context, builder, signature.args[0],
            args[0])
        return impl_ret_borrowed(context, builder, signature.return_type,
            cxps__xkb.name)
    sig = signature(series_typ.name_typ, series_typ)
    return sig, codegen


def get_series_data_equiv(self, scope, equiv_set, loc, args, kws):
    assert len(args) == 1 and not kws
    ztvsw__wsjle = args[0]
    cmud__cbv = self.typemap[ztvsw__wsjle.name].data
    if is_heterogeneous_tuple_type(cmud__cbv) or isinstance(cmud__cbv,
        types.BaseTuple):
        return None
    if equiv_set.has_shape(ztvsw__wsjle):
        return ArrayAnalysis.AnalyzeResult(shape=ztvsw__wsjle, pre=[])
    return None


(ArrayAnalysis._analyze_op_call_bodo_hiframes_pd_series_ext_get_series_data
    ) = get_series_data_equiv


def get_series_index_equiv(self, scope, equiv_set, loc, args, kws):
    from bodo.hiframes.pd_index_ext import HeterogeneousIndexType
    assert len(args) == 1 and not kws
    ztvsw__wsjle = args[0]
    zzmw__fuu = self.typemap[ztvsw__wsjle.name].index
    if isinstance(zzmw__fuu, HeterogeneousIndexType):
        return None
    if equiv_set.has_shape(ztvsw__wsjle):
        return ArrayAnalysis.AnalyzeResult(shape=ztvsw__wsjle, pre=[])
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
        cxps__xkb = get_series_payload(context, builder, fromty, val)
        vrvwc__gnjlw = context.cast(builder, cxps__xkb.index, fromty.index,
            toty.index)
        context.nrt.incref(builder, fromty.data, cxps__xkb.data)
        context.nrt.incref(builder, fromty.name_typ, cxps__xkb.name)
        return construct_series(context, builder, toty, cxps__xkb.data,
            vrvwc__gnjlw, cxps__xkb.name)
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
        uvf__jpek = 'Series.head'
        jnozq__rogz = 'n',
        emlr__emzfa = {'n': 5}
        pysig, pmvw__duufk = bodo.utils.typing.fold_typing_args(uvf__jpek,
            args, kws, jnozq__rogz, emlr__emzfa)
        pka__vol = pmvw__duufk[0]
        if not is_overload_int(pka__vol):
            raise BodoError(f"{uvf__jpek}(): 'n' must be an Integer")
        pagi__zyl = ary
        return pagi__zyl(*pmvw__duufk).replace(pysig=pysig)

    def _resolve_map_func(self, ary, func, pysig, fname, f_args=None, kws=None
        ):
        dtype = ary.dtype
        if dtype == types.NPDatetime('ns'):
            dtype = pd_timestamp_type
        if dtype == types.NPTimedelta('ns'):
            dtype = pd_timedelta_type
        okm__tuhds = dtype,
        if f_args is not None:
            okm__tuhds += tuple(f_args.types)
        if kws is None:
            kws = {}
        ejnhk__qlgt = False
        sxhg__jsu = True
        if fname == 'map' and isinstance(func, types.DictType):
            xmj__bcyxn = func.value_type
            ejnhk__qlgt = True
        else:
            try:
                if types.unliteral(func) == types.unicode_type:
                    if not is_overload_constant_str(func):
                        raise BodoError(
                            f'Series.apply(): string argument (for builtins) must be a compile time constant'
                            )
                    xmj__bcyxn = bodo.utils.transform.get_udf_str_return_type(
                        ary, get_overload_const_str(func), self.context,
                        'Series.apply')
                    sxhg__jsu = False
                elif bodo.utils.typing.is_numpy_ufunc(func):
                    xmj__bcyxn = func.get_call_type(self.context, (ary,), {}
                        ).return_type
                    sxhg__jsu = False
                else:
                    xmj__bcyxn = get_const_func_output_type(func,
                        okm__tuhds, kws, self.context, numba.core.registry.
                        cpu_target.target_context)
            except Exception as hgkqq__imk:
                raise BodoError(get_udf_error_msg(f'Series.{fname}()',
                    hgkqq__imk))
        if sxhg__jsu:
            if isinstance(xmj__bcyxn, (SeriesType, HeterogeneousSeriesType)
                ) and xmj__bcyxn.const_info is None:
                raise BodoError(
                    'Invalid Series output in UDF (Series with constant length and constant Index value expected)'
                    )
            if isinstance(xmj__bcyxn, HeterogeneousSeriesType):
                zom__eex, vhc__idz = xmj__bcyxn.const_info
                fdqx__yeou = tuple(dtype_to_array_type(t) for t in
                    xmj__bcyxn.data.types)
                iboli__akzj = bodo.DataFrameType(fdqx__yeou, ary.index,
                    vhc__idz)
            elif isinstance(xmj__bcyxn, SeriesType):
                fje__unuo, vhc__idz = xmj__bcyxn.const_info
                fdqx__yeou = tuple(dtype_to_array_type(xmj__bcyxn.dtype) for
                    zom__eex in range(fje__unuo))
                iboli__akzj = bodo.DataFrameType(fdqx__yeou, ary.index,
                    vhc__idz)
            else:
                drzj__idov = get_udf_out_arr_type(xmj__bcyxn, ejnhk__qlgt)
                iboli__akzj = SeriesType(drzj__idov.dtype, drzj__idov, ary.
                    index, ary.name_typ)
        else:
            iboli__akzj = xmj__bcyxn
        return signature(iboli__akzj, (func,)).replace(pysig=pysig)

    @bound_function('series.map', no_unliteral=True)
    def resolve_map(self, ary, args, kws):
        kws = dict(kws)
        func = args[0] if len(args) > 0 else kws['arg']
        kws.pop('arg', None)
        na_action = args[1] if len(args) > 1 else kws.pop('na_action',
            types.none)
        ruaz__ozlre = dict(na_action=na_action)
        ubnqa__lfoe = dict(na_action=None)
        check_unsupported_args('Series.map', ruaz__ozlre, ubnqa__lfoe,
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
        vppye__fvpc = args[1] if len(args) > 1 else kws.pop('convert_dtype',
            types.literal(True))
        f_args = args[2] if len(args) > 2 else kws.pop('args', None)
        ruaz__ozlre = dict(convert_dtype=vppye__fvpc)
        baqsp__yskp = dict(convert_dtype=True)
        check_unsupported_args('Series.apply', ruaz__ozlre, baqsp__yskp,
            package_name='pandas', module_name='Series')
        cknmx__ume = ', '.join("{} = ''".format(cipoh__yvox) for
            cipoh__yvox in kws.keys())
        wxy__eju = (
            f'def apply_stub(func, convert_dtype=True, args=(), {cknmx__ume}):\n'
            )
        wxy__eju += '    pass\n'
        rjudx__iahtf = {}
        exec(wxy__eju, {}, rjudx__iahtf)
        tzk__wcdbw = rjudx__iahtf['apply_stub']
        pysig = numba.core.utils.pysignature(tzk__wcdbw)
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
        omsqt__cdkpx = ary.dtype
        if omsqt__cdkpx == types.NPDatetime('ns'):
            omsqt__cdkpx = pd_timestamp_type
        hdgd__zuy = other.dtype
        if hdgd__zuy == types.NPDatetime('ns'):
            hdgd__zuy = pd_timestamp_type
        xmj__bcyxn = get_const_func_output_type(func, (omsqt__cdkpx,
            hdgd__zuy), {}, self.context, numba.core.registry.cpu_target.
            target_context)
        sig = signature(SeriesType(xmj__bcyxn, index=ary.index, name_typ=
            types.none), (other, func, fill_value))
        return sig.replace(pysig=pysig)

    @bound_function('series.combine', no_unliteral=True)
    def resolve_combine(self, ary, args, kws):
        return self._resolve_combine_func(ary, args, kws)

    @bound_function('series.pipe', no_unliteral=True)
    def resolve_pipe(self, ary, args, kws):
        return bodo.hiframes.pd_groupby_ext.resolve_obj_pipe(self, ary,
            args, kws, 'Series')

    def generic_resolve(self, S, attr):
        from bodo.hiframes.pd_index_ext import HeterogeneousIndexType
        if self._is_existing_attr(attr):
            return
        if isinstance(S.index, HeterogeneousIndexType
            ) and is_overload_constant_tuple(S.index.data):
            jgskc__qvx = get_overload_const_tuple(S.index.data)
            if attr in jgskc__qvx:
                xcz__jgxc = jgskc__qvx.index(attr)
                return S.data[xcz__jgxc]


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
    kqh__zech = is_overload_none(data)
    iac__wwpru = is_overload_none(index)
    fyh__ybbx = is_overload_none(dtype)
    if kqh__zech and iac__wwpru and fyh__ybbx:
        raise BodoError(
            'pd.Series() requires at least 1 of data, index, and dtype to not be none'
            )
    if is_series_type(data) and not iac__wwpru:
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
            tsb__lzzw = bodo.utils.conversion.extract_index_if_none(data, index
                )
            kylnw__xsob = bodo.utils.conversion.to_tuple(data)
            return bodo.hiframes.pd_series_ext.init_series(kylnw__xsob,
                bodo.utils.conversion.convert_to_index(tsb__lzzw), name)
        return impl_heter
    if kqh__zech:
        if fyh__ybbx:

            def impl(data=None, index=None, dtype=None, name=None, copy=
                False, fastpath=False):
                evdsf__jtir = bodo.utils.conversion.extract_name_if_none(data,
                    name)
                tsb__lzzw = bodo.utils.conversion.extract_index_if_none(data,
                    index)
                numba.parfors.parfor.init_prange()
                yov__cbwh = len(tsb__lzzw)
                kylnw__xsob = np.empty(yov__cbwh, np.float64)
                for ewkhi__okky in numba.parfors.parfor.internal_prange(
                    yov__cbwh):
                    bodo.libs.array_kernels.setna(kylnw__xsob, ewkhi__okky)
                return bodo.hiframes.pd_series_ext.init_series(kylnw__xsob,
                    bodo.utils.conversion.convert_to_index(tsb__lzzw),
                    evdsf__jtir)
            return impl
        if bodo.utils.conversion._is_str_dtype(dtype):
            yeyeb__ppwch = bodo.string_array_type
        else:
            ptt__evdi = bodo.utils.typing.parse_dtype(dtype, 'pandas.Series')
            if isinstance(ptt__evdi, bodo.libs.int_arr_ext.IntDtype):
                yeyeb__ppwch = bodo.IntegerArrayType(ptt__evdi.dtype)
            elif ptt__evdi == bodo.libs.bool_arr_ext.boolean_dtype:
                yeyeb__ppwch = bodo.boolean_array
            elif isinstance(ptt__evdi, types.Number) or ptt__evdi in [bodo.
                datetime64ns, bodo.timedelta64ns]:
                yeyeb__ppwch = types.Array(ptt__evdi, 1, 'C')
            else:
                raise BodoError(
                    'pd.Series with dtype: {dtype} not currently supported')
        if iac__wwpru:

            def impl(data=None, index=None, dtype=None, name=None, copy=
                False, fastpath=False):
                evdsf__jtir = bodo.utils.conversion.extract_name_if_none(data,
                    name)
                tsb__lzzw = bodo.hiframes.pd_index_ext.init_range_index(0, 
                    0, 1, None)
                numba.parfors.parfor.init_prange()
                yov__cbwh = len(tsb__lzzw)
                kylnw__xsob = bodo.utils.utils.alloc_type(yov__cbwh,
                    yeyeb__ppwch, (-1,))
                return bodo.hiframes.pd_series_ext.init_series(kylnw__xsob,
                    tsb__lzzw, evdsf__jtir)
            return impl
        else:

            def impl(data=None, index=None, dtype=None, name=None, copy=
                False, fastpath=False):
                evdsf__jtir = bodo.utils.conversion.extract_name_if_none(data,
                    name)
                tsb__lzzw = bodo.utils.conversion.extract_index_if_none(data,
                    index)
                numba.parfors.parfor.init_prange()
                yov__cbwh = len(tsb__lzzw)
                kylnw__xsob = bodo.utils.utils.alloc_type(yov__cbwh,
                    yeyeb__ppwch, (-1,))
                for ewkhi__okky in numba.parfors.parfor.internal_prange(
                    yov__cbwh):
                    bodo.libs.array_kernels.setna(kylnw__xsob, ewkhi__okky)
                return bodo.hiframes.pd_series_ext.init_series(kylnw__xsob,
                    bodo.utils.conversion.convert_to_index(tsb__lzzw),
                    evdsf__jtir)
            return impl

    def impl(data=None, index=None, dtype=None, name=None, copy=False,
        fastpath=False):
        evdsf__jtir = bodo.utils.conversion.extract_name_if_none(data, name)
        tsb__lzzw = bodo.utils.conversion.extract_index_if_none(data, index)
        znjy__bwr = bodo.utils.conversion.coerce_to_array(data, True,
            scalar_to_arr_len=len(tsb__lzzw))
        cvx__nede = bodo.utils.conversion.fix_arr_dtype(znjy__bwr, dtype,
            None, False)
        return bodo.hiframes.pd_series_ext.init_series(cvx__nede, bodo.
            utils.conversion.convert_to_index(tsb__lzzw), evdsf__jtir)
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
    data_val = context.get_constant_generic(builder, series_type.data,
        pyval.values)
    index_val = context.get_constant_generic(builder, series_type.index,
        pyval.index)
    name_val = context.get_constant_generic(builder, series_type.name_typ,
        pyval.name)
    qll__ctxoh = lir.Constant.literal_struct([data_val, index_val, name_val])
    qll__ctxoh = cgutils.global_constant(builder, '.const.payload', qll__ctxoh
        ).bitcast(cgutils.voidptr_t)
    jorlr__vvgdv = context.get_constant(types.int64, -1)
    upks__nap = context.get_constant_null(types.voidptr)
    xfpct__ekcy = lir.Constant.literal_struct([jorlr__vvgdv, upks__nap,
        upks__nap, qll__ctxoh, jorlr__vvgdv])
    xfpct__ekcy = cgutils.global_constant(builder, '.const.meminfo',
        xfpct__ekcy).bitcast(cgutils.voidptr_t)
    iyv__pfj = lir.Constant.literal_struct([xfpct__ekcy, upks__nap])
    return iyv__pfj


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
    for lbgv__osb in series_unsupported_attrs:
        dew__dsom = 'Series.' + lbgv__osb
        overload_attribute(SeriesType, lbgv__osb)(create_unsupported_overload
            (dew__dsom))
    for fname in series_unsupported_methods:
        dew__dsom = 'Series.' + fname
        overload_method(SeriesType, fname, no_unliteral=True)(
            create_unsupported_overload(dew__dsom))


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
    for lbgv__osb in heter_series_unsupported_attrs:
        dew__dsom = 'HeterogeneousSeries.' + lbgv__osb
        overload_attribute(HeterogeneousSeriesType, lbgv__osb)(
            create_unsupported_overload(dew__dsom))
    for fname in heter_series_unsupported_methods:
        dew__dsom = 'HeterogeneousSeries.' + fname
        overload_method(HeterogeneousSeriesType, fname, no_unliteral=True)(
            create_unsupported_overload(dew__dsom))


_install_heter_series_unsupported()
