import fnmatch
from setuptools import find_packages, setup, Extension
from setuptools.command.build_py import build_py as build_py_orig
from Cython.Build import cythonize


extensions = [
    # example of extensions with regex
    #Extension('spam.fizz.buzz', ['spam/fizz/buzz.py']),
    Extension('verysimplemodule_test_ai.*', ['verysimplemodule_test_ai/*.py']),
]


class build_py(build_py_orig):
    def build_packages(self):
        pass


"""
python setup.py sdist bdist_wheel
twine upload dist/* 
"""
VERSION = '0.0.10'
DESCRIPTION = 'My first Python package'
LONG_DESCRIPTION = 'My first Python package with a slightly longer description'

# Setting up
setup(
    # the name must match the folder name 'verysimplemodule_test_ai'
    name="verysimplemodule_test_ai",
    version=VERSION,
    author="Jason Dsouza",
    author_email="<youremail@email.com>",
    description=DESCRIPTION,
    long_description=LONG_DESCRIPTION,
    packages=find_packages(),
    install_requires=[],  # add any additional packages that
    # needs to be installed along with your package. Eg: 'caer'

    ext_modules=cythonize(extensions),
    cmdclass={'build_py': build_py},

    keywords=['python', 'first package'],
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Education",
        "Programming Language :: Python :: 3",
        "Operating System :: MacOS :: MacOS X",
        "Operating System :: Microsoft :: Windows",
    ]
)