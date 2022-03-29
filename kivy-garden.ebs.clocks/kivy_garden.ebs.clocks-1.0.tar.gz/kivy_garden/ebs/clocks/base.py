

from kivy.clock import Clock


class ClockBase(object):
    def __init__(self):
        self._update_task = None
        super(ClockBase, self).__init__()

    def update(self):
        raise NotImplementedError

    def start(self):
        self._update_task = Clock.schedule_interval(self.step, 1)

    def step(self, *_):
        self.update()

    def stop(self):
        if self._update_task:
            self._update_task.cancel()
            self._update_task = None
