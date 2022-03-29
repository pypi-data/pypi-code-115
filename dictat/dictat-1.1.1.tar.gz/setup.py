import setuptools

setuptools.setup(
    name='dictat',
    version='1.1.1',
    description='Adict is an attribute-accessible dynamic dictionary wrapper',
    long_description=open('README.md').read(),
    long_description_content_type='text/markdown',
    author='Janos Kutscherauer',
    author_email='janoskut@gmail.com',
    url='https://gitlab.com/janoskut/dictat',
    license='UNLICENSE',
    license_files = ['UNLICENSE'],
    packages=setuptools.find_packages(),
    install_requires=[],
    python_requires='>=3.7',
)
