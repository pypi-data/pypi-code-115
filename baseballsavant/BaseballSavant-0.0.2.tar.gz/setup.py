import setuptools


with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()


setuptools.setup(
    name="BaseballSavant",
    version="0.0.2",
    author="Jacob Lee",
    author_email="JLpython@outlook.com",
    description="API wrapper for the MLB Baseball Savant website",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/JLpython-py/BaseballSavant.py",
    classifiers=[
        "Development Status :: 1 - Planning",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10"
    ],
    packages=setuptools.find_packages(
        include=["savant*"],
        exclude=["savant.tests"],
    ),
    python_requires=">=3.8",
)
