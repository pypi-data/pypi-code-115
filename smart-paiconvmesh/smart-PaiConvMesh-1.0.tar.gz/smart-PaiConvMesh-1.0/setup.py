
import setuptools

setuptools.setup(
    name="smart-PaiConvMesh",
    version="1.0",
    packages=setuptools.find_packages(),
    install_requires=['numpy', 'scipy', 'scikit-learn', 'matplotlib', 'tqdm', 'jupyter', 'ipython', 'tensorboard', 'tensorboardX', 'trimesh'],
)
