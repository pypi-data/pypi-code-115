
import os
from urllib.parse import urljoin

# 内部使用数字版本
VERSION = 1
SOURCE = 'gaia_utils'

# 通过环境变量注入
API_HOST = os.environ.get("API_HOST", "https://www.footprint.network")
# API_HOST = "http://127.0.0.1:3000"
# API_HOST = "https://beta.footprint.network"
API_UPLOAD_URL = urljoin(API_HOST, "/api/v1/custom/data/upload")
API_GET_TABLE_LIST_URL = urljoin(API_HOST, "/api/v1/database/gaia/table/list")

API_UPLOAD_DATA_SIZE_LIMIT = 90  # MB
BIG_QUERY_LOAD_DATA_SIZE_LIMIT = 1024  # MB
