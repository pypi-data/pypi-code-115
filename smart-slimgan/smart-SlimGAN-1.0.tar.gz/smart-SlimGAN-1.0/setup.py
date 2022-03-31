
import setuptools

setuptools.setup(
    name="smart-SlimGAN",
    version="1.0",
    packages=setuptools.find_packages(),
    install_requires=['numpy', 'scipy', 'requests', 'torch', 'tensorflow', 'torchvision<2.0', 'six', 'matplotlib', 'Pillow', 'scikit-image', 'pytest', 'scikit-learn', 'future', 'pytest-cov', 'pandas', 'psutil', 'yapf'],
)
