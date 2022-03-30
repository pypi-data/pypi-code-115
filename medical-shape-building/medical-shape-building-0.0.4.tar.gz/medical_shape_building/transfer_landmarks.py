import logging
from typing import Optional, Sequence, Tuple, Union

import torch
import torchio as tio
from medical_shape import Shape

from medical_shape_building.airlab import (
    affine_multiscale_demons_registration,
    RegistrationImage,
    transform_points,
)
from medical_shape_building.airlab.image import RegistrationDisplacement
from medical_shape_building.snapping import SnappingStrategies
from medical_shape_building.snapping.snapper import PointSnapper

_logger = logging.getLogger(__name__)


def transfer_landmarks_by_registration(
    target_image: Union[RegistrationImage, tio.data.Image],
    source_image: Union[RegistrationImage, tio.data.Image],
    landmarks: Shape,
    learning_rate_affine: float = 0.05,
    num_iterations_affine: int = 75,
    learning_rates_demons: Sequence[float] = (0.1, 0.1, 0.01),
    num_iterations_demons: Sequence[int] = (80, 40, 20),
    shrink_factors_demons: Sequence[Sequence[int]] = ((4, 4, 4), (2, 2, 2)),
    sigmas_demons: Sequence[Sequence[int]] = ((3, 3, 3), (3, 3, 3), (3, 3, 3)),
    snapping_strategy: str = "identity",
    device: Optional[Union[str, torch.device]] = None,
    landmarks_zyx: bool = False,
    boundary_margin_oob_detection: int = 0,
    **demons_kwargs,
) -> Tuple[Shape, Shape, RegistrationImage, RegistrationDisplacement, float]:
    (
        warped_image,
        displacement_field,
        dice_coefficient,
    ) = affine_multiscale_demons_registration(
        # Switch images on purpose since SimpleITK interpolates the other way around
        target_image=source_image,
        source_image=target_image,
        learning_rate_affine=learning_rate_affine,
        num_iterations_affine=num_iterations_affine,
        learning_rates_demons=learning_rates_demons,
        num_iterations_demons=num_iterations_demons,
        shrink_factors_demons=shrink_factors_demons,
        sigmas_demons=sigmas_demons,
        device=device,
        **demons_kwargs,
        # TODO: Remove this after debugging
        points=landmarks,
    )

    transformed_landmarks = Shape(
        tensor=transform_points(
            landmarks.tensor, displacement_field, zyx=landmarks_zyx
        ),
        affine=target_image.to_torchio().affine
        if isinstance(target_image, RegistrationImage)
        else target_image.affine,
        point_descriptions=landmarks.point_descriptions,
    )

    _logger.debug(f"Snapping Landmarks to mask with {snapping_strategy}")

    snapper = PointSnapper(
        SnappingStrategies.from_str(snapping_strategy).value(
            points_xyz=not landmarks_zyx
        )
    )

    transformed_landmarks_snapped = Shape(
        tensor=snapper(
            warped_image.to_torchio().tensor.to(device),
            transformed_landmarks.tensor.to(device),
        ).cpu(),
        affine=transformed_landmarks.affine,
        point_descriptions=transformed_landmarks.point_descriptions,
    )

    return (
        transformed_landmarks,
        transformed_landmarks_snapped,
        warped_image,
        displacement_field,
        dice_coefficient,
    )
