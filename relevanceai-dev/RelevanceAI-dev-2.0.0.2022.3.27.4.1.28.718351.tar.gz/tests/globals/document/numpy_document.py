import numpy as np

from relevanceai.package_utils.make_id import _make_id


def numpy_document():
    document = {
        "sample_1_numpy": np.random.randint(5, size=1)[0],
        "sample_2_numpy": np.random.rand(3, 2),
        "sample_3_numpy": np.nan,
    }
    document["_id"] = _make_id(document)
    return document
