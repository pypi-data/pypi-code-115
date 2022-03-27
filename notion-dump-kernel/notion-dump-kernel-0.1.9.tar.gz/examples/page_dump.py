# author: delta1037
# Date: 2022/01/11
# mail:geniusrabbit@qq.com

import logging

import NotionDump
from NotionDump.Dump.dump import Dump
from NotionDump.Notion.Notion import NotionQuery
from NotionDump.utils import common_op

TOKEN_TEST = "secret_g6easunNXs3S5OdTS4qBhlPZN9fjxTkdJ80wOImK5cZ"
PAGE_MIX_ID = "7a6df95c3f364d469feeb079e8d617df"
NotionDump.DUMP_MODE = NotionDump.DUMP_MODE_DEBUG


# 解析数据库内容测试：根据token和id解析数据库内容，得到临时CSV文件
def test_page_parser(query, export_child=False, db_parser_type=NotionDump.PARSER_TYPE_MD):
    page_handle = Dump(
        dump_id=PAGE_MIX_ID,
        query_handle=query,
        export_child_pages=export_child,
        dump_type=NotionDump.DUMP_TYPE_PAGE,
        db_parser_type=db_parser_type
    )
    # 将解析内容存储到文件中；返回内容存储为json文件
    page_detail_json = page_handle.dump_to_file()

    print("json output to page_parser_result")
    common_op.save_json_to_file(
        handle=page_detail_json,
        json_name=".tmp/page_parser_result.json"
    )


if __name__ == '__main__':
    query_handle = NotionQuery(token=TOKEN_TEST)
    if query_handle is None:
        logging.exception("query handle init error")
        exit(-1)

    # 页面解析测试,递归
    test_page_parser(query_handle, True)

    # 页面解析测试,非递归
    # test_page_parser(query_handle, False)

