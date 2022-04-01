from setuptools import setup

setup(
    name='cameo_fastapi',
    version='0.2.6',
    description='CAMEO FastAPI'
                '2022-04-01 v0.2.6 init_fastapi() to init()',
    url='https://github.com/bohachu/cameo_fastapi',
    author='Bowen Chiu',
    author_email='bohachu@gmail.com',
    license='BSD 0-clause license',
    packages=['cameo_fastapi'],
    install_requires=['uvicorn', 'fastapi', ],
    classifiers=['Programming Language :: Python :: 3']
)
