from typing import Optional, Tuple

import numpy as np
import SimpleITK as sitk
import torch
import torchio as tio
from pytorch_lightning.core.mixins import DeviceDtypeModuleMixin


class RegistrationImage(DeviceDtypeModuleMixin):
    def __init__(
        self,
        image: torch.Tensor,
        affine: torch.Tensor,
        image_type: str = tio.constants.INTENSITY,
    ):
        super().__init__()

        assert (
            image.ndim == 5
        ), "Image should be of format BxCxDxHxW, for 2D images set D=1"

        # Image should include batchsize and channels
        image_size = torch.tensor(image.shape[2:])

        self.register_buffer("image", image)
        self.register_buffer("image_size", image_size)
        self.register_buffer("affine", affine)
        self.image_type = image_type

    @property
    def spacing(self):
        return tuple(
            tio.data.io.get_rotation_and_spacing_from_affine(
                self.affine.detach().cpu().numpy()
            )[1].tolist()
        )

    @property
    def origin(self) -> Tuple[float, ...]:
        return tuple(self.affine[:3, 3].tolist())

    @property
    def ndim(self) -> int:
        if self.image_size[0] == 1:
            return 2
        else:
            return 3

    def to_itk(self):
        return self.to_torchio().as_sitk()

    def to_torchio(self):
        # flip affines from zyx to xyz
        flipped_affine = self.affine.cpu().detach()
        flipped_affine = flipped_affine[[2, 1, 0, 3]]
        flipped_affine = flipped_affine[:, [2, 1, 0, 3]]

        if self.image_type == tio.constants.INTENSITY:
            image_cls = tio.data.ScalarImage
            image_dtype = torch.float
        elif self.image_type == tio.constants.LABEL:
            image_cls = tio.data.LabelMap
            image_dtype = torch.uint8

        else:
            raise ValueError(
                f"Image Type should be one of {tio.constants.INTENSITY} and {tio.constants.LABEL} but got {self.image_type}"
            )
        # permute image from BCDHW to CWHD
        return image_cls(
            tensor=self.image.cpu().clone().permute(0, 1, 4, 3, 2)[0].to(image_dtype),
            affine=flipped_affine.numpy(),
        )

    @classmethod
    def from_torchio(cls, image: tio.data.Image):
        # flip affines from xyz auf zyx
        flipped_affine = torch.tensor(image.affine)
        flipped_affine = flipped_affine[[2, 1, 0, 3]]
        flipped_affine = flipped_affine[:, [2, 1, 0, 3]]
        return cls(
            # switch to BCDHW
            image.data[None].float().permute(0, 1, 4, 3, 2),
            affine=flipped_affine,
            image_type=image[tio.constants.TYPE],
        )

    @classmethod
    def from_itk(cls, image: sitk.Image):
        return cls.from_torchio(tio.Image.from_sitk(image))

    @classmethod
    def from_torch(
        cls,
        image: torch.Tensor,
        affine: Optional[torch.Tensor] = None,
        image_type: str = tio.constants.INTENSITY,
    ):
        while image.ndim < 5:
            image = image[None]

        while image.ndim > 5:
            image = image[0]

        if affine is None:
            affine = torch.eye(4, device=image.device, dtype=image.dtype)

        return cls(image=image, affine=affine, image_type=image_type).to(
            image.device, image.dtype
        )

    def to_torch(self) -> torch.Tensor:
        return self.image

    def to_numpy(self):
        return self.to_torch().cpu().detach().numpy()


class RegistrationDisplacement(RegistrationImage):
    @classmethod
    def from_torch(
        cls,
        displacement: torch.Tensor,
        affine: Optional[torch.Tensor] = None,
        image_type: str = tio.constants.INTENSITY,
    ):

        # remove channels here
        displacement = displacement[:, 0, ...]

        # move from BxDxHxWxN to BxNxDxHxW (treat DiplacementVectors N as channels)
        displacement = displacement.permute(0, 4, 1, 2, 3)

        if image_type != tio.constants.INTENSITY:
            raise ValueError(
                f"Displacement image type should be {tio.constants.INTENSITY} but got {image_type}"
            )
        return super().from_torch(
            image=displacement, affine=affine, image_type=image_type
        )

    def to_torch(self) -> torch.Tensor:
        displacement = self.image.permute(0, 2, 3, 4, 1)
        displacement = displacement[:, None]
        return displacement

    def to_itk(self) -> sitk.Image:

        # flip affine back to nib format used by torchio
        flipped_affine = self.affine.cpu().detach()
        flipped_affine = flipped_affine[[2, 1, 0, 3]]
        flipped_affine = flipped_affine[:, [2, 1, 0, 3]]
        origin, spacing, direction = tio.data.io.get_sitk_metadata_from_ras_affine(
            flipped_affine.numpy()
        )

        displacement = (
            self.image.clone().permute(0, 2, 3, 4, 1).cpu().detach().double()[0]
        )

        # scale by shape
        for dim in range(displacement.size(-1)):
            displacement[..., dim] = (
                float(displacement.size(-dim - 2) - 1) * displacement[..., dim] / 2
            )
            # displacement[:, dim] = (
            #     displacement[:, dim] * displacement.size(-(dim + 1)) / 2
            # )

        # revert order to SITK order (D,H,W)
        displacement = (
            torch.flip(displacement, dims=(-1,))
            .permute(*range(displacement.ndim - 2, -1, -1), displacement.ndim - 1)
            .numpy()
        )

        if self.ndim == 2:
            itk_displacement = sitk.GetImageFromArray(displacement, isVector=True)
        elif self.ndim == 3:
            itk_displacement = sitk.GetImageFromArray(displacement)

        # For some reason, I cannot set these as a plain list or tuple but need to convert from numpy back to list
        # Don't exactly know why, but this works
        # Assumption is that there is some issue with the underlying dtype mapping
        itk_displacement.SetSpacing(np.array(spacing, dtype="float32").tolist())
        itk_displacement.SetOrigin(np.array(origin, dtype="float32").tolist())
        itk_displacement.SetDirection(np.array(direction, dtype="float32").tolist())

        return itk_displacement

    def itk_transform(self) -> sitk.Transform:
        itk_disp = self.to_itk()
        trans = sitk.DisplacementFieldTransform(itk_disp)
        return trans

    def magnitude(self):
        return RegistrationImage(
            torch.sqrt(torch.sum(self.image.pow(2), -1)).squeeze(), self.affine
        )


def _flip(x, dim):
    """Flip order of a specific dimension dim.

    x (Tensor): input tensor dim (int): axis which should be flipped return (Tensor): returns the tensor with the
    specified axis flipped
    """
    indices = [slice(None)] * x.dim()
    indices[dim] = torch.arange(
        x.size(dim) - 1, -1, -1, dtype=torch.long, device=x.device
    )
    return x[tuple(indices)]
