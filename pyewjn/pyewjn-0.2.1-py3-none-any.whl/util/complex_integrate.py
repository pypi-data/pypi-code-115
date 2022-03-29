import numpy as np
from scipy.integrate import quad, quadrature


def complex_quad(func, a, b, **kwargs):
	'''
		Extends scipy.integrate for complex functions.
	'''
	def real_func(x):
		return np.real(func(x))

	def imag_func(x):
		return np.imag(func(x))

	real_integral = quad(real_func, a, b, **kwargs)
	imag_integral = quad(imag_func, a, b, **kwargs)

	return (
		real_integral[0] + 1j * imag_integral[0],
		real_integral[1:],
		imag_integral[1:],
	)


def complex_quadrature(func, a, b, **kwargs):
	def real_func(x):
		return np.real(func(x))

	def imag_func(x):
		return np.imag(func(x))

	real_integral = quadrature(real_func, a, b, **kwargs)
	imag_integral = quadrature(imag_func, a, b, **kwargs)

	return (
		real_integral[0] + 1j * imag_integral[0],
		real_integral[1:],
		imag_integral[1:],
	)
