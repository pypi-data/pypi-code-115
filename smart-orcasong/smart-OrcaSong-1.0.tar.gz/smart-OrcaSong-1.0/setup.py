
import setuptools

setuptools.setup(
    name="smart-OrcaSong",
    version="1.0",
    packages=setuptools.find_packages(),
    install_requires=['numpy==1.16.2', 'h5py', 'matplotlib', 'km3pipe', 'docopt', 'toml', 'setuptools_scm', 'sphinx', 'sphinx-rtd-theme', 'sphinx-autoapi', 'twine', 'numpydoc'],
)
