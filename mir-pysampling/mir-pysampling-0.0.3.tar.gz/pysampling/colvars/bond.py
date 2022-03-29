import numpy as np
from pysampling.colvars.base import Colvar


class Bond(Colvar):
    """Collective variable class based on bond distances: inherits directly from base class

    Parameters:
    atom1 (int): index of atom1 in array
    atom2 (int): index of atom2 in array
    colvardim (default colvardim=1)

    ----------------------------------------------------

    Methods:

    compute: returns collective variable and Jacobian
    compute_r: returns distance between both atoms
    """

    def __init__(self, atom1, atom2):
        super().__init__(colvardim=1)
        self.atom1 = atom1
        self.atom2 = atom2

    def compute(self, x, cell=None):

        # TO DO, need to consider periodic boundary
        d = x[self.atom1] - x[self.atom2]
        r = np.linalg.norm(d)
        jacobian = np.zeros_like(x)
        jacobian[self.atom1] = d / r
        jacobian[self.atom2] = -d / r
        return r, jacobian

    def compute_r(self, x, cell=None):

        r = np.linalg.norm(x[self.atom1] - x[self.atom2])
        return r


class Bond2(Colvar):
    """Collective variable class based on two bond distances: inherits directly from base class

    Parameters:
    atom1 (int): index of atom1 in array
    atom2 (int): index of atom2 in array
    atom3 (int): index of atom3 in array
    atom4 (int): index of atom4 in array
    colvardim (default colvardim=1)

    ----------------------------------------------------

    Methods:

    compute: returns collective variable and Jacobian
    """

    def __init__(self, atom1, atom2, atom3, atom4):
        super().__init__(colvardim=2)

        self.bond1 = Colvar_Bond(atom1, atom2)
        self.bond2 = Colvar_Bond(atom3, atom4)

    def compute(self, x, cell=None):

        b1, j1 = self.bond1.compute(x)
        b2, j2 = self.bond2.compute(x)
        return np.array([[b1, b2]]), np.vstack([j1.reshape([-1]), j2.reshape([-1])])
