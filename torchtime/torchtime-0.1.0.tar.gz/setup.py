# -*- coding: utf-8 -*-
from setuptools import setup

package_dir = \
{'': 'src'}

packages = \
['torchtime']

package_data = \
{'': ['*']}

install_requires = \
['requests>=2.27.1,<3.0.0',
 'sklearn>=0.0,<0.1',
 'sktime>=0.10.1,<0.11.0',
 'torch>=1.11.0,<2.0.0']

setup_kwargs = {
    'name': 'torchtime',
    'version': '0.1.0',
    'description': 'Time series data sets for PyTorch',
    'long_description': '# Time series data sets for PyTorch\n\n![PyPi](https://img.shields.io/pypi/v/torchtime)\n[![Build status](https://img.shields.io/github/workflow/status/philipdarke/torchtime/build.svg)](https://github.com/philipdarke/torchtime/actions/workflows/build.yml)\n![Coverage](https://philipdarke.com/torchtime/assets/coverage-badge.svg)\n[![License](https://img.shields.io/github/license/philipdarke/torchtime.svg)](https://github.com/philipdarke/torchtime/blob/main/LICENSE)\n\n`torchtime` provides ready-to-go time series data sets for use in PyTorch. The current list of supported data sets is:\n\n* All data sets in the UEA/UCR classification repository [[link]](https://www.timeseriesclassification.com/)\n* PhysioNet Challenge 2019 [[link]](https://physionet.org/content/challenge-2019/1.0.0/)\n\nThe package follows the *batch first* convention. Data tensors are therefore of shape (*n*, *s*, *c*) where *n* is batch size, *s* is trajectory length and *c* are the number of channels.\n\n## Installation\n\n```bash\n$ pip install torchtime\n```\n\n## Using `torchtime`\n\nThe example below uses the `torchtime.data.UEA` class. The data set is specified using the `dataset` argument (see list [here](https://www.timeseriesclassification.com/dataset.php)). The `split` argument determines whether training, validation or test data are returned. The size of the splits are controlled with the `train_split` and `val_split` arguments.\n\nFor example, to load training data for the [ArrowHead](https://www.timeseriesclassification.com/description.php?Dataset=ArrowHead) data set with a 70% training, 20% validation and 10% testing split:\n\n```\nfrom torch.utils.data import DataLoader\nfrom torchtime.data import UEA\n\narrowhead = UEA(\n    dataset="ArrowHead",\n    split="train",\n    train_split=0.7,\n    val_split=0.2,\n)\ndataloader = DataLoader(arrowhead, batch_size=32)\n```\n\nBatches are dictionaries of tensors `X`, `y` and `length`. `X` are the time series data with an additional time stamp in the first channel, `y` are one-hot encoded labels and `length` are the length of each trajectory.\n\nArrowHead is a univariate time series with 251 observations in each trajectory. `X` therefore has two channels, the time stamp followed by the time series. A batch size of 32 was specified above therefore `X` has shape (32, 251, 2).\n\n```\n>> next(iter(dataloader))["X"].shape\n\ntorch.Size([32, 251, 2])\n\n>> next(iter(dataloader))["X"]\n\ntensor([[[  0.0000,  -1.8295],\n         [  1.0000,  -1.8238],\n         [  2.0000,  -1.8101],\n         ...,\n         [248.0000,  -1.7759],\n         [249.0000,  -1.8088],\n         [250.0000,  -1.8110]],\n\n        ...,\n\n        [[  0.0000,  -2.0147],\n         [  1.0000,  -2.0311],\n         [  2.0000,  -1.9471],\n         ...,\n         [248.0000,  -1.9901],\n         [249.0000,  -1.9913],\n         [250.0000,  -2.0109]]])\n```\n\nThere are three classes therefore `y` has shape (32, 3).\n\n```\n>> next(iter(dataloader))["y"].shape\n\ntorch.Size([32, 3])\n\n>> next(iter(dataloader))["y"]\n\ntensor([[0, 0, 1],\n        ...,\n        [1, 0, 0]])\n```\n\nFinally, `length` is the length of each trajectory (before any padding for data sets of irregular length) and therefore has shape (32).\n\n```\n>> next(iter(dataloader))["length"].shape\n\ntorch.Size([32])\n\n>> next(iter(dataloader))["length"]\n\ntensor([251, ..., 251])\n```\n\n## Learn more\n\nOther features include missing data simulation for UEA data sets. See the [API](api) for more information.\n\nThis work is based on some of the data processing ideas in Kidger et al, 2020 [[link]](https://arxiv.org/abs/2005.08926) and Che et al, 2018 [[link]](https://doi.org/10.1038/s41598-018-24271-9).\n\n## License\n\nReleased under the MIT license.\n',
    'author': 'Philip Darke',
    'author_email': 'hello@philipdarke.com',
    'maintainer': None,
    'maintainer_email': None,
    'url': None,
    'package_dir': package_dir,
    'packages': packages,
    'package_data': package_data,
    'install_requires': install_requires,
    'python_requires': '>=3.8,<3.10',
}


setup(**setup_kwargs)
