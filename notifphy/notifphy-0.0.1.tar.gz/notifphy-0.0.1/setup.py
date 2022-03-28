import setuptools

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setuptools.setup(
    name="notifphy",
    version="0.0.1",
    author="Sakurai07/Ehnryu",
    author_email="",
    description="A library to push notifications",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/n30nyx/notifphy",
    project_urls={
        "Bug Tracker": "https://github.com/n30nyx/notifphy/issues",
    },
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    package_dir={"": "notify"},
    packages=setuptools.find_packages(where="notify"),
    install_requires=["poshpy"]
)
