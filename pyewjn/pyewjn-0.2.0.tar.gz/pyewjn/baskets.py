class CalculationConstants(object):
	"""Holds physical constants, in SI units"""

	def __init__(
		self,
		epsilon_0=8.854e-12,
		h_bar=1.0546e-34,
		c_light=3e8,
		electron_mass=9.10938356e-31,
	):
		"""Initialises constants in SI units, with sensible defaults

		:param epsilon_0:
		:param h_bar:
		:param c_light:
		:param electron_mass:
		"""

		self.epsilon_0 = epsilon_0
		self.h_bar = h_bar
		self.c_light = c_light
		self.electron_mass = electron_mass


class CalculationParams(object):
	"""Holds the parameters describing a calculation, in SI units."""

	def __init__(
		self,
		omega: float = None,
		omega_p: float = None,
		tau: float = None,
		v_f: float = None,
		t_rel: float = None,
		t_c: float = None,
		dipole_moment: float = None,
	):
		"""Creates parameter object, SI units

		:param omega:
		:param omega_p:
		:param tau:
		:param v_f:
		:param t_rel:
		:param t_c:
		:param dipole_moment:
		"""

		self.omega = omega
		self.omega_p = omega_p
		self.tau = tau
		self.v_f = v_f
		self.t_rel = t_rel
		self.t_c = t_c
		self.dipole_moment = dipole_moment
