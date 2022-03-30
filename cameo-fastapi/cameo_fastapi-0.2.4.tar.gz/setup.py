from setuptools import setup

setup(
    name='cameo_fastapi',
    version='0.2.4',
    description='CAMEO FastAPI, add main',
    url='https://github.com/bohachu/cameo_fastapi',
    author='Bowen Chiu',
    author_email='bohachu@gmail.com',
    license='BSD 0-clause license',
    packages=['cameo_fastapi'],
    install_requires=['uvicorn', 'fastapi', ],
    classifiers=['Programming Language :: Python :: 3']
)
