import numpy as np
from pyewjn.baskets import CalculationConstants, CalculationParams

LINDHARD_SERIES_THRESHOLD = 1e4


class LindhardDielectric(object):
	def __init__(
		self,
		params: CalculationParams,
		constants: CalculationConstants = CalculationConstants(),
		thres=LINDHARD_SERIES_THRESHOLD,
	):
		if params.omega is None:
			raise ValueError("omega expected to not be None")
		if params.v_f is None:
			raise ValueError("v_f expected to not be None")
		if params.omega_p is None:
			raise ValueError("omega_p expected to not be None")
		if params.tau is None:
			raise ValueError("tau expected to not be None")

		self.series_threshold = thres
		self.omega = params.omega
		self.v_f = params.v_f
		self.omega_p = params.omega_p
		self.tau = params.tau
		self.c_light = constants.c_light

		self.s = 1 / (self.tau * self.omega)
		self.prefactor = 3 * (self.omega_p**2) / (self.omega**2)

	def get_eps(self):
		def eps_lindhard(u_inverse_wavelength: float) -> complex:
			"""the lindhard dielectric function

			:param u_inverse_wavelength: u is in units of the reciprocal vacuum wavelength (omega / c_light)
			:return: returns the value of epsilon, dimensionless
			"""

			# converts u from inverse vacuum wavelength to inverse mean free path
			u = u_inverse_wavelength * self.v_f / self.c_light

			if u < LINDHARD_SERIES_THRESHOLD * self.v_f / self.omega:
				return eps_series(u)
			else:
				return eps_full_lindhard(u)

		def eps_series(u: float) -> complex:
			rel_value = (1j / (3 * (self.s - 1j))) + (
				u**2 * ((-9j + 5 * self.s) / (45 * (-1j + self.s) ** 3))
			)

			return 1 + (self.prefactor * rel_value)

		def eps_full_lindhard(u: float) -> complex:

			log_value = np.log((1 - u + (self.s * 1j)) / (1 + u + (self.s * 1j)))

			rel_value = (1 + ((1 + (self.s * 1j)) / (2 * u)) * log_value) / (
				1 + ((self.s * 1j) / (2 * u)) * log_value
			)

			return 1 + (self.prefactor / (u**2)) * rel_value

		return eps_lindhard


def get_lindhard_dielectric(
	params: CalculationParams, constants: CalculationConstants = CalculationConstants()
):
	return LindhardDielectric(params, constants).get_eps()
