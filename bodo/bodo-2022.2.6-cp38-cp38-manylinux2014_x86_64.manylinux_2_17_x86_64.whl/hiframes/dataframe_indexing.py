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
            nbz__vcpmb = idx
            qndg__xbcgy = df.data
            ytog__iurgn = df.columns
            cxx__upkp = self.replace_range_with_numeric_idx_if_needed(df,
                nbz__vcpmb)
            dke__lcgrx = DataFrameType(qndg__xbcgy, cxx__upkp, ytog__iurgn)
            return dke__lcgrx(*args)
        if isinstance(idx, types.BaseTuple) and len(idx) == 2:
            sshob__htmob = idx.types[0]
            dgnbx__ffx = idx.types[1]
            if isinstance(sshob__htmob, types.Integer):
                if not isinstance(df.index, bodo.hiframes.pd_index_ext.
                    RangeIndexType):
                    raise_bodo_error(
                        'Dataframe.loc[int, col_ind] getitem only supported for dataframes with RangeIndexes'
                        )
                if is_overload_constant_str(dgnbx__ffx):
                    pqv__vikg = get_overload_const_str(dgnbx__ffx)
                    if pqv__vikg not in df.columns:
                        raise_bodo_error(
                            'dataframe {} does not include column {}'.
                            format(df, pqv__vikg))
                    enfa__sbpk = df.columns.index(pqv__vikg)
                    return df.data[enfa__sbpk].dtype(*args)
                if isinstance(dgnbx__ffx, types.UnicodeType):
                    raise_bodo_error(
                        f'DataFrame.loc[] getitem (location-based indexing) requires constant column names. For more information, see https://docs.bodo.ai/latest/source/programming_with_bodo/require_constants.html.'
                        )
                else:
                    raise_bodo_error(
                        f'DataFrame.loc[] getitem (location-based indexing) using {idx} not supported yet.'
                        )
            if is_list_like_index_type(sshob__htmob
                ) and sshob__htmob.dtype == types.bool_ or isinstance(
                sshob__htmob, types.SliceType):
                cxx__upkp = self.replace_range_with_numeric_idx_if_needed(df,
                    sshob__htmob)
                if is_overload_constant_str(dgnbx__ffx):
                    yla__ldqi = get_overload_const_str(dgnbx__ffx)
                    if yla__ldqi not in df.columns:
                        raise_bodo_error(
                            f'dataframe {df} does not include column {yla__ldqi}'
                            )
                    enfa__sbpk = df.columns.index(yla__ldqi)
                    tidz__pbqfx = df.data[enfa__sbpk]
                    bbe__lgq = tidz__pbqfx.dtype
                    fggpv__jvd = types.literal(df.columns[enfa__sbpk])
                    dke__lcgrx = bodo.SeriesType(bbe__lgq, tidz__pbqfx,
                        cxx__upkp, fggpv__jvd)
                    return dke__lcgrx(*args)
                if isinstance(dgnbx__ffx, types.UnicodeType):
                    raise_bodo_error(
                        f'DataFrame.loc[] getitem (location-based indexing) requires constant column names. For more information, see https://docs.bodo.ai/latest/source/programming_with_bodo/require_constants.html.'
                        )
                elif is_overload_constant_list(dgnbx__ffx):
                    saajz__uncy = get_overload_const_list(dgnbx__ffx)
                    hymv__eosip = types.unliteral(dgnbx__ffx)
                    if hymv__eosip.dtype == types.bool_:
                        if len(df.columns) != len(saajz__uncy):
                            raise_bodo_error(
                                f'dataframe {df} has {len(df.columns)} columns, but boolean array used with DataFrame.loc[] {saajz__uncy} has {len(saajz__uncy)} values'
                                )
                        nmm__nih = []
                        uxj__zvowv = []
                        for htof__fpss in range(len(saajz__uncy)):
                            if saajz__uncy[htof__fpss]:
                                nmm__nih.append(df.columns[htof__fpss])
                                uxj__zvowv.append(df.data[htof__fpss])
                        lilb__hua = tuple()
                        dke__lcgrx = DataFrameType(tuple(uxj__zvowv),
                            cxx__upkp, tuple(nmm__nih))
                        return dke__lcgrx(*args)
                    elif hymv__eosip.dtype == bodo.string_type:
                        lilb__hua, uxj__zvowv = self.get_kept_cols_and_data(df,
                            saajz__uncy)
                        dke__lcgrx = DataFrameType(uxj__zvowv, cxx__upkp,
                            lilb__hua)
                        return dke__lcgrx(*args)
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
                nmm__nih = []
                uxj__zvowv = []
                for htof__fpss, hzr__fdzxs in enumerate(df.columns):
                    if hzr__fdzxs[0] != ind_val:
                        continue
                    nmm__nih.append(hzr__fdzxs[1] if len(hzr__fdzxs) == 2 else
                        hzr__fdzxs[1:])
                    uxj__zvowv.append(df.data[htof__fpss])
                tidz__pbqfx = tuple(uxj__zvowv)
                dfgqh__xsc = df.index
                dvq__bkm = tuple(nmm__nih)
                dke__lcgrx = DataFrameType(tidz__pbqfx, dfgqh__xsc, dvq__bkm)
                return dke__lcgrx(*args)
            else:
                if ind_val not in df.columns:
                    raise_bodo_error('dataframe {} does not include column {}'
                        .format(df, ind_val))
                enfa__sbpk = df.columns.index(ind_val)
                tidz__pbqfx = df.data[enfa__sbpk]
                bbe__lgq = tidz__pbqfx.dtype
                dfgqh__xsc = df.index
                fggpv__jvd = types.literal(df.columns[enfa__sbpk])
                dke__lcgrx = bodo.SeriesType(bbe__lgq, tidz__pbqfx,
                    dfgqh__xsc, fggpv__jvd)
                return dke__lcgrx(*args)
        if isinstance(ind, types.Integer) or isinstance(ind, types.UnicodeType
            ):
            raise_bodo_error(
                'df[] getitem selecting a subset of columns requires providing constant column names. For more information, see https://docs.bodo.ai/latest/source/programming_with_bodo/require_constants.html'
                )
        if is_list_like_index_type(ind
            ) and ind.dtype == types.bool_ or isinstance(ind, types.SliceType):
            tidz__pbqfx = df.data
            dfgqh__xsc = self.replace_range_with_numeric_idx_if_needed(df, ind)
            dvq__bkm = df.columns
            dke__lcgrx = DataFrameType(tidz__pbqfx, dfgqh__xsc, dvq__bkm,
                is_table_format=df.is_table_format)
            return dke__lcgrx(*args)
        elif is_overload_constant_list(ind):
            azp__njnyg = get_overload_const_list(ind)
            dvq__bkm, tidz__pbqfx = self.get_kept_cols_and_data(df, azp__njnyg)
            dfgqh__xsc = df.index
            dke__lcgrx = DataFrameType(tidz__pbqfx, dfgqh__xsc, dvq__bkm)
            return dke__lcgrx(*args)
        raise_bodo_error(
            f'df[] getitem using {ind} not supported. If you are trying to select a subset of the columns, you must provide the column names you are selecting as a constant. See https://docs.bodo.ai/latest/source/programming_with_bodo/require_constants.html'
            )

    def get_kept_cols_and_data(self, df, cols_to_keep_list):
        for ladfi__dunp in cols_to_keep_list:
            if ladfi__dunp not in df.columns:
                raise_bodo_error('Column {} not found in dataframe columns {}'
                    .format(ladfi__dunp, df.columns))
        dvq__bkm = tuple(cols_to_keep_list)
        tidz__pbqfx = tuple(df.data[df.columns.index(qopt__iyqm)] for
            qopt__iyqm in dvq__bkm)
        return dvq__bkm, tidz__pbqfx

    def replace_range_with_numeric_idx_if_needed(self, df, ind):
        cxx__upkp = bodo.hiframes.pd_index_ext.NumericIndexType(types.int64,
            df.index.name_typ) if not isinstance(ind, types.SliceType
            ) and isinstance(df.index, bodo.hiframes.pd_index_ext.
            RangeIndexType) else df.index
        return cxx__upkp


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
            nmm__nih = []
            uxj__zvowv = []
            for htof__fpss, hzr__fdzxs in enumerate(df.columns):
                if hzr__fdzxs[0] != ind_val:
                    continue
                nmm__nih.append(hzr__fdzxs[1] if len(hzr__fdzxs) == 2 else
                    hzr__fdzxs[1:])
                uxj__zvowv.append(
                    'bodo.hiframes.pd_dataframe_ext.get_dataframe_data(df, {})'
                    .format(htof__fpss))
            cae__cbo = 'def impl(df, ind):\n'
            gkpu__cdq = (
                'bodo.hiframes.pd_dataframe_ext.get_dataframe_index(df)')
            return bodo.hiframes.dataframe_impl._gen_init_df(cae__cbo,
                nmm__nih, ', '.join(uxj__zvowv), gkpu__cdq)
        if ind_val not in df.columns:
            raise_bodo_error('dataframe {} does not include column {}'.
                format(df, ind_val))
        col_no = df.columns.index(ind_val)
        return lambda df, ind: bodo.hiframes.pd_series_ext.init_series(bodo
            .hiframes.pd_dataframe_ext.get_dataframe_data(df, col_no), bodo
            .hiframes.pd_dataframe_ext.get_dataframe_index(df), ind_val)
    if is_overload_constant_list(ind):
        azp__njnyg = get_overload_const_list(ind)
        for ladfi__dunp in azp__njnyg:
            if ladfi__dunp not in df.columns:
                raise_bodo_error('Column {} not found in dataframe columns {}'
                    .format(ladfi__dunp, df.columns))
        uxj__zvowv = ', '.join(
            'bodo.hiframes.pd_dataframe_ext.get_dataframe_data(df, {}).copy()'
            .format(df.columns.index(ladfi__dunp)) for ladfi__dunp in
            azp__njnyg)
        cae__cbo = 'def impl(df, ind):\n'
        gkpu__cdq = 'bodo.hiframes.pd_dataframe_ext.get_dataframe_index(df)'
        return bodo.hiframes.dataframe_impl._gen_init_df(cae__cbo,
            azp__njnyg, uxj__zvowv, gkpu__cdq)
    if is_list_like_index_type(ind) and ind.dtype == types.bool_ or isinstance(
        ind, types.SliceType):
        cae__cbo = 'def impl(df, ind):\n'
        if not isinstance(ind, types.SliceType):
            cae__cbo += (
                '  ind = bodo.utils.conversion.coerce_to_ndarray(ind)\n')
        gkpu__cdq = (
            'bodo.hiframes.pd_dataframe_ext.get_dataframe_index(df)[ind]')
        if df.is_table_format:
            uxj__zvowv = (
                f'bodo.hiframes.pd_dataframe_ext.get_dataframe_table(df)[ind]')
        else:
            uxj__zvowv = ', '.join(
                f'bodo.hiframes.pd_dataframe_ext.get_dataframe_data(df, {df.columns.index(ladfi__dunp)})[ind]'
                 for ladfi__dunp in df.columns)
        return bodo.hiframes.dataframe_impl._gen_init_df(cae__cbo, df.
            columns, uxj__zvowv, gkpu__cdq, out_df_type=df)
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
        qopt__iyqm = 'DataFrameILocType({})'.format(df_type)
        super(DataFrameILocType, self).__init__(qopt__iyqm)

    @property
    def mangling_args(self):
        return self.__class__.__name__, (self._code,)
    ndim = 2


@register_model(DataFrameILocType)
class DataFrameILocModel(models.StructModel):

    def __init__(self, dmm, fe_type):
        qkfgh__okdwg = [('obj', fe_type.df_type)]
        super(DataFrameILocModel, self).__init__(dmm, fe_type, qkfgh__okdwg)


make_attribute_wrapper(DataFrameILocType, 'obj', '_obj')


@intrinsic
def init_dataframe_iloc(typingctx, obj=None):

    def codegen(context, builder, signature, args):
        kve__geqa, = args
        gbx__tbif = signature.return_type
        vhpjm__pdc = cgutils.create_struct_proxy(gbx__tbif)(context, builder)
        vhpjm__pdc.obj = kve__geqa
        context.nrt.incref(builder, signature.args[0], kve__geqa)
        return vhpjm__pdc._getvalue()
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
        bun__dgbw = len(df.data)
        if is_overload_constant_int(idx.types[1]):
            is_out_series = True
            ngkrd__uvnuv = get_overload_const_int(idx.types[1])
            if ngkrd__uvnuv < 0 or ngkrd__uvnuv >= bun__dgbw:
                raise BodoError(
                    'df.iloc: column integer must refer to a valid column number'
                    )
            bwxgx__qeozk = [ngkrd__uvnuv]
        else:
            is_out_series = False
            bwxgx__qeozk = get_overload_const_list(idx.types[1])
            if any(not isinstance(ind, int) or ind < 0 or ind >= bun__dgbw for
                ind in bwxgx__qeozk):
                raise BodoError(
                    'df.iloc: column list must be integers referring to a valid column number'
                    )
        col_names = tuple(pd.Series(df.columns, dtype=object)[bwxgx__qeozk])
        if isinstance(idx.types[0], types.Integer):
            if isinstance(idx.types[1], types.Integer):
                ngkrd__uvnuv = bwxgx__qeozk[0]

                def impl(I, idx):
                    df = I._obj
                    return bodo.utils.conversion.box_if_dt64(bodo.hiframes.
                        pd_dataframe_ext.get_dataframe_data(df,
                        ngkrd__uvnuv)[idx[0]])
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
    cae__cbo = 'def impl(I, idx):\n'
    cae__cbo += '  df = I._obj\n'
    if isinstance(idx_typ, types.SliceType):
        cae__cbo += f'  idx_t = {idx}\n'
    else:
        cae__cbo += (
            f'  idx_t = bodo.utils.conversion.coerce_to_ndarray({idx})\n')
    gkpu__cdq = 'bodo.hiframes.pd_dataframe_ext.get_dataframe_index(df)[idx_t]'
    uxj__zvowv = ', '.join(
        f'bodo.hiframes.pd_dataframe_ext.get_dataframe_data(df, {df.columns.index(ladfi__dunp)})[idx_t]'
         for ladfi__dunp in col_names)
    if is_out_series:
        saa__het = f"'{col_names[0]}'" if isinstance(col_names[0], str
            ) else f'{col_names[0]}'
        cae__cbo += f"""  return bodo.hiframes.pd_series_ext.init_series({uxj__zvowv}, {gkpu__cdq}, {saa__het})
"""
        ckbs__eqjsv = {}
        exec(cae__cbo, {'bodo': bodo}, ckbs__eqjsv)
        return ckbs__eqjsv['impl']
    return bodo.hiframes.dataframe_impl._gen_init_df(cae__cbo, col_names,
        uxj__zvowv, gkpu__cdq)


def _gen_iloc_getitem_row_impl(df, col_names, idx):
    cae__cbo = 'def impl(I, idx):\n'
    cae__cbo += '  df = I._obj\n'
    xwr__gny = ', '.join(
        f'bodo.hiframes.pd_dataframe_ext.get_dataframe_data(df, {df.columns.index(ladfi__dunp)})[{idx}]'
         for ladfi__dunp in col_names)
    cae__cbo += f"""  row_idx = bodo.hiframes.pd_index_ext.init_heter_index({gen_const_tup(col_names)}, None)
"""
    cae__cbo += (
        f'  return bodo.hiframes.pd_series_ext.init_series(({xwr__gny},), row_idx, None)\n'
        )
    ckbs__eqjsv = {}
    exec(cae__cbo, {'bodo': bodo}, ckbs__eqjsv)
    impl = ckbs__eqjsv['impl']
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
        qopt__iyqm = 'DataFrameLocType({})'.format(df_type)
        super(DataFrameLocType, self).__init__(qopt__iyqm)

    @property
    def mangling_args(self):
        return self.__class__.__name__, (self._code,)
    ndim = 2


@register_model(DataFrameLocType)
class DataFrameLocModel(models.StructModel):

    def __init__(self, dmm, fe_type):
        qkfgh__okdwg = [('obj', fe_type.df_type)]
        super(DataFrameLocModel, self).__init__(dmm, fe_type, qkfgh__okdwg)


make_attribute_wrapper(DataFrameLocType, 'obj', '_obj')


@intrinsic
def init_dataframe_loc(typingctx, obj=None):

    def codegen(context, builder, signature, args):
        kve__geqa, = args
        sqbr__rwj = signature.return_type
        ecfdc__nako = cgutils.create_struct_proxy(sqbr__rwj)(context, builder)
        ecfdc__nako.obj = kve__geqa
        context.nrt.incref(builder, signature.args[0], kve__geqa)
        return ecfdc__nako._getvalue()
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
        cae__cbo = 'def impl(I, idx):\n'
        cae__cbo += '  df = I._obj\n'
        cae__cbo += '  idx_t = bodo.utils.conversion.coerce_to_ndarray(idx)\n'
        gkpu__cdq = (
            'bodo.hiframes.pd_dataframe_ext.get_dataframe_index(df)[idx_t]')
        uxj__zvowv = ', '.join(
            'bodo.hiframes.pd_dataframe_ext.get_dataframe_data(df, {})[idx_t]'
            .format(df.columns.index(ladfi__dunp)) for ladfi__dunp in df.
            columns)
        return bodo.hiframes.dataframe_impl._gen_init_df(cae__cbo, df.
            columns, uxj__zvowv, gkpu__cdq)
    if isinstance(idx, types.BaseTuple) and len(idx) == 2:
        hii__fws = idx.types[1]
        if is_overload_constant_str(hii__fws):
            arjy__lhe = get_overload_const_str(hii__fws)
            ngkrd__uvnuv = df.columns.index(arjy__lhe)

            def impl_col_name(I, idx):
                df = I._obj
                gkpu__cdq = bodo.hiframes.pd_dataframe_ext.get_dataframe_index(
                    df)
                tryl__qhc = bodo.hiframes.pd_dataframe_ext.get_dataframe_data(
                    df, ngkrd__uvnuv)
                return bodo.hiframes.pd_series_ext.init_series(tryl__qhc,
                    gkpu__cdq, arjy__lhe).loc[idx[0]]
            return impl_col_name
        if is_overload_constant_list(hii__fws):
            col_idx_list = get_overload_const_list(hii__fws)
            if len(col_idx_list) > 0 and not isinstance(col_idx_list[0], (
                bool, np.bool_)) and not all(ladfi__dunp in df.columns for
                ladfi__dunp in col_idx_list):
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
    uxj__zvowv = ', '.join(
        'bodo.hiframes.pd_dataframe_ext.get_dataframe_data(df, {})[idx[0]]'
        .format(df.columns.index(ladfi__dunp)) for ladfi__dunp in col_idx_list)
    gkpu__cdq = (
        'bodo.hiframes.pd_dataframe_ext.get_dataframe_index(df)[idx[0]]')
    cae__cbo = 'def impl(I, idx):\n'
    cae__cbo += '  df = I._obj\n'
    return bodo.hiframes.dataframe_impl._gen_init_df(cae__cbo, col_idx_list,
        uxj__zvowv, gkpu__cdq)


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
        qopt__iyqm = 'DataFrameIatType({})'.format(df_type)
        super(DataFrameIatType, self).__init__(qopt__iyqm)

    @property
    def mangling_args(self):
        return self.__class__.__name__, (self._code,)
    ndim = 2


@register_model(DataFrameIatType)
class DataFrameIatModel(models.StructModel):

    def __init__(self, dmm, fe_type):
        qkfgh__okdwg = [('obj', fe_type.df_type)]
        super(DataFrameIatModel, self).__init__(dmm, fe_type, qkfgh__okdwg)


make_attribute_wrapper(DataFrameIatType, 'obj', '_obj')


@intrinsic
def init_dataframe_iat(typingctx, obj=None):

    def codegen(context, builder, signature, args):
        kve__geqa, = args
        mva__rgi = signature.return_type
        kqyb__fpcb = cgutils.create_struct_proxy(mva__rgi)(context, builder)
        kqyb__fpcb.obj = kve__geqa
        context.nrt.incref(builder, signature.args[0], kve__geqa)
        return kqyb__fpcb._getvalue()
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
        ngkrd__uvnuv = get_overload_const_int(idx.types[1])

        def impl_col_ind(I, idx):
            df = I._obj
            tryl__qhc = bodo.hiframes.pd_dataframe_ext.get_dataframe_data(df,
                ngkrd__uvnuv)
            return tryl__qhc[idx[0]]
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
        ngkrd__uvnuv = get_overload_const_int(idx.types[1])
        if is_immutable_array(I.df_type.data[ngkrd__uvnuv]):
            raise BodoError(
                f'DataFrame setitem not supported for column with immutable array type {I.df_type.data}'
                )

        def impl_col_ind(I, idx, val):
            df = I._obj
            tryl__qhc = bodo.hiframes.pd_dataframe_ext.get_dataframe_data(df,
                ngkrd__uvnuv)
            tryl__qhc[idx[0]] = bodo.utils.conversion.unbox_if_timestamp(val)
        return impl_col_ind
    raise BodoError('df.iat[] setitem using {} not supported'.format(idx))


@lower_cast(DataFrameIatType, DataFrameIatType)
@lower_cast(DataFrameILocType, DataFrameILocType)
@lower_cast(DataFrameLocType, DataFrameLocType)
def cast_series_iat(context, builder, fromty, toty, val):
    kqyb__fpcb = cgutils.create_struct_proxy(fromty)(context, builder, val)
    ypq__afznr = context.cast(builder, kqyb__fpcb.obj, fromty.df_type, toty
        .df_type)
    dpv__xoi = cgutils.create_struct_proxy(toty)(context, builder)
    dpv__xoi.obj = ypq__afznr
    return dpv__xoi._getvalue()
