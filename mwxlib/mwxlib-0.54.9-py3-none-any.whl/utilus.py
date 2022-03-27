#! python3
# -*- coding: utf-8 -*-
"""mwxlib core

Author: Kazuya O'moto <komoto@jeol.co.jp>
"""
from collections import OrderedDict
from functools import wraps
import traceback
import warnings
import shlex
import time
import sys
import os
import re
import fnmatch
import pkgutil
import inspect
from inspect import (isclass, ismodule, ismethod, isbuiltin,
                     isfunction, isgenerator, isframe, iscode, istraceback)
from pprint import pprint, pformat
from six import string_types


def atom(v):
    return not hasattr(v, '__name__')


def isobject(v):
    ## return atom(v) and hasattr(v, '__module__')
    return re.match(r"<([\w.]+) object at \w+>", repr(v))


def instance(*types):
    ## return lambda v: isinstance(v, types)
    def _pred(v):
        return isinstance(v, types)
    _pred.__name__ = str("instance<{}>".format(','.join(p.__name__ for p in types)))
    return _pred


def subclass(*types):
    ## return lambda v: issubclass(v, types)
    def _pred(v):
        return issubclass(v, types)
    _pred.__name__ = str("subclass<{}>".format(','.join(p.__name__ for p in types)))
    return _pred


def _Not(p):
    ## return lambda v: not p(v)
    if isinstance(p, type):
        p = instance(p)
    def _pred(v):
        return not p(v)
    _pred.__name__ = str("not {}".format(p.__name__))
    return _pred


def _And(p, q):
    ## return lambda v: p(v) and q(v)
    if isinstance(p, type):
        p = instance(p)
    if isinstance(q, type):
        q = instance(q)
    def _pred(v):
        return p(v) and q(v)
    _pred.__name__ = str("{} and {}".format(p.__name__, q.__name__))
    return _pred


def _Or(p, q):
    ## return lambda v: p(v) or q(v)
    if isinstance(p, type):
        p = instance(p)
    if isinstance(q, type):
        q = instance(q)
    def _pred(v):
        return p(v) or q(v)
    _pred.__name__ = str("{} or {}".format(p.__name__, q.__name__))
    return _pred


def predicate(text, locals):
    tokens = [x for x in split_words(text.strip()) if not x.isspace()]
    j = 0
    while j < len(tokens):
        c = tokens[j]
        if c == 'not' or c == '~':
            tokens[j:j+2] = ["_Not({})".format(tokens[j+1])]
        j += 1
    j = 0
    while j < len(tokens):
        c = tokens[j]
        if c == 'and' or c == '&':
            tokens[j-1:j+2] = ["_And({},{})".format(tokens[j-1], tokens[j+1])]
            continue
        j += 1
    j = 0
    while j < len(tokens):
        c = tokens[j]
        if c == 'or' or c == '|':
            tokens[j-1:j+2] = ["_Or({},{})".format(tokens[j-1], tokens[j+1])]
            continue
        j += 1
    return eval(' '.join(tokens) or 'None', None, locals)


def wdir(obj):
    """As the standard dir, but also listup fields of COM object
    
    Create COM object with [win32com.client.gencache.EnsureDispatch]
    for early-binding to get what methods and params are available.
    """
    keys = dir(obj)
    try:
        if hasattr(obj, '_dispobj_'):
            keys += dir(obj._dispobj_)
    finally:
        return keys


def apropos(obj, rexpr, ignorecase=True, alias=None, pred=None, locals=None):
    """Put a list of objects having expression `rexpr in `obj
    """
    name = alias or typename(obj)
    rexpr = (rexpr.replace('\\a','[a-z0-9]')  #\a: identifier chars (custom rule)
                  .replace('\\A','[A-Z0-9]')) #\A: 
    
    if isinstance(pred, string_types):
        pred = predicate(pred, locals)
    
    if isinstance(pred, type):
        pred = instance(pred)
    
    if pred:
        if not callable(pred):
            raise TypeError("{!r} is not callable".format(pred))
        try:
            pred(None)
        except (TypeError, ValueError):
            pass
    
    with warnings.catch_warnings():
        warnings.simplefilter('ignore', DeprecationWarning)
        
        print("matching to {!r} in {} {} :{}".format(
              rexpr, name, type(obj), pred and typename(pred)))
        try:
            p = re.compile(rexpr, re.I if ignorecase else 0)
            keys = sorted(filter(p.search, wdir(obj)), key=lambda s:s.upper())
            n = 0
            for key in keys:
                try:
                    value = getattr(obj, key)
                    if pred and not pred(value):
                        continue
                    word = repr(value)
                    word = ' '.join(s.strip() for s in word.splitlines())
                    n += 1
                except (TypeError, ValueError):
                    continue
                except Exception as e:
                    word = '#<{!r}>'.format(e)
                if len(word) > 80:
                    word = word[:80] + '...' # truncate words +3 ellipsis
                print("    {}.{:<36s} {}".format(name, key, word))
            if pred:
                print("found {} of {} words with :{}".format(n, len(keys), typename(pred)))
            else:
                print("found {} words.".format(len(keys)))
        except re.error as e:
            print("- re:miss compilation {!r} : {!r}".format(e, rexpr))


def typename(obj, docp=False, qualp=False):
    """Typename of the obj object
    
    retval-> module:obj<doc>       when obj is callable and qualp=False
             module:class<doc>     when obj is a class or an instance object3
             module:class.obj<doc> when obj is an atom or callable and qualp=True
             type<obj>             otherwise
    """
    _mods = (None, "__main__",
                   "mwx.utilus",
                   "mwx.framework",
                   )
    if hasattr(obj, '__name__'): # class, module, method, function, etc.
        name = obj.__name__
        if qualp:
            if hasattr(obj, '__qualname__'):
                name = obj.__qualname__
        
        if hasattr(obj, '__module__'): # -> module:name
            module = obj.__module__
            if module not in _mods:
                name = module + ':' + name
        
    elif hasattr(obj, '__module__'): # atom -> module.class
        name = obj.__class__.__name__
        module = obj.__module__
        if module not in _mods:
            name = module + '.' + name
    else:
        ## return "{}<{!r}>".format(type(obj), pydoc.describe(obj))
        return str(type(obj))
    
    if docp and callable(obj) and obj.__doc__:
        name += "<{!r}>".format(obj.__doc__.splitlines()[0]) # concat the first doc line
    return name


def where(obj):
    """Show @where (filename, lineno) the obj is defined
    
    A class, method, function, traceback, frame, or code object is expected.
    Otherwise, the module will be returned if it exists.
    """
    try:
        filename = inspect.getsourcefile(obj)
        src, lineno = inspect.getsourcelines(obj)
        if not lineno:
            return filename
        return "{!s}:{}:{!s}".format(filename, lineno, src[0].rstrip())
    except Exception:
        pass
    try:
        return inspect.getfile(obj.__class__)
    except Exception:
        module = inspect.getmodule(obj)
        if module:
            return repr(module)


def mro(obj):
    """Show @mro (method resolution order) of obj:class
    
    A list of filenames and lineno, or the module-names
    """
    if not isinstance(obj, type):
        obj = type(obj)
    for base in obj.__mro__:
        f = where(base)
        print("  {:40s} {}".format(str(base),
                        getattr(f, '__file__', None) or
                        getattr(f, '__name__', None) or f))


def pp(obj):
    pprint(obj, **pp.__dict__)

if pp:
    pp.indent = 1
    pp.width = 80 # default 80
    pp.depth = None
    if sys.version_info >= (3,6):
        pp.compact = False
    if sys.version_info >= (3,8):
        pp.sort_dicts = True


def _get_words_backward(text, sep=None):
    """Get words (from text at left side of caret)"""
    tokens = _split_tokens(text)[::-1]
    return _extract_words_from_tokens(tokens, sep, reverse=1)


def _get_words_forward(text, sep=None):
    """Get words (from text at right side of caret)"""
    tokens = _split_tokens(text)
    return _extract_words_from_tokens(tokens, sep)


def split_words(text):
    phrases = []
    tokens = _split_tokens(text)
    while tokens:
        words = _extract_words_from_tokens(tokens)
        phrases.append(words or tokens.pop(0)) # extracted words or a separator
    return phrases


def _split_tokens(text):
    lexer = shlex.shlex(text)
    lexer.wordchars += '.'
    lexer.whitespace = '' # nothing is white (for multiline analysis)
    lexer.commenters = '' # don't ignore comment lines
    ls = []
    n = 0
    p = re.compile(r"([a-zA-Z])[\"\']") # check [bfru]-string
    try:
        for token in lexer:
            m = p.match(token)
            if m:
                ls.append(m.group(1))
                return ls + _split_tokens(text[n+1:])
            ls.append(token)
            n += len(token)
    except ValueError:
        pass
    return ls


def _extract_words_from_tokens(tokens, sep=None, reverse=False):
    """Extract pythonic expressions from `tokens
    default `sep includes `@, binary-ops, and whitespaces, etc.
    """
    if sep is None:
        sep = "`@=+-/*%<>&|^~,:; \t\r\n!?" # OPS; SEPARATOR_CHARS; !?
    p, q = "({[", ")}]"
    if reverse:
        p,q = q,p
    stack = []
    words = []
    for j, c in enumerate(tokens):
        if c in p:
            stack.append(c)
        elif c in q:
            if not stack: # error("open-paren", c)
                break
            if c != q[p.index(stack.pop())]: # error("mismatch-paren", c)
                break
        elif not stack and c in sep: # ok
            break
        words.append(c) # stack word
    else:
        j = None
        if stack: # error("unclosed-paren", ''.join(stack))
            pass
    del tokens[:j] # Erase the extracted token
    return ''.join(reversed(words) if reverse else words)


def find_modules(force=False, verbose=True):
    """Find all modules available and write to log file.
    
    Similar to pydoc.help, it scans packages, but also the submodules.
    This creates a log file in ~/.deb and save the list.
    """
    f = get_rootpath("deb-modules-{}.log".format(sys.winver))
    
    if not force and os.path.exists(f):
        with open(f, 'r') as o:
            return eval(o.read()) # read and evaluate a list of modules
    else:
        print("Please wait a moment "
              "while Py{} gathers a list of all available modules... "
              "(This is executed once)".format(sys.winver))
        
        lm = list(sys.builtin_module_names)
        
        def _callback(path, modname, desc):
            lm.append(modname)
            if verbose:
                print('\b'*80 + "Scanning {:70s}".format(modname[:70]), end='',
                    file=sys.__stdout__)
        
        def _error(modname):
            if verbose:
                print('\b'*80 + "- failed: {}".format(modname),
                    file=sys.__stdout__)
        
        with warnings.catch_warnings():
            warnings.simplefilter('ignore') # ignore problems during import
            
            ## pydoc.ModuleScanner().run(_callback, key='', onerror=_error)
            for _importer, modname, _ispkg in pkgutil.walk_packages(onerror=_error):
                _callback(None, modname, '')
        
        lm.sort(key=str.upper)
        with open(f, 'w') as o:
            pprint(lm, stream=o) # write modules
        
        print('\b'*80 + "The results were written in {!r}.".format(f))
        return lm


def get_rootpath(f):
    """Return pathname ~/.mwxlib/f
    If ~/.mwxlib/ does not exist, it will be created.
    """
    home = os.path.normpath(os.path.expanduser("~/.mwxlib"))
    if not os.path.exists(home):
        os.mkdir(home)
    return os.path.join(home, f)


## --------------------------------
## Finite State Machine
## --------------------------------

class SSM(OrderedDict):
    """Single State Machine/Context of FSM
    """
    def __call__(self, event, *args, **kwargs):
        for act in self[event]:
            act(*args, **kwargs)
    
    def __repr__(self):
        return "<{} object at 0x{:X}>".format(typename(self), id(self))
    
    def __str__(self):
        def name(a):
            if callable(a):
                return typename(a, docp=1, qualp=0)
            return repr(a) # index
        return '\n'.join("{:>32} : {}".format(
            k, ', '.join(name(a) for a in v)) for k,v in self.items())
    
    def bind(self, event, action=None):
        """Append a transaction to the context"""
        transaction = self[event]
        if action is None:
            return lambda f: self.bind(event, f)
        if not callable(action):
            raise TypeError("{!r} is not callable".format(action))
        if action not in transaction:
            transaction.append(action)
        return action
    
    def unbind(self, event, action=None):
        """Remove a transaction from the context"""
        transaction = self[event]
        if action is None:
            del self[event]
            return True
        if not callable(action):
            raise TypeError("{!r} is not callable".format(action))
        if action in transaction:
            transaction.remove(action)
            if not any(callable(x) for x in transaction):
                del self[event]
            return True
        return False


class FSM(dict):
    """Finite State Machine
    
    contexts : map of context
        { state : initial state
            { event : event key <str>
                transaction (next_state, *actions ...) }
        }
        state `None` is a wildcard (as executed any time)
        event is a string that can include wildcards `*?[]` (fnmatch rule)
        actions must accept the same *args of function as __call__(*args)
        
    If no action, FSM carries out only a transition.
    The transition is always done before actions.
    
    Note: There is no enter/exit event handler.

Attributes:
    debug : verbose level
        [1] trace when state transits
        [2] + when different event comes
        [3] + all events and actions
        [4] ++ all events (+ including state:None)
        [5] ++ all events (even if no actions + state:None)
        [8] +++ max verbose level to put all args and kwargs
    default_state : referred as default state sucn as global-map
        default=None is given as an argument of the init.
        If there is only one state, that state will be the default.
    current_state : referred as the current state
   previous_state : (read-only, internal use only)
    """
    debug = 0
    default_state = None
    current_state = property(lambda self: self.__state)
    previous_state = property(lambda self: self.__prev_state)
    event = property(lambda self: self.__event)
    
    @current_state.setter
    def current_state(self, state):
        self.__state = state
        self.__event = '*forced*'
        self.__debcall__(self.__event)
    
    def clear(self, state):
        """Reset current and previous states"""
        self.default_state = state
        self.__state = state
        self.__prev_state = state
        self.__event = None
        self.__prev_event = None
    
    def __init__(self, contexts=None, default=None):
        dict.__init__(self) # update dict, however, it does not clear
        dict.clear(self)    # if and when __init__ is called, all contents are cleared
        if contexts is None:
            contexts = {}
        if default is None: # if no default given, reset the first state as the default
            if FSM.default_state is None:
                keys = list(contexts)
                if keys:
                    default = keys[0]
        self.clear(default) # the first clear creates object localvars
        self.update(contexts)
    
    def __missing__(self, key):
        raise Exception("FSM:logic-error - undefined state {!r}".format(key))
    
    def __repr__(self):
        return "<{} object at 0x{:X}>".format(typename(self), id(self))
    
    def __str__(self):
        return '\n'.join("[ {!r} ]\n{!s}".format(k,v) for k,v in self.items())
    
    def __call__(self, event, *args, **kwargs):
        """Dispatch the given event
        First, call with the state:None, then call with the current state.
        
        The retval dppends on the context:
            process the event (with transition or actions) -> list
            no event:transaction -> None
        """
        perf = False # Is transaction performed?
        retvals = [] # retvals of actions
        if None in self:
            org = self.__state
            prg = self.__prev_state
            try:
                self.__event = event
                self.__state = None
                ret = self.call(event, *args, **kwargs) # `None` process
                if ret is not None:
                    perf = True
                    retvals += ret
            finally:
                if self.__state is None: # restore original
                    self.__state = org
                    self.__prev_state = prg
        
        self.__event = event
        if self.__state is not None:
            ret = self.call(event, *args, **kwargs) # normal process
            if ret is not None:
                perf = True
                retvals += ret
        
        self.__prev_state = self.__state
        self.__prev_event = event
        if perf:
            return retvals
    
    def call(self, event, *args, **kwargs):
        """Invoke the event handler
        Process:
            1. transit the state
            2. try actions after transition
        retval-> list or None
        """
        context = self[self.__state]
        if event in context:
            transaction = context[event]
            self.__prev_state = self.__state # save previous state
            self.__state = transaction[0]    # the state transits here
            self.__debcall__(event, *args, **kwargs) # check after transition
            retvals = []
            for act in transaction[1:]:
                try:
                    ret = act(*args, **kwargs) # try actions after transition
                    retvals.append(ret)
                except Exception as e:
                    self.dump("- FSM:exception - {!r}".format(e),
                              "   event : {}".format(event),
                              "    from : {}".format(self.__prev_state),
                              "   state : {}".format(self.__state),
                              "  action : {}".format(typename(act)),
                              "    args : {}".format(args),
                              "  kwargs : {}".format(kwargs))
                    traceback.print_exc()
            return retvals
        else:
            ## matching test using fnmatch ファイル名規約によるマッチングテスト
            for pat in context:
                if fnmatch.fnmatchcase(event, pat):
                    return self.call(pat, *args, **kwargs) # recursive call with matched pattern
        
        self.__debcall__(event, *args, **kwargs) # check when no transition
        return None # no event, no action
    
    def __debcall__(self, pattern, *args, **kwargs):
        v = self.debug
        if v and self.__state is not None:
            transaction = self[self.__prev_state].get(pattern) or []
            actions = ', '.join(typename(a) for a in transaction[1:])
            if (v > 0 and self.__prev_state != self.__state
             or v > 1 and self.__prev_event != self.__event
             or v > 2 and actions
             or v > 3):
                self.log("{c} {1} --> {2} {0!r} {a}".format(
                    self.__event, self.__prev_state, self.__state,
                    a = '' if not actions else ('=> ' + actions),
                    c = '*' if self.__prev_state != self.__state else ' '))
        
        elif v > 3: # state is None
            transaction = self[None].get(pattern) or []
            actions = ', '.join(typename(a) for a in transaction[1:])
            if actions or v > 4:
                self.log("\t| {0!r} {a}".format(
                    self.__event,
                    a = '' if not actions else ('=> ' + actions)))
        
        if v > 7: # max verbose level puts all args
            self.log("\t:", *args)
            self.log("\t:", kwargs)
    
    @staticmethod
    def log(*args):
        print(*args, file=sys.__stdout__)
    
    @staticmethod
    def dump(*args):
        print(*args, sep='\n', file=sys.__stderr__)
        f = get_rootpath("deb-dump.log")
        with open(f, 'a') as o:
            print(time.strftime('!!! %Y/%m/%d %H:%M:%S'), file=o)
            print(*args, sep='\n', end='\n\n', file=o)
            print(traceback.format_exc(), file=o)
    
    @staticmethod
    def duplicate(context):
        """Duplicate the transaction:list in the context
        
        This method is used for the contexts given to :append and :update
        so that the original transaction (if they are lists) is not removed.
        
        このメソッドはオリジナルのコンテキストテンプレートに含まれる
        トランザクションリストを消さないようにするために使用される
        """
        return {event:transaction[:] for event, transaction in context.items()}
    
    def validate(self, state):
        """Sort and move to end items with key which includes `*?[]`"""
        context = self[state]
        ast = []
        bra = []
        for event in list(context): #? OrderedDict mutated during iteration
            if re.search(r"\[.+\]", event):
                bra.append((event, context.pop(event))) # event key has '[]'
            elif '*' in event or '?' in event:
                ast.append((event, context.pop(event))) # event key has '*?'
        
        temp = sorted(context.items()) # normal event key
        context.clear()
        context.update(temp)
        context.update(sorted(bra, reverse=1))
        context.update(sorted(ast, reverse=1, key=lambda v:len(v[0])))
    
    def update(self, contexts):
        """Update each context or Add new contexts"""
        for k,v in contexts.items():
            if k in self:
                self[k].update(self.duplicate(v))
            else:
                self[k] = SSM(self.duplicate(v)) # new context
            self.validate(k)
    
    def append(self, contexts):
        """Append new contexts"""
        for k,v in contexts.items():
            if k in self:
                for event, transaction in v.items():
                    if event not in self[k]:
                        self[k][event] = transaction[:] # copy the event:transaction
                        continue
                    for act in transaction[1:]:
                        self.bind(event, act, k, transaction[0])
            else:
                self[k] = SSM(self.duplicate(v)) # new context
            self.validate(k)
    
    def remove(self, contexts):
        """Remove old contexts"""
        for k,v in contexts.items():
            if k in self:
                for event, transaction in v.items():
                    if self[k].get(event) == transaction: # remove the event:transaction
                        self[k].pop(event)
                        continue
                    for act in transaction[1:]:
                        self.unbind(event, act, k)
    
    def hook(self, event, action=None, state=None):
        if not action:
            return lambda f: self.hook(event, f, state)
        
        def _hook(*args, **kwargs):
            action(*args, **kwargs)
            self.unbind(event, _hook) # release hook once called,
        
        return self.bind(event, _hook)
    
    def bind(self, event, action=None, state=None, state2=None):
        """Append a transaction to the context
        equiv. self[state] += {event : [state2, action]}
        
        The transaction is exepcted to be a list (not a tuple).
        If no action, it creates only the transition and returns @decor(binder).
        """
        warn = self.log
        
        if state not in self:
            warn("- FSM:warning - [{!r}] context newly created.".format(state))
            self[state] = SSM() # new context
        
        context = self[state]
        if state2 is None:
            state2 = state
        
        if event in context:
            if state2 != context[event][0]:
                warn("- FSM:warning - transaction may conflict"
                     " (state {2!r} and the original state is not the same)"
                     " {0!r} : {1!r} --> {2!r}".format(event, state, state2))
                pass
                context[event][0] = state2 # update transition
        else:
            ## if state2 not in self:
            ##     warn("- FSM:warning - transaction may contradict"
            ##          " (state {2!r} is not found in the contexts)"
            ##          " {0!r} : {1!r} --> {2!r}".format(event, state, state2))
            ##     pass
            context[event] = [state2] # new event:transaction
        
        transaction = context[event]
        if action is None:
            return lambda f: self.bind(event, f, state, state2)
        if not callable(action):
            raise TypeError("{!r} is not callable".format(action))
        if action not in transaction:
            try:
                transaction.append(action)
            except AttributeError:
                warn("- FSM:warning - appending action to context ({!r} : {!r})\n"
                     "  The transaction must be a list, not a tuple".format(state, event))
        return action
    
    def unbind(self, event, action=None, state=None):
        """Remove a transaction from the context
        equiv. self[state] -= {event : [*, action]}
        
        The transaction is exepcted to be a list (not a tuple).
        If no action, it will remove the transaction from the context.
        """
        warn = self.log
        
        if state not in self:
            warn("- FSM:warning - [{!r}] context does not exist.".format(state))
            return
        
        context = self[state]
        if event not in context:
            warn("- FSM:warning - No such transaction ({!r} : {!r})".format(state, event))
            return
        
        transaction = context[event]
        if action is None:
            del context[event]
            return True
        if not callable(action):
            raise TypeError("{!r} is not callable".format(action))
        if action in transaction:
            try:
                transaction.remove(action)
                if not any(callable(x) for x in transaction):
                    del context[event]
                return True
            except AttributeError:
                warn("- FSM:warning - removing action from context ({!r} : {!r})\n"
                     "  The transaction must be a list, not a tuple".format(state, event))
        return False


class TreeList(object):
    def __init__(self, ls=None):
        self.__items = ls or []
    
    def __getattr__(self, attr):
        return getattr(self.__items, attr)
    
    def __contains__(self, k):
        return self.getf(self.__items, k)
    
    def __iter__(self):
        return self.__items.__iter__()
    
    def __getitem__(self, k):
        if isinstance(k, string_types):
            return self.getf(self.__items, k)
        return self.__items.__getitem__(k)
    
    def __setitem__(self, k, v):
        if isinstance(k, string_types):
            return self.setf(self.__items, k, v)
        return self.__items.__setitem__(k, v)
    
    def __delitem__(self, k):
        if isinstance(k, string_types):
            return self.delf(self.__items, k)
        return self.__items.__delitem__(k)
    
    def tree(self, k):
        def _find(ls, key):
            if '/' in key:
                a, b = key.split('/', 1)
                la = _find(ls, a)
                if la is not None:
                    lb = next((x for x in la if isinstance(x, (tuple, list))), None)
                    if lb is not None:
                        return _find(lb, b)
                return None
            return next((x for x in ls if x and x[0] == key), None)
        return _find(self.__items, k)
    
    @classmethod
    def getf(self, ls, key):
        if '/' in key:
            a, b = key.split('/', 1)
            la = self.getf(ls, a)
            if la is not None:
                return self.getf(la, b)
            return None
        return next((x[-1] for x in ls if x and x[0] == key), None)
    
    @classmethod
    def setf(self, ls, key, value):
        if '/' in key:
            a, b = key.split('/', 1)
            la = self.getf(ls, a)
            if la is not None:
                return self.setf(la, b, value)
            p, key = key.rsplit('/', 1)
            return self.setf(ls, p, [[key, value]]) # >>> ls[p].append([key, value])
        try:
            li = next((x for x in ls if x and x[0] == key), None)
            if li is not None:
                if isinstance(value, list):
                    li[-1][:] = value # assign value:list to items:list
                else:
                    li[-1] = value # assign value to item (li must be a list)
            else:
                ls.append([key, value]) # append to items:list
        except (TypeError, AttributeError) as e:
            print("- TreeList:warning {!r}: key={!r}".format(e, key))
    
    @classmethod
    def delf(self, ls, key):
        if '/' in key:
            p, key = key.rsplit('/', 1)
            ls = self.getf(ls, p)
        ls.remove(next(x for x in ls if x and x[0] == key))


def funcall(f, *args, doc=None, alias=None, **kwargs): # PY3
    """Decorator as curried function
    
    event 引数などが省略できるかどうかチェックし，
    省略できる場合 (kwargs で必要な引数が与えられる場合) その関数を返す．
    Check if the event argument etc. can be omitted,
    If it can be omitted (if required arguments are given by kwargs),
    return the decorated function.
    
    retval-> (lambda *v: f`alias<doc:str>(*v, *args, **kwargs))
    """
    assert isinstance(doc, (string_types, type(None)))
    assert isinstance(alias, (string_types, type(None)))
    
    @wraps(f)
    def _Act(*v):
        return f(*(args + v), **kwargs)
    action = _Act
    
    def explicit_args(argv, defaults):
        ## 明示的に与えなければならない引数の数を数える
        ## defaults と kwargs はかぶることがあるので，次のようにする
        n = len(args) + len(defaults or ())
        rest = argv[:-n] if n else argv # explicit, non-default argv that must be given
        k = len(rest)                   # if k > 0: kwargs must give the rest of args
        for kw in kwargs:
            if kw not in argv:
                raise TypeError("{} got an unexpected keyword {!r}".format(f, kw))
            if kw in rest:
                k -= 1
        return k
    
    if not inspect.isbuiltin(f):
        try:
            argv, _varargs, _keywords, defaults,\
              _kwonlyargs, _kwonlydefaults, _annotations = inspect.getfullargspec(f) # PY3
        except AttributeError:
            argv, _varargs, _keywords, defaults = inspect.getargspec(f) # PY2
        
        k = explicit_args(argv, defaults)
        if k == 0 or inspect.ismethod(f) and k == 1: # 暗黙の引数 'self' は除く
            @wraps(f)
            def _Act2(*v):
                return f(*args, **kwargs) # function with no explicit args
            action = _Act2
            action.__name__ += str("~")
    else:
        ## Builtin functions don't have an argspec that we can get.
        ## Try alalyzing the doc:str to get argspec info.
        ## 
        ## Wx buitl-in method doc is written in the following style:
        ## ```name(argspec) -> retval
        ## 
        ## ...(details)...
        ## ```
        docs = [ln for ln in inspect.getdoc(f).splitlines() if ln]
        m = re.search(r"(\w+)\((.*)\)", docs[0])
        if m:
            name, argspec = m.groups()
            argv = [x for x in argspec.strip().split(',') if x]
            defaults = re.findall(r"\w+\s*=(\w+)", argspec)
            k = explicit_args(argv, defaults)
            if k == 0:
                @wraps(f)
                def _Act3(*v):
                    return f(*args, **kwargs) # function with no explicit args
                action = _Act3
                action.__name__ += str("~~")
                if len(docs) > 1:
                    action.__doc__ = '\n'.join(docs[1:])
    
    if alias:
        action.__name__ = str(alias)
    if doc:
        action.__doc__ = doc
    return action
