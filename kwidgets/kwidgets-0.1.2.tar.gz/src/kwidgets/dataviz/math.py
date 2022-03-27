""" Various data structures for data science visualization.

"""
from typing import Iterable, Union, List
import bisect
import numpy as np


class BoxPlotData:
    """ The parameters of a box plot

    Takes an iterable over some numbers and computes the parameters needed to draw a boxplot.
    """
    min: float
    q1: float
    median: float
    q3: float
    max: float
    outliers: List[float]

    def __init__(self, data: Iterable[Union[float, int]]):
        """ Compute the parameters for a boxplot.

        Uses description from matplotlib: https://matplotlib.org/stable/api/_as_gen/matplotlib.pyplot.boxplot.html

        :param data: An iterable over the data to be plotted.
        """
        data_sorted = sorted(list(data))
        self.q1, self.median, self.q3 = np.percentile(data, q=[25, 50, 75])
        self.min = data_sorted[bisect.bisect(data_sorted, self.q1 - 1.5 * (self.q3 - self.q1))]
        self.max = data_sorted[bisect.bisect(data_sorted, self.q3 + 1.5 * (self.q3 - self.q1)) - 1]
        self.outliers = [x for x in data_sorted if x < self.min or x > self.max]

    def __str__(self) -> str:
        return "BoxPlotData: min=%0.2f, q1=%0.2f, median=%0.2f, q3=%0.2f, max=%0.2f" % (self.min, self.q1, self.median, self.q3, self.max)

