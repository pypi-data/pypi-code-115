"""
Support for Series.str methods
"""
import operator
import re
import numba
import numpy as np
from numba.core import cgutils, types
from numba.extending import intrinsic, make_attribute_wrapper, models, overload, overload_attribute, overload_method, register_model
import bodo
from bodo.hiframes.pd_dataframe_ext import DataFrameType
from bodo.hiframes.pd_index_ext import StringIndexType
from bodo.hiframes.pd_series_ext import SeriesType
from bodo.hiframes.split_impl import get_split_view_data_ptr, get_split_view_index, string_array_split_view_type
from bodo.libs.array import get_search_regex
from bodo.libs.array_item_arr_ext import ArrayItemArrayType
from bodo.libs.str_arr_ext import get_utf8_size, pre_alloc_string_array, string_array_type
from bodo.libs.str_ext import str_findall_count
from bodo.utils.typing import BodoError, create_unsupported_overload, get_overload_const_int, get_overload_const_list, get_overload_const_str, get_overload_const_str_len, is_list_like_index_type, is_overload_constant_bool, is_overload_constant_int, is_overload_constant_list, is_overload_constant_str, is_overload_false, is_overload_none, is_overload_true, is_str_arr_type, raise_bodo_error


class SeriesStrMethodType(types.Type):

    def __init__(self, stype):
        self.stype = stype
        xat__hfr = 'SeriesStrMethodType({})'.format(stype)
        super(SeriesStrMethodType, self).__init__(xat__hfr)


@register_model(SeriesStrMethodType)
class SeriesStrModel(models.StructModel):

    def __init__(self, dmm, fe_type):
        fqkfl__xth = [('obj', fe_type.stype)]
        super(SeriesStrModel, self).__init__(dmm, fe_type, fqkfl__xth)


make_attribute_wrapper(SeriesStrMethodType, 'obj', '_obj')


@intrinsic
def init_series_str_method(typingctx, obj=None):

    def codegen(context, builder, signature, args):
        pnr__fwd, = args
        dft__aysuv = signature.return_type
        lwsh__lhhy = cgutils.create_struct_proxy(dft__aysuv)(context, builder)
        lwsh__lhhy.obj = pnr__fwd
        context.nrt.incref(builder, signature.args[0], pnr__fwd)
        return lwsh__lhhy._getvalue()
    return SeriesStrMethodType(obj)(obj), codegen


def str_arg_check(func_name, arg_name, arg):
    if not isinstance(arg, types.UnicodeType) and not is_overload_constant_str(
        arg):
        raise_bodo_error(
            "Series.str.{}(): parameter '{}' expected a string object, not {}"
            .format(func_name, arg_name, arg))


def int_arg_check(func_name, arg_name, arg):
    if not isinstance(arg, types.Integer) and not is_overload_constant_int(arg
        ):
        raise BodoError(
            "Series.str.{}(): parameter '{}' expected an int object, not {}"
            .format(func_name, arg_name, arg))


def not_supported_arg_check(func_name, arg_name, arg, defval):
    if arg_name == 'na':
        if not isinstance(arg, types.Omitted) and (not isinstance(arg,
            float) or not np.isnan(arg)):
            raise BodoError(
                "Series.str.{}(): parameter '{}' is not supported, default: np.nan"
                .format(func_name, arg_name))
    elif not isinstance(arg, types.Omitted) and arg != defval:
        raise BodoError(
            "Series.str.{}(): parameter '{}' is not supported, default: {}"
            .format(func_name, arg_name, defval))


def common_validate_padding(func_name, width, fillchar):
    if is_overload_constant_str(fillchar):
        if get_overload_const_str_len(fillchar) != 1:
            raise BodoError(
                'Series.str.{}(): fillchar must be a character, not str'.
                format(func_name))
    elif not isinstance(fillchar, types.UnicodeType):
        raise BodoError('Series.str.{}(): fillchar must be a character, not {}'
            .format(func_name, fillchar))
    int_arg_check(func_name, 'width', width)


@overload_attribute(SeriesType, 'str')
def overload_series_str(S):
    if not (is_str_arr_type(S.data) or S.data ==
        string_array_split_view_type or isinstance(S.data, ArrayItemArrayType)
        ):
        raise_bodo_error(
            'Series.str: input should be a series of string or arrays')
    return lambda S: bodo.hiframes.series_str_impl.init_series_str_method(S)


@overload_method(SeriesStrMethodType, 'len', inline='always', no_unliteral=True
    )
def overload_str_method_len(S_str):

    def impl(S_str):
        S = S_str._obj
        qyjsm__fosvh = bodo.hiframes.pd_series_ext.get_series_data(S)
        dys__gqut = bodo.hiframes.pd_series_ext.get_series_index(S)
        xat__hfr = bodo.hiframes.pd_series_ext.get_series_name(S)
        out_arr = bodo.libs.array_kernels.get_arr_lens(qyjsm__fosvh, False)
        return bodo.hiframes.pd_series_ext.init_series(out_arr, dys__gqut,
            xat__hfr)
    return impl


@overload_method(SeriesStrMethodType, 'split', inline='always',
    no_unliteral=True)
def overload_str_method_split(S_str, pat=None, n=-1, expand=False):
    if not is_overload_none(pat):
        str_arg_check('split', 'pat', pat)
    int_arg_check('split', 'n', n)
    not_supported_arg_check('split', 'expand', expand, False)
    if is_overload_constant_str(pat) and len(get_overload_const_str(pat)
        ) == 1 and get_overload_const_str(pat).isascii(
        ) and is_overload_constant_int(n) and get_overload_const_int(n
        ) == -1 and S_str.stype.data == string_array_type:

        def _str_split_view_impl(S_str, pat=None, n=-1, expand=False):
            S = S_str._obj
            qyjsm__fosvh = bodo.hiframes.pd_series_ext.get_series_data(S)
            dys__gqut = bodo.hiframes.pd_series_ext.get_series_index(S)
            xat__hfr = bodo.hiframes.pd_series_ext.get_series_name(S)
            out_arr = bodo.hiframes.split_impl.compute_split_view(qyjsm__fosvh,
                pat)
            return bodo.hiframes.pd_series_ext.init_series(out_arr,
                dys__gqut, xat__hfr)
        return _str_split_view_impl

    def _str_split_impl(S_str, pat=None, n=-1, expand=False):
        S = S_str._obj
        qyjsm__fosvh = bodo.hiframes.pd_series_ext.get_series_data(S)
        dys__gqut = bodo.hiframes.pd_series_ext.get_series_index(S)
        xat__hfr = bodo.hiframes.pd_series_ext.get_series_name(S)
        out_arr = bodo.libs.str_ext.str_split(qyjsm__fosvh, pat, n)
        return bodo.hiframes.pd_series_ext.init_series(out_arr, dys__gqut,
            xat__hfr)
    return _str_split_impl


@overload_method(SeriesStrMethodType, 'get', no_unliteral=True)
def overload_str_method_get(S_str, i):
    drwyv__ilh = S_str.stype.data
    if (drwyv__ilh != string_array_split_view_type and not is_str_arr_type(
        drwyv__ilh)) and not isinstance(drwyv__ilh, ArrayItemArrayType):
        raise_bodo_error(
            'Series.str.get(): only supports input type of Series(array(item)) and Series(str)'
            )
    int_arg_check('get', 'i', i)
    if isinstance(drwyv__ilh, ArrayItemArrayType):

        def _str_get_array_impl(S_str, i):
            S = S_str._obj
            qyjsm__fosvh = bodo.hiframes.pd_series_ext.get_series_data(S)
            dys__gqut = bodo.hiframes.pd_series_ext.get_series_index(S)
            xat__hfr = bodo.hiframes.pd_series_ext.get_series_name(S)
            out_arr = bodo.libs.array_kernels.get(qyjsm__fosvh, i)
            return bodo.hiframes.pd_series_ext.init_series(out_arr,
                dys__gqut, xat__hfr)
        return _str_get_array_impl
    if drwyv__ilh == string_array_split_view_type:

        def _str_get_split_impl(S_str, i):
            S = S_str._obj
            qyjsm__fosvh = bodo.hiframes.pd_series_ext.get_series_data(S)
            dys__gqut = bodo.hiframes.pd_series_ext.get_series_index(S)
            xat__hfr = bodo.hiframes.pd_series_ext.get_series_name(S)
            numba.parfors.parfor.init_prange()
            n = len(qyjsm__fosvh)
            anqh__bwwl = 0
            for gqh__fltne in numba.parfors.parfor.internal_prange(n):
                tvo__gql, tvo__gql, ektht__scclb = get_split_view_index(
                    qyjsm__fosvh, gqh__fltne, i)
                anqh__bwwl += ektht__scclb
            numba.parfors.parfor.init_prange()
            out_arr = pre_alloc_string_array(n, anqh__bwwl)
            for nrigc__ifu in numba.parfors.parfor.internal_prange(n):
                atksu__wlbmb, xvn__gqsy, ektht__scclb = get_split_view_index(
                    qyjsm__fosvh, nrigc__ifu, i)
                if atksu__wlbmb == 0:
                    bodo.libs.array_kernels.setna(out_arr, nrigc__ifu)
                    dmom__xnwiv = get_split_view_data_ptr(qyjsm__fosvh, 0)
                else:
                    bodo.libs.str_arr_ext.str_arr_set_not_na(out_arr,
                        nrigc__ifu)
                    dmom__xnwiv = get_split_view_data_ptr(qyjsm__fosvh,
                        xvn__gqsy)
                bodo.libs.str_arr_ext.setitem_str_arr_ptr(out_arr,
                    nrigc__ifu, dmom__xnwiv, ektht__scclb)
            return bodo.hiframes.pd_series_ext.init_series(out_arr,
                dys__gqut, xat__hfr)
        return _str_get_split_impl

    def _str_get_impl(S_str, i):
        S = S_str._obj
        qyjsm__fosvh = bodo.hiframes.pd_series_ext.get_series_data(S)
        dys__gqut = bodo.hiframes.pd_series_ext.get_series_index(S)
        xat__hfr = bodo.hiframes.pd_series_ext.get_series_name(S)
        numba.parfors.parfor.init_prange()
        n = len(qyjsm__fosvh)
        numba.parfors.parfor.init_prange()
        out_arr = pre_alloc_string_array(n, -1)
        for nrigc__ifu in numba.parfors.parfor.internal_prange(n):
            if bodo.libs.array_kernels.isna(qyjsm__fosvh, nrigc__ifu
                ) or not len(qyjsm__fosvh[nrigc__ifu]) > i >= -len(qyjsm__fosvh
                [nrigc__ifu]):
                out_arr[nrigc__ifu] = ''
                bodo.libs.array_kernels.setna(out_arr, nrigc__ifu)
            else:
                out_arr[nrigc__ifu] = qyjsm__fosvh[nrigc__ifu][i]
        return bodo.hiframes.pd_series_ext.init_series(out_arr, dys__gqut,
            xat__hfr)
    return _str_get_impl


@overload_method(SeriesStrMethodType, 'join', inline='always', no_unliteral
    =True)
def overload_str_method_join(S_str, sep):
    drwyv__ilh = S_str.stype.data
    if (drwyv__ilh != string_array_split_view_type and drwyv__ilh !=
        ArrayItemArrayType(string_array_type) and not is_str_arr_type(
        drwyv__ilh)):
        raise_bodo_error(
            'Series.str.join(): only supports input type of Series(list(str)) and Series(str)'
            )
    str_arg_check('join', 'sep', sep)

    def impl(S_str, sep):
        S = S_str._obj
        mcd__kjqp = bodo.hiframes.pd_series_ext.get_series_data(S)
        xat__hfr = bodo.hiframes.pd_series_ext.get_series_name(S)
        dys__gqut = bodo.hiframes.pd_series_ext.get_series_index(S)
        numba.parfors.parfor.init_prange()
        n = len(mcd__kjqp)
        out_arr = bodo.libs.str_arr_ext.pre_alloc_string_array(n, -1)
        for nrigc__ifu in numba.parfors.parfor.internal_prange(n):
            if bodo.libs.array_kernels.isna(mcd__kjqp, nrigc__ifu):
                out_arr[nrigc__ifu] = ''
                bodo.libs.array_kernels.setna(out_arr, nrigc__ifu)
            else:
                ovs__qpeij = mcd__kjqp[nrigc__ifu]
                out_arr[nrigc__ifu] = sep.join(ovs__qpeij)
        return bodo.hiframes.pd_series_ext.init_series(out_arr, dys__gqut,
            xat__hfr)
    return impl


@overload_method(SeriesStrMethodType, 'replace', inline='always',
    no_unliteral=True)
def overload_str_method_replace(S_str, pat, repl, n=-1, case=None, flags=0,
    regex=True):
    not_supported_arg_check('replace', 'n', n, -1)
    not_supported_arg_check('replace', 'case', case, None)
    str_arg_check('replace', 'pat', pat)
    str_arg_check('replace', 'repl', repl)
    int_arg_check('replace', 'flags', flags)
    if S_str.stype.data == bodo.dict_str_arr_type:

        def _str_replace_dict_impl(S_str, pat, repl, n=-1, case=None, flags
            =0, regex=True):
            S = S_str._obj
            qyjsm__fosvh = bodo.hiframes.pd_series_ext.get_series_data(S)
            dys__gqut = bodo.hiframes.pd_series_ext.get_series_index(S)
            xat__hfr = bodo.hiframes.pd_series_ext.get_series_name(S)
            out_arr = bodo.libs.dict_arr_ext.str_replace(qyjsm__fosvh, pat,
                repl, flags, regex)
            return bodo.hiframes.pd_series_ext.init_series(out_arr,
                dys__gqut, xat__hfr)
        return _str_replace_dict_impl
    if is_overload_true(regex):

        def _str_replace_regex_impl(S_str, pat, repl, n=-1, case=None,
            flags=0, regex=True):
            S = S_str._obj
            qyjsm__fosvh = bodo.hiframes.pd_series_ext.get_series_data(S)
            dys__gqut = bodo.hiframes.pd_series_ext.get_series_index(S)
            xat__hfr = bodo.hiframes.pd_series_ext.get_series_name(S)
            numba.parfors.parfor.init_prange()
            suet__jzs = re.compile(pat, flags)
            tbp__lnss = len(qyjsm__fosvh)
            out_arr = pre_alloc_string_array(tbp__lnss, -1)
            for nrigc__ifu in numba.parfors.parfor.internal_prange(tbp__lnss):
                if bodo.libs.array_kernels.isna(qyjsm__fosvh, nrigc__ifu):
                    out_arr[nrigc__ifu] = ''
                    bodo.libs.array_kernels.setna(out_arr, nrigc__ifu)
                    continue
                out_arr[nrigc__ifu] = suet__jzs.sub(repl, qyjsm__fosvh[
                    nrigc__ifu])
            return bodo.hiframes.pd_series_ext.init_series(out_arr,
                dys__gqut, xat__hfr)
        return _str_replace_regex_impl
    if not is_overload_false(regex):
        raise BodoError('Series.str.replace(): regex argument should be bool')

    def _str_replace_noregex_impl(S_str, pat, repl, n=-1, case=None, flags=
        0, regex=True):
        S = S_str._obj
        qyjsm__fosvh = bodo.hiframes.pd_series_ext.get_series_data(S)
        dys__gqut = bodo.hiframes.pd_series_ext.get_series_index(S)
        xat__hfr = bodo.hiframes.pd_series_ext.get_series_name(S)
        numba.parfors.parfor.init_prange()
        tbp__lnss = len(qyjsm__fosvh)
        numba.parfors.parfor.init_prange()
        out_arr = pre_alloc_string_array(tbp__lnss, -1)
        for nrigc__ifu in numba.parfors.parfor.internal_prange(tbp__lnss):
            if bodo.libs.array_kernels.isna(qyjsm__fosvh, nrigc__ifu):
                out_arr[nrigc__ifu] = ''
                bodo.libs.array_kernels.setna(out_arr, nrigc__ifu)
                continue
            out_arr[nrigc__ifu] = qyjsm__fosvh[nrigc__ifu].replace(pat, repl)
        return bodo.hiframes.pd_series_ext.init_series(out_arr, dys__gqut,
            xat__hfr)
    return _str_replace_noregex_impl


@numba.njit
def series_contains_regex(S, pat, case, flags, na, regex):
    with numba.objmode(out_arr=bodo.boolean_array):
        out_arr = S.array._str_contains(pat, case, flags, na, regex)
    return out_arr


def is_regex_unsupported(pat):
    dzktz__onk = ['(?a', '(?i', '(?L', '(?m', '(?s', '(?u', '(?x', '(?#']
    if is_overload_constant_str(pat):
        if isinstance(pat, types.StringLiteral):
            pat = pat.literal_value
        return any([(fpoh__fxacn in pat) for fpoh__fxacn in dzktz__onk])
    else:
        return True


@overload_method(SeriesStrMethodType, 'contains', no_unliteral=True)
def overload_str_method_contains(S_str, pat, case=True, flags=0, na=np.nan,
    regex=True):
    not_supported_arg_check('contains', 'na', na, np.nan)
    str_arg_check('contains', 'pat', pat)
    int_arg_check('contains', 'flags', flags)
    if not is_overload_constant_bool(regex):
        raise BodoError(
            "Series.str.contains(): 'regex' argument should be a constant boolean"
            )
    if not is_overload_constant_bool(case):
        raise BodoError(
            "Series.str.contains(): 'case' argument should be a constant boolean"
            )
    bnps__snk = re.IGNORECASE.value
    owv__kpf = 'def impl(\n'
    owv__kpf += '    S_str, pat, case=True, flags=0, na=np.nan, regex=True\n'
    owv__kpf += '):\n'
    owv__kpf += '  S = S_str._obj\n'
    owv__kpf += '  arr = bodo.hiframes.pd_series_ext.get_series_data(S)\n'
    owv__kpf += '  index = bodo.hiframes.pd_series_ext.get_series_index(S)\n'
    owv__kpf += '  name = bodo.hiframes.pd_series_ext.get_series_name(S)\n'
    owv__kpf += '  l = len(arr)\n'
    owv__kpf += '  out_arr = bodo.libs.bool_arr_ext.alloc_bool_array(l)\n'
    if is_overload_true(regex):
        if is_regex_unsupported(pat) or flags:
            owv__kpf += """  out_arr = bodo.hiframes.series_str_impl.series_contains_regex(S, pat, case, flags, na, regex)
"""
        else:
            owv__kpf += """  get_search_regex(arr, case, bodo.libs.str_ext.unicode_to_utf8(pat), out_arr)
"""
    else:
        owv__kpf += '  numba.parfors.parfor.init_prange()\n'
        if is_overload_false(case):
            owv__kpf += '  upper_pat = pat.upper()\n'
        owv__kpf += '  for i in numba.parfors.parfor.internal_prange(l):\n'
        owv__kpf += '      if bodo.libs.array_kernels.isna(arr, i):\n'
        owv__kpf += '          bodo.libs.array_kernels.setna(out_arr, i)\n'
        owv__kpf += '      else: \n'
        if is_overload_true(case):
            owv__kpf += '          out_arr[i] = pat in arr[i]\n'
        else:
            owv__kpf += '          out_arr[i] = upper_pat in arr[i].upper()\n'
    owv__kpf += (
        '  return bodo.hiframes.pd_series_ext.init_series(out_arr, index, name)\n'
        )
    lfct__xryo = {}
    exec(owv__kpf, {'re': re, 'bodo': bodo, 'numba': numba, 'np': np,
        're_ignorecase_value': bnps__snk, 'get_search_regex':
        get_search_regex}, lfct__xryo)
    impl = lfct__xryo['impl']
    return impl


@overload_method(SeriesStrMethodType, 'cat', no_unliteral=True)
def overload_str_method_cat(S_str, others=None, sep=None, na_rep=None, join
    ='left'):
    if not isinstance(others, DataFrameType):
        raise_bodo_error(
            "Series.str.cat(): 'others' must be a DataFrame currently")
    if not is_overload_none(sep):
        str_arg_check('cat', 'sep', sep)
    if not is_overload_constant_str(join) or get_overload_const_str(join
        ) != 'left':
        raise_bodo_error("Series.str.cat(): 'join' not supported yet")
    owv__kpf = (
        "def impl(S_str, others=None, sep=None, na_rep=None, join='left'):\n")
    owv__kpf += '  S = S_str._obj\n'
    owv__kpf += '  arr = bodo.hiframes.pd_series_ext.get_series_data(S)\n'
    owv__kpf += '  index = bodo.hiframes.pd_series_ext.get_series_index(S)\n'
    owv__kpf += '  name = bodo.hiframes.pd_series_ext.get_series_name(S)\n'
    owv__kpf += '  l = len(arr)\n'
    for i in range(len(others.columns)):
        owv__kpf += (
            f'  data{i} = bodo.hiframes.pd_dataframe_ext.get_dataframe_data(others, {i})\n'
            )
    if S_str.stype.data == bodo.dict_str_arr_type and all(aeol__bzc == bodo
        .dict_str_arr_type for aeol__bzc in others.data):
        nyovr__pmjon = ', '.join(f'data{i}' for i in range(len(others.columns))
            )
        owv__kpf += (
            f'  out_arr = bodo.libs.dict_arr_ext.cat_dict_str((arr, {nyovr__pmjon}), sep)\n'
            )
    else:
        lxhyg__dygk = ' or '.join(['bodo.libs.array_kernels.isna(arr, i)'] +
            [f'bodo.libs.array_kernels.isna(data{i}, i)' for i in range(len
            (others.columns))])
        owv__kpf += (
            '  out_arr = bodo.libs.str_arr_ext.pre_alloc_string_array(l, -1)\n'
            )
        owv__kpf += '  numba.parfors.parfor.init_prange()\n'
        owv__kpf += '  for i in numba.parfors.parfor.internal_prange(l):\n'
        owv__kpf += f'      if {lxhyg__dygk}:\n'
        owv__kpf += '          bodo.libs.array_kernels.setna(out_arr, i)\n'
        owv__kpf += '          continue\n'
        qcn__uxabw = ', '.join(['arr[i]'] + [f'data{i}[i]' for i in range(
            len(others.columns))])
        fxy__weqrh = "''" if is_overload_none(sep) else 'sep'
        owv__kpf += f'      out_arr[i] = {fxy__weqrh}.join([{qcn__uxabw}])\n'
    owv__kpf += (
        '  return bodo.hiframes.pd_series_ext.init_series(out_arr, index, name)\n'
        )
    lfct__xryo = {}
    exec(owv__kpf, {'bodo': bodo, 'numba': numba}, lfct__xryo)
    impl = lfct__xryo['impl']
    return impl


@overload_method(SeriesStrMethodType, 'count', inline='always',
    no_unliteral=True)
def overload_str_method_count(S_str, pat, flags=0):
    str_arg_check('count', 'pat', pat)
    int_arg_check('count', 'flags', flags)

    def impl(S_str, pat, flags=0):
        S = S_str._obj
        mcd__kjqp = bodo.hiframes.pd_series_ext.get_series_data(S)
        xat__hfr = bodo.hiframes.pd_series_ext.get_series_name(S)
        dys__gqut = bodo.hiframes.pd_series_ext.get_series_index(S)
        suet__jzs = re.compile(pat, flags)
        numba.parfors.parfor.init_prange()
        tbp__lnss = len(mcd__kjqp)
        out_arr = bodo.libs.int_arr_ext.alloc_int_array(tbp__lnss, np.int64)
        for i in numba.parfors.parfor.internal_prange(tbp__lnss):
            if bodo.libs.array_kernels.isna(mcd__kjqp, i):
                bodo.libs.array_kernels.setna(out_arr, i)
            else:
                out_arr[i] = str_findall_count(suet__jzs, mcd__kjqp[i])
        return bodo.hiframes.pd_series_ext.init_series(out_arr, dys__gqut,
            xat__hfr)
    return impl


@overload_method(SeriesStrMethodType, 'find', inline='always', no_unliteral
    =True)
def overload_str_method_find(S_str, sub, start=0, end=None):
    str_arg_check('find', 'sub', sub)
    int_arg_check('find', 'start', start)
    if not is_overload_none(end):
        int_arg_check('find', 'end', end)

    def impl(S_str, sub, start=0, end=None):
        S = S_str._obj
        mcd__kjqp = bodo.hiframes.pd_series_ext.get_series_data(S)
        xat__hfr = bodo.hiframes.pd_series_ext.get_series_name(S)
        dys__gqut = bodo.hiframes.pd_series_ext.get_series_index(S)
        numba.parfors.parfor.init_prange()
        tbp__lnss = len(mcd__kjqp)
        out_arr = bodo.libs.int_arr_ext.alloc_int_array(tbp__lnss, np.int64)
        for i in numba.parfors.parfor.internal_prange(tbp__lnss):
            if bodo.libs.array_kernels.isna(mcd__kjqp, i):
                bodo.libs.array_kernels.setna(out_arr, i)
            else:
                out_arr[i] = mcd__kjqp[i].find(sub, start, end)
        return bodo.hiframes.pd_series_ext.init_series(out_arr, dys__gqut,
            xat__hfr)
    return impl


@overload_method(SeriesStrMethodType, 'rfind', inline='always',
    no_unliteral=True)
def overload_str_method_rfind(S_str, sub, start=0, end=None):
    str_arg_check('rfind', 'sub', sub)
    if start != 0:
        int_arg_check('rfind', 'start', start)
    if not is_overload_none(end):
        int_arg_check('rfind', 'end', end)

    def impl(S_str, sub, start=0, end=None):
        S = S_str._obj
        mcd__kjqp = bodo.hiframes.pd_series_ext.get_series_data(S)
        xat__hfr = bodo.hiframes.pd_series_ext.get_series_name(S)
        dys__gqut = bodo.hiframes.pd_series_ext.get_series_index(S)
        numba.parfors.parfor.init_prange()
        tbp__lnss = len(mcd__kjqp)
        out_arr = bodo.libs.int_arr_ext.alloc_int_array(tbp__lnss, np.int64)
        for i in numba.parfors.parfor.internal_prange(tbp__lnss):
            if bodo.libs.array_kernels.isna(mcd__kjqp, i):
                bodo.libs.array_kernels.setna(out_arr, i)
            else:
                out_arr[i] = mcd__kjqp[i].rfind(sub, start, end)
        return bodo.hiframes.pd_series_ext.init_series(out_arr, dys__gqut,
            xat__hfr)
    return impl


@overload_method(SeriesStrMethodType, 'center', inline='always',
    no_unliteral=True)
def overload_str_method_center(S_str, width, fillchar=' '):
    common_validate_padding('center', width, fillchar)

    def impl(S_str, width, fillchar=' '):
        S = S_str._obj
        mcd__kjqp = bodo.hiframes.pd_series_ext.get_series_data(S)
        xat__hfr = bodo.hiframes.pd_series_ext.get_series_name(S)
        dys__gqut = bodo.hiframes.pd_series_ext.get_series_index(S)
        numba.parfors.parfor.init_prange()
        tbp__lnss = len(mcd__kjqp)
        out_arr = bodo.libs.str_arr_ext.pre_alloc_string_array(tbp__lnss, -1)
        for nrigc__ifu in numba.parfors.parfor.internal_prange(tbp__lnss):
            if bodo.libs.array_kernels.isna(mcd__kjqp, nrigc__ifu):
                out_arr[nrigc__ifu] = ''
                bodo.libs.array_kernels.setna(out_arr, nrigc__ifu)
            else:
                out_arr[nrigc__ifu] = mcd__kjqp[nrigc__ifu].center(width,
                    fillchar)
        return bodo.hiframes.pd_series_ext.init_series(out_arr, dys__gqut,
            xat__hfr)
    return impl


@overload_method(SeriesStrMethodType, 'slice_replace', inline='always',
    no_unliteral=True)
def overload_str_method_slice_replace(S_str, start=0, stop=None, repl=''):
    int_arg_check('slice_replace', 'start', start)
    if not is_overload_none(stop):
        int_arg_check('slice_replace', 'stop', stop)
    str_arg_check('slice_replace', 'repl', repl)

    def impl(S_str, start=0, stop=None, repl=''):
        S = S_str._obj
        mcd__kjqp = bodo.hiframes.pd_series_ext.get_series_data(S)
        xat__hfr = bodo.hiframes.pd_series_ext.get_series_name(S)
        dys__gqut = bodo.hiframes.pd_series_ext.get_series_index(S)
        numba.parfors.parfor.init_prange()
        tbp__lnss = len(mcd__kjqp)
        out_arr = bodo.libs.str_arr_ext.pre_alloc_string_array(tbp__lnss, -1)
        for nrigc__ifu in numba.parfors.parfor.internal_prange(tbp__lnss):
            if bodo.libs.array_kernels.isna(mcd__kjqp, nrigc__ifu):
                bodo.libs.array_kernels.setna(out_arr, nrigc__ifu)
            else:
                if stop is not None:
                    bhlre__xdahv = mcd__kjqp[nrigc__ifu][stop:]
                else:
                    bhlre__xdahv = ''
                out_arr[nrigc__ifu] = mcd__kjqp[nrigc__ifu][:start
                    ] + repl + bhlre__xdahv
        return bodo.hiframes.pd_series_ext.init_series(out_arr, dys__gqut,
            xat__hfr)
    return impl


@overload_method(SeriesStrMethodType, 'repeat', inline='always',
    no_unliteral=True)
def overload_str_method_repeat(S_str, repeats):
    if isinstance(repeats, types.Integer) or is_overload_constant_int(repeats):

        def impl(S_str, repeats):
            S = S_str._obj
            mcd__kjqp = bodo.hiframes.pd_series_ext.get_series_data(S)
            xat__hfr = bodo.hiframes.pd_series_ext.get_series_name(S)
            dys__gqut = bodo.hiframes.pd_series_ext.get_series_index(S)
            numba.parfors.parfor.init_prange()
            tbp__lnss = len(mcd__kjqp)
            out_arr = bodo.libs.str_arr_ext.pre_alloc_string_array(tbp__lnss,
                -1)
            for nrigc__ifu in numba.parfors.parfor.internal_prange(tbp__lnss):
                if bodo.libs.array_kernels.isna(mcd__kjqp, nrigc__ifu):
                    bodo.libs.array_kernels.setna(out_arr, nrigc__ifu)
                else:
                    out_arr[nrigc__ifu] = mcd__kjqp[nrigc__ifu] * repeats
            return bodo.hiframes.pd_series_ext.init_series(out_arr,
                dys__gqut, xat__hfr)
        return impl
    elif is_overload_constant_list(repeats):
        kwvyj__bkxll = get_overload_const_list(repeats)
        qudyc__oiqi = all([isinstance(ibk__hxa, int) for ibk__hxa in
            kwvyj__bkxll])
    elif is_list_like_index_type(repeats) and isinstance(repeats.dtype,
        types.Integer):
        qudyc__oiqi = True
    else:
        qudyc__oiqi = False
    if qudyc__oiqi:

        def impl(S_str, repeats):
            S = S_str._obj
            mcd__kjqp = bodo.hiframes.pd_series_ext.get_series_data(S)
            xat__hfr = bodo.hiframes.pd_series_ext.get_series_name(S)
            dys__gqut = bodo.hiframes.pd_series_ext.get_series_index(S)
            muijw__jkjap = bodo.utils.conversion.coerce_to_array(repeats)
            numba.parfors.parfor.init_prange()
            tbp__lnss = len(mcd__kjqp)
            out_arr = bodo.libs.str_arr_ext.pre_alloc_string_array(tbp__lnss,
                -1)
            for nrigc__ifu in numba.parfors.parfor.internal_prange(tbp__lnss):
                if bodo.libs.array_kernels.isna(mcd__kjqp, nrigc__ifu):
                    bodo.libs.array_kernels.setna(out_arr, nrigc__ifu)
                else:
                    out_arr[nrigc__ifu] = mcd__kjqp[nrigc__ifu] * muijw__jkjap[
                        nrigc__ifu]
            return bodo.hiframes.pd_series_ext.init_series(out_arr,
                dys__gqut, xat__hfr)
        return impl
    else:
        raise BodoError(
            'Series.str.repeat(): repeats argument must either be an integer or a sequence of integers'
            )


@overload_method(SeriesStrMethodType, 'ljust', inline='always',
    no_unliteral=True)
def overload_str_method_ljust(S_str, width, fillchar=' '):
    common_validate_padding('ljust', width, fillchar)

    def impl(S_str, width, fillchar=' '):
        S = S_str._obj
        mcd__kjqp = bodo.hiframes.pd_series_ext.get_series_data(S)
        xat__hfr = bodo.hiframes.pd_series_ext.get_series_name(S)
        dys__gqut = bodo.hiframes.pd_series_ext.get_series_index(S)
        numba.parfors.parfor.init_prange()
        tbp__lnss = len(mcd__kjqp)
        out_arr = bodo.libs.str_arr_ext.pre_alloc_string_array(tbp__lnss, -1)
        for nrigc__ifu in numba.parfors.parfor.internal_prange(tbp__lnss):
            if bodo.libs.array_kernels.isna(mcd__kjqp, nrigc__ifu):
                out_arr[nrigc__ifu] = ''
                bodo.libs.array_kernels.setna(out_arr, nrigc__ifu)
            else:
                out_arr[nrigc__ifu] = mcd__kjqp[nrigc__ifu].ljust(width,
                    fillchar)
        return bodo.hiframes.pd_series_ext.init_series(out_arr, dys__gqut,
            xat__hfr)
    return impl


@overload_method(SeriesStrMethodType, 'rjust', inline='always',
    no_unliteral=True)
def overload_str_method_rjust(S_str, width, fillchar=' '):
    common_validate_padding('rjust', width, fillchar)

    def impl(S_str, width, fillchar=' '):
        S = S_str._obj
        mcd__kjqp = bodo.hiframes.pd_series_ext.get_series_data(S)
        xat__hfr = bodo.hiframes.pd_series_ext.get_series_name(S)
        dys__gqut = bodo.hiframes.pd_series_ext.get_series_index(S)
        numba.parfors.parfor.init_prange()
        tbp__lnss = len(mcd__kjqp)
        out_arr = bodo.libs.str_arr_ext.pre_alloc_string_array(tbp__lnss, -1)
        for nrigc__ifu in numba.parfors.parfor.internal_prange(tbp__lnss):
            if bodo.libs.array_kernels.isna(mcd__kjqp, nrigc__ifu):
                out_arr[nrigc__ifu] = ''
                bodo.libs.array_kernels.setna(out_arr, nrigc__ifu)
            else:
                out_arr[nrigc__ifu] = mcd__kjqp[nrigc__ifu].rjust(width,
                    fillchar)
        return bodo.hiframes.pd_series_ext.init_series(out_arr, dys__gqut,
            xat__hfr)
    return impl


@overload_method(SeriesStrMethodType, 'pad', no_unliteral=True)
def overload_str_method_pad(S_str, width, side='left', fillchar=' '):
    common_validate_padding('pad', width, fillchar)
    if is_overload_constant_str(side):
        if get_overload_const_str(side) not in ['left', 'right', 'both']:
            raise BodoError('Series.str.pad(): Invalid Side')
    else:
        raise BodoError('Series.str.pad(): Invalid Side')

    def impl(S_str, width, side='left', fillchar=' '):
        S = S_str._obj
        mcd__kjqp = bodo.hiframes.pd_series_ext.get_series_data(S)
        xat__hfr = bodo.hiframes.pd_series_ext.get_series_name(S)
        dys__gqut = bodo.hiframes.pd_series_ext.get_series_index(S)
        numba.parfors.parfor.init_prange()
        tbp__lnss = len(mcd__kjqp)
        out_arr = bodo.libs.str_arr_ext.pre_alloc_string_array(tbp__lnss, -1)
        for nrigc__ifu in numba.parfors.parfor.internal_prange(tbp__lnss):
            if bodo.libs.array_kernels.isna(mcd__kjqp, nrigc__ifu):
                out_arr[nrigc__ifu] = ''
                bodo.libs.array_kernels.setna(out_arr, nrigc__ifu)
            elif side == 'left':
                out_arr[nrigc__ifu] = mcd__kjqp[nrigc__ifu].rjust(width,
                    fillchar)
            elif side == 'right':
                out_arr[nrigc__ifu] = mcd__kjqp[nrigc__ifu].ljust(width,
                    fillchar)
            elif side == 'both':
                out_arr[nrigc__ifu] = mcd__kjqp[nrigc__ifu].center(width,
                    fillchar)
        return bodo.hiframes.pd_series_ext.init_series(out_arr, dys__gqut,
            xat__hfr)
    return impl


@overload_method(SeriesStrMethodType, 'zfill', inline='always',
    no_unliteral=True)
def overload_str_method_zfill(S_str, width):
    int_arg_check('zfill', 'width', width)

    def impl(S_str, width):
        S = S_str._obj
        mcd__kjqp = bodo.hiframes.pd_series_ext.get_series_data(S)
        xat__hfr = bodo.hiframes.pd_series_ext.get_series_name(S)
        dys__gqut = bodo.hiframes.pd_series_ext.get_series_index(S)
        numba.parfors.parfor.init_prange()
        tbp__lnss = len(mcd__kjqp)
        out_arr = bodo.libs.str_arr_ext.pre_alloc_string_array(tbp__lnss, -1)
        for nrigc__ifu in numba.parfors.parfor.internal_prange(tbp__lnss):
            if bodo.libs.array_kernels.isna(mcd__kjqp, nrigc__ifu):
                out_arr[nrigc__ifu] = ''
                bodo.libs.array_kernels.setna(out_arr, nrigc__ifu)
            else:
                out_arr[nrigc__ifu] = mcd__kjqp[nrigc__ifu].zfill(width)
        return bodo.hiframes.pd_series_ext.init_series(out_arr, dys__gqut,
            xat__hfr)
    return impl


@overload_method(SeriesStrMethodType, 'slice', no_unliteral=True)
def overload_str_method_slice(S_str, start=None, stop=None, step=None):
    if not is_overload_none(start):
        int_arg_check('slice', 'start', start)
    if not is_overload_none(stop):
        int_arg_check('slice', 'stop', stop)
    if not is_overload_none(step):
        int_arg_check('slice', 'step', step)

    def impl(S_str, start=None, stop=None, step=None):
        S = S_str._obj
        mcd__kjqp = bodo.hiframes.pd_series_ext.get_series_data(S)
        xat__hfr = bodo.hiframes.pd_series_ext.get_series_name(S)
        dys__gqut = bodo.hiframes.pd_series_ext.get_series_index(S)
        numba.parfors.parfor.init_prange()
        tbp__lnss = len(mcd__kjqp)
        out_arr = bodo.libs.str_arr_ext.pre_alloc_string_array(tbp__lnss, -1)
        for nrigc__ifu in numba.parfors.parfor.internal_prange(tbp__lnss):
            if bodo.libs.array_kernels.isna(mcd__kjqp, nrigc__ifu):
                out_arr[nrigc__ifu] = ''
                bodo.libs.array_kernels.setna(out_arr, nrigc__ifu)
            else:
                out_arr[nrigc__ifu] = mcd__kjqp[nrigc__ifu][start:stop:step]
        return bodo.hiframes.pd_series_ext.init_series(out_arr, dys__gqut,
            xat__hfr)
    return impl


@overload_method(SeriesStrMethodType, 'startswith', inline='always',
    no_unliteral=True)
def overload_str_method_startswith(S_str, pat, na=np.nan):
    not_supported_arg_check('startswith', 'na', na, np.nan)
    str_arg_check('startswith', 'pat', pat)

    def impl(S_str, pat, na=np.nan):
        S = S_str._obj
        mcd__kjqp = bodo.hiframes.pd_series_ext.get_series_data(S)
        xat__hfr = bodo.hiframes.pd_series_ext.get_series_name(S)
        dys__gqut = bodo.hiframes.pd_series_ext.get_series_index(S)
        numba.parfors.parfor.init_prange()
        tbp__lnss = len(mcd__kjqp)
        out_arr = bodo.libs.bool_arr_ext.alloc_bool_array(tbp__lnss)
        for i in numba.parfors.parfor.internal_prange(tbp__lnss):
            if bodo.libs.array_kernels.isna(mcd__kjqp, i):
                bodo.libs.array_kernels.setna(out_arr, i)
            else:
                out_arr[i] = mcd__kjqp[i].startswith(pat)
        return bodo.hiframes.pd_series_ext.init_series(out_arr, dys__gqut,
            xat__hfr)
    return impl


@overload_method(SeriesStrMethodType, 'endswith', inline='always',
    no_unliteral=True)
def overload_str_method_endswith(S_str, pat, na=np.nan):
    not_supported_arg_check('endswith', 'na', na, np.nan)
    str_arg_check('endswith', 'pat', pat)

    def impl(S_str, pat, na=np.nan):
        S = S_str._obj
        mcd__kjqp = bodo.hiframes.pd_series_ext.get_series_data(S)
        xat__hfr = bodo.hiframes.pd_series_ext.get_series_name(S)
        dys__gqut = bodo.hiframes.pd_series_ext.get_series_index(S)
        numba.parfors.parfor.init_prange()
        tbp__lnss = len(mcd__kjqp)
        out_arr = bodo.libs.bool_arr_ext.alloc_bool_array(tbp__lnss)
        for i in numba.parfors.parfor.internal_prange(tbp__lnss):
            if bodo.libs.array_kernels.isna(mcd__kjqp, i):
                bodo.libs.array_kernels.setna(out_arr, i)
            else:
                out_arr[i] = mcd__kjqp[i].endswith(pat)
        return bodo.hiframes.pd_series_ext.init_series(out_arr, dys__gqut,
            xat__hfr)
    return impl


@overload(operator.getitem, no_unliteral=True)
def overload_str_method_getitem(S_str, ind):
    if not isinstance(S_str, SeriesStrMethodType):
        return
    if not isinstance(types.unliteral(ind), (types.SliceType, types.Integer)):
        raise BodoError(
            'index input to Series.str[] should be a slice or an integer')
    if isinstance(ind, types.SliceType):
        return lambda S_str, ind: S_str.slice(ind.start, ind.stop, ind.step)
    if isinstance(types.unliteral(ind), types.Integer):
        return lambda S_str, ind: S_str.get(ind)


@overload_method(SeriesStrMethodType, 'extract', inline='always',
    no_unliteral=True)
def overload_str_method_extract(S_str, pat, flags=0, expand=True):
    if not is_overload_constant_bool(expand):
        raise BodoError(
            "Series.str.extract(): 'expand' argument should be a constant bool"
            )
    dhra__wcttl, regex = _get_column_names_from_regex(pat, flags, 'extract')
    mogfv__wutj = len(dhra__wcttl)
    owv__kpf = 'def impl(S_str, pat, flags=0, expand=True):\n'
    owv__kpf += '  regex = re.compile(pat, flags=flags)\n'
    owv__kpf += '  S = S_str._obj\n'
    owv__kpf += '  str_arr = bodo.hiframes.pd_series_ext.get_series_data(S)\n'
    owv__kpf += '  index = bodo.hiframes.pd_series_ext.get_series_index(S)\n'
    owv__kpf += '  name = bodo.hiframes.pd_series_ext.get_series_name(S)\n'
    owv__kpf += '  numba.parfors.parfor.init_prange()\n'
    owv__kpf += '  n = len(str_arr)\n'
    for i in range(mogfv__wutj):
        owv__kpf += (
            '  out_arr_{0} = bodo.libs.str_arr_ext.pre_alloc_string_array(n, -1)\n'
            .format(i))
    owv__kpf += '  for j in numba.parfors.parfor.internal_prange(n):\n'
    owv__kpf += '      if bodo.libs.array_kernels.isna(str_arr, j):\n'
    for i in range(mogfv__wutj):
        owv__kpf += "          out_arr_{}[j] = ''\n".format(i)
        owv__kpf += ('          bodo.libs.array_kernels.setna(out_arr_{}, j)\n'
            .format(i))
    owv__kpf += '      else:\n'
    owv__kpf += '          m = regex.search(str_arr[j])\n'
    owv__kpf += '          if m:\n'
    owv__kpf += '            g = m.groups()\n'
    for i in range(mogfv__wutj):
        owv__kpf += '            out_arr_{0}[j] = g[{0}]\n'.format(i)
    owv__kpf += '          else:\n'
    for i in range(mogfv__wutj):
        owv__kpf += "            out_arr_{}[j] = ''\n".format(i)
        owv__kpf += (
            '            bodo.libs.array_kernels.setna(out_arr_{}, j)\n'.
            format(i))
    if is_overload_false(expand) and regex.groups == 1:
        xat__hfr = "'{}'".format(list(regex.groupindex.keys()).pop()) if len(
            regex.groupindex.keys()) > 0 else 'name'
        owv__kpf += (
            '  return bodo.hiframes.pd_series_ext.init_series(out_arr_0, index, {})\n'
            .format(xat__hfr))
        lfct__xryo = {}
        exec(owv__kpf, {'re': re, 'bodo': bodo, 'numba': numba,
            'get_utf8_size': get_utf8_size}, lfct__xryo)
        impl = lfct__xryo['impl']
        return impl
    inb__ihm = ', '.join('out_arr_{}'.format(i) for i in range(mogfv__wutj))
    impl = bodo.hiframes.dataframe_impl._gen_init_df(owv__kpf, dhra__wcttl,
        inb__ihm, 'index', extra_globals={'get_utf8_size': get_utf8_size,
        're': re})
    return impl


@overload_method(SeriesStrMethodType, 'extractall', inline='always',
    no_unliteral=True)
def overload_str_method_extractall(S_str, pat, flags=0):
    dhra__wcttl, tvo__gql = _get_column_names_from_regex(pat, flags,
        'extractall')
    mogfv__wutj = len(dhra__wcttl)
    plz__gbh = isinstance(S_str.stype.index, StringIndexType)
    owv__kpf = 'def impl(S_str, pat, flags=0):\n'
    owv__kpf += '  regex = re.compile(pat, flags=flags)\n'
    owv__kpf += '  S = S_str._obj\n'
    owv__kpf += '  str_arr = bodo.hiframes.pd_series_ext.get_series_data(S)\n'
    owv__kpf += '  index = bodo.hiframes.pd_series_ext.get_series_index(S)\n'
    owv__kpf += '  name = bodo.hiframes.pd_series_ext.get_series_name(S)\n'
    owv__kpf += '  index_arr = bodo.utils.conversion.index_to_array(index)\n'
    owv__kpf += (
        '  index_name = bodo.hiframes.pd_index_ext.get_index_name(index)\n')
    owv__kpf += '  numba.parfors.parfor.init_prange()\n'
    owv__kpf += '  n = len(str_arr)\n'
    owv__kpf += '  out_n_l = [0]\n'
    for i in range(mogfv__wutj):
        owv__kpf += '  num_chars_{} = 0\n'.format(i)
    if plz__gbh:
        owv__kpf += '  index_num_chars = 0\n'
    owv__kpf += '  for i in numba.parfors.parfor.internal_prange(n):\n'
    if plz__gbh:
        owv__kpf += '      index_num_chars += get_utf8_size(index_arr[i])\n'
    owv__kpf += '      if bodo.libs.array_kernels.isna(str_arr, i):\n'
    owv__kpf += '          continue\n'
    owv__kpf += '      m = regex.findall(str_arr[i])\n'
    owv__kpf += '      out_n_l[0] += len(m)\n'
    for i in range(mogfv__wutj):
        owv__kpf += '      l_{} = 0\n'.format(i)
    owv__kpf += '      for s in m:\n'
    for i in range(mogfv__wutj):
        owv__kpf += '        l_{} += get_utf8_size(s{})\n'.format(i, '[{}]'
            .format(i) if mogfv__wutj > 1 else '')
    for i in range(mogfv__wutj):
        owv__kpf += '      num_chars_{0} += l_{0}\n'.format(i)
    owv__kpf += (
        '  out_n = bodo.libs.distributed_api.local_alloc_size(out_n_l[0], str_arr)\n'
        )
    for i in range(mogfv__wutj):
        owv__kpf += (
            """  out_arr_{0} = bodo.libs.str_arr_ext.pre_alloc_string_array(out_n, num_chars_{0})
"""
            .format(i))
    if plz__gbh:
        owv__kpf += """  out_ind_arr = bodo.libs.str_arr_ext.pre_alloc_string_array(out_n, index_num_chars)
"""
    else:
        owv__kpf += '  out_ind_arr = np.empty(out_n, index_arr.dtype)\n'
    owv__kpf += '  out_match_arr = np.empty(out_n, np.int64)\n'
    owv__kpf += '  out_ind = 0\n'
    owv__kpf += '  for j in numba.parfors.parfor.internal_prange(n):\n'
    owv__kpf += '      if bodo.libs.array_kernels.isna(str_arr, j):\n'
    owv__kpf += '          continue\n'
    owv__kpf += '      m = regex.findall(str_arr[j])\n'
    owv__kpf += '      for k, s in enumerate(m):\n'
    for i in range(mogfv__wutj):
        owv__kpf += (
            '        bodo.libs.distributed_api.set_arr_local(out_arr_{}, out_ind, s{})\n'
            .format(i, '[{}]'.format(i) if mogfv__wutj > 1 else ''))
    owv__kpf += """        bodo.libs.distributed_api.set_arr_local(out_ind_arr, out_ind, index_arr[j])
"""
    owv__kpf += (
        '        bodo.libs.distributed_api.set_arr_local(out_match_arr, out_ind, k)\n'
        )
    owv__kpf += '        out_ind += 1\n'
    owv__kpf += (
        '  out_index = bodo.hiframes.pd_multi_index_ext.init_multi_index(\n')
    owv__kpf += "    (out_ind_arr, out_match_arr), (index_name, 'match'))\n"
    inb__ihm = ', '.join('out_arr_{}'.format(i) for i in range(mogfv__wutj))
    impl = bodo.hiframes.dataframe_impl._gen_init_df(owv__kpf, dhra__wcttl,
        inb__ihm, 'out_index', extra_globals={'get_utf8_size':
        get_utf8_size, 're': re})
    return impl


def _get_column_names_from_regex(pat, flags, func_name):
    if not is_overload_constant_str(pat):
        raise BodoError(
            "Series.str.{}(): 'pat' argument should be a constant string".
            format(func_name))
    if not is_overload_constant_int(flags):
        raise BodoError(
            "Series.str.{}(): 'flags' argument should be a constant int".
            format(func_name))
    pat = get_overload_const_str(pat)
    flags = get_overload_const_int(flags)
    regex = re.compile(pat, flags=flags)
    if regex.groups == 0:
        raise BodoError(
            'Series.str.{}(): pattern {} contains no capture groups'.format
            (func_name, pat))
    lhmn__zehs = dict(zip(regex.groupindex.values(), regex.groupindex.keys()))
    dhra__wcttl = [lhmn__zehs.get(1 + i, i) for i in range(regex.groups)]
    return dhra__wcttl, regex


def create_str2str_methods_overload(func_name):
    if func_name in ['lstrip', 'rstrip', 'strip']:
        owv__kpf = 'def f(S_str, to_strip=None):\n'
    else:
        owv__kpf = 'def f(S_str):\n'
    owv__kpf += '    S = S_str._obj\n'
    owv__kpf += (
        '    str_arr = bodo.hiframes.pd_series_ext.get_series_data(S)\n')
    owv__kpf += '    str_arr = decode_if_dict_array(str_arr)\n'
    owv__kpf += '    index = bodo.hiframes.pd_series_ext.get_series_index(S)\n'
    owv__kpf += '    name = bodo.hiframes.pd_series_ext.get_series_name(S)\n'
    owv__kpf += '    numba.parfors.parfor.init_prange()\n'
    owv__kpf += '    n = len(str_arr)\n'
    if func_name in ('capitalize', 'lower', 'swapcase', 'title', 'upper'):
        owv__kpf += '    num_chars = num_total_chars(str_arr)\n'
    else:
        owv__kpf += '    num_chars = -1\n'
    owv__kpf += (
        '    out_arr = bodo.libs.str_arr_ext.pre_alloc_string_array(n, num_chars)\n'
        )
    owv__kpf += '    for j in numba.parfors.parfor.internal_prange(n):\n'
    owv__kpf += '        if bodo.libs.array_kernels.isna(str_arr, j):\n'
    owv__kpf += '            out_arr[j] = ""\n'
    owv__kpf += '            bodo.libs.array_kernels.setna(out_arr, j)\n'
    owv__kpf += '        else:\n'
    if func_name in ['lstrip', 'rstrip', 'strip']:
        owv__kpf += ('            out_arr[j] = str_arr[j].{}(to_strip)\n'.
            format(func_name))
    else:
        owv__kpf += '            out_arr[j] = str_arr[j].{}()\n'.format(
            func_name)
    owv__kpf += (
        '    return bodo.hiframes.pd_series_ext.init_series(out_arr, index, name)\n'
        )
    lfct__xryo = {}
    exec(owv__kpf, {'bodo': bodo, 'numba': numba, 'num_total_chars': bodo.
        libs.str_arr_ext.num_total_chars, 'get_utf8_size': bodo.libs.
        str_arr_ext.get_utf8_size, 'decode_if_dict_array': bodo.utils.
        typing.decode_if_dict_array}, lfct__xryo)
    qsqxh__sfwtk = lfct__xryo['f']
    if func_name in ['lstrip', 'rstrip', 'strip']:

        def overload_strip_method(S_str, to_strip=None):
            if not is_overload_none(to_strip):
                str_arg_check(func_name, 'to_strip', to_strip)
            return qsqxh__sfwtk
        return overload_strip_method
    else:

        def overload_str2str_methods(S_str):
            return qsqxh__sfwtk
        return overload_str2str_methods


def create_str2bool_methods_overload(func_name):

    def overload_str2bool_methods(S_str):
        owv__kpf = 'def f(S_str):\n'
        owv__kpf += '    S = S_str._obj\n'
        owv__kpf += (
            '    str_arr = bodo.hiframes.pd_series_ext.get_series_data(S)\n')
        owv__kpf += (
            '    index = bodo.hiframes.pd_series_ext.get_series_index(S)\n')
        owv__kpf += (
            '    name = bodo.hiframes.pd_series_ext.get_series_name(S)\n')
        owv__kpf += '    numba.parfors.parfor.init_prange()\n'
        owv__kpf += '    l = len(str_arr)\n'
        owv__kpf += (
            '    out_arr = bodo.libs.bool_arr_ext.alloc_bool_array(l)\n')
        owv__kpf += '    for i in numba.parfors.parfor.internal_prange(l):\n'
        owv__kpf += '        if bodo.libs.array_kernels.isna(str_arr, i):\n'
        owv__kpf += '            bodo.libs.array_kernels.setna(out_arr, i)\n'
        owv__kpf += '        else:\n'
        owv__kpf += ('            out_arr[i] = np.bool_(str_arr[i].{}())\n'
            .format(func_name))
        owv__kpf += '    return bodo.hiframes.pd_series_ext.init_series(\n'
        owv__kpf += '      out_arr,index, name)\n'
        lfct__xryo = {}
        exec(owv__kpf, {'bodo': bodo, 'numba': numba, 'np': np}, lfct__xryo)
        qsqxh__sfwtk = lfct__xryo['f']
        return qsqxh__sfwtk
    return overload_str2bool_methods


def _install_str2str_methods():
    for nwz__yfl in bodo.hiframes.pd_series_ext.str2str_methods:
        vhgi__hjht = create_str2str_methods_overload(nwz__yfl)
        overload_method(SeriesStrMethodType, nwz__yfl, inline='always',
            no_unliteral=True)(vhgi__hjht)


def _install_str2bool_methods():
    for nwz__yfl in bodo.hiframes.pd_series_ext.str2bool_methods:
        vhgi__hjht = create_str2bool_methods_overload(nwz__yfl)
        overload_method(SeriesStrMethodType, nwz__yfl, inline='always',
            no_unliteral=True)(vhgi__hjht)


_install_str2str_methods()
_install_str2bool_methods()


@overload_attribute(SeriesType, 'cat')
def overload_series_cat(s):
    if not isinstance(s.dtype, bodo.hiframes.pd_categorical_ext.
        PDCategoricalDtype):
        raise BodoError('Can only use .cat accessor with categorical values.')
    return lambda s: bodo.hiframes.series_str_impl.init_series_cat_method(s)


class SeriesCatMethodType(types.Type):

    def __init__(self, stype):
        self.stype = stype
        xat__hfr = 'SeriesCatMethodType({})'.format(stype)
        super(SeriesCatMethodType, self).__init__(xat__hfr)

    @property
    def mangling_args(self):
        return self.__class__.__name__, (self._code,)


@register_model(SeriesCatMethodType)
class SeriesCatModel(models.StructModel):

    def __init__(self, dmm, fe_type):
        fqkfl__xth = [('obj', fe_type.stype)]
        super(SeriesCatModel, self).__init__(dmm, fe_type, fqkfl__xth)


make_attribute_wrapper(SeriesCatMethodType, 'obj', '_obj')


@intrinsic
def init_series_cat_method(typingctx, obj=None):

    def codegen(context, builder, signature, args):
        pnr__fwd, = args
        pzb__quc = signature.return_type
        zio__upksx = cgutils.create_struct_proxy(pzb__quc)(context, builder)
        zio__upksx.obj = pnr__fwd
        context.nrt.incref(builder, signature.args[0], pnr__fwd)
        return zio__upksx._getvalue()
    return SeriesCatMethodType(obj)(obj), codegen


@overload_attribute(SeriesCatMethodType, 'codes')
def series_cat_codes_overload(S_dt):

    def impl(S_dt):
        S = S_dt._obj
        qyjsm__fosvh = bodo.hiframes.pd_series_ext.get_series_data(S)
        dys__gqut = bodo.hiframes.pd_series_ext.get_series_index(S)
        xat__hfr = None
        return bodo.hiframes.pd_series_ext.init_series(bodo.hiframes.
            pd_categorical_ext.get_categorical_arr_codes(qyjsm__fosvh),
            dys__gqut, xat__hfr)
    return impl


unsupported_cat_attrs = {'categories', 'ordered'}
unsupported_cat_methods = {'rename_categories', 'reorder_categories',
    'add_categories', 'remove_categories', 'remove_unused_categories',
    'set_categories', 'as_ordered', 'as_unordered'}


def _install_catseries_unsupported():
    for pyhs__advo in unsupported_cat_attrs:
        blujb__ihxq = 'Series.cat.' + pyhs__advo
        overload_attribute(SeriesCatMethodType, pyhs__advo)(
            create_unsupported_overload(blujb__ihxq))
    for zox__hzaw in unsupported_cat_methods:
        blujb__ihxq = 'Series.cat.' + zox__hzaw
        overload_method(SeriesCatMethodType, zox__hzaw)(
            create_unsupported_overload(blujb__ihxq))


_install_catseries_unsupported()
unsupported_str_methods = {'casefold', 'decode', 'encode', 'findall',
    'fullmatch', 'index', 'match', 'normalize', 'partition', 'rindex',
    'rpartition', 'slice_replace', 'rsplit', 'translate', 'wrap', 'get_dummies'
    }


def _install_strseries_unsupported():
    for zox__hzaw in unsupported_str_methods:
        blujb__ihxq = 'Series.str.' + zox__hzaw
        overload_method(SeriesStrMethodType, zox__hzaw)(
            create_unsupported_overload(blujb__ihxq))


_install_strseries_unsupported()
