import random
from molml.Data.datastructures import Dataset, Molecule
from typing import List
import numpy as np


def random_split_molecules(molecules: List[Molecule], test_split: float = 0.2, val_split: float = 0.1,
                           random_state: int = 42):
    """"""

    if sum([test_split, val_split]) > 1:
        raise ValueError(f'Sum of test ({test_split}) + val ({val_split}) splits cannot be higher than 1.')

    # train, test, val = [], [], []
    # for idx, mol in enumerate(molecules):
    #     random_nr = random.uniform(0, 1)
    #     if random_nr < val_split:
    #         val.append(idx)
    #     elif val_split < random_nr < (test_split + val_split):
    #         test.append(idx)
    #     else:
    #         train.append(idx)

    random.seed(random_state)
    indices = list(range(len(molecules)))
    random.shuffle(indices)

    test_cutoff = round(len(indices) * test_split)
    val_cutoff = round(len(indices) * val_split)

    train = indices[:val_cutoff]
    test = indices[val_cutoff:(test_cutoff + val_cutoff)]
    val = indices[(test_cutoff + val_cutoff):]

    # In case a molecule got lost for some reason (don't know if this could happen, but yeah, safety)
    for i in indices:
        if i not in train + test + val:
            train.append(i)

    return train, test, val



def stratified_split_molecules(molecules: List[Molecule], labels: List[int] = None, test_split: float = 0.2,
                               val_split: float = 0.1, random_state: int = 42):

    if sum([test_split, val_split]) > 1:
        raise ValueError(f'Sum of test ({test_split}) + val ({val_split}) splits cannot be higher than 1.')

    random.seed(random_state)

    # If no labels are provided, use the molecule y values as label
    if labels is None:
        labels = [m.y for m in molecules]

        if all([elem is None for elem in labels]):
            labels = [0 for _ in molecules]
        else:
            # Distribute y into 1/0. Pick random sides if None
            median_label = np.median([x for x in labels if x is not None])
            labels = [round(random.uniform(0, 1)) if x is None else 0 if x < median_label else 1 for x in labels]

    if np.min(np.bincount(labels)) < 2:
        raise ValueError("The least populated group has only 1 member. It must be > 1 for stratified sampling")

    train, test, val = [], [], []
    for group in list(set(labels)):
        # Get the indices of the elements in the group
        group_idx = [idx for idx, lab in enumerate(labels) if lab == group]

        # Randomly distribute acrosss train/test/val
        indices = list(range(len(group_idx)))
        random.shuffle(indices)

        test_cutoff = round(len(indices) * test_split)
        val_cutoff = round(len(indices) * val_split)

        val_idx = indices[:val_cutoff]
        test_idx = indices[val_cutoff:(test_cutoff + val_cutoff)]
        train_idx = indices[(test_cutoff + val_cutoff):]

        # In case a molecule got lost for some reason (don't know if this could happen, but yeah, safety)
        for i in indices:
            if i not in val_idx + test_idx + train_idx:
                train_idx.append(i)

        # append the split group to the global train/test/val splits
        train.extend([group_idx[i] for i in train_idx])
        test.extend([group_idx[i] for i in test_idx])
        val.extend([group_idx[i] for i in val_idx])

    return train, test, val


def fold_split_random(dataset: Dataset, folds: int = 5, random_state: int = 42):
    from sklearn.model_selection import ShuffleSplit

    ss = ShuffleSplit(n_splits=folds, random_state=random_state)
    return [(i, j) for i, j in ss.split(list(range(len(dataset))))]


def fold_split_stratified():
    raise NotImplementedError
