import setuptools

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setuptools.setup(
    name="sapero_math",
    version="0.1.0",
    author="Saperoi",
    author_email="uesugi.sapero@gmail.com",
    description="Just a package for some math functions i needed on PyPI for easier access",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/saperoi/sapero_math-py",
    project_urls={
        "Bug Tracker": "https://github.com/saperoi/sapero_math-py/issues",
    },
    classifiers=[
        "Programming Language :: Python :: 3",
        "Operating System :: OS Independent",
        "License :: OSI Approved :: GNU General Public License v3 (GPLv3)"
    ],
    packages=['sapero_math'],
    python_requires=">=3.6",
)
