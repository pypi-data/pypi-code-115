from typing import List

import numpy as np

import pyaaware


class Predict:
    def __init__(self, name: str) -> None:
        self._predict = pyaaware._Predict(name)

    @property
    def file_name(self) -> str:
        return self._predict.get_file_name()

    @property
    def input_shape(self) -> List[int]:
        return self._predict.get_input_shape()

    @property
    def output_shape(self) -> List[int]:
        return self._predict.get_output_shape()

    def execute(self, x: np.ndarray) -> np.ndarray:
        y = self._predict.execute(x.ravel())
        return np.reshape(y, self.output_shape)
