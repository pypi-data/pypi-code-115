from typing import Optional

import torch
from pytorch_lightning.core.mixins import DeviceDtypeModuleMixin

from medical_shape_building.airlab.image import RegistrationImage
from medical_shape_building.airlab.utils import compute_grid, Diffeomorphic


class Transformation(DeviceDtypeModuleMixin):

    _diffeomorphic_calculator: Optional[Diffeomorphic]

    def __init__(
        self,
        moving_image: RegistrationImage,
        fixed_image: RegistrationImage,
        diffeomorphic: bool,
    ):

        super().__init__()

        image_size = fixed_image.image_size
        self._dim = len(image_size)
        if not isinstance(image_size, torch.Tensor):
            image_size = torch.tensor(image_size)
        self._image_size = image_size
        self._constant_displacement = None
        self._diffeomorphic = diffeomorphic
        self.register_buffer("_constant_flow", None)

        self._compute_flow = None

        if self._diffeomorphic:
            self._diffeomorphic_calculator = Diffeomorphic(image_size)
        else:
            self._diffeomorphic_calculator = None

    def get_flow(self):

        if self._constant_flow is None:
            return self.compute_flow().detach()
        else:
            return self.compute_flow().detach() + self._constant_flow

    def set_constant_flow(self, flow):
        self._constant_flow = flow

    def get_displacement_numpy(self):

        if self._dim == 2:
            return torch.unsqueeze(self().detach(), 0).cpu().numpy()
        elif self._dim == 3:
            return self().detach().cpu().numpy()

    def get_displacement(self):
        return self().detach()

    def get_inverse_displacement(self):

        flow = self._concatenate_flows(self._compute_flow()).detach()

        if self._diffeomorphic:
            inv_displacement = self._diffeomorphic_calculator.calculate(flow * -1)
        else:
            print("error displacement ")
            inv_displacement = None

        return inv_displacement

    def _compute_diffeomorphic_displacement(self, flow):

        return self._diffeomorphic_calculator.calculate(flow)

    def _concatenate_flows(self, flow):

        if self._constant_flow is None:
            return flow
        else:
            return flow + self._constant_flow


class RigidTransformation(Transformation):
    r"""
    Rigid centred transformation for 2D and 3D.

    Args:
        moving_image (Image): moving image for the registration
        opt_cm (bool): using center of as parameter for the optimisation
    """

    def __init__(
        self,
        moving_image: RegistrationImage,
        fixed_image: RegistrationImage,
        opt_cm: bool = False,
    ):
        super().__init__(moving_image, fixed_image, diffeomorphic=False)

        self._opt_cm = opt_cm

        grid = torch.squeeze(compute_grid(fixed_image.image_size, dtype=self.dtype))

        grid = torch.cat(
            (
                grid,
                torch.ones(*[list(fixed_image.image_size) + [1]], dtype=self.dtype),
            ),
            self._dim,
        ).to(device=self.device)

        self.register_buffer("_grid", grid)

        # compute the initial center of mass of the moving image
        intensity_sum = torch.sum(moving_image.image)

        self._center_mass_x = (
            torch.sum(moving_image.image.squeeze() * self._grid[..., 0]) / intensity_sum
        )
        self._center_mass_y = (
            torch.sum(moving_image.image.squeeze() * self._grid[..., 1]) / intensity_sum
        )

        self._phi_z = torch.nn.Parameter(torch.tensor(0.0))
        self._t_x = torch.nn.Parameter(torch.tensor(0.0))
        self._t_y = torch.nn.Parameter(torch.tensor(0.0))

        self._trans_matrix_pos = None
        self._trans_matrix_cm = None
        self._trans_matrix_cm_rw = None
        self._rotation_matrix = None

        if self._opt_cm:
            self._center_mass_x = torch.nn.Parameter(self._center_mass_x)
            self._center_mass_y = torch.nn.Parameter(self._center_mass_y)

        if self._dim == 2:
            self._compute_transformation = self._compute_transformation_2d

        else:
            self._compute_transformation = self._compute_transformation_3d

            self._center_mass_z = (
                torch.sum(moving_image.image.squeeze() * self._grid[..., 2])
                / intensity_sum
            )

            self._t_z = torch.nn.Parameter(torch.tensor(0.0))
            self._phi_x = torch.nn.Parameter(torch.tensor(0.0))
            self._phi_y = torch.nn.Parameter(torch.tensor(0.0))

            if self._opt_cm:
                self._center_mass_z = torch.nn.Parameter(self._center_mass_z)

    def init_translation(self, fixed_image):
        r"""
        Initialize the translation parameters with the difference between the center of mass of the
        fixed and the moving image

        Args:
            fixed_image (Image): Fixed image for the registration
        """
        intensity_sum = torch.sum(fixed_image.image)

        fixed_image_center_mass_x = (
            torch.sum(fixed_image.image.squeeze() * self._grid[..., 0]) / intensity_sum
        )
        fixed_image_center_mass_y = (
            torch.sum(fixed_image.image.squeeze() * self._grid[..., 1]) / intensity_sum
        )

        self._t_x = torch.nn.Parameter(self._center_mass_x - fixed_image_center_mass_x)
        self._t_y = torch.nn.Parameter(self._center_mass_y - fixed_image_center_mass_y)

        if self._dim == 3:
            fixed_image_center_mass_z = (
                torch.sum(fixed_image.image.squeeze() * self._grid[..., 2])
                / intensity_sum
            )
            self._t_z = torch.nn.Parameter(
                self._center_mass_z - fixed_image_center_mass_z
            )

    @property
    def transformation_matrix(self):
        self._compute_transformation()
        return self._compute_transformation_matrix()

    def set_parameters(self, t, phi, rotation_center=None):
        """Set parameters manually.

        t (array): 2 or 3 dimensional array specifying the spatial translation phi (array): 1 or 3 dimensional array
        specifying the rotation angles rotation_center (array): 2 or 3 dimensional array specifying the rotation center
        (default is zeros)
        """
        self._t_x = torch.nn.Parameter(
            torch.tensor(t[0]).to(dtype=self.dtype, device=self.device)
        )
        self._t_y = torch.nn.Parameter(
            torch.tensor(t[1]).to(dtype=self.dtype, device=self.device)
        )
        self._phi_z = torch.nn.Parameter(
            torch.tensor(phi[0]).to(dtype=self.dtype, device=self.device)
        )

        if rotation_center is not None:
            self._center_mass_x = rotation_center[0]
            self._center_mass_y = rotation_center[1]

        if len(t) == 2:
            self._compute_transformation_2d()
        else:
            self._t_z = torch.nn.Parameter(
                torch.tensor(t[2]).to(dtype=self.dtype, device=self.device)
            )
            self._phi_x = torch.nn.Parameter(
                torch.tensor(phi[1]).to(dtype=self.dtype, device=self.device)
            )
            self._phi_y = torch.nn.Parameter(
                torch.tensor(phi[2]).to(dtype=self.dtype, device=self.device)
            )
            if rotation_center is not None:
                self._center_mass_z = rotation_center[1]

            self._compute_transformation_3d()

    def _compute_transformation_2d(self):

        self._trans_matrix_pos = torch.diag(
            torch.ones(self._dim + 1, dtype=self.dtype, device=self.device)
        )
        self._trans_matrix_cm = torch.diag(
            torch.ones(self._dim + 1, dtype=self.dtype, device=self.device)
        )
        self._trans_matrix_cm_rw = torch.diag(
            torch.ones(self._dim + 1, dtype=self.dtype, device=self.device)
        )
        self._rotation_matrix = torch.zeros(
            self._dim + 1, self._dim + 1, dtype=self.dtype, device=self.device
        )
        self._rotation_matrix[-1, -1] = 1

        self._trans_matrix_pos[0, 2] = self._t_x
        self._trans_matrix_pos[1, 2] = self._t_y

        self._trans_matrix_cm[0, 2] = -self._center_mass_x
        self._trans_matrix_cm[1, 2] = -self._center_mass_y

        self._trans_matrix_cm_rw[0, 2] = self._center_mass_x
        self._trans_matrix_cm_rw[1, 2] = self._center_mass_y

        self._rotation_matrix[0, 0] = torch.cos(self._phi_z)
        self._rotation_matrix[0, 1] = -torch.sin(self._phi_z)
        self._rotation_matrix[1, 0] = torch.sin(self._phi_z)
        self._rotation_matrix[1, 1] = torch.cos(self._phi_z)

    def _compute_transformation_3d(self):

        self._trans_matrix_pos = torch.diag(
            torch.ones(self._dim + 1, dtype=self.dtype, device=self.device)
        )
        self._trans_matrix_cm = torch.diag(
            torch.ones(self._dim + 1, dtype=self.dtype, device=self.device)
        )
        self._trans_matrix_cm_rw = torch.diag(
            torch.ones(self._dim + 1, dtype=self.dtype, device=self.device)
        )

        self._trans_matrix_pos[0, 3] = self._t_x
        self._trans_matrix_pos[1, 3] = self._t_y
        self._trans_matrix_pos[2, 3] = self._t_z

        self._trans_matrix_cm[0, 3] = -self._center_mass_x
        self._trans_matrix_cm[1, 3] = -self._center_mass_y
        self._trans_matrix_cm[2, 3] = -self._center_mass_z

        self._trans_matrix_cm_rw[0, 3] = self._center_mass_x
        self._trans_matrix_cm_rw[1, 3] = self._center_mass_y
        self._trans_matrix_cm_rw[2, 3] = self._center_mass_z

        R_x = torch.diag(
            torch.ones(self._dim + 1, dtype=self.dtype, device=self.device)
        )
        R_x[1, 1] = torch.cos(self._phi_x)
        R_x[1, 2] = -torch.sin(self._phi_x)
        R_x[2, 1] = torch.sin(self._phi_x)
        R_x[2, 2] = torch.cos(self._phi_x)

        R_y = torch.diag(
            torch.ones(self._dim + 1, dtype=self.dtype, device=self.device)
        )
        R_y[0, 0] = torch.cos(self._phi_y)
        R_y[0, 2] = torch.sin(self._phi_y)
        R_y[2, 0] = -torch.sin(self._phi_y)
        R_y[2, 2] = torch.cos(self._phi_y)

        R_z = torch.diag(
            torch.ones(self._dim + 1, dtype=self.dtype, device=self.device)
        )
        R_z[0, 0] = torch.cos(self._phi_z)
        R_z[0, 1] = -torch.sin(self._phi_z)
        R_z[1, 0] = torch.sin(self._phi_z)
        R_z[1, 1] = torch.cos(self._phi_z)

        self._rotation_matrix = torch.mm(torch.mm(R_z, R_y), R_x)

    def _compute_transformation_matrix(self):
        transformation_matrix = torch.mm(
            torch.mm(
                torch.mm(self._trans_matrix_pos, self._trans_matrix_cm),
                self._rotation_matrix,
            ),
            self._trans_matrix_cm_rw,
        )[0 : self._dim, :]
        return transformation_matrix

    def _compute_dense_flow(self, transformation_matrix):

        displacement = (
            torch.mm(
                self._grid.view(torch.prod(self._image_size).tolist(), self._dim + 1),
                transformation_matrix.t(),
            ).view(*(self._image_size.tolist()), self._dim)
            - self._grid[..., : self._dim]
        )
        return displacement

    def print(self):
        for name, param in self.named_parameters():
            print(name, param.item())

    def compute_flow(self):
        return self._compute_dense_flow(self.transformation_matrix)

    def compute_displacement(self, transformation_matrix):
        return self._compute_dense_flow(transformation_matrix)

    def forward(self):

        self._compute_transformation()
        transformation_matrix = self._compute_transformation_matrix()
        flow = self._compute_dense_flow(transformation_matrix)

        return self._concatenate_flows(flow)


class SimilarityTransformation(RigidTransformation):
    r"""
    Similarity centred transformation for 2D and 3D.
    Args:
        moving_image (Image): moving image for the registration
        opt_cm (bool): using center of as parameter for the optimisation
    """

    def __init__(
        self,
        moving_image: RegistrationImage,
        fixed_image: RegistrationImage,
        opt_cm: bool = False,
    ):
        super().__init__(moving_image, fixed_image, opt_cm)

        self._scale_x = torch.nn.Parameter(torch.tensor(1.0))
        self._scale_y = torch.nn.Parameter(torch.tensor(1.0))

        self._scale_matrix = None

        if self._dim == 2:
            self._compute_transformation = self._compute_transformation_2d
        else:
            self._compute_transformation = self._compute_transformation_3d

            self._scale_z = torch.nn.Parameter(torch.tensor(1.0))

    def set_parameters(self, t, phi, scale, rotation_center=None):
        """Set parameters manually.

        t (array): 2 or 3 dimensional array specifying the spatial translation phi (array): 1 or 3 dimensional array
        specifying the rotation angles scale (array): 2 or 3 dimensional array specifying the scale in each dimension
        rotation_center (array): 2 or 3 dimensional array specifying the rotation center (default is zeros)
        """
        super().set_parameters(t, phi, rotation_center)

        self._scale_x = torch.nn.Parameter(
            torch.tensor(scale[0]).to(dtype=self.dtype, device=self.device)
        )
        self._scale_y = torch.nn.Parameter(
            torch.tensor(scale[1]).to(dtype=self.dtype, device=self.device)
        )

        if len(t) == 2:
            self._compute_transformation_2d()
        else:
            self._scale_z = torch.nn.Parameter(
                torch.tensor(scale[2]).to(dtype=self.dtype, device=self.device)
            )
            self._compute_transformation_3d()

    def _compute_transformation_2d(self):

        super()._compute_transformation_2d()

        self._scale_matrix = torch.diag(
            torch.ones(self._dim + 1, dtype=self.dtype, device=self.device)
        )

        self._scale_matrix[0, 0] = self._scale_x
        self._scale_matrix[1, 1] = self._scale_y

    def _compute_transformation_3d(self):

        super()._compute_transformation_3d()

        self._scale_matrix = torch.diag(
            torch.ones(self._dim + 1, dtype=self.dtype, device=self.device)
        )

        self._scale_matrix[0, 0] = self._scale_x
        self._scale_matrix[1, 1] = self._scale_y
        self._scale_matrix[2, 2] = self._scale_z

    def _compute_transformation_matrix(self):
        transformation_matrix = torch.mm(
            torch.mm(
                torch.mm(
                    torch.mm(self._trans_matrix_pos, self._trans_matrix_cm),
                    self._rotation_matrix,
                ),
                self._scale_matrix,
            ),
            self._trans_matrix_cm_rw,
        )[0 : self._dim, :]

        return transformation_matrix

    def forward(self):

        self._compute_transformation()
        transformation_matrix = self._compute_transformation_matrix()
        flow = self._compute_dense_flow(transformation_matrix)

        return self._concatenate_flows(flow)


class AffineTransformation(SimilarityTransformation):
    """Affine centred transformation for 2D and 3D.

    Args:
        moving_image (Image): moving image for the registration
        opt_cm (bool): using center of as parameter for the optimisation
    """

    def __init__(
        self,
        moving_image: RegistrationImage,
        fixed_image: RegistrationImage,
        opt_cm: bool = False,
    ):
        super().__init__(moving_image, fixed_image, opt_cm)

        self._shear_y_x = torch.nn.Parameter(torch.tensor(0.0))
        self._shear_x_y = torch.nn.Parameter(torch.tensor(0.0))

        self._shear_matrix = None

        if self._dim == 2:
            self._compute_displacement = self._compute_transformation_2d
        else:
            self._compute_displacement = self._compute_transformation_3d

            self._shear_z_x = torch.nn.Parameter(torch.tensor(0.0))
            self._shear_z_y = torch.nn.Parameter(torch.tensor(0.0))
            self._shear_x_z = torch.nn.Parameter(torch.tensor(0.0))
            self._shear_y_z = torch.nn.Parameter(torch.tensor(0.0))

    def set_parameters(self, t, phi, scale, shear, rotation_center=None):
        """Set parameters manually.

        t (array): 2 or 3 dimensional array specifying the spatial translation phi (array): 1 or 3 dimensional array
        specifying the rotation angles scale (array): 2 or 3 dimensional array specifying the scale in each dimension
        shear (array): 2 or 6 dimensional array specifying the shear in each dimension: yx, xy, zx, zy, xz, yz
        rotation_center (array): 2 or 3 dimensional array specifying the rotation center (default is zeros)
        """
        super().set_parameters(t, phi, scale, rotation_center)

        self._shear_y_x = torch.nn.Parameter(
            torch.tensor(shear[0]).to(dtype=self.dtype, device=self.device)
        )
        self._shear_x_y = torch.nn.Parameter(
            torch.tensor(shear[1]).to(dtype=self.dtype, device=self.device)
        )

        if len(t) == 2:
            self._compute_transformation_2d()
        else:
            self._shear_z_x = torch.nn.Parameter(
                torch.tensor(shear[2]).to(dtype=self.dtype, device=self.device)
            )
            self._shear_z_y = torch.nn.Parameter(
                torch.tensor(shear[3]).to(dtype=self.dtype, device=self.device)
            )
            self._shear_x_z = torch.nn.Parameter(
                torch.tensor(shear[4]).to(dtype=self.dtype, device=self.device)
            )
            self._shear_y_z = torch.nn.Parameter(
                torch.tensor(shear[5]).to(dtype=self.dtype, device=self.device)
            )
            self._compute_transformation_3d()

    def _compute_transformation_2d(self):

        super()._compute_transformation_2d()

        self._shear_matrix = torch.diag(
            torch.ones(self._dim + 1, dtype=self.dtype, device=self.device)
        )

        self._shear_matrix[0, 1] = self._shear_y_x
        self._shear_matrix[1, 0] = self._shear_x_y

    def _compute_transformation_3d(self):

        super()._compute_transformation_3d()

        self._shear_matrix = torch.diag(
            torch.ones(self._dim + 1, dtype=self.dtype, device=self.device)
        )

        self._shear_matrix[0, 1] = self._shear_y_x
        self._shear_matrix[0, 2] = self._shear_z_x
        self._shear_matrix[1, 0] = self._shear_x_y
        self._shear_matrix[1, 2] = self._shear_z_y
        self._shear_matrix[2, 0] = self._shear_x_z
        self._shear_matrix[2, 1] = self._shear_y_z

    def _compute_transformation_matrix(self):
        transformation_matrix = torch.mm(
            torch.mm(
                torch.mm(
                    torch.mm(
                        torch.mm(self._trans_matrix_pos, self._trans_matrix_cm),
                        self._rotation_matrix,
                    ),
                    self._scale_matrix,
                ),
                self._shear_matrix,
            ),
            self._trans_matrix_cm_rw,
        )[0 : self._dim, :]

        return transformation_matrix

    def forward(self):

        self._compute_transformation()
        transformation_matrix = self._compute_transformation_matrix()
        flow = self._compute_dense_flow(transformation_matrix)
        torch.cuda.empty_cache()
        return self._concatenate_flows(flow)


class NonParametricTransformation(Transformation):
    r"""
    None parametric transformation
    """

    def __init__(
        self,
        moving_image: RegistrationImage,
        fixed_image: RegistrationImage,
        diffeomorphic: bool = False,
    ):

        super().__init__(moving_image, fixed_image, diffeomorphic=diffeomorphic)

        self._tensor_size = [self._dim] + self._image_size.tolist()

        self.trans_parameters = torch.nn.Parameter(torch.Tensor(*self._tensor_size))
        self.trans_parameters.data.fill_(0)

        if self._dim == 2:
            self.compute_flow = self._compute_flow_2d
        else:
            self.compute_flow = self._compute_flow_3d

    def set_start_parameter(self, parameters):
        if self._dim == 2:
            self.trans_parameters = torch.nn.Parameter(
                torch.tensor(parameters.transpose(0, 2))
            )
        elif self._dim == 3:
            self.trans_parameters = torch.nn.Parameter(
                torch.tensor(parameters.transpose(0, 1).transpose(0, 2).transpose(0, 3))
            )

    def _compute_flow_2d(self):
        return self.trans_parameters.transpose(0, 2).transpose(0, 1)

    def _compute_flow_3d(self):
        return self.trans_parameters.transpose(0, 3).transpose(0, 2).transpose(0, 1)

    def forward(self):
        flow = self._concatenate_flows(self.compute_flow())

        if self._diffeomorphic:
            displacement = self._compute_diffeomorphic_displacement(flow)
        else:
            displacement = flow
        torch.cuda.empty_cache()
        return displacement
