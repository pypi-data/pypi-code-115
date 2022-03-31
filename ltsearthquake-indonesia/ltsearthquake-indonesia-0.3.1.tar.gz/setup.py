"""
https://packaging.python.org/en/latest/tutorials/packaging-projects/?highlight=setup.py%20
"""
import setuptools

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setuptools.setup(
    name="ltsearthquake-indonesia",
    version="0.3.1",
    author="Rahman Aji Pratama ",
    author_email="pratamaxadjie@gmail.com",
    description="This package will get the latest ",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/pypa/sampleproject",
    project_urls={
        "Website ": "https://github.com/pypa/sampleproject/issues",
    },

    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Development Status :: 5 - Production/Stable"
    ],
    # package_dir={"": "src"},
    # packages=setuptools.find_packages(where="src"),
    packages=setuptools.find_packages(),
    python_requires=">=3.6",
)
