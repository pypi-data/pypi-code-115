import seutils
import sys
from contextlib import contextmanager


class Implementation:

    def __init__(self):
        self._is_installed = None

    def is_installed(self):
        if self._is_installed is None:
            self._is_installed = self.check_is_installed()
        return self._is_installed

    def check_is_installed(self):
        raise NotImplementedError


class TTree:
    """
    Wrapper class for ttree-like objects.
    Aims to provide a uniform interface for ttree-like objects
    from various (up)root versions.
    """
    def __init__(self, name, tree):
        self.name = name
        self.tree = tree


@contextmanager
def open_uproot(path, mode='READ'):
    '''
    Does nothing if an open uproot object is passed
    '''
    do_open = seutils.is_string(path)
    try:
        yieldable = path
        if do_open:
            import uproot
            seutils.logger.debug('Opening %s with uproot', path)
            yieldable = uproot.open(path)
        yield yieldable
    finally:
        if do_open:
            try:
                yieldable.close()
            except Exception:
                pass


def is_node(f):
    """
    Checks whether the type of f is Directory-like
    """
    # This is not very robust but the route via isinstance was not working out.
    cls_name = repr(f)
    return cls_name.startswith('<ROOTDirectory') or cls_name.startswith('<ReadOnlyDirectory')


def is_ttree(f):
    cls_name = repr(f)
    return cls_name.startswith('<TTree')


def decode(s):
    """
    In python 3, returns a `str` object; in python 2, does nothing
    """
    if sys.version_info[0] >= 3 and isinstance(s, bytes):
        return s.decode()
    return s


def iter_contents(f, prefix='', seen=None, depth=0):
    """
    Starting from a node-like `f`, iterates and yields all contents.
    """
    # Keep a memo of seen memory addresses to avoid double counting
    if seen is None: seen = set()
    if id(f) in seen: return
    seen.add(id(f))

    is_nodelike = is_node(f)

    # Get a name for this node; Can be either the path (if nodelike) or the treename
    name = (decode(f.path[-1]) if len(f.path) else '') if is_nodelike else decode(f.name)
    name = prefix + '/' + name

    yield name, f

    if is_nodelike:
        for value in f.values():
            # `yield from` is python 3 only
            for _ in iter_contents(value, prefix=name, seen=seen, depth=depth+1):
                yield _


        
class UprootImplementation(Implementation):

    def check_is_installed(self):
        try:
            import uproot
            return True
        except ImportError:
            return False

    def ls(self, rootfile):
        with open_uproot(rootfile) as f:
            return list(iter_contents(f))






# def trees(rootfile):
#     with open_root(rootfile) as f:
#         return [ k.rsplit(';',1)[0] for k, v in sorted(f.items()) if repr(v).startswith('<TTree') ]




# def trees_and_counts(rootfile, branches=False):
#     r = []
#     with open_root(rootfile) as f:
#         for treename, tree in sorted(_iter_trees(f)):
#             treename = treename.rsplit(';',1)[0]
#             # Some uproot version incompatibilities
#             try:
#                 numentries = tree.num_entries
#             except AttributeError:
#                 numentries = tree.numentries
#             if branches:
#                 try:
#                     branches_ = [_make_str(b.name) for b in tree.branches]
#                 except AttributeError:
#                     branches_ = [_make_str(k) for k in tree.keys()]
#             r.append(
#                 (treename, numentries, branches_)
#                 if branches else (treename, numentries)
#                 )
#     return r


# def branches(rootfile, treepath=None):
#     with open_root(rootfile) as f:
#         if treepath is None:
#             treepath = seutils.root.select_most_likely_tree(trees(f))
#         tree = f[treepath]
#         for key in tree.keys(recursive=True):
#             value = tree[key]
#             yield (value, 1)

