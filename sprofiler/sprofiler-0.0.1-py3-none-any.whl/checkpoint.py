import numpy as np


def format_elapsed(m, s, dec=1):
    if m >= 1.:
        return f'{m:.{dec}f} s \u00B1 {s:.{dec}f} s'
    elif m >= 1e-3:
        return f'{1e3 * m:.{dec}f} ms \u00B1 {1e3 * s:.{dec}f} ms'
    elif m >= 1e-6:
        return f'{1e6 * m:.{dec}f} us \u00B1 {1e6 * s:.{dec}f} us'
    else:
        return f'{1e9 * m:.{dec}f} ns \u00B1 {1e9 * s:.{dec}f} ns'


class Checkpoint(object):
    def __init__(self, name):
        """
        Create checkpoint to save times
        """
        self.name = name
        self.starts = []
        self.stops = []
        self.elapsed = []
        
    def _get_elapsed(self):
        self.elapsed = [y - x for (x, y) in zip(self.starts, self.stops)]
        
    def add_times(self, start, stop):
        self.starts.append(start)
        self.stops.append(stop)
        self.elapsed.append(stop - start)
    
    def report(self, dec=1):
        n_iter = len(self.elapsed)
        mean = np.mean(self.elapsed)
        std = np.std(self.elapsed)
        
        return (
            f'{self.name} | '
            f'{format_elapsed(mean, std, dec=dec)} per iteration, '
            f'n = {n_iter}'
        )
        
    def __str__(self):
        return self.summarize(dec=1)
    