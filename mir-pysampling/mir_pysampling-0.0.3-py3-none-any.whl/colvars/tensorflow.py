import os
import numpy as np
import subprocess

import matplotlib.pyplot as plt
from matplotlib.colors import TABLEAU_COLORS

plt.switch_backend("agg")

color_name = list(TABLEAU_COLORS)
colors = TABLEAU_COLORS
ncolor = len(color_name)

"""
take xyz coordination and do plumed analysis
"""


class Tensorflow:
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
                f"--{self.mol_format} {filename} --length-units A"
            )
            print("cmd", cmd)
            subprocess.call(cmd.split())
            assert os.path.isfile(
                self.foutput
            ), f"dump file {self.foutput} is not found"
            data = np.loadtxt(self.foutput)

            trj_rc = {"rc": rc, "other": data}
            os.remove(self.foutput)
            trjs_rc += [trj_rc]

        return trjs_rc

    def plot(self, filename, trjs, trjs_rc, contour_lines, keep_id, ax=None):
        pass

        plt.figure()
        for v in contour_lines:
            if v is not float("Inf"):
                if self.icomp == 1:
                    plt.axvline(x=v, linestyle="--", color="b")
                else:
                    plt.axhline(y=v, linestyle="--", color="b")
        for i in range(len(trjs_rc)):
            trj_rc = trjs_rc[i]["other"][:, 2:4]
            alpha = 1
            linestyle = "-"
            if keep_id is not None:
                if i not in keep_id:
                    alpha = 0.5
                    linestyle = "--"
            plt.plot(
                trj_rc[:, 0], trj_rc[:, 1], color="k", alpha=alpha, linestyle=linestyle
            )
            plt.scatter(
                trj_rc[0, 0], trj_rc[0, 1], color="k", alpha=alpha, linestyle=linestyle
            )
        plt.savefig(f"{filename}.png", bbox_inches="tight")
        plt.close()
