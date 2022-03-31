
import setuptools

setuptools.setup(
    name="smart-RSGNet",
    version="1.0",
    packages=setuptools.find_packages(),
    install_requires=['EasyDict==1.7', 'Cython', 'scipy', 'pandas', 'pyyaml', 'json_tricks', 'scikit-image', 'yacs>=0.1.5', 'tensorboardX==1.6'],
)
