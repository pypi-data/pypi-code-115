import logging

import medical_shape
import torch
import torchio as tio
from medical_shape.transforms import TransformShapeValidationMixin

from medical_shape_building.snapping.strategy import SnappingStrategy

_logger = logging.getLogger(__name__)


class PointSnapper:
    def __init__(self, sampling_strategy: SnappingStrategy):
        self.strategy = sampling_strategy

    @torch.no_grad()
    def snap_points(self, mask: torch.Tensor, points: torch.Tensor) -> torch.Tensor:

        snapped_points = self.strategy.get_snapped_points(mask.squeeze(), points)

        _logger.debug(
            f"Snapped Points differ on average {snapped_points.sub(points).abs().mean().item()} voxels from original points"
        )
        return snapped_points

    def __call__(self, *args, **kwargs) -> torch.Tensor:
        return self.snap_points(*args, **kwargs)


class SnappingTransform(TransformShapeValidationMixin):
    def __init__(
        self,
        strategy: SnappingStrategy,
        key_prefix: str = "",
        key_postfix: str = "",
        *args,
        **kwargs,
    ):
        super().__init__(*args, **kwargs)
        self.key_prefix = key_prefix
        self.key_postfix = key_postfix
        self.snapper = PointSnapper(strategy)

    def apply_transform(self, subject: medical_shape.ShapeSupportSubject):
        for k, v in getattr(subject, "get_shapes_dict", lambda: {})().items():
            corresponding_image = subject[f"{self.key_prefix}{k}{self.key_postfix}"]
            if not isinstance(corresponding_image, tio.data.Image):
                raise TypeError(
                    f"Expected image of key {self.key_prefix}{k}{self.key_postfix} to be an torchio image but got {v}"
                )

            v.set_data(self.snapper(corresponding_image.tensor))

        return subject
