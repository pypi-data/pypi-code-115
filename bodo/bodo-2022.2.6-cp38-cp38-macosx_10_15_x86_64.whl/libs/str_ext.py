import operator
import re
import llvmlite.binding as ll
import numba
import numpy as np
from llvmlite import ir as lir
from numba.core import cgutils, types
from numba.core.typing.templates import AbstractTemplate, AttributeTemplate, bound_function, infer_getattr, infer_global, signature
from numba.extending import intrinsic, lower_cast, make_attribute_wrapper, models, overload, overload_attribute, register_jitable, register_model
from numba.parfors.array_analysis import ArrayAnalysis
import bodo
from bodo.libs import hstr_ext
from bodo.utils.typing import BodoError, get_overload_const_int, get_overload_const_str, is_overload_constant_int, is_overload_constant_str


def unliteral_all(args):
    return tuple(types.unliteral(a) for a in args)


ll.add_symbol('del_str', hstr_ext.del_str)
ll.add_symbol('unicode_to_utf8', hstr_ext.unicode_to_utf8)
ll.add_symbol('memcmp', hstr_ext.memcmp)
ll.add_symbol('int_to_hex', hstr_ext.int_to_hex)
string_type = types.unicode_type


@numba.njit
def contains_regex(e, in_str):
    with numba.objmode(res='bool_'):
        res = bool(e.search(in_str))
    return res


@numba.generated_jit
def str_findall_count(regex, in_str):

    def _str_findall_count_impl(regex, in_str):
        with numba.objmode(res='int64'):
            res = len(regex.findall(in_str))
        return res
    return _str_findall_count_impl


utf8_str_type = types.ArrayCTypes(types.Array(types.uint8, 1, 'C'))


@intrinsic
def unicode_to_utf8_and_len(typingctx, str_typ=None):
    assert str_typ in (string_type, types.Optional(string_type)) or isinstance(
        str_typ, types.StringLiteral)
    oxee__sodwg = types.Tuple([utf8_str_type, types.int64])

    def codegen(context, builder, sig, args):
        acpg__nve, = args
        mmich__wsxna = cgutils.create_struct_proxy(string_type)(context,
            builder, value=acpg__nve)
        iqdx__bjggj = cgutils.create_struct_proxy(utf8_str_type)(context,
            builder)
        brlte__lzys = cgutils.create_struct_proxy(oxee__sodwg)(context, builder
            )
        is_ascii = builder.icmp_unsigned('==', mmich__wsxna.is_ascii, lir.
            Constant(mmich__wsxna.is_ascii.type, 1))
        with builder.if_else(is_ascii) as (zwza__ylgm, myr__ajtz):
            with zwza__ylgm:
                context.nrt.incref(builder, string_type, acpg__nve)
                iqdx__bjggj.data = mmich__wsxna.data
                iqdx__bjggj.meminfo = mmich__wsxna.meminfo
                brlte__lzys.f1 = mmich__wsxna.length
            with myr__ajtz:
                pzef__cljs = lir.FunctionType(lir.IntType(64), [lir.IntType
                    (8).as_pointer(), lir.IntType(8).as_pointer(), lir.
                    IntType(64), lir.IntType(32)])
                rpai__lpv = cgutils.get_or_insert_function(builder.module,
                    pzef__cljs, name='unicode_to_utf8')
                xofw__eakur = context.get_constant_null(types.voidptr)
                mufd__mpbl = builder.call(rpai__lpv, [xofw__eakur,
                    mmich__wsxna.data, mmich__wsxna.length, mmich__wsxna.kind])
                brlte__lzys.f1 = mufd__mpbl
                lrv__pil = builder.add(mufd__mpbl, lir.Constant(lir.IntType
                    (64), 1))
                iqdx__bjggj.meminfo = context.nrt.meminfo_alloc_aligned(builder
                    , size=lrv__pil, align=32)
                iqdx__bjggj.data = context.nrt.meminfo_data(builder,
                    iqdx__bjggj.meminfo)
                builder.call(rpai__lpv, [iqdx__bjggj.data, mmich__wsxna.
                    data, mmich__wsxna.length, mmich__wsxna.kind])
                builder.store(lir.Constant(lir.IntType(8), 0), builder.gep(
                    iqdx__bjggj.data, [mufd__mpbl]))
        brlte__lzys.f0 = iqdx__bjggj._getvalue()
        return brlte__lzys._getvalue()
    return oxee__sodwg(string_type), codegen


def unicode_to_utf8(s):
    return s


@overload(unicode_to_utf8)
def overload_unicode_to_utf8(s):
    return lambda s: unicode_to_utf8_and_len(s)[0]


@overload(max)
def overload_builtin_max(lhs, rhs):
    if lhs == types.unicode_type and rhs == types.unicode_type:

        def impl(lhs, rhs):
            return lhs if lhs > rhs else rhs
        return impl


@overload(min)
def overload_builtin_min(lhs, rhs):
    if lhs == types.unicode_type and rhs == types.unicode_type:

        def impl(lhs, rhs):
            return lhs if lhs < rhs else rhs
        return impl


@intrinsic
def memcmp(typingctx, dest_t, src_t, count_t=None):

    def codegen(context, builder, sig, args):
        pzef__cljs = lir.FunctionType(lir.IntType(32), [lir.IntType(8).
            as_pointer(), lir.IntType(8).as_pointer(), lir.IntType(64)])
        bkkyo__dwhba = cgutils.get_or_insert_function(builder.module,
            pzef__cljs, name='memcmp')
        return builder.call(bkkyo__dwhba, args)
    return types.int32(types.voidptr, types.voidptr, types.intp), codegen


def int_to_str_len(n):
    return len(str(n))


@overload(int_to_str_len)
def overload_int_to_str_len(n):
    rbmt__kojdf = n(10)

    def impl(n):
        if n == 0:
            return 1
        maldh__yurc = 0
        if n < 0:
            n = -n
            maldh__yurc += 1
        while n > 0:
            n = n // rbmt__kojdf
            maldh__yurc += 1
        return maldh__yurc
    return impl


class StdStringType(types.Opaque):

    def __init__(self):
        super(StdStringType, self).__init__(name='StdStringType')


std_str_type = StdStringType()
register_model(StdStringType)(models.OpaqueModel)
del_str = types.ExternalFunction('del_str', types.void(std_str_type))
get_c_str = types.ExternalFunction('get_c_str', types.voidptr(std_str_type))
dummy_use = numba.njit(lambda a: None)


@overload(int)
def int_str_overload(in_str, base=10):
    if in_str == string_type:
        if is_overload_constant_int(base) and get_overload_const_int(base
            ) == 10:

            def _str_to_int_impl(in_str, base=10):
                val = _str_to_int64(in_str._data, in_str._length)
                dummy_use(in_str)
                return val
            return _str_to_int_impl

        def _str_to_int_base_impl(in_str, base=10):
            val = _str_to_int64_base(in_str._data, in_str._length, base)
            dummy_use(in_str)
            return val
        return _str_to_int_base_impl


@infer_global(float)
class StrToFloat(AbstractTemplate):

    def generic(self, args, kws):
        assert not kws
        [ygrv__vaqfs] = args
        if isinstance(ygrv__vaqfs, StdStringType):
            return signature(types.float64, ygrv__vaqfs)
        if ygrv__vaqfs == string_type:
            return signature(types.float64, ygrv__vaqfs)


ll.add_symbol('init_string_const', hstr_ext.init_string_const)
ll.add_symbol('get_c_str', hstr_ext.get_c_str)
ll.add_symbol('str_to_int64', hstr_ext.str_to_int64)
ll.add_symbol('str_to_uint64', hstr_ext.str_to_uint64)
ll.add_symbol('str_to_int64_base', hstr_ext.str_to_int64_base)
ll.add_symbol('str_to_float64', hstr_ext.str_to_float64)
ll.add_symbol('str_to_float32', hstr_ext.str_to_float32)
ll.add_symbol('get_str_len', hstr_ext.get_str_len)
ll.add_symbol('str_from_float32', hstr_ext.str_from_float32)
ll.add_symbol('str_from_float64', hstr_ext.str_from_float64)
get_std_str_len = types.ExternalFunction('get_str_len', signature(types.
    intp, std_str_type))
init_string_from_chars = types.ExternalFunction('init_string_const',
    std_str_type(types.voidptr, types.intp))
_str_to_int64 = types.ExternalFunction('str_to_int64', signature(types.
    int64, types.voidptr, types.int64))
_str_to_uint64 = types.ExternalFunction('str_to_uint64', signature(types.
    uint64, types.voidptr, types.int64))
_str_to_int64_base = types.ExternalFunction('str_to_int64_base', signature(
    types.int64, types.voidptr, types.int64, types.int64))


def gen_unicode_to_std_str(context, builder, unicode_val):
    mmich__wsxna = cgutils.create_struct_proxy(string_type)(context,
        builder, value=unicode_val)
    pzef__cljs = lir.FunctionType(lir.IntType(8).as_pointer(), [lir.IntType
        (8).as_pointer(), lir.IntType(64)])
    okt__bxib = cgutils.get_or_insert_function(builder.module, pzef__cljs,
        name='init_string_const')
    return builder.call(okt__bxib, [mmich__wsxna.data, mmich__wsxna.length])


def gen_std_str_to_unicode(context, builder, std_str_val, del_str=False):
    kind = numba.cpython.unicode.PY_UNICODE_1BYTE_KIND

    def _std_str_to_unicode(std_str):
        length = bodo.libs.str_ext.get_std_str_len(std_str)
        qtkq__uwd = numba.cpython.unicode._empty_string(kind, length, 1)
        bodo.libs.str_arr_ext._memcpy(qtkq__uwd._data, bodo.libs.str_ext.
            get_c_str(std_str), length, 1)
        if del_str:
            bodo.libs.str_ext.del_str(std_str)
        return qtkq__uwd
    val = context.compile_internal(builder, _std_str_to_unicode,
        string_type(bodo.libs.str_ext.std_str_type), [std_str_val])
    return val


def gen_get_unicode_chars(context, builder, unicode_val):
    mmich__wsxna = cgutils.create_struct_proxy(string_type)(context,
        builder, value=unicode_val)
    return mmich__wsxna.data


@intrinsic
def unicode_to_std_str(typingctx, unicode_t=None):

    def codegen(context, builder, sig, args):
        return gen_unicode_to_std_str(context, builder, args[0])
    return std_str_type(string_type), codegen


@intrinsic
def std_str_to_unicode(typingctx, unicode_t=None):

    def codegen(context, builder, sig, args):
        return gen_std_str_to_unicode(context, builder, args[0], True)
    return string_type(std_str_type), codegen


class RandomAccessStringArrayType(types.ArrayCompatible):

    def __init__(self):
        super(RandomAccessStringArrayType, self).__init__(name=
            'RandomAccessStringArrayType()')

    @property
    def as_array(self):
        return types.Array(types.undefined, 1, 'C')

    @property
    def dtype(self):
        return string_type

    def copy(self):
        RandomAccessStringArrayType()


random_access_string_array = RandomAccessStringArrayType()


@register_model(RandomAccessStringArrayType)
class RandomAccessStringArrayModel(models.StructModel):

    def __init__(self, dmm, fe_type):
        ruho__wic = [('data', types.List(string_type))]
        models.StructModel.__init__(self, dmm, fe_type, ruho__wic)


make_attribute_wrapper(RandomAccessStringArrayType, 'data', '_data')


@intrinsic
def alloc_random_access_string_array(typingctx, n_t=None):

    def codegen(context, builder, sig, args):
        fakeo__icmzz, = args
        tssm__nya = types.List(string_type)
        bmes__wujj = numba.cpython.listobj.ListInstance.allocate(context,
            builder, tssm__nya, fakeo__icmzz)
        bmes__wujj.size = fakeo__icmzz
        yqyuv__levxk = cgutils.create_struct_proxy(sig.return_type)(context,
            builder)
        yqyuv__levxk.data = bmes__wujj.value
        return yqyuv__levxk._getvalue()
    return random_access_string_array(types.intp), codegen


@overload(operator.getitem, no_unliteral=True)
def random_access_str_arr_getitem(A, ind):
    if A != random_access_string_array:
        return
    if isinstance(ind, types.Integer):
        return lambda A, ind: A._data[ind]


@overload(operator.setitem)
def random_access_str_arr_setitem(A, idx, val):
    if A != random_access_string_array:
        return
    if isinstance(idx, types.Integer):
        assert val == string_type

        def impl_scalar(A, idx, val):
            A._data[idx] = val
        return impl_scalar


@overload(len, no_unliteral=True)
def overload_str_arr_len(A):
    if A == random_access_string_array:
        return lambda A: len(A._data)


@overload_attribute(RandomAccessStringArrayType, 'shape')
def overload_str_arr_shape(A):
    return lambda A: (len(A._data),)


def alloc_random_access_str_arr_equiv(self, scope, equiv_set, loc, args, kws):
    assert len(args) == 1 and not kws
    return ArrayAnalysis.AnalyzeResult(shape=args[0], pre=[])


(ArrayAnalysis.
    _analyze_op_call_bodo_libs_str_ext_alloc_random_access_string_array
    ) = alloc_random_access_str_arr_equiv
str_from_float32 = types.ExternalFunction('str_from_float32', types.void(
    types.voidptr, types.float32))
str_from_float64 = types.ExternalFunction('str_from_float64', types.void(
    types.voidptr, types.float64))


def float_to_str(s, v):
    pass


@overload(float_to_str)
def float_to_str_overload(s, v):
    assert isinstance(v, types.Float)
    if v == types.float32:
        return lambda s, v: str_from_float32(s._data, v)
    return lambda s, v: str_from_float64(s._data, v)


@overload(str)
def float_str_overload(v):
    if isinstance(v, types.Float):
        kind = numba.cpython.unicode.PY_UNICODE_1BYTE_KIND

        def impl(v):
            if v == 0:
                return '0.0'
            lneu__jmlgn = 0
            udwtq__novu = v
            if udwtq__novu < 0:
                lneu__jmlgn = 1
                udwtq__novu = -udwtq__novu
            if udwtq__novu < 1:
                axla__zmyub = 1
            else:
                axla__zmyub = 1 + int(np.floor(np.log10(udwtq__novu)))
            length = lneu__jmlgn + axla__zmyub + 1 + 6
            s = numba.cpython.unicode._malloc_string(kind, 1, length, True)
            float_to_str(s, v)
            return s
        return impl


@overload(format, no_unliteral=True)
def overload_format(value, format_spec=''):
    if is_overload_constant_str(format_spec) and get_overload_const_str(
        format_spec) == '':

        def impl_fast(value, format_spec=''):
            return str(value)
        return impl_fast

    def impl(value, format_spec=''):
        with numba.objmode(res='string'):
            res = format(value, format_spec)
        return res
    return impl


@lower_cast(StdStringType, types.float64)
def cast_str_to_float64(context, builder, fromty, toty, val):
    pzef__cljs = lir.FunctionType(lir.DoubleType(), [lir.IntType(8).
        as_pointer()])
    okt__bxib = cgutils.get_or_insert_function(builder.module, pzef__cljs,
        name='str_to_float64')
    res = builder.call(okt__bxib, (val,))
    bodo.utils.utils.inlined_check_and_propagate_cpp_exception(context, builder
        )
    return res


@lower_cast(StdStringType, types.float32)
def cast_str_to_float32(context, builder, fromty, toty, val):
    pzef__cljs = lir.FunctionType(lir.FloatType(), [lir.IntType(8).
        as_pointer()])
    okt__bxib = cgutils.get_or_insert_function(builder.module, pzef__cljs,
        name='str_to_float32')
    res = builder.call(okt__bxib, (val,))
    bodo.utils.utils.inlined_check_and_propagate_cpp_exception(context, builder
        )
    return res


@lower_cast(string_type, types.float64)
def cast_unicode_str_to_float64(context, builder, fromty, toty, val):
    std_str = gen_unicode_to_std_str(context, builder, val)
    return cast_str_to_float64(context, builder, std_str_type, toty, std_str)


@lower_cast(string_type, types.float32)
def cast_unicode_str_to_float32(context, builder, fromty, toty, val):
    std_str = gen_unicode_to_std_str(context, builder, val)
    return cast_str_to_float32(context, builder, std_str_type, toty, std_str)


@lower_cast(string_type, types.int64)
@lower_cast(string_type, types.int32)
@lower_cast(string_type, types.int16)
@lower_cast(string_type, types.int8)
def cast_unicode_str_to_int64(context, builder, fromty, toty, val):
    mmich__wsxna = cgutils.create_struct_proxy(string_type)(context,
        builder, value=val)
    pzef__cljs = lir.FunctionType(lir.IntType(toty.bitwidth), [lir.IntType(
        8).as_pointer(), lir.IntType(64)])
    okt__bxib = cgutils.get_or_insert_function(builder.module, pzef__cljs,
        name='str_to_int64')
    res = builder.call(okt__bxib, (mmich__wsxna.data, mmich__wsxna.length))
    bodo.utils.utils.inlined_check_and_propagate_cpp_exception(context, builder
        )
    return res


@lower_cast(string_type, types.uint64)
@lower_cast(string_type, types.uint32)
@lower_cast(string_type, types.uint16)
@lower_cast(string_type, types.uint8)
def cast_unicode_str_to_uint64(context, builder, fromty, toty, val):
    mmich__wsxna = cgutils.create_struct_proxy(string_type)(context,
        builder, value=val)
    pzef__cljs = lir.FunctionType(lir.IntType(toty.bitwidth), [lir.IntType(
        8).as_pointer(), lir.IntType(64)])
    okt__bxib = cgutils.get_or_insert_function(builder.module, pzef__cljs,
        name='str_to_uint64')
    res = builder.call(okt__bxib, (mmich__wsxna.data, mmich__wsxna.length))
    bodo.utils.utils.inlined_check_and_propagate_cpp_exception(context, builder
        )
    return res


@infer_getattr
class StringAttribute(AttributeTemplate):
    key = types.UnicodeType

    @bound_function('str.format', no_unliteral=True)
    def resolve_format(self, string_typ, args, kws):
        kws = dict(kws)
        lxqii__uhx = ', '.join('e{}'.format(wdhqd__mwlt) for wdhqd__mwlt in
            range(len(args)))
        if lxqii__uhx:
            lxqii__uhx += ', '
        mlu__izc = ', '.join("{} = ''".format(a) for a in kws.keys())
        rbv__ncyj = f'def format_stub(string, {lxqii__uhx} {mlu__izc}):\n'
        rbv__ncyj += '    pass\n'
        awmz__foi = {}
        exec(rbv__ncyj, {}, awmz__foi)
        qab__duz = awmz__foi['format_stub']
        tyc__azk = numba.core.utils.pysignature(qab__duz)
        gzy__swb = (string_typ,) + args + tuple(kws.values())
        return signature(string_typ, gzy__swb).replace(pysig=tyc__azk)


@numba.njit(cache=True)
def str_split(arr, pat, n):
    yejfo__mjsg = pat is not None and len(pat) > 1
    if yejfo__mjsg:
        zqpof__yrvf = re.compile(pat)
        if n == -1:
            n = 0
    elif n == 0:
        n = -1
    bmes__wujj = len(arr)
    fare__fvrv = 0
    sljm__dmz = 0
    for wdhqd__mwlt in numba.parfors.parfor.internal_prange(bmes__wujj):
        if bodo.libs.array_kernels.isna(arr, wdhqd__mwlt):
            continue
        if yejfo__mjsg:
            rfql__pgke = zqpof__yrvf.split(arr[wdhqd__mwlt], maxsplit=n)
        elif pat == '':
            rfql__pgke = [''] + list(arr[wdhqd__mwlt]) + ['']
        else:
            rfql__pgke = arr[wdhqd__mwlt].split(pat, n)
        fare__fvrv += len(rfql__pgke)
        for s in rfql__pgke:
            sljm__dmz += bodo.libs.str_arr_ext.get_utf8_size(s)
    sfw__zwvas = bodo.libs.array_item_arr_ext.pre_alloc_array_item_array(
        bmes__wujj, (fare__fvrv, sljm__dmz), bodo.libs.str_arr_ext.
        string_array_type)
    omf__jggb = bodo.libs.array_item_arr_ext.get_offsets(sfw__zwvas)
    ejvr__yclv = bodo.libs.array_item_arr_ext.get_null_bitmap(sfw__zwvas)
    bnpqm__jfkf = bodo.libs.array_item_arr_ext.get_data(sfw__zwvas)
    spqoh__xenz = 0
    for izi__qyuio in numba.parfors.parfor.internal_prange(bmes__wujj):
        omf__jggb[izi__qyuio] = spqoh__xenz
        if bodo.libs.array_kernels.isna(arr, izi__qyuio):
            bodo.libs.int_arr_ext.set_bit_to_arr(ejvr__yclv, izi__qyuio, 0)
            continue
        bodo.libs.int_arr_ext.set_bit_to_arr(ejvr__yclv, izi__qyuio, 1)
        if yejfo__mjsg:
            rfql__pgke = zqpof__yrvf.split(arr[izi__qyuio], maxsplit=n)
        elif pat == '':
            rfql__pgke = [''] + list(arr[izi__qyuio]) + ['']
        else:
            rfql__pgke = arr[izi__qyuio].split(pat, n)
        kcymd__pokdj = len(rfql__pgke)
        for uao__budm in range(kcymd__pokdj):
            s = rfql__pgke[uao__budm]
            bnpqm__jfkf[spqoh__xenz] = s
            spqoh__xenz += 1
    omf__jggb[bmes__wujj] = spqoh__xenz
    return sfw__zwvas


@overload(hex)
def overload_hex(x):
    if isinstance(x, types.Integer):
        kind = numba.cpython.unicode.PY_UNICODE_1BYTE_KIND

        def impl(x):
            x = np.int64(x)
            if x < 0:
                kndz__bai = '-0x'
                x = x * -1
            else:
                kndz__bai = '0x'
            x = np.uint64(x)
            if x == 0:
                uiqmq__khwpm = 1
            else:
                uiqmq__khwpm = fast_ceil_log2(x + 1)
                uiqmq__khwpm = (uiqmq__khwpm + 3) // 4
            length = len(kndz__bai) + uiqmq__khwpm
            output = numba.cpython.unicode._empty_string(kind, length, 1)
            bodo.libs.str_arr_ext._memcpy(output._data, kndz__bai._data,
                len(kndz__bai), 1)
            int_to_hex(output, uiqmq__khwpm, len(kndz__bai), x)
            return output
        return impl


@register_jitable
def fast_ceil_log2(x):
    bxm__gbjrk = 0 if x & x - 1 == 0 else 1
    avkz__jeyq = [np.uint64(18446744069414584320), np.uint64(4294901760),
        np.uint64(65280), np.uint64(240), np.uint64(12), np.uint64(2)]
    huvk__dwfiw = 32
    for wdhqd__mwlt in range(len(avkz__jeyq)):
        axogv__gkt = 0 if x & avkz__jeyq[wdhqd__mwlt] == 0 else huvk__dwfiw
        bxm__gbjrk = bxm__gbjrk + axogv__gkt
        x = x >> axogv__gkt
        huvk__dwfiw = huvk__dwfiw >> 1
    return bxm__gbjrk


@intrinsic
def int_to_hex(typingctx, output, out_len, header_len, int_val):

    def codegen(context, builder, sig, args):
        output, out_len, header_len, int_val = args
        qbbvo__mld = cgutils.create_struct_proxy(sig.args[0])(context,
            builder, value=output)
        pzef__cljs = lir.FunctionType(lir.IntType(8).as_pointer(), [lir.
            IntType(8).as_pointer(), lir.IntType(64), lir.IntType(64)])
        fmd__nmeey = cgutils.get_or_insert_function(builder.module,
            pzef__cljs, name='int_to_hex')
        pxgz__sahu = builder.inttoptr(builder.add(builder.ptrtoint(
            qbbvo__mld.data, lir.IntType(64)), header_len), lir.IntType(8).
            as_pointer())
        builder.call(fmd__nmeey, (pxgz__sahu, out_len, int_val))
    return types.void(output, out_len, header_len, int_val), codegen


def alloc_empty_bytes_or_string_data(typ, kind, length, is_ascii=0):
    pass


@overload(alloc_empty_bytes_or_string_data)
def overload_alloc_empty_bytes_or_string_data(typ, kind, length, is_ascii=0):
    typ = typ.instance_type if isinstance(typ, types.TypeRef) else typ
    if typ == bodo.bytes_type:
        return lambda typ, kind, length, is_ascii=0: np.empty(length, np.uint8)
    if typ == string_type:
        return (lambda typ, kind, length, is_ascii=0: numba.cpython.unicode
            ._empty_string(kind, length, is_ascii))
    raise BodoError(
        f'Internal Error: Expected Bytes or String type, found {typ}')


def get_unicode_or_numpy_data(val):
    pass


@overload(get_unicode_or_numpy_data)
def overload_get_unicode_or_numpy_data(val):
    if val == string_type:
        return lambda val: val._data
    if isinstance(val, types.Array):
        return lambda val: val.ctypes
    raise BodoError(
        f'Internal Error: Expected String or Numpy Array, found {val}')
