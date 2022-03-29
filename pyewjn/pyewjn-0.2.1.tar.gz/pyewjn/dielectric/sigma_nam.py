import numpy as np
from numpy.lib.scimath import sqrt as csqrt

import pyewjn.util


def g(w, wp):
	return ((wp * (w + wp)) + 1) / (csqrt(wp**2 - 1) * csqrt((w + wp) ** 2 - 1))


def s(k, e, v):
	return (e - 1j * v) / k


def f(k, e, v):
	sv = s(k, e, v)
	logv = np.log(np.real_if_close((sv + 1) / (sv - 1)) + 0j)
	return (1 / k) * (2 * sv + ((1 - sv**2) * logv))


def i1(w, wp, k, v):
	gv = g(w, wp)
	e1 = csqrt((w + wp) ** 2 - 1)
	e2 = csqrt(wp**2 - 1)

	f_upper = f(k, np.real(e1 - e2), np.imag(e1 + e2) + 2 * v) * (gv + 1)
	f_lower = f(k, np.real(-e1 - e2), np.imag(e1 + e2) + 2 * v) * (gv - 1)

	return f_upper + f_lower


def i2(w, wp, k, v):
	gv = g(w, wp)
	e1 = csqrt((w + wp) ** 2 - 1)
	e2 = csqrt(wp**2 - 1)

	f_upper = f(k, np.real(e1 - e2), np.imag(e1 + e2) + 2 * v) * (gv + 1)
	f_lower = f(k, np.real(e1 + e2), np.imag(e1 + e2) + 2 * v) * (gv - 1)

	return f_upper + f_lower


def a(w, k, v, t):
	result = pyewjn.util.complex_quad(
		lambda wp: np.tanh((w + wp) / (2 * t)) * (i1(w, wp, k, v)),
		1 - w,
		1,
		epsabs=1e-10,
	)

	return result[0]


def b_int(wp, w, k, v, t):
	return (np.tanh((w + wp) / (2 * t)) * i1(w, wp, k, v)) - (
		np.tanh(wp / (2 * t)) * i2(w, wp, k, v)
	)


def b(w, k, v, t, b_max=np.inf):
	return pyewjn.util.complex_quad(lambda wp: b_int(wp, w, k, v, t), 1, b_max)[0]


def sigma_nam(w, k, v, t):
	return -1j * (3 / 4) * (v / w) * (-a(w, k, v, t) + b(w, k, v, t))
