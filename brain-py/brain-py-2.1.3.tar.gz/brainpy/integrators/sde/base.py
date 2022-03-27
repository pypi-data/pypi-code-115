# -*- coding: utf-8 -*-

import abc

from brainpy import math, errors
from brainpy.integrators import constants, utils
from brainpy.integrators.base import Integrator
from brainpy.tools.checking import check_float

__all__ = [
  'SDEIntegrator',
]


def f_names(f):
  func_name = constants.unique_name('sde')
  if f.__name__.isidentifier():
    func_name += '_' + f.__name__
  return func_name


class SDEIntegrator(Integrator):
  """SDE Integrator."""

  def __init__(self, f, g, dt=None, name=None, show_code=False,
               var_type=None, intg_type=None, wiener_type=None):

    dt = math.get_dt() if dt is None else dt
    parses = utils.get_args(f)
    variables = parses[0]  # variable names, (before 't')
    parameters = parses[1]  # parameter names, (after 't')
    arguments = parses[2]  # function arguments

    # super initialization
    super(SDEIntegrator, self).__init__(name=name,
                                        variables=variables,
                                        parameters=parameters,
                                        arguments=arguments,
                                        dt=dt)

    # derivative functions
    self.derivative = {constants.F: f, constants.G: g}
    self.f = f
    self.g = g

    # essential parameters
    intg_type = constants.ITO_SDE if intg_type is None else intg_type
    var_type = constants.SCALAR_VAR if var_type is None else var_type
    wiener_type = constants.SCALAR_WIENER if wiener_type is None else wiener_type
    if intg_type not in constants.SUPPORTED_INTG_TYPE:
      raise errors.IntegratorError(f'Currently, BrainPy only support SDE_INT types: '
                                   f'{constants.SUPPORTED_INTG_TYPE}. But we got {intg_type}.')
    if var_type not in constants.SUPPORTED_VAR_TYPE:
      raise errors.IntegratorError(f'Currently, BrainPy only supports variable types: '
                                   f'{constants.SUPPORTED_VAR_TYPE}. But we got {var_type}.')
    if wiener_type not in constants.SUPPORTED_WIENER_TYPE:
      raise errors.IntegratorError(f'Currently, BrainPy only supports Wiener '
                                   f'Process types: {constants.SUPPORTED_WIENER_TYPE}. '
                                   f'But we got {wiener_type}.')
    self.var_type = var_type  # variable type
    self.intg_type = intg_type  # integral type
    self.wiener_type = wiener_type # wiener process type

    # random seed
    self.rng = math.random.RandomState()

    # code scope
    self.code_scope = {constants.F: f, constants.G: g, 'math': math, 'random': self.rng}

    # code lines
    self.func_name = f_names(f)
    self.code_lines = [f'def {self.func_name}({", ".join(self.arguments)}):']

    # others
    self.show_code = show_code

  @abc.abstractmethod
  def build(self):
    raise NotImplementedError('Must implement how to build your step function.')
