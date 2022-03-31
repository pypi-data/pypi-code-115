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
        scg__qnbv = context.make_helper(builder, arr_type, in_arr)
        in_arr = scg__qnbv.data
        arr_type = StructArrayType(arr_type.data, ('dummy',) * len(arr_type
            .data))
    if isinstance(arr_type, ArrayItemArrayType
        ) and arr_type.dtype == string_array_type:
        yirgt__ubal = context.make_helper(builder, arr_type, in_arr)
        wjwif__sws = lir.FunctionType(lir.IntType(8).as_pointer(), [lir.
            IntType(8).as_pointer()])
        fxltu__ldx = cgutils.get_or_insert_function(builder.module,
            wjwif__sws, name='list_string_array_to_info')
        return builder.call(fxltu__ldx, [yirgt__ubal.meminfo])
    if isinstance(arr_type, (MapArrayType, ArrayItemArrayType, StructArrayType)
        ):

        def get_types(arr_typ):
            if isinstance(arr_typ, MapArrayType):
                return get_types(_get_map_arr_data_type(arr_typ))
            elif isinstance(arr_typ, ArrayItemArrayType):
                return [CTypeEnum.LIST.value] + get_types(arr_typ.dtype)
            elif isinstance(arr_typ, (StructType, StructArrayType)):
                hit__fxydn = [CTypeEnum.STRUCT.value, len(arr_typ.names)]
                for rkhmy__yqejt in arr_typ.data:
                    hit__fxydn += get_types(rkhmy__yqejt)
                return hit__fxydn
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
            yuhpt__xaf = context.compile_internal(builder, lambda a: len(a),
                types.intp(arr_typ), [arr])
            if isinstance(arr_typ, MapArrayType):
                ixtac__srr = context.make_helper(builder, arr_typ, value=arr)
                yxw__cqme = get_lengths(_get_map_arr_data_type(arr_typ),
                    ixtac__srr.data)
            elif isinstance(arr_typ, ArrayItemArrayType):
                nmi__qcmh = _get_array_item_arr_payload(context, builder,
                    arr_typ, arr)
                yxw__cqme = get_lengths(arr_typ.dtype, nmi__qcmh.data)
                yxw__cqme = cgutils.pack_array(builder, [nmi__qcmh.n_arrays
                    ] + [builder.extract_value(yxw__cqme, ubv__glkot) for
                    ubv__glkot in range(yxw__cqme.type.count)])
            elif isinstance(arr_typ, StructArrayType):
                nmi__qcmh = _get_struct_arr_payload(context, builder,
                    arr_typ, arr)
                yxw__cqme = []
                for ubv__glkot, rkhmy__yqejt in enumerate(arr_typ.data):
                    nopo__dry = get_lengths(rkhmy__yqejt, builder.
                        extract_value(nmi__qcmh.data, ubv__glkot))
                    yxw__cqme += [builder.extract_value(nopo__dry,
                        jfaew__ehjeo) for jfaew__ehjeo in range(nopo__dry.
                        type.count)]
                yxw__cqme = cgutils.pack_array(builder, [yuhpt__xaf,
                    context.get_constant(types.int64, -1)] + yxw__cqme)
            elif isinstance(arr_typ, (IntegerArrayType, DecimalArrayType,
                types.Array)) or arr_typ in (boolean_array,
                datetime_date_array_type, string_array_type, binary_array_type
                ):
                yxw__cqme = cgutils.pack_array(builder, [yuhpt__xaf])
            else:
                raise BodoError(
                    f'array_to_info: unsupported type for subarray {arr_typ}')
            return yxw__cqme

        def get_buffers(arr_typ, arr):
            if isinstance(arr_typ, MapArrayType):
                ixtac__srr = context.make_helper(builder, arr_typ, value=arr)
                nubhk__sle = get_buffers(_get_map_arr_data_type(arr_typ),
                    ixtac__srr.data)
            elif isinstance(arr_typ, ArrayItemArrayType):
                nmi__qcmh = _get_array_item_arr_payload(context, builder,
                    arr_typ, arr)
                lwct__fqjdy = get_buffers(arr_typ.dtype, nmi__qcmh.data)
                wzct__rqzk = context.make_array(types.Array(offset_type, 1,
                    'C'))(context, builder, nmi__qcmh.offsets)
                hdaj__jeh = builder.bitcast(wzct__rqzk.data, lir.IntType(8)
                    .as_pointer())
                pdpgo__rwjv = context.make_array(types.Array(types.uint8, 1,
                    'C'))(context, builder, nmi__qcmh.null_bitmap)
                oobte__hhju = builder.bitcast(pdpgo__rwjv.data, lir.IntType
                    (8).as_pointer())
                nubhk__sle = cgutils.pack_array(builder, [hdaj__jeh,
                    oobte__hhju] + [builder.extract_value(lwct__fqjdy,
                    ubv__glkot) for ubv__glkot in range(lwct__fqjdy.type.
                    count)])
            elif isinstance(arr_typ, StructArrayType):
                nmi__qcmh = _get_struct_arr_payload(context, builder,
                    arr_typ, arr)
                lwct__fqjdy = []
                for ubv__glkot, rkhmy__yqejt in enumerate(arr_typ.data):
                    ukd__jwqob = get_buffers(rkhmy__yqejt, builder.
                        extract_value(nmi__qcmh.data, ubv__glkot))
                    lwct__fqjdy += [builder.extract_value(ukd__jwqob,
                        jfaew__ehjeo) for jfaew__ehjeo in range(ukd__jwqob.
                        type.count)]
                pdpgo__rwjv = context.make_array(types.Array(types.uint8, 1,
                    'C'))(context, builder, nmi__qcmh.null_bitmap)
                oobte__hhju = builder.bitcast(pdpgo__rwjv.data, lir.IntType
                    (8).as_pointer())
                nubhk__sle = cgutils.pack_array(builder, [oobte__hhju] +
                    lwct__fqjdy)
            elif isinstance(arr_typ, (IntegerArrayType, DecimalArrayType)
                ) or arr_typ in (boolean_array, datetime_date_array_type):
                nxap__mkjyp = arr_typ.dtype
                if isinstance(arr_typ, DecimalArrayType):
                    nxap__mkjyp = int128_type
                elif arr_typ == datetime_date_array_type:
                    nxap__mkjyp = types.int64
                arr = cgutils.create_struct_proxy(arr_typ)(context, builder,
                    arr)
                sjbx__gstue = context.make_array(types.Array(nxap__mkjyp, 1,
                    'C'))(context, builder, arr.data)
                pdpgo__rwjv = context.make_array(types.Array(types.uint8, 1,
                    'C'))(context, builder, arr.null_bitmap)
                bij__lycu = builder.bitcast(sjbx__gstue.data, lir.IntType(8
                    ).as_pointer())
                oobte__hhju = builder.bitcast(pdpgo__rwjv.data, lir.IntType
                    (8).as_pointer())
                nubhk__sle = cgutils.pack_array(builder, [oobte__hhju,
                    bij__lycu])
            elif arr_typ in (string_array_type, binary_array_type):
                nmi__qcmh = _get_str_binary_arr_payload(context, builder,
                    arr, arr_typ)
                fpiv__vng = context.make_helper(builder, offset_arr_type,
                    nmi__qcmh.offsets).data
                chct__adja = context.make_helper(builder, char_arr_type,
                    nmi__qcmh.data).data
                ljf__xfb = context.make_helper(builder,
                    null_bitmap_arr_type, nmi__qcmh.null_bitmap).data
                nubhk__sle = cgutils.pack_array(builder, [builder.bitcast(
                    fpiv__vng, lir.IntType(8).as_pointer()), builder.
                    bitcast(ljf__xfb, lir.IntType(8).as_pointer()), builder
                    .bitcast(chct__adja, lir.IntType(8).as_pointer())])
            elif isinstance(arr_typ, types.Array):
                arr = context.make_array(arr_typ)(context, builder, arr)
                bij__lycu = builder.bitcast(arr.data, lir.IntType(8).
                    as_pointer())
                xhxyx__hyz = lir.Constant(lir.IntType(8).as_pointer(), None)
                nubhk__sle = cgutils.pack_array(builder, [xhxyx__hyz,
                    bij__lycu])
            else:
                raise RuntimeError(
                    'array_to_info: unsupported type for subarray ' + str(
                    arr_typ))
            return nubhk__sle

        def get_field_names(arr_typ):
            qawf__iopib = []
            if isinstance(arr_typ, StructArrayType):
                for algc__fxyu, cak__ddju in zip(arr_typ.dtype.names,
                    arr_typ.data):
                    qawf__iopib.append(algc__fxyu)
                    qawf__iopib += get_field_names(cak__ddju)
            elif isinstance(arr_typ, ArrayItemArrayType):
                qawf__iopib += get_field_names(arr_typ.dtype)
            elif isinstance(arr_typ, MapArrayType):
                qawf__iopib += get_field_names(_get_map_arr_data_type(arr_typ))
            return qawf__iopib
        hit__fxydn = get_types(arr_type)
        grg__yxk = cgutils.pack_array(builder, [context.get_constant(types.
            int32, t) for t in hit__fxydn])
        mvgy__azo = cgutils.alloca_once_value(builder, grg__yxk)
        yxw__cqme = get_lengths(arr_type, in_arr)
        lengths_ptr = cgutils.alloca_once_value(builder, yxw__cqme)
        nubhk__sle = get_buffers(arr_type, in_arr)
        tsm__przdg = cgutils.alloca_once_value(builder, nubhk__sle)
        qawf__iopib = get_field_names(arr_type)
        if len(qawf__iopib) == 0:
            qawf__iopib = ['irrelevant']
        wjej__uzv = cgutils.pack_array(builder, [context.
            insert_const_string(builder.module, a) for a in qawf__iopib])
        axal__uvt = cgutils.alloca_once_value(builder, wjej__uzv)
        if isinstance(arr_type, MapArrayType):
            uusts__laz = _get_map_arr_data_type(arr_type)
            eggjd__pnyyw = context.make_helper(builder, arr_type, value=in_arr)
            qjpnh__bvjen = eggjd__pnyyw.data
        else:
            uusts__laz = arr_type
            qjpnh__bvjen = in_arr
        tss__gtov = context.make_helper(builder, uusts__laz, qjpnh__bvjen)
        wjwif__sws = lir.FunctionType(lir.IntType(8).as_pointer(), [lir.
            IntType(32).as_pointer(), lir.IntType(8).as_pointer().
            as_pointer(), lir.IntType(64).as_pointer(), lir.IntType(8).
            as_pointer(), lir.IntType(8).as_pointer()])
        fxltu__ldx = cgutils.get_or_insert_function(builder.module,
            wjwif__sws, name='nested_array_to_info')
        sxo__etrbh = builder.call(fxltu__ldx, [builder.bitcast(mvgy__azo,
            lir.IntType(32).as_pointer()), builder.bitcast(tsm__przdg, lir.
            IntType(8).as_pointer().as_pointer()), builder.bitcast(
            lengths_ptr, lir.IntType(64).as_pointer()), builder.bitcast(
            axal__uvt, lir.IntType(8).as_pointer()), tss__gtov.meminfo])
        context.compile_internal(builder, lambda :
            check_and_propagate_cpp_exception(), types.none(), [])
        return sxo__etrbh
    if arr_type in (string_array_type, binary_array_type):
        ingvw__hyy = context.make_helper(builder, arr_type, in_arr)
        vezg__dwkgo = ArrayItemArrayType(char_arr_type)
        yirgt__ubal = context.make_helper(builder, vezg__dwkgo, ingvw__hyy.data
            )
        nmi__qcmh = _get_str_binary_arr_payload(context, builder, in_arr,
            arr_type)
        fpiv__vng = context.make_helper(builder, offset_arr_type, nmi__qcmh
            .offsets).data
        chct__adja = context.make_helper(builder, char_arr_type, nmi__qcmh.data
            ).data
        ljf__xfb = context.make_helper(builder, null_bitmap_arr_type,
            nmi__qcmh.null_bitmap).data
        thng__stekm = builder.zext(builder.load(builder.gep(fpiv__vng, [
            nmi__qcmh.n_arrays])), lir.IntType(64))
        aipsc__bslt = context.get_constant(types.int32, int(arr_type ==
            binary_array_type))
        wjwif__sws = lir.FunctionType(lir.IntType(8).as_pointer(), [lir.
            IntType(64), lir.IntType(64), lir.IntType(8).as_pointer(), lir.
            IntType(offset_type.bitwidth).as_pointer(), lir.IntType(8).
            as_pointer(), lir.IntType(8).as_pointer(), lir.IntType(32)])
        fxltu__ldx = cgutils.get_or_insert_function(builder.module,
            wjwif__sws, name='string_array_to_info')
        return builder.call(fxltu__ldx, [nmi__qcmh.n_arrays, thng__stekm,
            chct__adja, fpiv__vng, ljf__xfb, yirgt__ubal.meminfo, aipsc__bslt])
    if arr_type == bodo.dict_str_arr_type:
        arr = cgutils.create_struct_proxy(arr_type)(context, builder, in_arr)
        mreub__koedh = arr.data
        mek__bat = arr.indices
        sig = array_info_type(arr_type.data)
        ximw__hqob = array_to_info_codegen(context, builder, sig, (
            mreub__koedh,), False)
        sig = array_info_type(bodo.libs.dict_arr_ext.dict_indices_arr_type)
        qiuh__aflea = array_to_info_codegen(context, builder, sig, (
            mek__bat,), False)
        cclo__irlz = cgutils.create_struct_proxy(bodo.libs.dict_arr_ext.
            dict_indices_arr_type)(context, builder, mek__bat)
        oobte__hhju = context.make_array(types.Array(types.uint8, 1, 'C'))(
            context, builder, cclo__irlz.null_bitmap).data
        wjwif__sws = lir.FunctionType(lir.IntType(8).as_pointer(), [lir.
            IntType(8).as_pointer(), lir.IntType(8).as_pointer(), lir.
            IntType(8).as_pointer(), lir.IntType(32)])
        fxltu__ldx = cgutils.get_or_insert_function(builder.module,
            wjwif__sws, name='dict_str_array_to_info')
        ecuk__rliu = builder.zext(arr.has_global_dictionary, lir.IntType(32))
        return builder.call(fxltu__ldx, [ximw__hqob, qiuh__aflea, builder.
            bitcast(oobte__hhju, lir.IntType(8).as_pointer()), ecuk__rliu])
    phn__frna = False
    if isinstance(arr_type, CategoricalArrayType):
        context.nrt.decref(builder, arr_type, in_arr)
        jup__kgny = context.compile_internal(builder, lambda a: len(a.dtype
            .categories), types.intp(arr_type), [in_arr])
        in_arr = cgutils.create_struct_proxy(arr_type)(context, builder, in_arr
            ).codes
        vzfy__ysshb = get_categories_int_type(arr_type.dtype)
        arr_type = types.Array(vzfy__ysshb, 1, 'C')
        phn__frna = True
        context.nrt.incref(builder, arr_type, in_arr)
    if isinstance(arr_type, bodo.DatetimeArrayType):
        if phn__frna:
            raise BodoError(
                'array_to_info(): Categorical PandasDatetimeArrayType not supported'
                )
        in_arr = cgutils.create_struct_proxy(arr_type)(context, builder, in_arr
            ).data
        arr_type = arr_type.data_array_type
    if isinstance(arr_type, types.Array):
        arr = context.make_array(arr_type)(context, builder, in_arr)
        assert arr_type.ndim == 1, 'only 1D array shuffle supported'
        yuhpt__xaf = builder.extract_value(arr.shape, 0)
        gjwbn__tyssd = arr_type.dtype
        ocam__gex = numba_to_c_type(gjwbn__tyssd)
        corv__ggyrs = cgutils.alloca_once_value(builder, lir.Constant(lir.
            IntType(32), ocam__gex))
        if phn__frna:
            wjwif__sws = lir.FunctionType(lir.IntType(8).as_pointer(), [lir
                .IntType(64), lir.IntType(8).as_pointer(), lir.IntType(32),
                lir.IntType(64), lir.IntType(8).as_pointer()])
            fxltu__ldx = cgutils.get_or_insert_function(builder.module,
                wjwif__sws, name='categorical_array_to_info')
            return builder.call(fxltu__ldx, [yuhpt__xaf, builder.bitcast(
                arr.data, lir.IntType(8).as_pointer()), builder.load(
                corv__ggyrs), jup__kgny, arr.meminfo])
        else:
            wjwif__sws = lir.FunctionType(lir.IntType(8).as_pointer(), [lir
                .IntType(64), lir.IntType(8).as_pointer(), lir.IntType(32),
                lir.IntType(8).as_pointer()])
            fxltu__ldx = cgutils.get_or_insert_function(builder.module,
                wjwif__sws, name='numpy_array_to_info')
            return builder.call(fxltu__ldx, [yuhpt__xaf, builder.bitcast(
                arr.data, lir.IntType(8).as_pointer()), builder.load(
                corv__ggyrs), arr.meminfo])
    if isinstance(arr_type, (IntegerArrayType, DecimalArrayType)
        ) or arr_type in (boolean_array, datetime_date_array_type):
        arr = cgutils.create_struct_proxy(arr_type)(context, builder, in_arr)
        gjwbn__tyssd = arr_type.dtype
        nxap__mkjyp = gjwbn__tyssd
        if isinstance(arr_type, DecimalArrayType):
            nxap__mkjyp = int128_type
        if arr_type == datetime_date_array_type:
            nxap__mkjyp = types.int64
        sjbx__gstue = context.make_array(types.Array(nxap__mkjyp, 1, 'C'))(
            context, builder, arr.data)
        yuhpt__xaf = builder.extract_value(sjbx__gstue.shape, 0)
        dnpx__ukdm = context.make_array(types.Array(types.uint8, 1, 'C'))(
            context, builder, arr.null_bitmap)
        ocam__gex = numba_to_c_type(gjwbn__tyssd)
        corv__ggyrs = cgutils.alloca_once_value(builder, lir.Constant(lir.
            IntType(32), ocam__gex))
        if isinstance(arr_type, DecimalArrayType):
            wjwif__sws = lir.FunctionType(lir.IntType(8).as_pointer(), [lir
                .IntType(64), lir.IntType(8).as_pointer(), lir.IntType(32),
                lir.IntType(8).as_pointer(), lir.IntType(8).as_pointer(),
                lir.IntType(8).as_pointer(), lir.IntType(32), lir.IntType(32)])
            fxltu__ldx = cgutils.get_or_insert_function(builder.module,
                wjwif__sws, name='decimal_array_to_info')
            return builder.call(fxltu__ldx, [yuhpt__xaf, builder.bitcast(
                sjbx__gstue.data, lir.IntType(8).as_pointer()), builder.
                load(corv__ggyrs), builder.bitcast(dnpx__ukdm.data, lir.
                IntType(8).as_pointer()), sjbx__gstue.meminfo, dnpx__ukdm.
                meminfo, context.get_constant(types.int32, arr_type.
                precision), context.get_constant(types.int32, arr_type.scale)])
        else:
            wjwif__sws = lir.FunctionType(lir.IntType(8).as_pointer(), [lir
                .IntType(64), lir.IntType(8).as_pointer(), lir.IntType(32),
                lir.IntType(8).as_pointer(), lir.IntType(8).as_pointer(),
                lir.IntType(8).as_pointer()])
            fxltu__ldx = cgutils.get_or_insert_function(builder.module,
                wjwif__sws, name='nullable_array_to_info')
            return builder.call(fxltu__ldx, [yuhpt__xaf, builder.bitcast(
                sjbx__gstue.data, lir.IntType(8).as_pointer()), builder.
                load(corv__ggyrs), builder.bitcast(dnpx__ukdm.data, lir.
                IntType(8).as_pointer()), sjbx__gstue.meminfo, dnpx__ukdm.
                meminfo])
    if isinstance(arr_type, IntervalArrayType):
        assert isinstance(arr_type.arr_type, types.Array
            ), 'array_to_info(): only IntervalArrayType with Numpy arrays supported'
        arr = cgutils.create_struct_proxy(arr_type)(context, builder, in_arr)
        zxt__pis = context.make_array(arr_type.arr_type)(context, builder,
            arr.left)
        poxhe__iio = context.make_array(arr_type.arr_type)(context, builder,
            arr.right)
        yuhpt__xaf = builder.extract_value(zxt__pis.shape, 0)
        ocam__gex = numba_to_c_type(arr_type.arr_type.dtype)
        corv__ggyrs = cgutils.alloca_once_value(builder, lir.Constant(lir.
            IntType(32), ocam__gex))
        wjwif__sws = lir.FunctionType(lir.IntType(8).as_pointer(), [lir.
            IntType(64), lir.IntType(8).as_pointer(), lir.IntType(8).
            as_pointer(), lir.IntType(32), lir.IntType(8).as_pointer(), lir
            .IntType(8).as_pointer()])
        fxltu__ldx = cgutils.get_or_insert_function(builder.module,
            wjwif__sws, name='interval_array_to_info')
        return builder.call(fxltu__ldx, [yuhpt__xaf, builder.bitcast(
            zxt__pis.data, lir.IntType(8).as_pointer()), builder.bitcast(
            poxhe__iio.data, lir.IntType(8).as_pointer()), builder.load(
            corv__ggyrs), zxt__pis.meminfo, poxhe__iio.meminfo])
    raise_bodo_error(f'array_to_info(): array type {arr_type} is not supported'
        )


def _lower_info_to_array_numpy(arr_type, context, builder, in_info):
    assert arr_type.ndim == 1, 'only 1D array supported'
    arr = context.make_array(arr_type)(context, builder)
    eohj__rnpxf = cgutils.alloca_once(builder, lir.IntType(64))
    bij__lycu = cgutils.alloca_once(builder, lir.IntType(8).as_pointer())
    qamb__mclhh = cgutils.alloca_once(builder, lir.IntType(8).as_pointer())
    wjwif__sws = lir.FunctionType(lir.VoidType(), [lir.IntType(8).
        as_pointer(), lir.IntType(64).as_pointer(), lir.IntType(8).
        as_pointer().as_pointer(), lir.IntType(8).as_pointer().as_pointer()])
    fxltu__ldx = cgutils.get_or_insert_function(builder.module, wjwif__sws,
        name='info_to_numpy_array')
    builder.call(fxltu__ldx, [in_info, eohj__rnpxf, bij__lycu, qamb__mclhh])
    context.compile_internal(builder, lambda :
        check_and_propagate_cpp_exception(), types.none(), [])
    cut__nxn = context.get_value_type(types.intp)
    ilui__ycqxo = cgutils.pack_array(builder, [builder.load(eohj__rnpxf)],
        ty=cut__nxn)
    aqckb__ido = context.get_constant(types.intp, context.get_abi_sizeof(
        context.get_data_type(arr_type.dtype)))
    kqnpk__iswf = cgutils.pack_array(builder, [aqckb__ido], ty=cut__nxn)
    chct__adja = builder.bitcast(builder.load(bij__lycu), context.
        get_data_type(arr_type.dtype).as_pointer())
    numba.np.arrayobj.populate_array(arr, data=chct__adja, shape=
        ilui__ycqxo, strides=kqnpk__iswf, itemsize=aqckb__ido, meminfo=
        builder.load(qamb__mclhh))
    return arr._getvalue()


def _lower_info_to_array_list_string_array(arr_type, context, builder, in_info
    ):
    yuen__thkw = context.make_helper(builder, arr_type)
    wjwif__sws = lir.FunctionType(lir.VoidType(), [lir.IntType(8).
        as_pointer(), lir.IntType(8).as_pointer().as_pointer()])
    fxltu__ldx = cgutils.get_or_insert_function(builder.module, wjwif__sws,
        name='info_to_list_string_array')
    builder.call(fxltu__ldx, [in_info, yuen__thkw._get_ptr_by_name('meminfo')])
    context.compile_internal(builder, lambda :
        check_and_propagate_cpp_exception(), types.none(), [])
    return yuen__thkw._getvalue()


def nested_to_array(context, builder, arr_typ, lengths_ptr, array_infos_ptr,
    lengths_pos, infos_pos):
    yvmhr__vbq = context.get_data_type(array_info_type)
    if isinstance(arr_typ, ArrayItemArrayType):
        krb__fcjr = lengths_pos
        bxq__clzio = infos_pos
        omz__jtum, lengths_pos, infos_pos = nested_to_array(context,
            builder, arr_typ.dtype, lengths_ptr, array_infos_ptr, 
            lengths_pos + 1, infos_pos + 2)
        ptto__scm = ArrayItemArrayPayloadType(arr_typ)
        cepj__kbzzt = context.get_data_type(ptto__scm)
        aihfe__msr = context.get_abi_sizeof(cepj__kbzzt)
        jhwrp__khuaq = define_array_item_dtor(context, builder, arr_typ,
            ptto__scm)
        ojfyb__dwsrz = context.nrt.meminfo_alloc_dtor(builder, context.
            get_constant(types.uintp, aihfe__msr), jhwrp__khuaq)
        jupbk__onh = context.nrt.meminfo_data(builder, ojfyb__dwsrz)
        qykh__gibc = builder.bitcast(jupbk__onh, cepj__kbzzt.as_pointer())
        nmi__qcmh = cgutils.create_struct_proxy(ptto__scm)(context, builder)
        nmi__qcmh.n_arrays = builder.extract_value(builder.load(lengths_ptr
            ), krb__fcjr)
        nmi__qcmh.data = omz__jtum
        njy__fzujn = builder.load(array_infos_ptr)
        ggm__pagcm = builder.bitcast(builder.extract_value(njy__fzujn,
            bxq__clzio), yvmhr__vbq)
        nmi__qcmh.offsets = _lower_info_to_array_numpy(types.Array(
            offset_type, 1, 'C'), context, builder, ggm__pagcm)
        cmyx__tvo = builder.bitcast(builder.extract_value(njy__fzujn, 
            bxq__clzio + 1), yvmhr__vbq)
        nmi__qcmh.null_bitmap = _lower_info_to_array_numpy(types.Array(
            types.uint8, 1, 'C'), context, builder, cmyx__tvo)
        builder.store(nmi__qcmh._getvalue(), qykh__gibc)
        yirgt__ubal = context.make_helper(builder, arr_typ)
        yirgt__ubal.meminfo = ojfyb__dwsrz
        return yirgt__ubal._getvalue(), lengths_pos, infos_pos
    elif isinstance(arr_typ, StructArrayType):
        hma__bapzy = []
        bxq__clzio = infos_pos
        lengths_pos += 1
        infos_pos += 1
        for auo__vguvp in arr_typ.data:
            omz__jtum, lengths_pos, infos_pos = nested_to_array(context,
                builder, auo__vguvp, lengths_ptr, array_infos_ptr,
                lengths_pos, infos_pos)
            hma__bapzy.append(omz__jtum)
        ptto__scm = StructArrayPayloadType(arr_typ.data)
        cepj__kbzzt = context.get_value_type(ptto__scm)
        aihfe__msr = context.get_abi_sizeof(cepj__kbzzt)
        jhwrp__khuaq = define_struct_arr_dtor(context, builder, arr_typ,
            ptto__scm)
        ojfyb__dwsrz = context.nrt.meminfo_alloc_dtor(builder, context.
            get_constant(types.uintp, aihfe__msr), jhwrp__khuaq)
        jupbk__onh = context.nrt.meminfo_data(builder, ojfyb__dwsrz)
        qykh__gibc = builder.bitcast(jupbk__onh, cepj__kbzzt.as_pointer())
        nmi__qcmh = cgutils.create_struct_proxy(ptto__scm)(context, builder)
        nmi__qcmh.data = cgutils.pack_array(builder, hma__bapzy
            ) if types.is_homogeneous(*arr_typ.data) else cgutils.pack_struct(
            builder, hma__bapzy)
        njy__fzujn = builder.load(array_infos_ptr)
        cmyx__tvo = builder.bitcast(builder.extract_value(njy__fzujn,
            bxq__clzio), yvmhr__vbq)
        nmi__qcmh.null_bitmap = _lower_info_to_array_numpy(types.Array(
            types.uint8, 1, 'C'), context, builder, cmyx__tvo)
        builder.store(nmi__qcmh._getvalue(), qykh__gibc)
        tpm__xdgnp = context.make_helper(builder, arr_typ)
        tpm__xdgnp.meminfo = ojfyb__dwsrz
        return tpm__xdgnp._getvalue(), lengths_pos, infos_pos
    elif arr_typ in (string_array_type, binary_array_type):
        njy__fzujn = builder.load(array_infos_ptr)
        aez__wow = builder.bitcast(builder.extract_value(njy__fzujn,
            infos_pos), yvmhr__vbq)
        ingvw__hyy = context.make_helper(builder, arr_typ)
        vezg__dwkgo = ArrayItemArrayType(char_arr_type)
        yirgt__ubal = context.make_helper(builder, vezg__dwkgo)
        wjwif__sws = lir.FunctionType(lir.VoidType(), [lir.IntType(8).
            as_pointer(), lir.IntType(8).as_pointer().as_pointer()])
        fxltu__ldx = cgutils.get_or_insert_function(builder.module,
            wjwif__sws, name='info_to_string_array')
        builder.call(fxltu__ldx, [aez__wow, yirgt__ubal._get_ptr_by_name(
            'meminfo')])
        context.compile_internal(builder, lambda :
            check_and_propagate_cpp_exception(), types.none(), [])
        ingvw__hyy.data = yirgt__ubal._getvalue()
        return ingvw__hyy._getvalue(), lengths_pos + 1, infos_pos + 1
    elif isinstance(arr_typ, types.Array):
        njy__fzujn = builder.load(array_infos_ptr)
        smv__qee = builder.bitcast(builder.extract_value(njy__fzujn, 
            infos_pos + 1), yvmhr__vbq)
        return _lower_info_to_array_numpy(arr_typ, context, builder, smv__qee
            ), lengths_pos + 1, infos_pos + 2
    elif isinstance(arr_typ, (IntegerArrayType, DecimalArrayType)
        ) or arr_typ in (boolean_array, datetime_date_array_type):
        arr = cgutils.create_struct_proxy(arr_typ)(context, builder)
        nxap__mkjyp = arr_typ.dtype
        if isinstance(arr_typ, DecimalArrayType):
            nxap__mkjyp = int128_type
        elif arr_typ == datetime_date_array_type:
            nxap__mkjyp = types.int64
        njy__fzujn = builder.load(array_infos_ptr)
        cmyx__tvo = builder.bitcast(builder.extract_value(njy__fzujn,
            infos_pos), yvmhr__vbq)
        arr.null_bitmap = _lower_info_to_array_numpy(types.Array(types.
            uint8, 1, 'C'), context, builder, cmyx__tvo)
        smv__qee = builder.bitcast(builder.extract_value(njy__fzujn, 
            infos_pos + 1), yvmhr__vbq)
        arr.data = _lower_info_to_array_numpy(types.Array(nxap__mkjyp, 1,
            'C'), context, builder, smv__qee)
        return arr._getvalue(), lengths_pos + 1, infos_pos + 2


def info_to_array_codegen(context, builder, sig, args):
    array_type = sig.args[1]
    arr_type = array_type.instance_type if isinstance(array_type, types.TypeRef
        ) else array_type
    in_info, nuycx__qlkho = args
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
                return 1 + sum([get_num_arrays(auo__vguvp) for auo__vguvp in
                    arr_typ.data])
            else:
                return 1

        def get_num_infos(arr_typ):
            if isinstance(arr_typ, ArrayItemArrayType):
                return 2 + get_num_infos(arr_typ.dtype)
            elif isinstance(arr_typ, StructArrayType):
                return 1 + sum([get_num_infos(auo__vguvp) for auo__vguvp in
                    arr_typ.data])
            elif arr_typ in (string_array_type, binary_array_type):
                return 1
            else:
                return 2
        if isinstance(arr_type, TupleArrayType):
            sinw__hmv = StructArrayType(arr_type.data, ('dummy',) * len(
                arr_type.data))
        elif isinstance(arr_type, MapArrayType):
            sinw__hmv = _get_map_arr_data_type(arr_type)
        else:
            sinw__hmv = arr_type
        iqu__qqel = get_num_arrays(sinw__hmv)
        yxw__cqme = cgutils.pack_array(builder, [lir.Constant(lir.IntType(
            64), 0) for nuycx__qlkho in range(iqu__qqel)])
        lengths_ptr = cgutils.alloca_once_value(builder, yxw__cqme)
        xhxyx__hyz = lir.Constant(lir.IntType(8).as_pointer(), None)
        neusa__sqg = cgutils.pack_array(builder, [xhxyx__hyz for
            nuycx__qlkho in range(get_num_infos(sinw__hmv))])
        array_infos_ptr = cgutils.alloca_once_value(builder, neusa__sqg)
        wjwif__sws = lir.FunctionType(lir.VoidType(), [lir.IntType(8).
            as_pointer(), lir.IntType(64).as_pointer(), lir.IntType(8).
            as_pointer().as_pointer()])
        fxltu__ldx = cgutils.get_or_insert_function(builder.module,
            wjwif__sws, name='info_to_nested_array')
        builder.call(fxltu__ldx, [in_info, builder.bitcast(lengths_ptr, lir
            .IntType(64).as_pointer()), builder.bitcast(array_infos_ptr,
            lir.IntType(8).as_pointer().as_pointer())])
        context.compile_internal(builder, lambda :
            check_and_propagate_cpp_exception(), types.none(), [])
        arr, nuycx__qlkho, nuycx__qlkho = nested_to_array(context, builder,
            sinw__hmv, lengths_ptr, array_infos_ptr, 0, 0)
        if isinstance(arr_type, TupleArrayType):
            scg__qnbv = context.make_helper(builder, arr_type)
            scg__qnbv.data = arr
            context.nrt.incref(builder, sinw__hmv, arr)
            arr = scg__qnbv._getvalue()
        elif isinstance(arr_type, MapArrayType):
            sig = signature(arr_type, sinw__hmv)
            arr = init_map_arr_codegen(context, builder, sig, (arr,))
        return arr
    if arr_type in (string_array_type, binary_array_type):
        ingvw__hyy = context.make_helper(builder, arr_type)
        vezg__dwkgo = ArrayItemArrayType(char_arr_type)
        yirgt__ubal = context.make_helper(builder, vezg__dwkgo)
        wjwif__sws = lir.FunctionType(lir.VoidType(), [lir.IntType(8).
            as_pointer(), lir.IntType(8).as_pointer().as_pointer()])
        fxltu__ldx = cgutils.get_or_insert_function(builder.module,
            wjwif__sws, name='info_to_string_array')
        builder.call(fxltu__ldx, [in_info, yirgt__ubal._get_ptr_by_name(
            'meminfo')])
        context.compile_internal(builder, lambda :
            check_and_propagate_cpp_exception(), types.none(), [])
        ingvw__hyy.data = yirgt__ubal._getvalue()
        return ingvw__hyy._getvalue()
    if arr_type == bodo.dict_str_arr_type:
        wjwif__sws = lir.FunctionType(lir.IntType(8).as_pointer(), [lir.
            IntType(8).as_pointer(), lir.IntType(32)])
        fxltu__ldx = cgutils.get_or_insert_function(builder.module,
            wjwif__sws, name='get_nested_info')
        ximw__hqob = builder.call(fxltu__ldx, [in_info, lir.Constant(lir.
            IntType(32), 1)])
        qiuh__aflea = builder.call(fxltu__ldx, [in_info, lir.Constant(lir.
            IntType(32), 2)])
        yrb__ttok = context.make_helper(builder, arr_type)
        sig = arr_type.data(array_info_type, arr_type.data)
        yrb__ttok.data = info_to_array_codegen(context, builder, sig, (
            ximw__hqob, context.get_constant_null(arr_type.data)))
        wkuu__swkh = bodo.libs.dict_arr_ext.dict_indices_arr_type
        sig = wkuu__swkh(array_info_type, wkuu__swkh)
        yrb__ttok.indices = info_to_array_codegen(context, builder, sig, (
            qiuh__aflea, context.get_constant_null(wkuu__swkh)))
        wjwif__sws = lir.FunctionType(lir.IntType(32), [lir.IntType(8).
            as_pointer()])
        fxltu__ldx = cgutils.get_or_insert_function(builder.module,
            wjwif__sws, name='get_has_global_dictionary')
        ecuk__rliu = builder.call(fxltu__ldx, [in_info])
        yrb__ttok.has_global_dictionary = builder.trunc(ecuk__rliu, cgutils
            .bool_t)
        return yrb__ttok._getvalue()
    if isinstance(arr_type, CategoricalArrayType):
        out_arr = cgutils.create_struct_proxy(arr_type)(context, builder)
        vzfy__ysshb = get_categories_int_type(arr_type.dtype)
        zbltu__itda = types.Array(vzfy__ysshb, 1, 'C')
        out_arr.codes = _lower_info_to_array_numpy(zbltu__itda, context,
            builder, in_info)
        if isinstance(array_type, types.TypeRef):
            assert arr_type.dtype.categories is not None, 'info_to_array: unknown categories'
            is_ordered = arr_type.dtype.ordered
            hnuav__kip = pd.CategoricalDtype(arr_type.dtype.categories,
                is_ordered).categories.values
            new_cats_tup = MetaType(tuple(hnuav__kip))
            int_type = arr_type.dtype.int_type
            uvmhy__ongjx = bodo.typeof(hnuav__kip)
            wssal__etfy = context.get_constant_generic(builder,
                uvmhy__ongjx, hnuav__kip)
            gjwbn__tyssd = context.compile_internal(builder, lambda c_arr:
                bodo.hiframes.pd_categorical_ext.init_cat_dtype(bodo.utils.
                conversion.index_from_array(c_arr), is_ordered, int_type,
                new_cats_tup), arr_type.dtype(uvmhy__ongjx), [wssal__etfy])
        else:
            gjwbn__tyssd = cgutils.create_struct_proxy(arr_type)(context,
                builder, args[1]).dtype
            context.nrt.incref(builder, arr_type.dtype, gjwbn__tyssd)
        out_arr.dtype = gjwbn__tyssd
        return out_arr._getvalue()
    if isinstance(arr_type, bodo.DatetimeArrayType):
        arr = cgutils.create_struct_proxy(arr_type)(context, builder)
        chct__adja = _lower_info_to_array_numpy(arr_type.data_array_type,
            context, builder, in_info)
        arr.data = chct__adja
        return arr._getvalue()
    if isinstance(arr_type, types.Array):
        return _lower_info_to_array_numpy(arr_type, context, builder, in_info)
    if isinstance(arr_type, (IntegerArrayType, DecimalArrayType)
        ) or arr_type in (boolean_array, datetime_date_array_type):
        arr = cgutils.create_struct_proxy(arr_type)(context, builder)
        nxap__mkjyp = arr_type.dtype
        if isinstance(arr_type, DecimalArrayType):
            nxap__mkjyp = int128_type
        elif arr_type == datetime_date_array_type:
            nxap__mkjyp = types.int64
        hfmr__pfest = types.Array(nxap__mkjyp, 1, 'C')
        sjbx__gstue = context.make_array(hfmr__pfest)(context, builder)
        pefvz__hrfpy = types.Array(types.uint8, 1, 'C')
        reizk__tjmc = context.make_array(pefvz__hrfpy)(context, builder)
        eohj__rnpxf = cgutils.alloca_once(builder, lir.IntType(64))
        xmkoy__pkw = cgutils.alloca_once(builder, lir.IntType(64))
        bij__lycu = cgutils.alloca_once(builder, lir.IntType(8).as_pointer())
        pff__ihc = cgutils.alloca_once(builder, lir.IntType(8).as_pointer())
        qamb__mclhh = cgutils.alloca_once(builder, lir.IntType(8).as_pointer())
        tfchs__hpad = cgutils.alloca_once(builder, lir.IntType(8).as_pointer())
        wjwif__sws = lir.FunctionType(lir.VoidType(), [lir.IntType(8).
            as_pointer(), lir.IntType(64).as_pointer(), lir.IntType(64).
            as_pointer(), lir.IntType(8).as_pointer().as_pointer(), lir.
            IntType(8).as_pointer().as_pointer(), lir.IntType(8).as_pointer
            ().as_pointer(), lir.IntType(8).as_pointer().as_pointer()])
        fxltu__ldx = cgutils.get_or_insert_function(builder.module,
            wjwif__sws, name='info_to_nullable_array')
        builder.call(fxltu__ldx, [in_info, eohj__rnpxf, xmkoy__pkw,
            bij__lycu, pff__ihc, qamb__mclhh, tfchs__hpad])
        context.compile_internal(builder, lambda :
            check_and_propagate_cpp_exception(), types.none(), [])
        cut__nxn = context.get_value_type(types.intp)
        ilui__ycqxo = cgutils.pack_array(builder, [builder.load(eohj__rnpxf
            )], ty=cut__nxn)
        aqckb__ido = context.get_constant(types.intp, context.
            get_abi_sizeof(context.get_data_type(nxap__mkjyp)))
        kqnpk__iswf = cgutils.pack_array(builder, [aqckb__ido], ty=cut__nxn)
        chct__adja = builder.bitcast(builder.load(bij__lycu), context.
            get_data_type(nxap__mkjyp).as_pointer())
        numba.np.arrayobj.populate_array(sjbx__gstue, data=chct__adja,
            shape=ilui__ycqxo, strides=kqnpk__iswf, itemsize=aqckb__ido,
            meminfo=builder.load(qamb__mclhh))
        arr.data = sjbx__gstue._getvalue()
        ilui__ycqxo = cgutils.pack_array(builder, [builder.load(xmkoy__pkw)
            ], ty=cut__nxn)
        aqckb__ido = context.get_constant(types.intp, context.
            get_abi_sizeof(context.get_data_type(types.uint8)))
        kqnpk__iswf = cgutils.pack_array(builder, [aqckb__ido], ty=cut__nxn)
        chct__adja = builder.bitcast(builder.load(pff__ihc), context.
            get_data_type(types.uint8).as_pointer())
        numba.np.arrayobj.populate_array(reizk__tjmc, data=chct__adja,
            shape=ilui__ycqxo, strides=kqnpk__iswf, itemsize=aqckb__ido,
            meminfo=builder.load(tfchs__hpad))
        arr.null_bitmap = reizk__tjmc._getvalue()
        return arr._getvalue()
    if isinstance(arr_type, IntervalArrayType):
        arr = cgutils.create_struct_proxy(arr_type)(context, builder)
        zxt__pis = context.make_array(arr_type.arr_type)(context, builder)
        poxhe__iio = context.make_array(arr_type.arr_type)(context, builder)
        eohj__rnpxf = cgutils.alloca_once(builder, lir.IntType(64))
        twyb__ihdar = cgutils.alloca_once(builder, lir.IntType(8).as_pointer())
        cvd__yebg = cgutils.alloca_once(builder, lir.IntType(8).as_pointer())
        ums__dct = cgutils.alloca_once(builder, lir.IntType(8).as_pointer())
        omxzk__etb = cgutils.alloca_once(builder, lir.IntType(8).as_pointer())
        wjwif__sws = lir.FunctionType(lir.VoidType(), [lir.IntType(8).
            as_pointer(), lir.IntType(64).as_pointer(), lir.IntType(8).
            as_pointer().as_pointer(), lir.IntType(8).as_pointer().
            as_pointer(), lir.IntType(8).as_pointer().as_pointer(), lir.
            IntType(8).as_pointer().as_pointer()])
        fxltu__ldx = cgutils.get_or_insert_function(builder.module,
            wjwif__sws, name='info_to_interval_array')
        builder.call(fxltu__ldx, [in_info, eohj__rnpxf, twyb__ihdar,
            cvd__yebg, ums__dct, omxzk__etb])
        context.compile_internal(builder, lambda :
            check_and_propagate_cpp_exception(), types.none(), [])
        cut__nxn = context.get_value_type(types.intp)
        ilui__ycqxo = cgutils.pack_array(builder, [builder.load(eohj__rnpxf
            )], ty=cut__nxn)
        aqckb__ido = context.get_constant(types.intp, context.
            get_abi_sizeof(context.get_data_type(arr_type.arr_type.dtype)))
        kqnpk__iswf = cgutils.pack_array(builder, [aqckb__ido], ty=cut__nxn)
        najc__iclcb = builder.bitcast(builder.load(twyb__ihdar), context.
            get_data_type(arr_type.arr_type.dtype).as_pointer())
        numba.np.arrayobj.populate_array(zxt__pis, data=najc__iclcb, shape=
            ilui__ycqxo, strides=kqnpk__iswf, itemsize=aqckb__ido, meminfo=
            builder.load(ums__dct))
        arr.left = zxt__pis._getvalue()
        xlqai__wcx = builder.bitcast(builder.load(cvd__yebg), context.
            get_data_type(arr_type.arr_type.dtype).as_pointer())
        numba.np.arrayobj.populate_array(poxhe__iio, data=xlqai__wcx, shape
            =ilui__ycqxo, strides=kqnpk__iswf, itemsize=aqckb__ido, meminfo
            =builder.load(omxzk__etb))
        arr.right = poxhe__iio._getvalue()
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
        yuhpt__xaf, nuycx__qlkho = args
        ocam__gex = numba_to_c_type(array_type.dtype)
        corv__ggyrs = cgutils.alloca_once_value(builder, lir.Constant(lir.
            IntType(32), ocam__gex))
        wjwif__sws = lir.FunctionType(lir.IntType(8).as_pointer(), [lir.
            IntType(64), lir.IntType(32)])
        fxltu__ldx = cgutils.get_or_insert_function(builder.module,
            wjwif__sws, name='alloc_numpy')
        return builder.call(fxltu__ldx, [yuhpt__xaf, builder.load(corv__ggyrs)]
            )
    return array_info_type(len_typ, arr_type), codegen


@intrinsic
def test_alloc_string(typingctx, len_typ, n_chars_typ):

    def codegen(context, builder, sig, args):
        yuhpt__xaf, idsuh__bhv = args
        wjwif__sws = lir.FunctionType(lir.IntType(8).as_pointer(), [lir.
            IntType(64), lir.IntType(64)])
        fxltu__ldx = cgutils.get_or_insert_function(builder.module,
            wjwif__sws, name='alloc_string_array')
        return builder.call(fxltu__ldx, [yuhpt__xaf, idsuh__bhv])
    return array_info_type(len_typ, n_chars_typ), codegen


@intrinsic
def arr_info_list_to_table(typingctx, list_arr_info_typ=None):
    assert list_arr_info_typ == types.List(array_info_type)
    return table_type(list_arr_info_typ), arr_info_list_to_table_codegen


def arr_info_list_to_table_codegen(context, builder, sig, args):
    dseh__xvnt, = args
    rzelx__auk = numba.cpython.listobj.ListInstance(context, builder, sig.
        args[0], dseh__xvnt)
    wjwif__sws = lir.FunctionType(lir.IntType(8).as_pointer(), [lir.IntType
        (8).as_pointer().as_pointer(), lir.IntType(64)])
    fxltu__ldx = cgutils.get_or_insert_function(builder.module, wjwif__sws,
        name='arr_info_list_to_table')
    return builder.call(fxltu__ldx, [rzelx__auk.data, rzelx__auk.size])


@intrinsic
def info_from_table(typingctx, table_t, ind_t):

    def codegen(context, builder, sig, args):
        wjwif__sws = lir.FunctionType(lir.IntType(8).as_pointer(), [lir.
            IntType(8).as_pointer(), lir.IntType(64)])
        fxltu__ldx = cgutils.get_or_insert_function(builder.module,
            wjwif__sws, name='info_from_table')
        return builder.call(fxltu__ldx, args)
    return array_info_type(table_t, ind_t), codegen


@intrinsic
def cpp_table_to_py_table(typingctx, cpp_table_t, table_idx_arr_t,
    py_table_type_t):
    assert cpp_table_t == table_type, 'invalid cpp table type'
    assert isinstance(table_idx_arr_t, types.Array
        ) and table_idx_arr_t.dtype == types.int64, 'invalid table index array'
    assert isinstance(py_table_type_t, types.TypeRef), 'invalid py table ref'
    bzrqx__ysro = py_table_type_t.instance_type

    def codegen(context, builder, sig, args):
        rudh__bat, fqkyo__hhlpo, nuycx__qlkho = args
        wjwif__sws = lir.FunctionType(lir.IntType(8).as_pointer(), [lir.
            IntType(8).as_pointer(), lir.IntType(64)])
        fxltu__ldx = cgutils.get_or_insert_function(builder.module,
            wjwif__sws, name='info_from_table')
        ovh__iqpyg = cgutils.create_struct_proxy(bzrqx__ysro)(context, builder)
        ovh__iqpyg.parent = cgutils.get_null_value(ovh__iqpyg.parent.type)
        klr__ryof = context.make_array(table_idx_arr_t)(context, builder,
            fqkyo__hhlpo)
        xevi__bptde = context.get_constant(types.int64, -1)
        blffo__nxdo = context.get_constant(types.int64, 0)
        veoaj__yqws = cgutils.alloca_once_value(builder, blffo__nxdo)
        for t, qfwyv__exhvx in bzrqx__ysro.type_to_blk.items():
            gsvt__qxqgd = context.get_constant(types.int64, len(bzrqx__ysro
                .block_to_arr_ind[qfwyv__exhvx]))
            nuycx__qlkho, rls__oshiz = ListInstance.allocate_ex(context,
                builder, types.List(t), gsvt__qxqgd)
            rls__oshiz.size = gsvt__qxqgd
            hvpy__acnqh = context.make_constant_array(builder, types.Array(
                types.int64, 1, 'C'), np.array(bzrqx__ysro.block_to_arr_ind
                [qfwyv__exhvx], dtype=np.int64))
            nrhf__dcyei = context.make_array(types.Array(types.int64, 1, 'C'))(
                context, builder, hvpy__acnqh)
            with cgutils.for_range(builder, gsvt__qxqgd) as sqj__cvde:
                ubv__glkot = sqj__cvde.index
                hhrga__otanh = _getitem_array_single_int(context, builder,
                    types.int64, types.Array(types.int64, 1, 'C'),
                    nrhf__dcyei, ubv__glkot)
                eziym__lypl = _getitem_array_single_int(context, builder,
                    types.int64, table_idx_arr_t, klr__ryof, hhrga__otanh)
                tll__fdu = builder.icmp_unsigned('!=', eziym__lypl, xevi__bptde
                    )
                with builder.if_else(tll__fdu) as (ttc__wirxv, vganr__aoin):
                    with ttc__wirxv:
                        hcqm__hyws = builder.call(fxltu__ldx, [rudh__bat,
                            eziym__lypl])
                        arr = context.compile_internal(builder, lambda info:
                            info_to_array(info, t), t(array_info_type), [
                            hcqm__hyws])
                        rls__oshiz.inititem(ubv__glkot, arr, incref=False)
                        yuhpt__xaf = context.compile_internal(builder, lambda
                            arr: len(arr), types.int64(t), [arr])
                        builder.store(yuhpt__xaf, veoaj__yqws)
                    with vganr__aoin:
                        ttdbw__nfgd = context.get_constant_null(t)
                        rls__oshiz.inititem(ubv__glkot, ttdbw__nfgd, incref
                            =False)
            setattr(ovh__iqpyg, f'block_{qfwyv__exhvx}', rls__oshiz.value)
        ovh__iqpyg.len = builder.load(veoaj__yqws)
        return ovh__iqpyg._getvalue()
    return bzrqx__ysro(cpp_table_t, table_idx_arr_t, py_table_type_t), codegen


@intrinsic
def py_table_to_cpp_table(typingctx, py_table_t, py_table_type_t):
    assert isinstance(py_table_t, bodo.hiframes.table.TableType
        ), 'invalid py table type'
    assert isinstance(py_table_type_t, types.TypeRef), 'invalid py table ref'
    bzrqx__ysro = py_table_type_t.instance_type

    def codegen(context, builder, sig, args):
        bpo__fzz, nuycx__qlkho = args
        vdmun__zpxon = cgutils.create_struct_proxy(bzrqx__ysro)(context,
            builder, bpo__fzz)
        if bzrqx__ysro.has_runtime_cols:
            hmvp__dtc = lir.Constant(lir.IntType(64), 0)
            for qfwyv__exhvx, t in enumerate(bzrqx__ysro.arr_types):
                zcmsl__ajq = getattr(vdmun__zpxon, f'block_{qfwyv__exhvx}')
                adng__tohzk = ListInstance(context, builder, types.List(t),
                    zcmsl__ajq)
                hmvp__dtc = builder.add(hmvp__dtc, adng__tohzk.size)
        else:
            hmvp__dtc = lir.Constant(lir.IntType(64), len(bzrqx__ysro.
                arr_types))
        nuycx__qlkho, ajksy__gidb = ListInstance.allocate_ex(context,
            builder, types.List(array_info_type), hmvp__dtc)
        ajksy__gidb.size = hmvp__dtc
        if bzrqx__ysro.has_runtime_cols:
            xym__wbmq = lir.Constant(lir.IntType(64), 0)
            for qfwyv__exhvx, t in enumerate(bzrqx__ysro.arr_types):
                zcmsl__ajq = getattr(vdmun__zpxon, f'block_{qfwyv__exhvx}')
                adng__tohzk = ListInstance(context, builder, types.List(t),
                    zcmsl__ajq)
                gsvt__qxqgd = adng__tohzk.size
                with cgutils.for_range(builder, gsvt__qxqgd) as sqj__cvde:
                    ubv__glkot = sqj__cvde.index
                    arr = adng__tohzk.getitem(ubv__glkot)
                    jzad__feigj = signature(array_info_type, t)
                    eszq__ohnf = arr,
                    qsz__jvg = array_to_info_codegen(context, builder,
                        jzad__feigj, eszq__ohnf)
                    ajksy__gidb.inititem(builder.add(xym__wbmq, ubv__glkot),
                        qsz__jvg, incref=False)
                xym__wbmq = builder.add(xym__wbmq, gsvt__qxqgd)
        else:
            for t, qfwyv__exhvx in bzrqx__ysro.type_to_blk.items():
                gsvt__qxqgd = context.get_constant(types.int64, len(
                    bzrqx__ysro.block_to_arr_ind[qfwyv__exhvx]))
                zcmsl__ajq = getattr(vdmun__zpxon, f'block_{qfwyv__exhvx}')
                adng__tohzk = ListInstance(context, builder, types.List(t),
                    zcmsl__ajq)
                hvpy__acnqh = context.make_constant_array(builder, types.
                    Array(types.int64, 1, 'C'), np.array(bzrqx__ysro.
                    block_to_arr_ind[qfwyv__exhvx], dtype=np.int64))
                nrhf__dcyei = context.make_array(types.Array(types.int64, 1,
                    'C'))(context, builder, hvpy__acnqh)
                with cgutils.for_range(builder, gsvt__qxqgd) as sqj__cvde:
                    ubv__glkot = sqj__cvde.index
                    hhrga__otanh = _getitem_array_single_int(context,
                        builder, types.int64, types.Array(types.int64, 1,
                        'C'), nrhf__dcyei, ubv__glkot)
                    zhpi__giw = signature(types.none, bzrqx__ysro, types.
                        List(t), types.int64, types.int64)
                    vnx__vfhm = bpo__fzz, zcmsl__ajq, ubv__glkot, hhrga__otanh
                    bodo.hiframes.table.ensure_column_unboxed_codegen(context,
                        builder, zhpi__giw, vnx__vfhm)
                    arr = adng__tohzk.getitem(ubv__glkot)
                    jzad__feigj = signature(array_info_type, t)
                    eszq__ohnf = arr,
                    qsz__jvg = array_to_info_codegen(context, builder,
                        jzad__feigj, eszq__ohnf)
                    ajksy__gidb.inititem(hhrga__otanh, qsz__jvg, incref=False)
        deve__ppg = ajksy__gidb.value
        pfx__uwzm = signature(table_type, types.List(array_info_type))
        pbp__gxe = deve__ppg,
        rudh__bat = arr_info_list_to_table_codegen(context, builder,
            pfx__uwzm, pbp__gxe)
        context.nrt.decref(builder, types.List(array_info_type), deve__ppg)
        return rudh__bat
    return table_type(bzrqx__ysro, py_table_type_t), codegen


delete_info_decref_array = types.ExternalFunction('delete_info_decref_array',
    types.void(array_info_type))
delete_table_decref_arrays = types.ExternalFunction(
    'delete_table_decref_arrays', types.void(table_type))


@intrinsic
def delete_table(typingctx, table_t=None):
    assert table_t == table_type

    def codegen(context, builder, sig, args):
        wjwif__sws = lir.FunctionType(lir.VoidType(), [lir.IntType(8).
            as_pointer()])
        fxltu__ldx = cgutils.get_or_insert_function(builder.module,
            wjwif__sws, name='delete_table')
        builder.call(fxltu__ldx, args)
    return types.void(table_t), codegen


@intrinsic
def shuffle_table(typingctx, table_t, n_keys_t, _is_parallel, keep_comm_info_t
    ):
    assert table_t == table_type

    def codegen(context, builder, sig, args):
        wjwif__sws = lir.FunctionType(lir.IntType(8).as_pointer(), [lir.
            IntType(8).as_pointer(), lir.IntType(64), lir.IntType(1), lir.
            IntType(32)])
        fxltu__ldx = cgutils.get_or_insert_function(builder.module,
            wjwif__sws, name='shuffle_table')
        sxo__etrbh = builder.call(fxltu__ldx, args)
        context.compile_internal(builder, lambda :
            check_and_propagate_cpp_exception(), types.none(), [])
        return sxo__etrbh
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
        wjwif__sws = lir.FunctionType(lir.VoidType(), [lir.IntType(8).
            as_pointer()])
        fxltu__ldx = cgutils.get_or_insert_function(builder.module,
            wjwif__sws, name='delete_shuffle_info')
        return builder.call(fxltu__ldx, args)
    return types.void(shuffle_info_t), codegen


@intrinsic
def reverse_shuffle_table(typingctx, table_t, shuffle_info_t=None):

    def codegen(context, builder, sig, args):
        if sig.args[-1] == types.none:
            return context.get_constant_null(table_type)
        wjwif__sws = lir.FunctionType(lir.IntType(8).as_pointer(), [lir.
            IntType(8).as_pointer(), lir.IntType(8).as_pointer()])
        fxltu__ldx = cgutils.get_or_insert_function(builder.module,
            wjwif__sws, name='reverse_shuffle_table')
        return builder.call(fxltu__ldx, args)
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
        wjwif__sws = lir.FunctionType(lir.IntType(8).as_pointer(), [lir.
            IntType(8).as_pointer(), lir.IntType(8).as_pointer(), lir.
            IntType(1), lir.IntType(1), lir.IntType(64), lir.IntType(64),
            lir.IntType(64), lir.IntType(8).as_pointer(), lir.IntType(8).
            as_pointer(), lir.IntType(1), lir.IntType(1), lir.IntType(1),
            lir.IntType(1), lir.IntType(1), lir.IntType(1), lir.IntType(8).
            as_pointer(), lir.IntType(8).as_pointer(), lir.IntType(64), lir
            .IntType(8).as_pointer(), lir.IntType(64)])
        fxltu__ldx = cgutils.get_or_insert_function(builder.module,
            wjwif__sws, name='hash_join_table')
        sxo__etrbh = builder.call(fxltu__ldx, args)
        context.compile_internal(builder, lambda :
            check_and_propagate_cpp_exception(), types.none(), [])
        return sxo__etrbh
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
        wjwif__sws = lir.FunctionType(lir.IntType(8).as_pointer(), [lir.
            IntType(8).as_pointer(), lir.IntType(64), lir.IntType(8).
            as_pointer(), lir.IntType(8).as_pointer(), lir.IntType(1)])
        fxltu__ldx = cgutils.get_or_insert_function(builder.module,
            wjwif__sws, name='sort_values_table')
        sxo__etrbh = builder.call(fxltu__ldx, args)
        context.compile_internal(builder, lambda :
            check_and_propagate_cpp_exception(), types.none(), [])
        return sxo__etrbh
    return table_type(table_t, types.int64, types.voidptr, types.voidptr,
        types.boolean), codegen


@intrinsic
def sample_table(typingctx, table_t, n_keys_t, frac_t, replace_t, parallel_t):
    assert table_t == table_type

    def codegen(context, builder, sig, args):
        wjwif__sws = lir.FunctionType(lir.IntType(8).as_pointer(), [lir.
            IntType(8).as_pointer(), lir.IntType(64), lir.DoubleType(), lir
            .IntType(1), lir.IntType(1)])
        fxltu__ldx = cgutils.get_or_insert_function(builder.module,
            wjwif__sws, name='sample_table')
        sxo__etrbh = builder.call(fxltu__ldx, args)
        context.compile_internal(builder, lambda :
            check_and_propagate_cpp_exception(), types.none(), [])
        return sxo__etrbh
    return table_type(table_t, types.int64, types.float64, types.boolean,
        types.boolean), codegen


@intrinsic
def shuffle_renormalization(typingctx, table_t, random_t, random_seed_t,
    is_parallel_t):
    assert table_t == table_type

    def codegen(context, builder, sig, args):
        wjwif__sws = lir.FunctionType(lir.IntType(8).as_pointer(), [lir.
            IntType(8).as_pointer(), lir.IntType(32), lir.IntType(64), lir.
            IntType(1)])
        fxltu__ldx = cgutils.get_or_insert_function(builder.module,
            wjwif__sws, name='shuffle_renormalization')
        sxo__etrbh = builder.call(fxltu__ldx, args)
        context.compile_internal(builder, lambda :
            check_and_propagate_cpp_exception(), types.none(), [])
        return sxo__etrbh
    return table_type(table_t, types.int32, types.int64, types.boolean
        ), codegen


@intrinsic
def shuffle_renormalization_group(typingctx, table_t, random_t,
    random_seed_t, is_parallel_t, num_ranks_t, ranks_t):
    assert table_t == table_type

    def codegen(context, builder, sig, args):
        wjwif__sws = lir.FunctionType(lir.IntType(8).as_pointer(), [lir.
            IntType(8).as_pointer(), lir.IntType(32), lir.IntType(64), lir.
            IntType(1), lir.IntType(64), lir.IntType(8).as_pointer()])
        fxltu__ldx = cgutils.get_or_insert_function(builder.module,
            wjwif__sws, name='shuffle_renormalization_group')
        sxo__etrbh = builder.call(fxltu__ldx, args)
        context.compile_internal(builder, lambda :
            check_and_propagate_cpp_exception(), types.none(), [])
        return sxo__etrbh
    return table_type(table_t, types.int32, types.int64, types.boolean,
        types.int64, types.voidptr), codegen


@intrinsic
def drop_duplicates_table(typingctx, table_t, parallel_t, nkey_t, keep_t,
    dropna, drop_local_first):
    assert table_t == table_type

    def codegen(context, builder, sig, args):
        wjwif__sws = lir.FunctionType(lir.IntType(8).as_pointer(), [lir.
            IntType(8).as_pointer(), lir.IntType(1), lir.IntType(64), lir.
            IntType(64), lir.IntType(1), lir.IntType(1)])
        fxltu__ldx = cgutils.get_or_insert_function(builder.module,
            wjwif__sws, name='drop_duplicates_table')
        sxo__etrbh = builder.call(fxltu__ldx, args)
        context.compile_internal(builder, lambda :
            check_and_propagate_cpp_exception(), types.none(), [])
        return sxo__etrbh
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
        wjwif__sws = lir.FunctionType(lir.IntType(8).as_pointer(), [lir.
            IntType(8).as_pointer(), lir.IntType(64), lir.IntType(8).
            as_pointer(), lir.IntType(8).as_pointer(), lir.IntType(1), lir.
            IntType(8).as_pointer(), lir.IntType(8).as_pointer(), lir.
            IntType(8).as_pointer(), lir.IntType(1), lir.IntType(1), lir.
            IntType(1), lir.IntType(1), lir.IntType(1), lir.IntType(8).
            as_pointer(), lir.IntType(8).as_pointer(), lir.IntType(8).
            as_pointer(), lir.IntType(8).as_pointer()])
        fxltu__ldx = cgutils.get_or_insert_function(builder.module,
            wjwif__sws, name='pivot_groupby_and_aggregate')
        sxo__etrbh = builder.call(fxltu__ldx, args)
        context.compile_internal(builder, lambda :
            check_and_propagate_cpp_exception(), types.none(), [])
        return sxo__etrbh
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
        wjwif__sws = lir.FunctionType(lir.IntType(8).as_pointer(), [lir.
            IntType(8).as_pointer(), lir.IntType(64), lir.IntType(1), lir.
            IntType(8).as_pointer(), lir.IntType(8).as_pointer(), lir.
            IntType(8).as_pointer(), lir.IntType(1), lir.IntType(1), lir.
            IntType(64), lir.IntType(64), lir.IntType(64), lir.IntType(1),
            lir.IntType(1), lir.IntType(1), lir.IntType(8).as_pointer(),
            lir.IntType(8).as_pointer(), lir.IntType(8).as_pointer(), lir.
            IntType(8).as_pointer(), lir.IntType(8).as_pointer()])
        fxltu__ldx = cgutils.get_or_insert_function(builder.module,
            wjwif__sws, name='groupby_and_aggregate')
        sxo__etrbh = builder.call(fxltu__ldx, args)
        context.compile_internal(builder, lambda :
            check_and_propagate_cpp_exception(), types.none(), [])
        return sxo__etrbh
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
    whtfa__jvm = array_to_info(in_arr)
    uwnrk__gqz = array_to_info(in_values)
    dsf__pmq = array_to_info(out_arr)
    kgyel__apad = arr_info_list_to_table([whtfa__jvm, uwnrk__gqz, dsf__pmq])
    _array_isin(dsf__pmq, whtfa__jvm, uwnrk__gqz, is_parallel)
    check_and_propagate_cpp_exception()
    delete_table(kgyel__apad)


_get_search_regex = types.ExternalFunction('get_search_regex', types.void(
    array_info_type, types.bool_, types.voidptr, array_info_type))


@numba.njit(no_cpython_wrapper=True)
def get_search_regex(in_arr, case, pat, out_arr):
    in_arr = decode_if_dict_array(in_arr)
    whtfa__jvm = array_to_info(in_arr)
    dsf__pmq = array_to_info(out_arr)
    _get_search_regex(whtfa__jvm, case, pat, dsf__pmq)
    check_and_propagate_cpp_exception()


def _gen_row_access_intrinsic(col_array_typ, c_ind):
    from llvmlite import ir as lir
    vbvp__ywawt = col_array_typ.dtype
    if isinstance(vbvp__ywawt, types.Number) or vbvp__ywawt in [bodo.
        datetime_date_type, bodo.datetime64ns, bodo.timedelta64ns, types.bool_
        ]:

        @intrinsic
        def getitem_func(typingctx, table_t, ind_t):

            def codegen(context, builder, sig, args):
                ovh__iqpyg, wetd__nmmg = args
                ovh__iqpyg = builder.bitcast(ovh__iqpyg, lir.IntType(8).
                    as_pointer().as_pointer())
                aybpe__kds = lir.Constant(lir.IntType(64), c_ind)
                fog__esyl = builder.load(builder.gep(ovh__iqpyg, [aybpe__kds]))
                fog__esyl = builder.bitcast(fog__esyl, context.
                    get_data_type(vbvp__ywawt).as_pointer())
                return builder.load(builder.gep(fog__esyl, [wetd__nmmg]))
            return vbvp__ywawt(types.voidptr, types.int64), codegen
        return getitem_func
    if col_array_typ == bodo.string_array_type:

        @intrinsic
        def getitem_func(typingctx, table_t, ind_t):

            def codegen(context, builder, sig, args):
                ovh__iqpyg, wetd__nmmg = args
                ovh__iqpyg = builder.bitcast(ovh__iqpyg, lir.IntType(8).
                    as_pointer().as_pointer())
                aybpe__kds = lir.Constant(lir.IntType(64), c_ind)
                fog__esyl = builder.load(builder.gep(ovh__iqpyg, [aybpe__kds]))
                wjwif__sws = lir.FunctionType(lir.IntType(8).as_pointer(),
                    [lir.IntType(8).as_pointer(), lir.IntType(64), lir.
                    IntType(64).as_pointer()])
                nfk__wrh = cgutils.get_or_insert_function(builder.module,
                    wjwif__sws, name='array_info_getitem')
                szj__iomh = cgutils.alloca_once(builder, lir.IntType(64))
                args = fog__esyl, wetd__nmmg, szj__iomh
                bij__lycu = builder.call(nfk__wrh, args)
                return context.make_tuple(builder, sig.return_type, [
                    bij__lycu, builder.load(szj__iomh)])
            return types.Tuple([types.voidptr, types.int64])(types.voidptr,
                types.int64), codegen
        return getitem_func
    if col_array_typ == bodo.libs.dict_arr_ext.dict_str_arr_type:

        @intrinsic
        def getitem_func(typingctx, table_t, ind_t):

            def codegen(context, builder, sig, args):
                arpx__yhfk = lir.Constant(lir.IntType(64), 1)
                iyoyy__vdbhr = lir.Constant(lir.IntType(64), 2)
                ovh__iqpyg, wetd__nmmg = args
                ovh__iqpyg = builder.bitcast(ovh__iqpyg, lir.IntType(8).
                    as_pointer().as_pointer())
                aybpe__kds = lir.Constant(lir.IntType(64), c_ind)
                fog__esyl = builder.load(builder.gep(ovh__iqpyg, [aybpe__kds]))
                wjwif__sws = lir.FunctionType(lir.IntType(8).as_pointer(),
                    [lir.IntType(8).as_pointer(), lir.IntType(64)])
                oibwh__zqk = cgutils.get_or_insert_function(builder.module,
                    wjwif__sws, name='get_nested_info')
                args = fog__esyl, iyoyy__vdbhr
                gdpry__isijf = builder.call(oibwh__zqk, args)
                wjwif__sws = lir.FunctionType(lir.IntType(8).as_pointer(),
                    [lir.IntType(8).as_pointer()])
                svhx__ebye = cgutils.get_or_insert_function(builder.module,
                    wjwif__sws, name='array_info_getdata1')
                args = gdpry__isijf,
                ktlin__nzia = builder.call(svhx__ebye, args)
                ktlin__nzia = builder.bitcast(ktlin__nzia, context.
                    get_data_type(col_array_typ.indices_dtype).as_pointer())
                hkk__mwxwy = builder.sext(builder.load(builder.gep(
                    ktlin__nzia, [wetd__nmmg])), lir.IntType(64))
                args = fog__esyl, arpx__yhfk
                mge__uizv = builder.call(oibwh__zqk, args)
                wjwif__sws = lir.FunctionType(lir.IntType(8).as_pointer(),
                    [lir.IntType(8).as_pointer(), lir.IntType(64), lir.
                    IntType(64).as_pointer()])
                nfk__wrh = cgutils.get_or_insert_function(builder.module,
                    wjwif__sws, name='array_info_getitem')
                szj__iomh = cgutils.alloca_once(builder, lir.IntType(64))
                args = mge__uizv, hkk__mwxwy, szj__iomh
                bij__lycu = builder.call(nfk__wrh, args)
                return context.make_tuple(builder, sig.return_type, [
                    bij__lycu, builder.load(szj__iomh)])
            return types.Tuple([types.voidptr, types.int64])(types.voidptr,
                types.int64), codegen
        return getitem_func
    raise BodoError(
        f"General Join Conditions with '{vbvp__ywawt}' column data type not supported"
        )


def _gen_row_na_check_intrinsic(col_array_dtype, c_ind):
    if (isinstance(col_array_dtype, bodo.libs.int_arr_ext.IntegerArrayType) or
        col_array_dtype == bodo.libs.bool_arr_ext.boolean_array or
        is_str_arr_type(col_array_dtype) or isinstance(col_array_dtype,
        types.Array) and col_array_dtype.dtype == bodo.datetime_date_type):

        @intrinsic
        def checkna_func(typingctx, table_t, ind_t):

            def codegen(context, builder, sig, args):
                nhba__fcx, wetd__nmmg = args
                nhba__fcx = builder.bitcast(nhba__fcx, lir.IntType(8).
                    as_pointer().as_pointer())
                aybpe__kds = lir.Constant(lir.IntType(64), c_ind)
                fog__esyl = builder.load(builder.gep(nhba__fcx, [aybpe__kds]))
                ljf__xfb = builder.bitcast(fog__esyl, context.get_data_type
                    (types.bool_).as_pointer())
                auxfd__sjeir = bodo.utils.cg_helpers.get_bitmap_bit(builder,
                    ljf__xfb, wetd__nmmg)
                ycmpo__lrq = builder.icmp_unsigned('!=', auxfd__sjeir, lir.
                    Constant(lir.IntType(8), 0))
                return builder.sext(ycmpo__lrq, lir.IntType(8))
            return types.int8(types.voidptr, types.int64), codegen
        return checkna_func
    elif isinstance(col_array_dtype, types.Array):
        vbvp__ywawt = col_array_dtype.dtype
        if vbvp__ywawt in [bodo.datetime64ns, bodo.timedelta64ns]:

            @intrinsic
            def checkna_func(typingctx, table_t, ind_t):

                def codegen(context, builder, sig, args):
                    ovh__iqpyg, wetd__nmmg = args
                    ovh__iqpyg = builder.bitcast(ovh__iqpyg, lir.IntType(8)
                        .as_pointer().as_pointer())
                    aybpe__kds = lir.Constant(lir.IntType(64), c_ind)
                    fog__esyl = builder.load(builder.gep(ovh__iqpyg, [
                        aybpe__kds]))
                    fog__esyl = builder.bitcast(fog__esyl, context.
                        get_data_type(vbvp__ywawt).as_pointer())
                    plq__ggdwe = builder.load(builder.gep(fog__esyl, [
                        wetd__nmmg]))
                    ycmpo__lrq = builder.icmp_unsigned('!=', plq__ggdwe,
                        lir.Constant(lir.IntType(64), pd._libs.iNaT))
                    return builder.sext(ycmpo__lrq, lir.IntType(8))
                return types.int8(types.voidptr, types.int64), codegen
            return checkna_func
        elif isinstance(vbvp__ywawt, types.Float):

            @intrinsic
            def checkna_func(typingctx, table_t, ind_t):

                def codegen(context, builder, sig, args):
                    ovh__iqpyg, wetd__nmmg = args
                    ovh__iqpyg = builder.bitcast(ovh__iqpyg, lir.IntType(8)
                        .as_pointer().as_pointer())
                    aybpe__kds = lir.Constant(lir.IntType(64), c_ind)
                    fog__esyl = builder.load(builder.gep(ovh__iqpyg, [
                        aybpe__kds]))
                    fog__esyl = builder.bitcast(fog__esyl, context.
                        get_data_type(vbvp__ywawt).as_pointer())
                    plq__ggdwe = builder.load(builder.gep(fog__esyl, [
                        wetd__nmmg]))
                    bgfu__udln = signature(types.bool_, vbvp__ywawt)
                    auxfd__sjeir = numba.np.npyfuncs.np_real_isnan_impl(context
                        , builder, bgfu__udln, (plq__ggdwe,))
                    return builder.not_(builder.sext(auxfd__sjeir, lir.
                        IntType(8)))
                return types.int8(types.voidptr, types.int64), codegen
            return checkna_func
    raise BodoError(
        f"General Join Conditions with '{col_array_dtype}' column type not supported"
        )
