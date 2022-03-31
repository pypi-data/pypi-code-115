
import setuptools

setuptools.setup(
    name="smart-SIGN-pytorch",
    version="1.0",
    packages=setuptools.find_packages(),
    install_requires=['scikit-learn==0.22.2.post1', 'torch==1.6.0+cu101', 'torch-geometric==1.4.3'],
)
