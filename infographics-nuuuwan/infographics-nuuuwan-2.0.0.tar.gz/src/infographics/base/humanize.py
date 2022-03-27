import math

METRIC_PREFIX_LIST = ['', 'K', 'M', 'B', 'T', 'P', 'E', 'Z', 'Y']


def number(f):
    log10f = math.log10(f)
    i = (int)(log10f / 3)
    prefix = METRIC_PREFIX_LIST[i]

    a = 10 ** ((int)(log10f) - 1)
    fa = round(f / a, 0) * a

    b = 10 ** (3 * i)
    fb = fa / b

    c = 0 if ((int)(log10f) % 3) else 1
    return ('{fb:.%df}{prefix}' % (c)).format(fb=fb, prefix=prefix)


def percent(p):
    for n_decimals in range(0, 3):
        p_limit = 0.1 ** (1 + n_decimals)
        if p > p_limit:
            format_str = '{p:.%d%%}' % (n_decimals)
            return format_str.format(p=p)
    return '<0.1%'
