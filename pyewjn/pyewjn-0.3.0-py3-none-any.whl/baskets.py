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
		omega: float,
		omega_p: float,
		tau: float,
		v_f: float,
		t_rel: float = 0.8,
		t_c: float = 1e11,
		dipole_moment: float = 1,
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

		if omega is None:
			raise ValueError("omega expected to not be None")
		if v_f is None:
			raise ValueError("v_f expected to not be None")
		if omega_p is None:
			raise ValueError("omega_p expected to not be None")
		if tau is None:
			raise ValueError("tau expected to not be None")
		if t_rel is None:
			raise ValueError("relative temp expected to not be None")
		if t_c is None:
			raise ValueError("critical temp expected to not be None")

		self.omega = omega
		self.omega_p = omega_p
		self.tau = tau
		self.v_f = v_f
		self.t_rel = t_rel
		self.t_c = t_c
		self.dipole_moment = dipole_moment
