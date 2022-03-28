from setuptools import setup, find_packages

VERSION = "0.0.4"
DESCRIPTION = "Package for https://getbeacon.xyz"
LONG_DESCRIPTION = "Package for https://getbeacon.xyz - a way to notify your favourite channels when the interesting stuff happens on your server"

setup(
    name="beaconclient",
    version=VERSION,
    author="Cerwind",
    url="https://github.com/charliemday/beaconclient",
    author_email="",
    description=DESCRIPTION,
    long_description=LONG_DESCRIPTION,
    packages=find_packages(),
    install_requires=[
        'requests',
    ],  # add any additional packages that
    # needs to be installed along with your package
    keywords=["python", "beacon", "beaconclient", "notification"],
    classifiers=[],
)
