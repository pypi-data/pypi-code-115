from string import ascii_lowercase
import numpy as np
import crypton.affine as affine
import crypton.block as block


def affiner():
	encrypt, decrypt = affine.get_cryption_functions(a=3, b=5, space=ascii_lowercase)

	print("Affine", encrypt("batuhan"), decrypt(encrypt("batuhan")))


def blocker():
	space = ascii_lowercase
	a = np.array([[2, 3], [3, 5]])
	b = np.array([[13], [10]])

	encrypt, decrypt = block.get_cryption_functions(a=a, b=b, space=space)

	print("Block", encrypt("sefa"), decrypt(encrypt("sefa")))


affiner()
blocker()
