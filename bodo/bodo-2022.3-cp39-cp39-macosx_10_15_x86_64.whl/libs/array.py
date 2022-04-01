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
        cinum__jkkeh = context.make_helper(builder, arr_type, in_arr)
        in_arr = cinum__jkkeh.data
        arr_type = StructArrayType(arr_type.data, ('dummy',) * len(arr_type
            .data))
    if isinstance(arr_type, ArrayItemArrayType
        ) and arr_type.dtype == string_array_type:
        qhlgk__czwab = context.make_helper(builder, arr_type, in_arr)
        cqyvy__kxr = lir.FunctionType(lir.IntType(8).as_pointer(), [lir.
            IntType(8).as_pointer()])
        ckrr__dnxpp = cgutils.get_or_insert_function(builder.module,
            cqyvy__kxr, name='list_string_array_to_info')
        return builder.call(ckrr__dnxpp, [qhlgk__czwab.meminfo])
    if isinstance(arr_type, (MapArrayType, ArrayItemArrayType, StructArrayType)
        ):

        def get_types(arr_typ):
            if isinstance(arr_typ, MapArrayType):
                return get_types(_get_map_arr_data_type(arr_typ))
            elif isinstance(arr_typ, ArrayItemArrayType):
                return [CTypeEnum.LIST.value] + get_types(arr_typ.dtype)
            elif isinstance(arr_typ, (StructType, StructArrayType)):
                asyj__llhtm = [CTypeEnum.STRUCT.value, len(arr_typ.names)]
                for pwb__bovln in arr_typ.data:
                    asyj__llhtm += get_types(pwb__bovln)
                return asyj__llhtm
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
            inz__ynlv = context.compile_internal(builder, lambda a: len(a),
                types.intp(arr_typ), [arr])
            if isinstance(arr_typ, MapArrayType):
                wko__krvis = context.make_helper(builder, arr_typ, value=arr)
                jxp__nzf = get_lengths(_get_map_arr_data_type(arr_typ),
                    wko__krvis.data)
            elif isinstance(arr_typ, ArrayItemArrayType):
                jypo__wdg = _get_array_item_arr_payload(context, builder,
                    arr_typ, arr)
                jxp__nzf = get_lengths(arr_typ.dtype, jypo__wdg.data)
                jxp__nzf = cgutils.pack_array(builder, [jypo__wdg.n_arrays] +
                    [builder.extract_value(jxp__nzf, awxb__zbd) for
                    awxb__zbd in range(jxp__nzf.type.count)])
            elif isinstance(arr_typ, StructArrayType):
                jypo__wdg = _get_struct_arr_payload(context, builder,
                    arr_typ, arr)
                jxp__nzf = []
                for awxb__zbd, pwb__bovln in enumerate(arr_typ.data):
                    wqhai__vxgf = get_lengths(pwb__bovln, builder.
                        extract_value(jypo__wdg.data, awxb__zbd))
                    jxp__nzf += [builder.extract_value(wqhai__vxgf,
                        utjes__tgfm) for utjes__tgfm in range(wqhai__vxgf.
                        type.count)]
                jxp__nzf = cgutils.pack_array(builder, [inz__ynlv, context.
                    get_constant(types.int64, -1)] + jxp__nzf)
            elif isinstance(arr_typ, (IntegerArrayType, DecimalArrayType,
                types.Array)) or arr_typ in (boolean_array,
                datetime_date_array_type, string_array_type, binary_array_type
                ):
                jxp__nzf = cgutils.pack_array(builder, [inz__ynlv])
            else:
                raise BodoError(
                    f'array_to_info: unsupported type for subarray {arr_typ}')
            return jxp__nzf

        def get_buffers(arr_typ, arr):
            if isinstance(arr_typ, MapArrayType):
                wko__krvis = context.make_helper(builder, arr_typ, value=arr)
                mdf__fslj = get_buffers(_get_map_arr_data_type(arr_typ),
                    wko__krvis.data)
            elif isinstance(arr_typ, ArrayItemArrayType):
                jypo__wdg = _get_array_item_arr_payload(context, builder,
                    arr_typ, arr)
                irji__teulj = get_buffers(arr_typ.dtype, jypo__wdg.data)
                nhvgn__iwu = context.make_array(types.Array(offset_type, 1,
                    'C'))(context, builder, jypo__wdg.offsets)
                iqta__vmd = builder.bitcast(nhvgn__iwu.data, lir.IntType(8)
                    .as_pointer())
                wuek__vlml = context.make_array(types.Array(types.uint8, 1,
                    'C'))(context, builder, jypo__wdg.null_bitmap)
                tarw__kin = builder.bitcast(wuek__vlml.data, lir.IntType(8)
                    .as_pointer())
                mdf__fslj = cgutils.pack_array(builder, [iqta__vmd,
                    tarw__kin] + [builder.extract_value(irji__teulj,
                    awxb__zbd) for awxb__zbd in range(irji__teulj.type.count)])
            elif isinstance(arr_typ, StructArrayType):
                jypo__wdg = _get_struct_arr_payload(context, builder,
                    arr_typ, arr)
                irji__teulj = []
                for awxb__zbd, pwb__bovln in enumerate(arr_typ.data):
                    npmfu__atkgn = get_buffers(pwb__bovln, builder.
                        extract_value(jypo__wdg.data, awxb__zbd))
                    irji__teulj += [builder.extract_value(npmfu__atkgn,
                        utjes__tgfm) for utjes__tgfm in range(npmfu__atkgn.
                        type.count)]
                wuek__vlml = context.make_array(types.Array(types.uint8, 1,
                    'C'))(context, builder, jypo__wdg.null_bitmap)
                tarw__kin = builder.bitcast(wuek__vlml.data, lir.IntType(8)
                    .as_pointer())
                mdf__fslj = cgutils.pack_array(builder, [tarw__kin] +
                    irji__teulj)
            elif isinstance(arr_typ, (IntegerArrayType, DecimalArrayType)
                ) or arr_typ in (boolean_array, datetime_date_array_type):
                vwdy__sbeoz = arr_typ.dtype
                if isinstance(arr_typ, DecimalArrayType):
                    vwdy__sbeoz = int128_type
                elif arr_typ == datetime_date_array_type:
                    vwdy__sbeoz = types.int64
                arr = cgutils.create_struct_proxy(arr_typ)(context, builder,
                    arr)
                lhj__uhuwa = context.make_array(types.Array(vwdy__sbeoz, 1,
                    'C'))(context, builder, arr.data)
                wuek__vlml = context.make_array(types.Array(types.uint8, 1,
                    'C'))(context, builder, arr.null_bitmap)
                mtht__rttp = builder.bitcast(lhj__uhuwa.data, lir.IntType(8
                    ).as_pointer())
                tarw__kin = builder.bitcast(wuek__vlml.data, lir.IntType(8)
                    .as_pointer())
                mdf__fslj = cgutils.pack_array(builder, [tarw__kin, mtht__rttp]
                    )
            elif arr_typ in (string_array_type, binary_array_type):
                jypo__wdg = _get_str_binary_arr_payload(context, builder,
                    arr, arr_typ)
                qow__cxffe = context.make_helper(builder, offset_arr_type,
                    jypo__wdg.offsets).data
                ncx__krijk = context.make_helper(builder, char_arr_type,
                    jypo__wdg.data).data
                zxav__vrpy = context.make_helper(builder,
                    null_bitmap_arr_type, jypo__wdg.null_bitmap).data
                mdf__fslj = cgutils.pack_array(builder, [builder.bitcast(
                    qow__cxffe, lir.IntType(8).as_pointer()), builder.
                    bitcast(zxav__vrpy, lir.IntType(8).as_pointer()),
                    builder.bitcast(ncx__krijk, lir.IntType(8).as_pointer())])
            elif isinstance(arr_typ, types.Array):
                arr = context.make_array(arr_typ)(context, builder, arr)
                mtht__rttp = builder.bitcast(arr.data, lir.IntType(8).
                    as_pointer())
                sivt__vstbs = lir.Constant(lir.IntType(8).as_pointer(), None)
                mdf__fslj = cgutils.pack_array(builder, [sivt__vstbs,
                    mtht__rttp])
            else:
                raise RuntimeError(
                    'array_to_info: unsupported type for subarray ' + str(
                    arr_typ))
            return mdf__fslj

        def get_field_names(arr_typ):
            rwmnl__rez = []
            if isinstance(arr_typ, StructArrayType):
                for skw__gaom, gbzmt__xsbeo in zip(arr_typ.dtype.names,
                    arr_typ.data):
                    rwmnl__rez.append(skw__gaom)
                    rwmnl__rez += get_field_names(gbzmt__xsbeo)
            elif isinstance(arr_typ, ArrayItemArrayType):
                rwmnl__rez += get_field_names(arr_typ.dtype)
            elif isinstance(arr_typ, MapArrayType):
                rwmnl__rez += get_field_names(_get_map_arr_data_type(arr_typ))
            return rwmnl__rez
        asyj__llhtm = get_types(arr_type)
        gexxv__aff = cgutils.pack_array(builder, [context.get_constant(
            types.int32, t) for t in asyj__llhtm])
        xnd__ozt = cgutils.alloca_once_value(builder, gexxv__aff)
        jxp__nzf = get_lengths(arr_type, in_arr)
        lengths_ptr = cgutils.alloca_once_value(builder, jxp__nzf)
        mdf__fslj = get_buffers(arr_type, in_arr)
        ikj__zfye = cgutils.alloca_once_value(builder, mdf__fslj)
        rwmnl__rez = get_field_names(arr_type)
        if len(rwmnl__rez) == 0:
            rwmnl__rez = ['irrelevant']
        urr__vqmy = cgutils.pack_array(builder, [context.
            insert_const_string(builder.module, a) for a in rwmnl__rez])
        pihey__etxl = cgutils.alloca_once_value(builder, urr__vqmy)
        if isinstance(arr_type, MapArrayType):
            khc__txxy = _get_map_arr_data_type(arr_type)
            rywpx__ujmnv = context.make_helper(builder, arr_type, value=in_arr)
            qmaw__plop = rywpx__ujmnv.data
        else:
            khc__txxy = arr_type
            qmaw__plop = in_arr
        hsb__pueh = context.make_helper(builder, khc__txxy, qmaw__plop)
        cqyvy__kxr = lir.FunctionType(lir.IntType(8).as_pointer(), [lir.
            IntType(32).as_pointer(), lir.IntType(8).as_pointer().
            as_pointer(), lir.IntType(64).as_pointer(), lir.IntType(8).
            as_pointer(), lir.IntType(8).as_pointer()])
        ckrr__dnxpp = cgutils.get_or_insert_function(builder.module,
            cqyvy__kxr, name='nested_array_to_info')
        njo__hffa = builder.call(ckrr__dnxpp, [builder.bitcast(xnd__ozt,
            lir.IntType(32).as_pointer()), builder.bitcast(ikj__zfye, lir.
            IntType(8).as_pointer().as_pointer()), builder.bitcast(
            lengths_ptr, lir.IntType(64).as_pointer()), builder.bitcast(
            pihey__etxl, lir.IntType(8).as_pointer()), hsb__pueh.meminfo])
        context.compile_internal(builder, lambda :
            check_and_propagate_cpp_exception(), types.none(), [])
        return njo__hffa
    if arr_type in (string_array_type, binary_array_type):
        hsqwd__qzbo = context.make_helper(builder, arr_type, in_arr)
        lql__dmv = ArrayItemArrayType(char_arr_type)
        qhlgk__czwab = context.make_helper(builder, lql__dmv, hsqwd__qzbo.data)
        jypo__wdg = _get_str_binary_arr_payload(context, builder, in_arr,
            arr_type)
        qow__cxffe = context.make_helper(builder, offset_arr_type,
            jypo__wdg.offsets).data
        ncx__krijk = context.make_helper(builder, char_arr_type, jypo__wdg.data
            ).data
        zxav__vrpy = context.make_helper(builder, null_bitmap_arr_type,
            jypo__wdg.null_bitmap).data
        eknqq__bik = builder.zext(builder.load(builder.gep(qow__cxffe, [
            jypo__wdg.n_arrays])), lir.IntType(64))
        rgu__bwg = context.get_constant(types.int32, int(arr_type ==
            binary_array_type))
        cqyvy__kxr = lir.FunctionType(lir.IntType(8).as_pointer(), [lir.
            IntType(64), lir.IntType(64), lir.IntType(8).as_pointer(), lir.
            IntType(offset_type.bitwidth).as_pointer(), lir.IntType(8).
            as_pointer(), lir.IntType(8).as_pointer(), lir.IntType(32)])
        ckrr__dnxpp = cgutils.get_or_insert_function(builder.module,
            cqyvy__kxr, name='string_array_to_info')
        return builder.call(ckrr__dnxpp, [jypo__wdg.n_arrays, eknqq__bik,
            ncx__krijk, qow__cxffe, zxav__vrpy, qhlgk__czwab.meminfo, rgu__bwg]
            )
    if arr_type == bodo.dict_str_arr_type:
        arr = cgutils.create_struct_proxy(arr_type)(context, builder, in_arr)
        hfgum__gckt = arr.data
        tff__wkf = arr.indices
        sig = array_info_type(arr_type.data)
        oce__zqi = array_to_info_codegen(context, builder, sig, (
            hfgum__gckt,), False)
        sig = array_info_type(bodo.libs.dict_arr_ext.dict_indices_arr_type)
        rbos__uti = array_to_info_codegen(context, builder, sig, (tff__wkf,
            ), False)
        fvudq__wuj = cgutils.create_struct_proxy(bodo.libs.dict_arr_ext.
            dict_indices_arr_type)(context, builder, tff__wkf)
        tarw__kin = context.make_array(types.Array(types.uint8, 1, 'C'))(
            context, builder, fvudq__wuj.null_bitmap).data
        cqyvy__kxr = lir.FunctionType(lir.IntType(8).as_pointer(), [lir.
            IntType(8).as_pointer(), lir.IntType(8).as_pointer(), lir.
            IntType(8).as_pointer(), lir.IntType(32)])
        ckrr__dnxpp = cgutils.get_or_insert_function(builder.module,
            cqyvy__kxr, name='dict_str_array_to_info')
        saoi__yih = builder.zext(arr.has_global_dictionary, lir.IntType(32))
        return builder.call(ckrr__dnxpp, [oce__zqi, rbos__uti, builder.
            bitcast(tarw__kin, lir.IntType(8).as_pointer()), saoi__yih])
    kyfy__hvx = False
    if isinstance(arr_type, CategoricalArrayType):
        context.nrt.decref(builder, arr_type, in_arr)
        jgpny__qrmaq = context.compile_internal(builder, lambda a: len(a.
            dtype.categories), types.intp(arr_type), [in_arr])
        in_arr = cgutils.create_struct_proxy(arr_type)(context, builder, in_arr
            ).codes
        vasj__mtkfa = get_categories_int_type(arr_type.dtype)
        arr_type = types.Array(vasj__mtkfa, 1, 'C')
        kyfy__hvx = True
        context.nrt.incref(builder, arr_type, in_arr)
    if isinstance(arr_type, bodo.DatetimeArrayType):
        if kyfy__hvx:
            raise BodoError(
                'array_to_info(): Categorical PandasDatetimeArrayType not supported'
                )
        in_arr = cgutils.create_struct_proxy(arr_type)(context, builder, in_arr
            ).data
        arr_type = arr_type.data_array_type
    if isinstance(arr_type, types.Array):
        arr = context.make_array(arr_type)(context, builder, in_arr)
        assert arr_type.ndim == 1, 'only 1D array shuffle supported'
        inz__ynlv = builder.extract_value(arr.shape, 0)
        woog__knsl = arr_type.dtype
        ssbo__qzee = numba_to_c_type(woog__knsl)
        okb__tpqf = cgutils.alloca_once_value(builder, lir.Constant(lir.
            IntType(32), ssbo__qzee))
        if kyfy__hvx:
            cqyvy__kxr = lir.FunctionType(lir.IntType(8).as_pointer(), [lir
                .IntType(64), lir.IntType(8).as_pointer(), lir.IntType(32),
                lir.IntType(64), lir.IntType(8).as_pointer()])
            ckrr__dnxpp = cgutils.get_or_insert_function(builder.module,
                cqyvy__kxr, name='categorical_array_to_info')
            return builder.call(ckrr__dnxpp, [inz__ynlv, builder.bitcast(
                arr.data, lir.IntType(8).as_pointer()), builder.load(
                okb__tpqf), jgpny__qrmaq, arr.meminfo])
        else:
            cqyvy__kxr = lir.FunctionType(lir.IntType(8).as_pointer(), [lir
                .IntType(64), lir.IntType(8).as_pointer(), lir.IntType(32),
                lir.IntType(8).as_pointer()])
            ckrr__dnxpp = cgutils.get_or_insert_function(builder.module,
                cqyvy__kxr, name='numpy_array_to_info')
            return builder.call(ckrr__dnxpp, [inz__ynlv, builder.bitcast(
                arr.data, lir.IntType(8).as_pointer()), builder.load(
                okb__tpqf), arr.meminfo])
    if isinstance(arr_type, (IntegerArrayType, DecimalArrayType)
        ) or arr_type in (boolean_array, datetime_date_array_type):
        arr = cgutils.create_struct_proxy(arr_type)(context, builder, in_arr)
        woog__knsl = arr_type.dtype
        vwdy__sbeoz = woog__knsl
        if isinstance(arr_type, DecimalArrayType):
            vwdy__sbeoz = int128_type
        if arr_type == datetime_date_array_type:
            vwdy__sbeoz = types.int64
        lhj__uhuwa = context.make_array(types.Array(vwdy__sbeoz, 1, 'C'))(
            context, builder, arr.data)
        inz__ynlv = builder.extract_value(lhj__uhuwa.shape, 0)
        xtwi__aahgk = context.make_array(types.Array(types.uint8, 1, 'C'))(
            context, builder, arr.null_bitmap)
        ssbo__qzee = numba_to_c_type(woog__knsl)
        okb__tpqf = cgutils.alloca_once_value(builder, lir.Constant(lir.
            IntType(32), ssbo__qzee))
        if isinstance(arr_type, DecimalArrayType):
            cqyvy__kxr = lir.FunctionType(lir.IntType(8).as_pointer(), [lir
                .IntType(64), lir.IntType(8).as_pointer(), lir.IntType(32),
                lir.IntType(8).as_pointer(), lir.IntType(8).as_pointer(),
                lir.IntType(8).as_pointer(), lir.IntType(32), lir.IntType(32)])
            ckrr__dnxpp = cgutils.get_or_insert_function(builder.module,
                cqyvy__kxr, name='decimal_array_to_info')
            return builder.call(ckrr__dnxpp, [inz__ynlv, builder.bitcast(
                lhj__uhuwa.data, lir.IntType(8).as_pointer()), builder.load
                (okb__tpqf), builder.bitcast(xtwi__aahgk.data, lir.IntType(
                8).as_pointer()), lhj__uhuwa.meminfo, xtwi__aahgk.meminfo,
                context.get_constant(types.int32, arr_type.precision),
                context.get_constant(types.int32, arr_type.scale)])
        else:
            cqyvy__kxr = lir.FunctionType(lir.IntType(8).as_pointer(), [lir
                .IntType(64), lir.IntType(8).as_pointer(), lir.IntType(32),
                lir.IntType(8).as_pointer(), lir.IntType(8).as_pointer(),
                lir.IntType(8).as_pointer()])
            ckrr__dnxpp = cgutils.get_or_insert_function(builder.module,
                cqyvy__kxr, name='nullable_array_to_info')
            return builder.call(ckrr__dnxpp, [inz__ynlv, builder.bitcast(
                lhj__uhuwa.data, lir.IntType(8).as_pointer()), builder.load
                (okb__tpqf), builder.bitcast(xtwi__aahgk.data, lir.IntType(
                8).as_pointer()), lhj__uhuwa.meminfo, xtwi__aahgk.meminfo])
    if isinstance(arr_type, IntervalArrayType):
        assert isinstance(arr_type.arr_type, types.Array
            ), 'array_to_info(): only IntervalArrayType with Numpy arrays supported'
        arr = cgutils.create_struct_proxy(arr_type)(context, builder, in_arr)
        mqzsi__yxib = context.make_array(arr_type.arr_type)(context,
            builder, arr.left)
        tzji__zboax = context.make_array(arr_type.arr_type)(context,
            builder, arr.right)
        inz__ynlv = builder.extract_value(mqzsi__yxib.shape, 0)
        ssbo__qzee = numba_to_c_type(arr_type.arr_type.dtype)
        okb__tpqf = cgutils.alloca_once_value(builder, lir.Constant(lir.
            IntType(32), ssbo__qzee))
        cqyvy__kxr = lir.FunctionType(lir.IntType(8).as_pointer(), [lir.
            IntType(64), lir.IntType(8).as_pointer(), lir.IntType(8).
            as_pointer(), lir.IntType(32), lir.IntType(8).as_pointer(), lir
            .IntType(8).as_pointer()])
        ckrr__dnxpp = cgutils.get_or_insert_function(builder.module,
            cqyvy__kxr, name='interval_array_to_info')
        return builder.call(ckrr__dnxpp, [inz__ynlv, builder.bitcast(
            mqzsi__yxib.data, lir.IntType(8).as_pointer()), builder.bitcast
            (tzji__zboax.data, lir.IntType(8).as_pointer()), builder.load(
            okb__tpqf), mqzsi__yxib.meminfo, tzji__zboax.meminfo])
    raise_bodo_error(f'array_to_info(): array type {arr_type} is not supported'
        )


def _lower_info_to_array_numpy(arr_type, context, builder, in_info):
    assert arr_type.ndim == 1, 'only 1D array supported'
    arr = context.make_array(arr_type)(context, builder)
    bft__dsq = cgutils.alloca_once(builder, lir.IntType(64))
    mtht__rttp = cgutils.alloca_once(builder, lir.IntType(8).as_pointer())
    nqqd__ndx = cgutils.alloca_once(builder, lir.IntType(8).as_pointer())
    cqyvy__kxr = lir.FunctionType(lir.VoidType(), [lir.IntType(8).
        as_pointer(), lir.IntType(64).as_pointer(), lir.IntType(8).
        as_pointer().as_pointer(), lir.IntType(8).as_pointer().as_pointer()])
    ckrr__dnxpp = cgutils.get_or_insert_function(builder.module, cqyvy__kxr,
        name='info_to_numpy_array')
    builder.call(ckrr__dnxpp, [in_info, bft__dsq, mtht__rttp, nqqd__ndx])
    context.compile_internal(builder, lambda :
        check_and_propagate_cpp_exception(), types.none(), [])
    art__ldtdu = context.get_value_type(types.intp)
    mil__llhh = cgutils.pack_array(builder, [builder.load(bft__dsq)], ty=
        art__ldtdu)
    lyv__ttkh = context.get_constant(types.intp, context.get_abi_sizeof(
        context.get_data_type(arr_type.dtype)))
    jjce__vkaya = cgutils.pack_array(builder, [lyv__ttkh], ty=art__ldtdu)
    ncx__krijk = builder.bitcast(builder.load(mtht__rttp), context.
        get_data_type(arr_type.dtype).as_pointer())
    numba.np.arrayobj.populate_array(arr, data=ncx__krijk, shape=mil__llhh,
        strides=jjce__vkaya, itemsize=lyv__ttkh, meminfo=builder.load(
        nqqd__ndx))
    return arr._getvalue()


def _lower_info_to_array_list_string_array(arr_type, context, builder, in_info
    ):
    htds__fqkm = context.make_helper(builder, arr_type)
    cqyvy__kxr = lir.FunctionType(lir.VoidType(), [lir.IntType(8).
        as_pointer(), lir.IntType(8).as_pointer().as_pointer()])
    ckrr__dnxpp = cgutils.get_or_insert_function(builder.module, cqyvy__kxr,
        name='info_to_list_string_array')
    builder.call(ckrr__dnxpp, [in_info, htds__fqkm._get_ptr_by_name('meminfo')]
        )
    context.compile_internal(builder, lambda :
        check_and_propagate_cpp_exception(), types.none(), [])
    return htds__fqkm._getvalue()


def nested_to_array(context, builder, arr_typ, lengths_ptr, array_infos_ptr,
    lengths_pos, infos_pos):
    ejxhr__tlab = context.get_data_type(array_info_type)
    if isinstance(arr_typ, ArrayItemArrayType):
        vgwuq__neah = lengths_pos
        uum__yue = infos_pos
        hjhl__dqegy, lengths_pos, infos_pos = nested_to_array(context,
            builder, arr_typ.dtype, lengths_ptr, array_infos_ptr, 
            lengths_pos + 1, infos_pos + 2)
        qpoc__nlc = ArrayItemArrayPayloadType(arr_typ)
        zuw__mtfuy = context.get_data_type(qpoc__nlc)
        zwc__xagwd = context.get_abi_sizeof(zuw__mtfuy)
        mikjv__asi = define_array_item_dtor(context, builder, arr_typ,
            qpoc__nlc)
        kym__smofd = context.nrt.meminfo_alloc_dtor(builder, context.
            get_constant(types.uintp, zwc__xagwd), mikjv__asi)
        ljzbf__iszzv = context.nrt.meminfo_data(builder, kym__smofd)
        ggbmm__rinz = builder.bitcast(ljzbf__iszzv, zuw__mtfuy.as_pointer())
        jypo__wdg = cgutils.create_struct_proxy(qpoc__nlc)(context, builder)
        jypo__wdg.n_arrays = builder.extract_value(builder.load(lengths_ptr
            ), vgwuq__neah)
        jypo__wdg.data = hjhl__dqegy
        hzgl__mmcc = builder.load(array_infos_ptr)
        afu__lojc = builder.bitcast(builder.extract_value(hzgl__mmcc,
            uum__yue), ejxhr__tlab)
        jypo__wdg.offsets = _lower_info_to_array_numpy(types.Array(
            offset_type, 1, 'C'), context, builder, afu__lojc)
        cgcu__vvys = builder.bitcast(builder.extract_value(hzgl__mmcc, 
            uum__yue + 1), ejxhr__tlab)
        jypo__wdg.null_bitmap = _lower_info_to_array_numpy(types.Array(
            types.uint8, 1, 'C'), context, builder, cgcu__vvys)
        builder.store(jypo__wdg._getvalue(), ggbmm__rinz)
        qhlgk__czwab = context.make_helper(builder, arr_typ)
        qhlgk__czwab.meminfo = kym__smofd
        return qhlgk__czwab._getvalue(), lengths_pos, infos_pos
    elif isinstance(arr_typ, StructArrayType):
        cyt__gras = []
        uum__yue = infos_pos
        lengths_pos += 1
        infos_pos += 1
        for sito__jzngf in arr_typ.data:
            hjhl__dqegy, lengths_pos, infos_pos = nested_to_array(context,
                builder, sito__jzngf, lengths_ptr, array_infos_ptr,
                lengths_pos, infos_pos)
            cyt__gras.append(hjhl__dqegy)
        qpoc__nlc = StructArrayPayloadType(arr_typ.data)
        zuw__mtfuy = context.get_value_type(qpoc__nlc)
        zwc__xagwd = context.get_abi_sizeof(zuw__mtfuy)
        mikjv__asi = define_struct_arr_dtor(context, builder, arr_typ,
            qpoc__nlc)
        kym__smofd = context.nrt.meminfo_alloc_dtor(builder, context.
            get_constant(types.uintp, zwc__xagwd), mikjv__asi)
        ljzbf__iszzv = context.nrt.meminfo_data(builder, kym__smofd)
        ggbmm__rinz = builder.bitcast(ljzbf__iszzv, zuw__mtfuy.as_pointer())
        jypo__wdg = cgutils.create_struct_proxy(qpoc__nlc)(context, builder)
        jypo__wdg.data = cgutils.pack_array(builder, cyt__gras
            ) if types.is_homogeneous(*arr_typ.data) else cgutils.pack_struct(
            builder, cyt__gras)
        hzgl__mmcc = builder.load(array_infos_ptr)
        cgcu__vvys = builder.bitcast(builder.extract_value(hzgl__mmcc,
            uum__yue), ejxhr__tlab)
        jypo__wdg.null_bitmap = _lower_info_to_array_numpy(types.Array(
            types.uint8, 1, 'C'), context, builder, cgcu__vvys)
        builder.store(jypo__wdg._getvalue(), ggbmm__rinz)
        zwd__aww = context.make_helper(builder, arr_typ)
        zwd__aww.meminfo = kym__smofd
        return zwd__aww._getvalue(), lengths_pos, infos_pos
    elif arr_typ in (string_array_type, binary_array_type):
        hzgl__mmcc = builder.load(array_infos_ptr)
        yofq__qwzz = builder.bitcast(builder.extract_value(hzgl__mmcc,
            infos_pos), ejxhr__tlab)
        hsqwd__qzbo = context.make_helper(builder, arr_typ)
        lql__dmv = ArrayItemArrayType(char_arr_type)
        qhlgk__czwab = context.make_helper(builder, lql__dmv)
        cqyvy__kxr = lir.FunctionType(lir.VoidType(), [lir.IntType(8).
            as_pointer(), lir.IntType(8).as_pointer().as_pointer()])
        ckrr__dnxpp = cgutils.get_or_insert_function(builder.module,
            cqyvy__kxr, name='info_to_string_array')
        builder.call(ckrr__dnxpp, [yofq__qwzz, qhlgk__czwab.
            _get_ptr_by_name('meminfo')])
        context.compile_internal(builder, lambda :
            check_and_propagate_cpp_exception(), types.none(), [])
        hsqwd__qzbo.data = qhlgk__czwab._getvalue()
        return hsqwd__qzbo._getvalue(), lengths_pos + 1, infos_pos + 1
    elif isinstance(arr_typ, types.Array):
        hzgl__mmcc = builder.load(array_infos_ptr)
        hxgc__uwmfn = builder.bitcast(builder.extract_value(hzgl__mmcc, 
            infos_pos + 1), ejxhr__tlab)
        return _lower_info_to_array_numpy(arr_typ, context, builder,
            hxgc__uwmfn), lengths_pos + 1, infos_pos + 2
    elif isinstance(arr_typ, (IntegerArrayType, DecimalArrayType)
        ) or arr_typ in (boolean_array, datetime_date_array_type):
        arr = cgutils.create_struct_proxy(arr_typ)(context, builder)
        vwdy__sbeoz = arr_typ.dtype
        if isinstance(arr_typ, DecimalArrayType):
            vwdy__sbeoz = int128_type
        elif arr_typ == datetime_date_array_type:
            vwdy__sbeoz = types.int64
        hzgl__mmcc = builder.load(array_infos_ptr)
        cgcu__vvys = builder.bitcast(builder.extract_value(hzgl__mmcc,
            infos_pos), ejxhr__tlab)
        arr.null_bitmap = _lower_info_to_array_numpy(types.Array(types.
            uint8, 1, 'C'), context, builder, cgcu__vvys)
        hxgc__uwmfn = builder.bitcast(builder.extract_value(hzgl__mmcc, 
            infos_pos + 1), ejxhr__tlab)
        arr.data = _lower_info_to_array_numpy(types.Array(vwdy__sbeoz, 1,
            'C'), context, builder, hxgc__uwmfn)
        return arr._getvalue(), lengths_pos + 1, infos_pos + 2


def info_to_array_codegen(context, builder, sig, args):
    array_type = sig.args[1]
    arr_type = array_type.instance_type if isinstance(array_type, types.TypeRef
        ) else array_type
    in_info, wztb__qdb = args
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
                return 1 + sum([get_num_arrays(sito__jzngf) for sito__jzngf in
                    arr_typ.data])
            else:
                return 1

        def get_num_infos(arr_typ):
            if isinstance(arr_typ, ArrayItemArrayType):
                return 2 + get_num_infos(arr_typ.dtype)
            elif isinstance(arr_typ, StructArrayType):
                return 1 + sum([get_num_infos(sito__jzngf) for sito__jzngf in
                    arr_typ.data])
            elif arr_typ in (string_array_type, binary_array_type):
                return 1
            else:
                return 2
        if isinstance(arr_type, TupleArrayType):
            qig__qjda = StructArrayType(arr_type.data, ('dummy',) * len(
                arr_type.data))
        elif isinstance(arr_type, MapArrayType):
            qig__qjda = _get_map_arr_data_type(arr_type)
        else:
            qig__qjda = arr_type
        wjpt__cxdba = get_num_arrays(qig__qjda)
        jxp__nzf = cgutils.pack_array(builder, [lir.Constant(lir.IntType(64
            ), 0) for wztb__qdb in range(wjpt__cxdba)])
        lengths_ptr = cgutils.alloca_once_value(builder, jxp__nzf)
        sivt__vstbs = lir.Constant(lir.IntType(8).as_pointer(), None)
        obaxq__hfxnr = cgutils.pack_array(builder, [sivt__vstbs for
            wztb__qdb in range(get_num_infos(qig__qjda))])
        array_infos_ptr = cgutils.alloca_once_value(builder, obaxq__hfxnr)
        cqyvy__kxr = lir.FunctionType(lir.VoidType(), [lir.IntType(8).
            as_pointer(), lir.IntType(64).as_pointer(), lir.IntType(8).
            as_pointer().as_pointer()])
        ckrr__dnxpp = cgutils.get_or_insert_function(builder.module,
            cqyvy__kxr, name='info_to_nested_array')
        builder.call(ckrr__dnxpp, [in_info, builder.bitcast(lengths_ptr,
            lir.IntType(64).as_pointer()), builder.bitcast(array_infos_ptr,
            lir.IntType(8).as_pointer().as_pointer())])
        context.compile_internal(builder, lambda :
            check_and_propagate_cpp_exception(), types.none(), [])
        arr, wztb__qdb, wztb__qdb = nested_to_array(context, builder,
            qig__qjda, lengths_ptr, array_infos_ptr, 0, 0)
        if isinstance(arr_type, TupleArrayType):
            cinum__jkkeh = context.make_helper(builder, arr_type)
            cinum__jkkeh.data = arr
            context.nrt.incref(builder, qig__qjda, arr)
            arr = cinum__jkkeh._getvalue()
        elif isinstance(arr_type, MapArrayType):
            sig = signature(arr_type, qig__qjda)
            arr = init_map_arr_codegen(context, builder, sig, (arr,))
        return arr
    if arr_type in (string_array_type, binary_array_type):
        hsqwd__qzbo = context.make_helper(builder, arr_type)
        lql__dmv = ArrayItemArrayType(char_arr_type)
        qhlgk__czwab = context.make_helper(builder, lql__dmv)
        cqyvy__kxr = lir.FunctionType(lir.VoidType(), [lir.IntType(8).
            as_pointer(), lir.IntType(8).as_pointer().as_pointer()])
        ckrr__dnxpp = cgutils.get_or_insert_function(builder.module,
            cqyvy__kxr, name='info_to_string_array')
        builder.call(ckrr__dnxpp, [in_info, qhlgk__czwab._get_ptr_by_name(
            'meminfo')])
        context.compile_internal(builder, lambda :
            check_and_propagate_cpp_exception(), types.none(), [])
        hsqwd__qzbo.data = qhlgk__czwab._getvalue()
        return hsqwd__qzbo._getvalue()
    if arr_type == bodo.dict_str_arr_type:
        cqyvy__kxr = lir.FunctionType(lir.IntType(8).as_pointer(), [lir.
            IntType(8).as_pointer(), lir.IntType(32)])
        ckrr__dnxpp = cgutils.get_or_insert_function(builder.module,
            cqyvy__kxr, name='get_nested_info')
        oce__zqi = builder.call(ckrr__dnxpp, [in_info, lir.Constant(lir.
            IntType(32), 1)])
        rbos__uti = builder.call(ckrr__dnxpp, [in_info, lir.Constant(lir.
            IntType(32), 2)])
        pwgdl__kuu = context.make_helper(builder, arr_type)
        sig = arr_type.data(array_info_type, arr_type.data)
        pwgdl__kuu.data = info_to_array_codegen(context, builder, sig, (
            oce__zqi, context.get_constant_null(arr_type.data)))
        pww__yqo = bodo.libs.dict_arr_ext.dict_indices_arr_type
        sig = pww__yqo(array_info_type, pww__yqo)
        pwgdl__kuu.indices = info_to_array_codegen(context, builder, sig, (
            rbos__uti, context.get_constant_null(pww__yqo)))
        cqyvy__kxr = lir.FunctionType(lir.IntType(32), [lir.IntType(8).
            as_pointer()])
        ckrr__dnxpp = cgutils.get_or_insert_function(builder.module,
            cqyvy__kxr, name='get_has_global_dictionary')
        saoi__yih = builder.call(ckrr__dnxpp, [in_info])
        pwgdl__kuu.has_global_dictionary = builder.trunc(saoi__yih, cgutils
            .bool_t)
        return pwgdl__kuu._getvalue()
    if isinstance(arr_type, CategoricalArrayType):
        out_arr = cgutils.create_struct_proxy(arr_type)(context, builder)
        vasj__mtkfa = get_categories_int_type(arr_type.dtype)
        mqe__xgamc = types.Array(vasj__mtkfa, 1, 'C')
        out_arr.codes = _lower_info_to_array_numpy(mqe__xgamc, context,
            builder, in_info)
        if isinstance(array_type, types.TypeRef):
            assert arr_type.dtype.categories is not None, 'info_to_array: unknown categories'
            is_ordered = arr_type.dtype.ordered
            dow__ijsij = pd.CategoricalDtype(arr_type.dtype.categories,
                is_ordered).categories.values
            new_cats_tup = MetaType(tuple(dow__ijsij))
            int_type = arr_type.dtype.int_type
            ttjvd__wzqza = bodo.typeof(dow__ijsij)
            lrjx__uvy = context.get_constant_generic(builder, ttjvd__wzqza,
                dow__ijsij)
            woog__knsl = context.compile_internal(builder, lambda c_arr:
                bodo.hiframes.pd_categorical_ext.init_cat_dtype(bodo.utils.
                conversion.index_from_array(c_arr), is_ordered, int_type,
                new_cats_tup), arr_type.dtype(ttjvd__wzqza), [lrjx__uvy])
        else:
            woog__knsl = cgutils.create_struct_proxy(arr_type)(context,
                builder, args[1]).dtype
            context.nrt.incref(builder, arr_type.dtype, woog__knsl)
        out_arr.dtype = woog__knsl
        return out_arr._getvalue()
    if isinstance(arr_type, bodo.DatetimeArrayType):
        arr = cgutils.create_struct_proxy(arr_type)(context, builder)
        ncx__krijk = _lower_info_to_array_numpy(arr_type.data_array_type,
            context, builder, in_info)
        arr.data = ncx__krijk
        return arr._getvalue()
    if isinstance(arr_type, types.Array):
        return _lower_info_to_array_numpy(arr_type, context, builder, in_info)
    if isinstance(arr_type, (IntegerArrayType, DecimalArrayType)
        ) or arr_type in (boolean_array, datetime_date_array_type):
        arr = cgutils.create_struct_proxy(arr_type)(context, builder)
        vwdy__sbeoz = arr_type.dtype
        if isinstance(arr_type, DecimalArrayType):
            vwdy__sbeoz = int128_type
        elif arr_type == datetime_date_array_type:
            vwdy__sbeoz = types.int64
        eru__vds = types.Array(vwdy__sbeoz, 1, 'C')
        lhj__uhuwa = context.make_array(eru__vds)(context, builder)
        asrmp__fod = types.Array(types.uint8, 1, 'C')
        jnbf__znyx = context.make_array(asrmp__fod)(context, builder)
        bft__dsq = cgutils.alloca_once(builder, lir.IntType(64))
        aif__gzqf = cgutils.alloca_once(builder, lir.IntType(64))
        mtht__rttp = cgutils.alloca_once(builder, lir.IntType(8).as_pointer())
        qlsa__use = cgutils.alloca_once(builder, lir.IntType(8).as_pointer())
        nqqd__ndx = cgutils.alloca_once(builder, lir.IntType(8).as_pointer())
        vpu__cjb = cgutils.alloca_once(builder, lir.IntType(8).as_pointer())
        cqyvy__kxr = lir.FunctionType(lir.VoidType(), [lir.IntType(8).
            as_pointer(), lir.IntType(64).as_pointer(), lir.IntType(64).
            as_pointer(), lir.IntType(8).as_pointer().as_pointer(), lir.
            IntType(8).as_pointer().as_pointer(), lir.IntType(8).as_pointer
            ().as_pointer(), lir.IntType(8).as_pointer().as_pointer()])
        ckrr__dnxpp = cgutils.get_or_insert_function(builder.module,
            cqyvy__kxr, name='info_to_nullable_array')
        builder.call(ckrr__dnxpp, [in_info, bft__dsq, aif__gzqf, mtht__rttp,
            qlsa__use, nqqd__ndx, vpu__cjb])
        context.compile_internal(builder, lambda :
            check_and_propagate_cpp_exception(), types.none(), [])
        art__ldtdu = context.get_value_type(types.intp)
        mil__llhh = cgutils.pack_array(builder, [builder.load(bft__dsq)],
            ty=art__ldtdu)
        lyv__ttkh = context.get_constant(types.intp, context.get_abi_sizeof
            (context.get_data_type(vwdy__sbeoz)))
        jjce__vkaya = cgutils.pack_array(builder, [lyv__ttkh], ty=art__ldtdu)
        ncx__krijk = builder.bitcast(builder.load(mtht__rttp), context.
            get_data_type(vwdy__sbeoz).as_pointer())
        numba.np.arrayobj.populate_array(lhj__uhuwa, data=ncx__krijk, shape
            =mil__llhh, strides=jjce__vkaya, itemsize=lyv__ttkh, meminfo=
            builder.load(nqqd__ndx))
        arr.data = lhj__uhuwa._getvalue()
        mil__llhh = cgutils.pack_array(builder, [builder.load(aif__gzqf)],
            ty=art__ldtdu)
        lyv__ttkh = context.get_constant(types.intp, context.get_abi_sizeof
            (context.get_data_type(types.uint8)))
        jjce__vkaya = cgutils.pack_array(builder, [lyv__ttkh], ty=art__ldtdu)
        ncx__krijk = builder.bitcast(builder.load(qlsa__use), context.
            get_data_type(types.uint8).as_pointer())
        numba.np.arrayobj.populate_array(jnbf__znyx, data=ncx__krijk, shape
            =mil__llhh, strides=jjce__vkaya, itemsize=lyv__ttkh, meminfo=
            builder.load(vpu__cjb))
        arr.null_bitmap = jnbf__znyx._getvalue()
        return arr._getvalue()
    if isinstance(arr_type, IntervalArrayType):
        arr = cgutils.create_struct_proxy(arr_type)(context, builder)
        mqzsi__yxib = context.make_array(arr_type.arr_type)(context, builder)
        tzji__zboax = context.make_array(arr_type.arr_type)(context, builder)
        bft__dsq = cgutils.alloca_once(builder, lir.IntType(64))
        epas__schmy = cgutils.alloca_once(builder, lir.IntType(8).as_pointer())
        yjf__ceh = cgutils.alloca_once(builder, lir.IntType(8).as_pointer())
        simpg__ykm = cgutils.alloca_once(builder, lir.IntType(8).as_pointer())
        pvcmy__qlxbw = cgutils.alloca_once(builder, lir.IntType(8).as_pointer()
            )
        cqyvy__kxr = lir.FunctionType(lir.VoidType(), [lir.IntType(8).
            as_pointer(), lir.IntType(64).as_pointer(), lir.IntType(8).
            as_pointer().as_pointer(), lir.IntType(8).as_pointer().
            as_pointer(), lir.IntType(8).as_pointer().as_pointer(), lir.
            IntType(8).as_pointer().as_pointer()])
        ckrr__dnxpp = cgutils.get_or_insert_function(builder.module,
            cqyvy__kxr, name='info_to_interval_array')
        builder.call(ckrr__dnxpp, [in_info, bft__dsq, epas__schmy, yjf__ceh,
            simpg__ykm, pvcmy__qlxbw])
        context.compile_internal(builder, lambda :
            check_and_propagate_cpp_exception(), types.none(), [])
        art__ldtdu = context.get_value_type(types.intp)
        mil__llhh = cgutils.pack_array(builder, [builder.load(bft__dsq)],
            ty=art__ldtdu)
        lyv__ttkh = context.get_constant(types.intp, context.get_abi_sizeof
            (context.get_data_type(arr_type.arr_type.dtype)))
        jjce__vkaya = cgutils.pack_array(builder, [lyv__ttkh], ty=art__ldtdu)
        wuawn__ybv = builder.bitcast(builder.load(epas__schmy), context.
            get_data_type(arr_type.arr_type.dtype).as_pointer())
        numba.np.arrayobj.populate_array(mqzsi__yxib, data=wuawn__ybv,
            shape=mil__llhh, strides=jjce__vkaya, itemsize=lyv__ttkh,
            meminfo=builder.load(simpg__ykm))
        arr.left = mqzsi__yxib._getvalue()
        qgi__swlog = builder.bitcast(builder.load(yjf__ceh), context.
            get_data_type(arr_type.arr_type.dtype).as_pointer())
        numba.np.arrayobj.populate_array(tzji__zboax, data=qgi__swlog,
            shape=mil__llhh, strides=jjce__vkaya, itemsize=lyv__ttkh,
            meminfo=builder.load(pvcmy__qlxbw))
        arr.right = tzji__zboax._getvalue()
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
        inz__ynlv, wztb__qdb = args
        ssbo__qzee = numba_to_c_type(array_type.dtype)
        okb__tpqf = cgutils.alloca_once_value(builder, lir.Constant(lir.
            IntType(32), ssbo__qzee))
        cqyvy__kxr = lir.FunctionType(lir.IntType(8).as_pointer(), [lir.
            IntType(64), lir.IntType(32)])
        ckrr__dnxpp = cgutils.get_or_insert_function(builder.module,
            cqyvy__kxr, name='alloc_numpy')
        return builder.call(ckrr__dnxpp, [inz__ynlv, builder.load(okb__tpqf)])
    return array_info_type(len_typ, arr_type), codegen


@intrinsic
def test_alloc_string(typingctx, len_typ, n_chars_typ):

    def codegen(context, builder, sig, args):
        inz__ynlv, cbp__xccg = args
        cqyvy__kxr = lir.FunctionType(lir.IntType(8).as_pointer(), [lir.
            IntType(64), lir.IntType(64)])
        ckrr__dnxpp = cgutils.get_or_insert_function(builder.module,
            cqyvy__kxr, name='alloc_string_array')
        return builder.call(ckrr__dnxpp, [inz__ynlv, cbp__xccg])
    return array_info_type(len_typ, n_chars_typ), codegen


@intrinsic
def arr_info_list_to_table(typingctx, list_arr_info_typ=None):
    assert list_arr_info_typ == types.List(array_info_type)
    return table_type(list_arr_info_typ), arr_info_list_to_table_codegen


def arr_info_list_to_table_codegen(context, builder, sig, args):
    xsse__gnte, = args
    qvjb__unnhs = numba.cpython.listobj.ListInstance(context, builder, sig.
        args[0], xsse__gnte)
    cqyvy__kxr = lir.FunctionType(lir.IntType(8).as_pointer(), [lir.IntType
        (8).as_pointer().as_pointer(), lir.IntType(64)])
    ckrr__dnxpp = cgutils.get_or_insert_function(builder.module, cqyvy__kxr,
        name='arr_info_list_to_table')
    return builder.call(ckrr__dnxpp, [qvjb__unnhs.data, qvjb__unnhs.size])


@intrinsic
def info_from_table(typingctx, table_t, ind_t):

    def codegen(context, builder, sig, args):
        cqyvy__kxr = lir.FunctionType(lir.IntType(8).as_pointer(), [lir.
            IntType(8).as_pointer(), lir.IntType(64)])
        ckrr__dnxpp = cgutils.get_or_insert_function(builder.module,
            cqyvy__kxr, name='info_from_table')
        return builder.call(ckrr__dnxpp, args)
    return array_info_type(table_t, ind_t), codegen


@intrinsic
def cpp_table_to_py_table(typingctx, cpp_table_t, table_idx_arr_t,
    py_table_type_t):
    assert cpp_table_t == table_type, 'invalid cpp table type'
    assert isinstance(table_idx_arr_t, types.Array
        ) and table_idx_arr_t.dtype == types.int64, 'invalid table index array'
    assert isinstance(py_table_type_t, types.TypeRef), 'invalid py table ref'
    dcd__dct = py_table_type_t.instance_type

    def codegen(context, builder, sig, args):
        pkdj__snvqh, tfq__czh, wztb__qdb = args
        cqyvy__kxr = lir.FunctionType(lir.IntType(8).as_pointer(), [lir.
            IntType(8).as_pointer(), lir.IntType(64)])
        ckrr__dnxpp = cgutils.get_or_insert_function(builder.module,
            cqyvy__kxr, name='info_from_table')
        nbll__lkgm = cgutils.create_struct_proxy(dcd__dct)(context, builder)
        nbll__lkgm.parent = cgutils.get_null_value(nbll__lkgm.parent.type)
        nknvm__lej = context.make_array(table_idx_arr_t)(context, builder,
            tfq__czh)
        ueo__kxonj = context.get_constant(types.int64, -1)
        tghx__kpshq = context.get_constant(types.int64, 0)
        rnfj__wfh = cgutils.alloca_once_value(builder, tghx__kpshq)
        for t, rdrdl__hvui in dcd__dct.type_to_blk.items():
            ptkt__zvsbz = context.get_constant(types.int64, len(dcd__dct.
                block_to_arr_ind[rdrdl__hvui]))
            wztb__qdb, moodk__uic = ListInstance.allocate_ex(context,
                builder, types.List(t), ptkt__zvsbz)
            moodk__uic.size = ptkt__zvsbz
            crjt__uzlzz = context.make_constant_array(builder, types.Array(
                types.int64, 1, 'C'), np.array(dcd__dct.block_to_arr_ind[
                rdrdl__hvui], dtype=np.int64))
            xal__ekibk = context.make_array(types.Array(types.int64, 1, 'C'))(
                context, builder, crjt__uzlzz)
            with cgutils.for_range(builder, ptkt__zvsbz) as oodi__xtz:
                awxb__zbd = oodi__xtz.index
                znyz__bjek = _getitem_array_single_int(context, builder,
                    types.int64, types.Array(types.int64, 1, 'C'),
                    xal__ekibk, awxb__zbd)
                mmrc__motop = _getitem_array_single_int(context, builder,
                    types.int64, table_idx_arr_t, nknvm__lej, znyz__bjek)
                mqv__fvwyl = builder.icmp_unsigned('!=', mmrc__motop,
                    ueo__kxonj)
                with builder.if_else(mqv__fvwyl) as (erf__wbkdz, pwv__ptzl):
                    with erf__wbkdz:
                        xlwif__agu = builder.call(ckrr__dnxpp, [pkdj__snvqh,
                            mmrc__motop])
                        arr = context.compile_internal(builder, lambda info:
                            info_to_array(info, t), t(array_info_type), [
                            xlwif__agu])
                        moodk__uic.inititem(awxb__zbd, arr, incref=False)
                        inz__ynlv = context.compile_internal(builder, lambda
                            arr: len(arr), types.int64(t), [arr])
                        builder.store(inz__ynlv, rnfj__wfh)
                    with pwv__ptzl:
                        gxp__jvtgu = context.get_constant_null(t)
                        moodk__uic.inititem(awxb__zbd, gxp__jvtgu, incref=False
                            )
            setattr(nbll__lkgm, f'block_{rdrdl__hvui}', moodk__uic.value)
        nbll__lkgm.len = builder.load(rnfj__wfh)
        return nbll__lkgm._getvalue()
    return dcd__dct(cpp_table_t, table_idx_arr_t, py_table_type_t), codegen


@intrinsic
def py_table_to_cpp_table(typingctx, py_table_t, py_table_type_t):
    assert isinstance(py_table_t, bodo.hiframes.table.TableType
        ), 'invalid py table type'
    assert isinstance(py_table_type_t, types.TypeRef), 'invalid py table ref'
    dcd__dct = py_table_type_t.instance_type

    def codegen(context, builder, sig, args):
        ntip__yagm, wztb__qdb = args
        wyq__fso = cgutils.create_struct_proxy(dcd__dct)(context, builder,
            ntip__yagm)
        if dcd__dct.has_runtime_cols:
            jxy__iojci = lir.Constant(lir.IntType(64), 0)
            for rdrdl__hvui, t in enumerate(dcd__dct.arr_types):
                hox__mwjuh = getattr(wyq__fso, f'block_{rdrdl__hvui}')
                jet__kxbiw = ListInstance(context, builder, types.List(t),
                    hox__mwjuh)
                jxy__iojci = builder.add(jxy__iojci, jet__kxbiw.size)
        else:
            jxy__iojci = lir.Constant(lir.IntType(64), len(dcd__dct.arr_types))
        wztb__qdb, tkfd__tihp = ListInstance.allocate_ex(context, builder,
            types.List(array_info_type), jxy__iojci)
        tkfd__tihp.size = jxy__iojci
        if dcd__dct.has_runtime_cols:
            majix__hsfo = lir.Constant(lir.IntType(64), 0)
            for rdrdl__hvui, t in enumerate(dcd__dct.arr_types):
                hox__mwjuh = getattr(wyq__fso, f'block_{rdrdl__hvui}')
                jet__kxbiw = ListInstance(context, builder, types.List(t),
                    hox__mwjuh)
                ptkt__zvsbz = jet__kxbiw.size
                with cgutils.for_range(builder, ptkt__zvsbz) as oodi__xtz:
                    awxb__zbd = oodi__xtz.index
                    arr = jet__kxbiw.getitem(awxb__zbd)
                    xsx__tfaeo = signature(array_info_type, t)
                    yeut__xwbpc = arr,
                    cct__oek = array_to_info_codegen(context, builder,
                        xsx__tfaeo, yeut__xwbpc)
                    tkfd__tihp.inititem(builder.add(majix__hsfo, awxb__zbd),
                        cct__oek, incref=False)
                majix__hsfo = builder.add(majix__hsfo, ptkt__zvsbz)
        else:
            for t, rdrdl__hvui in dcd__dct.type_to_blk.items():
                ptkt__zvsbz = context.get_constant(types.int64, len(
                    dcd__dct.block_to_arr_ind[rdrdl__hvui]))
                hox__mwjuh = getattr(wyq__fso, f'block_{rdrdl__hvui}')
                jet__kxbiw = ListInstance(context, builder, types.List(t),
                    hox__mwjuh)
                crjt__uzlzz = context.make_constant_array(builder, types.
                    Array(types.int64, 1, 'C'), np.array(dcd__dct.
                    block_to_arr_ind[rdrdl__hvui], dtype=np.int64))
                xal__ekibk = context.make_array(types.Array(types.int64, 1,
                    'C'))(context, builder, crjt__uzlzz)
                with cgutils.for_range(builder, ptkt__zvsbz) as oodi__xtz:
                    awxb__zbd = oodi__xtz.index
                    znyz__bjek = _getitem_array_single_int(context, builder,
                        types.int64, types.Array(types.int64, 1, 'C'),
                        xal__ekibk, awxb__zbd)
                    cmnh__dksi = signature(types.none, dcd__dct, types.List
                        (t), types.int64, types.int64)
                    ypynu__zxfkh = (ntip__yagm, hox__mwjuh, awxb__zbd,
                        znyz__bjek)
                    bodo.hiframes.table.ensure_column_unboxed_codegen(context,
                        builder, cmnh__dksi, ypynu__zxfkh)
                    arr = jet__kxbiw.getitem(awxb__zbd)
                    xsx__tfaeo = signature(array_info_type, t)
                    yeut__xwbpc = arr,
                    cct__oek = array_to_info_codegen(context, builder,
                        xsx__tfaeo, yeut__xwbpc)
                    tkfd__tihp.inititem(znyz__bjek, cct__oek, incref=False)
        qbscf__sai = tkfd__tihp.value
        ayu__xsx = signature(table_type, types.List(array_info_type))
        ylx__xranr = qbscf__sai,
        pkdj__snvqh = arr_info_list_to_table_codegen(context, builder,
            ayu__xsx, ylx__xranr)
        context.nrt.decref(builder, types.List(array_info_type), qbscf__sai)
        return pkdj__snvqh
    return table_type(dcd__dct, py_table_type_t), codegen


delete_info_decref_array = types.ExternalFunction('delete_info_decref_array',
    types.void(array_info_type))
delete_table_decref_arrays = types.ExternalFunction(
    'delete_table_decref_arrays', types.void(table_type))


@intrinsic
def delete_table(typingctx, table_t=None):
    assert table_t == table_type

    def codegen(context, builder, sig, args):
        cqyvy__kxr = lir.FunctionType(lir.VoidType(), [lir.IntType(8).
            as_pointer()])
        ckrr__dnxpp = cgutils.get_or_insert_function(builder.module,
            cqyvy__kxr, name='delete_table')
        builder.call(ckrr__dnxpp, args)
    return types.void(table_t), codegen


@intrinsic
def shuffle_table(typingctx, table_t, n_keys_t, _is_parallel, keep_comm_info_t
    ):
    assert table_t == table_type

    def codegen(context, builder, sig, args):
        cqyvy__kxr = lir.FunctionType(lir.IntType(8).as_pointer(), [lir.
            IntType(8).as_pointer(), lir.IntType(64), lir.IntType(1), lir.
            IntType(32)])
        ckrr__dnxpp = cgutils.get_or_insert_function(builder.module,
            cqyvy__kxr, name='shuffle_table')
        njo__hffa = builder.call(ckrr__dnxpp, args)
        context.compile_internal(builder, lambda :
            check_and_propagate_cpp_exception(), types.none(), [])
        return njo__hffa
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
        cqyvy__kxr = lir.FunctionType(lir.VoidType(), [lir.IntType(8).
            as_pointer()])
        ckrr__dnxpp = cgutils.get_or_insert_function(builder.module,
            cqyvy__kxr, name='delete_shuffle_info')
        return builder.call(ckrr__dnxpp, args)
    return types.void(shuffle_info_t), codegen


@intrinsic
def reverse_shuffle_table(typingctx, table_t, shuffle_info_t=None):

    def codegen(context, builder, sig, args):
        if sig.args[-1] == types.none:
            return context.get_constant_null(table_type)
        cqyvy__kxr = lir.FunctionType(lir.IntType(8).as_pointer(), [lir.
            IntType(8).as_pointer(), lir.IntType(8).as_pointer()])
        ckrr__dnxpp = cgutils.get_or_insert_function(builder.module,
            cqyvy__kxr, name='reverse_shuffle_table')
        return builder.call(ckrr__dnxpp, args)
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
        cqyvy__kxr = lir.FunctionType(lir.IntType(8).as_pointer(), [lir.
            IntType(8).as_pointer(), lir.IntType(8).as_pointer(), lir.
            IntType(1), lir.IntType(1), lir.IntType(64), lir.IntType(64),
            lir.IntType(64), lir.IntType(8).as_pointer(), lir.IntType(8).
            as_pointer(), lir.IntType(1), lir.IntType(1), lir.IntType(1),
            lir.IntType(1), lir.IntType(1), lir.IntType(1), lir.IntType(8).
            as_pointer(), lir.IntType(8).as_pointer(), lir.IntType(64), lir
            .IntType(8).as_pointer(), lir.IntType(64)])
        ckrr__dnxpp = cgutils.get_or_insert_function(builder.module,
            cqyvy__kxr, name='hash_join_table')
        njo__hffa = builder.call(ckrr__dnxpp, args)
        context.compile_internal(builder, lambda :
            check_and_propagate_cpp_exception(), types.none(), [])
        return njo__hffa
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
        cqyvy__kxr = lir.FunctionType(lir.IntType(8).as_pointer(), [lir.
            IntType(8).as_pointer(), lir.IntType(64), lir.IntType(8).
            as_pointer(), lir.IntType(8).as_pointer(), lir.IntType(1)])
        ckrr__dnxpp = cgutils.get_or_insert_function(builder.module,
            cqyvy__kxr, name='sort_values_table')
        njo__hffa = builder.call(ckrr__dnxpp, args)
        context.compile_internal(builder, lambda :
            check_and_propagate_cpp_exception(), types.none(), [])
        return njo__hffa
    return table_type(table_t, types.int64, types.voidptr, types.voidptr,
        types.boolean), codegen


@intrinsic
def sample_table(typingctx, table_t, n_keys_t, frac_t, replace_t, parallel_t):
    assert table_t == table_type

    def codegen(context, builder, sig, args):
        cqyvy__kxr = lir.FunctionType(lir.IntType(8).as_pointer(), [lir.
            IntType(8).as_pointer(), lir.IntType(64), lir.DoubleType(), lir
            .IntType(1), lir.IntType(1)])
        ckrr__dnxpp = cgutils.get_or_insert_function(builder.module,
            cqyvy__kxr, name='sample_table')
        njo__hffa = builder.call(ckrr__dnxpp, args)
        context.compile_internal(builder, lambda :
            check_and_propagate_cpp_exception(), types.none(), [])
        return njo__hffa
    return table_type(table_t, types.int64, types.float64, types.boolean,
        types.boolean), codegen


@intrinsic
def shuffle_renormalization(typingctx, table_t, random_t, random_seed_t,
    is_parallel_t):
    assert table_t == table_type

    def codegen(context, builder, sig, args):
        cqyvy__kxr = lir.FunctionType(lir.IntType(8).as_pointer(), [lir.
            IntType(8).as_pointer(), lir.IntType(32), lir.IntType(64), lir.
            IntType(1)])
        ckrr__dnxpp = cgutils.get_or_insert_function(builder.module,
            cqyvy__kxr, name='shuffle_renormalization')
        njo__hffa = builder.call(ckrr__dnxpp, args)
        context.compile_internal(builder, lambda :
            check_and_propagate_cpp_exception(), types.none(), [])
        return njo__hffa
    return table_type(table_t, types.int32, types.int64, types.boolean
        ), codegen


@intrinsic
def shuffle_renormalization_group(typingctx, table_t, random_t,
    random_seed_t, is_parallel_t, num_ranks_t, ranks_t):
    assert table_t == table_type

    def codegen(context, builder, sig, args):
        cqyvy__kxr = lir.FunctionType(lir.IntType(8).as_pointer(), [lir.
            IntType(8).as_pointer(), lir.IntType(32), lir.IntType(64), lir.
            IntType(1), lir.IntType(64), lir.IntType(8).as_pointer()])
        ckrr__dnxpp = cgutils.get_or_insert_function(builder.module,
            cqyvy__kxr, name='shuffle_renormalization_group')
        njo__hffa = builder.call(ckrr__dnxpp, args)
        context.compile_internal(builder, lambda :
            check_and_propagate_cpp_exception(), types.none(), [])
        return njo__hffa
    return table_type(table_t, types.int32, types.int64, types.boolean,
        types.int64, types.voidptr), codegen


@intrinsic
def drop_duplicates_table(typingctx, table_t, parallel_t, nkey_t, keep_t,
    dropna, drop_local_first):
    assert table_t == table_type

    def codegen(context, builder, sig, args):
        cqyvy__kxr = lir.FunctionType(lir.IntType(8).as_pointer(), [lir.
            IntType(8).as_pointer(), lir.IntType(1), lir.IntType(64), lir.
            IntType(64), lir.IntType(1), lir.IntType(1)])
        ckrr__dnxpp = cgutils.get_or_insert_function(builder.module,
            cqyvy__kxr, name='drop_duplicates_table')
        njo__hffa = builder.call(ckrr__dnxpp, args)
        context.compile_internal(builder, lambda :
            check_and_propagate_cpp_exception(), types.none(), [])
        return njo__hffa
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
        cqyvy__kxr = lir.FunctionType(lir.IntType(8).as_pointer(), [lir.
            IntType(8).as_pointer(), lir.IntType(64), lir.IntType(8).
            as_pointer(), lir.IntType(8).as_pointer(), lir.IntType(1), lir.
            IntType(8).as_pointer(), lir.IntType(8).as_pointer(), lir.
            IntType(8).as_pointer(), lir.IntType(1), lir.IntType(1), lir.
            IntType(1), lir.IntType(1), lir.IntType(1), lir.IntType(8).
            as_pointer(), lir.IntType(8).as_pointer(), lir.IntType(8).
            as_pointer(), lir.IntType(8).as_pointer()])
        ckrr__dnxpp = cgutils.get_or_insert_function(builder.module,
            cqyvy__kxr, name='pivot_groupby_and_aggregate')
        njo__hffa = builder.call(ckrr__dnxpp, args)
        context.compile_internal(builder, lambda :
            check_and_propagate_cpp_exception(), types.none(), [])
        return njo__hffa
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
        cqyvy__kxr = lir.FunctionType(lir.IntType(8).as_pointer(), [lir.
            IntType(8).as_pointer(), lir.IntType(64), lir.IntType(1), lir.
            IntType(8).as_pointer(), lir.IntType(8).as_pointer(), lir.
            IntType(8).as_pointer(), lir.IntType(1), lir.IntType(1), lir.
            IntType(64), lir.IntType(64), lir.IntType(64), lir.IntType(1),
            lir.IntType(1), lir.IntType(1), lir.IntType(8).as_pointer(),
            lir.IntType(8).as_pointer(), lir.IntType(8).as_pointer(), lir.
            IntType(8).as_pointer(), lir.IntType(8).as_pointer()])
        ckrr__dnxpp = cgutils.get_or_insert_function(builder.module,
            cqyvy__kxr, name='groupby_and_aggregate')
        njo__hffa = builder.call(ckrr__dnxpp, args)
        context.compile_internal(builder, lambda :
            check_and_propagate_cpp_exception(), types.none(), [])
        return njo__hffa
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
    wdr__xpmop = array_to_info(in_arr)
    nrvf__bltp = array_to_info(in_values)
    fwyj__fysl = array_to_info(out_arr)
    ngq__lpw = arr_info_list_to_table([wdr__xpmop, nrvf__bltp, fwyj__fysl])
    _array_isin(fwyj__fysl, wdr__xpmop, nrvf__bltp, is_parallel)
    check_and_propagate_cpp_exception()
    delete_table(ngq__lpw)


_get_search_regex = types.ExternalFunction('get_search_regex', types.void(
    array_info_type, types.bool_, types.voidptr, array_info_type))


@numba.njit(no_cpython_wrapper=True)
def get_search_regex(in_arr, case, pat, out_arr):
    in_arr = decode_if_dict_array(in_arr)
    wdr__xpmop = array_to_info(in_arr)
    fwyj__fysl = array_to_info(out_arr)
    _get_search_regex(wdr__xpmop, case, pat, fwyj__fysl)
    check_and_propagate_cpp_exception()


def _gen_row_access_intrinsic(col_array_typ, c_ind):
    from llvmlite import ir as lir
    dhrcm__fdt = col_array_typ.dtype
    if isinstance(dhrcm__fdt, types.Number) or dhrcm__fdt in [bodo.
        datetime_date_type, bodo.datetime64ns, bodo.timedelta64ns, types.bool_
        ]:

        @intrinsic
        def getitem_func(typingctx, table_t, ind_t):

            def codegen(context, builder, sig, args):
                nbll__lkgm, gfmjq__vqo = args
                nbll__lkgm = builder.bitcast(nbll__lkgm, lir.IntType(8).
                    as_pointer().as_pointer())
                fxvh__ikw = lir.Constant(lir.IntType(64), c_ind)
                pwwtz__unop = builder.load(builder.gep(nbll__lkgm, [fxvh__ikw])
                    )
                pwwtz__unop = builder.bitcast(pwwtz__unop, context.
                    get_data_type(dhrcm__fdt).as_pointer())
                return builder.load(builder.gep(pwwtz__unop, [gfmjq__vqo]))
            return dhrcm__fdt(types.voidptr, types.int64), codegen
        return getitem_func
    if col_array_typ == bodo.string_array_type:

        @intrinsic
        def getitem_func(typingctx, table_t, ind_t):

            def codegen(context, builder, sig, args):
                nbll__lkgm, gfmjq__vqo = args
                nbll__lkgm = builder.bitcast(nbll__lkgm, lir.IntType(8).
                    as_pointer().as_pointer())
                fxvh__ikw = lir.Constant(lir.IntType(64), c_ind)
                pwwtz__unop = builder.load(builder.gep(nbll__lkgm, [fxvh__ikw])
                    )
                cqyvy__kxr = lir.FunctionType(lir.IntType(8).as_pointer(),
                    [lir.IntType(8).as_pointer(), lir.IntType(64), lir.
                    IntType(64).as_pointer()])
                allvj__jpy = cgutils.get_or_insert_function(builder.module,
                    cqyvy__kxr, name='array_info_getitem')
                ulgf__cwhyo = cgutils.alloca_once(builder, lir.IntType(64))
                args = pwwtz__unop, gfmjq__vqo, ulgf__cwhyo
                mtht__rttp = builder.call(allvj__jpy, args)
                return context.make_tuple(builder, sig.return_type, [
                    mtht__rttp, builder.load(ulgf__cwhyo)])
            return types.Tuple([types.voidptr, types.int64])(types.voidptr,
                types.int64), codegen
        return getitem_func
    if col_array_typ == bodo.libs.dict_arr_ext.dict_str_arr_type:

        @intrinsic
        def getitem_func(typingctx, table_t, ind_t):

            def codegen(context, builder, sig, args):
                iyjrg__qzq = lir.Constant(lir.IntType(64), 1)
                lmftp__hja = lir.Constant(lir.IntType(64), 2)
                nbll__lkgm, gfmjq__vqo = args
                nbll__lkgm = builder.bitcast(nbll__lkgm, lir.IntType(8).
                    as_pointer().as_pointer())
                fxvh__ikw = lir.Constant(lir.IntType(64), c_ind)
                pwwtz__unop = builder.load(builder.gep(nbll__lkgm, [fxvh__ikw])
                    )
                cqyvy__kxr = lir.FunctionType(lir.IntType(8).as_pointer(),
                    [lir.IntType(8).as_pointer(), lir.IntType(64)])
                znq__fsu = cgutils.get_or_insert_function(builder.module,
                    cqyvy__kxr, name='get_nested_info')
                args = pwwtz__unop, lmftp__hja
                ngr__niizb = builder.call(znq__fsu, args)
                cqyvy__kxr = lir.FunctionType(lir.IntType(8).as_pointer(),
                    [lir.IntType(8).as_pointer()])
                rpxut__dav = cgutils.get_or_insert_function(builder.module,
                    cqyvy__kxr, name='array_info_getdata1')
                args = ngr__niizb,
                hbgo__cya = builder.call(rpxut__dav, args)
                hbgo__cya = builder.bitcast(hbgo__cya, context.
                    get_data_type(col_array_typ.indices_dtype).as_pointer())
                ksnwm__geu = builder.sext(builder.load(builder.gep(
                    hbgo__cya, [gfmjq__vqo])), lir.IntType(64))
                args = pwwtz__unop, iyjrg__qzq
                xhk__zlk = builder.call(znq__fsu, args)
                cqyvy__kxr = lir.FunctionType(lir.IntType(8).as_pointer(),
                    [lir.IntType(8).as_pointer(), lir.IntType(64), lir.
                    IntType(64).as_pointer()])
                allvj__jpy = cgutils.get_or_insert_function(builder.module,
                    cqyvy__kxr, name='array_info_getitem')
                ulgf__cwhyo = cgutils.alloca_once(builder, lir.IntType(64))
                args = xhk__zlk, ksnwm__geu, ulgf__cwhyo
                mtht__rttp = builder.call(allvj__jpy, args)
                return context.make_tuple(builder, sig.return_type, [
                    mtht__rttp, builder.load(ulgf__cwhyo)])
            return types.Tuple([types.voidptr, types.int64])(types.voidptr,
                types.int64), codegen
        return getitem_func
    raise BodoError(
        f"General Join Conditions with '{dhrcm__fdt}' column data type not supported"
        )


def _gen_row_na_check_intrinsic(col_array_dtype, c_ind):
    if (isinstance(col_array_dtype, bodo.libs.int_arr_ext.IntegerArrayType) or
        col_array_dtype == bodo.libs.bool_arr_ext.boolean_array or
        is_str_arr_type(col_array_dtype) or isinstance(col_array_dtype,
        types.Array) and col_array_dtype.dtype == bodo.datetime_date_type):

        @intrinsic
        def checkna_func(typingctx, table_t, ind_t):

            def codegen(context, builder, sig, args):
                bjf__gcml, gfmjq__vqo = args
                bjf__gcml = builder.bitcast(bjf__gcml, lir.IntType(8).
                    as_pointer().as_pointer())
                fxvh__ikw = lir.Constant(lir.IntType(64), c_ind)
                pwwtz__unop = builder.load(builder.gep(bjf__gcml, [fxvh__ikw]))
                zxav__vrpy = builder.bitcast(pwwtz__unop, context.
                    get_data_type(types.bool_).as_pointer())
                dqjvx__xsce = bodo.utils.cg_helpers.get_bitmap_bit(builder,
                    zxav__vrpy, gfmjq__vqo)
                zhrp__unxld = builder.icmp_unsigned('!=', dqjvx__xsce, lir.
                    Constant(lir.IntType(8), 0))
                return builder.sext(zhrp__unxld, lir.IntType(8))
            return types.int8(types.voidptr, types.int64), codegen
        return checkna_func
    elif isinstance(col_array_dtype, types.Array):
        dhrcm__fdt = col_array_dtype.dtype
        if dhrcm__fdt in [bodo.datetime64ns, bodo.timedelta64ns]:

            @intrinsic
            def checkna_func(typingctx, table_t, ind_t):

                def codegen(context, builder, sig, args):
                    nbll__lkgm, gfmjq__vqo = args
                    nbll__lkgm = builder.bitcast(nbll__lkgm, lir.IntType(8)
                        .as_pointer().as_pointer())
                    fxvh__ikw = lir.Constant(lir.IntType(64), c_ind)
                    pwwtz__unop = builder.load(builder.gep(nbll__lkgm, [
                        fxvh__ikw]))
                    pwwtz__unop = builder.bitcast(pwwtz__unop, context.
                        get_data_type(dhrcm__fdt).as_pointer())
                    ahvz__dsl = builder.load(builder.gep(pwwtz__unop, [
                        gfmjq__vqo]))
                    zhrp__unxld = builder.icmp_unsigned('!=', ahvz__dsl,
                        lir.Constant(lir.IntType(64), pd._libs.iNaT))
                    return builder.sext(zhrp__unxld, lir.IntType(8))
                return types.int8(types.voidptr, types.int64), codegen
            return checkna_func
        elif isinstance(dhrcm__fdt, types.Float):

            @intrinsic
            def checkna_func(typingctx, table_t, ind_t):

                def codegen(context, builder, sig, args):
                    nbll__lkgm, gfmjq__vqo = args
                    nbll__lkgm = builder.bitcast(nbll__lkgm, lir.IntType(8)
                        .as_pointer().as_pointer())
                    fxvh__ikw = lir.Constant(lir.IntType(64), c_ind)
                    pwwtz__unop = builder.load(builder.gep(nbll__lkgm, [
                        fxvh__ikw]))
                    pwwtz__unop = builder.bitcast(pwwtz__unop, context.
                        get_data_type(dhrcm__fdt).as_pointer())
                    ahvz__dsl = builder.load(builder.gep(pwwtz__unop, [
                        gfmjq__vqo]))
                    nhynf__ocnut = signature(types.bool_, dhrcm__fdt)
                    dqjvx__xsce = numba.np.npyfuncs.np_real_isnan_impl(context,
                        builder, nhynf__ocnut, (ahvz__dsl,))
                    return builder.not_(builder.sext(dqjvx__xsce, lir.
                        IntType(8)))
                return types.int8(types.voidptr, types.int64), codegen
            return checkna_func
    raise BodoError(
        f"General Join Conditions with '{col_array_dtype}' column type not supported"
        )
