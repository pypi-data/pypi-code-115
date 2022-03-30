
import setuptools

setuptools.setup(
    name="smart-toolium",
    version="1.0",
    packages=setuptools.find_packages(),
    install_requires=['requests>=2.12.4            # api tests', 'selenium>=2.53.6,<4         # web tests', 'Appium-Python-Client>=0.24  # mobile tests', 'six>=1.10.0', 'screeninfo==0.3.1'],
)
