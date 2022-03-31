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
        gkk__ahaps = context.make_helper(builder, arr_type, in_arr)
        in_arr = gkk__ahaps.data
        arr_type = StructArrayType(arr_type.data, ('dummy',) * len(arr_type
            .data))
    if isinstance(arr_type, ArrayItemArrayType
        ) and arr_type.dtype == string_array_type:
        tbwj__dcs = context.make_helper(builder, arr_type, in_arr)
        ilujb__hctfe = lir.FunctionType(lir.IntType(8).as_pointer(), [lir.
            IntType(8).as_pointer()])
        wtiqd__rusv = cgutils.get_or_insert_function(builder.module,
            ilujb__hctfe, name='list_string_array_to_info')
        return builder.call(wtiqd__rusv, [tbwj__dcs.meminfo])
    if isinstance(arr_type, (MapArrayType, ArrayItemArrayType, StructArrayType)
        ):

        def get_types(arr_typ):
            if isinstance(arr_typ, MapArrayType):
                return get_types(_get_map_arr_data_type(arr_typ))
            elif isinstance(arr_typ, ArrayItemArrayType):
                return [CTypeEnum.LIST.value] + get_types(arr_typ.dtype)
            elif isinstance(arr_typ, (StructType, StructArrayType)):
                qbg__kvefi = [CTypeEnum.STRUCT.value, len(arr_typ.names)]
                for nddv__gdeyw in arr_typ.data:
                    qbg__kvefi += get_types(nddv__gdeyw)
                return qbg__kvefi
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
            msrws__chfl = context.compile_internal(builder, lambda a: len(a
                ), types.intp(arr_typ), [arr])
            if isinstance(arr_typ, MapArrayType):
                lsfsd__tmq = context.make_helper(builder, arr_typ, value=arr)
                axe__ynaj = get_lengths(_get_map_arr_data_type(arr_typ),
                    lsfsd__tmq.data)
            elif isinstance(arr_typ, ArrayItemArrayType):
                tcor__jeylo = _get_array_item_arr_payload(context, builder,
                    arr_typ, arr)
                axe__ynaj = get_lengths(arr_typ.dtype, tcor__jeylo.data)
                axe__ynaj = cgutils.pack_array(builder, [tcor__jeylo.
                    n_arrays] + [builder.extract_value(axe__ynaj,
                    okik__drlr) for okik__drlr in range(axe__ynaj.type.count)])
            elif isinstance(arr_typ, StructArrayType):
                tcor__jeylo = _get_struct_arr_payload(context, builder,
                    arr_typ, arr)
                axe__ynaj = []
                for okik__drlr, nddv__gdeyw in enumerate(arr_typ.data):
                    wjbnp__xsnc = get_lengths(nddv__gdeyw, builder.
                        extract_value(tcor__jeylo.data, okik__drlr))
                    axe__ynaj += [builder.extract_value(wjbnp__xsnc,
                        wsdo__xilxp) for wsdo__xilxp in range(wjbnp__xsnc.
                        type.count)]
                axe__ynaj = cgutils.pack_array(builder, [msrws__chfl,
                    context.get_constant(types.int64, -1)] + axe__ynaj)
            elif isinstance(arr_typ, (IntegerArrayType, DecimalArrayType,
                types.Array)) or arr_typ in (boolean_array,
                datetime_date_array_type, string_array_type, binary_array_type
                ):
                axe__ynaj = cgutils.pack_array(builder, [msrws__chfl])
            else:
                raise BodoError(
                    f'array_to_info: unsupported type for subarray {arr_typ}')
            return axe__ynaj

        def get_buffers(arr_typ, arr):
            if isinstance(arr_typ, MapArrayType):
                lsfsd__tmq = context.make_helper(builder, arr_typ, value=arr)
                ies__wmtiu = get_buffers(_get_map_arr_data_type(arr_typ),
                    lsfsd__tmq.data)
            elif isinstance(arr_typ, ArrayItemArrayType):
                tcor__jeylo = _get_array_item_arr_payload(context, builder,
                    arr_typ, arr)
                kxr__swqh = get_buffers(arr_typ.dtype, tcor__jeylo.data)
                rhe__fggid = context.make_array(types.Array(offset_type, 1,
                    'C'))(context, builder, tcor__jeylo.offsets)
                amspm__hjwv = builder.bitcast(rhe__fggid.data, lir.IntType(
                    8).as_pointer())
                ewxkf__nrry = context.make_array(types.Array(types.uint8, 1,
                    'C'))(context, builder, tcor__jeylo.null_bitmap)
                qauet__qjwc = builder.bitcast(ewxkf__nrry.data, lir.IntType
                    (8).as_pointer())
                ies__wmtiu = cgutils.pack_array(builder, [amspm__hjwv,
                    qauet__qjwc] + [builder.extract_value(kxr__swqh,
                    okik__drlr) for okik__drlr in range(kxr__swqh.type.count)])
            elif isinstance(arr_typ, StructArrayType):
                tcor__jeylo = _get_struct_arr_payload(context, builder,
                    arr_typ, arr)
                kxr__swqh = []
                for okik__drlr, nddv__gdeyw in enumerate(arr_typ.data):
                    twhzx__wesy = get_buffers(nddv__gdeyw, builder.
                        extract_value(tcor__jeylo.data, okik__drlr))
                    kxr__swqh += [builder.extract_value(twhzx__wesy,
                        wsdo__xilxp) for wsdo__xilxp in range(twhzx__wesy.
                        type.count)]
                ewxkf__nrry = context.make_array(types.Array(types.uint8, 1,
                    'C'))(context, builder, tcor__jeylo.null_bitmap)
                qauet__qjwc = builder.bitcast(ewxkf__nrry.data, lir.IntType
                    (8).as_pointer())
                ies__wmtiu = cgutils.pack_array(builder, [qauet__qjwc] +
                    kxr__swqh)
            elif isinstance(arr_typ, (IntegerArrayType, DecimalArrayType)
                ) or arr_typ in (boolean_array, datetime_date_array_type):
                exlia__rxgg = arr_typ.dtype
                if isinstance(arr_typ, DecimalArrayType):
                    exlia__rxgg = int128_type
                elif arr_typ == datetime_date_array_type:
                    exlia__rxgg = types.int64
                arr = cgutils.create_struct_proxy(arr_typ)(context, builder,
                    arr)
                kaha__kkd = context.make_array(types.Array(exlia__rxgg, 1, 'C')
                    )(context, builder, arr.data)
                ewxkf__nrry = context.make_array(types.Array(types.uint8, 1,
                    'C'))(context, builder, arr.null_bitmap)
                ijevb__qimyn = builder.bitcast(kaha__kkd.data, lir.IntType(
                    8).as_pointer())
                qauet__qjwc = builder.bitcast(ewxkf__nrry.data, lir.IntType
                    (8).as_pointer())
                ies__wmtiu = cgutils.pack_array(builder, [qauet__qjwc,
                    ijevb__qimyn])
            elif arr_typ in (string_array_type, binary_array_type):
                tcor__jeylo = _get_str_binary_arr_payload(context, builder,
                    arr, arr_typ)
                rlpfp__madk = context.make_helper(builder, offset_arr_type,
                    tcor__jeylo.offsets).data
                xeqd__wsgs = context.make_helper(builder, char_arr_type,
                    tcor__jeylo.data).data
                zjue__vmkl = context.make_helper(builder,
                    null_bitmap_arr_type, tcor__jeylo.null_bitmap).data
                ies__wmtiu = cgutils.pack_array(builder, [builder.bitcast(
                    rlpfp__madk, lir.IntType(8).as_pointer()), builder.
                    bitcast(zjue__vmkl, lir.IntType(8).as_pointer()),
                    builder.bitcast(xeqd__wsgs, lir.IntType(8).as_pointer())])
            elif isinstance(arr_typ, types.Array):
                arr = context.make_array(arr_typ)(context, builder, arr)
                ijevb__qimyn = builder.bitcast(arr.data, lir.IntType(8).
                    as_pointer())
                vrxr__dtne = lir.Constant(lir.IntType(8).as_pointer(), None)
                ies__wmtiu = cgutils.pack_array(builder, [vrxr__dtne,
                    ijevb__qimyn])
            else:
                raise RuntimeError(
                    'array_to_info: unsupported type for subarray ' + str(
                    arr_typ))
            return ies__wmtiu

        def get_field_names(arr_typ):
            bfcbf__jasj = []
            if isinstance(arr_typ, StructArrayType):
                for klyqe__vkzsr, nesm__cgu in zip(arr_typ.dtype.names,
                    arr_typ.data):
                    bfcbf__jasj.append(klyqe__vkzsr)
                    bfcbf__jasj += get_field_names(nesm__cgu)
            elif isinstance(arr_typ, ArrayItemArrayType):
                bfcbf__jasj += get_field_names(arr_typ.dtype)
            elif isinstance(arr_typ, MapArrayType):
                bfcbf__jasj += get_field_names(_get_map_arr_data_type(arr_typ))
            return bfcbf__jasj
        qbg__kvefi = get_types(arr_type)
        zpdtd__jhm = cgutils.pack_array(builder, [context.get_constant(
            types.int32, t) for t in qbg__kvefi])
        uxeyi__bshk = cgutils.alloca_once_value(builder, zpdtd__jhm)
        axe__ynaj = get_lengths(arr_type, in_arr)
        lengths_ptr = cgutils.alloca_once_value(builder, axe__ynaj)
        ies__wmtiu = get_buffers(arr_type, in_arr)
        mgbzh__nczo = cgutils.alloca_once_value(builder, ies__wmtiu)
        bfcbf__jasj = get_field_names(arr_type)
        if len(bfcbf__jasj) == 0:
            bfcbf__jasj = ['irrelevant']
        myl__kxrd = cgutils.pack_array(builder, [context.
            insert_const_string(builder.module, a) for a in bfcbf__jasj])
        gfsdk__pdpt = cgutils.alloca_once_value(builder, myl__kxrd)
        if isinstance(arr_type, MapArrayType):
            fabhh__zgjk = _get_map_arr_data_type(arr_type)
            oxyrz__wgtfv = context.make_helper(builder, arr_type, value=in_arr)
            gps__mweqv = oxyrz__wgtfv.data
        else:
            fabhh__zgjk = arr_type
            gps__mweqv = in_arr
        qpl__rsdk = context.make_helper(builder, fabhh__zgjk, gps__mweqv)
        ilujb__hctfe = lir.FunctionType(lir.IntType(8).as_pointer(), [lir.
            IntType(32).as_pointer(), lir.IntType(8).as_pointer().
            as_pointer(), lir.IntType(64).as_pointer(), lir.IntType(8).
            as_pointer(), lir.IntType(8).as_pointer()])
        wtiqd__rusv = cgutils.get_or_insert_function(builder.module,
            ilujb__hctfe, name='nested_array_to_info')
        nhe__say = builder.call(wtiqd__rusv, [builder.bitcast(uxeyi__bshk,
            lir.IntType(32).as_pointer()), builder.bitcast(mgbzh__nczo, lir
            .IntType(8).as_pointer().as_pointer()), builder.bitcast(
            lengths_ptr, lir.IntType(64).as_pointer()), builder.bitcast(
            gfsdk__pdpt, lir.IntType(8).as_pointer()), qpl__rsdk.meminfo])
        context.compile_internal(builder, lambda :
            check_and_propagate_cpp_exception(), types.none(), [])
        return nhe__say
    if arr_type in (string_array_type, binary_array_type):
        yqmq__nxmz = context.make_helper(builder, arr_type, in_arr)
        rqd__epf = ArrayItemArrayType(char_arr_type)
        tbwj__dcs = context.make_helper(builder, rqd__epf, yqmq__nxmz.data)
        tcor__jeylo = _get_str_binary_arr_payload(context, builder, in_arr,
            arr_type)
        rlpfp__madk = context.make_helper(builder, offset_arr_type,
            tcor__jeylo.offsets).data
        xeqd__wsgs = context.make_helper(builder, char_arr_type,
            tcor__jeylo.data).data
        zjue__vmkl = context.make_helper(builder, null_bitmap_arr_type,
            tcor__jeylo.null_bitmap).data
        jsrqr__jnh = builder.zext(builder.load(builder.gep(rlpfp__madk, [
            tcor__jeylo.n_arrays])), lir.IntType(64))
        daftr__pdv = context.get_constant(types.int32, int(arr_type ==
            binary_array_type))
        ilujb__hctfe = lir.FunctionType(lir.IntType(8).as_pointer(), [lir.
            IntType(64), lir.IntType(64), lir.IntType(8).as_pointer(), lir.
            IntType(offset_type.bitwidth).as_pointer(), lir.IntType(8).
            as_pointer(), lir.IntType(8).as_pointer(), lir.IntType(32)])
        wtiqd__rusv = cgutils.get_or_insert_function(builder.module,
            ilujb__hctfe, name='string_array_to_info')
        return builder.call(wtiqd__rusv, [tcor__jeylo.n_arrays, jsrqr__jnh,
            xeqd__wsgs, rlpfp__madk, zjue__vmkl, tbwj__dcs.meminfo, daftr__pdv]
            )
    if arr_type == bodo.dict_str_arr_type:
        arr = cgutils.create_struct_proxy(arr_type)(context, builder, in_arr)
        xye__num = arr.data
        khnw__wkz = arr.indices
        sig = array_info_type(arr_type.data)
        pjnir__lgw = array_to_info_codegen(context, builder, sig, (xye__num
            ,), False)
        sig = array_info_type(bodo.libs.dict_arr_ext.dict_indices_arr_type)
        tks__ojw = array_to_info_codegen(context, builder, sig, (khnw__wkz,
            ), False)
        srms__byn = cgutils.create_struct_proxy(bodo.libs.dict_arr_ext.
            dict_indices_arr_type)(context, builder, khnw__wkz)
        qauet__qjwc = context.make_array(types.Array(types.uint8, 1, 'C'))(
            context, builder, srms__byn.null_bitmap).data
        ilujb__hctfe = lir.FunctionType(lir.IntType(8).as_pointer(), [lir.
            IntType(8).as_pointer(), lir.IntType(8).as_pointer(), lir.
            IntType(8).as_pointer(), lir.IntType(32)])
        wtiqd__rusv = cgutils.get_or_insert_function(builder.module,
            ilujb__hctfe, name='dict_str_array_to_info')
        dnx__ghg = builder.zext(arr.has_global_dictionary, lir.IntType(32))
        return builder.call(wtiqd__rusv, [pjnir__lgw, tks__ojw, builder.
            bitcast(qauet__qjwc, lir.IntType(8).as_pointer()), dnx__ghg])
    gtby__ynzm = False
    if isinstance(arr_type, CategoricalArrayType):
        context.nrt.decref(builder, arr_type, in_arr)
        ygdkv__yutka = context.compile_internal(builder, lambda a: len(a.
            dtype.categories), types.intp(arr_type), [in_arr])
        in_arr = cgutils.create_struct_proxy(arr_type)(context, builder, in_arr
            ).codes
        yatt__xvd = get_categories_int_type(arr_type.dtype)
        arr_type = types.Array(yatt__xvd, 1, 'C')
        gtby__ynzm = True
        context.nrt.incref(builder, arr_type, in_arr)
    if isinstance(arr_type, bodo.DatetimeArrayType):
        if gtby__ynzm:
            raise BodoError(
                'array_to_info(): Categorical PandasDatetimeArrayType not supported'
                )
        in_arr = cgutils.create_struct_proxy(arr_type)(context, builder, in_arr
            ).data
        arr_type = arr_type.data_array_type
    if isinstance(arr_type, types.Array):
        arr = context.make_array(arr_type)(context, builder, in_arr)
        assert arr_type.ndim == 1, 'only 1D array shuffle supported'
        msrws__chfl = builder.extract_value(arr.shape, 0)
        sre__czhtw = arr_type.dtype
        jriyw__fcs = numba_to_c_type(sre__czhtw)
        ubr__ryj = cgutils.alloca_once_value(builder, lir.Constant(lir.
            IntType(32), jriyw__fcs))
        if gtby__ynzm:
            ilujb__hctfe = lir.FunctionType(lir.IntType(8).as_pointer(), [
                lir.IntType(64), lir.IntType(8).as_pointer(), lir.IntType(
                32), lir.IntType(64), lir.IntType(8).as_pointer()])
            wtiqd__rusv = cgutils.get_or_insert_function(builder.module,
                ilujb__hctfe, name='categorical_array_to_info')
            return builder.call(wtiqd__rusv, [msrws__chfl, builder.bitcast(
                arr.data, lir.IntType(8).as_pointer()), builder.load(
                ubr__ryj), ygdkv__yutka, arr.meminfo])
        else:
            ilujb__hctfe = lir.FunctionType(lir.IntType(8).as_pointer(), [
                lir.IntType(64), lir.IntType(8).as_pointer(), lir.IntType(
                32), lir.IntType(8).as_pointer()])
            wtiqd__rusv = cgutils.get_or_insert_function(builder.module,
                ilujb__hctfe, name='numpy_array_to_info')
            return builder.call(wtiqd__rusv, [msrws__chfl, builder.bitcast(
                arr.data, lir.IntType(8).as_pointer()), builder.load(
                ubr__ryj), arr.meminfo])
    if isinstance(arr_type, (IntegerArrayType, DecimalArrayType)
        ) or arr_type in (boolean_array, datetime_date_array_type):
        arr = cgutils.create_struct_proxy(arr_type)(context, builder, in_arr)
        sre__czhtw = arr_type.dtype
        exlia__rxgg = sre__czhtw
        if isinstance(arr_type, DecimalArrayType):
            exlia__rxgg = int128_type
        if arr_type == datetime_date_array_type:
            exlia__rxgg = types.int64
        kaha__kkd = context.make_array(types.Array(exlia__rxgg, 1, 'C'))(
            context, builder, arr.data)
        msrws__chfl = builder.extract_value(kaha__kkd.shape, 0)
        hjyz__tcqs = context.make_array(types.Array(types.uint8, 1, 'C'))(
            context, builder, arr.null_bitmap)
        jriyw__fcs = numba_to_c_type(sre__czhtw)
        ubr__ryj = cgutils.alloca_once_value(builder, lir.Constant(lir.
            IntType(32), jriyw__fcs))
        if isinstance(arr_type, DecimalArrayType):
            ilujb__hctfe = lir.FunctionType(lir.IntType(8).as_pointer(), [
                lir.IntType(64), lir.IntType(8).as_pointer(), lir.IntType(
                32), lir.IntType(8).as_pointer(), lir.IntType(8).as_pointer
                (), lir.IntType(8).as_pointer(), lir.IntType(32), lir.
                IntType(32)])
            wtiqd__rusv = cgutils.get_or_insert_function(builder.module,
                ilujb__hctfe, name='decimal_array_to_info')
            return builder.call(wtiqd__rusv, [msrws__chfl, builder.bitcast(
                kaha__kkd.data, lir.IntType(8).as_pointer()), builder.load(
                ubr__ryj), builder.bitcast(hjyz__tcqs.data, lir.IntType(8).
                as_pointer()), kaha__kkd.meminfo, hjyz__tcqs.meminfo,
                context.get_constant(types.int32, arr_type.precision),
                context.get_constant(types.int32, arr_type.scale)])
        else:
            ilujb__hctfe = lir.FunctionType(lir.IntType(8).as_pointer(), [
                lir.IntType(64), lir.IntType(8).as_pointer(), lir.IntType(
                32), lir.IntType(8).as_pointer(), lir.IntType(8).as_pointer
                (), lir.IntType(8).as_pointer()])
            wtiqd__rusv = cgutils.get_or_insert_function(builder.module,
                ilujb__hctfe, name='nullable_array_to_info')
            return builder.call(wtiqd__rusv, [msrws__chfl, builder.bitcast(
                kaha__kkd.data, lir.IntType(8).as_pointer()), builder.load(
                ubr__ryj), builder.bitcast(hjyz__tcqs.data, lir.IntType(8).
                as_pointer()), kaha__kkd.meminfo, hjyz__tcqs.meminfo])
    if isinstance(arr_type, IntervalArrayType):
        assert isinstance(arr_type.arr_type, types.Array
            ), 'array_to_info(): only IntervalArrayType with Numpy arrays supported'
        arr = cgutils.create_struct_proxy(arr_type)(context, builder, in_arr)
        otyn__irw = context.make_array(arr_type.arr_type)(context, builder,
            arr.left)
        jxbvx__voxxc = context.make_array(arr_type.arr_type)(context,
            builder, arr.right)
        msrws__chfl = builder.extract_value(otyn__irw.shape, 0)
        jriyw__fcs = numba_to_c_type(arr_type.arr_type.dtype)
        ubr__ryj = cgutils.alloca_once_value(builder, lir.Constant(lir.
            IntType(32), jriyw__fcs))
        ilujb__hctfe = lir.FunctionType(lir.IntType(8).as_pointer(), [lir.
            IntType(64), lir.IntType(8).as_pointer(), lir.IntType(8).
            as_pointer(), lir.IntType(32), lir.IntType(8).as_pointer(), lir
            .IntType(8).as_pointer()])
        wtiqd__rusv = cgutils.get_or_insert_function(builder.module,
            ilujb__hctfe, name='interval_array_to_info')
        return builder.call(wtiqd__rusv, [msrws__chfl, builder.bitcast(
            otyn__irw.data, lir.IntType(8).as_pointer()), builder.bitcast(
            jxbvx__voxxc.data, lir.IntType(8).as_pointer()), builder.load(
            ubr__ryj), otyn__irw.meminfo, jxbvx__voxxc.meminfo])
    raise_bodo_error(f'array_to_info(): array type {arr_type} is not supported'
        )


def _lower_info_to_array_numpy(arr_type, context, builder, in_info):
    assert arr_type.ndim == 1, 'only 1D array supported'
    arr = context.make_array(arr_type)(context, builder)
    wkeyf__xqkko = cgutils.alloca_once(builder, lir.IntType(64))
    ijevb__qimyn = cgutils.alloca_once(builder, lir.IntType(8).as_pointer())
    hmsj__jbqg = cgutils.alloca_once(builder, lir.IntType(8).as_pointer())
    ilujb__hctfe = lir.FunctionType(lir.VoidType(), [lir.IntType(8).
        as_pointer(), lir.IntType(64).as_pointer(), lir.IntType(8).
        as_pointer().as_pointer(), lir.IntType(8).as_pointer().as_pointer()])
    wtiqd__rusv = cgutils.get_or_insert_function(builder.module,
        ilujb__hctfe, name='info_to_numpy_array')
    builder.call(wtiqd__rusv, [in_info, wkeyf__xqkko, ijevb__qimyn, hmsj__jbqg]
        )
    context.compile_internal(builder, lambda :
        check_and_propagate_cpp_exception(), types.none(), [])
    zssa__zvlzl = context.get_value_type(types.intp)
    xvhpb__osh = cgutils.pack_array(builder, [builder.load(wkeyf__xqkko)],
        ty=zssa__zvlzl)
    stoze__nmbur = context.get_constant(types.intp, context.get_abi_sizeof(
        context.get_data_type(arr_type.dtype)))
    rlot__awb = cgutils.pack_array(builder, [stoze__nmbur], ty=zssa__zvlzl)
    xeqd__wsgs = builder.bitcast(builder.load(ijevb__qimyn), context.
        get_data_type(arr_type.dtype).as_pointer())
    numba.np.arrayobj.populate_array(arr, data=xeqd__wsgs, shape=xvhpb__osh,
        strides=rlot__awb, itemsize=stoze__nmbur, meminfo=builder.load(
        hmsj__jbqg))
    return arr._getvalue()


def _lower_info_to_array_list_string_array(arr_type, context, builder, in_info
    ):
    pstc__mbi = context.make_helper(builder, arr_type)
    ilujb__hctfe = lir.FunctionType(lir.VoidType(), [lir.IntType(8).
        as_pointer(), lir.IntType(8).as_pointer().as_pointer()])
    wtiqd__rusv = cgutils.get_or_insert_function(builder.module,
        ilujb__hctfe, name='info_to_list_string_array')
    builder.call(wtiqd__rusv, [in_info, pstc__mbi._get_ptr_by_name('meminfo')])
    context.compile_internal(builder, lambda :
        check_and_propagate_cpp_exception(), types.none(), [])
    return pstc__mbi._getvalue()


def nested_to_array(context, builder, arr_typ, lengths_ptr, array_infos_ptr,
    lengths_pos, infos_pos):
    wbfs__kycxd = context.get_data_type(array_info_type)
    if isinstance(arr_typ, ArrayItemArrayType):
        qyv__doav = lengths_pos
        dtiv__sntmv = infos_pos
        bruu__oruzc, lengths_pos, infos_pos = nested_to_array(context,
            builder, arr_typ.dtype, lengths_ptr, array_infos_ptr, 
            lengths_pos + 1, infos_pos + 2)
        jbu__tfvyi = ArrayItemArrayPayloadType(arr_typ)
        kmx__hyij = context.get_data_type(jbu__tfvyi)
        llnm__hrsz = context.get_abi_sizeof(kmx__hyij)
        geuh__olgbf = define_array_item_dtor(context, builder, arr_typ,
            jbu__tfvyi)
        rea__lffq = context.nrt.meminfo_alloc_dtor(builder, context.
            get_constant(types.uintp, llnm__hrsz), geuh__olgbf)
        rdyhg__pyv = context.nrt.meminfo_data(builder, rea__lffq)
        htxi__las = builder.bitcast(rdyhg__pyv, kmx__hyij.as_pointer())
        tcor__jeylo = cgutils.create_struct_proxy(jbu__tfvyi)(context, builder)
        tcor__jeylo.n_arrays = builder.extract_value(builder.load(
            lengths_ptr), qyv__doav)
        tcor__jeylo.data = bruu__oruzc
        ycpti__ejwlc = builder.load(array_infos_ptr)
        qjnr__znzck = builder.bitcast(builder.extract_value(ycpti__ejwlc,
            dtiv__sntmv), wbfs__kycxd)
        tcor__jeylo.offsets = _lower_info_to_array_numpy(types.Array(
            offset_type, 1, 'C'), context, builder, qjnr__znzck)
        ofcqn__jel = builder.bitcast(builder.extract_value(ycpti__ejwlc, 
            dtiv__sntmv + 1), wbfs__kycxd)
        tcor__jeylo.null_bitmap = _lower_info_to_array_numpy(types.Array(
            types.uint8, 1, 'C'), context, builder, ofcqn__jel)
        builder.store(tcor__jeylo._getvalue(), htxi__las)
        tbwj__dcs = context.make_helper(builder, arr_typ)
        tbwj__dcs.meminfo = rea__lffq
        return tbwj__dcs._getvalue(), lengths_pos, infos_pos
    elif isinstance(arr_typ, StructArrayType):
        skmc__ulj = []
        dtiv__sntmv = infos_pos
        lengths_pos += 1
        infos_pos += 1
        for lhyvj__wshsn in arr_typ.data:
            bruu__oruzc, lengths_pos, infos_pos = nested_to_array(context,
                builder, lhyvj__wshsn, lengths_ptr, array_infos_ptr,
                lengths_pos, infos_pos)
            skmc__ulj.append(bruu__oruzc)
        jbu__tfvyi = StructArrayPayloadType(arr_typ.data)
        kmx__hyij = context.get_value_type(jbu__tfvyi)
        llnm__hrsz = context.get_abi_sizeof(kmx__hyij)
        geuh__olgbf = define_struct_arr_dtor(context, builder, arr_typ,
            jbu__tfvyi)
        rea__lffq = context.nrt.meminfo_alloc_dtor(builder, context.
            get_constant(types.uintp, llnm__hrsz), geuh__olgbf)
        rdyhg__pyv = context.nrt.meminfo_data(builder, rea__lffq)
        htxi__las = builder.bitcast(rdyhg__pyv, kmx__hyij.as_pointer())
        tcor__jeylo = cgutils.create_struct_proxy(jbu__tfvyi)(context, builder)
        tcor__jeylo.data = cgutils.pack_array(builder, skmc__ulj
            ) if types.is_homogeneous(*arr_typ.data) else cgutils.pack_struct(
            builder, skmc__ulj)
        ycpti__ejwlc = builder.load(array_infos_ptr)
        ofcqn__jel = builder.bitcast(builder.extract_value(ycpti__ejwlc,
            dtiv__sntmv), wbfs__kycxd)
        tcor__jeylo.null_bitmap = _lower_info_to_array_numpy(types.Array(
            types.uint8, 1, 'C'), context, builder, ofcqn__jel)
        builder.store(tcor__jeylo._getvalue(), htxi__las)
        qrqp__uqg = context.make_helper(builder, arr_typ)
        qrqp__uqg.meminfo = rea__lffq
        return qrqp__uqg._getvalue(), lengths_pos, infos_pos
    elif arr_typ in (string_array_type, binary_array_type):
        ycpti__ejwlc = builder.load(array_infos_ptr)
        wjaq__hoepk = builder.bitcast(builder.extract_value(ycpti__ejwlc,
            infos_pos), wbfs__kycxd)
        yqmq__nxmz = context.make_helper(builder, arr_typ)
        rqd__epf = ArrayItemArrayType(char_arr_type)
        tbwj__dcs = context.make_helper(builder, rqd__epf)
        ilujb__hctfe = lir.FunctionType(lir.VoidType(), [lir.IntType(8).
            as_pointer(), lir.IntType(8).as_pointer().as_pointer()])
        wtiqd__rusv = cgutils.get_or_insert_function(builder.module,
            ilujb__hctfe, name='info_to_string_array')
        builder.call(wtiqd__rusv, [wjaq__hoepk, tbwj__dcs._get_ptr_by_name(
            'meminfo')])
        context.compile_internal(builder, lambda :
            check_and_propagate_cpp_exception(), types.none(), [])
        yqmq__nxmz.data = tbwj__dcs._getvalue()
        return yqmq__nxmz._getvalue(), lengths_pos + 1, infos_pos + 1
    elif isinstance(arr_typ, types.Array):
        ycpti__ejwlc = builder.load(array_infos_ptr)
        faqj__xvkii = builder.bitcast(builder.extract_value(ycpti__ejwlc, 
            infos_pos + 1), wbfs__kycxd)
        return _lower_info_to_array_numpy(arr_typ, context, builder,
            faqj__xvkii), lengths_pos + 1, infos_pos + 2
    elif isinstance(arr_typ, (IntegerArrayType, DecimalArrayType)
        ) or arr_typ in (boolean_array, datetime_date_array_type):
        arr = cgutils.create_struct_proxy(arr_typ)(context, builder)
        exlia__rxgg = arr_typ.dtype
        if isinstance(arr_typ, DecimalArrayType):
            exlia__rxgg = int128_type
        elif arr_typ == datetime_date_array_type:
            exlia__rxgg = types.int64
        ycpti__ejwlc = builder.load(array_infos_ptr)
        ofcqn__jel = builder.bitcast(builder.extract_value(ycpti__ejwlc,
            infos_pos), wbfs__kycxd)
        arr.null_bitmap = _lower_info_to_array_numpy(types.Array(types.
            uint8, 1, 'C'), context, builder, ofcqn__jel)
        faqj__xvkii = builder.bitcast(builder.extract_value(ycpti__ejwlc, 
            infos_pos + 1), wbfs__kycxd)
        arr.data = _lower_info_to_array_numpy(types.Array(exlia__rxgg, 1,
            'C'), context, builder, faqj__xvkii)
        return arr._getvalue(), lengths_pos + 1, infos_pos + 2


def info_to_array_codegen(context, builder, sig, args):
    array_type = sig.args[1]
    arr_type = array_type.instance_type if isinstance(array_type, types.TypeRef
        ) else array_type
    in_info, pcoo__cjxo = args
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
                return 1 + sum([get_num_arrays(lhyvj__wshsn) for
                    lhyvj__wshsn in arr_typ.data])
            else:
                return 1

        def get_num_infos(arr_typ):
            if isinstance(arr_typ, ArrayItemArrayType):
                return 2 + get_num_infos(arr_typ.dtype)
            elif isinstance(arr_typ, StructArrayType):
                return 1 + sum([get_num_infos(lhyvj__wshsn) for
                    lhyvj__wshsn in arr_typ.data])
            elif arr_typ in (string_array_type, binary_array_type):
                return 1
            else:
                return 2
        if isinstance(arr_type, TupleArrayType):
            oej__uhzt = StructArrayType(arr_type.data, ('dummy',) * len(
                arr_type.data))
        elif isinstance(arr_type, MapArrayType):
            oej__uhzt = _get_map_arr_data_type(arr_type)
        else:
            oej__uhzt = arr_type
        ltdie__wmhhw = get_num_arrays(oej__uhzt)
        axe__ynaj = cgutils.pack_array(builder, [lir.Constant(lir.IntType(
            64), 0) for pcoo__cjxo in range(ltdie__wmhhw)])
        lengths_ptr = cgutils.alloca_once_value(builder, axe__ynaj)
        vrxr__dtne = lir.Constant(lir.IntType(8).as_pointer(), None)
        wrxmp__lzke = cgutils.pack_array(builder, [vrxr__dtne for
            pcoo__cjxo in range(get_num_infos(oej__uhzt))])
        array_infos_ptr = cgutils.alloca_once_value(builder, wrxmp__lzke)
        ilujb__hctfe = lir.FunctionType(lir.VoidType(), [lir.IntType(8).
            as_pointer(), lir.IntType(64).as_pointer(), lir.IntType(8).
            as_pointer().as_pointer()])
        wtiqd__rusv = cgutils.get_or_insert_function(builder.module,
            ilujb__hctfe, name='info_to_nested_array')
        builder.call(wtiqd__rusv, [in_info, builder.bitcast(lengths_ptr,
            lir.IntType(64).as_pointer()), builder.bitcast(array_infos_ptr,
            lir.IntType(8).as_pointer().as_pointer())])
        context.compile_internal(builder, lambda :
            check_and_propagate_cpp_exception(), types.none(), [])
        arr, pcoo__cjxo, pcoo__cjxo = nested_to_array(context, builder,
            oej__uhzt, lengths_ptr, array_infos_ptr, 0, 0)
        if isinstance(arr_type, TupleArrayType):
            gkk__ahaps = context.make_helper(builder, arr_type)
            gkk__ahaps.data = arr
            context.nrt.incref(builder, oej__uhzt, arr)
            arr = gkk__ahaps._getvalue()
        elif isinstance(arr_type, MapArrayType):
            sig = signature(arr_type, oej__uhzt)
            arr = init_map_arr_codegen(context, builder, sig, (arr,))
        return arr
    if arr_type in (string_array_type, binary_array_type):
        yqmq__nxmz = context.make_helper(builder, arr_type)
        rqd__epf = ArrayItemArrayType(char_arr_type)
        tbwj__dcs = context.make_helper(builder, rqd__epf)
        ilujb__hctfe = lir.FunctionType(lir.VoidType(), [lir.IntType(8).
            as_pointer(), lir.IntType(8).as_pointer().as_pointer()])
        wtiqd__rusv = cgutils.get_or_insert_function(builder.module,
            ilujb__hctfe, name='info_to_string_array')
        builder.call(wtiqd__rusv, [in_info, tbwj__dcs._get_ptr_by_name(
            'meminfo')])
        context.compile_internal(builder, lambda :
            check_and_propagate_cpp_exception(), types.none(), [])
        yqmq__nxmz.data = tbwj__dcs._getvalue()
        return yqmq__nxmz._getvalue()
    if arr_type == bodo.dict_str_arr_type:
        ilujb__hctfe = lir.FunctionType(lir.IntType(8).as_pointer(), [lir.
            IntType(8).as_pointer(), lir.IntType(32)])
        wtiqd__rusv = cgutils.get_or_insert_function(builder.module,
            ilujb__hctfe, name='get_nested_info')
        pjnir__lgw = builder.call(wtiqd__rusv, [in_info, lir.Constant(lir.
            IntType(32), 1)])
        tks__ojw = builder.call(wtiqd__rusv, [in_info, lir.Constant(lir.
            IntType(32), 2)])
        ahm__gclj = context.make_helper(builder, arr_type)
        sig = arr_type.data(array_info_type, arr_type.data)
        ahm__gclj.data = info_to_array_codegen(context, builder, sig, (
            pjnir__lgw, context.get_constant_null(arr_type.data)))
        ytkog__fyqm = bodo.libs.dict_arr_ext.dict_indices_arr_type
        sig = ytkog__fyqm(array_info_type, ytkog__fyqm)
        ahm__gclj.indices = info_to_array_codegen(context, builder, sig, (
            tks__ojw, context.get_constant_null(ytkog__fyqm)))
        ilujb__hctfe = lir.FunctionType(lir.IntType(32), [lir.IntType(8).
            as_pointer()])
        wtiqd__rusv = cgutils.get_or_insert_function(builder.module,
            ilujb__hctfe, name='get_has_global_dictionary')
        dnx__ghg = builder.call(wtiqd__rusv, [in_info])
        ahm__gclj.has_global_dictionary = builder.trunc(dnx__ghg, cgutils.
            bool_t)
        return ahm__gclj._getvalue()
    if isinstance(arr_type, CategoricalArrayType):
        out_arr = cgutils.create_struct_proxy(arr_type)(context, builder)
        yatt__xvd = get_categories_int_type(arr_type.dtype)
        wscqr__mujs = types.Array(yatt__xvd, 1, 'C')
        out_arr.codes = _lower_info_to_array_numpy(wscqr__mujs, context,
            builder, in_info)
        if isinstance(array_type, types.TypeRef):
            assert arr_type.dtype.categories is not None, 'info_to_array: unknown categories'
            is_ordered = arr_type.dtype.ordered
            yitx__cghm = pd.CategoricalDtype(arr_type.dtype.categories,
                is_ordered).categories.values
            new_cats_tup = MetaType(tuple(yitx__cghm))
            int_type = arr_type.dtype.int_type
            tag__kce = bodo.typeof(yitx__cghm)
            udp__lau = context.get_constant_generic(builder, tag__kce,
                yitx__cghm)
            sre__czhtw = context.compile_internal(builder, lambda c_arr:
                bodo.hiframes.pd_categorical_ext.init_cat_dtype(bodo.utils.
                conversion.index_from_array(c_arr), is_ordered, int_type,
                new_cats_tup), arr_type.dtype(tag__kce), [udp__lau])
        else:
            sre__czhtw = cgutils.create_struct_proxy(arr_type)(context,
                builder, args[1]).dtype
            context.nrt.incref(builder, arr_type.dtype, sre__czhtw)
        out_arr.dtype = sre__czhtw
        return out_arr._getvalue()
    if isinstance(arr_type, bodo.DatetimeArrayType):
        arr = cgutils.create_struct_proxy(arr_type)(context, builder)
        xeqd__wsgs = _lower_info_to_array_numpy(arr_type.data_array_type,
            context, builder, in_info)
        arr.data = xeqd__wsgs
        return arr._getvalue()
    if isinstance(arr_type, types.Array):
        return _lower_info_to_array_numpy(arr_type, context, builder, in_info)
    if isinstance(arr_type, (IntegerArrayType, DecimalArrayType)
        ) or arr_type in (boolean_array, datetime_date_array_type):
        arr = cgutils.create_struct_proxy(arr_type)(context, builder)
        exlia__rxgg = arr_type.dtype
        if isinstance(arr_type, DecimalArrayType):
            exlia__rxgg = int128_type
        elif arr_type == datetime_date_array_type:
            exlia__rxgg = types.int64
        hlt__xmt = types.Array(exlia__rxgg, 1, 'C')
        kaha__kkd = context.make_array(hlt__xmt)(context, builder)
        tqb__iiuy = types.Array(types.uint8, 1, 'C')
        qng__rsxxo = context.make_array(tqb__iiuy)(context, builder)
        wkeyf__xqkko = cgutils.alloca_once(builder, lir.IntType(64))
        yzyji__hcxub = cgutils.alloca_once(builder, lir.IntType(64))
        ijevb__qimyn = cgutils.alloca_once(builder, lir.IntType(8).as_pointer()
            )
        qqu__lmgx = cgutils.alloca_once(builder, lir.IntType(8).as_pointer())
        hmsj__jbqg = cgutils.alloca_once(builder, lir.IntType(8).as_pointer())
        jyeim__slscm = cgutils.alloca_once(builder, lir.IntType(8).as_pointer()
            )
        ilujb__hctfe = lir.FunctionType(lir.VoidType(), [lir.IntType(8).
            as_pointer(), lir.IntType(64).as_pointer(), lir.IntType(64).
            as_pointer(), lir.IntType(8).as_pointer().as_pointer(), lir.
            IntType(8).as_pointer().as_pointer(), lir.IntType(8).as_pointer
            ().as_pointer(), lir.IntType(8).as_pointer().as_pointer()])
        wtiqd__rusv = cgutils.get_or_insert_function(builder.module,
            ilujb__hctfe, name='info_to_nullable_array')
        builder.call(wtiqd__rusv, [in_info, wkeyf__xqkko, yzyji__hcxub,
            ijevb__qimyn, qqu__lmgx, hmsj__jbqg, jyeim__slscm])
        context.compile_internal(builder, lambda :
            check_and_propagate_cpp_exception(), types.none(), [])
        zssa__zvlzl = context.get_value_type(types.intp)
        xvhpb__osh = cgutils.pack_array(builder, [builder.load(wkeyf__xqkko
            )], ty=zssa__zvlzl)
        stoze__nmbur = context.get_constant(types.intp, context.
            get_abi_sizeof(context.get_data_type(exlia__rxgg)))
        rlot__awb = cgutils.pack_array(builder, [stoze__nmbur], ty=zssa__zvlzl)
        xeqd__wsgs = builder.bitcast(builder.load(ijevb__qimyn), context.
            get_data_type(exlia__rxgg).as_pointer())
        numba.np.arrayobj.populate_array(kaha__kkd, data=xeqd__wsgs, shape=
            xvhpb__osh, strides=rlot__awb, itemsize=stoze__nmbur, meminfo=
            builder.load(hmsj__jbqg))
        arr.data = kaha__kkd._getvalue()
        xvhpb__osh = cgutils.pack_array(builder, [builder.load(yzyji__hcxub
            )], ty=zssa__zvlzl)
        stoze__nmbur = context.get_constant(types.intp, context.
            get_abi_sizeof(context.get_data_type(types.uint8)))
        rlot__awb = cgutils.pack_array(builder, [stoze__nmbur], ty=zssa__zvlzl)
        xeqd__wsgs = builder.bitcast(builder.load(qqu__lmgx), context.
            get_data_type(types.uint8).as_pointer())
        numba.np.arrayobj.populate_array(qng__rsxxo, data=xeqd__wsgs, shape
            =xvhpb__osh, strides=rlot__awb, itemsize=stoze__nmbur, meminfo=
            builder.load(jyeim__slscm))
        arr.null_bitmap = qng__rsxxo._getvalue()
        return arr._getvalue()
    if isinstance(arr_type, IntervalArrayType):
        arr = cgutils.create_struct_proxy(arr_type)(context, builder)
        otyn__irw = context.make_array(arr_type.arr_type)(context, builder)
        jxbvx__voxxc = context.make_array(arr_type.arr_type)(context, builder)
        wkeyf__xqkko = cgutils.alloca_once(builder, lir.IntType(64))
        wgox__synog = cgutils.alloca_once(builder, lir.IntType(8).as_pointer())
        gek__yih = cgutils.alloca_once(builder, lir.IntType(8).as_pointer())
        asokv__alp = cgutils.alloca_once(builder, lir.IntType(8).as_pointer())
        awb__rdsm = cgutils.alloca_once(builder, lir.IntType(8).as_pointer())
        ilujb__hctfe = lir.FunctionType(lir.VoidType(), [lir.IntType(8).
            as_pointer(), lir.IntType(64).as_pointer(), lir.IntType(8).
            as_pointer().as_pointer(), lir.IntType(8).as_pointer().
            as_pointer(), lir.IntType(8).as_pointer().as_pointer(), lir.
            IntType(8).as_pointer().as_pointer()])
        wtiqd__rusv = cgutils.get_or_insert_function(builder.module,
            ilujb__hctfe, name='info_to_interval_array')
        builder.call(wtiqd__rusv, [in_info, wkeyf__xqkko, wgox__synog,
            gek__yih, asokv__alp, awb__rdsm])
        context.compile_internal(builder, lambda :
            check_and_propagate_cpp_exception(), types.none(), [])
        zssa__zvlzl = context.get_value_type(types.intp)
        xvhpb__osh = cgutils.pack_array(builder, [builder.load(wkeyf__xqkko
            )], ty=zssa__zvlzl)
        stoze__nmbur = context.get_constant(types.intp, context.
            get_abi_sizeof(context.get_data_type(arr_type.arr_type.dtype)))
        rlot__awb = cgutils.pack_array(builder, [stoze__nmbur], ty=zssa__zvlzl)
        ubvkl__ygbms = builder.bitcast(builder.load(wgox__synog), context.
            get_data_type(arr_type.arr_type.dtype).as_pointer())
        numba.np.arrayobj.populate_array(otyn__irw, data=ubvkl__ygbms,
            shape=xvhpb__osh, strides=rlot__awb, itemsize=stoze__nmbur,
            meminfo=builder.load(asokv__alp))
        arr.left = otyn__irw._getvalue()
        zxg__qwfxj = builder.bitcast(builder.load(gek__yih), context.
            get_data_type(arr_type.arr_type.dtype).as_pointer())
        numba.np.arrayobj.populate_array(jxbvx__voxxc, data=zxg__qwfxj,
            shape=xvhpb__osh, strides=rlot__awb, itemsize=stoze__nmbur,
            meminfo=builder.load(awb__rdsm))
        arr.right = jxbvx__voxxc._getvalue()
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
        msrws__chfl, pcoo__cjxo = args
        jriyw__fcs = numba_to_c_type(array_type.dtype)
        ubr__ryj = cgutils.alloca_once_value(builder, lir.Constant(lir.
            IntType(32), jriyw__fcs))
        ilujb__hctfe = lir.FunctionType(lir.IntType(8).as_pointer(), [lir.
            IntType(64), lir.IntType(32)])
        wtiqd__rusv = cgutils.get_or_insert_function(builder.module,
            ilujb__hctfe, name='alloc_numpy')
        return builder.call(wtiqd__rusv, [msrws__chfl, builder.load(ubr__ryj)])
    return array_info_type(len_typ, arr_type), codegen


@intrinsic
def test_alloc_string(typingctx, len_typ, n_chars_typ):

    def codegen(context, builder, sig, args):
        msrws__chfl, jeaec__ijz = args
        ilujb__hctfe = lir.FunctionType(lir.IntType(8).as_pointer(), [lir.
            IntType(64), lir.IntType(64)])
        wtiqd__rusv = cgutils.get_or_insert_function(builder.module,
            ilujb__hctfe, name='alloc_string_array')
        return builder.call(wtiqd__rusv, [msrws__chfl, jeaec__ijz])
    return array_info_type(len_typ, n_chars_typ), codegen


@intrinsic
def arr_info_list_to_table(typingctx, list_arr_info_typ=None):
    assert list_arr_info_typ == types.List(array_info_type)
    return table_type(list_arr_info_typ), arr_info_list_to_table_codegen


def arr_info_list_to_table_codegen(context, builder, sig, args):
    abcg__walez, = args
    swfq__zhqqq = numba.cpython.listobj.ListInstance(context, builder, sig.
        args[0], abcg__walez)
    ilujb__hctfe = lir.FunctionType(lir.IntType(8).as_pointer(), [lir.
        IntType(8).as_pointer().as_pointer(), lir.IntType(64)])
    wtiqd__rusv = cgutils.get_or_insert_function(builder.module,
        ilujb__hctfe, name='arr_info_list_to_table')
    return builder.call(wtiqd__rusv, [swfq__zhqqq.data, swfq__zhqqq.size])


@intrinsic
def info_from_table(typingctx, table_t, ind_t):

    def codegen(context, builder, sig, args):
        ilujb__hctfe = lir.FunctionType(lir.IntType(8).as_pointer(), [lir.
            IntType(8).as_pointer(), lir.IntType(64)])
        wtiqd__rusv = cgutils.get_or_insert_function(builder.module,
            ilujb__hctfe, name='info_from_table')
        return builder.call(wtiqd__rusv, args)
    return array_info_type(table_t, ind_t), codegen


@intrinsic
def cpp_table_to_py_table(typingctx, cpp_table_t, table_idx_arr_t,
    py_table_type_t):
    assert cpp_table_t == table_type, 'invalid cpp table type'
    assert isinstance(table_idx_arr_t, types.Array
        ) and table_idx_arr_t.dtype == types.int64, 'invalid table index array'
    assert isinstance(py_table_type_t, types.TypeRef), 'invalid py table ref'
    tgrxe__ybgu = py_table_type_t.instance_type

    def codegen(context, builder, sig, args):
        acunm__vxgy, ajqln__rsqe, pcoo__cjxo = args
        ilujb__hctfe = lir.FunctionType(lir.IntType(8).as_pointer(), [lir.
            IntType(8).as_pointer(), lir.IntType(64)])
        wtiqd__rusv = cgutils.get_or_insert_function(builder.module,
            ilujb__hctfe, name='info_from_table')
        qcr__lufl = cgutils.create_struct_proxy(tgrxe__ybgu)(context, builder)
        qcr__lufl.parent = cgutils.get_null_value(qcr__lufl.parent.type)
        gmo__znqtk = context.make_array(table_idx_arr_t)(context, builder,
            ajqln__rsqe)
        iutnz__mloqw = context.get_constant(types.int64, -1)
        isk__wkqvf = context.get_constant(types.int64, 0)
        ejc__qemym = cgutils.alloca_once_value(builder, isk__wkqvf)
        for t, fpog__ndjp in tgrxe__ybgu.type_to_blk.items():
            lfryo__fcjvj = context.get_constant(types.int64, len(
                tgrxe__ybgu.block_to_arr_ind[fpog__ndjp]))
            pcoo__cjxo, zjxfu__zanvv = ListInstance.allocate_ex(context,
                builder, types.List(t), lfryo__fcjvj)
            zjxfu__zanvv.size = lfryo__fcjvj
            ziwns__ptn = context.make_constant_array(builder, types.Array(
                types.int64, 1, 'C'), np.array(tgrxe__ybgu.block_to_arr_ind
                [fpog__ndjp], dtype=np.int64))
            xubt__ntu = context.make_array(types.Array(types.int64, 1, 'C'))(
                context, builder, ziwns__ptn)
            with cgutils.for_range(builder, lfryo__fcjvj) as klfko__ekq:
                okik__drlr = klfko__ekq.index
                brjl__rqjv = _getitem_array_single_int(context, builder,
                    types.int64, types.Array(types.int64, 1, 'C'),
                    xubt__ntu, okik__drlr)
                mhcgg__gqrf = _getitem_array_single_int(context, builder,
                    types.int64, table_idx_arr_t, gmo__znqtk, brjl__rqjv)
                zmish__ucxmw = builder.icmp_unsigned('!=', mhcgg__gqrf,
                    iutnz__mloqw)
                with builder.if_else(zmish__ucxmw) as (aym__iuuwv, pgn__yuf):
                    with aym__iuuwv:
                        vedo__ggtno = builder.call(wtiqd__rusv, [
                            acunm__vxgy, mhcgg__gqrf])
                        arr = context.compile_internal(builder, lambda info:
                            info_to_array(info, t), t(array_info_type), [
                            vedo__ggtno])
                        zjxfu__zanvv.inititem(okik__drlr, arr, incref=False)
                        msrws__chfl = context.compile_internal(builder, lambda
                            arr: len(arr), types.int64(t), [arr])
                        builder.store(msrws__chfl, ejc__qemym)
                    with pgn__yuf:
                        lne__gkg = context.get_constant_null(t)
                        zjxfu__zanvv.inititem(okik__drlr, lne__gkg, incref=
                            False)
            setattr(qcr__lufl, f'block_{fpog__ndjp}', zjxfu__zanvv.value)
        qcr__lufl.len = builder.load(ejc__qemym)
        return qcr__lufl._getvalue()
    return tgrxe__ybgu(cpp_table_t, table_idx_arr_t, py_table_type_t), codegen


@intrinsic
def py_table_to_cpp_table(typingctx, py_table_t, py_table_type_t):
    assert isinstance(py_table_t, bodo.hiframes.table.TableType
        ), 'invalid py table type'
    assert isinstance(py_table_type_t, types.TypeRef), 'invalid py table ref'
    tgrxe__ybgu = py_table_type_t.instance_type

    def codegen(context, builder, sig, args):
        imj__ozsvb, pcoo__cjxo = args
        aio__bfba = cgutils.create_struct_proxy(tgrxe__ybgu)(context,
            builder, imj__ozsvb)
        if tgrxe__ybgu.has_runtime_cols:
            fdh__cnxoc = lir.Constant(lir.IntType(64), 0)
            for fpog__ndjp, t in enumerate(tgrxe__ybgu.arr_types):
                kwd__vzj = getattr(aio__bfba, f'block_{fpog__ndjp}')
                lokt__ffpn = ListInstance(context, builder, types.List(t),
                    kwd__vzj)
                fdh__cnxoc = builder.add(fdh__cnxoc, lokt__ffpn.size)
        else:
            fdh__cnxoc = lir.Constant(lir.IntType(64), len(tgrxe__ybgu.
                arr_types))
        pcoo__cjxo, ydu__mqfx = ListInstance.allocate_ex(context, builder,
            types.List(array_info_type), fdh__cnxoc)
        ydu__mqfx.size = fdh__cnxoc
        if tgrxe__ybgu.has_runtime_cols:
            nhbrn__tdpn = lir.Constant(lir.IntType(64), 0)
            for fpog__ndjp, t in enumerate(tgrxe__ybgu.arr_types):
                kwd__vzj = getattr(aio__bfba, f'block_{fpog__ndjp}')
                lokt__ffpn = ListInstance(context, builder, types.List(t),
                    kwd__vzj)
                lfryo__fcjvj = lokt__ffpn.size
                with cgutils.for_range(builder, lfryo__fcjvj) as klfko__ekq:
                    okik__drlr = klfko__ekq.index
                    arr = lokt__ffpn.getitem(okik__drlr)
                    jst__ago = signature(array_info_type, t)
                    pmldu__oriyx = arr,
                    jtmn__npro = array_to_info_codegen(context, builder,
                        jst__ago, pmldu__oriyx)
                    ydu__mqfx.inititem(builder.add(nhbrn__tdpn, okik__drlr),
                        jtmn__npro, incref=False)
                nhbrn__tdpn = builder.add(nhbrn__tdpn, lfryo__fcjvj)
        else:
            for t, fpog__ndjp in tgrxe__ybgu.type_to_blk.items():
                lfryo__fcjvj = context.get_constant(types.int64, len(
                    tgrxe__ybgu.block_to_arr_ind[fpog__ndjp]))
                kwd__vzj = getattr(aio__bfba, f'block_{fpog__ndjp}')
                lokt__ffpn = ListInstance(context, builder, types.List(t),
                    kwd__vzj)
                ziwns__ptn = context.make_constant_array(builder, types.
                    Array(types.int64, 1, 'C'), np.array(tgrxe__ybgu.
                    block_to_arr_ind[fpog__ndjp], dtype=np.int64))
                xubt__ntu = context.make_array(types.Array(types.int64, 1, 'C')
                    )(context, builder, ziwns__ptn)
                with cgutils.for_range(builder, lfryo__fcjvj) as klfko__ekq:
                    okik__drlr = klfko__ekq.index
                    brjl__rqjv = _getitem_array_single_int(context, builder,
                        types.int64, types.Array(types.int64, 1, 'C'),
                        xubt__ntu, okik__drlr)
                    lxgk__miqow = signature(types.none, tgrxe__ybgu, types.
                        List(t), types.int64, types.int64)
                    rtz__atagz = imj__ozsvb, kwd__vzj, okik__drlr, brjl__rqjv
                    bodo.hiframes.table.ensure_column_unboxed_codegen(context,
                        builder, lxgk__miqow, rtz__atagz)
                    arr = lokt__ffpn.getitem(okik__drlr)
                    jst__ago = signature(array_info_type, t)
                    pmldu__oriyx = arr,
                    jtmn__npro = array_to_info_codegen(context, builder,
                        jst__ago, pmldu__oriyx)
                    ydu__mqfx.inititem(brjl__rqjv, jtmn__npro, incref=False)
        qxd__oajb = ydu__mqfx.value
        igdk__kwcb = signature(table_type, types.List(array_info_type))
        ybb__zuth = qxd__oajb,
        acunm__vxgy = arr_info_list_to_table_codegen(context, builder,
            igdk__kwcb, ybb__zuth)
        context.nrt.decref(builder, types.List(array_info_type), qxd__oajb)
        return acunm__vxgy
    return table_type(tgrxe__ybgu, py_table_type_t), codegen


delete_info_decref_array = types.ExternalFunction('delete_info_decref_array',
    types.void(array_info_type))
delete_table_decref_arrays = types.ExternalFunction(
    'delete_table_decref_arrays', types.void(table_type))


@intrinsic
def delete_table(typingctx, table_t=None):
    assert table_t == table_type

    def codegen(context, builder, sig, args):
        ilujb__hctfe = lir.FunctionType(lir.VoidType(), [lir.IntType(8).
            as_pointer()])
        wtiqd__rusv = cgutils.get_or_insert_function(builder.module,
            ilujb__hctfe, name='delete_table')
        builder.call(wtiqd__rusv, args)
    return types.void(table_t), codegen


@intrinsic
def shuffle_table(typingctx, table_t, n_keys_t, _is_parallel, keep_comm_info_t
    ):
    assert table_t == table_type

    def codegen(context, builder, sig, args):
        ilujb__hctfe = lir.FunctionType(lir.IntType(8).as_pointer(), [lir.
            IntType(8).as_pointer(), lir.IntType(64), lir.IntType(1), lir.
            IntType(32)])
        wtiqd__rusv = cgutils.get_or_insert_function(builder.module,
            ilujb__hctfe, name='shuffle_table')
        nhe__say = builder.call(wtiqd__rusv, args)
        context.compile_internal(builder, lambda :
            check_and_propagate_cpp_exception(), types.none(), [])
        return nhe__say
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
        ilujb__hctfe = lir.FunctionType(lir.VoidType(), [lir.IntType(8).
            as_pointer()])
        wtiqd__rusv = cgutils.get_or_insert_function(builder.module,
            ilujb__hctfe, name='delete_shuffle_info')
        return builder.call(wtiqd__rusv, args)
    return types.void(shuffle_info_t), codegen


@intrinsic
def reverse_shuffle_table(typingctx, table_t, shuffle_info_t=None):

    def codegen(context, builder, sig, args):
        if sig.args[-1] == types.none:
            return context.get_constant_null(table_type)
        ilujb__hctfe = lir.FunctionType(lir.IntType(8).as_pointer(), [lir.
            IntType(8).as_pointer(), lir.IntType(8).as_pointer()])
        wtiqd__rusv = cgutils.get_or_insert_function(builder.module,
            ilujb__hctfe, name='reverse_shuffle_table')
        return builder.call(wtiqd__rusv, args)
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
        ilujb__hctfe = lir.FunctionType(lir.IntType(8).as_pointer(), [lir.
            IntType(8).as_pointer(), lir.IntType(8).as_pointer(), lir.
            IntType(1), lir.IntType(1), lir.IntType(64), lir.IntType(64),
            lir.IntType(64), lir.IntType(8).as_pointer(), lir.IntType(8).
            as_pointer(), lir.IntType(1), lir.IntType(1), lir.IntType(1),
            lir.IntType(1), lir.IntType(1), lir.IntType(1), lir.IntType(8).
            as_pointer(), lir.IntType(8).as_pointer(), lir.IntType(64), lir
            .IntType(8).as_pointer(), lir.IntType(64)])
        wtiqd__rusv = cgutils.get_or_insert_function(builder.module,
            ilujb__hctfe, name='hash_join_table')
        nhe__say = builder.call(wtiqd__rusv, args)
        context.compile_internal(builder, lambda :
            check_and_propagate_cpp_exception(), types.none(), [])
        return nhe__say
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
        ilujb__hctfe = lir.FunctionType(lir.IntType(8).as_pointer(), [lir.
            IntType(8).as_pointer(), lir.IntType(64), lir.IntType(8).
            as_pointer(), lir.IntType(8).as_pointer(), lir.IntType(1)])
        wtiqd__rusv = cgutils.get_or_insert_function(builder.module,
            ilujb__hctfe, name='sort_values_table')
        nhe__say = builder.call(wtiqd__rusv, args)
        context.compile_internal(builder, lambda :
            check_and_propagate_cpp_exception(), types.none(), [])
        return nhe__say
    return table_type(table_t, types.int64, types.voidptr, types.voidptr,
        types.boolean), codegen


@intrinsic
def sample_table(typingctx, table_t, n_keys_t, frac_t, replace_t, parallel_t):
    assert table_t == table_type

    def codegen(context, builder, sig, args):
        ilujb__hctfe = lir.FunctionType(lir.IntType(8).as_pointer(), [lir.
            IntType(8).as_pointer(), lir.IntType(64), lir.DoubleType(), lir
            .IntType(1), lir.IntType(1)])
        wtiqd__rusv = cgutils.get_or_insert_function(builder.module,
            ilujb__hctfe, name='sample_table')
        nhe__say = builder.call(wtiqd__rusv, args)
        context.compile_internal(builder, lambda :
            check_and_propagate_cpp_exception(), types.none(), [])
        return nhe__say
    return table_type(table_t, types.int64, types.float64, types.boolean,
        types.boolean), codegen


@intrinsic
def shuffle_renormalization(typingctx, table_t, random_t, random_seed_t,
    is_parallel_t):
    assert table_t == table_type

    def codegen(context, builder, sig, args):
        ilujb__hctfe = lir.FunctionType(lir.IntType(8).as_pointer(), [lir.
            IntType(8).as_pointer(), lir.IntType(32), lir.IntType(64), lir.
            IntType(1)])
        wtiqd__rusv = cgutils.get_or_insert_function(builder.module,
            ilujb__hctfe, name='shuffle_renormalization')
        nhe__say = builder.call(wtiqd__rusv, args)
        context.compile_internal(builder, lambda :
            check_and_propagate_cpp_exception(), types.none(), [])
        return nhe__say
    return table_type(table_t, types.int32, types.int64, types.boolean
        ), codegen


@intrinsic
def shuffle_renormalization_group(typingctx, table_t, random_t,
    random_seed_t, is_parallel_t, num_ranks_t, ranks_t):
    assert table_t == table_type

    def codegen(context, builder, sig, args):
        ilujb__hctfe = lir.FunctionType(lir.IntType(8).as_pointer(), [lir.
            IntType(8).as_pointer(), lir.IntType(32), lir.IntType(64), lir.
            IntType(1), lir.IntType(64), lir.IntType(8).as_pointer()])
        wtiqd__rusv = cgutils.get_or_insert_function(builder.module,
            ilujb__hctfe, name='shuffle_renormalization_group')
        nhe__say = builder.call(wtiqd__rusv, args)
        context.compile_internal(builder, lambda :
            check_and_propagate_cpp_exception(), types.none(), [])
        return nhe__say
    return table_type(table_t, types.int32, types.int64, types.boolean,
        types.int64, types.voidptr), codegen


@intrinsic
def drop_duplicates_table(typingctx, table_t, parallel_t, nkey_t, keep_t,
    dropna, drop_local_first):
    assert table_t == table_type

    def codegen(context, builder, sig, args):
        ilujb__hctfe = lir.FunctionType(lir.IntType(8).as_pointer(), [lir.
            IntType(8).as_pointer(), lir.IntType(1), lir.IntType(64), lir.
            IntType(64), lir.IntType(1), lir.IntType(1)])
        wtiqd__rusv = cgutils.get_or_insert_function(builder.module,
            ilujb__hctfe, name='drop_duplicates_table')
        nhe__say = builder.call(wtiqd__rusv, args)
        context.compile_internal(builder, lambda :
            check_and_propagate_cpp_exception(), types.none(), [])
        return nhe__say
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
        ilujb__hctfe = lir.FunctionType(lir.IntType(8).as_pointer(), [lir.
            IntType(8).as_pointer(), lir.IntType(64), lir.IntType(8).
            as_pointer(), lir.IntType(8).as_pointer(), lir.IntType(1), lir.
            IntType(8).as_pointer(), lir.IntType(8).as_pointer(), lir.
            IntType(8).as_pointer(), lir.IntType(1), lir.IntType(1), lir.
            IntType(1), lir.IntType(1), lir.IntType(1), lir.IntType(8).
            as_pointer(), lir.IntType(8).as_pointer(), lir.IntType(8).
            as_pointer(), lir.IntType(8).as_pointer()])
        wtiqd__rusv = cgutils.get_or_insert_function(builder.module,
            ilujb__hctfe, name='pivot_groupby_and_aggregate')
        nhe__say = builder.call(wtiqd__rusv, args)
        context.compile_internal(builder, lambda :
            check_and_propagate_cpp_exception(), types.none(), [])
        return nhe__say
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
        ilujb__hctfe = lir.FunctionType(lir.IntType(8).as_pointer(), [lir.
            IntType(8).as_pointer(), lir.IntType(64), lir.IntType(1), lir.
            IntType(8).as_pointer(), lir.IntType(8).as_pointer(), lir.
            IntType(8).as_pointer(), lir.IntType(1), lir.IntType(1), lir.
            IntType(64), lir.IntType(64), lir.IntType(64), lir.IntType(1),
            lir.IntType(1), lir.IntType(1), lir.IntType(8).as_pointer(),
            lir.IntType(8).as_pointer(), lir.IntType(8).as_pointer(), lir.
            IntType(8).as_pointer(), lir.IntType(8).as_pointer()])
        wtiqd__rusv = cgutils.get_or_insert_function(builder.module,
            ilujb__hctfe, name='groupby_and_aggregate')
        nhe__say = builder.call(wtiqd__rusv, args)
        context.compile_internal(builder, lambda :
            check_and_propagate_cpp_exception(), types.none(), [])
        return nhe__say
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
    tic__bmkl = array_to_info(in_arr)
    cou__ijnbl = array_to_info(in_values)
    akw__mmfji = array_to_info(out_arr)
    arztb__fzp = arr_info_list_to_table([tic__bmkl, cou__ijnbl, akw__mmfji])
    _array_isin(akw__mmfji, tic__bmkl, cou__ijnbl, is_parallel)
    check_and_propagate_cpp_exception()
    delete_table(arztb__fzp)


_get_search_regex = types.ExternalFunction('get_search_regex', types.void(
    array_info_type, types.bool_, types.voidptr, array_info_type))


@numba.njit(no_cpython_wrapper=True)
def get_search_regex(in_arr, case, pat, out_arr):
    in_arr = decode_if_dict_array(in_arr)
    tic__bmkl = array_to_info(in_arr)
    akw__mmfji = array_to_info(out_arr)
    _get_search_regex(tic__bmkl, case, pat, akw__mmfji)
    check_and_propagate_cpp_exception()


def _gen_row_access_intrinsic(col_array_typ, c_ind):
    from llvmlite import ir as lir
    adf__edd = col_array_typ.dtype
    if isinstance(adf__edd, types.Number) or adf__edd in [bodo.
        datetime_date_type, bodo.datetime64ns, bodo.timedelta64ns, types.bool_
        ]:

        @intrinsic
        def getitem_func(typingctx, table_t, ind_t):

            def codegen(context, builder, sig, args):
                qcr__lufl, yjce__nsctw = args
                qcr__lufl = builder.bitcast(qcr__lufl, lir.IntType(8).
                    as_pointer().as_pointer())
                jrcoq__ico = lir.Constant(lir.IntType(64), c_ind)
                uuxr__xbarb = builder.load(builder.gep(qcr__lufl, [jrcoq__ico])
                    )
                uuxr__xbarb = builder.bitcast(uuxr__xbarb, context.
                    get_data_type(adf__edd).as_pointer())
                return builder.load(builder.gep(uuxr__xbarb, [yjce__nsctw]))
            return adf__edd(types.voidptr, types.int64), codegen
        return getitem_func
    if col_array_typ == bodo.string_array_type:

        @intrinsic
        def getitem_func(typingctx, table_t, ind_t):

            def codegen(context, builder, sig, args):
                qcr__lufl, yjce__nsctw = args
                qcr__lufl = builder.bitcast(qcr__lufl, lir.IntType(8).
                    as_pointer().as_pointer())
                jrcoq__ico = lir.Constant(lir.IntType(64), c_ind)
                uuxr__xbarb = builder.load(builder.gep(qcr__lufl, [jrcoq__ico])
                    )
                ilujb__hctfe = lir.FunctionType(lir.IntType(8).as_pointer(),
                    [lir.IntType(8).as_pointer(), lir.IntType(64), lir.
                    IntType(64).as_pointer()])
                ybf__oamf = cgutils.get_or_insert_function(builder.module,
                    ilujb__hctfe, name='array_info_getitem')
                jwi__fghqh = cgutils.alloca_once(builder, lir.IntType(64))
                args = uuxr__xbarb, yjce__nsctw, jwi__fghqh
                ijevb__qimyn = builder.call(ybf__oamf, args)
                return context.make_tuple(builder, sig.return_type, [
                    ijevb__qimyn, builder.load(jwi__fghqh)])
            return types.Tuple([types.voidptr, types.int64])(types.voidptr,
                types.int64), codegen
        return getitem_func
    if col_array_typ == bodo.libs.dict_arr_ext.dict_str_arr_type:

        @intrinsic
        def getitem_func(typingctx, table_t, ind_t):

            def codegen(context, builder, sig, args):
                zjdh__kawyy = lir.Constant(lir.IntType(64), 1)
                mnk__bzrdw = lir.Constant(lir.IntType(64), 2)
                qcr__lufl, yjce__nsctw = args
                qcr__lufl = builder.bitcast(qcr__lufl, lir.IntType(8).
                    as_pointer().as_pointer())
                jrcoq__ico = lir.Constant(lir.IntType(64), c_ind)
                uuxr__xbarb = builder.load(builder.gep(qcr__lufl, [jrcoq__ico])
                    )
                ilujb__hctfe = lir.FunctionType(lir.IntType(8).as_pointer(),
                    [lir.IntType(8).as_pointer(), lir.IntType(64)])
                mwoj__eplc = cgutils.get_or_insert_function(builder.module,
                    ilujb__hctfe, name='get_nested_info')
                args = uuxr__xbarb, mnk__bzrdw
                yhslc__kroe = builder.call(mwoj__eplc, args)
                ilujb__hctfe = lir.FunctionType(lir.IntType(8).as_pointer(),
                    [lir.IntType(8).as_pointer()])
                lwzq__nbqd = cgutils.get_or_insert_function(builder.module,
                    ilujb__hctfe, name='array_info_getdata1')
                args = yhslc__kroe,
                twqpo__sfxz = builder.call(lwzq__nbqd, args)
                twqpo__sfxz = builder.bitcast(twqpo__sfxz, context.
                    get_data_type(col_array_typ.indices_dtype).as_pointer())
                whrru__esdx = builder.sext(builder.load(builder.gep(
                    twqpo__sfxz, [yjce__nsctw])), lir.IntType(64))
                args = uuxr__xbarb, zjdh__kawyy
                xwaj__pxq = builder.call(mwoj__eplc, args)
                ilujb__hctfe = lir.FunctionType(lir.IntType(8).as_pointer(),
                    [lir.IntType(8).as_pointer(), lir.IntType(64), lir.
                    IntType(64).as_pointer()])
                ybf__oamf = cgutils.get_or_insert_function(builder.module,
                    ilujb__hctfe, name='array_info_getitem')
                jwi__fghqh = cgutils.alloca_once(builder, lir.IntType(64))
                args = xwaj__pxq, whrru__esdx, jwi__fghqh
                ijevb__qimyn = builder.call(ybf__oamf, args)
                return context.make_tuple(builder, sig.return_type, [
                    ijevb__qimyn, builder.load(jwi__fghqh)])
            return types.Tuple([types.voidptr, types.int64])(types.voidptr,
                types.int64), codegen
        return getitem_func
    raise BodoError(
        f"General Join Conditions with '{adf__edd}' column data type not supported"
        )


def _gen_row_na_check_intrinsic(col_array_dtype, c_ind):
    if (isinstance(col_array_dtype, bodo.libs.int_arr_ext.IntegerArrayType) or
        col_array_dtype == bodo.libs.bool_arr_ext.boolean_array or
        is_str_arr_type(col_array_dtype) or isinstance(col_array_dtype,
        types.Array) and col_array_dtype.dtype == bodo.datetime_date_type):

        @intrinsic
        def checkna_func(typingctx, table_t, ind_t):

            def codegen(context, builder, sig, args):
                flmm__nym, yjce__nsctw = args
                flmm__nym = builder.bitcast(flmm__nym, lir.IntType(8).
                    as_pointer().as_pointer())
                jrcoq__ico = lir.Constant(lir.IntType(64), c_ind)
                uuxr__xbarb = builder.load(builder.gep(flmm__nym, [jrcoq__ico])
                    )
                zjue__vmkl = builder.bitcast(uuxr__xbarb, context.
                    get_data_type(types.bool_).as_pointer())
                ftywy__eqf = bodo.utils.cg_helpers.get_bitmap_bit(builder,
                    zjue__vmkl, yjce__nsctw)
                pnek__ssnw = builder.icmp_unsigned('!=', ftywy__eqf, lir.
                    Constant(lir.IntType(8), 0))
                return builder.sext(pnek__ssnw, lir.IntType(8))
            return types.int8(types.voidptr, types.int64), codegen
        return checkna_func
    elif isinstance(col_array_dtype, types.Array):
        adf__edd = col_array_dtype.dtype
        if adf__edd in [bodo.datetime64ns, bodo.timedelta64ns]:

            @intrinsic
            def checkna_func(typingctx, table_t, ind_t):

                def codegen(context, builder, sig, args):
                    qcr__lufl, yjce__nsctw = args
                    qcr__lufl = builder.bitcast(qcr__lufl, lir.IntType(8).
                        as_pointer().as_pointer())
                    jrcoq__ico = lir.Constant(lir.IntType(64), c_ind)
                    uuxr__xbarb = builder.load(builder.gep(qcr__lufl, [
                        jrcoq__ico]))
                    uuxr__xbarb = builder.bitcast(uuxr__xbarb, context.
                        get_data_type(adf__edd).as_pointer())
                    pxm__vbn = builder.load(builder.gep(uuxr__xbarb, [
                        yjce__nsctw]))
                    pnek__ssnw = builder.icmp_unsigned('!=', pxm__vbn, lir.
                        Constant(lir.IntType(64), pd._libs.iNaT))
                    return builder.sext(pnek__ssnw, lir.IntType(8))
                return types.int8(types.voidptr, types.int64), codegen
            return checkna_func
        elif isinstance(adf__edd, types.Float):

            @intrinsic
            def checkna_func(typingctx, table_t, ind_t):

                def codegen(context, builder, sig, args):
                    qcr__lufl, yjce__nsctw = args
                    qcr__lufl = builder.bitcast(qcr__lufl, lir.IntType(8).
                        as_pointer().as_pointer())
                    jrcoq__ico = lir.Constant(lir.IntType(64), c_ind)
                    uuxr__xbarb = builder.load(builder.gep(qcr__lufl, [
                        jrcoq__ico]))
                    uuxr__xbarb = builder.bitcast(uuxr__xbarb, context.
                        get_data_type(adf__edd).as_pointer())
                    pxm__vbn = builder.load(builder.gep(uuxr__xbarb, [
                        yjce__nsctw]))
                    zzk__enoq = signature(types.bool_, adf__edd)
                    ftywy__eqf = numba.np.npyfuncs.np_real_isnan_impl(context,
                        builder, zzk__enoq, (pxm__vbn,))
                    return builder.not_(builder.sext(ftywy__eqf, lir.
                        IntType(8)))
                return types.int8(types.voidptr, types.int64), codegen
            return checkna_func
    raise BodoError(
        f"General Join Conditions with '{col_array_dtype}' column type not supported"
        )
