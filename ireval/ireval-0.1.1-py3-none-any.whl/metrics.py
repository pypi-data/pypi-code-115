from math import ceil, floor
from typing import List, Union

import numpy as np
import numpy.typing as npt


def precision_at_k(
    relevancies: Union[List[int], npt.NDArray[int]], scores: Union[List[float], npt.NDArray[float]], k: int
) -> float:
    """Precision is the fraction of retrieved documents that are relevant to the query.
    For example, for a text search on a set of documents, precision is the number of correct results
    divided by the number of all returned results.

    Precision@k considers only the documents with the highest `k` scores.
    Please note that in `trec_eval`, the number of relevant documents is always `k`, even
    if there are actually fewer documents, that is, `len(relevancies) < k`.

    Args:
        relevancies: Array of non-negative relevancies.
        scores: Target scores assigned to each document.
        k: The cutoff value, only the documents with the highest `k` scores are considered.

    Returns: The precision at `k` over the inputs.
    """

    relevancies = np.asarray(relevancies)
    scores = np.asarray(scores)

    _check_that_array_has_dimension(relevancies, 1)
    _check_that_array_has_dimension(scores, 1)
    _check_that_arrays_have_the_same_shape(relevancies, scores)
    _check_that_array_contains_only_non_negative_elements(relevancies)
    _check_that_array_contains_only_non_negative_elements(scores)

    n = len(relevancies)

    if k < n:
        top_k_indices = np.argpartition(-scores, k)[:k]
        assert len(top_k_indices) == k
        num_relevant_and_retrieved = np.count_nonzero(relevancies[top_k_indices])
    else:
        num_relevant_and_retrieved = np.count_nonzero(relevancies)

    return num_relevant_and_retrieved / k


def precision_at_k_percent(
    relevancies: Union[List[int], npt.NDArray[int]], scores: Union[List[float], npt.NDArray[float]], k: float
) -> float:
    """Precision is the fraction of retrieved documents that are relevant to the query.
    For example, for a text search on a set of documents, precision is the number of correct results
    divided by the number of all returned results.

    Precision@k% considers only the documents with the highest `k`% scores. if the resulting number of documents
    to check is smaller than 1, then we perform precision@1.

    Args:
        relevancies: Array of non-negative relevancies.
        scores: Target scores assigned to each document.
        k: The cutoff value, only the documents with the highest `k`% scores are considered. Needs to be
        between 0 and 100.

    Returns: The precision at `k`% over the inputs.
    """

    relevancies = np.asarray(relevancies)
    scores = np.asarray(scores)

    _check_is_percentage(k)
    _check_that_array_has_dimension(relevancies, 1)
    _check_that_array_has_dimension(scores, 1)
    _check_that_arrays_have_the_same_shape(relevancies, scores)
    _check_that_array_contains_only_non_negative_elements(relevancies)
    _check_that_array_contains_only_non_negative_elements(scores)

    n = len(relevancies)

    cutoff = max(1, round(n * k / 100))

    assert cutoff > 0
    assert cutoff <= n

    return precision_at_k(relevancies, scores, cutoff)


def recall_at_k(
    relevancies: Union[List[int], npt.NDArray[int]], scores: Union[List[float], npt.NDArray[float]], k: float
) -> float:
    """Recall is the fraction of the documents that are relevant to the query that are successfully retrieved.
    For example, for a text search on a set of documents, recall is the number of correct results divided by the
    number of results that should have been returned.

    Recall@k% considers only the documents with the highest `k`% scores. if the resulting number of documents
    to check is smaller than 1, then we perform recall@1.

    Args:
        relevancies: Array of non-negative relevancies.
        scores: Target scores assigned to each document.
        k: The cutoff value, only the documents with the highest `k`% scores are considered. Needs to be
        between 0 and 100.

    Returns: The recall at `k`% over the inputs.
    """

    relevancies = np.asarray(relevancies)
    scores = np.asarray(scores)

    _check_that_array_has_dimension(relevancies, 1)
    _check_that_array_has_dimension(scores, 1)
    _check_that_arrays_have_the_same_shape(relevancies, scores)
    _check_that_array_contains_only_non_negative_elements(relevancies)
    _check_that_array_contains_only_non_negative_elements(scores)

    n = len(relevancies)

    if k < n:
        top_k_indices = np.argpartition(-scores, k)[:k]
        assert len(top_k_indices) == k
        num_relevant_and_retrieved = np.count_nonzero(relevancies[top_k_indices])
    else:
        num_relevant_and_retrieved = np.count_nonzero(relevancies)

    return num_relevant_and_retrieved / np.count_nonzero(relevancies)


def recall_at_k_percent(
    relevancies: Union[List[int], npt.NDArray[int]], scores: Union[List[float], npt.NDArray[float]], k: float
) -> float:
    """Recall is the fraction of the relevant documents that are successfully retrieved. .
    For example, for a text search on a set of documents, recall is the number of correct results divided by the
    number of results that should have been returned.

    Recall@k considers only the documents with the highest `k` scores.
    Please note that in `trec_eval`, the number of relevant documents is always `k`, even
    if there are actually fewer documents, that is, `len(relevancies) < k`.

    Args:
        relevancies: Array of non-negative relevancies.
        scores: Target scores assigned to each document.
        k: The cutoff value, only the documents with the highest `k` scores are considered.

    Returns: The recall at `k` over the inputs.
    """

    relevancies = np.asarray(relevancies)
    scores = np.asarray(scores)

    _check_is_percentage(k)
    _check_that_array_has_dimension(relevancies, 1)
    _check_that_array_has_dimension(scores, 1)
    _check_that_arrays_have_the_same_shape(relevancies, scores)
    _check_that_array_contains_only_non_negative_elements(relevancies)
    _check_that_array_contains_only_non_negative_elements(scores)

    n = len(relevancies)

    cutoff = max(1, round(n * k / 100))

    assert cutoff > 0
    assert cutoff <= n

    return recall_at_k(relevancies, scores, cutoff)


def average_precision(
    relevancies: Union[List[int], npt.NDArray[int]], scores: Union[List[float], npt.NDArray[float]]
) -> float:
    """Compute average precision (AP) from prediction scores.

    AP summarizes a precision-recall curve as the weighted mean of precisions achieved at each threshold, with the
    increase in recall from the previous threshold used as the weight. It is identical to the area under the
    precision-recall curve.

    Args:
        relevancies: Array of non-negative relevancies.
        scores: Target scores assigned to each document.

    Returns: The average precision (AP) over the inputs.
    """

    relevancies = np.asarray(relevancies)
    scores = np.asarray(scores)

    _check_that_array_has_dimension(relevancies, 1)
    _check_that_array_has_dimension(scores, 1)
    _check_that_arrays_have_the_same_shape(relevancies, scores)
    _check_that_array_contains_only_non_negative_elements(relevancies)
    _check_that_array_contains_only_non_negative_elements(scores)

    n = len(relevancies)

    indices = np.argsort(-scores)

    true_positives = 0

    result = 0
    for k in range(n):
        idx = indices[k]

        relevant = relevancies[idx] > 0
        if relevant:
            true_positives += 1

        pk = true_positives / (k + 1)

        result += pk * relevant

    num_relevant = np.count_nonzero(relevancies)
    return result / num_relevant


def r_precision(
    relevancies: Union[List[int], npt.NDArray[int]], scores: Union[List[float], npt.NDArray[float]]
) -> float:
    """R-Precision is the precision after `R` documents have been retrieved, where `R` is the number of
    relevant documents for the topic.

    R-precision requires knowing all documents that are relevant to a query. The number of relevant documents,
    `R`, is used as the cutoff for calculation, and this varies from query to query. For example,
    if there are `15` documents relevant to "red" in a corpus (`R=15`), R-precision for "red" looks at the top `15`
    documents returned, counts the number `r`  that are relevant and turns that into a relevancy
    fraction: `r / R = r / 15`.

    Returns:

    """
    relevancies = np.asarray(relevancies)
    scores = np.asarray(scores)

    _check_that_array_has_dimension(relevancies, 1)
    _check_that_array_has_dimension(scores, 1)
    _check_that_arrays_have_the_same_shape(relevancies, scores)
    _check_that_array_contains_only_non_negative_elements(relevancies)
    _check_that_array_contains_only_non_negative_elements(scores)

    num_relevant = np.count_nonzero(relevancies)

    return precision_at_k(relevancies, scores, num_relevant)


def _check_that_array_has_dimension(array: np.ndarray, expected_dim: int):
    if array.ndim != expected_dim:
        raise ValueError(f"Expected input to be of dimension [{expected_dim}], but was [{array.ndim}]")


def _check_that_arrays_have_the_same_shape(a: np.ndarray, b: np.ndarray):
    if a.shape != b.shape:
        raise ValueError(f"Expected input to have same shape, but  [{a.shape}] != [{b.shape}]")


def _check_that_array_contains_only_non_negative_elements(array: np.ndarray):
    if np.any(array < 0):
        raise ValueError("Input contains negative elements")


def _check_is_percentage(k: float):
    if k < 0 or k > 100:
        raise ValueError(f"Input is not a valid percentage (needs to be between 0 and 100, but was [{k}]")
