from __future__ import annotations

import logging
import os
import pathlib
from typing import Any, Sequence

import torch
import torchio as tio
from medical_shape import Shape, ShapeSupportSubject

from medical_shape_building.airlab.utils import dice_coefficient
from medical_shape_building.registration_pipeline import transfer_subject_landmarks
from medical_shape_building.sampling.sampler import Sampler
from medical_shape_building.sampling.strategy import (
    ManualShapeSampling,
    RandomSamplingStrategy,
    SamplingStrategy,
    SemiManualSamplingStrategy,
)
from medical_shape_building.snapping import SnappingStrategies
from medical_shape_building.snapping.snapper import PointSnapper
from medical_shape_building.split_structures import SplitStructuresTransform

_logger = logging.getLogger(__name__)


def process_subject(
    target_subject: tio.data.Subject,
    source_subject: ShapeSupportSubject,
    structures: dict[str, int],
    learning_rate_affine: float = 0.05,
    num_iterations_affine: int = 75,
    learning_rates_demons: Sequence[float] = (0.1, 0.1, 0.01),
    num_iterations_demons: Sequence[int] = (80, 40, 20),
    shrink_factors_demons: Sequence[Sequence[int]] = ((4, 4, 4), (2, 2, 2)),
    sigmas_demons: Sequence[Sequence[int]] = ((3, 3, 3), (3, 3, 3), (3, 3, 3)),
    device: str | torch.device | None = None,
    landmarks_zyx: bool = False,
    return_final_landmarks_only: bool = True,
    image_key_prefix: str = "label/",
    image_key_postfix: str = "",
    snapping_strategy: str = "identity",
    temp_output_path: str | None = None,
    not_only_largest_component: bool = False,
    **kwargs: Any,
):
    trafo = SplitStructuresTransform(
        structures,
        include_other_keys=True,
        not_only_largest_component=not_only_largest_component,
    )
    splitted_target = trafo(target_subject)

    if temp_output_path is None or not os.path.isdir(temp_output_path):
        (landmarks, snapped_landmarks, dice_coefficients,) = _process_not_cached(
            target_subject=target_subject,
            source_subject=source_subject,
            splitted_target=splitted_target,
            structures=structures,
            learning_rate_affine=learning_rate_affine,
            num_iterations_affine=num_iterations_affine,
            learning_rates_demons=learning_rates_demons,
            num_iterations_demons=num_iterations_demons,
            shrink_factors_demons=shrink_factors_demons,
            sigmas_demons=sigmas_demons,
            device=device,
            landmarks_zyx=landmarks_zyx,
            return_final_landmarks_only=return_final_landmarks_only,
            image_key_prefix=image_key_prefix,
            image_key_postfix=image_key_postfix,
            snapping_strategy=snapping_strategy,
            temp_output_path=temp_output_path,
            **kwargs,
        )
    else:
        try:
            (landmarks, snapped_landmarks, dice_coefficients,) = _process_cached(
                temp_output_path=temp_output_path,
                structures=structures,
                splitted_source=trafo(source_subject),
                image_key_prefix=image_key_prefix,
                image_key_postfix=image_key_postfix,
            )
        except Exception as e:
            _logger.warn(
                f"An exception occured while loading cached data: {e}. Recomputing instead"
            )

            (landmarks, snapped_landmarks, dice_coefficients,) = _process_not_cached(
                target_subject=target_subject,
                source_subject=source_subject,
                splitted_target=trafo(target_subject),
                structures=structures,
                learning_rate_affine=learning_rate_affine,
                num_iterations_affine=num_iterations_affine,
                learning_rates_demons=learning_rates_demons,
                num_iterations_demons=num_iterations_demons,
                shrink_factors_demons=shrink_factors_demons,
                sigmas_demons=sigmas_demons,
                device=device,
                landmarks_zyx=landmarks_zyx,
                return_final_landmarks_only=return_final_landmarks_only,
                image_key_prefix=image_key_prefix,
                image_key_postfix=image_key_postfix,
                snapping_strategy=snapping_strategy,
                temp_output_path=temp_output_path,
                **kwargs,
            )

    return (landmarks, snapped_landmarks, dice_coefficients)


def _process_not_cached(
    target_subject: tio.data.Subject,
    source_subject: ShapeSupportSubject,
    splitted_target: tio.data.Subject,
    structures: dict[str, int],
    learning_rate_affine: float = 0.05,
    num_iterations_affine: int = 75,
    learning_rates_demons: Sequence[float] = (0.1, 0.1, 0.01),
    num_iterations_demons: Sequence[int] = (80, 40, 20),
    shrink_factors_demons: Sequence[Sequence[int]] = ((4, 4, 4), (2, 2, 2)),
    sigmas_demons: Sequence[Sequence[int]] = ((3, 3, 3), (3, 3, 3), (3, 3, 3)),
    device: str | torch.device | None = None,
    landmarks_zyx: bool = False,
    return_final_landmarks_only: bool = True,
    image_key_prefix: str = "label/",
    image_key_postfix: str = "",
    snapping_strategy: str = "identity",
    temp_output_path: str | None = None,
    **kwargs: Any,
):

    _logger.debug(f"Processing subject {target_subject['pat_id']}")

    res = transfer_subject_landmarks(
        target_subject=target_subject,
        source_subject=source_subject,
        structures=structures,
        learning_rate_affine=learning_rate_affine,
        num_iterations_affine=num_iterations_affine,
        learning_rates_demons=learning_rates_demons,
        num_iterations_demons=num_iterations_demons,
        shrink_factors_demons=shrink_factors_demons,
        sigmas_demons=sigmas_demons,
        device=device,
        landmarks_zyx=landmarks_zyx,
        return_final_landmarks_only=return_final_landmarks_only,
        image_key_prefix=image_key_prefix,
        image_key_postfix=image_key_postfix,
        snapping_strategy=snapping_strategy,
        **kwargs,
    )

    if return_final_landmarks_only:
        landmarks, snapped_landmarks = res
        warped_images, dice_coefficients = {}, {}

    else:
        landmarks, snapped_landmarks, warped_images, _, dice_coefficients = res

    if temp_output_path is not None:
        os.makedirs(temp_output_path, exist_ok=True)

        for k, v in splitted_target.get_images_dict(intensity_only=False).items():
            if isinstance(v, (tio.data.ScalarImage, tio.data.LabelMap)):
                v.save(os.path.join(temp_output_path, k.rsplit("/", 1)[-1] + ".nii.gz"))

        for k, v in warped_images.items():
            v.save(os.path.join(temp_output_path, f"warped_{k}.nii.gz"))

        for k, v in landmarks.items():
            v.save(os.path.join(temp_output_path, f"{k}_pre_snapping.mjson"))

        for k, v in snapped_landmarks.items():
            v.save(os.path.join(temp_output_path, f"{k}_post_snapping.mjson"))
            v.save(os.path.join(temp_output_path, f"{k}.mjson"))

    return landmarks, snapped_landmarks, dice_coefficients


def _process_cached(
    temp_output_path: pathlib.Path | str,
    structures: dict[str, int],
    splitted_source: ShapeSupportSubject,
    image_key_prefix: str,
    image_key_postfix: str,
) -> tuple[ShapeSupportSubject, ShapeSupportSubject, dict[str, float]]:
    landmarks, snapped_landmarks, warped_images, dice_coefficients = {}, {}, {}, {}

    _logger.debug(f"Loading Warped Images and Landmarks from {temp_output_path}")
    for k in structures.keys():
        warped_images[k] = tio.data.LabelMap(
            os.path.join(temp_output_path, f"warped_{k}.nii.gz")
        )
        landmarks[k] = Shape(os.path.join(temp_output_path, f"{k}_pre_snapping.mjson"))
        snapped_landmarks[k] = Shape(
            os.path.join(temp_output_path, f"{k}_post_snapping.mjson")
        )

    warped_images_sub = tio.data.Subject(warped_images)
    landmarks_sub = ShapeSupportSubject(landmarks)
    snapped_landmarks_sub = ShapeSupportSubject(snapped_landmarks)

    for k, v in warped_images_sub.get_images_dict(intensity_only=False).items():
        # need to calculate the dice coefficient between warped and source here,
        # since internally the inverse transform from target to source is computed
        # as this is required for point transfer

        dice_coefficients[k] = dice_coefficient(
            v.as_sitk(),
            splitted_source[f"{image_key_prefix}{k}{image_key_postfix}"].as_sitk(),
        )

    return landmarks_sub, snapped_landmarks_sub, dice_coefficients


def process_ref_subject(
    ref_subject: ShapeSupportSubject,
    structures: dict[str, int],
    manual_ref_lmks: dict[str, str | Shape] | None,
    num_initial_points: int | None,
    snapping_strategy: str,
    device: None | str,
    temp_output_path: str,
    landmarks_zyx: bool,
    not_only_largest_component: bool,
    sampling_seed: int = 0,
) -> dict[str, Shape]:
    if temp_output_path is None or not os.path.exists(temp_output_path):
        if manual_ref_lmks is None:
            assert num_initial_points is not None
        else:
            assert set(manual_ref_lmks.keys()) == set(structures.keys())

            for k, v in manual_ref_lmks.items():
                if isinstance(v, str):
                    curr_lmks = Shape(v)

                ref_subject.add_image(curr_lmks, f"{k}_lmk")

        split_stuctures = SplitStructuresTransform(
            structures=structures, not_only_largest_component=not_only_largest_component
        )
        splitted_structures = split_stuctures(ref_subject)

        ref_landmarks: dict[str, Shape] = {}

        sampling_strategy: SamplingStrategy

        _logger.debug("Sample Reference Landmarks")
        for k in structures.keys():

            if manual_ref_lmks is not None:
                if num_initial_points is not None:
                    sampling_strategy = SemiManualSamplingStrategy(
                        RandomSamplingStrategy(seed=sampling_seed),
                        ManualShapeSampling(ref_subject[f"{k}_lmk"]),
                    )
                else:
                    sampling_strategy = ManualShapeSampling(ref_subject[f"{k}_lmk"])
            else:
                assert num_initial_points is not None
                sampling_strategy = RandomSamplingStrategy()

            sampler = Sampler(sampling_strategy)
            points, descriptions = sampler(
                splitted_structures[f"label/{k}"].tensor.cpu().detach().numpy(),
                num_initial_points,
            )
            ref_landmarks[k] = Shape(
                tensor=torch.from_numpy(points),
                affine=splitted_structures[f"label/{k}"].affine,
                point_descriptions=descriptions,
            )

        _logger.debug("Snapping Shapes to Masks")
        snapper = PointSnapper(
            SnappingStrategies.from_str(snapping_strategy).value(
                points_xyz=not landmarks_zyx
            )
        )
        _device = device or torch.device("cuda" if torch.cuda.is_available() else "cpu")

        for k in ref_landmarks.keys():
            ref_landmarks[k].set_data(
                snapper(
                    splitted_structures[f"label/{k}"].tensor.to(_device),
                    ref_landmarks[k].tensor.to(_device),
                ).cpu()
            )

        if temp_output_path is not None:
            ref_output_path_temp = os.path.join(temp_output_path, ref_subject["pat_id"])

            os.makedirs(ref_output_path_temp, exist_ok=True)

            _logger.debug("Saving Landmarks & Masks")

            for k, v in ref_landmarks.items():
                curr_path = os.path.join(ref_output_path_temp, f"{k}.mjson")
                if not os.path.exists(curr_path) and isinstance(v, Shape):
                    v.save(curr_path)

            for k, v in splitted_structures.items():
                if isinstance(v, (tio.data.LabelMap, tio.data.ScalarImage)):
                    v.save(
                        os.path.join(
                            ref_output_path_temp, f"{k.split('/', 1)[-1]}.nii.gz"
                        )
                    )
        else:
            _logger.warning("No output path specified, not saving anything.")
    else:
        ref_landmarks = {}
        ref_output_path_temp = os.path.join(temp_output_path, ref_subject["pat_id"])
        _logger.debug("Loading Landmarks")
        for k in structures.keys():
            ref_landmarks[k] = Shape(os.path.join(ref_output_path_temp, f"{k}.mjson"))

    return ref_landmarks
