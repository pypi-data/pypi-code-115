from .models import ValueLike, UnitLike
from .unit import Unit

class PhysicalMeasure(object):
    def __init__(self, value: ValueLike, units: UnitLike):
        if isinstance(units, str):
            self.__init_units = Unit(units)
        else:
            self.__init_units = units
        self.units = self.__init_units

        self.value = value
        self.__init_value = value

    def __call__(self, value: ValueLike, units: UnitLike):
        return self.__init__(value, units)

    @property
    def initial_units(self):
        return self.__init_units

    @property
    def initial_value(self):
        return self.__init_value


    def convert(self, to_units: UnitLike):
        if isinstance(to_units, str):
            to_units = Unit(to_units)

        simple_from = self.units.simplified
        simple_to = to_units.simplified

        if simple_from != simple_to:
            raise ValueError('Units {} can not be converted into {}.'.format(self.units.reduced_form, to_units.reduced_form))
        else:
            self.value = self.value * self.units.factor / to_units.factor
            self.units = to_units
        return self

    @property
    def get_value(self):
        return self.value
