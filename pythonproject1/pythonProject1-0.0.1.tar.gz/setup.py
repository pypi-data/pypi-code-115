
from setuptools import setup, find_packages
setup(
  name='pythonProject1',
  version='0.0.1',
  description='DIT document layout',
  long_description=open('readme.txt').read() ,
  author='sneha dhole',
  packages=['pythonProject1'],
  install_requires=['torch','pyyaml','torchvision','opencv-python']
)