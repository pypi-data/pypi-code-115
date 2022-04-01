"""
Indexing support for pd.DataFrame type.
"""
import operator
import numpy as np
import pandas as pd
from numba.core import cgutils, types
from numba.core.typing.templates import AbstractTemplate, infer_global
from numba.extending import intrinsic, lower_builtin, lower_cast, make_attribute_wrapper, models, overload, overload_attribute, register_model
import bodo
from bodo.hiframes.pd_dataframe_ext import DataFrameType, check_runtime_cols_unsupported
from bodo.utils.transform import gen_const_tup
from bodo.utils.typing import BodoError, get_overload_const_int, get_overload_const_list, get_overload_const_str, is_immutable_array, is_list_like_index_type, is_overload_constant_int, is_overload_constant_list, is_overload_constant_str, raise_bodo_error


@infer_global(operator.getitem)
class DataFrameGetItemTemplate(AbstractTemplate):

    def generic(self, args, kws):
        assert not kws
        assert len(args) == 2
        check_runtime_cols_unsupported(args[0], 'DataFrame getitem (df[])')
        if isinstance(args[0], DataFrameType):
            return self.typecheck_df_getitem(args)
        elif isinstance(args[0], DataFrameLocType):
            return self.typecheck_loc_getitem(args)
        else:
            return

    def typecheck_loc_getitem(self, args):
        I = args[0]
        idx = args[1]
        df = I.df_type
        if isinstance(df.columns[0], tuple):
            raise_bodo_error(
                'DataFrame.loc[] getitem (location-based indexing) with multi-indexed columns not supported yet'
                )
        if is_list_like_index_type(idx) and idx.dtype == types.bool_:
            olb__qjg = idx
            itvci__agh = df.data
            snnl__erty = df.columns
            wpd__njtxc = self.replace_range_with_numeric_idx_if_needed(df,
                olb__qjg)
            epsn__fst = DataFrameType(itvci__agh, wpd__njtxc, snnl__erty)
            return epsn__fst(*args)
        if isinstance(idx, types.BaseTuple) and len(idx) == 2:
            kbqfo__aho = idx.types[0]
            wxk__ehxf = idx.types[1]
            if isinstance(kbqfo__aho, types.Integer):
                if not isinstance(df.index, bodo.hiframes.pd_index_ext.
                    RangeIndexType):
                    raise_bodo_error(
                        'Dataframe.loc[int, col_ind] getitem only supported for dataframes with RangeIndexes'
                        )
                if is_overload_constant_str(wxk__ehxf):
                    eipvc__ogjtu = get_overload_const_str(wxk__ehxf)
                    if eipvc__ogjtu not in df.columns:
                        raise_bodo_error(
                            'dataframe {} does not include column {}'.
                            format(df, eipvc__ogjtu))
                    ysuce__ebf = df.columns.index(eipvc__ogjtu)
                    return df.data[ysuce__ebf].dtype(*args)
                if isinstance(wxk__ehxf, types.UnicodeType):
                    raise_bodo_error(
                        f'DataFrame.loc[] getitem (location-based indexing) requires constant column names. For more information, see https://docs.bodo.ai/latest/source/programming_with_bodo/require_constants.html.'
                        )
                else:
                    raise_bodo_error(
                        f'DataFrame.loc[] getitem (location-based indexing) using {idx} not supported yet.'
                        )
            if is_list_like_index_type(kbqfo__aho
                ) and kbqfo__aho.dtype == types.bool_ or isinstance(kbqfo__aho,
                types.SliceType):
                wpd__njtxc = self.replace_range_with_numeric_idx_if_needed(df,
                    kbqfo__aho)
                if is_overload_constant_str(wxk__ehxf):
                    ktzn__amdg = get_overload_const_str(wxk__ehxf)
                    if ktzn__amdg not in df.columns:
                        raise_bodo_error(
                            f'dataframe {df} does not include column {ktzn__amdg}'
                            )
                    ysuce__ebf = df.columns.index(ktzn__amdg)
                    hbits__fgn = df.data[ysuce__ebf]
                    fex__cxv = hbits__fgn.dtype
                    lcvd__zcia = types.literal(df.columns[ysuce__ebf])
                    epsn__fst = bodo.SeriesType(fex__cxv, hbits__fgn,
                        wpd__njtxc, lcvd__zcia)
                    return epsn__fst(*args)
                if isinstance(wxk__ehxf, types.UnicodeType):
                    raise_bodo_error(
                        f'DataFrame.loc[] getitem (location-based indexing) requires constant column names. For more information, see https://docs.bodo.ai/latest/source/programming_with_bodo/require_constants.html.'
                        )
                elif is_overload_constant_list(wxk__ehxf):
                    msn__ztyt = get_overload_const_list(wxk__ehxf)
                    fkrqn__aahny = types.unliteral(wxk__ehxf)
                    if fkrqn__aahny.dtype == types.bool_:
                        if len(df.columns) != len(msn__ztyt):
                            raise_bodo_error(
                                f'dataframe {df} has {len(df.columns)} columns, but boolean array used with DataFrame.loc[] {msn__ztyt} has {len(msn__ztyt)} values'
                                )
                        yfpa__uwlk = []
                        lbv__uoj = []
                        for crzbg__tolr in range(len(msn__ztyt)):
                            if msn__ztyt[crzbg__tolr]:
                                yfpa__uwlk.append(df.columns[crzbg__tolr])
                                lbv__uoj.append(df.data[crzbg__tolr])
                        ikg__cjyz = tuple()
                        epsn__fst = DataFrameType(tuple(lbv__uoj),
                            wpd__njtxc, tuple(yfpa__uwlk))
                        return epsn__fst(*args)
                    elif fkrqn__aahny.dtype == bodo.string_type:
                        ikg__cjyz, lbv__uoj = self.get_kept_cols_and_data(df,
                            msn__ztyt)
                        epsn__fst = DataFrameType(lbv__uoj, wpd__njtxc,
                            ikg__cjyz)
                        return epsn__fst(*args)
        raise_bodo_error(
            f'DataFrame.loc[] getitem (location-based indexing) using {idx} not supported yet. If you are trying to select a subset of the columns by passing a list of column names, that list must be a compile time constant. See https://docs.bodo.ai/latest/source/programming_with_bodo/require_constants.html.'
            )

    def typecheck_df_getitem(self, args):
        df = args[0]
        ind = args[1]
        if is_overload_constant_str(ind) or is_overload_constant_int(ind):
            ind_val = get_overload_const_str(ind) if is_overload_constant_str(
                ind) else get_overload_const_int(ind)
            if isinstance(df.columns[0], tuple):
                yfpa__uwlk = []
                lbv__uoj = []
                for crzbg__tolr, aisd__lna in enumerate(df.columns):
                    if aisd__lna[0] != ind_val:
                        continue
                    yfpa__uwlk.append(aisd__lna[1] if len(aisd__lna) == 2 else
                        aisd__lna[1:])
                    lbv__uoj.append(df.data[crzbg__tolr])
                hbits__fgn = tuple(lbv__uoj)
                bpaqz__bxxhb = df.index
                xvfw__bqlkx = tuple(yfpa__uwlk)
                epsn__fst = DataFrameType(hbits__fgn, bpaqz__bxxhb, xvfw__bqlkx
                    )
                return epsn__fst(*args)
            else:
                if ind_val not in df.columns:
                    raise_bodo_error('dataframe {} does not include column {}'
                        .format(df, ind_val))
                ysuce__ebf = df.columns.index(ind_val)
                hbits__fgn = df.data[ysuce__ebf]
                fex__cxv = hbits__fgn.dtype
                bpaqz__bxxhb = df.index
                lcvd__zcia = types.literal(df.columns[ysuce__ebf])
                epsn__fst = bodo.SeriesType(fex__cxv, hbits__fgn,
                    bpaqz__bxxhb, lcvd__zcia)
                return epsn__fst(*args)
        if isinstance(ind, types.Integer) or isinstance(ind, types.UnicodeType
            ):
            raise_bodo_error(
                'df[] getitem selecting a subset of columns requires providing constant column names. For more information, see https://docs.bodo.ai/latest/source/programming_with_bodo/require_constants.html'
                )
        if is_list_like_index_type(ind
            ) and ind.dtype == types.bool_ or isinstance(ind, types.SliceType):
            hbits__fgn = df.data
            bpaqz__bxxhb = self.replace_range_with_numeric_idx_if_needed(df,
                ind)
            xvfw__bqlkx = df.columns
            epsn__fst = DataFrameType(hbits__fgn, bpaqz__bxxhb, xvfw__bqlkx,
                is_table_format=df.is_table_format)
            return epsn__fst(*args)
        elif is_overload_constant_list(ind):
            utes__vrh = get_overload_const_list(ind)
            xvfw__bqlkx, hbits__fgn = self.get_kept_cols_and_data(df, utes__vrh
                )
            bpaqz__bxxhb = df.index
            epsn__fst = DataFrameType(hbits__fgn, bpaqz__bxxhb, xvfw__bqlkx)
            return epsn__fst(*args)
        raise_bodo_error(
            f'df[] getitem using {ind} not supported. If you are trying to select a subset of the columns, you must provide the column names you are selecting as a constant. See https://docs.bodo.ai/latest/source/programming_with_bodo/require_constants.html'
            )

    def get_kept_cols_and_data(self, df, cols_to_keep_list):
        for uhgb__avuw in cols_to_keep_list:
            if uhgb__avuw not in df.columns:
                raise_bodo_error('Column {} not found in dataframe columns {}'
                    .format(uhgb__avuw, df.columns))
        xvfw__bqlkx = tuple(cols_to_keep_list)
        hbits__fgn = tuple(df.data[df.columns.index(ghfby__baz)] for
            ghfby__baz in xvfw__bqlkx)
        return xvfw__bqlkx, hbits__fgn

    def replace_range_with_numeric_idx_if_needed(self, df, ind):
        wpd__njtxc = bodo.hiframes.pd_index_ext.NumericIndexType(types.
            int64, df.index.name_typ) if not isinstance(ind, types.SliceType
            ) and isinstance(df.index, bodo.hiframes.pd_index_ext.
            RangeIndexType) else df.index
        return wpd__njtxc


DataFrameGetItemTemplate._no_unliteral = True


@lower_builtin(operator.getitem, DataFrameType, types.Any)
def getitem_df_lower(context, builder, sig, args):
    impl = df_getitem_overload(*sig.args)
    return context.compile_internal(builder, impl, sig, args)


def df_getitem_overload(df, ind):
    if not isinstance(df, DataFrameType):
        return
    if is_overload_constant_str(ind) or is_overload_constant_int(ind):
        ind_val = get_overload_const_str(ind) if is_overload_constant_str(ind
            ) else get_overload_const_int(ind)
        if isinstance(df.columns[0], tuple):
            yfpa__uwlk = []
            lbv__uoj = []
            for crzbg__tolr, aisd__lna in enumerate(df.columns):
                if aisd__lna[0] != ind_val:
                    continue
                yfpa__uwlk.append(aisd__lna[1] if len(aisd__lna) == 2 else
                    aisd__lna[1:])
                lbv__uoj.append(
                    'bodo.hiframes.pd_dataframe_ext.get_dataframe_data(df, {})'
                    .format(crzbg__tolr))
            jmbx__mqiy = 'def impl(df, ind):\n'
            fbjh__ads = (
                'bodo.hiframes.pd_dataframe_ext.get_dataframe_index(df)')
            return bodo.hiframes.dataframe_impl._gen_init_df(jmbx__mqiy,
                yfpa__uwlk, ', '.join(lbv__uoj), fbjh__ads)
        if ind_val not in df.columns:
            raise_bodo_error('dataframe {} does not include column {}'.
                format(df, ind_val))
        col_no = df.columns.index(ind_val)
        return lambda df, ind: bodo.hiframes.pd_series_ext.init_series(bodo
            .hiframes.pd_dataframe_ext.get_dataframe_data(df, col_no), bodo
            .hiframes.pd_dataframe_ext.get_dataframe_index(df), ind_val)
    if is_overload_constant_list(ind):
        utes__vrh = get_overload_const_list(ind)
        for uhgb__avuw in utes__vrh:
            if uhgb__avuw not in df.columns:
                raise_bodo_error('Column {} not found in dataframe columns {}'
                    .format(uhgb__avuw, df.columns))
        lbv__uoj = ', '.join(
            'bodo.hiframes.pd_dataframe_ext.get_dataframe_data(df, {}).copy()'
            .format(df.columns.index(uhgb__avuw)) for uhgb__avuw in utes__vrh)
        jmbx__mqiy = 'def impl(df, ind):\n'
        fbjh__ads = 'bodo.hiframes.pd_dataframe_ext.get_dataframe_index(df)'
        return bodo.hiframes.dataframe_impl._gen_init_df(jmbx__mqiy,
            utes__vrh, lbv__uoj, fbjh__ads)
    if is_list_like_index_type(ind) and ind.dtype == types.bool_ or isinstance(
        ind, types.SliceType):
        jmbx__mqiy = 'def impl(df, ind):\n'
        if not isinstance(ind, types.SliceType):
            jmbx__mqiy += (
                '  ind = bodo.utils.conversion.coerce_to_ndarray(ind)\n')
        fbjh__ads = (
            'bodo.hiframes.pd_dataframe_ext.get_dataframe_index(df)[ind]')
        if df.is_table_format:
            lbv__uoj = (
                f'bodo.hiframes.pd_dataframe_ext.get_dataframe_table(df)[ind]')
        else:
            lbv__uoj = ', '.join(
                f'bodo.hiframes.pd_dataframe_ext.get_dataframe_data(df, {df.columns.index(uhgb__avuw)})[ind]'
                 for uhgb__avuw in df.columns)
        return bodo.hiframes.dataframe_impl._gen_init_df(jmbx__mqiy, df.
            columns, lbv__uoj, fbjh__ads, out_df_type=df)
    raise_bodo_error('df[] getitem using {} not supported'.format(ind))


@overload(operator.setitem, no_unliteral=True)
def df_setitem_overload(df, idx, val):
    check_runtime_cols_unsupported(df, 'DataFrame setitem (df[])')
    if not isinstance(df, DataFrameType):
        return
    raise_bodo_error('DataFrame setitem: transform necessary')


class DataFrameILocType(types.Type):

    def __init__(self, df_type):
        self.df_type = df_type
        ghfby__baz = 'DataFrameILocType({})'.format(df_type)
        super(DataFrameILocType, self).__init__(ghfby__baz)

    @property
    def mangling_args(self):
        return self.__class__.__name__, (self._code,)
    ndim = 2


@register_model(DataFrameILocType)
class DataFrameILocModel(models.StructModel):

    def __init__(self, dmm, fe_type):
        svp__acl = [('obj', fe_type.df_type)]
        super(DataFrameILocModel, self).__init__(dmm, fe_type, svp__acl)


make_attribute_wrapper(DataFrameILocType, 'obj', '_obj')


@intrinsic
def init_dataframe_iloc(typingctx, obj=None):

    def codegen(context, builder, signature, args):
        wvws__fkzte, = args
        ktv__vrjb = signature.return_type
        avhyl__sjves = cgutils.create_struct_proxy(ktv__vrjb)(context, builder)
        avhyl__sjves.obj = wvws__fkzte
        context.nrt.incref(builder, signature.args[0], wvws__fkzte)
        return avhyl__sjves._getvalue()
    return DataFrameILocType(obj)(obj), codegen


@overload_attribute(DataFrameType, 'iloc')
def overload_dataframe_iloc(df):
    check_runtime_cols_unsupported(df, 'DataFrame.iloc')
    return lambda df: bodo.hiframes.dataframe_indexing.init_dataframe_iloc(df)


@overload(operator.getitem, no_unliteral=True)
def overload_iloc_getitem(I, idx):
    if not isinstance(I, DataFrameILocType):
        return
    df = I.df_type
    if isinstance(idx, types.Integer):
        return _gen_iloc_getitem_row_impl(df, df.columns, 'idx')
    if isinstance(idx, types.BaseTuple) and len(idx) == 2 and not isinstance(
        idx[1], types.SliceType):
        if not (is_overload_constant_list(idx.types[1]) or
            is_overload_constant_int(idx.types[1])):
            raise_bodo_error(
                'idx2 in df.iloc[idx1, idx2] should be a constant integer or constant list of integers. For more information, see https://docs.bodo.ai/latest/source/programming_with_bodo/require_constants.html.'
                )
        wkb__yah = len(df.data)
        if is_overload_constant_int(idx.types[1]):
            is_out_series = True
            gcvjb__vqlwy = get_overload_const_int(idx.types[1])
            if gcvjb__vqlwy < 0 or gcvjb__vqlwy >= wkb__yah:
                raise BodoError(
                    'df.iloc: column integer must refer to a valid column number'
                    )
            oqgkz__bsuo = [gcvjb__vqlwy]
        else:
            is_out_series = False
            oqgkz__bsuo = get_overload_const_list(idx.types[1])
            if any(not isinstance(ind, int) or ind < 0 or ind >= wkb__yah for
                ind in oqgkz__bsuo):
                raise BodoError(
                    'df.iloc: column list must be integers referring to a valid column number'
                    )
        col_names = tuple(pd.Series(df.columns, dtype=object)[oqgkz__bsuo])
        if isinstance(idx.types[0], types.Integer):
            if isinstance(idx.types[1], types.Integer):
                gcvjb__vqlwy = oqgkz__bsuo[0]

                def impl(I, idx):
                    df = I._obj
                    return bodo.utils.conversion.box_if_dt64(bodo.hiframes.
                        pd_dataframe_ext.get_dataframe_data(df,
                        gcvjb__vqlwy)[idx[0]])
                return impl
            return _gen_iloc_getitem_row_impl(df, col_names, 'idx[0]')
        if is_list_like_index_type(idx.types[0]) and isinstance(idx.types[0
            ].dtype, (types.Integer, types.Boolean)) or isinstance(idx.
            types[0], types.SliceType):
            return _gen_iloc_getitem_bool_slice_impl(df, col_names, idx.
                types[0], 'idx[0]', is_out_series)
    if is_list_like_index_type(idx) and isinstance(idx.dtype, (types.
        Integer, types.Boolean)) or isinstance(idx, types.SliceType):
        return _gen_iloc_getitem_bool_slice_impl(df, df.columns, idx, 'idx',
            False)
    if isinstance(idx, types.BaseTuple) and len(idx) == 2 and isinstance(idx
        [0], types.SliceType) and isinstance(idx[1], types.SliceType):
        raise_bodo_error(
            'slice2 in df.iloc[slice1,slice2] should be constant. For more information, see https://docs.bodo.ai/latest/source/programming_with_bodo/require_constants.html.'
            )
    raise_bodo_error(f'df.iloc[] getitem using {idx} not supported')


def _gen_iloc_getitem_bool_slice_impl(df, col_names, idx_typ, idx,
    is_out_series):
    jmbx__mqiy = 'def impl(I, idx):\n'
    jmbx__mqiy += '  df = I._obj\n'
    if isinstance(idx_typ, types.SliceType):
        jmbx__mqiy += f'  idx_t = {idx}\n'
    else:
        jmbx__mqiy += (
            f'  idx_t = bodo.utils.conversion.coerce_to_ndarray({idx})\n')
    fbjh__ads = 'bodo.hiframes.pd_dataframe_ext.get_dataframe_index(df)[idx_t]'
    lbv__uoj = ', '.join(
        f'bodo.hiframes.pd_dataframe_ext.get_dataframe_data(df, {df.columns.index(uhgb__avuw)})[idx_t]'
         for uhgb__avuw in col_names)
    if is_out_series:
        eayzp__djqv = f"'{col_names[0]}'" if isinstance(col_names[0], str
            ) else f'{col_names[0]}'
        jmbx__mqiy += f"""  return bodo.hiframes.pd_series_ext.init_series({lbv__uoj}, {fbjh__ads}, {eayzp__djqv})
"""
        pzqmm__lsa = {}
        exec(jmbx__mqiy, {'bodo': bodo}, pzqmm__lsa)
        return pzqmm__lsa['impl']
    return bodo.hiframes.dataframe_impl._gen_init_df(jmbx__mqiy, col_names,
        lbv__uoj, fbjh__ads)


def _gen_iloc_getitem_row_impl(df, col_names, idx):
    jmbx__mqiy = 'def impl(I, idx):\n'
    jmbx__mqiy += '  df = I._obj\n'
    pwp__gjtc = ', '.join(
        f'bodo.hiframes.pd_dataframe_ext.get_dataframe_data(df, {df.columns.index(uhgb__avuw)})[{idx}]'
         for uhgb__avuw in col_names)
    jmbx__mqiy += f"""  row_idx = bodo.hiframes.pd_index_ext.init_heter_index({gen_const_tup(col_names)}, None)
"""
    jmbx__mqiy += f"""  return bodo.hiframes.pd_series_ext.init_series(({pwp__gjtc},), row_idx, None)
"""
    pzqmm__lsa = {}
    exec(jmbx__mqiy, {'bodo': bodo}, pzqmm__lsa)
    impl = pzqmm__lsa['impl']
    return impl


@overload(operator.setitem, no_unliteral=True)
def df_iloc_setitem_overload(df, idx, val):
    if not isinstance(df, DataFrameILocType):
        return
    raise_bodo_error(
        f'DataFrame.iloc setitem unsupported for dataframe {df.df_type}, index {idx}, value {val}'
        )


class DataFrameLocType(types.Type):

    def __init__(self, df_type):
        self.df_type = df_type
        ghfby__baz = 'DataFrameLocType({})'.format(df_type)
        super(DataFrameLocType, self).__init__(ghfby__baz)

    @property
    def mangling_args(self):
        return self.__class__.__name__, (self._code,)
    ndim = 2


@register_model(DataFrameLocType)
class DataFrameLocModel(models.StructModel):

    def __init__(self, dmm, fe_type):
        svp__acl = [('obj', fe_type.df_type)]
        super(DataFrameLocModel, self).__init__(dmm, fe_type, svp__acl)


make_attribute_wrapper(DataFrameLocType, 'obj', '_obj')


@intrinsic
def init_dataframe_loc(typingctx, obj=None):

    def codegen(context, builder, signature, args):
        wvws__fkzte, = args
        ymkli__mprfg = signature.return_type
        czai__pdi = cgutils.create_struct_proxy(ymkli__mprfg)(context, builder)
        czai__pdi.obj = wvws__fkzte
        context.nrt.incref(builder, signature.args[0], wvws__fkzte)
        return czai__pdi._getvalue()
    return DataFrameLocType(obj)(obj), codegen


@overload_attribute(DataFrameType, 'loc')
def overload_dataframe_loc(df):
    check_runtime_cols_unsupported(df, 'DataFrame.loc')
    return lambda df: bodo.hiframes.dataframe_indexing.init_dataframe_loc(df)


@lower_builtin(operator.getitem, DataFrameLocType, types.Any)
def loc_getitem_lower(context, builder, sig, args):
    impl = overload_loc_getitem(*sig.args)
    return context.compile_internal(builder, impl, sig, args)


def overload_loc_getitem(I, idx):
    if not isinstance(I, DataFrameLocType):
        return
    df = I.df_type
    if is_list_like_index_type(idx) and idx.dtype == types.bool_:
        jmbx__mqiy = 'def impl(I, idx):\n'
        jmbx__mqiy += '  df = I._obj\n'
        jmbx__mqiy += (
            '  idx_t = bodo.utils.conversion.coerce_to_ndarray(idx)\n')
        fbjh__ads = (
            'bodo.hiframes.pd_dataframe_ext.get_dataframe_index(df)[idx_t]')
        lbv__uoj = ', '.join(
            'bodo.hiframes.pd_dataframe_ext.get_dataframe_data(df, {})[idx_t]'
            .format(df.columns.index(uhgb__avuw)) for uhgb__avuw in df.columns)
        return bodo.hiframes.dataframe_impl._gen_init_df(jmbx__mqiy, df.
            columns, lbv__uoj, fbjh__ads)
    if isinstance(idx, types.BaseTuple) and len(idx) == 2:
        gtq__qpj = idx.types[1]
        if is_overload_constant_str(gtq__qpj):
            ezkan__fupzh = get_overload_const_str(gtq__qpj)
            gcvjb__vqlwy = df.columns.index(ezkan__fupzh)

            def impl_col_name(I, idx):
                df = I._obj
                fbjh__ads = bodo.hiframes.pd_dataframe_ext.get_dataframe_index(
                    df)
                atfr__ktk = bodo.hiframes.pd_dataframe_ext.get_dataframe_data(
                    df, gcvjb__vqlwy)
                return bodo.hiframes.pd_series_ext.init_series(atfr__ktk,
                    fbjh__ads, ezkan__fupzh).loc[idx[0]]
            return impl_col_name
        if is_overload_constant_list(gtq__qpj):
            col_idx_list = get_overload_const_list(gtq__qpj)
            if len(col_idx_list) > 0 and not isinstance(col_idx_list[0], (
                bool, np.bool_)) and not all(uhgb__avuw in df.columns for
                uhgb__avuw in col_idx_list):
                raise_bodo_error(
                    f'DataFrame.loc[]: invalid column list {col_idx_list}; not all in dataframe columns {df.columns}'
                    )
            return gen_df_loc_col_select_impl(df, col_idx_list)
    raise_bodo_error(
        f'DataFrame.loc[] getitem (location-based indexing) using {idx} not supported yet.'
        )


def gen_df_loc_col_select_impl(df, col_idx_list):
    if len(col_idx_list) > 0 and isinstance(col_idx_list[0], (bool, np.bool_)):
        col_idx_list = list(pd.Series(df.columns, dtype=object)[col_idx_list])
    lbv__uoj = ', '.join(
        'bodo.hiframes.pd_dataframe_ext.get_dataframe_data(df, {})[idx[0]]'
        .format(df.columns.index(uhgb__avuw)) for uhgb__avuw in col_idx_list)
    fbjh__ads = (
        'bodo.hiframes.pd_dataframe_ext.get_dataframe_index(df)[idx[0]]')
    jmbx__mqiy = 'def impl(I, idx):\n'
    jmbx__mqiy += '  df = I._obj\n'
    return bodo.hiframes.dataframe_impl._gen_init_df(jmbx__mqiy,
        col_idx_list, lbv__uoj, fbjh__ads)


@overload(operator.setitem, no_unliteral=True)
def df_loc_setitem_overload(df, idx, val):
    if not isinstance(df, DataFrameLocType):
        return
    raise_bodo_error(
        f'DataFrame.loc setitem unsupported for dataframe {df.df_type}, index {idx}, value {val}'
        )


class DataFrameIatType(types.Type):

    def __init__(self, df_type):
        self.df_type = df_type
        ghfby__baz = 'DataFrameIatType({})'.format(df_type)
        super(DataFrameIatType, self).__init__(ghfby__baz)

    @property
    def mangling_args(self):
        return self.__class__.__name__, (self._code,)
    ndim = 2


@register_model(DataFrameIatType)
class DataFrameIatModel(models.StructModel):

    def __init__(self, dmm, fe_type):
        svp__acl = [('obj', fe_type.df_type)]
        super(DataFrameIatModel, self).__init__(dmm, fe_type, svp__acl)


make_attribute_wrapper(DataFrameIatType, 'obj', '_obj')


@intrinsic
def init_dataframe_iat(typingctx, obj=None):

    def codegen(context, builder, signature, args):
        wvws__fkzte, = args
        ssurf__toykd = signature.return_type
        dpo__hco = cgutils.create_struct_proxy(ssurf__toykd)(context, builder)
        dpo__hco.obj = wvws__fkzte
        context.nrt.incref(builder, signature.args[0], wvws__fkzte)
        return dpo__hco._getvalue()
    return DataFrameIatType(obj)(obj), codegen


@overload_attribute(DataFrameType, 'iat')
def overload_dataframe_iat(df):
    check_runtime_cols_unsupported(df, 'DataFrame.iat')
    return lambda df: bodo.hiframes.dataframe_indexing.init_dataframe_iat(df)


@overload(operator.getitem, no_unliteral=True)
def overload_iat_getitem(I, idx):
    if not isinstance(I, DataFrameIatType):
        return
    if isinstance(idx, types.BaseTuple) and len(idx) == 2:
        if not isinstance(idx.types[0], types.Integer):
            raise BodoError(
                'DataFrame.iat: iAt based indexing can only have integer indexers'
                )
        if not is_overload_constant_int(idx.types[1]):
            raise_bodo_error(
                'DataFrame.iat getitem: column index must be a constant integer. For more informaton, see https://docs.bodo.ai/latest/source/programming_with_bodo/require_constants.html.'
                )
        gcvjb__vqlwy = get_overload_const_int(idx.types[1])

        def impl_col_ind(I, idx):
            df = I._obj
            atfr__ktk = bodo.hiframes.pd_dataframe_ext.get_dataframe_data(df,
                gcvjb__vqlwy)
            return atfr__ktk[idx[0]]
        return impl_col_ind
    raise BodoError('df.iat[] getitem using {} not supported'.format(idx))


@overload(operator.setitem, no_unliteral=True)
def overload_iat_setitem(I, idx, val):
    if not isinstance(I, DataFrameIatType):
        return
    if isinstance(idx, types.BaseTuple) and len(idx) == 2:
        if not isinstance(idx.types[0], types.Integer):
            raise BodoError(
                'DataFrame.iat: iAt based indexing can only have integer indexers'
                )
        if not is_overload_constant_int(idx.types[1]):
            raise_bodo_error(
                'DataFrame.iat setitem: column index must be a constant integer. For more informaton, see https://docs.bodo.ai/latest/source/programming_with_bodo/require_constants.html'
                )
        gcvjb__vqlwy = get_overload_const_int(idx.types[1])
        if is_immutable_array(I.df_type.data[gcvjb__vqlwy]):
            raise BodoError(
                f'DataFrame setitem not supported for column with immutable array type {I.df_type.data}'
                )

        def impl_col_ind(I, idx, val):
            df = I._obj
            atfr__ktk = bodo.hiframes.pd_dataframe_ext.get_dataframe_data(df,
                gcvjb__vqlwy)
            atfr__ktk[idx[0]] = bodo.utils.conversion.unbox_if_timestamp(val)
        return impl_col_ind
    raise BodoError('df.iat[] setitem using {} not supported'.format(idx))


@lower_cast(DataFrameIatType, DataFrameIatType)
@lower_cast(DataFrameILocType, DataFrameILocType)
@lower_cast(DataFrameLocType, DataFrameLocType)
def cast_series_iat(context, builder, fromty, toty, val):
    dpo__hco = cgutils.create_struct_proxy(fromty)(context, builder, val)
    dxbe__cjzs = context.cast(builder, dpo__hco.obj, fromty.df_type, toty.
        df_type)
    fqf__lwrwa = cgutils.create_struct_proxy(toty)(context, builder)
    fqf__lwrwa.obj = dxbe__cjzs
    return fqf__lwrwa._getvalue()
