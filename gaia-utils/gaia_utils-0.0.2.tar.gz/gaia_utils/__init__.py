import os

from .auth import set_token
from .common import load_dataframe, save_csv, submit
from .enumlib.bigquery_schema_type_enum import BigquerySchemaType
from .enumlib.load_data_frame_type_enum import LoadDataframeType
from .env import ENV_DEV, ENV_PROD, is_debug, is_prod, set_debug, set_env
from .user_table import get_table_list
from .utils import print_debug, print_info

if not os.environ.get('GOOGLE_APPLICATION_CREDENTIALS'):
    print_info("GOOGLE_APPLICATION_CREDENTIALS 本地环境没有设置 google key")
