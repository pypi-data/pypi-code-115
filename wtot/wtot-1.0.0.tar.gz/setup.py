import sys, os

from setuptools import setup, find_packages
from wtot.version import __version__

def readme():
  with open('README.rst') as f:
    return f.read()

setup(name='wtot',
      version=__version__,
      description="WordTranslationOnTerminal",
      long_description=readme(),
      keywords='python dictionary terminal',
      author='YeeKear',
      author_email='554408064@sjtu.edu.cn',
      url='https://pypi.org/project/wtot/',
      include_package_data=True,
      zip_safe=False,
      classifiers=[
          'Environment :: Console',
          'Intended Audience :: Developers',
          'License :: OSI Approved :: MIT License',
          'Operating System :: OS Independent',
          'Programming Language :: Python',
          'Topic :: Terminals'
      ],    
      install_requires=[
        'termcolor',
      ],
      entry_points={
        'console_scripts':[
            'wtot = wtot.wtot:main'
        ]
      },
)
