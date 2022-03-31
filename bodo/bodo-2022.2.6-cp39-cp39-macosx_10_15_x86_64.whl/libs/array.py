"""Tools for handling bodo arrays, e.g. passing to C/C++ code
"""
import llvmlite.binding as ll
import numba
import numpy as np
import pandas as pd
from llvmlite import ir as lir
from numba.core import cgutils, types
from numba.core.typing.templates import signature
from numba.cpython.listobj import ListInstance
from numba.extending import intrinsic, models, register_model
from numba.np.arrayobj import _getitem_array_single_int
import bodo
from bodo.hiframes.datetime_date_ext import datetime_date_array_type
from bodo.hiframes.pd_categorical_ext import CategoricalArrayType, get_categories_int_type
from bodo.libs import array_ext
from bodo.libs.array_item_arr_ext import ArrayItemArrayPayloadType, ArrayItemArrayType, _get_array_item_arr_payload, define_array_item_dtor, offset_type
from bodo.libs.binary_arr_ext import binary_array_type
from bodo.libs.bool_arr_ext import boolean_array
from bodo.libs.decimal_arr_ext import DecimalArrayType, int128_type
from bodo.libs.int_arr_ext import IntegerArrayType
from bodo.libs.interval_arr_ext import IntervalArrayType
from bodo.libs.map_arr_ext import MapArrayType, _get_map_arr_data_type, init_map_arr_codegen
from bodo.libs.str_arr_ext import _get_str_binary_arr_payload, char_arr_type, null_bitmap_arr_type, offset_arr_type, string_array_type
from bodo.libs.struct_arr_ext import StructArrayPayloadType, StructArrayType, StructType, _get_struct_arr_payload, define_struct_arr_dtor
from bodo.libs.tuple_arr_ext import TupleArrayType
from bodo.utils.typing import BodoError, MetaType, decode_if_dict_array, is_str_arr_type, raise_bodo_error
from bodo.utils.utils import CTypeEnum, check_and_propagate_cpp_exception, numba_to_c_type
ll.add_symbol('list_string_array_to_info', array_ext.list_string_array_to_info)
ll.add_symbol('nested_array_to_info', array_ext.nested_array_to_info)
ll.add_symbol('string_array_to_info', array_ext.string_array_to_info)
ll.add_symbol('dict_str_array_to_info', array_ext.dict_str_array_to_info)
ll.add_symbol('get_nested_info', array_ext.get_nested_info)
ll.add_symbol('get_has_global_dictionary', array_ext.get_has_global_dictionary)
ll.add_symbol('numpy_array_to_info', array_ext.numpy_array_to_info)
ll.add_symbol('categorical_array_to_info', array_ext.categorical_array_to_info)
ll.add_symbol('nullable_array_to_info', array_ext.nullable_array_to_info)
ll.add_symbol('interval_array_to_info', array_ext.interval_array_to_info)
ll.add_symbol('decimal_array_to_info', array_ext.decimal_array_to_info)
ll.add_symbol('info_to_nested_array', array_ext.info_to_nested_array)
ll.add_symbol('info_to_list_string_array', array_ext.info_to_list_string_array)
ll.add_symbol('info_to_string_array', array_ext.info_to_string_array)
ll.add_symbol('info_to_numpy_array', array_ext.info_to_numpy_array)
ll.add_symbol('info_to_nullable_array', array_ext.info_to_nullable_array)
ll.add_symbol('info_to_interval_array', array_ext.info_to_interval_array)
ll.add_symbol('alloc_numpy', array_ext.alloc_numpy)
ll.add_symbol('alloc_string_array', array_ext.alloc_string_array)
ll.add_symbol('arr_info_list_to_table', array_ext.arr_info_list_to_table)
ll.add_symbol('info_from_table', array_ext.info_from_table)
ll.add_symbol('delete_info_decref_array', array_ext.delete_info_decref_array)
ll.add_symbol('delete_table_decref_arrays', array_ext.
    delete_table_decref_arrays)
ll.add_symbol('delete_table', array_ext.delete_table)
ll.add_symbol('shuffle_table', array_ext.shuffle_table)
ll.add_symbol('get_shuffle_info', array_ext.get_shuffle_info)
ll.add_symbol('delete_shuffle_info', array_ext.delete_shuffle_info)
ll.add_symbol('reverse_shuffle_table', array_ext.reverse_shuffle_table)
ll.add_symbol('hash_join_table', array_ext.hash_join_table)
ll.add_symbol('drop_duplicates_table', array_ext.drop_duplicates_table)
ll.add_symbol('sort_values_table', array_ext.sort_values_table)
ll.add_symbol('sample_table', array_ext.sample_table)
ll.add_symbol('shuffle_renormalization', array_ext.shuffle_renormalization)
ll.add_symbol('shuffle_renormalization_group', array_ext.
    shuffle_renormalization_group)
ll.add_symbol('groupby_and_aggregate', array_ext.groupby_and_aggregate)
ll.add_symbol('pivot_groupby_and_aggregate', array_ext.
    pivot_groupby_and_aggregate)
ll.add_symbol('get_groupby_labels', array_ext.get_groupby_labels)
ll.add_symbol('array_isin', array_ext.array_isin)
ll.add_symbol('get_search_regex', array_ext.get_search_regex)
ll.add_symbol('array_info_getitem', array_ext.array_info_getitem)
ll.add_symbol('array_info_getdata1', array_ext.array_info_getdata1)


class ArrayInfoType(types.Type):

    def __init__(self):
        super(ArrayInfoType, self).__init__(name='ArrayInfoType()')


array_info_type = ArrayInfoType()
register_model(ArrayInfoType)(models.OpaqueModel)


class TableTypeCPP(types.Type):

    def __init__(self):
        super(TableTypeCPP, self).__init__(name='TableTypeCPP()')


table_type = TableTypeCPP()
register_model(TableTypeCPP)(models.OpaqueModel)


@intrinsic
def array_to_info(typingctx, arr_type_t=None):
    return array_info_type(arr_type_t), array_to_info_codegen


def array_to_info_codegen(context, builder, sig, args, incref=True):
    in_arr, = args
    arr_type = sig.args[0]
    if incref:
        context.nrt.incref(builder, arr_type, in_arr)
    if isinstance(arr_type, TupleArrayType):
        fmi__sbd = context.make_helper(builder, arr_type, in_arr)
        in_arr = fmi__sbd.data
        arr_type = StructArrayType(arr_type.data, ('dummy',) * len(arr_type
            .data))
    if isinstance(arr_type, ArrayItemArrayType
        ) and arr_type.dtype == string_array_type:
        sacw__jzlnd = context.make_helper(builder, arr_type, in_arr)
        dizka__xujg = lir.FunctionType(lir.IntType(8).as_pointer(), [lir.
            IntType(8).as_pointer()])
        gpnkh__rvh = cgutils.get_or_insert_function(builder.module,
            dizka__xujg, name='list_string_array_to_info')
        return builder.call(gpnkh__rvh, [sacw__jzlnd.meminfo])
    if isinstance(arr_type, (MapArrayType, ArrayItemArrayType, StructArrayType)
        ):

        def get_types(arr_typ):
            if isinstance(arr_typ, MapArrayType):
                return get_types(_get_map_arr_data_type(arr_typ))
            elif isinstance(arr_typ, ArrayItemArrayType):
                return [CTypeEnum.LIST.value] + get_types(arr_typ.dtype)
            elif isinstance(arr_typ, (StructType, StructArrayType)):
                ecs__aupe = [CTypeEnum.STRUCT.value, len(arr_typ.names)]
                for tkls__pmof in arr_typ.data:
                    ecs__aupe += get_types(tkls__pmof)
                return ecs__aupe
            elif isinstance(arr_typ, (types.Array, IntegerArrayType)
                ) or arr_typ == boolean_array:
                return get_types(arr_typ.dtype)
            elif arr_typ == string_array_type:
                return [CTypeEnum.STRING.value]
            elif arr_typ == binary_array_type:
                return [CTypeEnum.BINARY.value]
            elif isinstance(arr_typ, DecimalArrayType):
                return [CTypeEnum.Decimal.value, arr_typ.precision, arr_typ
                    .scale]
            else:
                return [numba_to_c_type(arr_typ)]

        def get_lengths(arr_typ, arr):
            knpz__uginh = context.compile_internal(builder, lambda a: len(a
                ), types.intp(arr_typ), [arr])
            if isinstance(arr_typ, MapArrayType):
                xdy__ymwpu = context.make_helper(builder, arr_typ, value=arr)
                pbw__hlhq = get_lengths(_get_map_arr_data_type(arr_typ),
                    xdy__ymwpu.data)
            elif isinstance(arr_typ, ArrayItemArrayType):
                ypxu__prwcc = _get_array_item_arr_payload(context, builder,
                    arr_typ, arr)
                pbw__hlhq = get_lengths(arr_typ.dtype, ypxu__prwcc.data)
                pbw__hlhq = cgutils.pack_array(builder, [ypxu__prwcc.
                    n_arrays] + [builder.extract_value(pbw__hlhq,
                    nggy__svcap) for nggy__svcap in range(pbw__hlhq.type.
                    count)])
            elif isinstance(arr_typ, StructArrayType):
                ypxu__prwcc = _get_struct_arr_payload(context, builder,
                    arr_typ, arr)
                pbw__hlhq = []
                for nggy__svcap, tkls__pmof in enumerate(arr_typ.data):
                    tjc__lks = get_lengths(tkls__pmof, builder.
                        extract_value(ypxu__prwcc.data, nggy__svcap))
                    pbw__hlhq += [builder.extract_value(tjc__lks,
                        tzebd__gfgd) for tzebd__gfgd in range(tjc__lks.type
                        .count)]
                pbw__hlhq = cgutils.pack_array(builder, [knpz__uginh,
                    context.get_constant(types.int64, -1)] + pbw__hlhq)
            elif isinstance(arr_typ, (IntegerArrayType, DecimalArrayType,
                types.Array)) or arr_typ in (boolean_array,
                datetime_date_array_type, string_array_type, binary_array_type
                ):
                pbw__hlhq = cgutils.pack_array(builder, [knpz__uginh])
            else:
                raise BodoError(
                    f'array_to_info: unsupported type for subarray {arr_typ}')
            return pbw__hlhq

        def get_buffers(arr_typ, arr):
            if isinstance(arr_typ, MapArrayType):
                xdy__ymwpu = context.make_helper(builder, arr_typ, value=arr)
                lgabh__qqpe = get_buffers(_get_map_arr_data_type(arr_typ),
                    xdy__ymwpu.data)
            elif isinstance(arr_typ, ArrayItemArrayType):
                ypxu__prwcc = _get_array_item_arr_payload(context, builder,
                    arr_typ, arr)
                eic__okc = get_buffers(arr_typ.dtype, ypxu__prwcc.data)
                fwyd__euw = context.make_array(types.Array(offset_type, 1, 'C')
                    )(context, builder, ypxu__prwcc.offsets)
                vvm__acrot = builder.bitcast(fwyd__euw.data, lir.IntType(8)
                    .as_pointer())
                byjvy__earr = context.make_array(types.Array(types.uint8, 1,
                    'C'))(context, builder, ypxu__prwcc.null_bitmap)
                oio__ygy = builder.bitcast(byjvy__earr.data, lir.IntType(8)
                    .as_pointer())
                lgabh__qqpe = cgutils.pack_array(builder, [vvm__acrot,
                    oio__ygy] + [builder.extract_value(eic__okc,
                    nggy__svcap) for nggy__svcap in range(eic__okc.type.count)]
                    )
            elif isinstance(arr_typ, StructArrayType):
                ypxu__prwcc = _get_struct_arr_payload(context, builder,
                    arr_typ, arr)
                eic__okc = []
                for nggy__svcap, tkls__pmof in enumerate(arr_typ.data):
                    zdsup__lcd = get_buffers(tkls__pmof, builder.
                        extract_value(ypxu__prwcc.data, nggy__svcap))
                    eic__okc += [builder.extract_value(zdsup__lcd,
                        tzebd__gfgd) for tzebd__gfgd in range(zdsup__lcd.
                        type.count)]
                byjvy__earr = context.make_array(types.Array(types.uint8, 1,
                    'C'))(context, builder, ypxu__prwcc.null_bitmap)
                oio__ygy = builder.bitcast(byjvy__earr.data, lir.IntType(8)
                    .as_pointer())
                lgabh__qqpe = cgutils.pack_array(builder, [oio__ygy] + eic__okc
                    )
            elif isinstance(arr_typ, (IntegerArrayType, DecimalArrayType)
                ) or arr_typ in (boolean_array, datetime_date_array_type):
                smve__arnn = arr_typ.dtype
                if isinstance(arr_typ, DecimalArrayType):
                    smve__arnn = int128_type
                elif arr_typ == datetime_date_array_type:
                    smve__arnn = types.int64
                arr = cgutils.create_struct_proxy(arr_typ)(context, builder,
                    arr)
                ysilu__sgmt = context.make_array(types.Array(smve__arnn, 1,
                    'C'))(context, builder, arr.data)
                byjvy__earr = context.make_array(types.Array(types.uint8, 1,
                    'C'))(context, builder, arr.null_bitmap)
                cltii__iuj = builder.bitcast(ysilu__sgmt.data, lir.IntType(
                    8).as_pointer())
                oio__ygy = builder.bitcast(byjvy__earr.data, lir.IntType(8)
                    .as_pointer())
                lgabh__qqpe = cgutils.pack_array(builder, [oio__ygy,
                    cltii__iuj])
            elif arr_typ in (string_array_type, binary_array_type):
                ypxu__prwcc = _get_str_binary_arr_payload(context, builder,
                    arr, arr_typ)
                eeu__rmmp = context.make_helper(builder, offset_arr_type,
                    ypxu__prwcc.offsets).data
                hylf__msil = context.make_helper(builder, char_arr_type,
                    ypxu__prwcc.data).data
                zuxp__nqk = context.make_helper(builder,
                    null_bitmap_arr_type, ypxu__prwcc.null_bitmap).data
                lgabh__qqpe = cgutils.pack_array(builder, [builder.bitcast(
                    eeu__rmmp, lir.IntType(8).as_pointer()), builder.
                    bitcast(zuxp__nqk, lir.IntType(8).as_pointer()),
                    builder.bitcast(hylf__msil, lir.IntType(8).as_pointer())])
            elif isinstance(arr_typ, types.Array):
                arr = context.make_array(arr_typ)(context, builder, arr)
                cltii__iuj = builder.bitcast(arr.data, lir.IntType(8).
                    as_pointer())
                abrqe__pseqz = lir.Constant(lir.IntType(8).as_pointer(), None)
                lgabh__qqpe = cgutils.pack_array(builder, [abrqe__pseqz,
                    cltii__iuj])
            else:
                raise RuntimeError(
                    'array_to_info: unsupported type for subarray ' + str(
                    arr_typ))
            return lgabh__qqpe

        def get_field_names(arr_typ):
            kfolh__ubxh = []
            if isinstance(arr_typ, StructArrayType):
                for wjjq__siy, muraw__iwvgn in zip(arr_typ.dtype.names,
                    arr_typ.data):
                    kfolh__ubxh.append(wjjq__siy)
                    kfolh__ubxh += get_field_names(muraw__iwvgn)
            elif isinstance(arr_typ, ArrayItemArrayType):
                kfolh__ubxh += get_field_names(arr_typ.dtype)
            elif isinstance(arr_typ, MapArrayType):
                kfolh__ubxh += get_field_names(_get_map_arr_data_type(arr_typ))
            return kfolh__ubxh
        ecs__aupe = get_types(arr_type)
        dxmmj__eakuz = cgutils.pack_array(builder, [context.get_constant(
            types.int32, t) for t in ecs__aupe])
        vrrz__uai = cgutils.alloca_once_value(builder, dxmmj__eakuz)
        pbw__hlhq = get_lengths(arr_type, in_arr)
        lengths_ptr = cgutils.alloca_once_value(builder, pbw__hlhq)
        lgabh__qqpe = get_buffers(arr_type, in_arr)
        lpdtd__eiy = cgutils.alloca_once_value(builder, lgabh__qqpe)
        kfolh__ubxh = get_field_names(arr_type)
        if len(kfolh__ubxh) == 0:
            kfolh__ubxh = ['irrelevant']
        pti__fmd = cgutils.pack_array(builder, [context.insert_const_string
            (builder.module, a) for a in kfolh__ubxh])
        xuns__sbbcw = cgutils.alloca_once_value(builder, pti__fmd)
        if isinstance(arr_type, MapArrayType):
            spfgb__toime = _get_map_arr_data_type(arr_type)
            zna__vslp = context.make_helper(builder, arr_type, value=in_arr)
            qmon__otz = zna__vslp.data
        else:
            spfgb__toime = arr_type
            qmon__otz = in_arr
        ylko__qhf = context.make_helper(builder, spfgb__toime, qmon__otz)
        dizka__xujg = lir.FunctionType(lir.IntType(8).as_pointer(), [lir.
            IntType(32).as_pointer(), lir.IntType(8).as_pointer().
            as_pointer(), lir.IntType(64).as_pointer(), lir.IntType(8).
            as_pointer(), lir.IntType(8).as_pointer()])
        gpnkh__rvh = cgutils.get_or_insert_function(builder.module,
            dizka__xujg, name='nested_array_to_info')
        lbv__nifgg = builder.call(gpnkh__rvh, [builder.bitcast(vrrz__uai,
            lir.IntType(32).as_pointer()), builder.bitcast(lpdtd__eiy, lir.
            IntType(8).as_pointer().as_pointer()), builder.bitcast(
            lengths_ptr, lir.IntType(64).as_pointer()), builder.bitcast(
            xuns__sbbcw, lir.IntType(8).as_pointer()), ylko__qhf.meminfo])
        context.compile_internal(builder, lambda :
            check_and_propagate_cpp_exception(), types.none(), [])
        return lbv__nifgg
    if arr_type in (string_array_type, binary_array_type):
        phha__dhzfc = context.make_helper(builder, arr_type, in_arr)
        vcys__beasx = ArrayItemArrayType(char_arr_type)
        sacw__jzlnd = context.make_helper(builder, vcys__beasx, phha__dhzfc
            .data)
        ypxu__prwcc = _get_str_binary_arr_payload(context, builder, in_arr,
            arr_type)
        eeu__rmmp = context.make_helper(builder, offset_arr_type,
            ypxu__prwcc.offsets).data
        hylf__msil = context.make_helper(builder, char_arr_type,
            ypxu__prwcc.data).data
        zuxp__nqk = context.make_helper(builder, null_bitmap_arr_type,
            ypxu__prwcc.null_bitmap).data
        zrfo__nxnzk = builder.zext(builder.load(builder.gep(eeu__rmmp, [
            ypxu__prwcc.n_arrays])), lir.IntType(64))
        ifnz__ovgi = context.get_constant(types.int32, int(arr_type ==
            binary_array_type))
        dizka__xujg = lir.FunctionType(lir.IntType(8).as_pointer(), [lir.
            IntType(64), lir.IntType(64), lir.IntType(8).as_pointer(), lir.
            IntType(offset_type.bitwidth).as_pointer(), lir.IntType(8).
            as_pointer(), lir.IntType(8).as_pointer(), lir.IntType(32)])
        gpnkh__rvh = cgutils.get_or_insert_function(builder.module,
            dizka__xujg, name='string_array_to_info')
        return builder.call(gpnkh__rvh, [ypxu__prwcc.n_arrays, zrfo__nxnzk,
            hylf__msil, eeu__rmmp, zuxp__nqk, sacw__jzlnd.meminfo, ifnz__ovgi])
    if arr_type == bodo.dict_str_arr_type:
        arr = cgutils.create_struct_proxy(arr_type)(context, builder, in_arr)
        hwltc__tiwb = arr.data
        ulin__oiyn = arr.indices
        sig = array_info_type(arr_type.data)
        pcdqm__pliw = array_to_info_codegen(context, builder, sig, (
            hwltc__tiwb,), False)
        sig = array_info_type(bodo.libs.dict_arr_ext.dict_indices_arr_type)
        qovut__ufhb = array_to_info_codegen(context, builder, sig, (
            ulin__oiyn,), False)
        tdsdv__btpfv = cgutils.create_struct_proxy(bodo.libs.dict_arr_ext.
            dict_indices_arr_type)(context, builder, ulin__oiyn)
        oio__ygy = context.make_array(types.Array(types.uint8, 1, 'C'))(context
            , builder, tdsdv__btpfv.null_bitmap).data
        dizka__xujg = lir.FunctionType(lir.IntType(8).as_pointer(), [lir.
            IntType(8).as_pointer(), lir.IntType(8).as_pointer(), lir.
            IntType(8).as_pointer(), lir.IntType(32)])
        gpnkh__rvh = cgutils.get_or_insert_function(builder.module,
            dizka__xujg, name='dict_str_array_to_info')
        hkur__huzy = builder.zext(arr.has_global_dictionary, lir.IntType(32))
        return builder.call(gpnkh__rvh, [pcdqm__pliw, qovut__ufhb, builder.
            bitcast(oio__ygy, lir.IntType(8).as_pointer()), hkur__huzy])
    lbi__nrxx = False
    if isinstance(arr_type, CategoricalArrayType):
        context.nrt.decref(builder, arr_type, in_arr)
        ejc__hajoe = context.compile_internal(builder, lambda a: len(a.
            dtype.categories), types.intp(arr_type), [in_arr])
        in_arr = cgutils.create_struct_proxy(arr_type)(context, builder, in_arr
            ).codes
        pwz__pjvol = get_categories_int_type(arr_type.dtype)
        arr_type = types.Array(pwz__pjvol, 1, 'C')
        lbi__nrxx = True
        context.nrt.incref(builder, arr_type, in_arr)
    if isinstance(arr_type, bodo.DatetimeArrayType):
        if lbi__nrxx:
            raise BodoError(
                'array_to_info(): Categorical PandasDatetimeArrayType not supported'
                )
        in_arr = cgutils.create_struct_proxy(arr_type)(context, builder, in_arr
            ).data
        arr_type = arr_type.data_array_type
    if isinstance(arr_type, types.Array):
        arr = context.make_array(arr_type)(context, builder, in_arr)
        assert arr_type.ndim == 1, 'only 1D array shuffle supported'
        knpz__uginh = builder.extract_value(arr.shape, 0)
        wbvar__zwblz = arr_type.dtype
        mvjkv__hho = numba_to_c_type(wbvar__zwblz)
        hlhkw__bmo = cgutils.alloca_once_value(builder, lir.Constant(lir.
            IntType(32), mvjkv__hho))
        if lbi__nrxx:
            dizka__xujg = lir.FunctionType(lir.IntType(8).as_pointer(), [
                lir.IntType(64), lir.IntType(8).as_pointer(), lir.IntType(
                32), lir.IntType(64), lir.IntType(8).as_pointer()])
            gpnkh__rvh = cgutils.get_or_insert_function(builder.module,
                dizka__xujg, name='categorical_array_to_info')
            return builder.call(gpnkh__rvh, [knpz__uginh, builder.bitcast(
                arr.data, lir.IntType(8).as_pointer()), builder.load(
                hlhkw__bmo), ejc__hajoe, arr.meminfo])
        else:
            dizka__xujg = lir.FunctionType(lir.IntType(8).as_pointer(), [
                lir.IntType(64), lir.IntType(8).as_pointer(), lir.IntType(
                32), lir.IntType(8).as_pointer()])
            gpnkh__rvh = cgutils.get_or_insert_function(builder.module,
                dizka__xujg, name='numpy_array_to_info')
            return builder.call(gpnkh__rvh, [knpz__uginh, builder.bitcast(
                arr.data, lir.IntType(8).as_pointer()), builder.load(
                hlhkw__bmo), arr.meminfo])
    if isinstance(arr_type, (IntegerArrayType, DecimalArrayType)
        ) or arr_type in (boolean_array, datetime_date_array_type):
        arr = cgutils.create_struct_proxy(arr_type)(context, builder, in_arr)
        wbvar__zwblz = arr_type.dtype
        smve__arnn = wbvar__zwblz
        if isinstance(arr_type, DecimalArrayType):
            smve__arnn = int128_type
        if arr_type == datetime_date_array_type:
            smve__arnn = types.int64
        ysilu__sgmt = context.make_array(types.Array(smve__arnn, 1, 'C'))(
            context, builder, arr.data)
        knpz__uginh = builder.extract_value(ysilu__sgmt.shape, 0)
        lcdj__ita = context.make_array(types.Array(types.uint8, 1, 'C'))(
            context, builder, arr.null_bitmap)
        mvjkv__hho = numba_to_c_type(wbvar__zwblz)
        hlhkw__bmo = cgutils.alloca_once_value(builder, lir.Constant(lir.
            IntType(32), mvjkv__hho))
        if isinstance(arr_type, DecimalArrayType):
            dizka__xujg = lir.FunctionType(lir.IntType(8).as_pointer(), [
                lir.IntType(64), lir.IntType(8).as_pointer(), lir.IntType(
                32), lir.IntType(8).as_pointer(), lir.IntType(8).as_pointer
                (), lir.IntType(8).as_pointer(), lir.IntType(32), lir.
                IntType(32)])
            gpnkh__rvh = cgutils.get_or_insert_function(builder.module,
                dizka__xujg, name='decimal_array_to_info')
            return builder.call(gpnkh__rvh, [knpz__uginh, builder.bitcast(
                ysilu__sgmt.data, lir.IntType(8).as_pointer()), builder.
                load(hlhkw__bmo), builder.bitcast(lcdj__ita.data, lir.
                IntType(8).as_pointer()), ysilu__sgmt.meminfo, lcdj__ita.
                meminfo, context.get_constant(types.int32, arr_type.
                precision), context.get_constant(types.int32, arr_type.scale)])
        else:
            dizka__xujg = lir.FunctionType(lir.IntType(8).as_pointer(), [
                lir.IntType(64), lir.IntType(8).as_pointer(), lir.IntType(
                32), lir.IntType(8).as_pointer(), lir.IntType(8).as_pointer
                (), lir.IntType(8).as_pointer()])
            gpnkh__rvh = cgutils.get_or_insert_function(builder.module,
                dizka__xujg, name='nullable_array_to_info')
            return builder.call(gpnkh__rvh, [knpz__uginh, builder.bitcast(
                ysilu__sgmt.data, lir.IntType(8).as_pointer()), builder.
                load(hlhkw__bmo), builder.bitcast(lcdj__ita.data, lir.
                IntType(8).as_pointer()), ysilu__sgmt.meminfo, lcdj__ita.
                meminfo])
    if isinstance(arr_type, IntervalArrayType):
        assert isinstance(arr_type.arr_type, types.Array
            ), 'array_to_info(): only IntervalArrayType with Numpy arrays supported'
        arr = cgutils.create_struct_proxy(arr_type)(context, builder, in_arr)
        gaww__xxkr = context.make_array(arr_type.arr_type)(context, builder,
            arr.left)
        dozc__hyvzk = context.make_array(arr_type.arr_type)(context,
            builder, arr.right)
        knpz__uginh = builder.extract_value(gaww__xxkr.shape, 0)
        mvjkv__hho = numba_to_c_type(arr_type.arr_type.dtype)
        hlhkw__bmo = cgutils.alloca_once_value(builder, lir.Constant(lir.
            IntType(32), mvjkv__hho))
        dizka__xujg = lir.FunctionType(lir.IntType(8).as_pointer(), [lir.
            IntType(64), lir.IntType(8).as_pointer(), lir.IntType(8).
            as_pointer(), lir.IntType(32), lir.IntType(8).as_pointer(), lir
            .IntType(8).as_pointer()])
        gpnkh__rvh = cgutils.get_or_insert_function(builder.module,
            dizka__xujg, name='interval_array_to_info')
        return builder.call(gpnkh__rvh, [knpz__uginh, builder.bitcast(
            gaww__xxkr.data, lir.IntType(8).as_pointer()), builder.bitcast(
            dozc__hyvzk.data, lir.IntType(8).as_pointer()), builder.load(
            hlhkw__bmo), gaww__xxkr.meminfo, dozc__hyvzk.meminfo])
    raise_bodo_error(f'array_to_info(): array type {arr_type} is not supported'
        )


def _lower_info_to_array_numpy(arr_type, context, builder, in_info):
    assert arr_type.ndim == 1, 'only 1D array supported'
    arr = context.make_array(arr_type)(context, builder)
    coac__irame = cgutils.alloca_once(builder, lir.IntType(64))
    cltii__iuj = cgutils.alloca_once(builder, lir.IntType(8).as_pointer())
    nedz__pktd = cgutils.alloca_once(builder, lir.IntType(8).as_pointer())
    dizka__xujg = lir.FunctionType(lir.VoidType(), [lir.IntType(8).
        as_pointer(), lir.IntType(64).as_pointer(), lir.IntType(8).
        as_pointer().as_pointer(), lir.IntType(8).as_pointer().as_pointer()])
    gpnkh__rvh = cgutils.get_or_insert_function(builder.module, dizka__xujg,
        name='info_to_numpy_array')
    builder.call(gpnkh__rvh, [in_info, coac__irame, cltii__iuj, nedz__pktd])
    context.compile_internal(builder, lambda :
        check_and_propagate_cpp_exception(), types.none(), [])
    vgtku__hluwd = context.get_value_type(types.intp)
    ivm__mttqe = cgutils.pack_array(builder, [builder.load(coac__irame)],
        ty=vgtku__hluwd)
    vyxsq__hwtk = context.get_constant(types.intp, context.get_abi_sizeof(
        context.get_data_type(arr_type.dtype)))
    wgw__bosq = cgutils.pack_array(builder, [vyxsq__hwtk], ty=vgtku__hluwd)
    hylf__msil = builder.bitcast(builder.load(cltii__iuj), context.
        get_data_type(arr_type.dtype).as_pointer())
    numba.np.arrayobj.populate_array(arr, data=hylf__msil, shape=ivm__mttqe,
        strides=wgw__bosq, itemsize=vyxsq__hwtk, meminfo=builder.load(
        nedz__pktd))
    return arr._getvalue()


def _lower_info_to_array_list_string_array(arr_type, context, builder, in_info
    ):
    ofg__wuzjj = context.make_helper(builder, arr_type)
    dizka__xujg = lir.FunctionType(lir.VoidType(), [lir.IntType(8).
        as_pointer(), lir.IntType(8).as_pointer().as_pointer()])
    gpnkh__rvh = cgutils.get_or_insert_function(builder.module, dizka__xujg,
        name='info_to_list_string_array')
    builder.call(gpnkh__rvh, [in_info, ofg__wuzjj._get_ptr_by_name('meminfo')])
    context.compile_internal(builder, lambda :
        check_and_propagate_cpp_exception(), types.none(), [])
    return ofg__wuzjj._getvalue()


def nested_to_array(context, builder, arr_typ, lengths_ptr, array_infos_ptr,
    lengths_pos, infos_pos):
    uieoj__kowk = context.get_data_type(array_info_type)
    if isinstance(arr_typ, ArrayItemArrayType):
        arli__rom = lengths_pos
        flyn__mkqou = infos_pos
        uwk__gqx, lengths_pos, infos_pos = nested_to_array(context, builder,
            arr_typ.dtype, lengths_ptr, array_infos_ptr, lengths_pos + 1, 
            infos_pos + 2)
        pditt__hdxn = ArrayItemArrayPayloadType(arr_typ)
        taxui__mjn = context.get_data_type(pditt__hdxn)
        fmk__wor = context.get_abi_sizeof(taxui__mjn)
        rmwd__smlrj = define_array_item_dtor(context, builder, arr_typ,
            pditt__hdxn)
        qwrnc__rbhy = context.nrt.meminfo_alloc_dtor(builder, context.
            get_constant(types.uintp, fmk__wor), rmwd__smlrj)
        kpdvl__akouo = context.nrt.meminfo_data(builder, qwrnc__rbhy)
        tglf__yxizu = builder.bitcast(kpdvl__akouo, taxui__mjn.as_pointer())
        ypxu__prwcc = cgutils.create_struct_proxy(pditt__hdxn)(context, builder
            )
        ypxu__prwcc.n_arrays = builder.extract_value(builder.load(
            lengths_ptr), arli__rom)
        ypxu__prwcc.data = uwk__gqx
        ksdhn__uliw = builder.load(array_infos_ptr)
        jrt__jcr = builder.bitcast(builder.extract_value(ksdhn__uliw,
            flyn__mkqou), uieoj__kowk)
        ypxu__prwcc.offsets = _lower_info_to_array_numpy(types.Array(
            offset_type, 1, 'C'), context, builder, jrt__jcr)
        lkkpm__aspbt = builder.bitcast(builder.extract_value(ksdhn__uliw, 
            flyn__mkqou + 1), uieoj__kowk)
        ypxu__prwcc.null_bitmap = _lower_info_to_array_numpy(types.Array(
            types.uint8, 1, 'C'), context, builder, lkkpm__aspbt)
        builder.store(ypxu__prwcc._getvalue(), tglf__yxizu)
        sacw__jzlnd = context.make_helper(builder, arr_typ)
        sacw__jzlnd.meminfo = qwrnc__rbhy
        return sacw__jzlnd._getvalue(), lengths_pos, infos_pos
    elif isinstance(arr_typ, StructArrayType):
        xwm__gicwn = []
        flyn__mkqou = infos_pos
        lengths_pos += 1
        infos_pos += 1
        for jxf__uvok in arr_typ.data:
            uwk__gqx, lengths_pos, infos_pos = nested_to_array(context,
                builder, jxf__uvok, lengths_ptr, array_infos_ptr,
                lengths_pos, infos_pos)
            xwm__gicwn.append(uwk__gqx)
        pditt__hdxn = StructArrayPayloadType(arr_typ.data)
        taxui__mjn = context.get_value_type(pditt__hdxn)
        fmk__wor = context.get_abi_sizeof(taxui__mjn)
        rmwd__smlrj = define_struct_arr_dtor(context, builder, arr_typ,
            pditt__hdxn)
        qwrnc__rbhy = context.nrt.meminfo_alloc_dtor(builder, context.
            get_constant(types.uintp, fmk__wor), rmwd__smlrj)
        kpdvl__akouo = context.nrt.meminfo_data(builder, qwrnc__rbhy)
        tglf__yxizu = builder.bitcast(kpdvl__akouo, taxui__mjn.as_pointer())
        ypxu__prwcc = cgutils.create_struct_proxy(pditt__hdxn)(context, builder
            )
        ypxu__prwcc.data = cgutils.pack_array(builder, xwm__gicwn
            ) if types.is_homogeneous(*arr_typ.data) else cgutils.pack_struct(
            builder, xwm__gicwn)
        ksdhn__uliw = builder.load(array_infos_ptr)
        lkkpm__aspbt = builder.bitcast(builder.extract_value(ksdhn__uliw,
            flyn__mkqou), uieoj__kowk)
        ypxu__prwcc.null_bitmap = _lower_info_to_array_numpy(types.Array(
            types.uint8, 1, 'C'), context, builder, lkkpm__aspbt)
        builder.store(ypxu__prwcc._getvalue(), tglf__yxizu)
        dzke__mjgm = context.make_helper(builder, arr_typ)
        dzke__mjgm.meminfo = qwrnc__rbhy
        return dzke__mjgm._getvalue(), lengths_pos, infos_pos
    elif arr_typ in (string_array_type, binary_array_type):
        ksdhn__uliw = builder.load(array_infos_ptr)
        yclfz__roev = builder.bitcast(builder.extract_value(ksdhn__uliw,
            infos_pos), uieoj__kowk)
        phha__dhzfc = context.make_helper(builder, arr_typ)
        vcys__beasx = ArrayItemArrayType(char_arr_type)
        sacw__jzlnd = context.make_helper(builder, vcys__beasx)
        dizka__xujg = lir.FunctionType(lir.VoidType(), [lir.IntType(8).
            as_pointer(), lir.IntType(8).as_pointer().as_pointer()])
        gpnkh__rvh = cgutils.get_or_insert_function(builder.module,
            dizka__xujg, name='info_to_string_array')
        builder.call(gpnkh__rvh, [yclfz__roev, sacw__jzlnd._get_ptr_by_name
            ('meminfo')])
        context.compile_internal(builder, lambda :
            check_and_propagate_cpp_exception(), types.none(), [])
        phha__dhzfc.data = sacw__jzlnd._getvalue()
        return phha__dhzfc._getvalue(), lengths_pos + 1, infos_pos + 1
    elif isinstance(arr_typ, types.Array):
        ksdhn__uliw = builder.load(array_infos_ptr)
        wgs__kqd = builder.bitcast(builder.extract_value(ksdhn__uliw, 
            infos_pos + 1), uieoj__kowk)
        return _lower_info_to_array_numpy(arr_typ, context, builder, wgs__kqd
            ), lengths_pos + 1, infos_pos + 2
    elif isinstance(arr_typ, (IntegerArrayType, DecimalArrayType)
        ) or arr_typ in (boolean_array, datetime_date_array_type):
        arr = cgutils.create_struct_proxy(arr_typ)(context, builder)
        smve__arnn = arr_typ.dtype
        if isinstance(arr_typ, DecimalArrayType):
            smve__arnn = int128_type
        elif arr_typ == datetime_date_array_type:
            smve__arnn = types.int64
        ksdhn__uliw = builder.load(array_infos_ptr)
        lkkpm__aspbt = builder.bitcast(builder.extract_value(ksdhn__uliw,
            infos_pos), uieoj__kowk)
        arr.null_bitmap = _lower_info_to_array_numpy(types.Array(types.
            uint8, 1, 'C'), context, builder, lkkpm__aspbt)
        wgs__kqd = builder.bitcast(builder.extract_value(ksdhn__uliw, 
            infos_pos + 1), uieoj__kowk)
        arr.data = _lower_info_to_array_numpy(types.Array(smve__arnn, 1,
            'C'), context, builder, wgs__kqd)
        return arr._getvalue(), lengths_pos + 1, infos_pos + 2


def info_to_array_codegen(context, builder, sig, args):
    array_type = sig.args[1]
    arr_type = array_type.instance_type if isinstance(array_type, types.TypeRef
        ) else array_type
    in_info, lqck__fver = args
    if isinstance(arr_type, ArrayItemArrayType
        ) and arr_type.dtype == string_array_type:
        return _lower_info_to_array_list_string_array(arr_type, context,
            builder, in_info)
    if isinstance(arr_type, (MapArrayType, ArrayItemArrayType,
        StructArrayType, TupleArrayType)):

        def get_num_arrays(arr_typ):
            if isinstance(arr_typ, ArrayItemArrayType):
                return 1 + get_num_arrays(arr_typ.dtype)
            elif isinstance(arr_typ, StructArrayType):
                return 1 + sum([get_num_arrays(jxf__uvok) for jxf__uvok in
                    arr_typ.data])
            else:
                return 1

        def get_num_infos(arr_typ):
            if isinstance(arr_typ, ArrayItemArrayType):
                return 2 + get_num_infos(arr_typ.dtype)
            elif isinstance(arr_typ, StructArrayType):
                return 1 + sum([get_num_infos(jxf__uvok) for jxf__uvok in
                    arr_typ.data])
            elif arr_typ in (string_array_type, binary_array_type):
                return 1
            else:
                return 2
        if isinstance(arr_type, TupleArrayType):
            khz__hwfzk = StructArrayType(arr_type.data, ('dummy',) * len(
                arr_type.data))
        elif isinstance(arr_type, MapArrayType):
            khz__hwfzk = _get_map_arr_data_type(arr_type)
        else:
            khz__hwfzk = arr_type
        hlpb__cwjb = get_num_arrays(khz__hwfzk)
        pbw__hlhq = cgutils.pack_array(builder, [lir.Constant(lir.IntType(
            64), 0) for lqck__fver in range(hlpb__cwjb)])
        lengths_ptr = cgutils.alloca_once_value(builder, pbw__hlhq)
        abrqe__pseqz = lir.Constant(lir.IntType(8).as_pointer(), None)
        xtr__ijdhy = cgutils.pack_array(builder, [abrqe__pseqz for
            lqck__fver in range(get_num_infos(khz__hwfzk))])
        array_infos_ptr = cgutils.alloca_once_value(builder, xtr__ijdhy)
        dizka__xujg = lir.FunctionType(lir.VoidType(), [lir.IntType(8).
            as_pointer(), lir.IntType(64).as_pointer(), lir.IntType(8).
            as_pointer().as_pointer()])
        gpnkh__rvh = cgutils.get_or_insert_function(builder.module,
            dizka__xujg, name='info_to_nested_array')
        builder.call(gpnkh__rvh, [in_info, builder.bitcast(lengths_ptr, lir
            .IntType(64).as_pointer()), builder.bitcast(array_infos_ptr,
            lir.IntType(8).as_pointer().as_pointer())])
        context.compile_internal(builder, lambda :
            check_and_propagate_cpp_exception(), types.none(), [])
        arr, lqck__fver, lqck__fver = nested_to_array(context, builder,
            khz__hwfzk, lengths_ptr, array_infos_ptr, 0, 0)
        if isinstance(arr_type, TupleArrayType):
            fmi__sbd = context.make_helper(builder, arr_type)
            fmi__sbd.data = arr
            context.nrt.incref(builder, khz__hwfzk, arr)
            arr = fmi__sbd._getvalue()
        elif isinstance(arr_type, MapArrayType):
            sig = signature(arr_type, khz__hwfzk)
            arr = init_map_arr_codegen(context, builder, sig, (arr,))
        return arr
    if arr_type in (string_array_type, binary_array_type):
        phha__dhzfc = context.make_helper(builder, arr_type)
        vcys__beasx = ArrayItemArrayType(char_arr_type)
        sacw__jzlnd = context.make_helper(builder, vcys__beasx)
        dizka__xujg = lir.FunctionType(lir.VoidType(), [lir.IntType(8).
            as_pointer(), lir.IntType(8).as_pointer().as_pointer()])
        gpnkh__rvh = cgutils.get_or_insert_function(builder.module,
            dizka__xujg, name='info_to_string_array')
        builder.call(gpnkh__rvh, [in_info, sacw__jzlnd._get_ptr_by_name(
            'meminfo')])
        context.compile_internal(builder, lambda :
            check_and_propagate_cpp_exception(), types.none(), [])
        phha__dhzfc.data = sacw__jzlnd._getvalue()
        return phha__dhzfc._getvalue()
    if arr_type == bodo.dict_str_arr_type:
        dizka__xujg = lir.FunctionType(lir.IntType(8).as_pointer(), [lir.
            IntType(8).as_pointer(), lir.IntType(32)])
        gpnkh__rvh = cgutils.get_or_insert_function(builder.module,
            dizka__xujg, name='get_nested_info')
        pcdqm__pliw = builder.call(gpnkh__rvh, [in_info, lir.Constant(lir.
            IntType(32), 1)])
        qovut__ufhb = builder.call(gpnkh__rvh, [in_info, lir.Constant(lir.
            IntType(32), 2)])
        vgfz__xhc = context.make_helper(builder, arr_type)
        sig = arr_type.data(array_info_type, arr_type.data)
        vgfz__xhc.data = info_to_array_codegen(context, builder, sig, (
            pcdqm__pliw, context.get_constant_null(arr_type.data)))
        ajk__grqlt = bodo.libs.dict_arr_ext.dict_indices_arr_type
        sig = ajk__grqlt(array_info_type, ajk__grqlt)
        vgfz__xhc.indices = info_to_array_codegen(context, builder, sig, (
            qovut__ufhb, context.get_constant_null(ajk__grqlt)))
        dizka__xujg = lir.FunctionType(lir.IntType(32), [lir.IntType(8).
            as_pointer()])
        gpnkh__rvh = cgutils.get_or_insert_function(builder.module,
            dizka__xujg, name='get_has_global_dictionary')
        hkur__huzy = builder.call(gpnkh__rvh, [in_info])
        vgfz__xhc.has_global_dictionary = builder.trunc(hkur__huzy, cgutils
            .bool_t)
        return vgfz__xhc._getvalue()
    if isinstance(arr_type, CategoricalArrayType):
        out_arr = cgutils.create_struct_proxy(arr_type)(context, builder)
        pwz__pjvol = get_categories_int_type(arr_type.dtype)
        wzz__orwgz = types.Array(pwz__pjvol, 1, 'C')
        out_arr.codes = _lower_info_to_array_numpy(wzz__orwgz, context,
            builder, in_info)
        if isinstance(array_type, types.TypeRef):
            assert arr_type.dtype.categories is not None, 'info_to_array: unknown categories'
            is_ordered = arr_type.dtype.ordered
            kfez__xnwvn = pd.CategoricalDtype(arr_type.dtype.categories,
                is_ordered).categories.values
            new_cats_tup = MetaType(tuple(kfez__xnwvn))
            int_type = arr_type.dtype.int_type
            nseq__bfte = bodo.typeof(kfez__xnwvn)
            pdx__dtlh = context.get_constant_generic(builder, nseq__bfte,
                kfez__xnwvn)
            wbvar__zwblz = context.compile_internal(builder, lambda c_arr:
                bodo.hiframes.pd_categorical_ext.init_cat_dtype(bodo.utils.
                conversion.index_from_array(c_arr), is_ordered, int_type,
                new_cats_tup), arr_type.dtype(nseq__bfte), [pdx__dtlh])
        else:
            wbvar__zwblz = cgutils.create_struct_proxy(arr_type)(context,
                builder, args[1]).dtype
            context.nrt.incref(builder, arr_type.dtype, wbvar__zwblz)
        out_arr.dtype = wbvar__zwblz
        return out_arr._getvalue()
    if isinstance(arr_type, bodo.DatetimeArrayType):
        arr = cgutils.create_struct_proxy(arr_type)(context, builder)
        hylf__msil = _lower_info_to_array_numpy(arr_type.data_array_type,
            context, builder, in_info)
        arr.data = hylf__msil
        return arr._getvalue()
    if isinstance(arr_type, types.Array):
        return _lower_info_to_array_numpy(arr_type, context, builder, in_info)
    if isinstance(arr_type, (IntegerArrayType, DecimalArrayType)
        ) or arr_type in (boolean_array, datetime_date_array_type):
        arr = cgutils.create_struct_proxy(arr_type)(context, builder)
        smve__arnn = arr_type.dtype
        if isinstance(arr_type, DecimalArrayType):
            smve__arnn = int128_type
        elif arr_type == datetime_date_array_type:
            smve__arnn = types.int64
        elwd__srsvv = types.Array(smve__arnn, 1, 'C')
        ysilu__sgmt = context.make_array(elwd__srsvv)(context, builder)
        nhsy__rwdcu = types.Array(types.uint8, 1, 'C')
        plu__uxpms = context.make_array(nhsy__rwdcu)(context, builder)
        coac__irame = cgutils.alloca_once(builder, lir.IntType(64))
        oost__omu = cgutils.alloca_once(builder, lir.IntType(64))
        cltii__iuj = cgutils.alloca_once(builder, lir.IntType(8).as_pointer())
        xvpm__cli = cgutils.alloca_once(builder, lir.IntType(8).as_pointer())
        nedz__pktd = cgutils.alloca_once(builder, lir.IntType(8).as_pointer())
        olgsy__ovih = cgutils.alloca_once(builder, lir.IntType(8).as_pointer())
        dizka__xujg = lir.FunctionType(lir.VoidType(), [lir.IntType(8).
            as_pointer(), lir.IntType(64).as_pointer(), lir.IntType(64).
            as_pointer(), lir.IntType(8).as_pointer().as_pointer(), lir.
            IntType(8).as_pointer().as_pointer(), lir.IntType(8).as_pointer
            ().as_pointer(), lir.IntType(8).as_pointer().as_pointer()])
        gpnkh__rvh = cgutils.get_or_insert_function(builder.module,
            dizka__xujg, name='info_to_nullable_array')
        builder.call(gpnkh__rvh, [in_info, coac__irame, oost__omu,
            cltii__iuj, xvpm__cli, nedz__pktd, olgsy__ovih])
        context.compile_internal(builder, lambda :
            check_and_propagate_cpp_exception(), types.none(), [])
        vgtku__hluwd = context.get_value_type(types.intp)
        ivm__mttqe = cgutils.pack_array(builder, [builder.load(coac__irame)
            ], ty=vgtku__hluwd)
        vyxsq__hwtk = context.get_constant(types.intp, context.
            get_abi_sizeof(context.get_data_type(smve__arnn)))
        wgw__bosq = cgutils.pack_array(builder, [vyxsq__hwtk], ty=vgtku__hluwd)
        hylf__msil = builder.bitcast(builder.load(cltii__iuj), context.
            get_data_type(smve__arnn).as_pointer())
        numba.np.arrayobj.populate_array(ysilu__sgmt, data=hylf__msil,
            shape=ivm__mttqe, strides=wgw__bosq, itemsize=vyxsq__hwtk,
            meminfo=builder.load(nedz__pktd))
        arr.data = ysilu__sgmt._getvalue()
        ivm__mttqe = cgutils.pack_array(builder, [builder.load(oost__omu)],
            ty=vgtku__hluwd)
        vyxsq__hwtk = context.get_constant(types.intp, context.
            get_abi_sizeof(context.get_data_type(types.uint8)))
        wgw__bosq = cgutils.pack_array(builder, [vyxsq__hwtk], ty=vgtku__hluwd)
        hylf__msil = builder.bitcast(builder.load(xvpm__cli), context.
            get_data_type(types.uint8).as_pointer())
        numba.np.arrayobj.populate_array(plu__uxpms, data=hylf__msil, shape
            =ivm__mttqe, strides=wgw__bosq, itemsize=vyxsq__hwtk, meminfo=
            builder.load(olgsy__ovih))
        arr.null_bitmap = plu__uxpms._getvalue()
        return arr._getvalue()
    if isinstance(arr_type, IntervalArrayType):
        arr = cgutils.create_struct_proxy(arr_type)(context, builder)
        gaww__xxkr = context.make_array(arr_type.arr_type)(context, builder)
        dozc__hyvzk = context.make_array(arr_type.arr_type)(context, builder)
        coac__irame = cgutils.alloca_once(builder, lir.IntType(64))
        njlc__lso = cgutils.alloca_once(builder, lir.IntType(8).as_pointer())
        ncas__bkjdp = cgutils.alloca_once(builder, lir.IntType(8).as_pointer())
        fnuhc__qxjbf = cgutils.alloca_once(builder, lir.IntType(8).as_pointer()
            )
        chuza__zgz = cgutils.alloca_once(builder, lir.IntType(8).as_pointer())
        dizka__xujg = lir.FunctionType(lir.VoidType(), [lir.IntType(8).
            as_pointer(), lir.IntType(64).as_pointer(), lir.IntType(8).
            as_pointer().as_pointer(), lir.IntType(8).as_pointer().
            as_pointer(), lir.IntType(8).as_pointer().as_pointer(), lir.
            IntType(8).as_pointer().as_pointer()])
        gpnkh__rvh = cgutils.get_or_insert_function(builder.module,
            dizka__xujg, name='info_to_interval_array')
        builder.call(gpnkh__rvh, [in_info, coac__irame, njlc__lso,
            ncas__bkjdp, fnuhc__qxjbf, chuza__zgz])
        context.compile_internal(builder, lambda :
            check_and_propagate_cpp_exception(), types.none(), [])
        vgtku__hluwd = context.get_value_type(types.intp)
        ivm__mttqe = cgutils.pack_array(builder, [builder.load(coac__irame)
            ], ty=vgtku__hluwd)
        vyxsq__hwtk = context.get_constant(types.intp, context.
            get_abi_sizeof(context.get_data_type(arr_type.arr_type.dtype)))
        wgw__bosq = cgutils.pack_array(builder, [vyxsq__hwtk], ty=vgtku__hluwd)
        axls__kpuv = builder.bitcast(builder.load(njlc__lso), context.
            get_data_type(arr_type.arr_type.dtype).as_pointer())
        numba.np.arrayobj.populate_array(gaww__xxkr, data=axls__kpuv, shape
            =ivm__mttqe, strides=wgw__bosq, itemsize=vyxsq__hwtk, meminfo=
            builder.load(fnuhc__qxjbf))
        arr.left = gaww__xxkr._getvalue()
        srf__hzqeg = builder.bitcast(builder.load(ncas__bkjdp), context.
            get_data_type(arr_type.arr_type.dtype).as_pointer())
        numba.np.arrayobj.populate_array(dozc__hyvzk, data=srf__hzqeg,
            shape=ivm__mttqe, strides=wgw__bosq, itemsize=vyxsq__hwtk,
            meminfo=builder.load(chuza__zgz))
        arr.right = dozc__hyvzk._getvalue()
        return arr._getvalue()
    raise_bodo_error(f'info_to_array(): array type {arr_type} is not supported'
        )


@intrinsic
def info_to_array(typingctx, info_type, array_type):
    arr_type = array_type.instance_type if isinstance(array_type, types.TypeRef
        ) else array_type
    assert info_type == array_info_type, 'info_to_array: expected info type'
    return arr_type(info_type, array_type), info_to_array_codegen


@intrinsic
def test_alloc_np(typingctx, len_typ, arr_type):
    array_type = arr_type.instance_type if isinstance(arr_type, types.TypeRef
        ) else arr_type

    def codegen(context, builder, sig, args):
        knpz__uginh, lqck__fver = args
        mvjkv__hho = numba_to_c_type(array_type.dtype)
        hlhkw__bmo = cgutils.alloca_once_value(builder, lir.Constant(lir.
            IntType(32), mvjkv__hho))
        dizka__xujg = lir.FunctionType(lir.IntType(8).as_pointer(), [lir.
            IntType(64), lir.IntType(32)])
        gpnkh__rvh = cgutils.get_or_insert_function(builder.module,
            dizka__xujg, name='alloc_numpy')
        return builder.call(gpnkh__rvh, [knpz__uginh, builder.load(hlhkw__bmo)]
            )
    return array_info_type(len_typ, arr_type), codegen


@intrinsic
def test_alloc_string(typingctx, len_typ, n_chars_typ):

    def codegen(context, builder, sig, args):
        knpz__uginh, rvb__boc = args
        dizka__xujg = lir.FunctionType(lir.IntType(8).as_pointer(), [lir.
            IntType(64), lir.IntType(64)])
        gpnkh__rvh = cgutils.get_or_insert_function(builder.module,
            dizka__xujg, name='alloc_string_array')
        return builder.call(gpnkh__rvh, [knpz__uginh, rvb__boc])
    return array_info_type(len_typ, n_chars_typ), codegen


@intrinsic
def arr_info_list_to_table(typingctx, list_arr_info_typ=None):
    assert list_arr_info_typ == types.List(array_info_type)
    return table_type(list_arr_info_typ), arr_info_list_to_table_codegen


def arr_info_list_to_table_codegen(context, builder, sig, args):
    asn__lst, = args
    wnzin__iao = numba.cpython.listobj.ListInstance(context, builder, sig.
        args[0], asn__lst)
    dizka__xujg = lir.FunctionType(lir.IntType(8).as_pointer(), [lir.
        IntType(8).as_pointer().as_pointer(), lir.IntType(64)])
    gpnkh__rvh = cgutils.get_or_insert_function(builder.module, dizka__xujg,
        name='arr_info_list_to_table')
    return builder.call(gpnkh__rvh, [wnzin__iao.data, wnzin__iao.size])


@intrinsic
def info_from_table(typingctx, table_t, ind_t):

    def codegen(context, builder, sig, args):
        dizka__xujg = lir.FunctionType(lir.IntType(8).as_pointer(), [lir.
            IntType(8).as_pointer(), lir.IntType(64)])
        gpnkh__rvh = cgutils.get_or_insert_function(builder.module,
            dizka__xujg, name='info_from_table')
        return builder.call(gpnkh__rvh, args)
    return array_info_type(table_t, ind_t), codegen


@intrinsic
def cpp_table_to_py_table(typingctx, cpp_table_t, table_idx_arr_t,
    py_table_type_t):
    assert cpp_table_t == table_type, 'invalid cpp table type'
    assert isinstance(table_idx_arr_t, types.Array
        ) and table_idx_arr_t.dtype == types.int64, 'invalid table index array'
    assert isinstance(py_table_type_t, types.TypeRef), 'invalid py table ref'
    zodzj__jmz = py_table_type_t.instance_type

    def codegen(context, builder, sig, args):
        rdf__yqhrp, qxksq__urezj, lqck__fver = args
        dizka__xujg = lir.FunctionType(lir.IntType(8).as_pointer(), [lir.
            IntType(8).as_pointer(), lir.IntType(64)])
        gpnkh__rvh = cgutils.get_or_insert_function(builder.module,
            dizka__xujg, name='info_from_table')
        ejcde__sel = cgutils.create_struct_proxy(zodzj__jmz)(context, builder)
        ejcde__sel.parent = cgutils.get_null_value(ejcde__sel.parent.type)
        thd__dhv = context.make_array(table_idx_arr_t)(context, builder,
            qxksq__urezj)
        fyd__bzbso = context.get_constant(types.int64, -1)
        fhv__xqcu = context.get_constant(types.int64, 0)
        cphh__dnzq = cgutils.alloca_once_value(builder, fhv__xqcu)
        for t, vxs__lioe in zodzj__jmz.type_to_blk.items():
            dcrso__zvog = context.get_constant(types.int64, len(zodzj__jmz.
                block_to_arr_ind[vxs__lioe]))
            lqck__fver, ehhcz__mjsa = ListInstance.allocate_ex(context,
                builder, types.List(t), dcrso__zvog)
            ehhcz__mjsa.size = dcrso__zvog
            nlv__cull = context.make_constant_array(builder, types.Array(
                types.int64, 1, 'C'), np.array(zodzj__jmz.block_to_arr_ind[
                vxs__lioe], dtype=np.int64))
            zkz__wya = context.make_array(types.Array(types.int64, 1, 'C'))(
                context, builder, nlv__cull)
            with cgutils.for_range(builder, dcrso__zvog) as dnub__amf:
                nggy__svcap = dnub__amf.index
                ywae__ath = _getitem_array_single_int(context, builder,
                    types.int64, types.Array(types.int64, 1, 'C'), zkz__wya,
                    nggy__svcap)
                liyu__wjw = _getitem_array_single_int(context, builder,
                    types.int64, table_idx_arr_t, thd__dhv, ywae__ath)
                oaj__aftgh = builder.icmp_unsigned('!=', liyu__wjw, fyd__bzbso)
                with builder.if_else(oaj__aftgh) as (gpgex__pnz, kpd__lgiwf):
                    with gpgex__pnz:
                        ucljz__ecc = builder.call(gpnkh__rvh, [rdf__yqhrp,
                            liyu__wjw])
                        arr = context.compile_internal(builder, lambda info:
                            info_to_array(info, t), t(array_info_type), [
                            ucljz__ecc])
                        ehhcz__mjsa.inititem(nggy__svcap, arr, incref=False)
                        knpz__uginh = context.compile_internal(builder, lambda
                            arr: len(arr), types.int64(t), [arr])
                        builder.store(knpz__uginh, cphh__dnzq)
                    with kpd__lgiwf:
                        rfk__jwpu = context.get_constant_null(t)
                        ehhcz__mjsa.inititem(nggy__svcap, rfk__jwpu, incref
                            =False)
            setattr(ejcde__sel, f'block_{vxs__lioe}', ehhcz__mjsa.value)
        ejcde__sel.len = builder.load(cphh__dnzq)
        return ejcde__sel._getvalue()
    return zodzj__jmz(cpp_table_t, table_idx_arr_t, py_table_type_t), codegen


@intrinsic
def py_table_to_cpp_table(typingctx, py_table_t, py_table_type_t):
    assert isinstance(py_table_t, bodo.hiframes.table.TableType
        ), 'invalid py table type'
    assert isinstance(py_table_type_t, types.TypeRef), 'invalid py table ref'
    zodzj__jmz = py_table_type_t.instance_type

    def codegen(context, builder, sig, args):
        ykqbz__yqta, lqck__fver = args
        amhc__tpfo = cgutils.create_struct_proxy(zodzj__jmz)(context,
            builder, ykqbz__yqta)
        if zodzj__jmz.has_runtime_cols:
            nhpsc__zrexr = lir.Constant(lir.IntType(64), 0)
            for vxs__lioe, t in enumerate(zodzj__jmz.arr_types):
                tlor__augo = getattr(amhc__tpfo, f'block_{vxs__lioe}')
                ogxm__anvpp = ListInstance(context, builder, types.List(t),
                    tlor__augo)
                nhpsc__zrexr = builder.add(nhpsc__zrexr, ogxm__anvpp.size)
        else:
            nhpsc__zrexr = lir.Constant(lir.IntType(64), len(zodzj__jmz.
                arr_types))
        lqck__fver, vygvw__edgi = ListInstance.allocate_ex(context, builder,
            types.List(array_info_type), nhpsc__zrexr)
        vygvw__edgi.size = nhpsc__zrexr
        if zodzj__jmz.has_runtime_cols:
            gqneg__vbg = lir.Constant(lir.IntType(64), 0)
            for vxs__lioe, t in enumerate(zodzj__jmz.arr_types):
                tlor__augo = getattr(amhc__tpfo, f'block_{vxs__lioe}')
                ogxm__anvpp = ListInstance(context, builder, types.List(t),
                    tlor__augo)
                dcrso__zvog = ogxm__anvpp.size
                with cgutils.for_range(builder, dcrso__zvog) as dnub__amf:
                    nggy__svcap = dnub__amf.index
                    arr = ogxm__anvpp.getitem(nggy__svcap)
                    hjj__ckhzk = signature(array_info_type, t)
                    tkflq__nlg = arr,
                    gyg__kfukx = array_to_info_codegen(context, builder,
                        hjj__ckhzk, tkflq__nlg)
                    vygvw__edgi.inititem(builder.add(gqneg__vbg,
                        nggy__svcap), gyg__kfukx, incref=False)
                gqneg__vbg = builder.add(gqneg__vbg, dcrso__zvog)
        else:
            for t, vxs__lioe in zodzj__jmz.type_to_blk.items():
                dcrso__zvog = context.get_constant(types.int64, len(
                    zodzj__jmz.block_to_arr_ind[vxs__lioe]))
                tlor__augo = getattr(amhc__tpfo, f'block_{vxs__lioe}')
                ogxm__anvpp = ListInstance(context, builder, types.List(t),
                    tlor__augo)
                nlv__cull = context.make_constant_array(builder, types.
                    Array(types.int64, 1, 'C'), np.array(zodzj__jmz.
                    block_to_arr_ind[vxs__lioe], dtype=np.int64))
                zkz__wya = context.make_array(types.Array(types.int64, 1, 'C')
                    )(context, builder, nlv__cull)
                with cgutils.for_range(builder, dcrso__zvog) as dnub__amf:
                    nggy__svcap = dnub__amf.index
                    ywae__ath = _getitem_array_single_int(context, builder,
                        types.int64, types.Array(types.int64, 1, 'C'),
                        zkz__wya, nggy__svcap)
                    dta__zadwy = signature(types.none, zodzj__jmz, types.
                        List(t), types.int64, types.int64)
                    vgul__apwwz = (ykqbz__yqta, tlor__augo, nggy__svcap,
                        ywae__ath)
                    bodo.hiframes.table.ensure_column_unboxed_codegen(context,
                        builder, dta__zadwy, vgul__apwwz)
                    arr = ogxm__anvpp.getitem(nggy__svcap)
                    hjj__ckhzk = signature(array_info_type, t)
                    tkflq__nlg = arr,
                    gyg__kfukx = array_to_info_codegen(context, builder,
                        hjj__ckhzk, tkflq__nlg)
                    vygvw__edgi.inititem(ywae__ath, gyg__kfukx, incref=False)
        vcs__mvyfu = vygvw__edgi.value
        zlh__ojr = signature(table_type, types.List(array_info_type))
        jjv__ldhs = vcs__mvyfu,
        rdf__yqhrp = arr_info_list_to_table_codegen(context, builder,
            zlh__ojr, jjv__ldhs)
        context.nrt.decref(builder, types.List(array_info_type), vcs__mvyfu)
        return rdf__yqhrp
    return table_type(zodzj__jmz, py_table_type_t), codegen


delete_info_decref_array = types.ExternalFunction('delete_info_decref_array',
    types.void(array_info_type))
delete_table_decref_arrays = types.ExternalFunction(
    'delete_table_decref_arrays', types.void(table_type))


@intrinsic
def delete_table(typingctx, table_t=None):
    assert table_t == table_type

    def codegen(context, builder, sig, args):
        dizka__xujg = lir.FunctionType(lir.VoidType(), [lir.IntType(8).
            as_pointer()])
        gpnkh__rvh = cgutils.get_or_insert_function(builder.module,
            dizka__xujg, name='delete_table')
        builder.call(gpnkh__rvh, args)
    return types.void(table_t), codegen


@intrinsic
def shuffle_table(typingctx, table_t, n_keys_t, _is_parallel, keep_comm_info_t
    ):
    assert table_t == table_type

    def codegen(context, builder, sig, args):
        dizka__xujg = lir.FunctionType(lir.IntType(8).as_pointer(), [lir.
            IntType(8).as_pointer(), lir.IntType(64), lir.IntType(1), lir.
            IntType(32)])
        gpnkh__rvh = cgutils.get_or_insert_function(builder.module,
            dizka__xujg, name='shuffle_table')
        lbv__nifgg = builder.call(gpnkh__rvh, args)
        context.compile_internal(builder, lambda :
            check_and_propagate_cpp_exception(), types.none(), [])
        return lbv__nifgg
    return table_type(table_t, types.int64, types.boolean, types.int32
        ), codegen


class ShuffleInfoType(types.Type):

    def __init__(self):
        super(ShuffleInfoType, self).__init__(name='ShuffleInfoType()')


shuffle_info_type = ShuffleInfoType()
register_model(ShuffleInfoType)(models.OpaqueModel)
get_shuffle_info = types.ExternalFunction('get_shuffle_info',
    shuffle_info_type(table_type))


@intrinsic
def delete_shuffle_info(typingctx, shuffle_info_t=None):

    def codegen(context, builder, sig, args):
        if sig.args[0] == types.none:
            return
        dizka__xujg = lir.FunctionType(lir.VoidType(), [lir.IntType(8).
            as_pointer()])
        gpnkh__rvh = cgutils.get_or_insert_function(builder.module,
            dizka__xujg, name='delete_shuffle_info')
        return builder.call(gpnkh__rvh, args)
    return types.void(shuffle_info_t), codegen


@intrinsic
def reverse_shuffle_table(typingctx, table_t, shuffle_info_t=None):

    def codegen(context, builder, sig, args):
        if sig.args[-1] == types.none:
            return context.get_constant_null(table_type)
        dizka__xujg = lir.FunctionType(lir.IntType(8).as_pointer(), [lir.
            IntType(8).as_pointer(), lir.IntType(8).as_pointer()])
        gpnkh__rvh = cgutils.get_or_insert_function(builder.module,
            dizka__xujg, name='reverse_shuffle_table')
        return builder.call(gpnkh__rvh, args)
    return table_type(table_type, shuffle_info_t), codegen


@intrinsic
def get_null_shuffle_info(typingctx):

    def codegen(context, builder, sig, args):
        return context.get_constant_null(sig.return_type)
    return shuffle_info_type(), codegen


@intrinsic
def hash_join_table(typingctx, left_table_t, right_table_t, left_parallel_t,
    right_parallel_t, n_keys_t, n_data_left_t, n_data_right_t, same_vect_t,
    same_need_typechange_t, is_left_t, is_right_t, is_join_t,
    optional_col_t, indicator, _bodo_na_equal, cond_func, left_col_nums,
    left_col_nums_len, right_col_nums, right_col_nums_len):
    assert left_table_t == table_type
    assert right_table_t == table_type

    def codegen(context, builder, sig, args):
        dizka__xujg = lir.FunctionType(lir.IntType(8).as_pointer(), [lir.
            IntType(8).as_pointer(), lir.IntType(8).as_pointer(), lir.
            IntType(1), lir.IntType(1), lir.IntType(64), lir.IntType(64),
            lir.IntType(64), lir.IntType(8).as_pointer(), lir.IntType(8).
            as_pointer(), lir.IntType(1), lir.IntType(1), lir.IntType(1),
            lir.IntType(1), lir.IntType(1), lir.IntType(1), lir.IntType(8).
            as_pointer(), lir.IntType(8).as_pointer(), lir.IntType(64), lir
            .IntType(8).as_pointer(), lir.IntType(64)])
        gpnkh__rvh = cgutils.get_or_insert_function(builder.module,
            dizka__xujg, name='hash_join_table')
        lbv__nifgg = builder.call(gpnkh__rvh, args)
        context.compile_internal(builder, lambda :
            check_and_propagate_cpp_exception(), types.none(), [])
        return lbv__nifgg
    return table_type(left_table_t, right_table_t, types.boolean, types.
        boolean, types.int64, types.int64, types.int64, types.voidptr,
        types.voidptr, types.boolean, types.boolean, types.boolean, types.
        boolean, types.boolean, types.boolean, types.voidptr, types.voidptr,
        types.int64, types.voidptr, types.int64), codegen


@intrinsic
def sort_values_table(typingctx, table_t, n_keys_t, vect_ascending_t,
    na_position_b_t, parallel_t):
    assert table_t == table_type

    def codegen(context, builder, sig, args):
        dizka__xujg = lir.FunctionType(lir.IntType(8).as_pointer(), [lir.
            IntType(8).as_pointer(), lir.IntType(64), lir.IntType(8).
            as_pointer(), lir.IntType(8).as_pointer(), lir.IntType(1)])
        gpnkh__rvh = cgutils.get_or_insert_function(builder.module,
            dizka__xujg, name='sort_values_table')
        lbv__nifgg = builder.call(gpnkh__rvh, args)
        context.compile_internal(builder, lambda :
            check_and_propagate_cpp_exception(), types.none(), [])
        return lbv__nifgg
    return table_type(table_t, types.int64, types.voidptr, types.voidptr,
        types.boolean), codegen


@intrinsic
def sample_table(typingctx, table_t, n_keys_t, frac_t, replace_t, parallel_t):
    assert table_t == table_type

    def codegen(context, builder, sig, args):
        dizka__xujg = lir.FunctionType(lir.IntType(8).as_pointer(), [lir.
            IntType(8).as_pointer(), lir.IntType(64), lir.DoubleType(), lir
            .IntType(1), lir.IntType(1)])
        gpnkh__rvh = cgutils.get_or_insert_function(builder.module,
            dizka__xujg, name='sample_table')
        lbv__nifgg = builder.call(gpnkh__rvh, args)
        context.compile_internal(builder, lambda :
            check_and_propagate_cpp_exception(), types.none(), [])
        return lbv__nifgg
    return table_type(table_t, types.int64, types.float64, types.boolean,
        types.boolean), codegen


@intrinsic
def shuffle_renormalization(typingctx, table_t, random_t, random_seed_t,
    is_parallel_t):
    assert table_t == table_type

    def codegen(context, builder, sig, args):
        dizka__xujg = lir.FunctionType(lir.IntType(8).as_pointer(), [lir.
            IntType(8).as_pointer(), lir.IntType(32), lir.IntType(64), lir.
            IntType(1)])
        gpnkh__rvh = cgutils.get_or_insert_function(builder.module,
            dizka__xujg, name='shuffle_renormalization')
        lbv__nifgg = builder.call(gpnkh__rvh, args)
        context.compile_internal(builder, lambda :
            check_and_propagate_cpp_exception(), types.none(), [])
        return lbv__nifgg
    return table_type(table_t, types.int32, types.int64, types.boolean
        ), codegen


@intrinsic
def shuffle_renormalization_group(typingctx, table_t, random_t,
    random_seed_t, is_parallel_t, num_ranks_t, ranks_t):
    assert table_t == table_type

    def codegen(context, builder, sig, args):
        dizka__xujg = lir.FunctionType(lir.IntType(8).as_pointer(), [lir.
            IntType(8).as_pointer(), lir.IntType(32), lir.IntType(64), lir.
            IntType(1), lir.IntType(64), lir.IntType(8).as_pointer()])
        gpnkh__rvh = cgutils.get_or_insert_function(builder.module,
            dizka__xujg, name='shuffle_renormalization_group')
        lbv__nifgg = builder.call(gpnkh__rvh, args)
        context.compile_internal(builder, lambda :
            check_and_propagate_cpp_exception(), types.none(), [])
        return lbv__nifgg
    return table_type(table_t, types.int32, types.int64, types.boolean,
        types.int64, types.voidptr), codegen


@intrinsic
def drop_duplicates_table(typingctx, table_t, parallel_t, nkey_t, keep_t,
    dropna, drop_local_first):
    assert table_t == table_type

    def codegen(context, builder, sig, args):
        dizka__xujg = lir.FunctionType(lir.IntType(8).as_pointer(), [lir.
            IntType(8).as_pointer(), lir.IntType(1), lir.IntType(64), lir.
            IntType(64), lir.IntType(1), lir.IntType(1)])
        gpnkh__rvh = cgutils.get_or_insert_function(builder.module,
            dizka__xujg, name='drop_duplicates_table')
        lbv__nifgg = builder.call(gpnkh__rvh, args)
        context.compile_internal(builder, lambda :
            check_and_propagate_cpp_exception(), types.none(), [])
        return lbv__nifgg
    return table_type(table_t, types.boolean, types.int64, types.int64,
        types.boolean, types.boolean), codegen


@intrinsic
def pivot_groupby_and_aggregate(typingctx, table_t, n_keys_t,
    dispatch_table_t, dispatch_info_t, input_has_index, ftypes,
    func_offsets, udf_n_redvars, is_parallel, is_crosstab, skipdropna_t,
    return_keys, return_index, update_cb, combine_cb, eval_cb,
    udf_table_dummy_t):
    assert table_t == table_type
    assert dispatch_table_t == table_type
    assert dispatch_info_t == table_type
    assert udf_table_dummy_t == table_type

    def codegen(context, builder, sig, args):
        dizka__xujg = lir.FunctionType(lir.IntType(8).as_pointer(), [lir.
            IntType(8).as_pointer(), lir.IntType(64), lir.IntType(8).
            as_pointer(), lir.IntType(8).as_pointer(), lir.IntType(1), lir.
            IntType(8).as_pointer(), lir.IntType(8).as_pointer(), lir.
            IntType(8).as_pointer(), lir.IntType(1), lir.IntType(1), lir.
            IntType(1), lir.IntType(1), lir.IntType(1), lir.IntType(8).
            as_pointer(), lir.IntType(8).as_pointer(), lir.IntType(8).
            as_pointer(), lir.IntType(8).as_pointer()])
        gpnkh__rvh = cgutils.get_or_insert_function(builder.module,
            dizka__xujg, name='pivot_groupby_and_aggregate')
        lbv__nifgg = builder.call(gpnkh__rvh, args)
        context.compile_internal(builder, lambda :
            check_and_propagate_cpp_exception(), types.none(), [])
        return lbv__nifgg
    return table_type(table_t, types.int64, table_t, table_t, types.boolean,
        types.voidptr, types.voidptr, types.voidptr, types.boolean, types.
        boolean, types.boolean, types.boolean, types.boolean, types.voidptr,
        types.voidptr, types.voidptr, table_t), codegen


@intrinsic
def groupby_and_aggregate(typingctx, table_t, n_keys_t, input_has_index,
    ftypes, func_offsets, udf_n_redvars, is_parallel, skipdropna_t,
    shift_periods_t, transform_func, head_n, return_keys, return_index,
    dropna, update_cb, combine_cb, eval_cb, general_udfs_cb, udf_table_dummy_t
    ):
    assert table_t == table_type
    assert udf_table_dummy_t == table_type

    def codegen(context, builder, sig, args):
        dizka__xujg = lir.FunctionType(lir.IntType(8).as_pointer(), [lir.
            IntType(8).as_pointer(), lir.IntType(64), lir.IntType(1), lir.
            IntType(8).as_pointer(), lir.IntType(8).as_pointer(), lir.
            IntType(8).as_pointer(), lir.IntType(1), lir.IntType(1), lir.
            IntType(64), lir.IntType(64), lir.IntType(64), lir.IntType(1),
            lir.IntType(1), lir.IntType(1), lir.IntType(8).as_pointer(),
            lir.IntType(8).as_pointer(), lir.IntType(8).as_pointer(), lir.
            IntType(8).as_pointer(), lir.IntType(8).as_pointer()])
        gpnkh__rvh = cgutils.get_or_insert_function(builder.module,
            dizka__xujg, name='groupby_and_aggregate')
        lbv__nifgg = builder.call(gpnkh__rvh, args)
        context.compile_internal(builder, lambda :
            check_and_propagate_cpp_exception(), types.none(), [])
        return lbv__nifgg
    return table_type(table_t, types.int64, types.boolean, types.voidptr,
        types.voidptr, types.voidptr, types.boolean, types.boolean, types.
        int64, types.int64, types.int64, types.boolean, types.boolean,
        types.boolean, types.voidptr, types.voidptr, types.voidptr, types.
        voidptr, table_t), codegen


get_groupby_labels = types.ExternalFunction('get_groupby_labels', types.
    int64(table_type, types.voidptr, types.voidptr, types.boolean, types.bool_)
    )
_array_isin = types.ExternalFunction('array_isin', types.void(
    array_info_type, array_info_type, array_info_type, types.bool_))


@numba.njit(no_cpython_wrapper=True)
def array_isin(out_arr, in_arr, in_values, is_parallel):
    in_arr = decode_if_dict_array(in_arr)
    in_values = decode_if_dict_array(in_values)
    btuy__iit = array_to_info(in_arr)
    yxbok__bzj = array_to_info(in_values)
    flmx__xsgmp = array_to_info(out_arr)
    qarvn__wrqg = arr_info_list_to_table([btuy__iit, yxbok__bzj, flmx__xsgmp])
    _array_isin(flmx__xsgmp, btuy__iit, yxbok__bzj, is_parallel)
    check_and_propagate_cpp_exception()
    delete_table(qarvn__wrqg)


_get_search_regex = types.ExternalFunction('get_search_regex', types.void(
    array_info_type, types.bool_, types.voidptr, array_info_type))


@numba.njit(no_cpython_wrapper=True)
def get_search_regex(in_arr, case, pat, out_arr):
    in_arr = decode_if_dict_array(in_arr)
    btuy__iit = array_to_info(in_arr)
    flmx__xsgmp = array_to_info(out_arr)
    _get_search_regex(btuy__iit, case, pat, flmx__xsgmp)
    check_and_propagate_cpp_exception()


def _gen_row_access_intrinsic(col_array_typ, c_ind):
    from llvmlite import ir as lir
    dgwve__oecik = col_array_typ.dtype
    if isinstance(dgwve__oecik, types.Number) or dgwve__oecik in [bodo.
        datetime_date_type, bodo.datetime64ns, bodo.timedelta64ns, types.bool_
        ]:

        @intrinsic
        def getitem_func(typingctx, table_t, ind_t):

            def codegen(context, builder, sig, args):
                ejcde__sel, bqmv__vstwi = args
                ejcde__sel = builder.bitcast(ejcde__sel, lir.IntType(8).
                    as_pointer().as_pointer())
                rblps__spg = lir.Constant(lir.IntType(64), c_ind)
                iyq__etagk = builder.load(builder.gep(ejcde__sel, [rblps__spg])
                    )
                iyq__etagk = builder.bitcast(iyq__etagk, context.
                    get_data_type(dgwve__oecik).as_pointer())
                return builder.load(builder.gep(iyq__etagk, [bqmv__vstwi]))
            return dgwve__oecik(types.voidptr, types.int64), codegen
        return getitem_func
    if col_array_typ == bodo.string_array_type:

        @intrinsic
        def getitem_func(typingctx, table_t, ind_t):

            def codegen(context, builder, sig, args):
                ejcde__sel, bqmv__vstwi = args
                ejcde__sel = builder.bitcast(ejcde__sel, lir.IntType(8).
                    as_pointer().as_pointer())
                rblps__spg = lir.Constant(lir.IntType(64), c_ind)
                iyq__etagk = builder.load(builder.gep(ejcde__sel, [rblps__spg])
                    )
                dizka__xujg = lir.FunctionType(lir.IntType(8).as_pointer(),
                    [lir.IntType(8).as_pointer(), lir.IntType(64), lir.
                    IntType(64).as_pointer()])
                abl__cizb = cgutils.get_or_insert_function(builder.module,
                    dizka__xujg, name='array_info_getitem')
                wrzu__tlbl = cgutils.alloca_once(builder, lir.IntType(64))
                args = iyq__etagk, bqmv__vstwi, wrzu__tlbl
                cltii__iuj = builder.call(abl__cizb, args)
                return context.make_tuple(builder, sig.return_type, [
                    cltii__iuj, builder.load(wrzu__tlbl)])
            return types.Tuple([types.voidptr, types.int64])(types.voidptr,
                types.int64), codegen
        return getitem_func
    if col_array_typ == bodo.libs.dict_arr_ext.dict_str_arr_type:

        @intrinsic
        def getitem_func(typingctx, table_t, ind_t):

            def codegen(context, builder, sig, args):
                kpn__tzam = lir.Constant(lir.IntType(64), 1)
                hxxc__vsk = lir.Constant(lir.IntType(64), 2)
                ejcde__sel, bqmv__vstwi = args
                ejcde__sel = builder.bitcast(ejcde__sel, lir.IntType(8).
                    as_pointer().as_pointer())
                rblps__spg = lir.Constant(lir.IntType(64), c_ind)
                iyq__etagk = builder.load(builder.gep(ejcde__sel, [rblps__spg])
                    )
                dizka__xujg = lir.FunctionType(lir.IntType(8).as_pointer(),
                    [lir.IntType(8).as_pointer(), lir.IntType(64)])
                obasb__kdpjy = cgutils.get_or_insert_function(builder.
                    module, dizka__xujg, name='get_nested_info')
                args = iyq__etagk, hxxc__vsk
                qxsm__bxbh = builder.call(obasb__kdpjy, args)
                dizka__xujg = lir.FunctionType(lir.IntType(8).as_pointer(),
                    [lir.IntType(8).as_pointer()])
                zyf__emqo = cgutils.get_or_insert_function(builder.module,
                    dizka__xujg, name='array_info_getdata1')
                args = qxsm__bxbh,
                plx__vrt = builder.call(zyf__emqo, args)
                plx__vrt = builder.bitcast(plx__vrt, context.get_data_type(
                    col_array_typ.indices_dtype).as_pointer())
                ngl__amylt = builder.sext(builder.load(builder.gep(plx__vrt,
                    [bqmv__vstwi])), lir.IntType(64))
                args = iyq__etagk, kpn__tzam
                ihyhx__oysjg = builder.call(obasb__kdpjy, args)
                dizka__xujg = lir.FunctionType(lir.IntType(8).as_pointer(),
                    [lir.IntType(8).as_pointer(), lir.IntType(64), lir.
                    IntType(64).as_pointer()])
                abl__cizb = cgutils.get_or_insert_function(builder.module,
                    dizka__xujg, name='array_info_getitem')
                wrzu__tlbl = cgutils.alloca_once(builder, lir.IntType(64))
                args = ihyhx__oysjg, ngl__amylt, wrzu__tlbl
                cltii__iuj = builder.call(abl__cizb, args)
                return context.make_tuple(builder, sig.return_type, [
                    cltii__iuj, builder.load(wrzu__tlbl)])
            return types.Tuple([types.voidptr, types.int64])(types.voidptr,
                types.int64), codegen
        return getitem_func
    raise BodoError(
        f"General Join Conditions with '{dgwve__oecik}' column data type not supported"
        )


def _gen_row_na_check_intrinsic(col_array_dtype, c_ind):
    if (isinstance(col_array_dtype, bodo.libs.int_arr_ext.IntegerArrayType) or
        col_array_dtype == bodo.libs.bool_arr_ext.boolean_array or
        is_str_arr_type(col_array_dtype) or isinstance(col_array_dtype,
        types.Array) and col_array_dtype.dtype == bodo.datetime_date_type):

        @intrinsic
        def checkna_func(typingctx, table_t, ind_t):

            def codegen(context, builder, sig, args):
                kuep__vosgb, bqmv__vstwi = args
                kuep__vosgb = builder.bitcast(kuep__vosgb, lir.IntType(8).
                    as_pointer().as_pointer())
                rblps__spg = lir.Constant(lir.IntType(64), c_ind)
                iyq__etagk = builder.load(builder.gep(kuep__vosgb, [
                    rblps__spg]))
                zuxp__nqk = builder.bitcast(iyq__etagk, context.
                    get_data_type(types.bool_).as_pointer())
                lxro__hpn = bodo.utils.cg_helpers.get_bitmap_bit(builder,
                    zuxp__nqk, bqmv__vstwi)
                oou__iah = builder.icmp_unsigned('!=', lxro__hpn, lir.
                    Constant(lir.IntType(8), 0))
                return builder.sext(oou__iah, lir.IntType(8))
            return types.int8(types.voidptr, types.int64), codegen
        return checkna_func
    elif isinstance(col_array_dtype, types.Array):
        dgwve__oecik = col_array_dtype.dtype
        if dgwve__oecik in [bodo.datetime64ns, bodo.timedelta64ns]:

            @intrinsic
            def checkna_func(typingctx, table_t, ind_t):

                def codegen(context, builder, sig, args):
                    ejcde__sel, bqmv__vstwi = args
                    ejcde__sel = builder.bitcast(ejcde__sel, lir.IntType(8)
                        .as_pointer().as_pointer())
                    rblps__spg = lir.Constant(lir.IntType(64), c_ind)
                    iyq__etagk = builder.load(builder.gep(ejcde__sel, [
                        rblps__spg]))
                    iyq__etagk = builder.bitcast(iyq__etagk, context.
                        get_data_type(dgwve__oecik).as_pointer())
                    zgb__ixnx = builder.load(builder.gep(iyq__etagk, [
                        bqmv__vstwi]))
                    oou__iah = builder.icmp_unsigned('!=', zgb__ixnx, lir.
                        Constant(lir.IntType(64), pd._libs.iNaT))
                    return builder.sext(oou__iah, lir.IntType(8))
                return types.int8(types.voidptr, types.int64), codegen
            return checkna_func
        elif isinstance(dgwve__oecik, types.Float):

            @intrinsic
            def checkna_func(typingctx, table_t, ind_t):

                def codegen(context, builder, sig, args):
                    ejcde__sel, bqmv__vstwi = args
                    ejcde__sel = builder.bitcast(ejcde__sel, lir.IntType(8)
                        .as_pointer().as_pointer())
                    rblps__spg = lir.Constant(lir.IntType(64), c_ind)
                    iyq__etagk = builder.load(builder.gep(ejcde__sel, [
                        rblps__spg]))
                    iyq__etagk = builder.bitcast(iyq__etagk, context.
                        get_data_type(dgwve__oecik).as_pointer())
                    zgb__ixnx = builder.load(builder.gep(iyq__etagk, [
                        bqmv__vstwi]))
                    oagfh__jxfa = signature(types.bool_, dgwve__oecik)
                    lxro__hpn = numba.np.npyfuncs.np_real_isnan_impl(context,
                        builder, oagfh__jxfa, (zgb__ixnx,))
                    return builder.not_(builder.sext(lxro__hpn, lir.IntType(8))
                        )
                return types.int8(types.voidptr, types.int64), codegen
            return checkna_func
    raise BodoError(
        f"General Join Conditions with '{col_array_dtype}' column type not supported"
        )
