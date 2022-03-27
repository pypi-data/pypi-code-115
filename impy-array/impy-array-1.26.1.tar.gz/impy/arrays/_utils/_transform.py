import numpy as np
import scipy
from scipy import ndimage as ndi
from collections import namedtuple
from ._skimage import sktrans
from ...array_api import xp

__all__ = ["compose_affine_matrix", 
           "decompose_affine_matrix",
           "affinefit", 
           "check_matrix",
           "warp"
           ]

AffineTransformationParameters = namedtuple(typename="AffineTransformationParameters", 
                                            field_names=["translation", "rotation", "scale", "shear"]
                                            )

def warp(img: xp.ndarray, matrix: xp.ndarray, cval=0, mode="constant", output_shape=None, order=1):
    img = xp.asarray(img, dtype=img.dtype)
    matrix = xp.asarray(matrix)
    out = xp.ndi.affine_transform(img, matrix, cval=cval, mode=mode, output_shape=output_shape, 
                                  order=order, prefilter=order>1)
    return out

def shift(img: xp.ndarray, shift: xp.ndarray, cval=0, mode="constant", order=1):
    img = xp.asarray(img, dtype=img.dtype)
    out = xp.ndi.shift(img, shift, cval=cval, mode=mode, 
                       order=order, prefilter=order>1)
    return out

def compose_affine_matrix(scale=None, translation=None, rotation=None, shear=None, ndim:int=2):
    # These two modules returns consistent matrix in the two dimensional case.
    # rotation must be in radian.
    if ndim == 2:
        af = sktrans.AffineTransform(scale=scale, translation=translation, rotation=rotation, shear=shear)
        mx = af.params
    else:
        from napari.utils.transforms import Affine
        if scale is None:
            scale = [1]*ndim
        elif np.isscalar(scale):
            scale = [scale]*ndim
        if translation is None:
            translation = [0]*ndim
        elif np.isscalar(translation):
            translation = [translation]*ndim
        if rotation is not None:
            rotation = np.rad2deg(rotation)
        
        af = Affine(scale=scale, translate=translation, rotate=rotation, shear=shear)
        mx = af.affine_matrix
    
    return mx


def decompose_affine_matrix(matrix:np.ndarray):
    ndim = matrix.shape[0] - 1
    if ndim == 2:
        af = sktrans.AffineTransform(matrix=matrix)
        out = AffineTransformationParameters(translation=af.translation, rotation=af.rotation, 
                                             scale=af.scale, shear=af.shear)
    else:
        from napari.utils.transforms import Affine
        af = Affine(affine_matrix=matrix)
        out = AffineTransformationParameters(translation=af.translate, rotation=af.rotate, 
                                             scale=af.scale, shear=af.shear)
    return out
        


def calc_corr(img0, img1, matrix, corr_func):
    """
    Calculate value of corr_func(img0, matrix(img1)).
    """
    img1_transformed = warp(img1, matrix)
    return corr_func(img0, img1_transformed)

def affinefit(img, imgref, bins=256, order=1):
    as_3x3_matrix = lambda mtx: np.vstack((mtx.reshape(2,3), [0., 0., 1.]))
    from scipy.stats import entropy
    def normalized_mutual_information(img, imgref):
        """
        Y(A,B) = (H(A)+H(B))/H(A,B)
        See "Elegant SciPy"
        """
        hist, edges = np.histogramdd([np.ravel(img), np.ravel(imgref)], bins=bins)
        hist /= np.sum(hist)
        e1 = entropy(np.sum(hist, axis=0)) # Shannon entropy
        e2 = entropy(np.sum(hist, axis=1))
        e12 = entropy(np.ravel(hist)) # mutual entropy
        return (e1 + e2)/e12
    
    def cost_nmi(mtx, img, imgref):
        mtx = as_3x3_matrix(mtx)
        img_transformed = sktrans.warp(img, mtx, order=order)
        return -normalized_mutual_information(img_transformed, imgref)
    
    mtx0 = np.array([[1., 0., 0.],
                     [0., 1., 0.]]) # aberration makes little difference
    
    result = scipy.optimize.minimize(cost_nmi, mtx0, args=(np.asarray(img), np.asarray(imgref)),
                                     method="Powell")
    mtx_opt = as_3x3_matrix(result.x)
    return mtx_opt

def check_matrix(matrices):
    """
    Check Affine transformation matrix
    """    
    mtx = []
    for m in matrices:
        if np.isscalar(m): 
            if m == 1:
                mtx.append(m)
            else:
                raise ValueError(f"Only `1` is ok, but got {m}")
            
        elif m.shape != (3, 3) or not np.allclose(m[2,:2], 0):
            raise ValueError(f"Wrong Affine transformation matrix:\n{m}")
        
        else:
            mtx.append(m)
    return mtx

def polar2d(
    img: xp.ndarray,
    rmax: int,
    dtheta: float = 0.1,
    order=1,
    mode="constant",
    cval=0
) -> np.ndarray:
    centers = np.array(img.shape)/2 - 0.5
    r = xp.arange(rmax) + 0.5
    theta = xp.arange(0, 2*np.pi, dtheta)
    r, theta = xp.meshgrid(r, theta)
    y = r * xp.sin(theta) + centers[0]
    x = r * xp.cos(theta) + centers[1]
    coords = xp.stack([y, x], axis=0)
    img = xp.asarray(img, dtype=img.dtype)
    out = xp.ndi.map_coordinates(img, coords, order=order, mode=mode, cval=cval, prefilter=order>1)
    return out

# def polar3d(
#     img: xp.ndarray, 
#     rmax: int,
#     dtheta: float = 0.1,
#     order=1,
#     mode="constant", 
#     cval=0
# ) -> np.ndarray:
#     centers = np.array(img.shape)/2 - 0.5
#     r = xp.arange(rmax) + 0.5
#     theta = xp.arange(0, 2*np.pi, dtheta)
#     phi = xp.arange(-np.pi/2, np.pi/2, dtheta)
#     r, theta, phi = xp.meshgrid(r, theta, phi)
#     z = r * xp.sin(phi) + centers[0]
#     _yx = r * xp.cos(phi)
#     y = _yx * xp.sin(theta) + centers[1]
#     x = _yx * xp.cos(theta) + centers[2]
#     coords = xp.stack([z, y, x], axis=0)
#     img = xp.asarray(img, dtype=img.dtype)
#     out = xp.ndi.map_coordinates(img, coords, order=order, mode=mode, cval=cval, prefilter=order>1)
#     return out
