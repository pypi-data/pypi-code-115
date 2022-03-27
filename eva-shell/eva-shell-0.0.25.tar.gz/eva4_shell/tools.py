import sys
import os
import time
import neotermcolor
from neotermcolor import colored
from datetime import datetime
from rapidtables import (format_table, FORMAT_GENERATOR, FORMAT_GENERATOR_COLS,
                         MULTILINE_ALLOW)
from collections import OrderedDict

from .sharedobj import current_command, common


def ok():
    print(colored('OK', color='green'))


def debug(s):
    print(colored(str(s), color='grey'))


def warn(s, delay=False):
    print(colored(str(s), color='yellow', attrs='bold'))


def err(e, delay=False):
    print(colored(str(e), color='red'))
    if delay:
        import getch
        getch.getch()


def prepare_time(t):
    if t is None:
        return None
    import dateutil.parser
    try:
        return float(t)
    except:
        return dateutil.parser.parse(t).timestamp()


def print_tb(force=False, delay=False):
    if force:
        import traceback
        err(traceback.format_exc())
    else:
        err('FAILED')
    if delay:
        import getch
        getch.getch()


def can_colorize():
    return os.getenv('ANSI_COLORS_DISABLED') is None and (
        not neotermcolor.tty_aware or neotermcolor._isatty)


def set_file_lock(name):
    lock_file = f'{common.dir_eva}/var/{name}.lock'
    if os.path.exists(lock_file):
        raise RuntimeError
    else:
        with open(lock_file, 'w'):
            pass


def remove_file_lock(name):
    lock_file = f'{common.dir_eva}/var/{name}.lock'
    try:
        os.unlink(lock_file)
    except FileNotFoundError:
        pass


TIME_ORD = {
    'created': 0,
    'accepted': 1,
    'pending': 0b10,
    'running': 0b1000,
    'completed': 0b1111,
    'failed': 0b10000000,
    'canceled': 0b10000001,
    'terminated': 0b10000010,
}

ACTION_STATUS_COLOR = {
    'completed': 'green',
    'canceled': 'grey',
    'terminated': 'yellow',
    'failed': 'red'
}


def print_action_result(result):
    import uuid
    result['uuid'] = str(uuid.UUID(bytes=result['uuid']))
    status = result['status']
    time = result['time']
    times = [v for _, v in time.items()]
    if status in ['completed', 'failed', 'terminated']:
        result['elapsed'] = '{:.6f}'.format(max(times) - min(times))
    if time:
        time_data = sorted([{
            'n': k,
            'v': datetime.fromtimestamp(v, common.TZ).isoformat()
        } for k, v in time.items()],
                           key=lambda k: TIME_ORD.get(k['n'], 10))
        result['time'] = format_table(time_data, generate_header=False)
    params = result['params']
    if params:
        params_data = [{'n': k, 'v': v} for k, v in params.items()]
        result['params'] = format_table(params_data, generate_header=False)
    out = result.pop('out')
    err = result.pop('err')
    data = sorted([{
        'n': k,
        'v': v
    } for k, v in result.items()],
                  key=lambda k: k['n'])
    rows = format_table(
        data,
        fmt=FORMAT_GENERATOR_COLS,
        generate_header=False,
        multiline=MULTILINE_ALLOW,
    )
    spacer = '  '
    for r in rows:
        print(colored(r[0], color='blue') + spacer, end='')
        if r[0].startswith('status '):
            print(colored(r[1], color=ACTION_STATUS_COLOR.get(status)))
        else:
            print(r[1])
    if out:
        print('--- OUT ---')
        print(out)
    if err:
        print('--- ERR ---')
        print(colored(err, color='red'))
    print()


def print_result(data, need_header=True, name_value=False, cols=None):
    if current_command.json:
        from pygments import highlight, lexers, formatters
        import json
        j = json.dumps(data, indent=4, sort_keys=True)
        if can_colorize():
            j = highlight(j, lexers.JsonLexer(), formatters.TerminalFormatter())
        print(j)
        return
    elif data:
        if name_value:
            if name_value is True:
                nn = 'field'
                vn = 'value'
            else:
                nn = name_value[0]
                vn = name_value[1]
            data = sorted([{
                nn: k,
                vn: v
            } for k, v in data.items()],
                          key=lambda k: k[nn])
            if need_header:
                header, rows = format_table(data, fmt=FORMAT_GENERATOR)
                print(colored(header, color='blue'))
                print(colored('-' * len(header), color='grey'))
                for r in rows:
                    print(r)
            else:
                rows = format_table(data,
                                    fmt=FORMAT_GENERATOR_COLS,
                                    generate_header=False)
                spacer = '  '
                for r in rows:
                    print(colored(r[0], color='blue') + spacer, end='')
                    print(r[1])
        else:
            if cols:
                col_rules = {}
                for i, c in enumerate(cols):
                    if '|' in c:
                        r = c.split('|')
                        rules = {'_': r[0]}
                        col_rules[i] = rules
                        for rule in r[1:]:
                            k, v = rule.split('=', maxsplit=1)
                            rules[k] = v
                    else:
                        col_rules[i] = {}
                formatted_data = []
                for d in data:
                    od = OrderedDict()
                    for i, c in enumerate(cols):
                        rules = col_rules[i]
                        src = rules.get('_', c)
                        val = d.get(src, '')
                        fmt = rules.get('f')
                        if val != '' and val is not None:
                            try:
                                if fmt == 'time':
                                    val = datetime.fromtimestamp(
                                        val, common.TZ).isoformat()
                                elif fmt.startswith('time:'):
                                    zone = fmt.split(':', 1)[-1]
                                    import pytz
                                    val = datetime.fromtimestamp(
                                        val, pytz.timezone(zone)).isoformat()
                            except:
                                pass
                        od[rules.get('n', c)] = val
                    formatted_data.append(od)
                header, rows = format_table(formatted_data,
                                            fmt=FORMAT_GENERATOR)
            else:
                if data and not isinstance(data[0], dict):
                    data = [{'value': d} for d in data]
                header, rows = format_table(data, fmt=FORMAT_GENERATOR)
            if need_header:
                print(colored(header, color='blue'))
                print(colored('-' * len(header), color='grey'))
            for r in rows:
                print(r)
    print()


def edit_config(value, ss, deploy_fn, initial=False):
    import yaml
    import tempfile
    from hashlib import sha256
    from pathlib import Path
    editor = os.getenv('EDITOR', 'vi')
    fname = sha256(ss.encode()).hexdigest()
    tmpfile = Path(f'{tempfile.gettempdir()}/{fname}.tmp.yml')
    if isinstance(value, str):
        tmpfile.write_text(value)
    else:
        tmpfile.write_text(yaml.dump(value, default_flow_style=False))
    try:
        while True:
            code = os.system(f'{editor} {tmpfile}')
            if code:
                err(f'editor exited with code {code}')
                break
            try:
                data = yaml.safe_load(tmpfile.read_text())
            except:
                print_tb(force=True, delay=True)
                continue
            if data == value and not initial:
                break
            else:
                try:
                    deploy_fn(data)
                    break
                except Exception as e:
                    err(e, delay=True)
                    continue
    finally:
        try:
            tmpfile.unlink()
        except FileNotFoundError:
            pass


def read_file(fname=None):
    if fname is None or fname == '-':
        if sys.stdin.isatty():
            print('Copy/paste or type data, press Ctrl-D to end')
        return sys.stdin.buffer.read()
    else:
        with open(fname, 'rb') as fh:
            return fh.read()


def format_value(value, advanced=False):
    if value.startswith('!'):
        return value[1:]
    elif advanced and ',' in value:
        return [format_value(v) for v in value.split(',')]
    else:
        if value == 'null':
            return None
        elif value == 'true':
            return True
        elif value == 'false':
            return False
        try:
            return int(value)
        except:
            try:
                return float(value)
            except:
                return value


def safe_print(val, extra=0):
    width, height = os.get_terminal_size(0)
    print(val[:width + extra])


def get_node_svc_info():
    import json
    return json.loads(
        os.popen(f'{common.dir_eva}/svc/eva-node --mode info').read())


def get_arch():
    import platform
    return platform.machine()


def safe_download(url, manifest=None, timeout=None, public_key=None, **kwargs):
    import requests
    r = requests.get(url,
                     timeout=timeout if timeout else current_command.timeout,
                     **kwargs)
    if not r.ok:
        raise RuntimeError(f'HTTP error {r.status_code} for {url}')
    if isinstance(manifest, str):
        r_m = requests.get(manifest, **kwargs)
        if not r_m.ok:
            raise RuntimeError(f'HTTP error {r.status_code} for {manifest}')
        manifest = r_m.json()
    if manifest:
        try:
            data = manifest['content'][url.rsplit('/', 1)[-1]]
            size = data['size']
            sha256 = data['sha256']
        except KeyError:
            raise RuntimeError(f'Info for {url} not found in manifest')
        if len(r.content) != size:
            raise RuntimeError(f'Size check error for {url}')
        import hashlib
        if hashlib.sha256(r.content).hexdigest() != sha256:
            raise RuntimeError(f'Checksum error for {url}')
    return r.content
