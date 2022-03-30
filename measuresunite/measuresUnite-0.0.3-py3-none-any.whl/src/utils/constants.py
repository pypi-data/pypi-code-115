physical_constants = ['microorganisms', 'microorganism']

order_factors = {
    'yotta': 24,
    'zetta': 21,
    'exa': 18,
    'peta': 15,
    'terra': 12,
    'giga': 9,
    'mega': 6,
    'kilo': 3,
    'hecto': 2,
    'deca': 1,
    'deci': -1,
    'centi': -2,
    'milli': -3,
    'micro': -6,
    'nano': -9,
    'pico': -12,
    'femto': -15,
    'atto': -18,
    'zepto': -21,
    'yocto': -24,
}

extra_units = {
    'angstrom': ['metre',10**(-10)],
    'feet': ['metre',0.3048],
    'tones': ['gram', 10**6],
    'minute': ['second', 60],
    'hours': ['second', 3600],
    'liter': ['metre^3', 0.001]
}

derived_si = {
    'newton': 'kilogram*metre/second^2',
    'joule': 'kilogram*metre^2/second^2',
    'watt': 'kilogram*metre^2/second^3',
    'volt': 'kilogram*metre^2/second^3/ampere',
    'coulomb': 'ampere*s',
    'farad': 'second^4*ampere^2/metre^2/kilogram'
}



