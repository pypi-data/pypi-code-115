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
    mcz__qejk = urlparse(conn_str)
    bfylz__twci = {}
    if mcz__qejk.username:
        bfylz__twci['user'] = mcz__qejk.username
    if mcz__qejk.password:
        bfylz__twci['password'] = mcz__qejk.password
    if mcz__qejk.hostname:
        bfylz__twci['account'] = mcz__qejk.hostname
    if mcz__qejk.port:
        bfylz__twci['port'] = mcz__qejk.port
    if mcz__qejk.path:
        bmzzi__fnbf = mcz__qejk.path
        if bmzzi__fnbf.startswith('/'):
            bmzzi__fnbf = bmzzi__fnbf[1:]
        zwuq__nghgw, schema = bmzzi__fnbf.split('/')
        bfylz__twci['database'] = zwuq__nghgw
        if schema:
            bfylz__twci['schema'] = schema
    if mcz__qejk.query:
        for bfxho__pqz, bybo__tzgu in parse_qsl(mcz__qejk.query):
            bfylz__twci[bfxho__pqz] = bybo__tzgu
            if bfxho__pqz == 'session_parameters':
                bfylz__twci[bfxho__pqz] = json.loads(bybo__tzgu)
    bfylz__twci['application'] = 'bodo'
    return bfylz__twci


class SnowflakeDataset(object):

    def __init__(self, batches, schema, conn):
        self.pieces = batches
        self._bodo_total_rows = 0
        for fhdq__tmm in batches:
            fhdq__tmm._bodo_num_rows = fhdq__tmm.rowcount
            self._bodo_total_rows += fhdq__tmm._bodo_num_rows
        self.schema = schema
        self.conn = conn


def get_dataset(query, conn_str):
    qtapl__ofy = tracing.Event('get_snowflake_dataset')
    from mpi4py import MPI
    ech__qqvdl = MPI.COMM_WORLD
    bekw__oom = tracing.Event('snowflake_connect', is_parallel=False)
    tondy__ekqze = get_connection_params(conn_str)
    conn = snowflake.connector.connect(**tondy__ekqze)
    bekw__oom.finalize()
    if bodo.get_rank() == 0:
        uam__zkmsm = conn.cursor()
        curh__dhtpc = tracing.Event('get_schema', is_parallel=False)
        syg__lym = f'select * from ({query}) x LIMIT {100}'
        yslae__nfijx = uam__zkmsm.execute(syg__lym).fetch_arrow_all()
        if yslae__nfijx is None:
            qjss__rshty = uam__zkmsm.describe(query)
            zaeps__xxz = [pa.field(clsqt__vjnj.name, FIELD_TYPE_TO_PA_TYPE[
                clsqt__vjnj.type_code]) for clsqt__vjnj in qjss__rshty]
            schema = pa.schema(zaeps__xxz)
        else:
            schema = yslae__nfijx.schema
        curh__dhtpc.finalize()
        qvlqs__cof = tracing.Event('execute_query', is_parallel=False)
        uam__zkmsm.execute(query)
        qvlqs__cof.finalize()
        batches = uam__zkmsm.get_result_batches()
        ech__qqvdl.bcast((batches, schema))
    else:
        batches, schema = ech__qqvdl.bcast(None)
    rvwrd__zbuxz = SnowflakeDataset(batches, schema, conn)
    qtapl__ofy.finalize()
    return rvwrd__zbuxz
