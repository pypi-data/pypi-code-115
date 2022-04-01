from setuptools import setup

with open('README.md', encoding='utf-8') as f:
    long_description = f.read()

version = {
    '__version__': '0.0.1',
}

setup(
    name='injection-mold',
    version=version['__version__'],
    description='Spring/Micronaut-esque dependency injection system for Python using type hints',
    long_description=long_description,
    long_description_content_type='text/markdown',
    author='Jonathan McCaffrey',
    author_email='jmc@teammccaffrey.com',
    url='https://github.com/jmccaffrey42/mold',
    license='MPL-2.0',
    packages=['mold'],
    package_dir={'': 'src'},
    install_requires=[
        'pytest'
    ],
    # scripts=['bin/cooley'],
    # include_package_data=True,
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Programming Language :: Python :: 3.6',
    ],
)
