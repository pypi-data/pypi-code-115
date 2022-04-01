
from fnmatch import fnmatch

import numpy as np
import scipy.constants

N_A = scipy.constants.N_A
R = scipy.constants.R

p0 = scipy.constants.physical_constants['standard atmosphere'][0] # pressure, units: Pa
T0 =  288.15                                                      # temperature, units: K

METRIC_PREFIXES = {
    'Y':  1e24, # yotta
    'Z':  1e21, # zetta
    'E':  1e18, # exa
    'P':  1e15, # peta
    'T':  1e12, # tera
    'G':  1e9,  # giga
    'M':  1e6,  # mega
    'k':  1e3,  # kilo
    'h':  1e2,  # hecto
    'da': 1e1,  # deca
    '':   1e0,
    'd':  1e-1, # deci
    'c':  1e-2, # centi
    'm':  1e-3, # milli
    'u':  1e-6, # micro
    'µ':  1e-6, # micro (again)
    'n':  1e-9, # nano
    'p':  1e-12, # pico
    'f':  1e-15, # femto
    'a':  1e-18, # atto
    'z':  1e-21, # zepto
    'y':  1e-24, # yocto
}


# molar mass (kg/m3)
M = {
    'air': 28.97e-3,  # dry air
    'CO':  28.01e-3,
    'CO2': 44.01e-3,
    '14CO2': 45.99307e-3,
    'H2O': 18.01528e-3,
    'NO2': 46.0055e-3,
    'NO':  30.01e-3,
    'O3':  48.00e-3,
    'SO2': 64.066e-3,
    'CH4': 16.0425e-3,
}



def _unit2quantity(unit):
    """
    Get quantitity from unit and conversion factor to convert unit
    to SI units.

    Quantities (point | column):
        xM: mole/molar fraction  | column-averaged dry air mole fraction
        xV: volume mixing ratios | column-averaged dry air volume mixing ratio
        xm: mass mixing ratios   | column-averaged dry air mass mixing ratio
        cM: molar concentration  | molar column density
        cn: number density       | number column density
        cm: mass concentration   | mass column density
    """
    unit = unit.strip()

    quantity = None
    conv = 1.0

    if ' ' in unit or '/' in unit:

        # split in numerator and denominator
        if '/' in unit:
            n, d = unit.split('/')
        else:
            n, d = unit.split()

        # remove whitespace
        n = n.strip()
        d = d.strip()

        # remove "-" and "1"
        d = d.replace('-', '')
        d = d.replace('1', '')

        # molar or mass concentration or volume mixing ratio
        if d.endswith('m3') or d.endswith('m2'):

            conv /= METRIC_PREFIXES[d[:-2]]**int(d[-1])

            if n.endswith('mol'):
                quantity = 'cM'
                conv *= METRIC_PREFIXES[n[:-3]]

            elif n.endswith('g'):
                quantity = 'cm'
                conv *= 1e-3 * METRIC_PREFIXES[n[:-1]]

            elif n.endswith('m3'):
                quantity = 'xV'
                conv *= METRIC_PREFIXES[n[:-2]]


        # mass mixing ratio
        elif n.endswith('g') and d.endswith('g'):
            quantity = 'xm'
            conv *= 1e-3 * METRIC_PREFIXES[n[:-1]]
            conv /= 1e-3 * METRIC_PREFIXES[d[:-1]]

        # molar fraction
        elif n.endswith('mol') and d.endswith('mol'):
            quantity = 'xM'
            conv *= METRIC_PREFIXES[n[:-3]]
            conv /= METRIC_PREFIXES[d[:-3]]

    else:
        # molar fraction
        if fnmatch(unit, 'pp?v'):
            quantity = 'xM'
            conv *= {'m': 1e-6, 'b': 1e-9, 't': 1e-12}[unit[2]]

        # mass mixing ratio
        elif fnmatch(unit, 'pp?m'):
            quantity = 'xm'
            conv *= {'m': 1e-6, 'b': 1e-9, 't': 1e-12}[unit[2]]

        # number density
        elif unit.endswith('m-3'):
            quantity = 'cn'
            conv /= METRIC_PREFIXES[unit[:-3]]**3

        elif unit.endswith('m-2'):
            quantity = 'cn'
            conv /= METRIC_PREFIXES[unit[:-3]]**2

    if quantity is None:
        raise ValueError('Failed to parse unit "%s"' % unit)

    return quantity, conv



def convert_points(x, from_, to, molar_mass=None, p=p0, T=T0):
    """
    Convert between mole fractions, mixing rations and different
    concentrations.

    The library is still work in progress. Please check if your results
    reasonable and let us know, if you find a bug.

    Parameters:
        x:          value that needs to be converted (numerical)
        from_:      unit of `x` (e.g. "mol mol-1", "ug/m3", ...)
        to:         unit to which `x` will be converted.
        molar_mass: name or molar mass value of gas
    """
    x = np.asarray(x)

    from_, from_conversion = _unit2quantity(from_)
    to, to_conversion = _unit2quantity(to)


    if isinstance(molar_mass, str):
        Mi = M[molar_mass]
    else:
        Mi = molar_mass

    if Mi is None and ((from_ in ['xm', 'cm'] and to not in ['xm', 'cm'])
                       or (from_ not in ['xm', 'cm'] and to in ['xm', 'cm'])):
        raise ValueError('Need molar mass to convert %s to %s but M is "%s"' %
                         (from_, to, Mi))

    # convert to molar fraction (in mol mol-1)
    if from_ in ['xM', 'xV']:
        pass
    elif from_ == 'xm':
        x = x * M['air'] / Mi
    elif from_ == 'cM':
        x = x * R * T / p
    elif from_ == 'cn':
        x = x / N_A * R * T / p
    elif from_ == 'cm':
        x = x / Mi * R * T / p
    else:
        raise ValueError('Cannot convert from "%s"' % from_)

    # convert mole fraction to output unit
    if to in ['xM', 'xV']:
        pass
    elif to == 'xm':
        x = x * Mi / M['air']
    elif to == 'cM':
        x = x * p / (R * T)
    elif to == 'cn':
        x = x * N_A * p / (R * T)
    elif to == 'cm':
        x = x * Mi * p / (R * T)
    else:
        raise ValueError('Cannot convert to "%s"' % to)

    return x * from_conversion / to_conversion



def convert_columns(x, from_, to, molar_mass=None, p=p0):
    """
    Convert between vertical column densities and column-averaged
    dry air mole fractions.

    The library is still work in progress. Please check if your results
    reasonable and let us know, if you find a bug.

    Parameters:
        x:          value that needs to be converted (numerical)
        from_:      unit of `x` (e.g. "mol mol-1", "ug/m3", ...)
        to:         unit to which `x` will be converted.
        molar_mass: name or molar mass value of gas
        p:          surface pressure (in Pa)
    """
    x = np.asarray(x)

    from_, from_conversion = _unit2quantity(from_)
    to, to_conversion = _unit2quantity(to)

    # molar mass
    if isinstance(molar_mass, str):
        Mi = M[molar_mass]
    else:
        Mi = molar_mass

    if Mi is None and ((from_ in ['xm', 'cm'] and to not in ['xm', 'cm'])
                       or (from_ not in ['xm', 'cm'] and to in ['xm', 'cm'])):
        raise ValueError('Need molar mass to convert %s to %s but M is "%s"' %
                         (from_, to, Mi))

    air_column = surface_pressure_to_airnumber(p)

    # convert to column density (in mol m-2)
    if from_ == 'cM':
        pass
    elif from_ == 'cn':
        x = x / N_A
    elif from_ == 'cm':
        x = x / Mi
    elif from_ == 'xM':
        x = x * air_column
    elif from_ == 'xn':
        x = x * air_column / N_A
    elif from_ == 'xm':
        x = x * air_column / Mi

    # convert molar column density to output unit
    if to == 'cM':
        pass
    elif to == 'cn':
        x = x * N_A
    elif to == 'cm':
        x = x * Mi
    elif to == 'xM':
        x = x / air_column
    elif to == 'xn':
        x = x / air_column
    elif to == 'xm':
        x = x / air_column * Mi / M['air']

    return x * from_conversion / to_conversion





def surface_pressure_to_airnumber(p_surf):
    """ Convert surface pressure (Pa) to mol of air molecules (mol m-2). """

    from scipy.constants import g

    return p_surf / g / M['air']



