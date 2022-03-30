import logging
from typing import Any, Dict, Optional, Sequence, Union

import torch
import torchio as tio
from medical_shape.apply_to_collection import apply_to_collection
from medical_shape.subject import ShapeSupportSubject

from medical_shape_building.airlab import RegistrationImage
from medical_shape_building.split_structures import SplitStructuresTransform
from medical_shape_building.transfer_landmarks import transfer_landmarks_by_registration

_logger = logging.getLogger(__name__)


def transfer_subject_landmarks(
    target_subject: tio.data.Subject,
    source_subject: ShapeSupportSubject,
    structures: Optional[Dict[str, int]] = None,
    learning_rate_affine: float = 0.05,
    num_iterations_affine: int = 75,
    learning_rates_demons: Sequence[float] = (0.1, 0.1, 0.01),
    num_iterations_demons: Sequence[int] = (80, 40, 20),
    shrink_factors_demons: Sequence[Sequence[int]] = ((4, 4, 4), (2, 2, 2)),
    sigmas_demons: Sequence[Sequence[int]] = ((3, 3, 3), (3, 3, 3), (3, 3, 3)),
    device: Optional[Union[str, torch.device]] = None,
    landmarks_zyx: bool = False,
    return_final_landmarks_only: bool = True,
    image_key_prefix: str = "label/",
    image_key_postfix: str = "",
    snapping_strategy: str = "identity",
    **kwargs: Any,
):
    if structures is None:
        # defaults to Knee Structures
        structures = {"femur": 1, "tibia": 2}  # TODO: Add Patella

    assert all([k in structures for k in source_subject.get_shapes_dict().keys()])

    trafo = SplitStructuresTransform(structures)

    splitted_target_subject = trafo(target_subject)
    splitted_source_subject = trafo(source_subject)

    transferred_landmarks = {}
    transferred_landmarks_snapped = {}
    warped_images = {}
    displacements = {}
    dice_coefficients = {}

    for k, v in source_subject.get_shapes_dict().items():
        image_key = f"{image_key_prefix}{k}{image_key_postfix}"
        _logger.debug(f"Transferring landmarks for {image_key}")
        res = transfer_landmarks_by_registration(
            RegistrationImage.from_torchio(splitted_target_subject[image_key]),
            RegistrationImage.from_torchio(splitted_source_subject[image_key]),
            v,
            learning_rate_affine=learning_rate_affine,
            num_iterations_affine=num_iterations_affine,
            learning_rates_demons=learning_rates_demons,
            num_iterations_demons=num_iterations_demons,
            shrink_factors_demons=shrink_factors_demons,
            sigmas_demons=sigmas_demons,
            device=device,
            landmarks_zyx=landmarks_zyx,
            snapping_strategy=snapping_strategy,
            **kwargs,
        )

        res = apply_to_collection(
            res, (torch.Tensor, torch.nn.Module), lambda x: x.cpu()
        )
        (
            transferred_landmarks[k],
            transferred_landmarks_snapped[k],
            warped_images[k],
            displacements[k],
            dice_coefficients[k],
        ) = res

    if not transferred_landmarks:
        raise ValueError("No landmarks were transferred")

    if return_final_landmarks_only:
        return (
            ShapeSupportSubject(transferred_landmarks),
            ShapeSupportSubject(transferred_landmarks_snapped),
        )
    else:
        return (
            ShapeSupportSubject(transferred_landmarks),
            ShapeSupportSubject(transferred_landmarks_snapped),
            tio.data.Subject({k: v.to_torchio() for k, v in warped_images.items()}),
            displacements,
            dice_coefficients,
        )
