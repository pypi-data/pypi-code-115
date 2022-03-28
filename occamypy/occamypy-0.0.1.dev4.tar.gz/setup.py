import os
from setuptools import setup, find_packages


def src(pth):
    return os.path.join(os.path.dirname(__file__), pth)


def read(file_name):
    """Read a text file and return the content as a string."""
    with open(os.path.join(os.path.dirname(__file__), file_name), encoding="utf-8") as f:
        return f.read()
    

setup(name='occamypy',
      # version='0.0.1dev3',
      version=read('version.txt'),
      url="https://github.com/fpicetti/occamypy",  # used for the documentation. TODO switch to readthedocs?
      description='An Object-Oriented Optimization Framework for Large-Scale Inverse Problems',
      long_description=open(src('README.md'), "r").read(),
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
      license='GNU',
      author='Ettore Biondi, Guillame Barnier, Robert Clapp, Francesco Picetti, Stuart Farris',
      author_email='francesco.picetti@polimi.it',
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
