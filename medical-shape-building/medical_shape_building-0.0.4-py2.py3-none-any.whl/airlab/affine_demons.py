import logging
from typing import Optional, Sequence, Union

import torch
import torchio as tio
from medical_shape import Shape

from medical_shape_building.airlab.affine import affine_registration
from medical_shape_building.airlab.demons import multiscale_demons_registration
from medical_shape_building.airlab.image import (
    RegistrationDisplacement,
    RegistrationImage,
)

_logger = logging.getLogger(__name__)


def affine_multiscale_demons_registration(
    target_image: Union[RegistrationImage, tio.data.Image],
    source_image: Union[RegistrationImage, tio.data.Image],
    learning_rate_affine: float = 0.05,
    num_iterations_affine: int = 75,
    learning_rates_demons: Sequence[float] = (0.1, 0.1, 0.01),
    num_iterations_demons: Sequence[int] = (80, 40, 20),
    shrink_factors_demons: Sequence[Sequence[int]] = ((4, 4, 4), (2, 2, 2)),
    sigmas_demons: Sequence[Sequence[int]] = ((3, 3, 3), (3, 3, 3), (3, 3, 3)),
    device: Optional[Union[str, torch.device]] = None,
    # TODO: Remove this after debugging
    points: Optional[Shape] = None,
    **demons_kwargs,
):
    displacements = []
    warped_images = []
    dice_coefficients = []

    if not isinstance(target_image, RegistrationImage):
        target_image = RegistrationImage.from_torchio(target_image)
    if not isinstance(source_image, RegistrationImage):
        source_image = RegistrationImage.from_torchio(source_image)

    _logger.debug("Start Affine Registration")
    (
        affine_warped_image,
        affine_displacement,
        affine_dice_coefficient,
    ) = affine_registration(
        target_image,
        source_image,
        learning_rate=learning_rate_affine,
        num_iterations=num_iterations_affine,
        device=device,
    )

    affine_warped_image = affine_warped_image.cpu()
    displacements.append(affine_displacement.cpu())
    warped_images.append(affine_warped_image)
    dice_coefficients.append(affine_dice_coefficient)

    _logger.debug("Start Multiscale Demons Registration")
    (
        demons_warped_image,
        demons_displacement,
        demons_dice_coefficient,
    ) = multiscale_demons_registration(
        target_image=target_image,
        source_image=affine_warped_image,
        shrink_factors=shrink_factors_demons,
        num_iterations=num_iterations_demons,
        sigmas=sigmas_demons,
        learning_rates=learning_rates_demons,
        device=device,
        **demons_kwargs,
    )

    displacements.append(demons_displacement.cpu())
    warped_images.append(demons_warped_image.cpu())

    dice_coefficients.append(demons_dice_coefficient)
    total_disp_torch = sum(x.image for x in displacements)

    return (
        warped_images[-1],
        RegistrationDisplacement(total_disp_torch, affine=displacements[-1].affine),
        dice_coefficients[-1],
    )
