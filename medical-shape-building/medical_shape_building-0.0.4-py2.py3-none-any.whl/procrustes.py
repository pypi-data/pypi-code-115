import numpy as np
import torch
from scipy.linalg import orthogonal_procrustes


def inverse_procrustes(
    moving_landmarks: torch.Tensor,
    norm: float,
    rotation_mtx: torch.Tensor,
    scale: float,
    mean: torch.Tensor,
) -> torch.Tensor:
    """
    Do the inverse procrustes operation: Used, because data is in trace(data1)=1 space - very small.
    Inverse procrustes transforms the data back in the normal image space according to norm, R, s, mean
    Args:
    moving_landmarks: Nxd landmarks to transform
    norm: 1x1 normalisation
    rotation_mtx: dxd rotation matrix
    scale: 1x1 scale
    mean: dx1 translation
    Returns
    np.array: inversed procrustes data
    """
    data = torch.dot(moving_landmarks.double() / scale, rotation_mtx)

    data *= norm
    data += mean

    return data


def procrustes(fixed_landmarks: torch.Tensor, moving_landmarks: torch.Tensor) -> tuple:
    """
    Modified version of scipy.spatial.procrustes returning transformation parameters to make inverse operation possible
    Args:
    fixed_landmarks: n rows represent points in k (columns) space, reference data
    moving_landmarks: n rows of data in k space to be fit to fixed_landmarks
    Returns:
    tuple: tuple containing
    mtx_fixed (standardized version of fixed_landmarks)
    mtx_moving (orientation of moving_landmarks that best fits fixed_landmarks)
    disparity (remaining difference between mtx_fixed and mtx_moving)
    list of applied transforms needed for inverse operation
    """
    mtx_fixed = np.array(fixed_landmarks.cpu().detach(), dtype=np.double, copy=True)
    mtx_moving = np.array(moving_landmarks.cpu().detach(), dtype=np.double, copy=True)

    if mtx_fixed.ndim != 2 or mtx_moving.ndim != 2:
        raise ValueError("Input matrices must be two-dimensional")
    if mtx_fixed.shape != mtx_moving.shape:
        raise ValueError("Input matrices must be of same shape")
    if mtx_fixed.size == 0:
        raise ValueError("Input matrices must be >0 rows and >0 cols")

    device, dtype = fixed_landmarks.device, fixed_landmarks.dtype
    # translate all the data to the origin
    mean1 = np.mean(mtx_fixed, 0)
    mean2 = np.mean(mtx_moving, 0)

    mtx_fixed -= np.mean(mtx_fixed, 0)
    mtx_moving -= np.mean(mtx_moving, 0)

    norm1 = np.linalg.norm(mtx_fixed)
    norm2 = np.linalg.norm(mtx_moving)

    if norm1 == 0 or norm2 == 0:
        raise ValueError("Input matrices must contain >1 unique points")

    # change scaling of data (in rows) such that trace(mtx*mtx') = 1
    mtx_fixed /= norm1
    mtx_moving /= norm2

    # transform mtx_moving to minimize disparity
    rotation_mtx, scale = orthogonal_procrustes(mtx_fixed, mtx_moving)
    mtx_moving = np.dot(mtx_moving, rotation_mtx.T) * scale

    # measure the dissimilarity between the two datasets
    disparity = np.sum(np.square(mtx_fixed - mtx_moving))

    tensor_kwargs = {"device": device, "dtype": dtype}
    return (
        torch.tensor(mtx_fixed, **tensor_kwargs),
        torch.tensor(mtx_moving, **tensor_kwargs),
        torch.tensor(disparity, **tensor_kwargs),
        (
            torch.tensor(mean1, **tensor_kwargs),
            torch.tensor(norm1, **tensor_kwargs),
            torch.tensor(mean2, **tensor_kwargs),
            torch.tensor(norm2, **tensor_kwargs),
            torch.tensor(rotation_mtx, **tensor_kwargs),
            torch.tensor(scale, **tensor_kwargs),
        ),
    )


def points2point_procrustes(
    fixed_landmarks: torch.Tensor, moving_landmarks: torch.Tensor
) -> tuple:
    """Procrustes Registration from points to points.

    Applies procrustes between moving and fixed landmarks
    and then registeres the moving landmarks using the transformation parameters from the procrustes algorithm
    (-> inverse procrustes of mtx_moving with transformation parameters)
    Args:
    fixed_landmarks: reference points
    moving_landmarks: points to be fit to fixed_landmarks
    Returns:
    tuple: Contains registered landmarks (np.array) and transformation parameters (list)
    """
    (
        mtx_fixed,
        mtx_moving,
        disparity,
        (translation1, norm1, translation2, norm2, rotation, scaling),
    ) = procrustes(fixed_landmarks, moving_landmarks)
    registered_landmarks = inverse_procrustes(
        mtx_moving, norm1, torch.eye(3), scaling, translation1
    )

    return (
        registered_landmarks,
        (translation1, norm1, translation2, norm2, rotation, scaling),
    )

    #     data_tibia = np.asarray(data_tibia)
    #     data_femur = np.asarray(data_femur)
    #     femur_mean = np.mean(data_femur, axis=0)
    #     tibia_mean = np.mean(data_tibia, axis=0)

    #     self._pts_exporter.do_export(femur_mean,os.path.join(output_dir , "mean_femur.pts"),image_origin=False)
    #     self._pts_exporter.do_export(tibia_mean,os.path.join(output_dir , "mean_tibia.pts"),image_origin=False)
    #     for id in to_process_femur.keys():
    #         landmarks_moving_femur = self._pts_importer.do_import(to_process_femur[id]["file_path"],image_origin=False)
    #         landmarks_moving_tibia = self._pts_importer.do_import(to_process_tibia[id]["file_path"],image_origin=False)

    #         (
    #             femur_mean_norm,
    #             registered_landmarks_femur,
    #             disparity,
    #             [translation1, norm1, translation2, norm2, rotation, scaling],
    #         ) = procrustes(femur_mean, landmarks_moving_femur)

    #         (
    #             tibia_mean_norm,
    #             registered_landmarks_tibia,
    #             disparity,
    #             [translation1, norm1, translation2, norm2, rotation, scaling],
    #         ) = procrustes(tibia_mean, landmarks_moving_tibia)

    #         # (
    #         #     registered_landmarks_femur,
    #         #     [translation1, norm1, translation2, norm2, rotation, scaling],
    #         # ) = points2point_procrustes(femur_mean, landmarks_moving_femur)
    #         # (
    #         #     registered_landmarks_tibia,
    #         #     [translation1, norm1, translation2, norm2, rotation, scaling],
    #         # ) = points2point_procrustes(tibia_mean, landmarks_moving_tibia)

    #         os.makedirs(os.path.join(output_dir, id),exist_ok=True)

    #         self._pts_exporter.do_export(registered_landmarks_femur,os.path.join(output_dir , id, id+"_procrustes_femur.pts"),image_origin=False)
    #         self._pts_exporter.do_export(registered_landmarks_tibia,os.path.join(output_dir , id, id+"_procrustes_tibia.pts"),image_origin=False)

    # def pca(self,source_dir:str= "",output_dir:str = "",n_components:int = 25,show_info:bool=True,file_types: List[str]=[".pts"],lmks_prefix:str="demons_landmarks_airlab_clipped"):
    #     if not source_dir.strip():
    #         source_dir = self._proc_dir
    #     if not output_dir.strip():
    #         output_dir = self._pca_dir
    #     get_pca(source_dir,output_file=output_dir,n_components=n_components,show_info=show_info,file_types=lmks_prefix+"_femur",bone_type="femur")
    #     get_pca(source_dir,output_file=output_dir,n_components=n_components,show_info=show_info,file_types=lmks_prefix+"_tibia",bone_type="tibia")
    #     pass
