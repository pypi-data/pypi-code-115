from setuptools import find_packages, setup

with open("requirements.txt") as f:
    requirements = f.readlines()

long_description = "Package that takes as command-line input a file path specifying a source text and a search term and return the words in lines that contain the substring"

setup(
    name="cpm_file",
    version="1.3",
    author="Laura Pérez Vera",
    author_email="lpvera22@gmail.com",
    # url="",
    description="Finding substrings in the lines of a file.",
    long_description=long_description,
    long_description_content_type="text/markdown",
    license="MIT",
    packages=find_packages(),
    entry_points={"console_scripts": ["cpm_file = cpm_file.main:main"]},
    classifiers=(
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ),
    keywords="search keyword substring research substring",
    install_requires=requirements,
    zip_safe=False,
)
