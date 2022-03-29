import setuptools


with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()


setuptools.setup(
    name="MLB-TrajectoryCalculator",
    version="0.0.1",
    author="Jacob Lee",
    author_email="JLpython@outlook.com",
    description="A package containing utilities for calculating MLB ball trajectories",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/JLpython-py/MLB-TrajectoryCalculator",
    classifiers=[
        "Development Status :: 1 - Planning",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
    ],
    packages=setuptools.find_packages(),
    python_requires=">=3.6",
)