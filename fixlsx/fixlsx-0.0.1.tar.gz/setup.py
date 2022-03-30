from setuptools import setup, find_packages
 
classifiers = [
  'Development Status :: 5 - Production/Stable',
  'Intended Audience :: Education',
  'Operating System :: Microsoft :: Windows :: Windows 10',
  'Programming Language :: Python :: 3'
]
 
setup(
  name='fixlsx',
  version='0.0.1',
  description='A very basic calculator',
  long_description=open('README.txt').read() + '\n\n' + open('CHANGELOG.txt').read(),
  url='',  
  author='Ereteam',
  author_email='devadm@ereteam.com',
  license='', 
  classifiers=classifiers,
  keywords='calculator', 
  packages=find_packages(),
  install_requires=["pyenchant==3.2.2", "openpyxl==3.0.9", "pandas"] 
)