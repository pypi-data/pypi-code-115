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
            pezhb__foh = 0
            ufo__fcckr = []
            for i in range(usecols[-1] + 1):
                if i == usecols[pezhb__foh]:
                    ufo__fcckr.append(arrs[pezhb__foh])
                    pezhb__foh += 1
                else:
                    ufo__fcckr.append(None)
            for gfs__qnz in range(usecols[-1] + 1, num_arrs):
                ufo__fcckr.append(None)
            self.arrays = ufo__fcckr
        else:
            self.arrays = arrs
        self.block_0 = arrs

    def __eq__(self, other):
        return isinstance(other, Table) and len(self.arrays) == len(other.
            arrays) and all((goqv__dgizs == sjn__gfrl).all() for 
            goqv__dgizs, sjn__gfrl in zip(self.arrays, other.arrays))

    def __str__(self) ->str:
        return str(self.arrays)

    def to_pandas(self, index=None):
        xtyf__huers = len(self.arrays)
        lqhvr__mlvy = dict(zip(range(xtyf__huers), self.arrays))
        df = pd.DataFrame(lqhvr__mlvy, index)
        return df


class TableType(types.ArrayCompatible):

    def __init__(self, arr_types, has_runtime_cols=False):
        self.arr_types = arr_types
        self.has_runtime_cols = has_runtime_cols
        qxkja__yday = []
        yyrjh__raf = []
        bxzpu__vvmc = {}
        nwuq__tsk = defaultdict(int)
        plixv__lvrth = defaultdict(list)
        if not has_runtime_cols:
            for i, uckk__jjlwa in enumerate(arr_types):
                if uckk__jjlwa not in bxzpu__vvmc:
                    bxzpu__vvmc[uckk__jjlwa] = len(bxzpu__vvmc)
                gdyzj__qzav = bxzpu__vvmc[uckk__jjlwa]
                qxkja__yday.append(gdyzj__qzav)
                yyrjh__raf.append(nwuq__tsk[gdyzj__qzav])
                nwuq__tsk[gdyzj__qzav] += 1
                plixv__lvrth[gdyzj__qzav].append(i)
        self.block_nums = qxkja__yday
        self.block_offsets = yyrjh__raf
        self.type_to_blk = bxzpu__vvmc
        self.block_to_arr_ind = plixv__lvrth
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
    return TableType(tuple(numba.typeof(dbe__obcf) for dbe__obcf in val.arrays)
        )


@register_model(TableType)
class TableTypeModel(models.StructModel):

    def __init__(self, dmm, fe_type):
        if fe_type.has_runtime_cols:
            wcoc__ibgye = [(f'block_{i}', types.List(uckk__jjlwa)) for i,
                uckk__jjlwa in enumerate(fe_type.arr_types)]
        else:
            wcoc__ibgye = [(f'block_{gdyzj__qzav}', types.List(uckk__jjlwa)
                ) for uckk__jjlwa, gdyzj__qzav in fe_type.type_to_blk.items()]
        wcoc__ibgye.append(('parent', types.pyobject))
        wcoc__ibgye.append(('len', types.int64))
        super(TableTypeModel, self).__init__(dmm, fe_type, wcoc__ibgye)


make_attribute_wrapper(TableType, 'block_0', 'block_0')
make_attribute_wrapper(TableType, 'len', '_len')


@infer_getattr
class TableTypeAttribute(OverloadedKeyAttributeTemplate):
    key = TableType

    def resolve_shape(self, df):
        return types.Tuple([types.int64, types.int64])


@unbox(TableType)
def unbox_table(typ, val, c):
    xakau__lgiu = c.pyapi.object_getattr_string(val, 'arrays')
    rbc__jyip = cgutils.create_struct_proxy(typ)(c.context, c.builder)
    rbc__jyip.parent = cgutils.get_null_value(rbc__jyip.parent.type)
    balt__ceus = c.pyapi.make_none()
    ssf__dukd = c.context.get_constant(types.int64, 0)
    ibofl__vdmdd = cgutils.alloca_once_value(c.builder, ssf__dukd)
    for uckk__jjlwa, gdyzj__qzav in typ.type_to_blk.items():
        nku__jpe = c.context.get_constant(types.int64, len(typ.
            block_to_arr_ind[gdyzj__qzav]))
        gfs__qnz, etv__hyms = ListInstance.allocate_ex(c.context, c.builder,
            types.List(uckk__jjlwa), nku__jpe)
        etv__hyms.size = nku__jpe
        box__jmubw = c.context.make_constant_array(c.builder, types.Array(
            types.int64, 1, 'C'), np.array(typ.block_to_arr_ind[gdyzj__qzav
            ], dtype=np.int64))
        jodt__arcul = c.context.make_array(types.Array(types.int64, 1, 'C'))(c
            .context, c.builder, box__jmubw)
        with cgutils.for_range(c.builder, nku__jpe) as doaz__are:
            i = doaz__are.index
            qadg__ysby = _getitem_array_single_int(c.context, c.builder,
                types.int64, types.Array(types.int64, 1, 'C'), jodt__arcul, i)
            qlk__gcqfm = c.pyapi.long_from_longlong(qadg__ysby)
            rkupd__dig = c.pyapi.object_getitem(xakau__lgiu, qlk__gcqfm)
            ahojf__tvgei = c.builder.icmp_unsigned('==', rkupd__dig, balt__ceus
                )
            with c.builder.if_else(ahojf__tvgei) as (ootw__xisp, yuig__sva):
                with ootw__xisp:
                    rle__saiw = c.context.get_constant_null(uckk__jjlwa)
                    etv__hyms.inititem(i, rle__saiw, incref=False)
                with yuig__sva:
                    jixlp__ymahu = c.pyapi.call_method(rkupd__dig,
                        '__len__', ())
                    vbjzx__sstua = c.pyapi.long_as_longlong(jixlp__ymahu)
                    c.builder.store(vbjzx__sstua, ibofl__vdmdd)
                    c.pyapi.decref(jixlp__ymahu)
                    dbe__obcf = c.pyapi.to_native_value(uckk__jjlwa, rkupd__dig
                        ).value
                    etv__hyms.inititem(i, dbe__obcf, incref=False)
            c.pyapi.decref(rkupd__dig)
            c.pyapi.decref(qlk__gcqfm)
        setattr(rbc__jyip, f'block_{gdyzj__qzav}', etv__hyms.value)
    rbc__jyip.len = c.builder.load(ibofl__vdmdd)
    c.pyapi.decref(xakau__lgiu)
    c.pyapi.decref(balt__ceus)
    ytha__bvhj = cgutils.is_not_null(c.builder, c.pyapi.err_occurred())
    return NativeValue(rbc__jyip._getvalue(), is_error=ytha__bvhj)


@box(TableType)
def box_table(typ, val, c, ensure_unboxed=None):
    from bodo.hiframes.boxing import get_df_obj_column_codegen
    rbc__jyip = cgutils.create_struct_proxy(typ)(c.context, c.builder, val)
    if typ.has_runtime_cols:
        qwa__hri = c.context.get_constant(types.int64, 0)
        for i, uckk__jjlwa in enumerate(typ.arr_types):
            ufo__fcckr = getattr(rbc__jyip, f'block_{i}')
            jhs__ioob = ListInstance(c.context, c.builder, types.List(
                uckk__jjlwa), ufo__fcckr)
            qwa__hri = c.builder.add(qwa__hri, jhs__ioob.size)
        qtb__awfs = c.pyapi.list_new(qwa__hri)
        trhqu__ihy = c.context.get_constant(types.int64, 0)
        for i, uckk__jjlwa in enumerate(typ.arr_types):
            ufo__fcckr = getattr(rbc__jyip, f'block_{i}')
            jhs__ioob = ListInstance(c.context, c.builder, types.List(
                uckk__jjlwa), ufo__fcckr)
            with cgutils.for_range(c.builder, jhs__ioob.size) as doaz__are:
                i = doaz__are.index
                dbe__obcf = jhs__ioob.getitem(i)
                c.context.nrt.incref(c.builder, uckk__jjlwa, dbe__obcf)
                idx = c.builder.add(trhqu__ihy, i)
                c.pyapi.list_setitem(qtb__awfs, idx, c.pyapi.
                    from_native_value(uckk__jjlwa, dbe__obcf, c.env_manager))
            trhqu__ihy = c.builder.add(trhqu__ihy, jhs__ioob.size)
        cyko__wspd = c.pyapi.unserialize(c.pyapi.serialize_object(Table))
        ahs__wet = c.pyapi.call_function_objargs(cyko__wspd, (qtb__awfs,))
        c.pyapi.decref(cyko__wspd)
        c.pyapi.decref(qtb__awfs)
        c.context.nrt.decref(c.builder, typ, val)
        return ahs__wet
    qtb__awfs = c.pyapi.list_new(c.context.get_constant(types.int64, len(
        typ.arr_types)))
    kmtw__joe = cgutils.is_not_null(c.builder, rbc__jyip.parent)
    if ensure_unboxed is None:
        ensure_unboxed = c.context.get_constant(types.bool_, False)
    for uckk__jjlwa, gdyzj__qzav in typ.type_to_blk.items():
        ufo__fcckr = getattr(rbc__jyip, f'block_{gdyzj__qzav}')
        jhs__ioob = ListInstance(c.context, c.builder, types.List(
            uckk__jjlwa), ufo__fcckr)
        box__jmubw = c.context.make_constant_array(c.builder, types.Array(
            types.int64, 1, 'C'), np.array(typ.block_to_arr_ind[gdyzj__qzav
            ], dtype=np.int64))
        jodt__arcul = c.context.make_array(types.Array(types.int64, 1, 'C'))(c
            .context, c.builder, box__jmubw)
        with cgutils.for_range(c.builder, jhs__ioob.size) as doaz__are:
            i = doaz__are.index
            qadg__ysby = _getitem_array_single_int(c.context, c.builder,
                types.int64, types.Array(types.int64, 1, 'C'), jodt__arcul, i)
            dbe__obcf = jhs__ioob.getitem(i)
            glty__wqqj = cgutils.alloca_once_value(c.builder, dbe__obcf)
            ilt__cbany = cgutils.alloca_once_value(c.builder, c.context.
                get_constant_null(uckk__jjlwa))
            dzcs__lodq = is_ll_eq(c.builder, glty__wqqj, ilt__cbany)
            with c.builder.if_else(c.builder.and_(dzcs__lodq, c.builder.
                not_(ensure_unboxed))) as (ootw__xisp, yuig__sva):
                with ootw__xisp:
                    balt__ceus = c.pyapi.make_none()
                    c.pyapi.list_setitem(qtb__awfs, qadg__ysby, balt__ceus)
                with yuig__sva:
                    rkupd__dig = cgutils.alloca_once(c.builder, c.context.
                        get_value_type(types.pyobject))
                    with c.builder.if_else(c.builder.and_(dzcs__lodq,
                        kmtw__joe)) as (mozc__ewz, orcdk__vxmf):
                        with mozc__ewz:
                            rfrw__uhgct = get_df_obj_column_codegen(c.
                                context, c.builder, c.pyapi, rbc__jyip.
                                parent, qadg__ysby, uckk__jjlwa)
                            c.builder.store(rfrw__uhgct, rkupd__dig)
                        with orcdk__vxmf:
                            c.context.nrt.incref(c.builder, uckk__jjlwa,
                                dbe__obcf)
                            c.builder.store(c.pyapi.from_native_value(
                                uckk__jjlwa, dbe__obcf, c.env_manager),
                                rkupd__dig)
                    c.pyapi.list_setitem(qtb__awfs, qadg__ysby, c.builder.
                        load(rkupd__dig))
    cyko__wspd = c.pyapi.unserialize(c.pyapi.serialize_object(Table))
    ahs__wet = c.pyapi.call_function_objargs(cyko__wspd, (qtb__awfs,))
    c.pyapi.decref(cyko__wspd)
    c.pyapi.decref(qtb__awfs)
    c.context.nrt.decref(c.builder, typ, val)
    return ahs__wet


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
        rbc__jyip = cgutils.create_struct_proxy(table_type)(context,
            builder, table_arg)
        dfno__lphwv = context.get_constant(types.int64, 0)
        for i, uckk__jjlwa in enumerate(table_type.arr_types):
            ufo__fcckr = getattr(rbc__jyip, f'block_{i}')
            jhs__ioob = ListInstance(context, builder, types.List(
                uckk__jjlwa), ufo__fcckr)
            dfno__lphwv = builder.add(dfno__lphwv, jhs__ioob.size)
        return dfno__lphwv
    sig = types.int64(table_type)
    return sig, codegen


def get_table_data_codegen(context, builder, table_arg, col_ind, table_type):
    arr_type = table_type.arr_types[col_ind]
    rbc__jyip = cgutils.create_struct_proxy(table_type)(context, builder,
        table_arg)
    gdyzj__qzav = table_type.block_nums[col_ind]
    mxiy__bytv = table_type.block_offsets[col_ind]
    ufo__fcckr = getattr(rbc__jyip, f'block_{gdyzj__qzav}')
    jhs__ioob = ListInstance(context, builder, types.List(arr_type), ufo__fcckr
        )
    dbe__obcf = jhs__ioob.getitem(mxiy__bytv)
    return dbe__obcf


@intrinsic
def get_table_data(typingctx, table_type, ind_typ=None):
    assert isinstance(table_type, TableType)
    assert is_overload_constant_int(ind_typ)
    col_ind = get_overload_const_int(ind_typ)
    arr_type = table_type.arr_types[col_ind]

    def codegen(context, builder, sig, args):
        table_arg, gfs__qnz = args
        dbe__obcf = get_table_data_codegen(context, builder, table_arg,
            col_ind, table_type)
        return impl_ret_borrowed(context, builder, arr_type, dbe__obcf)
    sig = arr_type(table_type, ind_typ)
    return sig, codegen


@intrinsic
def del_column(typingctx, table_type, ind_typ=None):
    assert isinstance(table_type, TableType)
    assert is_overload_constant_int(ind_typ)
    col_ind = get_overload_const_int(ind_typ)
    arr_type = table_type.arr_types[col_ind]

    def codegen(context, builder, sig, args):
        table_arg, gfs__qnz = args
        rbc__jyip = cgutils.create_struct_proxy(table_type)(context,
            builder, table_arg)
        gdyzj__qzav = table_type.block_nums[col_ind]
        mxiy__bytv = table_type.block_offsets[col_ind]
        ufo__fcckr = getattr(rbc__jyip, f'block_{gdyzj__qzav}')
        jhs__ioob = ListInstance(context, builder, types.List(arr_type),
            ufo__fcckr)
        dbe__obcf = jhs__ioob.getitem(mxiy__bytv)
        context.nrt.decref(builder, arr_type, dbe__obcf)
        rle__saiw = context.get_constant_null(arr_type)
        jhs__ioob.inititem(mxiy__bytv, rle__saiw, incref=False)
    sig = types.void(table_type, ind_typ)
    return sig, codegen


def set_table_data_codegen(context, builder, in_table_type, in_table,
    out_table_type, arr_type, arr_arg, col_ind, is_new_col):
    in_table = cgutils.create_struct_proxy(in_table_type)(context, builder,
        in_table)
    out_table = cgutils.create_struct_proxy(out_table_type)(context, builder)
    out_table.len = in_table.len
    out_table.parent = in_table.parent
    ssf__dukd = context.get_constant(types.int64, 0)
    mhrrs__kkjs = context.get_constant(types.int64, 1)
    afbxo__cltk = arr_type not in in_table_type.type_to_blk
    for uckk__jjlwa, gdyzj__qzav in out_table_type.type_to_blk.items():
        if uckk__jjlwa in in_table_type.type_to_blk:
            uouy__bpz = in_table_type.type_to_blk[uckk__jjlwa]
            etv__hyms = ListInstance(context, builder, types.List(
                uckk__jjlwa), getattr(in_table, f'block_{uouy__bpz}'))
            context.nrt.incref(builder, types.List(uckk__jjlwa), etv__hyms.
                value)
            setattr(out_table, f'block_{gdyzj__qzav}', etv__hyms.value)
    if afbxo__cltk:
        gfs__qnz, etv__hyms = ListInstance.allocate_ex(context, builder,
            types.List(arr_type), mhrrs__kkjs)
        etv__hyms.size = mhrrs__kkjs
        etv__hyms.inititem(ssf__dukd, arr_arg, incref=True)
        gdyzj__qzav = out_table_type.type_to_blk[arr_type]
        setattr(out_table, f'block_{gdyzj__qzav}', etv__hyms.value)
        if not is_new_col:
            _rm_old_array(col_ind, out_table_type, out_table, in_table_type,
                context, builder)
    else:
        gdyzj__qzav = out_table_type.type_to_blk[arr_type]
        etv__hyms = ListInstance(context, builder, types.List(arr_type),
            getattr(out_table, f'block_{gdyzj__qzav}'))
        if is_new_col:
            n = etv__hyms.size
            jqy__liqm = builder.add(n, mhrrs__kkjs)
            etv__hyms.resize(jqy__liqm)
            etv__hyms.inititem(n, arr_arg, incref=True)
        elif arr_type == in_table_type.arr_types[col_ind]:
            vjrhf__ndg = context.get_constant(types.int64, out_table_type.
                block_offsets[col_ind])
            etv__hyms.setitem(vjrhf__ndg, arr_arg, True)
        else:
            _rm_old_array(col_ind, out_table_type, out_table, in_table_type,
                context, builder)
            vjrhf__ndg = context.get_constant(types.int64, out_table_type.
                block_offsets[col_ind])
            n = etv__hyms.size
            jqy__liqm = builder.add(n, mhrrs__kkjs)
            etv__hyms.resize(jqy__liqm)
            context.nrt.incref(builder, arr_type, etv__hyms.getitem(vjrhf__ndg)
                )
            etv__hyms.move(builder.add(vjrhf__ndg, mhrrs__kkjs), vjrhf__ndg,
                builder.sub(n, vjrhf__ndg))
            etv__hyms.setitem(vjrhf__ndg, arr_arg, incref=True)
    return out_table._getvalue()


def _rm_old_array(col_ind, out_table_type, out_table, in_table_type,
    context, builder):
    buk__jtczn = in_table_type.arr_types[col_ind]
    if buk__jtczn in out_table_type.type_to_blk:
        gdyzj__qzav = out_table_type.type_to_blk[buk__jtczn]
        hcj__mdn = getattr(out_table, f'block_{gdyzj__qzav}')
        oxxlb__zir = types.List(buk__jtczn)
        vjrhf__ndg = context.get_constant(types.int64, in_table_type.
            block_offsets[col_ind])
        uuvq__qnn = oxxlb__zir.dtype(oxxlb__zir, types.intp)
        ffqok__ihdv = context.compile_internal(builder, lambda lst, i: lst.
            pop(i), uuvq__qnn, (hcj__mdn, vjrhf__ndg))
        context.nrt.decref(builder, buk__jtczn, ffqok__ihdv)


@intrinsic
def set_table_data(typingctx, table_type, ind_type, arr_type=None):
    assert isinstance(table_type, TableType), 'invalid input to set_table_data'
    assert is_overload_constant_int(ind_type
        ), 'set_table_data expects const index'
    col_ind = get_overload_const_int(ind_type)
    is_new_col = col_ind == len(table_type.arr_types)
    zic__ool = list(table_type.arr_types)
    if is_new_col:
        zic__ool.append(arr_type)
    else:
        zic__ool[col_ind] = arr_type
    out_table_type = TableType(tuple(zic__ool))

    def codegen(context, builder, sig, args):
        table_arg, gfs__qnz, mxlqm__aqvdp = args
        out_table = set_table_data_codegen(context, builder, table_type,
            table_arg, out_table_type, arr_type, mxlqm__aqvdp, col_ind,
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
    bqh__aeh = args[0]
    if equiv_set.has_shape(bqh__aeh):
        return ArrayAnalysis.AnalyzeResult(shape=equiv_set.get_shape(
            bqh__aeh)[0], pre=[])


ArrayAnalysis._analyze_op_call_bodo_hiframes_table_get_table_data = (
    get_table_data_equiv)


@lower_constant(TableType)
def lower_constant_table(context, builder, table_type, pyval):
    esp__mnjdh = []
    for uckk__jjlwa, gdyzj__qzav in table_type.type_to_blk.items():
        jgn__drrut = len(table_type.block_to_arr_ind[gdyzj__qzav])
        zycp__lkadp = []
        for i in range(jgn__drrut):
            qadg__ysby = table_type.block_to_arr_ind[gdyzj__qzav][i]
            zycp__lkadp.append(pyval.arrays[qadg__ysby])
        esp__mnjdh.append(context.get_constant_generic(builder, types.List(
            uckk__jjlwa), zycp__lkadp))
    iow__ipj = context.get_constant_null(types.pyobject)
    ztput__dtb = context.get_constant(types.int64, 0 if len(pyval.arrays) ==
        0 else len(pyval.arrays[0]))
    return lir.Constant.literal_struct(esp__mnjdh + [iow__ipj, ztput__dtb])


@intrinsic
def init_table(typingctx, table_type, to_str_if_dict_t=None):
    assert isinstance(table_type, TableType), 'table type expected'
    assert is_overload_constant_bool(to_str_if_dict_t
        ), 'constant to_str_if_dict_t expected'
    out_table_type = table_type
    if is_overload_true(to_str_if_dict_t):
        out_table_type = to_str_arr_if_dict_array(table_type)

    def codegen(context, builder, sig, args):
        rbc__jyip = cgutils.create_struct_proxy(out_table_type)(context,
            builder)
        for uckk__jjlwa, gdyzj__qzav in out_table_type.type_to_blk.items():
            mkk__uulw = context.get_constant_null(types.List(uckk__jjlwa))
            setattr(rbc__jyip, f'block_{gdyzj__qzav}', mkk__uulw)
        return rbc__jyip._getvalue()
    sig = out_table_type(table_type, to_str_if_dict_t)
    return sig, codegen


@intrinsic
def get_table_block(typingctx, table_type, blk_type=None):
    assert isinstance(table_type, TableType), 'table type expected'
    assert is_overload_constant_int(blk_type)
    gdyzj__qzav = get_overload_const_int(blk_type)
    arr_type = None
    for uckk__jjlwa, sjn__gfrl in table_type.type_to_blk.items():
        if sjn__gfrl == gdyzj__qzav:
            arr_type = uckk__jjlwa
            break
    assert arr_type is not None, 'invalid table type block'
    dtnu__krgla = types.List(arr_type)

    def codegen(context, builder, sig, args):
        rbc__jyip = cgutils.create_struct_proxy(table_type)(context,
            builder, args[0])
        ufo__fcckr = getattr(rbc__jyip, f'block_{gdyzj__qzav}')
        return impl_ret_borrowed(context, builder, dtnu__krgla, ufo__fcckr)
    sig = dtnu__krgla(table_type, blk_type)
    return sig, codegen


@intrinsic
def ensure_column_unboxed(typingctx, table_type, arr_list_t, ind_t,
    arr_ind_t=None):
    assert isinstance(table_type, TableType), 'table type expected'
    sig = types.none(table_type, arr_list_t, ind_t, arr_ind_t)
    return sig, ensure_column_unboxed_codegen


def ensure_column_unboxed_codegen(context, builder, sig, args):
    from bodo.hiframes.boxing import get_df_obj_column_codegen
    table_arg, xxdvi__uykeg, spcl__onis, fxgq__soajl = args
    vtni__bnl = context.get_python_api(builder)
    rbc__jyip = cgutils.create_struct_proxy(sig.args[0])(context, builder,
        table_arg)
    kmtw__joe = cgutils.is_not_null(builder, rbc__jyip.parent)
    jhs__ioob = ListInstance(context, builder, sig.args[1], xxdvi__uykeg)
    hln__ycoau = jhs__ioob.getitem(spcl__onis)
    glty__wqqj = cgutils.alloca_once_value(builder, hln__ycoau)
    ilt__cbany = cgutils.alloca_once_value(builder, context.
        get_constant_null(sig.args[1].dtype))
    dzcs__lodq = is_ll_eq(builder, glty__wqqj, ilt__cbany)
    with builder.if_then(dzcs__lodq):
        with builder.if_else(kmtw__joe) as (ootw__xisp, yuig__sva):
            with ootw__xisp:
                rkupd__dig = get_df_obj_column_codegen(context, builder,
                    vtni__bnl, rbc__jyip.parent, fxgq__soajl, sig.args[1].dtype
                    )
                dbe__obcf = vtni__bnl.to_native_value(sig.args[1].dtype,
                    rkupd__dig).value
                jhs__ioob.inititem(spcl__onis, dbe__obcf, incref=False)
                vtni__bnl.decref(rkupd__dig)
            with yuig__sva:
                context.call_conv.return_user_exc(builder, BodoError, (
                    'unexpected null table column',))


@intrinsic
def set_table_block(typingctx, table_type, arr_list_type, blk_type=None):
    assert isinstance(table_type, TableType), 'table type expected'
    assert isinstance(arr_list_type, types.List), 'list type expected'
    assert is_overload_constant_int(blk_type), 'blk should be const int'
    gdyzj__qzav = get_overload_const_int(blk_type)

    def codegen(context, builder, sig, args):
        table_arg, oxy__zec, gfs__qnz = args
        in_table = cgutils.create_struct_proxy(table_type)(context, builder,
            table_arg)
        setattr(in_table, f'block_{gdyzj__qzav}', oxy__zec)
        return impl_ret_borrowed(context, builder, table_type, in_table.
            _getvalue())
    sig = table_type(table_type, arr_list_type, blk_type)
    return sig, codegen


@intrinsic
def set_table_len(typingctx, table_type, l_type=None):
    assert isinstance(table_type, TableType), 'table type expected'

    def codegen(context, builder, sig, args):
        table_arg, yxg__oaxl = args
        in_table = cgutils.create_struct_proxy(table_type)(context, builder,
            table_arg)
        in_table.len = yxg__oaxl
        return impl_ret_borrowed(context, builder, table_type, in_table.
            _getvalue())
    sig = table_type(table_type, l_type)
    return sig, codegen


@intrinsic
def alloc_list_like(typingctx, list_type, to_str_if_dict_t=None):
    assert isinstance(list_type, types.List), 'list type expected'
    assert is_overload_constant_bool(to_str_if_dict_t
        ), 'constant to_str_if_dict_t expected'
    dtnu__krgla = list_type
    if is_overload_true(to_str_if_dict_t):
        dtnu__krgla = types.List(to_str_arr_if_dict_array(list_type.dtype))

    def codegen(context, builder, sig, args):
        iul__jgufs = ListInstance(context, builder, list_type, args[0])
        drjc__ydn = iul__jgufs.size
        gfs__qnz, etv__hyms = ListInstance.allocate_ex(context, builder,
            dtnu__krgla, drjc__ydn)
        etv__hyms.size = drjc__ydn
        return etv__hyms.value
    sig = dtnu__krgla(list_type, to_str_if_dict_t)
    return sig, codegen


def _get_idx_length(idx):
    pass


@overload(_get_idx_length)
def overload_get_idx_length(idx, n):
    if is_list_like_index_type(idx) and idx.dtype == types.bool_:
        return lambda idx, n: idx.sum()
    assert isinstance(idx, types.SliceType), 'slice index expected'

    def impl(idx, n):
        lshc__noih = numba.cpython.unicode._normalize_slice(idx, n)
        return numba.cpython.unicode._slice_span(lshc__noih)
    return impl


def gen_table_filter(T, used_cols=None):
    from bodo.utils.conversion import ensure_contig_if_np
    fpitc__upv = {'init_table': init_table, 'get_table_block':
        get_table_block, 'ensure_column_unboxed': ensure_column_unboxed,
        'set_table_block': set_table_block, 'set_table_len': set_table_len,
        'alloc_list_like': alloc_list_like, '_get_idx_length':
        _get_idx_length, 'ensure_contig_if_np': ensure_contig_if_np}
    if used_cols is not None:
        fpitc__upv['used_cols'] = np.array(used_cols, dtype=np.int64)
    vxka__vply = 'def impl(T, idx):\n'
    vxka__vply += f'  T2 = init_table(T, False)\n'
    vxka__vply += f'  l = 0\n'
    if used_cols is not None and len(used_cols) == 0:
        vxka__vply += f'  l = _get_idx_length(idx, len(T))\n'
        vxka__vply += f'  T2 = set_table_len(T2, l)\n'
        vxka__vply += f'  return T2\n'
        ileg__qhhb = {}
        exec(vxka__vply, fpitc__upv, ileg__qhhb)
        return ileg__qhhb['impl']
    if used_cols is not None:
        vxka__vply += f'  used_set = set(used_cols)\n'
    for gdyzj__qzav in T.type_to_blk.values():
        fpitc__upv[f'arr_inds_{gdyzj__qzav}'] = np.array(T.block_to_arr_ind
            [gdyzj__qzav], dtype=np.int64)
        vxka__vply += (
            f'  arr_list_{gdyzj__qzav} = get_table_block(T, {gdyzj__qzav})\n')
        vxka__vply += f"""  out_arr_list_{gdyzj__qzav} = alloc_list_like(arr_list_{gdyzj__qzav}, False)
"""
        vxka__vply += f'  for i in range(len(arr_list_{gdyzj__qzav})):\n'
        vxka__vply += (
            f'    arr_ind_{gdyzj__qzav} = arr_inds_{gdyzj__qzav}[i]\n')
        if used_cols is not None:
            vxka__vply += (
                f'    if arr_ind_{gdyzj__qzav} not in used_set: continue\n')
        vxka__vply += f"""    ensure_column_unboxed(T, arr_list_{gdyzj__qzav}, i, arr_ind_{gdyzj__qzav})
"""
        vxka__vply += f"""    out_arr_{gdyzj__qzav} = ensure_contig_if_np(arr_list_{gdyzj__qzav}[i][idx])
"""
        vxka__vply += f'    l = len(out_arr_{gdyzj__qzav})\n'
        vxka__vply += (
            f'    out_arr_list_{gdyzj__qzav}[i] = out_arr_{gdyzj__qzav}\n')
        vxka__vply += (
            f'  T2 = set_table_block(T2, out_arr_list_{gdyzj__qzav}, {gdyzj__qzav})\n'
            )
    vxka__vply += f'  T2 = set_table_len(T2, l)\n'
    vxka__vply += f'  return T2\n'
    ileg__qhhb = {}
    exec(vxka__vply, fpitc__upv, ileg__qhhb)
    return ileg__qhhb['impl']


@numba.generated_jit(nopython=True, no_cpython_wrapper=True)
def decode_if_dict_table(T):
    vxka__vply = 'def impl(T):\n'
    vxka__vply += f'  T2 = init_table(T, True)\n'
    vxka__vply += f'  l = len(T)\n'
    fpitc__upv = {'init_table': init_table, 'get_table_block':
        get_table_block, 'ensure_column_unboxed': ensure_column_unboxed,
        'set_table_block': set_table_block, 'set_table_len': set_table_len,
        'alloc_list_like': alloc_list_like, 'decode_if_dict_array':
        decode_if_dict_array}
    for gdyzj__qzav in T.type_to_blk.values():
        fpitc__upv[f'arr_inds_{gdyzj__qzav}'] = np.array(T.block_to_arr_ind
            [gdyzj__qzav], dtype=np.int64)
        vxka__vply += (
            f'  arr_list_{gdyzj__qzav} = get_table_block(T, {gdyzj__qzav})\n')
        vxka__vply += f"""  out_arr_list_{gdyzj__qzav} = alloc_list_like(arr_list_{gdyzj__qzav}, True)
"""
        vxka__vply += f'  for i in range(len(arr_list_{gdyzj__qzav})):\n'
        vxka__vply += (
            f'    arr_ind_{gdyzj__qzav} = arr_inds_{gdyzj__qzav}[i]\n')
        vxka__vply += f"""    ensure_column_unboxed(T, arr_list_{gdyzj__qzav}, i, arr_ind_{gdyzj__qzav})
"""
        vxka__vply += f"""    out_arr_{gdyzj__qzav} = decode_if_dict_array(arr_list_{gdyzj__qzav}[i])
"""
        vxka__vply += (
            f'    out_arr_list_{gdyzj__qzav}[i] = out_arr_{gdyzj__qzav}\n')
        vxka__vply += (
            f'  T2 = set_table_block(T2, out_arr_list_{gdyzj__qzav}, {gdyzj__qzav})\n'
            )
    vxka__vply += f'  T2 = set_table_len(T2, l)\n'
    vxka__vply += f'  return T2\n'
    ileg__qhhb = {}
    exec(vxka__vply, fpitc__upv, ileg__qhhb)
    return ileg__qhhb['impl']


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
        rwl__oofqp = [arr_list_tup_typ.dtype.dtype] * len(arr_list_tup_typ)
    else:
        rwl__oofqp = []
        for typ in arr_list_tup_typ:
            if typ.dtype == types.undefined:
                return
            rwl__oofqp.append(typ.dtype)
    assert isinstance(nrows_typ, types.Integer
        ), 'init_runtime_table_from_lists requires an integer length'

    def codegen(context, builder, sig, args):
        hqz__zrun, hro__orll = args
        rbc__jyip = cgutils.create_struct_proxy(table_type)(context, builder)
        rbc__jyip.len = hro__orll
        esp__mnjdh = cgutils.unpack_tuple(builder, hqz__zrun)
        for i, ufo__fcckr in enumerate(esp__mnjdh):
            setattr(rbc__jyip, f'block_{i}', ufo__fcckr)
            context.nrt.incref(builder, types.List(rwl__oofqp[i]), ufo__fcckr)
        return rbc__jyip._getvalue()
    table_type = TableType(tuple(rwl__oofqp), True)
    sig = table_type(arr_list_tup_typ, nrows_typ)
    return sig, codegen
