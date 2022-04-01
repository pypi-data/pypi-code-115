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
            oblt__vzuxu = 0
            fkh__gim = []
            for i in range(usecols[-1] + 1):
                if i == usecols[oblt__vzuxu]:
                    fkh__gim.append(arrs[oblt__vzuxu])
                    oblt__vzuxu += 1
                else:
                    fkh__gim.append(None)
            for urs__kzlue in range(usecols[-1] + 1, num_arrs):
                fkh__gim.append(None)
            self.arrays = fkh__gim
        else:
            self.arrays = arrs
        self.block_0 = arrs

    def __eq__(self, other):
        return isinstance(other, Table) and len(self.arrays) == len(other.
            arrays) and all((gag__zyvt == hrhd__orygh).all() for gag__zyvt,
            hrhd__orygh in zip(self.arrays, other.arrays))

    def __str__(self) ->str:
        return str(self.arrays)

    def to_pandas(self, index=None):
        seox__hwmbn = len(self.arrays)
        gbqms__hjct = dict(zip(range(seox__hwmbn), self.arrays))
        df = pd.DataFrame(gbqms__hjct, index)
        return df


class TableType(types.ArrayCompatible):

    def __init__(self, arr_types, has_runtime_cols=False):
        self.arr_types = arr_types
        self.has_runtime_cols = has_runtime_cols
        sut__lbd = []
        cks__wlzs = []
        hrpp__yyi = {}
        qpo__iwjs = defaultdict(int)
        xqe__pxavp = defaultdict(list)
        if not has_runtime_cols:
            for i, xnmpm__tys in enumerate(arr_types):
                if xnmpm__tys not in hrpp__yyi:
                    hrpp__yyi[xnmpm__tys] = len(hrpp__yyi)
                cje__dpe = hrpp__yyi[xnmpm__tys]
                sut__lbd.append(cje__dpe)
                cks__wlzs.append(qpo__iwjs[cje__dpe])
                qpo__iwjs[cje__dpe] += 1
                xqe__pxavp[cje__dpe].append(i)
        self.block_nums = sut__lbd
        self.block_offsets = cks__wlzs
        self.type_to_blk = hrpp__yyi
        self.block_to_arr_ind = xqe__pxavp
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
    return TableType(tuple(numba.typeof(uxar__qnwb) for uxar__qnwb in val.
        arrays))


@register_model(TableType)
class TableTypeModel(models.StructModel):

    def __init__(self, dmm, fe_type):
        if fe_type.has_runtime_cols:
            dme__sycju = [(f'block_{i}', types.List(xnmpm__tys)) for i,
                xnmpm__tys in enumerate(fe_type.arr_types)]
        else:
            dme__sycju = [(f'block_{cje__dpe}', types.List(xnmpm__tys)) for
                xnmpm__tys, cje__dpe in fe_type.type_to_blk.items()]
        dme__sycju.append(('parent', types.pyobject))
        dme__sycju.append(('len', types.int64))
        super(TableTypeModel, self).__init__(dmm, fe_type, dme__sycju)


make_attribute_wrapper(TableType, 'block_0', 'block_0')
make_attribute_wrapper(TableType, 'len', '_len')


@infer_getattr
class TableTypeAttribute(OverloadedKeyAttributeTemplate):
    key = TableType

    def resolve_shape(self, df):
        return types.Tuple([types.int64, types.int64])


@unbox(TableType)
def unbox_table(typ, val, c):
    ucs__oiorv = c.pyapi.object_getattr_string(val, 'arrays')
    wckb__lkb = cgutils.create_struct_proxy(typ)(c.context, c.builder)
    wckb__lkb.parent = cgutils.get_null_value(wckb__lkb.parent.type)
    srcek__zxsaa = c.pyapi.make_none()
    zoj__tyu = c.context.get_constant(types.int64, 0)
    cev__asr = cgutils.alloca_once_value(c.builder, zoj__tyu)
    for xnmpm__tys, cje__dpe in typ.type_to_blk.items():
        ofedu__ycm = c.context.get_constant(types.int64, len(typ.
            block_to_arr_ind[cje__dpe]))
        urs__kzlue, gpwj__jwtr = ListInstance.allocate_ex(c.context, c.
            builder, types.List(xnmpm__tys), ofedu__ycm)
        gpwj__jwtr.size = ofedu__ycm
        gck__ytlgy = c.context.make_constant_array(c.builder, types.Array(
            types.int64, 1, 'C'), np.array(typ.block_to_arr_ind[cje__dpe],
            dtype=np.int64))
        fhac__zki = c.context.make_array(types.Array(types.int64, 1, 'C'))(c
            .context, c.builder, gck__ytlgy)
        with cgutils.for_range(c.builder, ofedu__ycm) as xiaj__bdeze:
            i = xiaj__bdeze.index
            qsfo__pcikc = _getitem_array_single_int(c.context, c.builder,
                types.int64, types.Array(types.int64, 1, 'C'), fhac__zki, i)
            sbj__imcp = c.pyapi.long_from_longlong(qsfo__pcikc)
            bpcws__fmzw = c.pyapi.object_getitem(ucs__oiorv, sbj__imcp)
            ugfh__glhrd = c.builder.icmp_unsigned('==', bpcws__fmzw,
                srcek__zxsaa)
            with c.builder.if_else(ugfh__glhrd) as (ysb__hwj, hsfb__qiupc):
                with ysb__hwj:
                    adlbg__biczv = c.context.get_constant_null(xnmpm__tys)
                    gpwj__jwtr.inititem(i, adlbg__biczv, incref=False)
                with hsfb__qiupc:
                    gkbn__nrvj = c.pyapi.call_method(bpcws__fmzw, '__len__', ()
                        )
                    eyaq__nvzkn = c.pyapi.long_as_longlong(gkbn__nrvj)
                    c.builder.store(eyaq__nvzkn, cev__asr)
                    c.pyapi.decref(gkbn__nrvj)
                    uxar__qnwb = c.pyapi.to_native_value(xnmpm__tys,
                        bpcws__fmzw).value
                    gpwj__jwtr.inititem(i, uxar__qnwb, incref=False)
            c.pyapi.decref(bpcws__fmzw)
            c.pyapi.decref(sbj__imcp)
        setattr(wckb__lkb, f'block_{cje__dpe}', gpwj__jwtr.value)
    wckb__lkb.len = c.builder.load(cev__asr)
    c.pyapi.decref(ucs__oiorv)
    c.pyapi.decref(srcek__zxsaa)
    axqq__uun = cgutils.is_not_null(c.builder, c.pyapi.err_occurred())
    return NativeValue(wckb__lkb._getvalue(), is_error=axqq__uun)


@box(TableType)
def box_table(typ, val, c, ensure_unboxed=None):
    from bodo.hiframes.boxing import get_df_obj_column_codegen
    wckb__lkb = cgutils.create_struct_proxy(typ)(c.context, c.builder, val)
    if typ.has_runtime_cols:
        wwxb__ouaz = c.context.get_constant(types.int64, 0)
        for i, xnmpm__tys in enumerate(typ.arr_types):
            fkh__gim = getattr(wckb__lkb, f'block_{i}')
            psro__seznl = ListInstance(c.context, c.builder, types.List(
                xnmpm__tys), fkh__gim)
            wwxb__ouaz = c.builder.add(wwxb__ouaz, psro__seznl.size)
        ncrs__ihh = c.pyapi.list_new(wwxb__ouaz)
        qdok__icge = c.context.get_constant(types.int64, 0)
        for i, xnmpm__tys in enumerate(typ.arr_types):
            fkh__gim = getattr(wckb__lkb, f'block_{i}')
            psro__seznl = ListInstance(c.context, c.builder, types.List(
                xnmpm__tys), fkh__gim)
            with cgutils.for_range(c.builder, psro__seznl.size) as xiaj__bdeze:
                i = xiaj__bdeze.index
                uxar__qnwb = psro__seznl.getitem(i)
                c.context.nrt.incref(c.builder, xnmpm__tys, uxar__qnwb)
                idx = c.builder.add(qdok__icge, i)
                c.pyapi.list_setitem(ncrs__ihh, idx, c.pyapi.
                    from_native_value(xnmpm__tys, uxar__qnwb, c.env_manager))
            qdok__icge = c.builder.add(qdok__icge, psro__seznl.size)
        imlz__hzgnx = c.pyapi.unserialize(c.pyapi.serialize_object(Table))
        cli__dwnl = c.pyapi.call_function_objargs(imlz__hzgnx, (ncrs__ihh,))
        c.pyapi.decref(imlz__hzgnx)
        c.pyapi.decref(ncrs__ihh)
        c.context.nrt.decref(c.builder, typ, val)
        return cli__dwnl
    ncrs__ihh = c.pyapi.list_new(c.context.get_constant(types.int64, len(
        typ.arr_types)))
    kqjy__ldumy = cgutils.is_not_null(c.builder, wckb__lkb.parent)
    if ensure_unboxed is None:
        ensure_unboxed = c.context.get_constant(types.bool_, False)
    for xnmpm__tys, cje__dpe in typ.type_to_blk.items():
        fkh__gim = getattr(wckb__lkb, f'block_{cje__dpe}')
        psro__seznl = ListInstance(c.context, c.builder, types.List(
            xnmpm__tys), fkh__gim)
        gck__ytlgy = c.context.make_constant_array(c.builder, types.Array(
            types.int64, 1, 'C'), np.array(typ.block_to_arr_ind[cje__dpe],
            dtype=np.int64))
        fhac__zki = c.context.make_array(types.Array(types.int64, 1, 'C'))(c
            .context, c.builder, gck__ytlgy)
        with cgutils.for_range(c.builder, psro__seznl.size) as xiaj__bdeze:
            i = xiaj__bdeze.index
            qsfo__pcikc = _getitem_array_single_int(c.context, c.builder,
                types.int64, types.Array(types.int64, 1, 'C'), fhac__zki, i)
            uxar__qnwb = psro__seznl.getitem(i)
            gwmfw__ckt = cgutils.alloca_once_value(c.builder, uxar__qnwb)
            eyex__pau = cgutils.alloca_once_value(c.builder, c.context.
                get_constant_null(xnmpm__tys))
            erjc__jxemb = is_ll_eq(c.builder, gwmfw__ckt, eyex__pau)
            with c.builder.if_else(c.builder.and_(erjc__jxemb, c.builder.
                not_(ensure_unboxed))) as (ysb__hwj, hsfb__qiupc):
                with ysb__hwj:
                    srcek__zxsaa = c.pyapi.make_none()
                    c.pyapi.list_setitem(ncrs__ihh, qsfo__pcikc, srcek__zxsaa)
                with hsfb__qiupc:
                    bpcws__fmzw = cgutils.alloca_once(c.builder, c.context.
                        get_value_type(types.pyobject))
                    with c.builder.if_else(c.builder.and_(erjc__jxemb,
                        kqjy__ldumy)) as (blvgg__azi, kuif__wyzon):
                        with blvgg__azi:
                            siknx__qwy = get_df_obj_column_codegen(c.
                                context, c.builder, c.pyapi, wckb__lkb.
                                parent, qsfo__pcikc, xnmpm__tys)
                            c.builder.store(siknx__qwy, bpcws__fmzw)
                        with kuif__wyzon:
                            c.context.nrt.incref(c.builder, xnmpm__tys,
                                uxar__qnwb)
                            c.builder.store(c.pyapi.from_native_value(
                                xnmpm__tys, uxar__qnwb, c.env_manager),
                                bpcws__fmzw)
                    c.pyapi.list_setitem(ncrs__ihh, qsfo__pcikc, c.builder.
                        load(bpcws__fmzw))
    imlz__hzgnx = c.pyapi.unserialize(c.pyapi.serialize_object(Table))
    cli__dwnl = c.pyapi.call_function_objargs(imlz__hzgnx, (ncrs__ihh,))
    c.pyapi.decref(imlz__hzgnx)
    c.pyapi.decref(ncrs__ihh)
    c.context.nrt.decref(c.builder, typ, val)
    return cli__dwnl


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
        wckb__lkb = cgutils.create_struct_proxy(table_type)(context,
            builder, table_arg)
        ngkb__gtwnz = context.get_constant(types.int64, 0)
        for i, xnmpm__tys in enumerate(table_type.arr_types):
            fkh__gim = getattr(wckb__lkb, f'block_{i}')
            psro__seznl = ListInstance(context, builder, types.List(
                xnmpm__tys), fkh__gim)
            ngkb__gtwnz = builder.add(ngkb__gtwnz, psro__seznl.size)
        return ngkb__gtwnz
    sig = types.int64(table_type)
    return sig, codegen


def get_table_data_codegen(context, builder, table_arg, col_ind, table_type):
    arr_type = table_type.arr_types[col_ind]
    wckb__lkb = cgutils.create_struct_proxy(table_type)(context, builder,
        table_arg)
    cje__dpe = table_type.block_nums[col_ind]
    mcghr__ugx = table_type.block_offsets[col_ind]
    fkh__gim = getattr(wckb__lkb, f'block_{cje__dpe}')
    psro__seznl = ListInstance(context, builder, types.List(arr_type), fkh__gim
        )
    uxar__qnwb = psro__seznl.getitem(mcghr__ugx)
    return uxar__qnwb


@intrinsic
def get_table_data(typingctx, table_type, ind_typ=None):
    assert isinstance(table_type, TableType)
    assert is_overload_constant_int(ind_typ)
    col_ind = get_overload_const_int(ind_typ)
    arr_type = table_type.arr_types[col_ind]

    def codegen(context, builder, sig, args):
        table_arg, urs__kzlue = args
        uxar__qnwb = get_table_data_codegen(context, builder, table_arg,
            col_ind, table_type)
        return impl_ret_borrowed(context, builder, arr_type, uxar__qnwb)
    sig = arr_type(table_type, ind_typ)
    return sig, codegen


@intrinsic
def del_column(typingctx, table_type, ind_typ=None):
    assert isinstance(table_type, TableType)
    assert is_overload_constant_int(ind_typ)
    col_ind = get_overload_const_int(ind_typ)
    arr_type = table_type.arr_types[col_ind]

    def codegen(context, builder, sig, args):
        table_arg, urs__kzlue = args
        wckb__lkb = cgutils.create_struct_proxy(table_type)(context,
            builder, table_arg)
        cje__dpe = table_type.block_nums[col_ind]
        mcghr__ugx = table_type.block_offsets[col_ind]
        fkh__gim = getattr(wckb__lkb, f'block_{cje__dpe}')
        psro__seznl = ListInstance(context, builder, types.List(arr_type),
            fkh__gim)
        uxar__qnwb = psro__seznl.getitem(mcghr__ugx)
        context.nrt.decref(builder, arr_type, uxar__qnwb)
        adlbg__biczv = context.get_constant_null(arr_type)
        psro__seznl.inititem(mcghr__ugx, adlbg__biczv, incref=False)
    sig = types.void(table_type, ind_typ)
    return sig, codegen


def set_table_data_codegen(context, builder, in_table_type, in_table,
    out_table_type, arr_type, arr_arg, col_ind, is_new_col):
    in_table = cgutils.create_struct_proxy(in_table_type)(context, builder,
        in_table)
    out_table = cgutils.create_struct_proxy(out_table_type)(context, builder)
    out_table.len = in_table.len
    out_table.parent = in_table.parent
    zoj__tyu = context.get_constant(types.int64, 0)
    qvfq__rimgc = context.get_constant(types.int64, 1)
    ullc__hxv = arr_type not in in_table_type.type_to_blk
    for xnmpm__tys, cje__dpe in out_table_type.type_to_blk.items():
        if xnmpm__tys in in_table_type.type_to_blk:
            dxq__mgzj = in_table_type.type_to_blk[xnmpm__tys]
            gpwj__jwtr = ListInstance(context, builder, types.List(
                xnmpm__tys), getattr(in_table, f'block_{dxq__mgzj}'))
            context.nrt.incref(builder, types.List(xnmpm__tys), gpwj__jwtr.
                value)
            setattr(out_table, f'block_{cje__dpe}', gpwj__jwtr.value)
    if ullc__hxv:
        urs__kzlue, gpwj__jwtr = ListInstance.allocate_ex(context, builder,
            types.List(arr_type), qvfq__rimgc)
        gpwj__jwtr.size = qvfq__rimgc
        gpwj__jwtr.inititem(zoj__tyu, arr_arg, incref=True)
        cje__dpe = out_table_type.type_to_blk[arr_type]
        setattr(out_table, f'block_{cje__dpe}', gpwj__jwtr.value)
        if not is_new_col:
            _rm_old_array(col_ind, out_table_type, out_table, in_table_type,
                context, builder)
    else:
        cje__dpe = out_table_type.type_to_blk[arr_type]
        gpwj__jwtr = ListInstance(context, builder, types.List(arr_type),
            getattr(out_table, f'block_{cje__dpe}'))
        if is_new_col:
            n = gpwj__jwtr.size
            gvkg__ykz = builder.add(n, qvfq__rimgc)
            gpwj__jwtr.resize(gvkg__ykz)
            gpwj__jwtr.inititem(n, arr_arg, incref=True)
        elif arr_type == in_table_type.arr_types[col_ind]:
            gwz__yreb = context.get_constant(types.int64, out_table_type.
                block_offsets[col_ind])
            gpwj__jwtr.setitem(gwz__yreb, arr_arg, True)
        else:
            _rm_old_array(col_ind, out_table_type, out_table, in_table_type,
                context, builder)
            gwz__yreb = context.get_constant(types.int64, out_table_type.
                block_offsets[col_ind])
            n = gpwj__jwtr.size
            gvkg__ykz = builder.add(n, qvfq__rimgc)
            gpwj__jwtr.resize(gvkg__ykz)
            context.nrt.incref(builder, arr_type, gpwj__jwtr.getitem(gwz__yreb)
                )
            gpwj__jwtr.move(builder.add(gwz__yreb, qvfq__rimgc), gwz__yreb,
                builder.sub(n, gwz__yreb))
            gpwj__jwtr.setitem(gwz__yreb, arr_arg, incref=True)
    return out_table._getvalue()


def _rm_old_array(col_ind, out_table_type, out_table, in_table_type,
    context, builder):
    ysy__vyjv = in_table_type.arr_types[col_ind]
    if ysy__vyjv in out_table_type.type_to_blk:
        cje__dpe = out_table_type.type_to_blk[ysy__vyjv]
        ptpv__vneg = getattr(out_table, f'block_{cje__dpe}')
        hfu__qsqc = types.List(ysy__vyjv)
        gwz__yreb = context.get_constant(types.int64, in_table_type.
            block_offsets[col_ind])
        cddax__hke = hfu__qsqc.dtype(hfu__qsqc, types.intp)
        fjc__wvxfj = context.compile_internal(builder, lambda lst, i: lst.
            pop(i), cddax__hke, (ptpv__vneg, gwz__yreb))
        context.nrt.decref(builder, ysy__vyjv, fjc__wvxfj)


@intrinsic
def set_table_data(typingctx, table_type, ind_type, arr_type=None):
    assert isinstance(table_type, TableType), 'invalid input to set_table_data'
    assert is_overload_constant_int(ind_type
        ), 'set_table_data expects const index'
    col_ind = get_overload_const_int(ind_type)
    is_new_col = col_ind == len(table_type.arr_types)
    tayw__wgce = list(table_type.arr_types)
    if is_new_col:
        tayw__wgce.append(arr_type)
    else:
        tayw__wgce[col_ind] = arr_type
    out_table_type = TableType(tuple(tayw__wgce))

    def codegen(context, builder, sig, args):
        table_arg, urs__kzlue, rfgef__wvvi = args
        out_table = set_table_data_codegen(context, builder, table_type,
            table_arg, out_table_type, arr_type, rfgef__wvvi, col_ind,
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
    quy__zdso = args[0]
    if equiv_set.has_shape(quy__zdso):
        return ArrayAnalysis.AnalyzeResult(shape=equiv_set.get_shape(
            quy__zdso)[0], pre=[])


ArrayAnalysis._analyze_op_call_bodo_hiframes_table_get_table_data = (
    get_table_data_equiv)


@lower_constant(TableType)
def lower_constant_table(context, builder, table_type, pyval):
    dwdkv__qiqgn = []
    for xnmpm__tys, cje__dpe in table_type.type_to_blk.items():
        dchqc__hoxon = len(table_type.block_to_arr_ind[cje__dpe])
        rieh__citgu = []
        for i in range(dchqc__hoxon):
            qsfo__pcikc = table_type.block_to_arr_ind[cje__dpe][i]
            rieh__citgu.append(pyval.arrays[qsfo__pcikc])
        dwdkv__qiqgn.append(context.get_constant_generic(builder, types.
            List(xnmpm__tys), rieh__citgu))
    qkem__ynu = context.get_constant_null(types.pyobject)
    qfucw__sdnsv = context.get_constant(types.int64, 0 if len(pyval.arrays) ==
        0 else len(pyval.arrays[0]))
    return lir.Constant.literal_struct(dwdkv__qiqgn + [qkem__ynu, qfucw__sdnsv]
        )


@intrinsic
def init_table(typingctx, table_type, to_str_if_dict_t=None):
    assert isinstance(table_type, TableType), 'table type expected'
    assert is_overload_constant_bool(to_str_if_dict_t
        ), 'constant to_str_if_dict_t expected'
    out_table_type = table_type
    if is_overload_true(to_str_if_dict_t):
        out_table_type = to_str_arr_if_dict_array(table_type)

    def codegen(context, builder, sig, args):
        wckb__lkb = cgutils.create_struct_proxy(out_table_type)(context,
            builder)
        for xnmpm__tys, cje__dpe in out_table_type.type_to_blk.items():
            qsmrt__crow = context.get_constant_null(types.List(xnmpm__tys))
            setattr(wckb__lkb, f'block_{cje__dpe}', qsmrt__crow)
        return wckb__lkb._getvalue()
    sig = out_table_type(table_type, to_str_if_dict_t)
    return sig, codegen


@intrinsic
def get_table_block(typingctx, table_type, blk_type=None):
    assert isinstance(table_type, TableType), 'table type expected'
    assert is_overload_constant_int(blk_type)
    cje__dpe = get_overload_const_int(blk_type)
    arr_type = None
    for xnmpm__tys, hrhd__orygh in table_type.type_to_blk.items():
        if hrhd__orygh == cje__dpe:
            arr_type = xnmpm__tys
            break
    assert arr_type is not None, 'invalid table type block'
    jzkw__kfdhn = types.List(arr_type)

    def codegen(context, builder, sig, args):
        wckb__lkb = cgutils.create_struct_proxy(table_type)(context,
            builder, args[0])
        fkh__gim = getattr(wckb__lkb, f'block_{cje__dpe}')
        return impl_ret_borrowed(context, builder, jzkw__kfdhn, fkh__gim)
    sig = jzkw__kfdhn(table_type, blk_type)
    return sig, codegen


@intrinsic
def ensure_column_unboxed(typingctx, table_type, arr_list_t, ind_t,
    arr_ind_t=None):
    assert isinstance(table_type, TableType), 'table type expected'
    sig = types.none(table_type, arr_list_t, ind_t, arr_ind_t)
    return sig, ensure_column_unboxed_codegen


def ensure_column_unboxed_codegen(context, builder, sig, args):
    from bodo.hiframes.boxing import get_df_obj_column_codegen
    table_arg, iuvyu__xwxgp, wkgbq__svi, rdm__htg = args
    idiyy__dmbii = context.get_python_api(builder)
    wckb__lkb = cgutils.create_struct_proxy(sig.args[0])(context, builder,
        table_arg)
    kqjy__ldumy = cgutils.is_not_null(builder, wckb__lkb.parent)
    psro__seznl = ListInstance(context, builder, sig.args[1], iuvyu__xwxgp)
    djm__iwbq = psro__seznl.getitem(wkgbq__svi)
    gwmfw__ckt = cgutils.alloca_once_value(builder, djm__iwbq)
    eyex__pau = cgutils.alloca_once_value(builder, context.
        get_constant_null(sig.args[1].dtype))
    erjc__jxemb = is_ll_eq(builder, gwmfw__ckt, eyex__pau)
    with builder.if_then(erjc__jxemb):
        with builder.if_else(kqjy__ldumy) as (ysb__hwj, hsfb__qiupc):
            with ysb__hwj:
                bpcws__fmzw = get_df_obj_column_codegen(context, builder,
                    idiyy__dmbii, wckb__lkb.parent, rdm__htg, sig.args[1].dtype
                    )
                uxar__qnwb = idiyy__dmbii.to_native_value(sig.args[1].dtype,
                    bpcws__fmzw).value
                psro__seznl.inititem(wkgbq__svi, uxar__qnwb, incref=False)
                idiyy__dmbii.decref(bpcws__fmzw)
            with hsfb__qiupc:
                context.call_conv.return_user_exc(builder, BodoError, (
                    'unexpected null table column',))


@intrinsic
def set_table_block(typingctx, table_type, arr_list_type, blk_type=None):
    assert isinstance(table_type, TableType), 'table type expected'
    assert isinstance(arr_list_type, types.List), 'list type expected'
    assert is_overload_constant_int(blk_type), 'blk should be const int'
    cje__dpe = get_overload_const_int(blk_type)

    def codegen(context, builder, sig, args):
        table_arg, rue__nyi, urs__kzlue = args
        in_table = cgutils.create_struct_proxy(table_type)(context, builder,
            table_arg)
        setattr(in_table, f'block_{cje__dpe}', rue__nyi)
        return impl_ret_borrowed(context, builder, table_type, in_table.
            _getvalue())
    sig = table_type(table_type, arr_list_type, blk_type)
    return sig, codegen


@intrinsic
def set_table_len(typingctx, table_type, l_type=None):
    assert isinstance(table_type, TableType), 'table type expected'

    def codegen(context, builder, sig, args):
        table_arg, kbg__vewo = args
        in_table = cgutils.create_struct_proxy(table_type)(context, builder,
            table_arg)
        in_table.len = kbg__vewo
        return impl_ret_borrowed(context, builder, table_type, in_table.
            _getvalue())
    sig = table_type(table_type, l_type)
    return sig, codegen


@intrinsic
def alloc_list_like(typingctx, list_type, to_str_if_dict_t=None):
    assert isinstance(list_type, types.List), 'list type expected'
    assert is_overload_constant_bool(to_str_if_dict_t
        ), 'constant to_str_if_dict_t expected'
    jzkw__kfdhn = list_type
    if is_overload_true(to_str_if_dict_t):
        jzkw__kfdhn = types.List(to_str_arr_if_dict_array(list_type.dtype))

    def codegen(context, builder, sig, args):
        uaf__ceud = ListInstance(context, builder, list_type, args[0])
        orlaw__djd = uaf__ceud.size
        urs__kzlue, gpwj__jwtr = ListInstance.allocate_ex(context, builder,
            jzkw__kfdhn, orlaw__djd)
        gpwj__jwtr.size = orlaw__djd
        return gpwj__jwtr.value
    sig = jzkw__kfdhn(list_type, to_str_if_dict_t)
    return sig, codegen


def _get_idx_length(idx):
    pass


@overload(_get_idx_length)
def overload_get_idx_length(idx, n):
    if is_list_like_index_type(idx) and idx.dtype == types.bool_:
        return lambda idx, n: idx.sum()
    assert isinstance(idx, types.SliceType), 'slice index expected'

    def impl(idx, n):
        rgrg__ysm = numba.cpython.unicode._normalize_slice(idx, n)
        return numba.cpython.unicode._slice_span(rgrg__ysm)
    return impl


def gen_table_filter(T, used_cols=None):
    from bodo.utils.conversion import ensure_contig_if_np
    fzt__whlx = {'init_table': init_table, 'get_table_block':
        get_table_block, 'ensure_column_unboxed': ensure_column_unboxed,
        'set_table_block': set_table_block, 'set_table_len': set_table_len,
        'alloc_list_like': alloc_list_like, '_get_idx_length':
        _get_idx_length, 'ensure_contig_if_np': ensure_contig_if_np}
    if used_cols is not None:
        fzt__whlx['used_cols'] = np.array(used_cols, dtype=np.int64)
    wbuuv__xhcrp = 'def impl(T, idx):\n'
    wbuuv__xhcrp += f'  T2 = init_table(T, False)\n'
    wbuuv__xhcrp += f'  l = 0\n'
    if used_cols is not None and len(used_cols) == 0:
        wbuuv__xhcrp += f'  l = _get_idx_length(idx, len(T))\n'
        wbuuv__xhcrp += f'  T2 = set_table_len(T2, l)\n'
        wbuuv__xhcrp += f'  return T2\n'
        gwgp__ktgf = {}
        exec(wbuuv__xhcrp, fzt__whlx, gwgp__ktgf)
        return gwgp__ktgf['impl']
    if used_cols is not None:
        wbuuv__xhcrp += f'  used_set = set(used_cols)\n'
    for cje__dpe in T.type_to_blk.values():
        fzt__whlx[f'arr_inds_{cje__dpe}'] = np.array(T.block_to_arr_ind[
            cje__dpe], dtype=np.int64)
        wbuuv__xhcrp += (
            f'  arr_list_{cje__dpe} = get_table_block(T, {cje__dpe})\n')
        wbuuv__xhcrp += (
            f'  out_arr_list_{cje__dpe} = alloc_list_like(arr_list_{cje__dpe}, False)\n'
            )
        wbuuv__xhcrp += f'  for i in range(len(arr_list_{cje__dpe})):\n'
        wbuuv__xhcrp += f'    arr_ind_{cje__dpe} = arr_inds_{cje__dpe}[i]\n'
        if used_cols is not None:
            wbuuv__xhcrp += (
                f'    if arr_ind_{cje__dpe} not in used_set: continue\n')
        wbuuv__xhcrp += f"""    ensure_column_unboxed(T, arr_list_{cje__dpe}, i, arr_ind_{cje__dpe})
"""
        wbuuv__xhcrp += f"""    out_arr_{cje__dpe} = ensure_contig_if_np(arr_list_{cje__dpe}[i][idx])
"""
        wbuuv__xhcrp += f'    l = len(out_arr_{cje__dpe})\n'
        wbuuv__xhcrp += (
            f'    out_arr_list_{cje__dpe}[i] = out_arr_{cje__dpe}\n')
        wbuuv__xhcrp += (
            f'  T2 = set_table_block(T2, out_arr_list_{cje__dpe}, {cje__dpe})\n'
            )
    wbuuv__xhcrp += f'  T2 = set_table_len(T2, l)\n'
    wbuuv__xhcrp += f'  return T2\n'
    gwgp__ktgf = {}
    exec(wbuuv__xhcrp, fzt__whlx, gwgp__ktgf)
    return gwgp__ktgf['impl']


@numba.generated_jit(nopython=True, no_cpython_wrapper=True)
def decode_if_dict_table(T):
    wbuuv__xhcrp = 'def impl(T):\n'
    wbuuv__xhcrp += f'  T2 = init_table(T, True)\n'
    wbuuv__xhcrp += f'  l = len(T)\n'
    fzt__whlx = {'init_table': init_table, 'get_table_block':
        get_table_block, 'ensure_column_unboxed': ensure_column_unboxed,
        'set_table_block': set_table_block, 'set_table_len': set_table_len,
        'alloc_list_like': alloc_list_like, 'decode_if_dict_array':
        decode_if_dict_array}
    for cje__dpe in T.type_to_blk.values():
        fzt__whlx[f'arr_inds_{cje__dpe}'] = np.array(T.block_to_arr_ind[
            cje__dpe], dtype=np.int64)
        wbuuv__xhcrp += (
            f'  arr_list_{cje__dpe} = get_table_block(T, {cje__dpe})\n')
        wbuuv__xhcrp += (
            f'  out_arr_list_{cje__dpe} = alloc_list_like(arr_list_{cje__dpe}, True)\n'
            )
        wbuuv__xhcrp += f'  for i in range(len(arr_list_{cje__dpe})):\n'
        wbuuv__xhcrp += f'    arr_ind_{cje__dpe} = arr_inds_{cje__dpe}[i]\n'
        wbuuv__xhcrp += f"""    ensure_column_unboxed(T, arr_list_{cje__dpe}, i, arr_ind_{cje__dpe})
"""
        wbuuv__xhcrp += (
            f'    out_arr_{cje__dpe} = decode_if_dict_array(arr_list_{cje__dpe}[i])\n'
            )
        wbuuv__xhcrp += (
            f'    out_arr_list_{cje__dpe}[i] = out_arr_{cje__dpe}\n')
        wbuuv__xhcrp += (
            f'  T2 = set_table_block(T2, out_arr_list_{cje__dpe}, {cje__dpe})\n'
            )
    wbuuv__xhcrp += f'  T2 = set_table_len(T2, l)\n'
    wbuuv__xhcrp += f'  return T2\n'
    gwgp__ktgf = {}
    exec(wbuuv__xhcrp, fzt__whlx, gwgp__ktgf)
    return gwgp__ktgf['impl']


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
        qds__ijqs = [arr_list_tup_typ.dtype.dtype] * len(arr_list_tup_typ)
    else:
        qds__ijqs = []
        for typ in arr_list_tup_typ:
            if typ.dtype == types.undefined:
                return
            qds__ijqs.append(typ.dtype)
    assert isinstance(nrows_typ, types.Integer
        ), 'init_runtime_table_from_lists requires an integer length'

    def codegen(context, builder, sig, args):
        bpquo__pye, ypcsa__ncj = args
        wckb__lkb = cgutils.create_struct_proxy(table_type)(context, builder)
        wckb__lkb.len = ypcsa__ncj
        dwdkv__qiqgn = cgutils.unpack_tuple(builder, bpquo__pye)
        for i, fkh__gim in enumerate(dwdkv__qiqgn):
            setattr(wckb__lkb, f'block_{i}', fkh__gim)
            context.nrt.incref(builder, types.List(qds__ijqs[i]), fkh__gim)
        return wckb__lkb._getvalue()
    table_type = TableType(tuple(qds__ijqs), True)
    sig = table_type(arr_list_tup_typ, nrows_typ)
    return sig, codegen
