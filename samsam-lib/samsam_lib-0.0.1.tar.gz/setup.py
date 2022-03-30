import pathlib
from setuptools import setup
#The directory containing this file
HERE = pathlib.Path(__file__).parent
#The text of the README file
README = (HERE / "README.md").read_text()
#This call to setup() does all the work
setup(
    name="samsam_lib", # package name
    version="0.0.1", # package version
    author="c-tawayip", # creator username
    author_email="piyawatchuangkrud@gmail.com", # email creator
    description="A temp package", # description
    long_description=README,
    ong_description_content_type="text/markdown",
    url="https://github.com/c-tawayip/sam_simple_package", #directory ที่เก็บ file code
    # url="#", #directory ที่เก็บ file code
    # license="MIT",
     classifiers=[
         "License :: OSI Approved :: MIT License",
         "Programming Language :: Python :: 3",
         "Programming Language :: Python :: 3.8",
     ],
     packages=["samsam_lib"], # folder ที่เก็บ package
     include_package_data=True,
     install_requires=[], # requirement
 )

