import numpy as np
import pyewjn.dielectric.sigma_nam
import pyewjn.dielectric.low_k_nam

from pyewjn.baskets import CalculationParams, CalculationConstants

from typing import Tuple

FIXED_LARGE_MOMENTUM = 1e8


class DedimensionalisedParameters(object):
	def __init__(
		self,
		omega: float,
		sigma_n: float,
		tau: float,
		v_f: float,
		temp: float,
		critical_temp: float,
		c_light: float,
	):
		gap = 0
		if temp < critical_temp:
			# else, problems will happen
			gap = 3.06 * np.sqrt(critical_temp * (critical_temp - temp))
		self.xi = omega / gap
		self.nu = 1 / (tau * gap)
		self.t = temp / gap
		self.a = omega * v_f / (c_light * gap)
		self.b = sigma_n / omega


class NamDielectricCoefficients(object):
	def __init__(self, a: float, b: float, c: float, d: float):
		self.a = a
		self.b = b
		self.c = c
		self.d = d
		self.u_l = np.real((-self.c + 1j * self.d) / (-self.a + 1j * self.b))

	def eps(self, u_c: float):
		def piecewise_eps(u: float):
			# todo add check for u_c vs u_l
			if u < self.u_l:
				return -self.a + 1j * self.b
			elif self.u_l < u < u_c:
				return 1 + (-self.c + 1j * self.d) / u
			else:
				return 1

		return piecewise_eps


def get_dedimensionalised_parameters(
	omega: float,
	sigma_n: float,
	tau: float,
	v_f: float,
	temp: float,
	critical_temp: float,
	c_light: float,
) -> DedimensionalisedParameters:
	return DedimensionalisedParameters(
		omega, sigma_n, tau, v_f, temp, critical_temp, c_light
	)


def get_small_momentum_coefficients(
	dedim_params: DedimensionalisedParameters,
) -> Tuple[float, float]:
	prefactor = 4j * np.pi * dedim_params.b
	s = pyewjn.dielectric.low_k_nam.sigma_nam_alk(
		dedim_params.xi, 0, dedim_params.nu, dedim_params.t
	)
	conductivity = prefactor * s
	return -np.real(conductivity), np.imag(conductivity)


def get_big_momentum_coefficients(
	dedim_params: DedimensionalisedParameters,
) -> Tuple[float, float]:
	prefactor = 4j * np.pi * dedim_params.b * FIXED_LARGE_MOMENTUM / dedim_params.a
	s = pyewjn.dielectric.sigma_nam.sigma_nam(
		dedim_params.xi, FIXED_LARGE_MOMENTUM, dedim_params.nu, dedim_params.t
	)
	conductivity = prefactor * s
	return -np.real(conductivity), np.imag(conductivity)


def get_nam_dielectric_coefficients(
	omega: float,
	sigma_n: float,
	tau: float,
	v_f: float,
	temp: float,
	crit_temp: float,
	c_light: float,
) -> NamDielectricCoefficients:
	"""Gets a NamDielectricCoefficients object, using SI unit parameters

	:param omega: frequency
	:param sigma_n: normal state conductivity
	:param tau: tau in Hz
	:param v_f: Fermi velocity, in m/s
	:param temp: temperature in Hz
	:param crit_temp: critical temperature, in Hz
	:param c_light: speed of light, meters per second
	:return:
	"""

	dedim = get_dedimensionalised_parameters(
		omega, sigma_n, tau, v_f, temp, crit_temp, c_light
	)
	a, b = get_small_momentum_coefficients(dedim)
	c, d = get_big_momentum_coefficients(dedim)

	return NamDielectricCoefficients(a, b, c, d)


def get_nam_dielectric(
	u_c: float,
	params: CalculationParams,
	constants: CalculationConstants = CalculationConstants(),
):
	if params.omega is None:
		raise ValueError("omega expected to not be None")
	if params.v_f is None:
		raise ValueError("v_f expected to not be None")
	if params.omega_p is None:
		raise ValueError("omega_p expected to not be None")
	if params.tau is None:
		raise ValueError("tau expected to not be None")
	if params.t_rel is None:
		raise ValueError("relative temp expected to not be None")
	if params.t_c is None:
		raise ValueError("critical temp expected to not be None")
	sigma_n = params.omega_p**2 * params.tau / (4 * np.pi)
	coeffs = get_nam_dielectric_coefficients(
		params.omega,
		sigma_n,
		params.tau,
		params.v_f,
		params.t_rel * params.t_c,
		params.t_c,
		constants.c_light,
	)
	return coeffs.eps(u_c)
