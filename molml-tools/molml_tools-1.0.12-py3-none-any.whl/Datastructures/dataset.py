import numpy as np
import os
import shelve
from typing import List, Callable
from molml.Datastructures.molecule import Molecule


class Dataset:
    def __init__(self, molecules: List[Molecule] = None, name: str = 'molml_dataset', root: str = ".",
                 transform: Callable = None, target_transform: Callable = None, post_transform: Callable = None,
                 post_target_transform: Callable = None):

        self.transform = transform
        self.target_transform = target_transform
        self.post_transform = post_transform
        self.post_target_transform = post_target_transform

        self.root = root
        self.name = name
        self.filename = os.path.join(root, name)

        if molecules is None:
            with shelve.open(self.filename) as db:
                self.molecules = db['molecules']
            if self.molecules is None or len(self.molecules) == 0:
                raise IOError('File not found. If you have not pre-processed this file, init Dataset with a list of '
                              'molecules: Dataset(List[Molecule]) and perform Dataset.process(). Otherwise this class'
                              'has noting to work with :).')
        else:
            self.molecules = molecules

    def show(self, idx, size: tuple = (500, 500), kekulize: bool = True):
        self.molecules[idx].show(size, kekulize)

    def process(self, redo: bool = False):

        # Make intermediate dirs if needed
        os.makedirs(self.root, exist_ok=True)

        # Check if you already did this
        if os.path.exists(self.filename + '.db') and not redo:
            pass
        else:
            # Transform x and y and save them to a path
            with shelve.open(self.filename) as db:
                for idx, m in enumerate(self.molecules):
                    if self.transform:
                        x = self.transform(m.smiles)
                    if self.target_transform:
                        y = self.target_transform(m.y)

                    db[str(idx)] = (x, y)

                # save molecules
                db['molecules'] = self.molecules

    def get_x(self, idx: int = None, to_array: bool = False):
        """ Return a numpy array of molecules """
        if idx is None:
            idx = list(range(len(self)))

        if type(idx) is int:
            x = self[idx][0] if not to_array else np.array(self[idx][0])

        else:
            with shelve.open(self.filename) as db:
                x = [db[str(i)][0] for i in idx] if not to_array else np.array([db[str(i)][0] for i in idx])

        return x

    def get_y(self, idx: int = None, to_array: bool = False):
        """ Return a numpy array of labels """
        if idx is None:
            idx = list(range(len(self)))

        if type(idx) is int:
            y = self[idx][1] if not to_array else np.array(self[idx][1])
        else:
            with shelve.open(self.filename) as db:
                y = [db[str(i)][1] for i in idx] if not to_array else np.array([db[str(i)][1] for i in idx])

        return y

    def __len__(self):
        return len(self.molecules)

    def __getitem__(self, idx):

        # Read from file
        with shelve.open(self.filename) as db:
            x, y = db[str(idx)]

        # apply any post-processing functions on the data
        if self.post_transform:
            x = self.post_transform(x)
        if self.post_target_transform:
            y = self.post_target_transform(y)

        return x, y

    def __repr__(self):
        return f"Dataset containing {len(self.molecules)} molecules."
