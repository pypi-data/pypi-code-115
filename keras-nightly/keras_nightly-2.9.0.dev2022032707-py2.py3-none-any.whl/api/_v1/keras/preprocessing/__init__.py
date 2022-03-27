# This file is MACHINE GENERATED! Do not edit.
# Generated by: tensorflow/python/tools/api/generator/create_python_api.py script.
"""Utilities to preprocess data before training.

Warning: `tf.keras.preprocessing` APIs do not operate on tensors and are
not recommended for new code. Prefer loading data with either
`tf.keras.utils.text_dataset_from_directory` or
`tf.keras.utils.image_dataset_from_directory`, and then transforming the output
`tf.data.Dataset` with preprocessing layers. These approaches will offer
better performance and intergration with the broader Tensorflow ecosystem. For
more information, see the tutorials for [loading text](
https://www.tensorflow.org/tutorials/load_data/text), [loading images](
https://www.tensorflow.org/tutorials/load_data/images), and [augmenting images](
https://www.tensorflow.org/tutorials/images/data_augmentation), as well as the
[preprocessing layer guide](
https://www.tensorflow.org/guide/keras/preprocessing_layers).

"""

import sys as _sys

from keras.api._v1.keras.preprocessing import image
from keras.api._v1.keras.preprocessing import sequence
from keras.api._v1.keras.preprocessing import text
from tensorflow.python.util import module_wrapper as _module_wrapper

if not isinstance(_sys.modules[__name__], _module_wrapper.TFModuleWrapper):
  _sys.modules[__name__] = _module_wrapper.TFModuleWrapper(
      _sys.modules[__name__], "keras.preprocessing", public_apis=None, deprecation=True,
      has_lite=False)
