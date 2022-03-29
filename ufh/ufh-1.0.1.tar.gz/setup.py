from setuptools import setup, find_packages

with open("README.md", "r") as readme_file:
    readme = readme_file.read()

setup(
    name="ufh",
    version="1.0.1",
    author="Cobalt-A",
    author_email="nikitos.eng@gmail.com",
    description="A package to redact unturned dat files",
    long_description=readme,
    long_description_content_type="text/markdown",
    url="https://github.com/UntFileHelper/UFH.git",
    packages=find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3.10",
        "License :: OSI Approved :: GNU General Public License v3 (GPLv3)",
    ],
)