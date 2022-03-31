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
    'version': '0.1.1',
    'description': 'Time series data sets for PyTorch',
    'long_description': '# Time series data sets for PyTorch\n\n[![PyPi](https://img.shields.io/pypi/v/torchtime)](https://pypi.org/project/torchtime)\n[![Build status](https://img.shields.io/github/workflow/status/philipdarke/torchtime/build.svg)](https://github.com/philipdarke/torchtime/actions/workflows/build.yml)\n![Coverage](https://philipdarke.com/torchtime/assets/coverage-badge.svg)\n[![License](https://img.shields.io/github/license/philipdarke/torchtime.svg)](https://github.com/philipdarke/torchtime/blob/main/LICENSE)\n\n`torchtime` provides ready-to-go time series data sets for use in PyTorch. The current list of supported data sets is:\n\n* All data sets in the UEA/UCR classification repository [[link]](https://www.timeseriesclassification.com/)\n* PhysioNet Challenge 2019 (early prediction of sepsis) [[link]](https://physionet.org/content/challenge-2019/1.0.0/)\n\n## Installation\n\n```bash\n$ pip install torchtime\n```\n\n## Using `torchtime`\n\nThe example below uses the `torchtime.data.UEA` class. The data set is specified using the `dataset` argument (see list of data sets [here](https://www.timeseriesclassification.com/dataset.php)). The `split` argument determines whether training, validation or test data are returned. The size of the splits are controlled with the `train_split` and `val_split` arguments. Reproducibility is achieved using the `seed` argument.\n\nFor example, to load training data for the [ArrowHead](https://www.timeseriesclassification.com/description.php?Dataset=ArrowHead) data set with a 70/30% training/validation split:\n\n```\nfrom torch.utils.data import DataLoader\nfrom torchtime.data import UEA\n\narrowhead = UEA(\n    dataset="ArrowHead",\n    split="train",\n    train_split=0.7,\n    seed=456789,\n)\ndataloader = DataLoader(arrowhead, batch_size=32)\n```\n\nThe DataLoader returns batches as a dictionary of tensors `X`, `y` and `length`. `X` are the time series data. By default, a time stamp is appended to the data as the first channel. This package follows the *batch first* convention therefore `X` has shape (*n*, *s*, *c*) where *n* is batch size, *s* is trajectory length and *c* is the number of channels.\n\nArrowHead is a univariate time series with 251 observations in each trajectory. `X` therefore has two channels, the time stamp followed by the time series.\n\n```\n>> next(iter(dataloader))["X"]\n\ntensor([[[  0.0000,  -1.8302],\n         [  1.0000,  -1.8123],\n         [  2.0000,  -1.8122],\n         ...,\n         [248.0000,  -1.7821],\n         [249.0000,  -1.7971],\n         [250.0000,  -1.8280]],\n\n        ...,\n\n        [[  0.0000,  -1.8392],\n         [  1.0000,  -1.8314],\n         [  2.0000,  -1.8125],\n         ...,\n         [248.0000,  -1.8359],\n         [249.0000,  -1.8202],\n         [250.0000,  -1.8387]]])\n```\n\nLabels `y` are one-hot encoded and have shape (*n*, *l*) where *l* is the number of classes.\n\n```\n>> next(iter(dataloader))["y"]\n\ntensor([[0, 0, 1],\n        [1, 0, 0],\n        [1, 0, 0],\n\n        ...,\n\n        [0, 0, 1],\n        [0, 1, 0],\n        [1, 0, 0]])\n\n```\n\nThe `length` of each trajectory (before padding if the data set is of irregular length) is provided as a tensor of shape (*n*).\n\n```\n>> next(iter(dataloader))["length"]\n\ntensor([251, 251, 251, 251, 251, 251, 251, 251, 251, 251, 251, 251, 251, 251,\n        251, 251, 251, 251, 251, 251, 251, 251, 251, 251, 251, 251, 251, 251,\n        251, 251, 251, 251])\n```\n\n## Learn more\n\nMissing data can be simulated using the `missing` argument. In addition, missing data/observational masks and time delta channels can be appended using the `mask` and `delta` arguments. See the [tutorial](https://philipdarke.com/torchtime/tutorial.html) and [API](https://philipdarke.com/torchtime/api.html) for more information.\n\nThis work is based on some of the data processing ideas in Kidger et al, 2020 [[1]](https://arxiv.org/abs/2005.08926) and Che et al, 2018 [[2]](https://doi.org/10.1038/s41598-018-24271-9).\n\n## References\n\n1. Kidger, P, Morrill, J, Foster, J, *et al*. Neural Controlled Differential Equations for Irregular Time Series. *arXiv* 2005.08926 (2020). [[arXiv]](https://arxiv.org/abs/2005.08926)\n\n1. Che, Z, Purushotham, S, Cho, K, *et al*. Recurrent Neural Networks for Multivariate Time Series with Missing Values. *Sci Rep* 8, 6085 (2018). [[doi]](https://doi.org/10.1038/s41598-018-24271-9)\n\n1. Reyna M, Josef C, Jeter R, *et al*. Early Prediction of Sepsis From Clinical Data: The PhysioNet/Computing in Cardiology Challenge. *Critical Care Medicine* 48 2: 210-217 (2019). [[doi]](https://doi.org/10.1097/CCM.0000000000004145)\n\n1. Reyna, M, Josef, C, Jeter, R, *et al*. Early Prediction of Sepsis from Clinical Data: The PhysioNet/Computing in Cardiology Challenge 2019 (version 1.0.0). *PhysioNet* (2019). [[doi]](https://doi.org/10.13026/v64v-d857)\n\n1. Goldberger, A, Amaral, L, Glass, L, *et al*. PhysioBank, PhysioToolkit, and PhysioNet: Components of a new research resource for complex physiologic signals. *Circulation* 101 (23), pp. e215–e220 (2000). [[doi]](https://doi.org/10.1161/01.cir.101.23.e215)\n\n## Funding\n\nThis work was supported by the Engineering and Physical Sciences Research Council, Centre for Doctoral Training in Cloud Computing for Big Data, Newcastle University (grant number EP/L015358/1).\n\n## License\n\nReleased under the MIT license.\n',
    'author': 'Philip Darke',
    'author_email': 'hello@philipdarke.com',
    'maintainer': None,
    'maintainer_email': None,
    'url': 'https://philipdarke.com/torchtime',
    'package_dir': package_dir,
    'packages': packages,
    'package_data': package_data,
    'install_requires': install_requires,
    'python_requires': '>=3.8,<3.10',
}


setup(**setup_kwargs)
