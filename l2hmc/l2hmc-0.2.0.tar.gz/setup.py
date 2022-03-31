# -*- coding: utf-8 -*-
from setuptools import setup

package_dir = \
{'': 'src'}

packages = \
['l2hmc',
 'l2hmc.distributions',
 'l2hmc.distributions.pytorch',
 'l2hmc.distributions.tensorflow',
 'l2hmc.dynamics',
 'l2hmc.dynamics.pytorch',
 'l2hmc.dynamics.tensorflow',
 'l2hmc.group',
 'l2hmc.group.pytorch',
 'l2hmc.group.tensorflow',
 'l2hmc.lattice',
 'l2hmc.lattice.su3',
 'l2hmc.lattice.su3.numpy',
 'l2hmc.lattice.su3.pytorch',
 'l2hmc.lattice.su3.tensorflow',
 'l2hmc.lattice.u1.numpy',
 'l2hmc.lattice.u1.pytorch',
 'l2hmc.lattice.u1.tensorflow',
 'l2hmc.learning_rate.tensorflow',
 'l2hmc.loss',
 'l2hmc.loss.pytorch',
 'l2hmc.loss.tensorflow',
 'l2hmc.network',
 'l2hmc.network.jax',
 'l2hmc.network.pytorch',
 'l2hmc.network.tensorflow',
 'l2hmc.notebooks',
 'l2hmc.scripts',
 'l2hmc.scripts.pytorch',
 'l2hmc.scripts.tensorflow',
 'l2hmc.trackers',
 'l2hmc.trackers.pytorch',
 'l2hmc.trackers.tensorflow',
 'l2hmc.trainers',
 'l2hmc.trainers.pytorch',
 'l2hmc.trainers.tensorflow',
 'l2hmc.utils',
 'l2hmc.utils.tensorflow']

package_data = \
{'': ['*'],
 'l2hmc': ['bin/*',
           'conf/accelerate/cpu/*',
           'conf/accelerate/gpu/*',
           'conf/annealing_schedule/*',
           'conf/config.yaml',
           'conf/conv/*',
           'conf/dynamics/*',
           'conf/learning_rate/*',
           'conf/loss/*',
           'conf/mode/*',
           'conf/net_weights/*',
           'conf/network/*',
           'conf/steps/*',
           'conf/wandb/*']}

install_requires = \
['accelerate>=0.5.1,<0.6.0',
 'horovod>=0.24.2,<0.25.0',
 'ipython>=8.1.0,<9.0.0',
 'matplotx>=0.3.6,<0.4.0',
 'neovim>=0.3.1,<0.4.0',
 'pyright>=1.1.226,<2.0.0',
 'tensorflow>=2.8.0,<3.0.0',
 'torch>=1.11.0,<2.0.0']

setup_kwargs = {
    'name': 'l2hmc',
    'version': '0.2.0',
    'description': 'L2HMC algorithm for sampling in Lattice QCD',
    'long_description': None,
    'author': 'Sam Foreman',
    'author_email': 'saforem2@gmail.com',
    'maintainer': None,
    'maintainer_email': None,
    'url': None,
    'package_dir': package_dir,
    'packages': packages,
    'package_data': package_data,
    'install_requires': install_requires,
    'python_requires': '>=3.8,<3.11',
}


setup(**setup_kwargs)
