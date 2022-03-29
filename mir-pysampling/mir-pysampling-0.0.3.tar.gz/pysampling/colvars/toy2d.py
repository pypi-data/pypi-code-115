import numpy as np
from .base import Colvar

import matplotlib.pyplot as plt
from matplotlib.colors import TABLEAU_COLORS


class Proj2d(Colvar):
    direction = 0

    def __init__(self, **kwargs):
        Colvar.__init__(self, **kwargs)

    def analyse_trjs(self, trjs):
        """
        calculate RC for the trajectories

        Args:
            trjs(list): list of trajectories
        """
        trjs_rc = []
        ntrj = len(trjs)
        for itrj in range(ntrj):

            trjs_rc += [
                {
                    "rc": self.callback(trjs[itrj]["x"]),
                    "other": np.copy(trjs[itrj]["x"]),
                }
            ]
        return trjs_rc

    def callback(self, data):
        return data[:, self.direction]

    def plot(self, filename, trjs, trjs_rc, contour_lines, keep_id, ax=None):

        plt.switch_backend("agg")

        plt.figure()
        for v in contour_lines:
            if v is not float("Inf"):
                if self.direction == 0:
                    plt.axvline(x=v, linestyle="--", color="b")
                else:
                    plt.axhline(y=v, linestyle="--", color="b")
        for i in range(len(trjs)):
            trj = trjs[i]["x"]
            alpha = 1
            linestyle = "-"
            if keep_id is not None:
                if i not in keep_id:
                    alpha = 0.5
                    linestyle = "--"
            plt.plot(trj[:, 0], trj[:, 1], color="k", alpha=alpha, linestyle=linestyle)
            plt.scatter(
                trj[0, 0], trj[0, 1], color="k", alpha=alpha, linestyle=linestyle
            )
        plt.xlim([10, 30])
        plt.ylim([0, 40])
        plt.savefig(f"{filename}.png", bbox_inches="tight")
        plt.close()


class ExtractY(Proj2d):
    direction = 1


class ExtractX(Proj2d):
    direction = 0


class TiltedY(Proj2d):
    direction = 0

    def callback(self, data):
        return data[:, 0] * 0.1 + data[:, 1]

    def plot(self, filename, trjs, trjs_rc, contour_lines, keep_id, ax=None):
        plt.figure()
        for v in contour_lines:
            if v is not float("Inf"):
                x = np.arange(10, 30, 1)
                y = -x * 0.1 + v
                plt.plot(x, y, linestyle="--", color="b")
        for i in range(len(trjs)):
            trj = trjs[i]["x"]
            alpha = 1
            linestyle = "-"
            if keep_id is not None:
                if i not in keep_id:
                    alpha = 0.5
                    linestyle = "--"
            plt.plot(trj[:, 0], trj[:, 1], color="k", alpha=alpha, linestyle=linestyle)
            plt.scatter(
                trj[0, 0], trj[0, 1], color="k", alpha=alpha, linestyle=linestyle
            )
        plt.xlim([10, 30])
        plt.ylim([0, 40])
        plt.savefig(f"{filename}.png", bbox_inches="tight")
        plt.close()


class NegX(Proj2d):
    direction = 0

    def callback(self, data):
        return -1 * data[:, self.direction]
