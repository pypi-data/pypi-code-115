import pyewjn.util

from typing import Callable
import numpy as np

SMALL_X_BOUNDARY = 1e3


def get_zeta_p_integrand(
	eps: Callable[[float], complex]
) -> Callable[[float, float], complex]:
	"""Gets the integrand function zeta_p_integrand(u, y).

	Returns zeta_p_integrand(u, y), a complex valued function of two momenta in units of vacuum wavelength.

	:param eps:
	:return:
	"""

	def zeta_p_integrand(y: float, u: float) -> complex:
		"""
		Here y and u are in units of vacuum wavelength, coming from Ford-Weber / from the EWJN noise expressions.
		:param u:
		:param y:
		:return:
		"""
		u2 = u**2
		y2 = y**2
		k2 = u2 + y2
		k = np.sqrt(k2)
		eps_value = eps(k)
		term_1 = y2 / (eps_value - k2)
		term_2 = u2 / eps_value
		return (term_1 + term_2) / k2

	return zeta_p_integrand


def get_zeta_p_function(eps: Callable[[float], complex]):
	def integrand1_small_x(x: float, u: float) -> complex:
		u2 = u**2
		x2 = x**2
		eps_value = eps(u * np.sqrt(1 + x**2))
		return (x2 / (eps_value - 1 - x2)) / ((1 + x2) * u2)

	def integrand1_big_x(x: float, u: float) -> complex:
		u2 = u**2
		x2 = x**2
		eps_value = eps(u * x)
		return 1 / ((eps_value - x2) * u2)

	# 1 / (eps(u * sqrt(1 + x^2)))   * 1 / (1 + x^2)

	def integrand2_small_x(x: float, u: float) -> complex:
		x2 = x**2
		eps_value = eps(u * np.sqrt(1 + x**2))
		return 1 / (eps_value * (1 + x2))

	def integrand2_big_x(x: float, u: float) -> complex:
		x2 = x**2
		eps_value = eps(u * x)
		return 1 / (eps_value * x2)

	def zeta_p(u: float) -> complex:
		# zeta_p_integrand = get_zeta_p_integrand(eps)

		i1_small = pyewjn.util.complex_quad(
			lambda x: integrand1_small_x(x, u), 0, SMALL_X_BOUNDARY, epsabs=1e-12
		)
		i1_big = pyewjn.util.complex_quad(
			lambda x: integrand1_big_x(x, u), SMALL_X_BOUNDARY, np.inf, epsabs=1e-12
		)
		i2_small = pyewjn.util.complex_quad(
			lambda x: integrand2_small_x(x, u), 0, SMALL_X_BOUNDARY, epsabs=1e-12
		)
		i2_big = pyewjn.util.complex_quad(
			lambda x: integrand2_big_x(x, u), SMALL_X_BOUNDARY, np.inf, epsabs=1e-12
		)

		integral = sum(term[0] for term in [i1_small, i2_small, i1_big, i2_big])

		return integral * 2j * u

	return zeta_p
