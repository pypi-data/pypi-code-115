
import setuptools

setuptools.setup(
    name="smart-Voxel-R-CNN",
    version="1.0",
    packages=setuptools.find_packages(),
    install_requires=['numpy', 'torch>=1.1', 'spconv', 'numba', 'tensorboardX', 'easydict', 'pyyaml'],
)
