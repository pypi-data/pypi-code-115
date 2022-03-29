import setuptools

with open("README.md", 'r', encoding="utf-8") as fh:
    long_description = fh.read()


setuptools.setup(
    name="magic-terminal",
    version="1.5.0",
    author="Marseel Eeso",
    author_email="marseeleeso@gmail.com",
    description="A fun way to customize your terminal with colors, styles etc...",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/Marseel-E/magic-terminal",
    project_urls={
        "Bug Tracker": "https://github.com/Marseel-E/magic-terminal/issues"
    },
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    package_dir={"": "MagicTerminal"},
    packages=setuptools.find_packages(where="MagicTerminal"),
    python_requires=">=3.8",
)
