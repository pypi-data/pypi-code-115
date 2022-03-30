from typing import Dict, Optional

import numpy as np
import torch
from sklearn.decomposition import PCA


def compute_pca(
    landmarks: torch.Tensor,
    n_components: Optional[int] = None,
    min_explained_variance_ratio: Optional[float] = None,
) -> Dict[str, torch.Tensor]:

    # center each of the landmarks
    means = torch.mean(landmarks, dim=1, keepdim=True)
    landmarks_centered = landmarks - means
    landmarks_transposed = landmarks_centered.permute(0, 2, 1)

    reshaped = landmarks_transposed.reshape(landmarks.size(0), -1)

    pca = PCA()
    pca.fit(reshaped.cpu().detach().numpy())

    if n_components is None and min_explained_variance_ratio is not None:
        n_components = (
            np.argmin(
                np.abs(
                    np.cumsum(pca.explained_variance_ratio_)
                    - min_explained_variance_ratio
                )
            )
            + 1
        )

    assert n_components is None or 0 < n_components <= pca.components_.shape[0]

    components = pca.components_ * pca.singular_values_.reshape(-1, 1)
    singular_values = torch.from_numpy(pca.singular_values_).float()
    explained_variance_ratio = torch.from_numpy(pca.explained_variance_ratio_).float()

    if n_components is not None:
        components = components[:n_components]
        singular_values = singular_values[:n_components]
        explained_variance_ratio = explained_variance_ratio[:n_components]

    components = (
        torch.from_numpy(components)
        .view(-1, *landmarks_transposed.shape[1:])
        .permute(0, 2, 1)
    )
    mean = (
        torch.from_numpy(pca.mean_)[None]
        .view(-1, *landmarks_transposed.shape[1:])
        .permute(0, 2, 1)
    )

    # explained variance and singular values have different shape than components since components also include mean
    return {
        "mean": mean,
        "components": components,
        "explained_variance": explained_variance_ratio,
        "singular_values": singular_values,
    }
