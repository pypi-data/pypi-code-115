from tools import stdinout
import sys, os
if sys.path[0][len(sys.path[0]) - 1] == 'interfaces': sys.path[0] = sys.path[0][:len(sys.path[0]) - 1]
import core
_core = core
hello_text = f'anthros-core (1.0p-a) for {sys.platform}\n  write "help" for command help\n'

def clear_screen():
    if sys.platform == 'win32': os.system('cls')
    else: os.system('clear')

def run():
    global _core
    clear_screen()
    tools = _core.tools()
    core = _core.run()
    clear_screen()
    print(hello_text)

    cmd = ''
    while cmd not in ['exit', 'restart']:
        cmd = input('>')

        if cmd == 'clear':
            clear_screen()
            print(hello_text)
            continue

        try:
            if cmd not in ['exit', 'restart']:
                out = core.command(cmd)
                if out != None: print(out, end = '\n\n')
                else: print(end = '\n')
        except:
            err = stdinout.exception(sys.exc_info())
            print(err, end = '\n\n')

    if cmd == 'restart': run()