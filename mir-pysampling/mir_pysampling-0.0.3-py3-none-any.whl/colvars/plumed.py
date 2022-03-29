import logging
import numpy as np
import os
import subprocess


class Plumed:
    def __init__(self, finput, foutput, mol_format="ixyz"):
        self.icomp = 2
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

            rc = self.callback(data)

            trj_rc = {"rc": rc, "other": data}
            os.remove(self.foutput)
            trjs_rc += [trj_rc]

        return trjs_rc

    def callback(self, data):
        return data[:, self.icomp]

    def plot(self, filename, trjs, trjs_rc, contour_lines, keep_id, ax=None):
        pass
