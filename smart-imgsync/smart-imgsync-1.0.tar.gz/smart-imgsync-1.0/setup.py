
import setuptools

setuptools.setup(
    name="smart-imgsync",
    version="1.0",
    packages=setuptools.find_packages(),
    install_requires=['pbr>=0.6,!=0.7,<1.0', 'requests', 'oslo.config', 'oslo.log', 'six', 'dateutils', 'backports.lzma', 'python-glanceclient', 'keystoneauth1'],
)
