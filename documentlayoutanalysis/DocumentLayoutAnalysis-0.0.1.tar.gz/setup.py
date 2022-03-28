
from setuptools import setup, find_packages
setup(
  name='DocumentLayoutAnalysis',
  version='0.0.1',
  description='DIT document layout',
  long_description=open('readme.txt').read() ,
  author='sneha dhole',
  packages=['DocumentLayoutAnalysis'],
  install_requires=['torch','pyyaml','torchvision','opencv-python','Pillow','fvcore','cloudpickle','omegaconf','pycocotools','timm','scipy','shapely','numpy']
)