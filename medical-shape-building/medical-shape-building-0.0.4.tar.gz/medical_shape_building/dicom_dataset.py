from __future__ import annotations

import os
import pathlib

import torchio as tio
from medical_shape import ShapeSupportSubject


def query_nifti_label_dicom_subject_candidates(
    root_path_labels: str,
    ref_pat_id: str | None,
    target_pat_id: None | str,
    ignore_patients: tuple[str, ...] | tuple = (),
    label_extensions: tuple[str, ...] = (".nii", ".nii.gz"),
) -> tuple[str, ...]:
    possible_candidates = []

    for ext in label_extensions:
        possible_candidates.extend(
            [(x, ext) for x in sorted(pathlib.Path(root_path_labels).rglob(f"*{ext}"))]
        )

    final_subject_candidates = []
    for candidate, ext in possible_candidates:
        # assume dicom structure for images.
        # For labels assume dicom structure, but instead of a series directory, expect a single nifti
        pat_id = os.path.split(os.path.split(os.path.split(candidate)[0])[0])[-1]

        if (
            (target_pat_id is not None and pat_id != target_pat_id)
            and (ref_pat_id is None or pat_id != ref_pat_id)
        ) or pat_id in ignore_patients:
            continue
        final_subject_candidates.append((candidate, pat_id, ext))

    return tuple(final_subject_candidates)


def build_dicom_subject(
    label_candidate_path: str,
    patient_id: str,
    candidate_label_extension: str,
    image_root_path: str,
    label_root_path: str,
) -> None:

    image_dir = (
        str(label_candidate_path)
        .replace(str(label_root_path), str(image_root_path))
        .replace(candidate_label_extension, "")
    )

    return ShapeSupportSubject(
        pat_id=patient_id,
        image=tio.data.ScalarImage(image_dir),
        label=tio.data.LabelMap(label_candidate_path),
    )
