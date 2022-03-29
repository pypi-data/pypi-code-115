from setuptools import setup, find_packages

VERSION = '0.0.1'
DESCRIPTION = 'Abhinav TP twine Testing'
LONG_DESCRIPTION = 'Abhinav TP twine Testing'

setup(
    name="mycustompackage12345",
    version=VERSION,
    author="Abhinav",
    author_email="abhinav@example.com",
    description=DESCRIPTION,
    long_description=LONG_DESCRIPTION,
    packages=find_packages(),
    install_requires=[],  # add any additional packages that
    # needs to be installed along with your package. Eg: 'caer'

    keywords=['python', 'mycustompackage12345'],
)
