import logging

import torch
import tqdm

from medical_shape_building.logging_tqdm import TqdmToLogger
from medical_shape_building.snapping.strategy.distance import DistanceSnappingStrategy

_logger = logging.getLogger(__name__)


class NormalSnappingStrategy(DistanceSnappingStrategy):
    def __init__(
        self,
        num_neighbors: int = 5,
        points_xyz: bool = True,
    ):
        super().__init__(points_xyz)
        self.num_neighbors = num_neighbors

    def neighbors(self, surface, point):
        d = self.euclidian_distance(surface, point)
        ns_index = torch.argsort(d)[: self.num_neighbors]
        return ns_index

    def get_snapped_points(self, mask, points: torch.Tensor) -> torch.Tensor:
        boundary_points = self.get_boundary_points(mask, xyz=self.points_xyz)
        normals = self.get_normals(boundary_points)
        snapped_points = torch.zeros_like(points)

        iterable = tqdm.tqdm(
            points,
            desc="Snapping points",
            file=TqdmToLogger(logger=_logger, level=logging.DEBUG),
            mininterval=10,
            unit="point",
        )
        for i, p in enumerate(iterable):
            min_idx = self.min_distance_normal(boundary_points, p, normals)
            snapped_points[i] = boundary_points[min_idx]
        return snapped_points

    def min_distance_normal(self, surface, point, normals):
        d = self.euclidian_distance(surface, point)
        point_unit = point / torch.linalg.norm(point)

        factor = 1 - torch.mm(point_unit[None].float(), normals.T)
        d = d + factor[0]
        ind = torch.argmin(d).flatten()
        return ind[0]

    def get_normals(self, boundary_points) -> torch.Tensor:
        normals = torch.zeros_like(boundary_points, dtype=torch.float)

        ctr = torch.mean(boundary_points, axis=0)

        iterable = tqdm.tqdm(
            range(len(boundary_points)),
            desc="Calculating normals",
            file=TqdmToLogger(logger=_logger, level=logging.DEBUG),
            miniters=1000,
            unit="normal",
        )
        for i in iterable:
            ns_index = self.neighbors(boundary_points, boundary_points[i])
            neighbor_points = boundary_points[ns_index]
            normal = self.calc_normal(neighbor_points, ctr, xyz=self.points_xyz)
            normals[i] = normal
        return normals

    def calc_normal(self, points: torch.Tensor, ctr: torch.Tensor, xyz: bool = True):
        if xyz:
            points = torch.flip(points, (-1,))
            ctr = torch.flip(ctr, (-1,))

        # This definition only holds for zyx format.
        # Too lazy to recalc for xyz -> switch to zyx and switch back results
        x = points - points[0]
        m = torch.mm(x.T, x)
        u, _, v = torch.svd(m)
        normal = u[:, -1]
        v = points[0] - ctr
        norm1 = v / torch.linalg.norm(v)
        norm2 = normal / torch.linalg.norm(normal)
        direction = torch.dot(norm2, norm1)
        # check orientation
        if direction < 0:
            norm2 *= -1

        if xyz:
            norm2 = torch.flip(norm2, (-1,))
        return norm2
