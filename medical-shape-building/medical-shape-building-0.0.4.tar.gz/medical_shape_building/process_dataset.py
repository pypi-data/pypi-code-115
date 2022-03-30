from __future__ import annotations

import gc
import logging
import os
from copy import deepcopy
from typing import Callable

import torch
from medical_shape import Shape, ShapeSupportSubject
from medical_shape.transforms import ToCanonical
from tqdm import tqdm

from medical_shape_building.dicom_dataset import (
    build_dicom_subject,
    query_nifti_label_dicom_subject_candidates,
)
from medical_shape_building.logging_tqdm import TqdmToLogger
from medical_shape_building.postprocessing import postprocess_landmark_dataset
from medical_shape_building.process_subject import process_ref_subject, process_subject
from medical_shape_building.utils import save_processing_results as save_results

_logger = logging.getLogger(__name__)


def process_dataset(
    root_path_images: str,
    root_path_labels: str,
    output_path: str,
    ref_pat_id: str,
    structures: dict[str, int],
    target_pat_id: str | None = None,
    manual_ref_lmks: dict[str, str | Shape] | None = None,
    ignore_patients: tuple[str, ...] | tuple = (),
    num_initial_points: int | None = 10000,
    device: str | int | None = None,
    sampling_seed: int = 0,
    snapping_strategy: str = "normals",
    not_only_largest_component: bool = False,
    temp_output_path: str | None = None,
    label_extensions: tuple[str, ...] = (".nii", ".nii.gz"),
    build_subject_fn: Callable[
        [str, str, str, str, str], ShapeSupportSubject
    ] = build_dicom_subject,
    query_subject_candidates_fn: Callable[
        [str, str, None | str, tuple[str, ...] | tuple, tuple[str, ...]],
        tuple[str, ...],
    ] = query_nifti_label_dicom_subject_candidates,
    landmarks_zyx=False,
) -> None:

    _logger.info("Build Subjects")
    subjects = [
        build_subject_fn(path, pat_id, ext, root_path_images, root_path_labels)
        for path, pat_id, ext in query_subject_candidates_fn(
            root_path_labels,
            ref_pat_id,
            target_pat_id,
            ignore_patients,
            label_extensions,
        )
    ]

    # TODO: Optional selection of ref patient

    reference_subject = subjects.pop(
        subjects.index([sub for sub in subjects if sub["pat_id"] == ref_pat_id][0])
    )

    ref_landmarks = process_ref_subject(
        ref_subject=reference_subject,
        structures=structures,
        manual_ref_lmks=manual_ref_lmks,
        num_initial_points=num_initial_points,
        snapping_strategy=snapping_strategy,
        device=device,
        temp_output_path=temp_output_path,
        landmarks_zyx=landmarks_zyx,
        not_only_largest_component=not_only_largest_component,
        sampling_seed=sampling_seed,
    )

    complete_ref_subject = ShapeSupportSubject(
        **ShapeSupportSubject.exclude_shapes(dict(reference_subject)),
        **ref_landmarks,
    )

    canonical_trafo = ToCanonical(shape_image_key="label")
    complete_ref_subject_canonical: ShapeSupportSubject = canonical_trafo(
        complete_ref_subject
    )

    ref_landmarks_canonical = ShapeSupportSubject(
        complete_ref_subject_canonical.get_shapes_dict()
    )

    all_landmarks_canonical = {ref_pat_id: ref_landmarks_canonical}
    all_landmarks_snapped_canonical = {ref_pat_id: ref_landmarks_canonical}
    image_sizes_canonical = {ref_pat_id: complete_ref_subject_canonical["image"].shape}
    affines_orig = {ref_pat_id: complete_ref_subject["image"].affine}
    all_paths = {ref_pat_id: reference_subject["image"].path}

    for sub in tqdm(subjects, file=TqdmToLogger(logger=_logger, level=logging.INFO)):
        pat_id = sub["pat_id"]

        curr_affine = deepcopy(sub["image"].affine)
        curr_path = deepcopy(sub["image"].path)
        sub_canonical = canonical_trafo(sub)

        (landmarks, snapped_landmarks, dice_coefficients) = process_subject(
            target_subject=sub_canonical,
            source_subject=complete_ref_subject_canonical,
            structures=structures,
            landmarks_zyx=landmarks_zyx,
            return_final_landmarks_only=False,
            device=device
            or torch.device("cuda" if torch.cuda.is_available() else "cpu"),
            snapping_strategy=snapping_strategy,
            temp_output_path=os.path.join(temp_output_path, pat_id),
            not_only_largest_component=not_only_largest_component,
        )

        if all(v > 0.99 for v in dice_coefficients.values()):
            all_landmarks_canonical[pat_id] = deepcopy(landmarks)
            all_landmarks_snapped_canonical[pat_id] = deepcopy(snapped_landmarks)
            image_sizes_canonical[pat_id] = deepcopy(
                sub_canonical["image"].spatial_shape
            )
            affines_orig[pat_id] = curr_affine
            all_paths[pat_id] = curr_path

        del landmarks
        del snapped_landmarks
        del sub
        del sub_canonical
        gc.collect()

    if not target_pat_id:
        (
            (landmarks_pre_snap, procrustes_landmarks_pre_snap, pca_pre_snap),
            (landmarks_post_snap, procrustes_landmarks_post_snap, pca_post_snap),
        ) = postprocess_landmark_dataset(
            all_landmarks_canonical,
            all_landmarks_snapped_canonical,
            image_sizes_canonical,
            original_affines=affines_orig,
        )

        if output_path is not None:
            save_results(
                landmarks_pre_snap,
                procrustes_landmarks_pre_snap,
                pca_pre_snap,
                os.path.join(output_path, "pre_snap"),
                root_path_images,
                all_paths,
            )
            save_results(
                landmarks_post_snap,
                procrustes_landmarks_post_snap,
                pca_post_snap,
                os.path.join(output_path, "post_snap"),
                root_path_images,
                all_paths,
            )
