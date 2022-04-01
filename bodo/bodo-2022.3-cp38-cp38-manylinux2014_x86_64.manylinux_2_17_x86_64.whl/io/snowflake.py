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
    nly__hhu = urlparse(conn_str)
    iqmxz__qoh = {}
    if nly__hhu.username:
        iqmxz__qoh['user'] = nly__hhu.username
    if nly__hhu.password:
        iqmxz__qoh['password'] = nly__hhu.password
    if nly__hhu.hostname:
        iqmxz__qoh['account'] = nly__hhu.hostname
    if nly__hhu.port:
        iqmxz__qoh['port'] = nly__hhu.port
    if nly__hhu.path:
        wah__qyhj = nly__hhu.path
        if wah__qyhj.startswith('/'):
            wah__qyhj = wah__qyhj[1:]
        ryr__ggdp, schema = wah__qyhj.split('/')
        iqmxz__qoh['database'] = ryr__ggdp
        if schema:
            iqmxz__qoh['schema'] = schema
    if nly__hhu.query:
        for stsmb__wgfsn, gtcer__sbn in parse_qsl(nly__hhu.query):
            iqmxz__qoh[stsmb__wgfsn] = gtcer__sbn
            if stsmb__wgfsn == 'session_parameters':
                iqmxz__qoh[stsmb__wgfsn] = json.loads(gtcer__sbn)
    iqmxz__qoh['application'] = 'bodo'
    return iqmxz__qoh


class SnowflakeDataset(object):

    def __init__(self, batches, schema, conn):
        self.pieces = batches
        self._bodo_total_rows = 0
        for dbg__wvf in batches:
            dbg__wvf._bodo_num_rows = dbg__wvf.rowcount
            self._bodo_total_rows += dbg__wvf._bodo_num_rows
        self.schema = schema
        self.conn = conn


def get_dataset(query, conn_str):
    smyk__vlj = tracing.Event('get_snowflake_dataset')
    from mpi4py import MPI
    xmu__uuvld = MPI.COMM_WORLD
    obbr__yrpih = tracing.Event('snowflake_connect', is_parallel=False)
    mhmr__cpxa = get_connection_params(conn_str)
    conn = snowflake.connector.connect(**mhmr__cpxa)
    obbr__yrpih.finalize()
    if bodo.get_rank() == 0:
        pvxq__sxhl = conn.cursor()
        hdkkg__vszel = tracing.Event('get_schema', is_parallel=False)
        lgmw__kuyp = f'select * from ({query}) x LIMIT {100}'
        merg__begr = pvxq__sxhl.execute(lgmw__kuyp).fetch_arrow_all()
        if merg__begr is None:
            eomhz__ijcso = pvxq__sxhl.describe(query)
            agcm__idw = [pa.field(maq__hyi.name, FIELD_TYPE_TO_PA_TYPE[
                maq__hyi.type_code]) for maq__hyi in eomhz__ijcso]
            schema = pa.schema(agcm__idw)
        else:
            schema = merg__begr.schema
        hdkkg__vszel.finalize()
        alpg__bary = tracing.Event('execute_query', is_parallel=False)
        pvxq__sxhl.execute(query)
        alpg__bary.finalize()
        batches = pvxq__sxhl.get_result_batches()
        xmu__uuvld.bcast((batches, schema))
    else:
        batches, schema = xmu__uuvld.bcast(None)
    zglxc__lmzrx = SnowflakeDataset(batches, schema, conn)
    smyk__vlj.finalize()
    return zglxc__lmzrx
