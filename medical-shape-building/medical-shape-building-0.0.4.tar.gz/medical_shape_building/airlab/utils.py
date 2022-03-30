# Copyright 2018 University of Basel, Center for medical Image Analysis and Navigation
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from typing import Optional, Sequence, Union

import numpy as np
import SimpleITK as sitk
import torch
from pytorch_lightning.core.mixins import DeviceDtypeModuleMixin
from rising.transforms.functional.affine import matrix_to_homogeneous
from scipy.spatial.distance import dice as dice_dissimilarity
from torch.nn import functional as F

from medical_shape_building.airlab.image import (
    RegistrationDisplacement,
    RegistrationImage,
)


def parse_devices(device: Optional[Union[str, torch.device]]) -> str:

    # autodetect devices
    if device is None:
        if torch.cuda.is_available():
            device = "cuda"
        else:
            device = "cpu"

    # map to uniform type of torch.device
    if isinstance(device, str):
        device = torch.device(device)

    # Map back to something Lightning understands
    device = device.type

    if device == "cuda":
        device = "gpu"

    return device


def dice_coefficient(image1: sitk.Image, image2: sitk.Image) -> float:
    """Takes two SimpleITK images as input, converts them to numpy array and flattens them to apply the scipy dice
    dissimilarity.

    Returns dice coefficient
    Args:
        image1: input image
        image2: second input image to calculate dice similarity
    Returns:
        float: the dice coefficient between the two input images
    """
    assert isinstance(image1, sitk.Image) and isinstance(
        image2, sitk.Image
    ), "Input class mismatch"

    array1 = sitk.GetArrayFromImage(image1).flatten()
    array2 = sitk.GetArrayFromImage(image2).flatten()
    _dice_dissimilarity = dice_dissimilarity(array1, array2)

    return 1 - _dice_dissimilarity


def create_image_pyramid(
    image: RegistrationImage, down_sample_factor: Sequence[Sequence[int]]
):

    image_dim = len(image.image_size)
    image_pyramide = []
    if image_dim == 2:
        for level in down_sample_factor:
            level_tensor = torch.tensor(level, device=image.device)
            if len(level_tensor) != image_dim:
                level_tensor = level_tensor.repeat(image_dim / len(level_tensor))
            sigma = (level_tensor / 2).to(dtype=torch.float32)

            kernel = gaussian_kernel_2d(sigma.numpy(), asTensor=True)
            padding = np.array([(x - 1) / 2 for x in kernel.size()], dtype=int).tolist()
            kernel = kernel.unsqueeze(0).unsqueeze(0)
            kernel = kernel.to(dtype=image.dtype, device=image.device)

            image_sample = F.conv2d(image.image, kernel, stride=level, padding=padding)

            image_affine = (
                matrix_to_homogeneous(
                    torch.eye(3, device=image.device, dtype=image.affine.dtype)[None]
                    * level_tensor
                )[0]
                @ image.affine
            )

            image_pyramide.append(
                RegistrationImage(
                    image_sample,
                    image_affine,
                )
            )

        image_pyramide.append(image)
    elif image_dim == 3:
        for level in down_sample_factor:
            level_tensor = torch.tensor(level, device=image.device)
            if len(level_tensor) != image_dim:
                level_tensor = level_tensor.repeat(image_dim / len(level_tensor))
            sigma = (level_tensor / 2).to(dtype=torch.float32)

            kernel = gaussian_kernel_3d(sigma.numpy(), asTensor=True)
            padding = np.array([(x - 1) / 2 for x in kernel.size()], dtype=int).tolist()
            kernel = kernel.unsqueeze(0).unsqueeze(0)
            kernel = kernel.to(dtype=image.dtype, device=image.device)

            image_sample = F.conv3d(image.image, kernel, stride=level, padding=padding)

            image_affine = (
                matrix_to_homogeneous(
                    torch.eye(3, device=image.device, dtype=image.affine.dtype)[None]
                    * level_tensor
                )[0]
                @ image.affine
            )

            image_pyramide.append(
                RegistrationImage(
                    image_sample,
                    image_affine,
                )
            )

        image_pyramide.append(image)

    else:
        raise ValueError(
            f"{image_dim} is not supported with create_image_pyramide. Dimension should be 2 or 3."
        )

    return image_pyramide


def compute_grid(image_size, dtype=torch.float32, device="cpu"):

    dim = len(image_size)

    if dim == 2:
        nx = image_size[0]
        ny = image_size[1]

        x = torch.linspace(-1, 1, steps=ny).to(dtype=dtype)
        y = torch.linspace(-1, 1, steps=nx).to(dtype=dtype)

        x = x.expand(nx, -1)
        y = y.expand(ny, -1).transpose(0, 1)

        x.unsqueeze_(0).unsqueeze_(3)
        y.unsqueeze_(0).unsqueeze_(3)

        return torch.cat((x, y), 3).to(dtype=dtype, device=device)

    elif dim == 3:
        nz = image_size[0]
        ny = image_size[1]
        nx = image_size[2]

        x = torch.linspace(-1, 1, steps=nx).to(dtype=dtype)
        y = torch.linspace(-1, 1, steps=ny).to(dtype=dtype)
        z = torch.linspace(-1, 1, steps=nz).to(dtype=dtype)

        x = x.expand(ny, -1).expand(nz, -1, -1)
        y = y.expand(nx, -1).expand(nz, -1, -1).transpose(1, 2)
        z = z.expand(nx, -1).transpose(0, 1).expand(ny, -1, -1).transpose(0, 1)

        x.unsqueeze_(0).unsqueeze_(4)
        y.unsqueeze_(0).unsqueeze_(4)
        z.unsqueeze_(0).unsqueeze_(4)

        torch.cuda.empty_cache()
        return torch.cat((x, y, z), 4).to(dtype=dtype, device=device)
    else:
        raise ValueError(f"{dim} is not a valid grid dimensionality.")


def upsample_displacement(displacement, new_size, interpolation="linear"):
    dim = displacement.size()[-1]
    if dim == 2:
        displacement = torch.transpose(displacement.unsqueeze(0), 0, 3).unsqueeze(0)
        if interpolation == "linear":
            interpolation = "bilinear"
        else:
            interpolation = "nearest"
    elif dim == 3:
        displacement = torch.transpose(displacement.unsqueeze(0), 0, 4).unsqueeze(0)
        if interpolation == "linear":
            interpolation = "trilinear"
        else:
            interpolation = "nearest"

    if isinstance(new_size, (torch.Tensor, np.ndarray)):
        new_size = new_size.tolist()

    upsampled_displacement = F.interpolate(
        displacement[..., 0], size=new_size, mode=interpolation, align_corners=False
    )

    if dim == 2:
        upsampled_displacement = torch.transpose(
            upsampled_displacement.unsqueeze(-1), 1, -1
        )
    elif dim == 3:
        upsampled_displacement = torch.transpose(
            upsampled_displacement.unsqueeze(-1), 1, -1
        )

    return upsampled_displacement[0, 0, ...]


def warp_image(image, displacement, affine: Optional[torch.Tensor] = None):

    image_size = image.image_size

    grid = compute_grid(image_size, dtype=image.dtype, device=image.device)

    # warp image
    warped_image = F.grid_sample(image.image, displacement.to(image.device) + grid)

    image_affine = image.affine

    if affine is not None:
        image_affine = (
            matrix_to_homogeneous(affine[None])[0].to(image_affine) @ image_affine
        )
    return RegistrationImage(warped_image, image_affine)


def displacement_to_unit_displacement(displacement):
    # scale displacements from image
    # domain to 2square
    # - last dimension are displacements
    if isinstance(displacement, RegistrationDisplacement):
        df = displacement.image
    else:
        df = displacement

    for dim in range(df.shape[-1]):
        df[..., dim] = 2.0 * df[..., dim] / float(df.shape[-dim - 2] - 1)

    return displacement


def unit_displacement_to_displacement(displacement):
    # scale displacements from 2square
    # domain to image domain
    # - last dimension are displacements
    if isinstance(displacement, RegistrationDisplacement):
        df = displacement.image[0, 0]
    else:
        df = displacement

    # manipulate displacement field
    for dim in range(df.shape[-1]):
        df[..., dim] = float(df.shape[-dim - 2] - 1) * df[..., dim] / 2.0

    return displacement


def get_displacement_itk(displacement):
    displacement = displacement.detach().clone()
    unit_displacement_to_displacement(displacement)
    dispIm = sitk.GetImageFromArray(
        displacement.cpu().double(),
        # .transpose(list(range(dim - 1, -1, -1)) + [dim])[
        # simpleitk image in numpy: D, H, W
        isVector=True,
    )

    trans = sitk.DisplacementFieldTransform(dispIm)
    return trans


def rotation_matrix(
    phi_x, phi_y, phi_z, dtype=torch.float32, device="cpu", homogene=False
):
    R_x = torch.Tensor(
        [
            [1, 0, 0],
            [0, torch.cos(phi_x), -torch.sin(phi_x)],
            [0, torch.sin(phi_x), torch.cos(phi_x)],
        ]
    )
    R_y = torch.Tensor(
        [
            [torch.cos(phi_y), 0, torch.sin(phi_y)],
            [0, 1, 0],
            [-torch.sin(phi_y), 0, torch.cos(phi_y)],
        ]
    )
    R_z = torch.Tensor(
        [
            [torch.cos(phi_z), -torch.sin(phi_z), 0],
            [torch.sin(phi_z), torch.cos(phi_z), 0],
            [0, 0, 1],
        ]
    )

    matrix = torch.mm(torch.mm(R_z, R_y), R_x).to(dtype=dtype, device=device)

    if homogene:
        matrix_homogene = torch.zeros(4, 4, dtype=dtype, device=device)
        matrix_homogene[3, 3] = 1
        matrix_homogene[0:3, 0:3] = matrix

        matrix = matrix_homogene

    return matrix


class Diffeomorphic(DeviceDtypeModuleMixin):
    r"""
    Diffeomorphic transformation. This class computes the matrix exponential of a given flow field using the scaling
    and squaring algorithm according to:
              Unsupervised Learning for Fast Probabilistic Diffeomorphic Registration
              Adrian V. Dalca, Guha Balakrishnan, John Guttag, Mert R. Sabuncu
              MICCAI 2018
              and
              Diffeomorphic Demons: Efficient Non-parametric Image Registration
              Tom Vercauterena et al., 2008

    """

    def __init__(self, image_size, scaling=10):

        super().__init__()
        self._dim = len(image_size)
        self._image_size = image_size
        self._scaling = scaling
        self._init_scaling = 8

        if image_size is not None:
            _image_grid = compute_grid(image_size, dtype=self.dtype, device=self.device)
        else:
            _image_grid = None

        self.register_buffer("_image_grid", _image_grid)

    def set_image_size(self, image_szie):
        self._image_size = image_szie
        self._image_grid = compute_grid(
            self._image_size, dtype=self._dtype, device=self._device
        )

    def calculate(self, displacement):
        if self._dim == 2:
            return Diffeomorphic.diffeomorphic_2D(
                displacement, self._image_grid, self._scaling
            )
        else:
            return Diffeomorphic.diffeomorphic_3D(
                displacement, self._image_grid, self._scaling
            )

    @staticmethod
    def _compute_scaling_value(displacement):

        with torch.no_grad():
            scaling = 8
            norm = torch.norm(displacement / (2 ** scaling))

            while norm > 0.5:
                scaling += 1
                norm = torch.norm(displacement / (2 ** scaling))

        return scaling

    @staticmethod
    def diffeomorphic_2D(displacement, grid, scaling=-1):

        if scaling < 0:
            scaling = Diffeomorphic._compute_scaling_value(displacement)

        displacement = displacement / (2 ** scaling)

        displacement = displacement.transpose(2, 1).transpose(1, 0).unsqueeze(0)

        for _ in range(scaling):
            displacement_trans = displacement.transpose(1, 2).transpose(2, 3)
            displacement = displacement + F.grid_sample(
                displacement, displacement_trans + grid
            )

        return displacement.transpose(1, 2).transpose(2, 3).squeeze()

    @staticmethod
    def diffeomorphic_3D(displacement, grid, scaling=-1):
        displacement = displacement / (2 ** scaling)
        torch.cuda.empty_cache()
        displacement = (
            displacement.transpose(3, 2).transpose(2, 1).transpose(0, 1).unsqueeze(0)
        )

        for _ in range(scaling):
            displacement_trans = (
                displacement.transpose(1, 2).transpose(2, 3).transpose(3, 4)
            )
            displacement = displacement + F.grid_sample(
                displacement, displacement_trans + grid
            )

        return displacement.transpose(1, 2).transpose(2, 3).transpose(3, 4).squeeze()


def gaussian_kernel_1d(sigma, asTensor=False, dtype=torch.float32, device="cpu"):

    kernel_size = int(2 * np.ceil(sigma * 2) + 1)

    x = np.linspace(-(kernel_size - 1) // 2, (kernel_size - 1) // 2, num=kernel_size)

    kernel = 1.0 / (sigma * np.sqrt(2 * np.pi)) * np.exp(-(x ** 2) / (2 * sigma ** 2))
    kernel = kernel / np.sum(kernel)

    if asTensor:
        return torch.tensor(kernel, dtype=dtype, device=device)
    else:
        return kernel


def gaussian_kernel_2d(sigma, asTensor=False, dtype=torch.float32, device="cpu"):

    y_1 = gaussian_kernel_1d(sigma[0])
    y_2 = gaussian_kernel_1d(sigma[1])

    kernel = np.tensordot(y_1, y_2, 0)
    kernel = kernel / np.sum(kernel)

    if asTensor:
        return torch.tensor(kernel, dtype=dtype, device=device)
    else:
        return kernel


def gaussian_kernel_3d(sigma, asTensor=False, dtype=torch.float32, device="cpu"):

    kernel_2d = gaussian_kernel_2d(sigma[:2])
    kernel_1d = gaussian_kernel_1d(sigma[-1])

    kernel = np.tensordot(kernel_2d, kernel_1d, 0)
    kernel = kernel / np.sum(kernel)

    if asTensor:
        return torch.tensor(kernel, dtype=dtype, device=device)
    else:
        return kernel


def gaussian_kernel(sigma, dim=1, asTensor=False, dtype=torch.float32, device="cpu"):

    assert dim > 0 and dim <= 3

    if dim == 1:
        return gaussian_kernel_1d(sigma, asTensor=asTensor, dtype=dtype, device=device)
    elif dim == 2:
        return gaussian_kernel_2d(sigma, asTensor=asTensor, dtype=dtype, device=device)
    else:
        return gaussian_kernel_3d(sigma, asTensor=asTensor, dtype=dtype, device=device)
