import os
from typing import Dict, Sequence, Union

import numpy as np
import torch
import torchio as tio
from medical_shape import ShapeSupportSubject
from medical_shape.shape import SHAPE
from skimage.measure import label


def save_subject(path: str, subject: tio.data.Subject, exist_ok: bool = True):

    os.makedirs(path, exist_ok=exist_ok)
    extensions = {
        tio.constants.LABEL: ".nii.gz",
        tio.constants.INTENSITY: ".nii.gz",
        SHAPE: ".mjson",
    }
    for k, v in subject.get_images_dict(intensity_only=False).items():
        v.save(os.path.join(path, k.replace("/", "_") + extensions[v.type]))


def detect_out_of_bound_landmarks(
    landmarks: torch.Tensor,
    image_shape: Union[Sequence[int], torch.Tensor],
    boundary_margin: int = 0,
):
    curr_indices = torch.nonzero(
        (
            (landmarks < boundary_margin)
            + torch.stack(
                [
                    landmarks[..., i] >= image_shape[-(i + 1)] - boundary_margin
                    for i in range(landmarks.size(-1))
                ],
                -1,
            )
        ).sum(-1)
    )

    return curr_indices.view(-1).tolist()


def get_largest_cc(mask: torch.Tensor) -> torch.Tensor:
    labels = label(mask.cpu().detach()[0].numpy())
    assert labels.max() != 0  # assume at least 1 CC
    largest_cc = labels == np.argmax(np.bincount(labels.flat)[1:]) + 1
    return torch.from_numpy(largest_cc).to(mask)[None]


def save_processing_results(
    landmarks: Dict[str, ShapeSupportSubject],
    procrustes_landmarks: Dict[str, Dict[str, torch.Tensor]],
    pca: Dict[str, Dict[str, torch.Tensor]],
    output_path: str,
    root_path_images: str,
    all_original_image_paths: Dict[str, str],
) -> None:

    for pat, lmk_sub in landmarks.items():
        curr_out_path = str(all_original_image_paths[pat]).replace(
            root_path_images, os.path.join(output_path, "landmarks")
        )
        save_subject(curr_out_path, lmk_sub, exist_ok=True)

    for pat, lmk_dict in procrustes_landmarks.items():
        curr_out_path = os.path.join(output_path, "procrustes_landmarks", pat)
        os.makedirs(curr_out_path, exist_ok=True)
        for lmk_name, lmk in lmk_dict.items():
            torch.save(lmk, os.path.join(curr_out_path, lmk_name + ".pt"))

    pca_out_path = os.path.join(output_path, "pca")
    os.makedirs(pca_out_path, exist_ok=True)
    for bone, pca_dict in pca.items():
        torch.save(pca_dict, os.path.join(pca_out_path, bone + ".pt"))
