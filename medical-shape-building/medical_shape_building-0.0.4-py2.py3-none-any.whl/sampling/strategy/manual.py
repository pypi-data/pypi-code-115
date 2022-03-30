from abc import ABC, abstractmethod
from typing import Optional, Tuple

import numpy as np
from medical_shape import Shape

from medical_shape_building.sampling.strategy.base import SamplingStrategy


class ManualSamplingStrategy(SamplingStrategy, ABC):
    @abstractmethod
    def get_sampling_points(
        self, masked_image: np.ndarray, number_of_points: int, *args, **kwargs
    ) -> np.ndarray:
        assert number_of_points is None


class ManualShapeSampling(ManualSamplingStrategy):
    def __init__(self, shape: Optional[Shape] = None, path: Optional[str] = None):
        super().__init__()

        assert shape is not None or path is not None

        if shape is None:
            shape = Shape(path)

        self.shape = shape

    def get_sampling_points(
        self, masked_image: np.ndarray, number_of_points: int, *args, **kwargs
    ) -> np.ndarray:
        super().get_sampling_points(masked_image, number_of_points=number_of_points)

        return np.array(self.shape.tensor.cpu().detach().numpy())

    def get_point_descriptions(self, points: np.ndarray) -> Tuple[str, ...]:
        return self.shape.point_descriptions or tuple(
            f"Manual Defined Point {idx}" for idx in range(len(self.shape.tensor))
        )
