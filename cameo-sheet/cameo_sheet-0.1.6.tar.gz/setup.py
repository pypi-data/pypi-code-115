from setuptools import setup

setup(
    name='cameo_sheet',
    version='0.1.6',
    description='Read Google Sheet'
                '2022-04-01 v0.1.6 test_cameo_sheet.py ok, go.sh can work now.',
    url='https://github.com/bohachu/cameo_sheet',
    author='Bowen Chiu',
    author_email='bohachu@gmail.com',
    license='BSD 2-clause',
    packages=['cameo_sheet'],
    install_requires=[
        'fastapi',
        'gspread',
        'oauth2client',
    ],
    classifiers=[
        'Programming Language :: Python :: 3',
    ],
)
