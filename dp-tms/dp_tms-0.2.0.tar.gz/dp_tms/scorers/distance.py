"""
    distance scoring methods

    methods include
    ------------------------------------
    1. adjusted_cosine
    2. score_method_handler
"""
from scipy import spatial
import numpy as np


def adjusted_cosine(base_vector, comp_vector):
    """finds indices in entity_vector that equal, removes in both vectors and applies cosine

    Args:
        base_vector (list): base vector
        comp_vector (list): comparison vector

    Returns:
        float: adjusted cosine score
    """
    if isinstance(base_vector, np.ndarray):
        base_vector = base_vector.tolist()

    if isinstance(comp_vector, np.ndarray):
        comp_vector = comp_vector.tolist()

    indices = [
        i for i, x in enumerate(base_vector) if x == 0
    ]  # must be from joblisting

    indices = sorted(indices, reverse=True)

    for idx in indices:
        comp_vector.pop(idx)

    for idx in indices:
        base_vector.pop(idx)

    score = 1 - spatial.distance.cosine(base_vector, comp_vector)

    return float(score)
