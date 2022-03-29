class Colvar:
    def __init__(self, colvardim=None, **kwargs):
        self.colvardim = colvardim

    def __call__(self, x=None, cell=None, ase_atoms=None):
        return self.compute(x, cell, ase_atoms)

    def compute(self, x=None, cell=None, ase_atoms=None):
        raise NotImplementedError("")

    def analyse_trajectory(self, x, cell=None):
        raise NotImplementedError("")
