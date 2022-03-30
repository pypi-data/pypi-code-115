from typing import Optional

import torch

from medical_shape_building.airlab.image import RegistrationDisplacement


@torch.no_grad()
def transform_points(
    points: torch.Tensor,
    inverse_displacement_field: RegistrationDisplacement,
    current_image_shape: Optional[torch.Tensor] = None,
    **kwargs,
):
    dst_img_size = inverse_displacement_field.image_size.to(points)

    if current_image_shape is None:
        current_image_shape = dst_img_size
    elif not isinstance(current_image_shape, torch.Tensor):
        current_image_shape = torch.tensor(current_image_shape)

    current_image_shape = current_image_shape.to(points)

    from medical_shape.normalization import ShapeNormalization

    normalized_points = ShapeNormalization.normalize(points, current_image_shape)

    inv_disp_tensor = inverse_displacement_field.image[0].to(points)

    floored_pts = torch.floor(points)
    ceiled_pts = torch.ceil(points)
    floored_pts_list = floored_pts.long().tolist()
    ceiled_pts_list = ceiled_pts.long().tolist()

    factors_ceiled = ceiled_pts - points

    for idx in range(points.size(0)):

        # points outside the image don't have a defined displacement -> Skip them. They'll likely be clamped /discarded later anyway
        if (ceiled_pts[idx] >= dst_img_size).any():
            continue

        curr_disp_tensor_ceiled = inv_disp_tensor
        curr_disp_tensor_floored = inv_disp_tensor

        for i in range(points.size(-1)):
            curr_disp_tensor_floored = curr_disp_tensor_floored[
                :, floored_pts_list[idx][i]
            ]
            curr_disp_tensor_ceiled = curr_disp_tensor_ceiled[
                :, ceiled_pts_list[idx][i]
            ]

        curr_disp_tensor_ceiled = torch.flip(curr_disp_tensor_ceiled, (-1,))
        curr_disp_tensor_floored = torch.flip(curr_disp_tensor_floored, (-1,))

        normalized_points[idx] = (
            normalized_points[idx]
            + factors_ceiled[idx] * curr_disp_tensor_ceiled
            + (1 - factors_ceiled[idx]) * curr_disp_tensor_floored
        )

    transformed_points = ShapeNormalization.denormalize(normalized_points, dst_img_size)
    return transformed_points
