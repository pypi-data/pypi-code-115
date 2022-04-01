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
    mxux__lxqs = types.Tuple([utf8_str_type, types.int64])

    def codegen(context, builder, sig, args):
        wctuv__lnytn, = args
        bjv__icsai = cgutils.create_struct_proxy(string_type)(context,
            builder, value=wctuv__lnytn)
        iyxs__zep = cgutils.create_struct_proxy(utf8_str_type)(context, builder
            )
        klmo__cqb = cgutils.create_struct_proxy(mxux__lxqs)(context, builder)
        is_ascii = builder.icmp_unsigned('==', bjv__icsai.is_ascii, lir.
            Constant(bjv__icsai.is_ascii.type, 1))
        with builder.if_else(is_ascii) as (oxcwh__ddrg, qaem__tuk):
            with oxcwh__ddrg:
                context.nrt.incref(builder, string_type, wctuv__lnytn)
                iyxs__zep.data = bjv__icsai.data
                iyxs__zep.meminfo = bjv__icsai.meminfo
                klmo__cqb.f1 = bjv__icsai.length
            with qaem__tuk:
                qmbcm__fnqjl = lir.FunctionType(lir.IntType(64), [lir.
                    IntType(8).as_pointer(), lir.IntType(8).as_pointer(),
                    lir.IntType(64), lir.IntType(32)])
                ouik__cbu = cgutils.get_or_insert_function(builder.module,
                    qmbcm__fnqjl, name='unicode_to_utf8')
                hwlfm__lrwvk = context.get_constant_null(types.voidptr)
                wdv__yqzfa = builder.call(ouik__cbu, [hwlfm__lrwvk,
                    bjv__icsai.data, bjv__icsai.length, bjv__icsai.kind])
                klmo__cqb.f1 = wdv__yqzfa
                udrrt__flh = builder.add(wdv__yqzfa, lir.Constant(lir.
                    IntType(64), 1))
                iyxs__zep.meminfo = context.nrt.meminfo_alloc_aligned(builder,
                    size=udrrt__flh, align=32)
                iyxs__zep.data = context.nrt.meminfo_data(builder,
                    iyxs__zep.meminfo)
                builder.call(ouik__cbu, [iyxs__zep.data, bjv__icsai.data,
                    bjv__icsai.length, bjv__icsai.kind])
                builder.store(lir.Constant(lir.IntType(8), 0), builder.gep(
                    iyxs__zep.data, [wdv__yqzfa]))
        klmo__cqb.f0 = iyxs__zep._getvalue()
        return klmo__cqb._getvalue()
    return mxux__lxqs(string_type), codegen


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
        qmbcm__fnqjl = lir.FunctionType(lir.IntType(32), [lir.IntType(8).
            as_pointer(), lir.IntType(8).as_pointer(), lir.IntType(64)])
        lkb__kro = cgutils.get_or_insert_function(builder.module,
            qmbcm__fnqjl, name='memcmp')
        return builder.call(lkb__kro, args)
    return types.int32(types.voidptr, types.voidptr, types.intp), codegen


def int_to_str_len(n):
    return len(str(n))


@overload(int_to_str_len)
def overload_int_to_str_len(n):
    qqcmu__svqj = n(10)

    def impl(n):
        if n == 0:
            return 1
        zap__dmxvw = 0
        if n < 0:
            n = -n
            zap__dmxvw += 1
        while n > 0:
            n = n // qqcmu__svqj
            zap__dmxvw += 1
        return zap__dmxvw
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
        [qhx__bxqo] = args
        if isinstance(qhx__bxqo, StdStringType):
            return signature(types.float64, qhx__bxqo)
        if qhx__bxqo == string_type:
            return signature(types.float64, qhx__bxqo)


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
    bjv__icsai = cgutils.create_struct_proxy(string_type)(context, builder,
        value=unicode_val)
    qmbcm__fnqjl = lir.FunctionType(lir.IntType(8).as_pointer(), [lir.
        IntType(8).as_pointer(), lir.IntType(64)])
    hsr__wuvdv = cgutils.get_or_insert_function(builder.module,
        qmbcm__fnqjl, name='init_string_const')
    return builder.call(hsr__wuvdv, [bjv__icsai.data, bjv__icsai.length])


def gen_std_str_to_unicode(context, builder, std_str_val, del_str=False):
    kind = numba.cpython.unicode.PY_UNICODE_1BYTE_KIND

    def _std_str_to_unicode(std_str):
        length = bodo.libs.str_ext.get_std_str_len(std_str)
        ojrs__bfc = numba.cpython.unicode._empty_string(kind, length, 1)
        bodo.libs.str_arr_ext._memcpy(ojrs__bfc._data, bodo.libs.str_ext.
            get_c_str(std_str), length, 1)
        if del_str:
            bodo.libs.str_ext.del_str(std_str)
        return ojrs__bfc
    val = context.compile_internal(builder, _std_str_to_unicode,
        string_type(bodo.libs.str_ext.std_str_type), [std_str_val])
    return val


def gen_get_unicode_chars(context, builder, unicode_val):
    bjv__icsai = cgutils.create_struct_proxy(string_type)(context, builder,
        value=unicode_val)
    return bjv__icsai.data


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
        qypx__vsai = [('data', types.List(string_type))]
        models.StructModel.__init__(self, dmm, fe_type, qypx__vsai)


make_attribute_wrapper(RandomAccessStringArrayType, 'data', '_data')


@intrinsic
def alloc_random_access_string_array(typingctx, n_t=None):

    def codegen(context, builder, sig, args):
        dvto__oxeb, = args
        chid__qgg = types.List(string_type)
        wbha__lhl = numba.cpython.listobj.ListInstance.allocate(context,
            builder, chid__qgg, dvto__oxeb)
        wbha__lhl.size = dvto__oxeb
        lqo__pev = cgutils.create_struct_proxy(sig.return_type)(context,
            builder)
        lqo__pev.data = wbha__lhl.value
        return lqo__pev._getvalue()
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
            hjto__lhpnd = 0
            ikl__hgiy = v
            if ikl__hgiy < 0:
                hjto__lhpnd = 1
                ikl__hgiy = -ikl__hgiy
            if ikl__hgiy < 1:
                xewlq__sxhbn = 1
            else:
                xewlq__sxhbn = 1 + int(np.floor(np.log10(ikl__hgiy)))
            length = hjto__lhpnd + xewlq__sxhbn + 1 + 6
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
    qmbcm__fnqjl = lir.FunctionType(lir.DoubleType(), [lir.IntType(8).
        as_pointer()])
    hsr__wuvdv = cgutils.get_or_insert_function(builder.module,
        qmbcm__fnqjl, name='str_to_float64')
    res = builder.call(hsr__wuvdv, (val,))
    bodo.utils.utils.inlined_check_and_propagate_cpp_exception(context, builder
        )
    return res


@lower_cast(StdStringType, types.float32)
def cast_str_to_float32(context, builder, fromty, toty, val):
    qmbcm__fnqjl = lir.FunctionType(lir.FloatType(), [lir.IntType(8).
        as_pointer()])
    hsr__wuvdv = cgutils.get_or_insert_function(builder.module,
        qmbcm__fnqjl, name='str_to_float32')
    res = builder.call(hsr__wuvdv, (val,))
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
    bjv__icsai = cgutils.create_struct_proxy(string_type)(context, builder,
        value=val)
    qmbcm__fnqjl = lir.FunctionType(lir.IntType(toty.bitwidth), [lir.
        IntType(8).as_pointer(), lir.IntType(64)])
    hsr__wuvdv = cgutils.get_or_insert_function(builder.module,
        qmbcm__fnqjl, name='str_to_int64')
    res = builder.call(hsr__wuvdv, (bjv__icsai.data, bjv__icsai.length))
    bodo.utils.utils.inlined_check_and_propagate_cpp_exception(context, builder
        )
    return res


@lower_cast(string_type, types.uint64)
@lower_cast(string_type, types.uint32)
@lower_cast(string_type, types.uint16)
@lower_cast(string_type, types.uint8)
def cast_unicode_str_to_uint64(context, builder, fromty, toty, val):
    bjv__icsai = cgutils.create_struct_proxy(string_type)(context, builder,
        value=val)
    qmbcm__fnqjl = lir.FunctionType(lir.IntType(toty.bitwidth), [lir.
        IntType(8).as_pointer(), lir.IntType(64)])
    hsr__wuvdv = cgutils.get_or_insert_function(builder.module,
        qmbcm__fnqjl, name='str_to_uint64')
    res = builder.call(hsr__wuvdv, (bjv__icsai.data, bjv__icsai.length))
    bodo.utils.utils.inlined_check_and_propagate_cpp_exception(context, builder
        )
    return res


@infer_getattr
class StringAttribute(AttributeTemplate):
    key = types.UnicodeType

    @bound_function('str.format', no_unliteral=True)
    def resolve_format(self, string_typ, args, kws):
        kws = dict(kws)
        fnrff__gta = ', '.join('e{}'.format(mhtj__otdxl) for mhtj__otdxl in
            range(len(args)))
        if fnrff__gta:
            fnrff__gta += ', '
        xhfse__nov = ', '.join("{} = ''".format(a) for a in kws.keys())
        gimfh__sug = f'def format_stub(string, {fnrff__gta} {xhfse__nov}):\n'
        gimfh__sug += '    pass\n'
        drz__dpe = {}
        exec(gimfh__sug, {}, drz__dpe)
        eyng__kow = drz__dpe['format_stub']
        eixw__bypik = numba.core.utils.pysignature(eyng__kow)
        wxj__jehg = (string_typ,) + args + tuple(kws.values())
        return signature(string_typ, wxj__jehg).replace(pysig=eixw__bypik)


@numba.njit(cache=True)
def str_split(arr, pat, n):
    tfz__tejz = pat is not None and len(pat) > 1
    if tfz__tejz:
        zense__imzdb = re.compile(pat)
        if n == -1:
            n = 0
    elif n == 0:
        n = -1
    wbha__lhl = len(arr)
    bjob__dulez = 0
    xqka__kvnlh = 0
    for mhtj__otdxl in numba.parfors.parfor.internal_prange(wbha__lhl):
        if bodo.libs.array_kernels.isna(arr, mhtj__otdxl):
            continue
        if tfz__tejz:
            rmyk__mfca = zense__imzdb.split(arr[mhtj__otdxl], maxsplit=n)
        elif pat == '':
            rmyk__mfca = [''] + list(arr[mhtj__otdxl]) + ['']
        else:
            rmyk__mfca = arr[mhtj__otdxl].split(pat, n)
        bjob__dulez += len(rmyk__mfca)
        for s in rmyk__mfca:
            xqka__kvnlh += bodo.libs.str_arr_ext.get_utf8_size(s)
    enmgz__dyhx = bodo.libs.array_item_arr_ext.pre_alloc_array_item_array(
        wbha__lhl, (bjob__dulez, xqka__kvnlh), bodo.libs.str_arr_ext.
        string_array_type)
    fulcp__dcemo = bodo.libs.array_item_arr_ext.get_offsets(enmgz__dyhx)
    tdjz__yjvvp = bodo.libs.array_item_arr_ext.get_null_bitmap(enmgz__dyhx)
    zgalr__ndnf = bodo.libs.array_item_arr_ext.get_data(enmgz__dyhx)
    eid__ldrhc = 0
    for kom__bhswl in numba.parfors.parfor.internal_prange(wbha__lhl):
        fulcp__dcemo[kom__bhswl] = eid__ldrhc
        if bodo.libs.array_kernels.isna(arr, kom__bhswl):
            bodo.libs.int_arr_ext.set_bit_to_arr(tdjz__yjvvp, kom__bhswl, 0)
            continue
        bodo.libs.int_arr_ext.set_bit_to_arr(tdjz__yjvvp, kom__bhswl, 1)
        if tfz__tejz:
            rmyk__mfca = zense__imzdb.split(arr[kom__bhswl], maxsplit=n)
        elif pat == '':
            rmyk__mfca = [''] + list(arr[kom__bhswl]) + ['']
        else:
            rmyk__mfca = arr[kom__bhswl].split(pat, n)
        vsv__mzxn = len(rmyk__mfca)
        for tnml__gpwkx in range(vsv__mzxn):
            s = rmyk__mfca[tnml__gpwkx]
            zgalr__ndnf[eid__ldrhc] = s
            eid__ldrhc += 1
    fulcp__dcemo[wbha__lhl] = eid__ldrhc
    return enmgz__dyhx


@overload(hex)
def overload_hex(x):
    if isinstance(x, types.Integer):
        kind = numba.cpython.unicode.PY_UNICODE_1BYTE_KIND

        def impl(x):
            x = np.int64(x)
            if x < 0:
                uqsze__but = '-0x'
                x = x * -1
            else:
                uqsze__but = '0x'
            x = np.uint64(x)
            if x == 0:
                mjco__zdqn = 1
            else:
                mjco__zdqn = fast_ceil_log2(x + 1)
                mjco__zdqn = (mjco__zdqn + 3) // 4
            length = len(uqsze__but) + mjco__zdqn
            output = numba.cpython.unicode._empty_string(kind, length, 1)
            bodo.libs.str_arr_ext._memcpy(output._data, uqsze__but._data,
                len(uqsze__but), 1)
            int_to_hex(output, mjco__zdqn, len(uqsze__but), x)
            return output
        return impl


@register_jitable
def fast_ceil_log2(x):
    pgxh__cbwpt = 0 if x & x - 1 == 0 else 1
    inyv__pdgfj = [np.uint64(18446744069414584320), np.uint64(4294901760),
        np.uint64(65280), np.uint64(240), np.uint64(12), np.uint64(2)]
    pwfg__bogs = 32
    for mhtj__otdxl in range(len(inyv__pdgfj)):
        aajhj__hacxt = 0 if x & inyv__pdgfj[mhtj__otdxl] == 0 else pwfg__bogs
        pgxh__cbwpt = pgxh__cbwpt + aajhj__hacxt
        x = x >> aajhj__hacxt
        pwfg__bogs = pwfg__bogs >> 1
    return pgxh__cbwpt


@intrinsic
def int_to_hex(typingctx, output, out_len, header_len, int_val):

    def codegen(context, builder, sig, args):
        output, out_len, header_len, int_val = args
        glta__pxypf = cgutils.create_struct_proxy(sig.args[0])(context,
            builder, value=output)
        qmbcm__fnqjl = lir.FunctionType(lir.IntType(8).as_pointer(), [lir.
            IntType(8).as_pointer(), lir.IntType(64), lir.IntType(64)])
        nsiy__rkht = cgutils.get_or_insert_function(builder.module,
            qmbcm__fnqjl, name='int_to_hex')
        ggqd__jswb = builder.inttoptr(builder.add(builder.ptrtoint(
            glta__pxypf.data, lir.IntType(64)), header_len), lir.IntType(8)
            .as_pointer())
        builder.call(nsiy__rkht, (ggqd__jswb, out_len, int_val))
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
