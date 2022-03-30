
import setuptools

setuptools.setup(
    name="smart-scvelo",
    version="1.0",
    packages=setuptools.find_packages(),
    install_requires=['scanpy>=1.4', 'anndata>=0.6.21', 'numpy>=1.17', 'pandas>=0.23', 'scikit-learn>=0.21.2', 'scipy>=1.0', 'matplotlib>=2.2', 'umap-learn>=0.3', 'loompy>=2.0.12'],
)
