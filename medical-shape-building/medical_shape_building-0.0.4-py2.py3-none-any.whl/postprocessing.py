import logging
from collections import defaultdict
from typing import Dict, Tuple

import numpy as np
import torch
from medical_shape import ShapeSupportSubject
from medical_shape.transforms import ShapeToOrientation

from medical_shape_building.pca import compute_pca
from medical_shape_building.procrustes import procrustes
from medical_shape_building.utils import detect_out_of_bound_landmarks

_LandmarksDataset = Dict[str, ShapeSupportSubject]

_logger = logging.getLogger(__name__)


@torch.no_grad()
def postprocess_landmark_dataset(
    landmarks_pre_snap: _LandmarksDataset,
    landmarks_post_snap: _LandmarksDataset,
    image_sizes: Dict[str, Tuple[int, ...]],
    original_affines: Dict[str, np.ndarray],
) -> Tuple[
    Tuple[
        _LandmarksDataset,
        Dict[str, _LandmarksDataset],
        Dict[str, Dict[str, torch.Tensor]],
    ],
    ...,
]:

    _logger.debug("Postprocessing landmarks")
    patient_ids = tuple(
        set(landmarks_pre_snap.keys())
        .intersection(set(image_sizes.keys()))
        .intersection(set(original_affines.keys()))
    )

    ignore_indices = defaultdict(list)
    _logger.debug("Detecting out of bound landmarks after registration")
    for patient_id in patient_ids:
        for k, v in landmarks_pre_snap[patient_id].get_shapes_dict().items():
            ignore_indices[k].extend(
                detect_out_of_bound_landmarks(v.tensor, image_sizes[patient_id])
            )

    _logger.debug("Removing all out of bound landmarks.")
    for patient_id in patient_ids:
        for shape_subject in (
            landmarks_pre_snap[patient_id],
            landmarks_post_snap[patient_id],
        ):
            for k, v in shape_subject.get_shapes_dict().items():
                v.set_data(
                    torch.stack(
                        [
                            x
                            for i, x in enumerate(v.tensor)
                            if i not in ignore_indices[k]
                        ]
                    )
                )

    _logger.debug("Applying Procrustes to landmarks and computing PCA")
    procrustes_landmarks, pcas = [], []
    for landmarks_list in (landmarks_pre_snap, landmarks_post_snap):

        means = {
            k: torch.stack([x[k].tensor.cpu() for x in landmarks_list.values()]).mean(0)
            for k in landmarks_list[patient_ids[0]].get_shapes_dict().keys()
        }

        curr_procrustes = defaultdict(dict)
        for k, v in landmarks_list.items():
            for _k, _v in v.get_shapes_dict().items():
                proc = procrustes(means[_k], _v.tensor.cpu())[1]
                curr_procrustes[k][_k] = proc
        procrustes_landmarks.append(
            {
                k: {
                    _k: procrustes(means[_k], _v.tensor)[1]
                    for _k, _v in v.get_shapes_dict().items()
                }
                for k, v in landmarks_list.items()
            }
        )

        pcas.append(
            {
                k: compute_pca(
                    torch.stack([v[k] for v in procrustes_landmarks[-1].values()])
                )
                for k in landmarks_list[patient_ids[0]].get_shapes_dict().keys()
            }
        )

    for k in patient_ids:
        trafo = ShapeToOrientation(affine=original_affines[k])
        landmarks_pre_snap[k] = trafo(landmarks_pre_snap[k])
        landmarks_post_snap[k] = trafo(landmarks_post_snap[k])

    return_values = (
        (landmarks_pre_snap, procrustes_landmarks[0], pcas[0]),
        (landmarks_post_snap, procrustes_landmarks[1], pcas[1]),
    )

    return return_values
