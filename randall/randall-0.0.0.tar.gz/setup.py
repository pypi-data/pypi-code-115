import platform
from pathlib import Path

from setuptools import (find_packages,
                        setup)

import randall

project_base_url = 'https://github.com/lycantropos/randall/'


def read_file(path_string: str) -> str:
    return Path(path_string).read_text(encoding='utf-8')


parameters = dict(
        name=randall.__name__,
        packages=find_packages(exclude=('tests', 'tests.*')),
        version=randall.__version__,
        description=randall.__doc__,
        long_description=read_file('README.md'),
        long_description_content_type='text/markdown',
        author='Azat Ibrakov',
        author_email='azatibrakov@gmail.com',
        license='MIT License',
        classifiers=[
            'License :: OSI Approved :: MIT License',
            'Programming Language :: Python :: 3.6',
            'Programming Language :: Python :: 3.7',
            'Programming Language :: Python :: 3.8',
            'Programming Language :: Python :: 3.9',
            'Programming Language :: Python :: 3.10',
            'Programming Language :: Python :: Implementation :: CPython',
            'Programming Language :: Python :: Implementation :: PyPy',
        ],
        url=project_base_url,
        download_url=project_base_url + 'archive/master.zip',
        python_requires='>=3.6',
        setup_requires=read_file('requirements-setup.txt'))
if platform.python_implementation() == 'CPython':
    from typing import (TYPE_CHECKING,
                        Iterator)

    if TYPE_CHECKING:
        from setuptools_rust import RustExtension


    class LazyRustExtensions:
        def __iter__(self) -> Iterator['RustExtension']:
            from setuptools_rust import RustExtension
            yield RustExtension('._' + randall.__name__)


    parameters.update(rust_extensions=LazyRustExtensions(),
                      include_package_data=True,
                      zip_safe=False)
setup(**parameters)
