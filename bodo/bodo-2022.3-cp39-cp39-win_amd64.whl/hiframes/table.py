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
            vdnt__llajx = 0
            ymm__fmgrn = []
            for i in range(usecols[-1] + 1):
                if i == usecols[vdnt__llajx]:
                    ymm__fmgrn.append(arrs[vdnt__llajx])
                    vdnt__llajx += 1
                else:
                    ymm__fmgrn.append(None)
            for kchw__yyyqs in range(usecols[-1] + 1, num_arrs):
                ymm__fmgrn.append(None)
            self.arrays = ymm__fmgrn
        else:
            self.arrays = arrs
        self.block_0 = arrs

    def __eq__(self, other):
        return isinstance(other, Table) and len(self.arrays) == len(other.
            arrays) and all((ced__iuwd == erx__wvyl).all() for ced__iuwd,
            erx__wvyl in zip(self.arrays, other.arrays))

    def __str__(self) ->str:
        return str(self.arrays)

    def to_pandas(self, index=None):
        sbio__ivy = len(self.arrays)
        deoa__fwz = dict(zip(range(sbio__ivy), self.arrays))
        df = pd.DataFrame(deoa__fwz, index)
        return df


class TableType(types.ArrayCompatible):

    def __init__(self, arr_types, has_runtime_cols=False):
        self.arr_types = arr_types
        self.has_runtime_cols = has_runtime_cols
        rycqb__pmiq = []
        rrz__ajfms = []
        qopb__dfur = {}
        mgbe__zmnc = defaultdict(int)
        gqg__jseoa = defaultdict(list)
        if not has_runtime_cols:
            for i, pzw__smwgx in enumerate(arr_types):
                if pzw__smwgx not in qopb__dfur:
                    qopb__dfur[pzw__smwgx] = len(qopb__dfur)
                nwg__ytia = qopb__dfur[pzw__smwgx]
                rycqb__pmiq.append(nwg__ytia)
                rrz__ajfms.append(mgbe__zmnc[nwg__ytia])
                mgbe__zmnc[nwg__ytia] += 1
                gqg__jseoa[nwg__ytia].append(i)
        self.block_nums = rycqb__pmiq
        self.block_offsets = rrz__ajfms
        self.type_to_blk = qopb__dfur
        self.block_to_arr_ind = gqg__jseoa
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
    return TableType(tuple(numba.typeof(hjfq__klnpg) for hjfq__klnpg in val
        .arrays))


@register_model(TableType)
class TableTypeModel(models.StructModel):

    def __init__(self, dmm, fe_type):
        if fe_type.has_runtime_cols:
            hfesi__cvxp = [(f'block_{i}', types.List(pzw__smwgx)) for i,
                pzw__smwgx in enumerate(fe_type.arr_types)]
        else:
            hfesi__cvxp = [(f'block_{nwg__ytia}', types.List(pzw__smwgx)) for
                pzw__smwgx, nwg__ytia in fe_type.type_to_blk.items()]
        hfesi__cvxp.append(('parent', types.pyobject))
        hfesi__cvxp.append(('len', types.int64))
        super(TableTypeModel, self).__init__(dmm, fe_type, hfesi__cvxp)


make_attribute_wrapper(TableType, 'block_0', 'block_0')
make_attribute_wrapper(TableType, 'len', '_len')


@infer_getattr
class TableTypeAttribute(OverloadedKeyAttributeTemplate):
    key = TableType

    def resolve_shape(self, df):
        return types.Tuple([types.int64, types.int64])


@unbox(TableType)
def unbox_table(typ, val, c):
    lkj__hzr = c.pyapi.object_getattr_string(val, 'arrays')
    synbk__ulh = cgutils.create_struct_proxy(typ)(c.context, c.builder)
    synbk__ulh.parent = cgutils.get_null_value(synbk__ulh.parent.type)
    tvc__ved = c.pyapi.make_none()
    qksnv__aeyib = c.context.get_constant(types.int64, 0)
    yih__emxd = cgutils.alloca_once_value(c.builder, qksnv__aeyib)
    for pzw__smwgx, nwg__ytia in typ.type_to_blk.items():
        sab__jianl = c.context.get_constant(types.int64, len(typ.
            block_to_arr_ind[nwg__ytia]))
        kchw__yyyqs, hzobe__rtqz = ListInstance.allocate_ex(c.context, c.
            builder, types.List(pzw__smwgx), sab__jianl)
        hzobe__rtqz.size = sab__jianl
        mjprx__ezeo = c.context.make_constant_array(c.builder, types.Array(
            types.int64, 1, 'C'), np.array(typ.block_to_arr_ind[nwg__ytia],
            dtype=np.int64))
        ynn__ponjw = c.context.make_array(types.Array(types.int64, 1, 'C'))(c
            .context, c.builder, mjprx__ezeo)
        with cgutils.for_range(c.builder, sab__jianl) as ncusq__jrlx:
            i = ncusq__jrlx.index
            mmbo__dbby = _getitem_array_single_int(c.context, c.builder,
                types.int64, types.Array(types.int64, 1, 'C'), ynn__ponjw, i)
            gxsr__yhnpu = c.pyapi.long_from_longlong(mmbo__dbby)
            eahtx__uojpp = c.pyapi.object_getitem(lkj__hzr, gxsr__yhnpu)
            qhvdd__dttvs = c.builder.icmp_unsigned('==', eahtx__uojpp, tvc__ved
                )
            with c.builder.if_else(qhvdd__dttvs) as (acd__pru, lid__vojxq):
                with acd__pru:
                    vsx__qvu = c.context.get_constant_null(pzw__smwgx)
                    hzobe__rtqz.inititem(i, vsx__qvu, incref=False)
                with lid__vojxq:
                    qkx__hzo = c.pyapi.call_method(eahtx__uojpp, '__len__', ())
                    qewee__hypi = c.pyapi.long_as_longlong(qkx__hzo)
                    c.builder.store(qewee__hypi, yih__emxd)
                    c.pyapi.decref(qkx__hzo)
                    hjfq__klnpg = c.pyapi.to_native_value(pzw__smwgx,
                        eahtx__uojpp).value
                    hzobe__rtqz.inititem(i, hjfq__klnpg, incref=False)
            c.pyapi.decref(eahtx__uojpp)
            c.pyapi.decref(gxsr__yhnpu)
        setattr(synbk__ulh, f'block_{nwg__ytia}', hzobe__rtqz.value)
    synbk__ulh.len = c.builder.load(yih__emxd)
    c.pyapi.decref(lkj__hzr)
    c.pyapi.decref(tvc__ved)
    vqwn__nvfvz = cgutils.is_not_null(c.builder, c.pyapi.err_occurred())
    return NativeValue(synbk__ulh._getvalue(), is_error=vqwn__nvfvz)


@box(TableType)
def box_table(typ, val, c, ensure_unboxed=None):
    from bodo.hiframes.boxing import get_df_obj_column_codegen
    synbk__ulh = cgutils.create_struct_proxy(typ)(c.context, c.builder, val)
    if typ.has_runtime_cols:
        bid__rgx = c.context.get_constant(types.int64, 0)
        for i, pzw__smwgx in enumerate(typ.arr_types):
            ymm__fmgrn = getattr(synbk__ulh, f'block_{i}')
            pjw__qhi = ListInstance(c.context, c.builder, types.List(
                pzw__smwgx), ymm__fmgrn)
            bid__rgx = c.builder.add(bid__rgx, pjw__qhi.size)
        sqvs__lziim = c.pyapi.list_new(bid__rgx)
        cnmsk__qjzvd = c.context.get_constant(types.int64, 0)
        for i, pzw__smwgx in enumerate(typ.arr_types):
            ymm__fmgrn = getattr(synbk__ulh, f'block_{i}')
            pjw__qhi = ListInstance(c.context, c.builder, types.List(
                pzw__smwgx), ymm__fmgrn)
            with cgutils.for_range(c.builder, pjw__qhi.size) as ncusq__jrlx:
                i = ncusq__jrlx.index
                hjfq__klnpg = pjw__qhi.getitem(i)
                c.context.nrt.incref(c.builder, pzw__smwgx, hjfq__klnpg)
                idx = c.builder.add(cnmsk__qjzvd, i)
                c.pyapi.list_setitem(sqvs__lziim, idx, c.pyapi.
                    from_native_value(pzw__smwgx, hjfq__klnpg, c.env_manager))
            cnmsk__qjzvd = c.builder.add(cnmsk__qjzvd, pjw__qhi.size)
        dqocg__nfaev = c.pyapi.unserialize(c.pyapi.serialize_object(Table))
        aog__iwk = c.pyapi.call_function_objargs(dqocg__nfaev, (sqvs__lziim,))
        c.pyapi.decref(dqocg__nfaev)
        c.pyapi.decref(sqvs__lziim)
        c.context.nrt.decref(c.builder, typ, val)
        return aog__iwk
    sqvs__lziim = c.pyapi.list_new(c.context.get_constant(types.int64, len(
        typ.arr_types)))
    tfyt__ehptd = cgutils.is_not_null(c.builder, synbk__ulh.parent)
    if ensure_unboxed is None:
        ensure_unboxed = c.context.get_constant(types.bool_, False)
    for pzw__smwgx, nwg__ytia in typ.type_to_blk.items():
        ymm__fmgrn = getattr(synbk__ulh, f'block_{nwg__ytia}')
        pjw__qhi = ListInstance(c.context, c.builder, types.List(pzw__smwgx
            ), ymm__fmgrn)
        mjprx__ezeo = c.context.make_constant_array(c.builder, types.Array(
            types.int64, 1, 'C'), np.array(typ.block_to_arr_ind[nwg__ytia],
            dtype=np.int64))
        ynn__ponjw = c.context.make_array(types.Array(types.int64, 1, 'C'))(c
            .context, c.builder, mjprx__ezeo)
        with cgutils.for_range(c.builder, pjw__qhi.size) as ncusq__jrlx:
            i = ncusq__jrlx.index
            mmbo__dbby = _getitem_array_single_int(c.context, c.builder,
                types.int64, types.Array(types.int64, 1, 'C'), ynn__ponjw, i)
            hjfq__klnpg = pjw__qhi.getitem(i)
            cjtm__zuf = cgutils.alloca_once_value(c.builder, hjfq__klnpg)
            jpo__jip = cgutils.alloca_once_value(c.builder, c.context.
                get_constant_null(pzw__smwgx))
            uvt__qno = is_ll_eq(c.builder, cjtm__zuf, jpo__jip)
            with c.builder.if_else(c.builder.and_(uvt__qno, c.builder.not_(
                ensure_unboxed))) as (acd__pru, lid__vojxq):
                with acd__pru:
                    tvc__ved = c.pyapi.make_none()
                    c.pyapi.list_setitem(sqvs__lziim, mmbo__dbby, tvc__ved)
                with lid__vojxq:
                    eahtx__uojpp = cgutils.alloca_once(c.builder, c.context
                        .get_value_type(types.pyobject))
                    with c.builder.if_else(c.builder.and_(uvt__qno,
                        tfyt__ehptd)) as (scal__enx, ahc__lggtm):
                        with scal__enx:
                            fuk__som = get_df_obj_column_codegen(c.context,
                                c.builder, c.pyapi, synbk__ulh.parent,
                                mmbo__dbby, pzw__smwgx)
                            c.builder.store(fuk__som, eahtx__uojpp)
                        with ahc__lggtm:
                            c.context.nrt.incref(c.builder, pzw__smwgx,
                                hjfq__klnpg)
                            c.builder.store(c.pyapi.from_native_value(
                                pzw__smwgx, hjfq__klnpg, c.env_manager),
                                eahtx__uojpp)
                    c.pyapi.list_setitem(sqvs__lziim, mmbo__dbby, c.builder
                        .load(eahtx__uojpp))
    dqocg__nfaev = c.pyapi.unserialize(c.pyapi.serialize_object(Table))
    aog__iwk = c.pyapi.call_function_objargs(dqocg__nfaev, (sqvs__lziim,))
    c.pyapi.decref(dqocg__nfaev)
    c.pyapi.decref(sqvs__lziim)
    c.context.nrt.decref(c.builder, typ, val)
    return aog__iwk


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
        synbk__ulh = cgutils.create_struct_proxy(table_type)(context,
            builder, table_arg)
        aqt__hvc = context.get_constant(types.int64, 0)
        for i, pzw__smwgx in enumerate(table_type.arr_types):
            ymm__fmgrn = getattr(synbk__ulh, f'block_{i}')
            pjw__qhi = ListInstance(context, builder, types.List(pzw__smwgx
                ), ymm__fmgrn)
            aqt__hvc = builder.add(aqt__hvc, pjw__qhi.size)
        return aqt__hvc
    sig = types.int64(table_type)
    return sig, codegen


def get_table_data_codegen(context, builder, table_arg, col_ind, table_type):
    arr_type = table_type.arr_types[col_ind]
    synbk__ulh = cgutils.create_struct_proxy(table_type)(context, builder,
        table_arg)
    nwg__ytia = table_type.block_nums[col_ind]
    btdfx__ohtxl = table_type.block_offsets[col_ind]
    ymm__fmgrn = getattr(synbk__ulh, f'block_{nwg__ytia}')
    pjw__qhi = ListInstance(context, builder, types.List(arr_type), ymm__fmgrn)
    hjfq__klnpg = pjw__qhi.getitem(btdfx__ohtxl)
    return hjfq__klnpg


@intrinsic
def get_table_data(typingctx, table_type, ind_typ=None):
    assert isinstance(table_type, TableType)
    assert is_overload_constant_int(ind_typ)
    col_ind = get_overload_const_int(ind_typ)
    arr_type = table_type.arr_types[col_ind]

    def codegen(context, builder, sig, args):
        table_arg, kchw__yyyqs = args
        hjfq__klnpg = get_table_data_codegen(context, builder, table_arg,
            col_ind, table_type)
        return impl_ret_borrowed(context, builder, arr_type, hjfq__klnpg)
    sig = arr_type(table_type, ind_typ)
    return sig, codegen


@intrinsic
def del_column(typingctx, table_type, ind_typ=None):
    assert isinstance(table_type, TableType)
    assert is_overload_constant_int(ind_typ)
    col_ind = get_overload_const_int(ind_typ)
    arr_type = table_type.arr_types[col_ind]

    def codegen(context, builder, sig, args):
        table_arg, kchw__yyyqs = args
        synbk__ulh = cgutils.create_struct_proxy(table_type)(context,
            builder, table_arg)
        nwg__ytia = table_type.block_nums[col_ind]
        btdfx__ohtxl = table_type.block_offsets[col_ind]
        ymm__fmgrn = getattr(synbk__ulh, f'block_{nwg__ytia}')
        pjw__qhi = ListInstance(context, builder, types.List(arr_type),
            ymm__fmgrn)
        hjfq__klnpg = pjw__qhi.getitem(btdfx__ohtxl)
        context.nrt.decref(builder, arr_type, hjfq__klnpg)
        vsx__qvu = context.get_constant_null(arr_type)
        pjw__qhi.inititem(btdfx__ohtxl, vsx__qvu, incref=False)
    sig = types.void(table_type, ind_typ)
    return sig, codegen


def set_table_data_codegen(context, builder, in_table_type, in_table,
    out_table_type, arr_type, arr_arg, col_ind, is_new_col):
    in_table = cgutils.create_struct_proxy(in_table_type)(context, builder,
        in_table)
    out_table = cgutils.create_struct_proxy(out_table_type)(context, builder)
    out_table.len = in_table.len
    out_table.parent = in_table.parent
    qksnv__aeyib = context.get_constant(types.int64, 0)
    vwpya__eyxvg = context.get_constant(types.int64, 1)
    mxyvf__vhm = arr_type not in in_table_type.type_to_blk
    for pzw__smwgx, nwg__ytia in out_table_type.type_to_blk.items():
        if pzw__smwgx in in_table_type.type_to_blk:
            fkq__okcs = in_table_type.type_to_blk[pzw__smwgx]
            hzobe__rtqz = ListInstance(context, builder, types.List(
                pzw__smwgx), getattr(in_table, f'block_{fkq__okcs}'))
            context.nrt.incref(builder, types.List(pzw__smwgx), hzobe__rtqz
                .value)
            setattr(out_table, f'block_{nwg__ytia}', hzobe__rtqz.value)
    if mxyvf__vhm:
        kchw__yyyqs, hzobe__rtqz = ListInstance.allocate_ex(context,
            builder, types.List(arr_type), vwpya__eyxvg)
        hzobe__rtqz.size = vwpya__eyxvg
        hzobe__rtqz.inititem(qksnv__aeyib, arr_arg, incref=True)
        nwg__ytia = out_table_type.type_to_blk[arr_type]
        setattr(out_table, f'block_{nwg__ytia}', hzobe__rtqz.value)
        if not is_new_col:
            _rm_old_array(col_ind, out_table_type, out_table, in_table_type,
                context, builder)
    else:
        nwg__ytia = out_table_type.type_to_blk[arr_type]
        hzobe__rtqz = ListInstance(context, builder, types.List(arr_type),
            getattr(out_table, f'block_{nwg__ytia}'))
        if is_new_col:
            n = hzobe__rtqz.size
            pifau__nwz = builder.add(n, vwpya__eyxvg)
            hzobe__rtqz.resize(pifau__nwz)
            hzobe__rtqz.inititem(n, arr_arg, incref=True)
        elif arr_type == in_table_type.arr_types[col_ind]:
            ybfs__gtaa = context.get_constant(types.int64, out_table_type.
                block_offsets[col_ind])
            hzobe__rtqz.setitem(ybfs__gtaa, arr_arg, True)
        else:
            _rm_old_array(col_ind, out_table_type, out_table, in_table_type,
                context, builder)
            ybfs__gtaa = context.get_constant(types.int64, out_table_type.
                block_offsets[col_ind])
            n = hzobe__rtqz.size
            pifau__nwz = builder.add(n, vwpya__eyxvg)
            hzobe__rtqz.resize(pifau__nwz)
            context.nrt.incref(builder, arr_type, hzobe__rtqz.getitem(
                ybfs__gtaa))
            hzobe__rtqz.move(builder.add(ybfs__gtaa, vwpya__eyxvg),
                ybfs__gtaa, builder.sub(n, ybfs__gtaa))
            hzobe__rtqz.setitem(ybfs__gtaa, arr_arg, incref=True)
    return out_table._getvalue()


def _rm_old_array(col_ind, out_table_type, out_table, in_table_type,
    context, builder):
    dnn__vzxg = in_table_type.arr_types[col_ind]
    if dnn__vzxg in out_table_type.type_to_blk:
        nwg__ytia = out_table_type.type_to_blk[dnn__vzxg]
        psvnh__oznei = getattr(out_table, f'block_{nwg__ytia}')
        xpnz__hlyp = types.List(dnn__vzxg)
        ybfs__gtaa = context.get_constant(types.int64, in_table_type.
            block_offsets[col_ind])
        zpqgk__sua = xpnz__hlyp.dtype(xpnz__hlyp, types.intp)
        tnjoo__zrf = context.compile_internal(builder, lambda lst, i: lst.
            pop(i), zpqgk__sua, (psvnh__oznei, ybfs__gtaa))
        context.nrt.decref(builder, dnn__vzxg, tnjoo__zrf)


@intrinsic
def set_table_data(typingctx, table_type, ind_type, arr_type=None):
    assert isinstance(table_type, TableType), 'invalid input to set_table_data'
    assert is_overload_constant_int(ind_type
        ), 'set_table_data expects const index'
    col_ind = get_overload_const_int(ind_type)
    is_new_col = col_ind == len(table_type.arr_types)
    wxa__cdade = list(table_type.arr_types)
    if is_new_col:
        wxa__cdade.append(arr_type)
    else:
        wxa__cdade[col_ind] = arr_type
    out_table_type = TableType(tuple(wxa__cdade))

    def codegen(context, builder, sig, args):
        table_arg, kchw__yyyqs, qgmnn__cnje = args
        out_table = set_table_data_codegen(context, builder, table_type,
            table_arg, out_table_type, arr_type, qgmnn__cnje, col_ind,
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
    hqv__gwre = args[0]
    if equiv_set.has_shape(hqv__gwre):
        return ArrayAnalysis.AnalyzeResult(shape=equiv_set.get_shape(
            hqv__gwre)[0], pre=[])


ArrayAnalysis._analyze_op_call_bodo_hiframes_table_get_table_data = (
    get_table_data_equiv)


@lower_constant(TableType)
def lower_constant_table(context, builder, table_type, pyval):
    iajnq__exemc = []
    for pzw__smwgx, nwg__ytia in table_type.type_to_blk.items():
        nby__xkkw = len(table_type.block_to_arr_ind[nwg__ytia])
        wsexv__orld = []
        for i in range(nby__xkkw):
            mmbo__dbby = table_type.block_to_arr_ind[nwg__ytia][i]
            wsexv__orld.append(pyval.arrays[mmbo__dbby])
        iajnq__exemc.append(context.get_constant_generic(builder, types.
            List(pzw__smwgx), wsexv__orld))
    dlnmn__cpyyn = context.get_constant_null(types.pyobject)
    wvvd__kiuw = context.get_constant(types.int64, 0 if len(pyval.arrays) ==
        0 else len(pyval.arrays[0]))
    return lir.Constant.literal_struct(iajnq__exemc + [dlnmn__cpyyn,
        wvvd__kiuw])


@intrinsic
def init_table(typingctx, table_type, to_str_if_dict_t=None):
    assert isinstance(table_type, TableType), 'table type expected'
    assert is_overload_constant_bool(to_str_if_dict_t
        ), 'constant to_str_if_dict_t expected'
    out_table_type = table_type
    if is_overload_true(to_str_if_dict_t):
        out_table_type = to_str_arr_if_dict_array(table_type)

    def codegen(context, builder, sig, args):
        synbk__ulh = cgutils.create_struct_proxy(out_table_type)(context,
            builder)
        for pzw__smwgx, nwg__ytia in out_table_type.type_to_blk.items():
            eigcl__zqtw = context.get_constant_null(types.List(pzw__smwgx))
            setattr(synbk__ulh, f'block_{nwg__ytia}', eigcl__zqtw)
        return synbk__ulh._getvalue()
    sig = out_table_type(table_type, to_str_if_dict_t)
    return sig, codegen


@intrinsic
def get_table_block(typingctx, table_type, blk_type=None):
    assert isinstance(table_type, TableType), 'table type expected'
    assert is_overload_constant_int(blk_type)
    nwg__ytia = get_overload_const_int(blk_type)
    arr_type = None
    for pzw__smwgx, erx__wvyl in table_type.type_to_blk.items():
        if erx__wvyl == nwg__ytia:
            arr_type = pzw__smwgx
            break
    assert arr_type is not None, 'invalid table type block'
    taz__dgk = types.List(arr_type)

    def codegen(context, builder, sig, args):
        synbk__ulh = cgutils.create_struct_proxy(table_type)(context,
            builder, args[0])
        ymm__fmgrn = getattr(synbk__ulh, f'block_{nwg__ytia}')
        return impl_ret_borrowed(context, builder, taz__dgk, ymm__fmgrn)
    sig = taz__dgk(table_type, blk_type)
    return sig, codegen


@intrinsic
def ensure_column_unboxed(typingctx, table_type, arr_list_t, ind_t,
    arr_ind_t=None):
    assert isinstance(table_type, TableType), 'table type expected'
    sig = types.none(table_type, arr_list_t, ind_t, arr_ind_t)
    return sig, ensure_column_unboxed_codegen


def ensure_column_unboxed_codegen(context, builder, sig, args):
    from bodo.hiframes.boxing import get_df_obj_column_codegen
    table_arg, ukk__jlypj, imzbw__vuqhl, gstt__gpd = args
    rjh__nerx = context.get_python_api(builder)
    synbk__ulh = cgutils.create_struct_proxy(sig.args[0])(context, builder,
        table_arg)
    tfyt__ehptd = cgutils.is_not_null(builder, synbk__ulh.parent)
    pjw__qhi = ListInstance(context, builder, sig.args[1], ukk__jlypj)
    meqrr__hlyz = pjw__qhi.getitem(imzbw__vuqhl)
    cjtm__zuf = cgutils.alloca_once_value(builder, meqrr__hlyz)
    jpo__jip = cgutils.alloca_once_value(builder, context.get_constant_null
        (sig.args[1].dtype))
    uvt__qno = is_ll_eq(builder, cjtm__zuf, jpo__jip)
    with builder.if_then(uvt__qno):
        with builder.if_else(tfyt__ehptd) as (acd__pru, lid__vojxq):
            with acd__pru:
                eahtx__uojpp = get_df_obj_column_codegen(context, builder,
                    rjh__nerx, synbk__ulh.parent, gstt__gpd, sig.args[1].dtype)
                hjfq__klnpg = rjh__nerx.to_native_value(sig.args[1].dtype,
                    eahtx__uojpp).value
                pjw__qhi.inititem(imzbw__vuqhl, hjfq__klnpg, incref=False)
                rjh__nerx.decref(eahtx__uojpp)
            with lid__vojxq:
                context.call_conv.return_user_exc(builder, BodoError, (
                    'unexpected null table column',))


@intrinsic
def set_table_block(typingctx, table_type, arr_list_type, blk_type=None):
    assert isinstance(table_type, TableType), 'table type expected'
    assert isinstance(arr_list_type, types.List), 'list type expected'
    assert is_overload_constant_int(blk_type), 'blk should be const int'
    nwg__ytia = get_overload_const_int(blk_type)

    def codegen(context, builder, sig, args):
        table_arg, dglu__zqhj, kchw__yyyqs = args
        in_table = cgutils.create_struct_proxy(table_type)(context, builder,
            table_arg)
        setattr(in_table, f'block_{nwg__ytia}', dglu__zqhj)
        return impl_ret_borrowed(context, builder, table_type, in_table.
            _getvalue())
    sig = table_type(table_type, arr_list_type, blk_type)
    return sig, codegen


@intrinsic
def set_table_len(typingctx, table_type, l_type=None):
    assert isinstance(table_type, TableType), 'table type expected'

    def codegen(context, builder, sig, args):
        table_arg, jac__dcail = args
        in_table = cgutils.create_struct_proxy(table_type)(context, builder,
            table_arg)
        in_table.len = jac__dcail
        return impl_ret_borrowed(context, builder, table_type, in_table.
            _getvalue())
    sig = table_type(table_type, l_type)
    return sig, codegen


@intrinsic
def alloc_list_like(typingctx, list_type, to_str_if_dict_t=None):
    assert isinstance(list_type, types.List), 'list type expected'
    assert is_overload_constant_bool(to_str_if_dict_t
        ), 'constant to_str_if_dict_t expected'
    taz__dgk = list_type
    if is_overload_true(to_str_if_dict_t):
        taz__dgk = types.List(to_str_arr_if_dict_array(list_type.dtype))

    def codegen(context, builder, sig, args):
        boe__tptb = ListInstance(context, builder, list_type, args[0])
        laq__eqnna = boe__tptb.size
        kchw__yyyqs, hzobe__rtqz = ListInstance.allocate_ex(context,
            builder, taz__dgk, laq__eqnna)
        hzobe__rtqz.size = laq__eqnna
        return hzobe__rtqz.value
    sig = taz__dgk(list_type, to_str_if_dict_t)
    return sig, codegen


def _get_idx_length(idx):
    pass


@overload(_get_idx_length)
def overload_get_idx_length(idx, n):
    if is_list_like_index_type(idx) and idx.dtype == types.bool_:
        return lambda idx, n: idx.sum()
    assert isinstance(idx, types.SliceType), 'slice index expected'

    def impl(idx, n):
        nvb__ztbl = numba.cpython.unicode._normalize_slice(idx, n)
        return numba.cpython.unicode._slice_span(nvb__ztbl)
    return impl


def gen_table_filter(T, used_cols=None):
    from bodo.utils.conversion import ensure_contig_if_np
    ueuts__pbelg = {'init_table': init_table, 'get_table_block':
        get_table_block, 'ensure_column_unboxed': ensure_column_unboxed,
        'set_table_block': set_table_block, 'set_table_len': set_table_len,
        'alloc_list_like': alloc_list_like, '_get_idx_length':
        _get_idx_length, 'ensure_contig_if_np': ensure_contig_if_np}
    if used_cols is not None:
        ueuts__pbelg['used_cols'] = np.array(used_cols, dtype=np.int64)
    beds__olap = 'def impl(T, idx):\n'
    beds__olap += f'  T2 = init_table(T, False)\n'
    beds__olap += f'  l = 0\n'
    if used_cols is not None and len(used_cols) == 0:
        beds__olap += f'  l = _get_idx_length(idx, len(T))\n'
        beds__olap += f'  T2 = set_table_len(T2, l)\n'
        beds__olap += f'  return T2\n'
        bbqbw__bmfw = {}
        exec(beds__olap, ueuts__pbelg, bbqbw__bmfw)
        return bbqbw__bmfw['impl']
    if used_cols is not None:
        beds__olap += f'  used_set = set(used_cols)\n'
    for nwg__ytia in T.type_to_blk.values():
        ueuts__pbelg[f'arr_inds_{nwg__ytia}'] = np.array(T.block_to_arr_ind
            [nwg__ytia], dtype=np.int64)
        beds__olap += (
            f'  arr_list_{nwg__ytia} = get_table_block(T, {nwg__ytia})\n')
        beds__olap += (
            f'  out_arr_list_{nwg__ytia} = alloc_list_like(arr_list_{nwg__ytia}, False)\n'
            )
        beds__olap += f'  for i in range(len(arr_list_{nwg__ytia})):\n'
        beds__olap += f'    arr_ind_{nwg__ytia} = arr_inds_{nwg__ytia}[i]\n'
        if used_cols is not None:
            beds__olap += (
                f'    if arr_ind_{nwg__ytia} not in used_set: continue\n')
        beds__olap += f"""    ensure_column_unboxed(T, arr_list_{nwg__ytia}, i, arr_ind_{nwg__ytia})
"""
        beds__olap += f"""    out_arr_{nwg__ytia} = ensure_contig_if_np(arr_list_{nwg__ytia}[i][idx])
"""
        beds__olap += f'    l = len(out_arr_{nwg__ytia})\n'
        beds__olap += (
            f'    out_arr_list_{nwg__ytia}[i] = out_arr_{nwg__ytia}\n')
        beds__olap += (
            f'  T2 = set_table_block(T2, out_arr_list_{nwg__ytia}, {nwg__ytia})\n'
            )
    beds__olap += f'  T2 = set_table_len(T2, l)\n'
    beds__olap += f'  return T2\n'
    bbqbw__bmfw = {}
    exec(beds__olap, ueuts__pbelg, bbqbw__bmfw)
    return bbqbw__bmfw['impl']


@numba.generated_jit(nopython=True, no_cpython_wrapper=True)
def decode_if_dict_table(T):
    beds__olap = 'def impl(T):\n'
    beds__olap += f'  T2 = init_table(T, True)\n'
    beds__olap += f'  l = len(T)\n'
    ueuts__pbelg = {'init_table': init_table, 'get_table_block':
        get_table_block, 'ensure_column_unboxed': ensure_column_unboxed,
        'set_table_block': set_table_block, 'set_table_len': set_table_len,
        'alloc_list_like': alloc_list_like, 'decode_if_dict_array':
        decode_if_dict_array}
    for nwg__ytia in T.type_to_blk.values():
        ueuts__pbelg[f'arr_inds_{nwg__ytia}'] = np.array(T.block_to_arr_ind
            [nwg__ytia], dtype=np.int64)
        beds__olap += (
            f'  arr_list_{nwg__ytia} = get_table_block(T, {nwg__ytia})\n')
        beds__olap += (
            f'  out_arr_list_{nwg__ytia} = alloc_list_like(arr_list_{nwg__ytia}, True)\n'
            )
        beds__olap += f'  for i in range(len(arr_list_{nwg__ytia})):\n'
        beds__olap += f'    arr_ind_{nwg__ytia} = arr_inds_{nwg__ytia}[i]\n'
        beds__olap += f"""    ensure_column_unboxed(T, arr_list_{nwg__ytia}, i, arr_ind_{nwg__ytia})
"""
        beds__olap += (
            f'    out_arr_{nwg__ytia} = decode_if_dict_array(arr_list_{nwg__ytia}[i])\n'
            )
        beds__olap += (
            f'    out_arr_list_{nwg__ytia}[i] = out_arr_{nwg__ytia}\n')
        beds__olap += (
            f'  T2 = set_table_block(T2, out_arr_list_{nwg__ytia}, {nwg__ytia})\n'
            )
    beds__olap += f'  T2 = set_table_len(T2, l)\n'
    beds__olap += f'  return T2\n'
    bbqbw__bmfw = {}
    exec(beds__olap, ueuts__pbelg, bbqbw__bmfw)
    return bbqbw__bmfw['impl']


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
        xjkx__kilzo = [arr_list_tup_typ.dtype.dtype] * len(arr_list_tup_typ)
    else:
        xjkx__kilzo = []
        for typ in arr_list_tup_typ:
            if typ.dtype == types.undefined:
                return
            xjkx__kilzo.append(typ.dtype)
    assert isinstance(nrows_typ, types.Integer
        ), 'init_runtime_table_from_lists requires an integer length'

    def codegen(context, builder, sig, args):
        bae__ztooz, tglkp__kbukj = args
        synbk__ulh = cgutils.create_struct_proxy(table_type)(context, builder)
        synbk__ulh.len = tglkp__kbukj
        iajnq__exemc = cgutils.unpack_tuple(builder, bae__ztooz)
        for i, ymm__fmgrn in enumerate(iajnq__exemc):
            setattr(synbk__ulh, f'block_{i}', ymm__fmgrn)
            context.nrt.incref(builder, types.List(xjkx__kilzo[i]), ymm__fmgrn)
        return synbk__ulh._getvalue()
    table_type = TableType(tuple(xjkx__kilzo), True)
    sig = table_type(arr_list_tup_typ, nrows_typ)
    return sig, codegen
