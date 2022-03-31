
from google.cloud import bigquery
from pandas import DataFrame

from .contants import BIG_QUERY_LOAD_DATA_SIZE_LIMIT
from .utils import print_debug, print_info


def query_bigquery(query_string: str, project_id: str = 'footprint-etl-internal') -> DataFrame:
    bqclient = bigquery.Client(project=project_id)
    print_debug('query_string:', query_string)

    try_query_result: bigquery.QueryJob = try_query_bigquery(query_string=query_string, project_id=project_id)
    if try_query_result.total_bytes_processed:
        try_query_size = round((try_query_result.total_bytes_processed/1024/1024), 2)
        print_info(f"SQL 将要处理的 {try_query_size} MB 数据")
        if try_query_size > BIG_QUERY_LOAD_DATA_SIZE_LIMIT:
            print_info("超过查询限制 {BIG_QUERY_LOAD_DATA_SIZE_LIMIT} MB , 请修改 sql 语句减少单次查询量")
            return

    dataframe: DataFrame = bqclient.query(query_string) \
        .result() \
        .to_dataframe(create_bqstorage_client=False)

    return dataframe


def try_query_bigquery(query_string: str, project_id: str = 'footprint-etl-internal') -> bigquery.QueryJob:
    bqclient = bigquery.Client(project=project_id)
    print_debug('query_string:', query_string)
    job_config = bigquery.QueryJobConfig(dry_run=True, use_query_cache=False)
    query_job = bqclient.query(
        query_string,
        job_config=job_config,
    )
    return query_job
