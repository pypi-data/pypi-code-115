import os
from setuptools import setup, find_packages

# Package meta-data.
NAME = "catalyst"
DESCRIPTION = "OccamyPy. An object-oriented optimization library for small- and large-scale problems."
URL = "https://github.com/fpicetti/occamypy"
EMAIL = "francesco.picetti@polimi.it"
AUTHOR = "Ettore Biondi, Guillame Barnier, Robert Clapp, Francesco Picetti, Stuart Farris"
REQUIRES_PYTHON = ">=3.6.0"

PROJECT_ROOT = os.path.abspath(os.path.dirname(__file__))


def load_readme():
    """Docs? Contribution is welcome."""
    readme_path = os.path.join(PROJECT_ROOT, "README.md")
    with open(readme_path, encoding="utf-8") as f:
        return f"\n{f.read()}"


def load_version():
    """Docs? Contribution is welcome."""
    context = {}
    with open(os.path.join(PROJECT_ROOT, "occamypy", "__version__.py")) as f:
        exec(f.read(), context)
    return context["__version__"]


def src(pth):
    return os.path.join(os.path.dirname(__file__), pth)


def read(file_name):
    """Read a text file and return the content as a string."""
    with open(os.path.join(os.path.dirname(__file__), file_name), encoding="utf-8") as f:
        return f.read()
    

setup(name='occamypy',
      version=load_version(),
      url="https://github.com/fpicetti/occamypy",  # used for the documentation. TODO switch to readthedocs?
      description='An Object-Oriented Optimization Framework for Large-Scale Inverse Problems',
      long_description=load_readme(),
      long_description_content_type='text/markdown',
      keywords=['algebra', 'inverse problems', 'large-scale optimization'],
      classifiers=[
          'Development Status :: 4 - Beta',
          'Intended Audience :: Developers',
          'Intended Audience :: Science/Research',
          'Natural Language :: English',
          'Programming Language :: Python :: 3.6',
          'Programming Language :: Python :: 3.7',
          'Programming Language :: Python :: 3.8',
          'Topic :: Scientific/Engineering :: Mathematics',
          'Operating System :: Unix'
      ],
      author=AUTHOR,
      author_email=EMAIL,
      install_requires=['numpy',
                        'scipy',
                        'h5py',
                        'numba',
                        'torch>=1.7.0',
                        'dask',
                        'dask-jobqueue',
                        'dask-kubernetes',
                        'matplotlib',
                        'gputil',
                        ],
      # extras_require={  # one can install two of them with pip install occamypy[cuda]
      #     'cuda': ['cupy>=8.0', 'gputil']},
      packages=find_packages(),
      zip_safe=True)
