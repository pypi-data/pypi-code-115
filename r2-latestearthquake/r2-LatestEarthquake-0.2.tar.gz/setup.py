import setuptools

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setuptools.setup(
    name="r2-LatestEarthquake",
    version="0.2",
    author="Ricky Rinaldy",
    author_email="ricky.rinaldy77@gmail.com",
    description="This package will get the latest earthquake from BMKG",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/ricky-blip/LatestEarthquakeIndonesia.git",
    project_urls={
        "About Author": "https://bit.ly/3ABmegZ",
    },
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: GNU General Public License v3 (GPLv3)",
        "Operating System :: OS Independent",
        "Development Status :: 5 - Production/Stable",
    ],
    packages=setuptools.find_packages(),
    python_requires=">=3.6",
)