"""
climatik

Create command line interface from function definitions.
Each function will be a subcommand of your application.
"""

import inspect
import argparse
from typing import Callable, Optional, TypedDict, Dict, Any,  Union, get_origin, get_args
try:
    import argcomplete
except ImportError:
    argcomplete = None

__version__ = "0.4.1"

class NameClashException(Exception):
    pass

class CommandType(TypedDict):
    help:Optional[str]
    description:Optional[str]
    func:Callable
    args:Dict[str, Any]

class CommandGroup(TypedDict):
    help:Optional[str]
    description:Optional[str]
    commands:Dict[str,CommandType]

commands:Dict[str,CommandGroup] = {
    '' : {
        'help': '',
        'description': '',
        'commands': {}
    }
}

def is_optional(field):
    return get_origin(field) is Union and \
           type(None) in get_args(field)

def get_parser(*args, **kwargs) -> argparse.ArgumentParser:
    """Build command line parser
    
    Arguments are passed to `argparse.ArgumentParser` constructor
    """
    parser = argparse.ArgumentParser(*args, **kwargs)
    parser.set_defaults(func=lambda *a,**k: parser.print_help())
    subparsers = parser.add_subparsers(title="Subcommands")

    for groupname, group in commands.items():
        if groupname == "":
            groupparsers = subparsers
        else:
            grouparser = subparsers.add_parser(groupname,  help=group['help'], description=group['description'])
            groupparsers = grouparser.add_subparsers(title="Subcommands")
            grouparser.set_defaults(func=lambda *a,**k: grouparser.print_help())

        for name, command in group['commands'].items():
            s_parser = groupparsers.add_parser(name, help=command['help'], description=command['description'])
            for s_name, arg in command['args'].items():
                s_parser.add_argument(s_name, **arg)
            s_parser.set_defaults(func=command['func'])
            
    if argcomplete:
        argcomplete.autocomplete(parser)
    return parser


def execute(parser:argparse.ArgumentParser):
    """Execute command line from given parser"""
    nsargs = parser.parse_args()
    args = vars(nsargs)
    func = args['func']
    del args['func']
    kwargs = { k.replace("-","_"): args[k] for k in args }
    func(**kwargs)


def run(prog:str=None, usage:str=None, description:str=None, **kwargs):
    """Run your application"""
    parser = get_parser(prog=prog, usage=usage, description=description, **kwargs)
    execute(parser)


def _optional_arg_decorator(fn:Callable):
    """ Decorate a function decorator to allow optional parameters to be passed to the decorated decorator...

    (from https://stackoverflow.com/a/20966822. yeah! stackoverflow!)
    """
    def wrapped_decorator(*args, **kwargs):
        if (len(args)==1 and callable(args[0])):
            return fn(*args)
        else:
            def real_decorator(decoratee):
                return fn(decoratee, *args, **kwargs)
            return real_decorator
    return wrapped_decorator


class group():
    """Set command group help and description

    If a group named `name` does not exists, is created

    Can be used also as a context manager. Each command defined
    in context will be added to the group

    with group('file', help="Manage files", description="Functions to manage files"):
        @command
        def ls():
            ...
        
        @command
        def rm():
            ...
    """
    name:Optional[str] = None

    def __init__(self, name:str, help:str = "", description:str = ""):
        self._name = name
        if name not in commands:
            commands[name] = {
                'help': help,
                'description': description,
                'commands': {}
            }
        else:
            commands[name]['help'] = help
            commands[name]['description'] = description

    def __enter__(self):
        group.name = self._name

    def __exit__(self, type, value, traceback):
        group.name = None


@_optional_arg_decorator
def command(fnc:Callable, command_name:str=None, group_name:str=''):
    """Build subcommand from function

    Subcommand name will be the function name and arguments are parsed to build the command line.
    Optionally, subcommand name can be passed as parameter:
    
        @command('name')
        def test():
            ...

    Subcommands can be groupped passing `group_name` paramenter:

        @command(group_name="group")
        def bar()
            ...

        @command(group_name="group")
        def baz()
            ...

    This two functions will be called from command line as `group bar` and `group baz`

    Each positional argument of the decorated function will be a positional paramenter.
    
    Each optional argument will be an optional flag.

    Type hints are used to covert types from command line string.
    
    An argument with `bool` type is converted to an optional flag parameter (with default sematic as "False")
    
    To create an optional positional paramenter, use the `typing.Optional` type as hint with the parameter type,
    e.g. `Optional[str]` and default value `None`

    Function docstring is used to set command's help and description.
    To set arguments help string, add a line in docstring like

        @param argname : argument help

    Exacmple:

        @command
        def one(name, debug:bool, value="default", switchoff=True):
            \"""First subcommand
            
            @param debug: enable debug output
            ""\"
            ...

        @command
        def two(name:Optional[str] = None, long_param = None):
            "Second subcommand"
            ...

    gives:

        $ script -h
        usage: script [-h] {one,two} ...

        Subcommands:
        {one,two}
            one       First subcommand
            two       Second subcommand

        optional arguments:
        -h, --help  show this help message and exit

        $ script one -h
        usage: script one [-h] [--debug] [--value VALUE] [--switchoff] name

        First subcommand

        positional arguments:
        name

        optional arguments:
        -h, --help     show this help message and exit
        --debug        enable debug output
        --value VALUE  (default 'default')
        --switchoff

        $ script two -h
        usage: script two [-h] [--long-param LONG_PARAM] [name]

        Second subcommand

        positional arguments:
        name

        optional arguments:
        -h, --help            show this help message and exit
        --long-param LONG_PARAM

    """

    description:str = fnc.__doc__ or ""

    # extract "@param name help str" from docstring
    args_help:Dict[str,str] = {}
    for l in description.split("\n"):
        if l.strip().startswith("@param "):
            p_name, p_help = l.replace("@param", "").strip().split(":",1)
            args_help[p_name.strip()] = p_help.strip() 
            description = description.replace(l, "")

    help:Optional[str] = None
    try:
        help = description
        help = help.split('\n')[0].strip()
    except (AttributeError, IndexError):
        help = None

    command:CommandType = {
        'help' : help,
        'description' : description,
        'func' : fnc,
        'args' : {},
    }

    sig = inspect.signature(fnc)
    for k in sig.parameters:
        param = sig.parameters[k]
        name = param.name
        arg = {}

        # let's use annotation type for argument type
        if not param.annotation is param.empty:
            # TODO: this is ugly.. may be it's better in python 3.10 with `match`?
            if is_optional(param.annotation):
                arg['type'] = get_args(param.annotation)[0]
            else:
                arg['type'] = param.annotation

        # if param has default value, argument is optional
        if not param.default is param.empty:
            # make it a flag but not if type is Optional
            if is_optional(param.annotation):
                arg['nargs'] = "?"
            else:
                name = "--"+name
            arg['default'] = param.default
            
            if 'type' not in arg:
                arg['type'] = type(param.default)

        # we don't want arguments with type "None". default to "str"
        if not 'type' in arg or arg['type'] == type(None):
            arg['type'] = str

        # if argument type is bool, the argument become a switch
        if 'type' in arg and arg['type'] is bool:
            if not name.startswith('--'):
                name = "--"+name
            if not 'default' in arg:
                arg['action']="store_true"
            else:
                arg['action']="store_" + str(not arg['default']).lower()
                del arg['default']
            del arg['type']

        # build arg help text
        a_help = args_help.get(param.name, "")
        if arg.get('default') is not None:
            a_help += f" (default '{arg['default']}')"
        arg['help'] = a_help.strip()

        # "arg_name" to "arg-name"
        name = name.replace("_", "-")
        command['args'][name] = arg

    if command_name is None:
        command_name = fnc.__name__

    if group.name is not None and group_name == "":
        group_name = group.name

    if group_name in commands['']['commands'].keys():
        raise NameClashException(f"Cannot define group with same name as command '{group_name}'")
    else:
        for gname in commands.keys():
            if gname == command_name:
                raise NameClashException(f"Cannot define command with same name as group '{command_name}'")

    if group_name not in commands:
        commands[group_name] = {
            'help': '',
            'description': '',
            'commands': {}
        }

    commands[group_name]['commands'][command_name] = command

    return fnc


if __name__=="__main__":
    @command
    def one(name, debug:bool, value="default", switchoff=True):
        "First subcommand"
        print(f"name: {name!r}, debug: {debug!r}, value: {value!r}, switchoff: {switchoff!r}")

    @command(group_name='group')
    def two(name:Optional[str] = None, long_param = None):
        "Second subcommand"
        print(f"name: {name!r}, long_param: {long_param!r}")

    run()
