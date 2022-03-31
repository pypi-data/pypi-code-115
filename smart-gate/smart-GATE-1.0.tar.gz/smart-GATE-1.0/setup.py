
import setuptools

setuptools.setup(
    name="smart-GATE",
    version="1.0",
    packages=setuptools.find_packages(),
    install_requires=['numpy', 'ufal.udpipe', 'tqdm', 'transformers', 'prettytable', 'conllu', 'torch>=1.3.0', 'seaborn', 'pandas'],
)
