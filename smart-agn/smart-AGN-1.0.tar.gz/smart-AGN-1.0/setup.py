
import setuptools

setuptools.setup(
    name="smart-AGN",
    version="1.0",
    packages=setuptools.find_packages(),
    install_requires=['Keras==2.3.1', 'numpy', 'langml', 'seaborn', 'boltons', 'scikit_learn', 'bert4keras'],
)
