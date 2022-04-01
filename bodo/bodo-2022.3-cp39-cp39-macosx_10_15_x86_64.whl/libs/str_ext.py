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
    mpd__ish = types.Tuple([utf8_str_type, types.int64])

    def codegen(context, builder, sig, args):
        ajj__txi, = args
        cpx__amd = cgutils.create_struct_proxy(string_type)(context,
            builder, value=ajj__txi)
        pjobg__zpfvd = cgutils.create_struct_proxy(utf8_str_type)(context,
            builder)
        cpxf__nwht = cgutils.create_struct_proxy(mpd__ish)(context, builder)
        is_ascii = builder.icmp_unsigned('==', cpx__amd.is_ascii, lir.
            Constant(cpx__amd.is_ascii.type, 1))
        with builder.if_else(is_ascii) as (gvm__bhvu, hpux__sptpk):
            with gvm__bhvu:
                context.nrt.incref(builder, string_type, ajj__txi)
                pjobg__zpfvd.data = cpx__amd.data
                pjobg__zpfvd.meminfo = cpx__amd.meminfo
                cpxf__nwht.f1 = cpx__amd.length
            with hpux__sptpk:
                ojek__sgss = lir.FunctionType(lir.IntType(64), [lir.IntType
                    (8).as_pointer(), lir.IntType(8).as_pointer(), lir.
                    IntType(64), lir.IntType(32)])
                tuzg__cyzn = cgutils.get_or_insert_function(builder.module,
                    ojek__sgss, name='unicode_to_utf8')
                wdce__cdmiz = context.get_constant_null(types.voidptr)
                fcuy__hjsz = builder.call(tuzg__cyzn, [wdce__cdmiz,
                    cpx__amd.data, cpx__amd.length, cpx__amd.kind])
                cpxf__nwht.f1 = fcuy__hjsz
                dxzcy__qthb = builder.add(fcuy__hjsz, lir.Constant(lir.
                    IntType(64), 1))
                pjobg__zpfvd.meminfo = context.nrt.meminfo_alloc_aligned(
                    builder, size=dxzcy__qthb, align=32)
                pjobg__zpfvd.data = context.nrt.meminfo_data(builder,
                    pjobg__zpfvd.meminfo)
                builder.call(tuzg__cyzn, [pjobg__zpfvd.data, cpx__amd.data,
                    cpx__amd.length, cpx__amd.kind])
                builder.store(lir.Constant(lir.IntType(8), 0), builder.gep(
                    pjobg__zpfvd.data, [fcuy__hjsz]))
        cpxf__nwht.f0 = pjobg__zpfvd._getvalue()
        return cpxf__nwht._getvalue()
    return mpd__ish(string_type), codegen


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
        ojek__sgss = lir.FunctionType(lir.IntType(32), [lir.IntType(8).
            as_pointer(), lir.IntType(8).as_pointer(), lir.IntType(64)])
        jsf__thnve = cgutils.get_or_insert_function(builder.module,
            ojek__sgss, name='memcmp')
        return builder.call(jsf__thnve, args)
    return types.int32(types.voidptr, types.voidptr, types.intp), codegen


def int_to_str_len(n):
    return len(str(n))


@overload(int_to_str_len)
def overload_int_to_str_len(n):
    rkvl__gawz = n(10)

    def impl(n):
        if n == 0:
            return 1
        pci__mrfm = 0
        if n < 0:
            n = -n
            pci__mrfm += 1
        while n > 0:
            n = n // rkvl__gawz
            pci__mrfm += 1
        return pci__mrfm
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
        [bmwc__nap] = args
        if isinstance(bmwc__nap, StdStringType):
            return signature(types.float64, bmwc__nap)
        if bmwc__nap == string_type:
            return signature(types.float64, bmwc__nap)


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
    cpx__amd = cgutils.create_struct_proxy(string_type)(context, builder,
        value=unicode_val)
    ojek__sgss = lir.FunctionType(lir.IntType(8).as_pointer(), [lir.IntType
        (8).as_pointer(), lir.IntType(64)])
    lks__qgy = cgutils.get_or_insert_function(builder.module, ojek__sgss,
        name='init_string_const')
    return builder.call(lks__qgy, [cpx__amd.data, cpx__amd.length])


def gen_std_str_to_unicode(context, builder, std_str_val, del_str=False):
    kind = numba.cpython.unicode.PY_UNICODE_1BYTE_KIND

    def _std_str_to_unicode(std_str):
        length = bodo.libs.str_ext.get_std_str_len(std_str)
        hci__cst = numba.cpython.unicode._empty_string(kind, length, 1)
        bodo.libs.str_arr_ext._memcpy(hci__cst._data, bodo.libs.str_ext.
            get_c_str(std_str), length, 1)
        if del_str:
            bodo.libs.str_ext.del_str(std_str)
        return hci__cst
    val = context.compile_internal(builder, _std_str_to_unicode,
        string_type(bodo.libs.str_ext.std_str_type), [std_str_val])
    return val


def gen_get_unicode_chars(context, builder, unicode_val):
    cpx__amd = cgutils.create_struct_proxy(string_type)(context, builder,
        value=unicode_val)
    return cpx__amd.data


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
        yjbz__ouen = [('data', types.List(string_type))]
        models.StructModel.__init__(self, dmm, fe_type, yjbz__ouen)


make_attribute_wrapper(RandomAccessStringArrayType, 'data', '_data')


@intrinsic
def alloc_random_access_string_array(typingctx, n_t=None):

    def codegen(context, builder, sig, args):
        gyki__vqwa, = args
        eyy__hhqn = types.List(string_type)
        mfq__fkuxc = numba.cpython.listobj.ListInstance.allocate(context,
            builder, eyy__hhqn, gyki__vqwa)
        mfq__fkuxc.size = gyki__vqwa
        puia__qmb = cgutils.create_struct_proxy(sig.return_type)(context,
            builder)
        puia__qmb.data = mfq__fkuxc.value
        return puia__qmb._getvalue()
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
            ponzr__bytr = 0
            xham__utkl = v
            if xham__utkl < 0:
                ponzr__bytr = 1
                xham__utkl = -xham__utkl
            if xham__utkl < 1:
                hhcv__dvlbj = 1
            else:
                hhcv__dvlbj = 1 + int(np.floor(np.log10(xham__utkl)))
            length = ponzr__bytr + hhcv__dvlbj + 1 + 6
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
    ojek__sgss = lir.FunctionType(lir.DoubleType(), [lir.IntType(8).
        as_pointer()])
    lks__qgy = cgutils.get_or_insert_function(builder.module, ojek__sgss,
        name='str_to_float64')
    res = builder.call(lks__qgy, (val,))
    bodo.utils.utils.inlined_check_and_propagate_cpp_exception(context, builder
        )
    return res


@lower_cast(StdStringType, types.float32)
def cast_str_to_float32(context, builder, fromty, toty, val):
    ojek__sgss = lir.FunctionType(lir.FloatType(), [lir.IntType(8).
        as_pointer()])
    lks__qgy = cgutils.get_or_insert_function(builder.module, ojek__sgss,
        name='str_to_float32')
    res = builder.call(lks__qgy, (val,))
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
    cpx__amd = cgutils.create_struct_proxy(string_type)(context, builder,
        value=val)
    ojek__sgss = lir.FunctionType(lir.IntType(toty.bitwidth), [lir.IntType(
        8).as_pointer(), lir.IntType(64)])
    lks__qgy = cgutils.get_or_insert_function(builder.module, ojek__sgss,
        name='str_to_int64')
    res = builder.call(lks__qgy, (cpx__amd.data, cpx__amd.length))
    bodo.utils.utils.inlined_check_and_propagate_cpp_exception(context, builder
        )
    return res


@lower_cast(string_type, types.uint64)
@lower_cast(string_type, types.uint32)
@lower_cast(string_type, types.uint16)
@lower_cast(string_type, types.uint8)
def cast_unicode_str_to_uint64(context, builder, fromty, toty, val):
    cpx__amd = cgutils.create_struct_proxy(string_type)(context, builder,
        value=val)
    ojek__sgss = lir.FunctionType(lir.IntType(toty.bitwidth), [lir.IntType(
        8).as_pointer(), lir.IntType(64)])
    lks__qgy = cgutils.get_or_insert_function(builder.module, ojek__sgss,
        name='str_to_uint64')
    res = builder.call(lks__qgy, (cpx__amd.data, cpx__amd.length))
    bodo.utils.utils.inlined_check_and_propagate_cpp_exception(context, builder
        )
    return res


@infer_getattr
class StringAttribute(AttributeTemplate):
    key = types.UnicodeType

    @bound_function('str.format', no_unliteral=True)
    def resolve_format(self, string_typ, args, kws):
        kws = dict(kws)
        nbxxc__jmqxf = ', '.join('e{}'.format(gez__vizjq) for gez__vizjq in
            range(len(args)))
        if nbxxc__jmqxf:
            nbxxc__jmqxf += ', '
        nwlq__lyb = ', '.join("{} = ''".format(a) for a in kws.keys())
        cwuhj__bnmuo = (
            f'def format_stub(string, {nbxxc__jmqxf} {nwlq__lyb}):\n')
        cwuhj__bnmuo += '    pass\n'
        abv__pgqw = {}
        exec(cwuhj__bnmuo, {}, abv__pgqw)
        ress__cqy = abv__pgqw['format_stub']
        opb__xtyj = numba.core.utils.pysignature(ress__cqy)
        bmhhg__msh = (string_typ,) + args + tuple(kws.values())
        return signature(string_typ, bmhhg__msh).replace(pysig=opb__xtyj)


@numba.njit(cache=True)
def str_split(arr, pat, n):
    gnx__xgw = pat is not None and len(pat) > 1
    if gnx__xgw:
        kjv__omhop = re.compile(pat)
        if n == -1:
            n = 0
    elif n == 0:
        n = -1
    mfq__fkuxc = len(arr)
    mxw__kqw = 0
    soef__onhwn = 0
    for gez__vizjq in numba.parfors.parfor.internal_prange(mfq__fkuxc):
        if bodo.libs.array_kernels.isna(arr, gez__vizjq):
            continue
        if gnx__xgw:
            kugc__vbku = kjv__omhop.split(arr[gez__vizjq], maxsplit=n)
        elif pat == '':
            kugc__vbku = [''] + list(arr[gez__vizjq]) + ['']
        else:
            kugc__vbku = arr[gez__vizjq].split(pat, n)
        mxw__kqw += len(kugc__vbku)
        for s in kugc__vbku:
            soef__onhwn += bodo.libs.str_arr_ext.get_utf8_size(s)
    cisvj__zslpx = bodo.libs.array_item_arr_ext.pre_alloc_array_item_array(
        mfq__fkuxc, (mxw__kqw, soef__onhwn), bodo.libs.str_arr_ext.
        string_array_type)
    onqr__mnnkt = bodo.libs.array_item_arr_ext.get_offsets(cisvj__zslpx)
    vvaxe__ebn = bodo.libs.array_item_arr_ext.get_null_bitmap(cisvj__zslpx)
    kkhed__vtpmv = bodo.libs.array_item_arr_ext.get_data(cisvj__zslpx)
    xbide__itrd = 0
    for pnf__rnxwg in numba.parfors.parfor.internal_prange(mfq__fkuxc):
        onqr__mnnkt[pnf__rnxwg] = xbide__itrd
        if bodo.libs.array_kernels.isna(arr, pnf__rnxwg):
            bodo.libs.int_arr_ext.set_bit_to_arr(vvaxe__ebn, pnf__rnxwg, 0)
            continue
        bodo.libs.int_arr_ext.set_bit_to_arr(vvaxe__ebn, pnf__rnxwg, 1)
        if gnx__xgw:
            kugc__vbku = kjv__omhop.split(arr[pnf__rnxwg], maxsplit=n)
        elif pat == '':
            kugc__vbku = [''] + list(arr[pnf__rnxwg]) + ['']
        else:
            kugc__vbku = arr[pnf__rnxwg].split(pat, n)
        hcf__fbnt = len(kugc__vbku)
        for emk__uzc in range(hcf__fbnt):
            s = kugc__vbku[emk__uzc]
            kkhed__vtpmv[xbide__itrd] = s
            xbide__itrd += 1
    onqr__mnnkt[mfq__fkuxc] = xbide__itrd
    return cisvj__zslpx


@overload(hex)
def overload_hex(x):
    if isinstance(x, types.Integer):
        kind = numba.cpython.unicode.PY_UNICODE_1BYTE_KIND

        def impl(x):
            x = np.int64(x)
            if x < 0:
                wos__wuwdm = '-0x'
                x = x * -1
            else:
                wos__wuwdm = '0x'
            x = np.uint64(x)
            if x == 0:
                mapu__dgsgo = 1
            else:
                mapu__dgsgo = fast_ceil_log2(x + 1)
                mapu__dgsgo = (mapu__dgsgo + 3) // 4
            length = len(wos__wuwdm) + mapu__dgsgo
            output = numba.cpython.unicode._empty_string(kind, length, 1)
            bodo.libs.str_arr_ext._memcpy(output._data, wos__wuwdm._data,
                len(wos__wuwdm), 1)
            int_to_hex(output, mapu__dgsgo, len(wos__wuwdm), x)
            return output
        return impl


@register_jitable
def fast_ceil_log2(x):
    uno__ywr = 0 if x & x - 1 == 0 else 1
    kuhto__tsqyi = [np.uint64(18446744069414584320), np.uint64(4294901760),
        np.uint64(65280), np.uint64(240), np.uint64(12), np.uint64(2)]
    nxbj__sbs = 32
    for gez__vizjq in range(len(kuhto__tsqyi)):
        kcb__lhfx = 0 if x & kuhto__tsqyi[gez__vizjq] == 0 else nxbj__sbs
        uno__ywr = uno__ywr + kcb__lhfx
        x = x >> kcb__lhfx
        nxbj__sbs = nxbj__sbs >> 1
    return uno__ywr


@intrinsic
def int_to_hex(typingctx, output, out_len, header_len, int_val):

    def codegen(context, builder, sig, args):
        output, out_len, header_len, int_val = args
        qmko__ypjh = cgutils.create_struct_proxy(sig.args[0])(context,
            builder, value=output)
        ojek__sgss = lir.FunctionType(lir.IntType(8).as_pointer(), [lir.
            IntType(8).as_pointer(), lir.IntType(64), lir.IntType(64)])
        etimx__hlgi = cgutils.get_or_insert_function(builder.module,
            ojek__sgss, name='int_to_hex')
        ljrto__ikhqe = builder.inttoptr(builder.add(builder.ptrtoint(
            qmko__ypjh.data, lir.IntType(64)), header_len), lir.IntType(8).
            as_pointer())
        builder.call(etimx__hlgi, (ljrto__ikhqe, out_len, int_val))
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
