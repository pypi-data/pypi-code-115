
import setuptools

setuptools.setup(
    name="smart-boofuzz",
    version="1.0",
    packages=setuptools.find_packages(),
    install_requires=['', 'future', 'pyserial', 'pydot', 'tornado~=4.0', 'Flask~=1.0', 'impacket', 'colorama', 'attrs', 'click', 'psutil'],
)
