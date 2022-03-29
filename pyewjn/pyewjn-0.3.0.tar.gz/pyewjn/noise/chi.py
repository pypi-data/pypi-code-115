from typing import Callable

import numpy as np
import scipy.integrate

import pyewjn.noise.im_ref


def get_chi_zz_e(eps: Callable[[float], complex]) -> Callable[[float], float]:
	im_ref_p = pyewjn.noise.im_ref.get_im_ref_p(eps)

	def chi_zz_e(z: float) -> float:
		def integrand(y: float) -> float:
			return (y**2) * im_ref_p(y / z) * np.exp(-2 * y)

		integral = scipy.integrate.quad(
			integrand, 0, np.inf, epsabs=1e-10, epsrel=1e-10
		)
		return integral[0] / (z**3)

	return chi_zz_e
