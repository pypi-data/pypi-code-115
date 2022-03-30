import setuptools

setuptools.setup(
    name="zzha529_test",
    version="1.0",
    author="author",
    author_email="my@abc.ab",
    description="testtest",
    long_description="alonglongtest",
    packages=setuptools.find_packages(),
    install_requires=["redis==4.1.0"],
    python_requires=">3",
)

