from setuptools import setup
setup(
    name='cameo_sheet',
    version='0.1.0',
    description='Read google sheet',
    url='https://github.com/bohachu/cameo_sheet',
    author='Bowen Chiu',
    author_email='bohachu@gmail.com',
    license='BSD 2-clause',
    packages=['cameo_sheet'],
    install_requires=[
      'gspread',
    ],
    classifiers=[
        'Programming Language :: Python :: 3',
    ],
)
