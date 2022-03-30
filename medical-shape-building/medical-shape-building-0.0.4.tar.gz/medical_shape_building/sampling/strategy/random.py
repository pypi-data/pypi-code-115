import random
from typing import Optional, Tuple

import numpy as np
from skimage.segmentation import find_boundaries

from medical_shape_building.sampling.strategy.base import SamplingStrategy


class RandomSamplingStrategy(SamplingStrategy):
    """Class defining a random sampling of points on the mask surface."""

    def __init__(self, seed: Optional[int] = None):
        super().__init__()
        self.seed = seed

    # TODO: use helper function (duplicated code within snapping)
    def get_sampling_points(
        self, masked_image: np.ndarray, number_of_points: int, *args, **kwargs
    ) -> np.ndarray:
        """
        Performs a random sampling of points on the mask surface
        Args:
            mask_image: 3D numpy array
            number of points: number of landmarks we want to sample
        Returns:
            np.ndarray: array containing coordinates of the selected landmarks
        """
        if not isinstance(masked_image, np.ndarray):
            masked_image = np.asarray(masked_image)
        boundary = find_boundaries(masked_image, mode="outer")
        possible_points = np.asarray(np.where(boundary))
        points = possible_points[::-1].T.tolist()
        rng = random.Random(self.seed)
        out_points = rng.sample(points, number_of_points)

        return np.asarray(out_points)

    def get_point_descriptions(self, points: np.ndarray) -> Tuple[str, ...]:
        return tuple(f"Random-Sampled Point {idx}" for idx in range(len(points)))
