
import setuptools

setuptools.setup(
    name="smart-Indy-node",
    version="1.0",
    packages=setuptools.find_packages(),
    install_requires=['indy-plenum==1.9.0.dev847', 'python-dateutil', 'timeout-decorator==0.4.0', 'distro==1.3.0'],
)
