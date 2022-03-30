from typing import Tuple

import numpy as np

from medical_shape_building.sampling.strategy.base import SamplingStrategy


class Sampler:
    """
    Class used to sample points from a mask surface
    Args:
            sampling_strategy: SamplingStrategy
    """

    def __init__(self, sampling_strategy: SamplingStrategy):
        self.strategy = sampling_strategy

    def sample(
        self, img: np.ndarray, number_of_points: int = 2000
    ) -> Tuple[np.ndarray, Tuple[str, ...]]:
        """
        Samples points from a mask surface using the provided sampling_strategy
        Args:
                img: image we want to sample from
        """
        points = self.strategy.get_sampling_points(img.squeeze(), number_of_points)
        descriptions = self.strategy.get_point_descriptions(points)
        return points, descriptions

    def __call__(self, *args, **kwargs) -> np.ndarray:
        return self.sample(*args, **kwargs)
