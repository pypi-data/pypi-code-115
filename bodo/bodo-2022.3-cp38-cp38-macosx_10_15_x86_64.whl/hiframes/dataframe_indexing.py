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
            fcya__igxi = idx
            wkqq__louo = df.data
            uqlc__pdun = df.columns
            giqyc__xnr = self.replace_range_with_numeric_idx_if_needed(df,
                fcya__igxi)
            bkwzb__tjh = DataFrameType(wkqq__louo, giqyc__xnr, uqlc__pdun)
            return bkwzb__tjh(*args)
        if isinstance(idx, types.BaseTuple) and len(idx) == 2:
            swhq__erno = idx.types[0]
            nbv__lsg = idx.types[1]
            if isinstance(swhq__erno, types.Integer):
                if not isinstance(df.index, bodo.hiframes.pd_index_ext.
                    RangeIndexType):
                    raise_bodo_error(
                        'Dataframe.loc[int, col_ind] getitem only supported for dataframes with RangeIndexes'
                        )
                if is_overload_constant_str(nbv__lsg):
                    cqbr__dram = get_overload_const_str(nbv__lsg)
                    if cqbr__dram not in df.columns:
                        raise_bodo_error(
                            'dataframe {} does not include column {}'.
                            format(df, cqbr__dram))
                    nni__kxwhn = df.columns.index(cqbr__dram)
                    return df.data[nni__kxwhn].dtype(*args)
                if isinstance(nbv__lsg, types.UnicodeType):
                    raise_bodo_error(
                        f'DataFrame.loc[] getitem (location-based indexing) requires constant column names. For more information, see https://docs.bodo.ai/latest/source/programming_with_bodo/require_constants.html.'
                        )
                else:
                    raise_bodo_error(
                        f'DataFrame.loc[] getitem (location-based indexing) using {idx} not supported yet.'
                        )
            if is_list_like_index_type(swhq__erno
                ) and swhq__erno.dtype == types.bool_ or isinstance(swhq__erno,
                types.SliceType):
                giqyc__xnr = self.replace_range_with_numeric_idx_if_needed(df,
                    swhq__erno)
                if is_overload_constant_str(nbv__lsg):
                    dfbqx__rrs = get_overload_const_str(nbv__lsg)
                    if dfbqx__rrs not in df.columns:
                        raise_bodo_error(
                            f'dataframe {df} does not include column {dfbqx__rrs}'
                            )
                    nni__kxwhn = df.columns.index(dfbqx__rrs)
                    nqql__qqlpu = df.data[nni__kxwhn]
                    qzh__kjj = nqql__qqlpu.dtype
                    tuh__dui = types.literal(df.columns[nni__kxwhn])
                    bkwzb__tjh = bodo.SeriesType(qzh__kjj, nqql__qqlpu,
                        giqyc__xnr, tuh__dui)
                    return bkwzb__tjh(*args)
                if isinstance(nbv__lsg, types.UnicodeType):
                    raise_bodo_error(
                        f'DataFrame.loc[] getitem (location-based indexing) requires constant column names. For more information, see https://docs.bodo.ai/latest/source/programming_with_bodo/require_constants.html.'
                        )
                elif is_overload_constant_list(nbv__lsg):
                    hxx__soj = get_overload_const_list(nbv__lsg)
                    vmzju__ojclj = types.unliteral(nbv__lsg)
                    if vmzju__ojclj.dtype == types.bool_:
                        if len(df.columns) != len(hxx__soj):
                            raise_bodo_error(
                                f'dataframe {df} has {len(df.columns)} columns, but boolean array used with DataFrame.loc[] {hxx__soj} has {len(hxx__soj)} values'
                                )
                        cmtx__egwi = []
                        mvgg__sffda = []
                        for gssq__bgmb in range(len(hxx__soj)):
                            if hxx__soj[gssq__bgmb]:
                                cmtx__egwi.append(df.columns[gssq__bgmb])
                                mvgg__sffda.append(df.data[gssq__bgmb])
                        qrnx__opqa = tuple()
                        bkwzb__tjh = DataFrameType(tuple(mvgg__sffda),
                            giqyc__xnr, tuple(cmtx__egwi))
                        return bkwzb__tjh(*args)
                    elif vmzju__ojclj.dtype == bodo.string_type:
                        qrnx__opqa, mvgg__sffda = self.get_kept_cols_and_data(
                            df, hxx__soj)
                        bkwzb__tjh = DataFrameType(mvgg__sffda, giqyc__xnr,
                            qrnx__opqa)
                        return bkwzb__tjh(*args)
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
                cmtx__egwi = []
                mvgg__sffda = []
                for gssq__bgmb, qki__tci in enumerate(df.columns):
                    if qki__tci[0] != ind_val:
                        continue
                    cmtx__egwi.append(qki__tci[1] if len(qki__tci) == 2 else
                        qki__tci[1:])
                    mvgg__sffda.append(df.data[gssq__bgmb])
                nqql__qqlpu = tuple(mvgg__sffda)
                qqd__qkz = df.index
                lvtop__csmp = tuple(cmtx__egwi)
                bkwzb__tjh = DataFrameType(nqql__qqlpu, qqd__qkz, lvtop__csmp)
                return bkwzb__tjh(*args)
            else:
                if ind_val not in df.columns:
                    raise_bodo_error('dataframe {} does not include column {}'
                        .format(df, ind_val))
                nni__kxwhn = df.columns.index(ind_val)
                nqql__qqlpu = df.data[nni__kxwhn]
                qzh__kjj = nqql__qqlpu.dtype
                qqd__qkz = df.index
                tuh__dui = types.literal(df.columns[nni__kxwhn])
                bkwzb__tjh = bodo.SeriesType(qzh__kjj, nqql__qqlpu,
                    qqd__qkz, tuh__dui)
                return bkwzb__tjh(*args)
        if isinstance(ind, types.Integer) or isinstance(ind, types.UnicodeType
            ):
            raise_bodo_error(
                'df[] getitem selecting a subset of columns requires providing constant column names. For more information, see https://docs.bodo.ai/latest/source/programming_with_bodo/require_constants.html'
                )
        if is_list_like_index_type(ind
            ) and ind.dtype == types.bool_ or isinstance(ind, types.SliceType):
            nqql__qqlpu = df.data
            qqd__qkz = self.replace_range_with_numeric_idx_if_needed(df, ind)
            lvtop__csmp = df.columns
            bkwzb__tjh = DataFrameType(nqql__qqlpu, qqd__qkz, lvtop__csmp,
                is_table_format=df.is_table_format)
            return bkwzb__tjh(*args)
        elif is_overload_constant_list(ind):
            rwn__qcjc = get_overload_const_list(ind)
            lvtop__csmp, nqql__qqlpu = self.get_kept_cols_and_data(df,
                rwn__qcjc)
            qqd__qkz = df.index
            bkwzb__tjh = DataFrameType(nqql__qqlpu, qqd__qkz, lvtop__csmp)
            return bkwzb__tjh(*args)
        raise_bodo_error(
            f'df[] getitem using {ind} not supported. If you are trying to select a subset of the columns, you must provide the column names you are selecting as a constant. See https://docs.bodo.ai/latest/source/programming_with_bodo/require_constants.html'
            )

    def get_kept_cols_and_data(self, df, cols_to_keep_list):
        for mhifv__oqst in cols_to_keep_list:
            if mhifv__oqst not in df.columns:
                raise_bodo_error('Column {} not found in dataframe columns {}'
                    .format(mhifv__oqst, df.columns))
        lvtop__csmp = tuple(cols_to_keep_list)
        nqql__qqlpu = tuple(df.data[df.columns.index(uobce__zfb)] for
            uobce__zfb in lvtop__csmp)
        return lvtop__csmp, nqql__qqlpu

    def replace_range_with_numeric_idx_if_needed(self, df, ind):
        giqyc__xnr = bodo.hiframes.pd_index_ext.NumericIndexType(types.
            int64, df.index.name_typ) if not isinstance(ind, types.SliceType
            ) and isinstance(df.index, bodo.hiframes.pd_index_ext.
            RangeIndexType) else df.index
        return giqyc__xnr


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
            cmtx__egwi = []
            mvgg__sffda = []
            for gssq__bgmb, qki__tci in enumerate(df.columns):
                if qki__tci[0] != ind_val:
                    continue
                cmtx__egwi.append(qki__tci[1] if len(qki__tci) == 2 else
                    qki__tci[1:])
                mvgg__sffda.append(
                    'bodo.hiframes.pd_dataframe_ext.get_dataframe_data(df, {})'
                    .format(gssq__bgmb))
            rzcr__eiqh = 'def impl(df, ind):\n'
            dslne__fnfjx = (
                'bodo.hiframes.pd_dataframe_ext.get_dataframe_index(df)')
            return bodo.hiframes.dataframe_impl._gen_init_df(rzcr__eiqh,
                cmtx__egwi, ', '.join(mvgg__sffda), dslne__fnfjx)
        if ind_val not in df.columns:
            raise_bodo_error('dataframe {} does not include column {}'.
                format(df, ind_val))
        col_no = df.columns.index(ind_val)
        return lambda df, ind: bodo.hiframes.pd_series_ext.init_series(bodo
            .hiframes.pd_dataframe_ext.get_dataframe_data(df, col_no), bodo
            .hiframes.pd_dataframe_ext.get_dataframe_index(df), ind_val)
    if is_overload_constant_list(ind):
        rwn__qcjc = get_overload_const_list(ind)
        for mhifv__oqst in rwn__qcjc:
            if mhifv__oqst not in df.columns:
                raise_bodo_error('Column {} not found in dataframe columns {}'
                    .format(mhifv__oqst, df.columns))
        mvgg__sffda = ', '.join(
            'bodo.hiframes.pd_dataframe_ext.get_dataframe_data(df, {}).copy()'
            .format(df.columns.index(mhifv__oqst)) for mhifv__oqst in rwn__qcjc
            )
        rzcr__eiqh = 'def impl(df, ind):\n'
        dslne__fnfjx = 'bodo.hiframes.pd_dataframe_ext.get_dataframe_index(df)'
        return bodo.hiframes.dataframe_impl._gen_init_df(rzcr__eiqh,
            rwn__qcjc, mvgg__sffda, dslne__fnfjx)
    if is_list_like_index_type(ind) and ind.dtype == types.bool_ or isinstance(
        ind, types.SliceType):
        rzcr__eiqh = 'def impl(df, ind):\n'
        if not isinstance(ind, types.SliceType):
            rzcr__eiqh += (
                '  ind = bodo.utils.conversion.coerce_to_ndarray(ind)\n')
        dslne__fnfjx = (
            'bodo.hiframes.pd_dataframe_ext.get_dataframe_index(df)[ind]')
        if df.is_table_format:
            mvgg__sffda = (
                f'bodo.hiframes.pd_dataframe_ext.get_dataframe_table(df)[ind]')
        else:
            mvgg__sffda = ', '.join(
                f'bodo.hiframes.pd_dataframe_ext.get_dataframe_data(df, {df.columns.index(mhifv__oqst)})[ind]'
                 for mhifv__oqst in df.columns)
        return bodo.hiframes.dataframe_impl._gen_init_df(rzcr__eiqh, df.
            columns, mvgg__sffda, dslne__fnfjx, out_df_type=df)
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
        uobce__zfb = 'DataFrameILocType({})'.format(df_type)
        super(DataFrameILocType, self).__init__(uobce__zfb)

    @property
    def mangling_args(self):
        return self.__class__.__name__, (self._code,)
    ndim = 2


@register_model(DataFrameILocType)
class DataFrameILocModel(models.StructModel):

    def __init__(self, dmm, fe_type):
        fsprg__dngvy = [('obj', fe_type.df_type)]
        super(DataFrameILocModel, self).__init__(dmm, fe_type, fsprg__dngvy)


make_attribute_wrapper(DataFrameILocType, 'obj', '_obj')


@intrinsic
def init_dataframe_iloc(typingctx, obj=None):

    def codegen(context, builder, signature, args):
        fzt__tkrjg, = args
        mhr__oyejo = signature.return_type
        zbo__iyj = cgutils.create_struct_proxy(mhr__oyejo)(context, builder)
        zbo__iyj.obj = fzt__tkrjg
        context.nrt.incref(builder, signature.args[0], fzt__tkrjg)
        return zbo__iyj._getvalue()
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
        rmr__sgb = len(df.data)
        if is_overload_constant_int(idx.types[1]):
            is_out_series = True
            ohl__ulmui = get_overload_const_int(idx.types[1])
            if ohl__ulmui < 0 or ohl__ulmui >= rmr__sgb:
                raise BodoError(
                    'df.iloc: column integer must refer to a valid column number'
                    )
            xqma__hog = [ohl__ulmui]
        else:
            is_out_series = False
            xqma__hog = get_overload_const_list(idx.types[1])
            if any(not isinstance(ind, int) or ind < 0 or ind >= rmr__sgb for
                ind in xqma__hog):
                raise BodoError(
                    'df.iloc: column list must be integers referring to a valid column number'
                    )
        col_names = tuple(pd.Series(df.columns, dtype=object)[xqma__hog])
        if isinstance(idx.types[0], types.Integer):
            if isinstance(idx.types[1], types.Integer):
                ohl__ulmui = xqma__hog[0]

                def impl(I, idx):
                    df = I._obj
                    return bodo.utils.conversion.box_if_dt64(bodo.hiframes.
                        pd_dataframe_ext.get_dataframe_data(df, ohl__ulmui)
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
    rzcr__eiqh = 'def impl(I, idx):\n'
    rzcr__eiqh += '  df = I._obj\n'
    if isinstance(idx_typ, types.SliceType):
        rzcr__eiqh += f'  idx_t = {idx}\n'
    else:
        rzcr__eiqh += (
            f'  idx_t = bodo.utils.conversion.coerce_to_ndarray({idx})\n')
    dslne__fnfjx = (
        'bodo.hiframes.pd_dataframe_ext.get_dataframe_index(df)[idx_t]')
    mvgg__sffda = ', '.join(
        f'bodo.hiframes.pd_dataframe_ext.get_dataframe_data(df, {df.columns.index(mhifv__oqst)})[idx_t]'
         for mhifv__oqst in col_names)
    if is_out_series:
        fph__xtgyp = f"'{col_names[0]}'" if isinstance(col_names[0], str
            ) else f'{col_names[0]}'
        rzcr__eiqh += f"""  return bodo.hiframes.pd_series_ext.init_series({mvgg__sffda}, {dslne__fnfjx}, {fph__xtgyp})
"""
        fwnad__buu = {}
        exec(rzcr__eiqh, {'bodo': bodo}, fwnad__buu)
        return fwnad__buu['impl']
    return bodo.hiframes.dataframe_impl._gen_init_df(rzcr__eiqh, col_names,
        mvgg__sffda, dslne__fnfjx)


def _gen_iloc_getitem_row_impl(df, col_names, idx):
    rzcr__eiqh = 'def impl(I, idx):\n'
    rzcr__eiqh += '  df = I._obj\n'
    qvlhm__iwr = ', '.join(
        f'bodo.hiframes.pd_dataframe_ext.get_dataframe_data(df, {df.columns.index(mhifv__oqst)})[{idx}]'
         for mhifv__oqst in col_names)
    rzcr__eiqh += f"""  row_idx = bodo.hiframes.pd_index_ext.init_heter_index({gen_const_tup(col_names)}, None)
"""
    rzcr__eiqh += f"""  return bodo.hiframes.pd_series_ext.init_series(({qvlhm__iwr},), row_idx, None)
"""
    fwnad__buu = {}
    exec(rzcr__eiqh, {'bodo': bodo}, fwnad__buu)
    impl = fwnad__buu['impl']
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
        uobce__zfb = 'DataFrameLocType({})'.format(df_type)
        super(DataFrameLocType, self).__init__(uobce__zfb)

    @property
    def mangling_args(self):
        return self.__class__.__name__, (self._code,)
    ndim = 2


@register_model(DataFrameLocType)
class DataFrameLocModel(models.StructModel):

    def __init__(self, dmm, fe_type):
        fsprg__dngvy = [('obj', fe_type.df_type)]
        super(DataFrameLocModel, self).__init__(dmm, fe_type, fsprg__dngvy)


make_attribute_wrapper(DataFrameLocType, 'obj', '_obj')


@intrinsic
def init_dataframe_loc(typingctx, obj=None):

    def codegen(context, builder, signature, args):
        fzt__tkrjg, = args
        awvr__qdkkz = signature.return_type
        vwqld__norq = cgutils.create_struct_proxy(awvr__qdkkz)(context, builder
            )
        vwqld__norq.obj = fzt__tkrjg
        context.nrt.incref(builder, signature.args[0], fzt__tkrjg)
        return vwqld__norq._getvalue()
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
        rzcr__eiqh = 'def impl(I, idx):\n'
        rzcr__eiqh += '  df = I._obj\n'
        rzcr__eiqh += (
            '  idx_t = bodo.utils.conversion.coerce_to_ndarray(idx)\n')
        dslne__fnfjx = (
            'bodo.hiframes.pd_dataframe_ext.get_dataframe_index(df)[idx_t]')
        mvgg__sffda = ', '.join(
            'bodo.hiframes.pd_dataframe_ext.get_dataframe_data(df, {})[idx_t]'
            .format(df.columns.index(mhifv__oqst)) for mhifv__oqst in df.
            columns)
        return bodo.hiframes.dataframe_impl._gen_init_df(rzcr__eiqh, df.
            columns, mvgg__sffda, dslne__fnfjx)
    if isinstance(idx, types.BaseTuple) and len(idx) == 2:
        hbj__ofkwl = idx.types[1]
        if is_overload_constant_str(hbj__ofkwl):
            zvx__xgnd = get_overload_const_str(hbj__ofkwl)
            ohl__ulmui = df.columns.index(zvx__xgnd)

            def impl_col_name(I, idx):
                df = I._obj
                dslne__fnfjx = (bodo.hiframes.pd_dataframe_ext.
                    get_dataframe_index(df))
                ggwbh__avvs = (bodo.hiframes.pd_dataframe_ext.
                    get_dataframe_data(df, ohl__ulmui))
                return bodo.hiframes.pd_series_ext.init_series(ggwbh__avvs,
                    dslne__fnfjx, zvx__xgnd).loc[idx[0]]
            return impl_col_name
        if is_overload_constant_list(hbj__ofkwl):
            col_idx_list = get_overload_const_list(hbj__ofkwl)
            if len(col_idx_list) > 0 and not isinstance(col_idx_list[0], (
                bool, np.bool_)) and not all(mhifv__oqst in df.columns for
                mhifv__oqst in col_idx_list):
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
    mvgg__sffda = ', '.join(
        'bodo.hiframes.pd_dataframe_ext.get_dataframe_data(df, {})[idx[0]]'
        .format(df.columns.index(mhifv__oqst)) for mhifv__oqst in col_idx_list)
    dslne__fnfjx = (
        'bodo.hiframes.pd_dataframe_ext.get_dataframe_index(df)[idx[0]]')
    rzcr__eiqh = 'def impl(I, idx):\n'
    rzcr__eiqh += '  df = I._obj\n'
    return bodo.hiframes.dataframe_impl._gen_init_df(rzcr__eiqh,
        col_idx_list, mvgg__sffda, dslne__fnfjx)


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
        uobce__zfb = 'DataFrameIatType({})'.format(df_type)
        super(DataFrameIatType, self).__init__(uobce__zfb)

    @property
    def mangling_args(self):
        return self.__class__.__name__, (self._code,)
    ndim = 2


@register_model(DataFrameIatType)
class DataFrameIatModel(models.StructModel):

    def __init__(self, dmm, fe_type):
        fsprg__dngvy = [('obj', fe_type.df_type)]
        super(DataFrameIatModel, self).__init__(dmm, fe_type, fsprg__dngvy)


make_attribute_wrapper(DataFrameIatType, 'obj', '_obj')


@intrinsic
def init_dataframe_iat(typingctx, obj=None):

    def codegen(context, builder, signature, args):
        fzt__tkrjg, = args
        xbik__kxq = signature.return_type
        emjr__tkx = cgutils.create_struct_proxy(xbik__kxq)(context, builder)
        emjr__tkx.obj = fzt__tkrjg
        context.nrt.incref(builder, signature.args[0], fzt__tkrjg)
        return emjr__tkx._getvalue()
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
        ohl__ulmui = get_overload_const_int(idx.types[1])

        def impl_col_ind(I, idx):
            df = I._obj
            ggwbh__avvs = bodo.hiframes.pd_dataframe_ext.get_dataframe_data(df,
                ohl__ulmui)
            return ggwbh__avvs[idx[0]]
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
        ohl__ulmui = get_overload_const_int(idx.types[1])
        if is_immutable_array(I.df_type.data[ohl__ulmui]):
            raise BodoError(
                f'DataFrame setitem not supported for column with immutable array type {I.df_type.data}'
                )

        def impl_col_ind(I, idx, val):
            df = I._obj
            ggwbh__avvs = bodo.hiframes.pd_dataframe_ext.get_dataframe_data(df,
                ohl__ulmui)
            ggwbh__avvs[idx[0]] = bodo.utils.conversion.unbox_if_timestamp(val)
        return impl_col_ind
    raise BodoError('df.iat[] setitem using {} not supported'.format(idx))


@lower_cast(DataFrameIatType, DataFrameIatType)
@lower_cast(DataFrameILocType, DataFrameILocType)
@lower_cast(DataFrameLocType, DataFrameLocType)
def cast_series_iat(context, builder, fromty, toty, val):
    emjr__tkx = cgutils.create_struct_proxy(fromty)(context, builder, val)
    bej__eoep = context.cast(builder, emjr__tkx.obj, fromty.df_type, toty.
        df_type)
    pjmmu__xhyc = cgutils.create_struct_proxy(toty)(context, builder)
    pjmmu__xhyc.obj = bej__eoep
    return pjmmu__xhyc._getvalue()
