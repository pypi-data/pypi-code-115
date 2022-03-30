from measuresUnite.src.utils.constants import *
from measuresUnite.src.unit_systems.si import si_dict
import numpy as np

def process_unit(unit: str):
    # unit = unit.lower()
    unit = unit.replace('metres', 'm')
    unit = unit.replace('metre', 'm')

    unit = unit.replace('seconds', 's')
    unit = unit.replace('second', 's')
    unit = unit.replace('secs', 's')
    unit = unit.replace('sec', 's')

    unit = unit.replace('pascals', 'Pa')
    unit = unit.replace('pascal', 'Pa')

    unit = unit.replace('minutes', 'min')
    unit = unit.replace('minute', 'min')

    unit = unit.replace('amperes', 'A')
    unit = unit.replace('ampere', 'A')

    unit = unit.replace('kelvins', 'K')
    unit = unit.replace('kelvin', 'K')

    unit = unit.replace('mols', 'mol')
    unit = unit.replace('moles', 'mol')
    unit = unit.replace('mol', 'mol')

    unit = unit.replace('grams', 'g')
    unit = unit.replace('gram', 'g')

    unit = unit.replace('angstroms', 'ang')
    unit = unit.replace('angstrom', 'ang')

    unit = unit.replace('litters', 'l')
    unit = unit.replace('litter', 'l')
    unit = unit.replace('liters', 'l')
    unit = unit.replace('liter', 'l')
    return unit

def process_order(unit: str):
    unit = unit.lower()
    unit = unit.replace('yotta', 'Y')
    unit = unit.replace('zetta', 'Z')
    unit = unit.replace('exa', 'E')
    unit = unit.replace('peta', 'P')
    unit = unit.replace('tera', 'T')
    unit = unit.replace('giga', 'G')
    unit = unit.replace('mega', 'M')
    unit = unit.replace('kilo', 'k')
    unit = unit.replace('hecto', 'h')
    unit = unit.replace('deca', 'da')
    unit = unit.replace('deci', 'd')
    unit = unit.replace('centi', 'c')
    unit = unit.replace('milli', 'm')
    unit = unit.replace('micro', 'u')
    unit = unit.replace('nano', 'n')
    unit = unit.replace('pico', 'p')
    unit = unit.replace('femto', 'f')
    unit = unit.replace('atto', 'a')
    unit = unit.replace('zepto', 'z')
    unit = unit.replace('yocto', 'y')
    return unit

def listarize(form):
    lst = []
    curr = ''
    for item in list(form):
        if item in '^*/':
            lst.append(curr)
            lst.append(item)
            curr = ''
        else:
            curr += item
    if curr != '':
        lst.append(curr)
    return lst

def unit_extend(unit_0):
    lst = []
    curr = ''
    for item in list(unit_0):
        if item in '^*/':
            lst.append(curr)
            lst.append(item)
            curr = ''
        else:
            curr += item
    if curr != '':
        lst.append(curr)

    new_lst = []
    for item in lst:
        if item.isnumeric() or item in '^*/':
            new_lst.append(item)
        else:
            try:
                new_lst.append(si_dict[item])
            except:
                new_lst.append(item)

    return ''.join(new_lst)


def factorize(lst):
    numerators = []
    denominators = []
    i = 0
    append_to_num = True
    while True:
        try:
            item = lst[i]
        except:
            break

        try:
            if lst[i + 1] == '^':
                item += ''.join(lst[i + 1:i + 3])
                i += 2
        except:
            if append_to_num:
                numerators.append(item)
            else:
                denominators.append(item)

            break
        else:
            if item not in '*/':
                if append_to_num:
                    numerators.append(item)
                else:
                    denominators.append(item)
            elif item == '*':
                append_to_num = True
            else:
                append_to_num = False
        i += 1

    return numerators, denominators


def factor_form(factor, numerators, denominators):
    rerun = False
    drop = []
    extend_num = []
    extend_den = []

    for i in range(len(numerators)):
        for key, value in order_factors.items():
            if key in numerators[i] and numerators[i] not in physical_constants:
                try:
                    power = float(numerators[i].split('^')[1])
                except:
                    power = 1.0
                factor *= (10 ** value) ** power
                numerators[i] = numerators[i].replace(key, '')

        if numerators[i].split('^')[0] in derived_si.keys():
            der = '({})^{}'.format(derived_si[numerators[i].split('^')[0]], numerators[i].split('^')[1])
            new_num, new_den = factorize(listarize(resolve_par(der)))
            drop.append(numerators[i])
            extend_num.extend(new_num)
            extend_den.extend(new_den)
            rerun = True

        if numerators[i].split('^')[0] in extra_units.keys():
            try:
                power = float(numerators[i].split('^')[1])
            except:
                power = 1.0
            factor *= extra_units[numerators[i]][1] ** power
            numerators[i] = extra_units[numerators[i]][0]
            rerun = True

    if rerun:
        for i in drop:
            del numerators[numerators.index(i)]
        numerators.extend(extend_num)
        denominators.extend(extend_den)
        return factor_form(factor, numerators, denominators)

    for i in range(len(denominators)):
        for key, value in order_factors.items():
            if key in denominators[i] and denominators[i] not in physical_constants:
                try:
                    power = float(denominators[i].split('^')[1])
                except:
                    power = 1.0
                factor /= (10 ** value) ** power
                denominators[i] = denominators[i].replace(key, '')

        if denominators[i].split('^')[0] in derived_si.keys():
            der = '({})^{}'.format(derived_si[denominators[i].split('^')[0]], denominators[i].split('^')[1])
            new_den, new_num = factorize(listarize(resolve_par(der)))
            drop.append(denominators[i])
            extend_num.extend(new_num)
            extend_den.extend(new_den)
            rerun = True

        if denominators[i] in extra_units.keys():
            try:
                power = float(denominators[i].split('^')[1])
            except:
                power = 1.0
            factor /= extra_units[denominators[i]][1] ** power
            denominators[i] = extra_units[denominators[i]][0]
            rerun = True

    if rerun:
        for i in drop:
            del denominators[denominators.index(i)]
        numerators.extend(extend_num)
        denominators.extend(extend_den)
        return factor_form(factor, numerators, denominators)

    return factor, numerators, denominators


def resolve_par(unit):
    if '(' in unit:

        unit = unit.replace(' ', '')

        start = unit.index('(')
        stop = unit.index(')')
        in_par = unit[start + 1:stop]

        lst = []
        curr = ''
        for item in list(in_par):
            if item in '^*/':
                lst.append(curr)
                lst.append(item)
                curr = ''
            else:
                curr += item
        if curr != '':
            lst.append(curr)

        try:
            if unit[stop + 1] == '^':
                to_pow_str = ''
                for item in list(unit[stop + 2:]):
                    if not item.isnumeric():
                        break
                    else:
                        to_pow_str += item
                try:
                    to_pow = float(to_pow_str)
                except:
                    to_pow = 1.0
            else:
                to_pow = 1.0
        except:
            to_pow = 1.0

        new_lst = []
        in_pow = ''
        prev_pow = False
        for item in lst:

            if item not in '*/^' and not item.isnumeric():

                new_lst.append(item)
            elif item in '*/':
                if prev_pow:
                    new_pow = str(float(in_pow) * to_pow)
                    new_lst.append(f'^{new_pow}')
                    in_pow = ''
                    prev_pow = False
                else:
                    new_lst.append(f'^{str(to_pow)}')
                new_lst.append(item)
            elif item == '^':
                prev_pow = True
            elif prev_pow:
                if item.isnumeric() or item == '-':
                    in_pow += item
            else:
                if prev_pow:
                    new_pow = str(float(in_pow) * to_pow)
                    new_lst.append(f'^{new_pow}')
                    new_lst.append(item)
                new_lst.append(item)

        if prev_pow:
            new_pow = str(float(in_pow) * to_pow)
            new_lst.append(f'^{new_pow}')
        else:
            new_lst.append(f'^{str(to_pow)}')

        new_par = ''.join(new_lst)

        if unit[start - 1] == '/':
            new_par = new_par.replace('/', 'star')
            new_par = new_par.replace('*', '/')
            new_par = new_par.replace('star', '*')

        try:
            if unit[stop + 1] == '^':
                return resolve_par(unit[:start] + new_par + unit[stop + 1:].replace(f'^{to_pow_str}', ''))
        except:
            pass
        return resolve_par(unit[:start] + new_par + unit[stop + 1:])
    else:
        return unit

def merger(lst):
    un_numers = list(np.unique([item.split('^')[0] if '^' in item else item for item in lst]))
    final_lst = []
    for un_item in un_numers:
        power = 0
        for item in lst:
            if item.split('^')[0] == un_item:
                try:
                    power += float(item.split('^')[1])
                except:
                    power += 1
        final_lst.append([un_item, power])
    return final_lst