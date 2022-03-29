from time import perf_counter_ns, perf_counter

def timer_ms(func):
    s = perf_counter()
    func
    e = perf_counter()
    return e-s

def timer_ns(func):
    s = perf_counter_ns()
    func
    e = perf_counter_ns()
    return e-s