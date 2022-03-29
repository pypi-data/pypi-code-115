from multiprocessing import Pool as ProcessPool
from multiprocessing.dummy import Pool as ThreadPool
from typing import Callable, Collection, Optional, Iterable

from alive_progress import alive_bar
from gevent.pool import Pool as GeventPool
from ringo_scanner.concurrency_mode import ConcurrencyMode


class Scanner:
    def __init__(self, proc: Callable, items: Collection, outfile: str = None, max_workers: Optional[int] = None,
                 mode: ConcurrencyMode = ConcurrencyMode.GEVENT):
        self.proc = proc
        self.items = items
        self.outfile = outfile
        self.max_workers = max_workers or mode.value
        self.mode = mode
        self.bar = None

    @property
    def proc(self) -> Callable:
        def func(*args, **kwargs):
            result = self._proc(*args, **kwargs)
            if self.bar:
                self.bar()
            return result

        return func

    @proc.setter
    def proc(self, value: Callable) -> None:
        self._proc = value

    @property
    def map(self) -> Callable[[Callable, Iterable], Iterable]:
        if self.mode == ConcurrencyMode.GEVENT:
            return GeventPool(self.max_workers).imap_unordered
        elif self.mode == ConcurrencyMode.THREADING:
            return ThreadPool(self.max_workers).imap_unordered
        elif self.mode == ConcurrencyMode.PROCESSING:
            return ProcessPool(self.max_workers).imap_unordered
        else:
            return map

    def execute(self) -> Iterable:
        with alive_bar(len(self.items)) as bar:
            self.bar = bar
            result = self.map(str, set(filter(bool, self.map(self.proc, self.items))))
        if self.outfile and len(self.outfile) > 0:
            with open(self.outfile, 'w') as f:
                f.writelines(result)
        return result
