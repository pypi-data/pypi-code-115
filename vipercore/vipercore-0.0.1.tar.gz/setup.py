from setuptools import setup, find_packages
 
classifiers = [
  'Development Status :: 5 - Production/Stable',
  'Intended Audience :: Education',
  'Operating System :: Microsoft :: Windows :: Windows 10',
  'License :: OSI Approved :: MIT License',
  'Programming Language :: Python :: 3'
]
 
setup(
  name='vipercore',
  version='0.0.1',
  description='Viper/Sage Apps Dev ENV',
  long_description=open('README.txt').read() + '\n\n' + open('CHANGELOG.txt').read(),
  url='',  
  author='Sage',
  author_email='naitikpgupta@gmail.com',
  license='MIT', 
  classifiers=classifiers,
  keywords='viper pkgs', 
  packages=find_packages(),
  install_requires=['sly'] 
)