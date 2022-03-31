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
    egsb__ssyxo = []
    assert len(node.out_vars) > 0, 'empty {} in array analysis'.format(node
        .connector_typ)
    if node.connector_typ == 'csv' and node.chunksize is not None:
        return [], []
    smeac__zsr = []
    for iiaq__vqiv in node.out_vars:
        typ = typemap[iiaq__vqiv.name]
        if typ == types.none:
            continue
        tzdq__ztjsa = array_analysis._gen_shape_call(equiv_set, iiaq__vqiv,
            typ.ndim, None, egsb__ssyxo)
        equiv_set.insert_equiv(iiaq__vqiv, tzdq__ztjsa)
        smeac__zsr.append(tzdq__ztjsa[0])
        equiv_set.define(iiaq__vqiv, set())
    if len(smeac__zsr) > 1:
        equiv_set.insert_equiv(*smeac__zsr)
    return [], egsb__ssyxo


def connector_distributed_analysis(node, array_dists):
    from bodo.ir.sql_ext import SqlReader
    if isinstance(node, SqlReader) and not node.is_select_query:
        gomr__mmxof = Distribution.REP
    elif isinstance(node, SqlReader) and node.limit is not None:
        gomr__mmxof = Distribution.OneD_Var
    else:
        gomr__mmxof = Distribution.OneD
    for fjj__chv in node.out_vars:
        if fjj__chv.name in array_dists:
            gomr__mmxof = Distribution(min(gomr__mmxof.value, array_dists[
                fjj__chv.name].value))
    for fjj__chv in node.out_vars:
        array_dists[fjj__chv.name] = gomr__mmxof


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
    for iiaq__vqiv, typ in zip(node.out_vars, node.out_types):
        typeinferer.lock_type(iiaq__vqiv.name, typ, loc=node.loc)


def visit_vars_connector(node, callback, cbdata):
    if debug_prints():
        print('visiting {} vars for:'.format(node.connector_typ), node)
        print('cbdata: ', sorted(cbdata.items()))
    kcu__glelq = []
    for iiaq__vqiv in node.out_vars:
        nbu__fgnx = visit_vars_inner(iiaq__vqiv, callback, cbdata)
        kcu__glelq.append(nbu__fgnx)
    node.out_vars = kcu__glelq
    if node.connector_typ in ('csv', 'parquet', 'json'):
        node.file_name = visit_vars_inner(node.file_name, callback, cbdata)
    if node.connector_typ == 'csv':
        node.nrows = visit_vars_inner(node.nrows, callback, cbdata)
        node.skiprows = visit_vars_inner(node.skiprows, callback, cbdata)
    if node.connector_typ in ('parquet', 'sql') and node.filters:
        for lls__badqw in node.filters:
            for swga__cmx in range(len(lls__badqw)):
                val = lls__badqw[swga__cmx]
                lls__badqw[swga__cmx] = val[0], val[1], visit_vars_inner(val
                    [2], callback, cbdata)


def connector_usedefs(node, use_set=None, def_set=None):
    if use_set is None:
        use_set = set()
    if def_set is None:
        def_set = set()
    def_set.update({fjj__chv.name for fjj__chv in node.out_vars})
    if node.connector_typ in ('csv', 'parquet', 'json'):
        use_set.add(node.file_name.name)
    if node.connector_typ == 'csv':
        if isinstance(node.nrows, numba.core.ir.Var):
            use_set.add(node.nrows.name)
        if isinstance(node.skiprows, numba.core.ir.Var):
            use_set.add(node.skiprows.name)
    if node.connector_typ in ('parquet', 'sql') and node.filters:
        for bne__lco in node.filters:
            for fjj__chv in bne__lco:
                if isinstance(fjj__chv[2], ir.Var):
                    use_set.add(fjj__chv[2].name)
    return numba.core.analysis._use_defs_result(usemap=use_set, defmap=def_set)


def get_copies_connector(node, typemap):
    mflt__zjjej = set(fjj__chv.name for fjj__chv in node.out_vars)
    return set(), mflt__zjjej


def apply_copies_connector(node, var_dict, name_var_table, typemap,
    calltypes, save_copies):
    kcu__glelq = []
    for iiaq__vqiv in node.out_vars:
        nbu__fgnx = replace_vars_inner(iiaq__vqiv, var_dict)
        kcu__glelq.append(nbu__fgnx)
    node.out_vars = kcu__glelq
    if node.connector_typ in ('csv', 'parquet', 'json'):
        node.file_name = replace_vars_inner(node.file_name, var_dict)
    if node.connector_typ in ('parquet', 'sql') and node.filters:
        for lls__badqw in node.filters:
            for swga__cmx in range(len(lls__badqw)):
                val = lls__badqw[swga__cmx]
                lls__badqw[swga__cmx] = val[0], val[1], replace_vars_inner(val
                    [2], var_dict)
    if node.connector_typ == 'csv':
        node.nrows = replace_vars_inner(node.nrows, var_dict)
        node.skiprows = replace_vars_inner(node.skiprows, var_dict)


def build_connector_definitions(node, definitions=None):
    if definitions is None:
        definitions = defaultdict(list)
    for iiaq__vqiv in node.out_vars:
        gqyah__njv = definitions[iiaq__vqiv.name]
        if node not in gqyah__njv:
            gqyah__njv.append(node)
    return definitions


def generate_filter_map(filters):
    if filters:
        ptjl__jiiri = []
        ccwd__did = [fjj__chv[2] for bne__lco in filters for fjj__chv in
            bne__lco]
        mngh__abx = set()
        for euvfm__btq in ccwd__did:
            if isinstance(euvfm__btq, ir.Var):
                if euvfm__btq.name not in mngh__abx:
                    ptjl__jiiri.append(euvfm__btq)
                mngh__abx.add(euvfm__btq.name)
        return {fjj__chv.name: f'f{swga__cmx}' for swga__cmx, fjj__chv in
            enumerate(ptjl__jiiri)}, ptjl__jiiri
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
    edxtf__omb = len(used_columns)
    for swga__cmx in range(len(used_columns) - 1, -1, -1):
        if used_columns[swga__cmx] < num_columns:
            break
        edxtf__omb = swga__cmx
    return used_columns[:edxtf__omb]
