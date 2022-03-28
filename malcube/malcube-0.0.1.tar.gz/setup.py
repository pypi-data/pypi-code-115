import setuptools

from malcube import __version__

with open("README.md") as fh:
    long_description = fh.read()

required_requirements = [
    "pefile",
    "pyelftools",
    "click",
]

setuptools.setup(
    name="malcube",  # Replace with your own username
    version=__version__,
    author="JunWei Song",
    author_email="sungboss2004@gmail.com",
    description="Next-generation reverse engineering engine and threat intelligence analyzer",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/malcube/malcube",
    packages=setuptools.find_packages(),

    entry_points={
        "console_scripts": [
            "malcube=malcube.cli:entry_point",
        ]
    },
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: GNU General Public License v3 (GPLv3)",
        "Operating System :: OS Independent",
        "Topic :: Security",
    ],
    python_requires=">=3.9",
    install_requires=required_requirements,
)
