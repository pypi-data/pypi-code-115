
import setuptools

setuptools.setup(
    name="smart-TSQA",
    version="1.0",
    packages=setuptools.find_packages(),
    install_requires=['tqdm', 'jieba>=0.42.1', 'sklearn', 'torch==1.5.1', 'pandas', 'argparse'],
)
