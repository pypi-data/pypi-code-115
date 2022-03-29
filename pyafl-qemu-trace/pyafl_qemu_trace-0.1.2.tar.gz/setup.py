# -*- coding: utf-8 -*-
from setuptools import setup

packages = \
['pyafl_qemu_trace', 'pyafl_qemu_trace.binaries']

package_data = \
{'': ['*']}

setup_kwargs = {
    'name': 'pyafl-qemu-trace',
    'version': '0.1.2',
    'description': 'A pip-installable distribution of afl-qemu-trace.',
    'long_description': '[![PyPI version](https://badge.fury.io/py/pyafl-qemu-trace.svg)](https://badge.fury.io/py/pyafl-qemu-trace)\n# pyafl_qemu_trace\n\npip-installable afl-qemu-trace python package\n\n## Installation\n\n```\npython3 -m pip install pyafl-qemu-trace\n```\n\n## Examples\n\n```\nfrom pyafl_qemu_trace import qemu_path\n\ntracer = qemu_path("x86_64")\n```\n\n## Requirements\n\nEither `docker-compose` or `docker compose` should be available at build time, but when\ninstalling, no dependencies are required, this basically just downloads a bunch of\nbinaries for you.\n\n## Targets\n\nSupported targets for `afl-qemu-trace` are as follows, but at the moment only `x86_64`\nand `aarch64` are built -- the infrastructure to generate the rest is already in place,\nhowever, I just need to enable it.\n\n```txt\naarch64-softmmu\nalpha-softmmu\narm-softmmu\navr-softmmu\ncris-softmmu\nhppa-softmmu\ni386-softmmu\nm68k-softmmu\nmicroblaze-softmmu\nmicroblazeel-softmmu\nmips-softmmu\nmips64-softmmu\nmips64el-softmmu\nmipsel-softmmu\nmoxie-softmmu\nnios2-softmmu\nor1k-softmmu\nppc-softmmu\nppc64-softmmu\nriscv32-softmmu\nriscv64-softmmu\nrx-softmmu\ns390x-softmmu\nsh4-softmmu\nsh4eb-softmmu\nsparc-softmmu\nsparc64-softmmu\ntricore-softmmu\nx86_64-softmmu\nxtensa-softmmu\nxtensaeb-softmmu\naarch64\naarch64_be\nalpha\narm\narmeb\ncris\nhexagon\nhppa\ni386\nm68k\nmicroblaze\nmicroblazeel\nmips\nmips64\nmips64el\nmipsel\nmipsn32\nmipsn32el\nnios2\nor1k\nppc\nppc64\nppc64le\nriscv32\nriscv64\ns390x\nsh4\nsh4eb\nsparc\nsparc32plus\nsparc64\nx86_64\nxtensa\nxtensaeb\n```',
    'author': 'novafacing',
    'author_email': 'rowanbhart@gmail.com',
    'maintainer': None,
    'maintainer_email': None,
    'url': 'https://github.com/novafacing/pyafl_qemu_trace.git',
    'packages': packages,
    'package_data': package_data,
    'python_requires': '>=3.6,<4.0',
}
from build import *
build(setup_kwargs)

setup(**setup_kwargs)
