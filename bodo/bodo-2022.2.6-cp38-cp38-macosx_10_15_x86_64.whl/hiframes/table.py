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
            pdpfk__uac = 0
            usya__ake = []
            for i in range(usecols[-1] + 1):
                if i == usecols[pdpfk__uac]:
                    usya__ake.append(arrs[pdpfk__uac])
                    pdpfk__uac += 1
                else:
                    usya__ake.append(None)
            for rdu__dan in range(usecols[-1] + 1, num_arrs):
                usya__ake.append(None)
            self.arrays = usya__ake
        else:
            self.arrays = arrs
        self.block_0 = arrs

    def __eq__(self, other):
        return isinstance(other, Table) and len(self.arrays) == len(other.
            arrays) and all((ldk__pyrm == kkp__wive).all() for ldk__pyrm,
            kkp__wive in zip(self.arrays, other.arrays))

    def __str__(self) ->str:
        return str(self.arrays)

    def to_pandas(self, index=None):
        ljve__ccr = len(self.arrays)
        odc__vjm = dict(zip(range(ljve__ccr), self.arrays))
        df = pd.DataFrame(odc__vjm, index)
        return df


class TableType(types.ArrayCompatible):

    def __init__(self, arr_types, has_runtime_cols=False):
        self.arr_types = arr_types
        self.has_runtime_cols = has_runtime_cols
        hti__fuurz = []
        pny__nma = []
        zaj__rkk = {}
        xbl__ydptv = defaultdict(int)
        lvjko__qtg = defaultdict(list)
        if not has_runtime_cols:
            for i, nyvbb__rlfuu in enumerate(arr_types):
                if nyvbb__rlfuu not in zaj__rkk:
                    zaj__rkk[nyvbb__rlfuu] = len(zaj__rkk)
                afvr__hftj = zaj__rkk[nyvbb__rlfuu]
                hti__fuurz.append(afvr__hftj)
                pny__nma.append(xbl__ydptv[afvr__hftj])
                xbl__ydptv[afvr__hftj] += 1
                lvjko__qtg[afvr__hftj].append(i)
        self.block_nums = hti__fuurz
        self.block_offsets = pny__nma
        self.type_to_blk = zaj__rkk
        self.block_to_arr_ind = lvjko__qtg
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
    return TableType(tuple(numba.typeof(nzu__pwzde) for nzu__pwzde in val.
        arrays))


@register_model(TableType)
class TableTypeModel(models.StructModel):

    def __init__(self, dmm, fe_type):
        if fe_type.has_runtime_cols:
            mzhr__olfaf = [(f'block_{i}', types.List(nyvbb__rlfuu)) for i,
                nyvbb__rlfuu in enumerate(fe_type.arr_types)]
        else:
            mzhr__olfaf = [(f'block_{afvr__hftj}', types.List(nyvbb__rlfuu)
                ) for nyvbb__rlfuu, afvr__hftj in fe_type.type_to_blk.items()]
        mzhr__olfaf.append(('parent', types.pyobject))
        mzhr__olfaf.append(('len', types.int64))
        super(TableTypeModel, self).__init__(dmm, fe_type, mzhr__olfaf)


make_attribute_wrapper(TableType, 'block_0', 'block_0')
make_attribute_wrapper(TableType, 'len', '_len')


@infer_getattr
class TableTypeAttribute(OverloadedKeyAttributeTemplate):
    key = TableType

    def resolve_shape(self, df):
        return types.Tuple([types.int64, types.int64])


@unbox(TableType)
def unbox_table(typ, val, c):
    fuyha__fuzoo = c.pyapi.object_getattr_string(val, 'arrays')
    fmwbx__qgjew = cgutils.create_struct_proxy(typ)(c.context, c.builder)
    fmwbx__qgjew.parent = cgutils.get_null_value(fmwbx__qgjew.parent.type)
    czy__ddil = c.pyapi.make_none()
    hapd__lviv = c.context.get_constant(types.int64, 0)
    stjcg__zqxsr = cgutils.alloca_once_value(c.builder, hapd__lviv)
    for nyvbb__rlfuu, afvr__hftj in typ.type_to_blk.items():
        bmf__fcmv = c.context.get_constant(types.int64, len(typ.
            block_to_arr_ind[afvr__hftj]))
        rdu__dan, bhj__yqmp = ListInstance.allocate_ex(c.context, c.builder,
            types.List(nyvbb__rlfuu), bmf__fcmv)
        bhj__yqmp.size = bmf__fcmv
        zfbi__awifm = c.context.make_constant_array(c.builder, types.Array(
            types.int64, 1, 'C'), np.array(typ.block_to_arr_ind[afvr__hftj],
            dtype=np.int64))
        isjs__hoj = c.context.make_array(types.Array(types.int64, 1, 'C'))(c
            .context, c.builder, zfbi__awifm)
        with cgutils.for_range(c.builder, bmf__fcmv) as wbhyf__pwg:
            i = wbhyf__pwg.index
            fmz__hdq = _getitem_array_single_int(c.context, c.builder,
                types.int64, types.Array(types.int64, 1, 'C'), isjs__hoj, i)
            okioa__wjx = c.pyapi.long_from_longlong(fmz__hdq)
            qtzo__oxecm = c.pyapi.object_getitem(fuyha__fuzoo, okioa__wjx)
            rwuxl__tsgao = c.builder.icmp_unsigned('==', qtzo__oxecm, czy__ddil
                )
            with c.builder.if_else(rwuxl__tsgao) as (pna__ozn, jixjx__gwl):
                with pna__ozn:
                    gmrj__rgqw = c.context.get_constant_null(nyvbb__rlfuu)
                    bhj__yqmp.inititem(i, gmrj__rgqw, incref=False)
                with jixjx__gwl:
                    dhct__ehae = c.pyapi.call_method(qtzo__oxecm, '__len__', ()
                        )
                    pxw__pxjas = c.pyapi.long_as_longlong(dhct__ehae)
                    c.builder.store(pxw__pxjas, stjcg__zqxsr)
                    c.pyapi.decref(dhct__ehae)
                    nzu__pwzde = c.pyapi.to_native_value(nyvbb__rlfuu,
                        qtzo__oxecm).value
                    bhj__yqmp.inititem(i, nzu__pwzde, incref=False)
            c.pyapi.decref(qtzo__oxecm)
            c.pyapi.decref(okioa__wjx)
        setattr(fmwbx__qgjew, f'block_{afvr__hftj}', bhj__yqmp.value)
    fmwbx__qgjew.len = c.builder.load(stjcg__zqxsr)
    c.pyapi.decref(fuyha__fuzoo)
    c.pyapi.decref(czy__ddil)
    cezk__rgyvi = cgutils.is_not_null(c.builder, c.pyapi.err_occurred())
    return NativeValue(fmwbx__qgjew._getvalue(), is_error=cezk__rgyvi)


@box(TableType)
def box_table(typ, val, c, ensure_unboxed=None):
    from bodo.hiframes.boxing import get_df_obj_column_codegen
    fmwbx__qgjew = cgutils.create_struct_proxy(typ)(c.context, c.builder, val)
    if typ.has_runtime_cols:
        jpmm__hhmqb = c.context.get_constant(types.int64, 0)
        for i, nyvbb__rlfuu in enumerate(typ.arr_types):
            usya__ake = getattr(fmwbx__qgjew, f'block_{i}')
            xav__mic = ListInstance(c.context, c.builder, types.List(
                nyvbb__rlfuu), usya__ake)
            jpmm__hhmqb = c.builder.add(jpmm__hhmqb, xav__mic.size)
        hzr__qvp = c.pyapi.list_new(jpmm__hhmqb)
        uebg__tfq = c.context.get_constant(types.int64, 0)
        for i, nyvbb__rlfuu in enumerate(typ.arr_types):
            usya__ake = getattr(fmwbx__qgjew, f'block_{i}')
            xav__mic = ListInstance(c.context, c.builder, types.List(
                nyvbb__rlfuu), usya__ake)
            with cgutils.for_range(c.builder, xav__mic.size) as wbhyf__pwg:
                i = wbhyf__pwg.index
                nzu__pwzde = xav__mic.getitem(i)
                c.context.nrt.incref(c.builder, nyvbb__rlfuu, nzu__pwzde)
                idx = c.builder.add(uebg__tfq, i)
                c.pyapi.list_setitem(hzr__qvp, idx, c.pyapi.
                    from_native_value(nyvbb__rlfuu, nzu__pwzde, c.env_manager))
            uebg__tfq = c.builder.add(uebg__tfq, xav__mic.size)
        okfss__khd = c.pyapi.unserialize(c.pyapi.serialize_object(Table))
        lgt__ndd = c.pyapi.call_function_objargs(okfss__khd, (hzr__qvp,))
        c.pyapi.decref(okfss__khd)
        c.pyapi.decref(hzr__qvp)
        c.context.nrt.decref(c.builder, typ, val)
        return lgt__ndd
    hzr__qvp = c.pyapi.list_new(c.context.get_constant(types.int64, len(typ
        .arr_types)))
    atqu__hjw = cgutils.is_not_null(c.builder, fmwbx__qgjew.parent)
    if ensure_unboxed is None:
        ensure_unboxed = c.context.get_constant(types.bool_, False)
    for nyvbb__rlfuu, afvr__hftj in typ.type_to_blk.items():
        usya__ake = getattr(fmwbx__qgjew, f'block_{afvr__hftj}')
        xav__mic = ListInstance(c.context, c.builder, types.List(
            nyvbb__rlfuu), usya__ake)
        zfbi__awifm = c.context.make_constant_array(c.builder, types.Array(
            types.int64, 1, 'C'), np.array(typ.block_to_arr_ind[afvr__hftj],
            dtype=np.int64))
        isjs__hoj = c.context.make_array(types.Array(types.int64, 1, 'C'))(c
            .context, c.builder, zfbi__awifm)
        with cgutils.for_range(c.builder, xav__mic.size) as wbhyf__pwg:
            i = wbhyf__pwg.index
            fmz__hdq = _getitem_array_single_int(c.context, c.builder,
                types.int64, types.Array(types.int64, 1, 'C'), isjs__hoj, i)
            nzu__pwzde = xav__mic.getitem(i)
            ihcpy__jjs = cgutils.alloca_once_value(c.builder, nzu__pwzde)
            vog__dozdl = cgutils.alloca_once_value(c.builder, c.context.
                get_constant_null(nyvbb__rlfuu))
            rybl__jzfmp = is_ll_eq(c.builder, ihcpy__jjs, vog__dozdl)
            with c.builder.if_else(c.builder.and_(rybl__jzfmp, c.builder.
                not_(ensure_unboxed))) as (pna__ozn, jixjx__gwl):
                with pna__ozn:
                    czy__ddil = c.pyapi.make_none()
                    c.pyapi.list_setitem(hzr__qvp, fmz__hdq, czy__ddil)
                with jixjx__gwl:
                    qtzo__oxecm = cgutils.alloca_once(c.builder, c.context.
                        get_value_type(types.pyobject))
                    with c.builder.if_else(c.builder.and_(rybl__jzfmp,
                        atqu__hjw)) as (shku__xtad, qoz__eszep):
                        with shku__xtad:
                            kuqq__zxotm = get_df_obj_column_codegen(c.
                                context, c.builder, c.pyapi, fmwbx__qgjew.
                                parent, fmz__hdq, nyvbb__rlfuu)
                            c.builder.store(kuqq__zxotm, qtzo__oxecm)
                        with qoz__eszep:
                            c.context.nrt.incref(c.builder, nyvbb__rlfuu,
                                nzu__pwzde)
                            c.builder.store(c.pyapi.from_native_value(
                                nyvbb__rlfuu, nzu__pwzde, c.env_manager),
                                qtzo__oxecm)
                    c.pyapi.list_setitem(hzr__qvp, fmz__hdq, c.builder.load
                        (qtzo__oxecm))
    okfss__khd = c.pyapi.unserialize(c.pyapi.serialize_object(Table))
    lgt__ndd = c.pyapi.call_function_objargs(okfss__khd, (hzr__qvp,))
    c.pyapi.decref(okfss__khd)
    c.pyapi.decref(hzr__qvp)
    c.context.nrt.decref(c.builder, typ, val)
    return lgt__ndd


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
        fmwbx__qgjew = cgutils.create_struct_proxy(table_type)(context,
            builder, table_arg)
        edf__ypmoy = context.get_constant(types.int64, 0)
        for i, nyvbb__rlfuu in enumerate(table_type.arr_types):
            usya__ake = getattr(fmwbx__qgjew, f'block_{i}')
            xav__mic = ListInstance(context, builder, types.List(
                nyvbb__rlfuu), usya__ake)
            edf__ypmoy = builder.add(edf__ypmoy, xav__mic.size)
        return edf__ypmoy
    sig = types.int64(table_type)
    return sig, codegen


def get_table_data_codegen(context, builder, table_arg, col_ind, table_type):
    arr_type = table_type.arr_types[col_ind]
    fmwbx__qgjew = cgutils.create_struct_proxy(table_type)(context, builder,
        table_arg)
    afvr__hftj = table_type.block_nums[col_ind]
    zryp__utv = table_type.block_offsets[col_ind]
    usya__ake = getattr(fmwbx__qgjew, f'block_{afvr__hftj}')
    xav__mic = ListInstance(context, builder, types.List(arr_type), usya__ake)
    nzu__pwzde = xav__mic.getitem(zryp__utv)
    return nzu__pwzde


@intrinsic
def get_table_data(typingctx, table_type, ind_typ=None):
    assert isinstance(table_type, TableType)
    assert is_overload_constant_int(ind_typ)
    col_ind = get_overload_const_int(ind_typ)
    arr_type = table_type.arr_types[col_ind]

    def codegen(context, builder, sig, args):
        table_arg, rdu__dan = args
        nzu__pwzde = get_table_data_codegen(context, builder, table_arg,
            col_ind, table_type)
        return impl_ret_borrowed(context, builder, arr_type, nzu__pwzde)
    sig = arr_type(table_type, ind_typ)
    return sig, codegen


@intrinsic
def del_column(typingctx, table_type, ind_typ=None):
    assert isinstance(table_type, TableType)
    assert is_overload_constant_int(ind_typ)
    col_ind = get_overload_const_int(ind_typ)
    arr_type = table_type.arr_types[col_ind]

    def codegen(context, builder, sig, args):
        table_arg, rdu__dan = args
        fmwbx__qgjew = cgutils.create_struct_proxy(table_type)(context,
            builder, table_arg)
        afvr__hftj = table_type.block_nums[col_ind]
        zryp__utv = table_type.block_offsets[col_ind]
        usya__ake = getattr(fmwbx__qgjew, f'block_{afvr__hftj}')
        xav__mic = ListInstance(context, builder, types.List(arr_type),
            usya__ake)
        nzu__pwzde = xav__mic.getitem(zryp__utv)
        context.nrt.decref(builder, arr_type, nzu__pwzde)
        gmrj__rgqw = context.get_constant_null(arr_type)
        xav__mic.inititem(zryp__utv, gmrj__rgqw, incref=False)
    sig = types.void(table_type, ind_typ)
    return sig, codegen


def set_table_data_codegen(context, builder, in_table_type, in_table,
    out_table_type, arr_type, arr_arg, col_ind, is_new_col):
    in_table = cgutils.create_struct_proxy(in_table_type)(context, builder,
        in_table)
    out_table = cgutils.create_struct_proxy(out_table_type)(context, builder)
    out_table.len = in_table.len
    out_table.parent = in_table.parent
    hapd__lviv = context.get_constant(types.int64, 0)
    ixrkv__two = context.get_constant(types.int64, 1)
    dydey__dxug = arr_type not in in_table_type.type_to_blk
    for nyvbb__rlfuu, afvr__hftj in out_table_type.type_to_blk.items():
        if nyvbb__rlfuu in in_table_type.type_to_blk:
            hag__wye = in_table_type.type_to_blk[nyvbb__rlfuu]
            bhj__yqmp = ListInstance(context, builder, types.List(
                nyvbb__rlfuu), getattr(in_table, f'block_{hag__wye}'))
            context.nrt.incref(builder, types.List(nyvbb__rlfuu), bhj__yqmp
                .value)
            setattr(out_table, f'block_{afvr__hftj}', bhj__yqmp.value)
    if dydey__dxug:
        rdu__dan, bhj__yqmp = ListInstance.allocate_ex(context, builder,
            types.List(arr_type), ixrkv__two)
        bhj__yqmp.size = ixrkv__two
        bhj__yqmp.inititem(hapd__lviv, arr_arg, incref=True)
        afvr__hftj = out_table_type.type_to_blk[arr_type]
        setattr(out_table, f'block_{afvr__hftj}', bhj__yqmp.value)
        if not is_new_col:
            _rm_old_array(col_ind, out_table_type, out_table, in_table_type,
                context, builder)
    else:
        afvr__hftj = out_table_type.type_to_blk[arr_type]
        bhj__yqmp = ListInstance(context, builder, types.List(arr_type),
            getattr(out_table, f'block_{afvr__hftj}'))
        if is_new_col:
            n = bhj__yqmp.size
            sga__mhci = builder.add(n, ixrkv__two)
            bhj__yqmp.resize(sga__mhci)
            bhj__yqmp.inititem(n, arr_arg, incref=True)
        elif arr_type == in_table_type.arr_types[col_ind]:
            znl__pezxx = context.get_constant(types.int64, out_table_type.
                block_offsets[col_ind])
            bhj__yqmp.setitem(znl__pezxx, arr_arg, True)
        else:
            _rm_old_array(col_ind, out_table_type, out_table, in_table_type,
                context, builder)
            znl__pezxx = context.get_constant(types.int64, out_table_type.
                block_offsets[col_ind])
            n = bhj__yqmp.size
            sga__mhci = builder.add(n, ixrkv__two)
            bhj__yqmp.resize(sga__mhci)
            context.nrt.incref(builder, arr_type, bhj__yqmp.getitem(znl__pezxx)
                )
            bhj__yqmp.move(builder.add(znl__pezxx, ixrkv__two), znl__pezxx,
                builder.sub(n, znl__pezxx))
            bhj__yqmp.setitem(znl__pezxx, arr_arg, incref=True)
    return out_table._getvalue()


def _rm_old_array(col_ind, out_table_type, out_table, in_table_type,
    context, builder):
    animb__wufr = in_table_type.arr_types[col_ind]
    if animb__wufr in out_table_type.type_to_blk:
        afvr__hftj = out_table_type.type_to_blk[animb__wufr]
        kddfq__msc = getattr(out_table, f'block_{afvr__hftj}')
        bxur__cduhi = types.List(animb__wufr)
        znl__pezxx = context.get_constant(types.int64, in_table_type.
            block_offsets[col_ind])
        kvw__bvoco = bxur__cduhi.dtype(bxur__cduhi, types.intp)
        rrsk__qjjj = context.compile_internal(builder, lambda lst, i: lst.
            pop(i), kvw__bvoco, (kddfq__msc, znl__pezxx))
        context.nrt.decref(builder, animb__wufr, rrsk__qjjj)


@intrinsic
def set_table_data(typingctx, table_type, ind_type, arr_type=None):
    assert isinstance(table_type, TableType), 'invalid input to set_table_data'
    assert is_overload_constant_int(ind_type
        ), 'set_table_data expects const index'
    col_ind = get_overload_const_int(ind_type)
    is_new_col = col_ind == len(table_type.arr_types)
    vthcj__kzs = list(table_type.arr_types)
    if is_new_col:
        vthcj__kzs.append(arr_type)
    else:
        vthcj__kzs[col_ind] = arr_type
    out_table_type = TableType(tuple(vthcj__kzs))

    def codegen(context, builder, sig, args):
        table_arg, rdu__dan, dip__pigxv = args
        out_table = set_table_data_codegen(context, builder, table_type,
            table_arg, out_table_type, arr_type, dip__pigxv, col_ind,
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
    daukz__zdx = args[0]
    if equiv_set.has_shape(daukz__zdx):
        return ArrayAnalysis.AnalyzeResult(shape=equiv_set.get_shape(
            daukz__zdx)[0], pre=[])


ArrayAnalysis._analyze_op_call_bodo_hiframes_table_get_table_data = (
    get_table_data_equiv)


@lower_constant(TableType)
def lower_constant_table(context, builder, table_type, pyval):
    fueg__uymze = []
    for nyvbb__rlfuu, afvr__hftj in table_type.type_to_blk.items():
        ritx__uktu = len(table_type.block_to_arr_ind[afvr__hftj])
        hhhjc__sxy = []
        for i in range(ritx__uktu):
            fmz__hdq = table_type.block_to_arr_ind[afvr__hftj][i]
            hhhjc__sxy.append(pyval.arrays[fmz__hdq])
        fueg__uymze.append(context.get_constant_generic(builder, types.List
            (nyvbb__rlfuu), hhhjc__sxy))
    qieeb__nyhn = context.get_constant_null(types.pyobject)
    jkp__wef = context.get_constant(types.int64, 0 if len(pyval.arrays) == 
        0 else len(pyval.arrays[0]))
    return lir.Constant.literal_struct(fueg__uymze + [qieeb__nyhn, jkp__wef])


@intrinsic
def init_table(typingctx, table_type, to_str_if_dict_t=None):
    assert isinstance(table_type, TableType), 'table type expected'
    assert is_overload_constant_bool(to_str_if_dict_t
        ), 'constant to_str_if_dict_t expected'
    out_table_type = table_type
    if is_overload_true(to_str_if_dict_t):
        out_table_type = to_str_arr_if_dict_array(table_type)

    def codegen(context, builder, sig, args):
        fmwbx__qgjew = cgutils.create_struct_proxy(out_table_type)(context,
            builder)
        for nyvbb__rlfuu, afvr__hftj in out_table_type.type_to_blk.items():
            nznqg__wtuii = context.get_constant_null(types.List(nyvbb__rlfuu))
            setattr(fmwbx__qgjew, f'block_{afvr__hftj}', nznqg__wtuii)
        return fmwbx__qgjew._getvalue()
    sig = out_table_type(table_type, to_str_if_dict_t)
    return sig, codegen


@intrinsic
def get_table_block(typingctx, table_type, blk_type=None):
    assert isinstance(table_type, TableType), 'table type expected'
    assert is_overload_constant_int(blk_type)
    afvr__hftj = get_overload_const_int(blk_type)
    arr_type = None
    for nyvbb__rlfuu, kkp__wive in table_type.type_to_blk.items():
        if kkp__wive == afvr__hftj:
            arr_type = nyvbb__rlfuu
            break
    assert arr_type is not None, 'invalid table type block'
    paoi__cjfg = types.List(arr_type)

    def codegen(context, builder, sig, args):
        fmwbx__qgjew = cgutils.create_struct_proxy(table_type)(context,
            builder, args[0])
        usya__ake = getattr(fmwbx__qgjew, f'block_{afvr__hftj}')
        return impl_ret_borrowed(context, builder, paoi__cjfg, usya__ake)
    sig = paoi__cjfg(table_type, blk_type)
    return sig, codegen


@intrinsic
def ensure_column_unboxed(typingctx, table_type, arr_list_t, ind_t,
    arr_ind_t=None):
    assert isinstance(table_type, TableType), 'table type expected'
    sig = types.none(table_type, arr_list_t, ind_t, arr_ind_t)
    return sig, ensure_column_unboxed_codegen


def ensure_column_unboxed_codegen(context, builder, sig, args):
    from bodo.hiframes.boxing import get_df_obj_column_codegen
    table_arg, xsxdb__rrhfa, vkvsm__vxv, kvbv__hqulx = args
    mluk__mjq = context.get_python_api(builder)
    fmwbx__qgjew = cgutils.create_struct_proxy(sig.args[0])(context,
        builder, table_arg)
    atqu__hjw = cgutils.is_not_null(builder, fmwbx__qgjew.parent)
    xav__mic = ListInstance(context, builder, sig.args[1], xsxdb__rrhfa)
    uthd__xruc = xav__mic.getitem(vkvsm__vxv)
    ihcpy__jjs = cgutils.alloca_once_value(builder, uthd__xruc)
    vog__dozdl = cgutils.alloca_once_value(builder, context.
        get_constant_null(sig.args[1].dtype))
    rybl__jzfmp = is_ll_eq(builder, ihcpy__jjs, vog__dozdl)
    with builder.if_then(rybl__jzfmp):
        with builder.if_else(atqu__hjw) as (pna__ozn, jixjx__gwl):
            with pna__ozn:
                qtzo__oxecm = get_df_obj_column_codegen(context, builder,
                    mluk__mjq, fmwbx__qgjew.parent, kvbv__hqulx, sig.args[1
                    ].dtype)
                nzu__pwzde = mluk__mjq.to_native_value(sig.args[1].dtype,
                    qtzo__oxecm).value
                xav__mic.inititem(vkvsm__vxv, nzu__pwzde, incref=False)
                mluk__mjq.decref(qtzo__oxecm)
            with jixjx__gwl:
                context.call_conv.return_user_exc(builder, BodoError, (
                    'unexpected null table column',))


@intrinsic
def set_table_block(typingctx, table_type, arr_list_type, blk_type=None):
    assert isinstance(table_type, TableType), 'table type expected'
    assert isinstance(arr_list_type, types.List), 'list type expected'
    assert is_overload_constant_int(blk_type), 'blk should be const int'
    afvr__hftj = get_overload_const_int(blk_type)

    def codegen(context, builder, sig, args):
        table_arg, hgn__min, rdu__dan = args
        in_table = cgutils.create_struct_proxy(table_type)(context, builder,
            table_arg)
        setattr(in_table, f'block_{afvr__hftj}', hgn__min)
        return impl_ret_borrowed(context, builder, table_type, in_table.
            _getvalue())
    sig = table_type(table_type, arr_list_type, blk_type)
    return sig, codegen


@intrinsic
def set_table_len(typingctx, table_type, l_type=None):
    assert isinstance(table_type, TableType), 'table type expected'

    def codegen(context, builder, sig, args):
        table_arg, tqaqv__wggg = args
        in_table = cgutils.create_struct_proxy(table_type)(context, builder,
            table_arg)
        in_table.len = tqaqv__wggg
        return impl_ret_borrowed(context, builder, table_type, in_table.
            _getvalue())
    sig = table_type(table_type, l_type)
    return sig, codegen


@intrinsic
def alloc_list_like(typingctx, list_type, to_str_if_dict_t=None):
    assert isinstance(list_type, types.List), 'list type expected'
    assert is_overload_constant_bool(to_str_if_dict_t
        ), 'constant to_str_if_dict_t expected'
    paoi__cjfg = list_type
    if is_overload_true(to_str_if_dict_t):
        paoi__cjfg = types.List(to_str_arr_if_dict_array(list_type.dtype))

    def codegen(context, builder, sig, args):
        iynt__qypmu = ListInstance(context, builder, list_type, args[0])
        jjbj__pkfya = iynt__qypmu.size
        rdu__dan, bhj__yqmp = ListInstance.allocate_ex(context, builder,
            paoi__cjfg, jjbj__pkfya)
        bhj__yqmp.size = jjbj__pkfya
        return bhj__yqmp.value
    sig = paoi__cjfg(list_type, to_str_if_dict_t)
    return sig, codegen


def _get_idx_length(idx):
    pass


@overload(_get_idx_length)
def overload_get_idx_length(idx, n):
    if is_list_like_index_type(idx) and idx.dtype == types.bool_:
        return lambda idx, n: idx.sum()
    assert isinstance(idx, types.SliceType), 'slice index expected'

    def impl(idx, n):
        ykfh__udfmq = numba.cpython.unicode._normalize_slice(idx, n)
        return numba.cpython.unicode._slice_span(ykfh__udfmq)
    return impl


def gen_table_filter(T, used_cols=None):
    from bodo.utils.conversion import ensure_contig_if_np
    vjrk__ecxdn = {'init_table': init_table, 'get_table_block':
        get_table_block, 'ensure_column_unboxed': ensure_column_unboxed,
        'set_table_block': set_table_block, 'set_table_len': set_table_len,
        'alloc_list_like': alloc_list_like, '_get_idx_length':
        _get_idx_length, 'ensure_contig_if_np': ensure_contig_if_np}
    if used_cols is not None:
        vjrk__ecxdn['used_cols'] = np.array(used_cols, dtype=np.int64)
    abi__bfjsa = 'def impl(T, idx):\n'
    abi__bfjsa += f'  T2 = init_table(T, False)\n'
    abi__bfjsa += f'  l = 0\n'
    if used_cols is not None and len(used_cols) == 0:
        abi__bfjsa += f'  l = _get_idx_length(idx, len(T))\n'
        abi__bfjsa += f'  T2 = set_table_len(T2, l)\n'
        abi__bfjsa += f'  return T2\n'
        fxa__aud = {}
        exec(abi__bfjsa, vjrk__ecxdn, fxa__aud)
        return fxa__aud['impl']
    if used_cols is not None:
        abi__bfjsa += f'  used_set = set(used_cols)\n'
    for afvr__hftj in T.type_to_blk.values():
        vjrk__ecxdn[f'arr_inds_{afvr__hftj}'] = np.array(T.block_to_arr_ind
            [afvr__hftj], dtype=np.int64)
        abi__bfjsa += (
            f'  arr_list_{afvr__hftj} = get_table_block(T, {afvr__hftj})\n')
        abi__bfjsa += f"""  out_arr_list_{afvr__hftj} = alloc_list_like(arr_list_{afvr__hftj}, False)
"""
        abi__bfjsa += f'  for i in range(len(arr_list_{afvr__hftj})):\n'
        abi__bfjsa += f'    arr_ind_{afvr__hftj} = arr_inds_{afvr__hftj}[i]\n'
        if used_cols is not None:
            abi__bfjsa += (
                f'    if arr_ind_{afvr__hftj} not in used_set: continue\n')
        abi__bfjsa += f"""    ensure_column_unboxed(T, arr_list_{afvr__hftj}, i, arr_ind_{afvr__hftj})
"""
        abi__bfjsa += f"""    out_arr_{afvr__hftj} = ensure_contig_if_np(arr_list_{afvr__hftj}[i][idx])
"""
        abi__bfjsa += f'    l = len(out_arr_{afvr__hftj})\n'
        abi__bfjsa += (
            f'    out_arr_list_{afvr__hftj}[i] = out_arr_{afvr__hftj}\n')
        abi__bfjsa += (
            f'  T2 = set_table_block(T2, out_arr_list_{afvr__hftj}, {afvr__hftj})\n'
            )
    abi__bfjsa += f'  T2 = set_table_len(T2, l)\n'
    abi__bfjsa += f'  return T2\n'
    fxa__aud = {}
    exec(abi__bfjsa, vjrk__ecxdn, fxa__aud)
    return fxa__aud['impl']


@numba.generated_jit(nopython=True, no_cpython_wrapper=True)
def decode_if_dict_table(T):
    abi__bfjsa = 'def impl(T):\n'
    abi__bfjsa += f'  T2 = init_table(T, True)\n'
    abi__bfjsa += f'  l = len(T)\n'
    vjrk__ecxdn = {'init_table': init_table, 'get_table_block':
        get_table_block, 'ensure_column_unboxed': ensure_column_unboxed,
        'set_table_block': set_table_block, 'set_table_len': set_table_len,
        'alloc_list_like': alloc_list_like, 'decode_if_dict_array':
        decode_if_dict_array}
    for afvr__hftj in T.type_to_blk.values():
        vjrk__ecxdn[f'arr_inds_{afvr__hftj}'] = np.array(T.block_to_arr_ind
            [afvr__hftj], dtype=np.int64)
        abi__bfjsa += (
            f'  arr_list_{afvr__hftj} = get_table_block(T, {afvr__hftj})\n')
        abi__bfjsa += f"""  out_arr_list_{afvr__hftj} = alloc_list_like(arr_list_{afvr__hftj}, True)
"""
        abi__bfjsa += f'  for i in range(len(arr_list_{afvr__hftj})):\n'
        abi__bfjsa += f'    arr_ind_{afvr__hftj} = arr_inds_{afvr__hftj}[i]\n'
        abi__bfjsa += f"""    ensure_column_unboxed(T, arr_list_{afvr__hftj}, i, arr_ind_{afvr__hftj})
"""
        abi__bfjsa += (
            f'    out_arr_{afvr__hftj} = decode_if_dict_array(arr_list_{afvr__hftj}[i])\n'
            )
        abi__bfjsa += (
            f'    out_arr_list_{afvr__hftj}[i] = out_arr_{afvr__hftj}\n')
        abi__bfjsa += (
            f'  T2 = set_table_block(T2, out_arr_list_{afvr__hftj}, {afvr__hftj})\n'
            )
    abi__bfjsa += f'  T2 = set_table_len(T2, l)\n'
    abi__bfjsa += f'  return T2\n'
    fxa__aud = {}
    exec(abi__bfjsa, vjrk__ecxdn, fxa__aud)
    return fxa__aud['impl']


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
        uhtbt__ylpl = [arr_list_tup_typ.dtype.dtype] * len(arr_list_tup_typ)
    else:
        uhtbt__ylpl = []
        for typ in arr_list_tup_typ:
            if typ.dtype == types.undefined:
                return
            uhtbt__ylpl.append(typ.dtype)
    assert isinstance(nrows_typ, types.Integer
        ), 'init_runtime_table_from_lists requires an integer length'

    def codegen(context, builder, sig, args):
        efupn__cwl, nbz__jayn = args
        fmwbx__qgjew = cgutils.create_struct_proxy(table_type)(context, builder
            )
        fmwbx__qgjew.len = nbz__jayn
        fueg__uymze = cgutils.unpack_tuple(builder, efupn__cwl)
        for i, usya__ake in enumerate(fueg__uymze):
            setattr(fmwbx__qgjew, f'block_{i}', usya__ake)
            context.nrt.incref(builder, types.List(uhtbt__ylpl[i]), usya__ake)
        return fmwbx__qgjew._getvalue()
    table_type = TableType(tuple(uhtbt__ylpl), True)
    sig = table_type(arr_list_tup_typ, nrows_typ)
    return sig, codegen
