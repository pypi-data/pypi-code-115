from typing import Tuple

import torch
from sklearn.cluster import KMeans

from medical_shape_building.snapping.strategy.normal import NormalSnappingStrategy


class LocalNormalSnappingStrategy(NormalSnappingStrategy):
    def __init__(
        self,
        num_neighbors: int = 5,
        num_cluster_centers: int = 4000,
        init_clusters: bool = False,
        points_xyz: bool = True,
    ) -> None:
        super().__init__(num_neighbors, points_xyz)
        self.num_cluster_centers = num_cluster_centers
        self.init_clusters = init_clusters

    def group_points(
        self, boundary_points: torch.Tensor, init_clusters_pos: torch.Tensor
    ) -> Tuple[torch.Tensor, torch.Tensor]:
        if self.init_clusters:
            kmeans = KMeans(
                n_clusters=init_clusters_pos.size(0),
                init=init_clusters_pos.clone().cpu().numpy(),
                n_init=1,
                max_iter=300,
                algorithm="full",
            )
        else:
            kmeans = KMeans(
                n_clusters=self.num_cluster_centers,
                n_init=1,
                max_iter=300,
                algorithm="full",
            )

        kmeans.fit(boundary_points.cpu().detach())

        return (
            torch.from_numpy(kmeans.cluster_centers_).to(boundary_points),
            torch.from_numpy(kmeans.labels_).to(boundary_points),
        )

    def get_snapped_points(self, mask, points: torch.Tensor) -> torch.Tensor:
        boundary_points = self.get_boundary_points(mask)
        grouped_points, labels = self.group_points(boundary_points, points)
        normals = self.get_normals_grouped(boundary_points, grouped_points)
        snapped_points = torch.zeros_like(points)
        for idx, point in enumerate(points.unbind(0)):
            cl_idx = self.min_distance_normal(grouped_points, point, normals)
            p_idx_in_cluster = torch.where(labels == cl_idx)[0]
            points_in_cluster = boundary_points[p_idx_in_cluster]
            min_idx = self.min_distance(points_in_cluster, point)
            snapped_points[idx] = points_in_cluster[min_idx]
        return points

    def get_normals_grouped(self, boundary_points, grouped_points) -> torch.Tensor:
        normals = torch.zeros_like(grouped_points, dtype=torch.float)
        ctr = torch.mean(boundary_points.float(), axis=0)
        for i in range(len(grouped_points)):
            ns_index = self.neighbors(boundary_points, grouped_points[i])
            neighbor_points = boundary_points[ns_index]
            normal = self.calc_normal(neighbor_points, ctr, xyz=self.points_xyz)
            normals[i] = normal
        return normals
