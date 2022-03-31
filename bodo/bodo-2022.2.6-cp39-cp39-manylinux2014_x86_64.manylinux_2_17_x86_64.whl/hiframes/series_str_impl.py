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
        bbzay__wle = 'SeriesStrMethodType({})'.format(stype)
        super(SeriesStrMethodType, self).__init__(bbzay__wle)


@register_model(SeriesStrMethodType)
class SeriesStrModel(models.StructModel):

    def __init__(self, dmm, fe_type):
        xbv__nrrc = [('obj', fe_type.stype)]
        super(SeriesStrModel, self).__init__(dmm, fe_type, xbv__nrrc)


make_attribute_wrapper(SeriesStrMethodType, 'obj', '_obj')


@intrinsic
def init_series_str_method(typingctx, obj=None):

    def codegen(context, builder, signature, args):
        crmz__asitc, = args
        cybv__edb = signature.return_type
        onsle__tztnb = cgutils.create_struct_proxy(cybv__edb)(context, builder)
        onsle__tztnb.obj = crmz__asitc
        context.nrt.incref(builder, signature.args[0], crmz__asitc)
        return onsle__tztnb._getvalue()
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
        wzgxc__oxy = bodo.hiframes.pd_series_ext.get_series_data(S)
        tksf__cmxlz = bodo.hiframes.pd_series_ext.get_series_index(S)
        bbzay__wle = bodo.hiframes.pd_series_ext.get_series_name(S)
        out_arr = bodo.libs.array_kernels.get_arr_lens(wzgxc__oxy, False)
        return bodo.hiframes.pd_series_ext.init_series(out_arr, tksf__cmxlz,
            bbzay__wle)
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
            wzgxc__oxy = bodo.hiframes.pd_series_ext.get_series_data(S)
            tksf__cmxlz = bodo.hiframes.pd_series_ext.get_series_index(S)
            bbzay__wle = bodo.hiframes.pd_series_ext.get_series_name(S)
            out_arr = bodo.hiframes.split_impl.compute_split_view(wzgxc__oxy,
                pat)
            return bodo.hiframes.pd_series_ext.init_series(out_arr,
                tksf__cmxlz, bbzay__wle)
        return _str_split_view_impl

    def _str_split_impl(S_str, pat=None, n=-1, expand=False):
        S = S_str._obj
        wzgxc__oxy = bodo.hiframes.pd_series_ext.get_series_data(S)
        tksf__cmxlz = bodo.hiframes.pd_series_ext.get_series_index(S)
        bbzay__wle = bodo.hiframes.pd_series_ext.get_series_name(S)
        out_arr = bodo.libs.str_ext.str_split(wzgxc__oxy, pat, n)
        return bodo.hiframes.pd_series_ext.init_series(out_arr, tksf__cmxlz,
            bbzay__wle)
    return _str_split_impl


@overload_method(SeriesStrMethodType, 'get', no_unliteral=True)
def overload_str_method_get(S_str, i):
    bwg__oemj = S_str.stype.data
    if (bwg__oemj != string_array_split_view_type and not is_str_arr_type(
        bwg__oemj)) and not isinstance(bwg__oemj, ArrayItemArrayType):
        raise_bodo_error(
            'Series.str.get(): only supports input type of Series(array(item)) and Series(str)'
            )
    int_arg_check('get', 'i', i)
    if isinstance(bwg__oemj, ArrayItemArrayType):

        def _str_get_array_impl(S_str, i):
            S = S_str._obj
            wzgxc__oxy = bodo.hiframes.pd_series_ext.get_series_data(S)
            tksf__cmxlz = bodo.hiframes.pd_series_ext.get_series_index(S)
            bbzay__wle = bodo.hiframes.pd_series_ext.get_series_name(S)
            out_arr = bodo.libs.array_kernels.get(wzgxc__oxy, i)
            return bodo.hiframes.pd_series_ext.init_series(out_arr,
                tksf__cmxlz, bbzay__wle)
        return _str_get_array_impl
    if bwg__oemj == string_array_split_view_type:

        def _str_get_split_impl(S_str, i):
            S = S_str._obj
            wzgxc__oxy = bodo.hiframes.pd_series_ext.get_series_data(S)
            tksf__cmxlz = bodo.hiframes.pd_series_ext.get_series_index(S)
            bbzay__wle = bodo.hiframes.pd_series_ext.get_series_name(S)
            numba.parfors.parfor.init_prange()
            n = len(wzgxc__oxy)
            czo__jdlr = 0
            for cdt__gphw in numba.parfors.parfor.internal_prange(n):
                pcd__acmsf, pcd__acmsf, mbqz__cwhl = get_split_view_index(
                    wzgxc__oxy, cdt__gphw, i)
                czo__jdlr += mbqz__cwhl
            numba.parfors.parfor.init_prange()
            out_arr = pre_alloc_string_array(n, czo__jdlr)
            for nql__zvhz in numba.parfors.parfor.internal_prange(n):
                ycmaa__bdyxb, khm__tsqvk, mbqz__cwhl = get_split_view_index(
                    wzgxc__oxy, nql__zvhz, i)
                if ycmaa__bdyxb == 0:
                    bodo.libs.array_kernels.setna(out_arr, nql__zvhz)
                    vgx__avc = get_split_view_data_ptr(wzgxc__oxy, 0)
                else:
                    bodo.libs.str_arr_ext.str_arr_set_not_na(out_arr, nql__zvhz
                        )
                    vgx__avc = get_split_view_data_ptr(wzgxc__oxy, khm__tsqvk)
                bodo.libs.str_arr_ext.setitem_str_arr_ptr(out_arr,
                    nql__zvhz, vgx__avc, mbqz__cwhl)
            return bodo.hiframes.pd_series_ext.init_series(out_arr,
                tksf__cmxlz, bbzay__wle)
        return _str_get_split_impl

    def _str_get_impl(S_str, i):
        S = S_str._obj
        wzgxc__oxy = bodo.hiframes.pd_series_ext.get_series_data(S)
        tksf__cmxlz = bodo.hiframes.pd_series_ext.get_series_index(S)
        bbzay__wle = bodo.hiframes.pd_series_ext.get_series_name(S)
        numba.parfors.parfor.init_prange()
        n = len(wzgxc__oxy)
        numba.parfors.parfor.init_prange()
        out_arr = pre_alloc_string_array(n, -1)
        for nql__zvhz in numba.parfors.parfor.internal_prange(n):
            if bodo.libs.array_kernels.isna(wzgxc__oxy, nql__zvhz) or not len(
                wzgxc__oxy[nql__zvhz]) > i >= -len(wzgxc__oxy[nql__zvhz]):
                out_arr[nql__zvhz] = ''
                bodo.libs.array_kernels.setna(out_arr, nql__zvhz)
            else:
                out_arr[nql__zvhz] = wzgxc__oxy[nql__zvhz][i]
        return bodo.hiframes.pd_series_ext.init_series(out_arr, tksf__cmxlz,
            bbzay__wle)
    return _str_get_impl


@overload_method(SeriesStrMethodType, 'join', inline='always', no_unliteral
    =True)
def overload_str_method_join(S_str, sep):
    bwg__oemj = S_str.stype.data
    if (bwg__oemj != string_array_split_view_type and bwg__oemj !=
        ArrayItemArrayType(string_array_type) and not is_str_arr_type(
        bwg__oemj)):
        raise_bodo_error(
            'Series.str.join(): only supports input type of Series(list(str)) and Series(str)'
            )
    str_arg_check('join', 'sep', sep)

    def impl(S_str, sep):
        S = S_str._obj
        yyohm__jtwf = bodo.hiframes.pd_series_ext.get_series_data(S)
        bbzay__wle = bodo.hiframes.pd_series_ext.get_series_name(S)
        tksf__cmxlz = bodo.hiframes.pd_series_ext.get_series_index(S)
        numba.parfors.parfor.init_prange()
        n = len(yyohm__jtwf)
        out_arr = bodo.libs.str_arr_ext.pre_alloc_string_array(n, -1)
        for nql__zvhz in numba.parfors.parfor.internal_prange(n):
            if bodo.libs.array_kernels.isna(yyohm__jtwf, nql__zvhz):
                out_arr[nql__zvhz] = ''
                bodo.libs.array_kernels.setna(out_arr, nql__zvhz)
            else:
                lll__tesh = yyohm__jtwf[nql__zvhz]
                out_arr[nql__zvhz] = sep.join(lll__tesh)
        return bodo.hiframes.pd_series_ext.init_series(out_arr, tksf__cmxlz,
            bbzay__wle)
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
            wzgxc__oxy = bodo.hiframes.pd_series_ext.get_series_data(S)
            tksf__cmxlz = bodo.hiframes.pd_series_ext.get_series_index(S)
            bbzay__wle = bodo.hiframes.pd_series_ext.get_series_name(S)
            out_arr = bodo.libs.dict_arr_ext.str_replace(wzgxc__oxy, pat,
                repl, flags, regex)
            return bodo.hiframes.pd_series_ext.init_series(out_arr,
                tksf__cmxlz, bbzay__wle)
        return _str_replace_dict_impl
    if is_overload_true(regex):

        def _str_replace_regex_impl(S_str, pat, repl, n=-1, case=None,
            flags=0, regex=True):
            S = S_str._obj
            wzgxc__oxy = bodo.hiframes.pd_series_ext.get_series_data(S)
            tksf__cmxlz = bodo.hiframes.pd_series_ext.get_series_index(S)
            bbzay__wle = bodo.hiframes.pd_series_ext.get_series_name(S)
            numba.parfors.parfor.init_prange()
            iuho__ongml = re.compile(pat, flags)
            qiq__mgu = len(wzgxc__oxy)
            out_arr = pre_alloc_string_array(qiq__mgu, -1)
            for nql__zvhz in numba.parfors.parfor.internal_prange(qiq__mgu):
                if bodo.libs.array_kernels.isna(wzgxc__oxy, nql__zvhz):
                    out_arr[nql__zvhz] = ''
                    bodo.libs.array_kernels.setna(out_arr, nql__zvhz)
                    continue
                out_arr[nql__zvhz] = iuho__ongml.sub(repl, wzgxc__oxy[
                    nql__zvhz])
            return bodo.hiframes.pd_series_ext.init_series(out_arr,
                tksf__cmxlz, bbzay__wle)
        return _str_replace_regex_impl
    if not is_overload_false(regex):
        raise BodoError('Series.str.replace(): regex argument should be bool')

    def _str_replace_noregex_impl(S_str, pat, repl, n=-1, case=None, flags=
        0, regex=True):
        S = S_str._obj
        wzgxc__oxy = bodo.hiframes.pd_series_ext.get_series_data(S)
        tksf__cmxlz = bodo.hiframes.pd_series_ext.get_series_index(S)
        bbzay__wle = bodo.hiframes.pd_series_ext.get_series_name(S)
        numba.parfors.parfor.init_prange()
        qiq__mgu = len(wzgxc__oxy)
        numba.parfors.parfor.init_prange()
        out_arr = pre_alloc_string_array(qiq__mgu, -1)
        for nql__zvhz in numba.parfors.parfor.internal_prange(qiq__mgu):
            if bodo.libs.array_kernels.isna(wzgxc__oxy, nql__zvhz):
                out_arr[nql__zvhz] = ''
                bodo.libs.array_kernels.setna(out_arr, nql__zvhz)
                continue
            out_arr[nql__zvhz] = wzgxc__oxy[nql__zvhz].replace(pat, repl)
        return bodo.hiframes.pd_series_ext.init_series(out_arr, tksf__cmxlz,
            bbzay__wle)
    return _str_replace_noregex_impl


@numba.njit
def series_contains_regex(S, pat, case, flags, na, regex):
    with numba.objmode(out_arr=bodo.boolean_array):
        out_arr = S.array._str_contains(pat, case, flags, na, regex)
    return out_arr


def is_regex_unsupported(pat):
    jfrq__uxchc = ['(?a', '(?i', '(?L', '(?m', '(?s', '(?u', '(?x', '(?#']
    if is_overload_constant_str(pat):
        if isinstance(pat, types.StringLiteral):
            pat = pat.literal_value
        return any([(eoz__toj in pat) for eoz__toj in jfrq__uxchc])
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
    fbn__ehppf = re.IGNORECASE.value
    mdc__xoxm = 'def impl(\n'
    mdc__xoxm += '    S_str, pat, case=True, flags=0, na=np.nan, regex=True\n'
    mdc__xoxm += '):\n'
    mdc__xoxm += '  S = S_str._obj\n'
    mdc__xoxm += '  arr = bodo.hiframes.pd_series_ext.get_series_data(S)\n'
    mdc__xoxm += '  index = bodo.hiframes.pd_series_ext.get_series_index(S)\n'
    mdc__xoxm += '  name = bodo.hiframes.pd_series_ext.get_series_name(S)\n'
    mdc__xoxm += '  l = len(arr)\n'
    mdc__xoxm += '  out_arr = bodo.libs.bool_arr_ext.alloc_bool_array(l)\n'
    if is_overload_true(regex):
        if is_regex_unsupported(pat) or flags:
            mdc__xoxm += """  out_arr = bodo.hiframes.series_str_impl.series_contains_regex(S, pat, case, flags, na, regex)
"""
        else:
            mdc__xoxm += """  get_search_regex(arr, case, bodo.libs.str_ext.unicode_to_utf8(pat), out_arr)
"""
    else:
        mdc__xoxm += '  numba.parfors.parfor.init_prange()\n'
        if is_overload_false(case):
            mdc__xoxm += '  upper_pat = pat.upper()\n'
        mdc__xoxm += '  for i in numba.parfors.parfor.internal_prange(l):\n'
        mdc__xoxm += '      if bodo.libs.array_kernels.isna(arr, i):\n'
        mdc__xoxm += '          bodo.libs.array_kernels.setna(out_arr, i)\n'
        mdc__xoxm += '      else: \n'
        if is_overload_true(case):
            mdc__xoxm += '          out_arr[i] = pat in arr[i]\n'
        else:
            mdc__xoxm += '          out_arr[i] = upper_pat in arr[i].upper()\n'
    mdc__xoxm += (
        '  return bodo.hiframes.pd_series_ext.init_series(out_arr, index, name)\n'
        )
    hklc__lmu = {}
    exec(mdc__xoxm, {'re': re, 'bodo': bodo, 'numba': numba, 'np': np,
        're_ignorecase_value': fbn__ehppf, 'get_search_regex':
        get_search_regex}, hklc__lmu)
    impl = hklc__lmu['impl']
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
    mdc__xoxm = (
        "def impl(S_str, others=None, sep=None, na_rep=None, join='left'):\n")
    mdc__xoxm += '  S = S_str._obj\n'
    mdc__xoxm += '  arr = bodo.hiframes.pd_series_ext.get_series_data(S)\n'
    mdc__xoxm += '  index = bodo.hiframes.pd_series_ext.get_series_index(S)\n'
    mdc__xoxm += '  name = bodo.hiframes.pd_series_ext.get_series_name(S)\n'
    mdc__xoxm += '  l = len(arr)\n'
    for i in range(len(others.columns)):
        mdc__xoxm += (
            f'  data{i} = bodo.hiframes.pd_dataframe_ext.get_dataframe_data(others, {i})\n'
            )
    if S_str.stype.data == bodo.dict_str_arr_type and all(hdx__cndm == bodo
        .dict_str_arr_type for hdx__cndm in others.data):
        kej__yqxdo = ', '.join(f'data{i}' for i in range(len(others.columns)))
        mdc__xoxm += (
            f'  out_arr = bodo.libs.dict_arr_ext.cat_dict_str((arr, {kej__yqxdo}), sep)\n'
            )
    else:
        zlxn__svvie = ' or '.join(['bodo.libs.array_kernels.isna(arr, i)'] +
            [f'bodo.libs.array_kernels.isna(data{i}, i)' for i in range(len
            (others.columns))])
        mdc__xoxm += (
            '  out_arr = bodo.libs.str_arr_ext.pre_alloc_string_array(l, -1)\n'
            )
        mdc__xoxm += '  numba.parfors.parfor.init_prange()\n'
        mdc__xoxm += '  for i in numba.parfors.parfor.internal_prange(l):\n'
        mdc__xoxm += f'      if {zlxn__svvie}:\n'
        mdc__xoxm += '          bodo.libs.array_kernels.setna(out_arr, i)\n'
        mdc__xoxm += '          continue\n'
        tsgtu__pcbj = ', '.join(['arr[i]'] + [f'data{i}[i]' for i in range(
            len(others.columns))])
        hvct__rys = "''" if is_overload_none(sep) else 'sep'
        mdc__xoxm += f'      out_arr[i] = {hvct__rys}.join([{tsgtu__pcbj}])\n'
    mdc__xoxm += (
        '  return bodo.hiframes.pd_series_ext.init_series(out_arr, index, name)\n'
        )
    hklc__lmu = {}
    exec(mdc__xoxm, {'bodo': bodo, 'numba': numba}, hklc__lmu)
    impl = hklc__lmu['impl']
    return impl


@overload_method(SeriesStrMethodType, 'count', inline='always',
    no_unliteral=True)
def overload_str_method_count(S_str, pat, flags=0):
    str_arg_check('count', 'pat', pat)
    int_arg_check('count', 'flags', flags)

    def impl(S_str, pat, flags=0):
        S = S_str._obj
        yyohm__jtwf = bodo.hiframes.pd_series_ext.get_series_data(S)
        bbzay__wle = bodo.hiframes.pd_series_ext.get_series_name(S)
        tksf__cmxlz = bodo.hiframes.pd_series_ext.get_series_index(S)
        iuho__ongml = re.compile(pat, flags)
        numba.parfors.parfor.init_prange()
        qiq__mgu = len(yyohm__jtwf)
        out_arr = bodo.libs.int_arr_ext.alloc_int_array(qiq__mgu, np.int64)
        for i in numba.parfors.parfor.internal_prange(qiq__mgu):
            if bodo.libs.array_kernels.isna(yyohm__jtwf, i):
                bodo.libs.array_kernels.setna(out_arr, i)
            else:
                out_arr[i] = str_findall_count(iuho__ongml, yyohm__jtwf[i])
        return bodo.hiframes.pd_series_ext.init_series(out_arr, tksf__cmxlz,
            bbzay__wle)
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
        yyohm__jtwf = bodo.hiframes.pd_series_ext.get_series_data(S)
        bbzay__wle = bodo.hiframes.pd_series_ext.get_series_name(S)
        tksf__cmxlz = bodo.hiframes.pd_series_ext.get_series_index(S)
        numba.parfors.parfor.init_prange()
        qiq__mgu = len(yyohm__jtwf)
        out_arr = bodo.libs.int_arr_ext.alloc_int_array(qiq__mgu, np.int64)
        for i in numba.parfors.parfor.internal_prange(qiq__mgu):
            if bodo.libs.array_kernels.isna(yyohm__jtwf, i):
                bodo.libs.array_kernels.setna(out_arr, i)
            else:
                out_arr[i] = yyohm__jtwf[i].find(sub, start, end)
        return bodo.hiframes.pd_series_ext.init_series(out_arr, tksf__cmxlz,
            bbzay__wle)
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
        yyohm__jtwf = bodo.hiframes.pd_series_ext.get_series_data(S)
        bbzay__wle = bodo.hiframes.pd_series_ext.get_series_name(S)
        tksf__cmxlz = bodo.hiframes.pd_series_ext.get_series_index(S)
        numba.parfors.parfor.init_prange()
        qiq__mgu = len(yyohm__jtwf)
        out_arr = bodo.libs.int_arr_ext.alloc_int_array(qiq__mgu, np.int64)
        for i in numba.parfors.parfor.internal_prange(qiq__mgu):
            if bodo.libs.array_kernels.isna(yyohm__jtwf, i):
                bodo.libs.array_kernels.setna(out_arr, i)
            else:
                out_arr[i] = yyohm__jtwf[i].rfind(sub, start, end)
        return bodo.hiframes.pd_series_ext.init_series(out_arr, tksf__cmxlz,
            bbzay__wle)
    return impl


@overload_method(SeriesStrMethodType, 'center', inline='always',
    no_unliteral=True)
def overload_str_method_center(S_str, width, fillchar=' '):
    common_validate_padding('center', width, fillchar)

    def impl(S_str, width, fillchar=' '):
        S = S_str._obj
        yyohm__jtwf = bodo.hiframes.pd_series_ext.get_series_data(S)
        bbzay__wle = bodo.hiframes.pd_series_ext.get_series_name(S)
        tksf__cmxlz = bodo.hiframes.pd_series_ext.get_series_index(S)
        numba.parfors.parfor.init_prange()
        qiq__mgu = len(yyohm__jtwf)
        out_arr = bodo.libs.str_arr_ext.pre_alloc_string_array(qiq__mgu, -1)
        for nql__zvhz in numba.parfors.parfor.internal_prange(qiq__mgu):
            if bodo.libs.array_kernels.isna(yyohm__jtwf, nql__zvhz):
                out_arr[nql__zvhz] = ''
                bodo.libs.array_kernels.setna(out_arr, nql__zvhz)
            else:
                out_arr[nql__zvhz] = yyohm__jtwf[nql__zvhz].center(width,
                    fillchar)
        return bodo.hiframes.pd_series_ext.init_series(out_arr, tksf__cmxlz,
            bbzay__wle)
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
        yyohm__jtwf = bodo.hiframes.pd_series_ext.get_series_data(S)
        bbzay__wle = bodo.hiframes.pd_series_ext.get_series_name(S)
        tksf__cmxlz = bodo.hiframes.pd_series_ext.get_series_index(S)
        numba.parfors.parfor.init_prange()
        qiq__mgu = len(yyohm__jtwf)
        out_arr = bodo.libs.str_arr_ext.pre_alloc_string_array(qiq__mgu, -1)
        for nql__zvhz in numba.parfors.parfor.internal_prange(qiq__mgu):
            if bodo.libs.array_kernels.isna(yyohm__jtwf, nql__zvhz):
                bodo.libs.array_kernels.setna(out_arr, nql__zvhz)
            else:
                if stop is not None:
                    ena__vkfy = yyohm__jtwf[nql__zvhz][stop:]
                else:
                    ena__vkfy = ''
                out_arr[nql__zvhz] = yyohm__jtwf[nql__zvhz][:start
                    ] + repl + ena__vkfy
        return bodo.hiframes.pd_series_ext.init_series(out_arr, tksf__cmxlz,
            bbzay__wle)
    return impl


@overload_method(SeriesStrMethodType, 'repeat', inline='always',
    no_unliteral=True)
def overload_str_method_repeat(S_str, repeats):
    if isinstance(repeats, types.Integer) or is_overload_constant_int(repeats):

        def impl(S_str, repeats):
            S = S_str._obj
            yyohm__jtwf = bodo.hiframes.pd_series_ext.get_series_data(S)
            bbzay__wle = bodo.hiframes.pd_series_ext.get_series_name(S)
            tksf__cmxlz = bodo.hiframes.pd_series_ext.get_series_index(S)
            numba.parfors.parfor.init_prange()
            qiq__mgu = len(yyohm__jtwf)
            out_arr = bodo.libs.str_arr_ext.pre_alloc_string_array(qiq__mgu, -1
                )
            for nql__zvhz in numba.parfors.parfor.internal_prange(qiq__mgu):
                if bodo.libs.array_kernels.isna(yyohm__jtwf, nql__zvhz):
                    bodo.libs.array_kernels.setna(out_arr, nql__zvhz)
                else:
                    out_arr[nql__zvhz] = yyohm__jtwf[nql__zvhz] * repeats
            return bodo.hiframes.pd_series_ext.init_series(out_arr,
                tksf__cmxlz, bbzay__wle)
        return impl
    elif is_overload_constant_list(repeats):
        ggi__agpec = get_overload_const_list(repeats)
        rthwh__gul = all([isinstance(pgpic__ogyd, int) for pgpic__ogyd in
            ggi__agpec])
    elif is_list_like_index_type(repeats) and isinstance(repeats.dtype,
        types.Integer):
        rthwh__gul = True
    else:
        rthwh__gul = False
    if rthwh__gul:

        def impl(S_str, repeats):
            S = S_str._obj
            yyohm__jtwf = bodo.hiframes.pd_series_ext.get_series_data(S)
            bbzay__wle = bodo.hiframes.pd_series_ext.get_series_name(S)
            tksf__cmxlz = bodo.hiframes.pd_series_ext.get_series_index(S)
            eqzas__sxbbq = bodo.utils.conversion.coerce_to_array(repeats)
            numba.parfors.parfor.init_prange()
            qiq__mgu = len(yyohm__jtwf)
            out_arr = bodo.libs.str_arr_ext.pre_alloc_string_array(qiq__mgu, -1
                )
            for nql__zvhz in numba.parfors.parfor.internal_prange(qiq__mgu):
                if bodo.libs.array_kernels.isna(yyohm__jtwf, nql__zvhz):
                    bodo.libs.array_kernels.setna(out_arr, nql__zvhz)
                else:
                    out_arr[nql__zvhz] = yyohm__jtwf[nql__zvhz] * eqzas__sxbbq[
                        nql__zvhz]
            return bodo.hiframes.pd_series_ext.init_series(out_arr,
                tksf__cmxlz, bbzay__wle)
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
        yyohm__jtwf = bodo.hiframes.pd_series_ext.get_series_data(S)
        bbzay__wle = bodo.hiframes.pd_series_ext.get_series_name(S)
        tksf__cmxlz = bodo.hiframes.pd_series_ext.get_series_index(S)
        numba.parfors.parfor.init_prange()
        qiq__mgu = len(yyohm__jtwf)
        out_arr = bodo.libs.str_arr_ext.pre_alloc_string_array(qiq__mgu, -1)
        for nql__zvhz in numba.parfors.parfor.internal_prange(qiq__mgu):
            if bodo.libs.array_kernels.isna(yyohm__jtwf, nql__zvhz):
                out_arr[nql__zvhz] = ''
                bodo.libs.array_kernels.setna(out_arr, nql__zvhz)
            else:
                out_arr[nql__zvhz] = yyohm__jtwf[nql__zvhz].ljust(width,
                    fillchar)
        return bodo.hiframes.pd_series_ext.init_series(out_arr, tksf__cmxlz,
            bbzay__wle)
    return impl


@overload_method(SeriesStrMethodType, 'rjust', inline='always',
    no_unliteral=True)
def overload_str_method_rjust(S_str, width, fillchar=' '):
    common_validate_padding('rjust', width, fillchar)

    def impl(S_str, width, fillchar=' '):
        S = S_str._obj
        yyohm__jtwf = bodo.hiframes.pd_series_ext.get_series_data(S)
        bbzay__wle = bodo.hiframes.pd_series_ext.get_series_name(S)
        tksf__cmxlz = bodo.hiframes.pd_series_ext.get_series_index(S)
        numba.parfors.parfor.init_prange()
        qiq__mgu = len(yyohm__jtwf)
        out_arr = bodo.libs.str_arr_ext.pre_alloc_string_array(qiq__mgu, -1)
        for nql__zvhz in numba.parfors.parfor.internal_prange(qiq__mgu):
            if bodo.libs.array_kernels.isna(yyohm__jtwf, nql__zvhz):
                out_arr[nql__zvhz] = ''
                bodo.libs.array_kernels.setna(out_arr, nql__zvhz)
            else:
                out_arr[nql__zvhz] = yyohm__jtwf[nql__zvhz].rjust(width,
                    fillchar)
        return bodo.hiframes.pd_series_ext.init_series(out_arr, tksf__cmxlz,
            bbzay__wle)
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
        yyohm__jtwf = bodo.hiframes.pd_series_ext.get_series_data(S)
        bbzay__wle = bodo.hiframes.pd_series_ext.get_series_name(S)
        tksf__cmxlz = bodo.hiframes.pd_series_ext.get_series_index(S)
        numba.parfors.parfor.init_prange()
        qiq__mgu = len(yyohm__jtwf)
        out_arr = bodo.libs.str_arr_ext.pre_alloc_string_array(qiq__mgu, -1)
        for nql__zvhz in numba.parfors.parfor.internal_prange(qiq__mgu):
            if bodo.libs.array_kernels.isna(yyohm__jtwf, nql__zvhz):
                out_arr[nql__zvhz] = ''
                bodo.libs.array_kernels.setna(out_arr, nql__zvhz)
            elif side == 'left':
                out_arr[nql__zvhz] = yyohm__jtwf[nql__zvhz].rjust(width,
                    fillchar)
            elif side == 'right':
                out_arr[nql__zvhz] = yyohm__jtwf[nql__zvhz].ljust(width,
                    fillchar)
            elif side == 'both':
                out_arr[nql__zvhz] = yyohm__jtwf[nql__zvhz].center(width,
                    fillchar)
        return bodo.hiframes.pd_series_ext.init_series(out_arr, tksf__cmxlz,
            bbzay__wle)
    return impl


@overload_method(SeriesStrMethodType, 'zfill', inline='always',
    no_unliteral=True)
def overload_str_method_zfill(S_str, width):
    int_arg_check('zfill', 'width', width)

    def impl(S_str, width):
        S = S_str._obj
        yyohm__jtwf = bodo.hiframes.pd_series_ext.get_series_data(S)
        bbzay__wle = bodo.hiframes.pd_series_ext.get_series_name(S)
        tksf__cmxlz = bodo.hiframes.pd_series_ext.get_series_index(S)
        numba.parfors.parfor.init_prange()
        qiq__mgu = len(yyohm__jtwf)
        out_arr = bodo.libs.str_arr_ext.pre_alloc_string_array(qiq__mgu, -1)
        for nql__zvhz in numba.parfors.parfor.internal_prange(qiq__mgu):
            if bodo.libs.array_kernels.isna(yyohm__jtwf, nql__zvhz):
                out_arr[nql__zvhz] = ''
                bodo.libs.array_kernels.setna(out_arr, nql__zvhz)
            else:
                out_arr[nql__zvhz] = yyohm__jtwf[nql__zvhz].zfill(width)
        return bodo.hiframes.pd_series_ext.init_series(out_arr, tksf__cmxlz,
            bbzay__wle)
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
        yyohm__jtwf = bodo.hiframes.pd_series_ext.get_series_data(S)
        bbzay__wle = bodo.hiframes.pd_series_ext.get_series_name(S)
        tksf__cmxlz = bodo.hiframes.pd_series_ext.get_series_index(S)
        numba.parfors.parfor.init_prange()
        qiq__mgu = len(yyohm__jtwf)
        out_arr = bodo.libs.str_arr_ext.pre_alloc_string_array(qiq__mgu, -1)
        for nql__zvhz in numba.parfors.parfor.internal_prange(qiq__mgu):
            if bodo.libs.array_kernels.isna(yyohm__jtwf, nql__zvhz):
                out_arr[nql__zvhz] = ''
                bodo.libs.array_kernels.setna(out_arr, nql__zvhz)
            else:
                out_arr[nql__zvhz] = yyohm__jtwf[nql__zvhz][start:stop:step]
        return bodo.hiframes.pd_series_ext.init_series(out_arr, tksf__cmxlz,
            bbzay__wle)
    return impl


@overload_method(SeriesStrMethodType, 'startswith', inline='always',
    no_unliteral=True)
def overload_str_method_startswith(S_str, pat, na=np.nan):
    not_supported_arg_check('startswith', 'na', na, np.nan)
    str_arg_check('startswith', 'pat', pat)

    def impl(S_str, pat, na=np.nan):
        S = S_str._obj
        yyohm__jtwf = bodo.hiframes.pd_series_ext.get_series_data(S)
        bbzay__wle = bodo.hiframes.pd_series_ext.get_series_name(S)
        tksf__cmxlz = bodo.hiframes.pd_series_ext.get_series_index(S)
        numba.parfors.parfor.init_prange()
        qiq__mgu = len(yyohm__jtwf)
        out_arr = bodo.libs.bool_arr_ext.alloc_bool_array(qiq__mgu)
        for i in numba.parfors.parfor.internal_prange(qiq__mgu):
            if bodo.libs.array_kernels.isna(yyohm__jtwf, i):
                bodo.libs.array_kernels.setna(out_arr, i)
            else:
                out_arr[i] = yyohm__jtwf[i].startswith(pat)
        return bodo.hiframes.pd_series_ext.init_series(out_arr, tksf__cmxlz,
            bbzay__wle)
    return impl


@overload_method(SeriesStrMethodType, 'endswith', inline='always',
    no_unliteral=True)
def overload_str_method_endswith(S_str, pat, na=np.nan):
    not_supported_arg_check('endswith', 'na', na, np.nan)
    str_arg_check('endswith', 'pat', pat)

    def impl(S_str, pat, na=np.nan):
        S = S_str._obj
        yyohm__jtwf = bodo.hiframes.pd_series_ext.get_series_data(S)
        bbzay__wle = bodo.hiframes.pd_series_ext.get_series_name(S)
        tksf__cmxlz = bodo.hiframes.pd_series_ext.get_series_index(S)
        numba.parfors.parfor.init_prange()
        qiq__mgu = len(yyohm__jtwf)
        out_arr = bodo.libs.bool_arr_ext.alloc_bool_array(qiq__mgu)
        for i in numba.parfors.parfor.internal_prange(qiq__mgu):
            if bodo.libs.array_kernels.isna(yyohm__jtwf, i):
                bodo.libs.array_kernels.setna(out_arr, i)
            else:
                out_arr[i] = yyohm__jtwf[i].endswith(pat)
        return bodo.hiframes.pd_series_ext.init_series(out_arr, tksf__cmxlz,
            bbzay__wle)
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
    ack__agwj, regex = _get_column_names_from_regex(pat, flags, 'extract')
    psgn__jvrf = len(ack__agwj)
    mdc__xoxm = 'def impl(S_str, pat, flags=0, expand=True):\n'
    mdc__xoxm += '  regex = re.compile(pat, flags=flags)\n'
    mdc__xoxm += '  S = S_str._obj\n'
    mdc__xoxm += '  str_arr = bodo.hiframes.pd_series_ext.get_series_data(S)\n'
    mdc__xoxm += '  index = bodo.hiframes.pd_series_ext.get_series_index(S)\n'
    mdc__xoxm += '  name = bodo.hiframes.pd_series_ext.get_series_name(S)\n'
    mdc__xoxm += '  numba.parfors.parfor.init_prange()\n'
    mdc__xoxm += '  n = len(str_arr)\n'
    for i in range(psgn__jvrf):
        mdc__xoxm += (
            '  out_arr_{0} = bodo.libs.str_arr_ext.pre_alloc_string_array(n, -1)\n'
            .format(i))
    mdc__xoxm += '  for j in numba.parfors.parfor.internal_prange(n):\n'
    mdc__xoxm += '      if bodo.libs.array_kernels.isna(str_arr, j):\n'
    for i in range(psgn__jvrf):
        mdc__xoxm += "          out_arr_{}[j] = ''\n".format(i)
        mdc__xoxm += (
            '          bodo.libs.array_kernels.setna(out_arr_{}, j)\n'.
            format(i))
    mdc__xoxm += '      else:\n'
    mdc__xoxm += '          m = regex.search(str_arr[j])\n'
    mdc__xoxm += '          if m:\n'
    mdc__xoxm += '            g = m.groups()\n'
    for i in range(psgn__jvrf):
        mdc__xoxm += '            out_arr_{0}[j] = g[{0}]\n'.format(i)
    mdc__xoxm += '          else:\n'
    for i in range(psgn__jvrf):
        mdc__xoxm += "            out_arr_{}[j] = ''\n".format(i)
        mdc__xoxm += (
            '            bodo.libs.array_kernels.setna(out_arr_{}, j)\n'.
            format(i))
    if is_overload_false(expand) and regex.groups == 1:
        bbzay__wle = "'{}'".format(list(regex.groupindex.keys()).pop()) if len(
            regex.groupindex.keys()) > 0 else 'name'
        mdc__xoxm += (
            '  return bodo.hiframes.pd_series_ext.init_series(out_arr_0, index, {})\n'
            .format(bbzay__wle))
        hklc__lmu = {}
        exec(mdc__xoxm, {'re': re, 'bodo': bodo, 'numba': numba,
            'get_utf8_size': get_utf8_size}, hklc__lmu)
        impl = hklc__lmu['impl']
        return impl
    cbtlm__iwxn = ', '.join('out_arr_{}'.format(i) for i in range(psgn__jvrf))
    impl = bodo.hiframes.dataframe_impl._gen_init_df(mdc__xoxm, ack__agwj,
        cbtlm__iwxn, 'index', extra_globals={'get_utf8_size': get_utf8_size,
        're': re})
    return impl


@overload_method(SeriesStrMethodType, 'extractall', inline='always',
    no_unliteral=True)
def overload_str_method_extractall(S_str, pat, flags=0):
    ack__agwj, pcd__acmsf = _get_column_names_from_regex(pat, flags,
        'extractall')
    psgn__jvrf = len(ack__agwj)
    bik__wawzp = isinstance(S_str.stype.index, StringIndexType)
    mdc__xoxm = 'def impl(S_str, pat, flags=0):\n'
    mdc__xoxm += '  regex = re.compile(pat, flags=flags)\n'
    mdc__xoxm += '  S = S_str._obj\n'
    mdc__xoxm += '  str_arr = bodo.hiframes.pd_series_ext.get_series_data(S)\n'
    mdc__xoxm += '  index = bodo.hiframes.pd_series_ext.get_series_index(S)\n'
    mdc__xoxm += '  name = bodo.hiframes.pd_series_ext.get_series_name(S)\n'
    mdc__xoxm += '  index_arr = bodo.utils.conversion.index_to_array(index)\n'
    mdc__xoxm += (
        '  index_name = bodo.hiframes.pd_index_ext.get_index_name(index)\n')
    mdc__xoxm += '  numba.parfors.parfor.init_prange()\n'
    mdc__xoxm += '  n = len(str_arr)\n'
    mdc__xoxm += '  out_n_l = [0]\n'
    for i in range(psgn__jvrf):
        mdc__xoxm += '  num_chars_{} = 0\n'.format(i)
    if bik__wawzp:
        mdc__xoxm += '  index_num_chars = 0\n'
    mdc__xoxm += '  for i in numba.parfors.parfor.internal_prange(n):\n'
    if bik__wawzp:
        mdc__xoxm += '      index_num_chars += get_utf8_size(index_arr[i])\n'
    mdc__xoxm += '      if bodo.libs.array_kernels.isna(str_arr, i):\n'
    mdc__xoxm += '          continue\n'
    mdc__xoxm += '      m = regex.findall(str_arr[i])\n'
    mdc__xoxm += '      out_n_l[0] += len(m)\n'
    for i in range(psgn__jvrf):
        mdc__xoxm += '      l_{} = 0\n'.format(i)
    mdc__xoxm += '      for s in m:\n'
    for i in range(psgn__jvrf):
        mdc__xoxm += '        l_{} += get_utf8_size(s{})\n'.format(i, 
            '[{}]'.format(i) if psgn__jvrf > 1 else '')
    for i in range(psgn__jvrf):
        mdc__xoxm += '      num_chars_{0} += l_{0}\n'.format(i)
    mdc__xoxm += (
        '  out_n = bodo.libs.distributed_api.local_alloc_size(out_n_l[0], str_arr)\n'
        )
    for i in range(psgn__jvrf):
        mdc__xoxm += (
            """  out_arr_{0} = bodo.libs.str_arr_ext.pre_alloc_string_array(out_n, num_chars_{0})
"""
            .format(i))
    if bik__wawzp:
        mdc__xoxm += """  out_ind_arr = bodo.libs.str_arr_ext.pre_alloc_string_array(out_n, index_num_chars)
"""
    else:
        mdc__xoxm += '  out_ind_arr = np.empty(out_n, index_arr.dtype)\n'
    mdc__xoxm += '  out_match_arr = np.empty(out_n, np.int64)\n'
    mdc__xoxm += '  out_ind = 0\n'
    mdc__xoxm += '  for j in numba.parfors.parfor.internal_prange(n):\n'
    mdc__xoxm += '      if bodo.libs.array_kernels.isna(str_arr, j):\n'
    mdc__xoxm += '          continue\n'
    mdc__xoxm += '      m = regex.findall(str_arr[j])\n'
    mdc__xoxm += '      for k, s in enumerate(m):\n'
    for i in range(psgn__jvrf):
        mdc__xoxm += (
            '        bodo.libs.distributed_api.set_arr_local(out_arr_{}, out_ind, s{})\n'
            .format(i, '[{}]'.format(i) if psgn__jvrf > 1 else ''))
    mdc__xoxm += """        bodo.libs.distributed_api.set_arr_local(out_ind_arr, out_ind, index_arr[j])
"""
    mdc__xoxm += (
        '        bodo.libs.distributed_api.set_arr_local(out_match_arr, out_ind, k)\n'
        )
    mdc__xoxm += '        out_ind += 1\n'
    mdc__xoxm += (
        '  out_index = bodo.hiframes.pd_multi_index_ext.init_multi_index(\n')
    mdc__xoxm += "    (out_ind_arr, out_match_arr), (index_name, 'match'))\n"
    cbtlm__iwxn = ', '.join('out_arr_{}'.format(i) for i in range(psgn__jvrf))
    impl = bodo.hiframes.dataframe_impl._gen_init_df(mdc__xoxm, ack__agwj,
        cbtlm__iwxn, 'out_index', extra_globals={'get_utf8_size':
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
    dblx__clt = dict(zip(regex.groupindex.values(), regex.groupindex.keys()))
    ack__agwj = [dblx__clt.get(1 + i, i) for i in range(regex.groups)]
    return ack__agwj, regex


def create_str2str_methods_overload(func_name):
    if func_name in ['lstrip', 'rstrip', 'strip']:
        mdc__xoxm = 'def f(S_str, to_strip=None):\n'
    else:
        mdc__xoxm = 'def f(S_str):\n'
    mdc__xoxm += '    S = S_str._obj\n'
    mdc__xoxm += (
        '    str_arr = bodo.hiframes.pd_series_ext.get_series_data(S)\n')
    mdc__xoxm += '    str_arr = decode_if_dict_array(str_arr)\n'
    mdc__xoxm += (
        '    index = bodo.hiframes.pd_series_ext.get_series_index(S)\n')
    mdc__xoxm += '    name = bodo.hiframes.pd_series_ext.get_series_name(S)\n'
    mdc__xoxm += '    numba.parfors.parfor.init_prange()\n'
    mdc__xoxm += '    n = len(str_arr)\n'
    if func_name in ('capitalize', 'lower', 'swapcase', 'title', 'upper'):
        mdc__xoxm += '    num_chars = num_total_chars(str_arr)\n'
    else:
        mdc__xoxm += '    num_chars = -1\n'
    mdc__xoxm += (
        '    out_arr = bodo.libs.str_arr_ext.pre_alloc_string_array(n, num_chars)\n'
        )
    mdc__xoxm += '    for j in numba.parfors.parfor.internal_prange(n):\n'
    mdc__xoxm += '        if bodo.libs.array_kernels.isna(str_arr, j):\n'
    mdc__xoxm += '            out_arr[j] = ""\n'
    mdc__xoxm += '            bodo.libs.array_kernels.setna(out_arr, j)\n'
    mdc__xoxm += '        else:\n'
    if func_name in ['lstrip', 'rstrip', 'strip']:
        mdc__xoxm += ('            out_arr[j] = str_arr[j].{}(to_strip)\n'.
            format(func_name))
    else:
        mdc__xoxm += '            out_arr[j] = str_arr[j].{}()\n'.format(
            func_name)
    mdc__xoxm += (
        '    return bodo.hiframes.pd_series_ext.init_series(out_arr, index, name)\n'
        )
    hklc__lmu = {}
    exec(mdc__xoxm, {'bodo': bodo, 'numba': numba, 'num_total_chars': bodo.
        libs.str_arr_ext.num_total_chars, 'get_utf8_size': bodo.libs.
        str_arr_ext.get_utf8_size, 'decode_if_dict_array': bodo.utils.
        typing.decode_if_dict_array}, hklc__lmu)
    cob__ggus = hklc__lmu['f']
    if func_name in ['lstrip', 'rstrip', 'strip']:

        def overload_strip_method(S_str, to_strip=None):
            if not is_overload_none(to_strip):
                str_arg_check(func_name, 'to_strip', to_strip)
            return cob__ggus
        return overload_strip_method
    else:

        def overload_str2str_methods(S_str):
            return cob__ggus
        return overload_str2str_methods


def create_str2bool_methods_overload(func_name):

    def overload_str2bool_methods(S_str):
        mdc__xoxm = 'def f(S_str):\n'
        mdc__xoxm += '    S = S_str._obj\n'
        mdc__xoxm += (
            '    str_arr = bodo.hiframes.pd_series_ext.get_series_data(S)\n')
        mdc__xoxm += (
            '    index = bodo.hiframes.pd_series_ext.get_series_index(S)\n')
        mdc__xoxm += (
            '    name = bodo.hiframes.pd_series_ext.get_series_name(S)\n')
        mdc__xoxm += '    numba.parfors.parfor.init_prange()\n'
        mdc__xoxm += '    l = len(str_arr)\n'
        mdc__xoxm += (
            '    out_arr = bodo.libs.bool_arr_ext.alloc_bool_array(l)\n')
        mdc__xoxm += '    for i in numba.parfors.parfor.internal_prange(l):\n'
        mdc__xoxm += '        if bodo.libs.array_kernels.isna(str_arr, i):\n'
        mdc__xoxm += '            bodo.libs.array_kernels.setna(out_arr, i)\n'
        mdc__xoxm += '        else:\n'
        mdc__xoxm += ('            out_arr[i] = np.bool_(str_arr[i].{}())\n'
            .format(func_name))
        mdc__xoxm += '    return bodo.hiframes.pd_series_ext.init_series(\n'
        mdc__xoxm += '      out_arr,index, name)\n'
        hklc__lmu = {}
        exec(mdc__xoxm, {'bodo': bodo, 'numba': numba, 'np': np}, hklc__lmu)
        cob__ggus = hklc__lmu['f']
        return cob__ggus
    return overload_str2bool_methods


def _install_str2str_methods():
    for rxi__uoda in bodo.hiframes.pd_series_ext.str2str_methods:
        qyicf__lkza = create_str2str_methods_overload(rxi__uoda)
        overload_method(SeriesStrMethodType, rxi__uoda, inline='always',
            no_unliteral=True)(qyicf__lkza)


def _install_str2bool_methods():
    for rxi__uoda in bodo.hiframes.pd_series_ext.str2bool_methods:
        qyicf__lkza = create_str2bool_methods_overload(rxi__uoda)
        overload_method(SeriesStrMethodType, rxi__uoda, inline='always',
            no_unliteral=True)(qyicf__lkza)


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
        bbzay__wle = 'SeriesCatMethodType({})'.format(stype)
        super(SeriesCatMethodType, self).__init__(bbzay__wle)

    @property
    def mangling_args(self):
        return self.__class__.__name__, (self._code,)


@register_model(SeriesCatMethodType)
class SeriesCatModel(models.StructModel):

    def __init__(self, dmm, fe_type):
        xbv__nrrc = [('obj', fe_type.stype)]
        super(SeriesCatModel, self).__init__(dmm, fe_type, xbv__nrrc)


make_attribute_wrapper(SeriesCatMethodType, 'obj', '_obj')


@intrinsic
def init_series_cat_method(typingctx, obj=None):

    def codegen(context, builder, signature, args):
        crmz__asitc, = args
        pni__spiwo = signature.return_type
        azb__btvuf = cgutils.create_struct_proxy(pni__spiwo)(context, builder)
        azb__btvuf.obj = crmz__asitc
        context.nrt.incref(builder, signature.args[0], crmz__asitc)
        return azb__btvuf._getvalue()
    return SeriesCatMethodType(obj)(obj), codegen


@overload_attribute(SeriesCatMethodType, 'codes')
def series_cat_codes_overload(S_dt):

    def impl(S_dt):
        S = S_dt._obj
        wzgxc__oxy = bodo.hiframes.pd_series_ext.get_series_data(S)
        tksf__cmxlz = bodo.hiframes.pd_series_ext.get_series_index(S)
        bbzay__wle = None
        return bodo.hiframes.pd_series_ext.init_series(bodo.hiframes.
            pd_categorical_ext.get_categorical_arr_codes(wzgxc__oxy),
            tksf__cmxlz, bbzay__wle)
    return impl


unsupported_cat_attrs = {'categories', 'ordered'}
unsupported_cat_methods = {'rename_categories', 'reorder_categories',
    'add_categories', 'remove_categories', 'remove_unused_categories',
    'set_categories', 'as_ordered', 'as_unordered'}


def _install_catseries_unsupported():
    for bqzif__rsi in unsupported_cat_attrs:
        omfh__wrv = 'Series.cat.' + bqzif__rsi
        overload_attribute(SeriesCatMethodType, bqzif__rsi)(
            create_unsupported_overload(omfh__wrv))
    for wbqlj__jjve in unsupported_cat_methods:
        omfh__wrv = 'Series.cat.' + wbqlj__jjve
        overload_method(SeriesCatMethodType, wbqlj__jjve)(
            create_unsupported_overload(omfh__wrv))


_install_catseries_unsupported()
unsupported_str_methods = {'casefold', 'decode', 'encode', 'findall',
    'fullmatch', 'index', 'match', 'normalize', 'partition', 'rindex',
    'rpartition', 'slice_replace', 'rsplit', 'translate', 'wrap', 'get_dummies'
    }


def _install_strseries_unsupported():
    for wbqlj__jjve in unsupported_str_methods:
        omfh__wrv = 'Series.str.' + wbqlj__jjve
        overload_method(SeriesStrMethodType, wbqlj__jjve)(
            create_unsupported_overload(omfh__wrv))


_install_strseries_unsupported()
