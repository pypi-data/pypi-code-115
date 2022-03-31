import setuptools

# python setup.py sdist bdist_wheel
# twine upload dist/* && rm -rf build dist *.egg-info

setuptools.setup(
    name="opensea_sdk",
    version="0.0.2",
    author="RA",
    author_email="busybus@null.net",
    keywords="python sdk opensea nft",
    description="Python SDK for OpenSea.",
    long_description="Python SDK for OpenSea (a port of [opensea-js](https://github.com/ProjectOpenSea/opensea-js)).",
    long_description_content_type="text/markdown",
    url="https://github.com/numpde/opensea_sdk",
    packages=setuptools.find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.8',
    install_requires=[],

    # Required for includes in MANIFEST.in
    #include_package_data=True,

    test_suite="nose.collector",
    tests_require=["nose"],
)
