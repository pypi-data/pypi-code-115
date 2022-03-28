import sys
from . import version
import argparse
from . import parse_json
from datetime import datetime


def command_argparse_main(**kwargs):
    parser = argparse.ArgumentParser(
        prog='parse-json',
        usage='parse-json [OPTION]... data...',
        description="字符串转为json",
        add_help=False
    )

    
    parser.add_argument(
        '-V', '--version', help="输出版本", action="store_true"
    )
    parser.add_argument('string', nargs='*', help=argparse.SUPPRESS)
    
    parser.add_argument("-d", "--debug", action="store_true", help="默认为False")

    parser.add_argument("-f", help="读取数据的文件名")

    parser.add_argument("-h", "--help", action="store_true", help="获取帮助文档")

    parser.add_argument("-p", "--primary_key", default=".", help="主key")

    parser.add_argument('-k', action="store_true", help="是否打印key")

    parser.add_argument('-x', action="store_true", help="是否输出到excel")

    parser.add_argument('-excel_name', help="输出的excel的名字")

    args = parser.parse_args()

    is_print_key = args.k
    primary_key = args.primary_key
    if args.version:
        print("{} : {}".format(version.__package_name__, version.__version__))
        sys.exit()

    if args.string and args.f:
        raise argparse.ArgumentError
    
    excel_file_name = ''
    kwargs = {}
    if args.x:
        if args.excel_name:
            excel_file_name = args.excel_name
        else:
            excel_file_name = datetime.now().strftime("%Y%m%d-%H%M%S")
        excel_file_name = excel_file_name+".xlsx"
        kwargs['excel_file_name'] = excel_file_name
    

    if args.string:
        string = ''.join(args.string)
        string = string.strip()
        if not string:
            sys.exit()

        parse_json.print_data(string,primary_key=primary_key,is_print_key=is_print_key,**kwargs)
        sys.exit()
    if args.f:
        file_name = args.f
        parse_json.parse_file_data(file_name,primary_key=primary_key,is_print_key=is_print_key,**kwargs)
        sys.exit()



def main(**kwargs):  
    command_argparse_main(**kwargs)


if __name__ == '__main__':
    main()
    
