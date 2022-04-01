"""Table data type for storing dataframe column arrays. Supports storing many columns
(e.g. >10k) efficiently.
"""
import operator
from collections import defaultdict
import numba
import numpy as np
import pandas as pd
from llvmlite import ir as lir
from numba.core import cgutils, types
from numba.core.imputils import impl_ret_borrowed, lower_constant
from numba.cpython.listobj import ListInstance
from numba.extending import NativeValue, box, infer_getattr, intrinsic, lower_builtin, lower_getattr, make_attribute_wrapper, models, overload, register_model, typeof_impl, unbox
from numba.np.arrayobj import _getitem_array_single_int
from numba.parfors.array_analysis import ArrayAnalysis
from bodo.utils.cg_helpers import is_ll_eq
from bodo.utils.templates import OverloadedKeyAttributeTemplate
from bodo.utils.typing import BodoError, decode_if_dict_array, get_overload_const_int, is_list_like_index_type, is_overload_constant_bool, is_overload_constant_int, is_overload_true, to_str_arr_if_dict_array


class Table:

    def __init__(self, arrs, usecols=None, num_arrs=-1):
        if usecols is not None:
            assert num_arrs != -1, 'num_arrs must be provided if usecols is not None'
            skn__msva = 0
            puov__xdi = []
            for i in range(usecols[-1] + 1):
                if i == usecols[skn__msva]:
                    puov__xdi.append(arrs[skn__msva])
                    skn__msva += 1
                else:
                    puov__xdi.append(None)
            for vexiw__roe in range(usecols[-1] + 1, num_arrs):
                puov__xdi.append(None)
            self.arrays = puov__xdi
        else:
            self.arrays = arrs
        self.block_0 = arrs

    def __eq__(self, other):
        return isinstance(other, Table) and len(self.arrays) == len(other.
            arrays) and all((mkh__vdy == mje__hdwr).all() for mkh__vdy,
            mje__hdwr in zip(self.arrays, other.arrays))

    def __str__(self) ->str:
        return str(self.arrays)

    def to_pandas(self, index=None):
        rcus__qztpp = len(self.arrays)
        hac__iml = dict(zip(range(rcus__qztpp), self.arrays))
        df = pd.DataFrame(hac__iml, index)
        return df


class TableType(types.ArrayCompatible):

    def __init__(self, arr_types, has_runtime_cols=False):
        self.arr_types = arr_types
        self.has_runtime_cols = has_runtime_cols
        dylf__motks = []
        vsxiz__vzz = []
        tau__nyya = {}
        xpgn__xlcyq = defaultdict(int)
        ztyc__fqm = defaultdict(list)
        if not has_runtime_cols:
            for i, jxlf__ohgxi in enumerate(arr_types):
                if jxlf__ohgxi not in tau__nyya:
                    tau__nyya[jxlf__ohgxi] = len(tau__nyya)
                jqw__wqszd = tau__nyya[jxlf__ohgxi]
                dylf__motks.append(jqw__wqszd)
                vsxiz__vzz.append(xpgn__xlcyq[jqw__wqszd])
                xpgn__xlcyq[jqw__wqszd] += 1
                ztyc__fqm[jqw__wqszd].append(i)
        self.block_nums = dylf__motks
        self.block_offsets = vsxiz__vzz
        self.type_to_blk = tau__nyya
        self.block_to_arr_ind = ztyc__fqm
        super(TableType, self).__init__(name=
            f'TableType({arr_types}, {has_runtime_cols})')

    @property
    def as_array(self):
        return types.Array(types.undefined, 2, 'C')

    @property
    def key(self):
        return self.arr_types, self.has_runtime_cols

    @property
    def mangling_args(self):
        return self.__class__.__name__, (self._code,)


@typeof_impl.register(Table)
def typeof_table(val, c):
    return TableType(tuple(numba.typeof(fmgq__fihbf) for fmgq__fihbf in val
        .arrays))


@register_model(TableType)
class TableTypeModel(models.StructModel):

    def __init__(self, dmm, fe_type):
        if fe_type.has_runtime_cols:
            dxlv__aet = [(f'block_{i}', types.List(jxlf__ohgxi)) for i,
                jxlf__ohgxi in enumerate(fe_type.arr_types)]
        else:
            dxlv__aet = [(f'block_{jqw__wqszd}', types.List(jxlf__ohgxi)) for
                jxlf__ohgxi, jqw__wqszd in fe_type.type_to_blk.items()]
        dxlv__aet.append(('parent', types.pyobject))
        dxlv__aet.append(('len', types.int64))
        super(TableTypeModel, self).__init__(dmm, fe_type, dxlv__aet)


make_attribute_wrapper(TableType, 'block_0', 'block_0')
make_attribute_wrapper(TableType, 'len', '_len')


@infer_getattr
class TableTypeAttribute(OverloadedKeyAttributeTemplate):
    key = TableType

    def resolve_shape(self, df):
        return types.Tuple([types.int64, types.int64])


@unbox(TableType)
def unbox_table(typ, val, c):
    lzbyw__khok = c.pyapi.object_getattr_string(val, 'arrays')
    sasv__jjorh = cgutils.create_struct_proxy(typ)(c.context, c.builder)
    sasv__jjorh.parent = cgutils.get_null_value(sasv__jjorh.parent.type)
    yaeki__cnk = c.pyapi.make_none()
    hoiuu__oir = c.context.get_constant(types.int64, 0)
    tgoak__xvj = cgutils.alloca_once_value(c.builder, hoiuu__oir)
    for jxlf__ohgxi, jqw__wqszd in typ.type_to_blk.items():
        ieh__ptd = c.context.get_constant(types.int64, len(typ.
            block_to_arr_ind[jqw__wqszd]))
        vexiw__roe, umrc__wnqk = ListInstance.allocate_ex(c.context, c.
            builder, types.List(jxlf__ohgxi), ieh__ptd)
        umrc__wnqk.size = ieh__ptd
        rpqx__dytdq = c.context.make_constant_array(c.builder, types.Array(
            types.int64, 1, 'C'), np.array(typ.block_to_arr_ind[jqw__wqszd],
            dtype=np.int64))
        ekxwe__dllb = c.context.make_array(types.Array(types.int64, 1, 'C'))(c
            .context, c.builder, rpqx__dytdq)
        with cgutils.for_range(c.builder, ieh__ptd) as ukage__tptx:
            i = ukage__tptx.index
            xlmxt__ynod = _getitem_array_single_int(c.context, c.builder,
                types.int64, types.Array(types.int64, 1, 'C'), ekxwe__dllb, i)
            kbon__gsyy = c.pyapi.long_from_longlong(xlmxt__ynod)
            fbim__ezmpr = c.pyapi.object_getitem(lzbyw__khok, kbon__gsyy)
            bpht__xwufi = c.builder.icmp_unsigned('==', fbim__ezmpr, yaeki__cnk
                )
            with c.builder.if_else(bpht__xwufi) as (uzpd__ppna, wmd__hkg):
                with uzpd__ppna:
                    yqzg__wqmpp = c.context.get_constant_null(jxlf__ohgxi)
                    umrc__wnqk.inititem(i, yqzg__wqmpp, incref=False)
                with wmd__hkg:
                    xba__svw = c.pyapi.call_method(fbim__ezmpr, '__len__', ())
                    iogs__vis = c.pyapi.long_as_longlong(xba__svw)
                    c.builder.store(iogs__vis, tgoak__xvj)
                    c.pyapi.decref(xba__svw)
                    fmgq__fihbf = c.pyapi.to_native_value(jxlf__ohgxi,
                        fbim__ezmpr).value
                    umrc__wnqk.inititem(i, fmgq__fihbf, incref=False)
            c.pyapi.decref(fbim__ezmpr)
            c.pyapi.decref(kbon__gsyy)
        setattr(sasv__jjorh, f'block_{jqw__wqszd}', umrc__wnqk.value)
    sasv__jjorh.len = c.builder.load(tgoak__xvj)
    c.pyapi.decref(lzbyw__khok)
    c.pyapi.decref(yaeki__cnk)
    iog__awl = cgutils.is_not_null(c.builder, c.pyapi.err_occurred())
    return NativeValue(sasv__jjorh._getvalue(), is_error=iog__awl)


@box(TableType)
def box_table(typ, val, c, ensure_unboxed=None):
    from bodo.hiframes.boxing import get_df_obj_column_codegen
    sasv__jjorh = cgutils.create_struct_proxy(typ)(c.context, c.builder, val)
    if typ.has_runtime_cols:
        izscg__yfnj = c.context.get_constant(types.int64, 0)
        for i, jxlf__ohgxi in enumerate(typ.arr_types):
            puov__xdi = getattr(sasv__jjorh, f'block_{i}')
            vkxyu__uae = ListInstance(c.context, c.builder, types.List(
                jxlf__ohgxi), puov__xdi)
            izscg__yfnj = c.builder.add(izscg__yfnj, vkxyu__uae.size)
        mbker__lfx = c.pyapi.list_new(izscg__yfnj)
        jzt__egjk = c.context.get_constant(types.int64, 0)
        for i, jxlf__ohgxi in enumerate(typ.arr_types):
            puov__xdi = getattr(sasv__jjorh, f'block_{i}')
            vkxyu__uae = ListInstance(c.context, c.builder, types.List(
                jxlf__ohgxi), puov__xdi)
            with cgutils.for_range(c.builder, vkxyu__uae.size) as ukage__tptx:
                i = ukage__tptx.index
                fmgq__fihbf = vkxyu__uae.getitem(i)
                c.context.nrt.incref(c.builder, jxlf__ohgxi, fmgq__fihbf)
                idx = c.builder.add(jzt__egjk, i)
                c.pyapi.list_setitem(mbker__lfx, idx, c.pyapi.
                    from_native_value(jxlf__ohgxi, fmgq__fihbf, c.env_manager))
            jzt__egjk = c.builder.add(jzt__egjk, vkxyu__uae.size)
        tgbz__yvnr = c.pyapi.unserialize(c.pyapi.serialize_object(Table))
        uxf__lbt = c.pyapi.call_function_objargs(tgbz__yvnr, (mbker__lfx,))
        c.pyapi.decref(tgbz__yvnr)
        c.pyapi.decref(mbker__lfx)
        c.context.nrt.decref(c.builder, typ, val)
        return uxf__lbt
    mbker__lfx = c.pyapi.list_new(c.context.get_constant(types.int64, len(
        typ.arr_types)))
    ylqg__bzd = cgutils.is_not_null(c.builder, sasv__jjorh.parent)
    if ensure_unboxed is None:
        ensure_unboxed = c.context.get_constant(types.bool_, False)
    for jxlf__ohgxi, jqw__wqszd in typ.type_to_blk.items():
        puov__xdi = getattr(sasv__jjorh, f'block_{jqw__wqszd}')
        vkxyu__uae = ListInstance(c.context, c.builder, types.List(
            jxlf__ohgxi), puov__xdi)
        rpqx__dytdq = c.context.make_constant_array(c.builder, types.Array(
            types.int64, 1, 'C'), np.array(typ.block_to_arr_ind[jqw__wqszd],
            dtype=np.int64))
        ekxwe__dllb = c.context.make_array(types.Array(types.int64, 1, 'C'))(c
            .context, c.builder, rpqx__dytdq)
        with cgutils.for_range(c.builder, vkxyu__uae.size) as ukage__tptx:
            i = ukage__tptx.index
            xlmxt__ynod = _getitem_array_single_int(c.context, c.builder,
                types.int64, types.Array(types.int64, 1, 'C'), ekxwe__dllb, i)
            fmgq__fihbf = vkxyu__uae.getitem(i)
            ixp__hds = cgutils.alloca_once_value(c.builder, fmgq__fihbf)
            nwkbe__ahkve = cgutils.alloca_once_value(c.builder, c.context.
                get_constant_null(jxlf__ohgxi))
            suqyo__mdeqi = is_ll_eq(c.builder, ixp__hds, nwkbe__ahkve)
            with c.builder.if_else(c.builder.and_(suqyo__mdeqi, c.builder.
                not_(ensure_unboxed))) as (uzpd__ppna, wmd__hkg):
                with uzpd__ppna:
                    yaeki__cnk = c.pyapi.make_none()
                    c.pyapi.list_setitem(mbker__lfx, xlmxt__ynod, yaeki__cnk)
                with wmd__hkg:
                    fbim__ezmpr = cgutils.alloca_once(c.builder, c.context.
                        get_value_type(types.pyobject))
                    with c.builder.if_else(c.builder.and_(suqyo__mdeqi,
                        ylqg__bzd)) as (opdyb__tjee, uirl__reatv):
                        with opdyb__tjee:
                            rqjb__dsd = get_df_obj_column_codegen(c.context,
                                c.builder, c.pyapi, sasv__jjorh.parent,
                                xlmxt__ynod, jxlf__ohgxi)
                            c.builder.store(rqjb__dsd, fbim__ezmpr)
                        with uirl__reatv:
                            c.context.nrt.incref(c.builder, jxlf__ohgxi,
                                fmgq__fihbf)
                            c.builder.store(c.pyapi.from_native_value(
                                jxlf__ohgxi, fmgq__fihbf, c.env_manager),
                                fbim__ezmpr)
                    c.pyapi.list_setitem(mbker__lfx, xlmxt__ynod, c.builder
                        .load(fbim__ezmpr))
    tgbz__yvnr = c.pyapi.unserialize(c.pyapi.serialize_object(Table))
    uxf__lbt = c.pyapi.call_function_objargs(tgbz__yvnr, (mbker__lfx,))
    c.pyapi.decref(tgbz__yvnr)
    c.pyapi.decref(mbker__lfx)
    c.context.nrt.decref(c.builder, typ, val)
    return uxf__lbt


@lower_builtin(len, TableType)
def table_len_lower(context, builder, sig, args):
    impl = table_len_overload(*sig.args)
    return context.compile_internal(builder, impl, sig, args)


def table_len_overload(T):
    if not isinstance(T, TableType):
        return

    def impl(T):
        return T._len
    return impl


@lower_getattr(TableType, 'shape')
def lower_table_shape(context, builder, typ, val):
    impl = table_shape_overload(typ)
    return context.compile_internal(builder, impl, types.Tuple([types.int64,
        types.int64])(typ), (val,))


def table_shape_overload(T):
    if T.has_runtime_cols:

        def impl(T):
            return T._len, compute_num_runtime_columns(T)
        return impl
    ncols = len(T.arr_types)
    return lambda T: (T._len, types.int64(ncols))


@intrinsic
def compute_num_runtime_columns(typingctx, table_type):
    assert isinstance(table_type, TableType)

    def codegen(context, builder, sig, args):
        table_arg, = args
        sasv__jjorh = cgutils.create_struct_proxy(table_type)(context,
            builder, table_arg)
        old__anka = context.get_constant(types.int64, 0)
        for i, jxlf__ohgxi in enumerate(table_type.arr_types):
            puov__xdi = getattr(sasv__jjorh, f'block_{i}')
            vkxyu__uae = ListInstance(context, builder, types.List(
                jxlf__ohgxi), puov__xdi)
            old__anka = builder.add(old__anka, vkxyu__uae.size)
        return old__anka
    sig = types.int64(table_type)
    return sig, codegen


def get_table_data_codegen(context, builder, table_arg, col_ind, table_type):
    arr_type = table_type.arr_types[col_ind]
    sasv__jjorh = cgutils.create_struct_proxy(table_type)(context, builder,
        table_arg)
    jqw__wqszd = table_type.block_nums[col_ind]
    wvde__rvk = table_type.block_offsets[col_ind]
    puov__xdi = getattr(sasv__jjorh, f'block_{jqw__wqszd}')
    vkxyu__uae = ListInstance(context, builder, types.List(arr_type), puov__xdi
        )
    fmgq__fihbf = vkxyu__uae.getitem(wvde__rvk)
    return fmgq__fihbf


@intrinsic
def get_table_data(typingctx, table_type, ind_typ=None):
    assert isinstance(table_type, TableType)
    assert is_overload_constant_int(ind_typ)
    col_ind = get_overload_const_int(ind_typ)
    arr_type = table_type.arr_types[col_ind]

    def codegen(context, builder, sig, args):
        table_arg, vexiw__roe = args
        fmgq__fihbf = get_table_data_codegen(context, builder, table_arg,
            col_ind, table_type)
        return impl_ret_borrowed(context, builder, arr_type, fmgq__fihbf)
    sig = arr_type(table_type, ind_typ)
    return sig, codegen


@intrinsic
def del_column(typingctx, table_type, ind_typ=None):
    assert isinstance(table_type, TableType)
    assert is_overload_constant_int(ind_typ)
    col_ind = get_overload_const_int(ind_typ)
    arr_type = table_type.arr_types[col_ind]

    def codegen(context, builder, sig, args):
        table_arg, vexiw__roe = args
        sasv__jjorh = cgutils.create_struct_proxy(table_type)(context,
            builder, table_arg)
        jqw__wqszd = table_type.block_nums[col_ind]
        wvde__rvk = table_type.block_offsets[col_ind]
        puov__xdi = getattr(sasv__jjorh, f'block_{jqw__wqszd}')
        vkxyu__uae = ListInstance(context, builder, types.List(arr_type),
            puov__xdi)
        fmgq__fihbf = vkxyu__uae.getitem(wvde__rvk)
        context.nrt.decref(builder, arr_type, fmgq__fihbf)
        yqzg__wqmpp = context.get_constant_null(arr_type)
        vkxyu__uae.inititem(wvde__rvk, yqzg__wqmpp, incref=False)
    sig = types.void(table_type, ind_typ)
    return sig, codegen


def set_table_data_codegen(context, builder, in_table_type, in_table,
    out_table_type, arr_type, arr_arg, col_ind, is_new_col):
    in_table = cgutils.create_struct_proxy(in_table_type)(context, builder,
        in_table)
    out_table = cgutils.create_struct_proxy(out_table_type)(context, builder)
    out_table.len = in_table.len
    out_table.parent = in_table.parent
    hoiuu__oir = context.get_constant(types.int64, 0)
    kle__nvbdr = context.get_constant(types.int64, 1)
    xiomj__evya = arr_type not in in_table_type.type_to_blk
    for jxlf__ohgxi, jqw__wqszd in out_table_type.type_to_blk.items():
        if jxlf__ohgxi in in_table_type.type_to_blk:
            ind__suzpl = in_table_type.type_to_blk[jxlf__ohgxi]
            umrc__wnqk = ListInstance(context, builder, types.List(
                jxlf__ohgxi), getattr(in_table, f'block_{ind__suzpl}'))
            context.nrt.incref(builder, types.List(jxlf__ohgxi), umrc__wnqk
                .value)
            setattr(out_table, f'block_{jqw__wqszd}', umrc__wnqk.value)
    if xiomj__evya:
        vexiw__roe, umrc__wnqk = ListInstance.allocate_ex(context, builder,
            types.List(arr_type), kle__nvbdr)
        umrc__wnqk.size = kle__nvbdr
        umrc__wnqk.inititem(hoiuu__oir, arr_arg, incref=True)
        jqw__wqszd = out_table_type.type_to_blk[arr_type]
        setattr(out_table, f'block_{jqw__wqszd}', umrc__wnqk.value)
        if not is_new_col:
            _rm_old_array(col_ind, out_table_type, out_table, in_table_type,
                context, builder)
    else:
        jqw__wqszd = out_table_type.type_to_blk[arr_type]
        umrc__wnqk = ListInstance(context, builder, types.List(arr_type),
            getattr(out_table, f'block_{jqw__wqszd}'))
        if is_new_col:
            n = umrc__wnqk.size
            uhls__ajcr = builder.add(n, kle__nvbdr)
            umrc__wnqk.resize(uhls__ajcr)
            umrc__wnqk.inititem(n, arr_arg, incref=True)
        elif arr_type == in_table_type.arr_types[col_ind]:
            bui__drwwl = context.get_constant(types.int64, out_table_type.
                block_offsets[col_ind])
            umrc__wnqk.setitem(bui__drwwl, arr_arg, True)
        else:
            _rm_old_array(col_ind, out_table_type, out_table, in_table_type,
                context, builder)
            bui__drwwl = context.get_constant(types.int64, out_table_type.
                block_offsets[col_ind])
            n = umrc__wnqk.size
            uhls__ajcr = builder.add(n, kle__nvbdr)
            umrc__wnqk.resize(uhls__ajcr)
            context.nrt.incref(builder, arr_type, umrc__wnqk.getitem(
                bui__drwwl))
            umrc__wnqk.move(builder.add(bui__drwwl, kle__nvbdr), bui__drwwl,
                builder.sub(n, bui__drwwl))
            umrc__wnqk.setitem(bui__drwwl, arr_arg, incref=True)
    return out_table._getvalue()


def _rm_old_array(col_ind, out_table_type, out_table, in_table_type,
    context, builder):
    usjn__aso = in_table_type.arr_types[col_ind]
    if usjn__aso in out_table_type.type_to_blk:
        jqw__wqszd = out_table_type.type_to_blk[usjn__aso]
        ehhah__kprl = getattr(out_table, f'block_{jqw__wqszd}')
        acl__vjp = types.List(usjn__aso)
        bui__drwwl = context.get_constant(types.int64, in_table_type.
            block_offsets[col_ind])
        lvhet__juq = acl__vjp.dtype(acl__vjp, types.intp)
        nuq__ecea = context.compile_internal(builder, lambda lst, i: lst.
            pop(i), lvhet__juq, (ehhah__kprl, bui__drwwl))
        context.nrt.decref(builder, usjn__aso, nuq__ecea)


@intrinsic
def set_table_data(typingctx, table_type, ind_type, arr_type=None):
    assert isinstance(table_type, TableType), 'invalid input to set_table_data'
    assert is_overload_constant_int(ind_type
        ), 'set_table_data expects const index'
    col_ind = get_overload_const_int(ind_type)
    is_new_col = col_ind == len(table_type.arr_types)
    pzgb__wftg = list(table_type.arr_types)
    if is_new_col:
        pzgb__wftg.append(arr_type)
    else:
        pzgb__wftg[col_ind] = arr_type
    out_table_type = TableType(tuple(pzgb__wftg))

    def codegen(context, builder, sig, args):
        table_arg, vexiw__roe, yrh__nkhjt = args
        out_table = set_table_data_codegen(context, builder, table_type,
            table_arg, out_table_type, arr_type, yrh__nkhjt, col_ind,
            is_new_col)
        return out_table
    return out_table_type(table_type, ind_type, arr_type), codegen


def alias_ext_dummy_func(lhs_name, args, alias_map, arg_aliases):
    assert len(args) >= 1
    numba.core.ir_utils._add_alias(lhs_name, args[0].name, alias_map,
        arg_aliases)


numba.core.ir_utils.alias_func_extensions['get_table_data',
    'bodo.hiframes.table'] = alias_ext_dummy_func


def get_table_data_equiv(self, scope, equiv_set, loc, args, kws):
    assert len(args) == 2 and not kws
    makv__owlc = args[0]
    if equiv_set.has_shape(makv__owlc):
        return ArrayAnalysis.AnalyzeResult(shape=equiv_set.get_shape(
            makv__owlc)[0], pre=[])


ArrayAnalysis._analyze_op_call_bodo_hiframes_table_get_table_data = (
    get_table_data_equiv)


@lower_constant(TableType)
def lower_constant_table(context, builder, table_type, pyval):
    bcs__mhj = []
    for jxlf__ohgxi, jqw__wqszd in table_type.type_to_blk.items():
        huyqq__gsgr = len(table_type.block_to_arr_ind[jqw__wqszd])
        plv__eqhyi = []
        for i in range(huyqq__gsgr):
            xlmxt__ynod = table_type.block_to_arr_ind[jqw__wqszd][i]
            plv__eqhyi.append(pyval.arrays[xlmxt__ynod])
        bcs__mhj.append(context.get_constant_generic(builder, types.List(
            jxlf__ohgxi), plv__eqhyi))
    gcuru__yijj = context.get_constant_null(types.pyobject)
    jehr__xjao = context.get_constant(types.int64, 0 if len(pyval.arrays) ==
        0 else len(pyval.arrays[0]))
    return lir.Constant.literal_struct(bcs__mhj + [gcuru__yijj, jehr__xjao])


@intrinsic
def init_table(typingctx, table_type, to_str_if_dict_t=None):
    assert isinstance(table_type, TableType), 'table type expected'
    assert is_overload_constant_bool(to_str_if_dict_t
        ), 'constant to_str_if_dict_t expected'
    out_table_type = table_type
    if is_overload_true(to_str_if_dict_t):
        out_table_type = to_str_arr_if_dict_array(table_type)

    def codegen(context, builder, sig, args):
        sasv__jjorh = cgutils.create_struct_proxy(out_table_type)(context,
            builder)
        for jxlf__ohgxi, jqw__wqszd in out_table_type.type_to_blk.items():
            mpk__ggh = context.get_constant_null(types.List(jxlf__ohgxi))
            setattr(sasv__jjorh, f'block_{jqw__wqszd}', mpk__ggh)
        return sasv__jjorh._getvalue()
    sig = out_table_type(table_type, to_str_if_dict_t)
    return sig, codegen


@intrinsic
def get_table_block(typingctx, table_type, blk_type=None):
    assert isinstance(table_type, TableType), 'table type expected'
    assert is_overload_constant_int(blk_type)
    jqw__wqszd = get_overload_const_int(blk_type)
    arr_type = None
    for jxlf__ohgxi, mje__hdwr in table_type.type_to_blk.items():
        if mje__hdwr == jqw__wqszd:
            arr_type = jxlf__ohgxi
            break
    assert arr_type is not None, 'invalid table type block'
    qgrup__wcsb = types.List(arr_type)

    def codegen(context, builder, sig, args):
        sasv__jjorh = cgutils.create_struct_proxy(table_type)(context,
            builder, args[0])
        puov__xdi = getattr(sasv__jjorh, f'block_{jqw__wqszd}')
        return impl_ret_borrowed(context, builder, qgrup__wcsb, puov__xdi)
    sig = qgrup__wcsb(table_type, blk_type)
    return sig, codegen


@intrinsic
def ensure_column_unboxed(typingctx, table_type, arr_list_t, ind_t,
    arr_ind_t=None):
    assert isinstance(table_type, TableType), 'table type expected'
    sig = types.none(table_type, arr_list_t, ind_t, arr_ind_t)
    return sig, ensure_column_unboxed_codegen


def ensure_column_unboxed_codegen(context, builder, sig, args):
    from bodo.hiframes.boxing import get_df_obj_column_codegen
    table_arg, ytcm__rdksg, zjg__nrg, mzxxh__uxa = args
    ompht__hva = context.get_python_api(builder)
    sasv__jjorh = cgutils.create_struct_proxy(sig.args[0])(context, builder,
        table_arg)
    ylqg__bzd = cgutils.is_not_null(builder, sasv__jjorh.parent)
    vkxyu__uae = ListInstance(context, builder, sig.args[1], ytcm__rdksg)
    mebw__jzx = vkxyu__uae.getitem(zjg__nrg)
    ixp__hds = cgutils.alloca_once_value(builder, mebw__jzx)
    nwkbe__ahkve = cgutils.alloca_once_value(builder, context.
        get_constant_null(sig.args[1].dtype))
    suqyo__mdeqi = is_ll_eq(builder, ixp__hds, nwkbe__ahkve)
    with builder.if_then(suqyo__mdeqi):
        with builder.if_else(ylqg__bzd) as (uzpd__ppna, wmd__hkg):
            with uzpd__ppna:
                fbim__ezmpr = get_df_obj_column_codegen(context, builder,
                    ompht__hva, sasv__jjorh.parent, mzxxh__uxa, sig.args[1]
                    .dtype)
                fmgq__fihbf = ompht__hva.to_native_value(sig.args[1].dtype,
                    fbim__ezmpr).value
                vkxyu__uae.inititem(zjg__nrg, fmgq__fihbf, incref=False)
                ompht__hva.decref(fbim__ezmpr)
            with wmd__hkg:
                context.call_conv.return_user_exc(builder, BodoError, (
                    'unexpected null table column',))


@intrinsic
def set_table_block(typingctx, table_type, arr_list_type, blk_type=None):
    assert isinstance(table_type, TableType), 'table type expected'
    assert isinstance(arr_list_type, types.List), 'list type expected'
    assert is_overload_constant_int(blk_type), 'blk should be const int'
    jqw__wqszd = get_overload_const_int(blk_type)

    def codegen(context, builder, sig, args):
        table_arg, bca__jnq, vexiw__roe = args
        in_table = cgutils.create_struct_proxy(table_type)(context, builder,
            table_arg)
        setattr(in_table, f'block_{jqw__wqszd}', bca__jnq)
        return impl_ret_borrowed(context, builder, table_type, in_table.
            _getvalue())
    sig = table_type(table_type, arr_list_type, blk_type)
    return sig, codegen


@intrinsic
def set_table_len(typingctx, table_type, l_type=None):
    assert isinstance(table_type, TableType), 'table type expected'

    def codegen(context, builder, sig, args):
        table_arg, fsecn__sxa = args
        in_table = cgutils.create_struct_proxy(table_type)(context, builder,
            table_arg)
        in_table.len = fsecn__sxa
        return impl_ret_borrowed(context, builder, table_type, in_table.
            _getvalue())
    sig = table_type(table_type, l_type)
    return sig, codegen


@intrinsic
def alloc_list_like(typingctx, list_type, to_str_if_dict_t=None):
    assert isinstance(list_type, types.List), 'list type expected'
    assert is_overload_constant_bool(to_str_if_dict_t
        ), 'constant to_str_if_dict_t expected'
    qgrup__wcsb = list_type
    if is_overload_true(to_str_if_dict_t):
        qgrup__wcsb = types.List(to_str_arr_if_dict_array(list_type.dtype))

    def codegen(context, builder, sig, args):
        ebep__locgb = ListInstance(context, builder, list_type, args[0])
        bglb__qyzt = ebep__locgb.size
        vexiw__roe, umrc__wnqk = ListInstance.allocate_ex(context, builder,
            qgrup__wcsb, bglb__qyzt)
        umrc__wnqk.size = bglb__qyzt
        return umrc__wnqk.value
    sig = qgrup__wcsb(list_type, to_str_if_dict_t)
    return sig, codegen


def _get_idx_length(idx):
    pass


@overload(_get_idx_length)
def overload_get_idx_length(idx, n):
    if is_list_like_index_type(idx) and idx.dtype == types.bool_:
        return lambda idx, n: idx.sum()
    assert isinstance(idx, types.SliceType), 'slice index expected'

    def impl(idx, n):
        bcex__lgf = numba.cpython.unicode._normalize_slice(idx, n)
        return numba.cpython.unicode._slice_span(bcex__lgf)
    return impl


def gen_table_filter(T, used_cols=None):
    from bodo.utils.conversion import ensure_contig_if_np
    avzho__ixj = {'init_table': init_table, 'get_table_block':
        get_table_block, 'ensure_column_unboxed': ensure_column_unboxed,
        'set_table_block': set_table_block, 'set_table_len': set_table_len,
        'alloc_list_like': alloc_list_like, '_get_idx_length':
        _get_idx_length, 'ensure_contig_if_np': ensure_contig_if_np}
    if used_cols is not None:
        avzho__ixj['used_cols'] = np.array(used_cols, dtype=np.int64)
    gzbw__ojnh = 'def impl(T, idx):\n'
    gzbw__ojnh += f'  T2 = init_table(T, False)\n'
    gzbw__ojnh += f'  l = 0\n'
    if used_cols is not None and len(used_cols) == 0:
        gzbw__ojnh += f'  l = _get_idx_length(idx, len(T))\n'
        gzbw__ojnh += f'  T2 = set_table_len(T2, l)\n'
        gzbw__ojnh += f'  return T2\n'
        mhq__ppd = {}
        exec(gzbw__ojnh, avzho__ixj, mhq__ppd)
        return mhq__ppd['impl']
    if used_cols is not None:
        gzbw__ojnh += f'  used_set = set(used_cols)\n'
    for jqw__wqszd in T.type_to_blk.values():
        avzho__ixj[f'arr_inds_{jqw__wqszd}'] = np.array(T.block_to_arr_ind[
            jqw__wqszd], dtype=np.int64)
        gzbw__ojnh += (
            f'  arr_list_{jqw__wqszd} = get_table_block(T, {jqw__wqszd})\n')
        gzbw__ojnh += f"""  out_arr_list_{jqw__wqszd} = alloc_list_like(arr_list_{jqw__wqszd}, False)
"""
        gzbw__ojnh += f'  for i in range(len(arr_list_{jqw__wqszd})):\n'
        gzbw__ojnh += f'    arr_ind_{jqw__wqszd} = arr_inds_{jqw__wqszd}[i]\n'
        if used_cols is not None:
            gzbw__ojnh += (
                f'    if arr_ind_{jqw__wqszd} not in used_set: continue\n')
        gzbw__ojnh += f"""    ensure_column_unboxed(T, arr_list_{jqw__wqszd}, i, arr_ind_{jqw__wqszd})
"""
        gzbw__ojnh += f"""    out_arr_{jqw__wqszd} = ensure_contig_if_np(arr_list_{jqw__wqszd}[i][idx])
"""
        gzbw__ojnh += f'    l = len(out_arr_{jqw__wqszd})\n'
        gzbw__ojnh += (
            f'    out_arr_list_{jqw__wqszd}[i] = out_arr_{jqw__wqszd}\n')
        gzbw__ojnh += (
            f'  T2 = set_table_block(T2, out_arr_list_{jqw__wqszd}, {jqw__wqszd})\n'
            )
    gzbw__ojnh += f'  T2 = set_table_len(T2, l)\n'
    gzbw__ojnh += f'  return T2\n'
    mhq__ppd = {}
    exec(gzbw__ojnh, avzho__ixj, mhq__ppd)
    return mhq__ppd['impl']


@numba.generated_jit(nopython=True, no_cpython_wrapper=True)
def decode_if_dict_table(T):
    gzbw__ojnh = 'def impl(T):\n'
    gzbw__ojnh += f'  T2 = init_table(T, True)\n'
    gzbw__ojnh += f'  l = len(T)\n'
    avzho__ixj = {'init_table': init_table, 'get_table_block':
        get_table_block, 'ensure_column_unboxed': ensure_column_unboxed,
        'set_table_block': set_table_block, 'set_table_len': set_table_len,
        'alloc_list_like': alloc_list_like, 'decode_if_dict_array':
        decode_if_dict_array}
    for jqw__wqszd in T.type_to_blk.values():
        avzho__ixj[f'arr_inds_{jqw__wqszd}'] = np.array(T.block_to_arr_ind[
            jqw__wqszd], dtype=np.int64)
        gzbw__ojnh += (
            f'  arr_list_{jqw__wqszd} = get_table_block(T, {jqw__wqszd})\n')
        gzbw__ojnh += f"""  out_arr_list_{jqw__wqszd} = alloc_list_like(arr_list_{jqw__wqszd}, True)
"""
        gzbw__ojnh += f'  for i in range(len(arr_list_{jqw__wqszd})):\n'
        gzbw__ojnh += f'    arr_ind_{jqw__wqszd} = arr_inds_{jqw__wqszd}[i]\n'
        gzbw__ojnh += f"""    ensure_column_unboxed(T, arr_list_{jqw__wqszd}, i, arr_ind_{jqw__wqszd})
"""
        gzbw__ojnh += (
            f'    out_arr_{jqw__wqszd} = decode_if_dict_array(arr_list_{jqw__wqszd}[i])\n'
            )
        gzbw__ojnh += (
            f'    out_arr_list_{jqw__wqszd}[i] = out_arr_{jqw__wqszd}\n')
        gzbw__ojnh += (
            f'  T2 = set_table_block(T2, out_arr_list_{jqw__wqszd}, {jqw__wqszd})\n'
            )
    gzbw__ojnh += f'  T2 = set_table_len(T2, l)\n'
    gzbw__ojnh += f'  return T2\n'
    mhq__ppd = {}
    exec(gzbw__ojnh, avzho__ixj, mhq__ppd)
    return mhq__ppd['impl']


@overload(operator.getitem, no_unliteral=True)
def table_getitem(T, idx):
    if not isinstance(T, TableType):
        return
    return gen_table_filter(T)


@intrinsic
def init_runtime_table_from_lists(typingctx, arr_list_tup_typ, nrows_typ=None):
    assert isinstance(arr_list_tup_typ, types.BaseTuple
        ), 'init_runtime_table_from_lists requires a tuple of list of arrays'
    if isinstance(arr_list_tup_typ, types.UniTuple):
        if arr_list_tup_typ.dtype.dtype == types.undefined:
            return
        cxh__bkbyg = [arr_list_tup_typ.dtype.dtype] * len(arr_list_tup_typ)
    else:
        cxh__bkbyg = []
        for typ in arr_list_tup_typ:
            if typ.dtype == types.undefined:
                return
            cxh__bkbyg.append(typ.dtype)
    assert isinstance(nrows_typ, types.Integer
        ), 'init_runtime_table_from_lists requires an integer length'

    def codegen(context, builder, sig, args):
        pchj__rdn, oca__hyzm = args
        sasv__jjorh = cgutils.create_struct_proxy(table_type)(context, builder)
        sasv__jjorh.len = oca__hyzm
        bcs__mhj = cgutils.unpack_tuple(builder, pchj__rdn)
        for i, puov__xdi in enumerate(bcs__mhj):
            setattr(sasv__jjorh, f'block_{i}', puov__xdi)
            context.nrt.incref(builder, types.List(cxh__bkbyg[i]), puov__xdi)
        return sasv__jjorh._getvalue()
    table_type = TableType(tuple(cxh__bkbyg), True)
    sig = table_type(arr_list_tup_typ, nrows_typ)
    return sig, codegen
