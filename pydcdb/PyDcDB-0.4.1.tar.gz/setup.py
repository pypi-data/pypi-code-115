from setuptools import setup, find_packages
from pathlib import Path
this_directory = Path(__file__).parent
long_description = (this_directory / "README.md").read_text()


setup(
    name='PyDcDB',
    version='0.4.1',
    license="GNU",
    author="Dark-Light",
    author_email='darklight02014@gmail.com',
    packages=find_packages('src'),
    package_dir={'': 'src'},
    keywords='database sqlite3',
    install_requires=['aiosqlite'],
    long_description=long_description,
    long_description_content_type='text/markdown'
)