from abc import ABC, abstractmethod

import numpy as np
import torch
from skimage.segmentation import find_boundaries


class SnappingStrategy(ABC):
    """Abstract Base Class defining how points are snapped to a mask."""

    def __init__(self, points_xyz: bool = True):
        self.points_xyz = points_xyz

    @abstractmethod
    def get_snapped_points(
        self, mask: torch.Tensor, points: torch.Tensor
    ) -> torch.Tensor:
        pass

    @staticmethod
    def euclidian_distance(surface: torch.Tensor, points: torch.Tensor):
        try:
            diffs = surface - points
        except:

            diffs = surface - points

        d = (diffs ** 2).sum(-1)

        if isinstance(d, torch.Tensor):
            d = torch.sqrt(d)
        else:
            d = np.sqrt(d)
        return d

    @staticmethod
    def get_boundary_points(mask: torch.Tensor, xyz: bool = True):
        mask_np = mask.long().cpu().detach().numpy()

        boundary = find_boundaries(mask_np, mode="outer")
        boundary_points = torch.tensor(
            np.array(np.where(boundary)), device=mask.device, dtype=torch.float
        ).T

        if xyz:
            boundary_points = torch.flip(boundary_points, (-1,))
        return boundary_points
