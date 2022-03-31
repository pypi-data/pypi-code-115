"""Load Eclipse Grid Files
"""
from typing import Literal
import pathlib
import itertools
import contextlib
from enum import Enum

import pandas as pd
import numpy as np
from numpy import typing as npt

from ecl.grid import EclGrid

from ._utils import import_tqdm, get_filetype, EclFileEnum

tqdm = import_tqdm()

GRID_FILE_TYPES = [EclFileEnum.ECL_GRID_FILE, EclFileEnum.ECL_EGRID_FILE]


class EclGridCPrefix(Enum):
    x = "x"
    y = "y"
    z = "z"


class EclSimFaces(Enum):
    i1 = (0, 4, 6, 2)
    i2 = (1, 5, 7, 3)
    j1 = (0, 1, 5, 4)
    j2 = (2, 3, 7, 6)
    k1 = (0, 1, 3, 2)
    k2 = (4, 5, 7, 6)
    ecl_order = (0, 1, 2, 3, 4, 5, 6, 7)


def _corner_names(order=EclSimFaces.ecl_order.value):
    """create corner names list so they can be easily referenced later"""
    return [
        f"{dim}{n}"
        for (n, dim) in itertools.product(
            order,
            (
                EclGridCPrefix["x"].value,
                EclGridCPrefix["y"].value,
                EclGridCPrefix["z"].value,
            ),
        )
    ]


def _xcorn_names():
    return [c for c in _corner_names() if EclGridCPrefix["x"].value in c]


def _ycorn_names():
    return [c for c in _corner_names() if EclGridCPrefix["y"].value in c]


def _zcorn_names():
    return [c for c in _corner_names() if EclGridCPrefix["z"].value in c]


@contextlib.contextmanager
def open_EclGrid(filepath):
    """Safely open an EclGrid instance with a context manager"""
    filepath = pathlib.Path(filepath)
    if not filepath.exists():
        raise FileNotFoundError(f"Cannot find input grid file {filepath}")

    egrid = None
    # safety clause for loading eclipse data with ecl
    try:
        file_type = get_filetype(filepath)
        if file_type not in GRID_FILE_TYPES:
            raise ValueError
        egrid = EclGrid.load_from_file(str(filepath.absolute()))
        yield egrid
    except (ValueError, OSError):  # OSError on windows
        raise ValueError(f"cannot interpret file type {filepath}")
    finally:
        del egrid


def get_face_corner_names(face: EclSimFaces):
    face_ns = EclSimFaces[face].value
    return _corner_names(order=face_ns)


def get_sim_surface(
    xyzcorn: pd.DataFrame,
    n: int,
    face: Literal["top", "base"] = "top",
    slice_dir: Literal["i", "j", "k"] = "k",
) -> npt.NDArray(3, np.float_):
    """Get the corner points which define a surface from the grid using an i,j or k index `n`.

    Args:
        xyzcorn: The corner point grid dataframe from EclDeck
        n: The i/j/k layer to slice
        face: The top or base face of a cell
        slice_dir: The direction to slice along
    """
    face = 1 if face == "top" else 2
    facename = f"{slice_dir}{face}"
    corners = xyzcorn.query(f"{slice_dir} == {n}")
    if corners.empty:
        raise ValueError(f"No cells match {slice_dir} == {n}")
    corners = corners[get_face_corner_names(facename)].values.reshape(-1, 3)
    corners = np.unique(corners, axis=0)
    return corners


def get_ecl_grid_dims(filepath):
    """Get the dimensions of the grid

    Args:

    Returns:
        tuple: i, j, k dim sizes
    """
    with open_EclGrid(filepath) as egrid:
        return (
            egrid.nx,
            egrid.ny,
            egrid.nz,
        )


def load_ecl_grid_index(filepath, silent=True):
    """Load a simulation grid index

    Args:

    Returns:

    """
    with open_EclGrid(filepath) as egrid:
        data = egrid.export_index()
        data["actnum"] = egrid.export_actnum().numpy_copy()

    return data


def load_ecl_grid(filepath, silent=True):
    """Load a simulation grid

    Args:

    Returns:

    """
    with open_EclGrid(filepath) as egrid:
        xyzcorn = pd.DataFrame(egrid.export_index())
        zcorn = egrid.export_corners(egrid.export_index())

        # create zcorn names list so they can be easily referenced later
        cnames = _corner_names()
        for c, zc in enumerate(cnames):
            xyzcorn[zc] = zcorn[:, c]

    return xyzcorn
