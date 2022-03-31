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
            ttds__lfiv = idx
            bry__cmeon = df.data
            fdqq__bfj = df.columns
            kjp__qamvl = self.replace_range_with_numeric_idx_if_needed(df,
                ttds__lfiv)
            iyg__skr = DataFrameType(bry__cmeon, kjp__qamvl, fdqq__bfj)
            return iyg__skr(*args)
        if isinstance(idx, types.BaseTuple) and len(idx) == 2:
            swp__dcpoc = idx.types[0]
            gmoey__rbo = idx.types[1]
            if isinstance(swp__dcpoc, types.Integer):
                if not isinstance(df.index, bodo.hiframes.pd_index_ext.
                    RangeIndexType):
                    raise_bodo_error(
                        'Dataframe.loc[int, col_ind] getitem only supported for dataframes with RangeIndexes'
                        )
                if is_overload_constant_str(gmoey__rbo):
                    icnz__maj = get_overload_const_str(gmoey__rbo)
                    if icnz__maj not in df.columns:
                        raise_bodo_error(
                            'dataframe {} does not include column {}'.
                            format(df, icnz__maj))
                    yvzrg__bjafq = df.columns.index(icnz__maj)
                    return df.data[yvzrg__bjafq].dtype(*args)
                if isinstance(gmoey__rbo, types.UnicodeType):
                    raise_bodo_error(
                        f'DataFrame.loc[] getitem (location-based indexing) requires constant column names. For more information, see https://docs.bodo.ai/latest/source/programming_with_bodo/require_constants.html.'
                        )
                else:
                    raise_bodo_error(
                        f'DataFrame.loc[] getitem (location-based indexing) using {idx} not supported yet.'
                        )
            if is_list_like_index_type(swp__dcpoc
                ) and swp__dcpoc.dtype == types.bool_ or isinstance(swp__dcpoc,
                types.SliceType):
                kjp__qamvl = self.replace_range_with_numeric_idx_if_needed(df,
                    swp__dcpoc)
                if is_overload_constant_str(gmoey__rbo):
                    iru__xupwz = get_overload_const_str(gmoey__rbo)
                    if iru__xupwz not in df.columns:
                        raise_bodo_error(
                            f'dataframe {df} does not include column {iru__xupwz}'
                            )
                    yvzrg__bjafq = df.columns.index(iru__xupwz)
                    fxl__zohr = df.data[yvzrg__bjafq]
                    fpc__dysw = fxl__zohr.dtype
                    gjjuv__wlrhe = types.literal(df.columns[yvzrg__bjafq])
                    iyg__skr = bodo.SeriesType(fpc__dysw, fxl__zohr,
                        kjp__qamvl, gjjuv__wlrhe)
                    return iyg__skr(*args)
                if isinstance(gmoey__rbo, types.UnicodeType):
                    raise_bodo_error(
                        f'DataFrame.loc[] getitem (location-based indexing) requires constant column names. For more information, see https://docs.bodo.ai/latest/source/programming_with_bodo/require_constants.html.'
                        )
                elif is_overload_constant_list(gmoey__rbo):
                    ywbl__habkl = get_overload_const_list(gmoey__rbo)
                    oqjae__abz = types.unliteral(gmoey__rbo)
                    if oqjae__abz.dtype == types.bool_:
                        if len(df.columns) != len(ywbl__habkl):
                            raise_bodo_error(
                                f'dataframe {df} has {len(df.columns)} columns, but boolean array used with DataFrame.loc[] {ywbl__habkl} has {len(ywbl__habkl)} values'
                                )
                        yizh__cyjrc = []
                        xwefe__vfc = []
                        for svxs__fbf in range(len(ywbl__habkl)):
                            if ywbl__habkl[svxs__fbf]:
                                yizh__cyjrc.append(df.columns[svxs__fbf])
                                xwefe__vfc.append(df.data[svxs__fbf])
                        gbd__awz = tuple()
                        iyg__skr = DataFrameType(tuple(xwefe__vfc),
                            kjp__qamvl, tuple(yizh__cyjrc))
                        return iyg__skr(*args)
                    elif oqjae__abz.dtype == bodo.string_type:
                        gbd__awz, xwefe__vfc = self.get_kept_cols_and_data(df,
                            ywbl__habkl)
                        iyg__skr = DataFrameType(xwefe__vfc, kjp__qamvl,
                            gbd__awz)
                        return iyg__skr(*args)
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
                yizh__cyjrc = []
                xwefe__vfc = []
                for svxs__fbf, eine__rhjb in enumerate(df.columns):
                    if eine__rhjb[0] != ind_val:
                        continue
                    yizh__cyjrc.append(eine__rhjb[1] if len(eine__rhjb) == 
                        2 else eine__rhjb[1:])
                    xwefe__vfc.append(df.data[svxs__fbf])
                fxl__zohr = tuple(xwefe__vfc)
                bgb__laug = df.index
                ltio__zwys = tuple(yizh__cyjrc)
                iyg__skr = DataFrameType(fxl__zohr, bgb__laug, ltio__zwys)
                return iyg__skr(*args)
            else:
                if ind_val not in df.columns:
                    raise_bodo_error('dataframe {} does not include column {}'
                        .format(df, ind_val))
                yvzrg__bjafq = df.columns.index(ind_val)
                fxl__zohr = df.data[yvzrg__bjafq]
                fpc__dysw = fxl__zohr.dtype
                bgb__laug = df.index
                gjjuv__wlrhe = types.literal(df.columns[yvzrg__bjafq])
                iyg__skr = bodo.SeriesType(fpc__dysw, fxl__zohr, bgb__laug,
                    gjjuv__wlrhe)
                return iyg__skr(*args)
        if isinstance(ind, types.Integer) or isinstance(ind, types.UnicodeType
            ):
            raise_bodo_error(
                'df[] getitem selecting a subset of columns requires providing constant column names. For more information, see https://docs.bodo.ai/latest/source/programming_with_bodo/require_constants.html'
                )
        if is_list_like_index_type(ind
            ) and ind.dtype == types.bool_ or isinstance(ind, types.SliceType):
            fxl__zohr = df.data
            bgb__laug = self.replace_range_with_numeric_idx_if_needed(df, ind)
            ltio__zwys = df.columns
            iyg__skr = DataFrameType(fxl__zohr, bgb__laug, ltio__zwys,
                is_table_format=df.is_table_format)
            return iyg__skr(*args)
        elif is_overload_constant_list(ind):
            vcog__cremn = get_overload_const_list(ind)
            ltio__zwys, fxl__zohr = self.get_kept_cols_and_data(df, vcog__cremn
                )
            bgb__laug = df.index
            iyg__skr = DataFrameType(fxl__zohr, bgb__laug, ltio__zwys)
            return iyg__skr(*args)
        raise_bodo_error(
            f'df[] getitem using {ind} not supported. If you are trying to select a subset of the columns, you must provide the column names you are selecting as a constant. See https://docs.bodo.ai/latest/source/programming_with_bodo/require_constants.html'
            )

    def get_kept_cols_and_data(self, df, cols_to_keep_list):
        for ale__eznq in cols_to_keep_list:
            if ale__eznq not in df.columns:
                raise_bodo_error('Column {} not found in dataframe columns {}'
                    .format(ale__eznq, df.columns))
        ltio__zwys = tuple(cols_to_keep_list)
        fxl__zohr = tuple(df.data[df.columns.index(ylr__kqdu)] for
            ylr__kqdu in ltio__zwys)
        return ltio__zwys, fxl__zohr

    def replace_range_with_numeric_idx_if_needed(self, df, ind):
        kjp__qamvl = bodo.hiframes.pd_index_ext.NumericIndexType(types.
            int64, df.index.name_typ) if not isinstance(ind, types.SliceType
            ) and isinstance(df.index, bodo.hiframes.pd_index_ext.
            RangeIndexType) else df.index
        return kjp__qamvl


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
            yizh__cyjrc = []
            xwefe__vfc = []
            for svxs__fbf, eine__rhjb in enumerate(df.columns):
                if eine__rhjb[0] != ind_val:
                    continue
                yizh__cyjrc.append(eine__rhjb[1] if len(eine__rhjb) == 2 else
                    eine__rhjb[1:])
                xwefe__vfc.append(
                    'bodo.hiframes.pd_dataframe_ext.get_dataframe_data(df, {})'
                    .format(svxs__fbf))
            ctuoe__cevyj = 'def impl(df, ind):\n'
            kznu__qensr = (
                'bodo.hiframes.pd_dataframe_ext.get_dataframe_index(df)')
            return bodo.hiframes.dataframe_impl._gen_init_df(ctuoe__cevyj,
                yizh__cyjrc, ', '.join(xwefe__vfc), kznu__qensr)
        if ind_val not in df.columns:
            raise_bodo_error('dataframe {} does not include column {}'.
                format(df, ind_val))
        col_no = df.columns.index(ind_val)
        return lambda df, ind: bodo.hiframes.pd_series_ext.init_series(bodo
            .hiframes.pd_dataframe_ext.get_dataframe_data(df, col_no), bodo
            .hiframes.pd_dataframe_ext.get_dataframe_index(df), ind_val)
    if is_overload_constant_list(ind):
        vcog__cremn = get_overload_const_list(ind)
        for ale__eznq in vcog__cremn:
            if ale__eznq not in df.columns:
                raise_bodo_error('Column {} not found in dataframe columns {}'
                    .format(ale__eznq, df.columns))
        xwefe__vfc = ', '.join(
            'bodo.hiframes.pd_dataframe_ext.get_dataframe_data(df, {}).copy()'
            .format(df.columns.index(ale__eznq)) for ale__eznq in vcog__cremn)
        ctuoe__cevyj = 'def impl(df, ind):\n'
        kznu__qensr = 'bodo.hiframes.pd_dataframe_ext.get_dataframe_index(df)'
        return bodo.hiframes.dataframe_impl._gen_init_df(ctuoe__cevyj,
            vcog__cremn, xwefe__vfc, kznu__qensr)
    if is_list_like_index_type(ind) and ind.dtype == types.bool_ or isinstance(
        ind, types.SliceType):
        ctuoe__cevyj = 'def impl(df, ind):\n'
        if not isinstance(ind, types.SliceType):
            ctuoe__cevyj += (
                '  ind = bodo.utils.conversion.coerce_to_ndarray(ind)\n')
        kznu__qensr = (
            'bodo.hiframes.pd_dataframe_ext.get_dataframe_index(df)[ind]')
        if df.is_table_format:
            xwefe__vfc = (
                f'bodo.hiframes.pd_dataframe_ext.get_dataframe_table(df)[ind]')
        else:
            xwefe__vfc = ', '.join(
                f'bodo.hiframes.pd_dataframe_ext.get_dataframe_data(df, {df.columns.index(ale__eznq)})[ind]'
                 for ale__eznq in df.columns)
        return bodo.hiframes.dataframe_impl._gen_init_df(ctuoe__cevyj, df.
            columns, xwefe__vfc, kznu__qensr, out_df_type=df)
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
        ylr__kqdu = 'DataFrameILocType({})'.format(df_type)
        super(DataFrameILocType, self).__init__(ylr__kqdu)

    @property
    def mangling_args(self):
        return self.__class__.__name__, (self._code,)
    ndim = 2


@register_model(DataFrameILocType)
class DataFrameILocModel(models.StructModel):

    def __init__(self, dmm, fe_type):
        ceid__bijf = [('obj', fe_type.df_type)]
        super(DataFrameILocModel, self).__init__(dmm, fe_type, ceid__bijf)


make_attribute_wrapper(DataFrameILocType, 'obj', '_obj')


@intrinsic
def init_dataframe_iloc(typingctx, obj=None):

    def codegen(context, builder, signature, args):
        iisrn__spl, = args
        ikn__bqb = signature.return_type
        ingg__rli = cgutils.create_struct_proxy(ikn__bqb)(context, builder)
        ingg__rli.obj = iisrn__spl
        context.nrt.incref(builder, signature.args[0], iisrn__spl)
        return ingg__rli._getvalue()
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
        guq__dlr = len(df.data)
        if is_overload_constant_int(idx.types[1]):
            is_out_series = True
            lgfj__qdtrj = get_overload_const_int(idx.types[1])
            if lgfj__qdtrj < 0 or lgfj__qdtrj >= guq__dlr:
                raise BodoError(
                    'df.iloc: column integer must refer to a valid column number'
                    )
            yex__oeywi = [lgfj__qdtrj]
        else:
            is_out_series = False
            yex__oeywi = get_overload_const_list(idx.types[1])
            if any(not isinstance(ind, int) or ind < 0 or ind >= guq__dlr for
                ind in yex__oeywi):
                raise BodoError(
                    'df.iloc: column list must be integers referring to a valid column number'
                    )
        col_names = tuple(pd.Series(df.columns, dtype=object)[yex__oeywi])
        if isinstance(idx.types[0], types.Integer):
            if isinstance(idx.types[1], types.Integer):
                lgfj__qdtrj = yex__oeywi[0]

                def impl(I, idx):
                    df = I._obj
                    return bodo.utils.conversion.box_if_dt64(bodo.hiframes.
                        pd_dataframe_ext.get_dataframe_data(df, lgfj__qdtrj
                        )[idx[0]])
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
    ctuoe__cevyj = 'def impl(I, idx):\n'
    ctuoe__cevyj += '  df = I._obj\n'
    if isinstance(idx_typ, types.SliceType):
        ctuoe__cevyj += f'  idx_t = {idx}\n'
    else:
        ctuoe__cevyj += (
            f'  idx_t = bodo.utils.conversion.coerce_to_ndarray({idx})\n')
    kznu__qensr = (
        'bodo.hiframes.pd_dataframe_ext.get_dataframe_index(df)[idx_t]')
    xwefe__vfc = ', '.join(
        f'bodo.hiframes.pd_dataframe_ext.get_dataframe_data(df, {df.columns.index(ale__eznq)})[idx_t]'
         for ale__eznq in col_names)
    if is_out_series:
        bqaf__pxls = f"'{col_names[0]}'" if isinstance(col_names[0], str
            ) else f'{col_names[0]}'
        ctuoe__cevyj += f"""  return bodo.hiframes.pd_series_ext.init_series({xwefe__vfc}, {kznu__qensr}, {bqaf__pxls})
"""
        thzyz__fnta = {}
        exec(ctuoe__cevyj, {'bodo': bodo}, thzyz__fnta)
        return thzyz__fnta['impl']
    return bodo.hiframes.dataframe_impl._gen_init_df(ctuoe__cevyj,
        col_names, xwefe__vfc, kznu__qensr)


def _gen_iloc_getitem_row_impl(df, col_names, idx):
    ctuoe__cevyj = 'def impl(I, idx):\n'
    ctuoe__cevyj += '  df = I._obj\n'
    zrv__xdff = ', '.join(
        f'bodo.hiframes.pd_dataframe_ext.get_dataframe_data(df, {df.columns.index(ale__eznq)})[{idx}]'
         for ale__eznq in col_names)
    ctuoe__cevyj += f"""  row_idx = bodo.hiframes.pd_index_ext.init_heter_index({gen_const_tup(col_names)}, None)
"""
    ctuoe__cevyj += f"""  return bodo.hiframes.pd_series_ext.init_series(({zrv__xdff},), row_idx, None)
"""
    thzyz__fnta = {}
    exec(ctuoe__cevyj, {'bodo': bodo}, thzyz__fnta)
    impl = thzyz__fnta['impl']
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
        ylr__kqdu = 'DataFrameLocType({})'.format(df_type)
        super(DataFrameLocType, self).__init__(ylr__kqdu)

    @property
    def mangling_args(self):
        return self.__class__.__name__, (self._code,)
    ndim = 2


@register_model(DataFrameLocType)
class DataFrameLocModel(models.StructModel):

    def __init__(self, dmm, fe_type):
        ceid__bijf = [('obj', fe_type.df_type)]
        super(DataFrameLocModel, self).__init__(dmm, fe_type, ceid__bijf)


make_attribute_wrapper(DataFrameLocType, 'obj', '_obj')


@intrinsic
def init_dataframe_loc(typingctx, obj=None):

    def codegen(context, builder, signature, args):
        iisrn__spl, = args
        mlu__zhs = signature.return_type
        jmv__ivzi = cgutils.create_struct_proxy(mlu__zhs)(context, builder)
        jmv__ivzi.obj = iisrn__spl
        context.nrt.incref(builder, signature.args[0], iisrn__spl)
        return jmv__ivzi._getvalue()
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
        ctuoe__cevyj = 'def impl(I, idx):\n'
        ctuoe__cevyj += '  df = I._obj\n'
        ctuoe__cevyj += (
            '  idx_t = bodo.utils.conversion.coerce_to_ndarray(idx)\n')
        kznu__qensr = (
            'bodo.hiframes.pd_dataframe_ext.get_dataframe_index(df)[idx_t]')
        xwefe__vfc = ', '.join(
            'bodo.hiframes.pd_dataframe_ext.get_dataframe_data(df, {})[idx_t]'
            .format(df.columns.index(ale__eznq)) for ale__eznq in df.columns)
        return bodo.hiframes.dataframe_impl._gen_init_df(ctuoe__cevyj, df.
            columns, xwefe__vfc, kznu__qensr)
    if isinstance(idx, types.BaseTuple) and len(idx) == 2:
        ixkuo__jyb = idx.types[1]
        if is_overload_constant_str(ixkuo__jyb):
            tsiyl__bwmvl = get_overload_const_str(ixkuo__jyb)
            lgfj__qdtrj = df.columns.index(tsiyl__bwmvl)

            def impl_col_name(I, idx):
                df = I._obj
                kznu__qensr = (bodo.hiframes.pd_dataframe_ext.
                    get_dataframe_index(df))
                pet__nmf = bodo.hiframes.pd_dataframe_ext.get_dataframe_data(df
                    , lgfj__qdtrj)
                return bodo.hiframes.pd_series_ext.init_series(pet__nmf,
                    kznu__qensr, tsiyl__bwmvl).loc[idx[0]]
            return impl_col_name
        if is_overload_constant_list(ixkuo__jyb):
            col_idx_list = get_overload_const_list(ixkuo__jyb)
            if len(col_idx_list) > 0 and not isinstance(col_idx_list[0], (
                bool, np.bool_)) and not all(ale__eznq in df.columns for
                ale__eznq in col_idx_list):
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
    xwefe__vfc = ', '.join(
        'bodo.hiframes.pd_dataframe_ext.get_dataframe_data(df, {})[idx[0]]'
        .format(df.columns.index(ale__eznq)) for ale__eznq in col_idx_list)
    kznu__qensr = (
        'bodo.hiframes.pd_dataframe_ext.get_dataframe_index(df)[idx[0]]')
    ctuoe__cevyj = 'def impl(I, idx):\n'
    ctuoe__cevyj += '  df = I._obj\n'
    return bodo.hiframes.dataframe_impl._gen_init_df(ctuoe__cevyj,
        col_idx_list, xwefe__vfc, kznu__qensr)


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
        ylr__kqdu = 'DataFrameIatType({})'.format(df_type)
        super(DataFrameIatType, self).__init__(ylr__kqdu)

    @property
    def mangling_args(self):
        return self.__class__.__name__, (self._code,)
    ndim = 2


@register_model(DataFrameIatType)
class DataFrameIatModel(models.StructModel):

    def __init__(self, dmm, fe_type):
        ceid__bijf = [('obj', fe_type.df_type)]
        super(DataFrameIatModel, self).__init__(dmm, fe_type, ceid__bijf)


make_attribute_wrapper(DataFrameIatType, 'obj', '_obj')


@intrinsic
def init_dataframe_iat(typingctx, obj=None):

    def codegen(context, builder, signature, args):
        iisrn__spl, = args
        vdbi__yzyd = signature.return_type
        sbkj__dbpm = cgutils.create_struct_proxy(vdbi__yzyd)(context, builder)
        sbkj__dbpm.obj = iisrn__spl
        context.nrt.incref(builder, signature.args[0], iisrn__spl)
        return sbkj__dbpm._getvalue()
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
        lgfj__qdtrj = get_overload_const_int(idx.types[1])

        def impl_col_ind(I, idx):
            df = I._obj
            pet__nmf = bodo.hiframes.pd_dataframe_ext.get_dataframe_data(df,
                lgfj__qdtrj)
            return pet__nmf[idx[0]]
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
        lgfj__qdtrj = get_overload_const_int(idx.types[1])
        if is_immutable_array(I.df_type.data[lgfj__qdtrj]):
            raise BodoError(
                f'DataFrame setitem not supported for column with immutable array type {I.df_type.data}'
                )

        def impl_col_ind(I, idx, val):
            df = I._obj
            pet__nmf = bodo.hiframes.pd_dataframe_ext.get_dataframe_data(df,
                lgfj__qdtrj)
            pet__nmf[idx[0]] = bodo.utils.conversion.unbox_if_timestamp(val)
        return impl_col_ind
    raise BodoError('df.iat[] setitem using {} not supported'.format(idx))


@lower_cast(DataFrameIatType, DataFrameIatType)
@lower_cast(DataFrameILocType, DataFrameILocType)
@lower_cast(DataFrameLocType, DataFrameLocType)
def cast_series_iat(context, builder, fromty, toty, val):
    sbkj__dbpm = cgutils.create_struct_proxy(fromty)(context, builder, val)
    ujh__tfsu = context.cast(builder, sbkj__dbpm.obj, fromty.df_type, toty.
        df_type)
    xzuvg__sqtz = cgutils.create_struct_proxy(toty)(context, builder)
    xzuvg__sqtz.obj = ujh__tfsu
    return xzuvg__sqtz._getvalue()
