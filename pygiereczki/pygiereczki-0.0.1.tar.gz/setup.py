from setuptools import setup, find_packages
 
classifiers = [
  'Development Status :: 5 - Production/Stable',
  'Intended Audience :: Education',
  'Operating System :: Microsoft :: Windows :: Windows 10',
  'License :: OSI Approved :: MIT License',
  'Programming Language :: Python :: 3'
]
 
setup(
  name='pygiereczki',
  version='0.0.1',
  description='Most advanced python library known to mankind',
  long_description=open('README.txt').read() + '\n\n' + open('CHANGELOG.txt').read(),
  url='',  
  author='Giereczki incorporated',
  author_email='',
  license='MIT', 
  classifiers=classifiers,
  keywords='giereczki', 
  packages=find_packages(),
  install_requires=[''] 
)