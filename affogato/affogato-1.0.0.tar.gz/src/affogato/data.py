"""
For loading data from anywhere and converting it to numpy arrays for use in Affogato.
"""

__all__ = [ 'image_file_to_array', 'labeled_image_directory', 'numpy_file', 'save_numpy_file' ]

from typing import Iterable
import numpy as np
from PIL import Image
from tqdm import tqdm


TrainingData = list[tuple[np.ndarray, np.ndarray]]

def label_to_output(
        label: int, label_count: int,
        merge_binary_classification_labels: bool = False,
    ) -> np.ndarray:
    """
    Converts a label to a numpy array of outputs.

    Parameters:
    -----------
    label: int
        The label to convert.

    label_count: int
        The number of labels.

    merge_binary_classification_labels: bool
        Whether to merge labels to a single output when there are only 0 and 1
        labels. So if there are only 2 labels, the output will be of size 1.

    Returns:
    --------
    np.ndarray
        A numpy array of the label.
    """

    if merge_binary_classification_labels and label_count == 2:
        return np.array([[label]])

    output = np.zeros((1, label_count))
    output[0][label] = 1
    return output


def image_file_to_array(image_path: str, gray_scale: bool = False) -> np.ndarray:
    """
    Converts an image file to a numpy array of shape (1, width, height, 3).

    If the image is grayscale, the array will be of shape (1, width, height, 1).

    Raises:
    ------
    FileNotFoundError
        If the image file does not exist.

    PIL.UnidentifiedImageError
        If the image file is not an image.
    """
    array = np.array(Image.open(image_path).convert('RGB')).reshape(1, *Image.open(image_path).size, 3)

    if gray_scale:
        # Average the RGB values to get the grayscale value.
        array = np.mean(array, axis=3, keepdims=True)

    return array


def labeled_image_directory(
        path: str,
        gray_scale: bool = False,
        verbose: bool = False,
        merge_binary_classification_labels: bool = False,
    ) -> TrainingData:
    """
    Loads images with labels into numpy arrays.

    The directory should be structured like this:
    root
    ├── 0
    │   ├── 0.png
    │   ├── 1.png
    │   ├── 2.png
    │   ...
    ├── 1
    │   ├── 0.png
    │   ...
    ├── 2
    │   ├── 0.png
    │   ...
    ...

    Here the root directory contains a subfolder for each label.
    Each subfolder contains images of that label.
    The names of the images are irrelevant.

    Parameters:
    -----------
    path: str
        The path to the root directory.

    gray_scale: bool
        Whether to convert the images to grayscale.
        Note: Also changes their shape. See `image_file_to_array`.

    verbose: bool
        Whether to print progress.

    merge_binary_classification_labels: bool
        Whether to merge labels to a single output when there are only 0 and 1
        labels. So if there are only 0 and 1 labels, the output will be of size 1.

    Returns:
    --------
    TrainingData
        A list of tuples of the form (image, label).

    Raises:
    ------
    FileNotFoundError
        If the root directory does not exist.

    NotADirectoryError
        If the root directory is not a directory, or if it contains files which
        are not directories.

    ValueError
        If the subdirectories' names are not labels.
    """

    from pathlib import Path
    from sys import stdout

    root = Path(path)

    if not root.exists():
        raise FileNotFoundError(f"The path '{path}' does not exist.")

    if not root.is_dir():
        raise NotADirectoryError(f"The path '{path}' is not a directory.")

    if any(not child.is_dir() for child in root.iterdir()):
        raise NotADirectoryError(f"The path '{path}' contains files that are not directories.")

    child_names = [ child.name for child in root.iterdir() ]
    if any(not name.isdigit() for name in child_names):
        raise ValueError(f"The path '{path}' contains directories that are not labels. "
                         f"All directory names should be integers.")

    labels = [ int(name) for name in child_names ]
    if any(labels.count(label) > 1 for label in labels):
        raise ValueError(f"The path '{path}' contains multiple directories with the "
                         f"same name. All labels should be unique.")

    if min(labels) != 0:
        raise ValueError(f"The path '{path}' contains directories with names that are not "
                         f"labels. All labels should be integers starting at 0.")

    labels = set(labels)
    if any(n not in labels for n in range(0, max(labels) + 1)):
        missing_labels = [n for n in range(0, max(labels) + 1) if n not in labels]
        raise ValueError(f"The path '{path}' is missing some labels. "
                         f"The labels are {missing_labels}.")
    
    # After all of the checks, we can assume that the directory is structured correctly.
    if verbose: print("Loading images...")
    data = []
    for subfolder in root.iterdir():
        label = int(subfolder.name)
        output = label_to_output(label, len(labels), merge_binary_classification_labels)

        # Wrap in `tqdm` for progress bar.
        image_iter = tqdm(
            list(subfolder.iterdir()),
            desc=f"Label {label}",
            disable=not verbose,
            file=stdout,
        )

        for image in image_iter:
            array = image_file_to_array(str(image), gray_scale)
            data.append((array, output))

    return data


def save_numpy_file(path: str, data: Iterable[tuple[np.ndarray, np.ndarray]]):
    """
    Saves a list of tuples of the form (input, label) to a numpy file.

    Parameters:
    -----------
    path: str
        The path to the file.

    data: Iterable[tuple[np.ndarray, np.ndarray]]
        The data to save.
    """
    inputs = [ input for input, _ in data ]
    labels = [ label for _, label in data ]
    np.savez(path, inputs=inputs, labels=labels)


def numpy_file(path: str) -> TrainingData:
    """
    Load data from an .npz file.

    Parameters:
    -----------
    path: str
        The path to the file.

    Returns:
    --------
    TrainingData
        A list of tuples of the form (input, label).

    Raises:
    ------
    FileNotFoundError
        If the file does not exist.

    ValueError
        If the file is not a .npz file or if it is missing the inputs or labels
        arrays.
    """
    try:
        with np.load(path) as data:
            if 'inputs' not in data or 'labels' not in data:
                raise ValueError(f"The file '{path}' does not contain the "
                                  "expected keys 'inputs' and 'labels'.")

            inputs = data['inputs']
            labels = data['labels']

            return list(zip(inputs, labels))

    except AttributeError as err: # Hacky check if file is .npz
        raise ValueError(f"The file '{path}' is not a .npz file.") from err

