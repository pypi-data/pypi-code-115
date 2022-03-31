from setuptools import setup, find_packages


setup(
    name='Stemming-Ind',
    version='0.0.1',
    license='MIT',
    author="Hangsbreaker",
    author_email='hangbreaker@gmail.com',
    packages=find_packages('src'),
    package_dir={'': 'src'},
    url='https://github.com/hangsbreaker/ind-stemming',
    keywords='Stemming Bahasa Indonesia',
    install_requires=['re'],
)