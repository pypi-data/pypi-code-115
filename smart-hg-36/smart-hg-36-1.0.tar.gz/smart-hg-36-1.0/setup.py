
import setuptools

setuptools.setup(
    name="smart-hg-36",
    version="1.0",
    packages=setuptools.find_packages(),
    install_requires=['six==1.16.0', 'numpy==1.18.5', 'keras-applications==1.0.8', 'scikit-image==0.18.0', 'tensorflow==2.3.1', 'keras'],
)
