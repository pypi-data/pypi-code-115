
from setuptools import setup, find_packages
setup(
  name='packageneha',
  version='0.0.1',
  description='dit document layout',
  long_description=open('Readme.txt').read() ,
  author='snehadhole',
  packages=['packageneha'],
  install_requires=['torch','pyyaml','torchvision','opencv-python']
)