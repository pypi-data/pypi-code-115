
import setuptools

setuptools.setup(
    name="smart-InterpretableClustering",
    version="1.0",
    packages=setuptools.find_packages(),
    install_requires=['TensorFlow==1.11.0', 'dgl-cu101', 'dynamicgem', 'networkx', 'sklearn', 'scipy', 'keras==2.2.4', 'numpy>=1.15.3'],
)
