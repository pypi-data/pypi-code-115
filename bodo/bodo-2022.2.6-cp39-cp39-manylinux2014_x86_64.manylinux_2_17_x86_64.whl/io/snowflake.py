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
    hpys__pqk = urlparse(conn_str)
    qcvao__dzzpx = {}
    if hpys__pqk.username:
        qcvao__dzzpx['user'] = hpys__pqk.username
    if hpys__pqk.password:
        qcvao__dzzpx['password'] = hpys__pqk.password
    if hpys__pqk.hostname:
        qcvao__dzzpx['account'] = hpys__pqk.hostname
    if hpys__pqk.port:
        qcvao__dzzpx['port'] = hpys__pqk.port
    if hpys__pqk.path:
        apejr__qeln = hpys__pqk.path
        if apejr__qeln.startswith('/'):
            apejr__qeln = apejr__qeln[1:]
        uft__eyta, schema = apejr__qeln.split('/')
        qcvao__dzzpx['database'] = uft__eyta
        if schema:
            qcvao__dzzpx['schema'] = schema
    if hpys__pqk.query:
        for lcq__zaqll, jpqd__ymd in parse_qsl(hpys__pqk.query):
            qcvao__dzzpx[lcq__zaqll] = jpqd__ymd
            if lcq__zaqll == 'session_parameters':
                qcvao__dzzpx[lcq__zaqll] = json.loads(jpqd__ymd)
    qcvao__dzzpx['application'] = 'bodo'
    return qcvao__dzzpx


class SnowflakeDataset(object):

    def __init__(self, batches, schema, conn):
        self.pieces = batches
        self._bodo_total_rows = 0
        for fvx__yct in batches:
            fvx__yct._bodo_num_rows = fvx__yct.rowcount
            self._bodo_total_rows += fvx__yct._bodo_num_rows
        self.schema = schema
        self.conn = conn


def get_dataset(query, conn_str):
    hrlm__ocxvo = tracing.Event('get_snowflake_dataset')
    from mpi4py import MPI
    zqu__auoi = MPI.COMM_WORLD
    meuwz__mhjb = tracing.Event('snowflake_connect', is_parallel=False)
    rwiih__zkbsd = get_connection_params(conn_str)
    conn = snowflake.connector.connect(**rwiih__zkbsd)
    meuwz__mhjb.finalize()
    if bodo.get_rank() == 0:
        dbelt__frq = conn.cursor()
        erxlw__uzqye = tracing.Event('get_schema', is_parallel=False)
        dfhem__hjnmj = f'select * from ({query}) x LIMIT {100}'
        qvyg__pukc = dbelt__frq.execute(dfhem__hjnmj).fetch_arrow_all()
        if qvyg__pukc is None:
            vpo__uqe = dbelt__frq.describe(query)
            aoe__shr = [pa.field(wln__qytyx.name, FIELD_TYPE_TO_PA_TYPE[
                wln__qytyx.type_code]) for wln__qytyx in vpo__uqe]
            schema = pa.schema(aoe__shr)
        else:
            schema = qvyg__pukc.schema
        erxlw__uzqye.finalize()
        mwct__nimnj = tracing.Event('execute_query', is_parallel=False)
        dbelt__frq.execute(query)
        mwct__nimnj.finalize()
        batches = dbelt__frq.get_result_batches()
        zqu__auoi.bcast((batches, schema))
    else:
        batches, schema = zqu__auoi.bcast(None)
    xgiyt__rmt = SnowflakeDataset(batches, schema, conn)
    hrlm__ocxvo.finalize()
    return xgiyt__rmt
