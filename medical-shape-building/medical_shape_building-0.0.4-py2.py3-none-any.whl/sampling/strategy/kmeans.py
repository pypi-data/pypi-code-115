import numpy as np
from skimage.segmentation import find_boundaries
from sklearn.cluster import KMeans

from medical_shape_building.sampling.strategy.base import SamplingStrategy


class KMeansSamplingStrategy(SamplingStrategy):
    """Class defining a random sampling of points on the mask surface."""

    def __init__(
        self,
        number_of_seeds=30,
        max_iteration=300,
        algorithm="full",
    ) -> None:
        super().__init__()
        self.number_of_seeds = number_of_seeds
        self.max_iteration = max_iteration
        self.algorithm = algorithm

    def get_sampling_points(
        self, masked_image: np.ndarray, number_of_points: int = 2000, *args, **kwargs
    ) -> np.ndarray:
        """
         Performs a random sampling of points on the mask surface
         Args:
             mask_image: 3D numpy array
        Returns:
             np.ndarray: array containing coordinates of the selected landmarks
        """
        if not isinstance(masked_image, np.ndarray):
            masked_image = np.asarray(masked_image)
        kmeans = KMeans(
            n_clusters=number_of_points,
            n_init=self.number_of_seeds,
            max_iter=self.max_iteration,
            algorithm=self.algorithm,
        )
        boundary = find_boundaries(masked_image, mode="outer")
        possible_points = np.asarray(np.where(boundary))
        possible_points = possible_points[::-1].T

        kmeans.fit(possible_points)

        # cluster centers are not necessarily on boundary
        distances = kmeans.transform(possible_points).T
        point_indices = np.argmin(distances, 1)
        return possible_points[point_indices]

    def get_point_descriptions(self, points: np.ndarray) -> Tuple[str, ...]:
        return tuple(f"KMeans-Sampled Point {idx}" for idx in range(len(points)))
