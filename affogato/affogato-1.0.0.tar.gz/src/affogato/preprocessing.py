import numpy as np


def _handle_zeros_in_scale(scale, copy=True, constant_mask=None):
    
    # chech if we scale a scalar
    if np.isscalar(scale):
        if scale == 0.0:
            scale = 1.0
        return scale

    elif scale is np.ndarray:
        if constant_mask is None:
            # Detect near constant values to avoid dividing by a very small
            # value that could lead to surprising results and numerical
            # stability issues.
            constant_mask = scale < 10 * np.finfo(scale.dtype).eps

        if copy:
            # New array to avoid side-effects
            scale = scale.copy()
        scale[constant_mask] = 1.0
        return scale


class Preprocessor:
    """
    Represents a preprocessor that transfroms the data to fit some formula. 
    Used for making Normalizers and standarizers.
    """
    def fit(self, x: np.ndarray):
        raise NotImplementedError()

    def transform(self, x: np.ndarray):
        raise NotImplementedError()


class MinMaxScaler(Preprocessor):
    """
    Min max scaler is a normalaizer, that scales the input to a given range.   

    Parameters
    ----------
    feature_range: tuple. Default: (0,1)
        the scaled values would be between the feature range

    copy: bool. Default: True 
        decides if the values given for `fit()` and `transform()` should be copied or not

    clip: bool. Default: False
        decides if the final values should be cliped between the `feature_range`

    Example:
    ------
    we initialize the scaler, and give it the output feature range. for example [-1, 1].
    >>> scaler = MinMaxScaler((-1, 1)).    
    
    we use the `fit()` function to fit our scaler to the data.
    >>> scaler.fit(data)
    
    we use the `transform()` function to transform the data between the fitted value range. 
    >>> data = scaler.transform(data)
    
    """
    def __init__(self, feature_range=(0, 1), copy=True, clip=False):
        self.feature_range = feature_range
        self.copy = copy
        self.clip = clip
        self.n_samples_seen_ = 0

    def fit(self, x: np.ndarray):
        """
        The function fits the scaler to the target data inorder to transfrom it later.
        """

        # resets the properties before each new fit TODO: make it possiable to partial fit
        if hasattr(self, "scale_"):
            del self.scale_
            del self.min_
            del self.n_samples_seen_
            del self.data_min_
            del self.data_max_
            del self.data_range_

        feature_range = self.feature_range
        if feature_range[0] >= feature_range[1]:
            raise ValueError("Minimum of feature range must be smaller than maximum.")
        
        data_min = np.nanmin(x, axis=0)
        data_max = np.nanmax(x, axis=0)

        if self.n_samples_seen_ == 0:
            self.n_samples_seen_ = x.shape[0]
        else:
            data_min = np.minimum(self.data_min_, data_min)
            data_max = np.maximum(self.data_max_, data_max)
            self.n_samples_seen_ += x.shape[0]


        data_range = data_max - data_min
        self.scale_ = (feature_range[1] - feature_range[0]) / _handle_zeros_in_scale(
            data_range, copy=True
        )

        self.min_ = feature_range[0] - data_min * self.scale_
        self.data_min_ = data_min
        self.data_max_ = data_max
        self.data_range_ = data_range
        return self

    def transform(self, x: np.ndarray) -> np.ndarray:
        """
        Scale features of X according to feature_range.
        """

        if not hasattr(self, "scale_"):
            raise RuntimeError("the scaler has not been fitted")
        
        x *= self.scale_
        x += self.min_
        if self.clip:
            np.clip(x, self.feature_range[0], self.feature_range[1], out=x)
        return x
