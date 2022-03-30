from typing import Optional

import torch
from pytorch_lightning.core.mixins import DeviceDtypeModuleMixin
from torch.nn import functional as F

from medical_shape_building.airlab.image import RegistrationImage
from medical_shape_building.airlab.utils import compute_grid


class PairwiseImageLoss(DeviceDtypeModuleMixin):
    def __init__(
        self,
        fixed_image: RegistrationImage,
        moving_image: RegistrationImage,
        fixed_mask: Optional[torch.Tensor] = None,
        moving_mask: Optional[torch.Tensor] = None,
        size_average: bool = True,
        reduce: bool = True,
    ):
        super().__init__()
        self._size_average = size_average
        self._reduce = reduce
        self._name = "parent"

        self._warped_moving_image = None
        self._warped_moving_mask = None
        self._weight = 1

        self._moving_image = moving_image
        self._moving_mask = moving_mask
        self._fixed_image = fixed_image
        self._fixed_mask = fixed_mask

        assert self._moving_image != None and self._fixed_image != None
        # # TODO allow different image size for each image in the future
        # assert self._moving_image.image_size == self._fixed_image.image_size

        _grid = compute_grid(
            self._moving_image.image_size,
            dtype=self._moving_image.dtype,
            device=self._moving_image.device,
        )
        self.register_buffer("_grid", _grid)

        torch.cuda.empty_cache()

    @property
    def name(self):
        return self._name

    def get_warped_image(self):
        return self._warped_moving_image[0, 0, ...].detach().cpu()

    def get_current_mask(self, displacement):
        """Computes a mask defining if pixels are warped outside the image domain, or if they fall into a fixed
        image mask or a warped moving image mask.

        return (Tensor): maks array
        """
        # exclude points which are transformed outside the image domain
        mask = torch.zeros_like(
            self._fixed_image.image, dtype=torch.uint8, device=displacement.device
        )

        for dim in range(displacement.size()[-1]):
            mask += displacement[..., dim].gt(1) + displacement[..., dim].lt(-1)

        mask = mask == 0

        # and exclude points which are masked by the warped moving and the fixed mask
        if not self._moving_mask is None:
            self._warped_moving_mask = F.grid_sample(
                self._moving_mask.image, displacement
            )
            self._warped_moving_mask = self._warped_moving_mask >= 0.5

            # if either the warped moving mask or the fixed mask is zero take zero,
            # otherwise take the value of mask
            if not self._fixed_mask is None:
                mask = torch.where(
                    ((self._warped_moving_mask == 0) | (self._fixed_mask == 0)),
                    torch.zeros_like(mask),
                    mask,
                )
            else:
                mask = torch.where(
                    (self._warped_moving_mask == 0), torch.zeros_like(mask), mask
                )

        return mask

    def set_loss_weight(self, weight):
        self._weight = weight

    # conditional return
    def return_loss(self, tensor):
        if self._size_average and self._reduce:
            return tensor.mean() * self._weight
        if not self._size_average and self._reduce:
            return tensor.sum() * self._weight
        if not self.reduce:
            return tensor * self._weight


class MSE(PairwiseImageLoss):
    """The mean square error loss is a simple and fast to compute point-wise measure which is well suited for
    monomodal image registration.

    Args:
        fixed_image (Image): Fixed image for the registration
        moving_image (Image): Moving image for the registration
        size_average (bool): Average loss function
        reduce (bool): Reduce loss function to a single value
    """

    def __init__(
        self,
        fixed_image: RegistrationImage,
        moving_image: RegistrationImage,
        fixed_mask: Optional[torch.Tensor] = None,
        moving_mask: Optional[torch.Tensor] = None,
        size_average: bool = True,
        reduce: bool = True,
    ):
        super().__init__(
            fixed_image, moving_image, fixed_mask, moving_mask, size_average, reduce
        )

        self._name = "mse"

        self.warped_moving_image = None

    def forward(self, displacement):

        # compute displacement field
        displacement = self._grid + displacement

        # compute current mask
        mask = super().get_current_mask(displacement)

        # warp moving image with dispalcement field
        self.warped_moving_image = F.grid_sample(self._moving_image.image, displacement)

        # compute squared differences
        value = (self.warped_moving_image - self._fixed_image.image).pow(2)

        # mask values
        value = torch.masked_select(value, mask)
        torch.cuda.empty_cache()
        return self.return_loss(value)
