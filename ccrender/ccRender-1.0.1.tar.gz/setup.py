import io
import os
from setuptools import setup
from setuptools import find_packages

# Encoding specification for PY3
with io.open('README.rst', encoding='utf-8') as fp:
    description = fp.read()

# check and tweak version number
# can change author and email if necessary
setup(
    name='ccRender',
    # version number (will change later)
    version='1.0.1',
    # used own name and email, will change later if necessary
    author='Cliffton Hicks',
    author_email='cliffton@omnibond.com',
    license='LGPL',
    url='https://github.com/omnibond/ccRender',
    description='Cloud-based Blender rendering addon',
    long_description=description,
    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3',
    ],
    py_modules=['ccrender'],
    packages=find_packages(exclude=['samples', 'tests']),
    install_requires=['scp', 'pyperclip'],
    python_requires=">=3.4",
)
