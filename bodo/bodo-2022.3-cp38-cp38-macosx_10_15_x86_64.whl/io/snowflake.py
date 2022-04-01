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
    oakht__nvwgx = urlparse(conn_str)
    pxbd__wwhbi = {}
    if oakht__nvwgx.username:
        pxbd__wwhbi['user'] = oakht__nvwgx.username
    if oakht__nvwgx.password:
        pxbd__wwhbi['password'] = oakht__nvwgx.password
    if oakht__nvwgx.hostname:
        pxbd__wwhbi['account'] = oakht__nvwgx.hostname
    if oakht__nvwgx.port:
        pxbd__wwhbi['port'] = oakht__nvwgx.port
    if oakht__nvwgx.path:
        gtbup__ddmws = oakht__nvwgx.path
        if gtbup__ddmws.startswith('/'):
            gtbup__ddmws = gtbup__ddmws[1:]
        tpnw__wbcop, schema = gtbup__ddmws.split('/')
        pxbd__wwhbi['database'] = tpnw__wbcop
        if schema:
            pxbd__wwhbi['schema'] = schema
    if oakht__nvwgx.query:
        for enlbx__xmbz, sjtzc__qaqeo in parse_qsl(oakht__nvwgx.query):
            pxbd__wwhbi[enlbx__xmbz] = sjtzc__qaqeo
            if enlbx__xmbz == 'session_parameters':
                pxbd__wwhbi[enlbx__xmbz] = json.loads(sjtzc__qaqeo)
    pxbd__wwhbi['application'] = 'bodo'
    return pxbd__wwhbi


class SnowflakeDataset(object):

    def __init__(self, batches, schema, conn):
        self.pieces = batches
        self._bodo_total_rows = 0
        for izuo__fsa in batches:
            izuo__fsa._bodo_num_rows = izuo__fsa.rowcount
            self._bodo_total_rows += izuo__fsa._bodo_num_rows
        self.schema = schema
        self.conn = conn


def get_dataset(query, conn_str):
    acro__htd = tracing.Event('get_snowflake_dataset')
    from mpi4py import MPI
    mfpmm__rwrp = MPI.COMM_WORLD
    foe__bsc = tracing.Event('snowflake_connect', is_parallel=False)
    adx__llvd = get_connection_params(conn_str)
    conn = snowflake.connector.connect(**adx__llvd)
    foe__bsc.finalize()
    if bodo.get_rank() == 0:
        mrb__wbu = conn.cursor()
        loui__thqn = tracing.Event('get_schema', is_parallel=False)
        ipm__voy = f'select * from ({query}) x LIMIT {100}'
        dqyh__xpfjb = mrb__wbu.execute(ipm__voy).fetch_arrow_all()
        if dqyh__xpfjb is None:
            ace__yzly = mrb__wbu.describe(query)
            fko__gvcua = [pa.field(ppjhl__vnkmj.name, FIELD_TYPE_TO_PA_TYPE
                [ppjhl__vnkmj.type_code]) for ppjhl__vnkmj in ace__yzly]
            schema = pa.schema(fko__gvcua)
        else:
            schema = dqyh__xpfjb.schema
        loui__thqn.finalize()
        jmmb__qgpic = tracing.Event('execute_query', is_parallel=False)
        mrb__wbu.execute(query)
        jmmb__qgpic.finalize()
        batches = mrb__wbu.get_result_batches()
        mfpmm__rwrp.bcast((batches, schema))
    else:
        batches, schema = mfpmm__rwrp.bcast(None)
    ozvd__csoh = SnowflakeDataset(batches, schema, conn)
    acro__htd.finalize()
    return ozvd__csoh
