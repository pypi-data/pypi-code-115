from setuptools import setup, find_packages

def GetText(fName):
    with open(fName, 'r') as f:
        return f.read()

setup(
    name='unicode-nfd2c',
    version='1.0.2',
    license='GPLv2',
    description='Renames NFD Unicode names to NFC',
    long_description=GetText('README.md'),
    long_description_content_type='text/markdown',
    author='xvim64',
    author_email='xvim64@gmail.com',
    url='https://github.com/xvim64/nfd2c',
    classifiers=[
        'Environment :: Console',
        'Programming Language :: Python :: 3',
        'License :: OSI Approved :: GNU General Public License v2 (GPLv2)',
        'Operating System :: OS Independent',
    ],
    packages=find_packages(),
    keywords=['mac', 'hangeul','hangul', 'unicode', 'nfd', 'nfc'],
    entry_points={
        'console_scripts': [ 'nfd2c=nfd2c:main' ]
    },
    python_requires='>=3',
)
