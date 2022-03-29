import numpy as np
from pysampling.colvars.base import Colvar


class dZ(Colvar):
    """Collective variable class based on verticle difference : inherits directly from base class

    Parameters:
    atom1 (int): index of atom1 in array
    atom2 (int): index of atom2 in array
    colvardim (default colvardim=1)

    ----------------------------------------------------

    Methods:

    compute: returns collective variable and Jacobian
    compute_r: returns z distance between both atoms
    """

    def __init__(self, atom1, atom2):
        super().__init__(colvardim=1)
        self.atom1 = atom1
        self.atom2 = atom2

    def compute(self, x, cell=None):

        # TO DO, need to consider periodic boundary
        dz = x[self.atom1, 2] - x[self.atom2, 2]
        jacobian = np.zeros_like(x)
        jacobian[self.atom1, 2] = 1.0
        jacobian[self.atom2, 2] = -1.0
        return dz, jacobian

    def compute_r(self, x, cell=None):

        dz = x[self.atom1, 2] - x[self.atom2, 2]
        return dz
