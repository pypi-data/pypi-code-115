#!/usr/bin/env python

try:
    from skbuild import setup
except ImportError:
    from setuptools import setup

import os


# readme
readme_filepath = os.path.join(os.path.dirname(__file__), "README.md")
try:
    import pypandoc
    long_description = pypandoc.convert(readme_filepath, 'rst')
except ImportError:
    long_description = open(readme_filepath).read()


# Windows
build_cmake_args = list()
if os.getenv("WIN_BUID"):
    build_cmake_args.append('-DUSE_WIN_DEP=ON')

# setup
setup(
    name='mixstream',
    version='1.1.0',
    description='MixStream is a C-extension to combine SoundTouch and SDL_mixer',
    long_description=long_description,
    long_description_content_type='text/markdown',
    author='FoFiX team',
    author_email='contact@fofix.org',
    license='GPLv2+',
    url='https://github.com/fofix/python-mixstream',
    packages=['mixstream'],
    package_data={'mixstream': ['*.dll']},
    zip_safe=False,
    classifiers=[
        'Intended Audience :: Developers',
        'License :: OSI Approved :: GNU General Public License v2 or later (GPLv2+)',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
        'Programming Language :: Python :: 3.10',
        'Topic :: Multimedia',
        'Topic :: Multimedia :: Sound/Audio',
        'Topic :: Software Development :: Libraries',
    ],
    keywords='music vorbis sdl soundtouch',
    test_suite="tests",
    # skbuild options
    cmake_args=build_cmake_args,
)
