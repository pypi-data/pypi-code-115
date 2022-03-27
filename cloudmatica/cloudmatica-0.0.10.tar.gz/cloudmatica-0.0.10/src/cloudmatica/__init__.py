import argparse
parser = argparse.ArgumentParser(description='Cloudmatica CLI')
subparsers = parser.add_subparsers(dest='command', help='sub-command help')
parser_shorten = subparsers.add_parser('shorten',
                                       help='Create a link by shortening a long url',
                                       epilog='EXAMPLE: shorten https://example.com/my-very-long-url myshort')
parser_shorten.add_argument('url', type=str, help='The url to shorten')
parser_shorten.add_argument('short', type=str, help='The short name')
parser_go = subparsers.add_parser('go',
                                  help='Go to the url based on the short',
                                  epilog='EXAMPLE: go myshort')
parser_go.add_argument('short', type=str, help='The short name')
parser_go = subparsers.add_parser('list-shorts',
                                  help='Return a list of shorts and their corresponding urls',
                                  epilog='EXAMPLE: list-shorts')
args = parser.parse_args()


def get_endpoint():
    import sys
    import os
    # PYTEST environment variable is set in Pycharm run configuration
    if sys.platform == 'darwin' and os.getenv('PYTEST') == 'TRUE':
        return 'http://127.0.0.1:8888'
    else:
        return 'https://mdsl09trll.execute-api.us-east-1.amazonaws.com/api'


def shorten(args):
    request_url = f'{get_endpoint()}/shorten/{args.short}?url={args.url}'
    import requests
    response = requests.get(request_url)
    result = response.text
    print(result)
    return result


def go(args):
    request_url = f'{get_endpoint()}/go/{args.short}'
    import requests
    response = requests.get(request_url)
    result = response.text
    print(result)
    return result


def list_shorts():
    request_url = f'{get_endpoint()}/list_shorts'
    import requests
    response = requests.get(request_url)
    result = response.text
    print(result)
    return result



def main():
    import sys
    if not len(sys.argv) > 1:
        parser.print_help()
    if args.command == 'shorten':
        shorten(args)
    elif args.command == 'go':
        go(args)
    elif args.command == 'list-shorts':
        list_shorts()


if __name__ == '__main__':
    main()
