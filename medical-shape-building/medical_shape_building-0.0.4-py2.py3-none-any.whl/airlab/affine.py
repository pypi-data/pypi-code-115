import logging
from typing import Optional, Union

import torch
import torchio as tio

from medical_shape_building.airlab.image import RegistrationImage
from medical_shape_building.airlab.registration import Registration
from medical_shape_building.airlab.utils import dice_coefficient, parse_devices

_logger = logging.getLogger(__name__)


def affine_registration(
    target_image: Union[RegistrationImage, tio.data.Image],
    source_image: Union[RegistrationImage, tio.data.Image],
    learning_rate: float,
    num_iterations: int,
    device: Optional[Union[str, torch.device]] = None,
):
    device = parse_devices(device)
    reg = Registration(accelerator=device, devices=1)

    _logger.debug(f"Affine registration with {num_iterations} iterations")
    warped_image, displacement = reg.register(
        target_image,
        source_image,
        num_iterations=[num_iterations],
        shrink_factors=[],
        sigmas=[],
        learning_rates=[learning_rate],
        transformation="affine",
        regulariser=None,
        loss_functions=["mse"],
    )

    dice_val = dice_coefficient(warped_image.to_itk(), target_image.to_itk())
    return warped_image, displacement, dice_val
