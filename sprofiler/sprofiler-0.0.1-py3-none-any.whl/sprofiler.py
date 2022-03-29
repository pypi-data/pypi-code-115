import time

from . import checkpoint
        

class Profiler(object):
    def __init__(self):
        self.profile_start = time.time()
        self.checkpoints = {}
        self.open_checkpoint_starts = {}
        
    def start(self, name=None):
        if name == None:
            name = 'Misc'
        if name in self.open_checkpoint_starts:
            raise RuntimeError(f'Open checkpoint named {name} already exists')
        
        start = time.time()
        self.open_checkpoint_starts[name] = start
        if name not in self.checkpoints:
            self.checkpoints[name] = checkpoint.Checkpoint(name)
        
    def stop(self, name=None):
        if name == None:
            name = list(self.open_checkpoint_starts.keys())[-1]
        elif name not in self.open_checkpoint_starts:
            raise KeyError(f'No open checkpoint named {name}')
        
        stop = time.time()
        start = self.open_checkpoint_starts.pop(name)
        self.checkpoints[name].add_times(start, stop)
        
        
    def end(self, name=None):
        self.stop(name=name)
        
    def remove(self, name=None):
        """
        Option to remove checkpoint start instead of completing a profiling
        set, for example on catching an error.
        """
        if name == None:
            name = list(self.open_checkpoint_starts.keys())[-1]
        elif name not in self.open_checkpoint_starts:
            raise KeyError(f'No open checkpoint named {name}')
        
        start = self.open_checkpoint_starts.pop(name)
        
    def clear_open(self):
        self.open_checkpoint_starts = {}
        
    def report(self, dec=1):
        for name in self.checkpoints:
            ckpt = self.checkpoints[name]
            print(ckpt.report(dec=dec))