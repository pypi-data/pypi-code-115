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
            nua__lkw = idx
            gtbls__bsoa = df.data
            garhj__xjf = df.columns
            baazt__jrmf = self.replace_range_with_numeric_idx_if_needed(df,
                nua__lkw)
            nsld__hlmja = DataFrameType(gtbls__bsoa, baazt__jrmf, garhj__xjf)
            return nsld__hlmja(*args)
        if isinstance(idx, types.BaseTuple) and len(idx) == 2:
            rgzoz__josk = idx.types[0]
            yvdi__vms = idx.types[1]
            if isinstance(rgzoz__josk, types.Integer):
                if not isinstance(df.index, bodo.hiframes.pd_index_ext.
                    RangeIndexType):
                    raise_bodo_error(
                        'Dataframe.loc[int, col_ind] getitem only supported for dataframes with RangeIndexes'
                        )
                if is_overload_constant_str(yvdi__vms):
                    gkmds__cxaum = get_overload_const_str(yvdi__vms)
                    if gkmds__cxaum not in df.columns:
                        raise_bodo_error(
                            'dataframe {} does not include column {}'.
                            format(df, gkmds__cxaum))
                    wxj__yeu = df.columns.index(gkmds__cxaum)
                    return df.data[wxj__yeu].dtype(*args)
                if isinstance(yvdi__vms, types.UnicodeType):
                    raise_bodo_error(
                        f'DataFrame.loc[] getitem (location-based indexing) requires constant column names. For more information, see https://docs.bodo.ai/latest/source/programming_with_bodo/require_constants.html.'
                        )
                else:
                    raise_bodo_error(
                        f'DataFrame.loc[] getitem (location-based indexing) using {idx} not supported yet.'
                        )
            if is_list_like_index_type(rgzoz__josk
                ) and rgzoz__josk.dtype == types.bool_ or isinstance(
                rgzoz__josk, types.SliceType):
                baazt__jrmf = self.replace_range_with_numeric_idx_if_needed(df,
                    rgzoz__josk)
                if is_overload_constant_str(yvdi__vms):
                    krr__rnu = get_overload_const_str(yvdi__vms)
                    if krr__rnu not in df.columns:
                        raise_bodo_error(
                            f'dataframe {df} does not include column {krr__rnu}'
                            )
                    wxj__yeu = df.columns.index(krr__rnu)
                    qyw__rrz = df.data[wxj__yeu]
                    ebmms__chjh = qyw__rrz.dtype
                    yqdek__eltp = types.literal(df.columns[wxj__yeu])
                    nsld__hlmja = bodo.SeriesType(ebmms__chjh, qyw__rrz,
                        baazt__jrmf, yqdek__eltp)
                    return nsld__hlmja(*args)
                if isinstance(yvdi__vms, types.UnicodeType):
                    raise_bodo_error(
                        f'DataFrame.loc[] getitem (location-based indexing) requires constant column names. For more information, see https://docs.bodo.ai/latest/source/programming_with_bodo/require_constants.html.'
                        )
                elif is_overload_constant_list(yvdi__vms):
                    ncz__uicrv = get_overload_const_list(yvdi__vms)
                    rnztn__jvo = types.unliteral(yvdi__vms)
                    if rnztn__jvo.dtype == types.bool_:
                        if len(df.columns) != len(ncz__uicrv):
                            raise_bodo_error(
                                f'dataframe {df} has {len(df.columns)} columns, but boolean array used with DataFrame.loc[] {ncz__uicrv} has {len(ncz__uicrv)} values'
                                )
                        nlztg__pyy = []
                        hgfv__snd = []
                        for icdjo__pxp in range(len(ncz__uicrv)):
                            if ncz__uicrv[icdjo__pxp]:
                                nlztg__pyy.append(df.columns[icdjo__pxp])
                                hgfv__snd.append(df.data[icdjo__pxp])
                        sure__cegom = tuple()
                        nsld__hlmja = DataFrameType(tuple(hgfv__snd),
                            baazt__jrmf, tuple(nlztg__pyy))
                        return nsld__hlmja(*args)
                    elif rnztn__jvo.dtype == bodo.string_type:
                        sure__cegom, hgfv__snd = self.get_kept_cols_and_data(df
                            , ncz__uicrv)
                        nsld__hlmja = DataFrameType(hgfv__snd, baazt__jrmf,
                            sure__cegom)
                        return nsld__hlmja(*args)
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
                nlztg__pyy = []
                hgfv__snd = []
                for icdjo__pxp, qnr__yrzw in enumerate(df.columns):
                    if qnr__yrzw[0] != ind_val:
                        continue
                    nlztg__pyy.append(qnr__yrzw[1] if len(qnr__yrzw) == 2 else
                        qnr__yrzw[1:])
                    hgfv__snd.append(df.data[icdjo__pxp])
                qyw__rrz = tuple(hgfv__snd)
                gjaf__cls = df.index
                ymj__cafsn = tuple(nlztg__pyy)
                nsld__hlmja = DataFrameType(qyw__rrz, gjaf__cls, ymj__cafsn)
                return nsld__hlmja(*args)
            else:
                if ind_val not in df.columns:
                    raise_bodo_error('dataframe {} does not include column {}'
                        .format(df, ind_val))
                wxj__yeu = df.columns.index(ind_val)
                qyw__rrz = df.data[wxj__yeu]
                ebmms__chjh = qyw__rrz.dtype
                gjaf__cls = df.index
                yqdek__eltp = types.literal(df.columns[wxj__yeu])
                nsld__hlmja = bodo.SeriesType(ebmms__chjh, qyw__rrz,
                    gjaf__cls, yqdek__eltp)
                return nsld__hlmja(*args)
        if isinstance(ind, types.Integer) or isinstance(ind, types.UnicodeType
            ):
            raise_bodo_error(
                'df[] getitem selecting a subset of columns requires providing constant column names. For more information, see https://docs.bodo.ai/latest/source/programming_with_bodo/require_constants.html'
                )
        if is_list_like_index_type(ind
            ) and ind.dtype == types.bool_ or isinstance(ind, types.SliceType):
            qyw__rrz = df.data
            gjaf__cls = self.replace_range_with_numeric_idx_if_needed(df, ind)
            ymj__cafsn = df.columns
            nsld__hlmja = DataFrameType(qyw__rrz, gjaf__cls, ymj__cafsn,
                is_table_format=df.is_table_format)
            return nsld__hlmja(*args)
        elif is_overload_constant_list(ind):
            ijv__jzlql = get_overload_const_list(ind)
            ymj__cafsn, qyw__rrz = self.get_kept_cols_and_data(df, ijv__jzlql)
            gjaf__cls = df.index
            nsld__hlmja = DataFrameType(qyw__rrz, gjaf__cls, ymj__cafsn)
            return nsld__hlmja(*args)
        raise_bodo_error(
            f'df[] getitem using {ind} not supported. If you are trying to select a subset of the columns, you must provide the column names you are selecting as a constant. See https://docs.bodo.ai/latest/source/programming_with_bodo/require_constants.html'
            )

    def get_kept_cols_and_data(self, df, cols_to_keep_list):
        for ouu__kcfi in cols_to_keep_list:
            if ouu__kcfi not in df.columns:
                raise_bodo_error('Column {} not found in dataframe columns {}'
                    .format(ouu__kcfi, df.columns))
        ymj__cafsn = tuple(cols_to_keep_list)
        qyw__rrz = tuple(df.data[df.columns.index(izrkc__zkm)] for
            izrkc__zkm in ymj__cafsn)
        return ymj__cafsn, qyw__rrz

    def replace_range_with_numeric_idx_if_needed(self, df, ind):
        baazt__jrmf = bodo.hiframes.pd_index_ext.NumericIndexType(types.
            int64, df.index.name_typ) if not isinstance(ind, types.SliceType
            ) and isinstance(df.index, bodo.hiframes.pd_index_ext.
            RangeIndexType) else df.index
        return baazt__jrmf


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
            nlztg__pyy = []
            hgfv__snd = []
            for icdjo__pxp, qnr__yrzw in enumerate(df.columns):
                if qnr__yrzw[0] != ind_val:
                    continue
                nlztg__pyy.append(qnr__yrzw[1] if len(qnr__yrzw) == 2 else
                    qnr__yrzw[1:])
                hgfv__snd.append(
                    'bodo.hiframes.pd_dataframe_ext.get_dataframe_data(df, {})'
                    .format(icdjo__pxp))
            zxjhs__kgci = 'def impl(df, ind):\n'
            ncmyw__uxfqu = (
                'bodo.hiframes.pd_dataframe_ext.get_dataframe_index(df)')
            return bodo.hiframes.dataframe_impl._gen_init_df(zxjhs__kgci,
                nlztg__pyy, ', '.join(hgfv__snd), ncmyw__uxfqu)
        if ind_val not in df.columns:
            raise_bodo_error('dataframe {} does not include column {}'.
                format(df, ind_val))
        col_no = df.columns.index(ind_val)
        return lambda df, ind: bodo.hiframes.pd_series_ext.init_series(bodo
            .hiframes.pd_dataframe_ext.get_dataframe_data(df, col_no), bodo
            .hiframes.pd_dataframe_ext.get_dataframe_index(df), ind_val)
    if is_overload_constant_list(ind):
        ijv__jzlql = get_overload_const_list(ind)
        for ouu__kcfi in ijv__jzlql:
            if ouu__kcfi not in df.columns:
                raise_bodo_error('Column {} not found in dataframe columns {}'
                    .format(ouu__kcfi, df.columns))
        hgfv__snd = ', '.join(
            'bodo.hiframes.pd_dataframe_ext.get_dataframe_data(df, {}).copy()'
            .format(df.columns.index(ouu__kcfi)) for ouu__kcfi in ijv__jzlql)
        zxjhs__kgci = 'def impl(df, ind):\n'
        ncmyw__uxfqu = 'bodo.hiframes.pd_dataframe_ext.get_dataframe_index(df)'
        return bodo.hiframes.dataframe_impl._gen_init_df(zxjhs__kgci,
            ijv__jzlql, hgfv__snd, ncmyw__uxfqu)
    if is_list_like_index_type(ind) and ind.dtype == types.bool_ or isinstance(
        ind, types.SliceType):
        zxjhs__kgci = 'def impl(df, ind):\n'
        if not isinstance(ind, types.SliceType):
            zxjhs__kgci += (
                '  ind = bodo.utils.conversion.coerce_to_ndarray(ind)\n')
        ncmyw__uxfqu = (
            'bodo.hiframes.pd_dataframe_ext.get_dataframe_index(df)[ind]')
        if df.is_table_format:
            hgfv__snd = (
                f'bodo.hiframes.pd_dataframe_ext.get_dataframe_table(df)[ind]')
        else:
            hgfv__snd = ', '.join(
                f'bodo.hiframes.pd_dataframe_ext.get_dataframe_data(df, {df.columns.index(ouu__kcfi)})[ind]'
                 for ouu__kcfi in df.columns)
        return bodo.hiframes.dataframe_impl._gen_init_df(zxjhs__kgci, df.
            columns, hgfv__snd, ncmyw__uxfqu, out_df_type=df)
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
        izrkc__zkm = 'DataFrameILocType({})'.format(df_type)
        super(DataFrameILocType, self).__init__(izrkc__zkm)

    @property
    def mangling_args(self):
        return self.__class__.__name__, (self._code,)
    ndim = 2


@register_model(DataFrameILocType)
class DataFrameILocModel(models.StructModel):

    def __init__(self, dmm, fe_type):
        wady__zgjhh = [('obj', fe_type.df_type)]
        super(DataFrameILocModel, self).__init__(dmm, fe_type, wady__zgjhh)


make_attribute_wrapper(DataFrameILocType, 'obj', '_obj')


@intrinsic
def init_dataframe_iloc(typingctx, obj=None):

    def codegen(context, builder, signature, args):
        aikbr__tam, = args
        rsgs__hkve = signature.return_type
        rpqs__zvss = cgutils.create_struct_proxy(rsgs__hkve)(context, builder)
        rpqs__zvss.obj = aikbr__tam
        context.nrt.incref(builder, signature.args[0], aikbr__tam)
        return rpqs__zvss._getvalue()
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
        hwvb__wzihr = len(df.data)
        if is_overload_constant_int(idx.types[1]):
            is_out_series = True
            lvb__vlyb = get_overload_const_int(idx.types[1])
            if lvb__vlyb < 0 or lvb__vlyb >= hwvb__wzihr:
                raise BodoError(
                    'df.iloc: column integer must refer to a valid column number'
                    )
            tsogy__iht = [lvb__vlyb]
        else:
            is_out_series = False
            tsogy__iht = get_overload_const_list(idx.types[1])
            if any(not isinstance(ind, int) or ind < 0 or ind >=
                hwvb__wzihr for ind in tsogy__iht):
                raise BodoError(
                    'df.iloc: column list must be integers referring to a valid column number'
                    )
        col_names = tuple(pd.Series(df.columns, dtype=object)[tsogy__iht])
        if isinstance(idx.types[0], types.Integer):
            if isinstance(idx.types[1], types.Integer):
                lvb__vlyb = tsogy__iht[0]

                def impl(I, idx):
                    df = I._obj
                    return bodo.utils.conversion.box_if_dt64(bodo.hiframes.
                        pd_dataframe_ext.get_dataframe_data(df, lvb__vlyb)[
                        idx[0]])
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
    zxjhs__kgci = 'def impl(I, idx):\n'
    zxjhs__kgci += '  df = I._obj\n'
    if isinstance(idx_typ, types.SliceType):
        zxjhs__kgci += f'  idx_t = {idx}\n'
    else:
        zxjhs__kgci += (
            f'  idx_t = bodo.utils.conversion.coerce_to_ndarray({idx})\n')
    ncmyw__uxfqu = (
        'bodo.hiframes.pd_dataframe_ext.get_dataframe_index(df)[idx_t]')
    hgfv__snd = ', '.join(
        f'bodo.hiframes.pd_dataframe_ext.get_dataframe_data(df, {df.columns.index(ouu__kcfi)})[idx_t]'
         for ouu__kcfi in col_names)
    if is_out_series:
        cyy__xvkt = f"'{col_names[0]}'" if isinstance(col_names[0], str
            ) else f'{col_names[0]}'
        zxjhs__kgci += f"""  return bodo.hiframes.pd_series_ext.init_series({hgfv__snd}, {ncmyw__uxfqu}, {cyy__xvkt})
"""
        txt__hilca = {}
        exec(zxjhs__kgci, {'bodo': bodo}, txt__hilca)
        return txt__hilca['impl']
    return bodo.hiframes.dataframe_impl._gen_init_df(zxjhs__kgci, col_names,
        hgfv__snd, ncmyw__uxfqu)


def _gen_iloc_getitem_row_impl(df, col_names, idx):
    zxjhs__kgci = 'def impl(I, idx):\n'
    zxjhs__kgci += '  df = I._obj\n'
    sjosx__yhqfs = ', '.join(
        f'bodo.hiframes.pd_dataframe_ext.get_dataframe_data(df, {df.columns.index(ouu__kcfi)})[{idx}]'
         for ouu__kcfi in col_names)
    zxjhs__kgci += f"""  row_idx = bodo.hiframes.pd_index_ext.init_heter_index({gen_const_tup(col_names)}, None)
"""
    zxjhs__kgci += f"""  return bodo.hiframes.pd_series_ext.init_series(({sjosx__yhqfs},), row_idx, None)
"""
    txt__hilca = {}
    exec(zxjhs__kgci, {'bodo': bodo}, txt__hilca)
    impl = txt__hilca['impl']
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
        izrkc__zkm = 'DataFrameLocType({})'.format(df_type)
        super(DataFrameLocType, self).__init__(izrkc__zkm)

    @property
    def mangling_args(self):
        return self.__class__.__name__, (self._code,)
    ndim = 2


@register_model(DataFrameLocType)
class DataFrameLocModel(models.StructModel):

    def __init__(self, dmm, fe_type):
        wady__zgjhh = [('obj', fe_type.df_type)]
        super(DataFrameLocModel, self).__init__(dmm, fe_type, wady__zgjhh)


make_attribute_wrapper(DataFrameLocType, 'obj', '_obj')


@intrinsic
def init_dataframe_loc(typingctx, obj=None):

    def codegen(context, builder, signature, args):
        aikbr__tam, = args
        qugn__pqg = signature.return_type
        lioi__kyogn = cgutils.create_struct_proxy(qugn__pqg)(context, builder)
        lioi__kyogn.obj = aikbr__tam
        context.nrt.incref(builder, signature.args[0], aikbr__tam)
        return lioi__kyogn._getvalue()
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
        zxjhs__kgci = 'def impl(I, idx):\n'
        zxjhs__kgci += '  df = I._obj\n'
        zxjhs__kgci += (
            '  idx_t = bodo.utils.conversion.coerce_to_ndarray(idx)\n')
        ncmyw__uxfqu = (
            'bodo.hiframes.pd_dataframe_ext.get_dataframe_index(df)[idx_t]')
        hgfv__snd = ', '.join(
            'bodo.hiframes.pd_dataframe_ext.get_dataframe_data(df, {})[idx_t]'
            .format(df.columns.index(ouu__kcfi)) for ouu__kcfi in df.columns)
        return bodo.hiframes.dataframe_impl._gen_init_df(zxjhs__kgci, df.
            columns, hgfv__snd, ncmyw__uxfqu)
    if isinstance(idx, types.BaseTuple) and len(idx) == 2:
        qkhg__noj = idx.types[1]
        if is_overload_constant_str(qkhg__noj):
            dha__wtbn = get_overload_const_str(qkhg__noj)
            lvb__vlyb = df.columns.index(dha__wtbn)

            def impl_col_name(I, idx):
                df = I._obj
                ncmyw__uxfqu = (bodo.hiframes.pd_dataframe_ext.
                    get_dataframe_index(df))
                iaj__wznz = bodo.hiframes.pd_dataframe_ext.get_dataframe_data(
                    df, lvb__vlyb)
                return bodo.hiframes.pd_series_ext.init_series(iaj__wznz,
                    ncmyw__uxfqu, dha__wtbn).loc[idx[0]]
            return impl_col_name
        if is_overload_constant_list(qkhg__noj):
            col_idx_list = get_overload_const_list(qkhg__noj)
            if len(col_idx_list) > 0 and not isinstance(col_idx_list[0], (
                bool, np.bool_)) and not all(ouu__kcfi in df.columns for
                ouu__kcfi in col_idx_list):
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
    hgfv__snd = ', '.join(
        'bodo.hiframes.pd_dataframe_ext.get_dataframe_data(df, {})[idx[0]]'
        .format(df.columns.index(ouu__kcfi)) for ouu__kcfi in col_idx_list)
    ncmyw__uxfqu = (
        'bodo.hiframes.pd_dataframe_ext.get_dataframe_index(df)[idx[0]]')
    zxjhs__kgci = 'def impl(I, idx):\n'
    zxjhs__kgci += '  df = I._obj\n'
    return bodo.hiframes.dataframe_impl._gen_init_df(zxjhs__kgci,
        col_idx_list, hgfv__snd, ncmyw__uxfqu)


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
        izrkc__zkm = 'DataFrameIatType({})'.format(df_type)
        super(DataFrameIatType, self).__init__(izrkc__zkm)

    @property
    def mangling_args(self):
        return self.__class__.__name__, (self._code,)
    ndim = 2


@register_model(DataFrameIatType)
class DataFrameIatModel(models.StructModel):

    def __init__(self, dmm, fe_type):
        wady__zgjhh = [('obj', fe_type.df_type)]
        super(DataFrameIatModel, self).__init__(dmm, fe_type, wady__zgjhh)


make_attribute_wrapper(DataFrameIatType, 'obj', '_obj')


@intrinsic
def init_dataframe_iat(typingctx, obj=None):

    def codegen(context, builder, signature, args):
        aikbr__tam, = args
        uhl__vtheu = signature.return_type
        xppl__xdh = cgutils.create_struct_proxy(uhl__vtheu)(context, builder)
        xppl__xdh.obj = aikbr__tam
        context.nrt.incref(builder, signature.args[0], aikbr__tam)
        return xppl__xdh._getvalue()
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
        lvb__vlyb = get_overload_const_int(idx.types[1])

        def impl_col_ind(I, idx):
            df = I._obj
            iaj__wznz = bodo.hiframes.pd_dataframe_ext.get_dataframe_data(df,
                lvb__vlyb)
            return iaj__wznz[idx[0]]
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
        lvb__vlyb = get_overload_const_int(idx.types[1])
        if is_immutable_array(I.df_type.data[lvb__vlyb]):
            raise BodoError(
                f'DataFrame setitem not supported for column with immutable array type {I.df_type.data}'
                )

        def impl_col_ind(I, idx, val):
            df = I._obj
            iaj__wznz = bodo.hiframes.pd_dataframe_ext.get_dataframe_data(df,
                lvb__vlyb)
            iaj__wznz[idx[0]] = bodo.utils.conversion.unbox_if_timestamp(val)
        return impl_col_ind
    raise BodoError('df.iat[] setitem using {} not supported'.format(idx))


@lower_cast(DataFrameIatType, DataFrameIatType)
@lower_cast(DataFrameILocType, DataFrameILocType)
@lower_cast(DataFrameLocType, DataFrameLocType)
def cast_series_iat(context, builder, fromty, toty, val):
    xppl__xdh = cgutils.create_struct_proxy(fromty)(context, builder, val)
    lhrb__rid = context.cast(builder, xppl__xdh.obj, fromty.df_type, toty.
        df_type)
    dvys__wcu = cgutils.create_struct_proxy(toty)(context, builder)
    dvys__wcu.obj = lhrb__rid
    return dvys__wcu._getvalue()
