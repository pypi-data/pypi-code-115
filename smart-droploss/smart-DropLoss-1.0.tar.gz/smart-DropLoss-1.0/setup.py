
import setuptools

setuptools.setup(
    name="smart-DropLoss",
    version="1.0",
    packages=setuptools.find_packages(),
    install_requires=['termcolor>=1.1', 'Pillow', 'yacs>=0.1.6', 'tabulate', 'cloudpickle', 'matplotlib', 'tqdm>4.29.0', 'tensorboard', 'fvcore', 'future', 'pydot'],
)
