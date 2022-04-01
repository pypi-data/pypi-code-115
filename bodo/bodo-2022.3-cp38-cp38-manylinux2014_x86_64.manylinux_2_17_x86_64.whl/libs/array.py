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
        qjh__gqh = context.make_helper(builder, arr_type, in_arr)
        in_arr = qjh__gqh.data
        arr_type = StructArrayType(arr_type.data, ('dummy',) * len(arr_type
            .data))
    if isinstance(arr_type, ArrayItemArrayType
        ) and arr_type.dtype == string_array_type:
        ertq__xtwdn = context.make_helper(builder, arr_type, in_arr)
        bjo__pojp = lir.FunctionType(lir.IntType(8).as_pointer(), [lir.
            IntType(8).as_pointer()])
        rvy__hvxn = cgutils.get_or_insert_function(builder.module,
            bjo__pojp, name='list_string_array_to_info')
        return builder.call(rvy__hvxn, [ertq__xtwdn.meminfo])
    if isinstance(arr_type, (MapArrayType, ArrayItemArrayType, StructArrayType)
        ):

        def get_types(arr_typ):
            if isinstance(arr_typ, MapArrayType):
                return get_types(_get_map_arr_data_type(arr_typ))
            elif isinstance(arr_typ, ArrayItemArrayType):
                return [CTypeEnum.LIST.value] + get_types(arr_typ.dtype)
            elif isinstance(arr_typ, (StructType, StructArrayType)):
                vpwhe__tod = [CTypeEnum.STRUCT.value, len(arr_typ.names)]
                for tuwvi__pma in arr_typ.data:
                    vpwhe__tod += get_types(tuwvi__pma)
                return vpwhe__tod
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
            ztrm__slcv = context.compile_internal(builder, lambda a: len(a),
                types.intp(arr_typ), [arr])
            if isinstance(arr_typ, MapArrayType):
                oofvh__hmyaz = context.make_helper(builder, arr_typ, value=arr)
                hjly__krvek = get_lengths(_get_map_arr_data_type(arr_typ),
                    oofvh__hmyaz.data)
            elif isinstance(arr_typ, ArrayItemArrayType):
                dbvpe__cht = _get_array_item_arr_payload(context, builder,
                    arr_typ, arr)
                hjly__krvek = get_lengths(arr_typ.dtype, dbvpe__cht.data)
                hjly__krvek = cgutils.pack_array(builder, [dbvpe__cht.
                    n_arrays] + [builder.extract_value(hjly__krvek,
                    nyk__kgymk) for nyk__kgymk in range(hjly__krvek.type.
                    count)])
            elif isinstance(arr_typ, StructArrayType):
                dbvpe__cht = _get_struct_arr_payload(context, builder,
                    arr_typ, arr)
                hjly__krvek = []
                for nyk__kgymk, tuwvi__pma in enumerate(arr_typ.data):
                    utydv__nwfj = get_lengths(tuwvi__pma, builder.
                        extract_value(dbvpe__cht.data, nyk__kgymk))
                    hjly__krvek += [builder.extract_value(utydv__nwfj,
                        dnwdu__rak) for dnwdu__rak in range(utydv__nwfj.
                        type.count)]
                hjly__krvek = cgutils.pack_array(builder, [ztrm__slcv,
                    context.get_constant(types.int64, -1)] + hjly__krvek)
            elif isinstance(arr_typ, (IntegerArrayType, DecimalArrayType,
                types.Array)) or arr_typ in (boolean_array,
                datetime_date_array_type, string_array_type, binary_array_type
                ):
                hjly__krvek = cgutils.pack_array(builder, [ztrm__slcv])
            else:
                raise BodoError(
                    f'array_to_info: unsupported type for subarray {arr_typ}')
            return hjly__krvek

        def get_buffers(arr_typ, arr):
            if isinstance(arr_typ, MapArrayType):
                oofvh__hmyaz = context.make_helper(builder, arr_typ, value=arr)
                bls__ecaz = get_buffers(_get_map_arr_data_type(arr_typ),
                    oofvh__hmyaz.data)
            elif isinstance(arr_typ, ArrayItemArrayType):
                dbvpe__cht = _get_array_item_arr_payload(context, builder,
                    arr_typ, arr)
                yqzy__lsh = get_buffers(arr_typ.dtype, dbvpe__cht.data)
                zika__ruo = context.make_array(types.Array(offset_type, 1, 'C')
                    )(context, builder, dbvpe__cht.offsets)
                yizll__czu = builder.bitcast(zika__ruo.data, lir.IntType(8)
                    .as_pointer())
                zkmed__dfi = context.make_array(types.Array(types.uint8, 1,
                    'C'))(context, builder, dbvpe__cht.null_bitmap)
                wql__imojb = builder.bitcast(zkmed__dfi.data, lir.IntType(8
                    ).as_pointer())
                bls__ecaz = cgutils.pack_array(builder, [yizll__czu,
                    wql__imojb] + [builder.extract_value(yqzy__lsh,
                    nyk__kgymk) for nyk__kgymk in range(yqzy__lsh.type.count)])
            elif isinstance(arr_typ, StructArrayType):
                dbvpe__cht = _get_struct_arr_payload(context, builder,
                    arr_typ, arr)
                yqzy__lsh = []
                for nyk__kgymk, tuwvi__pma in enumerate(arr_typ.data):
                    laosp__crzqu = get_buffers(tuwvi__pma, builder.
                        extract_value(dbvpe__cht.data, nyk__kgymk))
                    yqzy__lsh += [builder.extract_value(laosp__crzqu,
                        dnwdu__rak) for dnwdu__rak in range(laosp__crzqu.
                        type.count)]
                zkmed__dfi = context.make_array(types.Array(types.uint8, 1,
                    'C'))(context, builder, dbvpe__cht.null_bitmap)
                wql__imojb = builder.bitcast(zkmed__dfi.data, lir.IntType(8
                    ).as_pointer())
                bls__ecaz = cgutils.pack_array(builder, [wql__imojb] +
                    yqzy__lsh)
            elif isinstance(arr_typ, (IntegerArrayType, DecimalArrayType)
                ) or arr_typ in (boolean_array, datetime_date_array_type):
                obm__sym = arr_typ.dtype
                if isinstance(arr_typ, DecimalArrayType):
                    obm__sym = int128_type
                elif arr_typ == datetime_date_array_type:
                    obm__sym = types.int64
                arr = cgutils.create_struct_proxy(arr_typ)(context, builder,
                    arr)
                lzfpe__iya = context.make_array(types.Array(obm__sym, 1, 'C'))(
                    context, builder, arr.data)
                zkmed__dfi = context.make_array(types.Array(types.uint8, 1,
                    'C'))(context, builder, arr.null_bitmap)
                dtwz__cglej = builder.bitcast(lzfpe__iya.data, lir.IntType(
                    8).as_pointer())
                wql__imojb = builder.bitcast(zkmed__dfi.data, lir.IntType(8
                    ).as_pointer())
                bls__ecaz = cgutils.pack_array(builder, [wql__imojb,
                    dtwz__cglej])
            elif arr_typ in (string_array_type, binary_array_type):
                dbvpe__cht = _get_str_binary_arr_payload(context, builder,
                    arr, arr_typ)
                hcqew__xyna = context.make_helper(builder, offset_arr_type,
                    dbvpe__cht.offsets).data
                aoin__csdpx = context.make_helper(builder, char_arr_type,
                    dbvpe__cht.data).data
                aegy__xbt = context.make_helper(builder,
                    null_bitmap_arr_type, dbvpe__cht.null_bitmap).data
                bls__ecaz = cgutils.pack_array(builder, [builder.bitcast(
                    hcqew__xyna, lir.IntType(8).as_pointer()), builder.
                    bitcast(aegy__xbt, lir.IntType(8).as_pointer()),
                    builder.bitcast(aoin__csdpx, lir.IntType(8).as_pointer())])
            elif isinstance(arr_typ, types.Array):
                arr = context.make_array(arr_typ)(context, builder, arr)
                dtwz__cglej = builder.bitcast(arr.data, lir.IntType(8).
                    as_pointer())
                luuw__qnu = lir.Constant(lir.IntType(8).as_pointer(), None)
                bls__ecaz = cgutils.pack_array(builder, [luuw__qnu,
                    dtwz__cglej])
            else:
                raise RuntimeError(
                    'array_to_info: unsupported type for subarray ' + str(
                    arr_typ))
            return bls__ecaz

        def get_field_names(arr_typ):
            ypk__msm = []
            if isinstance(arr_typ, StructArrayType):
                for btx__pvumu, accl__mwyne in zip(arr_typ.dtype.names,
                    arr_typ.data):
                    ypk__msm.append(btx__pvumu)
                    ypk__msm += get_field_names(accl__mwyne)
            elif isinstance(arr_typ, ArrayItemArrayType):
                ypk__msm += get_field_names(arr_typ.dtype)
            elif isinstance(arr_typ, MapArrayType):
                ypk__msm += get_field_names(_get_map_arr_data_type(arr_typ))
            return ypk__msm
        vpwhe__tod = get_types(arr_type)
        gfzhk__jgkxf = cgutils.pack_array(builder, [context.get_constant(
            types.int32, t) for t in vpwhe__tod])
        ggazw__dlxrw = cgutils.alloca_once_value(builder, gfzhk__jgkxf)
        hjly__krvek = get_lengths(arr_type, in_arr)
        lengths_ptr = cgutils.alloca_once_value(builder, hjly__krvek)
        bls__ecaz = get_buffers(arr_type, in_arr)
        bclu__aec = cgutils.alloca_once_value(builder, bls__ecaz)
        ypk__msm = get_field_names(arr_type)
        if len(ypk__msm) == 0:
            ypk__msm = ['irrelevant']
        utvhs__bto = cgutils.pack_array(builder, [context.
            insert_const_string(builder.module, a) for a in ypk__msm])
        nyf__gvc = cgutils.alloca_once_value(builder, utvhs__bto)
        if isinstance(arr_type, MapArrayType):
            yyz__mjx = _get_map_arr_data_type(arr_type)
            rzz__vqtp = context.make_helper(builder, arr_type, value=in_arr)
            lrnd__irmxb = rzz__vqtp.data
        else:
            yyz__mjx = arr_type
            lrnd__irmxb = in_arr
        gyh__vws = context.make_helper(builder, yyz__mjx, lrnd__irmxb)
        bjo__pojp = lir.FunctionType(lir.IntType(8).as_pointer(), [lir.
            IntType(32).as_pointer(), lir.IntType(8).as_pointer().
            as_pointer(), lir.IntType(64).as_pointer(), lir.IntType(8).
            as_pointer(), lir.IntType(8).as_pointer()])
        rvy__hvxn = cgutils.get_or_insert_function(builder.module,
            bjo__pojp, name='nested_array_to_info')
        eixx__qalp = builder.call(rvy__hvxn, [builder.bitcast(ggazw__dlxrw,
            lir.IntType(32).as_pointer()), builder.bitcast(bclu__aec, lir.
            IntType(8).as_pointer().as_pointer()), builder.bitcast(
            lengths_ptr, lir.IntType(64).as_pointer()), builder.bitcast(
            nyf__gvc, lir.IntType(8).as_pointer()), gyh__vws.meminfo])
        context.compile_internal(builder, lambda :
            check_and_propagate_cpp_exception(), types.none(), [])
        return eixx__qalp
    if arr_type in (string_array_type, binary_array_type):
        jyd__jshs = context.make_helper(builder, arr_type, in_arr)
        vbie__daflu = ArrayItemArrayType(char_arr_type)
        ertq__xtwdn = context.make_helper(builder, vbie__daflu, jyd__jshs.data)
        dbvpe__cht = _get_str_binary_arr_payload(context, builder, in_arr,
            arr_type)
        hcqew__xyna = context.make_helper(builder, offset_arr_type,
            dbvpe__cht.offsets).data
        aoin__csdpx = context.make_helper(builder, char_arr_type,
            dbvpe__cht.data).data
        aegy__xbt = context.make_helper(builder, null_bitmap_arr_type,
            dbvpe__cht.null_bitmap).data
        zwwt__vyb = builder.zext(builder.load(builder.gep(hcqew__xyna, [
            dbvpe__cht.n_arrays])), lir.IntType(64))
        fja__fqmw = context.get_constant(types.int32, int(arr_type ==
            binary_array_type))
        bjo__pojp = lir.FunctionType(lir.IntType(8).as_pointer(), [lir.
            IntType(64), lir.IntType(64), lir.IntType(8).as_pointer(), lir.
            IntType(offset_type.bitwidth).as_pointer(), lir.IntType(8).
            as_pointer(), lir.IntType(8).as_pointer(), lir.IntType(32)])
        rvy__hvxn = cgutils.get_or_insert_function(builder.module,
            bjo__pojp, name='string_array_to_info')
        return builder.call(rvy__hvxn, [dbvpe__cht.n_arrays, zwwt__vyb,
            aoin__csdpx, hcqew__xyna, aegy__xbt, ertq__xtwdn.meminfo,
            fja__fqmw])
    if arr_type == bodo.dict_str_arr_type:
        arr = cgutils.create_struct_proxy(arr_type)(context, builder, in_arr)
        tvj__ghdcj = arr.data
        foah__xlbi = arr.indices
        sig = array_info_type(arr_type.data)
        ubas__bsix = array_to_info_codegen(context, builder, sig, (
            tvj__ghdcj,), False)
        sig = array_info_type(bodo.libs.dict_arr_ext.dict_indices_arr_type)
        kcidb__hlf = array_to_info_codegen(context, builder, sig, (
            foah__xlbi,), False)
        benxz__dtcpw = cgutils.create_struct_proxy(bodo.libs.dict_arr_ext.
            dict_indices_arr_type)(context, builder, foah__xlbi)
        wql__imojb = context.make_array(types.Array(types.uint8, 1, 'C'))(
            context, builder, benxz__dtcpw.null_bitmap).data
        bjo__pojp = lir.FunctionType(lir.IntType(8).as_pointer(), [lir.
            IntType(8).as_pointer(), lir.IntType(8).as_pointer(), lir.
            IntType(8).as_pointer(), lir.IntType(32)])
        rvy__hvxn = cgutils.get_or_insert_function(builder.module,
            bjo__pojp, name='dict_str_array_to_info')
        qjxl__zdrwg = builder.zext(arr.has_global_dictionary, lir.IntType(32))
        return builder.call(rvy__hvxn, [ubas__bsix, kcidb__hlf, builder.
            bitcast(wql__imojb, lir.IntType(8).as_pointer()), qjxl__zdrwg])
    eatmd__nngxp = False
    if isinstance(arr_type, CategoricalArrayType):
        context.nrt.decref(builder, arr_type, in_arr)
        qdfic__pqk = context.compile_internal(builder, lambda a: len(a.
            dtype.categories), types.intp(arr_type), [in_arr])
        in_arr = cgutils.create_struct_proxy(arr_type)(context, builder, in_arr
            ).codes
        caiy__xafd = get_categories_int_type(arr_type.dtype)
        arr_type = types.Array(caiy__xafd, 1, 'C')
        eatmd__nngxp = True
        context.nrt.incref(builder, arr_type, in_arr)
    if isinstance(arr_type, bodo.DatetimeArrayType):
        if eatmd__nngxp:
            raise BodoError(
                'array_to_info(): Categorical PandasDatetimeArrayType not supported'
                )
        in_arr = cgutils.create_struct_proxy(arr_type)(context, builder, in_arr
            ).data
        arr_type = arr_type.data_array_type
    if isinstance(arr_type, types.Array):
        arr = context.make_array(arr_type)(context, builder, in_arr)
        assert arr_type.ndim == 1, 'only 1D array shuffle supported'
        ztrm__slcv = builder.extract_value(arr.shape, 0)
        blxe__plhyf = arr_type.dtype
        pdol__rcay = numba_to_c_type(blxe__plhyf)
        ekb__suuk = cgutils.alloca_once_value(builder, lir.Constant(lir.
            IntType(32), pdol__rcay))
        if eatmd__nngxp:
            bjo__pojp = lir.FunctionType(lir.IntType(8).as_pointer(), [lir.
                IntType(64), lir.IntType(8).as_pointer(), lir.IntType(32),
                lir.IntType(64), lir.IntType(8).as_pointer()])
            rvy__hvxn = cgutils.get_or_insert_function(builder.module,
                bjo__pojp, name='categorical_array_to_info')
            return builder.call(rvy__hvxn, [ztrm__slcv, builder.bitcast(arr
                .data, lir.IntType(8).as_pointer()), builder.load(ekb__suuk
                ), qdfic__pqk, arr.meminfo])
        else:
            bjo__pojp = lir.FunctionType(lir.IntType(8).as_pointer(), [lir.
                IntType(64), lir.IntType(8).as_pointer(), lir.IntType(32),
                lir.IntType(8).as_pointer()])
            rvy__hvxn = cgutils.get_or_insert_function(builder.module,
                bjo__pojp, name='numpy_array_to_info')
            return builder.call(rvy__hvxn, [ztrm__slcv, builder.bitcast(arr
                .data, lir.IntType(8).as_pointer()), builder.load(ekb__suuk
                ), arr.meminfo])
    if isinstance(arr_type, (IntegerArrayType, DecimalArrayType)
        ) or arr_type in (boolean_array, datetime_date_array_type):
        arr = cgutils.create_struct_proxy(arr_type)(context, builder, in_arr)
        blxe__plhyf = arr_type.dtype
        obm__sym = blxe__plhyf
        if isinstance(arr_type, DecimalArrayType):
            obm__sym = int128_type
        if arr_type == datetime_date_array_type:
            obm__sym = types.int64
        lzfpe__iya = context.make_array(types.Array(obm__sym, 1, 'C'))(context,
            builder, arr.data)
        ztrm__slcv = builder.extract_value(lzfpe__iya.shape, 0)
        udf__bip = context.make_array(types.Array(types.uint8, 1, 'C'))(context
            , builder, arr.null_bitmap)
        pdol__rcay = numba_to_c_type(blxe__plhyf)
        ekb__suuk = cgutils.alloca_once_value(builder, lir.Constant(lir.
            IntType(32), pdol__rcay))
        if isinstance(arr_type, DecimalArrayType):
            bjo__pojp = lir.FunctionType(lir.IntType(8).as_pointer(), [lir.
                IntType(64), lir.IntType(8).as_pointer(), lir.IntType(32),
                lir.IntType(8).as_pointer(), lir.IntType(8).as_pointer(),
                lir.IntType(8).as_pointer(), lir.IntType(32), lir.IntType(32)])
            rvy__hvxn = cgutils.get_or_insert_function(builder.module,
                bjo__pojp, name='decimal_array_to_info')
            return builder.call(rvy__hvxn, [ztrm__slcv, builder.bitcast(
                lzfpe__iya.data, lir.IntType(8).as_pointer()), builder.load
                (ekb__suuk), builder.bitcast(udf__bip.data, lir.IntType(8).
                as_pointer()), lzfpe__iya.meminfo, udf__bip.meminfo,
                context.get_constant(types.int32, arr_type.precision),
                context.get_constant(types.int32, arr_type.scale)])
        else:
            bjo__pojp = lir.FunctionType(lir.IntType(8).as_pointer(), [lir.
                IntType(64), lir.IntType(8).as_pointer(), lir.IntType(32),
                lir.IntType(8).as_pointer(), lir.IntType(8).as_pointer(),
                lir.IntType(8).as_pointer()])
            rvy__hvxn = cgutils.get_or_insert_function(builder.module,
                bjo__pojp, name='nullable_array_to_info')
            return builder.call(rvy__hvxn, [ztrm__slcv, builder.bitcast(
                lzfpe__iya.data, lir.IntType(8).as_pointer()), builder.load
                (ekb__suuk), builder.bitcast(udf__bip.data, lir.IntType(8).
                as_pointer()), lzfpe__iya.meminfo, udf__bip.meminfo])
    if isinstance(arr_type, IntervalArrayType):
        assert isinstance(arr_type.arr_type, types.Array
            ), 'array_to_info(): only IntervalArrayType with Numpy arrays supported'
        arr = cgutils.create_struct_proxy(arr_type)(context, builder, in_arr)
        jmnh__dna = context.make_array(arr_type.arr_type)(context, builder,
            arr.left)
        ljd__rei = context.make_array(arr_type.arr_type)(context, builder,
            arr.right)
        ztrm__slcv = builder.extract_value(jmnh__dna.shape, 0)
        pdol__rcay = numba_to_c_type(arr_type.arr_type.dtype)
        ekb__suuk = cgutils.alloca_once_value(builder, lir.Constant(lir.
            IntType(32), pdol__rcay))
        bjo__pojp = lir.FunctionType(lir.IntType(8).as_pointer(), [lir.
            IntType(64), lir.IntType(8).as_pointer(), lir.IntType(8).
            as_pointer(), lir.IntType(32), lir.IntType(8).as_pointer(), lir
            .IntType(8).as_pointer()])
        rvy__hvxn = cgutils.get_or_insert_function(builder.module,
            bjo__pojp, name='interval_array_to_info')
        return builder.call(rvy__hvxn, [ztrm__slcv, builder.bitcast(
            jmnh__dna.data, lir.IntType(8).as_pointer()), builder.bitcast(
            ljd__rei.data, lir.IntType(8).as_pointer()), builder.load(
            ekb__suuk), jmnh__dna.meminfo, ljd__rei.meminfo])
    raise_bodo_error(f'array_to_info(): array type {arr_type} is not supported'
        )


def _lower_info_to_array_numpy(arr_type, context, builder, in_info):
    assert arr_type.ndim == 1, 'only 1D array supported'
    arr = context.make_array(arr_type)(context, builder)
    wqsiz__jjeh = cgutils.alloca_once(builder, lir.IntType(64))
    dtwz__cglej = cgutils.alloca_once(builder, lir.IntType(8).as_pointer())
    qrbe__lmpn = cgutils.alloca_once(builder, lir.IntType(8).as_pointer())
    bjo__pojp = lir.FunctionType(lir.VoidType(), [lir.IntType(8).as_pointer
        (), lir.IntType(64).as_pointer(), lir.IntType(8).as_pointer().
        as_pointer(), lir.IntType(8).as_pointer().as_pointer()])
    rvy__hvxn = cgutils.get_or_insert_function(builder.module, bjo__pojp,
        name='info_to_numpy_array')
    builder.call(rvy__hvxn, [in_info, wqsiz__jjeh, dtwz__cglej, qrbe__lmpn])
    context.compile_internal(builder, lambda :
        check_and_propagate_cpp_exception(), types.none(), [])
    jjxg__irlto = context.get_value_type(types.intp)
    iht__hbdms = cgutils.pack_array(builder, [builder.load(wqsiz__jjeh)],
        ty=jjxg__irlto)
    catx__ayjk = context.get_constant(types.intp, context.get_abi_sizeof(
        context.get_data_type(arr_type.dtype)))
    rfl__uxa = cgutils.pack_array(builder, [catx__ayjk], ty=jjxg__irlto)
    aoin__csdpx = builder.bitcast(builder.load(dtwz__cglej), context.
        get_data_type(arr_type.dtype).as_pointer())
    numba.np.arrayobj.populate_array(arr, data=aoin__csdpx, shape=
        iht__hbdms, strides=rfl__uxa, itemsize=catx__ayjk, meminfo=builder.
        load(qrbe__lmpn))
    return arr._getvalue()


def _lower_info_to_array_list_string_array(arr_type, context, builder, in_info
    ):
    utsrm__rkf = context.make_helper(builder, arr_type)
    bjo__pojp = lir.FunctionType(lir.VoidType(), [lir.IntType(8).as_pointer
        (), lir.IntType(8).as_pointer().as_pointer()])
    rvy__hvxn = cgutils.get_or_insert_function(builder.module, bjo__pojp,
        name='info_to_list_string_array')
    builder.call(rvy__hvxn, [in_info, utsrm__rkf._get_ptr_by_name('meminfo')])
    context.compile_internal(builder, lambda :
        check_and_propagate_cpp_exception(), types.none(), [])
    return utsrm__rkf._getvalue()


def nested_to_array(context, builder, arr_typ, lengths_ptr, array_infos_ptr,
    lengths_pos, infos_pos):
    haqx__paz = context.get_data_type(array_info_type)
    if isinstance(arr_typ, ArrayItemArrayType):
        gadv__wvtc = lengths_pos
        tmqan__skowq = infos_pos
        urord__yem, lengths_pos, infos_pos = nested_to_array(context,
            builder, arr_typ.dtype, lengths_ptr, array_infos_ptr, 
            lengths_pos + 1, infos_pos + 2)
        ycm__vzgbc = ArrayItemArrayPayloadType(arr_typ)
        nxro__vjpcu = context.get_data_type(ycm__vzgbc)
        vczrp__mlyeb = context.get_abi_sizeof(nxro__vjpcu)
        nxa__lquyu = define_array_item_dtor(context, builder, arr_typ,
            ycm__vzgbc)
        yvlb__oxdd = context.nrt.meminfo_alloc_dtor(builder, context.
            get_constant(types.uintp, vczrp__mlyeb), nxa__lquyu)
        hkn__nbhe = context.nrt.meminfo_data(builder, yvlb__oxdd)
        odn__ngq = builder.bitcast(hkn__nbhe, nxro__vjpcu.as_pointer())
        dbvpe__cht = cgutils.create_struct_proxy(ycm__vzgbc)(context, builder)
        dbvpe__cht.n_arrays = builder.extract_value(builder.load(
            lengths_ptr), gadv__wvtc)
        dbvpe__cht.data = urord__yem
        dwrgn__gbp = builder.load(array_infos_ptr)
        ufvf__zhr = builder.bitcast(builder.extract_value(dwrgn__gbp,
            tmqan__skowq), haqx__paz)
        dbvpe__cht.offsets = _lower_info_to_array_numpy(types.Array(
            offset_type, 1, 'C'), context, builder, ufvf__zhr)
        cyi__jxvz = builder.bitcast(builder.extract_value(dwrgn__gbp, 
            tmqan__skowq + 1), haqx__paz)
        dbvpe__cht.null_bitmap = _lower_info_to_array_numpy(types.Array(
            types.uint8, 1, 'C'), context, builder, cyi__jxvz)
        builder.store(dbvpe__cht._getvalue(), odn__ngq)
        ertq__xtwdn = context.make_helper(builder, arr_typ)
        ertq__xtwdn.meminfo = yvlb__oxdd
        return ertq__xtwdn._getvalue(), lengths_pos, infos_pos
    elif isinstance(arr_typ, StructArrayType):
        uwses__donlk = []
        tmqan__skowq = infos_pos
        lengths_pos += 1
        infos_pos += 1
        for bqw__wdc in arr_typ.data:
            urord__yem, lengths_pos, infos_pos = nested_to_array(context,
                builder, bqw__wdc, lengths_ptr, array_infos_ptr,
                lengths_pos, infos_pos)
            uwses__donlk.append(urord__yem)
        ycm__vzgbc = StructArrayPayloadType(arr_typ.data)
        nxro__vjpcu = context.get_value_type(ycm__vzgbc)
        vczrp__mlyeb = context.get_abi_sizeof(nxro__vjpcu)
        nxa__lquyu = define_struct_arr_dtor(context, builder, arr_typ,
            ycm__vzgbc)
        yvlb__oxdd = context.nrt.meminfo_alloc_dtor(builder, context.
            get_constant(types.uintp, vczrp__mlyeb), nxa__lquyu)
        hkn__nbhe = context.nrt.meminfo_data(builder, yvlb__oxdd)
        odn__ngq = builder.bitcast(hkn__nbhe, nxro__vjpcu.as_pointer())
        dbvpe__cht = cgutils.create_struct_proxy(ycm__vzgbc)(context, builder)
        dbvpe__cht.data = cgutils.pack_array(builder, uwses__donlk
            ) if types.is_homogeneous(*arr_typ.data) else cgutils.pack_struct(
            builder, uwses__donlk)
        dwrgn__gbp = builder.load(array_infos_ptr)
        cyi__jxvz = builder.bitcast(builder.extract_value(dwrgn__gbp,
            tmqan__skowq), haqx__paz)
        dbvpe__cht.null_bitmap = _lower_info_to_array_numpy(types.Array(
            types.uint8, 1, 'C'), context, builder, cyi__jxvz)
        builder.store(dbvpe__cht._getvalue(), odn__ngq)
        xfjz__qcpqa = context.make_helper(builder, arr_typ)
        xfjz__qcpqa.meminfo = yvlb__oxdd
        return xfjz__qcpqa._getvalue(), lengths_pos, infos_pos
    elif arr_typ in (string_array_type, binary_array_type):
        dwrgn__gbp = builder.load(array_infos_ptr)
        lqwh__huxng = builder.bitcast(builder.extract_value(dwrgn__gbp,
            infos_pos), haqx__paz)
        jyd__jshs = context.make_helper(builder, arr_typ)
        vbie__daflu = ArrayItemArrayType(char_arr_type)
        ertq__xtwdn = context.make_helper(builder, vbie__daflu)
        bjo__pojp = lir.FunctionType(lir.VoidType(), [lir.IntType(8).
            as_pointer(), lir.IntType(8).as_pointer().as_pointer()])
        rvy__hvxn = cgutils.get_or_insert_function(builder.module,
            bjo__pojp, name='info_to_string_array')
        builder.call(rvy__hvxn, [lqwh__huxng, ertq__xtwdn._get_ptr_by_name(
            'meminfo')])
        context.compile_internal(builder, lambda :
            check_and_propagate_cpp_exception(), types.none(), [])
        jyd__jshs.data = ertq__xtwdn._getvalue()
        return jyd__jshs._getvalue(), lengths_pos + 1, infos_pos + 1
    elif isinstance(arr_typ, types.Array):
        dwrgn__gbp = builder.load(array_infos_ptr)
        sowrv__krbe = builder.bitcast(builder.extract_value(dwrgn__gbp, 
            infos_pos + 1), haqx__paz)
        return _lower_info_to_array_numpy(arr_typ, context, builder,
            sowrv__krbe), lengths_pos + 1, infos_pos + 2
    elif isinstance(arr_typ, (IntegerArrayType, DecimalArrayType)
        ) or arr_typ in (boolean_array, datetime_date_array_type):
        arr = cgutils.create_struct_proxy(arr_typ)(context, builder)
        obm__sym = arr_typ.dtype
        if isinstance(arr_typ, DecimalArrayType):
            obm__sym = int128_type
        elif arr_typ == datetime_date_array_type:
            obm__sym = types.int64
        dwrgn__gbp = builder.load(array_infos_ptr)
        cyi__jxvz = builder.bitcast(builder.extract_value(dwrgn__gbp,
            infos_pos), haqx__paz)
        arr.null_bitmap = _lower_info_to_array_numpy(types.Array(types.
            uint8, 1, 'C'), context, builder, cyi__jxvz)
        sowrv__krbe = builder.bitcast(builder.extract_value(dwrgn__gbp, 
            infos_pos + 1), haqx__paz)
        arr.data = _lower_info_to_array_numpy(types.Array(obm__sym, 1, 'C'),
            context, builder, sowrv__krbe)
        return arr._getvalue(), lengths_pos + 1, infos_pos + 2


def info_to_array_codegen(context, builder, sig, args):
    array_type = sig.args[1]
    arr_type = array_type.instance_type if isinstance(array_type, types.TypeRef
        ) else array_type
    in_info, aryfy__wwn = args
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
                return 1 + sum([get_num_arrays(bqw__wdc) for bqw__wdc in
                    arr_typ.data])
            else:
                return 1

        def get_num_infos(arr_typ):
            if isinstance(arr_typ, ArrayItemArrayType):
                return 2 + get_num_infos(arr_typ.dtype)
            elif isinstance(arr_typ, StructArrayType):
                return 1 + sum([get_num_infos(bqw__wdc) for bqw__wdc in
                    arr_typ.data])
            elif arr_typ in (string_array_type, binary_array_type):
                return 1
            else:
                return 2
        if isinstance(arr_type, TupleArrayType):
            btv__dvptg = StructArrayType(arr_type.data, ('dummy',) * len(
                arr_type.data))
        elif isinstance(arr_type, MapArrayType):
            btv__dvptg = _get_map_arr_data_type(arr_type)
        else:
            btv__dvptg = arr_type
        ufi__nceop = get_num_arrays(btv__dvptg)
        hjly__krvek = cgutils.pack_array(builder, [lir.Constant(lir.IntType
            (64), 0) for aryfy__wwn in range(ufi__nceop)])
        lengths_ptr = cgutils.alloca_once_value(builder, hjly__krvek)
        luuw__qnu = lir.Constant(lir.IntType(8).as_pointer(), None)
        cif__xje = cgutils.pack_array(builder, [luuw__qnu for aryfy__wwn in
            range(get_num_infos(btv__dvptg))])
        array_infos_ptr = cgutils.alloca_once_value(builder, cif__xje)
        bjo__pojp = lir.FunctionType(lir.VoidType(), [lir.IntType(8).
            as_pointer(), lir.IntType(64).as_pointer(), lir.IntType(8).
            as_pointer().as_pointer()])
        rvy__hvxn = cgutils.get_or_insert_function(builder.module,
            bjo__pojp, name='info_to_nested_array')
        builder.call(rvy__hvxn, [in_info, builder.bitcast(lengths_ptr, lir.
            IntType(64).as_pointer()), builder.bitcast(array_infos_ptr, lir
            .IntType(8).as_pointer().as_pointer())])
        context.compile_internal(builder, lambda :
            check_and_propagate_cpp_exception(), types.none(), [])
        arr, aryfy__wwn, aryfy__wwn = nested_to_array(context, builder,
            btv__dvptg, lengths_ptr, array_infos_ptr, 0, 0)
        if isinstance(arr_type, TupleArrayType):
            qjh__gqh = context.make_helper(builder, arr_type)
            qjh__gqh.data = arr
            context.nrt.incref(builder, btv__dvptg, arr)
            arr = qjh__gqh._getvalue()
        elif isinstance(arr_type, MapArrayType):
            sig = signature(arr_type, btv__dvptg)
            arr = init_map_arr_codegen(context, builder, sig, (arr,))
        return arr
    if arr_type in (string_array_type, binary_array_type):
        jyd__jshs = context.make_helper(builder, arr_type)
        vbie__daflu = ArrayItemArrayType(char_arr_type)
        ertq__xtwdn = context.make_helper(builder, vbie__daflu)
        bjo__pojp = lir.FunctionType(lir.VoidType(), [lir.IntType(8).
            as_pointer(), lir.IntType(8).as_pointer().as_pointer()])
        rvy__hvxn = cgutils.get_or_insert_function(builder.module,
            bjo__pojp, name='info_to_string_array')
        builder.call(rvy__hvxn, [in_info, ertq__xtwdn._get_ptr_by_name(
            'meminfo')])
        context.compile_internal(builder, lambda :
            check_and_propagate_cpp_exception(), types.none(), [])
        jyd__jshs.data = ertq__xtwdn._getvalue()
        return jyd__jshs._getvalue()
    if arr_type == bodo.dict_str_arr_type:
        bjo__pojp = lir.FunctionType(lir.IntType(8).as_pointer(), [lir.
            IntType(8).as_pointer(), lir.IntType(32)])
        rvy__hvxn = cgutils.get_or_insert_function(builder.module,
            bjo__pojp, name='get_nested_info')
        ubas__bsix = builder.call(rvy__hvxn, [in_info, lir.Constant(lir.
            IntType(32), 1)])
        kcidb__hlf = builder.call(rvy__hvxn, [in_info, lir.Constant(lir.
            IntType(32), 2)])
        nrag__hvzlo = context.make_helper(builder, arr_type)
        sig = arr_type.data(array_info_type, arr_type.data)
        nrag__hvzlo.data = info_to_array_codegen(context, builder, sig, (
            ubas__bsix, context.get_constant_null(arr_type.data)))
        tskg__wjhix = bodo.libs.dict_arr_ext.dict_indices_arr_type
        sig = tskg__wjhix(array_info_type, tskg__wjhix)
        nrag__hvzlo.indices = info_to_array_codegen(context, builder, sig,
            (kcidb__hlf, context.get_constant_null(tskg__wjhix)))
        bjo__pojp = lir.FunctionType(lir.IntType(32), [lir.IntType(8).
            as_pointer()])
        rvy__hvxn = cgutils.get_or_insert_function(builder.module,
            bjo__pojp, name='get_has_global_dictionary')
        qjxl__zdrwg = builder.call(rvy__hvxn, [in_info])
        nrag__hvzlo.has_global_dictionary = builder.trunc(qjxl__zdrwg,
            cgutils.bool_t)
        return nrag__hvzlo._getvalue()
    if isinstance(arr_type, CategoricalArrayType):
        out_arr = cgutils.create_struct_proxy(arr_type)(context, builder)
        caiy__xafd = get_categories_int_type(arr_type.dtype)
        mntg__mil = types.Array(caiy__xafd, 1, 'C')
        out_arr.codes = _lower_info_to_array_numpy(mntg__mil, context,
            builder, in_info)
        if isinstance(array_type, types.TypeRef):
            assert arr_type.dtype.categories is not None, 'info_to_array: unknown categories'
            is_ordered = arr_type.dtype.ordered
            wfll__tkql = pd.CategoricalDtype(arr_type.dtype.categories,
                is_ordered).categories.values
            new_cats_tup = MetaType(tuple(wfll__tkql))
            int_type = arr_type.dtype.int_type
            iobqw__wja = bodo.typeof(wfll__tkql)
            yav__bmgwd = context.get_constant_generic(builder, iobqw__wja,
                wfll__tkql)
            blxe__plhyf = context.compile_internal(builder, lambda c_arr:
                bodo.hiframes.pd_categorical_ext.init_cat_dtype(bodo.utils.
                conversion.index_from_array(c_arr), is_ordered, int_type,
                new_cats_tup), arr_type.dtype(iobqw__wja), [yav__bmgwd])
        else:
            blxe__plhyf = cgutils.create_struct_proxy(arr_type)(context,
                builder, args[1]).dtype
            context.nrt.incref(builder, arr_type.dtype, blxe__plhyf)
        out_arr.dtype = blxe__plhyf
        return out_arr._getvalue()
    if isinstance(arr_type, bodo.DatetimeArrayType):
        arr = cgutils.create_struct_proxy(arr_type)(context, builder)
        aoin__csdpx = _lower_info_to_array_numpy(arr_type.data_array_type,
            context, builder, in_info)
        arr.data = aoin__csdpx
        return arr._getvalue()
    if isinstance(arr_type, types.Array):
        return _lower_info_to_array_numpy(arr_type, context, builder, in_info)
    if isinstance(arr_type, (IntegerArrayType, DecimalArrayType)
        ) or arr_type in (boolean_array, datetime_date_array_type):
        arr = cgutils.create_struct_proxy(arr_type)(context, builder)
        obm__sym = arr_type.dtype
        if isinstance(arr_type, DecimalArrayType):
            obm__sym = int128_type
        elif arr_type == datetime_date_array_type:
            obm__sym = types.int64
        yuygh__vzflu = types.Array(obm__sym, 1, 'C')
        lzfpe__iya = context.make_array(yuygh__vzflu)(context, builder)
        fmpnp__bzcg = types.Array(types.uint8, 1, 'C')
        setjq__rbx = context.make_array(fmpnp__bzcg)(context, builder)
        wqsiz__jjeh = cgutils.alloca_once(builder, lir.IntType(64))
        uryl__dzk = cgutils.alloca_once(builder, lir.IntType(64))
        dtwz__cglej = cgutils.alloca_once(builder, lir.IntType(8).as_pointer())
        qbyz__yegk = cgutils.alloca_once(builder, lir.IntType(8).as_pointer())
        qrbe__lmpn = cgutils.alloca_once(builder, lir.IntType(8).as_pointer())
        yghvf__kxg = cgutils.alloca_once(builder, lir.IntType(8).as_pointer())
        bjo__pojp = lir.FunctionType(lir.VoidType(), [lir.IntType(8).
            as_pointer(), lir.IntType(64).as_pointer(), lir.IntType(64).
            as_pointer(), lir.IntType(8).as_pointer().as_pointer(), lir.
            IntType(8).as_pointer().as_pointer(), lir.IntType(8).as_pointer
            ().as_pointer(), lir.IntType(8).as_pointer().as_pointer()])
        rvy__hvxn = cgutils.get_or_insert_function(builder.module,
            bjo__pojp, name='info_to_nullable_array')
        builder.call(rvy__hvxn, [in_info, wqsiz__jjeh, uryl__dzk,
            dtwz__cglej, qbyz__yegk, qrbe__lmpn, yghvf__kxg])
        context.compile_internal(builder, lambda :
            check_and_propagate_cpp_exception(), types.none(), [])
        jjxg__irlto = context.get_value_type(types.intp)
        iht__hbdms = cgutils.pack_array(builder, [builder.load(wqsiz__jjeh)
            ], ty=jjxg__irlto)
        catx__ayjk = context.get_constant(types.intp, context.
            get_abi_sizeof(context.get_data_type(obm__sym)))
        rfl__uxa = cgutils.pack_array(builder, [catx__ayjk], ty=jjxg__irlto)
        aoin__csdpx = builder.bitcast(builder.load(dtwz__cglej), context.
            get_data_type(obm__sym).as_pointer())
        numba.np.arrayobj.populate_array(lzfpe__iya, data=aoin__csdpx,
            shape=iht__hbdms, strides=rfl__uxa, itemsize=catx__ayjk,
            meminfo=builder.load(qrbe__lmpn))
        arr.data = lzfpe__iya._getvalue()
        iht__hbdms = cgutils.pack_array(builder, [builder.load(uryl__dzk)],
            ty=jjxg__irlto)
        catx__ayjk = context.get_constant(types.intp, context.
            get_abi_sizeof(context.get_data_type(types.uint8)))
        rfl__uxa = cgutils.pack_array(builder, [catx__ayjk], ty=jjxg__irlto)
        aoin__csdpx = builder.bitcast(builder.load(qbyz__yegk), context.
            get_data_type(types.uint8).as_pointer())
        numba.np.arrayobj.populate_array(setjq__rbx, data=aoin__csdpx,
            shape=iht__hbdms, strides=rfl__uxa, itemsize=catx__ayjk,
            meminfo=builder.load(yghvf__kxg))
        arr.null_bitmap = setjq__rbx._getvalue()
        return arr._getvalue()
    if isinstance(arr_type, IntervalArrayType):
        arr = cgutils.create_struct_proxy(arr_type)(context, builder)
        jmnh__dna = context.make_array(arr_type.arr_type)(context, builder)
        ljd__rei = context.make_array(arr_type.arr_type)(context, builder)
        wqsiz__jjeh = cgutils.alloca_once(builder, lir.IntType(64))
        ysh__wpwj = cgutils.alloca_once(builder, lir.IntType(8).as_pointer())
        qqx__rdd = cgutils.alloca_once(builder, lir.IntType(8).as_pointer())
        rql__ulyml = cgutils.alloca_once(builder, lir.IntType(8).as_pointer())
        gzvio__xzrdz = cgutils.alloca_once(builder, lir.IntType(8).as_pointer()
            )
        bjo__pojp = lir.FunctionType(lir.VoidType(), [lir.IntType(8).
            as_pointer(), lir.IntType(64).as_pointer(), lir.IntType(8).
            as_pointer().as_pointer(), lir.IntType(8).as_pointer().
            as_pointer(), lir.IntType(8).as_pointer().as_pointer(), lir.
            IntType(8).as_pointer().as_pointer()])
        rvy__hvxn = cgutils.get_or_insert_function(builder.module,
            bjo__pojp, name='info_to_interval_array')
        builder.call(rvy__hvxn, [in_info, wqsiz__jjeh, ysh__wpwj, qqx__rdd,
            rql__ulyml, gzvio__xzrdz])
        context.compile_internal(builder, lambda :
            check_and_propagate_cpp_exception(), types.none(), [])
        jjxg__irlto = context.get_value_type(types.intp)
        iht__hbdms = cgutils.pack_array(builder, [builder.load(wqsiz__jjeh)
            ], ty=jjxg__irlto)
        catx__ayjk = context.get_constant(types.intp, context.
            get_abi_sizeof(context.get_data_type(arr_type.arr_type.dtype)))
        rfl__uxa = cgutils.pack_array(builder, [catx__ayjk], ty=jjxg__irlto)
        efwy__wgvj = builder.bitcast(builder.load(ysh__wpwj), context.
            get_data_type(arr_type.arr_type.dtype).as_pointer())
        numba.np.arrayobj.populate_array(jmnh__dna, data=efwy__wgvj, shape=
            iht__hbdms, strides=rfl__uxa, itemsize=catx__ayjk, meminfo=
            builder.load(rql__ulyml))
        arr.left = jmnh__dna._getvalue()
        rnh__vltog = builder.bitcast(builder.load(qqx__rdd), context.
            get_data_type(arr_type.arr_type.dtype).as_pointer())
        numba.np.arrayobj.populate_array(ljd__rei, data=rnh__vltog, shape=
            iht__hbdms, strides=rfl__uxa, itemsize=catx__ayjk, meminfo=
            builder.load(gzvio__xzrdz))
        arr.right = ljd__rei._getvalue()
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
        ztrm__slcv, aryfy__wwn = args
        pdol__rcay = numba_to_c_type(array_type.dtype)
        ekb__suuk = cgutils.alloca_once_value(builder, lir.Constant(lir.
            IntType(32), pdol__rcay))
        bjo__pojp = lir.FunctionType(lir.IntType(8).as_pointer(), [lir.
            IntType(64), lir.IntType(32)])
        rvy__hvxn = cgutils.get_or_insert_function(builder.module,
            bjo__pojp, name='alloc_numpy')
        return builder.call(rvy__hvxn, [ztrm__slcv, builder.load(ekb__suuk)])
    return array_info_type(len_typ, arr_type), codegen


@intrinsic
def test_alloc_string(typingctx, len_typ, n_chars_typ):

    def codegen(context, builder, sig, args):
        ztrm__slcv, oqgn__wxca = args
        bjo__pojp = lir.FunctionType(lir.IntType(8).as_pointer(), [lir.
            IntType(64), lir.IntType(64)])
        rvy__hvxn = cgutils.get_or_insert_function(builder.module,
            bjo__pojp, name='alloc_string_array')
        return builder.call(rvy__hvxn, [ztrm__slcv, oqgn__wxca])
    return array_info_type(len_typ, n_chars_typ), codegen


@intrinsic
def arr_info_list_to_table(typingctx, list_arr_info_typ=None):
    assert list_arr_info_typ == types.List(array_info_type)
    return table_type(list_arr_info_typ), arr_info_list_to_table_codegen


def arr_info_list_to_table_codegen(context, builder, sig, args):
    nsbcp__hqgw, = args
    xra__ukwe = numba.cpython.listobj.ListInstance(context, builder, sig.
        args[0], nsbcp__hqgw)
    bjo__pojp = lir.FunctionType(lir.IntType(8).as_pointer(), [lir.IntType(
        8).as_pointer().as_pointer(), lir.IntType(64)])
    rvy__hvxn = cgutils.get_or_insert_function(builder.module, bjo__pojp,
        name='arr_info_list_to_table')
    return builder.call(rvy__hvxn, [xra__ukwe.data, xra__ukwe.size])


@intrinsic
def info_from_table(typingctx, table_t, ind_t):

    def codegen(context, builder, sig, args):
        bjo__pojp = lir.FunctionType(lir.IntType(8).as_pointer(), [lir.
            IntType(8).as_pointer(), lir.IntType(64)])
        rvy__hvxn = cgutils.get_or_insert_function(builder.module,
            bjo__pojp, name='info_from_table')
        return builder.call(rvy__hvxn, args)
    return array_info_type(table_t, ind_t), codegen


@intrinsic
def cpp_table_to_py_table(typingctx, cpp_table_t, table_idx_arr_t,
    py_table_type_t):
    assert cpp_table_t == table_type, 'invalid cpp table type'
    assert isinstance(table_idx_arr_t, types.Array
        ) and table_idx_arr_t.dtype == types.int64, 'invalid table index array'
    assert isinstance(py_table_type_t, types.TypeRef), 'invalid py table ref'
    mjocb__rxeak = py_table_type_t.instance_type

    def codegen(context, builder, sig, args):
        nuarn__qkpf, qdnf__zprcb, aryfy__wwn = args
        bjo__pojp = lir.FunctionType(lir.IntType(8).as_pointer(), [lir.
            IntType(8).as_pointer(), lir.IntType(64)])
        rvy__hvxn = cgutils.get_or_insert_function(builder.module,
            bjo__pojp, name='info_from_table')
        rlubc__mbl = cgutils.create_struct_proxy(mjocb__rxeak)(context, builder
            )
        rlubc__mbl.parent = cgutils.get_null_value(rlubc__mbl.parent.type)
        bkpgg__cbubq = context.make_array(table_idx_arr_t)(context, builder,
            qdnf__zprcb)
        ivokw__bpt = context.get_constant(types.int64, -1)
        qypm__utoy = context.get_constant(types.int64, 0)
        gbheq__uulsb = cgutils.alloca_once_value(builder, qypm__utoy)
        for t, yadeh__pdbr in mjocb__rxeak.type_to_blk.items():
            onnj__dvwku = context.get_constant(types.int64, len(
                mjocb__rxeak.block_to_arr_ind[yadeh__pdbr]))
            aryfy__wwn, ubcju__bdi = ListInstance.allocate_ex(context,
                builder, types.List(t), onnj__dvwku)
            ubcju__bdi.size = onnj__dvwku
            vykx__cemv = context.make_constant_array(builder, types.Array(
                types.int64, 1, 'C'), np.array(mjocb__rxeak.
                block_to_arr_ind[yadeh__pdbr], dtype=np.int64))
            tdege__jiyg = context.make_array(types.Array(types.int64, 1, 'C'))(
                context, builder, vykx__cemv)
            with cgutils.for_range(builder, onnj__dvwku) as lfhd__pvdv:
                nyk__kgymk = lfhd__pvdv.index
                lxr__xgsk = _getitem_array_single_int(context, builder,
                    types.int64, types.Array(types.int64, 1, 'C'),
                    tdege__jiyg, nyk__kgymk)
                rcbz__nlhl = _getitem_array_single_int(context, builder,
                    types.int64, table_idx_arr_t, bkpgg__cbubq, lxr__xgsk)
                vhnge__pcfdw = builder.icmp_unsigned('!=', rcbz__nlhl,
                    ivokw__bpt)
                with builder.if_else(vhnge__pcfdw) as (qcfx__arv, kvubq__mhc):
                    with qcfx__arv:
                        jvp__oies = builder.call(rvy__hvxn, [nuarn__qkpf,
                            rcbz__nlhl])
                        arr = context.compile_internal(builder, lambda info:
                            info_to_array(info, t), t(array_info_type), [
                            jvp__oies])
                        ubcju__bdi.inititem(nyk__kgymk, arr, incref=False)
                        ztrm__slcv = context.compile_internal(builder, lambda
                            arr: len(arr), types.int64(t), [arr])
                        builder.store(ztrm__slcv, gbheq__uulsb)
                    with kvubq__mhc:
                        jym__lvn = context.get_constant_null(t)
                        ubcju__bdi.inititem(nyk__kgymk, jym__lvn, incref=False)
            setattr(rlubc__mbl, f'block_{yadeh__pdbr}', ubcju__bdi.value)
        rlubc__mbl.len = builder.load(gbheq__uulsb)
        return rlubc__mbl._getvalue()
    return mjocb__rxeak(cpp_table_t, table_idx_arr_t, py_table_type_t), codegen


@intrinsic
def py_table_to_cpp_table(typingctx, py_table_t, py_table_type_t):
    assert isinstance(py_table_t, bodo.hiframes.table.TableType
        ), 'invalid py table type'
    assert isinstance(py_table_type_t, types.TypeRef), 'invalid py table ref'
    mjocb__rxeak = py_table_type_t.instance_type

    def codegen(context, builder, sig, args):
        fuwd__jcg, aryfy__wwn = args
        doh__mlshl = cgutils.create_struct_proxy(mjocb__rxeak)(context,
            builder, fuwd__jcg)
        if mjocb__rxeak.has_runtime_cols:
            tnoxd__eeq = lir.Constant(lir.IntType(64), 0)
            for yadeh__pdbr, t in enumerate(mjocb__rxeak.arr_types):
                wvdtr__vil = getattr(doh__mlshl, f'block_{yadeh__pdbr}')
                tnt__chpz = ListInstance(context, builder, types.List(t),
                    wvdtr__vil)
                tnoxd__eeq = builder.add(tnoxd__eeq, tnt__chpz.size)
        else:
            tnoxd__eeq = lir.Constant(lir.IntType(64), len(mjocb__rxeak.
                arr_types))
        aryfy__wwn, jxlfa__muyy = ListInstance.allocate_ex(context, builder,
            types.List(array_info_type), tnoxd__eeq)
        jxlfa__muyy.size = tnoxd__eeq
        if mjocb__rxeak.has_runtime_cols:
            tincg__vpxmc = lir.Constant(lir.IntType(64), 0)
            for yadeh__pdbr, t in enumerate(mjocb__rxeak.arr_types):
                wvdtr__vil = getattr(doh__mlshl, f'block_{yadeh__pdbr}')
                tnt__chpz = ListInstance(context, builder, types.List(t),
                    wvdtr__vil)
                onnj__dvwku = tnt__chpz.size
                with cgutils.for_range(builder, onnj__dvwku) as lfhd__pvdv:
                    nyk__kgymk = lfhd__pvdv.index
                    arr = tnt__chpz.getitem(nyk__kgymk)
                    bxs__zroaz = signature(array_info_type, t)
                    jpq__gtwuh = arr,
                    cdky__pkc = array_to_info_codegen(context, builder,
                        bxs__zroaz, jpq__gtwuh)
                    jxlfa__muyy.inititem(builder.add(tincg__vpxmc,
                        nyk__kgymk), cdky__pkc, incref=False)
                tincg__vpxmc = builder.add(tincg__vpxmc, onnj__dvwku)
        else:
            for t, yadeh__pdbr in mjocb__rxeak.type_to_blk.items():
                onnj__dvwku = context.get_constant(types.int64, len(
                    mjocb__rxeak.block_to_arr_ind[yadeh__pdbr]))
                wvdtr__vil = getattr(doh__mlshl, f'block_{yadeh__pdbr}')
                tnt__chpz = ListInstance(context, builder, types.List(t),
                    wvdtr__vil)
                vykx__cemv = context.make_constant_array(builder, types.
                    Array(types.int64, 1, 'C'), np.array(mjocb__rxeak.
                    block_to_arr_ind[yadeh__pdbr], dtype=np.int64))
                tdege__jiyg = context.make_array(types.Array(types.int64, 1,
                    'C'))(context, builder, vykx__cemv)
                with cgutils.for_range(builder, onnj__dvwku) as lfhd__pvdv:
                    nyk__kgymk = lfhd__pvdv.index
                    lxr__xgsk = _getitem_array_single_int(context, builder,
                        types.int64, types.Array(types.int64, 1, 'C'),
                        tdege__jiyg, nyk__kgymk)
                    wtero__lobyr = signature(types.none, mjocb__rxeak,
                        types.List(t), types.int64, types.int64)
                    hej__predo = fuwd__jcg, wvdtr__vil, nyk__kgymk, lxr__xgsk
                    bodo.hiframes.table.ensure_column_unboxed_codegen(context,
                        builder, wtero__lobyr, hej__predo)
                    arr = tnt__chpz.getitem(nyk__kgymk)
                    bxs__zroaz = signature(array_info_type, t)
                    jpq__gtwuh = arr,
                    cdky__pkc = array_to_info_codegen(context, builder,
                        bxs__zroaz, jpq__gtwuh)
                    jxlfa__muyy.inititem(lxr__xgsk, cdky__pkc, incref=False)
        bbx__pztt = jxlfa__muyy.value
        uppco__qcn = signature(table_type, types.List(array_info_type))
        ljjom__ntxo = bbx__pztt,
        nuarn__qkpf = arr_info_list_to_table_codegen(context, builder,
            uppco__qcn, ljjom__ntxo)
        context.nrt.decref(builder, types.List(array_info_type), bbx__pztt)
        return nuarn__qkpf
    return table_type(mjocb__rxeak, py_table_type_t), codegen


delete_info_decref_array = types.ExternalFunction('delete_info_decref_array',
    types.void(array_info_type))
delete_table_decref_arrays = types.ExternalFunction(
    'delete_table_decref_arrays', types.void(table_type))


@intrinsic
def delete_table(typingctx, table_t=None):
    assert table_t == table_type

    def codegen(context, builder, sig, args):
        bjo__pojp = lir.FunctionType(lir.VoidType(), [lir.IntType(8).
            as_pointer()])
        rvy__hvxn = cgutils.get_or_insert_function(builder.module,
            bjo__pojp, name='delete_table')
        builder.call(rvy__hvxn, args)
    return types.void(table_t), codegen


@intrinsic
def shuffle_table(typingctx, table_t, n_keys_t, _is_parallel, keep_comm_info_t
    ):
    assert table_t == table_type

    def codegen(context, builder, sig, args):
        bjo__pojp = lir.FunctionType(lir.IntType(8).as_pointer(), [lir.
            IntType(8).as_pointer(), lir.IntType(64), lir.IntType(1), lir.
            IntType(32)])
        rvy__hvxn = cgutils.get_or_insert_function(builder.module,
            bjo__pojp, name='shuffle_table')
        eixx__qalp = builder.call(rvy__hvxn, args)
        context.compile_internal(builder, lambda :
            check_and_propagate_cpp_exception(), types.none(), [])
        return eixx__qalp
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
        bjo__pojp = lir.FunctionType(lir.VoidType(), [lir.IntType(8).
            as_pointer()])
        rvy__hvxn = cgutils.get_or_insert_function(builder.module,
            bjo__pojp, name='delete_shuffle_info')
        return builder.call(rvy__hvxn, args)
    return types.void(shuffle_info_t), codegen


@intrinsic
def reverse_shuffle_table(typingctx, table_t, shuffle_info_t=None):

    def codegen(context, builder, sig, args):
        if sig.args[-1] == types.none:
            return context.get_constant_null(table_type)
        bjo__pojp = lir.FunctionType(lir.IntType(8).as_pointer(), [lir.
            IntType(8).as_pointer(), lir.IntType(8).as_pointer()])
        rvy__hvxn = cgutils.get_or_insert_function(builder.module,
            bjo__pojp, name='reverse_shuffle_table')
        return builder.call(rvy__hvxn, args)
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
        bjo__pojp = lir.FunctionType(lir.IntType(8).as_pointer(), [lir.
            IntType(8).as_pointer(), lir.IntType(8).as_pointer(), lir.
            IntType(1), lir.IntType(1), lir.IntType(64), lir.IntType(64),
            lir.IntType(64), lir.IntType(8).as_pointer(), lir.IntType(8).
            as_pointer(), lir.IntType(1), lir.IntType(1), lir.IntType(1),
            lir.IntType(1), lir.IntType(1), lir.IntType(1), lir.IntType(8).
            as_pointer(), lir.IntType(8).as_pointer(), lir.IntType(64), lir
            .IntType(8).as_pointer(), lir.IntType(64)])
        rvy__hvxn = cgutils.get_or_insert_function(builder.module,
            bjo__pojp, name='hash_join_table')
        eixx__qalp = builder.call(rvy__hvxn, args)
        context.compile_internal(builder, lambda :
            check_and_propagate_cpp_exception(), types.none(), [])
        return eixx__qalp
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
        bjo__pojp = lir.FunctionType(lir.IntType(8).as_pointer(), [lir.
            IntType(8).as_pointer(), lir.IntType(64), lir.IntType(8).
            as_pointer(), lir.IntType(8).as_pointer(), lir.IntType(1)])
        rvy__hvxn = cgutils.get_or_insert_function(builder.module,
            bjo__pojp, name='sort_values_table')
        eixx__qalp = builder.call(rvy__hvxn, args)
        context.compile_internal(builder, lambda :
            check_and_propagate_cpp_exception(), types.none(), [])
        return eixx__qalp
    return table_type(table_t, types.int64, types.voidptr, types.voidptr,
        types.boolean), codegen


@intrinsic
def sample_table(typingctx, table_t, n_keys_t, frac_t, replace_t, parallel_t):
    assert table_t == table_type

    def codegen(context, builder, sig, args):
        bjo__pojp = lir.FunctionType(lir.IntType(8).as_pointer(), [lir.
            IntType(8).as_pointer(), lir.IntType(64), lir.DoubleType(), lir
            .IntType(1), lir.IntType(1)])
        rvy__hvxn = cgutils.get_or_insert_function(builder.module,
            bjo__pojp, name='sample_table')
        eixx__qalp = builder.call(rvy__hvxn, args)
        context.compile_internal(builder, lambda :
            check_and_propagate_cpp_exception(), types.none(), [])
        return eixx__qalp
    return table_type(table_t, types.int64, types.float64, types.boolean,
        types.boolean), codegen


@intrinsic
def shuffle_renormalization(typingctx, table_t, random_t, random_seed_t,
    is_parallel_t):
    assert table_t == table_type

    def codegen(context, builder, sig, args):
        bjo__pojp = lir.FunctionType(lir.IntType(8).as_pointer(), [lir.
            IntType(8).as_pointer(), lir.IntType(32), lir.IntType(64), lir.
            IntType(1)])
        rvy__hvxn = cgutils.get_or_insert_function(builder.module,
            bjo__pojp, name='shuffle_renormalization')
        eixx__qalp = builder.call(rvy__hvxn, args)
        context.compile_internal(builder, lambda :
            check_and_propagate_cpp_exception(), types.none(), [])
        return eixx__qalp
    return table_type(table_t, types.int32, types.int64, types.boolean
        ), codegen


@intrinsic
def shuffle_renormalization_group(typingctx, table_t, random_t,
    random_seed_t, is_parallel_t, num_ranks_t, ranks_t):
    assert table_t == table_type

    def codegen(context, builder, sig, args):
        bjo__pojp = lir.FunctionType(lir.IntType(8).as_pointer(), [lir.
            IntType(8).as_pointer(), lir.IntType(32), lir.IntType(64), lir.
            IntType(1), lir.IntType(64), lir.IntType(8).as_pointer()])
        rvy__hvxn = cgutils.get_or_insert_function(builder.module,
            bjo__pojp, name='shuffle_renormalization_group')
        eixx__qalp = builder.call(rvy__hvxn, args)
        context.compile_internal(builder, lambda :
            check_and_propagate_cpp_exception(), types.none(), [])
        return eixx__qalp
    return table_type(table_t, types.int32, types.int64, types.boolean,
        types.int64, types.voidptr), codegen


@intrinsic
def drop_duplicates_table(typingctx, table_t, parallel_t, nkey_t, keep_t,
    dropna, drop_local_first):
    assert table_t == table_type

    def codegen(context, builder, sig, args):
        bjo__pojp = lir.FunctionType(lir.IntType(8).as_pointer(), [lir.
            IntType(8).as_pointer(), lir.IntType(1), lir.IntType(64), lir.
            IntType(64), lir.IntType(1), lir.IntType(1)])
        rvy__hvxn = cgutils.get_or_insert_function(builder.module,
            bjo__pojp, name='drop_duplicates_table')
        eixx__qalp = builder.call(rvy__hvxn, args)
        context.compile_internal(builder, lambda :
            check_and_propagate_cpp_exception(), types.none(), [])
        return eixx__qalp
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
        bjo__pojp = lir.FunctionType(lir.IntType(8).as_pointer(), [lir.
            IntType(8).as_pointer(), lir.IntType(64), lir.IntType(8).
            as_pointer(), lir.IntType(8).as_pointer(), lir.IntType(1), lir.
            IntType(8).as_pointer(), lir.IntType(8).as_pointer(), lir.
            IntType(8).as_pointer(), lir.IntType(1), lir.IntType(1), lir.
            IntType(1), lir.IntType(1), lir.IntType(1), lir.IntType(8).
            as_pointer(), lir.IntType(8).as_pointer(), lir.IntType(8).
            as_pointer(), lir.IntType(8).as_pointer()])
        rvy__hvxn = cgutils.get_or_insert_function(builder.module,
            bjo__pojp, name='pivot_groupby_and_aggregate')
        eixx__qalp = builder.call(rvy__hvxn, args)
        context.compile_internal(builder, lambda :
            check_and_propagate_cpp_exception(), types.none(), [])
        return eixx__qalp
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
        bjo__pojp = lir.FunctionType(lir.IntType(8).as_pointer(), [lir.
            IntType(8).as_pointer(), lir.IntType(64), lir.IntType(1), lir.
            IntType(8).as_pointer(), lir.IntType(8).as_pointer(), lir.
            IntType(8).as_pointer(), lir.IntType(1), lir.IntType(1), lir.
            IntType(64), lir.IntType(64), lir.IntType(64), lir.IntType(1),
            lir.IntType(1), lir.IntType(1), lir.IntType(8).as_pointer(),
            lir.IntType(8).as_pointer(), lir.IntType(8).as_pointer(), lir.
            IntType(8).as_pointer(), lir.IntType(8).as_pointer()])
        rvy__hvxn = cgutils.get_or_insert_function(builder.module,
            bjo__pojp, name='groupby_and_aggregate')
        eixx__qalp = builder.call(rvy__hvxn, args)
        context.compile_internal(builder, lambda :
            check_and_propagate_cpp_exception(), types.none(), [])
        return eixx__qalp
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
    tgc__dssa = array_to_info(in_arr)
    msqkz__haxg = array_to_info(in_values)
    zcdh__hkrmb = array_to_info(out_arr)
    riwt__tnzku = arr_info_list_to_table([tgc__dssa, msqkz__haxg, zcdh__hkrmb])
    _array_isin(zcdh__hkrmb, tgc__dssa, msqkz__haxg, is_parallel)
    check_and_propagate_cpp_exception()
    delete_table(riwt__tnzku)


_get_search_regex = types.ExternalFunction('get_search_regex', types.void(
    array_info_type, types.bool_, types.voidptr, array_info_type))


@numba.njit(no_cpython_wrapper=True)
def get_search_regex(in_arr, case, pat, out_arr):
    in_arr = decode_if_dict_array(in_arr)
    tgc__dssa = array_to_info(in_arr)
    zcdh__hkrmb = array_to_info(out_arr)
    _get_search_regex(tgc__dssa, case, pat, zcdh__hkrmb)
    check_and_propagate_cpp_exception()


def _gen_row_access_intrinsic(col_array_typ, c_ind):
    from llvmlite import ir as lir
    wrgu__spi = col_array_typ.dtype
    if isinstance(wrgu__spi, types.Number) or wrgu__spi in [bodo.
        datetime_date_type, bodo.datetime64ns, bodo.timedelta64ns, types.bool_
        ]:

        @intrinsic
        def getitem_func(typingctx, table_t, ind_t):

            def codegen(context, builder, sig, args):
                rlubc__mbl, dimmn__rbs = args
                rlubc__mbl = builder.bitcast(rlubc__mbl, lir.IntType(8).
                    as_pointer().as_pointer())
                eujb__yleca = lir.Constant(lir.IntType(64), c_ind)
                fiykv__epehd = builder.load(builder.gep(rlubc__mbl, [
                    eujb__yleca]))
                fiykv__epehd = builder.bitcast(fiykv__epehd, context.
                    get_data_type(wrgu__spi).as_pointer())
                return builder.load(builder.gep(fiykv__epehd, [dimmn__rbs]))
            return wrgu__spi(types.voidptr, types.int64), codegen
        return getitem_func
    if col_array_typ == bodo.string_array_type:

        @intrinsic
        def getitem_func(typingctx, table_t, ind_t):

            def codegen(context, builder, sig, args):
                rlubc__mbl, dimmn__rbs = args
                rlubc__mbl = builder.bitcast(rlubc__mbl, lir.IntType(8).
                    as_pointer().as_pointer())
                eujb__yleca = lir.Constant(lir.IntType(64), c_ind)
                fiykv__epehd = builder.load(builder.gep(rlubc__mbl, [
                    eujb__yleca]))
                bjo__pojp = lir.FunctionType(lir.IntType(8).as_pointer(), [
                    lir.IntType(8).as_pointer(), lir.IntType(64), lir.
                    IntType(64).as_pointer()])
                iqnsv__gpkw = cgutils.get_or_insert_function(builder.module,
                    bjo__pojp, name='array_info_getitem')
                byb__aoue = cgutils.alloca_once(builder, lir.IntType(64))
                args = fiykv__epehd, dimmn__rbs, byb__aoue
                dtwz__cglej = builder.call(iqnsv__gpkw, args)
                return context.make_tuple(builder, sig.return_type, [
                    dtwz__cglej, builder.load(byb__aoue)])
            return types.Tuple([types.voidptr, types.int64])(types.voidptr,
                types.int64), codegen
        return getitem_func
    if col_array_typ == bodo.libs.dict_arr_ext.dict_str_arr_type:

        @intrinsic
        def getitem_func(typingctx, table_t, ind_t):

            def codegen(context, builder, sig, args):
                alt__fuvn = lir.Constant(lir.IntType(64), 1)
                efif__aute = lir.Constant(lir.IntType(64), 2)
                rlubc__mbl, dimmn__rbs = args
                rlubc__mbl = builder.bitcast(rlubc__mbl, lir.IntType(8).
                    as_pointer().as_pointer())
                eujb__yleca = lir.Constant(lir.IntType(64), c_ind)
                fiykv__epehd = builder.load(builder.gep(rlubc__mbl, [
                    eujb__yleca]))
                bjo__pojp = lir.FunctionType(lir.IntType(8).as_pointer(), [
                    lir.IntType(8).as_pointer(), lir.IntType(64)])
                bfrvm__yaru = cgutils.get_or_insert_function(builder.module,
                    bjo__pojp, name='get_nested_info')
                args = fiykv__epehd, efif__aute
                zsg__iuamm = builder.call(bfrvm__yaru, args)
                bjo__pojp = lir.FunctionType(lir.IntType(8).as_pointer(), [
                    lir.IntType(8).as_pointer()])
                ijh__hqept = cgutils.get_or_insert_function(builder.module,
                    bjo__pojp, name='array_info_getdata1')
                args = zsg__iuamm,
                aemy__gqm = builder.call(ijh__hqept, args)
                aemy__gqm = builder.bitcast(aemy__gqm, context.
                    get_data_type(col_array_typ.indices_dtype).as_pointer())
                njlt__qndzz = builder.sext(builder.load(builder.gep(
                    aemy__gqm, [dimmn__rbs])), lir.IntType(64))
                args = fiykv__epehd, alt__fuvn
                rfwkx__zlb = builder.call(bfrvm__yaru, args)
                bjo__pojp = lir.FunctionType(lir.IntType(8).as_pointer(), [
                    lir.IntType(8).as_pointer(), lir.IntType(64), lir.
                    IntType(64).as_pointer()])
                iqnsv__gpkw = cgutils.get_or_insert_function(builder.module,
                    bjo__pojp, name='array_info_getitem')
                byb__aoue = cgutils.alloca_once(builder, lir.IntType(64))
                args = rfwkx__zlb, njlt__qndzz, byb__aoue
                dtwz__cglej = builder.call(iqnsv__gpkw, args)
                return context.make_tuple(builder, sig.return_type, [
                    dtwz__cglej, builder.load(byb__aoue)])
            return types.Tuple([types.voidptr, types.int64])(types.voidptr,
                types.int64), codegen
        return getitem_func
    raise BodoError(
        f"General Join Conditions with '{wrgu__spi}' column data type not supported"
        )


def _gen_row_na_check_intrinsic(col_array_dtype, c_ind):
    if (isinstance(col_array_dtype, bodo.libs.int_arr_ext.IntegerArrayType) or
        col_array_dtype == bodo.libs.bool_arr_ext.boolean_array or
        is_str_arr_type(col_array_dtype) or isinstance(col_array_dtype,
        types.Array) and col_array_dtype.dtype == bodo.datetime_date_type):

        @intrinsic
        def checkna_func(typingctx, table_t, ind_t):

            def codegen(context, builder, sig, args):
                icm__pwfjz, dimmn__rbs = args
                icm__pwfjz = builder.bitcast(icm__pwfjz, lir.IntType(8).
                    as_pointer().as_pointer())
                eujb__yleca = lir.Constant(lir.IntType(64), c_ind)
                fiykv__epehd = builder.load(builder.gep(icm__pwfjz, [
                    eujb__yleca]))
                aegy__xbt = builder.bitcast(fiykv__epehd, context.
                    get_data_type(types.bool_).as_pointer())
                kgabz__ozu = bodo.utils.cg_helpers.get_bitmap_bit(builder,
                    aegy__xbt, dimmn__rbs)
                mdr__izpvd = builder.icmp_unsigned('!=', kgabz__ozu, lir.
                    Constant(lir.IntType(8), 0))
                return builder.sext(mdr__izpvd, lir.IntType(8))
            return types.int8(types.voidptr, types.int64), codegen
        return checkna_func
    elif isinstance(col_array_dtype, types.Array):
        wrgu__spi = col_array_dtype.dtype
        if wrgu__spi in [bodo.datetime64ns, bodo.timedelta64ns]:

            @intrinsic
            def checkna_func(typingctx, table_t, ind_t):

                def codegen(context, builder, sig, args):
                    rlubc__mbl, dimmn__rbs = args
                    rlubc__mbl = builder.bitcast(rlubc__mbl, lir.IntType(8)
                        .as_pointer().as_pointer())
                    eujb__yleca = lir.Constant(lir.IntType(64), c_ind)
                    fiykv__epehd = builder.load(builder.gep(rlubc__mbl, [
                        eujb__yleca]))
                    fiykv__epehd = builder.bitcast(fiykv__epehd, context.
                        get_data_type(wrgu__spi).as_pointer())
                    uuhd__opd = builder.load(builder.gep(fiykv__epehd, [
                        dimmn__rbs]))
                    mdr__izpvd = builder.icmp_unsigned('!=', uuhd__opd, lir
                        .Constant(lir.IntType(64), pd._libs.iNaT))
                    return builder.sext(mdr__izpvd, lir.IntType(8))
                return types.int8(types.voidptr, types.int64), codegen
            return checkna_func
        elif isinstance(wrgu__spi, types.Float):

            @intrinsic
            def checkna_func(typingctx, table_t, ind_t):

                def codegen(context, builder, sig, args):
                    rlubc__mbl, dimmn__rbs = args
                    rlubc__mbl = builder.bitcast(rlubc__mbl, lir.IntType(8)
                        .as_pointer().as_pointer())
                    eujb__yleca = lir.Constant(lir.IntType(64), c_ind)
                    fiykv__epehd = builder.load(builder.gep(rlubc__mbl, [
                        eujb__yleca]))
                    fiykv__epehd = builder.bitcast(fiykv__epehd, context.
                        get_data_type(wrgu__spi).as_pointer())
                    uuhd__opd = builder.load(builder.gep(fiykv__epehd, [
                        dimmn__rbs]))
                    tob__vpw = signature(types.bool_, wrgu__spi)
                    kgabz__ozu = numba.np.npyfuncs.np_real_isnan_impl(context,
                        builder, tob__vpw, (uuhd__opd,))
                    return builder.not_(builder.sext(kgabz__ozu, lir.
                        IntType(8)))
                return types.int8(types.voidptr, types.int64), codegen
            return checkna_func
    raise BodoError(
        f"General Join Conditions with '{col_array_dtype}' column type not supported"
        )
