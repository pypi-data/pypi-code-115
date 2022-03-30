import torch

from medical_shape_building.snapping.strategy.base import SnappingStrategy


class DistanceSnappingStrategy(SnappingStrategy):
    def min_distance(self, surface: torch.Tensor, point: torch.Tensor) -> torch.Tensor:
        return torch.argmin(self.euclidian_distance(surface, point))

    def get_snapped_points(
        self, mask: torch.Tensor, points: torch.Tensor
    ) -> torch.Tensor:
        boundary_points = self.get_boundary_points(mask, xyz=self.points_xyz)

        snapped_points = []
        for p in points.unbind(0):
            snapped_points.append(
                boundary_points[self.min_distance(boundary_points, p)]
            )

        return torch.stack(snapped_points)
