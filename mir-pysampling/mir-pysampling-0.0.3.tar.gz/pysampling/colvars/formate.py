import numpy as np

from copy import deepcopy
from ase.atoms import Atoms

from pysampling.colvars.base import Colvar


class formate(Colvar):
    """
    3d collective variables max(CH), min(OCu), min(HCu)
    """

    def __init__(self, species=None):

        Colvar.__init__(self, colvardim=3)

        self.species = deepcopy(species)

        self.Hid = np.array([i for i, s in enumerate(self.species) if s == "H"])
        self.Cid = np.array([i for i, s in enumerate(self.species) if s == "C"])
        self.Oid = np.array([i for i, s in enumerate(self.species) if s == "O"])
        self.Cuid = np.array([i for i, s in enumerate(self.species) if s == "Cu"])

    def compute(self, x=None, cell=None, ase_atoms=None):

        if ase_atoms is None and x is not None:
            ase_atoms = Atoms(self.species, x, cell=cell, pbc=True)

        xyz = ase_atoms.get_positions()

        dist_mat = ase_atoms.get_all_distances(mic=True)
        dist_CH = np.max((dist_mat[self.Hid].T)[self.Cid])

        dist_OCu = np.max(np.min((dist_mat[self.Oid].T)[self.Cuid], axis=0))
        dist_HCu = np.min((dist_mat[self.Hid].T)[self.Cuid])

        e = ase_atoms.get_potential_energies()[self.Hid]

        return np.hstack([dist_CH, dist_OCu, dist_HCu, e])

    # def analyse_trjs(self, trjs, prefix=""):
    #     """
    #     calculate RC for the trajectories

    #     Args:
    #         trjs(list): list of trajectories in lammpstrj format
    #     """

    #     trjs_rc = []
    #     ntrj = len(trjs)
    #     for itrj in range(ntrj):
    #         filename = trjs[itrj]['name']
    #         cmd = f"plumed driver --plumed {self.finput} "\
    #               f"--{self.mol_format} {filename}"
    #         if (self.mol_format == "mf_lammpstrj"):
    #             cmd += " --length-units A"
    #         logger.debug(f"cmd {cmd}")
    #         subprocess.call(cmd.split())
    #         assert os.path.isfile(self.foutput), \
    #             f"dump file {self.foutput} is not found"

    #         data = np.loadtxt(self.foutput)

    #         logger.debug(f"{self.phi}")
    #         logger.debug(f"{data}")
    #         rc = self.callback(data)

    #         trj_rc = {'rc': rc,
    #                   'other': data}
    #         os.remove(self.foutput)
    #         trjs_rc += [trj_rc]

    #     return trjs_rc

    # def callback(self, data):
    #     return data[:, self.phi]

    # def plot(self, filename, trjs, trjs_rc, contour_lines, keep_id, ax=None):
    #     pass
