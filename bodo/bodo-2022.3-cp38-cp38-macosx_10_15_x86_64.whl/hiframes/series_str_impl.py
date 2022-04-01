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
        uzzpm__pvwvk = 'SeriesStrMethodType({})'.format(stype)
        super(SeriesStrMethodType, self).__init__(uzzpm__pvwvk)


@register_model(SeriesStrMethodType)
class SeriesStrModel(models.StructModel):

    def __init__(self, dmm, fe_type):
        jlry__rzsch = [('obj', fe_type.stype)]
        super(SeriesStrModel, self).__init__(dmm, fe_type, jlry__rzsch)


make_attribute_wrapper(SeriesStrMethodType, 'obj', '_obj')


@intrinsic
def init_series_str_method(typingctx, obj=None):

    def codegen(context, builder, signature, args):
        etbvv__cfdo, = args
        rtahf__moz = signature.return_type
        mmxsf__favc = cgutils.create_struct_proxy(rtahf__moz)(context, builder)
        mmxsf__favc.obj = etbvv__cfdo
        context.nrt.incref(builder, signature.args[0], etbvv__cfdo)
        return mmxsf__favc._getvalue()
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
        pqgi__tjkhd = bodo.hiframes.pd_series_ext.get_series_data(S)
        voeur__rdpzf = bodo.hiframes.pd_series_ext.get_series_index(S)
        uzzpm__pvwvk = bodo.hiframes.pd_series_ext.get_series_name(S)
        out_arr = bodo.libs.array_kernels.get_arr_lens(pqgi__tjkhd, False)
        return bodo.hiframes.pd_series_ext.init_series(out_arr,
            voeur__rdpzf, uzzpm__pvwvk)
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
            pqgi__tjkhd = bodo.hiframes.pd_series_ext.get_series_data(S)
            voeur__rdpzf = bodo.hiframes.pd_series_ext.get_series_index(S)
            uzzpm__pvwvk = bodo.hiframes.pd_series_ext.get_series_name(S)
            out_arr = bodo.hiframes.split_impl.compute_split_view(pqgi__tjkhd,
                pat)
            return bodo.hiframes.pd_series_ext.init_series(out_arr,
                voeur__rdpzf, uzzpm__pvwvk)
        return _str_split_view_impl

    def _str_split_impl(S_str, pat=None, n=-1, expand=False):
        S = S_str._obj
        pqgi__tjkhd = bodo.hiframes.pd_series_ext.get_series_data(S)
        voeur__rdpzf = bodo.hiframes.pd_series_ext.get_series_index(S)
        uzzpm__pvwvk = bodo.hiframes.pd_series_ext.get_series_name(S)
        out_arr = bodo.libs.str_ext.str_split(pqgi__tjkhd, pat, n)
        return bodo.hiframes.pd_series_ext.init_series(out_arr,
            voeur__rdpzf, uzzpm__pvwvk)
    return _str_split_impl


@overload_method(SeriesStrMethodType, 'get', no_unliteral=True)
def overload_str_method_get(S_str, i):
    cbm__sumq = S_str.stype.data
    if (cbm__sumq != string_array_split_view_type and not is_str_arr_type(
        cbm__sumq)) and not isinstance(cbm__sumq, ArrayItemArrayType):
        raise_bodo_error(
            'Series.str.get(): only supports input type of Series(array(item)) and Series(str)'
            )
    int_arg_check('get', 'i', i)
    if isinstance(cbm__sumq, ArrayItemArrayType):

        def _str_get_array_impl(S_str, i):
            S = S_str._obj
            pqgi__tjkhd = bodo.hiframes.pd_series_ext.get_series_data(S)
            voeur__rdpzf = bodo.hiframes.pd_series_ext.get_series_index(S)
            uzzpm__pvwvk = bodo.hiframes.pd_series_ext.get_series_name(S)
            out_arr = bodo.libs.array_kernels.get(pqgi__tjkhd, i)
            return bodo.hiframes.pd_series_ext.init_series(out_arr,
                voeur__rdpzf, uzzpm__pvwvk)
        return _str_get_array_impl
    if cbm__sumq == string_array_split_view_type:

        def _str_get_split_impl(S_str, i):
            S = S_str._obj
            pqgi__tjkhd = bodo.hiframes.pd_series_ext.get_series_data(S)
            voeur__rdpzf = bodo.hiframes.pd_series_ext.get_series_index(S)
            uzzpm__pvwvk = bodo.hiframes.pd_series_ext.get_series_name(S)
            numba.parfors.parfor.init_prange()
            n = len(pqgi__tjkhd)
            fgruv__pkrbz = 0
            for qub__whr in numba.parfors.parfor.internal_prange(n):
                uih__zifpj, uih__zifpj, sxqn__lnc = get_split_view_index(
                    pqgi__tjkhd, qub__whr, i)
                fgruv__pkrbz += sxqn__lnc
            numba.parfors.parfor.init_prange()
            out_arr = pre_alloc_string_array(n, fgruv__pkrbz)
            for vqmuo__ijf in numba.parfors.parfor.internal_prange(n):
                agkz__ndwj, syxxf__unxa, sxqn__lnc = get_split_view_index(
                    pqgi__tjkhd, vqmuo__ijf, i)
                if agkz__ndwj == 0:
                    bodo.libs.array_kernels.setna(out_arr, vqmuo__ijf)
                    tnvk__mpb = get_split_view_data_ptr(pqgi__tjkhd, 0)
                else:
                    bodo.libs.str_arr_ext.str_arr_set_not_na(out_arr,
                        vqmuo__ijf)
                    tnvk__mpb = get_split_view_data_ptr(pqgi__tjkhd,
                        syxxf__unxa)
                bodo.libs.str_arr_ext.setitem_str_arr_ptr(out_arr,
                    vqmuo__ijf, tnvk__mpb, sxqn__lnc)
            return bodo.hiframes.pd_series_ext.init_series(out_arr,
                voeur__rdpzf, uzzpm__pvwvk)
        return _str_get_split_impl

    def _str_get_impl(S_str, i):
        S = S_str._obj
        pqgi__tjkhd = bodo.hiframes.pd_series_ext.get_series_data(S)
        voeur__rdpzf = bodo.hiframes.pd_series_ext.get_series_index(S)
        uzzpm__pvwvk = bodo.hiframes.pd_series_ext.get_series_name(S)
        numba.parfors.parfor.init_prange()
        n = len(pqgi__tjkhd)
        numba.parfors.parfor.init_prange()
        out_arr = pre_alloc_string_array(n, -1)
        for vqmuo__ijf in numba.parfors.parfor.internal_prange(n):
            if bodo.libs.array_kernels.isna(pqgi__tjkhd, vqmuo__ijf
                ) or not len(pqgi__tjkhd[vqmuo__ijf]) > i >= -len(pqgi__tjkhd
                [vqmuo__ijf]):
                out_arr[vqmuo__ijf] = ''
                bodo.libs.array_kernels.setna(out_arr, vqmuo__ijf)
            else:
                out_arr[vqmuo__ijf] = pqgi__tjkhd[vqmuo__ijf][i]
        return bodo.hiframes.pd_series_ext.init_series(out_arr,
            voeur__rdpzf, uzzpm__pvwvk)
    return _str_get_impl


@overload_method(SeriesStrMethodType, 'join', inline='always', no_unliteral
    =True)
def overload_str_method_join(S_str, sep):
    cbm__sumq = S_str.stype.data
    if (cbm__sumq != string_array_split_view_type and cbm__sumq !=
        ArrayItemArrayType(string_array_type) and not is_str_arr_type(
        cbm__sumq)):
        raise_bodo_error(
            'Series.str.join(): only supports input type of Series(list(str)) and Series(str)'
            )
    str_arg_check('join', 'sep', sep)

    def impl(S_str, sep):
        S = S_str._obj
        sej__bhrb = bodo.hiframes.pd_series_ext.get_series_data(S)
        uzzpm__pvwvk = bodo.hiframes.pd_series_ext.get_series_name(S)
        voeur__rdpzf = bodo.hiframes.pd_series_ext.get_series_index(S)
        numba.parfors.parfor.init_prange()
        n = len(sej__bhrb)
        out_arr = bodo.libs.str_arr_ext.pre_alloc_string_array(n, -1)
        for vqmuo__ijf in numba.parfors.parfor.internal_prange(n):
            if bodo.libs.array_kernels.isna(sej__bhrb, vqmuo__ijf):
                out_arr[vqmuo__ijf] = ''
                bodo.libs.array_kernels.setna(out_arr, vqmuo__ijf)
            else:
                rolsb__cjn = sej__bhrb[vqmuo__ijf]
                out_arr[vqmuo__ijf] = sep.join(rolsb__cjn)
        return bodo.hiframes.pd_series_ext.init_series(out_arr,
            voeur__rdpzf, uzzpm__pvwvk)
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
            pqgi__tjkhd = bodo.hiframes.pd_series_ext.get_series_data(S)
            voeur__rdpzf = bodo.hiframes.pd_series_ext.get_series_index(S)
            uzzpm__pvwvk = bodo.hiframes.pd_series_ext.get_series_name(S)
            out_arr = bodo.libs.dict_arr_ext.str_replace(pqgi__tjkhd, pat,
                repl, flags, regex)
            return bodo.hiframes.pd_series_ext.init_series(out_arr,
                voeur__rdpzf, uzzpm__pvwvk)
        return _str_replace_dict_impl
    if is_overload_true(regex):

        def _str_replace_regex_impl(S_str, pat, repl, n=-1, case=None,
            flags=0, regex=True):
            S = S_str._obj
            pqgi__tjkhd = bodo.hiframes.pd_series_ext.get_series_data(S)
            voeur__rdpzf = bodo.hiframes.pd_series_ext.get_series_index(S)
            uzzpm__pvwvk = bodo.hiframes.pd_series_ext.get_series_name(S)
            numba.parfors.parfor.init_prange()
            lyh__fgxfg = re.compile(pat, flags)
            bvttc__kwwaa = len(pqgi__tjkhd)
            out_arr = pre_alloc_string_array(bvttc__kwwaa, -1)
            for vqmuo__ijf in numba.parfors.parfor.internal_prange(bvttc__kwwaa
                ):
                if bodo.libs.array_kernels.isna(pqgi__tjkhd, vqmuo__ijf):
                    out_arr[vqmuo__ijf] = ''
                    bodo.libs.array_kernels.setna(out_arr, vqmuo__ijf)
                    continue
                out_arr[vqmuo__ijf] = lyh__fgxfg.sub(repl, pqgi__tjkhd[
                    vqmuo__ijf])
            return bodo.hiframes.pd_series_ext.init_series(out_arr,
                voeur__rdpzf, uzzpm__pvwvk)
        return _str_replace_regex_impl
    if not is_overload_false(regex):
        raise BodoError('Series.str.replace(): regex argument should be bool')

    def _str_replace_noregex_impl(S_str, pat, repl, n=-1, case=None, flags=
        0, regex=True):
        S = S_str._obj
        pqgi__tjkhd = bodo.hiframes.pd_series_ext.get_series_data(S)
        voeur__rdpzf = bodo.hiframes.pd_series_ext.get_series_index(S)
        uzzpm__pvwvk = bodo.hiframes.pd_series_ext.get_series_name(S)
        numba.parfors.parfor.init_prange()
        bvttc__kwwaa = len(pqgi__tjkhd)
        numba.parfors.parfor.init_prange()
        out_arr = pre_alloc_string_array(bvttc__kwwaa, -1)
        for vqmuo__ijf in numba.parfors.parfor.internal_prange(bvttc__kwwaa):
            if bodo.libs.array_kernels.isna(pqgi__tjkhd, vqmuo__ijf):
                out_arr[vqmuo__ijf] = ''
                bodo.libs.array_kernels.setna(out_arr, vqmuo__ijf)
                continue
            out_arr[vqmuo__ijf] = pqgi__tjkhd[vqmuo__ijf].replace(pat, repl)
        return bodo.hiframes.pd_series_ext.init_series(out_arr,
            voeur__rdpzf, uzzpm__pvwvk)
    return _str_replace_noregex_impl


@numba.njit
def series_contains_regex(S, pat, case, flags, na, regex):
    with numba.objmode(out_arr=bodo.boolean_array):
        out_arr = S.array._str_contains(pat, case, flags, na, regex)
    return out_arr


def is_regex_unsupported(pat):
    vge__rgz = ['(?a', '(?i', '(?L', '(?m', '(?s', '(?u', '(?x', '(?#']
    if is_overload_constant_str(pat):
        if isinstance(pat, types.StringLiteral):
            pat = pat.literal_value
        return any([(smzib__reykk in pat) for smzib__reykk in vge__rgz])
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
    yapyb__kemwg = re.IGNORECASE.value
    tej__naw = 'def impl(\n'
    tej__naw += '    S_str, pat, case=True, flags=0, na=np.nan, regex=True\n'
    tej__naw += '):\n'
    tej__naw += '  S = S_str._obj\n'
    tej__naw += '  arr = bodo.hiframes.pd_series_ext.get_series_data(S)\n'
    tej__naw += '  index = bodo.hiframes.pd_series_ext.get_series_index(S)\n'
    tej__naw += '  name = bodo.hiframes.pd_series_ext.get_series_name(S)\n'
    tej__naw += '  l = len(arr)\n'
    tej__naw += '  out_arr = bodo.libs.bool_arr_ext.alloc_bool_array(l)\n'
    if is_overload_true(regex):
        if is_regex_unsupported(pat) or flags:
            tej__naw += """  out_arr = bodo.hiframes.series_str_impl.series_contains_regex(S, pat, case, flags, na, regex)
"""
        else:
            tej__naw += """  get_search_regex(arr, case, bodo.libs.str_ext.unicode_to_utf8(pat), out_arr)
"""
    else:
        tej__naw += '  numba.parfors.parfor.init_prange()\n'
        if is_overload_false(case):
            tej__naw += '  upper_pat = pat.upper()\n'
        tej__naw += '  for i in numba.parfors.parfor.internal_prange(l):\n'
        tej__naw += '      if bodo.libs.array_kernels.isna(arr, i):\n'
        tej__naw += '          bodo.libs.array_kernels.setna(out_arr, i)\n'
        tej__naw += '      else: \n'
        if is_overload_true(case):
            tej__naw += '          out_arr[i] = pat in arr[i]\n'
        else:
            tej__naw += '          out_arr[i] = upper_pat in arr[i].upper()\n'
    tej__naw += (
        '  return bodo.hiframes.pd_series_ext.init_series(out_arr, index, name)\n'
        )
    vkkao__tmh = {}
    exec(tej__naw, {'re': re, 'bodo': bodo, 'numba': numba, 'np': np,
        're_ignorecase_value': yapyb__kemwg, 'get_search_regex':
        get_search_regex}, vkkao__tmh)
    impl = vkkao__tmh['impl']
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
    tej__naw = (
        "def impl(S_str, others=None, sep=None, na_rep=None, join='left'):\n")
    tej__naw += '  S = S_str._obj\n'
    tej__naw += '  arr = bodo.hiframes.pd_series_ext.get_series_data(S)\n'
    tej__naw += '  index = bodo.hiframes.pd_series_ext.get_series_index(S)\n'
    tej__naw += '  name = bodo.hiframes.pd_series_ext.get_series_name(S)\n'
    tej__naw += '  l = len(arr)\n'
    for i in range(len(others.columns)):
        tej__naw += (
            f'  data{i} = bodo.hiframes.pd_dataframe_ext.get_dataframe_data(others, {i})\n'
            )
    if S_str.stype.data == bodo.dict_str_arr_type and all(axohx__dfjgo ==
        bodo.dict_str_arr_type for axohx__dfjgo in others.data):
        xei__nbmkr = ', '.join(f'data{i}' for i in range(len(others.columns)))
        tej__naw += (
            f'  out_arr = bodo.libs.dict_arr_ext.cat_dict_str((arr, {xei__nbmkr}), sep)\n'
            )
    else:
        gaq__qvoge = ' or '.join(['bodo.libs.array_kernels.isna(arr, i)'] +
            [f'bodo.libs.array_kernels.isna(data{i}, i)' for i in range(len
            (others.columns))])
        tej__naw += (
            '  out_arr = bodo.libs.str_arr_ext.pre_alloc_string_array(l, -1)\n'
            )
        tej__naw += '  numba.parfors.parfor.init_prange()\n'
        tej__naw += '  for i in numba.parfors.parfor.internal_prange(l):\n'
        tej__naw += f'      if {gaq__qvoge}:\n'
        tej__naw += '          bodo.libs.array_kernels.setna(out_arr, i)\n'
        tej__naw += '          continue\n'
        vwuic__slos = ', '.join(['arr[i]'] + [f'data{i}[i]' for i in range(
            len(others.columns))])
        ypxb__yaejz = "''" if is_overload_none(sep) else 'sep'
        tej__naw += f'      out_arr[i] = {ypxb__yaejz}.join([{vwuic__slos}])\n'
    tej__naw += (
        '  return bodo.hiframes.pd_series_ext.init_series(out_arr, index, name)\n'
        )
    vkkao__tmh = {}
    exec(tej__naw, {'bodo': bodo, 'numba': numba}, vkkao__tmh)
    impl = vkkao__tmh['impl']
    return impl


@overload_method(SeriesStrMethodType, 'count', inline='always',
    no_unliteral=True)
def overload_str_method_count(S_str, pat, flags=0):
    str_arg_check('count', 'pat', pat)
    int_arg_check('count', 'flags', flags)

    def impl(S_str, pat, flags=0):
        S = S_str._obj
        sej__bhrb = bodo.hiframes.pd_series_ext.get_series_data(S)
        uzzpm__pvwvk = bodo.hiframes.pd_series_ext.get_series_name(S)
        voeur__rdpzf = bodo.hiframes.pd_series_ext.get_series_index(S)
        lyh__fgxfg = re.compile(pat, flags)
        numba.parfors.parfor.init_prange()
        bvttc__kwwaa = len(sej__bhrb)
        out_arr = bodo.libs.int_arr_ext.alloc_int_array(bvttc__kwwaa, np.int64)
        for i in numba.parfors.parfor.internal_prange(bvttc__kwwaa):
            if bodo.libs.array_kernels.isna(sej__bhrb, i):
                bodo.libs.array_kernels.setna(out_arr, i)
            else:
                out_arr[i] = str_findall_count(lyh__fgxfg, sej__bhrb[i])
        return bodo.hiframes.pd_series_ext.init_series(out_arr,
            voeur__rdpzf, uzzpm__pvwvk)
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
        sej__bhrb = bodo.hiframes.pd_series_ext.get_series_data(S)
        uzzpm__pvwvk = bodo.hiframes.pd_series_ext.get_series_name(S)
        voeur__rdpzf = bodo.hiframes.pd_series_ext.get_series_index(S)
        numba.parfors.parfor.init_prange()
        bvttc__kwwaa = len(sej__bhrb)
        out_arr = bodo.libs.int_arr_ext.alloc_int_array(bvttc__kwwaa, np.int64)
        for i in numba.parfors.parfor.internal_prange(bvttc__kwwaa):
            if bodo.libs.array_kernels.isna(sej__bhrb, i):
                bodo.libs.array_kernels.setna(out_arr, i)
            else:
                out_arr[i] = sej__bhrb[i].find(sub, start, end)
        return bodo.hiframes.pd_series_ext.init_series(out_arr,
            voeur__rdpzf, uzzpm__pvwvk)
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
        sej__bhrb = bodo.hiframes.pd_series_ext.get_series_data(S)
        uzzpm__pvwvk = bodo.hiframes.pd_series_ext.get_series_name(S)
        voeur__rdpzf = bodo.hiframes.pd_series_ext.get_series_index(S)
        numba.parfors.parfor.init_prange()
        bvttc__kwwaa = len(sej__bhrb)
        out_arr = bodo.libs.int_arr_ext.alloc_int_array(bvttc__kwwaa, np.int64)
        for i in numba.parfors.parfor.internal_prange(bvttc__kwwaa):
            if bodo.libs.array_kernels.isna(sej__bhrb, i):
                bodo.libs.array_kernels.setna(out_arr, i)
            else:
                out_arr[i] = sej__bhrb[i].rfind(sub, start, end)
        return bodo.hiframes.pd_series_ext.init_series(out_arr,
            voeur__rdpzf, uzzpm__pvwvk)
    return impl


@overload_method(SeriesStrMethodType, 'center', inline='always',
    no_unliteral=True)
def overload_str_method_center(S_str, width, fillchar=' '):
    common_validate_padding('center', width, fillchar)

    def impl(S_str, width, fillchar=' '):
        S = S_str._obj
        sej__bhrb = bodo.hiframes.pd_series_ext.get_series_data(S)
        uzzpm__pvwvk = bodo.hiframes.pd_series_ext.get_series_name(S)
        voeur__rdpzf = bodo.hiframes.pd_series_ext.get_series_index(S)
        numba.parfors.parfor.init_prange()
        bvttc__kwwaa = len(sej__bhrb)
        out_arr = bodo.libs.str_arr_ext.pre_alloc_string_array(bvttc__kwwaa, -1
            )
        for vqmuo__ijf in numba.parfors.parfor.internal_prange(bvttc__kwwaa):
            if bodo.libs.array_kernels.isna(sej__bhrb, vqmuo__ijf):
                out_arr[vqmuo__ijf] = ''
                bodo.libs.array_kernels.setna(out_arr, vqmuo__ijf)
            else:
                out_arr[vqmuo__ijf] = sej__bhrb[vqmuo__ijf].center(width,
                    fillchar)
        return bodo.hiframes.pd_series_ext.init_series(out_arr,
            voeur__rdpzf, uzzpm__pvwvk)
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
        sej__bhrb = bodo.hiframes.pd_series_ext.get_series_data(S)
        uzzpm__pvwvk = bodo.hiframes.pd_series_ext.get_series_name(S)
        voeur__rdpzf = bodo.hiframes.pd_series_ext.get_series_index(S)
        numba.parfors.parfor.init_prange()
        bvttc__kwwaa = len(sej__bhrb)
        out_arr = bodo.libs.str_arr_ext.pre_alloc_string_array(bvttc__kwwaa, -1
            )
        for vqmuo__ijf in numba.parfors.parfor.internal_prange(bvttc__kwwaa):
            if bodo.libs.array_kernels.isna(sej__bhrb, vqmuo__ijf):
                bodo.libs.array_kernels.setna(out_arr, vqmuo__ijf)
            else:
                if stop is not None:
                    wxa__nnol = sej__bhrb[vqmuo__ijf][stop:]
                else:
                    wxa__nnol = ''
                out_arr[vqmuo__ijf] = sej__bhrb[vqmuo__ijf][:start
                    ] + repl + wxa__nnol
        return bodo.hiframes.pd_series_ext.init_series(out_arr,
            voeur__rdpzf, uzzpm__pvwvk)
    return impl


@overload_method(SeriesStrMethodType, 'repeat', inline='always',
    no_unliteral=True)
def overload_str_method_repeat(S_str, repeats):
    if isinstance(repeats, types.Integer) or is_overload_constant_int(repeats):

        def impl(S_str, repeats):
            S = S_str._obj
            sej__bhrb = bodo.hiframes.pd_series_ext.get_series_data(S)
            uzzpm__pvwvk = bodo.hiframes.pd_series_ext.get_series_name(S)
            voeur__rdpzf = bodo.hiframes.pd_series_ext.get_series_index(S)
            numba.parfors.parfor.init_prange()
            bvttc__kwwaa = len(sej__bhrb)
            out_arr = bodo.libs.str_arr_ext.pre_alloc_string_array(bvttc__kwwaa
                , -1)
            for vqmuo__ijf in numba.parfors.parfor.internal_prange(bvttc__kwwaa
                ):
                if bodo.libs.array_kernels.isna(sej__bhrb, vqmuo__ijf):
                    bodo.libs.array_kernels.setna(out_arr, vqmuo__ijf)
                else:
                    out_arr[vqmuo__ijf] = sej__bhrb[vqmuo__ijf] * repeats
            return bodo.hiframes.pd_series_ext.init_series(out_arr,
                voeur__rdpzf, uzzpm__pvwvk)
        return impl
    elif is_overload_constant_list(repeats):
        qurhh__ncvdw = get_overload_const_list(repeats)
        pqda__rvej = all([isinstance(buywe__end, int) for buywe__end in
            qurhh__ncvdw])
    elif is_list_like_index_type(repeats) and isinstance(repeats.dtype,
        types.Integer):
        pqda__rvej = True
    else:
        pqda__rvej = False
    if pqda__rvej:

        def impl(S_str, repeats):
            S = S_str._obj
            sej__bhrb = bodo.hiframes.pd_series_ext.get_series_data(S)
            uzzpm__pvwvk = bodo.hiframes.pd_series_ext.get_series_name(S)
            voeur__rdpzf = bodo.hiframes.pd_series_ext.get_series_index(S)
            zeb__gxbvt = bodo.utils.conversion.coerce_to_array(repeats)
            numba.parfors.parfor.init_prange()
            bvttc__kwwaa = len(sej__bhrb)
            out_arr = bodo.libs.str_arr_ext.pre_alloc_string_array(bvttc__kwwaa
                , -1)
            for vqmuo__ijf in numba.parfors.parfor.internal_prange(bvttc__kwwaa
                ):
                if bodo.libs.array_kernels.isna(sej__bhrb, vqmuo__ijf):
                    bodo.libs.array_kernels.setna(out_arr, vqmuo__ijf)
                else:
                    out_arr[vqmuo__ijf] = sej__bhrb[vqmuo__ijf] * zeb__gxbvt[
                        vqmuo__ijf]
            return bodo.hiframes.pd_series_ext.init_series(out_arr,
                voeur__rdpzf, uzzpm__pvwvk)
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
        sej__bhrb = bodo.hiframes.pd_series_ext.get_series_data(S)
        uzzpm__pvwvk = bodo.hiframes.pd_series_ext.get_series_name(S)
        voeur__rdpzf = bodo.hiframes.pd_series_ext.get_series_index(S)
        numba.parfors.parfor.init_prange()
        bvttc__kwwaa = len(sej__bhrb)
        out_arr = bodo.libs.str_arr_ext.pre_alloc_string_array(bvttc__kwwaa, -1
            )
        for vqmuo__ijf in numba.parfors.parfor.internal_prange(bvttc__kwwaa):
            if bodo.libs.array_kernels.isna(sej__bhrb, vqmuo__ijf):
                out_arr[vqmuo__ijf] = ''
                bodo.libs.array_kernels.setna(out_arr, vqmuo__ijf)
            else:
                out_arr[vqmuo__ijf] = sej__bhrb[vqmuo__ijf].ljust(width,
                    fillchar)
        return bodo.hiframes.pd_series_ext.init_series(out_arr,
            voeur__rdpzf, uzzpm__pvwvk)
    return impl


@overload_method(SeriesStrMethodType, 'rjust', inline='always',
    no_unliteral=True)
def overload_str_method_rjust(S_str, width, fillchar=' '):
    common_validate_padding('rjust', width, fillchar)

    def impl(S_str, width, fillchar=' '):
        S = S_str._obj
        sej__bhrb = bodo.hiframes.pd_series_ext.get_series_data(S)
        uzzpm__pvwvk = bodo.hiframes.pd_series_ext.get_series_name(S)
        voeur__rdpzf = bodo.hiframes.pd_series_ext.get_series_index(S)
        numba.parfors.parfor.init_prange()
        bvttc__kwwaa = len(sej__bhrb)
        out_arr = bodo.libs.str_arr_ext.pre_alloc_string_array(bvttc__kwwaa, -1
            )
        for vqmuo__ijf in numba.parfors.parfor.internal_prange(bvttc__kwwaa):
            if bodo.libs.array_kernels.isna(sej__bhrb, vqmuo__ijf):
                out_arr[vqmuo__ijf] = ''
                bodo.libs.array_kernels.setna(out_arr, vqmuo__ijf)
            else:
                out_arr[vqmuo__ijf] = sej__bhrb[vqmuo__ijf].rjust(width,
                    fillchar)
        return bodo.hiframes.pd_series_ext.init_series(out_arr,
            voeur__rdpzf, uzzpm__pvwvk)
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
        sej__bhrb = bodo.hiframes.pd_series_ext.get_series_data(S)
        uzzpm__pvwvk = bodo.hiframes.pd_series_ext.get_series_name(S)
        voeur__rdpzf = bodo.hiframes.pd_series_ext.get_series_index(S)
        numba.parfors.parfor.init_prange()
        bvttc__kwwaa = len(sej__bhrb)
        out_arr = bodo.libs.str_arr_ext.pre_alloc_string_array(bvttc__kwwaa, -1
            )
        for vqmuo__ijf in numba.parfors.parfor.internal_prange(bvttc__kwwaa):
            if bodo.libs.array_kernels.isna(sej__bhrb, vqmuo__ijf):
                out_arr[vqmuo__ijf] = ''
                bodo.libs.array_kernels.setna(out_arr, vqmuo__ijf)
            elif side == 'left':
                out_arr[vqmuo__ijf] = sej__bhrb[vqmuo__ijf].rjust(width,
                    fillchar)
            elif side == 'right':
                out_arr[vqmuo__ijf] = sej__bhrb[vqmuo__ijf].ljust(width,
                    fillchar)
            elif side == 'both':
                out_arr[vqmuo__ijf] = sej__bhrb[vqmuo__ijf].center(width,
                    fillchar)
        return bodo.hiframes.pd_series_ext.init_series(out_arr,
            voeur__rdpzf, uzzpm__pvwvk)
    return impl


@overload_method(SeriesStrMethodType, 'zfill', inline='always',
    no_unliteral=True)
def overload_str_method_zfill(S_str, width):
    int_arg_check('zfill', 'width', width)

    def impl(S_str, width):
        S = S_str._obj
        sej__bhrb = bodo.hiframes.pd_series_ext.get_series_data(S)
        uzzpm__pvwvk = bodo.hiframes.pd_series_ext.get_series_name(S)
        voeur__rdpzf = bodo.hiframes.pd_series_ext.get_series_index(S)
        numba.parfors.parfor.init_prange()
        bvttc__kwwaa = len(sej__bhrb)
        out_arr = bodo.libs.str_arr_ext.pre_alloc_string_array(bvttc__kwwaa, -1
            )
        for vqmuo__ijf in numba.parfors.parfor.internal_prange(bvttc__kwwaa):
            if bodo.libs.array_kernels.isna(sej__bhrb, vqmuo__ijf):
                out_arr[vqmuo__ijf] = ''
                bodo.libs.array_kernels.setna(out_arr, vqmuo__ijf)
            else:
                out_arr[vqmuo__ijf] = sej__bhrb[vqmuo__ijf].zfill(width)
        return bodo.hiframes.pd_series_ext.init_series(out_arr,
            voeur__rdpzf, uzzpm__pvwvk)
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
        sej__bhrb = bodo.hiframes.pd_series_ext.get_series_data(S)
        uzzpm__pvwvk = bodo.hiframes.pd_series_ext.get_series_name(S)
        voeur__rdpzf = bodo.hiframes.pd_series_ext.get_series_index(S)
        numba.parfors.parfor.init_prange()
        bvttc__kwwaa = len(sej__bhrb)
        out_arr = bodo.libs.str_arr_ext.pre_alloc_string_array(bvttc__kwwaa, -1
            )
        for vqmuo__ijf in numba.parfors.parfor.internal_prange(bvttc__kwwaa):
            if bodo.libs.array_kernels.isna(sej__bhrb, vqmuo__ijf):
                out_arr[vqmuo__ijf] = ''
                bodo.libs.array_kernels.setna(out_arr, vqmuo__ijf)
            else:
                out_arr[vqmuo__ijf] = sej__bhrb[vqmuo__ijf][start:stop:step]
        return bodo.hiframes.pd_series_ext.init_series(out_arr,
            voeur__rdpzf, uzzpm__pvwvk)
    return impl


@overload_method(SeriesStrMethodType, 'startswith', inline='always',
    no_unliteral=True)
def overload_str_method_startswith(S_str, pat, na=np.nan):
    not_supported_arg_check('startswith', 'na', na, np.nan)
    str_arg_check('startswith', 'pat', pat)

    def impl(S_str, pat, na=np.nan):
        S = S_str._obj
        sej__bhrb = bodo.hiframes.pd_series_ext.get_series_data(S)
        uzzpm__pvwvk = bodo.hiframes.pd_series_ext.get_series_name(S)
        voeur__rdpzf = bodo.hiframes.pd_series_ext.get_series_index(S)
        numba.parfors.parfor.init_prange()
        bvttc__kwwaa = len(sej__bhrb)
        out_arr = bodo.libs.bool_arr_ext.alloc_bool_array(bvttc__kwwaa)
        for i in numba.parfors.parfor.internal_prange(bvttc__kwwaa):
            if bodo.libs.array_kernels.isna(sej__bhrb, i):
                bodo.libs.array_kernels.setna(out_arr, i)
            else:
                out_arr[i] = sej__bhrb[i].startswith(pat)
        return bodo.hiframes.pd_series_ext.init_series(out_arr,
            voeur__rdpzf, uzzpm__pvwvk)
    return impl


@overload_method(SeriesStrMethodType, 'endswith', inline='always',
    no_unliteral=True)
def overload_str_method_endswith(S_str, pat, na=np.nan):
    not_supported_arg_check('endswith', 'na', na, np.nan)
    str_arg_check('endswith', 'pat', pat)

    def impl(S_str, pat, na=np.nan):
        S = S_str._obj
        sej__bhrb = bodo.hiframes.pd_series_ext.get_series_data(S)
        uzzpm__pvwvk = bodo.hiframes.pd_series_ext.get_series_name(S)
        voeur__rdpzf = bodo.hiframes.pd_series_ext.get_series_index(S)
        numba.parfors.parfor.init_prange()
        bvttc__kwwaa = len(sej__bhrb)
        out_arr = bodo.libs.bool_arr_ext.alloc_bool_array(bvttc__kwwaa)
        for i in numba.parfors.parfor.internal_prange(bvttc__kwwaa):
            if bodo.libs.array_kernels.isna(sej__bhrb, i):
                bodo.libs.array_kernels.setna(out_arr, i)
            else:
                out_arr[i] = sej__bhrb[i].endswith(pat)
        return bodo.hiframes.pd_series_ext.init_series(out_arr,
            voeur__rdpzf, uzzpm__pvwvk)
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
    kll__vezvw, regex = _get_column_names_from_regex(pat, flags, 'extract')
    rtxgj__tqdv = len(kll__vezvw)
    tej__naw = 'def impl(S_str, pat, flags=0, expand=True):\n'
    tej__naw += '  regex = re.compile(pat, flags=flags)\n'
    tej__naw += '  S = S_str._obj\n'
    tej__naw += '  str_arr = bodo.hiframes.pd_series_ext.get_series_data(S)\n'
    tej__naw += '  index = bodo.hiframes.pd_series_ext.get_series_index(S)\n'
    tej__naw += '  name = bodo.hiframes.pd_series_ext.get_series_name(S)\n'
    tej__naw += '  numba.parfors.parfor.init_prange()\n'
    tej__naw += '  n = len(str_arr)\n'
    for i in range(rtxgj__tqdv):
        tej__naw += (
            '  out_arr_{0} = bodo.libs.str_arr_ext.pre_alloc_string_array(n, -1)\n'
            .format(i))
    tej__naw += '  for j in numba.parfors.parfor.internal_prange(n):\n'
    tej__naw += '      if bodo.libs.array_kernels.isna(str_arr, j):\n'
    for i in range(rtxgj__tqdv):
        tej__naw += "          out_arr_{}[j] = ''\n".format(i)
        tej__naw += ('          bodo.libs.array_kernels.setna(out_arr_{}, j)\n'
            .format(i))
    tej__naw += '      else:\n'
    tej__naw += '          m = regex.search(str_arr[j])\n'
    tej__naw += '          if m:\n'
    tej__naw += '            g = m.groups()\n'
    for i in range(rtxgj__tqdv):
        tej__naw += '            out_arr_{0}[j] = g[{0}]\n'.format(i)
    tej__naw += '          else:\n'
    for i in range(rtxgj__tqdv):
        tej__naw += "            out_arr_{}[j] = ''\n".format(i)
        tej__naw += (
            '            bodo.libs.array_kernels.setna(out_arr_{}, j)\n'.
            format(i))
    if is_overload_false(expand) and regex.groups == 1:
        uzzpm__pvwvk = "'{}'".format(list(regex.groupindex.keys()).pop()
            ) if len(regex.groupindex.keys()) > 0 else 'name'
        tej__naw += (
            '  return bodo.hiframes.pd_series_ext.init_series(out_arr_0, index, {})\n'
            .format(uzzpm__pvwvk))
        vkkao__tmh = {}
        exec(tej__naw, {'re': re, 'bodo': bodo, 'numba': numba,
            'get_utf8_size': get_utf8_size}, vkkao__tmh)
        impl = vkkao__tmh['impl']
        return impl
    bcuc__izbgi = ', '.join('out_arr_{}'.format(i) for i in range(rtxgj__tqdv))
    impl = bodo.hiframes.dataframe_impl._gen_init_df(tej__naw, kll__vezvw,
        bcuc__izbgi, 'index', extra_globals={'get_utf8_size': get_utf8_size,
        're': re})
    return impl


@overload_method(SeriesStrMethodType, 'extractall', inline='always',
    no_unliteral=True)
def overload_str_method_extractall(S_str, pat, flags=0):
    kll__vezvw, uih__zifpj = _get_column_names_from_regex(pat, flags,
        'extractall')
    rtxgj__tqdv = len(kll__vezvw)
    ojta__term = isinstance(S_str.stype.index, StringIndexType)
    tej__naw = 'def impl(S_str, pat, flags=0):\n'
    tej__naw += '  regex = re.compile(pat, flags=flags)\n'
    tej__naw += '  S = S_str._obj\n'
    tej__naw += '  str_arr = bodo.hiframes.pd_series_ext.get_series_data(S)\n'
    tej__naw += '  index = bodo.hiframes.pd_series_ext.get_series_index(S)\n'
    tej__naw += '  name = bodo.hiframes.pd_series_ext.get_series_name(S)\n'
    tej__naw += '  index_arr = bodo.utils.conversion.index_to_array(index)\n'
    tej__naw += (
        '  index_name = bodo.hiframes.pd_index_ext.get_index_name(index)\n')
    tej__naw += '  numba.parfors.parfor.init_prange()\n'
    tej__naw += '  n = len(str_arr)\n'
    tej__naw += '  out_n_l = [0]\n'
    for i in range(rtxgj__tqdv):
        tej__naw += '  num_chars_{} = 0\n'.format(i)
    if ojta__term:
        tej__naw += '  index_num_chars = 0\n'
    tej__naw += '  for i in numba.parfors.parfor.internal_prange(n):\n'
    if ojta__term:
        tej__naw += '      index_num_chars += get_utf8_size(index_arr[i])\n'
    tej__naw += '      if bodo.libs.array_kernels.isna(str_arr, i):\n'
    tej__naw += '          continue\n'
    tej__naw += '      m = regex.findall(str_arr[i])\n'
    tej__naw += '      out_n_l[0] += len(m)\n'
    for i in range(rtxgj__tqdv):
        tej__naw += '      l_{} = 0\n'.format(i)
    tej__naw += '      for s in m:\n'
    for i in range(rtxgj__tqdv):
        tej__naw += '        l_{} += get_utf8_size(s{})\n'.format(i, '[{}]'
            .format(i) if rtxgj__tqdv > 1 else '')
    for i in range(rtxgj__tqdv):
        tej__naw += '      num_chars_{0} += l_{0}\n'.format(i)
    tej__naw += (
        '  out_n = bodo.libs.distributed_api.local_alloc_size(out_n_l[0], str_arr)\n'
        )
    for i in range(rtxgj__tqdv):
        tej__naw += (
            """  out_arr_{0} = bodo.libs.str_arr_ext.pre_alloc_string_array(out_n, num_chars_{0})
"""
            .format(i))
    if ojta__term:
        tej__naw += """  out_ind_arr = bodo.libs.str_arr_ext.pre_alloc_string_array(out_n, index_num_chars)
"""
    else:
        tej__naw += '  out_ind_arr = np.empty(out_n, index_arr.dtype)\n'
    tej__naw += '  out_match_arr = np.empty(out_n, np.int64)\n'
    tej__naw += '  out_ind = 0\n'
    tej__naw += '  for j in numba.parfors.parfor.internal_prange(n):\n'
    tej__naw += '      if bodo.libs.array_kernels.isna(str_arr, j):\n'
    tej__naw += '          continue\n'
    tej__naw += '      m = regex.findall(str_arr[j])\n'
    tej__naw += '      for k, s in enumerate(m):\n'
    for i in range(rtxgj__tqdv):
        tej__naw += (
            '        bodo.libs.distributed_api.set_arr_local(out_arr_{}, out_ind, s{})\n'
            .format(i, '[{}]'.format(i) if rtxgj__tqdv > 1 else ''))
    tej__naw += """        bodo.libs.distributed_api.set_arr_local(out_ind_arr, out_ind, index_arr[j])
"""
    tej__naw += (
        '        bodo.libs.distributed_api.set_arr_local(out_match_arr, out_ind, k)\n'
        )
    tej__naw += '        out_ind += 1\n'
    tej__naw += (
        '  out_index = bodo.hiframes.pd_multi_index_ext.init_multi_index(\n')
    tej__naw += "    (out_ind_arr, out_match_arr), (index_name, 'match'))\n"
    bcuc__izbgi = ', '.join('out_arr_{}'.format(i) for i in range(rtxgj__tqdv))
    impl = bodo.hiframes.dataframe_impl._gen_init_df(tej__naw, kll__vezvw,
        bcuc__izbgi, 'out_index', extra_globals={'get_utf8_size':
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
    llp__symmp = dict(zip(regex.groupindex.values(), regex.groupindex.keys()))
    kll__vezvw = [llp__symmp.get(1 + i, i) for i in range(regex.groups)]
    return kll__vezvw, regex


def create_str2str_methods_overload(func_name):
    if func_name in ['lstrip', 'rstrip', 'strip']:
        tej__naw = 'def f(S_str, to_strip=None):\n'
    else:
        tej__naw = 'def f(S_str):\n'
    tej__naw += '    S = S_str._obj\n'
    tej__naw += (
        '    str_arr = bodo.hiframes.pd_series_ext.get_series_data(S)\n')
    tej__naw += '    str_arr = decode_if_dict_array(str_arr)\n'
    tej__naw += '    index = bodo.hiframes.pd_series_ext.get_series_index(S)\n'
    tej__naw += '    name = bodo.hiframes.pd_series_ext.get_series_name(S)\n'
    tej__naw += '    numba.parfors.parfor.init_prange()\n'
    tej__naw += '    n = len(str_arr)\n'
    if func_name in ('capitalize', 'lower', 'swapcase', 'title', 'upper'):
        tej__naw += '    num_chars = num_total_chars(str_arr)\n'
    else:
        tej__naw += '    num_chars = -1\n'
    tej__naw += (
        '    out_arr = bodo.libs.str_arr_ext.pre_alloc_string_array(n, num_chars)\n'
        )
    tej__naw += '    for j in numba.parfors.parfor.internal_prange(n):\n'
    tej__naw += '        if bodo.libs.array_kernels.isna(str_arr, j):\n'
    tej__naw += '            out_arr[j] = ""\n'
    tej__naw += '            bodo.libs.array_kernels.setna(out_arr, j)\n'
    tej__naw += '        else:\n'
    if func_name in ['lstrip', 'rstrip', 'strip']:
        tej__naw += ('            out_arr[j] = str_arr[j].{}(to_strip)\n'.
            format(func_name))
    else:
        tej__naw += '            out_arr[j] = str_arr[j].{}()\n'.format(
            func_name)
    tej__naw += (
        '    return bodo.hiframes.pd_series_ext.init_series(out_arr, index, name)\n'
        )
    vkkao__tmh = {}
    exec(tej__naw, {'bodo': bodo, 'numba': numba, 'num_total_chars': bodo.
        libs.str_arr_ext.num_total_chars, 'get_utf8_size': bodo.libs.
        str_arr_ext.get_utf8_size, 'decode_if_dict_array': bodo.utils.
        typing.decode_if_dict_array}, vkkao__tmh)
    qyey__okj = vkkao__tmh['f']
    if func_name in ['lstrip', 'rstrip', 'strip']:

        def overload_strip_method(S_str, to_strip=None):
            if not is_overload_none(to_strip):
                str_arg_check(func_name, 'to_strip', to_strip)
            return qyey__okj
        return overload_strip_method
    else:

        def overload_str2str_methods(S_str):
            return qyey__okj
        return overload_str2str_methods


def create_str2bool_methods_overload(func_name):

    def overload_str2bool_methods(S_str):
        tej__naw = 'def f(S_str):\n'
        tej__naw += '    S = S_str._obj\n'
        tej__naw += (
            '    str_arr = bodo.hiframes.pd_series_ext.get_series_data(S)\n')
        tej__naw += (
            '    index = bodo.hiframes.pd_series_ext.get_series_index(S)\n')
        tej__naw += (
            '    name = bodo.hiframes.pd_series_ext.get_series_name(S)\n')
        tej__naw += '    numba.parfors.parfor.init_prange()\n'
        tej__naw += '    l = len(str_arr)\n'
        tej__naw += (
            '    out_arr = bodo.libs.bool_arr_ext.alloc_bool_array(l)\n')
        tej__naw += '    for i in numba.parfors.parfor.internal_prange(l):\n'
        tej__naw += '        if bodo.libs.array_kernels.isna(str_arr, i):\n'
        tej__naw += '            bodo.libs.array_kernels.setna(out_arr, i)\n'
        tej__naw += '        else:\n'
        tej__naw += ('            out_arr[i] = np.bool_(str_arr[i].{}())\n'
            .format(func_name))
        tej__naw += '    return bodo.hiframes.pd_series_ext.init_series(\n'
        tej__naw += '      out_arr,index, name)\n'
        vkkao__tmh = {}
        exec(tej__naw, {'bodo': bodo, 'numba': numba, 'np': np}, vkkao__tmh)
        qyey__okj = vkkao__tmh['f']
        return qyey__okj
    return overload_str2bool_methods


def _install_str2str_methods():
    for lrkmd__jdz in bodo.hiframes.pd_series_ext.str2str_methods:
        mmxp__cab = create_str2str_methods_overload(lrkmd__jdz)
        overload_method(SeriesStrMethodType, lrkmd__jdz, inline='always',
            no_unliteral=True)(mmxp__cab)


def _install_str2bool_methods():
    for lrkmd__jdz in bodo.hiframes.pd_series_ext.str2bool_methods:
        mmxp__cab = create_str2bool_methods_overload(lrkmd__jdz)
        overload_method(SeriesStrMethodType, lrkmd__jdz, inline='always',
            no_unliteral=True)(mmxp__cab)


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
        uzzpm__pvwvk = 'SeriesCatMethodType({})'.format(stype)
        super(SeriesCatMethodType, self).__init__(uzzpm__pvwvk)

    @property
    def mangling_args(self):
        return self.__class__.__name__, (self._code,)


@register_model(SeriesCatMethodType)
class SeriesCatModel(models.StructModel):

    def __init__(self, dmm, fe_type):
        jlry__rzsch = [('obj', fe_type.stype)]
        super(SeriesCatModel, self).__init__(dmm, fe_type, jlry__rzsch)


make_attribute_wrapper(SeriesCatMethodType, 'obj', '_obj')


@intrinsic
def init_series_cat_method(typingctx, obj=None):

    def codegen(context, builder, signature, args):
        etbvv__cfdo, = args
        zpoio__nhqy = signature.return_type
        zsp__yvk = cgutils.create_struct_proxy(zpoio__nhqy)(context, builder)
        zsp__yvk.obj = etbvv__cfdo
        context.nrt.incref(builder, signature.args[0], etbvv__cfdo)
        return zsp__yvk._getvalue()
    return SeriesCatMethodType(obj)(obj), codegen


@overload_attribute(SeriesCatMethodType, 'codes')
def series_cat_codes_overload(S_dt):

    def impl(S_dt):
        S = S_dt._obj
        pqgi__tjkhd = bodo.hiframes.pd_series_ext.get_series_data(S)
        voeur__rdpzf = bodo.hiframes.pd_series_ext.get_series_index(S)
        uzzpm__pvwvk = None
        return bodo.hiframes.pd_series_ext.init_series(bodo.hiframes.
            pd_categorical_ext.get_categorical_arr_codes(pqgi__tjkhd),
            voeur__rdpzf, uzzpm__pvwvk)
    return impl


unsupported_cat_attrs = {'categories', 'ordered'}
unsupported_cat_methods = {'rename_categories', 'reorder_categories',
    'add_categories', 'remove_categories', 'remove_unused_categories',
    'set_categories', 'as_ordered', 'as_unordered'}


def _install_catseries_unsupported():
    for gbo__gxbtm in unsupported_cat_attrs:
        jjpfc__bmue = 'Series.cat.' + gbo__gxbtm
        overload_attribute(SeriesCatMethodType, gbo__gxbtm)(
            create_unsupported_overload(jjpfc__bmue))
    for aooq__hvtqa in unsupported_cat_methods:
        jjpfc__bmue = 'Series.cat.' + aooq__hvtqa
        overload_method(SeriesCatMethodType, aooq__hvtqa)(
            create_unsupported_overload(jjpfc__bmue))


_install_catseries_unsupported()
unsupported_str_methods = {'casefold', 'decode', 'encode', 'findall',
    'fullmatch', 'index', 'match', 'normalize', 'partition', 'rindex',
    'rpartition', 'slice_replace', 'rsplit', 'translate', 'wrap', 'get_dummies'
    }


def _install_strseries_unsupported():
    for aooq__hvtqa in unsupported_str_methods:
        jjpfc__bmue = 'Series.str.' + aooq__hvtqa
        overload_method(SeriesStrMethodType, aooq__hvtqa)(
            create_unsupported_overload(jjpfc__bmue))


_install_strseries_unsupported()
