from distutils.command import install_lib
from setuptools import setup, find_packages


classifiers = [
    'Development Status :: 5 - Production/Stable',
    ' Intended Audience :: Education',
    'Operating System :: Microsoft :: Windows :: Windows 10',
    'License :: OSI Approved :: MIT License',
    'Programming Language :: Python :: 3'
]


setup(
    name='F1_data',
    version='0.0.1',
    description='Formula 1 data analysis based on FastF1 library',
    long_description=open('README.txt').read() + '\n\n'+ open('CHANGELOG.txt').read(),
    url='https://www.leonardorama.tk',
    author='Leonardo Ramazzotti',
    license='MIT',
    classifiers=classifiers,
    keywords='formula1',
    packages=find_packages(),
    install_requires=['Fastf1']


)