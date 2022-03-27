import torch
import typing
import toolz
import numpy as np
import pickle

__all__ = [
    'load_npz_file',
    'load_pkl_file',
]

def load_npz_file(
    filename:   str,
) -> typing.Dict[str, torch.Tensor]:
    data = np.load(filename)
    return toolz.valmap(lambda a: torch.from_numpy(a), data)

def load_pkl_file(
    filename:   str,
) -> typing.Dict[str, torch.Tensor]:
    data = { }
    with open(filename, 'rb') as f:
        data = pickle.load(f)
    return data