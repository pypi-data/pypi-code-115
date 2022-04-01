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
            jfz__tbxba = idx
            opw__eenub = df.data
            qqpa__rroug = df.columns
            wbq__ixzll = self.replace_range_with_numeric_idx_if_needed(df,
                jfz__tbxba)
            ykc__wptn = DataFrameType(opw__eenub, wbq__ixzll, qqpa__rroug)
            return ykc__wptn(*args)
        if isinstance(idx, types.BaseTuple) and len(idx) == 2:
            ejw__mozns = idx.types[0]
            dvgjj__ocbi = idx.types[1]
            if isinstance(ejw__mozns, types.Integer):
                if not isinstance(df.index, bodo.hiframes.pd_index_ext.
                    RangeIndexType):
                    raise_bodo_error(
                        'Dataframe.loc[int, col_ind] getitem only supported for dataframes with RangeIndexes'
                        )
                if is_overload_constant_str(dvgjj__ocbi):
                    jkga__ovgle = get_overload_const_str(dvgjj__ocbi)
                    if jkga__ovgle not in df.columns:
                        raise_bodo_error(
                            'dataframe {} does not include column {}'.
                            format(df, jkga__ovgle))
                    psbj__ucl = df.columns.index(jkga__ovgle)
                    return df.data[psbj__ucl].dtype(*args)
                if isinstance(dvgjj__ocbi, types.UnicodeType):
                    raise_bodo_error(
                        f'DataFrame.loc[] getitem (location-based indexing) requires constant column names. For more information, see https://docs.bodo.ai/latest/source/programming_with_bodo/require_constants.html.'
                        )
                else:
                    raise_bodo_error(
                        f'DataFrame.loc[] getitem (location-based indexing) using {idx} not supported yet.'
                        )
            if is_list_like_index_type(ejw__mozns
                ) and ejw__mozns.dtype == types.bool_ or isinstance(ejw__mozns,
                types.SliceType):
                wbq__ixzll = self.replace_range_with_numeric_idx_if_needed(df,
                    ejw__mozns)
                if is_overload_constant_str(dvgjj__ocbi):
                    fjv__icw = get_overload_const_str(dvgjj__ocbi)
                    if fjv__icw not in df.columns:
                        raise_bodo_error(
                            f'dataframe {df} does not include column {fjv__icw}'
                            )
                    psbj__ucl = df.columns.index(fjv__icw)
                    yqj__ipc = df.data[psbj__ucl]
                    jaaaq__zbsjp = yqj__ipc.dtype
                    eipxp__dfae = types.literal(df.columns[psbj__ucl])
                    ykc__wptn = bodo.SeriesType(jaaaq__zbsjp, yqj__ipc,
                        wbq__ixzll, eipxp__dfae)
                    return ykc__wptn(*args)
                if isinstance(dvgjj__ocbi, types.UnicodeType):
                    raise_bodo_error(
                        f'DataFrame.loc[] getitem (location-based indexing) requires constant column names. For more information, see https://docs.bodo.ai/latest/source/programming_with_bodo/require_constants.html.'
                        )
                elif is_overload_constant_list(dvgjj__ocbi):
                    ospyw__smfd = get_overload_const_list(dvgjj__ocbi)
                    qzv__tsvoc = types.unliteral(dvgjj__ocbi)
                    if qzv__tsvoc.dtype == types.bool_:
                        if len(df.columns) != len(ospyw__smfd):
                            raise_bodo_error(
                                f'dataframe {df} has {len(df.columns)} columns, but boolean array used with DataFrame.loc[] {ospyw__smfd} has {len(ospyw__smfd)} values'
                                )
                        wupo__bdfms = []
                        xrld__crxi = []
                        for bvm__ykd in range(len(ospyw__smfd)):
                            if ospyw__smfd[bvm__ykd]:
                                wupo__bdfms.append(df.columns[bvm__ykd])
                                xrld__crxi.append(df.data[bvm__ykd])
                        wpic__lntix = tuple()
                        ykc__wptn = DataFrameType(tuple(xrld__crxi),
                            wbq__ixzll, tuple(wupo__bdfms))
                        return ykc__wptn(*args)
                    elif qzv__tsvoc.dtype == bodo.string_type:
                        wpic__lntix, xrld__crxi = self.get_kept_cols_and_data(
                            df, ospyw__smfd)
                        ykc__wptn = DataFrameType(xrld__crxi, wbq__ixzll,
                            wpic__lntix)
                        return ykc__wptn(*args)
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
                wupo__bdfms = []
                xrld__crxi = []
                for bvm__ykd, lwhjr__piiny in enumerate(df.columns):
                    if lwhjr__piiny[0] != ind_val:
                        continue
                    wupo__bdfms.append(lwhjr__piiny[1] if len(lwhjr__piiny) ==
                        2 else lwhjr__piiny[1:])
                    xrld__crxi.append(df.data[bvm__ykd])
                yqj__ipc = tuple(xrld__crxi)
                dbar__vjil = df.index
                wqmqd__bibab = tuple(wupo__bdfms)
                ykc__wptn = DataFrameType(yqj__ipc, dbar__vjil, wqmqd__bibab)
                return ykc__wptn(*args)
            else:
                if ind_val not in df.columns:
                    raise_bodo_error('dataframe {} does not include column {}'
                        .format(df, ind_val))
                psbj__ucl = df.columns.index(ind_val)
                yqj__ipc = df.data[psbj__ucl]
                jaaaq__zbsjp = yqj__ipc.dtype
                dbar__vjil = df.index
                eipxp__dfae = types.literal(df.columns[psbj__ucl])
                ykc__wptn = bodo.SeriesType(jaaaq__zbsjp, yqj__ipc,
                    dbar__vjil, eipxp__dfae)
                return ykc__wptn(*args)
        if isinstance(ind, types.Integer) or isinstance(ind, types.UnicodeType
            ):
            raise_bodo_error(
                'df[] getitem selecting a subset of columns requires providing constant column names. For more information, see https://docs.bodo.ai/latest/source/programming_with_bodo/require_constants.html'
                )
        if is_list_like_index_type(ind
            ) and ind.dtype == types.bool_ or isinstance(ind, types.SliceType):
            yqj__ipc = df.data
            dbar__vjil = self.replace_range_with_numeric_idx_if_needed(df, ind)
            wqmqd__bibab = df.columns
            ykc__wptn = DataFrameType(yqj__ipc, dbar__vjil, wqmqd__bibab,
                is_table_format=df.is_table_format)
            return ykc__wptn(*args)
        elif is_overload_constant_list(ind):
            zgezc__fzxp = get_overload_const_list(ind)
            wqmqd__bibab, yqj__ipc = self.get_kept_cols_and_data(df,
                zgezc__fzxp)
            dbar__vjil = df.index
            ykc__wptn = DataFrameType(yqj__ipc, dbar__vjil, wqmqd__bibab)
            return ykc__wptn(*args)
        raise_bodo_error(
            f'df[] getitem using {ind} not supported. If you are trying to select a subset of the columns, you must provide the column names you are selecting as a constant. See https://docs.bodo.ai/latest/source/programming_with_bodo/require_constants.html'
            )

    def get_kept_cols_and_data(self, df, cols_to_keep_list):
        for jwc__rvbhb in cols_to_keep_list:
            if jwc__rvbhb not in df.columns:
                raise_bodo_error('Column {} not found in dataframe columns {}'
                    .format(jwc__rvbhb, df.columns))
        wqmqd__bibab = tuple(cols_to_keep_list)
        yqj__ipc = tuple(df.data[df.columns.index(kahm__bhe)] for kahm__bhe in
            wqmqd__bibab)
        return wqmqd__bibab, yqj__ipc

    def replace_range_with_numeric_idx_if_needed(self, df, ind):
        wbq__ixzll = bodo.hiframes.pd_index_ext.NumericIndexType(types.
            int64, df.index.name_typ) if not isinstance(ind, types.SliceType
            ) and isinstance(df.index, bodo.hiframes.pd_index_ext.
            RangeIndexType) else df.index
        return wbq__ixzll


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
            wupo__bdfms = []
            xrld__crxi = []
            for bvm__ykd, lwhjr__piiny in enumerate(df.columns):
                if lwhjr__piiny[0] != ind_val:
                    continue
                wupo__bdfms.append(lwhjr__piiny[1] if len(lwhjr__piiny) == 
                    2 else lwhjr__piiny[1:])
                xrld__crxi.append(
                    'bodo.hiframes.pd_dataframe_ext.get_dataframe_data(df, {})'
                    .format(bvm__ykd))
            yay__pmd = 'def impl(df, ind):\n'
            ztrux__rill = (
                'bodo.hiframes.pd_dataframe_ext.get_dataframe_index(df)')
            return bodo.hiframes.dataframe_impl._gen_init_df(yay__pmd,
                wupo__bdfms, ', '.join(xrld__crxi), ztrux__rill)
        if ind_val not in df.columns:
            raise_bodo_error('dataframe {} does not include column {}'.
                format(df, ind_val))
        col_no = df.columns.index(ind_val)
        return lambda df, ind: bodo.hiframes.pd_series_ext.init_series(bodo
            .hiframes.pd_dataframe_ext.get_dataframe_data(df, col_no), bodo
            .hiframes.pd_dataframe_ext.get_dataframe_index(df), ind_val)
    if is_overload_constant_list(ind):
        zgezc__fzxp = get_overload_const_list(ind)
        for jwc__rvbhb in zgezc__fzxp:
            if jwc__rvbhb not in df.columns:
                raise_bodo_error('Column {} not found in dataframe columns {}'
                    .format(jwc__rvbhb, df.columns))
        xrld__crxi = ', '.join(
            'bodo.hiframes.pd_dataframe_ext.get_dataframe_data(df, {}).copy()'
            .format(df.columns.index(jwc__rvbhb)) for jwc__rvbhb in zgezc__fzxp
            )
        yay__pmd = 'def impl(df, ind):\n'
        ztrux__rill = 'bodo.hiframes.pd_dataframe_ext.get_dataframe_index(df)'
        return bodo.hiframes.dataframe_impl._gen_init_df(yay__pmd,
            zgezc__fzxp, xrld__crxi, ztrux__rill)
    if is_list_like_index_type(ind) and ind.dtype == types.bool_ or isinstance(
        ind, types.SliceType):
        yay__pmd = 'def impl(df, ind):\n'
        if not isinstance(ind, types.SliceType):
            yay__pmd += (
                '  ind = bodo.utils.conversion.coerce_to_ndarray(ind)\n')
        ztrux__rill = (
            'bodo.hiframes.pd_dataframe_ext.get_dataframe_index(df)[ind]')
        if df.is_table_format:
            xrld__crxi = (
                f'bodo.hiframes.pd_dataframe_ext.get_dataframe_table(df)[ind]')
        else:
            xrld__crxi = ', '.join(
                f'bodo.hiframes.pd_dataframe_ext.get_dataframe_data(df, {df.columns.index(jwc__rvbhb)})[ind]'
                 for jwc__rvbhb in df.columns)
        return bodo.hiframes.dataframe_impl._gen_init_df(yay__pmd, df.
            columns, xrld__crxi, ztrux__rill, out_df_type=df)
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
        kahm__bhe = 'DataFrameILocType({})'.format(df_type)
        super(DataFrameILocType, self).__init__(kahm__bhe)

    @property
    def mangling_args(self):
        return self.__class__.__name__, (self._code,)
    ndim = 2


@register_model(DataFrameILocType)
class DataFrameILocModel(models.StructModel):

    def __init__(self, dmm, fe_type):
        boay__gbcmx = [('obj', fe_type.df_type)]
        super(DataFrameILocModel, self).__init__(dmm, fe_type, boay__gbcmx)


make_attribute_wrapper(DataFrameILocType, 'obj', '_obj')


@intrinsic
def init_dataframe_iloc(typingctx, obj=None):

    def codegen(context, builder, signature, args):
        ahz__tfur, = args
        xtp__uqwdg = signature.return_type
        rgd__eeu = cgutils.create_struct_proxy(xtp__uqwdg)(context, builder)
        rgd__eeu.obj = ahz__tfur
        context.nrt.incref(builder, signature.args[0], ahz__tfur)
        return rgd__eeu._getvalue()
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
        idjpz__rppa = len(df.data)
        if is_overload_constant_int(idx.types[1]):
            is_out_series = True
            rngm__ncig = get_overload_const_int(idx.types[1])
            if rngm__ncig < 0 or rngm__ncig >= idjpz__rppa:
                raise BodoError(
                    'df.iloc: column integer must refer to a valid column number'
                    )
            yas__nbn = [rngm__ncig]
        else:
            is_out_series = False
            yas__nbn = get_overload_const_list(idx.types[1])
            if any(not isinstance(ind, int) or ind < 0 or ind >=
                idjpz__rppa for ind in yas__nbn):
                raise BodoError(
                    'df.iloc: column list must be integers referring to a valid column number'
                    )
        col_names = tuple(pd.Series(df.columns, dtype=object)[yas__nbn])
        if isinstance(idx.types[0], types.Integer):
            if isinstance(idx.types[1], types.Integer):
                rngm__ncig = yas__nbn[0]

                def impl(I, idx):
                    df = I._obj
                    return bodo.utils.conversion.box_if_dt64(bodo.hiframes.
                        pd_dataframe_ext.get_dataframe_data(df, rngm__ncig)
                        [idx[0]])
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
    yay__pmd = 'def impl(I, idx):\n'
    yay__pmd += '  df = I._obj\n'
    if isinstance(idx_typ, types.SliceType):
        yay__pmd += f'  idx_t = {idx}\n'
    else:
        yay__pmd += (
            f'  idx_t = bodo.utils.conversion.coerce_to_ndarray({idx})\n')
    ztrux__rill = (
        'bodo.hiframes.pd_dataframe_ext.get_dataframe_index(df)[idx_t]')
    xrld__crxi = ', '.join(
        f'bodo.hiframes.pd_dataframe_ext.get_dataframe_data(df, {df.columns.index(jwc__rvbhb)})[idx_t]'
         for jwc__rvbhb in col_names)
    if is_out_series:
        tdi__hkew = f"'{col_names[0]}'" if isinstance(col_names[0], str
            ) else f'{col_names[0]}'
        yay__pmd += f"""  return bodo.hiframes.pd_series_ext.init_series({xrld__crxi}, {ztrux__rill}, {tdi__hkew})
"""
        rlxiw__hnnqc = {}
        exec(yay__pmd, {'bodo': bodo}, rlxiw__hnnqc)
        return rlxiw__hnnqc['impl']
    return bodo.hiframes.dataframe_impl._gen_init_df(yay__pmd, col_names,
        xrld__crxi, ztrux__rill)


def _gen_iloc_getitem_row_impl(df, col_names, idx):
    yay__pmd = 'def impl(I, idx):\n'
    yay__pmd += '  df = I._obj\n'
    xoq__brs = ', '.join(
        f'bodo.hiframes.pd_dataframe_ext.get_dataframe_data(df, {df.columns.index(jwc__rvbhb)})[{idx}]'
         for jwc__rvbhb in col_names)
    yay__pmd += f"""  row_idx = bodo.hiframes.pd_index_ext.init_heter_index({gen_const_tup(col_names)}, None)
"""
    yay__pmd += (
        f'  return bodo.hiframes.pd_series_ext.init_series(({xoq__brs},), row_idx, None)\n'
        )
    rlxiw__hnnqc = {}
    exec(yay__pmd, {'bodo': bodo}, rlxiw__hnnqc)
    impl = rlxiw__hnnqc['impl']
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
        kahm__bhe = 'DataFrameLocType({})'.format(df_type)
        super(DataFrameLocType, self).__init__(kahm__bhe)

    @property
    def mangling_args(self):
        return self.__class__.__name__, (self._code,)
    ndim = 2


@register_model(DataFrameLocType)
class DataFrameLocModel(models.StructModel):

    def __init__(self, dmm, fe_type):
        boay__gbcmx = [('obj', fe_type.df_type)]
        super(DataFrameLocModel, self).__init__(dmm, fe_type, boay__gbcmx)


make_attribute_wrapper(DataFrameLocType, 'obj', '_obj')


@intrinsic
def init_dataframe_loc(typingctx, obj=None):

    def codegen(context, builder, signature, args):
        ahz__tfur, = args
        ydrg__wub = signature.return_type
        shkgf__htu = cgutils.create_struct_proxy(ydrg__wub)(context, builder)
        shkgf__htu.obj = ahz__tfur
        context.nrt.incref(builder, signature.args[0], ahz__tfur)
        return shkgf__htu._getvalue()
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
        yay__pmd = 'def impl(I, idx):\n'
        yay__pmd += '  df = I._obj\n'
        yay__pmd += '  idx_t = bodo.utils.conversion.coerce_to_ndarray(idx)\n'
        ztrux__rill = (
            'bodo.hiframes.pd_dataframe_ext.get_dataframe_index(df)[idx_t]')
        xrld__crxi = ', '.join(
            'bodo.hiframes.pd_dataframe_ext.get_dataframe_data(df, {})[idx_t]'
            .format(df.columns.index(jwc__rvbhb)) for jwc__rvbhb in df.columns)
        return bodo.hiframes.dataframe_impl._gen_init_df(yay__pmd, df.
            columns, xrld__crxi, ztrux__rill)
    if isinstance(idx, types.BaseTuple) and len(idx) == 2:
        elez__rwxhd = idx.types[1]
        if is_overload_constant_str(elez__rwxhd):
            tuk__clby = get_overload_const_str(elez__rwxhd)
            rngm__ncig = df.columns.index(tuk__clby)

            def impl_col_name(I, idx):
                df = I._obj
                ztrux__rill = (bodo.hiframes.pd_dataframe_ext.
                    get_dataframe_index(df))
                czkkj__tokg = (bodo.hiframes.pd_dataframe_ext.
                    get_dataframe_data(df, rngm__ncig))
                return bodo.hiframes.pd_series_ext.init_series(czkkj__tokg,
                    ztrux__rill, tuk__clby).loc[idx[0]]
            return impl_col_name
        if is_overload_constant_list(elez__rwxhd):
            col_idx_list = get_overload_const_list(elez__rwxhd)
            if len(col_idx_list) > 0 and not isinstance(col_idx_list[0], (
                bool, np.bool_)) and not all(jwc__rvbhb in df.columns for
                jwc__rvbhb in col_idx_list):
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
    xrld__crxi = ', '.join(
        'bodo.hiframes.pd_dataframe_ext.get_dataframe_data(df, {})[idx[0]]'
        .format(df.columns.index(jwc__rvbhb)) for jwc__rvbhb in col_idx_list)
    ztrux__rill = (
        'bodo.hiframes.pd_dataframe_ext.get_dataframe_index(df)[idx[0]]')
    yay__pmd = 'def impl(I, idx):\n'
    yay__pmd += '  df = I._obj\n'
    return bodo.hiframes.dataframe_impl._gen_init_df(yay__pmd, col_idx_list,
        xrld__crxi, ztrux__rill)


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
        kahm__bhe = 'DataFrameIatType({})'.format(df_type)
        super(DataFrameIatType, self).__init__(kahm__bhe)

    @property
    def mangling_args(self):
        return self.__class__.__name__, (self._code,)
    ndim = 2


@register_model(DataFrameIatType)
class DataFrameIatModel(models.StructModel):

    def __init__(self, dmm, fe_type):
        boay__gbcmx = [('obj', fe_type.df_type)]
        super(DataFrameIatModel, self).__init__(dmm, fe_type, boay__gbcmx)


make_attribute_wrapper(DataFrameIatType, 'obj', '_obj')


@intrinsic
def init_dataframe_iat(typingctx, obj=None):

    def codegen(context, builder, signature, args):
        ahz__tfur, = args
        boxc__iycvc = signature.return_type
        pcm__cyp = cgutils.create_struct_proxy(boxc__iycvc)(context, builder)
        pcm__cyp.obj = ahz__tfur
        context.nrt.incref(builder, signature.args[0], ahz__tfur)
        return pcm__cyp._getvalue()
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
        rngm__ncig = get_overload_const_int(idx.types[1])

        def impl_col_ind(I, idx):
            df = I._obj
            czkkj__tokg = bodo.hiframes.pd_dataframe_ext.get_dataframe_data(df,
                rngm__ncig)
            return czkkj__tokg[idx[0]]
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
        rngm__ncig = get_overload_const_int(idx.types[1])
        if is_immutable_array(I.df_type.data[rngm__ncig]):
            raise BodoError(
                f'DataFrame setitem not supported for column with immutable array type {I.df_type.data}'
                )

        def impl_col_ind(I, idx, val):
            df = I._obj
            czkkj__tokg = bodo.hiframes.pd_dataframe_ext.get_dataframe_data(df,
                rngm__ncig)
            czkkj__tokg[idx[0]] = bodo.utils.conversion.unbox_if_timestamp(val)
        return impl_col_ind
    raise BodoError('df.iat[] setitem using {} not supported'.format(idx))


@lower_cast(DataFrameIatType, DataFrameIatType)
@lower_cast(DataFrameILocType, DataFrameILocType)
@lower_cast(DataFrameLocType, DataFrameLocType)
def cast_series_iat(context, builder, fromty, toty, val):
    pcm__cyp = cgutils.create_struct_proxy(fromty)(context, builder, val)
    jwyex__exqp = context.cast(builder, pcm__cyp.obj, fromty.df_type, toty.
        df_type)
    eio__ktmtr = cgutils.create_struct_proxy(toty)(context, builder)
    eio__ktmtr.obj = jwyex__exqp
    return eio__ktmtr._getvalue()
