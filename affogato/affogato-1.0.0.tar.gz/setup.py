from setuptools import setup, find_packages

setup(
    name="affogato",
    version='1.0.0',
    packages=find_packages('src'),
    package_dir={'': 'src'},
    requires=["numpy"]
)