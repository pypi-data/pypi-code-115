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
    uxjxh__mwdja = []
    assert len(node.out_vars) > 0, 'empty {} in array analysis'.format(node
        .connector_typ)
    if node.connector_typ == 'csv' and node.chunksize is not None:
        return [], []
    yowk__iss = []
    for ggixv__xnon in node.out_vars:
        typ = typemap[ggixv__xnon.name]
        if typ == types.none:
            continue
        cvr__rfjk = array_analysis._gen_shape_call(equiv_set, ggixv__xnon,
            typ.ndim, None, uxjxh__mwdja)
        equiv_set.insert_equiv(ggixv__xnon, cvr__rfjk)
        yowk__iss.append(cvr__rfjk[0])
        equiv_set.define(ggixv__xnon, set())
    if len(yowk__iss) > 1:
        equiv_set.insert_equiv(*yowk__iss)
    return [], uxjxh__mwdja


def connector_distributed_analysis(node, array_dists):
    from bodo.ir.sql_ext import SqlReader
    if isinstance(node, SqlReader) and not node.is_select_query:
        wba__comtl = Distribution.REP
    elif isinstance(node, SqlReader) and node.limit is not None:
        wba__comtl = Distribution.OneD_Var
    else:
        wba__comtl = Distribution.OneD
    for oml__qfhpe in node.out_vars:
        if oml__qfhpe.name in array_dists:
            wba__comtl = Distribution(min(wba__comtl.value, array_dists[
                oml__qfhpe.name].value))
    for oml__qfhpe in node.out_vars:
        array_dists[oml__qfhpe.name] = wba__comtl


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
    for ggixv__xnon, typ in zip(node.out_vars, node.out_types):
        typeinferer.lock_type(ggixv__xnon.name, typ, loc=node.loc)


def visit_vars_connector(node, callback, cbdata):
    if debug_prints():
        print('visiting {} vars for:'.format(node.connector_typ), node)
        print('cbdata: ', sorted(cbdata.items()))
    ivu__snxrj = []
    for ggixv__xnon in node.out_vars:
        fgpsl__azob = visit_vars_inner(ggixv__xnon, callback, cbdata)
        ivu__snxrj.append(fgpsl__azob)
    node.out_vars = ivu__snxrj
    if node.connector_typ in ('csv', 'parquet', 'json'):
        node.file_name = visit_vars_inner(node.file_name, callback, cbdata)
    if node.connector_typ == 'csv':
        node.nrows = visit_vars_inner(node.nrows, callback, cbdata)
        node.skiprows = visit_vars_inner(node.skiprows, callback, cbdata)
    if node.connector_typ in ('parquet', 'sql') and node.filters:
        for qka__bhgh in node.filters:
            for gsqh__ken in range(len(qka__bhgh)):
                val = qka__bhgh[gsqh__ken]
                qka__bhgh[gsqh__ken] = val[0], val[1], visit_vars_inner(val
                    [2], callback, cbdata)


def connector_usedefs(node, use_set=None, def_set=None):
    if use_set is None:
        use_set = set()
    if def_set is None:
        def_set = set()
    def_set.update({oml__qfhpe.name for oml__qfhpe in node.out_vars})
    if node.connector_typ in ('csv', 'parquet', 'json'):
        use_set.add(node.file_name.name)
    if node.connector_typ == 'csv':
        if isinstance(node.nrows, numba.core.ir.Var):
            use_set.add(node.nrows.name)
        if isinstance(node.skiprows, numba.core.ir.Var):
            use_set.add(node.skiprows.name)
    if node.connector_typ in ('parquet', 'sql') and node.filters:
        for kehs__gii in node.filters:
            for oml__qfhpe in kehs__gii:
                if isinstance(oml__qfhpe[2], ir.Var):
                    use_set.add(oml__qfhpe[2].name)
    return numba.core.analysis._use_defs_result(usemap=use_set, defmap=def_set)


def get_copies_connector(node, typemap):
    ykkp__ihqs = set(oml__qfhpe.name for oml__qfhpe in node.out_vars)
    return set(), ykkp__ihqs


def apply_copies_connector(node, var_dict, name_var_table, typemap,
    calltypes, save_copies):
    ivu__snxrj = []
    for ggixv__xnon in node.out_vars:
        fgpsl__azob = replace_vars_inner(ggixv__xnon, var_dict)
        ivu__snxrj.append(fgpsl__azob)
    node.out_vars = ivu__snxrj
    if node.connector_typ in ('csv', 'parquet', 'json'):
        node.file_name = replace_vars_inner(node.file_name, var_dict)
    if node.connector_typ in ('parquet', 'sql') and node.filters:
        for qka__bhgh in node.filters:
            for gsqh__ken in range(len(qka__bhgh)):
                val = qka__bhgh[gsqh__ken]
                qka__bhgh[gsqh__ken] = val[0], val[1], replace_vars_inner(val
                    [2], var_dict)
    if node.connector_typ == 'csv':
        node.nrows = replace_vars_inner(node.nrows, var_dict)
        node.skiprows = replace_vars_inner(node.skiprows, var_dict)


def build_connector_definitions(node, definitions=None):
    if definitions is None:
        definitions = defaultdict(list)
    for ggixv__xnon in node.out_vars:
        msgy__stxm = definitions[ggixv__xnon.name]
        if node not in msgy__stxm:
            msgy__stxm.append(node)
    return definitions


def generate_filter_map(filters):
    if filters:
        caa__qdauh = []
        pnh__xhoib = [oml__qfhpe[2] for kehs__gii in filters for oml__qfhpe in
            kehs__gii]
        xgsir__ohtg = set()
        for guj__dzjt in pnh__xhoib:
            if isinstance(guj__dzjt, ir.Var):
                if guj__dzjt.name not in xgsir__ohtg:
                    caa__qdauh.append(guj__dzjt)
                xgsir__ohtg.add(guj__dzjt.name)
        return {oml__qfhpe.name: f'f{gsqh__ken}' for gsqh__ken, oml__qfhpe in
            enumerate(caa__qdauh)}, caa__qdauh
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
    dne__lblbe = len(used_columns)
    for gsqh__ken in range(len(used_columns) - 1, -1, -1):
        if used_columns[gsqh__ken] < num_columns:
            break
        dne__lblbe = gsqh__ken
    return used_columns[:dne__lblbe]
