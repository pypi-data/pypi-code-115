import time


class ADTkClock(Exception):
    __module__ = Exception.__module__


class DigitalClock:
    """
    valid parameter ::--
    tk_widget -- label, or another widget support text parameter
    time_format -- same as time.strftime
    """
    def __init__(self, tk_widget, time_format="%I:%M:%S"):
        tk_widget.config(text=time.strftime(time_format))
        tk_widget.after(200, self.__init__, tk_widget, time_format)


class Timer:
    """
    valid parameter ::--
      year, month, week, day, hour, minute, second

    """
    _value = ("year", 'month', "week", "day", "hour", "minute", "second")

    def __init__(self, tk_widget, **kwargs):
        self._sec = 0
        self.time_over = False
        if self._check(**kwargs) and not self.time_over:
            for i in kwargs:
                if i == "year":
                    val = kwargs[i]
                    self._sec += val * 31556952
                elif i == "month":
                    val = kwargs[i]
                    self._sec += val * 2628000
                elif i == "week":
                    val = kwargs[i]
                    self._sec += val * 604800
                elif i == "day":
                    val = kwargs[i]
                    self._sec += val * 86400
                elif i == "hour":
                    val = kwargs[i]
                    self._sec += val * 3600
                elif i == "minute":
                    val = kwargs[i]
                    self._sec += val * 60
                elif i == "second":
                    val = kwargs[i]
                    self._sec += val * 1
            self._time_it(tk_widget, self._sec)
        else:
            raise ADTkClock(f"kwargs must be {self._value}")

    def _time_it(self, tk_widget, sec):
        _ = sec

        year = sec // 31556952
        sec -= year * 31556952

        month = sec // 2628000
        sec -= month * 2628000

        week = sec // 604800
        sec -= week * 604800

        day = sec // 86400
        sec -= day * 86400

        hour = sec // 3600
        sec -= hour * 3600

        minute = sec // 60
        sec -= minute * 60

        second = sec // 1
        get = f"{year}:{month}:{week}:{day}:{hour}:{minute}:{second}"
        if _ >= 0 and not self.time_over:
            tk_widget['text'] = get
            tk_widget.update()
            tk_widget.after(1000, self._time_it, tk_widget, _ - 1)
        else:
            self.time_over = True

    def _check(self, **kwargs):
        ch = []
        for i in kwargs:
            if i in self._value:
                ch.append(True)
            else:
                ch.append(False)
                break
        return all(ch)


class StopWatch:
    """
        valid parameter ::--
        tk_widget -- label, or another widget support text parameter
    """
    def __init__(self, tk_widget):
        self._tk_widget = tk_widget
        self._second = 0
        self._minute = 0
        self._hour = 0
        self._run = True

    def start(self):
        if self._run:
            self._tk_widget["text"] = self.time_text()
            if self._second == 59:
                self._minute += 1
                self._second -= 60
            if self._minute == 59:
                self._hour += 1
                self._minute -= 60
            self._second += 1
            self._tk_widget.after(1000, self.start)

    def pause(self):
        self._run = False

    def stop(self):
        self._run = False
        self._second = 0
        self._minute = 0
        self._hour = 0

    def time_text(self):
        _time = f"{self._hour}:{self._minute}:{self._second}"
        return _time

    def get_time(self):
        return self._hour, self._minute, self._second


print("---:: ADtkclock ::---")
if __name__ == '__main__':
    from tkinter import Tk, Label, Toplevel

    r1 = Tk()

    l1 = Label(r1)
    l1.pack()
    
    r2 = Toplevel(r1)
    l2 = Label(r2)
    l2.pack()

    r3 = Toplevel(r1)
    l3 = Label(r3)
    l3.pack()

    # Digital clock
    DigitalClock(l1)

    # Timer
    Timer(l2, second=10, minute=0)

    # Stop Clock
    StopWatch(l3).start()

    r1.mainloop()
