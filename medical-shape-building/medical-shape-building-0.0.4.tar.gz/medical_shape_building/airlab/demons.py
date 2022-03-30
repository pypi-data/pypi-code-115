from typing import Any, Optional, Sequence, Union

import torch
import torchio as tio

from medical_shape_building.airlab.image import RegistrationImage
from medical_shape_building.airlab.registration import Registration
from medical_shape_building.airlab.utils import dice_coefficient, parse_devices


def multiscale_demons_registration(
    target_image: Union[RegistrationImage, tio.data.Image],
    source_image: Union[RegistrationImage, tio.data.Image],
    shrink_factors: Sequence[Sequence[int]],
    num_iterations: Sequence[int],
    sigmas: Sequence[Sequence[int]],
    learning_rates: Sequence[float],
    device: Optional[Union[str, torch.device]] = None,
    **kwargs: Any,
):
    device = parse_devices(device)
    reg = Registration(accelerator=device, devices=1)
    warped_image, displacement = reg.register(
        target_image=target_image,
        source_image=source_image,
        num_iterations=num_iterations,
        shrink_factors=shrink_factors,
        sigmas=sigmas,
        learning_rates=learning_rates,
        transformation="demons",
        regulariser="gaussian",
        loss_functions=["mse"],
        **kwargs,
    )

    dice_val = dice_coefficient(warped_image.to_itk(), target_image.to_itk())
    return warped_image, displacement, dice_val
