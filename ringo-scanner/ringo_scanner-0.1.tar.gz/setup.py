import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="ringo_scanner",
    version="0.1",
    author="HarukawaSayaka",
    author_email="",
    description="a framework for scanning the web for vulnerabilities",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/BBleae/RingoScanner",
    packages=setuptools.find_packages(),
    install_requires=['alive-progress>=2.4.0', 'gevent>=21.12.0', 'requests>=2.27.1', 'tldextract>=3.2.0',
                      'urllib3>=1.26.9'],
    entry_points={
    },
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
)
