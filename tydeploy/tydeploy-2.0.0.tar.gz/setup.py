from setuptools import setup, find_packages
from tydeploy import __title__, __description__, __version__

setup(
    name="tydeploy",
    version=__version__,
    description=__title__,
    long_description=__description__,
    classifiers=[
        "Development Status :: 4 - Beta",
        "Programming Language :: Python :: 3 :: Only",
        "License :: OSI Approved :: GNU General Public License v3 or later (GPLv3+)",
        "Operating System :: OS Independent",
    ],
    keywords="deployer",
    author="Joseph Chris",
    author_email="joseph@josephcz.xyz",
    url="https://github.com/baobao1270/tydeploy.git",
    license="GPL-3.0-or-later",
    packages=find_packages(),
    include_package_data=True,
    zip_safe=True,
    install_requires=[req.strip() for req in open("requirements.txt", "r").read().strip().split("\n")],
    entry_points={
          'console_scripts': [
              'tydeploy = tydeploy.tydeploy:main'
          ]
    }
)
