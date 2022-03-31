from setuptools import setup, find_packages

classifiers = [
  'Development Status :: 6 - Mature',
  'Intended Audience :: Information Technology',
  'Operating System :: Microsoft :: Windows :: Windows 10',
  'License :: OSI Approved :: MIT License',
  'Programming Language :: Python :: 3'
]
 
setup(
  name="hydrapyxl",
  version='0.0.2',
  description="HydraPyXl, Excel automation using Python.",
  long_description=open('README.txt').read() + '\n\n' + open('CHANGELOG.txt').read(),
  url='',
  author='Rizky Irswanda',
  author_email='rizky.irswanda115@gmail.com',
  license='MIT',
  classifiers=classifiers,
  keywords='excel',
  packages=find_packages(),
  install_requires=['openpyxl']
)