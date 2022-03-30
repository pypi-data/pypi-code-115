
import setuptools

setuptools.setup(
    name="smart-zarp",
    version="1.0",
    packages=setuptools.find_packages(),
    install_requires=['Flask==0.10.1', 'netlib==0.11.1', 'paramiko==1.15.2', 'pyOpenSSL==0.13.1'],
)
