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
    ped__cfk = []
    assert len(node.out_vars) > 0, 'empty {} in array analysis'.format(node
        .connector_typ)
    if node.connector_typ == 'csv' and node.chunksize is not None:
        return [], []
    egu__izoa = []
    for llupi__fqb in node.out_vars:
        typ = typemap[llupi__fqb.name]
        if typ == types.none:
            continue
        xwnlh__gae = array_analysis._gen_shape_call(equiv_set, llupi__fqb,
            typ.ndim, None, ped__cfk)
        equiv_set.insert_equiv(llupi__fqb, xwnlh__gae)
        egu__izoa.append(xwnlh__gae[0])
        equiv_set.define(llupi__fqb, set())
    if len(egu__izoa) > 1:
        equiv_set.insert_equiv(*egu__izoa)
    return [], ped__cfk


def connector_distributed_analysis(node, array_dists):
    from bodo.ir.sql_ext import SqlReader
    if isinstance(node, SqlReader) and not node.is_select_query:
        mcxtf__gdrx = Distribution.REP
    elif isinstance(node, SqlReader) and node.limit is not None:
        mcxtf__gdrx = Distribution.OneD_Var
    else:
        mcxtf__gdrx = Distribution.OneD
    for thjf__qbdbp in node.out_vars:
        if thjf__qbdbp.name in array_dists:
            mcxtf__gdrx = Distribution(min(mcxtf__gdrx.value, array_dists[
                thjf__qbdbp.name].value))
    for thjf__qbdbp in node.out_vars:
        array_dists[thjf__qbdbp.name] = mcxtf__gdrx


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
    for llupi__fqb, typ in zip(node.out_vars, node.out_types):
        typeinferer.lock_type(llupi__fqb.name, typ, loc=node.loc)


def visit_vars_connector(node, callback, cbdata):
    if debug_prints():
        print('visiting {} vars for:'.format(node.connector_typ), node)
        print('cbdata: ', sorted(cbdata.items()))
    orpd__rakk = []
    for llupi__fqb in node.out_vars:
        efhn__qpp = visit_vars_inner(llupi__fqb, callback, cbdata)
        orpd__rakk.append(efhn__qpp)
    node.out_vars = orpd__rakk
    if node.connector_typ in ('csv', 'parquet', 'json'):
        node.file_name = visit_vars_inner(node.file_name, callback, cbdata)
    if node.connector_typ == 'csv':
        node.nrows = visit_vars_inner(node.nrows, callback, cbdata)
        node.skiprows = visit_vars_inner(node.skiprows, callback, cbdata)
    if node.connector_typ in ('parquet', 'sql') and node.filters:
        for nvmu__wczd in node.filters:
            for eakdd__qbtz in range(len(nvmu__wczd)):
                val = nvmu__wczd[eakdd__qbtz]
                nvmu__wczd[eakdd__qbtz] = val[0], val[1], visit_vars_inner(val
                    [2], callback, cbdata)


def connector_usedefs(node, use_set=None, def_set=None):
    if use_set is None:
        use_set = set()
    if def_set is None:
        def_set = set()
    def_set.update({thjf__qbdbp.name for thjf__qbdbp in node.out_vars})
    if node.connector_typ in ('csv', 'parquet', 'json'):
        use_set.add(node.file_name.name)
    if node.connector_typ == 'csv':
        if isinstance(node.nrows, numba.core.ir.Var):
            use_set.add(node.nrows.name)
        if isinstance(node.skiprows, numba.core.ir.Var):
            use_set.add(node.skiprows.name)
    if node.connector_typ in ('parquet', 'sql') and node.filters:
        for uwk__tkg in node.filters:
            for thjf__qbdbp in uwk__tkg:
                if isinstance(thjf__qbdbp[2], ir.Var):
                    use_set.add(thjf__qbdbp[2].name)
    return numba.core.analysis._use_defs_result(usemap=use_set, defmap=def_set)


def get_copies_connector(node, typemap):
    rvbd__kowhm = set(thjf__qbdbp.name for thjf__qbdbp in node.out_vars)
    return set(), rvbd__kowhm


def apply_copies_connector(node, var_dict, name_var_table, typemap,
    calltypes, save_copies):
    orpd__rakk = []
    for llupi__fqb in node.out_vars:
        efhn__qpp = replace_vars_inner(llupi__fqb, var_dict)
        orpd__rakk.append(efhn__qpp)
    node.out_vars = orpd__rakk
    if node.connector_typ in ('csv', 'parquet', 'json'):
        node.file_name = replace_vars_inner(node.file_name, var_dict)
    if node.connector_typ in ('parquet', 'sql') and node.filters:
        for nvmu__wczd in node.filters:
            for eakdd__qbtz in range(len(nvmu__wczd)):
                val = nvmu__wczd[eakdd__qbtz]
                nvmu__wczd[eakdd__qbtz] = val[0], val[1], replace_vars_inner(
                    val[2], var_dict)
    if node.connector_typ == 'csv':
        node.nrows = replace_vars_inner(node.nrows, var_dict)
        node.skiprows = replace_vars_inner(node.skiprows, var_dict)


def build_connector_definitions(node, definitions=None):
    if definitions is None:
        definitions = defaultdict(list)
    for llupi__fqb in node.out_vars:
        jdcw__bqc = definitions[llupi__fqb.name]
        if node not in jdcw__bqc:
            jdcw__bqc.append(node)
    return definitions


def generate_filter_map(filters):
    if filters:
        zsj__eqbtc = []
        nfgfj__mwk = [thjf__qbdbp[2] for uwk__tkg in filters for
            thjf__qbdbp in uwk__tkg]
        yzq__tkrqm = set()
        for drz__wsr in nfgfj__mwk:
            if isinstance(drz__wsr, ir.Var):
                if drz__wsr.name not in yzq__tkrqm:
                    zsj__eqbtc.append(drz__wsr)
                yzq__tkrqm.add(drz__wsr.name)
        return {thjf__qbdbp.name: f'f{eakdd__qbtz}' for eakdd__qbtz,
            thjf__qbdbp in enumerate(zsj__eqbtc)}, zsj__eqbtc
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
    irzn__dhusf = len(used_columns)
    for eakdd__qbtz in range(len(used_columns) - 1, -1, -1):
        if used_columns[eakdd__qbtz] < num_columns:
            break
        irzn__dhusf = eakdd__qbtz
    return used_columns[:irzn__dhusf]
