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
            usq__arntm = 0
            rijn__vvi = []
            for i in range(usecols[-1] + 1):
                if i == usecols[usq__arntm]:
                    rijn__vvi.append(arrs[usq__arntm])
                    usq__arntm += 1
                else:
                    rijn__vvi.append(None)
            for lniyj__myfx in range(usecols[-1] + 1, num_arrs):
                rijn__vvi.append(None)
            self.arrays = rijn__vvi
        else:
            self.arrays = arrs
        self.block_0 = arrs

    def __eq__(self, other):
        return isinstance(other, Table) and len(self.arrays) == len(other.
            arrays) and all((rvzu__egy == ktisl__nnxpc).all() for rvzu__egy,
            ktisl__nnxpc in zip(self.arrays, other.arrays))

    def __str__(self) ->str:
        return str(self.arrays)

    def to_pandas(self, index=None):
        qmorb__iawat = len(self.arrays)
        tplmn__ecv = dict(zip(range(qmorb__iawat), self.arrays))
        df = pd.DataFrame(tplmn__ecv, index)
        return df


class TableType(types.ArrayCompatible):

    def __init__(self, arr_types, has_runtime_cols=False):
        self.arr_types = arr_types
        self.has_runtime_cols = has_runtime_cols
        rjh__tbsh = []
        mdf__zfe = []
        fik__dhwpq = {}
        ejdqj__jhovk = defaultdict(int)
        jghtw__akzy = defaultdict(list)
        if not has_runtime_cols:
            for i, rjlr__ned in enumerate(arr_types):
                if rjlr__ned not in fik__dhwpq:
                    fik__dhwpq[rjlr__ned] = len(fik__dhwpq)
                xibef__tmgiu = fik__dhwpq[rjlr__ned]
                rjh__tbsh.append(xibef__tmgiu)
                mdf__zfe.append(ejdqj__jhovk[xibef__tmgiu])
                ejdqj__jhovk[xibef__tmgiu] += 1
                jghtw__akzy[xibef__tmgiu].append(i)
        self.block_nums = rjh__tbsh
        self.block_offsets = mdf__zfe
        self.type_to_blk = fik__dhwpq
        self.block_to_arr_ind = jghtw__akzy
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
    return TableType(tuple(numba.typeof(iaewm__jsu) for iaewm__jsu in val.
        arrays))


@register_model(TableType)
class TableTypeModel(models.StructModel):

    def __init__(self, dmm, fe_type):
        if fe_type.has_runtime_cols:
            fgzrg__vfmm = [(f'block_{i}', types.List(rjlr__ned)) for i,
                rjlr__ned in enumerate(fe_type.arr_types)]
        else:
            fgzrg__vfmm = [(f'block_{xibef__tmgiu}', types.List(rjlr__ned)) for
                rjlr__ned, xibef__tmgiu in fe_type.type_to_blk.items()]
        fgzrg__vfmm.append(('parent', types.pyobject))
        fgzrg__vfmm.append(('len', types.int64))
        super(TableTypeModel, self).__init__(dmm, fe_type, fgzrg__vfmm)


make_attribute_wrapper(TableType, 'block_0', 'block_0')
make_attribute_wrapper(TableType, 'len', '_len')


@infer_getattr
class TableTypeAttribute(OverloadedKeyAttributeTemplate):
    key = TableType

    def resolve_shape(self, df):
        return types.Tuple([types.int64, types.int64])


@unbox(TableType)
def unbox_table(typ, val, c):
    pkrn__qcbw = c.pyapi.object_getattr_string(val, 'arrays')
    pij__apdm = cgutils.create_struct_proxy(typ)(c.context, c.builder)
    pij__apdm.parent = cgutils.get_null_value(pij__apdm.parent.type)
    nmwe__jsi = c.pyapi.make_none()
    qcbl__lajj = c.context.get_constant(types.int64, 0)
    urkwx__xso = cgutils.alloca_once_value(c.builder, qcbl__lajj)
    for rjlr__ned, xibef__tmgiu in typ.type_to_blk.items():
        cvc__yxzj = c.context.get_constant(types.int64, len(typ.
            block_to_arr_ind[xibef__tmgiu]))
        lniyj__myfx, dkvsd__yws = ListInstance.allocate_ex(c.context, c.
            builder, types.List(rjlr__ned), cvc__yxzj)
        dkvsd__yws.size = cvc__yxzj
        jiq__hjgq = c.context.make_constant_array(c.builder, types.Array(
            types.int64, 1, 'C'), np.array(typ.block_to_arr_ind[
            xibef__tmgiu], dtype=np.int64))
        khgk__ehx = c.context.make_array(types.Array(types.int64, 1, 'C'))(c
            .context, c.builder, jiq__hjgq)
        with cgutils.for_range(c.builder, cvc__yxzj) as djhm__cehe:
            i = djhm__cehe.index
            nxg__wne = _getitem_array_single_int(c.context, c.builder,
                types.int64, types.Array(types.int64, 1, 'C'), khgk__ehx, i)
            bvdmr__too = c.pyapi.long_from_longlong(nxg__wne)
            jutjy__yjl = c.pyapi.object_getitem(pkrn__qcbw, bvdmr__too)
            buaec__edz = c.builder.icmp_unsigned('==', jutjy__yjl, nmwe__jsi)
            with c.builder.if_else(buaec__edz) as (acsz__kpq, ems__pqnp):
                with acsz__kpq:
                    nwca__eauy = c.context.get_constant_null(rjlr__ned)
                    dkvsd__yws.inititem(i, nwca__eauy, incref=False)
                with ems__pqnp:
                    ycc__voe = c.pyapi.call_method(jutjy__yjl, '__len__', ())
                    nug__qck = c.pyapi.long_as_longlong(ycc__voe)
                    c.builder.store(nug__qck, urkwx__xso)
                    c.pyapi.decref(ycc__voe)
                    iaewm__jsu = c.pyapi.to_native_value(rjlr__ned, jutjy__yjl
                        ).value
                    dkvsd__yws.inititem(i, iaewm__jsu, incref=False)
            c.pyapi.decref(jutjy__yjl)
            c.pyapi.decref(bvdmr__too)
        setattr(pij__apdm, f'block_{xibef__tmgiu}', dkvsd__yws.value)
    pij__apdm.len = c.builder.load(urkwx__xso)
    c.pyapi.decref(pkrn__qcbw)
    c.pyapi.decref(nmwe__jsi)
    wvkan__aqa = cgutils.is_not_null(c.builder, c.pyapi.err_occurred())
    return NativeValue(pij__apdm._getvalue(), is_error=wvkan__aqa)


@box(TableType)
def box_table(typ, val, c, ensure_unboxed=None):
    from bodo.hiframes.boxing import get_df_obj_column_codegen
    pij__apdm = cgutils.create_struct_proxy(typ)(c.context, c.builder, val)
    if typ.has_runtime_cols:
        rzdkl__bdnb = c.context.get_constant(types.int64, 0)
        for i, rjlr__ned in enumerate(typ.arr_types):
            rijn__vvi = getattr(pij__apdm, f'block_{i}')
            gjy__awvsc = ListInstance(c.context, c.builder, types.List(
                rjlr__ned), rijn__vvi)
            rzdkl__bdnb = c.builder.add(rzdkl__bdnb, gjy__awvsc.size)
        terid__ccez = c.pyapi.list_new(rzdkl__bdnb)
        payk__yykpp = c.context.get_constant(types.int64, 0)
        for i, rjlr__ned in enumerate(typ.arr_types):
            rijn__vvi = getattr(pij__apdm, f'block_{i}')
            gjy__awvsc = ListInstance(c.context, c.builder, types.List(
                rjlr__ned), rijn__vvi)
            with cgutils.for_range(c.builder, gjy__awvsc.size) as djhm__cehe:
                i = djhm__cehe.index
                iaewm__jsu = gjy__awvsc.getitem(i)
                c.context.nrt.incref(c.builder, rjlr__ned, iaewm__jsu)
                idx = c.builder.add(payk__yykpp, i)
                c.pyapi.list_setitem(terid__ccez, idx, c.pyapi.
                    from_native_value(rjlr__ned, iaewm__jsu, c.env_manager))
            payk__yykpp = c.builder.add(payk__yykpp, gjy__awvsc.size)
        sogp__icq = c.pyapi.unserialize(c.pyapi.serialize_object(Table))
        wsu__dcp = c.pyapi.call_function_objargs(sogp__icq, (terid__ccez,))
        c.pyapi.decref(sogp__icq)
        c.pyapi.decref(terid__ccez)
        c.context.nrt.decref(c.builder, typ, val)
        return wsu__dcp
    terid__ccez = c.pyapi.list_new(c.context.get_constant(types.int64, len(
        typ.arr_types)))
    gnpo__djzk = cgutils.is_not_null(c.builder, pij__apdm.parent)
    if ensure_unboxed is None:
        ensure_unboxed = c.context.get_constant(types.bool_, False)
    for rjlr__ned, xibef__tmgiu in typ.type_to_blk.items():
        rijn__vvi = getattr(pij__apdm, f'block_{xibef__tmgiu}')
        gjy__awvsc = ListInstance(c.context, c.builder, types.List(
            rjlr__ned), rijn__vvi)
        jiq__hjgq = c.context.make_constant_array(c.builder, types.Array(
            types.int64, 1, 'C'), np.array(typ.block_to_arr_ind[
            xibef__tmgiu], dtype=np.int64))
        khgk__ehx = c.context.make_array(types.Array(types.int64, 1, 'C'))(c
            .context, c.builder, jiq__hjgq)
        with cgutils.for_range(c.builder, gjy__awvsc.size) as djhm__cehe:
            i = djhm__cehe.index
            nxg__wne = _getitem_array_single_int(c.context, c.builder,
                types.int64, types.Array(types.int64, 1, 'C'), khgk__ehx, i)
            iaewm__jsu = gjy__awvsc.getitem(i)
            yrd__mvat = cgutils.alloca_once_value(c.builder, iaewm__jsu)
            jqb__ajt = cgutils.alloca_once_value(c.builder, c.context.
                get_constant_null(rjlr__ned))
            hasj__fhmv = is_ll_eq(c.builder, yrd__mvat, jqb__ajt)
            with c.builder.if_else(c.builder.and_(hasj__fhmv, c.builder.
                not_(ensure_unboxed))) as (acsz__kpq, ems__pqnp):
                with acsz__kpq:
                    nmwe__jsi = c.pyapi.make_none()
                    c.pyapi.list_setitem(terid__ccez, nxg__wne, nmwe__jsi)
                with ems__pqnp:
                    jutjy__yjl = cgutils.alloca_once(c.builder, c.context.
                        get_value_type(types.pyobject))
                    with c.builder.if_else(c.builder.and_(hasj__fhmv,
                        gnpo__djzk)) as (mrcge__rit, qjyj__forh):
                        with mrcge__rit:
                            tzoxd__auhe = get_df_obj_column_codegen(c.
                                context, c.builder, c.pyapi, pij__apdm.
                                parent, nxg__wne, rjlr__ned)
                            c.builder.store(tzoxd__auhe, jutjy__yjl)
                        with qjyj__forh:
                            c.context.nrt.incref(c.builder, rjlr__ned,
                                iaewm__jsu)
                            c.builder.store(c.pyapi.from_native_value(
                                rjlr__ned, iaewm__jsu, c.env_manager),
                                jutjy__yjl)
                    c.pyapi.list_setitem(terid__ccez, nxg__wne, c.builder.
                        load(jutjy__yjl))
    sogp__icq = c.pyapi.unserialize(c.pyapi.serialize_object(Table))
    wsu__dcp = c.pyapi.call_function_objargs(sogp__icq, (terid__ccez,))
    c.pyapi.decref(sogp__icq)
    c.pyapi.decref(terid__ccez)
    c.context.nrt.decref(c.builder, typ, val)
    return wsu__dcp


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
        pij__apdm = cgutils.create_struct_proxy(table_type)(context,
            builder, table_arg)
        wbs__pml = context.get_constant(types.int64, 0)
        for i, rjlr__ned in enumerate(table_type.arr_types):
            rijn__vvi = getattr(pij__apdm, f'block_{i}')
            gjy__awvsc = ListInstance(context, builder, types.List(
                rjlr__ned), rijn__vvi)
            wbs__pml = builder.add(wbs__pml, gjy__awvsc.size)
        return wbs__pml
    sig = types.int64(table_type)
    return sig, codegen


def get_table_data_codegen(context, builder, table_arg, col_ind, table_type):
    arr_type = table_type.arr_types[col_ind]
    pij__apdm = cgutils.create_struct_proxy(table_type)(context, builder,
        table_arg)
    xibef__tmgiu = table_type.block_nums[col_ind]
    bkky__wybc = table_type.block_offsets[col_ind]
    rijn__vvi = getattr(pij__apdm, f'block_{xibef__tmgiu}')
    gjy__awvsc = ListInstance(context, builder, types.List(arr_type), rijn__vvi
        )
    iaewm__jsu = gjy__awvsc.getitem(bkky__wybc)
    return iaewm__jsu


@intrinsic
def get_table_data(typingctx, table_type, ind_typ=None):
    assert isinstance(table_type, TableType)
    assert is_overload_constant_int(ind_typ)
    col_ind = get_overload_const_int(ind_typ)
    arr_type = table_type.arr_types[col_ind]

    def codegen(context, builder, sig, args):
        table_arg, lniyj__myfx = args
        iaewm__jsu = get_table_data_codegen(context, builder, table_arg,
            col_ind, table_type)
        return impl_ret_borrowed(context, builder, arr_type, iaewm__jsu)
    sig = arr_type(table_type, ind_typ)
    return sig, codegen


@intrinsic
def del_column(typingctx, table_type, ind_typ=None):
    assert isinstance(table_type, TableType)
    assert is_overload_constant_int(ind_typ)
    col_ind = get_overload_const_int(ind_typ)
    arr_type = table_type.arr_types[col_ind]

    def codegen(context, builder, sig, args):
        table_arg, lniyj__myfx = args
        pij__apdm = cgutils.create_struct_proxy(table_type)(context,
            builder, table_arg)
        xibef__tmgiu = table_type.block_nums[col_ind]
        bkky__wybc = table_type.block_offsets[col_ind]
        rijn__vvi = getattr(pij__apdm, f'block_{xibef__tmgiu}')
        gjy__awvsc = ListInstance(context, builder, types.List(arr_type),
            rijn__vvi)
        iaewm__jsu = gjy__awvsc.getitem(bkky__wybc)
        context.nrt.decref(builder, arr_type, iaewm__jsu)
        nwca__eauy = context.get_constant_null(arr_type)
        gjy__awvsc.inititem(bkky__wybc, nwca__eauy, incref=False)
    sig = types.void(table_type, ind_typ)
    return sig, codegen


def set_table_data_codegen(context, builder, in_table_type, in_table,
    out_table_type, arr_type, arr_arg, col_ind, is_new_col):
    in_table = cgutils.create_struct_proxy(in_table_type)(context, builder,
        in_table)
    out_table = cgutils.create_struct_proxy(out_table_type)(context, builder)
    out_table.len = in_table.len
    out_table.parent = in_table.parent
    qcbl__lajj = context.get_constant(types.int64, 0)
    mcgqo__tjw = context.get_constant(types.int64, 1)
    oxtgh__ztndq = arr_type not in in_table_type.type_to_blk
    for rjlr__ned, xibef__tmgiu in out_table_type.type_to_blk.items():
        if rjlr__ned in in_table_type.type_to_blk:
            rehox__iufc = in_table_type.type_to_blk[rjlr__ned]
            dkvsd__yws = ListInstance(context, builder, types.List(
                rjlr__ned), getattr(in_table, f'block_{rehox__iufc}'))
            context.nrt.incref(builder, types.List(rjlr__ned), dkvsd__yws.value
                )
            setattr(out_table, f'block_{xibef__tmgiu}', dkvsd__yws.value)
    if oxtgh__ztndq:
        lniyj__myfx, dkvsd__yws = ListInstance.allocate_ex(context, builder,
            types.List(arr_type), mcgqo__tjw)
        dkvsd__yws.size = mcgqo__tjw
        dkvsd__yws.inititem(qcbl__lajj, arr_arg, incref=True)
        xibef__tmgiu = out_table_type.type_to_blk[arr_type]
        setattr(out_table, f'block_{xibef__tmgiu}', dkvsd__yws.value)
        if not is_new_col:
            _rm_old_array(col_ind, out_table_type, out_table, in_table_type,
                context, builder)
    else:
        xibef__tmgiu = out_table_type.type_to_blk[arr_type]
        dkvsd__yws = ListInstance(context, builder, types.List(arr_type),
            getattr(out_table, f'block_{xibef__tmgiu}'))
        if is_new_col:
            n = dkvsd__yws.size
            ambo__oxhww = builder.add(n, mcgqo__tjw)
            dkvsd__yws.resize(ambo__oxhww)
            dkvsd__yws.inititem(n, arr_arg, incref=True)
        elif arr_type == in_table_type.arr_types[col_ind]:
            dtf__dso = context.get_constant(types.int64, out_table_type.
                block_offsets[col_ind])
            dkvsd__yws.setitem(dtf__dso, arr_arg, True)
        else:
            _rm_old_array(col_ind, out_table_type, out_table, in_table_type,
                context, builder)
            dtf__dso = context.get_constant(types.int64, out_table_type.
                block_offsets[col_ind])
            n = dkvsd__yws.size
            ambo__oxhww = builder.add(n, mcgqo__tjw)
            dkvsd__yws.resize(ambo__oxhww)
            context.nrt.incref(builder, arr_type, dkvsd__yws.getitem(dtf__dso))
            dkvsd__yws.move(builder.add(dtf__dso, mcgqo__tjw), dtf__dso,
                builder.sub(n, dtf__dso))
            dkvsd__yws.setitem(dtf__dso, arr_arg, incref=True)
    return out_table._getvalue()


def _rm_old_array(col_ind, out_table_type, out_table, in_table_type,
    context, builder):
    pig__mct = in_table_type.arr_types[col_ind]
    if pig__mct in out_table_type.type_to_blk:
        xibef__tmgiu = out_table_type.type_to_blk[pig__mct]
        nil__yzr = getattr(out_table, f'block_{xibef__tmgiu}')
        rswya__lrtt = types.List(pig__mct)
        dtf__dso = context.get_constant(types.int64, in_table_type.
            block_offsets[col_ind])
        wntiq__onwj = rswya__lrtt.dtype(rswya__lrtt, types.intp)
        ccqx__hixc = context.compile_internal(builder, lambda lst, i: lst.
            pop(i), wntiq__onwj, (nil__yzr, dtf__dso))
        context.nrt.decref(builder, pig__mct, ccqx__hixc)


@intrinsic
def set_table_data(typingctx, table_type, ind_type, arr_type=None):
    assert isinstance(table_type, TableType), 'invalid input to set_table_data'
    assert is_overload_constant_int(ind_type
        ), 'set_table_data expects const index'
    col_ind = get_overload_const_int(ind_type)
    is_new_col = col_ind == len(table_type.arr_types)
    chyf__pax = list(table_type.arr_types)
    if is_new_col:
        chyf__pax.append(arr_type)
    else:
        chyf__pax[col_ind] = arr_type
    out_table_type = TableType(tuple(chyf__pax))

    def codegen(context, builder, sig, args):
        table_arg, lniyj__myfx, ouwur__cacn = args
        out_table = set_table_data_codegen(context, builder, table_type,
            table_arg, out_table_type, arr_type, ouwur__cacn, col_ind,
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
    rwx__gsud = args[0]
    if equiv_set.has_shape(rwx__gsud):
        return ArrayAnalysis.AnalyzeResult(shape=equiv_set.get_shape(
            rwx__gsud)[0], pre=[])


ArrayAnalysis._analyze_op_call_bodo_hiframes_table_get_table_data = (
    get_table_data_equiv)


@lower_constant(TableType)
def lower_constant_table(context, builder, table_type, pyval):
    bml__sxa = []
    for rjlr__ned, xibef__tmgiu in table_type.type_to_blk.items():
        ktjt__ygdk = len(table_type.block_to_arr_ind[xibef__tmgiu])
        sla__cucu = []
        for i in range(ktjt__ygdk):
            nxg__wne = table_type.block_to_arr_ind[xibef__tmgiu][i]
            sla__cucu.append(pyval.arrays[nxg__wne])
        bml__sxa.append(context.get_constant_generic(builder, types.List(
            rjlr__ned), sla__cucu))
    ylsey__mglyv = context.get_constant_null(types.pyobject)
    qdje__kyfw = context.get_constant(types.int64, 0 if len(pyval.arrays) ==
        0 else len(pyval.arrays[0]))
    return lir.Constant.literal_struct(bml__sxa + [ylsey__mglyv, qdje__kyfw])


@intrinsic
def init_table(typingctx, table_type, to_str_if_dict_t=None):
    assert isinstance(table_type, TableType), 'table type expected'
    assert is_overload_constant_bool(to_str_if_dict_t
        ), 'constant to_str_if_dict_t expected'
    out_table_type = table_type
    if is_overload_true(to_str_if_dict_t):
        out_table_type = to_str_arr_if_dict_array(table_type)

    def codegen(context, builder, sig, args):
        pij__apdm = cgutils.create_struct_proxy(out_table_type)(context,
            builder)
        for rjlr__ned, xibef__tmgiu in out_table_type.type_to_blk.items():
            agjs__bdik = context.get_constant_null(types.List(rjlr__ned))
            setattr(pij__apdm, f'block_{xibef__tmgiu}', agjs__bdik)
        return pij__apdm._getvalue()
    sig = out_table_type(table_type, to_str_if_dict_t)
    return sig, codegen


@intrinsic
def get_table_block(typingctx, table_type, blk_type=None):
    assert isinstance(table_type, TableType), 'table type expected'
    assert is_overload_constant_int(blk_type)
    xibef__tmgiu = get_overload_const_int(blk_type)
    arr_type = None
    for rjlr__ned, ktisl__nnxpc in table_type.type_to_blk.items():
        if ktisl__nnxpc == xibef__tmgiu:
            arr_type = rjlr__ned
            break
    assert arr_type is not None, 'invalid table type block'
    ygddz__rmqd = types.List(arr_type)

    def codegen(context, builder, sig, args):
        pij__apdm = cgutils.create_struct_proxy(table_type)(context,
            builder, args[0])
        rijn__vvi = getattr(pij__apdm, f'block_{xibef__tmgiu}')
        return impl_ret_borrowed(context, builder, ygddz__rmqd, rijn__vvi)
    sig = ygddz__rmqd(table_type, blk_type)
    return sig, codegen


@intrinsic
def ensure_column_unboxed(typingctx, table_type, arr_list_t, ind_t,
    arr_ind_t=None):
    assert isinstance(table_type, TableType), 'table type expected'
    sig = types.none(table_type, arr_list_t, ind_t, arr_ind_t)
    return sig, ensure_column_unboxed_codegen


def ensure_column_unboxed_codegen(context, builder, sig, args):
    from bodo.hiframes.boxing import get_df_obj_column_codegen
    table_arg, lolem__hlr, bjth__skajj, kgo__ttplv = args
    knol__qwqn = context.get_python_api(builder)
    pij__apdm = cgutils.create_struct_proxy(sig.args[0])(context, builder,
        table_arg)
    gnpo__djzk = cgutils.is_not_null(builder, pij__apdm.parent)
    gjy__awvsc = ListInstance(context, builder, sig.args[1], lolem__hlr)
    vdc__pqv = gjy__awvsc.getitem(bjth__skajj)
    yrd__mvat = cgutils.alloca_once_value(builder, vdc__pqv)
    jqb__ajt = cgutils.alloca_once_value(builder, context.get_constant_null
        (sig.args[1].dtype))
    hasj__fhmv = is_ll_eq(builder, yrd__mvat, jqb__ajt)
    with builder.if_then(hasj__fhmv):
        with builder.if_else(gnpo__djzk) as (acsz__kpq, ems__pqnp):
            with acsz__kpq:
                jutjy__yjl = get_df_obj_column_codegen(context, builder,
                    knol__qwqn, pij__apdm.parent, kgo__ttplv, sig.args[1].dtype
                    )
                iaewm__jsu = knol__qwqn.to_native_value(sig.args[1].dtype,
                    jutjy__yjl).value
                gjy__awvsc.inititem(bjth__skajj, iaewm__jsu, incref=False)
                knol__qwqn.decref(jutjy__yjl)
            with ems__pqnp:
                context.call_conv.return_user_exc(builder, BodoError, (
                    'unexpected null table column',))


@intrinsic
def set_table_block(typingctx, table_type, arr_list_type, blk_type=None):
    assert isinstance(table_type, TableType), 'table type expected'
    assert isinstance(arr_list_type, types.List), 'list type expected'
    assert is_overload_constant_int(blk_type), 'blk should be const int'
    xibef__tmgiu = get_overload_const_int(blk_type)

    def codegen(context, builder, sig, args):
        table_arg, ipuo__jmlj, lniyj__myfx = args
        in_table = cgutils.create_struct_proxy(table_type)(context, builder,
            table_arg)
        setattr(in_table, f'block_{xibef__tmgiu}', ipuo__jmlj)
        return impl_ret_borrowed(context, builder, table_type, in_table.
            _getvalue())
    sig = table_type(table_type, arr_list_type, blk_type)
    return sig, codegen


@intrinsic
def set_table_len(typingctx, table_type, l_type=None):
    assert isinstance(table_type, TableType), 'table type expected'

    def codegen(context, builder, sig, args):
        table_arg, boc__pxbm = args
        in_table = cgutils.create_struct_proxy(table_type)(context, builder,
            table_arg)
        in_table.len = boc__pxbm
        return impl_ret_borrowed(context, builder, table_type, in_table.
            _getvalue())
    sig = table_type(table_type, l_type)
    return sig, codegen


@intrinsic
def alloc_list_like(typingctx, list_type, to_str_if_dict_t=None):
    assert isinstance(list_type, types.List), 'list type expected'
    assert is_overload_constant_bool(to_str_if_dict_t
        ), 'constant to_str_if_dict_t expected'
    ygddz__rmqd = list_type
    if is_overload_true(to_str_if_dict_t):
        ygddz__rmqd = types.List(to_str_arr_if_dict_array(list_type.dtype))

    def codegen(context, builder, sig, args):
        ovuht__tmv = ListInstance(context, builder, list_type, args[0])
        ydzqn__uelcx = ovuht__tmv.size
        lniyj__myfx, dkvsd__yws = ListInstance.allocate_ex(context, builder,
            ygddz__rmqd, ydzqn__uelcx)
        dkvsd__yws.size = ydzqn__uelcx
        return dkvsd__yws.value
    sig = ygddz__rmqd(list_type, to_str_if_dict_t)
    return sig, codegen


def _get_idx_length(idx):
    pass


@overload(_get_idx_length)
def overload_get_idx_length(idx, n):
    if is_list_like_index_type(idx) and idx.dtype == types.bool_:
        return lambda idx, n: idx.sum()
    assert isinstance(idx, types.SliceType), 'slice index expected'

    def impl(idx, n):
        sqa__giex = numba.cpython.unicode._normalize_slice(idx, n)
        return numba.cpython.unicode._slice_span(sqa__giex)
    return impl


def gen_table_filter(T, used_cols=None):
    from bodo.utils.conversion import ensure_contig_if_np
    ffml__iwaui = {'init_table': init_table, 'get_table_block':
        get_table_block, 'ensure_column_unboxed': ensure_column_unboxed,
        'set_table_block': set_table_block, 'set_table_len': set_table_len,
        'alloc_list_like': alloc_list_like, '_get_idx_length':
        _get_idx_length, 'ensure_contig_if_np': ensure_contig_if_np}
    if used_cols is not None:
        ffml__iwaui['used_cols'] = np.array(used_cols, dtype=np.int64)
    bszs__obqq = 'def impl(T, idx):\n'
    bszs__obqq += f'  T2 = init_table(T, False)\n'
    bszs__obqq += f'  l = 0\n'
    if used_cols is not None and len(used_cols) == 0:
        bszs__obqq += f'  l = _get_idx_length(idx, len(T))\n'
        bszs__obqq += f'  T2 = set_table_len(T2, l)\n'
        bszs__obqq += f'  return T2\n'
        eyjq__oukr = {}
        exec(bszs__obqq, ffml__iwaui, eyjq__oukr)
        return eyjq__oukr['impl']
    if used_cols is not None:
        bszs__obqq += f'  used_set = set(used_cols)\n'
    for xibef__tmgiu in T.type_to_blk.values():
        ffml__iwaui[f'arr_inds_{xibef__tmgiu}'] = np.array(T.
            block_to_arr_ind[xibef__tmgiu], dtype=np.int64)
        bszs__obqq += (
            f'  arr_list_{xibef__tmgiu} = get_table_block(T, {xibef__tmgiu})\n'
            )
        bszs__obqq += f"""  out_arr_list_{xibef__tmgiu} = alloc_list_like(arr_list_{xibef__tmgiu}, False)
"""
        bszs__obqq += f'  for i in range(len(arr_list_{xibef__tmgiu})):\n'
        bszs__obqq += (
            f'    arr_ind_{xibef__tmgiu} = arr_inds_{xibef__tmgiu}[i]\n')
        if used_cols is not None:
            bszs__obqq += (
                f'    if arr_ind_{xibef__tmgiu} not in used_set: continue\n')
        bszs__obqq += f"""    ensure_column_unboxed(T, arr_list_{xibef__tmgiu}, i, arr_ind_{xibef__tmgiu})
"""
        bszs__obqq += f"""    out_arr_{xibef__tmgiu} = ensure_contig_if_np(arr_list_{xibef__tmgiu}[i][idx])
"""
        bszs__obqq += f'    l = len(out_arr_{xibef__tmgiu})\n'
        bszs__obqq += (
            f'    out_arr_list_{xibef__tmgiu}[i] = out_arr_{xibef__tmgiu}\n')
        bszs__obqq += (
            f'  T2 = set_table_block(T2, out_arr_list_{xibef__tmgiu}, {xibef__tmgiu})\n'
            )
    bszs__obqq += f'  T2 = set_table_len(T2, l)\n'
    bszs__obqq += f'  return T2\n'
    eyjq__oukr = {}
    exec(bszs__obqq, ffml__iwaui, eyjq__oukr)
    return eyjq__oukr['impl']


@numba.generated_jit(nopython=True, no_cpython_wrapper=True)
def decode_if_dict_table(T):
    bszs__obqq = 'def impl(T):\n'
    bszs__obqq += f'  T2 = init_table(T, True)\n'
    bszs__obqq += f'  l = len(T)\n'
    ffml__iwaui = {'init_table': init_table, 'get_table_block':
        get_table_block, 'ensure_column_unboxed': ensure_column_unboxed,
        'set_table_block': set_table_block, 'set_table_len': set_table_len,
        'alloc_list_like': alloc_list_like, 'decode_if_dict_array':
        decode_if_dict_array}
    for xibef__tmgiu in T.type_to_blk.values():
        ffml__iwaui[f'arr_inds_{xibef__tmgiu}'] = np.array(T.
            block_to_arr_ind[xibef__tmgiu], dtype=np.int64)
        bszs__obqq += (
            f'  arr_list_{xibef__tmgiu} = get_table_block(T, {xibef__tmgiu})\n'
            )
        bszs__obqq += f"""  out_arr_list_{xibef__tmgiu} = alloc_list_like(arr_list_{xibef__tmgiu}, True)
"""
        bszs__obqq += f'  for i in range(len(arr_list_{xibef__tmgiu})):\n'
        bszs__obqq += (
            f'    arr_ind_{xibef__tmgiu} = arr_inds_{xibef__tmgiu}[i]\n')
        bszs__obqq += f"""    ensure_column_unboxed(T, arr_list_{xibef__tmgiu}, i, arr_ind_{xibef__tmgiu})
"""
        bszs__obqq += f"""    out_arr_{xibef__tmgiu} = decode_if_dict_array(arr_list_{xibef__tmgiu}[i])
"""
        bszs__obqq += (
            f'    out_arr_list_{xibef__tmgiu}[i] = out_arr_{xibef__tmgiu}\n')
        bszs__obqq += (
            f'  T2 = set_table_block(T2, out_arr_list_{xibef__tmgiu}, {xibef__tmgiu})\n'
            )
    bszs__obqq += f'  T2 = set_table_len(T2, l)\n'
    bszs__obqq += f'  return T2\n'
    eyjq__oukr = {}
    exec(bszs__obqq, ffml__iwaui, eyjq__oukr)
    return eyjq__oukr['impl']


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
        rlsj__itqm = [arr_list_tup_typ.dtype.dtype] * len(arr_list_tup_typ)
    else:
        rlsj__itqm = []
        for typ in arr_list_tup_typ:
            if typ.dtype == types.undefined:
                return
            rlsj__itqm.append(typ.dtype)
    assert isinstance(nrows_typ, types.Integer
        ), 'init_runtime_table_from_lists requires an integer length'

    def codegen(context, builder, sig, args):
        ruvwo__dlbjp, yjl__pryqh = args
        pij__apdm = cgutils.create_struct_proxy(table_type)(context, builder)
        pij__apdm.len = yjl__pryqh
        bml__sxa = cgutils.unpack_tuple(builder, ruvwo__dlbjp)
        for i, rijn__vvi in enumerate(bml__sxa):
            setattr(pij__apdm, f'block_{i}', rijn__vvi)
            context.nrt.incref(builder, types.List(rlsj__itqm[i]), rijn__vvi)
        return pij__apdm._getvalue()
    table_type = TableType(tuple(rlsj__itqm), True)
    sig = table_type(arr_list_tup_typ, nrows_typ)
    return sig, codegen
