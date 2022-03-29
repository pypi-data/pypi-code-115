from typing import Callable

import numpy as np

import pyewjn.noise.zeta


def get_im_ref_p(eps: Callable[[float], complex]) -> Callable[[float], float]:
	zeta_p = pyewjn.noise.zeta.get_zeta_p_function(eps)

	def im_ref_p(u: float) -> float:
		zeta_p_val = zeta_p(u)
		return np.imag((np.pi * 1j * u - zeta_p_val) / (np.pi * 1j * u + zeta_p_val))

	return im_ref_p
