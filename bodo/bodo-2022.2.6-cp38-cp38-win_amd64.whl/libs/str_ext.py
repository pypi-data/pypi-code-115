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
    xrbj__tbiey = types.Tuple([utf8_str_type, types.int64])

    def codegen(context, builder, sig, args):
        ahg__bvrj, = args
        fny__yacnb = cgutils.create_struct_proxy(string_type)(context,
            builder, value=ahg__bvrj)
        ndnsj__stpw = cgutils.create_struct_proxy(utf8_str_type)(context,
            builder)
        dpyrg__guh = cgutils.create_struct_proxy(xrbj__tbiey)(context, builder)
        is_ascii = builder.icmp_unsigned('==', fny__yacnb.is_ascii, lir.
            Constant(fny__yacnb.is_ascii.type, 1))
        with builder.if_else(is_ascii) as (lcqrg__zyt, raal__jji):
            with lcqrg__zyt:
                context.nrt.incref(builder, string_type, ahg__bvrj)
                ndnsj__stpw.data = fny__yacnb.data
                ndnsj__stpw.meminfo = fny__yacnb.meminfo
                dpyrg__guh.f1 = fny__yacnb.length
            with raal__jji:
                vqaz__bkvqm = lir.FunctionType(lir.IntType(64), [lir.
                    IntType(8).as_pointer(), lir.IntType(8).as_pointer(),
                    lir.IntType(64), lir.IntType(32)])
                wbb__exjl = cgutils.get_or_insert_function(builder.module,
                    vqaz__bkvqm, name='unicode_to_utf8')
                iltbq__ypxub = context.get_constant_null(types.voidptr)
                nov__wcet = builder.call(wbb__exjl, [iltbq__ypxub,
                    fny__yacnb.data, fny__yacnb.length, fny__yacnb.kind])
                dpyrg__guh.f1 = nov__wcet
                ymru__pmdm = builder.add(nov__wcet, lir.Constant(lir.
                    IntType(64), 1))
                ndnsj__stpw.meminfo = context.nrt.meminfo_alloc_aligned(builder
                    , size=ymru__pmdm, align=32)
                ndnsj__stpw.data = context.nrt.meminfo_data(builder,
                    ndnsj__stpw.meminfo)
                builder.call(wbb__exjl, [ndnsj__stpw.data, fny__yacnb.data,
                    fny__yacnb.length, fny__yacnb.kind])
                builder.store(lir.Constant(lir.IntType(8), 0), builder.gep(
                    ndnsj__stpw.data, [nov__wcet]))
        dpyrg__guh.f0 = ndnsj__stpw._getvalue()
        return dpyrg__guh._getvalue()
    return xrbj__tbiey(string_type), codegen


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
        vqaz__bkvqm = lir.FunctionType(lir.IntType(32), [lir.IntType(8).
            as_pointer(), lir.IntType(8).as_pointer(), lir.IntType(64)])
        mtrbw__plst = cgutils.get_or_insert_function(builder.module,
            vqaz__bkvqm, name='memcmp')
        return builder.call(mtrbw__plst, args)
    return types.int32(types.voidptr, types.voidptr, types.intp), codegen


def int_to_str_len(n):
    return len(str(n))


@overload(int_to_str_len)
def overload_int_to_str_len(n):
    tzlr__bxb = n(10)

    def impl(n):
        if n == 0:
            return 1
        gfsu__hrq = 0
        if n < 0:
            n = -n
            gfsu__hrq += 1
        while n > 0:
            n = n // tzlr__bxb
            gfsu__hrq += 1
        return gfsu__hrq
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
        [xhwqy__suf] = args
        if isinstance(xhwqy__suf, StdStringType):
            return signature(types.float64, xhwqy__suf)
        if xhwqy__suf == string_type:
            return signature(types.float64, xhwqy__suf)


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
    fny__yacnb = cgutils.create_struct_proxy(string_type)(context, builder,
        value=unicode_val)
    vqaz__bkvqm = lir.FunctionType(lir.IntType(8).as_pointer(), [lir.
        IntType(8).as_pointer(), lir.IntType(64)])
    gpet__rak = cgutils.get_or_insert_function(builder.module, vqaz__bkvqm,
        name='init_string_const')
    return builder.call(gpet__rak, [fny__yacnb.data, fny__yacnb.length])


def gen_std_str_to_unicode(context, builder, std_str_val, del_str=False):
    kind = numba.cpython.unicode.PY_UNICODE_1BYTE_KIND

    def _std_str_to_unicode(std_str):
        length = bodo.libs.str_ext.get_std_str_len(std_str)
        jnz__ymjq = numba.cpython.unicode._empty_string(kind, length, 1)
        bodo.libs.str_arr_ext._memcpy(jnz__ymjq._data, bodo.libs.str_ext.
            get_c_str(std_str), length, 1)
        if del_str:
            bodo.libs.str_ext.del_str(std_str)
        return jnz__ymjq
    val = context.compile_internal(builder, _std_str_to_unicode,
        string_type(bodo.libs.str_ext.std_str_type), [std_str_val])
    return val


def gen_get_unicode_chars(context, builder, unicode_val):
    fny__yacnb = cgutils.create_struct_proxy(string_type)(context, builder,
        value=unicode_val)
    return fny__yacnb.data


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
        yulb__jnz = [('data', types.List(string_type))]
        models.StructModel.__init__(self, dmm, fe_type, yulb__jnz)


make_attribute_wrapper(RandomAccessStringArrayType, 'data', '_data')


@intrinsic
def alloc_random_access_string_array(typingctx, n_t=None):

    def codegen(context, builder, sig, args):
        uxbdv__zoki, = args
        hjtt__huuz = types.List(string_type)
        qchwi__ivofw = numba.cpython.listobj.ListInstance.allocate(context,
            builder, hjtt__huuz, uxbdv__zoki)
        qchwi__ivofw.size = uxbdv__zoki
        drw__pffdz = cgutils.create_struct_proxy(sig.return_type)(context,
            builder)
        drw__pffdz.data = qchwi__ivofw.value
        return drw__pffdz._getvalue()
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
            cafre__sis = 0
            vjwn__jmd = v
            if vjwn__jmd < 0:
                cafre__sis = 1
                vjwn__jmd = -vjwn__jmd
            if vjwn__jmd < 1:
                rpfqq__worjw = 1
            else:
                rpfqq__worjw = 1 + int(np.floor(np.log10(vjwn__jmd)))
            length = cafre__sis + rpfqq__worjw + 1 + 6
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
    vqaz__bkvqm = lir.FunctionType(lir.DoubleType(), [lir.IntType(8).
        as_pointer()])
    gpet__rak = cgutils.get_or_insert_function(builder.module, vqaz__bkvqm,
        name='str_to_float64')
    res = builder.call(gpet__rak, (val,))
    bodo.utils.utils.inlined_check_and_propagate_cpp_exception(context, builder
        )
    return res


@lower_cast(StdStringType, types.float32)
def cast_str_to_float32(context, builder, fromty, toty, val):
    vqaz__bkvqm = lir.FunctionType(lir.FloatType(), [lir.IntType(8).
        as_pointer()])
    gpet__rak = cgutils.get_or_insert_function(builder.module, vqaz__bkvqm,
        name='str_to_float32')
    res = builder.call(gpet__rak, (val,))
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
    fny__yacnb = cgutils.create_struct_proxy(string_type)(context, builder,
        value=val)
    vqaz__bkvqm = lir.FunctionType(lir.IntType(toty.bitwidth), [lir.IntType
        (8).as_pointer(), lir.IntType(64)])
    gpet__rak = cgutils.get_or_insert_function(builder.module, vqaz__bkvqm,
        name='str_to_int64')
    res = builder.call(gpet__rak, (fny__yacnb.data, fny__yacnb.length))
    bodo.utils.utils.inlined_check_and_propagate_cpp_exception(context, builder
        )
    return res


@lower_cast(string_type, types.uint64)
@lower_cast(string_type, types.uint32)
@lower_cast(string_type, types.uint16)
@lower_cast(string_type, types.uint8)
def cast_unicode_str_to_uint64(context, builder, fromty, toty, val):
    fny__yacnb = cgutils.create_struct_proxy(string_type)(context, builder,
        value=val)
    vqaz__bkvqm = lir.FunctionType(lir.IntType(toty.bitwidth), [lir.IntType
        (8).as_pointer(), lir.IntType(64)])
    gpet__rak = cgutils.get_or_insert_function(builder.module, vqaz__bkvqm,
        name='str_to_uint64')
    res = builder.call(gpet__rak, (fny__yacnb.data, fny__yacnb.length))
    bodo.utils.utils.inlined_check_and_propagate_cpp_exception(context, builder
        )
    return res


@infer_getattr
class StringAttribute(AttributeTemplate):
    key = types.UnicodeType

    @bound_function('str.format', no_unliteral=True)
    def resolve_format(self, string_typ, args, kws):
        kws = dict(kws)
        wgi__xqpuo = ', '.join('e{}'.format(ucmd__ugomu) for ucmd__ugomu in
            range(len(args)))
        if wgi__xqpuo:
            wgi__xqpuo += ', '
        mjpm__tlji = ', '.join("{} = ''".format(a) for a in kws.keys())
        ftgjw__rkwi = f'def format_stub(string, {wgi__xqpuo} {mjpm__tlji}):\n'
        ftgjw__rkwi += '    pass\n'
        encwd__nmec = {}
        exec(ftgjw__rkwi, {}, encwd__nmec)
        qpqb__zefse = encwd__nmec['format_stub']
        zsmu__nqgu = numba.core.utils.pysignature(qpqb__zefse)
        pkkz__nvmfd = (string_typ,) + args + tuple(kws.values())
        return signature(string_typ, pkkz__nvmfd).replace(pysig=zsmu__nqgu)


@numba.njit(cache=True)
def str_split(arr, pat, n):
    romun__uchjh = pat is not None and len(pat) > 1
    if romun__uchjh:
        uknk__tltnh = re.compile(pat)
        if n == -1:
            n = 0
    elif n == 0:
        n = -1
    qchwi__ivofw = len(arr)
    xbh__dgd = 0
    yrcs__vxt = 0
    for ucmd__ugomu in numba.parfors.parfor.internal_prange(qchwi__ivofw):
        if bodo.libs.array_kernels.isna(arr, ucmd__ugomu):
            continue
        if romun__uchjh:
            zdyjo__xnkys = uknk__tltnh.split(arr[ucmd__ugomu], maxsplit=n)
        elif pat == '':
            zdyjo__xnkys = [''] + list(arr[ucmd__ugomu]) + ['']
        else:
            zdyjo__xnkys = arr[ucmd__ugomu].split(pat, n)
        xbh__dgd += len(zdyjo__xnkys)
        for s in zdyjo__xnkys:
            yrcs__vxt += bodo.libs.str_arr_ext.get_utf8_size(s)
    xio__aoh = bodo.libs.array_item_arr_ext.pre_alloc_array_item_array(
        qchwi__ivofw, (xbh__dgd, yrcs__vxt), bodo.libs.str_arr_ext.
        string_array_type)
    dxng__pxlv = bodo.libs.array_item_arr_ext.get_offsets(xio__aoh)
    ytwnq__mckr = bodo.libs.array_item_arr_ext.get_null_bitmap(xio__aoh)
    wda__qgx = bodo.libs.array_item_arr_ext.get_data(xio__aoh)
    xdj__xylx = 0
    for hmil__xldbr in numba.parfors.parfor.internal_prange(qchwi__ivofw):
        dxng__pxlv[hmil__xldbr] = xdj__xylx
        if bodo.libs.array_kernels.isna(arr, hmil__xldbr):
            bodo.libs.int_arr_ext.set_bit_to_arr(ytwnq__mckr, hmil__xldbr, 0)
            continue
        bodo.libs.int_arr_ext.set_bit_to_arr(ytwnq__mckr, hmil__xldbr, 1)
        if romun__uchjh:
            zdyjo__xnkys = uknk__tltnh.split(arr[hmil__xldbr], maxsplit=n)
        elif pat == '':
            zdyjo__xnkys = [''] + list(arr[hmil__xldbr]) + ['']
        else:
            zdyjo__xnkys = arr[hmil__xldbr].split(pat, n)
        wgvah__evye = len(zdyjo__xnkys)
        for daimu__vlt in range(wgvah__evye):
            s = zdyjo__xnkys[daimu__vlt]
            wda__qgx[xdj__xylx] = s
            xdj__xylx += 1
    dxng__pxlv[qchwi__ivofw] = xdj__xylx
    return xio__aoh


@overload(hex)
def overload_hex(x):
    if isinstance(x, types.Integer):
        kind = numba.cpython.unicode.PY_UNICODE_1BYTE_KIND

        def impl(x):
            x = np.int64(x)
            if x < 0:
                eru__izbxb = '-0x'
                x = x * -1
            else:
                eru__izbxb = '0x'
            x = np.uint64(x)
            if x == 0:
                yae__ldc = 1
            else:
                yae__ldc = fast_ceil_log2(x + 1)
                yae__ldc = (yae__ldc + 3) // 4
            length = len(eru__izbxb) + yae__ldc
            output = numba.cpython.unicode._empty_string(kind, length, 1)
            bodo.libs.str_arr_ext._memcpy(output._data, eru__izbxb._data,
                len(eru__izbxb), 1)
            int_to_hex(output, yae__ldc, len(eru__izbxb), x)
            return output
        return impl


@register_jitable
def fast_ceil_log2(x):
    nwo__vleyh = 0 if x & x - 1 == 0 else 1
    nru__syhpd = [np.uint64(18446744069414584320), np.uint64(4294901760),
        np.uint64(65280), np.uint64(240), np.uint64(12), np.uint64(2)]
    wmtyh__vtdz = 32
    for ucmd__ugomu in range(len(nru__syhpd)):
        lqu__khgpw = 0 if x & nru__syhpd[ucmd__ugomu] == 0 else wmtyh__vtdz
        nwo__vleyh = nwo__vleyh + lqu__khgpw
        x = x >> lqu__khgpw
        wmtyh__vtdz = wmtyh__vtdz >> 1
    return nwo__vleyh


@intrinsic
def int_to_hex(typingctx, output, out_len, header_len, int_val):

    def codegen(context, builder, sig, args):
        output, out_len, header_len, int_val = args
        zthg__mjufp = cgutils.create_struct_proxy(sig.args[0])(context,
            builder, value=output)
        vqaz__bkvqm = lir.FunctionType(lir.IntType(8).as_pointer(), [lir.
            IntType(8).as_pointer(), lir.IntType(64), lir.IntType(64)])
        mppve__eczs = cgutils.get_or_insert_function(builder.module,
            vqaz__bkvqm, name='int_to_hex')
        qfmt__clgl = builder.inttoptr(builder.add(builder.ptrtoint(
            zthg__mjufp.data, lir.IntType(64)), header_len), lir.IntType(8)
            .as_pointer())
        builder.call(mppve__eczs, (qfmt__clgl, out_len, int_val))
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
