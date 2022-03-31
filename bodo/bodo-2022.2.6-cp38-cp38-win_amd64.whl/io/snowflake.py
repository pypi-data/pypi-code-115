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
    pkclc__hdue = urlparse(conn_str)
    tmnyg__ztd = {}
    if pkclc__hdue.username:
        tmnyg__ztd['user'] = pkclc__hdue.username
    if pkclc__hdue.password:
        tmnyg__ztd['password'] = pkclc__hdue.password
    if pkclc__hdue.hostname:
        tmnyg__ztd['account'] = pkclc__hdue.hostname
    if pkclc__hdue.port:
        tmnyg__ztd['port'] = pkclc__hdue.port
    if pkclc__hdue.path:
        hzf__txs = pkclc__hdue.path
        if hzf__txs.startswith('/'):
            hzf__txs = hzf__txs[1:]
        sqmmg__txsbc, schema = hzf__txs.split('/')
        tmnyg__ztd['database'] = sqmmg__txsbc
        if schema:
            tmnyg__ztd['schema'] = schema
    if pkclc__hdue.query:
        for jnvk__mfc, wer__dgfo in parse_qsl(pkclc__hdue.query):
            tmnyg__ztd[jnvk__mfc] = wer__dgfo
            if jnvk__mfc == 'session_parameters':
                tmnyg__ztd[jnvk__mfc] = json.loads(wer__dgfo)
    tmnyg__ztd['application'] = 'bodo'
    return tmnyg__ztd


class SnowflakeDataset(object):

    def __init__(self, batches, schema, conn):
        self.pieces = batches
        self._bodo_total_rows = 0
        for qbps__dovxl in batches:
            qbps__dovxl._bodo_num_rows = qbps__dovxl.rowcount
            self._bodo_total_rows += qbps__dovxl._bodo_num_rows
        self.schema = schema
        self.conn = conn


def get_dataset(query, conn_str):
    qxpd__sbcz = tracing.Event('get_snowflake_dataset')
    from mpi4py import MPI
    qcxb__uokek = MPI.COMM_WORLD
    dzj__habi = tracing.Event('snowflake_connect', is_parallel=False)
    ubuhl__shg = get_connection_params(conn_str)
    conn = snowflake.connector.connect(**ubuhl__shg)
    dzj__habi.finalize()
    if bodo.get_rank() == 0:
        dxu__mzlnh = conn.cursor()
        goyui__dcyya = tracing.Event('get_schema', is_parallel=False)
        xefjr__edjn = f'select * from ({query}) x LIMIT {100}'
        moij__wvra = dxu__mzlnh.execute(xefjr__edjn).fetch_arrow_all()
        if moij__wvra is None:
            uxp__hmws = dxu__mzlnh.describe(query)
            qrz__wqwpp = [pa.field(usug__epva.name, FIELD_TYPE_TO_PA_TYPE[
                usug__epva.type_code]) for usug__epva in uxp__hmws]
            schema = pa.schema(qrz__wqwpp)
        else:
            schema = moij__wvra.schema
        goyui__dcyya.finalize()
        wldmg__ltm = tracing.Event('execute_query', is_parallel=False)
        dxu__mzlnh.execute(query)
        wldmg__ltm.finalize()
        batches = dxu__mzlnh.get_result_batches()
        qcxb__uokek.bcast((batches, schema))
    else:
        batches, schema = qcxb__uokek.bcast(None)
    nuhzu__gogc = SnowflakeDataset(batches, schema, conn)
    qxpd__sbcz.finalize()
    return nuhzu__gogc
