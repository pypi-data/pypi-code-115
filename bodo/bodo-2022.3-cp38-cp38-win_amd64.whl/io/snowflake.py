from urllib.parse import parse_qsl, urlparse
import pyarrow as pa
import snowflake.connector
import bodo
from bodo.utils import tracing
FIELD_TYPE_TO_PA_TYPE = [pa.int64(), pa.float64(), pa.string(), pa.date32(),
    pa.timestamp('ns'), pa.string(), pa.timestamp('ns'), pa.timestamp('ns'),
    pa.timestamp('ns'), pa.string(), pa.string(), pa.binary(), pa.time64(
    'ns'), pa.bool_()]


def get_connection_params(conn_str):
    import json
    ibfir__ukmq = urlparse(conn_str)
    tyu__fpjy = {}
    if ibfir__ukmq.username:
        tyu__fpjy['user'] = ibfir__ukmq.username
    if ibfir__ukmq.password:
        tyu__fpjy['password'] = ibfir__ukmq.password
    if ibfir__ukmq.hostname:
        tyu__fpjy['account'] = ibfir__ukmq.hostname
    if ibfir__ukmq.port:
        tyu__fpjy['port'] = ibfir__ukmq.port
    if ibfir__ukmq.path:
        adiwx__uifax = ibfir__ukmq.path
        if adiwx__uifax.startswith('/'):
            adiwx__uifax = adiwx__uifax[1:]
        sir__trt, schema = adiwx__uifax.split('/')
        tyu__fpjy['database'] = sir__trt
        if schema:
            tyu__fpjy['schema'] = schema
    if ibfir__ukmq.query:
        for ocf__bqey, fctyd__upnov in parse_qsl(ibfir__ukmq.query):
            tyu__fpjy[ocf__bqey] = fctyd__upnov
            if ocf__bqey == 'session_parameters':
                tyu__fpjy[ocf__bqey] = json.loads(fctyd__upnov)
    tyu__fpjy['application'] = 'bodo'
    return tyu__fpjy


class SnowflakeDataset(object):

    def __init__(self, batches, schema, conn):
        self.pieces = batches
        self._bodo_total_rows = 0
        for xctg__pdhpf in batches:
            xctg__pdhpf._bodo_num_rows = xctg__pdhpf.rowcount
            self._bodo_total_rows += xctg__pdhpf._bodo_num_rows
        self.schema = schema
        self.conn = conn


def get_dataset(query, conn_str):
    ciwlr__snahs = tracing.Event('get_snowflake_dataset')
    from mpi4py import MPI
    mqlx__gwscw = MPI.COMM_WORLD
    ivv__maufd = tracing.Event('snowflake_connect', is_parallel=False)
    rut__lrjel = get_connection_params(conn_str)
    conn = snowflake.connector.connect(**rut__lrjel)
    ivv__maufd.finalize()
    if bodo.get_rank() == 0:
        lbuam__bxblf = conn.cursor()
        xdq__uajsb = tracing.Event('get_schema', is_parallel=False)
        vtxk__lnmk = f'select * from ({query}) x LIMIT {100}'
        wsfy__xsu = lbuam__bxblf.execute(vtxk__lnmk).fetch_arrow_all()
        if wsfy__xsu is None:
            ehnqt__bup = lbuam__bxblf.describe(query)
            tpx__vyodm = [pa.field(gws__ntsod.name, FIELD_TYPE_TO_PA_TYPE[
                gws__ntsod.type_code]) for gws__ntsod in ehnqt__bup]
            schema = pa.schema(tpx__vyodm)
        else:
            schema = wsfy__xsu.schema
        xdq__uajsb.finalize()
        pdvj__uibmy = tracing.Event('execute_query', is_parallel=False)
        lbuam__bxblf.execute(query)
        pdvj__uibmy.finalize()
        batches = lbuam__bxblf.get_result_batches()
        mqlx__gwscw.bcast((batches, schema))
    else:
        batches, schema = mqlx__gwscw.bcast(None)
    fxsnn__kjvva = SnowflakeDataset(batches, schema, conn)
    ciwlr__snahs.finalize()
    return fxsnn__kjvva
