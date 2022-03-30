import numpy as np
import torch
import torch.nn.functional as F
from pytorch_lightning.core.mixins import DeviceDtypeModuleMixin

from medical_shape_building.airlab.utils import gaussian_kernel


class DemonsRegulariser(DeviceDtypeModuleMixin):
    def __init__(self, pixel_spacing):
        super().__init__()
        self._weight = 1
        self._dim = len(pixel_spacing)
        self._pixel_spacing = pixel_spacing
        self.name = "parent"


class GaussianRegulariser(DemonsRegulariser):
    def __init__(self, pixel_spacing, sigma):
        super().__init__(
            pixel_spacing,
        )

        sigma = np.array(sigma)

        if sigma.size != self._dim:
            sigma_app = sigma[-1]
            while sigma.size != self._dim:
                sigma = np.append(sigma, sigma_app)

        _kernel = gaussian_kernel(
            sigma, self._dim, asTensor=True, dtype=self.dtype, device=self.device
        )

        self._padding = (np.array(_kernel.size()) - 1) / 2
        self._padding = self._padding.astype(dtype=int).tolist()

        _kernel.unsqueeze_(0).unsqueeze_(0)
        _kernel = _kernel.expand(
            self._dim, *((np.ones(self._dim + 1, dtype=int) * -1).tolist())
        )
        _kernel = _kernel.to(dtype=self.dtype, device=self._device)
        self.register_buffer("_kernel", _kernel)

        if self._dim == 2:
            self._regulariser = self._regularise_2d
        elif self._dim == 3:
            self._regulariser = self._regularise_3d

    def _regularise_2d(self, data):

        data.data = data.data.unsqueeze(0)
        data.data = F.conv2d(
            data.data, self._kernel.contiguous(), padding=self._padding, groups=2
        )
        data.data = data.data.squeeze()

    def _regularise_3d(self, data):

        data.data = data.data.unsqueeze(0)
        data.data = F.conv3d(data.data, self._kernel, padding=self._padding, groups=3)
        data.data = data.data.squeeze()

    def forward(self, data):
        for parameter in data:
            # no gradient calculation for the demons regularisation
            with torch.no_grad():
                self._regulariser(parameter)
