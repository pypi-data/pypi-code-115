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
    liiz__cyi = []
    assert len(node.out_vars) > 0, 'empty {} in array analysis'.format(node
        .connector_typ)
    if node.connector_typ == 'csv' and node.chunksize is not None:
        return [], []
    oyaq__etzki = []
    for nhze__ucq in node.out_vars:
        typ = typemap[nhze__ucq.name]
        if typ == types.none:
            continue
        cnel__vqdv = array_analysis._gen_shape_call(equiv_set, nhze__ucq,
            typ.ndim, None, liiz__cyi)
        equiv_set.insert_equiv(nhze__ucq, cnel__vqdv)
        oyaq__etzki.append(cnel__vqdv[0])
        equiv_set.define(nhze__ucq, set())
    if len(oyaq__etzki) > 1:
        equiv_set.insert_equiv(*oyaq__etzki)
    return [], liiz__cyi


def connector_distributed_analysis(node, array_dists):
    from bodo.ir.sql_ext import SqlReader
    if isinstance(node, SqlReader) and not node.is_select_query:
        veb__tpz = Distribution.REP
    elif isinstance(node, SqlReader) and node.limit is not None:
        veb__tpz = Distribution.OneD_Var
    else:
        veb__tpz = Distribution.OneD
    for vwi__nsg in node.out_vars:
        if vwi__nsg.name in array_dists:
            veb__tpz = Distribution(min(veb__tpz.value, array_dists[
                vwi__nsg.name].value))
    for vwi__nsg in node.out_vars:
        array_dists[vwi__nsg.name] = veb__tpz


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
    for nhze__ucq, typ in zip(node.out_vars, node.out_types):
        typeinferer.lock_type(nhze__ucq.name, typ, loc=node.loc)


def visit_vars_connector(node, callback, cbdata):
    if debug_prints():
        print('visiting {} vars for:'.format(node.connector_typ), node)
        print('cbdata: ', sorted(cbdata.items()))
    cvsgc__elizb = []
    for nhze__ucq in node.out_vars:
        udg__jvtvp = visit_vars_inner(nhze__ucq, callback, cbdata)
        cvsgc__elizb.append(udg__jvtvp)
    node.out_vars = cvsgc__elizb
    if node.connector_typ in ('csv', 'parquet', 'json'):
        node.file_name = visit_vars_inner(node.file_name, callback, cbdata)
    if node.connector_typ == 'csv':
        node.nrows = visit_vars_inner(node.nrows, callback, cbdata)
        node.skiprows = visit_vars_inner(node.skiprows, callback, cbdata)
    if node.connector_typ in ('parquet', 'sql') and node.filters:
        for jpth__fsf in node.filters:
            for iyll__yrufj in range(len(jpth__fsf)):
                val = jpth__fsf[iyll__yrufj]
                jpth__fsf[iyll__yrufj] = val[0], val[1], visit_vars_inner(val
                    [2], callback, cbdata)


def connector_usedefs(node, use_set=None, def_set=None):
    if use_set is None:
        use_set = set()
    if def_set is None:
        def_set = set()
    def_set.update({vwi__nsg.name for vwi__nsg in node.out_vars})
    if node.connector_typ in ('csv', 'parquet', 'json'):
        use_set.add(node.file_name.name)
    if node.connector_typ == 'csv':
        if isinstance(node.nrows, numba.core.ir.Var):
            use_set.add(node.nrows.name)
        if isinstance(node.skiprows, numba.core.ir.Var):
            use_set.add(node.skiprows.name)
    if node.connector_typ in ('parquet', 'sql') and node.filters:
        for rlees__dxcee in node.filters:
            for vwi__nsg in rlees__dxcee:
                if isinstance(vwi__nsg[2], ir.Var):
                    use_set.add(vwi__nsg[2].name)
    return numba.core.analysis._use_defs_result(usemap=use_set, defmap=def_set)


def get_copies_connector(node, typemap):
    acd__bpkw = set(vwi__nsg.name for vwi__nsg in node.out_vars)
    return set(), acd__bpkw


def apply_copies_connector(node, var_dict, name_var_table, typemap,
    calltypes, save_copies):
    cvsgc__elizb = []
    for nhze__ucq in node.out_vars:
        udg__jvtvp = replace_vars_inner(nhze__ucq, var_dict)
        cvsgc__elizb.append(udg__jvtvp)
    node.out_vars = cvsgc__elizb
    if node.connector_typ in ('csv', 'parquet', 'json'):
        node.file_name = replace_vars_inner(node.file_name, var_dict)
    if node.connector_typ in ('parquet', 'sql') and node.filters:
        for jpth__fsf in node.filters:
            for iyll__yrufj in range(len(jpth__fsf)):
                val = jpth__fsf[iyll__yrufj]
                jpth__fsf[iyll__yrufj] = val[0], val[1], replace_vars_inner(val
                    [2], var_dict)
    if node.connector_typ == 'csv':
        node.nrows = replace_vars_inner(node.nrows, var_dict)
        node.skiprows = replace_vars_inner(node.skiprows, var_dict)


def build_connector_definitions(node, definitions=None):
    if definitions is None:
        definitions = defaultdict(list)
    for nhze__ucq in node.out_vars:
        yhm__mqv = definitions[nhze__ucq.name]
        if node not in yhm__mqv:
            yhm__mqv.append(node)
    return definitions


def generate_filter_map(filters):
    if filters:
        ivhbx__acr = []
        qpo__wrxy = [vwi__nsg[2] for rlees__dxcee in filters for vwi__nsg in
            rlees__dxcee]
        noxr__odc = set()
        for gfz__chx in qpo__wrxy:
            if isinstance(gfz__chx, ir.Var):
                if gfz__chx.name not in noxr__odc:
                    ivhbx__acr.append(gfz__chx)
                noxr__odc.add(gfz__chx.name)
        return {vwi__nsg.name: f'f{iyll__yrufj}' for iyll__yrufj, vwi__nsg in
            enumerate(ivhbx__acr)}, ivhbx__acr
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
    xhh__ubic = len(used_columns)
    for iyll__yrufj in range(len(used_columns) - 1, -1, -1):
        if used_columns[iyll__yrufj] < num_columns:
            break
        xhh__ubic = iyll__yrufj
    return used_columns[:xhh__ubic]
