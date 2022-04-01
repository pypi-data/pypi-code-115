"""
Common IR extension functions for connectors such as CSV, Parquet and JSON readers.
"""
from collections import defaultdict
import numba
from numba.core import ir, types
from numba.core.ir_utils import replace_vars_inner, visit_vars_inner
from numba.extending import box, models, register_model
from bodo.hiframes.table import TableType
from bodo.transforms.distributed_analysis import Distribution
from bodo.utils.utils import debug_prints


def connector_array_analysis(node, equiv_set, typemap, array_analysis):
    axg__ajaqc = []
    assert len(node.out_vars) > 0, 'empty {} in array analysis'.format(node
        .connector_typ)
    if node.connector_typ == 'csv' and node.chunksize is not None:
        return [], []
    refkn__uvth = []
    for xmbxu__wwh in node.out_vars:
        typ = typemap[xmbxu__wwh.name]
        if typ == types.none:
            continue
        una__swg = array_analysis._gen_shape_call(equiv_set, xmbxu__wwh,
            typ.ndim, None, axg__ajaqc)
        equiv_set.insert_equiv(xmbxu__wwh, una__swg)
        refkn__uvth.append(una__swg[0])
        equiv_set.define(xmbxu__wwh, set())
    if len(refkn__uvth) > 1:
        equiv_set.insert_equiv(*refkn__uvth)
    return [], axg__ajaqc


def connector_distributed_analysis(node, array_dists):
    from bodo.ir.sql_ext import SqlReader
    if isinstance(node, SqlReader) and not node.is_select_query:
        nwpo__ffy = Distribution.REP
    elif isinstance(node, SqlReader) and node.limit is not None:
        nwpo__ffy = Distribution.OneD_Var
    else:
        nwpo__ffy = Distribution.OneD
    for dyl__xavk in node.out_vars:
        if dyl__xavk.name in array_dists:
            nwpo__ffy = Distribution(min(nwpo__ffy.value, array_dists[
                dyl__xavk.name].value))
    for dyl__xavk in node.out_vars:
        array_dists[dyl__xavk.name] = nwpo__ffy


def connector_typeinfer(node, typeinferer):
    if node.connector_typ == 'csv':
        if node.chunksize is not None:
            typeinferer.lock_type(node.out_vars[0].name, node.out_types[0],
                loc=node.loc)
        else:
            typeinferer.lock_type(node.out_vars[0].name, TableType(tuple(
                node.out_types)), loc=node.loc)
            typeinferer.lock_type(node.out_vars[1].name, node.
                index_column_typ, loc=node.loc)
        return
    if node.connector_typ == 'parquet':
        typeinferer.lock_type(node.out_vars[0].name, TableType(tuple(node.
            out_types)), loc=node.loc)
        typeinferer.lock_type(node.out_vars[1].name, node.index_column_type,
            loc=node.loc)
        return
    for xmbxu__wwh, typ in zip(node.out_vars, node.out_types):
        typeinferer.lock_type(xmbxu__wwh.name, typ, loc=node.loc)


def visit_vars_connector(node, callback, cbdata):
    if debug_prints():
        print('visiting {} vars for:'.format(node.connector_typ), node)
        print('cbdata: ', sorted(cbdata.items()))
    ynowa__coqq = []
    for xmbxu__wwh in node.out_vars:
        laq__wazij = visit_vars_inner(xmbxu__wwh, callback, cbdata)
        ynowa__coqq.append(laq__wazij)
    node.out_vars = ynowa__coqq
    if node.connector_typ in ('csv', 'parquet', 'json'):
        node.file_name = visit_vars_inner(node.file_name, callback, cbdata)
    if node.connector_typ == 'csv':
        node.nrows = visit_vars_inner(node.nrows, callback, cbdata)
        node.skiprows = visit_vars_inner(node.skiprows, callback, cbdata)
    if node.connector_typ in ('parquet', 'sql') and node.filters:
        for qpfvj__cldt in node.filters:
            for iebbu__kmm in range(len(qpfvj__cldt)):
                val = qpfvj__cldt[iebbu__kmm]
                qpfvj__cldt[iebbu__kmm] = val[0], val[1], visit_vars_inner(val
                    [2], callback, cbdata)


def connector_usedefs(node, use_set=None, def_set=None):
    if use_set is None:
        use_set = set()
    if def_set is None:
        def_set = set()
    def_set.update({dyl__xavk.name for dyl__xavk in node.out_vars})
    if node.connector_typ in ('csv', 'parquet', 'json'):
        use_set.add(node.file_name.name)
    if node.connector_typ == 'csv':
        if isinstance(node.nrows, numba.core.ir.Var):
            use_set.add(node.nrows.name)
        if isinstance(node.skiprows, numba.core.ir.Var):
            use_set.add(node.skiprows.name)
    if node.connector_typ in ('parquet', 'sql') and node.filters:
        for mmac__ugyry in node.filters:
            for dyl__xavk in mmac__ugyry:
                if isinstance(dyl__xavk[2], ir.Var):
                    use_set.add(dyl__xavk[2].name)
    return numba.core.analysis._use_defs_result(usemap=use_set, defmap=def_set)


def get_copies_connector(node, typemap):
    fqtax__ixh = set(dyl__xavk.name for dyl__xavk in node.out_vars)
    return set(), fqtax__ixh


def apply_copies_connector(node, var_dict, name_var_table, typemap,
    calltypes, save_copies):
    ynowa__coqq = []
    for xmbxu__wwh in node.out_vars:
        laq__wazij = replace_vars_inner(xmbxu__wwh, var_dict)
        ynowa__coqq.append(laq__wazij)
    node.out_vars = ynowa__coqq
    if node.connector_typ in ('csv', 'parquet', 'json'):
        node.file_name = replace_vars_inner(node.file_name, var_dict)
    if node.connector_typ in ('parquet', 'sql') and node.filters:
        for qpfvj__cldt in node.filters:
            for iebbu__kmm in range(len(qpfvj__cldt)):
                val = qpfvj__cldt[iebbu__kmm]
                qpfvj__cldt[iebbu__kmm] = val[0], val[1], replace_vars_inner(
                    val[2], var_dict)
    if node.connector_typ == 'csv':
        node.nrows = replace_vars_inner(node.nrows, var_dict)
        node.skiprows = replace_vars_inner(node.skiprows, var_dict)


def build_connector_definitions(node, definitions=None):
    if definitions is None:
        definitions = defaultdict(list)
    for xmbxu__wwh in node.out_vars:
        uczxb__omk = definitions[xmbxu__wwh.name]
        if node not in uczxb__omk:
            uczxb__omk.append(node)
    return definitions


def generate_filter_map(filters):
    if filters:
        bdeg__nag = []
        ihaj__ryj = [dyl__xavk[2] for mmac__ugyry in filters for dyl__xavk in
            mmac__ugyry]
        ygc__lnyzs = set()
        for uudcm__sma in ihaj__ryj:
            if isinstance(uudcm__sma, ir.Var):
                if uudcm__sma.name not in ygc__lnyzs:
                    bdeg__nag.append(uudcm__sma)
                ygc__lnyzs.add(uudcm__sma.name)
        return {dyl__xavk.name: f'f{iebbu__kmm}' for iebbu__kmm, dyl__xavk in
            enumerate(bdeg__nag)}, bdeg__nag
    else:
        return {}, []


class StreamReaderType(types.Opaque):

    def __init__(self):
        super(StreamReaderType, self).__init__(name='StreamReaderType')


stream_reader_type = StreamReaderType()
register_model(StreamReaderType)(models.OpaqueModel)


@box(StreamReaderType)
def box_stream_reader(typ, val, c):
    c.pyapi.incref(val)
    return val


def trim_extra_used_columns(used_columns, num_columns):
    hgv__gfwdb = len(used_columns)
    for iebbu__kmm in range(len(used_columns) - 1, -1, -1):
        if used_columns[iebbu__kmm] < num_columns:
            break
        hgv__gfwdb = iebbu__kmm
    return used_columns[:hgv__gfwdb]
