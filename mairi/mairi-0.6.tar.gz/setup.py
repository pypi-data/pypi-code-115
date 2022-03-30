from setuptools import setup, find_packages


setup(
    name='mairi',
    version='0.6',
    license='MIT',
    author="mairi lydia",
    author_email='email@example.com',
    packages=find_packages('src'),
    package_dir={'': 'src'},
    url='https://github.com/johndahunsi/omni',
    keywords='example project',
    install_requires=[
          'scikit-learn',
      ],

)
