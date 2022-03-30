from typing import Optional

import torchio as tio
from matplotlib import pyplot as plt
from medical_shape import Shape
from skimage.segmentation import find_boundaries


def visualize_shape(
    shape: Shape,
    axes: Optional[plt.Axes] = None,
    sub_sample_factor: int = 1,
    color: str = "orange",
    marker_size: int = 2,
    **kwargs,
):
    if axes is None:
        figure = plt.figure(**kwargs)
        axes = figure.add_subplot(projection="3d")

    axes.scatter(
        shape.tensor[..., ::sub_sample_factor, 0].flatten(),
        shape.tensor[..., ::sub_sample_factor, 1].flatten(),
        shape.tensor[..., ::sub_sample_factor, 2].flatten(),
        s=marker_size,
        c=color,
    )
    return axes


def visualize_volume(
    image: tio.data.Image,
    axes: Optional[plt.Axes] = None,
    bone_structure_index: Optional[int] = None,
    boundaries_only: bool = True,
    color: str = "gray",
    **kwargs,
):
    if axes is None:
        figure = plt.figure(**kwargs)
        axes = figure.add_subplot(
            projection="3d",
        )

    volume = image.tensor.cpu().detach().numpy().squeeze().transpose(2, 1, 0)

    if bone_structure_index is not None:
        volume = volume == bone_structure_index

    if boundaries_only:
        volume = find_boundaries(volume)
    axes.voxels(volume, facecolors=color, edgecolors=color)
    return axes
