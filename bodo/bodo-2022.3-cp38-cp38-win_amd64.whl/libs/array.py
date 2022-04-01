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
        iuxe__uek = context.make_helper(builder, arr_type, in_arr)
        in_arr = iuxe__uek.data
        arr_type = StructArrayType(arr_type.data, ('dummy',) * len(arr_type
            .data))
    if isinstance(arr_type, ArrayItemArrayType
        ) and arr_type.dtype == string_array_type:
        lsqs__chl = context.make_helper(builder, arr_type, in_arr)
        diud__vdb = lir.FunctionType(lir.IntType(8).as_pointer(), [lir.
            IntType(8).as_pointer()])
        feu__sndi = cgutils.get_or_insert_function(builder.module,
            diud__vdb, name='list_string_array_to_info')
        return builder.call(feu__sndi, [lsqs__chl.meminfo])
    if isinstance(arr_type, (MapArrayType, ArrayItemArrayType, StructArrayType)
        ):

        def get_types(arr_typ):
            if isinstance(arr_typ, MapArrayType):
                return get_types(_get_map_arr_data_type(arr_typ))
            elif isinstance(arr_typ, ArrayItemArrayType):
                return [CTypeEnum.LIST.value] + get_types(arr_typ.dtype)
            elif isinstance(arr_typ, (StructType, StructArrayType)):
                ztwxs__ourva = [CTypeEnum.STRUCT.value, len(arr_typ.names)]
                for rdbps__xzb in arr_typ.data:
                    ztwxs__ourva += get_types(rdbps__xzb)
                return ztwxs__ourva
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
            lao__vnf = context.compile_internal(builder, lambda a: len(a),
                types.intp(arr_typ), [arr])
            if isinstance(arr_typ, MapArrayType):
                lbbd__joy = context.make_helper(builder, arr_typ, value=arr)
                nouth__ojou = get_lengths(_get_map_arr_data_type(arr_typ),
                    lbbd__joy.data)
            elif isinstance(arr_typ, ArrayItemArrayType):
                yym__igysn = _get_array_item_arr_payload(context, builder,
                    arr_typ, arr)
                nouth__ojou = get_lengths(arr_typ.dtype, yym__igysn.data)
                nouth__ojou = cgutils.pack_array(builder, [yym__igysn.
                    n_arrays] + [builder.extract_value(nouth__ojou,
                    wgork__kunqv) for wgork__kunqv in range(nouth__ojou.
                    type.count)])
            elif isinstance(arr_typ, StructArrayType):
                yym__igysn = _get_struct_arr_payload(context, builder,
                    arr_typ, arr)
                nouth__ojou = []
                for wgork__kunqv, rdbps__xzb in enumerate(arr_typ.data):
                    iom__ftm = get_lengths(rdbps__xzb, builder.
                        extract_value(yym__igysn.data, wgork__kunqv))
                    nouth__ojou += [builder.extract_value(iom__ftm,
                        obd__gqe) for obd__gqe in range(iom__ftm.type.count)]
                nouth__ojou = cgutils.pack_array(builder, [lao__vnf,
                    context.get_constant(types.int64, -1)] + nouth__ojou)
            elif isinstance(arr_typ, (IntegerArrayType, DecimalArrayType,
                types.Array)) or arr_typ in (boolean_array,
                datetime_date_array_type, string_array_type, binary_array_type
                ):
                nouth__ojou = cgutils.pack_array(builder, [lao__vnf])
            else:
                raise BodoError(
                    f'array_to_info: unsupported type for subarray {arr_typ}')
            return nouth__ojou

        def get_buffers(arr_typ, arr):
            if isinstance(arr_typ, MapArrayType):
                lbbd__joy = context.make_helper(builder, arr_typ, value=arr)
                cnkrm__acoa = get_buffers(_get_map_arr_data_type(arr_typ),
                    lbbd__joy.data)
            elif isinstance(arr_typ, ArrayItemArrayType):
                yym__igysn = _get_array_item_arr_payload(context, builder,
                    arr_typ, arr)
                jdelg__yczzi = get_buffers(arr_typ.dtype, yym__igysn.data)
                rlu__jpeyt = context.make_array(types.Array(offset_type, 1,
                    'C'))(context, builder, yym__igysn.offsets)
                rbtu__ihc = builder.bitcast(rlu__jpeyt.data, lir.IntType(8)
                    .as_pointer())
                yce__xeqfv = context.make_array(types.Array(types.uint8, 1,
                    'C'))(context, builder, yym__igysn.null_bitmap)
                edai__pqgm = builder.bitcast(yce__xeqfv.data, lir.IntType(8
                    ).as_pointer())
                cnkrm__acoa = cgutils.pack_array(builder, [rbtu__ihc,
                    edai__pqgm] + [builder.extract_value(jdelg__yczzi,
                    wgork__kunqv) for wgork__kunqv in range(jdelg__yczzi.
                    type.count)])
            elif isinstance(arr_typ, StructArrayType):
                yym__igysn = _get_struct_arr_payload(context, builder,
                    arr_typ, arr)
                jdelg__yczzi = []
                for wgork__kunqv, rdbps__xzb in enumerate(arr_typ.data):
                    pwp__hac = get_buffers(rdbps__xzb, builder.
                        extract_value(yym__igysn.data, wgork__kunqv))
                    jdelg__yczzi += [builder.extract_value(pwp__hac,
                        obd__gqe) for obd__gqe in range(pwp__hac.type.count)]
                yce__xeqfv = context.make_array(types.Array(types.uint8, 1,
                    'C'))(context, builder, yym__igysn.null_bitmap)
                edai__pqgm = builder.bitcast(yce__xeqfv.data, lir.IntType(8
                    ).as_pointer())
                cnkrm__acoa = cgutils.pack_array(builder, [edai__pqgm] +
                    jdelg__yczzi)
            elif isinstance(arr_typ, (IntegerArrayType, DecimalArrayType)
                ) or arr_typ in (boolean_array, datetime_date_array_type):
                mrob__mxfub = arr_typ.dtype
                if isinstance(arr_typ, DecimalArrayType):
                    mrob__mxfub = int128_type
                elif arr_typ == datetime_date_array_type:
                    mrob__mxfub = types.int64
                arr = cgutils.create_struct_proxy(arr_typ)(context, builder,
                    arr)
                fyf__wjk = context.make_array(types.Array(mrob__mxfub, 1, 'C')
                    )(context, builder, arr.data)
                yce__xeqfv = context.make_array(types.Array(types.uint8, 1,
                    'C'))(context, builder, arr.null_bitmap)
                zert__yjdfm = builder.bitcast(fyf__wjk.data, lir.IntType(8)
                    .as_pointer())
                edai__pqgm = builder.bitcast(yce__xeqfv.data, lir.IntType(8
                    ).as_pointer())
                cnkrm__acoa = cgutils.pack_array(builder, [edai__pqgm,
                    zert__yjdfm])
            elif arr_typ in (string_array_type, binary_array_type):
                yym__igysn = _get_str_binary_arr_payload(context, builder,
                    arr, arr_typ)
                inp__ris = context.make_helper(builder, offset_arr_type,
                    yym__igysn.offsets).data
                yhq__olifs = context.make_helper(builder, char_arr_type,
                    yym__igysn.data).data
                wjoyi__jnlfe = context.make_helper(builder,
                    null_bitmap_arr_type, yym__igysn.null_bitmap).data
                cnkrm__acoa = cgutils.pack_array(builder, [builder.bitcast(
                    inp__ris, lir.IntType(8).as_pointer()), builder.bitcast
                    (wjoyi__jnlfe, lir.IntType(8).as_pointer()), builder.
                    bitcast(yhq__olifs, lir.IntType(8).as_pointer())])
            elif isinstance(arr_typ, types.Array):
                arr = context.make_array(arr_typ)(context, builder, arr)
                zert__yjdfm = builder.bitcast(arr.data, lir.IntType(8).
                    as_pointer())
                lgm__hhyr = lir.Constant(lir.IntType(8).as_pointer(), None)
                cnkrm__acoa = cgutils.pack_array(builder, [lgm__hhyr,
                    zert__yjdfm])
            else:
                raise RuntimeError(
                    'array_to_info: unsupported type for subarray ' + str(
                    arr_typ))
            return cnkrm__acoa

        def get_field_names(arr_typ):
            gylr__gve = []
            if isinstance(arr_typ, StructArrayType):
                for ubmq__rqssm, gla__haias in zip(arr_typ.dtype.names,
                    arr_typ.data):
                    gylr__gve.append(ubmq__rqssm)
                    gylr__gve += get_field_names(gla__haias)
            elif isinstance(arr_typ, ArrayItemArrayType):
                gylr__gve += get_field_names(arr_typ.dtype)
            elif isinstance(arr_typ, MapArrayType):
                gylr__gve += get_field_names(_get_map_arr_data_type(arr_typ))
            return gylr__gve
        ztwxs__ourva = get_types(arr_type)
        iwz__rkfh = cgutils.pack_array(builder, [context.get_constant(types
            .int32, t) for t in ztwxs__ourva])
        thg__ryz = cgutils.alloca_once_value(builder, iwz__rkfh)
        nouth__ojou = get_lengths(arr_type, in_arr)
        lengths_ptr = cgutils.alloca_once_value(builder, nouth__ojou)
        cnkrm__acoa = get_buffers(arr_type, in_arr)
        fmk__thywn = cgutils.alloca_once_value(builder, cnkrm__acoa)
        gylr__gve = get_field_names(arr_type)
        if len(gylr__gve) == 0:
            gylr__gve = ['irrelevant']
        yhj__ypa = cgutils.pack_array(builder, [context.insert_const_string
            (builder.module, a) for a in gylr__gve])
        cvu__syso = cgutils.alloca_once_value(builder, yhj__ypa)
        if isinstance(arr_type, MapArrayType):
            eyp__zai = _get_map_arr_data_type(arr_type)
            cjkad__rsw = context.make_helper(builder, arr_type, value=in_arr)
            qift__huhak = cjkad__rsw.data
        else:
            eyp__zai = arr_type
            qift__huhak = in_arr
        rwbm__bgmed = context.make_helper(builder, eyp__zai, qift__huhak)
        diud__vdb = lir.FunctionType(lir.IntType(8).as_pointer(), [lir.
            IntType(32).as_pointer(), lir.IntType(8).as_pointer().
            as_pointer(), lir.IntType(64).as_pointer(), lir.IntType(8).
            as_pointer(), lir.IntType(8).as_pointer()])
        feu__sndi = cgutils.get_or_insert_function(builder.module,
            diud__vdb, name='nested_array_to_info')
        hxb__nhiky = builder.call(feu__sndi, [builder.bitcast(thg__ryz, lir
            .IntType(32).as_pointer()), builder.bitcast(fmk__thywn, lir.
            IntType(8).as_pointer().as_pointer()), builder.bitcast(
            lengths_ptr, lir.IntType(64).as_pointer()), builder.bitcast(
            cvu__syso, lir.IntType(8).as_pointer()), rwbm__bgmed.meminfo])
        context.compile_internal(builder, lambda :
            check_and_propagate_cpp_exception(), types.none(), [])
        return hxb__nhiky
    if arr_type in (string_array_type, binary_array_type):
        xkcpx__stwn = context.make_helper(builder, arr_type, in_arr)
        rpnjl__ndvlc = ArrayItemArrayType(char_arr_type)
        lsqs__chl = context.make_helper(builder, rpnjl__ndvlc, xkcpx__stwn.data
            )
        yym__igysn = _get_str_binary_arr_payload(context, builder, in_arr,
            arr_type)
        inp__ris = context.make_helper(builder, offset_arr_type, yym__igysn
            .offsets).data
        yhq__olifs = context.make_helper(builder, char_arr_type, yym__igysn
            .data).data
        wjoyi__jnlfe = context.make_helper(builder, null_bitmap_arr_type,
            yym__igysn.null_bitmap).data
        wrxnu__tip = builder.zext(builder.load(builder.gep(inp__ris, [
            yym__igysn.n_arrays])), lir.IntType(64))
        dcw__mnxin = context.get_constant(types.int32, int(arr_type ==
            binary_array_type))
        diud__vdb = lir.FunctionType(lir.IntType(8).as_pointer(), [lir.
            IntType(64), lir.IntType(64), lir.IntType(8).as_pointer(), lir.
            IntType(offset_type.bitwidth).as_pointer(), lir.IntType(8).
            as_pointer(), lir.IntType(8).as_pointer(), lir.IntType(32)])
        feu__sndi = cgutils.get_or_insert_function(builder.module,
            diud__vdb, name='string_array_to_info')
        return builder.call(feu__sndi, [yym__igysn.n_arrays, wrxnu__tip,
            yhq__olifs, inp__ris, wjoyi__jnlfe, lsqs__chl.meminfo, dcw__mnxin])
    if arr_type == bodo.dict_str_arr_type:
        arr = cgutils.create_struct_proxy(arr_type)(context, builder, in_arr)
        krel__zwmk = arr.data
        tfzqr__dzwom = arr.indices
        sig = array_info_type(arr_type.data)
        oeu__ymtzg = array_to_info_codegen(context, builder, sig, (
            krel__zwmk,), False)
        sig = array_info_type(bodo.libs.dict_arr_ext.dict_indices_arr_type)
        akkf__uie = array_to_info_codegen(context, builder, sig, (
            tfzqr__dzwom,), False)
        worrf__qqdas = cgutils.create_struct_proxy(bodo.libs.dict_arr_ext.
            dict_indices_arr_type)(context, builder, tfzqr__dzwom)
        edai__pqgm = context.make_array(types.Array(types.uint8, 1, 'C'))(
            context, builder, worrf__qqdas.null_bitmap).data
        diud__vdb = lir.FunctionType(lir.IntType(8).as_pointer(), [lir.
            IntType(8).as_pointer(), lir.IntType(8).as_pointer(), lir.
            IntType(8).as_pointer(), lir.IntType(32)])
        feu__sndi = cgutils.get_or_insert_function(builder.module,
            diud__vdb, name='dict_str_array_to_info')
        qyjk__man = builder.zext(arr.has_global_dictionary, lir.IntType(32))
        return builder.call(feu__sndi, [oeu__ymtzg, akkf__uie, builder.
            bitcast(edai__pqgm, lir.IntType(8).as_pointer()), qyjk__man])
    bmsp__icho = False
    if isinstance(arr_type, CategoricalArrayType):
        context.nrt.decref(builder, arr_type, in_arr)
        mfrh__uenj = context.compile_internal(builder, lambda a: len(a.
            dtype.categories), types.intp(arr_type), [in_arr])
        in_arr = cgutils.create_struct_proxy(arr_type)(context, builder, in_arr
            ).codes
        jkpnl__ucy = get_categories_int_type(arr_type.dtype)
        arr_type = types.Array(jkpnl__ucy, 1, 'C')
        bmsp__icho = True
        context.nrt.incref(builder, arr_type, in_arr)
    if isinstance(arr_type, bodo.DatetimeArrayType):
        if bmsp__icho:
            raise BodoError(
                'array_to_info(): Categorical PandasDatetimeArrayType not supported'
                )
        in_arr = cgutils.create_struct_proxy(arr_type)(context, builder, in_arr
            ).data
        arr_type = arr_type.data_array_type
    if isinstance(arr_type, types.Array):
        arr = context.make_array(arr_type)(context, builder, in_arr)
        assert arr_type.ndim == 1, 'only 1D array shuffle supported'
        lao__vnf = builder.extract_value(arr.shape, 0)
        rrop__wrv = arr_type.dtype
        whik__fout = numba_to_c_type(rrop__wrv)
        epy__jyelr = cgutils.alloca_once_value(builder, lir.Constant(lir.
            IntType(32), whik__fout))
        if bmsp__icho:
            diud__vdb = lir.FunctionType(lir.IntType(8).as_pointer(), [lir.
                IntType(64), lir.IntType(8).as_pointer(), lir.IntType(32),
                lir.IntType(64), lir.IntType(8).as_pointer()])
            feu__sndi = cgutils.get_or_insert_function(builder.module,
                diud__vdb, name='categorical_array_to_info')
            return builder.call(feu__sndi, [lao__vnf, builder.bitcast(arr.
                data, lir.IntType(8).as_pointer()), builder.load(epy__jyelr
                ), mfrh__uenj, arr.meminfo])
        else:
            diud__vdb = lir.FunctionType(lir.IntType(8).as_pointer(), [lir.
                IntType(64), lir.IntType(8).as_pointer(), lir.IntType(32),
                lir.IntType(8).as_pointer()])
            feu__sndi = cgutils.get_or_insert_function(builder.module,
                diud__vdb, name='numpy_array_to_info')
            return builder.call(feu__sndi, [lao__vnf, builder.bitcast(arr.
                data, lir.IntType(8).as_pointer()), builder.load(epy__jyelr
                ), arr.meminfo])
    if isinstance(arr_type, (IntegerArrayType, DecimalArrayType)
        ) or arr_type in (boolean_array, datetime_date_array_type):
        arr = cgutils.create_struct_proxy(arr_type)(context, builder, in_arr)
        rrop__wrv = arr_type.dtype
        mrob__mxfub = rrop__wrv
        if isinstance(arr_type, DecimalArrayType):
            mrob__mxfub = int128_type
        if arr_type == datetime_date_array_type:
            mrob__mxfub = types.int64
        fyf__wjk = context.make_array(types.Array(mrob__mxfub, 1, 'C'))(context
            , builder, arr.data)
        lao__vnf = builder.extract_value(fyf__wjk.shape, 0)
        kcr__rkaie = context.make_array(types.Array(types.uint8, 1, 'C'))(
            context, builder, arr.null_bitmap)
        whik__fout = numba_to_c_type(rrop__wrv)
        epy__jyelr = cgutils.alloca_once_value(builder, lir.Constant(lir.
            IntType(32), whik__fout))
        if isinstance(arr_type, DecimalArrayType):
            diud__vdb = lir.FunctionType(lir.IntType(8).as_pointer(), [lir.
                IntType(64), lir.IntType(8).as_pointer(), lir.IntType(32),
                lir.IntType(8).as_pointer(), lir.IntType(8).as_pointer(),
                lir.IntType(8).as_pointer(), lir.IntType(32), lir.IntType(32)])
            feu__sndi = cgutils.get_or_insert_function(builder.module,
                diud__vdb, name='decimal_array_to_info')
            return builder.call(feu__sndi, [lao__vnf, builder.bitcast(
                fyf__wjk.data, lir.IntType(8).as_pointer()), builder.load(
                epy__jyelr), builder.bitcast(kcr__rkaie.data, lir.IntType(8
                ).as_pointer()), fyf__wjk.meminfo, kcr__rkaie.meminfo,
                context.get_constant(types.int32, arr_type.precision),
                context.get_constant(types.int32, arr_type.scale)])
        else:
            diud__vdb = lir.FunctionType(lir.IntType(8).as_pointer(), [lir.
                IntType(64), lir.IntType(8).as_pointer(), lir.IntType(32),
                lir.IntType(8).as_pointer(), lir.IntType(8).as_pointer(),
                lir.IntType(8).as_pointer()])
            feu__sndi = cgutils.get_or_insert_function(builder.module,
                diud__vdb, name='nullable_array_to_info')
            return builder.call(feu__sndi, [lao__vnf, builder.bitcast(
                fyf__wjk.data, lir.IntType(8).as_pointer()), builder.load(
                epy__jyelr), builder.bitcast(kcr__rkaie.data, lir.IntType(8
                ).as_pointer()), fyf__wjk.meminfo, kcr__rkaie.meminfo])
    if isinstance(arr_type, IntervalArrayType):
        assert isinstance(arr_type.arr_type, types.Array
            ), 'array_to_info(): only IntervalArrayType with Numpy arrays supported'
        arr = cgutils.create_struct_proxy(arr_type)(context, builder, in_arr)
        vrpje__zgjy = context.make_array(arr_type.arr_type)(context,
            builder, arr.left)
        bul__sbe = context.make_array(arr_type.arr_type)(context, builder,
            arr.right)
        lao__vnf = builder.extract_value(vrpje__zgjy.shape, 0)
        whik__fout = numba_to_c_type(arr_type.arr_type.dtype)
        epy__jyelr = cgutils.alloca_once_value(builder, lir.Constant(lir.
            IntType(32), whik__fout))
        diud__vdb = lir.FunctionType(lir.IntType(8).as_pointer(), [lir.
            IntType(64), lir.IntType(8).as_pointer(), lir.IntType(8).
            as_pointer(), lir.IntType(32), lir.IntType(8).as_pointer(), lir
            .IntType(8).as_pointer()])
        feu__sndi = cgutils.get_or_insert_function(builder.module,
            diud__vdb, name='interval_array_to_info')
        return builder.call(feu__sndi, [lao__vnf, builder.bitcast(
            vrpje__zgjy.data, lir.IntType(8).as_pointer()), builder.bitcast
            (bul__sbe.data, lir.IntType(8).as_pointer()), builder.load(
            epy__jyelr), vrpje__zgjy.meminfo, bul__sbe.meminfo])
    raise_bodo_error(f'array_to_info(): array type {arr_type} is not supported'
        )


def _lower_info_to_array_numpy(arr_type, context, builder, in_info):
    assert arr_type.ndim == 1, 'only 1D array supported'
    arr = context.make_array(arr_type)(context, builder)
    whkr__xncd = cgutils.alloca_once(builder, lir.IntType(64))
    zert__yjdfm = cgutils.alloca_once(builder, lir.IntType(8).as_pointer())
    bpeap__ewp = cgutils.alloca_once(builder, lir.IntType(8).as_pointer())
    diud__vdb = lir.FunctionType(lir.VoidType(), [lir.IntType(8).as_pointer
        (), lir.IntType(64).as_pointer(), lir.IntType(8).as_pointer().
        as_pointer(), lir.IntType(8).as_pointer().as_pointer()])
    feu__sndi = cgutils.get_or_insert_function(builder.module, diud__vdb,
        name='info_to_numpy_array')
    builder.call(feu__sndi, [in_info, whkr__xncd, zert__yjdfm, bpeap__ewp])
    context.compile_internal(builder, lambda :
        check_and_propagate_cpp_exception(), types.none(), [])
    kik__obhw = context.get_value_type(types.intp)
    ybvs__dpk = cgutils.pack_array(builder, [builder.load(whkr__xncd)], ty=
        kik__obhw)
    wnoz__eid = context.get_constant(types.intp, context.get_abi_sizeof(
        context.get_data_type(arr_type.dtype)))
    own__zrlr = cgutils.pack_array(builder, [wnoz__eid], ty=kik__obhw)
    yhq__olifs = builder.bitcast(builder.load(zert__yjdfm), context.
        get_data_type(arr_type.dtype).as_pointer())
    numba.np.arrayobj.populate_array(arr, data=yhq__olifs, shape=ybvs__dpk,
        strides=own__zrlr, itemsize=wnoz__eid, meminfo=builder.load(bpeap__ewp)
        )
    return arr._getvalue()


def _lower_info_to_array_list_string_array(arr_type, context, builder, in_info
    ):
    unnou__ggys = context.make_helper(builder, arr_type)
    diud__vdb = lir.FunctionType(lir.VoidType(), [lir.IntType(8).as_pointer
        (), lir.IntType(8).as_pointer().as_pointer()])
    feu__sndi = cgutils.get_or_insert_function(builder.module, diud__vdb,
        name='info_to_list_string_array')
    builder.call(feu__sndi, [in_info, unnou__ggys._get_ptr_by_name('meminfo')])
    context.compile_internal(builder, lambda :
        check_and_propagate_cpp_exception(), types.none(), [])
    return unnou__ggys._getvalue()


def nested_to_array(context, builder, arr_typ, lengths_ptr, array_infos_ptr,
    lengths_pos, infos_pos):
    fplix__gfeb = context.get_data_type(array_info_type)
    if isinstance(arr_typ, ArrayItemArrayType):
        jzfp__eqt = lengths_pos
        eob__bergm = infos_pos
        unlvg__utizu, lengths_pos, infos_pos = nested_to_array(context,
            builder, arr_typ.dtype, lengths_ptr, array_infos_ptr, 
            lengths_pos + 1, infos_pos + 2)
        rqn__beb = ArrayItemArrayPayloadType(arr_typ)
        hedhv__byja = context.get_data_type(rqn__beb)
        mcjz__jhvhl = context.get_abi_sizeof(hedhv__byja)
        lsnpv__wxklv = define_array_item_dtor(context, builder, arr_typ,
            rqn__beb)
        ntiu__ymg = context.nrt.meminfo_alloc_dtor(builder, context.
            get_constant(types.uintp, mcjz__jhvhl), lsnpv__wxklv)
        vkswx__hsl = context.nrt.meminfo_data(builder, ntiu__ymg)
        tetx__clq = builder.bitcast(vkswx__hsl, hedhv__byja.as_pointer())
        yym__igysn = cgutils.create_struct_proxy(rqn__beb)(context, builder)
        yym__igysn.n_arrays = builder.extract_value(builder.load(
            lengths_ptr), jzfp__eqt)
        yym__igysn.data = unlvg__utizu
        zid__mls = builder.load(array_infos_ptr)
        nxryj__oxxs = builder.bitcast(builder.extract_value(zid__mls,
            eob__bergm), fplix__gfeb)
        yym__igysn.offsets = _lower_info_to_array_numpy(types.Array(
            offset_type, 1, 'C'), context, builder, nxryj__oxxs)
        yeue__nbura = builder.bitcast(builder.extract_value(zid__mls, 
            eob__bergm + 1), fplix__gfeb)
        yym__igysn.null_bitmap = _lower_info_to_array_numpy(types.Array(
            types.uint8, 1, 'C'), context, builder, yeue__nbura)
        builder.store(yym__igysn._getvalue(), tetx__clq)
        lsqs__chl = context.make_helper(builder, arr_typ)
        lsqs__chl.meminfo = ntiu__ymg
        return lsqs__chl._getvalue(), lengths_pos, infos_pos
    elif isinstance(arr_typ, StructArrayType):
        erv__olysv = []
        eob__bergm = infos_pos
        lengths_pos += 1
        infos_pos += 1
        for xdfv__mri in arr_typ.data:
            unlvg__utizu, lengths_pos, infos_pos = nested_to_array(context,
                builder, xdfv__mri, lengths_ptr, array_infos_ptr,
                lengths_pos, infos_pos)
            erv__olysv.append(unlvg__utizu)
        rqn__beb = StructArrayPayloadType(arr_typ.data)
        hedhv__byja = context.get_value_type(rqn__beb)
        mcjz__jhvhl = context.get_abi_sizeof(hedhv__byja)
        lsnpv__wxklv = define_struct_arr_dtor(context, builder, arr_typ,
            rqn__beb)
        ntiu__ymg = context.nrt.meminfo_alloc_dtor(builder, context.
            get_constant(types.uintp, mcjz__jhvhl), lsnpv__wxklv)
        vkswx__hsl = context.nrt.meminfo_data(builder, ntiu__ymg)
        tetx__clq = builder.bitcast(vkswx__hsl, hedhv__byja.as_pointer())
        yym__igysn = cgutils.create_struct_proxy(rqn__beb)(context, builder)
        yym__igysn.data = cgutils.pack_array(builder, erv__olysv
            ) if types.is_homogeneous(*arr_typ.data) else cgutils.pack_struct(
            builder, erv__olysv)
        zid__mls = builder.load(array_infos_ptr)
        yeue__nbura = builder.bitcast(builder.extract_value(zid__mls,
            eob__bergm), fplix__gfeb)
        yym__igysn.null_bitmap = _lower_info_to_array_numpy(types.Array(
            types.uint8, 1, 'C'), context, builder, yeue__nbura)
        builder.store(yym__igysn._getvalue(), tetx__clq)
        caf__dsud = context.make_helper(builder, arr_typ)
        caf__dsud.meminfo = ntiu__ymg
        return caf__dsud._getvalue(), lengths_pos, infos_pos
    elif arr_typ in (string_array_type, binary_array_type):
        zid__mls = builder.load(array_infos_ptr)
        mozq__qvt = builder.bitcast(builder.extract_value(zid__mls,
            infos_pos), fplix__gfeb)
        xkcpx__stwn = context.make_helper(builder, arr_typ)
        rpnjl__ndvlc = ArrayItemArrayType(char_arr_type)
        lsqs__chl = context.make_helper(builder, rpnjl__ndvlc)
        diud__vdb = lir.FunctionType(lir.VoidType(), [lir.IntType(8).
            as_pointer(), lir.IntType(8).as_pointer().as_pointer()])
        feu__sndi = cgutils.get_or_insert_function(builder.module,
            diud__vdb, name='info_to_string_array')
        builder.call(feu__sndi, [mozq__qvt, lsqs__chl._get_ptr_by_name(
            'meminfo')])
        context.compile_internal(builder, lambda :
            check_and_propagate_cpp_exception(), types.none(), [])
        xkcpx__stwn.data = lsqs__chl._getvalue()
        return xkcpx__stwn._getvalue(), lengths_pos + 1, infos_pos + 1
    elif isinstance(arr_typ, types.Array):
        zid__mls = builder.load(array_infos_ptr)
        xvjj__wdd = builder.bitcast(builder.extract_value(zid__mls, 
            infos_pos + 1), fplix__gfeb)
        return _lower_info_to_array_numpy(arr_typ, context, builder, xvjj__wdd
            ), lengths_pos + 1, infos_pos + 2
    elif isinstance(arr_typ, (IntegerArrayType, DecimalArrayType)
        ) or arr_typ in (boolean_array, datetime_date_array_type):
        arr = cgutils.create_struct_proxy(arr_typ)(context, builder)
        mrob__mxfub = arr_typ.dtype
        if isinstance(arr_typ, DecimalArrayType):
            mrob__mxfub = int128_type
        elif arr_typ == datetime_date_array_type:
            mrob__mxfub = types.int64
        zid__mls = builder.load(array_infos_ptr)
        yeue__nbura = builder.bitcast(builder.extract_value(zid__mls,
            infos_pos), fplix__gfeb)
        arr.null_bitmap = _lower_info_to_array_numpy(types.Array(types.
            uint8, 1, 'C'), context, builder, yeue__nbura)
        xvjj__wdd = builder.bitcast(builder.extract_value(zid__mls, 
            infos_pos + 1), fplix__gfeb)
        arr.data = _lower_info_to_array_numpy(types.Array(mrob__mxfub, 1,
            'C'), context, builder, xvjj__wdd)
        return arr._getvalue(), lengths_pos + 1, infos_pos + 2


def info_to_array_codegen(context, builder, sig, args):
    array_type = sig.args[1]
    arr_type = array_type.instance_type if isinstance(array_type, types.TypeRef
        ) else array_type
    in_info, aptsd__pafc = args
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
                return 1 + sum([get_num_arrays(xdfv__mri) for xdfv__mri in
                    arr_typ.data])
            else:
                return 1

        def get_num_infos(arr_typ):
            if isinstance(arr_typ, ArrayItemArrayType):
                return 2 + get_num_infos(arr_typ.dtype)
            elif isinstance(arr_typ, StructArrayType):
                return 1 + sum([get_num_infos(xdfv__mri) for xdfv__mri in
                    arr_typ.data])
            elif arr_typ in (string_array_type, binary_array_type):
                return 1
            else:
                return 2
        if isinstance(arr_type, TupleArrayType):
            iag__ekxf = StructArrayType(arr_type.data, ('dummy',) * len(
                arr_type.data))
        elif isinstance(arr_type, MapArrayType):
            iag__ekxf = _get_map_arr_data_type(arr_type)
        else:
            iag__ekxf = arr_type
        apm__vfzop = get_num_arrays(iag__ekxf)
        nouth__ojou = cgutils.pack_array(builder, [lir.Constant(lir.IntType
            (64), 0) for aptsd__pafc in range(apm__vfzop)])
        lengths_ptr = cgutils.alloca_once_value(builder, nouth__ojou)
        lgm__hhyr = lir.Constant(lir.IntType(8).as_pointer(), None)
        iuujv__ktp = cgutils.pack_array(builder, [lgm__hhyr for aptsd__pafc in
            range(get_num_infos(iag__ekxf))])
        array_infos_ptr = cgutils.alloca_once_value(builder, iuujv__ktp)
        diud__vdb = lir.FunctionType(lir.VoidType(), [lir.IntType(8).
            as_pointer(), lir.IntType(64).as_pointer(), lir.IntType(8).
            as_pointer().as_pointer()])
        feu__sndi = cgutils.get_or_insert_function(builder.module,
            diud__vdb, name='info_to_nested_array')
        builder.call(feu__sndi, [in_info, builder.bitcast(lengths_ptr, lir.
            IntType(64).as_pointer()), builder.bitcast(array_infos_ptr, lir
            .IntType(8).as_pointer().as_pointer())])
        context.compile_internal(builder, lambda :
            check_and_propagate_cpp_exception(), types.none(), [])
        arr, aptsd__pafc, aptsd__pafc = nested_to_array(context, builder,
            iag__ekxf, lengths_ptr, array_infos_ptr, 0, 0)
        if isinstance(arr_type, TupleArrayType):
            iuxe__uek = context.make_helper(builder, arr_type)
            iuxe__uek.data = arr
            context.nrt.incref(builder, iag__ekxf, arr)
            arr = iuxe__uek._getvalue()
        elif isinstance(arr_type, MapArrayType):
            sig = signature(arr_type, iag__ekxf)
            arr = init_map_arr_codegen(context, builder, sig, (arr,))
        return arr
    if arr_type in (string_array_type, binary_array_type):
        xkcpx__stwn = context.make_helper(builder, arr_type)
        rpnjl__ndvlc = ArrayItemArrayType(char_arr_type)
        lsqs__chl = context.make_helper(builder, rpnjl__ndvlc)
        diud__vdb = lir.FunctionType(lir.VoidType(), [lir.IntType(8).
            as_pointer(), lir.IntType(8).as_pointer().as_pointer()])
        feu__sndi = cgutils.get_or_insert_function(builder.module,
            diud__vdb, name='info_to_string_array')
        builder.call(feu__sndi, [in_info, lsqs__chl._get_ptr_by_name(
            'meminfo')])
        context.compile_internal(builder, lambda :
            check_and_propagate_cpp_exception(), types.none(), [])
        xkcpx__stwn.data = lsqs__chl._getvalue()
        return xkcpx__stwn._getvalue()
    if arr_type == bodo.dict_str_arr_type:
        diud__vdb = lir.FunctionType(lir.IntType(8).as_pointer(), [lir.
            IntType(8).as_pointer(), lir.IntType(32)])
        feu__sndi = cgutils.get_or_insert_function(builder.module,
            diud__vdb, name='get_nested_info')
        oeu__ymtzg = builder.call(feu__sndi, [in_info, lir.Constant(lir.
            IntType(32), 1)])
        akkf__uie = builder.call(feu__sndi, [in_info, lir.Constant(lir.
            IntType(32), 2)])
        jurk__qwf = context.make_helper(builder, arr_type)
        sig = arr_type.data(array_info_type, arr_type.data)
        jurk__qwf.data = info_to_array_codegen(context, builder, sig, (
            oeu__ymtzg, context.get_constant_null(arr_type.data)))
        eghvg__wugkh = bodo.libs.dict_arr_ext.dict_indices_arr_type
        sig = eghvg__wugkh(array_info_type, eghvg__wugkh)
        jurk__qwf.indices = info_to_array_codegen(context, builder, sig, (
            akkf__uie, context.get_constant_null(eghvg__wugkh)))
        diud__vdb = lir.FunctionType(lir.IntType(32), [lir.IntType(8).
            as_pointer()])
        feu__sndi = cgutils.get_or_insert_function(builder.module,
            diud__vdb, name='get_has_global_dictionary')
        qyjk__man = builder.call(feu__sndi, [in_info])
        jurk__qwf.has_global_dictionary = builder.trunc(qyjk__man, cgutils.
            bool_t)
        return jurk__qwf._getvalue()
    if isinstance(arr_type, CategoricalArrayType):
        out_arr = cgutils.create_struct_proxy(arr_type)(context, builder)
        jkpnl__ucy = get_categories_int_type(arr_type.dtype)
        hndqr__zkh = types.Array(jkpnl__ucy, 1, 'C')
        out_arr.codes = _lower_info_to_array_numpy(hndqr__zkh, context,
            builder, in_info)
        if isinstance(array_type, types.TypeRef):
            assert arr_type.dtype.categories is not None, 'info_to_array: unknown categories'
            is_ordered = arr_type.dtype.ordered
            aqim__hkfx = pd.CategoricalDtype(arr_type.dtype.categories,
                is_ordered).categories.values
            new_cats_tup = MetaType(tuple(aqim__hkfx))
            int_type = arr_type.dtype.int_type
            xzzqg__teub = bodo.typeof(aqim__hkfx)
            vcr__lfix = context.get_constant_generic(builder, xzzqg__teub,
                aqim__hkfx)
            rrop__wrv = context.compile_internal(builder, lambda c_arr:
                bodo.hiframes.pd_categorical_ext.init_cat_dtype(bodo.utils.
                conversion.index_from_array(c_arr), is_ordered, int_type,
                new_cats_tup), arr_type.dtype(xzzqg__teub), [vcr__lfix])
        else:
            rrop__wrv = cgutils.create_struct_proxy(arr_type)(context,
                builder, args[1]).dtype
            context.nrt.incref(builder, arr_type.dtype, rrop__wrv)
        out_arr.dtype = rrop__wrv
        return out_arr._getvalue()
    if isinstance(arr_type, bodo.DatetimeArrayType):
        arr = cgutils.create_struct_proxy(arr_type)(context, builder)
        yhq__olifs = _lower_info_to_array_numpy(arr_type.data_array_type,
            context, builder, in_info)
        arr.data = yhq__olifs
        return arr._getvalue()
    if isinstance(arr_type, types.Array):
        return _lower_info_to_array_numpy(arr_type, context, builder, in_info)
    if isinstance(arr_type, (IntegerArrayType, DecimalArrayType)
        ) or arr_type in (boolean_array, datetime_date_array_type):
        arr = cgutils.create_struct_proxy(arr_type)(context, builder)
        mrob__mxfub = arr_type.dtype
        if isinstance(arr_type, DecimalArrayType):
            mrob__mxfub = int128_type
        elif arr_type == datetime_date_array_type:
            mrob__mxfub = types.int64
        jis__mvzo = types.Array(mrob__mxfub, 1, 'C')
        fyf__wjk = context.make_array(jis__mvzo)(context, builder)
        kqylv__ilk = types.Array(types.uint8, 1, 'C')
        lbp__ylz = context.make_array(kqylv__ilk)(context, builder)
        whkr__xncd = cgutils.alloca_once(builder, lir.IntType(64))
        hfcgu__ajoj = cgutils.alloca_once(builder, lir.IntType(64))
        zert__yjdfm = cgutils.alloca_once(builder, lir.IntType(8).as_pointer())
        seilp__yiy = cgutils.alloca_once(builder, lir.IntType(8).as_pointer())
        bpeap__ewp = cgutils.alloca_once(builder, lir.IntType(8).as_pointer())
        ajyg__dls = cgutils.alloca_once(builder, lir.IntType(8).as_pointer())
        diud__vdb = lir.FunctionType(lir.VoidType(), [lir.IntType(8).
            as_pointer(), lir.IntType(64).as_pointer(), lir.IntType(64).
            as_pointer(), lir.IntType(8).as_pointer().as_pointer(), lir.
            IntType(8).as_pointer().as_pointer(), lir.IntType(8).as_pointer
            ().as_pointer(), lir.IntType(8).as_pointer().as_pointer()])
        feu__sndi = cgutils.get_or_insert_function(builder.module,
            diud__vdb, name='info_to_nullable_array')
        builder.call(feu__sndi, [in_info, whkr__xncd, hfcgu__ajoj,
            zert__yjdfm, seilp__yiy, bpeap__ewp, ajyg__dls])
        context.compile_internal(builder, lambda :
            check_and_propagate_cpp_exception(), types.none(), [])
        kik__obhw = context.get_value_type(types.intp)
        ybvs__dpk = cgutils.pack_array(builder, [builder.load(whkr__xncd)],
            ty=kik__obhw)
        wnoz__eid = context.get_constant(types.intp, context.get_abi_sizeof
            (context.get_data_type(mrob__mxfub)))
        own__zrlr = cgutils.pack_array(builder, [wnoz__eid], ty=kik__obhw)
        yhq__olifs = builder.bitcast(builder.load(zert__yjdfm), context.
            get_data_type(mrob__mxfub).as_pointer())
        numba.np.arrayobj.populate_array(fyf__wjk, data=yhq__olifs, shape=
            ybvs__dpk, strides=own__zrlr, itemsize=wnoz__eid, meminfo=
            builder.load(bpeap__ewp))
        arr.data = fyf__wjk._getvalue()
        ybvs__dpk = cgutils.pack_array(builder, [builder.load(hfcgu__ajoj)],
            ty=kik__obhw)
        wnoz__eid = context.get_constant(types.intp, context.get_abi_sizeof
            (context.get_data_type(types.uint8)))
        own__zrlr = cgutils.pack_array(builder, [wnoz__eid], ty=kik__obhw)
        yhq__olifs = builder.bitcast(builder.load(seilp__yiy), context.
            get_data_type(types.uint8).as_pointer())
        numba.np.arrayobj.populate_array(lbp__ylz, data=yhq__olifs, shape=
            ybvs__dpk, strides=own__zrlr, itemsize=wnoz__eid, meminfo=
            builder.load(ajyg__dls))
        arr.null_bitmap = lbp__ylz._getvalue()
        return arr._getvalue()
    if isinstance(arr_type, IntervalArrayType):
        arr = cgutils.create_struct_proxy(arr_type)(context, builder)
        vrpje__zgjy = context.make_array(arr_type.arr_type)(context, builder)
        bul__sbe = context.make_array(arr_type.arr_type)(context, builder)
        whkr__xncd = cgutils.alloca_once(builder, lir.IntType(64))
        ebfxv__mybyj = cgutils.alloca_once(builder, lir.IntType(8).as_pointer()
            )
        ysxko__hxjet = cgutils.alloca_once(builder, lir.IntType(8).as_pointer()
            )
        fou__oqydd = cgutils.alloca_once(builder, lir.IntType(8).as_pointer())
        wwpfl__ppzu = cgutils.alloca_once(builder, lir.IntType(8).as_pointer())
        diud__vdb = lir.FunctionType(lir.VoidType(), [lir.IntType(8).
            as_pointer(), lir.IntType(64).as_pointer(), lir.IntType(8).
            as_pointer().as_pointer(), lir.IntType(8).as_pointer().
            as_pointer(), lir.IntType(8).as_pointer().as_pointer(), lir.
            IntType(8).as_pointer().as_pointer()])
        feu__sndi = cgutils.get_or_insert_function(builder.module,
            diud__vdb, name='info_to_interval_array')
        builder.call(feu__sndi, [in_info, whkr__xncd, ebfxv__mybyj,
            ysxko__hxjet, fou__oqydd, wwpfl__ppzu])
        context.compile_internal(builder, lambda :
            check_and_propagate_cpp_exception(), types.none(), [])
        kik__obhw = context.get_value_type(types.intp)
        ybvs__dpk = cgutils.pack_array(builder, [builder.load(whkr__xncd)],
            ty=kik__obhw)
        wnoz__eid = context.get_constant(types.intp, context.get_abi_sizeof
            (context.get_data_type(arr_type.arr_type.dtype)))
        own__zrlr = cgutils.pack_array(builder, [wnoz__eid], ty=kik__obhw)
        jkw__jtm = builder.bitcast(builder.load(ebfxv__mybyj), context.
            get_data_type(arr_type.arr_type.dtype).as_pointer())
        numba.np.arrayobj.populate_array(vrpje__zgjy, data=jkw__jtm, shape=
            ybvs__dpk, strides=own__zrlr, itemsize=wnoz__eid, meminfo=
            builder.load(fou__oqydd))
        arr.left = vrpje__zgjy._getvalue()
        strv__whw = builder.bitcast(builder.load(ysxko__hxjet), context.
            get_data_type(arr_type.arr_type.dtype).as_pointer())
        numba.np.arrayobj.populate_array(bul__sbe, data=strv__whw, shape=
            ybvs__dpk, strides=own__zrlr, itemsize=wnoz__eid, meminfo=
            builder.load(wwpfl__ppzu))
        arr.right = bul__sbe._getvalue()
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
        lao__vnf, aptsd__pafc = args
        whik__fout = numba_to_c_type(array_type.dtype)
        epy__jyelr = cgutils.alloca_once_value(builder, lir.Constant(lir.
            IntType(32), whik__fout))
        diud__vdb = lir.FunctionType(lir.IntType(8).as_pointer(), [lir.
            IntType(64), lir.IntType(32)])
        feu__sndi = cgutils.get_or_insert_function(builder.module,
            diud__vdb, name='alloc_numpy')
        return builder.call(feu__sndi, [lao__vnf, builder.load(epy__jyelr)])
    return array_info_type(len_typ, arr_type), codegen


@intrinsic
def test_alloc_string(typingctx, len_typ, n_chars_typ):

    def codegen(context, builder, sig, args):
        lao__vnf, dleim__jlt = args
        diud__vdb = lir.FunctionType(lir.IntType(8).as_pointer(), [lir.
            IntType(64), lir.IntType(64)])
        feu__sndi = cgutils.get_or_insert_function(builder.module,
            diud__vdb, name='alloc_string_array')
        return builder.call(feu__sndi, [lao__vnf, dleim__jlt])
    return array_info_type(len_typ, n_chars_typ), codegen


@intrinsic
def arr_info_list_to_table(typingctx, list_arr_info_typ=None):
    assert list_arr_info_typ == types.List(array_info_type)
    return table_type(list_arr_info_typ), arr_info_list_to_table_codegen


def arr_info_list_to_table_codegen(context, builder, sig, args):
    tib__xwz, = args
    hvj__xpd = numba.cpython.listobj.ListInstance(context, builder, sig.
        args[0], tib__xwz)
    diud__vdb = lir.FunctionType(lir.IntType(8).as_pointer(), [lir.IntType(
        8).as_pointer().as_pointer(), lir.IntType(64)])
    feu__sndi = cgutils.get_or_insert_function(builder.module, diud__vdb,
        name='arr_info_list_to_table')
    return builder.call(feu__sndi, [hvj__xpd.data, hvj__xpd.size])


@intrinsic
def info_from_table(typingctx, table_t, ind_t):

    def codegen(context, builder, sig, args):
        diud__vdb = lir.FunctionType(lir.IntType(8).as_pointer(), [lir.
            IntType(8).as_pointer(), lir.IntType(64)])
        feu__sndi = cgutils.get_or_insert_function(builder.module,
            diud__vdb, name='info_from_table')
        return builder.call(feu__sndi, args)
    return array_info_type(table_t, ind_t), codegen


@intrinsic
def cpp_table_to_py_table(typingctx, cpp_table_t, table_idx_arr_t,
    py_table_type_t):
    assert cpp_table_t == table_type, 'invalid cpp table type'
    assert isinstance(table_idx_arr_t, types.Array
        ) and table_idx_arr_t.dtype == types.int64, 'invalid table index array'
    assert isinstance(py_table_type_t, types.TypeRef), 'invalid py table ref'
    wlgcf__mniv = py_table_type_t.instance_type

    def codegen(context, builder, sig, args):
        crxnw__kpj, hokan__xse, aptsd__pafc = args
        diud__vdb = lir.FunctionType(lir.IntType(8).as_pointer(), [lir.
            IntType(8).as_pointer(), lir.IntType(64)])
        feu__sndi = cgutils.get_or_insert_function(builder.module,
            diud__vdb, name='info_from_table')
        svsw__naggc = cgutils.create_struct_proxy(wlgcf__mniv)(context, builder
            )
        svsw__naggc.parent = cgutils.get_null_value(svsw__naggc.parent.type)
        vtqcn__syd = context.make_array(table_idx_arr_t)(context, builder,
            hokan__xse)
        lueo__vzvwv = context.get_constant(types.int64, -1)
        tfmg__igxu = context.get_constant(types.int64, 0)
        quq__baeix = cgutils.alloca_once_value(builder, tfmg__igxu)
        for t, bvql__cib in wlgcf__mniv.type_to_blk.items():
            yzrc__tbev = context.get_constant(types.int64, len(wlgcf__mniv.
                block_to_arr_ind[bvql__cib]))
            aptsd__pafc, aglm__mpuky = ListInstance.allocate_ex(context,
                builder, types.List(t), yzrc__tbev)
            aglm__mpuky.size = yzrc__tbev
            iuya__gwado = context.make_constant_array(builder, types.Array(
                types.int64, 1, 'C'), np.array(wlgcf__mniv.block_to_arr_ind
                [bvql__cib], dtype=np.int64))
            ayqh__two = context.make_array(types.Array(types.int64, 1, 'C'))(
                context, builder, iuya__gwado)
            with cgutils.for_range(builder, yzrc__tbev) as mswnx__tnig:
                wgork__kunqv = mswnx__tnig.index
                uni__gbgc = _getitem_array_single_int(context, builder,
                    types.int64, types.Array(types.int64, 1, 'C'),
                    ayqh__two, wgork__kunqv)
                pszic__mnzah = _getitem_array_single_int(context, builder,
                    types.int64, table_idx_arr_t, vtqcn__syd, uni__gbgc)
                fjt__xmwsi = builder.icmp_unsigned('!=', pszic__mnzah,
                    lueo__vzvwv)
                with builder.if_else(fjt__xmwsi) as (qfcc__vmzm, xthr__wbmw):
                    with qfcc__vmzm:
                        uik__kqv = builder.call(feu__sndi, [crxnw__kpj,
                            pszic__mnzah])
                        arr = context.compile_internal(builder, lambda info:
                            info_to_array(info, t), t(array_info_type), [
                            uik__kqv])
                        aglm__mpuky.inititem(wgork__kunqv, arr, incref=False)
                        lao__vnf = context.compile_internal(builder, lambda
                            arr: len(arr), types.int64(t), [arr])
                        builder.store(lao__vnf, quq__baeix)
                    with xthr__wbmw:
                        hos__agcu = context.get_constant_null(t)
                        aglm__mpuky.inititem(wgork__kunqv, hos__agcu,
                            incref=False)
            setattr(svsw__naggc, f'block_{bvql__cib}', aglm__mpuky.value)
        svsw__naggc.len = builder.load(quq__baeix)
        return svsw__naggc._getvalue()
    return wlgcf__mniv(cpp_table_t, table_idx_arr_t, py_table_type_t), codegen


@intrinsic
def py_table_to_cpp_table(typingctx, py_table_t, py_table_type_t):
    assert isinstance(py_table_t, bodo.hiframes.table.TableType
        ), 'invalid py table type'
    assert isinstance(py_table_type_t, types.TypeRef), 'invalid py table ref'
    wlgcf__mniv = py_table_type_t.instance_type

    def codegen(context, builder, sig, args):
        vkyx__cuvvb, aptsd__pafc = args
        jzmq__bxgsg = cgutils.create_struct_proxy(wlgcf__mniv)(context,
            builder, vkyx__cuvvb)
        if wlgcf__mniv.has_runtime_cols:
            krjy__cuubh = lir.Constant(lir.IntType(64), 0)
            for bvql__cib, t in enumerate(wlgcf__mniv.arr_types):
                hfofd__azq = getattr(jzmq__bxgsg, f'block_{bvql__cib}')
                vqxz__bfq = ListInstance(context, builder, types.List(t),
                    hfofd__azq)
                krjy__cuubh = builder.add(krjy__cuubh, vqxz__bfq.size)
        else:
            krjy__cuubh = lir.Constant(lir.IntType(64), len(wlgcf__mniv.
                arr_types))
        aptsd__pafc, givd__jfe = ListInstance.allocate_ex(context, builder,
            types.List(array_info_type), krjy__cuubh)
        givd__jfe.size = krjy__cuubh
        if wlgcf__mniv.has_runtime_cols:
            pho__mvfou = lir.Constant(lir.IntType(64), 0)
            for bvql__cib, t in enumerate(wlgcf__mniv.arr_types):
                hfofd__azq = getattr(jzmq__bxgsg, f'block_{bvql__cib}')
                vqxz__bfq = ListInstance(context, builder, types.List(t),
                    hfofd__azq)
                yzrc__tbev = vqxz__bfq.size
                with cgutils.for_range(builder, yzrc__tbev) as mswnx__tnig:
                    wgork__kunqv = mswnx__tnig.index
                    arr = vqxz__bfq.getitem(wgork__kunqv)
                    ycmy__baws = signature(array_info_type, t)
                    nwu__ylt = arr,
                    qxw__lwbg = array_to_info_codegen(context, builder,
                        ycmy__baws, nwu__ylt)
                    givd__jfe.inititem(builder.add(pho__mvfou, wgork__kunqv
                        ), qxw__lwbg, incref=False)
                pho__mvfou = builder.add(pho__mvfou, yzrc__tbev)
        else:
            for t, bvql__cib in wlgcf__mniv.type_to_blk.items():
                yzrc__tbev = context.get_constant(types.int64, len(
                    wlgcf__mniv.block_to_arr_ind[bvql__cib]))
                hfofd__azq = getattr(jzmq__bxgsg, f'block_{bvql__cib}')
                vqxz__bfq = ListInstance(context, builder, types.List(t),
                    hfofd__azq)
                iuya__gwado = context.make_constant_array(builder, types.
                    Array(types.int64, 1, 'C'), np.array(wlgcf__mniv.
                    block_to_arr_ind[bvql__cib], dtype=np.int64))
                ayqh__two = context.make_array(types.Array(types.int64, 1, 'C')
                    )(context, builder, iuya__gwado)
                with cgutils.for_range(builder, yzrc__tbev) as mswnx__tnig:
                    wgork__kunqv = mswnx__tnig.index
                    uni__gbgc = _getitem_array_single_int(context, builder,
                        types.int64, types.Array(types.int64, 1, 'C'),
                        ayqh__two, wgork__kunqv)
                    ztacc__suw = signature(types.none, wlgcf__mniv, types.
                        List(t), types.int64, types.int64)
                    bcul__vizdg = (vkyx__cuvvb, hfofd__azq, wgork__kunqv,
                        uni__gbgc)
                    bodo.hiframes.table.ensure_column_unboxed_codegen(context,
                        builder, ztacc__suw, bcul__vizdg)
                    arr = vqxz__bfq.getitem(wgork__kunqv)
                    ycmy__baws = signature(array_info_type, t)
                    nwu__ylt = arr,
                    qxw__lwbg = array_to_info_codegen(context, builder,
                        ycmy__baws, nwu__ylt)
                    givd__jfe.inititem(uni__gbgc, qxw__lwbg, incref=False)
        fzkvu__fgdn = givd__jfe.value
        znmnr__osrm = signature(table_type, types.List(array_info_type))
        onuf__rxxs = fzkvu__fgdn,
        crxnw__kpj = arr_info_list_to_table_codegen(context, builder,
            znmnr__osrm, onuf__rxxs)
        context.nrt.decref(builder, types.List(array_info_type), fzkvu__fgdn)
        return crxnw__kpj
    return table_type(wlgcf__mniv, py_table_type_t), codegen


delete_info_decref_array = types.ExternalFunction('delete_info_decref_array',
    types.void(array_info_type))
delete_table_decref_arrays = types.ExternalFunction(
    'delete_table_decref_arrays', types.void(table_type))


@intrinsic
def delete_table(typingctx, table_t=None):
    assert table_t == table_type

    def codegen(context, builder, sig, args):
        diud__vdb = lir.FunctionType(lir.VoidType(), [lir.IntType(8).
            as_pointer()])
        feu__sndi = cgutils.get_or_insert_function(builder.module,
            diud__vdb, name='delete_table')
        builder.call(feu__sndi, args)
    return types.void(table_t), codegen


@intrinsic
def shuffle_table(typingctx, table_t, n_keys_t, _is_parallel, keep_comm_info_t
    ):
    assert table_t == table_type

    def codegen(context, builder, sig, args):
        diud__vdb = lir.FunctionType(lir.IntType(8).as_pointer(), [lir.
            IntType(8).as_pointer(), lir.IntType(64), lir.IntType(1), lir.
            IntType(32)])
        feu__sndi = cgutils.get_or_insert_function(builder.module,
            diud__vdb, name='shuffle_table')
        hxb__nhiky = builder.call(feu__sndi, args)
        context.compile_internal(builder, lambda :
            check_and_propagate_cpp_exception(), types.none(), [])
        return hxb__nhiky
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
        diud__vdb = lir.FunctionType(lir.VoidType(), [lir.IntType(8).
            as_pointer()])
        feu__sndi = cgutils.get_or_insert_function(builder.module,
            diud__vdb, name='delete_shuffle_info')
        return builder.call(feu__sndi, args)
    return types.void(shuffle_info_t), codegen


@intrinsic
def reverse_shuffle_table(typingctx, table_t, shuffle_info_t=None):

    def codegen(context, builder, sig, args):
        if sig.args[-1] == types.none:
            return context.get_constant_null(table_type)
        diud__vdb = lir.FunctionType(lir.IntType(8).as_pointer(), [lir.
            IntType(8).as_pointer(), lir.IntType(8).as_pointer()])
        feu__sndi = cgutils.get_or_insert_function(builder.module,
            diud__vdb, name='reverse_shuffle_table')
        return builder.call(feu__sndi, args)
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
        diud__vdb = lir.FunctionType(lir.IntType(8).as_pointer(), [lir.
            IntType(8).as_pointer(), lir.IntType(8).as_pointer(), lir.
            IntType(1), lir.IntType(1), lir.IntType(64), lir.IntType(64),
            lir.IntType(64), lir.IntType(8).as_pointer(), lir.IntType(8).
            as_pointer(), lir.IntType(1), lir.IntType(1), lir.IntType(1),
            lir.IntType(1), lir.IntType(1), lir.IntType(1), lir.IntType(8).
            as_pointer(), lir.IntType(8).as_pointer(), lir.IntType(64), lir
            .IntType(8).as_pointer(), lir.IntType(64)])
        feu__sndi = cgutils.get_or_insert_function(builder.module,
            diud__vdb, name='hash_join_table')
        hxb__nhiky = builder.call(feu__sndi, args)
        context.compile_internal(builder, lambda :
            check_and_propagate_cpp_exception(), types.none(), [])
        return hxb__nhiky
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
        diud__vdb = lir.FunctionType(lir.IntType(8).as_pointer(), [lir.
            IntType(8).as_pointer(), lir.IntType(64), lir.IntType(8).
            as_pointer(), lir.IntType(8).as_pointer(), lir.IntType(1)])
        feu__sndi = cgutils.get_or_insert_function(builder.module,
            diud__vdb, name='sort_values_table')
        hxb__nhiky = builder.call(feu__sndi, args)
        context.compile_internal(builder, lambda :
            check_and_propagate_cpp_exception(), types.none(), [])
        return hxb__nhiky
    return table_type(table_t, types.int64, types.voidptr, types.voidptr,
        types.boolean), codegen


@intrinsic
def sample_table(typingctx, table_t, n_keys_t, frac_t, replace_t, parallel_t):
    assert table_t == table_type

    def codegen(context, builder, sig, args):
        diud__vdb = lir.FunctionType(lir.IntType(8).as_pointer(), [lir.
            IntType(8).as_pointer(), lir.IntType(64), lir.DoubleType(), lir
            .IntType(1), lir.IntType(1)])
        feu__sndi = cgutils.get_or_insert_function(builder.module,
            diud__vdb, name='sample_table')
        hxb__nhiky = builder.call(feu__sndi, args)
        context.compile_internal(builder, lambda :
            check_and_propagate_cpp_exception(), types.none(), [])
        return hxb__nhiky
    return table_type(table_t, types.int64, types.float64, types.boolean,
        types.boolean), codegen


@intrinsic
def shuffle_renormalization(typingctx, table_t, random_t, random_seed_t,
    is_parallel_t):
    assert table_t == table_type

    def codegen(context, builder, sig, args):
        diud__vdb = lir.FunctionType(lir.IntType(8).as_pointer(), [lir.
            IntType(8).as_pointer(), lir.IntType(32), lir.IntType(64), lir.
            IntType(1)])
        feu__sndi = cgutils.get_or_insert_function(builder.module,
            diud__vdb, name='shuffle_renormalization')
        hxb__nhiky = builder.call(feu__sndi, args)
        context.compile_internal(builder, lambda :
            check_and_propagate_cpp_exception(), types.none(), [])
        return hxb__nhiky
    return table_type(table_t, types.int32, types.int64, types.boolean
        ), codegen


@intrinsic
def shuffle_renormalization_group(typingctx, table_t, random_t,
    random_seed_t, is_parallel_t, num_ranks_t, ranks_t):
    assert table_t == table_type

    def codegen(context, builder, sig, args):
        diud__vdb = lir.FunctionType(lir.IntType(8).as_pointer(), [lir.
            IntType(8).as_pointer(), lir.IntType(32), lir.IntType(64), lir.
            IntType(1), lir.IntType(64), lir.IntType(8).as_pointer()])
        feu__sndi = cgutils.get_or_insert_function(builder.module,
            diud__vdb, name='shuffle_renormalization_group')
        hxb__nhiky = builder.call(feu__sndi, args)
        context.compile_internal(builder, lambda :
            check_and_propagate_cpp_exception(), types.none(), [])
        return hxb__nhiky
    return table_type(table_t, types.int32, types.int64, types.boolean,
        types.int64, types.voidptr), codegen


@intrinsic
def drop_duplicates_table(typingctx, table_t, parallel_t, nkey_t, keep_t,
    dropna, drop_local_first):
    assert table_t == table_type

    def codegen(context, builder, sig, args):
        diud__vdb = lir.FunctionType(lir.IntType(8).as_pointer(), [lir.
            IntType(8).as_pointer(), lir.IntType(1), lir.IntType(64), lir.
            IntType(64), lir.IntType(1), lir.IntType(1)])
        feu__sndi = cgutils.get_or_insert_function(builder.module,
            diud__vdb, name='drop_duplicates_table')
        hxb__nhiky = builder.call(feu__sndi, args)
        context.compile_internal(builder, lambda :
            check_and_propagate_cpp_exception(), types.none(), [])
        return hxb__nhiky
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
        diud__vdb = lir.FunctionType(lir.IntType(8).as_pointer(), [lir.
            IntType(8).as_pointer(), lir.IntType(64), lir.IntType(8).
            as_pointer(), lir.IntType(8).as_pointer(), lir.IntType(1), lir.
            IntType(8).as_pointer(), lir.IntType(8).as_pointer(), lir.
            IntType(8).as_pointer(), lir.IntType(1), lir.IntType(1), lir.
            IntType(1), lir.IntType(1), lir.IntType(1), lir.IntType(8).
            as_pointer(), lir.IntType(8).as_pointer(), lir.IntType(8).
            as_pointer(), lir.IntType(8).as_pointer()])
        feu__sndi = cgutils.get_or_insert_function(builder.module,
            diud__vdb, name='pivot_groupby_and_aggregate')
        hxb__nhiky = builder.call(feu__sndi, args)
        context.compile_internal(builder, lambda :
            check_and_propagate_cpp_exception(), types.none(), [])
        return hxb__nhiky
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
        diud__vdb = lir.FunctionType(lir.IntType(8).as_pointer(), [lir.
            IntType(8).as_pointer(), lir.IntType(64), lir.IntType(1), lir.
            IntType(8).as_pointer(), lir.IntType(8).as_pointer(), lir.
            IntType(8).as_pointer(), lir.IntType(1), lir.IntType(1), lir.
            IntType(64), lir.IntType(64), lir.IntType(64), lir.IntType(1),
            lir.IntType(1), lir.IntType(1), lir.IntType(8).as_pointer(),
            lir.IntType(8).as_pointer(), lir.IntType(8).as_pointer(), lir.
            IntType(8).as_pointer(), lir.IntType(8).as_pointer()])
        feu__sndi = cgutils.get_or_insert_function(builder.module,
            diud__vdb, name='groupby_and_aggregate')
        hxb__nhiky = builder.call(feu__sndi, args)
        context.compile_internal(builder, lambda :
            check_and_propagate_cpp_exception(), types.none(), [])
        return hxb__nhiky
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
    joht__nptda = array_to_info(in_arr)
    ugc__vkqi = array_to_info(in_values)
    jahat__tvjdf = array_to_info(out_arr)
    nfp__lfoq = arr_info_list_to_table([joht__nptda, ugc__vkqi, jahat__tvjdf])
    _array_isin(jahat__tvjdf, joht__nptda, ugc__vkqi, is_parallel)
    check_and_propagate_cpp_exception()
    delete_table(nfp__lfoq)


_get_search_regex = types.ExternalFunction('get_search_regex', types.void(
    array_info_type, types.bool_, types.voidptr, array_info_type))


@numba.njit(no_cpython_wrapper=True)
def get_search_regex(in_arr, case, pat, out_arr):
    in_arr = decode_if_dict_array(in_arr)
    joht__nptda = array_to_info(in_arr)
    jahat__tvjdf = array_to_info(out_arr)
    _get_search_regex(joht__nptda, case, pat, jahat__tvjdf)
    check_and_propagate_cpp_exception()


def _gen_row_access_intrinsic(col_array_typ, c_ind):
    from llvmlite import ir as lir
    enfq__xkvjq = col_array_typ.dtype
    if isinstance(enfq__xkvjq, types.Number) or enfq__xkvjq in [bodo.
        datetime_date_type, bodo.datetime64ns, bodo.timedelta64ns, types.bool_
        ]:

        @intrinsic
        def getitem_func(typingctx, table_t, ind_t):

            def codegen(context, builder, sig, args):
                svsw__naggc, fefu__piwjo = args
                svsw__naggc = builder.bitcast(svsw__naggc, lir.IntType(8).
                    as_pointer().as_pointer())
                fqi__jykpk = lir.Constant(lir.IntType(64), c_ind)
                pad__rgzzd = builder.load(builder.gep(svsw__naggc, [
                    fqi__jykpk]))
                pad__rgzzd = builder.bitcast(pad__rgzzd, context.
                    get_data_type(enfq__xkvjq).as_pointer())
                return builder.load(builder.gep(pad__rgzzd, [fefu__piwjo]))
            return enfq__xkvjq(types.voidptr, types.int64), codegen
        return getitem_func
    if col_array_typ == bodo.string_array_type:

        @intrinsic
        def getitem_func(typingctx, table_t, ind_t):

            def codegen(context, builder, sig, args):
                svsw__naggc, fefu__piwjo = args
                svsw__naggc = builder.bitcast(svsw__naggc, lir.IntType(8).
                    as_pointer().as_pointer())
                fqi__jykpk = lir.Constant(lir.IntType(64), c_ind)
                pad__rgzzd = builder.load(builder.gep(svsw__naggc, [
                    fqi__jykpk]))
                diud__vdb = lir.FunctionType(lir.IntType(8).as_pointer(), [
                    lir.IntType(8).as_pointer(), lir.IntType(64), lir.
                    IntType(64).as_pointer()])
                coh__irn = cgutils.get_or_insert_function(builder.module,
                    diud__vdb, name='array_info_getitem')
                lcgo__bwfbb = cgutils.alloca_once(builder, lir.IntType(64))
                args = pad__rgzzd, fefu__piwjo, lcgo__bwfbb
                zert__yjdfm = builder.call(coh__irn, args)
                return context.make_tuple(builder, sig.return_type, [
                    zert__yjdfm, builder.load(lcgo__bwfbb)])
            return types.Tuple([types.voidptr, types.int64])(types.voidptr,
                types.int64), codegen
        return getitem_func
    if col_array_typ == bodo.libs.dict_arr_ext.dict_str_arr_type:

        @intrinsic
        def getitem_func(typingctx, table_t, ind_t):

            def codegen(context, builder, sig, args):
                kamhq__beaw = lir.Constant(lir.IntType(64), 1)
                ymjwz__avf = lir.Constant(lir.IntType(64), 2)
                svsw__naggc, fefu__piwjo = args
                svsw__naggc = builder.bitcast(svsw__naggc, lir.IntType(8).
                    as_pointer().as_pointer())
                fqi__jykpk = lir.Constant(lir.IntType(64), c_ind)
                pad__rgzzd = builder.load(builder.gep(svsw__naggc, [
                    fqi__jykpk]))
                diud__vdb = lir.FunctionType(lir.IntType(8).as_pointer(), [
                    lir.IntType(8).as_pointer(), lir.IntType(64)])
                pnguf__gmg = cgutils.get_or_insert_function(builder.module,
                    diud__vdb, name='get_nested_info')
                args = pad__rgzzd, ymjwz__avf
                xguce__uwidu = builder.call(pnguf__gmg, args)
                diud__vdb = lir.FunctionType(lir.IntType(8).as_pointer(), [
                    lir.IntType(8).as_pointer()])
                uhc__ecye = cgutils.get_or_insert_function(builder.module,
                    diud__vdb, name='array_info_getdata1')
                args = xguce__uwidu,
                cbh__jvr = builder.call(uhc__ecye, args)
                cbh__jvr = builder.bitcast(cbh__jvr, context.get_data_type(
                    col_array_typ.indices_dtype).as_pointer())
                jjwkt__dysog = builder.sext(builder.load(builder.gep(
                    cbh__jvr, [fefu__piwjo])), lir.IntType(64))
                args = pad__rgzzd, kamhq__beaw
                gpf__pvo = builder.call(pnguf__gmg, args)
                diud__vdb = lir.FunctionType(lir.IntType(8).as_pointer(), [
                    lir.IntType(8).as_pointer(), lir.IntType(64), lir.
                    IntType(64).as_pointer()])
                coh__irn = cgutils.get_or_insert_function(builder.module,
                    diud__vdb, name='array_info_getitem')
                lcgo__bwfbb = cgutils.alloca_once(builder, lir.IntType(64))
                args = gpf__pvo, jjwkt__dysog, lcgo__bwfbb
                zert__yjdfm = builder.call(coh__irn, args)
                return context.make_tuple(builder, sig.return_type, [
                    zert__yjdfm, builder.load(lcgo__bwfbb)])
            return types.Tuple([types.voidptr, types.int64])(types.voidptr,
                types.int64), codegen
        return getitem_func
    raise BodoError(
        f"General Join Conditions with '{enfq__xkvjq}' column data type not supported"
        )


def _gen_row_na_check_intrinsic(col_array_dtype, c_ind):
    if (isinstance(col_array_dtype, bodo.libs.int_arr_ext.IntegerArrayType) or
        col_array_dtype == bodo.libs.bool_arr_ext.boolean_array or
        is_str_arr_type(col_array_dtype) or isinstance(col_array_dtype,
        types.Array) and col_array_dtype.dtype == bodo.datetime_date_type):

        @intrinsic
        def checkna_func(typingctx, table_t, ind_t):

            def codegen(context, builder, sig, args):
                fbge__txmvt, fefu__piwjo = args
                fbge__txmvt = builder.bitcast(fbge__txmvt, lir.IntType(8).
                    as_pointer().as_pointer())
                fqi__jykpk = lir.Constant(lir.IntType(64), c_ind)
                pad__rgzzd = builder.load(builder.gep(fbge__txmvt, [
                    fqi__jykpk]))
                wjoyi__jnlfe = builder.bitcast(pad__rgzzd, context.
                    get_data_type(types.bool_).as_pointer())
                thdrg__uwhcq = bodo.utils.cg_helpers.get_bitmap_bit(builder,
                    wjoyi__jnlfe, fefu__piwjo)
                fqw__iaua = builder.icmp_unsigned('!=', thdrg__uwhcq, lir.
                    Constant(lir.IntType(8), 0))
                return builder.sext(fqw__iaua, lir.IntType(8))
            return types.int8(types.voidptr, types.int64), codegen
        return checkna_func
    elif isinstance(col_array_dtype, types.Array):
        enfq__xkvjq = col_array_dtype.dtype
        if enfq__xkvjq in [bodo.datetime64ns, bodo.timedelta64ns]:

            @intrinsic
            def checkna_func(typingctx, table_t, ind_t):

                def codegen(context, builder, sig, args):
                    svsw__naggc, fefu__piwjo = args
                    svsw__naggc = builder.bitcast(svsw__naggc, lir.IntType(
                        8).as_pointer().as_pointer())
                    fqi__jykpk = lir.Constant(lir.IntType(64), c_ind)
                    pad__rgzzd = builder.load(builder.gep(svsw__naggc, [
                        fqi__jykpk]))
                    pad__rgzzd = builder.bitcast(pad__rgzzd, context.
                        get_data_type(enfq__xkvjq).as_pointer())
                    mpv__fealy = builder.load(builder.gep(pad__rgzzd, [
                        fefu__piwjo]))
                    fqw__iaua = builder.icmp_unsigned('!=', mpv__fealy, lir
                        .Constant(lir.IntType(64), pd._libs.iNaT))
                    return builder.sext(fqw__iaua, lir.IntType(8))
                return types.int8(types.voidptr, types.int64), codegen
            return checkna_func
        elif isinstance(enfq__xkvjq, types.Float):

            @intrinsic
            def checkna_func(typingctx, table_t, ind_t):

                def codegen(context, builder, sig, args):
                    svsw__naggc, fefu__piwjo = args
                    svsw__naggc = builder.bitcast(svsw__naggc, lir.IntType(
                        8).as_pointer().as_pointer())
                    fqi__jykpk = lir.Constant(lir.IntType(64), c_ind)
                    pad__rgzzd = builder.load(builder.gep(svsw__naggc, [
                        fqi__jykpk]))
                    pad__rgzzd = builder.bitcast(pad__rgzzd, context.
                        get_data_type(enfq__xkvjq).as_pointer())
                    mpv__fealy = builder.load(builder.gep(pad__rgzzd, [
                        fefu__piwjo]))
                    fmv__saer = signature(types.bool_, enfq__xkvjq)
                    thdrg__uwhcq = numba.np.npyfuncs.np_real_isnan_impl(context
                        , builder, fmv__saer, (mpv__fealy,))
                    return builder.not_(builder.sext(thdrg__uwhcq, lir.
                        IntType(8)))
                return types.int8(types.voidptr, types.int64), codegen
            return checkna_func
    raise BodoError(
        f"General Join Conditions with '{col_array_dtype}' column type not supported"
        )
