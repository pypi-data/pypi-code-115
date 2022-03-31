
import setuptools

setuptools.setup(
    name="smart-HiGAN",
    version="1.0",
    packages=setuptools.find_packages(),
    install_requires=['torch>=1.0', 'tensorboard', 'munch', 'opencv-python', 'h5py', 'sklearn'],
)
