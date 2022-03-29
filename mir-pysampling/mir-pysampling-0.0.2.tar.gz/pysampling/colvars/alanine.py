import logging
import numpy as np
import os
import subprocess


class Alanine:
    def __init__(self, finput, foutput, mol_format="ixyz"):
        self.phi = 2
        self.psi = 3
        self.finput = finput
        self.foutput = foutput
        self.mol_format = mol_format

    def analyse_trjs(self, trjs, prefix=""):
        """
        calculate RC for the trajectories

        Args:
            trjs(list): list of trajectories in lammpstrj format
        """

        trjs_rc = []
        ntrj = len(trjs)
        for itrj in range(ntrj):
            filename = trjs[itrj]["name"]
            cmd = (
                f"plumed driver --plumed {self.finput} "
                f"--{self.mol_format} {filename}"
            )
            if self.mol_format == "mf_lammpstrj":
                cmd += " --length-units A"
            logging.debug(f"cmd {cmd}")
            subprocess.call(cmd.split())
            assert os.path.isfile(
                self.foutput
            ), f"dump file {self.foutput} is not found"

            data = np.loadtxt(self.foutput)

            logging.debug(f"{self.phi}")
            logging.debug(f"{data}")
            rc = self.callback(data)

            trj_rc = {"rc": rc, "other": data}
            os.remove(self.foutput)
            trjs_rc += [trj_rc]

        return trjs_rc

    def callback(self, data):
        return data[:, self.phi]

    def plot(self, filename, trjs, trjs_rc, contour_lines, keep_id, ax=None):
        pass


"""
affine rc for alanine dipeptide as defined in paper by Lopes and Lelievre (2019)
parameterizes into 5 piecewise linear functions
TODO: custom user-defined piecewise parameterization

"""


class affine(Alanine):
    def __init__(self, finput, foutput, mol_format="ixyz"):
        super().__init__(finput, foutput, mol_format)

    def callback(self, data):

        phi_data = data[:, self.phi]

        for i in range(len(phi_data)):
            if phi_data[i] < -52.5:
                phi_data[i] = -5.25
            elif phi_data[i] >= -52.5 and phi_data[i] <= 45:
                phi_data[i] = 0.1 * phi_data[i]
            elif phi_data[i] > 45 and phi_data[i] < 92.5:
                phi_data[i] = 4.5
            elif phi_data[i] >= 92.5 and phi_data[i] <= 172.5:
                phi_data[i] = -0.122 * phi_data[i] + 15.773
            else:
                phi_data[i] = -5.25

        return phi_data


"""
rc for alanine dipeptide that returns phi only
"""


class phi(Alanine):
    def __init__(self, finput, foutput, mol_format="ixyz"):
        super().__init__(finput, foutput, mol_format)

    def callback(self, data):
        return data[:, self.phi]


"""
rc for alanine dipeptide that returns psi only
"""


class psi(Alanine):
    def __init__(self, finput, foutput, mol_format="ixyz"):
        super().__init__(finput, foutput, mol_format)

    def callback(self, data):
        return data[:, self.psi]
