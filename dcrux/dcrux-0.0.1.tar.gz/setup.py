import setuptools

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setuptools.setup(
    name="dcrux",
    version="0.0.1",
    author="Vinay Panchal",
    author_email="vinay.npanchal@gmail.com",
    description="Dataset creation, management and analysis tool",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/datasetcrux/dcrux",
    project_urls={
        "Bug Tracker": "https://github.com/datasetcrux/dcrux/issues",
    },
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    package_dir={"": "src"},
    packages=setuptools.find_packages(where="src"),
    python_requires=">=3.6",
)