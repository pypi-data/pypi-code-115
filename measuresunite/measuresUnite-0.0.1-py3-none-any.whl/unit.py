from .src.utils.process import process_unit, process_order, resolve_par, \
    unit_extend, listarize, factorize, factor_form, merger


class Unit(object):
    def __init__(self, unit: str):

        self._has_parenthesis = '(' in unit
        if self._has_parenthesis:
            unit = resolve_par(unit)
            unit = unit.replace('^1.0', '')
        self._is_fraction = len(unit.split('/'))>1
        self._is_product = len(unit.split('*'))>1
        self._is_powered = len(unit.split('^'))>1

        if self._is_fraction:
            self.numerator = Unit(unit.split('/')[0])
            self.denominator = Unit('/'.join(unit.split('/')[1:]))
        elif self._is_product:
            self.products = [Unit(item) for item in unit.split('*')]
        elif self._is_powered:
            self.unit = unit.split('^')[0]
            self.power = unit.split('^')[1]
        else:
            self.unit = unit

        self.factor = 1
        return

    def __call__(self, unit):
        return self.__init__(unit)

    @property
    def reduced_form(self) -> str:

        if self._is_fraction:
            return self.numerator.reduced_form + '/' + self.denominator.reduced_form
        elif self._is_product:
            return '*'.join([item.reduced_form for item in self.products])
        elif self._is_powered:
            return process_unit(self.unit) + '^' + self.power
        else:
            reduce = process_unit(self.unit)
            reduce = process_order(reduce)
            return reduce

    @property
    def simplified(self):
        unit = self.reduced_form
        extended = unit_extend(resolve_par(unit))
        lst = listarize(extended)
        nums, dens = factorize(lst)

        factor, nums, dens = factor_form(self.factor, nums, dens)
        self.factor = factor
        nums = merger(nums)
        dens = merger(dens)

        for i in range(len(nums)):
            for j in range(len(dens)):
                if nums[i][0] == dens[j][0]:
                    if nums[i][1] > dens[j][1]:
                        nums[i][1] = nums[i][1] - dens[j][1]
                        dens[j][1] = 0
                    else:
                        dens[j][1] = dens[j][1] - nums[i][1]
                        nums[i][1] = 0

        nums = sorted(nums, key=lambda x: x[0])
        dens = sorted(dens, key=lambda x: x[0])

        retval =  '(' + ''.join(item[0]+f'^{str(item[1])}*' for item in nums if item[1]>0)[:-1] \
               + ') / (' + \
               ''.join(item[0]+f'^{str(item[1])}*' for item in dens if item[1]>0)[:-1] + ')'

        if retval == '() / ()':
            return  'Unitless'
        elif '() /' in retval:
            return '1 / (' + ''.join(item[0]+f'^{str(item[1])}*' for item in dens if item[1]>0)[:-1] + ')'
        elif '/ ()' in retval:
            return ''.join(item[0]+f'^{str(item[1])}*' for item in nums if item[1]>0)[:-1]
        else:
            return retval