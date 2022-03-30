"""Handler classes which can be used to combined logic for scorers with similar requirements"""
from scipy import spatial
from dp_tms.scorers import distance as custom_distance_scorers


def vector_scorer_handler(
    base_vector: list, comp_vector: list, scorer_types: list
) -> dict:
    """scorer method handler for vector based scorers

    Args:
        base_vector (list): base vector
        comp_vector (list): comparison vector
        scorer_types (list): scorer types to run scoring for

    Raises:
        TypeError: _description_

    Returns:
        dict: scores for given vectors
    """
    scores = {}

    if "simple_cosine" in scorer_types:

        score = 1 - spatial.distance.cosine(base_vector, comp_vector)
        scores["simple_cosine"] = float(score)

    if "adjusted_cosine" in scorer_types:

        scores["adjusted_cosine"] = custom_distance_scorers.adjusted_cosine(
            base_vector, comp_vector
        )

    if "simple_euclidean" in scorer_types:

        # score = np.linalg.norm(np.asarray(base_1)-np.asarray(comp_1))#this is theoratically faster function
        score = 1 / (
            1 + spatial.distance.euclidean(base_vector, comp_vector)
        )  # this is a slower function, should actually use np sqrt
        scores["simple_euclidean"] = float(score)

    if len(scores.keys()) == 0:
        raise TypeError(
            f"None of `scorer_types` == {scorer_types} are currently supported"
        )

    return scores
