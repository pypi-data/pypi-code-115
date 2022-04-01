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
    tis__chwp = []
    assert len(node.out_vars) > 0, 'empty {} in array analysis'.format(node
        .connector_typ)
    if node.connector_typ == 'csv' and node.chunksize is not None:
        return [], []
    vzdr__gaf = []
    for jeyww__yta in node.out_vars:
        typ = typemap[jeyww__yta.name]
        if typ == types.none:
            continue
        qxmwy__gvfl = array_analysis._gen_shape_call(equiv_set, jeyww__yta,
            typ.ndim, None, tis__chwp)
        equiv_set.insert_equiv(jeyww__yta, qxmwy__gvfl)
        vzdr__gaf.append(qxmwy__gvfl[0])
        equiv_set.define(jeyww__yta, set())
    if len(vzdr__gaf) > 1:
        equiv_set.insert_equiv(*vzdr__gaf)
    return [], tis__chwp


def connector_distributed_analysis(node, array_dists):
    from bodo.ir.sql_ext import SqlReader
    if isinstance(node, SqlReader) and not node.is_select_query:
        qhpab__kyzz = Distribution.REP
    elif isinstance(node, SqlReader) and node.limit is not None:
        qhpab__kyzz = Distribution.OneD_Var
    else:
        qhpab__kyzz = Distribution.OneD
    for qppzx__knwux in node.out_vars:
        if qppzx__knwux.name in array_dists:
            qhpab__kyzz = Distribution(min(qhpab__kyzz.value, array_dists[
                qppzx__knwux.name].value))
    for qppzx__knwux in node.out_vars:
        array_dists[qppzx__knwux.name] = qhpab__kyzz


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
    for jeyww__yta, typ in zip(node.out_vars, node.out_types):
        typeinferer.lock_type(jeyww__yta.name, typ, loc=node.loc)


def visit_vars_connector(node, callback, cbdata):
    if debug_prints():
        print('visiting {} vars for:'.format(node.connector_typ), node)
        print('cbdata: ', sorted(cbdata.items()))
    bckow__crhxf = []
    for jeyww__yta in node.out_vars:
        cejoa__exp = visit_vars_inner(jeyww__yta, callback, cbdata)
        bckow__crhxf.append(cejoa__exp)
    node.out_vars = bckow__crhxf
    if node.connector_typ in ('csv', 'parquet', 'json'):
        node.file_name = visit_vars_inner(node.file_name, callback, cbdata)
    if node.connector_typ == 'csv':
        node.nrows = visit_vars_inner(node.nrows, callback, cbdata)
        node.skiprows = visit_vars_inner(node.skiprows, callback, cbdata)
    if node.connector_typ in ('parquet', 'sql') and node.filters:
        for tvcn__xdkej in node.filters:
            for acg__kql in range(len(tvcn__xdkej)):
                val = tvcn__xdkej[acg__kql]
                tvcn__xdkej[acg__kql] = val[0], val[1], visit_vars_inner(val
                    [2], callback, cbdata)


def connector_usedefs(node, use_set=None, def_set=None):
    if use_set is None:
        use_set = set()
    if def_set is None:
        def_set = set()
    def_set.update({qppzx__knwux.name for qppzx__knwux in node.out_vars})
    if node.connector_typ in ('csv', 'parquet', 'json'):
        use_set.add(node.file_name.name)
    if node.connector_typ == 'csv':
        if isinstance(node.nrows, numba.core.ir.Var):
            use_set.add(node.nrows.name)
        if isinstance(node.skiprows, numba.core.ir.Var):
            use_set.add(node.skiprows.name)
    if node.connector_typ in ('parquet', 'sql') and node.filters:
        for nswr__bsrsk in node.filters:
            for qppzx__knwux in nswr__bsrsk:
                if isinstance(qppzx__knwux[2], ir.Var):
                    use_set.add(qppzx__knwux[2].name)
    return numba.core.analysis._use_defs_result(usemap=use_set, defmap=def_set)


def get_copies_connector(node, typemap):
    blhy__kmwcn = set(qppzx__knwux.name for qppzx__knwux in node.out_vars)
    return set(), blhy__kmwcn


def apply_copies_connector(node, var_dict, name_var_table, typemap,
    calltypes, save_copies):
    bckow__crhxf = []
    for jeyww__yta in node.out_vars:
        cejoa__exp = replace_vars_inner(jeyww__yta, var_dict)
        bckow__crhxf.append(cejoa__exp)
    node.out_vars = bckow__crhxf
    if node.connector_typ in ('csv', 'parquet', 'json'):
        node.file_name = replace_vars_inner(node.file_name, var_dict)
    if node.connector_typ in ('parquet', 'sql') and node.filters:
        for tvcn__xdkej in node.filters:
            for acg__kql in range(len(tvcn__xdkej)):
                val = tvcn__xdkej[acg__kql]
                tvcn__xdkej[acg__kql] = val[0], val[1], replace_vars_inner(val
                    [2], var_dict)
    if node.connector_typ == 'csv':
        node.nrows = replace_vars_inner(node.nrows, var_dict)
        node.skiprows = replace_vars_inner(node.skiprows, var_dict)


def build_connector_definitions(node, definitions=None):
    if definitions is None:
        definitions = defaultdict(list)
    for jeyww__yta in node.out_vars:
        nqcv__mahz = definitions[jeyww__yta.name]
        if node not in nqcv__mahz:
            nqcv__mahz.append(node)
    return definitions


def generate_filter_map(filters):
    if filters:
        vpkv__ihde = []
        mbf__sjack = [qppzx__knwux[2] for nswr__bsrsk in filters for
            qppzx__knwux in nswr__bsrsk]
        yaopn__uitl = set()
        for gnzxx__glpqs in mbf__sjack:
            if isinstance(gnzxx__glpqs, ir.Var):
                if gnzxx__glpqs.name not in yaopn__uitl:
                    vpkv__ihde.append(gnzxx__glpqs)
                yaopn__uitl.add(gnzxx__glpqs.name)
        return {qppzx__knwux.name: f'f{acg__kql}' for acg__kql,
            qppzx__knwux in enumerate(vpkv__ihde)}, vpkv__ihde
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
    hefn__ednmr = len(used_columns)
    for acg__kql in range(len(used_columns) - 1, -1, -1):
        if used_columns[acg__kql] < num_columns:
            break
        hefn__ednmr = acg__kql
    return used_columns[:hefn__ednmr]
